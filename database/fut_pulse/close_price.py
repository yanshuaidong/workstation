"""期货收盘价同步工具。"""

from __future__ import annotations

import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable

from database.init_tables import connect, ensure_required_tables
from uploader.mysql import sync_varieties

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
VARIETIES_PATH = BASE_DIR / "config" / "varieties.json"

MAX_RETRIES = 3
RETRY_SLEEP_RANGE = (0.8, 1.5)

CLOSE_API_SYMBOL_MAP = {
    "im": "I0",
    "rbm": "RB0",
    "hcm": "HC0",
    "smm": "SM0",
    "cum": "CU0",
    "alm": "AL0",
    "znm": "ZN0",
    "pbm": "PB0",
    "snm": "SN0",
    "sim": "SI0",
    "psm": "PS0",
    "lcm": "LC0",
    "aum": "AU0",
    "am": "A0",
    "bm": "B0",
    "ym": "Y0",
    "mm": "M0",
    "oim": "OI0",
    "rmm": "RM0",
    "pm": "P0",
    "cm": "C0",
    "jdm": "JD0",
    "cfm": "CF0",
    "srm": "SR0",
    "apm": "AP0",
    "cjm": "CJ0",
    "pkm": "PK0",
    "tam": "TA0",
    "pxm": "PX0",
    "ppm": "PP0",
    "ebm": "EB0",
    "bzm": "BZ0",
    "shm": "SH0",
    "urm": "UR0",
    "rum": "RU0",
    "brm": "BR0",
    "lgm": "LG0",
    "spm": "SP0",
    "ihm": "IH0",
    "aom": "AO0",
    "nim": "NI0",
    "agm": "AG0",
    "lhm": "LH0",
    "fum": "FU0",
    "lum": "LU0",
    "mam": "MA0",
    "vm": "V0",
    "sam": "SA0",
    "fgm": "FG0",
    "lm": "L0",
    "egm": "EG0",
    "bum": "BU0",
    "pgm": "PG0",
    "jmm": "JM0",
    "ecm": "EC0",
}


