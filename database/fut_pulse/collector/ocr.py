"""
OCR 识别模块

读取「主力资金」「散户资金」两个目录下的截图，
按 varieties.json 中的品种表合并为一条 JSON 列表。

today 模式：
  读取 contract_{id:03d}.png
  每项字段：id, key, main_force（单值）, retail（单值）

history 模式：
  读取 contract_{id:03d}_day_{day:03d}.png（day_001 为最新）
  每项字段：id, key, main_force（列表）, retail（列表）
"""

import json
import logging
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from cnocr import CnOcr

logger = logging.getLogger(__name__)

VARIETIES_PATH = Path(__file__).resolve().parent.parent / "config" / "varieties.json"

# OCR 置信度阈值：低于此值记 warning（cnocr 返回的 score 为 0~1）
CONFIDENCE_THRESHOLD = 0.6


# ── 品种配置加载 ──────────────────────────────────────────────────────────────

def load_varieties() -> list:
    """从 config/varieties.json 加载品种列表。"""
    if not VARIETIES_PATH.exists():
        raise FileNotFoundError(f"缺少品种配置: {VARIETIES_PATH}")
    with open(VARIETIES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        raise ValueError("varieties.json 为空，请先配置品种列表")
    return data


# ── 图像预处理 ────────────────────────────────────────────────────────────────

def preprocess(img_path: Path) -> np.ndarray:
    """放大并增强图像以提高 OCR 识别准确率。"""
    img = Image.open(img_path).convert("RGB")
    img = img.resize((img.width * 4, img.height * 4), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    return np.array(img)


# ── 数值提取 ──────────────────────────────────────────────────────────────────

def extract_value(text: str) -> float | None:
    """从 OCR 文本中提取数值（支持负数和小数）。

    源数据始终为 2 位小数格式（如 -21.31）。当 OCR 漏识别小数点时，
    会产生异常大的整数（如 2131），此时自动在倒数第 2 位前补回小数点。
    """
    text = text.replace(" ", "").replace("：", ":").replace(",", "")
    text = text.replace("一", "-").replace("—", "-").replace("–", "-")
    for ch in "↑↓个↗↘†‡":
        text = text.replace(ch, "")
    match = re.search(r"(-?\d+\.?\d*)", text)
    if not match:
        return None
    raw = match.group(1)
    if "." not in raw:
        sign = "-" if raw.startswith("-") else ""
        digits = raw.lstrip("-")
        if len(digits) >= 4:
            integer_part = digits[:-2]
            decimal_part = digits[-2:]
            corrected = f"{sign}{integer_part}.{decimal_part}"
            logger.info("小数点修正: %r → %s（原始文本: %r）", raw, corrected, text)
            raw = corrected
        elif len(digits) == 3:
            logger.warning(
                "疑似漏识别小数点（3位整数 %s），但无法确定是否为正常值，未自动修正（原始文本: %r）",
                raw, text,
            )
    return round(float(raw), 2)


# ── 单张图识别 ────────────────────────────────────────────────────────────────

def ocr_single(ocr: CnOcr, img_path: Path, label: str = "") -> tuple[float | None, str]:
    """
    识别单张截图，返回 (数值, 原始文本)。
    若文件不存在或识别不到数值，返回 (None, "")。
    低置信度结果会记录 warning 日志。
    """
    if not img_path.is_file():
        logger.debug("文件不存在: %s", img_path)
        return None, ""

    processed = preprocess(img_path)
    ocr_out = ocr.ocr(processed)

    if not ocr_out:
        logger.warning("[%s] OCR 无输出: %s", label, img_path.name)
        return None, ""

    # 置信度检查
    scores = [item.get("score", 1.0) for item in ocr_out]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    raw_text = "".join(item["text"] for item in ocr_out)

    if avg_score < CONFIDENCE_THRESHOLD:
        logger.warning(
            "[%s] 低置信度 %.2f (阈值 %.2f)，文件: %s，识别文本: %r",
            label, avg_score, CONFIDENCE_THRESHOLD, img_path.name, raw_text,
        )

    value = extract_value(raw_text)
    if value is None:
        logger.warning("[%s] 未能从文本 %r 中提取数值，文件: %s", label, raw_text, img_path.name)

    return value, raw_text


# ── 今日模式 ──────────────────────────────────────────────────────────────────

def run_today(
    main_dir: Path,
    retail_dir: Path,
    out_path: Path,
    total_count: int | None = None,
) -> list:
    """
    今日模式：每个品种读取单张截图，输出单值。
    返回结果列表（同时写入 out_path）。
    """
    varieties = sorted(load_varieties(), key=lambda x: x["id"])
    cap = total_count or len(varieties)

    _check_dirs(main_dir, retail_dir)
    logger.info("初始化 OCR 引擎...")
    print("正在初始化 OCR ...")
    ocr = CnOcr(det_model_name="naive_det")

    results = []
    for v in varieties:
        vid = v["id"]
        if vid > cap:
            break
        key = v["key"]
        stem = f"contract_{vid:03d}.png"

        label_m = f"{key}/主力"
        label_r = f"{key}/散户"
        main_force, _ = ocr_single(ocr, main_dir / stem, label_m)
        retail, _     = ocr_single(ocr, retail_dir / stem, label_r)

        results.append({"id": vid, "key": key, "main_force": main_force, "retail": retail})
        print(f"  [{vid:03d}] {key}: 主力={main_force}  散户={retail}")

    _save_and_report_today(results, out_path)
    return results


# ── 历史模式 ──────────────────────────────────────────────────────────────────

def run_history(
    main_dir: Path,
    retail_dir: Path,
    out_path: Path,
    history_count: int = 30,
    total_count: int | None = None,
) -> list:
    """
    历史模式：每个品种读取 history_count 天的截图，
    main_force 和 retail 均输出为列表（下标0=day_001=最新）。
    返回结果列表（同时写入 out_path）。
    """
    varieties = sorted(load_varieties(), key=lambda x: x["id"])
    cap = total_count or len(varieties)

    _check_dirs(main_dir, retail_dir)
    logger.info("初始化 OCR 引擎，历史模式，%d 天", history_count)
    print(f"正在初始化 OCR ... (历史模式，{history_count} 天)")
    ocr = CnOcr(det_model_name="naive_det")

    results = []
    for v in varieties:
        vid = v["id"]
        if vid > cap:
            break
        key = v["key"]

        main_list, retail_list = [], []
        ok_m = ok_r = 0

        for day in range(1, history_count + 1):
            stem = f"contract_{vid:03d}_day_{day:03d}.png"
            label_m = f"{key}/主力/day{day:03d}"
            label_r = f"{key}/散户/day{day:03d}"
            val_m, _ = ocr_single(ocr, main_dir / stem, label_m)
            val_r, _ = ocr_single(ocr, retail_dir / stem, label_r)
            main_list.append(val_m)
            retail_list.append(val_r)
            if val_m is not None:
                ok_m += 1
            if val_r is not None:
                ok_r += 1
            print(f"  [{vid:03d}] {key} day{day:03d}: 主力={val_m}  散户={val_r}")

        results.append({"id": vid, "key": key, "main_force": main_list, "retail": retail_list})
        miss_m = history_count - ok_m
        miss_r = history_count - ok_r
        if miss_m or miss_r:
            logger.warning(
                "[%s] 识别缺失 - 主力 %d/%d，散户 %d/%d",
                key, ok_m, history_count, ok_r, history_count,
            )
        print(f"  >> [{vid:03d}] {key} 完成，主力 {ok_m}/{history_count}，散户 {ok_r}/{history_count}")

    _save_and_report_history(results, history_count, out_path)
    return results


# ── 内部工具 ──────────────────────────────────────────────────────────────────

def _check_dirs(main_dir: Path, retail_dir: Path):
    for d, name in [(main_dir, "主力资金"), (retail_dir, "散户资金")]:
        if not d.is_dir():
            logger.warning("%s 目录不存在: %s", name, d)
            print(f"警告：{name} 目录不存在: {d}")
        else:
            logger.info("%s 目录: %s", name, d)
            print(f"{name} 目录: {d}")


def _save_and_report_today(results: list, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    ok_m = sum(1 for r in results if r["main_force"] is not None)
    ok_r = sum(1 for r in results if r["retail"] is not None)
    total = len(results)
    logger.info("OCR 完成：主力 %d/%d，散户 %d/%d，输出: %s", ok_m, total, ok_r, total, out_path)
    print(f"\n完成！主力识别 {ok_m}/{total}，散户识别 {ok_r}/{total}")
    print(f"结果已保存至 {out_path}")


def _save_and_report_history(results: list, history_count: int, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    total_m = sum(sum(1 for x in r["main_force"] if x is not None) for r in results)
    total_r = sum(sum(1 for x in r["retail"] if x is not None) for r in results)
    total_cells = len(results) * history_count
    logger.info(
        "OCR 完成：主力 %d/%d，散户 %d/%d，输出: %s",
        total_m, total_cells, total_r, total_cells, out_path,
    )
    print(f"\n完成！主力识别 {total_m}/{total_cells}，散户识别 {total_r}/{total_cells}")
    print(f"结果已保存至 {out_path}")
