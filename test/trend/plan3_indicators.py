"""
计划3：基于结论2的量化信号指标发明与趋势收益检验

7 个量化信号指标，每个都包含 LONG / SHORT 对称版本。
统一在信号触发日收盘价开仓，测量持有 3/5/10 天后的收益率与胜率。
"""

import json
import sqlite3
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False

BASE_DIR = Path(__file__).parent
DB_PATH  = BASE_DIR / "local_fut_pulse.sqlite"
OUTPUT_DIR = BASE_DIR / "output3"
OUTPUT_DIR.mkdir(exist_ok=True)

with open(BASE_DIR / "varieties.json", "r", encoding="utf-8") as f:
    VARIETIES = {v["id"]: v["name"] for v in json.load(f)}

SECTOR_MAP = {
    "黑色系":   ["铁矿石", "螺纹钢", "热卷", "锰硅", "焦煤"],
    "有色金属": ["沪铜", "沪铝", "沪锌", "沪铅", "沪锡", "沪镍", "沪金", "沪银",
                "氧化铝", "工业硅", "碳酸锂", "多晶硅"],
    "能源化工": ["PTA", "对二甲苯", "聚丙烯", "苯乙烯", "纯苯", "烧碱", "尿素",
                "橡胶", "丁二烯胶", "甲醇", "PVC", "纯碱", "玻璃", "塑料",
                "乙二醇", "沥青", "LPG", "燃油", "低硫燃油"],
    "农产品":   ["豆一", "豆二", "豆油", "豆粕", "菜油", "菜粕", "棕榈油", "玉米",
                "鸡蛋", "棉花", "白糖", "苹果", "红枣", "花生", "生猪"],
    "其他":     ["纸浆", "原木", "上证", "欧线集运"],
}
NAME_TO_SECTOR = {}
for _sec, _names in SECTOR_MAP.items():
    for _n in _names:
        NAME_TO_SECTOR[_n] = _sec

HOLD_DAYS = [3, 5, 10]
RANDOM_SAMPLES = 2000  # 随机基准抽样次数


# ═══════════════════════════════════════════════════════════════
# 数据加载
# ═══════════════════════════════════════════════════════════════

def load_data() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    sql = """
    SELECT s.variety_id, s.trade_date, s.main_force, s.retail, c.close_price
    FROM fut_strength s
    INNER JOIN fut_daily_close c
        ON s.variety_id = c.variety_id AND s.trade_date = c.trade_date
    ORDER BY s.variety_id, s.trade_date
    """
    df = pd.read_sql(sql, conn)
    conn.close()
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df["variety_name"] = df["variety_id"].map(VARIETIES)
    df["sector"] = df["variety_name"].map(NAME_TO_SECTOR).fillna("其他")
    return df


# ═══════════════════════════════════════════════════════════════
# 收益率计算工具
# ═══════════════════════════════════════════════════════════════

def compute_forward_returns(g: pd.DataFrame, signal_idx: int, direction: str) -> dict:
    """
    计算信号触发日 (signal_idx) 对应的 3/5/10 天持有收益率。
    direction: "LONG" or "SHORT"
    若未来数据不足则返回 NaN。
    """
    entry = g["close_price"].iloc[signal_idx]
    result = {}
    for n in HOLD_DAYS:
        future_idx = signal_idx + n
        if future_idx >= len(g):
            result[f"return_{n}d"] = np.nan
            result[f"win_{n}d"]    = np.nan
        else:
            future = g["close_price"].iloc[future_idx]
            raw_ret = (future - entry) / entry
            ret = raw_ret if direction == "LONG" else -raw_ret
            result[f"return_{n}d"] = ret
            result[f"win_{n}d"]    = 1.0 if ret > 0 else 0.0
    return result


def make_record(variety_id, variety_name, sector, signal_date, direction,
                indicator_name, indicator_value, returns: dict) -> dict:
    rec = {
        "variety_id":      variety_id,
        "variety_name":    variety_name,
        "sector":          sector,
        "signal_date":     signal_date,
        "direction":       direction,
        "indicator_name":  indicator_name,
        "indicator_value": indicator_value,
    }
    rec.update(returns)
    return rec


def get_zone(value: float, p10: float, p20: float, p80: float, p90: float) -> str:
    if value < p10:
        return "极端负值"
    elif value < p20:
        return "负值区低"
    elif value < p80:
        return "中性区"
    elif value < p90:
        return "正值区高"
    else:
        return "极端正值"


# ═══════════════════════════════════════════════════════════════
# 指标1：MF_Edge3 — 主力底部/顶部3连变信号
# ═══════════════════════════════════════════════════════════════

