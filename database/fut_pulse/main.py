"""
期货资金强度采集系统 - 统一入口

用法：
  python main.py today                                  # 采集当天数据
  python main.py today --no-upload                      # 仅截图+OCR，不上传
  python main.py history --days 30                      # 采集最近30个交易日
  python main.py history --start 2026-03-01 --end 2026-04-10  # 指定日期范围
  python main.py close-history --days 30                # 只回填收盘价
  python main.py history --no-screenshot                # 仅对已有历史截图跑OCR+上传
  python main.py calibrate                              # 进入校准菜单
  python main.py ocr-only                               # 仅对已有截图跑OCR（历史模式）
  python main.py ocr-only --today                       # 仅对已有截图跑OCR（今日模式）
  python main.py upload-only                            # 仅上传已有result.json

全局选项：
  --dry-run   只打印操作计划，不执行实际截图/OCR/上传
"""

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def cmd_today(args):
    from pipeline import run
    run(
        mode="today",
        skip_upload=args.no_upload,
        dry_run=args.dry_run,
    )


def cmd_history(args):
    from pipeline import run
    run(
        mode="history",
        days=args.days,
        start=args.start,
        end=args.end,
        skip_screenshot=args.no_screenshot,
        skip_upload=args.no_upload,
        dry_run=args.dry_run,
    )


def cmd_calibrate(args):
    from collector.screenshot import run_calibrate_menu
    run_calibrate_menu()


def cmd_ocr_only(args):
    from pipeline import run_ocr_only
    mode = "today" if args.today else "history"
    run_ocr_only(mode=mode)


def cmd_upload_only(args):
    from pipeline import run_upload_only
    run_upload_only(dry_run=args.dry_run)


def cmd_close_history(args):
    from close_price import run_close_history

    run_close_history(
        days=args.days,
        start=args.start,
        end=args.end,
        symbols=args.symbol,
        dry_run=args.dry_run,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="期货资金强度采集系统 - 统一入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印操作计划，不执行实际截图/OCR/上传",
    )

    sub = parser.add_subparsers(dest="command", metavar="<命令>")
    sub.required = True

    # ── today ──
    p_today = sub.add_parser("today", help="采集当天数据（截图 → OCR → 上传）")
    p_today.add_argument("--no-upload", action="store_true", help="仅截图+OCR，跳过上传")
    p_today.set_defaults(func=cmd_today)

    # ── history ──
    p_hist = sub.add_parser("history", help="采集连续多日历史数据（截图 → OCR → 上传）")
    hist_days = p_hist.add_mutually_exclusive_group()
    hist_days.add_argument(
        "--days", type=int, metavar="N",
        help="从今天向前取 N 个交易日（默认读 calibration.json 中的 history_count 或 30）",
    )
    hist_days.add_argument(
        "--start", metavar="YYYY-MM-DD",
        help="与 --end 配合指定日期范围的开始日期",
    )
    p_hist.add_argument(
        "--end", metavar="YYYY-MM-DD",
        help="与 --start 配合指定日期范围的结束日期（默认今天）",
    )
    p_hist.add_argument(
        "--no-screenshot", action="store_true",
        help="跳过截图步骤，使用 data/ 目录下已有截图直接跑 OCR",
    )
    p_hist.add_argument("--no-upload", action="store_true", help="仅截图+OCR，跳过上传")
    p_hist.set_defaults(func=cmd_history)

    # ── close-history ──
    p_close = sub.add_parser("close-history", help="仅通过 AkShare 回填 fut_daily_close")
    close_days = p_close.add_mutually_exclusive_group()
    close_days.add_argument(
        "--days", type=int, metavar="N",
        help="从今天向前取 N 个交易日进行 close 价格回填",
    )
    close_days.add_argument(
        "--start", metavar="YYYY-MM-DD",
        help="与 --end 配合指定 close 回填开始日期",
    )
    p_close.add_argument(
        "--end", metavar="YYYY-MM-DD",
        help="与 --start 配合指定 close 回填结束日期（默认今天）",
    )
    p_close.add_argument(
        "--symbol", metavar="k1,k2",
        help="只处理指定品种 key，例如 rbm,cum",
    )
    p_close.set_defaults(func=cmd_close_history)

    # ── calibrate ──
    p_calib = sub.add_parser("calibrate", help="进入校准交互菜单（框选屏幕区域）")
    p_calib.set_defaults(func=cmd_calibrate)

    # ── ocr-only ──
    p_ocr = sub.add_parser("ocr-only", help="仅对 data/ 目录下已有截图执行 OCR")
    p_ocr.add_argument(
        "--today", action="store_true",
        help="以今日模式解析（默认为历史模式）",
    )
    p_ocr.set_defaults(func=cmd_ocr_only)

    # ── upload-only ──
    p_up = sub.add_parser("upload-only", help="仅将已有 data/result.json 上传到 MySQL")
    p_up.set_defaults(func=cmd_upload_only)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # --start 指定但 --end 未指定时，默认 end=今天
    if hasattr(args, "start") and args.start and not args.end:
        from datetime import date
        args.end = date.today().isoformat()

    # --start/--end 必须同时提供
    if hasattr(args, "end") and args.end and not getattr(args, "start", None):
        parser.error("--end 需要与 --start 一起使用")

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\n用户中断。")
        sys.exit(0)


if __name__ == "__main__":
    main()
