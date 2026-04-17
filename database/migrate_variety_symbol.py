"""
迁移脚本：给 fut_variety 表新增 contracts_symbol 字段，并按配置文件填充映射。

映射配置文件：database/variety_contracts_map.json
  - 大小写以 contracts_main.symbol 实际值为准
  - 后续特殊品种直接改 JSON，无需动此脚本

执行方式：
  cd /Users/zxxk/ysd/ysdproject/workstation/database/fut_pulse
  python ../../migrate_variety_symbol.py
"""

import json
import os
import sys
from pathlib import Path

import pymysql
import pymysql.cursors
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
MAP_FILE = BASE_DIR / "variety_contracts_map.json"
ENV_PATH = BASE_DIR / "fut_pulse" / ".env"

load_dotenv(ENV_PATH)

DB_CONFIG = {
    "host":        os.getenv("DB_HOST"),
    "port":        int(os.getenv("DB_PORT", 3306)),
    "user":        os.getenv("DB_USER"),
    "password":    os.getenv("DB_PASSWORD"),
    "database":    os.getenv("DB_NAME"),
    "charset":     "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


def load_mapping():
    with open(MAP_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data["mapping"]


def ensure_column(cur, conn):
    cur.execute("SHOW COLUMNS FROM fut_variety LIKE 'contracts_symbol'")
    if cur.fetchone():
        print("contracts_symbol 字段已存在，跳过 ALTER TABLE。")
        return
    cur.execute("ALTER TABLE fut_variety ADD COLUMN contracts_symbol VARCHAR(20) DEFAULT NULL")
    conn.commit()
    print("已新增 contracts_symbol 字段。")


def fetch_current(cur):
    cur.execute("SELECT id, name, contracts_symbol FROM fut_variety ORDER BY id")
    return {row["id"]: row for row in cur.fetchall()}


def preview(mapping, current):
    print("\n===== 变更预览（共 {} 条） =====".format(len(mapping)))
    print(f"{'ID':>4}  {'品种名':<10}  {'当前值':<14}  {'目标symbol':<14}  状态")
    print("-" * 65)
    for item in mapping:
        vid = item["variety_id"]
        vsymbol = item["contracts_symbol"]
        row = current.get(vid)
        cur_val = row["contracts_symbol"] if row else "-"
        if row is None:
            status = "★ 新增行"
        elif cur_val == vsymbol:
            status = "  一致"
        else:
            status = "✎ 更新"
        print(f"{vid:>4}  {item['variety_name']:<10}  {str(cur_val):<14}  {vsymbol:<14}  {status}")
    print()


def run_migration(cur, conn, mapping):
    sql = "UPDATE fut_variety SET contracts_symbol = %s WHERE id = %s"
    rows = [(item["contracts_symbol"], item["variety_id"]) for item in mapping]
    cur.executemany(sql, rows)
    conn.commit()
    print(f"迁移完成，共更新 {cur.rowcount} 行（实际变更行数）。")


def main():
    mapping = load_mapping()

    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            ensure_column(cur, conn)
            current = fetch_current(cur)
            preview(mapping, current)

            answer = input("确认执行以上变更？[y/N] ").strip().lower()
            if answer != "y":
                print("已取消。")
                return

            run_migration(cur, conn, mapping)

            print("\n===== 执行后验证（前10条） =====")
            cur.execute("SELECT id, name, contracts_symbol FROM fut_variety ORDER BY id LIMIT 10")
            for row in cur.fetchall():
                print(f"  id={row['id']:>3}  name={row['name']:<10}  contracts_symbol={row['contracts_symbol']}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