def load_varieties() -> list[dict]:
    """读取 fut_pulse 品种配置。"""
    with open(VARIETIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_symbol_filter(symbols: str | Iterable[str] | None) -> set[str]:
    """统一解析品种过滤参数。"""
    if symbols is None:
        return set()
    if isinstance(symbols, str):
        raw_items = symbols.split(",")
    else:
        raw_items = list(symbols)
    return {str(item).strip().lower() for item in raw_items if str(item).strip()}


def filter_varieties(varieties: list[dict], symbols: str | Iterable[str] | None = None) -> list[dict]:
    """按 key 过滤品种。"""
    symbols_set = parse_symbol_filter(symbols)
    if not symbols_set:
        return list(varieties)

    available = {item["key"].lower() for item in varieties}
    missing = sorted(symbols_set - available)
    if missing:
        raise ValueError(f"未在 varieties.json 中找到品种: {', '.join(missing)}")

    return [item for item in varieties if item["key"].lower() in symbols_set]


def validate_fixed_map(varieties: list[dict]) -> None:
    """校验固定映射表覆盖当前品种清单。"""
    missing = [item["key"] for item in varieties if item["key"].lower() not in CLOSE_API_SYMBOL_MAP]
    if missing:
        raise RuntimeError(
            "close 固定映射缺失以下品种，请先补齐 CLOSE_API_SYMBOL_MAP: "
            + ", ".join(missing)
        )


def normalize_trade_dates(trade_dates: Iterable[str]) -> list[str]:
    """去重并保留原顺序。"""
    normalized: list[str] = []
    seen = set()
    for item in trade_dates:
        trade_date = str(item).strip()[:10]
        if not trade_date or trade_date in seen:
            continue
        normalized.append(trade_date)
        seen.add(trade_date)
    if not normalized:
        raise ValueError("缺少目标交易日")
    return normalized


def _import_market_libs():
    try:
        import akshare as ak
    except ImportError as exc:  # pragma: no cover - 依赖缺失时走运行时保护
        raise RuntimeError("缺少 akshare，请先在 fut_pulse 环境中安装依赖。") from exc

    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - akshare 通常会带 pandas
        raise RuntimeError("缺少 pandas，请先在 fut_pulse 环境中安装依赖。") from exc

    return ak, pd


def safe_float(value, default=None):
    """兼容字符串和空值的浮点转换。"""
    if value is None:
        return default
    if isinstance(value, str):
        value = value.strip()
        if value in ("", "-", "None", "null"):
            return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fetch_main_history_df(api_symbol: str, max_retries: int = MAX_RETRIES):
    """从 AkShare 拉取主连历史收盘价。"""
    ak, pd = _import_market_libs()
    col_map = {
        "日期": "trade_date",
        "开盘价": "open_price",
        "最高价": "high_price",
        "最低价": "low_price",
        "收盘价": "close_price",
        "成交量": "volume",
        "持仓量": "open_interest",
    }

    for attempt in range(1, max_retries + 1):
        try:
            df = ak.futures_main_sina(symbol=api_symbol)
            if df is None or df.empty:
                return None

            rename_map = {k: v for k, v in col_map.items() if k in df.columns}
            df = df.rename(columns=rename_map).copy()
            if "trade_date" not in df.columns or "close_price" not in df.columns:
                return None

            df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y-%m-%d")
            return df
        except Exception as exc:
            if attempt < max_retries:
                wait_secs = 2 ** attempt + random.uniform(0.5, 1.5)
                logger.warning(
                    "AkShare 拉取 %s 失败（第 %d 次）: %s，%.1fs 后重试",
                    api_symbol, attempt, exc, wait_secs,
                )
                time.sleep(wait_secs)
            else:
                raise RuntimeError(f"AkShare 拉取 {api_symbol} 失败（已重试 {max_retries} 次）：{exc}") from exc
    return None


def _extract_close_rows(df_hist, trade_dates: list[str], variety_id: int):
    target_dates = set(trade_dates)
    date_to_close: dict[str, float] = {}

    for _, row in df_hist.iterrows():
        trade_date = str(row.get("trade_date", "")).strip()[:10]
        if trade_date not in target_dates:
            continue
        close_price = safe_float(row.get("close_price"))
        if close_price is None:
            continue
        date_to_close[trade_date] = close_price

    rows = [(variety_id, trade_date, date_to_close[trade_date]) for trade_date in trade_dates if trade_date in date_to_close]
    missing_dates = [trade_date for trade_date in trade_dates if trade_date not in date_to_close]
    return rows, missing_dates


def upsert_close_rows(conn, rows: list[tuple[int, str, float]], collected_at: str | None = None) -> dict[str, int]:
    """写入 fut_daily_close，已存在则更新。"""
    if collected_at is None:
        collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sql = """
        INSERT INTO fut_daily_close
            (variety_id, trade_date, close_price, collected_at)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            close_price = VALUES(close_price),
            collected_at = VALUES(collected_at)
    """

    inserted = updated = unchanged = 0
    with conn.cursor() as cur:
        for variety_id, trade_date, close_price in rows:
            affected = cur.execute(sql, (variety_id, trade_date, close_price, collected_at))
            if affected == 1:
                inserted += 1
            elif affected == 2:
                updated += 1
            else:
                unchanged += 1
    conn.commit()
    return {"inserted": inserted, "updated": updated, "unchanged": unchanged}


def sync_close_prices(
    trade_dates: Iterable[str],
    varieties: list[dict] | None = None,
    symbols: str | Iterable[str] | None = None,
    dry_run: bool = False,
) -> dict:
    """同步指定交易日的收盘价到 fut_daily_close。"""
    normalized_dates = normalize_trade_dates(trade_dates)
    all_varieties = load_varieties() if varieties is None else list(varieties)
    selected_varieties = filter_varieties(all_varieties, symbols)
    if not selected_varieties:
        raise RuntimeError("没有可同步的品种，请检查 varieties.json 或 --symbol 参数。")
    validate_fixed_map(selected_varieties)

    logger.info(
        "开始同步 fut_daily_close：日期=%s，品种数=%d，dry_run=%s",
        ",".join(normalized_dates), len(selected_varieties), dry_run,
    )

    if dry_run:
        print(
            f"[dry-run] 将同步 fut_daily_close：{len(selected_varieties)} 个品种，"
            f"{len(normalized_dates)} 个交易日。"
        )
        return {
            "trade_dates": normalized_dates,
            "selected_count": len(selected_varieties),
            "dry_run": True,
            "failures": [],
        }

    conn = connect()
    failures: list[str] = []
    total_inserted = total_updated = total_unchanged = 0
    try:
        ensure_required_tables(conn)
        sync_varieties(conn, selected_varieties)

        total = len(selected_varieties)
        for idx, item in enumerate(selected_varieties, 1):
            key = item["key"].lower()
            label = f"{item['key']}({item['name']})"
            api_symbol = CLOSE_API_SYMBOL_MAP[key]

            try:
                df_hist = fetch_main_history_df(api_symbol)
                if df_hist is None or df_hist.empty:
                    raise RuntimeError("AkShare 无返回数据")

                rows, missing_dates = _extract_close_rows(df_hist, normalized_dates, int(item["id"]))
                if not rows:
                    raise RuntimeError(f"目标交易日均无 close 数据：{', '.join(normalized_dates)}")

                result = upsert_close_rows(conn, rows)
                total_inserted += result["inserted"]
                total_updated += result["updated"]
                total_unchanged += result["unchanged"]

                logger.info(
                    "[%d/%d] %s close 同步完成：新增 %d，更新 %d，未变化 %d",
                    idx, total, label, result["inserted"], result["updated"], result["unchanged"],
                )
                if missing_dates:
                    failures.append(f"{label} 缺少日期数据: {', '.join(missing_dates)}")
                    logger.warning("[%d/%d] %s 缺少日期数据: %s", idx, total, label, ",".join(missing_dates))
            except Exception as exc:
                failures.append(f"{label} 同步失败: {exc}")
                logger.warning("[%d/%d] %s 同步失败: %s", idx, total, label, exc)

            if idx < total:
                time.sleep(random.uniform(*RETRY_SLEEP_RANGE))
    finally:
        conn.close()

    print(
        "close 价格同步完成："
        f"新增 {total_inserted} 条，更新 {total_updated} 条，未变化 {total_unchanged} 条。"
    )
    if failures:
        print("以下项目需要补查：")
        for item in failures:
            print(f"  - {item}")
        raise RuntimeError("fut_daily_close 同步存在失败项，请查看日志或稍后重试。")

    return {
        "trade_dates": normalized_dates,
        "selected_count": len(selected_varieties),
        "inserted": total_inserted,
        "updated": total_updated,
        "unchanged": total_unchanged,
        "failures": failures,
    }


def run_close_history(
    days: int | None = None,
    start: str | None = None,
    end: str | None = None,
    symbols: str | Iterable[str] | None = None,
    dry_run: bool = False,
) -> dict:
    """历史 close 回填入口。"""
    from pipeline import generate_trade_dates, setup_logging

    run_tag = f"close_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    setup_logging(run_tag)
    logger.info("========== close-history 模式 [%s] ==========", run_tag)

    trade_dates = generate_trade_dates(days=days, start=start, end=end)
    if not trade_dates:
        raise RuntimeError("指定范围内没有交易日，无法回填 fut_daily_close。")
    logger.info("close-history 交易日: %s ~ %s，共 %d 天", trade_dates[-1], trade_dates[0], len(trade_dates))
    print(f"\nclose-history 交易日期：{trade_dates[-1]} ~ {trade_dates[0]}，共 {len(trade_dates)} 天")

    return sync_close_prices(
        trade_dates=trade_dates,
        symbols=symbols,
        dry_run=dry_run,
    )
