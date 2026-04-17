"""
create_tables.py — 仅运行一次，创建 assistant 模块所需的四张 MySQL 表。

用法：
    cd test/assistant/src
    python create_tables.py

依赖：
    pip install pymysql python-dotenv
"""

import sys
from pathlib import Path
import pymysql
from dotenv import load_dotenv
import os

# ── 环境变量加载 ──────────────────────────────────────────────────────────────
# 从项目根目录（workstation/）加载 .env
_ROOT = Path(__file__).resolve().parents[3]  # workstation/
for _env_file in [_ROOT / '.env', _ROOT / 'env.production']:
    if _env_file.exists():
        load_dotenv(_env_file)
        print(f"已加载环境配置: {_env_file}")
        break

def _require_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        print(f"[ERROR] 环境变量 {key} 未设置，请检查 .env 文件", file=sys.stderr)
        sys.exit(1)
    return val

DB_CONFIG = {
    'host':     _require_env('DB_HOST'),
    'port':     int(os.getenv('DB_PORT', 3306)),
    'user':     _require_env('DB_USER'),
    'password': _require_env('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'futures'),
    'charset':  'utf8mb4',
}

# ── 建表 SQL ──────────────────────────────────────────────────────────────────
CREATE_SQLS = [
    # 1. 每日信号记录
    """
    CREATE TABLE IF NOT EXISTS assistant_signals (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        signal_date  DATE NOT NULL,
        variety_id   INT NOT NULL,
        variety_name VARCHAR(20),
        indicator    VARCHAR(40) NOT NULL,
        direction    VARCHAR(10),
        triggered    TINYINT(1) DEFAULT 0,
        strength     FLOAT,
        extra_json   JSON,
        created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
        KEY idx_date_variety (signal_date, variety_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日指标信号记录'
    """,

    # 2. 策略操作建议
    """
    CREATE TABLE IF NOT EXISTS assistant_operations (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        signal_date  DATE NOT NULL,
        variety_id   INT NOT NULL,
        variety_name VARCHAR(20),
        strategy     VARCHAR(40) NOT NULL,
        direction    VARCHAR(10) NOT NULL,
        extra_json   JSON,
        account_type VARCHAR(20) DEFAULT 'mechanical',
        executed     TINYINT(1) DEFAULT 0,
        created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
        KEY idx_date (signal_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='策略操作建议（机械/LLM）'
    """,

    # 3. 模拟持仓
    """
    CREATE TABLE IF NOT EXISTS assistant_positions (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        account_type VARCHAR(20) NOT NULL,
        variety_id   INT NOT NULL,
        variety_name VARCHAR(20),
        direction    VARCHAR(10) NOT NULL,
        open_date    DATE NOT NULL,
        open_price   FLOAT NOT NULL,
        close_date   DATE,
        close_price  FLOAT,
        size_pct     FLOAT DEFAULT 0.3,
        status       VARCHAR(10) DEFAULT 'open',
        pnl_pct      FLOAT,
        strategy     VARCHAR(40),
        created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
        KEY idx_account_status (account_type, status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模拟账户持仓记录'
    """,

    # 4. 账户每日净值
    """
    CREATE TABLE IF NOT EXISTS assistant_account_daily (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        record_date  DATE NOT NULL,
        account_type VARCHAR(20) NOT NULL,
        equity       FLOAT NOT NULL,
        cash         FLOAT NOT NULL,
        position_val FLOAT DEFAULT 0,
        daily_pnl    FLOAT DEFAULT 0,
        created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_date_account (record_date, account_type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='账户每日净值曲线'
    """,
]

TABLE_NAMES = [
    'assistant_signals',
    'assistant_operations',
    'assistant_positions',
    'assistant_account_daily',
]

# ── 主流程 ────────────────────────────────────────────────────────────────────
def main():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        for name, sql in zip(TABLE_NAMES, CREATE_SQLS):
            cursor.execute(sql)
            print(f"  [OK] {name}")
        conn.commit()
        print("\n四张 assistant 表创建完成（已存在的表不会被修改）。")
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] 建表失败: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
