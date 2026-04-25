"""
fut_pulse 单日补采工具（独立自包含）

专门解决"漏采某天 + 软件上多出半天夜盘数据"这种错位场景。
例如：
  - 4月24 忘记采集
  - 4月27（周一）凌晨的夜盘半天数据占据了东方财富软件最右列
  - 右边第二列才是 4月24 的完整日数据

本功能与 today / history 主流程完全隔离：
  - 本目录（fut_pulse/backfill/）自包含代码、配置、数据、日志
  - 不改、不依赖主流程的 today / history / pipeline 逻辑
  - 通过把 fut_pulse/ 注入 sys.path，复用主项目的：
      collector.screenshot / collector.ocr
      uploader.mysql / close_price / database.init_tables
      config/calibration.json（列表/截图区域/步长）
      config/varieties.json（品种清单）

命令（在本目录下运行，或从任意位置指定完整路径运行均可）：
  python backfill_day.py calibrate    # 框选目标日期竖线 + 设置 trade_date
  python backfill_day.py screenshot   # 采集截图（主力 + 散户）
  python backfill_day.py ocr          # OCR 识别 → data/result.json
  python backfill_day.py upload       # 写入 fut_strength + 同步 fut_daily_close
  python backfill_day.py all          # 一键：screenshot → ocr → upload

全局选项：
  --dry-run   只打印，不执行实际操作
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import date, datetime
from pathlib import Path

# ── 路径常量 ──────────────────────────────────────────────────────────────────
# BASE_DIR = backfill/          PARENT_DIR = fut_pulse/
BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent

# 让本脚本能 import fut_pulse 根目录下的主模块（collector/uploader/close_price/...）
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

# 本功能独占的目录
CONFIG_PATH = BASE_DIR / "config.json"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
RESULT_PATH = DATA_DIR / "result.json"

# 主项目（fut_pulse）共享资源
MAIN_CALIB_PATH = PARENT_DIR / "config" / "calibration.json"
MAIN_VARIETIES_PATH = PARENT_DIR / "config" / "varieties.json"

# 本目录下的截图子目录名（相对 DATA_DIR）
DEFAULT_SUBDIRS = {
    "main_force": "main_force",
    "retail": "retail",
}

REQUIRED_CALIB_KEYS = (
    "list_region", "screenshot_region", "total_count",
    "item_height", "visible_count", "click_x",
)


# ── 日志 ──────────────────────────────────────────────────────────────────────

def setup_logging(run_tag: str) -> logging.Logger:
    """日志写入 backfill/logs/backfill_*.log，与主流程 logs/ 完全隔离。"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"backfill_{run_tag}.log"

    fmt = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(fmt, datefmt))

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(fmt, datefmt))

    root.addHandler(ch)
    root.addHandler(fh)

    logging.info("日志文件: %s", log_file)
    return root


# ── 配置读写 ──────────────────────────────────────────────────────────────────

def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"缺少配置文件: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_main_calibration() -> dict:
    if not MAIN_CALIB_PATH.exists():
        raise FileNotFoundError(
            f"缺少主校准: {MAIN_CALIB_PATH}，请先在 fut_pulse/ 运行 "
            f"`python main.py calibrate`"
        )
    cfg = load_json(MAIN_CALIB_PATH)
    missing = [k for k in REQUIRED_CALIB_KEYS if k not in cfg]
    if missing:
        raise ValueError(
            f"主校准缺少字段 {missing}，请先运行 `python main.py calibrate`"
        )
    return cfg


def load_backfill_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"缺少 {CONFIG_PATH}，请先运行 `python backfill_day.py calibrate`"
        )
    cfg = load_json(CONFIG_PATH)
    cfg.setdefault("screenshot_subdirs", dict(DEFAULT_SUBDIRS))
    for key in ("target_trade_date", "hover_x", "hover_y"):
        if key not in cfg:
            raise ValueError(f"{CONFIG_PATH} 缺少字段 `{key}`，请重新执行 calibrate")
    return cfg


def screenshot_dir_for(backfill_cfg: dict, mode_key: str) -> Path:
    subdirs = backfill_cfg.get("screenshot_subdirs") or DEFAULT_SUBDIRS
    name = subdirs.get(mode_key) or DEFAULT_SUBDIRS[mode_key]
    return DATA_DIR / name


# ── 校准 ──────────────────────────────────────────────────────────────────────

