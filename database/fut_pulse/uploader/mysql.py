"""
MySQL 上传模块

功能：
  1. 自动检测并创建 fut_variety / fut_strength 表（不存在时才创建）。
  2. 将品种列表同步到 fut_variety。
  3. 按 trade_dates 日期索引将 result 数据逐条写入 fut_strength。
     重复的 (variety_id, trade_date) 使用 INSERT IGNORE 自动跳过。

连接配置从项目根目录的 .env 文件读取：
  DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
"""

import logging
import os
import time
from datetime import datetime
from pathlib import Path

import pymysql
import pymysql.cursors
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

MAX_RETRIES = 3
RETRY_DELAY = 3  # 秒

# ── DDL ───────────────────────────────────────────────────────────────────────

DDL_VARIETY = """
CREATE TABLE IF NOT EXISTS fut_variety (
    id    INT          NOT NULL,
    name  VARCHAR(50)  NOT NULL,
    `key` VARCHAR(20)  NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_key (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

DDL_STRENGTH = """
CREATE TABLE IF NOT EXISTS fut_strength (
    id           BIGINT   NOT NULL AUTO_INCREMENT,
    variety_id   INT      NOT NULL,
    trade_date   DATE     NOT NULL,
    main_force   FLOAT    DEFAULT NULL,
    retail       FLOAT    DEFAULT NULL,
    collected_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_variety_date (variety_id, trade_date),
    KEY idx_variety_date (variety_id, trade_date),
    KEY idx_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


# ── 配置加载 ──────────────────────────────────────────────────────────────────

def load_db_config() -> dict:
    """从 .env 文件加载数据库连接配置。"""
    load_dotenv(ENV_PATH)
    return {
        "host":     os.getenv("DB_HOST", "127.0.0.1"),
        "port":     int(os.getenv("DB_PORT", "3306")),
        "user":     os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "futures"),
    }


# ── 连接（含重试） ────────────────────────────────────────────────────────────

def connect(db_cfg: dict | None = None) -> pymysql.connections.Connection:
    """
    建立 MySQL 连接，失败时自动重试最多 MAX_RETRIES 次。
    db_cfg 为 None 时自动从 .env 加载。
    """
    if db_cfg is None:
        db_cfg = load_db_config()

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            conn = pymysql.connect(
                host=db_cfg["host"],
                port=db_cfg["port"],
                user=db_cfg["user"],
                password=db_cfg["password"],
                database=db_cfg["database"],
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
                connect_timeout=10,
            )
            logger.info(
                "已连接 MySQL: %s:%s  数据库=%s",
                db_cfg["host"], db_cfg["port"], db_cfg["database"],
            )
            print(f"已连接到 MySQL：{db_cfg['host']}:{db_cfg['port']}  数据库={db_cfg['database']}")
            return conn
        except pymysql.Error as e:
            last_err = e
            logger.warning("MySQL 连接失败（第 %d/%d 次）：%s", attempt, MAX_RETRIES, e)
            if attempt < MAX_RETRIES:
                print(f"连接失败（第 {attempt}/{MAX_RETRIES} 次），{RETRY_DELAY}s 后重试... ({e})")
                time.sleep(RETRY_DELAY)

    raise ConnectionError(f"MySQL 连接失败，已重试 {MAX_RETRIES} 次，最后错误：{last_err}")


# ── 表结构 ────────────────────────────────────────────────────────────────────

def ensure_tables(conn: pymysql.connections.Connection):
    """检查并创建所需的表（不存在时才创建）。"""
    with conn.cursor() as cur:
        cur.execute(DDL_VARIETY)
        cur.execute(DDL_STRENGTH)
    conn.commit()
    logger.info("表结构就绪（fut_variety / fut_strength）")
    print("表结构已就绪（fut_variety / fut_strength）。")


# ── 品种同步 ──────────────────────────────────────────────────────────────────

def sync_varieties(conn: pymysql.connections.Connection, varieties: list):
    """将品种列表同步到 fut_variety，已存在的跳过。"""
    sql = "INSERT IGNORE INTO fut_variety (id, name, `key`) VALUES (%s, %s, %s)"
    rows = [(v["id"], v["name"], v["key"]) for v in varieties]
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()
    logger.info("品种同步完成，共 %d 个", len(rows))
    print(f"品种同步完成，共 {len(rows)} 个（已存在的自动跳过）。")


# ── 强度数据上传 ──────────────────────────────────────────────────────────────

def upload_strength(
    conn: pymysql.connections.Connection,
    result: list,
    trade_dates: list,
    collected_at: str | None = None,
):
    """
    将 result 数据按 trade_dates 索引逐条上传到 fut_strength。
    result 中 main_force / retail 可为标量（today 模式）或列表（history 模式）。
    重复的 (variety_id, trade_date) 使用 INSERT IGNORE 跳过。
    """
    if collected_at is None:
        collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sql = """
        INSERT IGNORE INTO fut_strength
            (variety_id, trade_date, main_force, retail, collected_at)
        VALUES (%s, %s, %s, %s, %s)
    """
    batch = []
    for item in result:
        variety_id = item["id"]
        main_raw   = item.get("main_force")
        retail_raw = item.get("retail")

        # 统一为列表形式
        main_list   = main_raw   if isinstance(main_raw, list)   else [main_raw]
        retail_list = retail_raw if isinstance(retail_raw, list) else [retail_raw]

        for day_idx, trade_date in enumerate(trade_dates):
            main_val   = main_list[day_idx]   if day_idx < len(main_list)   else None
            retail_val = retail_list[day_idx] if day_idx < len(retail_list) else None
            batch.append((variety_id, trade_date, main_val, retail_val, collected_at))

    inserted = skipped = 0
    with conn.cursor() as cur:
        for row in batch:
            affected = cur.execute(sql, row)
            if affected:
                inserted += 1
            else:
                skipped += 1
    conn.commit()

    logger.info(
        "强度数据上传完成：新增 %d 条，跳过 %d 条（合计 %d 条）",
        inserted, skipped, len(batch),
    )
    print(
        f"日度数据上传完成：新增 {inserted} 条，跳过重复 {skipped} 条。"
        f"（合计尝试 {len(batch)} 条）"
    )


# ── 高层接口（供 pipeline 直接调用） ─────────────────────────────────────────

def upload(result: list, trade_dates: list, varieties: list):
    """
    完整上传流程：连接 → 建表 → 同步品种 → 写入强度数据。
    供 pipeline.py 调用。
    """
    conn = connect()
    try:
        ensure_tables(conn)
        sync_varieties(conn, varieties)
        upload_strength(conn, result, trade_dates)
    finally:
        conn.close()
    print("\n全部完成！数据已上传至远端 MySQL。")
