"""
A通道信号计算模块。
对每个品种计算4种信号：A_OPEN_LONG / A_OPEN_SHORT / A_CLOSE_LONG / A_CLOSE_SHORT。
信号逻辑严格对照 backtest_portfolio_strict7_tp3.py compute_signals_strict7_tp3。
"""
from __future__ import annotations

import json
import logging
from datetime import date

import numpy as np
import pandas as pd
import pymysql

from .settings import MOMENTUM_LOOKBACK

logger = logging.getLogger(__name__)


def _mark_breakpoints(dates: pd.Series) -> pd.Series:
    diffs = dates.diff().dt.days.fillna(1)
    return diffs.le(7)


def _make_cycle_id(variety_id: int | None, direction: str, open_date: date) -> str:
    prefix = f"{variety_id}-" if variety_id is not None else ""
    return f"{prefix}{direction}-{open_date.isoformat()}"


def compute_signals(df: pd.DataFrame, variety_id: int | None = None) -> pd.DataFrame:
    out = df.copy()
    out["date_cont"] = _mark_breakpoints(out["trade_date"])
    out["main_diff"] = out["main_force"].diff()
    out["retail_diff"] = out["retail"].diff()

    cont7 = out["date_cont"].astype(int).rolling(6, min_periods=6).sum().eq(6)
    cont3 = out["date_cont"].astype(int).rolling(2, min_periods=2).sum().eq(2)

    out["cont7"] = cont7
    out["cont3"] = cont3

    bg1 = out["main_force"].shift(6)
    bg2 = out["main_force"].shift(5)
    bg3 = out["main_force"].shift(4)
    bg4 = out["main_force"].shift(3)
    bg5 = out["main_force"].shift(2)

    out["bg1"] = bg1
    out["bg2"] = bg2
    out["bg3"] = bg3
    out["bg4"] = bg4
    out["bg5"] = bg5

    trigger_main_up = out["main_diff"].shift(1).gt(0) & out["main_diff"].gt(0)
    trigger_main_down = out["main_diff"].shift(1).lt(0) & out["main_diff"].lt(0)
    trigger_retail_down = out["retail_diff"].shift(1).lt(0) & out["retail_diff"].lt(0)
    trigger_retail_up = out["retail_diff"].shift(1).gt(0) & out["retail_diff"].gt(0)

    # bg5 必须是 bg1..bg5 中的极值，确保转折点唯一性（避免连续触发）
    long_extremum = bg5.lt(bg1) & bg5.lt(bg2) & bg5.lt(bg3) & bg5.lt(bg4)
    short_extremum = bg5.gt(bg1) & bg5.gt(bg2) & bg5.gt(bg3) & bg5.gt(bg4)

    long_bg = bg1.lt(0) & bg2.lt(0) & bg3.lt(0) & bg4.lt(0) & bg5.lt(0) & long_extremum
    short_bg = bg1.gt(0) & bg2.gt(0) & bg3.gt(0) & bg4.gt(0) & bg5.gt(0) & short_extremum

    out["A_OPEN_LONG"] = cont7 & long_bg & trigger_main_up & trigger_retail_down
    out["A_OPEN_SHORT"] = cont7 & short_bg & trigger_main_down & trigger_retail_up

    out["m3"] = out["main_force"] - out["main_force"].shift(2)
    out["A_CLOSE_LONG"] = cont3 & out["m3"].lt(0)
    out["A_CLOSE_SHORT"] = cont3 & out["m3"].gt(0)

    # 理论状态机：平仓信号只依赖理论开仓周期，不依赖真实账户持仓。
    current_state = "none"
    current_cycle_id: str | None = None
    current_open_date: date | None = None
    close_long_filtered: list[bool] = []
    close_short_filtered: list[bool] = []
    signal_roles: list[str | None] = []
    directions: list[str | None] = []
    cycle_ids: list[str | None] = []
    related_open_dates: list[date | None] = []
    theory_state_before: list[str] = []
    theory_state_after: list[str] = []
    signal_states: list[str] = []

    for i in range(len(out)):
        open_long  = bool(out["A_OPEN_LONG"].iloc[i])
        open_short = bool(out["A_OPEN_SHORT"].iloc[i])
        close_long = bool(out["A_CLOSE_LONG"].iloc[i])
        close_short = bool(out["A_CLOSE_SHORT"].iloc[i])
        trade_date = out["trade_date"].iloc[i].date()

        state_before = current_state
        role: str | None = None
        direction: str | None = None
        row_cycle_id: str | None = None
        row_open_date: date | None = None
        close_long_allowed = False
        close_short_allowed = False

        if close_long and current_state == "long":
            role = "close"
            direction = "LONG"
            row_cycle_id = current_cycle_id
            row_open_date = current_open_date
            close_long_allowed = True
            current_state = "none"
            current_cycle_id = None
            current_open_date = None
        elif close_short and current_state == "short":
            role = "close"
            direction = "SHORT"
            row_cycle_id = current_cycle_id
            row_open_date = current_open_date
            close_short_allowed = True
            current_state = "none"
            current_cycle_id = None
            current_open_date = None
        elif open_long:
            role = "open"
            direction = "LONG"
            row_cycle_id = _make_cycle_id(variety_id, direction, trade_date)
            current_state = "long"
            current_cycle_id = row_cycle_id
            current_open_date = trade_date
        elif open_short:
            role = "open"
            direction = "SHORT"
            row_cycle_id = _make_cycle_id(variety_id, direction, trade_date)
            current_state = "short"
            current_cycle_id = row_cycle_id
            current_open_date = trade_date

        close_long_filtered.append(close_long_allowed)
        close_short_filtered.append(close_short_allowed)
        signal_roles.append(role)
        directions.append(direction)
        cycle_ids.append(row_cycle_id)
        related_open_dates.append(row_open_date)
        theory_state_before.append(state_before)
        theory_state_after.append(current_state)
        signal_states.append(current_state)

    out["A_CLOSE_LONG"] = close_long_filtered
    out["A_CLOSE_SHORT"] = close_short_filtered
    out["signal_role"] = signal_roles
    out["direction"] = directions
    out["cycle_id"] = cycle_ids
    out["related_open_date"] = related_open_dates
    out["theory_state_before"] = theory_state_before
    out["theory_state_after"] = theory_state_after
    out["signal_state"] = signal_states

    scores: list[float] = []
    abs_m3 = out["m3"].abs()
    for i in range(len(out)):
        current = abs_m3.iloc[i]
        hist = abs_m3.iloc[max(0, i - MOMENTUM_LOOKBACK) : i].dropna()
        if pd.isna(current) or len(hist) < MOMENTUM_LOOKBACK:
            scores.append(np.nan)
            continue
        scores.append(float(hist.le(current).sum() / MOMENTUM_LOOKBACK))
    out["main_score"] = scores

    return out