def cmd_calibrate(args):
    run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    setup_logging(run_tag)
    logger = logging.getLogger("backfill.calibrate")

    from collector.screenshot import select_region

    main_cfg = load_main_calibration()

    existing = load_json(CONFIG_PATH) if CONFIG_PATH.exists() else {}

    default_date = existing.get("target_trade_date", "")
    prompt = (
        f"请输入补采目标日期 YYYY-MM-DD"
        + (f"（回车使用上次的 {default_date}）" if default_date else "")
        + ": "
    )
    target = input(prompt).strip()
    if not target:
        if not default_date:
            print("[错误] 必须指定目标日期。")
            sys.exit(1)
        target = default_date
    try:
        date.fromisoformat(target)
    except ValueError:
        print(f"[错误] 日期格式不合法: {target}（应为 YYYY-MM-DD）")
        sys.exit(1)

    print("\n===== 框选目标日期竖线 =====")
    print(f"请在图表顶部日期轴上，框选【{target}】那根竖线的左右相邻区域。")
    print("  · 目的是取框的中点作为该日期的 hover X 坐标。")
    print("  · 框选宽度约一两个像素即可（足够包住那根竖线）。")
    print("  · Esc 取消。")
    input("准备好后按回车开始框选...")

    region = select_region(f"框选【{target}】的日期竖线（取中点为 hover X）")
    if region is None:
        print("已取消。")
        return

    x1, y1, x2, y2 = region
    hover_x = (x1 + x2) // 2
    region_mid_y = (y1 + y2) // 2

    default_hover_y = main_cfg.get("history_date_bar_y", region_mid_y)
    default_delay = main_cfg.get("history_hover_delay", 1.0)

    print(f"\n  框选区域: {region}")
    print(f"  推导 hover X = {hover_x}")
    print(f"  框选区域 Y 中点 = {region_mid_y}")
    print(f"  calibration.json 中的 history_date_bar_y = {default_hover_y}")

    use_region_y = input(
        f"hover Y 使用哪个？[1] calibration 的 {default_hover_y}（推荐）"
        f"  [2] 本次框选中点 {region_mid_y}  (默认1): "
    ).strip() or "1"
    hover_y = region_mid_y if use_region_y == "2" else default_hover_y

    delay_input = input(f"hover 等待秒数（默认 {default_delay}）: ").strip()
    try:
        hover_delay = float(delay_input) if delay_input else float(default_delay)
    except ValueError:
        hover_delay = float(default_delay)

    cfg = {
        "target_trade_date": target,
        "hover_x": hover_x,
        "hover_y": hover_y,
        "hover_delay": hover_delay,
        "hover_region": region,
        "move_duration": float(existing.get("move_duration", 0.4)),
        "jiggle_pixels": int(existing.get("jiggle_pixels", 2)),
        "pre_jiggle_wait": float(existing.get("pre_jiggle_wait", 0.2)),
        "screenshot_subdirs": existing.get("screenshot_subdirs") or dict(DEFAULT_SUBDIRS),
    }
    save_json(CONFIG_PATH, cfg)
    logger.info("校准完成：%s", cfg)
    print(f"\n已保存 → {CONFIG_PATH}")
    print("  target_trade_date:", target)
    print("  hover_x / hover_y / delay:", hover_x, hover_y, hover_delay)
    print(
        "  move_duration / jiggle_pixels / pre_jiggle_wait:",
        cfg["move_duration"], cfg["jiggle_pixels"], cfg["pre_jiggle_wait"],
    )
    print("  若 tooltip 还是出不来，可以直接编辑 config.json 调大这几个值。")


# ── 截图 ──────────────────────────────────────────────────────────────────────

def _hover_and_trigger(
    pyautogui,
    hover_x: int,
    hover_y: int,
    move_duration: float,
    jiggle_pixels: int,
    pre_jiggle_wait: float,
    hover_delay: float,
):
    """
    稳妥地 hover 到目标位置并触发 tooltip。

    步骤：
      1. 缓慢移动到 (hover_x, hover_y)，给软件反应时间
      2. 短暂等待，让 tooltip 首次有机会弹出
      3. jiggle：左偏 N 像素 → 回到中心，强制触发 tooltip 重绘
      4. 等 hover_delay 再截图
    """
    pyautogui.moveTo(hover_x, hover_y, duration=move_duration)
    time.sleep(pre_jiggle_wait)

    if jiggle_pixels and jiggle_pixels > 0:
        pyautogui.moveTo(hover_x - jiggle_pixels, hover_y, duration=0.10)
        time.sleep(0.08)
        pyautogui.moveTo(hover_x, hover_y, duration=0.10)

    time.sleep(hover_delay)


