"""
东方财富客户端 - 自动截图模块

支持两种采集模式：
  today   - 采集当天数据（每个合约截一张图）
  history - 采集历史多日数据（每个合约 hover 日期轴逐日截图）

公共函数：calibrate, calibrate_history, take_screenshot
采集函数：collect_today(config, mode_key), collect_history(config, mode_key)
校准函数：calibrate(config), calibrate_history(config)
"""

import json
import logging
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path

import pyautogui

logger = logging.getLogger(__name__)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

DEFAULT_SUBDIRS = {"main_force": "screenshots_main_force", "retail": "screenshots_retail"}
DEFAULT_HISTORY_SUBDIRS = {"main_force": "history_main_force", "retail": "history_retail"}

CALIB_PATH = Path(__file__).resolve().parent.parent / "config" / "calibration.json"


# ── 配置读写 ──────────────────────────────────────────────────────────────────

def load_calibration() -> dict:
    """加载校准配置，不存在时返回含默认子目录的空配置。"""
    if CALIB_PATH.exists():
        with open(CALIB_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        cfg.setdefault("screenshot_subdirs", dict(DEFAULT_SUBDIRS))
        cfg.setdefault("history_screenshot_subdirs", dict(DEFAULT_HISTORY_SUBDIRS))
        return cfg
    return {
        "screenshot_subdirs": dict(DEFAULT_SUBDIRS),
        "history_screenshot_subdirs": dict(DEFAULT_HISTORY_SUBDIRS),
    }


def save_calibration(cfg: dict):
    """将校准配置写回文件。"""
    CALIB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CALIB_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    logger.info("校准配置已保存至 %s", CALIB_PATH)


# ── 截图目录 ──────────────────────────────────────────────────────────────────

def _data_root() -> Path:
    return Path(__file__).resolve().parent.parent / "data"


def screenshot_dir_for(cfg: dict, mode_key: str) -> Path:
    """返回当天模式的截图目录。mode_key: main_force | retail"""
    subdirs = cfg.get("screenshot_subdirs") or DEFAULT_SUBDIRS
    name = subdirs.get(mode_key) or DEFAULT_SUBDIRS[mode_key]
    return _data_root() / name


def history_screenshot_dir_for(cfg: dict, mode_key: str) -> Path:
    """返回历史模式的截图目录。mode_key: main_force | retail"""
    subdirs = cfg.get("history_screenshot_subdirs") or DEFAULT_HISTORY_SUBDIRS
    name = subdirs.get(mode_key) or DEFAULT_HISTORY_SUBDIRS[mode_key]
    return _data_root() / name


# ── UI 框选工具 ───────────────────────────────────────────────────────────────

def select_region(prompt_text: str = "请按住鼠标左键拖拽框选区域，按 Esc 取消") -> list | None:
    """全屏半透明遮罩，让用户拖拽框选区域，返回 [x1, y1, x2, y2]。"""
    region_result = {"coords": None}

    root = tk.Tk()
    root.title("框选区域")
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.3)
    root.configure(bg="gray")

    canvas = tk.Canvas(root, cursor="cross", bg="gray", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    start_x = start_y = 0
    rect_id = None

    def on_press(event):
        nonlocal start_x, start_y, rect_id
        start_x, start_y = event.x_root, event.y_root
        if rect_id:
            canvas.delete(rect_id)
        rect_id = canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="red", width=2,
        )

    def on_drag(event):
        nonlocal rect_id
        if rect_id:
            canvas.coords(
                rect_id,
                start_x - root.winfo_rootx(),
                start_y - root.winfo_rooty(),
                event.x,
                event.y,
            )

    def on_release(event):
        end_x, end_y = event.x_root, event.y_root
        x1 = min(start_x, end_x)
        y1 = min(start_y, end_y)
        x2 = max(start_x, end_x)
        y2 = max(start_y, end_y)
        if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
            region_result["coords"] = [x1, y1, x2, y2]
        root.destroy()

    def on_escape(event):
        root.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", on_escape)

    tk.Label(
        root,
        text=prompt_text,
        font=("Microsoft YaHei", 16),
        fg="white",
        bg="gray",
    ).place(relx=0.5, rely=0.02, anchor="n")

    root.mainloop()
    return region_result["coords"]


# ── 截图基础操作 ──────────────────────────────────────────────────────────────

