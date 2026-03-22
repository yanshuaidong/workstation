#!/usr/bin/env python3
"""
MySQL 历史数据补录工具

通过 AkShare 拉取指定日期的期货主连数据，写入 MySQL。
适用场景：定时任务漏跑，需要手动补录某一天的数据。

使用方法:
    # 补录 2026-03-05 的数据
    python backfill_mysql.py --date 2026-03-05

    # 预览模式（只打印，不写库）
    python backfill_mysql.py --date 2026-03-05 --dry-run

    # 只补录指定品种
    python backfill_mysql.py --date 2026-03-05 --symbol aum,cum,rbm
"""

import os
import sys
import json
import argparse
import logging
import time
import random
from datetime import datetime

import akshare as ak
import pandas as pd
import pymysql

# ─────────────────────────── 路径 ────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAPPING_PATH = os.path.join(SCRIPT_DIR, "futures_mapping.json")

# ─────────────────────────── MySQL 配置 ──────────────────────
DB_CONFIG = {
    "host": "rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com",
    "port": 3306,
    "user": "ysd",
    "password": "Yan1234567",
    "database": "futures",
    "charset": "utf8mb4",
}

# ─────────────────────────── 日志 ────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


# ─────────────────────────── 工具函数 ────────────────────────

def load_mapping():
    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_conn():
    return pymysql.connect(**DB_CONFIG)


