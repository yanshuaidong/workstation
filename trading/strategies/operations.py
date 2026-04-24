"""
操作建议生成模块。
输入：当日全品种信号（trading_signals）+ trading_pool + 当前持仓
过滤逻辑严格对照 simulate_portfolio 中的组合约束步骤。
"""
from __future__ import annotations

import json
import logging
from datetime import date

import numpy as np
import pymysql

from .settings import MAX_SLOTS, SECTOR_BY_VARIETY

logger = logging.getLogger(__name__)


def _get_open_positions(conn: pymysql.Connection) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT variety_id, variety_name, direction, sector "
            "FROM trading_positions WHERE status='open'"
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
            "SELECT variety_id, variety_name, signal_type, main_score "
            "FROM trading_signals WHERE signal_date=%s "
            "AND signal_type IN ('A_OPEN_LONG','A_OPEN_SHORT')",
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
    open_positions = _get_open_positions(conn)
    closed_today = _get_closed_today(conn, signal_date)
    open_signals = _get_today_signals(conn, signal_date)

    held_variety_ids = {int(p["variety_id"]) for p in open_positions}
    start_sectors = {p["sector"] for p in open_positions}
    entry_capacity = MAX_SLOTS - len(held_variety_ids)

    candidates: list[dict] = []
    for sig in open_signals:
        vid = int(sig["variety_id"])
        if vid not in pool:
            continue
        if vid in held_variety_ids or vid in closed_today:
            continue
        score = float(sig["main_score"]) if sig["main_score"] is not None else np.nan
        candidates.append({
            "variety_id": vid,
            "variety_name": sig["variety_name"],
            "sector": pool[vid]["sector"],
            "signal_type": sig["signal_type"],
            "main_score": score,
        })

    if entry_capacity <= 0:
        _save_all_rejected(conn, signal_date, candidates, "capacity_full")
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
            bool(np.isnan(x["main_score"])),
            -(x["main_score"] if not np.isnan(x["main_score"]) else 0.0),
            x["variety_name"],
        )
    )

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
                    (signal_date, variety_id, variety_name, sector, signal_type,
                     main_score, is_selected, reject_reason, extra_json)
                VALUES (%s,%s,%s,%s,%s,%s,1,NULL,%s)
                ON DUPLICATE KEY UPDATE
                    variety_name=VALUES(variety_name), sector=VALUES(sector),
                    main_score=VALUES(main_score), is_selected=1, reject_reason=NULL,
                    extra_json=VALUES(extra_json)
                """,
                (
                    signal_date,
                    c["variety_id"],
                    c["variety_name"],
                    c["sector"],
                    c["signal_type"],
                    None if np.isnan(c["main_score"]) else c["main_score"],
                    json.dumps({"rank_note": "selected"}, ensure_ascii=False),
                ),
            )
        for c in sector_rejected + remaining_rejected:
            cur.execute(
                """
                INSERT INTO trading_operations
                    (signal_date, variety_id, variety_name, sector, signal_type,
                     main_score, is_selected, reject_reason, extra_json)
                VALUES (%s,%s,%s,%s,%s,%s,0,%s,%s)
                ON DUPLICATE KEY UPDATE
                    variety_name=VALUES(variety_name), sector=VALUES(sector),
                    main_score=VALUES(main_score), is_selected=0,
                    reject_reason=VALUES(reject_reason), extra_json=VALUES(extra_json)
                """,
                (
                    signal_date,
                    c["variety_id"],
                    c["variety_name"],
                    c["sector"],
                    c["signal_type"],
                    None if np.isnan(c["main_score"]) else c["main_score"],
                    c["reject_reason"],
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
                    (signal_date, variety_id, variety_name, sector, signal_type,
                     main_score, is_selected, reject_reason, extra_json)
                VALUES (%s,%s,%s,%s,%s,%s,0,%s,%s)
                ON DUPLICATE KEY UPDATE
                    variety_name=VALUES(variety_name), sector=VALUES(sector),
                    main_score=VALUES(main_score), is_selected=0,
                    reject_reason=VALUES(reject_reason), extra_json=VALUES(extra_json)
                """,
                (
                    signal_date,
                    c["variety_id"],
                    c["variety_name"],
                    c["sector"],
                    c["signal_type"],
                    None if np.isnan(c["main_score"]) else c["main_score"],
                    reason,
                    json.dumps({"rank_note": reason}, ensure_ascii=False),
                ),
            )
    conn.commit()
