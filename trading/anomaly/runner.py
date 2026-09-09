"""
异常检测独立 CLI 入口。

用法：
  python -m trading.anomaly.runner                       # 最近一个有 fut_strength 的交易日
  python -m trading.anomaly.runner 2026-09-04            # 检测指定日期
  python -m trading.anomaly.runner 2026-08-20 2026-09-04 # 区间内每个交易日
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("anomaly_runner")


def _parse_date(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        logger.error("日期格式错误：%s，应为 YYYY-MM-DD", value)
        sys.exit(1)
    return value


def _date_iso(value) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)[:10]


def _latest_trade_date(conn) -> str | None:
    with conn.cursor() as cur:
        cur.execute("SELECT MAX(trade_date) AS d FROM fut_strength")
        row = cur.fetchone()
    return _date_iso(row["d"]) if row else None


def _trade_dates_in_range(conn, start: str, end: str) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT trade_date FROM fut_strength "
            "WHERE trade_date >= %s AND trade_date <= %s "
            "ORDER BY trade_date",
            (start, end),
        )
        rows = cur.fetchall()
    dates: list[str] = []
    for row in rows:
        iso = _date_iso(row["trade_date"])
        if iso:
            dates.append(iso)
    return dates


def main() -> None:
    start = _parse_date(sys.argv[1]) if len(sys.argv) > 1 else None
    end = _parse_date(sys.argv[2]) if len(sys.argv) > 2 else None

    from trading.anomaly.detector import run_anomaly_detection
    from trading.strategies.db import get_connection

    conn = get_connection()
    try:
        if start and end:
            dates = _trade_dates_in_range(conn, start, end)
        elif start:
            dates = [start]
        else:
            latest = _latest_trade_date(conn)
            if not latest:
                logger.error("fut_strength 中没有交易日，无法检测")
                sys.exit(1)
            dates = [latest]
    finally:
        conn.close()

    if not dates:
        logger.error("指定区间内没有交易日：%s ~ %s", start, end)
        sys.exit(1)

    logger.info("========== 异常检测开始，共 %d 个交易日 ==========", len(dates))
    total = 0
    for td in dates:
        logger.info("---------- 检测 %s ----------", td)
        n = run_anomaly_detection(td)
        logger.info("日期 %s 写入 %d 条", td, n)
        total += n
    logger.info("========== 异常检测完成，共写入 %d 条 ==========", total)


if __name__ == "__main__":
    main()