def _fv(v) -> float | None:
    return float(v) if pd.notna(v) else None


def _bv(v) -> bool:
    return bool(v) if pd.notna(v) else False


def _make_extra_json(signal_df: pd.DataFrame, idx_pos: int, signal_type: str) -> str:
    r = signal_df.iloc[idx_pos]
    is_open = signal_type in ("A_OPEN_LONG", "A_OPEN_SHORT")
    win_size = 7 if is_open else 3

    start = max(0, idx_pos - win_size + 1)
    window = [
        {
            "trade_date": signal_df.iloc[i]["trade_date"].strftime("%Y-%m-%d"),
            "main_force": _fv(signal_df.iloc[i]["main_force"]),
            "retail": _fv(signal_df.iloc[i]["retail"]),
        }
        for i in range(start, idx_pos + 1)
    ]

    main_diff_t = _fv(r.get("main_diff"))
    retail_diff_t = _fv(r.get("retail_diff"))
    prev = signal_df.iloc[idx_pos - 1] if idx_pos >= 1 else None
    main_diff_t1 = _fv(prev["main_diff"]) if prev is not None else None
    retail_diff_t1 = _fv(prev["retail_diff"]) if prev is not None else None

    bg1 = _fv(r.get("bg1"))
    bg2 = _fv(r.get("bg2"))
    bg3 = _fv(r.get("bg3"))
    bg4 = _fv(r.get("bg4"))
    bg5 = _fv(r.get("bg5"))
    m3 = _fv(r.get("m3"))

    data: dict = {
        "main_force": _fv(r["main_force"]),
        "retail": _fv(r["retail"]),
        "m3": m3,
        "signal_role": r.get("signal_role"),
        "direction": r.get("direction"),
        "cycle_id": r.get("cycle_id"),
        "related_open_date": r.get("related_open_date").isoformat() if r.get("related_open_date") else None,
        "theory_state_before": r.get("theory_state_before"),
        "theory_state_after": r.get("theory_state_after"),
        "window": window,
    }

    if is_open:
        data["bg"] = {"bg1": bg1, "bg2": bg2, "bg3": bg3, "bg4": bg4, "bg5": bg5}
        data["trigger"] = {
            "main_diff_t1": main_diff_t1,
            "main_diff_t": main_diff_t,
            "retail_diff_t1": retail_diff_t1,
            "retail_diff_t": retail_diff_t,
        }

        def _bg5_is_min() -> bool:
            vals = [bg1, bg2, bg3, bg4, bg5]
            return all(v is not None for v in vals) and bg5 < bg1 and bg5 < bg2 and bg5 < bg3 and bg5 < bg4  # type: ignore[operator]

        def _bg5_is_max() -> bool:
            vals = [bg1, bg2, bg3, bg4, bg5]
            return all(v is not None for v in vals) and bg5 > bg1 and bg5 > bg2 and bg5 > bg3 and bg5 > bg4  # type: ignore[operator]

        if signal_type == "A_OPEN_LONG":
            data["conditions"] = {
                "cont7": _bv(r.get("cont7")),
                "bg1_lt0": bg1 is not None and bg1 < 0,
                "bg2_lt0": bg2 is not None and bg2 < 0,
                "bg3_lt0": bg3 is not None and bg3 < 0,
                "bg4_lt0": bg4 is not None and bg4 < 0,
                "bg5_lt0": bg5 is not None and bg5 < 0,
                "bg5_is_min": _bg5_is_min(),
                "main_diff_t1_gt0": main_diff_t1 is not None and main_diff_t1 > 0,
                "main_diff_t_gt0": main_diff_t is not None and main_diff_t > 0,
                "retail_diff_t1_lt0": retail_diff_t1 is not None and retail_diff_t1 < 0,
                "retail_diff_t_lt0": retail_diff_t is not None and retail_diff_t < 0,
            }
        else:  # A_OPEN_SHORT
            data["conditions"] = {
                "cont7": _bv(r.get("cont7")),
                "bg1_gt0": bg1 is not None and bg1 > 0,
                "bg2_gt0": bg2 is not None and bg2 > 0,
                "bg3_gt0": bg3 is not None and bg3 > 0,
                "bg4_gt0": bg4 is not None and bg4 > 0,
                "bg5_gt0": bg5 is not None and bg5 > 0,
                "bg5_is_max": _bg5_is_max(),
                "main_diff_t1_lt0": main_diff_t1 is not None and main_diff_t1 < 0,
                "main_diff_t_lt0": main_diff_t is not None and main_diff_t < 0,
                "retail_diff_t1_gt0": retail_diff_t1 is not None and retail_diff_t1 > 0,
                "retail_diff_t_gt0": retail_diff_t is not None and retail_diff_t > 0,
            }
    else:
        if signal_type == "A_CLOSE_LONG":
            cond_key = "m3_lt0"
            cond_val = m3 is not None and m3 < 0
        else:
            cond_key = "m3_gt0"
            cond_val = m3 is not None and m3 > 0
        data["conditions"] = {
            "cont3": _bv(r.get("cont3")),
            cond_key: cond_val,
        }

    return json.dumps(data, ensure_ascii=False)


