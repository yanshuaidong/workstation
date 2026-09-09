"""
异常信号检测器。

检测逻辑：
  - 基准窗口：过去 WINDOW_DAYS 个交易日（不含当日）
  - 算法：Z-Score 法，|z| > Z_THRESHOLD 时标记为异常
  - 涨跌幅额外规则：绝对值 > ABS_CHANGE_PCT_THRESHOLD 时也标记
  - 每个指标 UPSERT 到 anomaly_signals（同一天、同品种、同指标仅保留最新一条）

监控指标（5项）：
  change_pct     — 涨跌幅         来自 hist_{symbol}
  volume         — 成交量         来自 hist_{symbol}
  open_interest  — 持仓量         来自 hist_{symbol}
  main_force     — 大单/主力指数  来自 fut_strength
  retail         — 散单/散户指数  来自 fut_strength

运行：
  python -m trading.anomaly.detector [YYYY-MM-DD]
"""
from __future__ import annotations

import logging
import math
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from trading.strategies.db import get_connection

logger = logging.getLogger(__name__)

# ── 参数 ──────────────────────────────────────────────────────────────────────

WINDOW_DAYS = 20                   # 基准窗口（交易日数）
Z_THRESHOLD = 2.5                  # Z-Score 异常阈值
ABS_CHANGE_PCT_THRESHOLD = 4.0     # 涨跌幅绝对值阈值（%），超过即标记
MIN_STD = 1e-6                     # 防止除零


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def _mean_std(values: list[float]) -> tuple[float, float]:
    """计算均值和标准差（样本标准差）。"""
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    return mean, math.sqrt(variance)


def _z_score(current: float, mean: float, std: float) -> float:
    if std < MIN_STD:
        return 0.0
    return (current - mean) / std


def _direction(z: float) -> str:
    return "up" if z > 0 else "down"


def _description(metric: str, variety_name: str, current: float,
                 mean: float, std: float, z: float, is_abs: bool = False) -> str:
    labels = {
        "change_pct":    "涨跌幅",
        "volume":        "成交量",
        "open_interest": "持仓量",
        "main_force":    "大单指数",
        "retail":        "散单指数",
    }
    label = labels.get(metric, metric)
    unit = "%" if metric == "change_pct" else ""
    direction_cn = "偏高/放量" if z > 0 else "偏低/缩量"
    if metric == "change_pct":
        direction_cn = "大幅上涨" if z > 0 else "大幅下跌"
    if is_abs:
        return (
            f"{variety_name} {label}={current:.2f}{unit}，"
            f"绝对值超过阈值 {ABS_CHANGE_PCT_THRESHOLD}%（基准均值={mean:.2f}{unit}）"
        )
    return (
        f"{variety_name} {label}={current:.2f}{unit}，"
        f"较基准偏离 {z:+.2f}σ（{direction_cn}），"
        f"基准均值={mean:.2f}{unit}，σ={std:.2f}{unit}"
    )


# ── hist_* 指标检测（涨跌幅 / 成交量 / 持仓量） ──────────────────────────────

