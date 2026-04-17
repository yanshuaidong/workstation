"""assistant 模拟账户与持仓管理。"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import pymysql

from assistant_db import get_db_connection, parse_date, to_date_str
from assistant_settings import (
    DEFAULT_SIZE_PCT,
    INITIAL_CAPITAL,
    LEVERAGE,
    MAX_HOLD_DAYS,
    MAX_POSITIONS,
)


def _dict_cursor(conn):
    return conn.cursor(pymysql.cursors.DictCursor)


def build_market_map(market_df: pd.DataFrame) -> dict[int, pd.DataFrame]:
    """按品种构建行情索引。"""
    if market_df.empty:
        return {}
    market_map = {}
    for variety_id, group in market_df.groupby("variety_id"):
        prepared = group.copy().sort_values("trade_date").reset_index(drop=True)
        prepared["trade_day"] = prepared["trade_date"].dt.date
        market_map[int(variety_id)] = prepared
    return market_map


def get_market_row(market_map: dict[int, pd.DataFrame], variety_id: int, target_date) -> pd.Series | None:
    """获取指定品种在某交易日的行情行。"""
    group = market_map.get(int(variety_id))
    if group is None or group.empty:
        return None
    target_date = parse_date(target_date)
    matched = group[group["trade_day"] == target_date]
    if matched.empty:
        return None
    return matched.iloc[-1]


def get_previous_market_row(market_map: dict[int, pd.DataFrame], variety_id: int, target_date) -> pd.Series | None:
    """获取指定交易日前一条行情记录。"""
    group = market_map.get(int(variety_id))
    if group is None or group.empty:
        return None
    target_date = parse_date(target_date)
    matched = group[group["trade_day"] < target_date]
    if matched.empty:
        return None
    return matched.iloc[-1]


def get_trading_days_between(
    market_map: dict[int, pd.DataFrame], variety_id: int, start_date, end_date
) -> int:
    """统计持仓期间的交易日数（含首尾）。"""
    group = market_map.get(int(variety_id))
    if group is None or group.empty:
        return 0
    start_date = parse_date(start_date)
    end_date = parse_date(end_date)
    matched = group[(group["trade_day"] >= start_date) & (group["trade_day"] <= end_date)]
    return int(len(matched))


def calculate_position_pnl_pct(position: dict[str, Any], current_price: float) -> float:
    """计算仓位收益率（含杠杆，单位 %）。"""
    direction_sign = 1 if position["direction"] == "LONG" else -1
    raw_return = direction_sign * ((float(current_price) - float(position["open_price"])) / float(position["open_price"]))
    return raw_return * LEVERAGE * 100


def calculate_position_pnl_amount(position: dict[str, Any], current_price: float) -> float:
    """计算仓位盈亏金额。"""
    margin = INITIAL_CAPITAL * float(position["size_pct"])
    return margin * calculate_position_pnl_pct(position, current_price) / 100


def get_open_positions(conn, account_type: str) -> list[dict[str, Any]]:
    """读取当前未平仓持仓。"""
    cursor = _dict_cursor(conn)
    try:
        cursor.execute(
            """
            SELECT
                id, account_type, variety_id, variety_name, direction,
                open_date, open_price, close_date, close_price, size_pct,
                status, pnl_pct, strategy, created_at
            FROM assistant_positions
            WHERE account_type = %s AND status = 'open'
            ORDER BY open_date, id
            """,
            (account_type,),
        )
        rows = cursor.fetchall()
        for row in rows:
            row["open_date"] = parse_date(row["open_date"])
        return rows
    finally:
        cursor.close()


def get_latest_account_snapshot(conn, account_type: str, before_date=None) -> dict[str, Any] | None:
    """读取最近一条净值快照。"""
    cursor = _dict_cursor(conn)
    try:
        if before_date is None:
            cursor.execute(
                """
                SELECT record_date, equity, cash, position_val, daily_pnl
                FROM assistant_account_daily
                WHERE account_type = %s
                ORDER BY record_date DESC
                LIMIT 1
                """,
                (account_type,),
            )
        else:
            cursor.execute(
                """
                SELECT record_date, equity, cash, position_val, daily_pnl
                FROM assistant_account_daily
                WHERE account_type = %s AND record_date < %s
                ORDER BY record_date DESC
                LIMIT 1
                """,
                (account_type, to_date_str(before_date)),
            )
        row = cursor.fetchone()
        if row and row.get("record_date"):
            row["record_date"] = parse_date(row["record_date"])
        return row
    finally:
        cursor.close()


def open_position(
    conn,
    account_type: str,
    variety_id: int,
    variety_name: str,
    direction: str,
    open_date,
    open_price: float,
    size_pct: float = DEFAULT_SIZE_PCT,
    strategy: str | None = None,
) -> int:
    """写入一条新持仓。"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO assistant_positions
                (account_type, variety_id, variety_name, direction,
                 open_date, open_price, size_pct, status, strategy)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'open', %s)
            """,
            (
                account_type,
                int(variety_id),
                variety_name,
                direction,
                to_date_str(open_date),
                float(open_price),
                float(size_pct),
                strategy,
            ),
        )
        position_id = int(cursor.lastrowid)
        conn.commit()
        return position_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def close_position(
    conn,
    position_id: int,
    close_date,
    close_price: float,
    pnl_pct: float,
) -> None:
    """平掉一条已有持仓。"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE assistant_positions
            SET close_date = %s,
                close_price = %s,
                pnl_pct = %s,
                status = 'closed'
            WHERE id = %s
            """,
            (
                to_date_str(close_date),
                float(close_price),
                float(pnl_pct),
                int(position_id),
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def get_open_position_by_variety(conn, account_type: str, variety_id: int) -> dict[str, Any] | None:
    """按品种读取单条未平仓记录。"""
    cursor = _dict_cursor(conn)
    try:
        cursor.execute(
            """
            SELECT
                id, account_type, variety_id, variety_name, direction,
                open_date, open_price, close_date, close_price, size_pct,
                status, pnl_pct, strategy, created_at
            FROM assistant_positions
            WHERE account_type = %s
              AND variety_id = %s
              AND status = 'open'
            ORDER BY id DESC
            LIMIT 1
            """,
            (account_type, int(variety_id)),
        )
        row = cursor.fetchone()
        if row and row.get("open_date"):
            row["open_date"] = parse_date(row["open_date"])
        return row
    finally:
        cursor.close()


def determine_exit_reason(
    position: dict[str, Any],
    current_row: pd.Series | None,
    previous_row: pd.Series | None,
    market_map: dict[int, pd.DataFrame],
    signal_date,
) -> str | None:
    """按优先级判断是否应退出持仓。"""
    if current_row is None:
        return None

    signal_date = parse_date(signal_date)
    current_price = float(current_row["close_price"])
    current_force = float(current_row["main_force"])
    previous_force = float(previous_row["main_force"]) if previous_row is not None else None

    if previous_force is not None:
        if position["direction"] == "LONG" and current_force < previous_force:
            return "trend_take_profit"
        if position["direction"] == "SHORT" and current_force > previous_force:
            return "trend_take_profit"

    open_price = float(position["open_price"])
    if position["direction"] == "LONG" and current_price <= open_price * 0.95:
        return "hard_stop_loss"
    if position["direction"] == "SHORT" and current_price >= open_price * 1.05:
        return "hard_stop_loss"

    holding_days = get_trading_days_between(
        market_map, int(position["variety_id"]), position["open_date"], signal_date
    )
    if holding_days >= MAX_HOLD_DAYS:
        return "max_holding_days"

    return None


def upsert_account_snapshot(
    conn,
    account_type: str,
    record_date,
    market_df: pd.DataFrame,
) -> dict[str, Any]:
    """根据当前持仓重算当日净值。"""
    record_date = parse_date(record_date)
    market_map = build_market_map(market_df)
    open_positions = get_open_positions(conn, account_type)

    cursor = _dict_cursor(conn)
    try:
        cursor.execute(
            """
            SELECT size_pct, pnl_pct
            FROM assistant_positions
            WHERE account_type = %s
              AND status = 'closed'
              AND close_date <= %s
            """,
            (account_type, to_date_str(record_date)),
        )
        closed_positions = cursor.fetchall()
    finally:
        cursor.close()

    realized_pnl = 0.0
    for row in closed_positions:
        realized_pnl += INITIAL_CAPITAL * float(row["size_pct"]) * float(row["pnl_pct"] or 0.0) / 100

    unrealized_pnl = 0.0
    position_value = 0.0
    priced_open_positions = 0
    for position in open_positions:
        market_row = get_market_row(market_map, int(position["variety_id"]), record_date)
        if market_row is None:
            continue
        current_price = float(market_row["close_price"])
        pnl_amount = calculate_position_pnl_amount(position, current_price)
        margin = INITIAL_CAPITAL * float(position["size_pct"])
        unrealized_pnl += pnl_amount
        position_value += margin + pnl_amount
        priced_open_positions += 1

    equity = INITIAL_CAPITAL + realized_pnl + unrealized_pnl
    cash = equity - position_value
    previous_snapshot = get_latest_account_snapshot(conn, account_type, before_date=record_date)
    previous_equity = float(previous_snapshot["equity"]) if previous_snapshot else INITIAL_CAPITAL
    daily_pnl = equity - previous_equity

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO assistant_account_daily
                (record_date, account_type, equity, cash, position_val, daily_pnl)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                equity = VALUES(equity),
                cash = VALUES(cash),
                position_val = VALUES(position_val),
                daily_pnl = VALUES(daily_pnl)
            """,
            (
                to_date_str(record_date),
                account_type,
                round(equity, 4),
                round(cash, 4),
                round(position_value, 4),
                round(daily_pnl, 4),
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()

    return {
        "record_date": record_date,
        "account_type": account_type,
        "equity": round(equity, 4),
        "cash": round(cash, 4),
        "position_val": round(position_value, 4),
        "daily_pnl": round(daily_pnl, 4),
        "priced_open_positions": priced_open_positions,
    }


def available_slots(conn, account_type: str) -> int:
    """返回剩余可开仓位。"""
    return max(0, MAX_POSITIONS - len(get_open_positions(conn, account_type)))