def generate_mf_edge3(g: pd.DataFrame) -> list[dict]:
    """
    LONG：main_force 严格3连升
    SHORT：main_force 严格3连降
    衍生分组：起始位置的区域（极端边缘 vs 中性）
    """
    mf = g["main_force"].values
    p10 = np.percentile(mf, 10)
    p20 = np.percentile(mf, 20)
    p50 = np.percentile(mf, 50)
    p80 = np.percentile(mf, 80)
    p90 = np.percentile(mf, 90)

    records = []
    vid   = g["variety_id"].iloc[0]
    name  = g["variety_name"].iloc[0]
    sec   = g["sector"].iloc[0]

    for i in range(2, len(g)):
        v0, v1, v2 = mf[i-2], mf[i-1], mf[i]

        for direction, is_signal in [
            ("LONG",  v0 < v1 < v2),  # 严格3连升
            ("SHORT", v0 > v1 > v2),  # 严格3连降
        ]:
            if not is_signal:
                continue

            start_val = v0
            if direction == "LONG":
                if start_val < p10:
                    zone = "极端底部"
                elif start_val < p50:
                    zone = "普通底部"
                else:
                    zone = "中性偏高"
            else:  # SHORT
                if start_val > p90:
                    zone = "极端顶部"
                elif start_val > p50:
                    zone = "普通顶部"
                else:
                    zone = "中性偏低"

            indicator_value = f"{zone}"
            rets = compute_forward_returns(g, i, direction)
            records.append(make_record(
                vid, name, sec,
                g["trade_date"].iloc[i], direction,
                "MF_Edge3", indicator_value, rets
            ))
    return records


# ═══════════════════════════════════════════════════════════════
# 指标2：MF_Accel — 趋势加速度信号
# ═══════════════════════════════════════════════════════════════

def generate_mf_accel(g: pd.DataFrame) -> list[dict]:
    """
    在3连变基础上，测量第2步变化幅度是否大于第1步（加速 vs 减速）。
    indicator_value 存储加速度数值 delta2 - delta1 的绝对值差。
    """
    mf = g["main_force"].values
    records = []
    vid  = g["variety_id"].iloc[0]
    name = g["variety_name"].iloc[0]
    sec  = g["sector"].iloc[0]

    for i in range(2, len(g)):
        v0, v1, v2 = mf[i-2], mf[i-1], mf[i]
        delta1 = v1 - v0
        delta2 = v2 - v1

        # 需要同向
        if delta1 * delta2 <= 0:
            continue
        if abs(delta1) == 0:
            continue

        direction = "LONG" if delta1 > 0 else "SHORT"
        # 加速度：第2步幅度是否更大
        accel = abs(delta2) - abs(delta1)
        accel_type = "加速" if accel > 0 else "减速"
        indicator_value = f"{accel_type}({accel:+.2f})"

        rets = compute_forward_returns(g, i, direction)
        records.append(make_record(
            vid, name, sec,
            g["trade_date"].iloc[i], direction,
            "MF_Accel", indicator_value, rets
        ))
    return records


# ═══════════════════════════════════════════════════════════════
# 指标3：MF_Duration — 趋势持续天数信号（D3/D5/D7）
# ═══════════════════════════════════════════════════════════════

def generate_mf_duration(g: pd.DataFrame) -> list[dict]:
    """
    在第 n 天（n=3/5/7）确认连续 n 天同向后开仓。
    indicator_value = "D3" / "D5" / "D7"
    同一连续趋势只在刚好满足 3天、5天、7天时各触发一次（不重复）。
    """
    mf = g["main_force"].values
    records = []
    vid  = g["variety_id"].iloc[0]
    name = g["variety_name"].iloc[0]
    sec  = g["sector"].iloc[0]

    for i in range(1, len(g)):
        # 当前 delta
        if mf[i] == mf[i-1]:
            continue
        cur_dir = 1 if mf[i] > mf[i-1] else -1

        # 统计从 i 往前有多少连续同向
        streak = 1
        j = i - 1
        while j > 0 and ((mf[j] - mf[j-1]) * cur_dir > 0):
            streak += 1
            j -= 1

        if streak in (3, 5, 7):
            direction = "LONG" if cur_dir > 0 else "SHORT"
            rets = compute_forward_returns(g, i, direction)
            records.append(make_record(
                vid, name, sec,
                g["trade_date"].iloc[i], direction,
                "MF_Duration", f"D{streak}", rets
            ))
    return records


