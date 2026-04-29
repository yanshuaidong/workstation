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
        signal_role  VARCHAR(10) NOT NULL DEFAULT 'open' COMMENT '理论信号角色：open/close',
        direction    VARCHAR(10) COMMENT '理论方向：LONG/SHORT',
        cycle_id     VARCHAR(64) COMMENT '理论开平仓周期ID',
        related_open_signal_id INT COMMENT '平仓信号关联的理论开仓信号ID',
        related_open_date DATE COMMENT '平仓信号关联的理论开仓日期',
        theory_state_before VARCHAR(10) COMMENT '理论状态变化前：none/long/short',
        theory_state_after  VARCHAR(10) COMMENT '理论状态变化后：none/long/short',
        main_score   FLOAT COMMENT '动量分位分（仅 OPEN 信号有值）',
        extra_json   JSON COMMENT '计算明细',
        created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_date_variety_signal (signal_date, variety_id, signal_type),
        KEY idx_date_variety (signal_date, variety_id),
        KEY idx_cycle (variety_id, cycle_id)
    ) COMMENT='理论信号记录（全品种，含理论开平仓周期）'
    """,
    """
    CREATE TABLE IF NOT EXISTS trading_operations (
        id            INT AUTO_INCREMENT PRIMARY KEY,
        signal_id     INT COMMENT '关联 trading_signals.id，便于追溯原始信号明细',
        signal_date   DATE NOT NULL,
        variety_id    INT NOT NULL,
        variety_name  VARCHAR(20),
        sector        VARCHAR(20) COMMENT '板块',
        signal_type   VARCHAR(20) NOT NULL COMMENT 'A_OPEN_LONG/A_OPEN_SHORT',
        operation_type VARCHAR(10) NOT NULL DEFAULT 'OPEN' COMMENT '建议类型：OPEN',
        direction     VARCHAR(10) COMMENT '建议方向：LONG/SHORT',
        signal_cycle_id VARCHAR(64) COMMENT '来源理论信号周期ID',
        main_score    FLOAT COMMENT '动量分位分，决定优先级',
        is_selected   TINYINT(1) DEFAULT 0 COMMENT '是否通过组合约束被选中执行',
        reject_reason VARCHAR(30) COMMENT 'capacity_full/sector_conflict/null（已选中）',
        selection_rank INT COMMENT '同日开仓候选排序',
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
        open_operation_id INT COMMENT '真实开仓来源建议ID',
        open_signal_id INT COMMENT '真实开仓来源理论信号ID',
        close_signal_id INT COMMENT '真实平仓来源理论信号ID',
        theory_cycle_id VARCHAR(64) COMMENT '真实交易对应的理论信号周期ID',
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
    """
    CREATE TABLE IF NOT EXISTS trading_signal_state (
        variety_id  INT NOT NULL,
        state_date  DATE NOT NULL COMMENT '该状态对应的信号日期',
        state       ENUM('none','long','short') NOT NULL DEFAULT 'none',
        PRIMARY KEY (variety_id, state_date)
    ) COMMENT='旧理论状态快照缓存（不作为业务事实源）'
    """,
]


def sync_pool_with_varieties(conn) -> int:
    """把 fut_variety 中尚未在 trading_pool 的品种，以 is_active=0 + 标准 sector 的默认状态补齐。

    sector 从 VARIETY_SECTORS 映射取值；映射中不存在的品种回退为 DEFAULT_SECTOR。
    已存在的记录不会被改动，保留用户手动调整过的 sector 和 is_active。
    返回本次新补齐的品种数量，便于调用方打印日志。
    """
    from trading.strategies.settings import VARIETY_SECTORS, DEFAULT_SECTOR

    with conn.cursor() as cur:
        cur.execute("SELECT id, name FROM fut_variety")
        varieties = list(cur.fetchall())
        cur.execute("SELECT variety_id FROM trading_pool")
        existing_ids = {int(r["variety_id"]) for r in cur.fetchall()}

        added = 0
        for r in varieties:
            vid = int(r["id"])
            if vid in existing_ids:
                continue
            sector = VARIETY_SECTORS.get(r["name"], DEFAULT_SECTOR)
            cur.execute(
                "INSERT IGNORE INTO trading_pool (variety_id, variety_name, sector, is_active) "
                "VALUES (%s,%s,%s,0)",
                (vid, r["name"], sector),
            )
            added += 1
    conn.commit()
    return added


def init_pool(conn) -> None:
    from trading.strategies.settings import TARGET_POOL

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS cnt FROM trading_pool")
        existing_count = int(cur.fetchone()["cnt"])

        if existing_count == 0:
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
            print(f"trading_pool 初始化完成：默认激活 {len(TARGET_POOL)} 个品种")
        else:
            print(f"trading_pool 已有 {existing_count} 条记录，保留原有激活状态")

    added = sync_pool_with_varieties(conn)
    if added:
        print(f"trading_pool 补齐 {added} 个未激活品种（is_active=0）")


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


