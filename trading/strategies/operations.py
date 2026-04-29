"""
操作建议生成模块。
输入：当日全品种信号（trading_signals）+ trading_pool + 当前持仓
过滤逻辑严格对照 simulate_portfolio 中的组合约束步骤。
"""
from __future__ import annotations

import json
import logging
from datetime import date

import pymysql

from .settings import MAX_SLOTS

logger = logging.getLogger(__name__)


def _get_open_positions(conn: pymysql.Connection, signal_date: date) -> list[dict]:
    # 只取 signal_date 之前开仓的持仓，当天新开的不计入已有槽位
    with conn.cursor() as cur:
        cur.execute(
            "SELECT variety_id, variety_name, direction, sector "
            "FROM trading_positions WHERE status='open' AND open_date < %s",
            (signal_date,),
        )
        return list(cur.fetchall())


def _get_pool_varieties(conn: pymysql.Connection) -> dict[int, dict]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT variety_id, variety_name, sector FROM trading_pool WHERE is_active=1"
        )
        rows = cur.fetchall()
    return {int(r["variety_id"]): r for r in rows}


def _get_today_signals(conn: pymysql.Connection, signal_date: date) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, variety_id, variety_name, signal_type, direction, cycle_id, main_score "
            "FROM trading_signals WHERE signal_date=%s "
            "AND signal_role='open'",
            (signal_date,),
        )
        return list(cur.fetchall())


def _get_closed_today(conn: pymysql.Connection, signal_date: date) -> set[int]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT variety_id FROM trading_positions WHERE close_date=%s AND status='closed'",
            (signal_date,),
        )
        return {int(r["variety_id"]) for r in cur.fetchall()}


def generate_operations(conn: pymysql.Connection, signal_date: date) -> None:
    pool = _get_pool_varieties(conn)
    open_positions = _get_open_positions(conn, signal_date)
    closed_today = _get_closed_today(conn, signal_date)
    open_signals = _get_today_signals(conn, signal_date)

    # 先清除当日所有记录，确保重跑结果可预期（池子调整、重新计算均干净覆盖）
    with conn.cursor() as cur:
        cur.execute("DELETE FROM trading_operations WHERE signal_date=%s", (signal_date,))
    conn.commit()

    held_variety_ids = {int(p["variety_id"]) for p in open_positions}
    start_sectors = {p["sector"] for p in open_positions}
    entry_capacity = MAX_SLOTS - len(held_variety_ids)

    candidates: list[dict] = []
    rejected: list[dict] = []
    for sig in open_signals:
        vid = int(sig["variety_id"])
        if vid not in pool:
            continue
        score = float(sig["main_score"]) if sig["main_score"] is not None else float("nan")
        candidate = {
            "variety_id": vid,
            "variety_name": sig["variety_name"],
            "sector": pool[vid]["sector"],
            "signal_type": sig["signal_type"],
            "operation_type": "OPEN",
            "direction": sig["direction"],
            "signal_cycle_id": sig["cycle_id"],
            "main_score": score,
            "signal_id": sig["id"],
            "selection_rank": None,
        }
        if vid in held_variety_ids:
            rejected.append({**candidate, "reject_reason": "already_holding"})
            continue
        if vid in closed_today:
            rejected.append({**candidate, "reject_reason": "closed_today"})
            continue
        candidates.append(candidate)

    if entry_capacity <= 0:
        _save_all_rejected(conn, signal_date, rejected + candidates, "capacity_full")
        return

    sector_filtered: list[dict] = []
    sector_rejected: list[dict] = []
    for c in candidates:
        if c["sector"] in start_sectors:
            sector_rejected.append({**c, "reject_reason": "sector_conflict"})
        else:
            sector_filtered.append(c)

    sector_filtered.sort(
        key=lambda x: (
            x["main_score"] != x["main_score"],
            -(x["main_score"] if x["main_score"] == x["main_score"] else 0.0),
            x["variety_name"],
        )
    )
    for rank, c in enumerate(sector_filtered, start=1):
        c["selection_rank"] = rank

    selected: list[dict] = []
    used_sectors: set[str] = set(start_sectors)
    remaining_rejected: list[dict] = []
    for c in sector_filtered:
        if c["sector"] in used_sectors:
            remaining_rejected.append({**c, "reject_reason": "sector_conflict"})
            continue
        if len(selected) >= entry_capacity:
            remaining_rejected.append({**c, "reject_reason": "capacity_full"})
            continue
        selected.append(c)
        used_sectors.add(c["sector"])

    with conn.cursor() as cur:
        for c in selected:
            cur.execute(
                """
                INSERT INTO trading_operations
                    (signal_id, signal_date, variety_id, variety_name, sector, signal_type,
                     operation_type, direction, signal_cycle_id, main_score, is_selected,
                     reject_reason, selection_rank, extra_json)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,NULL,%s,%s)
                """,
                (
                    c["signal_id"],
                    signal_date,
                    c["variety_id"],
                    c["variety_name"],
                    c["sector"],
                    c["signal_type"],
                    c["operation_type"],
                    c["direction"],
                    c["signal_cycle_id"],
                    None if c["main_score"] != c["main_score"] else c["main_score"],
                    c["selection_rank"],
                    json.dumps({"rank_note": "selected", "selection_rank": c["selection_rank"]}, ensure_ascii=False),
                ),
            )
        for c in rejected + sector_rejected + remaining_rejected:
            cur.execute(
                """
                INSERT INTO trading_operations
                    (signal_id, signal_date, variety_id, variety_name, sector, signal_type,
                     operation_type, direction, signal_cycle_id, main_score, is_selected,
                     reject_reason, selection_rank, extra_json)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,%s,%s,%s)
                """,
                (
                    c["signal_id"],
                    signal_date,
                    c["variety_id"],
                    c["variety_name"],
                    c["sector"],
                    c["signal_type"],
                    c["operation_type"],
                    c["direction"],
                    c["signal_cycle_id"],
                    None if c["main_score"] != c["main_score"] else c["main_score"],
                    c["reject_reason"],
                    c["selection_rank"],
                    json.dumps({"rank_note": c["reject_reason"]}, ensure_ascii=False),
                ),
            )
    conn.commit()


def _save_all_rejected(
    conn: pymysql.Connection,
    signal_date: date,
    candidates: list[dict],
    reason: str,
) -> None:
    with conn.cursor() as cur:
        for c in candidates:
            cur.execute(
                """
                INSERT INTO trading_operations
                    (signal_id, signal_date, variety_id, variety_name, sector, signal_type,
                     operation_type, direction, signal_cycle_id, main_score, is_selected,
                     reject_reason, selection_rank, extra_json)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,%s,%s,%s)
                """,
                (
                    c["signal_id"],
                    signal_date,
                    c["variety_id"],
                    c["variety_name"],
                    c["sector"],
                    c["signal_type"],
                    c["operation_type"],
                    c["direction"],
                    c["signal_cycle_id"],
                    None if c["main_score"] != c["main_score"] else c["main_score"],
                    c.get("reject_reason", reason),
                    c.get("selection_rank"),
                    json.dumps({"rank_note": c.get("reject_reason", reason)}, ensure_ascii=False),
                ),
            )
    conn.commit()