# ═══════════════════════════════════════════════════════════════
# 指标4：MS_Divergence — 主散背离共振信号
# ═══════════════════════════════════════════════════════════════

def generate_ms_divergence(g: pd.DataFrame) -> list[dict]:
    """
    LONG：主力3连升 + 散户同期均值下降
    SHORT：主力3连降 + 散户同期均值上升
    indicator_value 存储背离强度分数。
    """
    mf = g["main_force"].values
    rt = g["retail"].values
    records = []
    vid  = g["variety_id"].iloc[0]
    name = g["variety_name"].iloc[0]
    sec  = g["sector"].iloc[0]

    for i in range(2, len(g)):
        v0, v1, v2 = mf[i-2], mf[i-1], mf[i]

        if v0 < v1 < v2:
            direction = "LONG"
            mf_delta = ((v1 - v0) + (v2 - v1)) / 2  # 主力平均升速
        elif v0 > v1 > v2:
            direction = "SHORT"
            mf_delta = ((v0 - v1) + (v1 - v2)) / 2  # 做空方向主力平均降速
        else:
            continue

        # 散户同期变化方向
        rt_delta_avg = ((rt[i-1] - rt[i-2]) + (rt[i] - rt[i-1])) / 2

        if direction == "LONG":
            # 散户下降才是背离
            if rt_delta_avg < 0:
                divergence_type = "强共振"
            else:
                divergence_type = "弱共振" if rt_delta_avg > 0 else "中性"
        else:  # SHORT
            # 散户上升才是背离
            if rt_delta_avg > 0:
                divergence_type = "强共振"
            else:
                divergence_type = "弱共振" if rt_delta_avg < 0 else "中性"

        divergence_score = mf_delta + abs(rt_delta_avg)
        indicator_value = f"{divergence_type}({divergence_score:.2f})"

        rets = compute_forward_returns(g, i, direction)
        records.append(make_record(
            vid, name, sec,
            g["trade_date"].iloc[i], direction,
            "MS_Divergence", indicator_value, rets
        ))
    return records


# ═══════════════════════════════════════════════════════════════
# 指标5：MF_Magnitude — 主力趋势总幅度门槛信号
# ═══════════════════════════════════════════════════════════════

def generate_mf_magnitude(g: pd.DataFrame) -> list[dict]:
    """
    在3连变基础上，按变化总幅度（绝对值）分三档（高/中/低）。
    """
    mf = g["main_force"].values
    records = []
    vid  = g["variety_id"].iloc[0]
    name = g["variety_name"].iloc[0]
    sec  = g["sector"].iloc[0]

    # 先计算所有可能的3连变幅度分布，用于确定分位数门槛
    all_magnitudes = []
    for i in range(2, len(g)):
        v0, v2 = mf[i-2], mf[i]
        if abs(v2 - v0) > 0:
            all_magnitudes.append(abs(v2 - v0))

    if len(all_magnitudes) < 4:
        return records

    p25 = np.percentile(all_magnitudes, 25)
    p75 = np.percentile(all_magnitudes, 75)

    for i in range(2, len(g)):
        v0, v1, v2 = mf[i-2], mf[i-1], mf[i]

        # 严格3连同向
        if not (v0 < v1 < v2 or v0 > v1 > v2):
            continue

        direction = "LONG" if v2 > v0 else "SHORT"
        magnitude = abs(v2 - v0)

        if magnitude >= p75:
            mag_type = "高幅度"
        elif magnitude >= p25:
            mag_type = "中幅度"
        else:
            mag_type = "低幅度"

        rets = compute_forward_returns(g, i, direction)
        records.append(make_record(
            vid, name, sec,
            g["trade_date"].iloc[i], direction,
            "MF_Magnitude", f"{mag_type}({magnitude:.2f})", rets
        ))
    return records


# ═══════════════════════════════════════════════════════════════
# 指标6：MF_BreakZone — 主力区域突破信号
# ═══════════════════════════════════════════════════════════════

