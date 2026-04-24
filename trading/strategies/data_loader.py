from __future__ import annotations

import pandas as pd
import pymysql

from .db import get_connection


def load_variety_map(conn: pymysql.Connection) -> pd.DataFrame:
    with conn.cursor() as cur:
        cur.execute("SELECT id, name FROM fut_variety ORDER BY id")
        return pd.DataFrame(cur.fetchall())


def load_variety_data(conn: pymysql.Connection, variety_id: int) -> pd.DataFrame:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT trade_date, main_force, retail "
            "FROM fut_strength WHERE variety_id=%s ORDER BY trade_date",
            (variety_id,),
        )
        strength = pd.DataFrame(cur.fetchall())

        cur.execute(
            "SELECT trade_date, close_price AS close "
            "FROM fut_daily_close WHERE variety_id=%s ORDER BY trade_date",
            (variety_id,),
        )
        close = pd.DataFrame(cur.fetchall())

    if strength.empty or close.empty:
        return pd.DataFrame()

    df = strength.merge(close, on="trade_date", how="inner").dropna()
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    return df.sort_values("trade_date").reset_index(drop=True)


def load_all_pool_data(conn: pymysql.Connection) -> dict[str, tuple[int, pd.DataFrame]]:
    variety_df = load_variety_map(conn)
    if variety_df.empty:
        return {}
    name_to_id = dict(zip(variety_df["name"], variety_df["id"]))

    from .settings import TARGET_VARIETIES

    result: dict[str, tuple[int, pd.DataFrame]] = {}
    for name in TARGET_VARIETIES:
        vid = name_to_id.get(name)
        if vid is None:
            continue
        df = load_variety_data(conn, int(vid))
        if not df.empty:
            result[name] = (int(vid), df)
    return result


def load_all_varieties_data(conn: pymysql.Connection) -> dict[int, pd.DataFrame]:
    variety_df = load_variety_map(conn)
    if variety_df.empty:
        return {}
    result: dict[int, pd.DataFrame] = {}
    for _, row in variety_df.iterrows():
        df = load_variety_data(conn, int(row["id"]))
        if not df.empty:
            result[int(row["id"])] = df
    return result


def check_data_completeness(conn: pymysql.Connection, trade_date: str) -> tuple[bool, str]:
    from .settings import TARGET_VARIETIES

    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(DISTINCT variety_id) AS cnt FROM fut_strength WHERE trade_date=%s",
            (trade_date,),
        )
        row = cur.fetchone()
        actual = row["cnt"] if row else 0

        cur.execute("SELECT COUNT(*) AS cnt FROM fut_variety")
        row = cur.fetchone()
        total = row["cnt"] if row else 0

        cur.execute(
            "SELECT v.name FROM fut_variety v "
            "LEFT JOIN fut_strength s ON s.variety_id=v.id AND s.trade_date=%s "
            "WHERE s.variety_id IS NULL ORDER BY v.name",
            (trade_date,),
        )
        missing = [r["name"] for r in cur.fetchall()]

    pool_missing = [n for n in TARGET_VARIETIES if n in missing]
    if pool_missing:
        return False, f"池子A品种数据缺失：{pool_missing}"
    return True, f"数据完整，共 {actual}/{total} 个品种有当日数据"