def _column_exists(cur, table_name: str, column_name: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s AND COLUMN_NAME=%s",
        (table_name, column_name),
    )
    return int(cur.fetchone()["cnt"]) > 0


def _index_exists(cur, table_name: str, index_name: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s AND INDEX_NAME=%s",
        (table_name, index_name),
    )
    return int(cur.fetchone()["cnt"]) > 0


def _add_column_if_missing(cur, table_name: str, column_name: str, ddl: str) -> None:
    if _column_exists(cur, table_name, column_name):
        return
    cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")
    print(f"迁移：{table_name} 添加 {column_name} 列")


def _add_index_if_missing(cur, table_name: str, index_name: str, ddl: str) -> None:
    if _index_exists(cur, table_name, index_name):
        return
    cur.execute(f"ALTER TABLE {table_name} ADD INDEX {ddl}")
    print(f"迁移：{table_name} 添加 {index_name} 索引")


def run_migrations(conn) -> None:
    """对已有数据库执行增量迁移，新建库走 CREATE_STMTS 即可，无需重复执行。"""
    with conn.cursor() as cur:
        _add_column_if_missing(
            cur,
            "trading_signals",
            "signal_role",
            "signal_role VARCHAR(10) NOT NULL DEFAULT 'open' COMMENT '理论信号角色：open/close' AFTER signal_type",
        )
        _add_column_if_missing(cur, "trading_signals", "direction", "direction VARCHAR(10) COMMENT '理论方向：LONG/SHORT' AFTER signal_role")
        _add_column_if_missing(cur, "trading_signals", "cycle_id", "cycle_id VARCHAR(64) COMMENT '理论开平仓周期ID' AFTER direction")
        _add_column_if_missing(cur, "trading_signals", "related_open_signal_id", "related_open_signal_id INT COMMENT '平仓信号关联的理论开仓信号ID' AFTER cycle_id")
        _add_column_if_missing(cur, "trading_signals", "related_open_date", "related_open_date DATE COMMENT '平仓信号关联的理论开仓日期' AFTER related_open_signal_id")
        _add_column_if_missing(cur, "trading_signals", "theory_state_before", "theory_state_before VARCHAR(10) COMMENT '理论状态变化前：none/long/short' AFTER related_open_date")
        _add_column_if_missing(cur, "trading_signals", "theory_state_after", "theory_state_after VARCHAR(10) COMMENT '理论状态变化后：none/long/short' AFTER theory_state_before")
        _add_index_if_missing(cur, "trading_signals", "idx_cycle", "idx_cycle (variety_id, cycle_id)")

        _add_column_if_missing(cur, "trading_operations", "signal_id", "signal_id INT COMMENT '关联 trading_signals.id' AFTER id")
        _add_column_if_missing(cur, "trading_operations", "operation_type", "operation_type VARCHAR(10) NOT NULL DEFAULT 'OPEN' COMMENT '建议类型：OPEN' AFTER signal_type")
        _add_column_if_missing(cur, "trading_operations", "direction", "direction VARCHAR(10) COMMENT '建议方向：LONG/SHORT' AFTER operation_type")
        _add_column_if_missing(cur, "trading_operations", "signal_cycle_id", "signal_cycle_id VARCHAR(64) COMMENT '来源理论信号周期ID' AFTER direction")
        _add_column_if_missing(cur, "trading_operations", "selection_rank", "selection_rank INT COMMENT '同日开仓候选排序' AFTER reject_reason")

        _add_column_if_missing(cur, "trading_positions", "open_operation_id", "open_operation_id INT COMMENT '真实开仓来源建议ID' AFTER operation_id")
        _add_column_if_missing(cur, "trading_positions", "open_signal_id", "open_signal_id INT COMMENT '真实开仓来源理论信号ID' AFTER open_operation_id")
        _add_column_if_missing(cur, "trading_positions", "close_signal_id", "close_signal_id INT COMMENT '真实平仓来源理论信号ID' AFTER open_signal_id")
        _add_column_if_missing(cur, "trading_positions", "theory_cycle_id", "theory_cycle_id VARCHAR(64) COMMENT '真实交易对应的理论信号周期ID' AFTER close_signal_id")
    conn.commit()


def reset_strategy_results(conn) -> None:
    """清空策略运行结果，保留 trading_pool 与 fut_* 基础数据。"""
    tables = [
        "trading_operations",
        "trading_positions",
        "trading_account_daily",
        "trading_signals",
        "trading_signal_state",
    ]
    with conn.cursor() as cur:
        for table in tables:
            cur.execute(f"DELETE FROM {table}")
            print(f"清空策略结果表：{table}")
    conn.commit()
    init_account_daily(conn)


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

        run_migrations(conn)
        init_pool(conn)
        init_account_daily(conn)
        print("所有表创建完成。")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