def generate_mf_breakzone(g: pd.DataFrame) -> list[dict]:
    """
    LONG：main_force 从极端负值区（<p10）3连升后穿越 p10 边界
    SHORT：main_force 从极端正值区（>p90）3连降后跌穿 p90 边界
    对照组（同区域内3连变，未穿越边界）也一并记录。
    """
    mf = g["main_force"].values
    p10 = np.percentile(mf, 10)
    p90 = np.percentile(mf, 90)
    records = []
    vid  = g["variety_id"].iloc[0]
    name = g["variety_name"].iloc[0]
    sec  = g["sector"].iloc[0]

    for i in range(2, len(g)):
        v0, v1, v2 = mf[i-2], mf[i-1], mf[i]

        if v0 < v1 < v2:
            direction = "LONG"
            # 判断是否从极端负值区升穿 p10
            if v0 < p10 and v2 >= p10:
                zone_type = "穿越底部边界"
            elif v0 < p10 and v2 < p10:
                zone_type = "极端区内震荡"
            else:
                zone_type = "普通区间3连升"

        elif v0 > v1 > v2:
            direction = "SHORT"
            # 判断是否从极端正值区跌穿 p90
            if v0 > p90 and v2 <= p90:
                zone_type = "穿越顶部边界"
            elif v0 > p90 and v2 > p90:
                zone_type = "极端区内震荡"
            else:
                zone_type = "普通区间3连降"
        else:
            continue

        rets = compute_forward_returns(g, i, direction)
        records.append(make_record(
            vid, name, sec,
            g["trade_date"].iloc[i], direction,
            "MF_BreakZone", zone_type, rets
        ))
    return records


# ═══════════════════════════════════════════════════════════════
# 指标7：Composite_Score — 综合评分信号
# ═══════════════════════════════════════════════════════════════

def generate_composite_score(g: pd.DataFrame) -> list[dict]:
    """
    综合评分：
      持续天数（3=1, 5=2, 7+=3）× 30%
      加速度（加速=1）          × 20%
      边缘区启动（极端=2, 边缘=1）× 20%
      主散背离（反向=1）         × 20%
      幅度强度（高=2, 中=1, 低=0）× 10%
    """
    mf = g["main_force"].values
    rt = g["retail"].values
    p10 = np.percentile(mf, 10)
    p20 = np.percentile(mf, 20)
    p50 = np.percentile(mf, 50)
    p80 = np.percentile(mf, 80)
    p90 = np.percentile(mf, 90)

    all_mags = [abs(mf[i] - mf[i-2]) for i in range(2, len(g)) if abs(mf[i] - mf[i-2]) > 0]
    mag_p25 = np.percentile(all_mags, 25) if all_mags else 0
    mag_p75 = np.percentile(all_mags, 75) if all_mags else 0

    records = []
    vid  = g["variety_id"].iloc[0]
    name = g["variety_name"].iloc[0]
    sec  = g["sector"].iloc[0]

    for i in range(1, len(g)):
        if mf[i] == mf[i-1]:
            continue
        cur_dir = 1 if mf[i] > mf[i-1] else -1

        # 统计连续同向天数
        streak = 1
        j = i - 1
        while j > 0 and ((mf[j] - mf[j-1]) * cur_dir > 0):
            streak += 1
            j -= 1
        if streak < 3:
            continue

        direction = "LONG" if cur_dir > 0 else "SHORT"

        # 1. 持续天数得分
        if streak >= 7:
            dur_score = 3
        elif streak >= 5:
            dur_score = 2
        else:
            dur_score = 1

        # 2. 加速度得分（用最后2步）
        if i >= 2:
            d1 = abs(mf[i-1] - mf[i-2])
            d2 = abs(mf[i]   - mf[i-1])
            accel_score = 1 if d2 > d1 else 0
        else:
            accel_score = 0

        # 3. 边缘区启动得分（起始点 = j+1 处的 main_force）
        start_val = mf[j + 1] if (j + 1) < len(mf) else mf[0]
        if direction == "LONG":
            if start_val < p10:
                edge_score = 2
            elif start_val < p20:
                edge_score = 1
            else:
                edge_score = 0
        else:  # SHORT
            if start_val > p90:
                edge_score = 2
            elif start_val > p80:
                edge_score = 1
            else:
                edge_score = 0

        # 4. 主散背离得分
        if i >= 2:
            rt_delta = rt[i] - rt[i-1]
            if direction == "LONG" and rt_delta < 0:
                div_score = 1
            elif direction == "SHORT" and rt_delta > 0:
                div_score = 1
            else:
                div_score = 0
        else:
            div_score = 0

        # 5. 幅度强度得分（用3天窗口幅度）
        if i >= 2:
            mag = abs(mf[i] - mf[i-2])
            if mag >= mag_p75:
                mag_score = 2
            elif mag >= mag_p25:
                mag_score = 1
            else:
                mag_score = 0
        else:
            mag_score = 0

        score = (dur_score * 0.30 + accel_score * 0.20 +
                 edge_score * 0.20 + div_score  * 0.20 +
                 mag_score  * 0.10)

        rets = compute_forward_returns(g, i, direction)
        records.append(make_record(
            vid, name, sec,
            g["trade_date"].iloc[i], direction,
            "Composite_Score", f"{score:.2f}", rets
        ))
    return records


