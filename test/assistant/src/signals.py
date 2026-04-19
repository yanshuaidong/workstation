"""assistant 七个指标信号计算与入库。"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from assistant_db import dump_json, parse_date, to_date_str
from assistant_settings import ROLLING_WINDOW_DAYS


INDICATORS = (
    "MF_Edge3",
    "MF_Accel",
    "MF_Duration",
    "MS_Divergence",
    "MF_Magnitude",
    "MF_BreakZone",
    "Composite_Score",
)


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    if pd.isna(value):
        return None
    return float(value)


def _rolling_window(values: np.ndarray, idx: int, window_size: int = ROLLING_WINDOW_DAYS) -> np.ndarray:
    start = max(0, idx - window_size + 1)
    window = values[start : idx + 1]
    return window[~np.isnan(window)]


def _streak_info(values: np.ndarray, idx: int) -> dict[str, Any] | None:
    if idx < 1 or np.isnan(values[idx]) or np.isnan(values[idx - 1]) or values[idx] == values[idx - 1]:
        return None

    sign = 1 if values[idx] > values[idx - 1] else -1
    length = 2
    start_idx = idx - 1
    j = idx - 1
    while j > 0:
        prev_delta = values[j] - values[j - 1]
        if prev_delta * sign > 0:
            length += 1
            start_idx = j - 1
            j -= 1
        else:
            break

    return {
        "sign": sign,
        "direction": "LONG" if sign > 0 else "SHORT",
        "length": length,
        "start_idx": start_idx,
    }


def _build_magnitude_distribution(values: np.ndarray, idx: int) -> list[float]:
    start = max(2, idx - ROLLING_WINDOW_DAYS + 1)
    magnitudes = []
    for j in range(start, idx + 1):
        v0, v1, v2 = values[j - 2], values[j - 1], values[j]
        if np.isnan(v0) or np.isnan(v1) or np.isnan(v2):
            continue
        if v0 < v1 < v2 or v0 > v1 > v2:
            magnitudes.append(abs(v2 - v0))
    return magnitudes


def _make_signal_row(
    group: pd.DataFrame,
    idx: int,
    indicator: str,
    direction: str,
    strength: float | None,
    indicator_value: str,
    extra_json: dict[str, Any],
) -> dict[str, Any]:
    return {
        "signal_date": parse_date(group.at[idx, "trade_date"]),
        "variety_id": int(group.at[idx, "variety_id"]),
        "variety_name": str(group.at[idx, "variety_name"]),
        "indicator": indicator,
        "direction": direction,
        "triggered": 1,
        "strength": _safe_float(strength),
        "indicator_value": indicator_value,
        "extra_json": {
            "indicator_value": indicator_value,
            **extra_json,
        },
    }


def _generate_variety_signals(group: pd.DataFrame) -> list[dict[str, Any]]:
    group = group.sort_values("trade_date").reset_index(drop=True)
    mf = group["main_force"].astype(float).to_numpy()
    rt = group["retail"].astype(float).to_numpy()
    records: list[dict[str, Any]] = []

    for idx in range(len(group)):
        window = _rolling_window(mf, idx)
        if len(window) == 0:
            continue

        q10 = float(np.percentile(window, 10))
        q20 = float(np.percentile(window, 20))
        q50 = float(np.percentile(window, 50))
        q80 = float(np.percentile(window, 80))
        q90 = float(np.percentile(window, 90))

        streak = _streak_info(mf, idx)
        if idx >= 2:
            v0, v1, v2 = float(mf[idx - 2]), float(mf[idx - 1]), float(mf[idx])
            if v0 < v1 < v2 or v0 > v1 > v2:
                edge_direction = "LONG" if v2 > v0 else "SHORT"
                start_val = v0
                if edge_direction == "LONG":
                    if start_val < q10:
                        zone = "极端底部"
                    elif start_val < q50:
                        zone = "普通底部"
                    else:
                        zone = "中性偏高"
                else:
                    if start_val > q90:
                        zone = "极端顶部"
                    elif start_val > q50:
                        zone = "普通顶部"
                    else:
                        zone = "中性偏低"

                records.append(
                    _make_signal_row(
                        group,
                        idx,
                        "MF_Edge3",
                        edge_direction,
                        start_val,
                        zone,
                        {
                            "window_quantiles": {"p10": q10, "p50": q50, "p90": q90},
                            "start_value": start_val,
                            "values": [v0, v1, v2],
                        },
                    )
                )

        if idx >= 2:
            if v0 < v1 < v2 or v0 > v1 > v2:
                direction = "LONG" if v2 > v0 else "SHORT"
                delta1 = v1 - v0
                delta2 = v2 - v1
                accel = abs(delta2) - abs(delta1)
                accel_text = "加速" if accel > 0 else "减速"
                records.append(
                    _make_signal_row(
                        group,
                        idx,
                        "MF_Accel",
                        direction,
                        accel,
                        f"{accel_text}({accel:+.2f})",
                        {
                            "delta1": delta1,
                            "delta2": delta2,
                            "acceleration": accel,
                        },
                    )
                )

                rt_delta_avg = ((rt[idx - 1] - rt[idx - 2]) + (rt[idx] - rt[idx - 1])) / 2
                mf_delta_avg = ((mf[idx - 1] - mf[idx - 2]) + (mf[idx] - mf[idx - 1])) / 2
                if direction == "LONG":
                    divergence_type = "强共振" if rt_delta_avg < 0 else "弱共振"
                else:
                    divergence_type = "强共振" if rt_delta_avg > 0 else "弱共振"
                divergence_score = abs(mf_delta_avg) + abs(rt_delta_avg)
                records.append(
                    _make_signal_row(
                        group,
                        idx,
                        "MS_Divergence",
                        direction,
                        divergence_score,
                        f"{divergence_type}({divergence_score:.2f})",
                        {
                            "divergence_type": divergence_type,
                            "divergence_score": divergence_score,
                            "main_force_delta_avg": float(mf_delta_avg),
                            "retail_delta_avg": float(rt_delta_avg),
                        },
                    )
                )

                magnitudes = _build_magnitude_distribution(mf, idx)
                magnitude = abs(v2 - v0)
                if magnitudes:
                    mag_p25 = float(np.percentile(magnitudes, 25))
                    mag_p75 = float(np.percentile(magnitudes, 75))
                else:
                    mag_p25 = magnitude
                    mag_p75 = magnitude

                if magnitude >= mag_p75:
                    magnitude_type = "高幅度"
                elif magnitude >= mag_p25:
                    magnitude_type = "中幅度"
                else:
                    magnitude_type = "低幅度"
                records.append(
                    _make_signal_row(
                        group,
                        idx,
                        "MF_Magnitude",
                        direction,
                        magnitude,
                        f"{magnitude_type}({magnitude:.2f})",
                        {
                            "magnitude": magnitude,
                            "magnitude_type": magnitude_type,
                            "window_quantiles": {"p25": mag_p25, "p75": mag_p75},
                        },
                    )
                )

                if direction == "LONG":
                    if v0 < q10 and v2 >= q10:
                        zone_type = "穿越底部边界"
                        zone_strength = 2.0
                    elif v0 < q10 and v2 < q10:
                        zone_type = "极端区内震荡"
                        zone_strength = 1.0
                    else:
                        zone_type = "普通区间3连升"
                        zone_strength = 0.0
                else:
                    if v0 > q90 and v2 <= q90:
                        zone_type = "穿越顶部边界"
                        zone_strength = 2.0
                    elif v0 > q90 and v2 > q90:
                        zone_type = "极端区内震荡"
                        zone_strength = 1.0
                    else:
                        zone_type = "普通区间3连降"
                        zone_strength = 0.0
                records.append(
                    _make_signal_row(
                        group,
                        idx,
                        "MF_BreakZone",
                        direction,
                        zone_strength,
                        zone_type,
                        {
                            "zone_type": zone_type,
                            "window_quantiles": {"p10": q10, "p90": q90},
                            "values": [v0, v1, v2],
                        },
                    )
                )

        if streak and streak["length"] in (3, 5, 7):
            duration_value = f"D{streak['length']}"
            duration_values = [
                float(mf[j])
                for j in range(streak["start_idx"], idx + 1)
                if not np.isnan(mf[j])
            ]
            duration_deltas = [
                float(duration_values[j] - duration_values[j - 1])
                for j in range(1, len(duration_values))
            ]
            records.append(
                _make_signal_row(
                    group,
                    idx,
                    "MF_Duration",
                    streak["direction"],
                    float(streak["length"]),
                    duration_value,
                    {
                        "streak_length": streak["length"],
                        "values": duration_values,
                        "deltas": duration_deltas,
                    },
                )
            )

        if streak and streak["length"] >= 3:
            direction = streak["direction"]
            length = streak["length"]
            if length >= 7:
                duration_score = 3
            elif length >= 5:
                duration_score = 2
            else:
                duration_score = 1

            accel_score = 0
            if idx >= 2:
                prev_step = abs(float(mf[idx - 1] - mf[idx - 2]))
                last_step = abs(float(mf[idx] - mf[idx - 1]))
                accel_score = 1 if last_step > prev_step else 0

            start_val = float(mf[streak["start_idx"]])
            if direction == "LONG":
                if start_val < q10:
                    edge_score = 2
                elif start_val < q20:
                    edge_score = 1
                else:
                    edge_score = 0
            else:
                if start_val > q90:
                    edge_score = 2
                elif start_val > q80:
                    edge_score = 1
                else:
                    edge_score = 0

            retail_delta = float(rt[idx] - rt[idx - 1]) if idx >= 1 else 0.0
            if direction == "LONG" and retail_delta < 0:
                divergence_score = 1
            elif direction == "SHORT" and retail_delta > 0:
                divergence_score = 1
            else:
                divergence_score = 0

            if idx >= 2:
                composite_magnitudes = _build_magnitude_distribution(mf, idx)
                current_mag = abs(float(mf[idx] - mf[idx - 2]))
                if composite_magnitudes:
                    mag_p25 = float(np.percentile(composite_magnitudes, 25))
                    mag_p75 = float(np.percentile(composite_magnitudes, 75))
                else:
                    mag_p25 = current_mag
                    mag_p75 = current_mag
                if current_mag >= mag_p75:
                    magnitude_score = 2
                elif current_mag >= mag_p25:
                    magnitude_score = 1
                else:
                    magnitude_score = 0
            else:
                current_mag = 0.0
                mag_p25 = 0.0
                mag_p75 = 0.0
                magnitude_score = 0

            composite_score = (
                duration_score * 0.30
                + accel_score * 0.20
                + edge_score * 0.20
                + divergence_score * 0.20
                + magnitude_score * 0.10
            )
            records.append(
                _make_signal_row(
                    group,
                    idx,
                    "Composite_Score",
                    direction,
                    composite_score,
                    f"{composite_score:.2f}",
                    {
                        "components": {
                            "duration_score": duration_score,
                            "accel_score": accel_score,
                            "edge_score": edge_score,
                            "divergence_score": divergence_score,
                            "magnitude_score": magnitude_score,
                        },
                        "window_quantiles": {
                            "edge_p10": q10,
                            "edge_p20": q20,
                            "edge_p80": q80,
                            "edge_p90": q90,
                            "magnitude_p25": mag_p25,
                            "magnitude_p75": mag_p75,
                        },
                        "streak_length": length,
                        "current_magnitude": current_mag,
                    },
                )
            )

    return records


def generate_signals(
    market_df: pd.DataFrame,
    start_date=None,
    end_date=None,
) -> pd.DataFrame:
    """按品种生成全部触发信号。"""
    if market_df.empty:
        return pd.DataFrame(
            columns=[
                "signal_date",
                "variety_id",
                "variety_name",
                "indicator",
                "direction",
                "triggered",
                "strength",
                "indicator_value",
                "extra_json",
            ]
        )

    start_filter = parse_date(start_date) if start_date else None
    end_filter = parse_date(end_date) if end_date else None

    records: list[dict[str, Any]] = []
    for _, group in market_df.groupby("variety_id"):
        records.extend(_generate_variety_signals(group))

    signals_df = pd.DataFrame(records)
    if signals_df.empty:
        return signals_df

    if start_filter:
        signals_df = signals_df[signals_df["signal_date"] >= start_filter]
    if end_filter:
        signals_df = signals_df[signals_df["signal_date"] <= end_filter]

    signals_df = signals_df.sort_values(
        ["signal_date", "variety_id", "indicator", "direction"]
    ).reset_index(drop=True)
    return signals_df


def replace_signals(conn, signals_df: pd.DataFrame, start_date, end_date) -> int:
    """按日期范围覆盖写入 assistant_signals。"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            DELETE FROM assistant_signals
            WHERE signal_date >= %s AND signal_date <= %s
            """,
            (to_date_str(start_date), to_date_str(end_date)),
        )

        if signals_df.empty:
            conn.commit()
            return 0

        sql = """
            INSERT INTO assistant_signals
                (signal_date, variety_id, variety_name, indicator, direction,
                 triggered, strength, extra_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = [
            (
                to_date_str(row.signal_date),
                int(row.variety_id),
                row.variety_name,
                row.indicator,
                row.direction,
                int(row.triggered),
                _safe_float(row.strength),
                dump_json(row.extra_json),
            )
            for row in signals_df.itertuples(index=False)
        ]
        cursor.executemany(sql, params)
        conn.commit()
        return len(params)
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
