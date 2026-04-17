"""MySQL 连接与基础表初始化。"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import pymysql
import pymysql.cursors
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

MAX_RETRIES = 3
RETRY_DELAY = 3  # 秒

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

DDL_DAILY_CLOSE = """
CREATE TABLE IF NOT EXISTS fut_daily_close (
    variety_id   INT      NOT NULL,
    trade_date   DATE     NOT NULL,
    close_price  FLOAT    NOT NULL,
    collected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (variety_id, trade_date),
    KEY idx_trade_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

TABLE_DDLS = {
    "fut_variety": DDL_VARIETY,
    "fut_strength": DDL_STRENGTH,
    "fut_daily_close": DDL_DAILY_CLOSE,
}


def load_db_config() -> dict:
    """从 .env 文件加载数据库连接配置。"""
    load_dotenv(ENV_PATH)
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "futures"),
    }


def connect(db_cfg: dict | None = None) -> pymysql.connections.Connection:
    """建立 MySQL 连接，失败时自动重试。"""
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
        except pymysql.Error as exc:
            last_err = exc
            logger.warning("MySQL 连接失败（第 %d/%d 次）：%s", attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                print(f"连接失败（第 {attempt}/{MAX_RETRIES} 次），{RETRY_DELAY}s 后重试... ({exc})")
                time.sleep(RETRY_DELAY)

    raise ConnectionError(f"MySQL 连接失败，已重试 {MAX_RETRIES} 次，最后错误：{last_err}")


def _extract_table_name(row) -> str | None:
    if isinstance(row, dict):
        for value in row.values():
            if value:
                return str(value)
        return None
    if isinstance(row, (list, tuple)):
        return str(row[0]) if row else None
    return str(row) if row else None


def list_existing_tables(conn: pymysql.connections.Connection) -> set[str]:
    """查询当前数据库已有的表名。"""
    with conn.cursor() as cur:
        cur.execute("SHOW TABLES")
        rows = cur.fetchall()
    tables = {name for name in (_extract_table_name(row) for row in rows) if name}
    logger.debug("当前数据库已有表: %s", sorted(tables))
    return tables


def ensure_required_tables(conn: pymysql.connections.Connection) -> dict[str, list[str]]:
    """检查必备表，缺失则创建，已存在则跳过。"""
    existing_tables = list_existing_tables(conn)
    created_tables: list[str] = []
    skipped_tables: list[str] = []

    with conn.cursor() as cur:
        for table_name, ddl in TABLE_DDLS.items():
            if table_name in existing_tables:
                skipped_tables.append(table_name)
                logger.info("表已存在，跳过创建: %s", table_name)
                continue
            cur.execute(ddl)
            created_tables.append(table_name)
            logger.info("表不存在，已创建: %s", table_name)
    conn.commit()

    summary = {
        "created_tables": created_tables,
        "skipped_tables": skipped_tables,
        "all_required_tables": list(TABLE_DDLS.keys()),
    }
    logger.info(
        "表结构检查完成：创建 %d 张，跳过 %d 张",
        len(created_tables), len(skipped_tables),
    )
    print(
        "表结构检查完成："
        f"已创建 {created_tables or '无'}；"
        f"已存在 {skipped_tables or '无'}。"
    )
    return summary
