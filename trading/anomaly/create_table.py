"""
创建 anomaly_signals 表。

运行：python -m trading.anomaly.create_table
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from trading.strategies.db import get_connection

CREATE_STMT = """
CREATE TABLE IF NOT EXISTS anomaly_signals (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    signal_date   DATE NOT NULL              COMMENT '信号日期（交易日）',
    variety_id    INT                        COMMENT '品种 ID（关联 fut_variety.id）',
    variety_name  VARCHAR(50)                COMMENT '品种名称',
    symbol        VARCHAR(20)                COMMENT '合约代码（contracts_symbol）',
    metric        VARCHAR(50) NOT NULL       COMMENT '异常指标：change_pct/volume/open_interest/main_force/retail',
    direction     ENUM('up','down')          COMMENT '异常方向：up=偏高/放量, down=偏低/缩量',
    current_value FLOAT                      COMMENT '当日指标值',
    baseline_mean FLOAT                      COMMENT '基准均值（过去 window_days 天）',
    baseline_std  FLOAT                      COMMENT '基准标准差',
    z_score       FLOAT                      COMMENT '标准差倍数（当日值偏离均值的 Z-Score）',
    window_days   INT DEFAULT 20             COMMENT '基准窗口天数',
    description   TEXT                       COMMENT '人读描述',
    is_trusted    TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1=展示 0=人工判定不可信',
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_date_variety_metric (signal_date, variety_id, metric),
    KEY idx_signal_date (signal_date),
    KEY idx_variety_id  (variety_id)
) COMMENT='期货指标异常信号（涨跌幅/成交量/持仓量/主力指数/散单指数）'
"""

ALTER_TRUSTED = """
ALTER TABLE anomaly_signals
    ADD COLUMN is_trusted TINYINT(1) NOT NULL DEFAULT 1
    COMMENT '1=展示 0=人工判定不可信'
"""


def ensure_trusted_column(cursor) -> None:
    """已建表补 is_trusted 列，列已存在则忽略。"""
    try:
        cursor.execute(ALTER_TRUSTED)
    except Exception as exc:
        code = exc.args[0] if exc.args else None
        if code == 1060 or "Duplicate column" in str(exc):
            return
        raise


def ensure_table(conn=None) -> None:
    """确保 anomaly_signals 表存在，幂等。"""
    _own = conn is None
    if _own:
        conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_STMT)
            ensure_trusted_column(cur)
        conn.commit()
        print("anomaly_signals 表已就绪")
    finally:
        if _own:
            conn.close()


def main() -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_STMT)
            ensure_trusted_column(cur)
        conn.commit()
        print("anomaly_signals 表创建完成")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