# ═══════════════════════════════════════════════════════════════
# 信号汇总与随机基准
# ═══════════════════════════════════════════════════════════════

GENERATORS = [
    generate_mf_edge3,
    generate_mf_accel,
    generate_mf_duration,
    generate_ms_divergence,
    generate_mf_magnitude,
    generate_mf_breakzone,
    generate_composite_score,
]


def generate_all_signals(df: pd.DataFrame) -> pd.DataFrame:
    all_records = []
    for vid, g in df.groupby("variety_id"):
        g = g.sort_values("trade_date").reset_index(drop=True)
        for gen_fn in GENERATORS:
            all_records.extend(gen_fn(g))
    return pd.DataFrame(all_records)


def generate_random_baseline(df: pd.DataFrame, n_samples: int = RANDOM_SAMPLES) -> pd.DataFrame:
    """随机选取买入日期，统计3/5/10天收益分布（随机做多）。"""
    rng = np.random.default_rng(42)
    records = []
    for vid, g in df.groupby("variety_id"):
        g = g.sort_values("trade_date").reset_index(drop=True)
        max_idx = len(g) - max(HOLD_DAYS) - 1
        if max_idx < 1:
            continue
        sampled = rng.integers(0, max_idx, size=n_samples // df["variety_id"].nunique() + 1)
        for idx in sampled:
            rets = compute_forward_returns(g, int(idx), "LONG")
            records.append(rets)
    return pd.DataFrame(records)


# ═══════════════════════════════════════════════════════════════
# 评估框架
# ═══════════════════════════════════════════════════════════════

def evaluate_signals(signals: pd.DataFrame) -> pd.DataFrame:
    """对每个 (indicator_name, direction) 组合计算汇总统计。"""
    rows = []
    for (ind, direc), grp in signals.groupby(["indicator_name", "direction"]):
        row = {"indicator_name": ind, "direction": direc, "n_signals": len(grp)}
        for n in HOLD_DAYS:
            ret_col = f"return_{n}d"
            win_col = f"win_{n}d"
            valid = grp[ret_col].dropna()
            wins  = grp[win_col].dropna()
            if len(valid) == 0:
                row[f"n_{n}d"]       = 0
                row[f"winrate_{n}d"] = np.nan
                row[f"mean_{n}d"]    = np.nan
                row[f"median_{n}d"]  = np.nan
                row[f"pnl_ratio_{n}d"] = np.nan
                row[f"max_loss_{n}d"]  = np.nan
                row[f"pvalue_{n}d"]    = np.nan
            else:
                gains  = valid[valid > 0]
                losses = valid[valid < 0]
                pnl    = (gains.mean() / abs(losses.mean())) if len(losses) > 0 and losses.mean() != 0 else np.nan
                t_stat, p_val = stats.ttest_1samp(valid, 0)
                row[f"n_{n}d"]          = len(valid)
                row[f"winrate_{n}d"]    = wins.mean()
                row[f"mean_{n}d"]       = valid.mean()
                row[f"median_{n}d"]     = valid.median()
                row[f"pnl_ratio_{n}d"]  = pnl
                row[f"max_loss_{n}d"]   = valid.min()
                row[f"pvalue_{n}d"]     = p_val
        rows.append(row)
    return pd.DataFrame(rows)


def evaluate_by_subgroup(signals: pd.DataFrame) -> pd.DataFrame:
    """按 indicator_name × direction × indicator_value（分组标签）做细分统计。"""
    rows = []
    for (ind, direc, val), grp in signals.groupby(
            ["indicator_name", "direction", "indicator_value"]):
        row = {"indicator_name": ind, "direction": direc,
               "subgroup": val, "n_signals": len(grp)}
        for n in HOLD_DAYS:
            valid = grp[f"return_{n}d"].dropna()
            wins  = grp[f"win_{n}d"].dropna()
            row[f"n_{n}d"]       = len(valid)
            row[f"winrate_{n}d"] = wins.mean() if len(wins) else np.nan
            row[f"mean_{n}d"]    = valid.mean() if len(valid) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def long_short_symmetry(summary: pd.DataFrame) -> pd.DataFrame:
    """对比每个指标的 LONG/SHORT 胜率差。"""
    long_  = summary[summary["direction"] == "LONG"].set_index("indicator_name")
    short_ = summary[summary["direction"] == "SHORT"].set_index("indicator_name")
    rows = []
    for ind in long_.index.intersection(short_.index):
        row = {"indicator_name": ind}
        for n in HOLD_DAYS:
            lw = long_.loc[ind, f"winrate_{n}d"]
            sw = short_.loc[ind, f"winrate_{n}d"]
            row[f"long_winrate_{n}d"]  = lw
            row[f"short_winrate_{n}d"] = sw
            row[f"diff_{n}d"]          = lw - sw if (not np.isnan(lw) and not np.isnan(sw)) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def compute_random_baseline_stats(baseline: pd.DataFrame) -> dict:
    result = {}
    for n in HOLD_DAYS:
        col = f"return_{n}d"
        valid = baseline[col].dropna()
        result[n] = {"mean": valid.mean(), "median": valid.median(),
                     "winrate": (valid > 0).mean()}
    return result


def indicator_ranking(summary: pd.DataFrame) -> pd.DataFrame:
    """按 5天胜率 × 5天均值收益 综合得分排名。"""
    df = summary.copy()
    df["composite"] = df["winrate_5d"].fillna(0) * df["mean_5d"].fillna(0)
    return df.sort_values("composite", ascending=False).reset_index(drop=True)


def sector_breakdown(signals: pd.DataFrame) -> pd.DataFrame:
    """按 indicator × direction × sector 做胜率统计。"""
    rows = []
    for (ind, direc, sec), grp in signals.groupby(
            ["indicator_name", "direction", "sector"]):
        row = {"indicator_name": ind, "direction": direc, "sector": sec,
               "n_signals": len(grp)}
        for n in HOLD_DAYS:
            valid = grp[f"return_{n}d"].dropna()
            wins  = grp[f"win_{n}d"].dropna()
            row[f"winrate_{n}d"] = wins.mean() if len(wins) else np.nan
            row[f"mean_{n}d"]    = valid.mean() if len(valid) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════
# 可视化
# ═══════════════════════════════════════════════════════════════

def plot_return_distribution(signals: pd.DataFrame, baseline_stats: dict):
    """各指标3/5/10天收益分布箱线图（LONG/SHORT 并列，vs 随机基准）。"""
    indicators = signals["indicator_name"].unique()
    fig, axes = plt.subplots(1, len(HOLD_DAYS), figsize=(18, 7))
    fig.suptitle("各指标收益分布 vs 随机基准（箱线图）", fontsize=14)

    colors = {"LONG": "#4CAF50", "SHORT": "#F44336"}

    for ax, n in zip(axes, HOLD_DAYS):
        col = f"return_{n}d"
        data_list, labels, clr_list = [], [], []
        for ind in indicators:
            for direc in ["LONG", "SHORT"]:
                sub = signals[(signals["indicator_name"] == ind) &
                              (signals["direction"] == direc)][col].dropna()
                if len(sub) == 0:
                    continue
                data_list.append(sub.values * 100)
                labels.append(f"{ind[:8]}\n{direc}")
                clr_list.append(colors[direc])

        bp = ax.boxplot(data_list, patch_artist=True, vert=True,
                        medianprops={"color": "black", "linewidth": 1.5})
        for patch, clr in zip(bp["boxes"], clr_list):
            patch.set_facecolor(clr)
            patch.set_alpha(0.6)

        # 随机基准线
        bm = baseline_stats[n]["mean"] * 100
        ax.axhline(bm, color="navy", linestyle="--", linewidth=1.2,
                   label=f"随机基准 {bm:+.2f}%")
        ax.axhline(0, color="gray", linestyle=":", linewidth=0.8)

        ax.set_title(f"持有 {n} 天")
        ax.set_ylabel("收益率 (%)")
        ax.set_xticks(range(1, len(labels) + 1))
        ax.set_xticklabels(labels, rotation=45, fontsize=6)
        ax.legend(fontsize=7)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "return_distribution.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  [图] return_distribution.png")


