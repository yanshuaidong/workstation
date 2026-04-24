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

    bg1 = out["main_force"].shift(6)
    bg2 = out["main_force"].shift(5)
    bg3 = out["main_force"].shift(4)
    bg4 = out["main_force"].shift(3)

    trigger_main_up = out["main_diff"].shift(1).gt(0) & out["main_diff"].gt(0)
    trigger_main_down = out["main_diff"].shift(1).lt(0) & out["main_diff"].lt(0)
    trigger_retail_down = out["retail_diff"].shift(1).lt(0) & out["retail_diff"].lt(0)
    trigger_retail_up = out["retail_diff"].shift(1).gt(0) & out["retail_diff"].gt(0)

    long_bg = bg1.lt(0) & bg2.lt(0) & bg3.lt(0) & bg4.lt(0) & (bg4 - bg1).lt(0)
    short_bg = bg1.gt(0) & bg2.gt(0) & bg3.gt(0) & bg4.gt(0) & (bg4 - bg1).gt(0)

    out["A_OPEN_LONG"] = cont7 & long_bg & trigger_main_up & trigger_retail_down
    out["A_OPEN_SHORT"] = cont7 & short_bg & trigger_main_down & trigger_retail_up

    out["m3"] = out["main_force"] - out["main_force"].shift(2)
    out["A_CLOSE_LONG"] = cont3 & out["m3"].lt(0)
    out["A_CLOSE_SHORT"] = cont3 & out["m3"].gt(0)

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


def _make_extra_json(row: pd.Series) -> str:
    data = {
        "main_force": float(row["main_force"]) if pd.notna(row.get("main_force")) else None,
        "retail": float(row["retail"]) if pd.notna(row.get("retail")) else None,
        "m3": float(row["m3"]) if pd.notna(row.get("m3")) else None,
    }
    return json.dumps(data, ensure_ascii=False)


def save_signals(
    conn: pymysql.Connection,
    signal_date: date,
    variety_id: int,
    variety_name: str,
    signal_df: pd.DataFrame,
) -> int:
    row = signal_df[signal_df["trade_date"].dt.date == signal_date]
    if row.empty:
        return 0

    r = row.iloc[-1]
    signal_types = [
        ("A_OPEN_LONG", "A_OPEN_LONG"),
        ("A_OPEN_SHORT", "A_OPEN_SHORT"),
        ("A_CLOSE_LONG", "A_CLOSE_LONG"),
        ("A_CLOSE_SHORT", "A_CLOSE_SHORT"),
    ]
    main_score = float(r["main_score"]) if pd.notna(r.get("main_score")) else None
    extra = _make_extra_json(r)

    inserted = 0
    with conn.cursor() as cur:
        for col, stype in signal_types:
            if not bool(r.get(col, False)):
                continue
            score = main_score if stype in ("A_OPEN_LONG", "A_OPEN_SHORT") else None
            cur.execute(
                """
                INSERT INTO trading_signals
                    (signal_date, variety_id, variety_name, signal_type, main_score, extra_json)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    variety_name=VALUES(variety_name),
                    main_score=VALUES(main_score),
                    extra_json=VALUES(extra_json)
                """,
                (signal_date, variety_id, variety_name, stype, score, extra),
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
            sig_df = compute_signals(df)
            save_signals(conn, signal_date, vid, vname, sig_df)
            row = sig_df[sig_df["trade_date"].dt.date == signal_date]
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
