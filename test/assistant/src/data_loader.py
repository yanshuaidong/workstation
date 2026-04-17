"""从 MySQL 读取 assistant 所需的基础行情数据。"""

from __future__ import annotations

from datetime import timedelta
from typing import Iterable

import pandas as pd

from assistant_db import get_db_connection, parse_date, to_date_str


def _normalize_variety_ids(variety_ids: Iterable[int] | None) -> list[int]:
    if not variety_ids:
        return []
    return sorted({int(item) for item in variety_ids})


def load_market_data(
    start_date=None,
    end_date=None,
    lookback_days: int = 90,
    variety_ids: Iterable[int] | None = None,
    conn=None,
) -> pd.DataFrame:
    """
    读取主力/散户/收盘价三类数据。

    为了支持滚动分位和持仓退出逻辑，默认会自动向前回看一段时间。
    """
    if end_date is None:
        raise ValueError("load_market_data 需要 end_date")

    end_date = parse_date(end_date)
    if start_date is None:
        start_date = end_date
    start_date = parse_date(start_date)
    query_start = start_date - timedelta(days=lookback_days)

    normalized_ids = _normalize_variety_ids(variety_ids)
    should_close = conn is None
    if conn is None:
        conn = get_db_connection()

    params = [to_date_str(query_start), to_date_str(end_date)]
    where_clauses = [
        "s.trade_date >= %s",
        "s.trade_date <= %s",
        "s.main_force IS NOT NULL",
        "s.retail IS NOT NULL",
        "c.close_price IS NOT NULL",
    ]

    if normalized_ids:
        placeholders = ", ".join(["%s"] * len(normalized_ids))
        where_clauses.append(f"s.variety_id IN ({placeholders})")
        params.extend(normalized_ids)

    sql = f"""
        SELECT
            s.variety_id,
            COALESCE(v.name, CAST(s.variety_id AS CHAR)) AS variety_name,
            s.trade_date,
            s.main_force,
            s.retail,
            c.close_price
        FROM fut_strength s
        INNER JOIN fut_daily_close c
            ON s.variety_id = c.variety_id
           AND s.trade_date = c.trade_date
        LEFT JOIN fut_variety v
            ON s.variety_id = v.id
        WHERE {" AND ".join(where_clauses)}
        ORDER BY s.variety_id, s.trade_date
    """

    try:
        df = pd.read_sql(sql, conn, params=params)
    finally:
        if should_close:
            conn.close()

    if df.empty:
        return df

    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df["variety_id"] = df["variety_id"].astype(int)
    df["variety_name"] = df["variety_name"].astype(str)
    for col in ("main_force", "retail", "close_price"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["main_force", "retail", "close_price"])
    df = df.sort_values(["variety_id", "trade_date"]).reset_index(drop=True)
    return df


def load_recent_market_context(
    variety_id: int,
    end_date=None,
    days: int = 10,
    conn=None,
) -> pd.DataFrame:
    """加载单品种最近若干交易日的上下文数据。"""
    if end_date is None:
        raise ValueError("load_recent_market_context 需要 end_date")

    df = load_market_data(
        start_date=parse_date(end_date) - timedelta(days=max(days * 3, 30)),
        end_date=end_date,
        lookback_days=0,
        variety_ids=[variety_id],
        conn=conn,
    )
    if df.empty:
        return df
    return df.sort_values("trade_date").tail(days).reset_index(drop=True)