def plot_winrate_heatmap(summary: pd.DataFrame):
    """指标 × 方向 × 持有期 的胜率热力图。"""
    summary["label"] = summary["indicator_name"] + "\n" + summary["direction"]
    pivot_data = {}
    for n in HOLD_DAYS:
        pivot_data[f"{n}d"] = summary.set_index("label")[f"winrate_{n}d"]

    combined = pd.DataFrame(pivot_data)
    fig, ax = plt.subplots(figsize=(7, max(4, len(combined) * 0.5)))
    im = ax.imshow(combined.values, cmap="RdYlGn", vmin=0.3, vmax=0.7, aspect="auto")
    ax.set_xticks(range(len(HOLD_DAYS)))
    ax.set_xticklabels([f"持有{n}天" for n in HOLD_DAYS])
    ax.set_yticks(range(len(combined)))
    ax.set_yticklabels(combined.index, fontsize=8)
    for i in range(len(combined)):
        for j in range(len(HOLD_DAYS)):
            val = combined.iloc[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.1%}", ha="center", va="center", fontsize=7)
    plt.colorbar(im, ax=ax, label="胜率")
    ax.set_title("各指标×方向×持有期 胜率热力图")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "winrate_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  [图] winrate_heatmap.png")


def plot_long_short_comparison(symmetry: pd.DataFrame):
    """LONG vs SHORT 胜率对比（5天胜率）。"""
    x = np.arange(len(symmetry))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - width/2, symmetry["long_winrate_5d"] * 100,  width,
           label="LONG 5d 胜率",  color="#4CAF50", alpha=0.8)
    ax.bar(x + width/2, symmetry["short_winrate_5d"] * 100, width,
           label="SHORT 5d 胜率", color="#F44336", alpha=0.8)
    ax.axhline(50, color="gray", linestyle="--", linewidth=1, label="50% 随机基准")
    ax.set_xticks(x)
    ax.set_xticklabels(symmetry["indicator_name"], rotation=25)
    ax.set_ylabel("5天胜率 (%)")
    ax.set_title("多空对称性对比（5天胜率）")
    ax.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "long_short_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  [图] long_short_comparison.png")