def _collect_one_mode(
    backfill_cfg: dict,
    main_cfg: dict,
    mode_key: str,
    dry_run: bool = False,
):
    import pyautogui
    from collector.screenshot import take_screenshot, _scroll_list_to_item

    logger = logging.getLogger("backfill.screenshot")
    label = "主力资金" if mode_key == "main_force" else "散户资金"

    hover_x = backfill_cfg["hover_x"]
    hover_y = backfill_cfg["hover_y"]
    hover_delay = float(backfill_cfg.get("hover_delay", 1.0))
    move_duration = float(backfill_cfg.get("move_duration", 0.4))
    jiggle_pixels = int(backfill_cfg.get("jiggle_pixels", 2))
    pre_jiggle_wait = float(backfill_cfg.get("pre_jiggle_wait", 0.2))

    list_region = main_cfg["list_region"]
    screenshot_region = main_cfg["screenshot_region"]
    total_count = main_cfg["total_count"]
    item_height = main_cfg["item_height"]
    click_x = main_cfg["click_x"]
    list_top_y = list_region[1]

    out_dir = screenshot_dir_for(backfill_cfg, mode_key)
    logger.info("[%s] 截图目录: %s", label, out_dir)
    print(f"\n【{label}】截图目录: {out_dir}")
    print(
        f"  共 {total_count} 个合约，hover=({hover_x},{hover_y})，"
        f"移动 {move_duration}s，jiggle±{jiggle_pixels}px，等待 {hover_delay}s"
    )

    if dry_run:
        print("[dry-run] 跳过实际截图")
        logger.info("[dry-run] %s collect skipped", label)
        return

    print("\n5秒后开始，请切换到东方财富窗口！")
    print("紧急停止：快速将鼠标移到屏幕左上角\n")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    scroll_offset = 0
    for idx in range(1, total_count + 1):
        scroll_offset = _scroll_list_to_item(main_cfg, idx, scroll_offset)

        visual_pos = idx - scroll_offset
        item_y = int(list_top_y + (visual_pos - 0.5) * item_height)
        logger.debug(
            "[合约 %d/%d] 点击列表第 %d 行 Y=%d", idx, total_count, visual_pos, item_y
        )
        print(f"[合约 {idx}/{total_count}] 点击第 {visual_pos} 行 (Y={item_y})", end="  ")
        pyautogui.click(click_x, item_y)
        time.sleep(2.0)

        _hover_and_trigger(
            pyautogui,
            hover_x=hover_x,
            hover_y=hover_y,
            move_duration=move_duration,
            jiggle_pixels=jiggle_pixels,
            pre_jiggle_wait=pre_jiggle_wait,
            hover_delay=hover_delay,
        )

        filename = f"contract_{idx:03d}.png"
        filepath = take_screenshot(screenshot_region, out_dir, filename)
        print(f"→ {filepath.name}")
        logger.debug("[%d/%d] 截图: %s", idx, total_count, filepath.name)

    logger.info("[%s] 采集完成，共 %d 张", label, total_count)
    print(f"\n【{label}】采集完成！共 {total_count} 张，保存在 {out_dir}")


def cmd_screenshot(args):
    run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    setup_logging(run_tag)
    logger = logging.getLogger("backfill.screenshot")
    logger.info("========== 补采截图 [%s] ==========", run_tag)

    backfill_cfg = load_backfill_config()
    main_cfg = load_main_calibration()

    target = backfill_cfg["target_trade_date"]
    logger.info("目标日期: %s", target)
    print(f"\n目标补采日期: {target}")

    _collect_one_mode(backfill_cfg, main_cfg, "main_force", dry_run=args.dry_run)

    if not args.dry_run:
        print("\n" + "=" * 60)
        print("  主力资金采集完成，即将开始【散户资金】采集")
        print("=" * 60)
        print("请先完成以下操作：")
        print("  1. 在东方财富客户端切换到【散户资金】图表")
        print("  2. 将左侧合约列表滚动回第一个合约")
        print("  3. 确保第一个合约处于选中（高亮）状态")
        print("  4. 若日期轴刻度有漂移，可重新执行 `calibrate`")
        print("-" * 60)
        input("完成后按回车键继续...")

    _collect_one_mode(backfill_cfg, main_cfg, "retail", dry_run=args.dry_run)

    logger.info("补采截图完成")


# ── OCR ───────────────────────────────────────────────────────────────────────