def ensure_table(conn, symbol: str):
    """建表（若不存在）"""
    table = f"hist_{symbol.lower()}"
    sql = f"""
        CREATE TABLE IF NOT EXISTS {table} (
            trade_date    DATE           NOT NULL PRIMARY KEY COMMENT '交易日期',
            open_price    DECIMAL(10,2)  NOT NULL DEFAULT 0  COMMENT '开盘价',
            high_price    DECIMAL(10,2)  NOT NULL DEFAULT 0  COMMENT '最高价',
            low_price     DECIMAL(10,2)  NOT NULL DEFAULT 0  COMMENT '最低价',
            close_price   DECIMAL(10,2)  NOT NULL DEFAULT 0  COMMENT '收盘价',
            volume        BIGINT         NOT NULL DEFAULT 0  COMMENT '成交量',
            open_interest BIGINT         NOT NULL DEFAULT 0  COMMENT '持仓量',
            turnover      DECIMAL(20,2)  NOT NULL DEFAULT 0  COMMENT '成交额',
            price_change  DECIMAL(10,2)           DEFAULT 0  COMMENT '涨跌',
            change_pct    DECIMAL(10,4)           DEFAULT 0  COMMENT '涨跌幅',
            macd_dif      DECIMAL(10,4)           DEFAULT NULL,
            macd_dea      DECIMAL(10,4)           DEFAULT NULL,
            macd_histogram DECIMAL(10,4)          DEFAULT NULL,
            rsi_14        DECIMAL(6,2)            DEFAULT NULL,
            kdj_k         DECIMAL(6,2)            DEFAULT NULL,
            kdj_d         DECIMAL(6,2)            DEFAULT NULL,
            kdj_j         DECIMAL(6,2)            DEFAULT NULL,
            bb_upper      DECIMAL(10,2)           DEFAULT NULL,
            bb_middle     DECIMAL(10,2)           DEFAULT NULL,
            bb_lower      DECIMAL(10,2)           DEFAULT NULL,
            bb_width      DECIMAL(10,2)           DEFAULT NULL,
            recommendation VARCHAR(20)            DEFAULT NULL,
            source_ts     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ingest_ts     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_trade_date (trade_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    return table


def safe_float(val, default=0.0):
    if val is None:
        return default
    if isinstance(val, str):
        val = val.strip()
        if val in ("", "-", "None", "null"):
            return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def fetch_day_data(api_symbol: str, target_date: str, max_retries: int = 3):
    """
    从 AkShare 拉取主连历史数据，仅返回 target_date 当天那行。
    target_date 格式：YYYY-MM-DD
    失败时自动重试，重试间隔指数递增。
    """
    col_map = {
        "日期": "trade_date",
        "开盘价": "open_price",
        "最高价": "high_price",
        "最低价": "low_price",
        "收盘价": "close_price",
        "成交量": "volume",
        "持仓量": "open_interest",
    }

    for attempt in range(1, max_retries + 1):
        try:
            df = ak.futures_main_sina(symbol=api_symbol)
            if df is None or df.empty:
                return None

            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
            if "trade_date" not in df.columns:
                return None

            df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y-%m-%d")
            row = df[df["trade_date"] == target_date]
            return row if not row.empty else None

        except Exception as e:
            if attempt < max_retries:
                wait = 2 ** attempt + random.uniform(0.5, 1.5)
                logger.warning(f"  AkShare 拉取 {api_symbol} 失败 (第{attempt}次): {e}，{wait:.1f}s 后重试...")
                time.sleep(wait)
            else:
                logger.warning(f"  AkShare 拉取 {api_symbol} 失败 (已重试{max_retries}次): {e}")
                return None


def upsert_row(conn, table: str, row: pd.Series, target_date: str):
    """INSERT … ON DUPLICATE KEY UPDATE"""
    sql = f"""
        INSERT INTO {table}
            (trade_date, open_price, high_price, low_price, close_price,
             volume, open_interest)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            open_price    = VALUES(open_price),
            high_price    = VALUES(high_price),
            low_price     = VALUES(low_price),
            close_price   = VALUES(close_price),
            volume        = VALUES(volume),
            open_interest = VALUES(open_interest),
            ingest_ts     = CURRENT_TIMESTAMP
    """
    params = (
        target_date,
        safe_float(row.get("open_price")),
        safe_float(row.get("high_price")),
        safe_float(row.get("low_price")),
        safe_float(row.get("close_price")),
        int(safe_float(row.get("volume", 0))),
        int(safe_float(row.get("open_interest", 0))),
    )
    with conn.cursor() as cur:
        cur.execute(sql, params)
    conn.commit()


# ─────────────────────────── 主逻辑 ──────────────────────────

def run(target_date: str, symbols_filter=None, dry_run=False):
    logger.info("=" * 60)
    logger.info(f"补录日期: {target_date}  dry-run={dry_run}")
    logger.info("=" * 60)

    mapping = load_mapping()
    futures_cfg = mapping.get("futures", {})

    if symbols_filter:
        symbols_filter_lower = {s.lower() for s in symbols_filter}
        futures_cfg = {k: v for k, v in futures_cfg.items()
                       if k.lower() in symbols_filter_lower}

    if not futures_cfg:
        logger.error("没有匹配的品种，请检查 --symbol 参数")
        return

    conn = None if dry_run else get_conn()

    ok, skip, fail = 0, 0, 0

    try:
        total = len(futures_cfg)
        for idx, (symbol, cfg) in enumerate(futures_cfg.items(), 1):
            api_symbol = cfg["api_symbol"]
            name = cfg["name"]
            label = f"{symbol}({name})"

            df_day = fetch_day_data(api_symbol, target_date)

            if df_day is None or df_day.empty:
                logger.info(f"  ⚠  [{idx}/{total}] {label} — {target_date} 无数据")
                skip += 1
            else:
                row = df_day.iloc[0]

                if dry_run:
                    logger.info(
                        f"  [预览] [{idx}/{total}] {label} — "
                        f"open={safe_float(row.get('open_price'))}, "
                        f"close={safe_float(row.get('close_price'))}, "
                        f"vol={safe_float(row.get('volume'))}"
                    )
                    ok += 1
                else:
                    try:
                        table = ensure_table(conn, symbol)
                        upsert_row(conn, table, row, target_date)
                        logger.info(f"  ✅ [{idx}/{total}] {label} → {table}")
                        ok += 1
                    except Exception as e:
                        logger.error(f"  ❌ [{idx}/{total}] {label} 写库失败: {e}")
                        fail += 1

            # 每次请求后随机等待，避免触发新浪API限流
            if idx < total:
                time.sleep(random.uniform(0.8, 1.5))

    finally:
        if conn:
            conn.close()

    logger.info("=" * 60)
    logger.info(f"完成: 写入 {ok}, 跳过 {skip}, 失败 {fail}")
    logger.info("=" * 60)


# ─────────────────────────── CLI ─────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MySQL 历史数据补录工具")
    parser.add_argument(
        "--date", "-d", required=True,
        help="要补录的交易日期，格式 YYYY-MM-DD，例如 2026-03-05"
    )
    parser.add_argument(
        "--symbol", "-s", type=str, default=None,
        help="只补录指定品种，多个用逗号分隔，例如 aum,cum,rbm"
    )
    parser.add_argument(
        "--dry-run", "-n", action="store_true",
        help="预览模式：只打印数据，不写入 MySQL"
    )
    args = parser.parse_args()

    # 校验日期格式
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        logger.error("日期格式错误，请使用 YYYY-MM-DD")
        sys.exit(1)

    symbols = [s.strip() for s in args.symbol.split(",")] if args.symbol else None
    run(args.date, symbols_filter=symbols, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
