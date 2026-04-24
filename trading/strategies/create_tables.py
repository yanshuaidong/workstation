"""
建表脚本：删除旧 assistant_* 表，创建新 trading_* 表，并插入初始资金曲线记录。
运行：python -m trading.strategies.create_tables
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from trading.strategies.db import get_connection
from trading.strategies.settings import INITIAL_CAPITAL


DROP_STMTS = [
    "DROP TABLE IF EXISTS assistant_signals",
    "DROP TABLE IF EXISTS assistant_operations",
    "DROP TABLE IF EXISTS assistant_positions",
    "DROP TABLE IF EXISTS assistant_account_daily",
]

CREATE_STMTS = [
    """
    CREATE TABLE IF NOT EXISTS trading_pool (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        variety_id   INT NOT NULL,
        variety_name VARCHAR(20),
        sector       VARCHAR(20) NOT NULL COMMENT '板块，用于组合约束',
        is_active    TINYINT(1) DEFAULT 1 COMMENT '是否在池子A中',
        created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_variety (variety_id)
    ) COMMENT='池子A品种配置，可动态调整'
    """,
    """
    CREATE TABLE IF NOT EXISTS trading_signals (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        signal_date  DATE NOT NULL,
        variety_id   INT NOT NULL,
        variety_name VARCHAR(20),
        signal_type  VARCHAR(20) NOT NULL COMMENT 'A_OPEN_LONG/A_OPEN_SHORT/A_CLOSE_LONG/A_CLOSE_SHORT',
        main_score   FLOAT COMMENT '动量分位分（仅 OPEN 信号有值）',
        extra_json   JSON COMMENT '计算明细',
        created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_date_variety_signal (signal_date, variety_id, signal_type),
        KEY idx_date_variety (signal_date, variety_id)
    ) COMMENT='每日A通道信号记录（全品种）'
    """,
    """
    CREATE TABLE IF NOT EXISTS trading_operations (
        id            INT AUTO_INCREMENT PRIMARY KEY,
        signal_date   DATE NOT NULL,
        variety_id    INT NOT NULL,
        variety_name  VARCHAR(20),
        sector        VARCHAR(20) COMMENT '板块',
        signal_type   VARCHAR(20) NOT NULL COMMENT 'A_OPEN_LONG/A_OPEN_SHORT',
        main_score    FLOAT COMMENT '动量分位分，决定优先级',
        is_selected   TINYINT(1) DEFAULT 0 COMMENT '是否通过组合约束被选中执行',
        reject_reason VARCHAR(30) COMMENT 'capacity_full/sector_conflict/null（已选中）',
        extra_json    JSON,
        created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_date_variety_signal (signal_date, variety_id, signal_type),
        KEY idx_date (signal_date)
    ) COMMENT='操作建议（仅池子A品种，含组合约束结果）'
    """,
    """
    CREATE TABLE IF NOT EXISTS trading_positions (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        operation_id INT COMMENT '关联 trading_operations.id',
        variety_id   INT NOT NULL,
        variety_name VARCHAR(20),
        sector       VARCHAR(20) COMMENT '板块',
        direction    VARCHAR(10) NOT NULL COMMENT 'LONG/SHORT',
        open_date    DATE NOT NULL,
        open_price   FLOAT NOT NULL,
        close_date   DATE,
        close_price  FLOAT,
        size_pct     FLOAT DEFAULT 0.3333 COMMENT '每槽1/3权重',
        status       VARCHAR(10) DEFAULT 'open' COMMENT 'open/closed',
        pnl_pct      FLOAT COMMENT '无杠杆收益率',
        created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
        KEY idx_status (status)
    ) COMMENT='自动化账户持仓（单账户，最多3槽）'
    """,
    """
    CREATE TABLE IF NOT EXISTS trading_account_daily (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        record_date  DATE NOT NULL,
        equity       FLOAT NOT NULL,
        cash         FLOAT NOT NULL,
        position_val FLOAT DEFAULT 0,
        daily_pnl    FLOAT DEFAULT 0,
        created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_date (record_date)
    ) COMMENT='自动化账户每日净值曲线（单账户）'
    """,
]


def init_pool(conn) -> None:
    from trading.strategies.settings import TARGET_POOL

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS cnt FROM trading_pool")
        if cur.fetchone()["cnt"] > 0:
            print("trading_pool 已有数据，跳过初始化")
            return

        cur.execute("SELECT id, name FROM fut_variety")
        variety_map = {r["name"]: int(r["id"]) for r in cur.fetchall()}

        for name, sector in TARGET_POOL:
            vid = variety_map.get(name)
            if vid is None:
                print(f"  警告：未找到品种 {name}，跳过")
                continue
            cur.execute(
                "INSERT IGNORE INTO trading_pool (variety_id, variety_name, sector, is_active) "
                "VALUES (%s,%s,%s,1)",
                (vid, name, sector),
            )
    conn.commit()
    print("trading_pool 初始化完成")


def init_account_daily(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS cnt FROM trading_account_daily")
        if cur.fetchone()["cnt"] > 0:
            print("trading_account_daily 已有数据，跳过初始化")
            return
        from datetime import date
        cur.execute(
            "INSERT INTO trading_account_daily "
            "(record_date, equity, cash, position_val, daily_pnl) "
            "VALUES (%s,%s,%s,0,0)",
            (date.today().isoformat(), INITIAL_CAPITAL, INITIAL_CAPITAL),
        )
    conn.commit()
    print(f"trading_account_daily 初始化：equity={INITIAL_CAPITAL}")


def main() -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for stmt in DROP_STMTS:
                cur.execute(stmt)
                print(f"执行: {stmt.strip()[:50]}")
            conn.commit()

            for stmt in CREATE_STMTS:
                cur.execute(stmt)
                print(f"创建表完成")
            conn.commit()

        init_pool(conn)
        init_account_daily(conn)
        print("所有表创建完成。")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
