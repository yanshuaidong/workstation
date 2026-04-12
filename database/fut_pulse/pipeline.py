"""
流程编排模块

串联三个步骤：截图 → OCR → 上传
支持 today / history 两种模式，自动生成 trade_dates（排除周末）。

每次运行的日志写入 logs/run_YYYYMMDD_HHMMSS.log
任一步骤失败后打印明确错误，跳过后续步骤，保留截图供复查。
"""

import json
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CALIB_PATH = BASE_DIR / "config" / "calibration.json"
VARIETIES_PATH = BASE_DIR / "config" / "varieties.json"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# ── 日志配置 ──────────────────────────────────────────────────────────────────

def setup_logging(run_tag: str) -> logging.Logger:
    """配置文件 + 控制台双输出日志，返回根 logger。"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"run_{run_tag}.log"

    fmt = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # 控制台：INFO 及以上
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(fmt, datefmt))

    # 文件：DEBUG 及以上（包含 OCR 置信度等详细信息）
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(fmt, datefmt))

    root.addHandler(ch)
    root.addHandler(fh)

    logging.info("日志文件: %s", log_file)
    return root


# ── 交易日历 ──────────────────────────────────────────────────────────────────

def load_holidays() -> set:
    """
    加载节假日列表（可选）。
    若 config/holidays.json 存在，读取其中的日期字符串列表；否则返回空集合。
    holidays.json 格式示例：["2026-01-01", "2026-02-04", ...]
    """
    holidays_path = BASE_DIR / "config" / "holidays.json"
    if holidays_path.exists():
        with open(holidays_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {date.fromisoformat(d) for d in raw}
    return set()


def is_trade_day(d: date, holidays: set) -> bool:
    """判断是否为交易日（排除周末和节假日）。"""
    return d.weekday() < 5 and d not in holidays


def generate_trade_dates(
    days: int | None = None,
    start: str | None = None,
    end: str | None = None,
) -> list[str]:
    """
    生成交易日列表（倒序，最新在前）。

    参数优先级：
      - start + end  → 指定范围
      - days         → 从今天往前取 N 个交易日
      - 默认          → 仅今天（如果是交易日）

    返回格式：["2026-04-10", "2026-04-09", ...]
    """
    holidays = load_holidays()
    today = date.today()

    if start and end:
        d_start = date.fromisoformat(start)
        d_end   = date.fromisoformat(end)
        all_days = []
        cur = d_end
        while cur >= d_start:
            if is_trade_day(cur, holidays):
                all_days.append(cur.isoformat())
            cur -= timedelta(days=1)
        return all_days

    if days:
        collected = []
        cur = today
        while len(collected) < days:
            if is_trade_day(cur, holidays):
                collected.append(cur.isoformat())
            cur -= timedelta(days=1)
        return collected

    # 默认：仅当天
    if is_trade_day(today, holidays):
        return [today.isoformat()]
    # 当天不是交易日，取最近一个交易日
    cur = today - timedelta(days=1)
    while not is_trade_day(cur, holidays):
        cur -= timedelta(days=1)
    logging.getLogger(__name__).warning(
        "今天 (%s) 不是交易日，使用最近交易日 %s", today.isoformat(), cur.isoformat()
    )
    return [cur.isoformat()]


# ── 配置加载 ──────────────────────────────────────────────────────────────────

def load_calibration() -> dict:
    if not CALIB_PATH.exists():
        raise FileNotFoundError(f"缺少校准配置: {CALIB_PATH}，请先运行 calibrate 命令")
    with open(CALIB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_varieties() -> list:
    if not VARIETIES_PATH.exists():
        raise FileNotFoundError(f"缺少品种配置: {VARIETIES_PATH}")
    with open(VARIETIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 步骤封装 ──────────────────────────────────────────────────────────────────

def step_screenshot(mode: str, cfg: dict, dry_run: bool = False):
    """步骤1：截图采集（today 或 history）。"""
    from collector.screenshot import collect_today, collect_history

    logger = logging.getLogger("pipeline.screenshot")
    logger.info("=== 步骤1：截图采集 [%s] ===", mode)

    for mode_key in ("main_force", "retail"):
        label = "主力资金" if mode_key == "main_force" else "散户资金"
        logger.info("开始采集 %s ...", label)
        if mode == "today":
            collect_today(cfg, mode_key, dry_run=dry_run)
        else:
            collect_history(cfg, mode_key, dry_run=dry_run)

    logger.info("截图采集完成")


def step_ocr(mode: str, cfg: dict, out_path: Path, history_count: int = 30, dry_run: bool = False) -> list:
    """步骤2：OCR 识别，返回结果列表。"""
    from collector.ocr import run_today, run_history
    from collector.screenshot import screenshot_dir_for, history_screenshot_dir_for

    logger = logging.getLogger("pipeline.ocr")
    logger.info("=== 步骤2：OCR 识别 [%s] ===", mode)

    if dry_run:
        logger.info("[dry-run] OCR 跳过，返回空结果")
        return []

    if mode == "today":
        main_dir   = screenshot_dir_for(cfg, "main_force")
        retail_dir = screenshot_dir_for(cfg, "retail")
        result = run_today(main_dir, retail_dir, out_path, cfg.get("total_count"))
    else:
        main_dir   = history_screenshot_dir_for(cfg, "main_force")
        retail_dir = history_screenshot_dir_for(cfg, "retail")
        result = run_history(main_dir, retail_dir, out_path, history_count, cfg.get("total_count"))

    logger.info("OCR 完成，结果已写入 %s", out_path)
    return result


def step_upload(result: list, trade_dates: list, varieties: list, dry_run: bool = False):
    """步骤3：上传 MySQL。"""
    from uploader.mysql import upload

    logger = logging.getLogger("pipeline.upload")
    logger.info("=== 步骤3：MySQL 上传 ===")
    logger.info("交易日范围: %s ~ %s，共 %d 天", trade_dates[-1], trade_dates[0], len(trade_dates))

    if dry_run:
        logger.info("[dry-run] 上传跳过")
        print(f"[dry-run] 将上传 {len(result)} 个品种，{len(trade_dates)} 个交易日")
        return

    upload(result, trade_dates, varieties)
    logger.info("MySQL 上传完成")


# ── 主编排函数 ────────────────────────────────────────────────────────────────

def run(
    mode: str,
    days: int | None = None,
    start: str | None = None,
    end: str | None = None,
    skip_screenshot: bool = False,
    skip_upload: bool = False,
    dry_run: bool = False,
):
    """
    完整流程入口。

    mode       : "today" | "history"
    days       : 历史模式下的天数（与 start/end 互斥）
    start/end  : 历史模式下的日期范围（格式 YYYY-MM-DD）
    skip_screenshot : True = 跳过截图步骤（使用已有截图）
    skip_upload     : True = 跳过上传步骤（仅截图+OCR）
    dry_run    : True = 所有步骤只打印，不执行实际操作
    """
    run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    setup_logging(run_tag)
    logger = logging.getLogger("pipeline")

    logger.info("========== 采集流程开始 [%s] mode=%s ==========", run_tag, mode)

    # ── 加载配置 ──
    try:
        cfg = load_calibration()
        varieties = load_varieties()
    except FileNotFoundError as e:
        logger.error("配置加载失败: %s", e)
        print(f"\n[错误] {e}")
        sys.exit(1)

    # ── 生成交易日期 ──
    if mode == "today":
        trade_dates = generate_trade_dates()
        history_count = 1
    else:
        if days is None and start is None:
            days = cfg.get("history_count", 30)
        trade_dates = generate_trade_dates(days=days, start=start, end=end)
        history_count = len(trade_dates)

    logger.info("交易日: %s ~ %s，共 %d 天", trade_dates[-1], trade_dates[0], len(trade_dates))
    print(f"\n交易日期：{trade_dates[-1]} ~ {trade_dates[0]}，共 {len(trade_dates)} 天")

    result_path = DATA_DIR / "result.json"

    # ── 步骤1：截图 ──
    if not skip_screenshot:
        try:
            step_screenshot(mode, cfg, dry_run=dry_run)
        except Exception as e:
            logger.error("截图步骤失败: %s", e, exc_info=True)
            print(f"\n[错误] 截图步骤失败，流程中止。\n  原因：{e}")
            print("  截图文件已保留在 data/ 目录供排查。")
            sys.exit(1)
    else:
        logger.info("跳过截图步骤（使用已有截图）")
        print("跳过截图步骤，使用已有截图。")

    # ── 步骤2：OCR ──
    try:
        result = step_ocr(mode, cfg, result_path, history_count=history_count, dry_run=dry_run)
    except Exception as e:
        logger.error("OCR 步骤失败: %s", e, exc_info=True)
        print(f"\n[错误] OCR 步骤失败，跳过上传。\n  原因：{e}")
        print("  截图文件已保留在 data/ 目录供排查。")
        sys.exit(1)

    # ── 步骤3：上传 ──
    if not skip_upload:
        try:
            step_upload(result, trade_dates, varieties, dry_run=dry_run)
        except Exception as e:
            logger.error("上传步骤失败: %s", e, exc_info=True)
            print(f"\n[错误] 上传步骤失败。\n  原因：{e}")
            print("  result.json 已保留，可稍后单独执行 upload-only 重试。")
            sys.exit(1)
    else:
        logger.info("跳过上传步骤")
        print("跳过上传步骤。")

    logger.info("========== 采集流程完成 [%s] ==========", run_tag)
    print(f"\n===== 全部完成！日志: logs/run_{run_tag}.log =====")


def run_ocr_only(mode: str = "history"):
    """仅对 data/ 目录下已有截图执行 OCR，输出 result.json。"""
    run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    setup_logging(run_tag)
    logger = logging.getLogger("pipeline")
    logger.info("========== OCR-only 模式 [%s] ==========", run_tag)

    try:
        cfg = load_calibration()
    except FileNotFoundError as e:
        logger.error("%s", e)
        sys.exit(1)

    # history_count 从现有文件数量推断
    history_count = cfg.get("history_count", 30)
    result_path = DATA_DIR / "result.json"

    result = step_ocr(mode, cfg, result_path, history_count=history_count)
    logger.info("OCR-only 完成")
    print(f"\n===== OCR 完成！结果: {result_path} =====")
    return result


def run_upload_only():
    """从已有 result.json 读取数据并上传 MySQL。"""
    run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    setup_logging(run_tag)
    logger = logging.getLogger("pipeline")
    logger.info("========== upload-only 模式 [%s] ==========", run_tag)

    result_path = DATA_DIR / "result.json"
    if not result_path.exists():
        logger.error("找不到 result.json: %s", result_path)
        print(f"[错误] 找不到 {result_path}，请先执行截图+OCR。")
        sys.exit(1)

    with open(result_path, "r", encoding="utf-8") as f:
        result = json.load(f)

    varieties = load_varieties()

    # 从 result 推断是 today 还是 history
    sample = result[0] if result else {}
    main_sample = sample.get("main_force")
    if isinstance(main_sample, list):
        n_days = len(main_sample)
        trade_dates = generate_trade_dates(days=n_days)
        logger.info("推断历史模式，%d 天", n_days)
        print(f"推断为历史模式，{n_days} 个交易日")
    else:
        trade_dates = generate_trade_dates()
        logger.info("推断今日模式")
        print("推断为今日模式")

    step_upload(result, trade_dates, varieties)
    logger.info("upload-only 完成")
    print(f"\n===== 上传完成！日志: logs/run_{run_tag}.log =====")
