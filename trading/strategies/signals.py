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


def compute_signals(df: pd.DataFrame) -> pd.DataFrame:
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

    # 状态机过滤：平仓信号仅在对应开仓信号激活后才生效
    in_long = False
    in_short = False
    close_long_filtered: list[bool] = []
    close_short_filtered: list[bool] = []

    for i in range(len(out)):
        open_long  = bool(out["A_OPEN_LONG"].iloc[i])
        open_short = bool(out["A_OPEN_SHORT"].iloc[i])
        close_long = bool(out["A_CLOSE_LONG"].iloc[i])
        close_short = bool(out["A_CLOSE_SHORT"].iloc[i])

        if open_long:
            in_long, in_short = True, False
        elif open_short:
            in_long, in_short = False, True

        close_long_filtered.append(close_long and in_long)
        close_short_filtered.append(close_short and in_short)

        if close_long and in_long:
            in_long = False
        if close_short and in_short:
            in_short = False

    out["A_CLOSE_LONG"] = close_long_filtered
    out["A_CLOSE_SHORT"] = close_short_filtered

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


def _get_db_state(conn: pymysql.Connection, variety_id: int, before_date: date) -> tuple[bool, bool]:
    """从 trading_signal_state 快照表读取该品种在 before_date 之前的最新持仓状态，O(log n)。"""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT state FROM trading_signal_state "
            "WHERE variety_id=%s AND state_date<%s "
            "ORDER BY state_date DESC LIMIT 1",
            (variety_id, before_date),
        )
        row = cur.fetchone()
    if row is None:
        return False, False
    state = row["state"] if isinstance(row, dict) else row[0]
    return state == "long", state == "short"


def _update_signal_state(
    cur,
    signal_date: date,
    variety_id: int,
    db_in_long: bool,
    db_in_short: bool,
    saved_types: set[str],
) -> None:
    """根据本次写入的信号类型更新状态快照，与信号写入在同一事务内。"""
    in_long = db_in_long
    in_short = db_in_short

    if "A_OPEN_LONG" in saved_types:
        in_long, in_short = True, False
    elif "A_OPEN_SHORT" in saved_types:
        in_long, in_short = False, True

    if "A_CLOSE_LONG" in saved_types:
        in_long = False
    if "A_CLOSE_SHORT" in saved_types:
        in_short = False

    new_state = "long" if in_long else ("short" if in_short else "none")
    cur.execute(
        """
        INSERT INTO trading_signal_state (variety_id, state_date, state)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE state=VALUES(state)
        """,
        (variety_id, signal_date, new_state),
    )


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

    # 查数据库确认该品种的实际持仓状态，防止保存孤立平仓信号
    db_in_long, db_in_short = _get_db_state(conn, variety_id, signal_date)

    saved_types: set[str] = set()
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
            # 平仓信号必须有数据库中对应的未平开仓记录才写入
            if stype == "A_CLOSE_LONG" and not db_in_long:
                logger.debug("品种 %s %s 平多信号被过滤：数据库无对应开多记录", variety_id, signal_date)
                continue
            if stype == "A_CLOSE_SHORT" and not db_in_short:
                logger.debug("品种 %s %s 平空信号被过滤：数据库无对应开空记录", variety_id, signal_date)
                continue
            score = main_score if stype in ("A_OPEN_LONG", "A_OPEN_SHORT") else None
            extra = _make_extra_json(signal_df, idx_pos, stype)
            cur.execute(
                """
                INSERT INTO trading_signals
                    (signal_date, variety_id, variety_name, signal_type, main_score, extra_json)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (signal_date, variety_id, variety_name, stype, score, extra),
            )
            saved_types.add(stype)
            inserted += 1
        # 与信号写入同一事务更新状态快照
        _update_signal_state(cur, signal_date, variety_id, db_in_long, db_in_short, saved_types)
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
            sig_df = compute_signals(df)
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