def _find_related_open_signal_id(cur, variety_id: int, cycle_id: str | None) -> int | None:
    if not cycle_id:
        return None
    cur.execute(
        """
        SELECT id FROM trading_signals
        WHERE variety_id=%s AND cycle_id=%s AND signal_role='open'
        ORDER BY signal_date DESC, id DESC LIMIT 1
        """,
        (variety_id, cycle_id),
    )
    row = cur.fetchone()
    return int(row["id"]) if row else None


def save_signals(
    conn: pymysql.Connection,
    signal_date: date,
    variety_id: int,
    variety_name: str,
    signal_df: pd.DataFrame,
) -> int:
    mask = signal_df["trade_date"].dt.date == signal_date
    positions = np.where(mask.values)[0]
    if len(positions) == 0:
        return 0

    idx_pos = int(positions[-1])
    r = signal_df.iloc[idx_pos]

    signal_types = [
        ("A_OPEN_LONG", "A_OPEN_LONG"),
        ("A_OPEN_SHORT", "A_OPEN_SHORT"),
        ("A_CLOSE_LONG", "A_CLOSE_LONG"),
        ("A_CLOSE_SHORT", "A_CLOSE_SHORT"),
    ]
    main_score = float(r["main_score"]) if pd.notna(r.get("main_score")) else None

    inserted = 0
    with conn.cursor() as cur:
        # 先清除该品种该日期的全部旧信号，确保重跑时不留残留记录
        cur.execute(
            "DELETE FROM trading_signals WHERE signal_date=%s AND variety_id=%s",
            (signal_date, variety_id),
        )
        for col, stype in signal_types:
            if not bool(r.get(col, False)):
                continue
            score = main_score if stype in ("A_OPEN_LONG", "A_OPEN_SHORT") else None
            extra = _make_extra_json(signal_df, idx_pos, stype)
            signal_role = str(r.get("signal_role") or ("open" if stype in ("A_OPEN_LONG", "A_OPEN_SHORT") else "close"))
            direction = str(r.get("direction") or ("LONG" if stype.endswith("LONG") else "SHORT"))
            cycle_id = r.get("cycle_id")
            related_open_date = r.get("related_open_date") if signal_role == "close" else None
            related_open_signal_id = _find_related_open_signal_id(cur, variety_id, cycle_id) if signal_role == "close" else None
            state_before = str(r.get("theory_state_before") or "none")
            state_after = str(r.get("theory_state_after") or "none")
            cur.execute(
                """
                INSERT INTO trading_signals
                    (signal_date, variety_id, variety_name, signal_type, signal_role,
                     direction, cycle_id, related_open_signal_id, related_open_date,
                     theory_state_before, theory_state_after, main_score, extra_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    signal_date, variety_id, variety_name, stype, signal_role,
                    direction, cycle_id, related_open_signal_id, related_open_date,
                    state_before, state_after, score, extra,
                ),
            )
            inserted += 1
    conn.commit()
    return inserted


def run_signals_for_all(conn: pymysql.Connection, signal_date: date) -> dict[str, list[str]]:
    from .data_loader import load_variety_map, load_variety_data

    variety_df = load_variety_map(conn)
    if variety_df.empty:
        return {}

    results: dict[str, list[str]] = {}
    for _, vrow in variety_df.iterrows():
        vid = int(vrow["id"])
        vname = str(vrow["name"])
        df = load_variety_data(conn, vid)
        if df.empty or df["trade_date"].dt.date.max() < signal_date:
            continue
        try:
            sig_df = compute_signals(df, vid)
            save_signals(conn, signal_date, vid, vname, sig_df)
            mask = sig_df["trade_date"].dt.date == signal_date
            row = sig_df[mask]
            if not row.empty:
                r = row.iloc[-1]
                triggered = [
                    st for st in ("A_OPEN_LONG", "A_OPEN_SHORT", "A_CLOSE_LONG", "A_CLOSE_SHORT")
                    if bool(r.get(st, False))
                ]
                if triggered:
                    results[vname] = triggered
        except Exception as exc:
            logger.warning("品种 %s 信号计算失败: %s", vname, exc)

    return results
