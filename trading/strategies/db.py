from __future__ import annotations

import os
from pathlib import Path

import pymysql
import pymysql.cursors
from dotenv import load_dotenv

_loaded = False


def _ensure_env() -> None:
    global _loaded
    if _loaded:
        return
    root = Path(__file__).resolve().parent.parent.parent
    for name in (".env", "env.production"):
        p = root / name
        if p.exists():
            load_dotenv(p)
            break
    _loaded = True


def get_connection() -> pymysql.Connection:
    _ensure_env()
    return pymysql.connect(
        host=os.getenv("DB_HOST", ""),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "futures"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
