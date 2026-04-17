"""assistant 模块数据库与日期工具。"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pymysql
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[3]


def load_env_config() -> Path | None:
    """从项目根目录加载环境变量。"""
    for env_file in (ROOT_DIR / ".env", ROOT_DIR / "env.production"):
        if env_file.exists():
            load_dotenv(env_file)
            return env_file
    return None


_LOADED_ENV_FILE = load_env_config()


def _require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"环境变量 {key} 未设置，请检查 {_LOADED_ENV_FILE or '.env'}")
    return value


DB_CONFIG = {
    "host": _require_env("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": _require_env("DB_USER"),
    "password": _require_env("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "futures"),
    "charset": "utf8mb4",
}


def get_db_connection(dict_cursor: bool = False):
    """获取 MySQL 连接。"""
    kwargs = dict(DB_CONFIG)
    if dict_cursor:
        kwargs["cursorclass"] = pymysql.cursors.DictCursor
    return pymysql.connect(**kwargs)


def parse_date(value: Any) -> date:
    """将字符串/日期/时间转换为 date。"""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    raise TypeError(f"无法解析日期: {value!r}")


def to_date_str(value: Any) -> str:
    """统一输出 YYYY-MM-DD。"""
    return parse_date(value).isoformat()


def parse_json(value: Any) -> dict[str, Any]:
    """兼容解析 MySQL JSON 字段。"""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return {}
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {"raw": value}
    return {"raw": value}


def dump_json(value: Any) -> str:
    """写入 MySQL 前统一转 JSON 字符串。"""
    return json.dumps(value or {}, ensure_ascii=False, default=str)


def get_latest_trade_date(conn=None) -> date:
    """获取 fut_daily_close 中最新交易日。"""
    should_close = conn is None
    if conn is None:
        conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(trade_date) FROM fut_daily_close")
        latest = cursor.fetchone()[0]
        if not latest:
            raise RuntimeError("fut_daily_close 暂无数据，无法确定最新交易日")
        return parse_date(latest)
    finally:
        cursor.close()
        if should_close:
            conn.close()


def cli_fail(message: str, code: int = 1) -> None:
    """命令行失败退出。"""
    print(f"[ERROR] {message}", file=sys.stderr)
    raise SystemExit(code)

