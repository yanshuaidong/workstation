"""MySQL 上传模块。"""

from __future__ import annotations

import logging
from datetime import datetime

import pymysql

from database.init_tables import connect, ensure_required_tables

logger = logging.getLogger(__name__)


def sync_varieties(conn: pymysql.connections.Connection, varieties: list):
    """将品种列表同步到 fut_variety，已存在的跳过。"""
    sql = "INSERT IGNORE INTO fut_variety (id, name, `key`) VALUES (%s, %s, %s)"
    rows = [(v["id"], v["name"], v["key"]) for v in varieties]
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()
    logger.info("品种同步完成，共 %d 个", len(rows))
    print(f"品种同步完成，共 {len(rows)} 个（已存在的自动跳过）。")


def upload_strength(
    conn: pymysql.connections.Connection,
    result: list,
    trade_dates: list,
    collected_at: str | None = None,
):
    """
    将 result 数据按 trade_dates 索引逐条上传到 fut_strength。
    result 中 main_force / retail 可为标量（today 模式）或列表（history 模式）。
    重复的 (variety_id, trade_date) 使用 ON DUPLICATE KEY UPDATE 更新。
    """
    if collected_at is None:
        collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sql = """
        INSERT INTO fut_strength
            (variety_id, trade_date, main_force, retail, collected_at)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            main_force = VALUES(main_force),
            retail = VALUES(retail),
            collected_at = VALUES(collected_at)
    """
    batch = []
    for item in result:
        variety_id = item["id"]
        main_raw = item.get("main_force")
        retail_raw = item.get("retail")

        main_list = main_raw if isinstance(main_raw, list) else [main_raw]
        retail_list = retail_raw if isinstance(retail_raw, list) else [retail_raw]

        for day_idx, trade_date in enumerate(trade_dates):
            main_val = main_list[day_idx] if day_idx < len(main_list) else None
            retail_val = retail_list[day_idx] if day_idx < len(retail_list) else None
            batch.append((variety_id, trade_date, main_val, retail_val, collected_at))

    inserted = updated = unchanged = 0
    with conn.cursor() as cur:
        for row in batch:
            affected = cur.execute(sql, row)
            if affected == 1:
                inserted += 1
            elif affected == 2:
                updated += 1
            else:
                unchanged += 1
    conn.commit()

    logger.info(
        "强度数据上传完成：新增 %d 条，更新 %d 条，未变化 %d 条（合计 %d 条）",
        inserted, updated, unchanged, len(batch),
    )
    print(
        f"日度数据上传完成：新增 {inserted} 条，更新重复 {updated} 条，未变化 {unchanged} 条。"
        f"（合计尝试 {len(batch)} 条）"
    )


def upload(result: list, trade_dates: list, varieties: list):
    """完整上传流程：连接 → 建表 → 同步品种 → 写入强度数据。"""
    conn = connect()
    try:
        ensure_required_tables(conn)
        sync_varieties(conn, varieties)
        upload_strength(conn, result, trade_dates)
    finally:
        conn.close()
    print("\n全部完成！数据已上传至远端 MySQL。")