def detect_hist_anomalies(
    cursor,
    symbol: str,
    variety_id: int,
    variety_name: str,
    trade_date: str,
) -> list[dict]:
    """
    读取 hist_{symbol} 中当日 + 过去 WINDOW_DAYS 天数据，
    检测 change_pct / volume / open_interest 是否异常。

    返回异常记录列表（已达到写库格式）。
    """
    table = f"hist_{symbol.lower()}"

    # 获取当日数据
    try:
        cursor.execute(
            f"SELECT change_pct, volume, open_interest "
            f"FROM {table} WHERE trade_date=%s LIMIT 1",
            (trade_date,),
        )
    except Exception as e:
        logger.debug("hist 表 %s 不存在或查询失败: %s", table, e)
        return []

    today_row = cursor.fetchone()
    if not today_row:
        logger.debug("%s %s 无当日数据，跳过", symbol, trade_date)
        return []

    # 获取历史基准数据（过去 WINDOW_DAYS 天，不含当日）
    cursor.execute(
        f"SELECT change_pct, volume, open_interest FROM {table} "
        f"WHERE trade_date < %s ORDER BY trade_date DESC LIMIT %s",
        (trade_date, WINDOW_DAYS),
    )
    hist_rows = cursor.fetchall()

    if len(hist_rows) < 5:
        logger.debug("%s %s 历史数据不足（%d条），跳过", symbol, trade_date, len(hist_rows))
        return []

    anomalies = []

    metrics = [
        ("change_pct", today_row.get("change_pct")),
        ("volume", today_row.get("volume")),
        ("open_interest", today_row.get("open_interest")),
    ]

    for metric, current in metrics:
        if current is None:
            continue
        current = float(current)
        hist_vals = [float(r[metric]) for r in hist_rows if r.get(metric) is not None]
        if len(hist_vals) < 5:
            continue

        mean, std = _mean_std(hist_vals)
        z = _z_score(current, mean, std)

        is_anomaly = abs(z) > Z_THRESHOLD
        is_abs_anomaly = False

        # 涨跌幅额外检测：绝对值超阈值也标记
        if metric == "change_pct" and abs(current) > ABS_CHANGE_PCT_THRESHOLD:
            is_abs_anomaly = True

        if is_anomaly or is_abs_anomaly:
            anomalies.append({
                "signal_date": trade_date,
                "variety_id": variety_id,
                "variety_name": variety_name,
                "symbol": symbol,
                "metric": metric,
                "direction": _direction(z if not (is_abs_anomaly and not is_anomaly) else current),
                "current_value": current,
                "baseline_mean": round(mean, 4),
                "baseline_std": round(std, 4),
                "z_score": round(z, 4),
                "window_days": WINDOW_DAYS,
                "description": _description(metric, variety_name, current, mean, std, z, is_abs_anomaly and not is_anomaly),
            })

    return anomalies


# ── fut_strength 指标检测（主力/散单指数） ────────────────────────────────────

def detect_strength_anomalies(
    cursor,
    variety_id: int,
    variety_name: str,
    trade_date: str,
) -> list[dict]:
    """
    读取 fut_strength 中当日 + 过去 WINDOW_DAYS 天数据，
    检测 main_force / retail 是否异常。
    """
    # 当日数据
    cursor.execute(
        "SELECT main_force, retail FROM fut_strength "
        "WHERE variety_id=%s AND trade_date=%s LIMIT 1",
        (variety_id, trade_date),
    )
    today_row = cursor.fetchone()
    if not today_row:
        logger.debug("variety_id=%d %s 无当日 fut_strength 数据，跳过", variety_id, trade_date)
        return []

    # 历史基准数据
    cursor.execute(
        "SELECT main_force, retail FROM fut_strength "
        "WHERE variety_id=%s AND trade_date < %s ORDER BY trade_date DESC LIMIT %s",
        (variety_id, trade_date, WINDOW_DAYS),
    )
    hist_rows = cursor.fetchall()

    if len(hist_rows) < 5:
        logger.debug("variety_id=%d 历史 fut_strength 不足（%d条），跳过", variety_id, len(hist_rows))
        return []

    anomalies = []

    for metric in ("main_force", "retail"):
        current = today_row.get(metric)
        if current is None:
            continue
        current = float(current)
        hist_vals = [float(r[metric]) for r in hist_rows if r.get(metric) is not None]
        if len(hist_vals) < 5:
            continue

        mean, std = _mean_std(hist_vals)
        z = _z_score(current, mean, std)

        if abs(z) > Z_THRESHOLD:
            anomalies.append({
                "signal_date": trade_date,
                "variety_id": variety_id,
                "variety_name": variety_name,
                "symbol": None,
                "metric": metric,
                "direction": _direction(z),
                "current_value": current,
                "baseline_mean": round(mean, 4),
                "baseline_std": round(std, 4),
                "z_score": round(z, 4),
                "window_days": WINDOW_DAYS,
                "description": _description(metric, variety_name, current, mean, std, z),
            })

    return anomalies