def take_screenshot(region: list, output_dir: Path, filename: str | None = None) -> Path:
    """对指定区域截图并保存到 output_dir，返回文件路径。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    x1, y1, x2, y2 = region
    img = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
    if filename is None:
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = output_dir / filename
    img.save(str(filepath))
    return filepath


# ── 校准 ──────────────────────────────────────────────────────────────────────

def calibrate(cfg: dict) -> dict | None:
    """
    当天数据校准：引导用户框选合约列表区域和数据截图区域。
    校准结果写入 cfg 并保存到 config/calibration.json。
    """
    print("\n===== 第1步：框选合约列表区域 =====")
    print("请框选左侧合约列表中【当前可见的所有合约行】（从第1行顶部到最后1行底部）")
    input("准备好后按回车开始框选...")
    list_region = select_region("请框选合约列表中所有可见行的区域")
    if list_region is None:
        print("已取消。")
        return None
    print(f"  列表区域: {list_region}")

    visible_count = input("当前列表中可见多少个合约？(默认11): ").strip()
    visible_count = int(visible_count) if visible_count else 11

    total_count = input("总共有多少个合约？(默认55): ").strip()
    total_count = int(total_count) if total_count else 55

    list_height = list_region[3] - list_region[1]
    item_height = list_height / visible_count
    click_x = (list_region[0] + list_region[2]) // 2

    print(f"  列表总高度: {list_height}px  单项高度: {item_height:.1f}px  点击X: {click_x}")

    print("\n===== 第2步：框选截图数据区域 =====")
    print("请框选右侧你需要截图的数据区域")
    input("准备好后按回车开始框选...")
    screenshot_region = select_region("请框选右侧需要截图的数据区域")
    if screenshot_region is None:
        print("已取消。")
        return None
    print(f"  截图区域: {screenshot_region}")

    cfg.update({
        "list_region": list_region,
        "screenshot_region": screenshot_region,
        "visible_count": visible_count,
        "total_count": total_count,
        "item_height": item_height,
        "click_x": click_x,
    })
    cfg.setdefault("screenshot_subdirs", dict(DEFAULT_SUBDIRS))
    save_calibration(cfg)
    print("\n配置已保存到 config/calibration.json")
    return cfg


def calibrate_history(cfg: dict) -> dict | None:
    """
    历史数据校准：框选日期轴上相邻两日的区域，推导步长。
    校准结果写入 cfg 并保存到 config/calibration.json。
    """
    print("\n===== 历史数据校准：框选日期区域 =====")
    print("请在图表顶部日期轴上，框选【上一个日期】到【最新日期】之间的区域")
    print("  · 右边界 = 最新日期所在X坐标")
    print("  · 左边界 = 上一个日期所在X坐标")
    input("准备好后按回车开始框选...")
    date_region = select_region("框选日期轴上【上一个日期 → 最新日期】的区域（左=旧，右=新）")
    if date_region is None:
        print("已取消。")
        return None

    x1, y1, x2, y2 = date_region
    date_step_x = x2 - x1
    latest_date_x = x2
    date_bar_y = (y1 + y2) // 2

    print(f"  日期步长: {date_step_x}px  最新日期X: {latest_date_x}  HoverY: {date_bar_y}")

    history_count = input("收集多少天的历史数据？(默认30): ").strip()
    history_count = int(history_count) if history_count.isdigit() else 30

    hover_delay = input("hover 后等待多少秒再截图？(默认0.8): ").strip()
    try:
        hover_delay = float(hover_delay)
    except ValueError:
        hover_delay = 0.8

    cfg.update({
        "history_date_region": date_region,
        "history_date_step_x": date_step_x,
        "history_latest_date_x": latest_date_x,
        "history_date_bar_y": date_bar_y,
        "history_count": history_count,
        "history_hover_delay": hover_delay,
    })
    cfg.setdefault("history_screenshot_subdirs", dict(DEFAULT_HISTORY_SUBDIRS))
    save_calibration(cfg)
    print("\n历史数据配置已保存到 config/calibration.json")
    return cfg


# ── 采集：当天模式 ────────────────────────────────────────────────────────────

def collect_today(cfg: dict, mode_key: str, dry_run: bool = False):
    """
    采集当天数据：点击第一个合约后用键盘↓逐个切换并截图。
    mode_key: main_force | retail
    """
    list_region = cfg["list_region"]
    screenshot_region = cfg["screenshot_region"]
    total_count = cfg["total_count"]
    item_height = cfg["item_height"]
    click_x = cfg["click_x"]
    list_top_y = list_region[1]

    out_dir = screenshot_dir_for(cfg, mode_key)
    label = "主力资金" if mode_key == "main_force" else "散户资金"

    logger.info("[今日·%s] 截图目录: %s", label, out_dir)
    print(f"\n【今日·{label}】截图将保存到: {out_dir}")
    print(f"共 {total_count} 个合约，采集方式：点击第1个合约 → 键盘↓逐个切换")

    if dry_run:
        print("[dry-run] 跳过实际截图操作")
        logger.info("[dry-run] collect_today skipped")
        return

    print("5秒后开始，请切换到东方财富窗口！")
    print("紧急停止：快速将鼠标移到屏幕左上角\n")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    first_click_y = int(list_top_y + item_height / 2)
    logger.info("点击第1个合约 (%d, %d)", click_x, first_click_y)
    pyautogui.click(click_x, first_click_y)
    time.sleep(2)

    filepath = take_screenshot(screenshot_region, out_dir, "contract_001.png")
    logger.debug("[1/%d] 截图: %s", total_count, filepath.name)
    print(f"  [1/{total_count}] → {filepath.name}")

    for idx in range(2, total_count + 1):
        pyautogui.press("down")
        time.sleep(2)
        filename = f"contract_{idx:03d}.png"
        filepath = take_screenshot(screenshot_region, out_dir, filename)
        logger.debug("[%d/%d] 截图: %s", idx, total_count, filepath.name)
        print(f"  [{idx}/{total_count}] → {filepath.name}")

    logger.info("[今日·%s] 采集完成，共 %d 张", label, total_count)
    print(f"\n采集完成！共 {total_count} 张，保存在 {out_dir}")


# ── 采集：历史模式 ────────────────────────────────────────────────────────────

def _scroll_list_to_item(cfg: dict, idx: int, scroll_offset: int) -> int:
    """
    将列表滚动到合约 idx 可见位置。
    策略：点击当前可见最后一行聚焦列表 → 按↓滚动一行 → 循环。
    返回更新后的 scroll_offset。
    """
    item_height = cfg["item_height"]
    visible_count = cfg["visible_count"]
    click_x = cfg["click_x"]
    list_top_y = cfg["list_region"][1]

    while idx - scroll_offset > visible_count:
        last_y = int(list_top_y + (visible_count - 0.5) * item_height)
        pyautogui.click(click_x, last_y)
        time.sleep(0.3)
        pyautogui.press("down")
        time.sleep(0.4)
        scroll_offset += 1

    return scroll_offset


def collect_history(cfg: dict, mode_key: str, dry_run: bool = False):
    """
    采集历史数据：对每个合约，直接点击列表项（含翻页处理），
    然后在日期轴上从最新日期向左逐日 hover 截图。
    mode_key: main_force | retail
    """
    required_keys = [
        "list_region", "screenshot_region", "total_count",
        "item_height", "click_x", "visible_count",
        "history_latest_date_x", "history_date_bar_y", "history_date_step_x",
    ]
    missing = [k for k in required_keys if k not in cfg]
    if missing:
        raise ValueError(f"缺少校准配置项，请先完成历史数据校准：{missing}")

    list_region = cfg["list_region"]
    screenshot_region = cfg["screenshot_region"]
    total_count = cfg["total_count"]
    item_height = cfg["item_height"]
    visible_count = cfg["visible_count"]
    click_x = cfg["click_x"]
    list_top_y = list_region[1]

    latest_date_x = cfg["history_latest_date_x"]
    date_bar_y = cfg["history_date_bar_y"]
    date_step_x = cfg["history_date_step_x"]
    history_count = cfg.get("history_count", 30)
    hover_delay = cfg.get("history_hover_delay", 0.8)

    out_base = history_screenshot_dir_for(cfg, mode_key)
    label = "主力资金" if mode_key == "main_force" else "散户资金"

    logger.info("[历史·%s] 截图目录: %s", label, out_base)
    print(f"\n【历史·{label}】截图将保存到: {out_base}")
    print(f"共 {total_count} 个合约，每合约收集 {history_count} 天")
    print(f"日期步长: {date_step_x}px  hover等待: {hover_delay}s")

    if dry_run:
        print("[dry-run] 跳过实际截图操作")
        logger.info("[dry-run] collect_history skipped")
        return

    print("\n5秒后开始，请切换到东方财富窗口！")
    print("紧急停止：快速将鼠标移到屏幕左上角\n")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    scroll_offset = 0

    for idx in range(1, total_count + 1):
        scroll_offset = _scroll_list_to_item(cfg, idx, scroll_offset)

        visual_pos = idx - scroll_offset
        item_y = int(list_top_y + (visual_pos - 0.5) * item_height)
        logger.debug("[合约 %d/%d] 点击列表第 %d 行 Y=%d", idx, total_count, visual_pos, item_y)
        print(f"\n[合约 {idx}/{total_count}] 点击第 {visual_pos} 行 (Y={item_y})")
        pyautogui.click(click_x, item_y)
        time.sleep(2.0)

        for day in range(1, history_count + 1):
            hover_x = latest_date_x - (day - 1) * date_step_x
            print(f"  [Day {day:>3}/{history_count}] hover ({hover_x:.0f}, {date_bar_y})", end="  ")
            pyautogui.moveTo(hover_x, date_bar_y, duration=0.15)
            time.sleep(hover_delay)

            filename = f"contract_{idx:03d}_day_{day:03d}.png"
            filepath = take_screenshot(screenshot_region, out_base, filename)
            print(f"→ {filepath.name}")

    total_shots = total_count * history_count
    logger.info("[历史·%s] 采集完成，共 %d 张", label, total_shots)
    print(f"\n历史数据采集完成！共 {total_shots} 张，保存在 {out_base}")


# ── 交互菜单（供 main.py calibrate 子命令调用） ───────────────────────────────

def run_calibrate_menu():
    """进入完整的校准交互菜单。"""
    cfg = load_calibration()

    has_today = all(k in cfg for k in ["list_region", "screenshot_region", "item_height"])
    has_history = all(
        k in cfg for k in [
            "history_date_region", "history_date_step_x",
            "history_latest_date_x", "history_date_bar_y",
        ]
    )

    print("=" * 60)
    print("  东方财富客户端 - 校准菜单")
    print("=" * 60)

    if has_today:
        print(f"\n【当前数据配置】")
        print(f"  列表区域: {cfg['list_region']}")
        print(f"  截图区域: {cfg['screenshot_region']}")
        print(f"  合约高度: {cfg['item_height']:.1f}px")
        print(f"  可见/总数: {cfg['visible_count']}/{cfg['total_count']}")
        print(f"  主力目录: {screenshot_dir_for(cfg, 'main_force')}")
        print(f"  散户目录: {screenshot_dir_for(cfg, 'retail')}")

    if has_history:
        print(f"\n【历史数据配置】")
        print(f"  日期步长: {cfg['history_date_step_x']}px")
        print(f"  最新日期X: {cfg['history_latest_date_x']}")
        print(f"  Hover Y: {cfg['history_date_bar_y']}")
        print(f"  收集天数: {cfg.get('history_count', 30)}")
        print(f"  Hover等待: {cfg.get('history_hover_delay', 0.8)}s")
        print(f"  历史主力: {history_screenshot_dir_for(cfg, 'main_force')}")
        print(f"  历史散户: {history_screenshot_dir_for(cfg, 'retail')}")

    print("\n" + "-" * 60)
    print("选择操作:")
    print("  1. 重新校准（列表区域 + 截图区域）")
    print("  2. 历史数据校准（日期轴步长）")
    if has_today:
        print("  3. 测试截图（截一张检验区域是否正确）")
    options = ["1", "2"] + (["3"] if has_today else [])
    choice = input(f"\n请输入选项 ({'/'.join(options)}): ").strip()

    if choice == "1":
        calibrate(cfg)
    elif choice == "2":
        calibrate_history(cfg)
    elif choice == "3" and has_today:
        out_dir = screenshot_dir_for(cfg, "main_force")
        print(f"\n3秒后截图到 {out_dir}...")
        for i in range(3, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        fp = take_screenshot(cfg["screenshot_region"], out_dir)
        print(f"截图已保存: {fp}")
    else:
        print("无效选项。")
