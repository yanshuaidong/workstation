"""
每日入口脚本。手动执行，依赖当日数据已完成采集。
执行顺序：
  1. 检查数据完整性
  2. 计算全品种 A 通道信号 → 写 trading_signals
  3. 生成池子A操作建议 → 写 trading_operations
  4. 执行平仓（先于开仓）
  5. 执行开仓
  6. 更新资金曲线 → 写 trading_account_daily

运行：python -m trading.strategies.daily_run [YYYY-MM-DD]
"""
from __future__ import annotations

import logging
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("daily_run")


def parse_date(arg: str | None) -> date:
    if arg:
        return datetime.strptime(arg, "%Y-%m-%d").date()
    return date.today()


def main() -> None:
    run_date = parse_date(sys.argv[1] if len(sys.argv) > 1 else None)
    logger.info("========== 开始每日运行，日期: %s ==========", run_date)

    from trading.strategies.db import get_connection
    from trading.strategies.data_loader import check_data_completeness
    from trading.strategies.signals import run_signals_for_all
    from trading.strategies.operations import generate_operations
    from trading.strategies.account import execute_close_signals, execute_open_operations, update_account_daily

    conn = get_connection()
    try:
        ok, msg = check_data_completeness(conn, run_date.isoformat())
        if not ok:
            logger.error("数据完整性校验失败，终止运行: %s", msg)
            sys.exit(1)
        logger.info("数据完整性校验通过: %s", msg)

        logger.info("Step 1: 计算全品种 A 通道信号")
        triggered = run_signals_for_all(conn, run_date)
        logger.info("触发信号的品种数: %d", len(triggered))
        for vname, stypes in triggered.items():
            logger.info("  %s → %s", vname, stypes)

        logger.info("Step 2: 生成池子A操作建议")
        generate_operations(conn, run_date)

        logger.info("Step 3: 执行平仓信号")
        closed_today = execute_close_signals(conn, run_date)
        logger.info("今日平仓品种数: %d", len(closed_today))

        logger.info("Step 4: 执行开仓建议")
        execute_open_operations(conn, run_date, closed_today)

        logger.info("Step 5: 更新资金曲线")
        update_account_daily(conn, run_date)

        logger.info("========== 每日运行完成 ==========")
    except Exception as exc:
        logger.exception("每日运行异常: %s", exc)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
