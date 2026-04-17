"""机械账户执行器。"""

from __future__ import annotations

from typing import Any

import pandas as pd
import pymysql

from assistant_db import parse_date, parse_json, to_date_str
from assistant_settings import DEFAULT_SIZE_PCT, MECHANICAL_ACCOUNT, STRATEGY_PRIORITY
from paper_account import (
    available_slots,
    build_market_map,
    calculate_position_pnl_pct,
    close_position,
    determine_exit_reason,
    get_latest_account_snapshot,
    get_market_row,
    get_open_positions,
    get_previous_market_row,
    open_position,
    upsert_account_snapshot,
)


def _load_operations_for_date(conn, signal_date) -> list[dict[str, Any]]:
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(
            """
            SELECT id, signal_date, variety_id, variety_name, strategy,
                   direction, extra_json, account_type, executed
            FROM assistant_operations
            WHERE signal_date = %s
              AND account_type = %s
            ORDER BY created_at, id
            """,
            (to_date_str(signal_date), MECHANICAL_ACCOUNT),
        )
        rows = cursor.fetchall()
        for row in rows:
            row["signal_date"] = parse_date(row["signal_date"])
            row["extra_json"] = parse_json(row["extra_json"])
            row["priority"] = STRATEGY_PRIORITY.get(row["strategy"], 99)
            row["composite_score"] = float(row["extra_json"].get("composite_score", 0.0))
        return rows
    finally:
        cursor.close()


def _mark_operation_executed(conn, operation_id: int) -> None:
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE assistant_operations SET executed = 1 WHERE id = %s",
            (int(operation_id),),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def process_mechanical_account_for_date(
    conn,
    signal_date,
    market_df: pd.DataFrame,
    force: bool = False,
) -> dict[str, Any]:
    """按单个交易日执行机械账户。"""
    signal_date = parse_date(signal_date)
    existing_snapshot = get_latest_account_snapshot(conn, MECHANICAL_ACCOUNT)
    if (
        not force
        and existing_snapshot
        and existing_snapshot["record_date"] == signal_date
    ):
        return {
            "signal_date": signal_date,
            "skipped": True,
            "reason": "snapshot_exists",
        }

    market_map = build_market_map(market_df)
    operations = _load_operations_for_date(conn, signal_date)
    open_positions_before = get_open_positions(conn, MECHANICAL_ACCOUNT)

    closed_positions = []
    for position in open_positions_before:
        current_row = get_market_row(market_map, int(position["variety_id"]), signal_date)
        previous_row = get_previous_market_row(market_map, int(position["variety_id"]), signal_date)
        reason = determine_exit_reason(position, current_row, previous_row, market_map, signal_date)
        if reason is None or current_row is None:
            continue
        pnl_pct = calculate_position_pnl_pct(position, float(current_row["close_price"]))
        close_position(
            conn,
            int(position["id"]),
            signal_date,
            float(current_row["close_price"]),
            pnl_pct,
        )
        closed_positions.append(
            {
                "position_id": int(position["id"]),
                "variety_id": int(position["variety_id"]),
                "reason": reason,
                "pnl_pct": round(pnl_pct, 4),
            }
        )

    open_positions_after_close = get_open_positions(conn, MECHANICAL_ACCOUNT)
    open_variety_ids = {int(row["variety_id"]) for row in open_positions_after_close}
    closed_today_variety_ids = {row["variety_id"] for row in closed_positions}
    slots = available_slots(conn, MECHANICAL_ACCOUNT)

    opened_positions = []
    ranked_operations = sorted(
        operations,
        key=lambda row: (-row["composite_score"], row["priority"], int(row["variety_id"])),
    )
    for operation in ranked_operations:
        if slots <= 0:
            break
        variety_id = int(operation["variety_id"])
        if variety_id in open_variety_ids or variety_id in closed_today_variety_ids:
            continue
        current_row = get_market_row(market_map, variety_id, signal_date)
        if current_row is None:
            continue
        position_id = open_position(
            conn,
            account_type=MECHANICAL_ACCOUNT,
            variety_id=variety_id,
            variety_name=str(operation["variety_name"]),
            direction=str(operation["direction"]),
            open_date=signal_date,
            open_price=float(current_row["close_price"]),
            size_pct=DEFAULT_SIZE_PCT,
            strategy=str(operation["strategy"]),
        )
        _mark_operation_executed(conn, int(operation["id"]))
        opened_positions.append(
            {
                "position_id": position_id,
                "operation_id": int(operation["id"]),
                "variety_id": variety_id,
                "strategy": operation["strategy"],
            }
        )
        open_variety_ids.add(variety_id)
        slots -= 1

    snapshot = upsert_account_snapshot(conn, MECHANICAL_ACCOUNT, signal_date, market_df)
    return {
        "signal_date": signal_date,
        "skipped": False,
        "closed_positions": closed_positions,
        "opened_positions": opened_positions,
        "snapshot": snapshot,
    }