def cmd_ocr(args):
    run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    setup_logging(run_tag)
    logger = logging.getLogger("backfill.ocr")
    logger.info("========== 补采 OCR [%s] ==========", run_tag)

    backfill_cfg = load_backfill_config()
    main_dir = screenshot_dir_for(backfill_cfg, "main_force")
    retail_dir = screenshot_dir_for(backfill_cfg, "retail")

    from collector.ocr import load_varieties, ocr_single

    if args.dry_run:
        print("[dry-run] 跳过 OCR 步骤")
        logger.info("[dry-run] OCR 跳过")
        return

    from cnocr import CnOcr

    varieties = sorted(load_varieties(), key=lambda x: x["id"])
    total_count = len(varieties)

    for d, name in [(main_dir, "主力资金"), (retail_dir, "散户资金")]:
        if not d.is_dir():
            logger.warning("%s 目录不存在: %s", name, d)
            print(f"[警告] {name} 目录不存在: {d}")
        else:
            print(f"{name} 目录: {d}")

    logger.info("初始化 OCR 引擎...")
    print("正在初始化 OCR ...")
    ocr = CnOcr(det_model_name="naive_det")

    results = []
    for v in varieties:
        vid = v["id"]
        key = v["key"]
        stem = f"contract_{vid:03d}.png"
        label_m = f"{key}/主力"
        label_r = f"{key}/散户"
        main_force, _ = ocr_single(ocr, main_dir / stem, label_m)
        retail, _ = ocr_single(ocr, retail_dir / stem, label_r)
        results.append(
            {"id": vid, "key": key, "main_force": main_force, "retail": retail}
        )
        print(f"  [{vid:03d}] {key}: 主力={main_force}  散户={retail}")

    save_json(RESULT_PATH, results)

    ok_m = sum(1 for r in results if r["main_force"] is not None)
    ok_r = sum(1 for r in results if r["retail"] is not None)
    logger.info(
        "OCR 完成：主力 %d/%d，散户 %d/%d，输出: %s",
        ok_m, total_count, ok_r, total_count, RESULT_PATH,
    )
    print(f"\n完成！主力识别 {ok_m}/{total_count}，散户识别 {ok_r}/{total_count}")
    print(f"结果已保存至 {RESULT_PATH}")


# ── 上传 ──────────────────────────────────────────────────────────────────────

def cmd_upload(args):
    run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    setup_logging(run_tag)
    logger = logging.getLogger("backfill.upload")
    logger.info("========== 补采上传 [%s] ==========", run_tag)

    backfill_cfg = load_backfill_config()
    target = backfill_cfg["target_trade_date"]

    if not RESULT_PATH.exists():
        print(f"[错误] 找不到 {RESULT_PATH}，请先执行 `screenshot` + `ocr`。")
        sys.exit(1)

    with open(RESULT_PATH, "r", encoding="utf-8") as f:
        result = json.load(f)

    varieties = load_json(MAIN_VARIETIES_PATH)

    logger.info("目标日期: %s，结果条数: %d", target, len(result))
    print(f"\n目标日期: {target}")
    print(f"待上传: {len(result)} 条")

    if args.dry_run:
        print("[dry-run] 跳过 MySQL 上传 + close 同步")
        logger.info("[dry-run] upload & close sync skipped")
        return

    try:
        from uploader.mysql import upload
        upload(result, [target], varieties)
    except Exception as e:
        logger.error("fut_strength 上传失败: %s", e, exc_info=True)
        print(f"\n[错误] fut_strength 上传失败。\n  原因：{e}")
        print(f"  {RESULT_PATH} 已保留，修复后可重跑 `upload` 子命令。")
        sys.exit(1)

    try:
        from close_price import sync_close_prices
        sync_close_prices(trade_dates=[target], varieties=varieties, dry_run=False)
    except Exception as e:
        logger.error("close 价格同步失败: %s", e, exc_info=True)
        print(f"\n[错误] fut_daily_close 同步失败。\n  原因：{e}")
        print(
            f"  fut_strength 已上传成功，可在 fut_pulse/ 运行 "
            f"`python main.py close-history --start {target} --end {target}` 单独补录。"
        )
        sys.exit(1)

    logger.info("补采上传完成")
    print(f"\n===== 补采完成！日志: {LOGS_DIR / f'backfill_{run_tag}.log'} =====")


# ── 一键 ──────────────────────────────────────────────────────────────────────

def cmd_all(args):
    cmd_screenshot(args)
    cmd_ocr(args)
    cmd_upload(args)


# ── 入口 ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="backfill_day.py",
        description="fut_pulse 单日补采工具（独立自包含：代码 + 配置 + 数据 + 日志）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="只打印，不执行实际截图/OCR/上传",
    )

    sub = parser.add_subparsers(dest="command", metavar="<命令>")
    sub.required = True

    p_cal = sub.add_parser("calibrate", help="框选目标日期竖线 + 设置 trade_date")
    p_cal.set_defaults(func=cmd_calibrate)

    p_shot = sub.add_parser("screenshot", help="按 config.json 采集主力 + 散户截图")
    p_shot.set_defaults(func=cmd_screenshot)

    p_ocr = sub.add_parser("ocr", help="OCR 识别截图 → data/result.json")
    p_ocr.set_defaults(func=cmd_ocr)

    p_up = sub.add_parser("upload", help="上传 fut_strength + 同步 fut_daily_close")
    p_up.set_defaults(func=cmd_upload)

    p_all = sub.add_parser("all", help="一键：screenshot → ocr → upload")
    p_all.set_defaults(func=cmd_all)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\n用户中断。")
        sys.exit(0)


if __name__ == "__main__":
    main()