def plot_composite_score_curve(signals: pd.DataFrame):
    """综合评分阈值 vs 胜率/触发频率权衡曲线。"""
    cs = signals[signals["indicator_name"] == "Composite_Score"].copy()
    if cs.empty:
        return
    cs["score_val"] = pd.to_numeric(cs["indicator_value"], errors="coerce")
    thresholds = np.arange(0.5, 2.6, 0.1)

    fig, ax1 = plt.subplots(figsize=(9, 5))
    ax2 = ax1.twinx()

    for direc, clr, ls in [("LONG", "#4CAF50", "-"), ("SHORT", "#F44336", "--")]:
        sub = cs[cs["direction"] == direc].dropna(subset=["score_val", "return_5d"])
        winrates, counts = [], []
        for thr in thresholds:
            filtered = sub[sub["score_val"] >= thr]
            winrates.append(filtered["win_5d"].mean() if len(filtered) else np.nan)
            counts.append(len(filtered))
        ax1.plot(thresholds, [w * 100 if w is not np.nan else np.nan for w in winrates],
                 color=clr, linestyle=ls, marker="o", markersize=4, label=f"{direc} 胜率")
        ax2.plot(thresholds, counts, color=clr, linestyle=":", alpha=0.5,
                 label=f"{direc} 触发次数")

    ax1.axhline(50, color="gray", linestyle=":", linewidth=1)
    ax1.set_xlabel("综合评分阈值")
    ax1.set_ylabel("5天胜率 (%)")
    ax2.set_ylabel("触发次数")
    ax1.set_title("综合评分阈值 vs 胜率/触发频率权衡曲线")
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "composite_score_curve.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  [图] composite_score_curve.png")


def plot_indicator_vs_random(summary: pd.DataFrame, baseline_stats: dict):
    """各指标平均收益 vs 随机基准对比柱状图（5天）。"""
    n = 5
    bm_mean = baseline_stats[n]["mean"] * 100
    fig, ax = plt.subplots(figsize=(12, 5))
    labels, longs, shorts = [], [], []
    for ind in summary["indicator_name"].unique():
        l_row = summary[(summary["indicator_name"] == ind) & (summary["direction"] == "LONG")]
        s_row = summary[(summary["indicator_name"] == ind) & (summary["direction"] == "SHORT")]
        if l_row.empty or s_row.empty:
            continue
        labels.append(ind)
        longs.append(l_row.iloc[0][f"mean_{n}d"] * 100)
        shorts.append(s_row.iloc[0][f"mean_{n}d"] * 100)

    x = np.arange(len(labels))
    w = 0.35
    ax.bar(x - w/2, longs,  w, label="LONG 平均收益",  color="#4CAF50", alpha=0.8)
    ax.bar(x + w/2, shorts, w, label="SHORT 平均收益", color="#F44336", alpha=0.8)
    ax.axhline(bm_mean,  color="navy",  linestyle="--", label=f"随机基准 {bm_mean:+.2f}%")
    ax.axhline(0, color="gray", linestyle=":", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20)
    ax.set_ylabel("5天平均收益率 (%)")
    ax.set_title("各指标平均收益 vs 随机基准（持有5天）")
    ax.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "indicator_vs_random.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  [图] indicator_vs_random.png")


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════