# ── 写库 ─────────────────────────────────────────────────────────────────────

def _upsert_anomalies(cursor, anomalies: list[dict]) -> int:
    """将异常列表 UPSERT 到 anomaly_signals，返回写入行数。"""
    if not anomalies:
        return 0
    sql = """
        INSERT INTO anomaly_signals
            (signal_date, variety_id, variety_name, symbol,
             metric, direction, current_value,
             baseline_mean, baseline_std, z_score, window_days, description)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            direction     = VALUES(direction),
            current_value = VALUES(current_value),
            baseline_mean = VALUES(baseline_mean),
            baseline_std  = VALUES(baseline_std),
            z_score       = VALUES(z_score),
            window_days   = VALUES(window_days),
            description   = VALUES(description),
            created_at    = CURRENT_TIMESTAMP
    """
    count = 0
    for a in anomalies:
        cursor.execute(sql, (
            a["signal_date"], a["variety_id"], a["variety_name"], a["symbol"],
            a["metric"], a["direction"], a["current_value"],
            a["baseline_mean"], a["baseline_std"], a["z_score"],
            a["window_days"], a["description"],
        ))
        count += 1
    return count


# ── 全量检测入口 ──────────────────────────────────────────────────────────────

def run_anomaly_detection(trade_date: Optional[str] = None, conn=None) -> int:
    """
    遍历 fut_variety 所有品种，执行全量异常检测，写入 anomaly_signals。

    trade_date: 格式 'YYYY-MM-DD'，默认今日
    conn      : 可复用已有连接，传 None 则自动创建并关闭

    返回：本次写入的异常信号总条数
    """
    if trade_date is None:
        trade_date = date.today().isoformat()

    _own = conn is None
    if _own:
        conn = get_connection()

    total = 0
    try:
        # 确保表存在
        from trading.anomaly.create_table import ensure_table
        ensure_table(conn)

        with conn.cursor() as cur:
            # 取所有有 contracts_symbol 的品种
            cur.execute(
                "SELECT id, name, contracts_symbol FROM fut_variety "
                "WHERE contracts_symbol IS NOT NULL AND contracts_symbol != ''"
            )
            varieties = cur.fetchall()

        logger.info("开始异常检测，日期=%s，品种数=%d", trade_date, len(varieties))

        with conn.cursor() as cur:
            for row in varieties:
                vid = int(row["id"])
                vname = row["name"]
                symbol = row["contracts_symbol"]

                anomalies: list[dict] = []

                # hist 指标
                try:
                    anomalies += detect_hist_anomalies(cur, symbol, vid, vname, trade_date)
                except Exception as e:
                    logger.warning("hist 检测失败 %s: %s", vname, e)

                # strength 指标
                try:
                    anomalies += detect_strength_anomalies(cur, vid, vname, trade_date)
                except Exception as e:
                    logger.warning("strength 检测失败 %s: %s", vname, e)

                if anomalies:
                    cnt = _upsert_anomalies(cur, anomalies)
                    total += cnt
                    logger.info("  %s → %d 条异常（%s）",
                                vname, cnt,
                                ", ".join(a["metric"] for a in anomalies))

        conn.commit()
        logger.info("异常检测完成，共写入 %d 条", total)
    except Exception as e:
        logger.error("异常检测运行错误: %s", e, exc_info=True)
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        if _own:
            conn.close()

    return total


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    arg_date = sys.argv[1] if len(sys.argv) > 1 else None
    if arg_date:
        try:
            datetime.strptime(arg_date, "%Y-%m-%d")
        except ValueError:
            print(f"日期格式错误：{arg_date}，应为 YYYY-MM-DD")
            sys.exit(1)
    n = run_anomaly_detection(arg_date)
    print(f"完成，共写入 {n} 条异常信号")