def main():
    print("=== 计划3：量化信号指标检验 ===\n")

    # 1. 加载数据
    print("[1] 加载数据...")
    df = load_data()
    print(f"    数据：{len(df)} 行，{df['variety_id'].nunique()} 个品种")

    # 2. 生成所有信号
    print("[2] 生成各指标信号...")
    signals = generate_all_signals(df)
    print(f"    信号总数：{len(signals)}")
    print(f"    指标分布：\n{signals.groupby(['indicator_name','direction']).size().to_string()}")
    signals.to_csv(OUTPUT_DIR / "all_signals.csv", index=False, encoding="utf-8-sig")
    print("  [CSV] all_signals.csv")

    # 3. 随机基准
    print("[3] 构建随机基准...")
    baseline_df = generate_random_baseline(df)
    baseline_stats = compute_random_baseline_stats(baseline_df)
    baseline_df.to_csv(OUTPUT_DIR / "random_baseline.csv", index=False, encoding="utf-8-sig")
    print(f"    随机基准 5d 均值={baseline_stats[5]['mean']*100:+.3f}%  "
          f"胜率={baseline_stats[5]['winrate']:.1%}")
    print("  [CSV] random_baseline.csv")

    # 4. 评估汇总
    print("[4] 评估各指标表现...")
    summary = evaluate_signals(signals)
    summary.to_csv(OUTPUT_DIR / "indicator_summary.csv", index=False, encoding="utf-8-sig")
    print("  [CSV] indicator_summary.csv")

    # 5. 子分组评估
    subgroup = evaluate_by_subgroup(signals)
    subgroup.to_csv(OUTPUT_DIR / "subgroup_breakdown.csv", index=False, encoding="utf-8-sig")
    print("  [CSV] subgroup_breakdown.csv")

    # 6. 多空对称性
    symmetry = long_short_symmetry(summary)
    symmetry.to_csv(OUTPUT_DIR / "long_short_symmetry.csv", index=False, encoding="utf-8-sig")
    print("  [CSV] long_short_symmetry.csv")

    # 7. 指标排名
    ranking = indicator_ranking(summary)
    ranking.to_csv(OUTPUT_DIR / "indicator_ranking.csv", index=False, encoding="utf-8-sig")
    print("  [CSV] indicator_ranking.csv")

    # 8. 板块细分
    sec_df = sector_breakdown(signals)
    sec_df.to_csv(OUTPUT_DIR / "sector_breakdown.csv", index=False, encoding="utf-8-sig")
    print("  [CSV] sector_breakdown.csv")

    # 9. 可视化
    print("[5] 生成图表...")
    plot_return_distribution(signals, baseline_stats)
    plot_winrate_heatmap(summary)
    plot_long_short_comparison(symmetry)
    plot_composite_score_curve(signals)
    plot_indicator_vs_random(summary, baseline_stats)

    # 10. 打印核心摘要
    print("\n=== 核心摘要（5天胜率）===")
    print(f"{'指标':<20} {'方向':<8} {'信号数':>6} {'5d胜率':>8} {'5d均值':>9} {'p值':>8}")
    print("-" * 62)
    for _, row in ranking.iterrows():
        wr = row["winrate_5d"]
        mn = row["mean_5d"]
        pv = row["pvalue_5d"]
        if np.isnan(wr):
            continue
        sig = "**" if (not np.isnan(pv) and pv < 0.05) else "  "
        print(f"{row['indicator_name']:<20} {row['direction']:<8} "
              f"{int(row['n_5d']):>6} {wr:>8.1%} {mn:>+9.3%} {pv:>8.4f}{sig}")

    print("\n=== 多空对称性（5天）===")
    print(f"{'指标':<20} {'LONG胜率':>9} {'SHORT胜率':>10} {'差值':>8} {'对称性'}")
    print("-" * 60)
    for _, row in symmetry.iterrows():
        lw = row["long_winrate_5d"]
        sw = row["short_winrate_5d"]
        diff = row["diff_5d"]
        if np.isnan(lw) or np.isnan(sw):
            continue
        sym = "✓ 对称" if abs(diff) <= 0.10 else "✗ 不对称"
        print(f"{row['indicator_name']:<20} {lw:>9.1%} {sw:>10.1%} {diff:>+8.1%}  {sym}")

    print(f"\n输出目录：{OUTPUT_DIR}")
    print("=== 完成 ===")


if __name__ == "__main__":
    main()
