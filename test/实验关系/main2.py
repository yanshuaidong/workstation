"""
计划2：基于主力资金趋势的价格共振研究
在 main_force / retail 时间序列上识别连续趋势段，分析其与期货价格趋势的共振关系，
验证"底部回升→不创新低"与"顶部回落→不创新高"两个假设，并设计趋势跟踪策略回测。
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
DB_PATH = BASE_DIR / "local_fut_pulse.sqlite"
OUTPUT_DIR = BASE_DIR / "output2"
OUTPUT_DIR.mkdir(exist_ok=True)

with open(BASE_DIR / "varieties.json", "r", encoding="utf-8") as f:
    VARIETIES = {v["id"]: v["name"] for v in json.load(f)}

SECTOR_MAP = {
    "黑色系": ["铁矿石", "螺纹钢", "热卷", "锰硅", "焦煤"],
    "有色金属": ["沪铜", "沪铝", "沪锌", "沪铅", "沪锡", "沪镍", "沪金", "沪银",
                "氧化铝", "工业硅", "碳酸锂", "多晶硅"],
    "能源化工": ["PTA", "对二甲苯", "聚丙烯", "苯乙烯", "纯苯", "烧碱", "尿素",
                "橡胶", "丁二烯胶", "甲醇", "PVC", "纯碱", "玻璃", "塑料",
                "乙二醇", "沥青", "LPG", "燃油", "低硫燃油"],
    "农产品": ["豆一", "豆二", "豆油", "豆粕", "菜油", "菜粕", "棕榈油", "玉米",
              "鸡蛋", "棉花", "白糖", "苹果", "红枣", "花生", "生猪"],
    "其他": ["纸浆", "原木", "上证", "欧线集运"],
}
NAME_TO_SECTOR = {}
for _sec, _names in SECTOR_MAP.items():
    for _n in _names:
        NAME_TO_SECTOR[_n] = _sec


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
# 阶段一：趋势识别与标注
# ═══════════════════════════════════════════════════════════════

def identify_trends(series: np.ndarray, dates: np.ndarray,
                    min_duration: int = 3, tolerance: int = 1) -> list[dict]:
    """
    在一维数值序列上识别连续趋势段。
    允许中间有 `tolerance` 天的小幅反向波动。
    返回趋势段列表，每段包含起止索引、方向、幅度等。
    """
    n = len(series)
    if n < min_duration:
        return []

    deltas = np.diff(series)
    segments = []
    i = 0
    while i < len(deltas):
        if deltas[i] == 0:
            i += 1
            continue
        direction = 1 if deltas[i] > 0 else -1
        start_idx = i
        j = i + 1
        contrary_count = 0
        while j < len(deltas):
            if (deltas[j] > 0 and direction == 1) or (deltas[j] < 0 and direction == -1):
                contrary_count = 0
                j += 1
            elif deltas[j] == 0:
                j += 1
            else:
                contrary_count += 1
                if contrary_count > tolerance:
                    j -= tolerance
                    break
                j += 1
        seg_end = min(j, len(deltas))
        duration = seg_end - start_idx + 1  # +1: segment covers indices [start_idx, seg_end]
        if duration >= min_duration:
            segments.append({
                "idx_start": start_idx,
                "idx_end": seg_end,
                "date_start": dates[start_idx],
                "date_end": dates[seg_end],
                "duration": duration,
                "start_value": series[start_idx],
                "end_value": series[seg_end],
                "direction": "up" if direction == 1 else "down",
                "magnitude": series[seg_end] - series[start_idx],
            })
        i = seg_end
    return segments


def compute_zone(value: float, quantiles: dict) -> str:
    if value < quantiles[0.10]:
        return "极端负值"
    elif value < quantiles[0.30]:
        return "负值区"
    elif value < quantiles[0.70]:
        return "中性区"
    elif value < quantiles[0.90]:
        return "正值区"
    else:
        return "极端正值"


def run_phase1(df: pd.DataFrame) -> pd.DataFrame:
    """阶段一：对每个品种的 main_force 和 retail 做趋势识别"""
    all_segments = []

    for vid, g in df.groupby("variety_id"):
        g = g.sort_values("trade_date").reset_index(drop=True)
        name = VARIETIES.get(vid, str(vid))
        dates = g["trade_date"].values

        mf_quantiles = {q: g["main_force"].quantile(q) for q in [0.10, 0.30, 0.70, 0.90]}
        rt_quantiles = {q: g["retail"].quantile(q) for q in [0.10, 0.30, 0.70, 0.90]}

        for field, label, quantiles in [
            ("main_force", "main_force", mf_quantiles),
            ("retail", "retail", rt_quantiles),
        ]:
            values = g[field].values
            segs = identify_trends(values, dates, min_duration=3, tolerance=1)
            for s in segs:
                s["variety_id"] = vid
                s["variety_name"] = name
                s["sector"] = NAME_TO_SECTOR.get(name, "其他")
                s["field"] = label
                s["start_zone"] = compute_zone(s["start_value"], quantiles)
            all_segments.extend(segs)

        # 对价格也做趋势识别
        prices = g["close_price"].values
        price_segs = identify_trends(prices, dates, min_duration=3, tolerance=1)
        for s in price_segs:
            s["variety_id"] = vid
            s["variety_name"] = name
            s["sector"] = NAME_TO_SECTOR.get(name, "其他")
            s["field"] = "close_price"
            s["start_zone"] = ""
        all_segments.extend(price_segs)

    seg_df = pd.DataFrame(all_segments)
    n_mf = len(seg_df[seg_df["field"] == "main_force"])
    n_rt = len(seg_df[seg_df["field"] == "retail"])
    n_pr = len(seg_df[seg_df["field"] == "close_price"])
    print(f"[阶段一] 趋势识别完成: main_force {n_mf} 段, retail {n_rt} 段, close_price {n_pr} 段")
    return seg_df


# ═══════════════════════════════════════════════════════════════
# 阶段二：趋势共振分析（验证 H1）
# ═══════════════════════════════════════════════════════════════

def run_phase2(df: pd.DataFrame, seg_df: pd.DataFrame) -> pd.DataFrame:
    """计算 main_force 趋势段与同期价格趋势的一致性"""
    concordance_records = []

    mf_segs = seg_df[seg_df["field"] == "main_force"]
    rt_segs = seg_df[seg_df["field"] == "retail"]
    price_segs = seg_df[seg_df["field"] == "close_price"]

    for field_label, fund_segs in [("main_force", mf_segs), ("retail", rt_segs)]:
        for _, seg in fund_segs.iterrows():
            vid = seg["variety_id"]
            d_start, d_end = seg["date_start"], seg["date_end"]

            # 同期价格变化
            g = df[(df["variety_id"] == vid)].sort_values("trade_date")
            mask = (g["trade_date"] >= d_start) & (g["trade_date"] <= d_end)
            window = g[mask]
            if len(window) < 2:
                continue

            price_change = window["close_price"].iloc[-1] - window["close_price"].iloc[0]
            price_direction = "up" if price_change > 0 else "down"
            direction_match = 1 if price_direction == seg["direction"] else 0

            # 价格趋势重叠度：查找同品种价格趋势段与当前资金趋势段的时间重叠
            v_price_segs = price_segs[price_segs["variety_id"] == vid]
            max_overlap = 0
            for _, ps in v_price_segs.iterrows():
                overlap_start = max(pd.Timestamp(d_start), pd.Timestamp(ps["date_start"]))
                overlap_end = min(pd.Timestamp(d_end), pd.Timestamp(ps["date_end"]))
                overlap_days = max(0, (overlap_end - overlap_start).days + 1)
                if overlap_days > max_overlap and ps["direction"] == seg["direction"]:
                    max_overlap = overlap_days
            overlap_ratio = max_overlap / seg["duration"] if seg["duration"] > 0 else 0

            concordance_records.append({
                "variety_id": vid,
                "variety_name": seg["variety_name"],
                "sector": seg["sector"],
                "field": field_label,
                "direction": seg["direction"],
                "duration": seg["duration"],
                "start_zone": seg["start_zone"],
                "magnitude": seg["magnitude"],
                "price_change": price_change,
                "price_pct_change": price_change / window["close_price"].iloc[0] if window["close_price"].iloc[0] != 0 else 0,
                "direction_match": direction_match,
                "overlap_ratio": overlap_ratio,
            })

    conc_df = pd.DataFrame(concordance_records)
    if conc_df.empty:
        print("[阶段二] 无共振数据")
        return conc_df

    mf_conc = conc_df[conc_df["field"] == "main_force"]
    rt_conc = conc_df[conc_df["field"] == "retail"]

    print(f"\n[阶段二] 趋势共振分析完成")
    if len(mf_conc) > 0:
        print(f"  main_force 方向一致率: {mf_conc['direction_match'].mean():.2%} ({len(mf_conc)} 段)")
        print(f"  main_force 平均趋势重叠度: {mf_conc['overlap_ratio'].mean():.2%}")
    if len(rt_conc) > 0:
        print(f"  retail 方向一致率: {rt_conc['direction_match'].mean():.2%} ({len(rt_conc)} 段)")

    # 分组对比
    if len(mf_conc) >= 3:
        print("\n  --- 按趋势持续天数分组 (main_force) ---")
        dur_bins = pd.cut(mf_conc["duration"], bins=[2, 3, 4, 100], labels=["3天", "4天", "5天+"])
        for label, group in mf_conc.groupby(dur_bins, observed=True):
            if len(group) > 0:
                print(f"    {label}: 方向一致率 {group['direction_match'].mean():.2%}, "
                      f"平均重叠度 {group['overlap_ratio'].mean():.2%}, N={len(group)}")

        print("\n  --- 按起始区域分组 (main_force) ---")
        for zone, group in mf_conc.groupby("start_zone"):
            if len(group) > 0:
                print(f"    {zone}: 方向一致率 {group['direction_match'].mean():.2%}, N={len(group)}")

        print("\n  --- 按品种板块分组 (main_force) ---")
        for sector, group in mf_conc.groupby("sector"):
            if len(group) > 0:
                print(f"    {sector}: 方向一致率 {group['direction_match'].mean():.2%}, "
                      f"平均重叠度 {group['overlap_ratio'].mean():.2%}, N={len(group)}")

    # 幅度相关性
    if len(mf_conc) >= 5:
        r, p = stats.pearsonr(mf_conc["magnitude"].abs(), mf_conc["price_pct_change"].abs())
        print(f"\n  幅度相关性 (|主力趋势幅度| vs |价格变化%|): r={r:.3f}, p={p:.4f}")

    return conc_df


# ═══════════════════════════════════════════════════════════════
# 阶段三：条件概率分析（验证 H2 & H3）
# ═══════════════════════════════════════════════════════════════

def run_phase3(df: pd.DataFrame, seg_df: pd.DataFrame,
               trend_min_days: int = 3, future_window: int = 5,
               lookback_window: int = 5) -> pd.DataFrame:
    """
    验证 H2（底部回升→不创新低）和 H3（顶部回落→不创新高）。
    """
    mf_segs = seg_df[seg_df["field"] == "main_force"]
    results = []

    for vid, g in df.groupby("variety_id"):
        g = g.sort_values("trade_date").reset_index(drop=True)
        name = VARIETIES.get(vid, str(vid))
        closes = g["close_price"].values
        dates = g["trade_date"].values
        n = len(g)

        # 基准概率 P(B): 在任意位置，未来 future_window 天创新低的概率
        base_new_low_count = 0
        base_new_high_count = 0
        base_total = 0
        for t in range(lookback_window, n - future_window):
            past_min = np.min(closes[t - lookback_window + 1: t + 1])
            future_min = np.min(closes[t + 1: t + 1 + future_window])
            past_max = np.max(closes[t - lookback_window + 1: t + 1])
            future_max = np.max(closes[t + 1: t + 1 + future_window])
            if future_min < past_min:
                base_new_low_count += 1
            if future_max > past_max:
                base_new_high_count += 1
            base_total += 1

        p_b = base_new_low_count / base_total if base_total > 0 else 0
        p_d = base_new_high_count / base_total if base_total > 0 else 0

        v_segs = mf_segs[mf_segs["variety_id"] == vid]

        # 事件 A: 主力底部回升（从极端负值/负值区开始，连续上升）
        bottom_rise = v_segs[
            (v_segs["direction"] == "up") &
            (v_segs["start_zone"].isin(["极端负值", "负值区"])) &
            (v_segs["duration"] >= trend_min_days)
        ]

        a_total, a_new_low = 0, 0
        for _, seg in bottom_rise.iterrows():
            t_idx = int(seg["idx_end"])
            if t_idx >= n or t_idx < lookback_window or t_idx + future_window >= n:
                continue
            past_min = np.min(closes[t_idx - lookback_window + 1: t_idx + 1])
            future_min = np.min(closes[t_idx + 1: t_idx + 1 + future_window])
            a_total += 1
            if future_min < past_min:
                a_new_low += 1

        p_b_given_a = a_new_low / a_total if a_total > 0 else np.nan

        # 事件 C: 主力顶部回落（从极端正值/正值区开始，连续下降）
        top_fall = v_segs[
            (v_segs["direction"] == "down") &
            (v_segs["start_zone"].isin(["极端正值", "正值区"])) &
            (v_segs["duration"] >= trend_min_days)
        ]

        c_total, c_new_high = 0, 0
        for _, seg in top_fall.iterrows():
            t_idx = int(seg["idx_end"])
            if t_idx >= n or t_idx < lookback_window or t_idx + future_window >= n:
                continue
            past_max = np.max(closes[t_idx - lookback_window + 1: t_idx + 1])
            future_max = np.max(closes[t_idx + 1: t_idx + 1 + future_window])
            c_total += 1
            if future_max > past_max:
                c_new_high += 1

        p_d_given_c = c_new_high / c_total if c_total > 0 else np.nan

        # Fisher 精确检验 (H2: P(B|A) < P(B))
        fisher_p_h2 = np.nan
        if a_total > 0 and base_total > 0:
            table_h2 = [
                [a_new_low, a_total - a_new_low],
                [base_new_low_count, base_total - base_new_low_count],
            ]
            try:
                _, fisher_p_h2 = stats.fisher_exact(table_h2, alternative="less")
            except Exception:
                pass

        fisher_p_h3 = np.nan
        if c_total > 0 and base_total > 0:
            table_h3 = [
                [c_new_high, c_total - c_new_high],
                [base_new_high_count, base_total - base_new_high_count],
            ]
            try:
                _, fisher_p_h3 = stats.fisher_exact(table_h3, alternative="less")
            except Exception:
                pass

        results.append({
            "variety_id": vid,
            "variety_name": name,
            "sector": NAME_TO_SECTOR.get(name, "其他"),
            "base_total": base_total,
            "P_B_base": p_b,
            "P_D_base": p_d,
            "H2_n_events": a_total,
            "H2_n_new_low": a_new_low,
            "P_B_given_A": p_b_given_a,
            "H2_fisher_p": fisher_p_h2,
            "H3_n_events": c_total,
            "H3_n_new_high": c_new_high,
            "P_D_given_C": p_d_given_c,
            "H3_fisher_p": fisher_p_h3,
        })

    prob_df = pd.DataFrame(results)
    print(f"\n[阶段三] 条件概率分析完成 ({len(prob_df)} 品种)")

    # 汇总
    valid_h2 = prob_df[prob_df["H2_n_events"] > 0]
    valid_h3 = prob_df[prob_df["H3_n_events"] > 0]

    print(f"  H2 (底部回升): {len(valid_h2)} 品种有有效事件")
    if len(valid_h2) > 0:
        avg_base = valid_h2["P_B_base"].mean()
        avg_cond = valid_h2["P_B_given_A"].mean()
        print(f"    平均 P(创新低|无条件) = {avg_base:.2%}")
        print(f"    平均 P(创新低|主力底部回升) = {avg_cond:.2%}")
        print(f"    效应方向: {'保护效应成立 ✓' if avg_cond < avg_base else '保护效应不成立 ✗'}")
        n_sig = (valid_h2["H2_fisher_p"] < 0.05).sum()
        print(f"    Fisher 显著品种数 (p<0.05): {n_sig}/{len(valid_h2)}")

    print(f"  H3 (顶部回落): {len(valid_h3)} 品种有有效事件")
    if len(valid_h3) > 0:
        avg_base = valid_h3["P_D_base"].mean()
        avg_cond = valid_h3["P_D_given_C"].mean()
        print(f"    平均 P(创新高|无条件) = {avg_base:.2%}")
        print(f"    平均 P(创新高|主力顶部回落) = {avg_cond:.2%}")
        print(f"    效应方向: {'保护效应成立 ✓' if avg_cond < avg_base else '保护效应不成立 ✗'}")
        n_sig = (valid_h3["H3_fisher_p"] < 0.05).sum()
        print(f"    Fisher 显著品种数 (p<0.05): {n_sig}/{len(valid_h3)}")

    return prob_df


def run_sensitivity(df: pd.DataFrame, seg_df_func, phase3_func) -> pd.DataFrame:
    """敏感性分析：调整参数重新运行阶段三"""
    param_combos = []
    for min_days in [3, 4, 5]:
        for fw in [3, 5, 7]:
            for lw in [3, 5, 10]:
                param_combos.append((min_days, fw, lw))

    results = []
    for min_days, fw, lw in param_combos:
        seg_df = seg_df_func(df, min_duration=min_days)
        prob_df = phase3_func(df, seg_df, trend_min_days=min_days,
                              future_window=fw, lookback_window=lw)
        valid_h2 = prob_df[prob_df["H2_n_events"] > 0]
        valid_h3 = prob_df[prob_df["H3_n_events"] > 0]

        results.append({
            "min_trend_days": min_days,
            "future_window": fw,
            "lookback_window": lw,
            "H2_n_varieties_with_events": len(valid_h2),
            "H2_total_events": valid_h2["H2_n_events"].sum() if len(valid_h2) > 0 else 0,
            "H2_avg_P_base": valid_h2["P_B_base"].mean() if len(valid_h2) > 0 else np.nan,
            "H2_avg_P_cond": valid_h2["P_B_given_A"].mean() if len(valid_h2) > 0 else np.nan,
            "H2_effect": (valid_h2["P_B_base"].mean() - valid_h2["P_B_given_A"].mean()) if len(valid_h2) > 0 else np.nan,
            "H2_n_sig": (valid_h2["H2_fisher_p"] < 0.05).sum() if len(valid_h2) > 0 else 0,
            "H3_n_varieties_with_events": len(valid_h3),
            "H3_total_events": valid_h3["H3_n_events"].sum() if len(valid_h3) > 0 else 0,
            "H3_avg_P_base": valid_h3["P_D_base"].mean() if len(valid_h3) > 0 else np.nan,
            "H3_avg_P_cond": valid_h3["P_D_given_C"].mean() if len(valid_h3) > 0 else np.nan,
            "H3_effect": (valid_h3["P_D_base"].mean() - valid_h3["P_D_given_C"].mean()) if len(valid_h3) > 0 else np.nan,
            "H3_n_sig": (valid_h3["H3_fisher_p"] < 0.05).sum() if len(valid_h3) > 0 else 0,
        })

    sens_df = pd.DataFrame(results)
    print(f"\n[敏感性分析] 完成 {len(sens_df)} 组参数组合")
    best_h2 = sens_df.loc[sens_df["H2_effect"].idxmax()] if sens_df["H2_effect"].notna().any() else None
    if best_h2 is not None:
        print(f"  H2 最佳参数: min_days={best_h2['min_trend_days']:.0f}, "
              f"future={best_h2['future_window']:.0f}, lookback={best_h2['lookback_window']:.0f}, "
              f"效应={best_h2['H2_effect']:.2%}")
    return sens_df


def _run_phase1_with_params(df: pd.DataFrame, min_duration: int = 3) -> pd.DataFrame:
    """供敏感性分析调用的趋势识别（静默版）"""
    all_segments = []
    for vid, g in df.groupby("variety_id"):
        g = g.sort_values("trade_date").reset_index(drop=True)
        name = VARIETIES.get(vid, str(vid))
        dates = g["trade_date"].values

        mf_quantiles = {q: g["main_force"].quantile(q) for q in [0.10, 0.30, 0.70, 0.90]}

        values = g["main_force"].values
        segs = identify_trends(values, dates, min_duration=min_duration, tolerance=1)
        for s in segs:
            s["variety_id"] = vid
            s["variety_name"] = name
            s["sector"] = NAME_TO_SECTOR.get(name, "其他")
            s["field"] = "main_force"
            s["start_zone"] = compute_zone(s["start_value"], mf_quantiles)
        all_segments.extend(segs)

    return pd.DataFrame(all_segments)


def _run_phase3_silent(df, seg_df, trend_min_days=3, future_window=5, lookback_window=5):
    """静默版阶段三（无打印）"""
    mf_segs = seg_df[seg_df["field"] == "main_force"] if "field" in seg_df.columns else seg_df
    results = []

    for vid, g in df.groupby("variety_id"):
        g = g.sort_values("trade_date").reset_index(drop=True)
        name = VARIETIES.get(vid, str(vid))
        closes = g["close_price"].values
        dates = g["trade_date"].values
        n = len(g)

        base_new_low_count = 0
        base_new_high_count = 0
        base_total = 0
        for t in range(lookback_window, n - future_window):
            past_min = np.min(closes[t - lookback_window + 1: t + 1])
            future_min = np.min(closes[t + 1: t + 1 + future_window])
            past_max = np.max(closes[t - lookback_window + 1: t + 1])
            future_max = np.max(closes[t + 1: t + 1 + future_window])
            if future_min < past_min:
                base_new_low_count += 1
            if future_max > past_max:
                base_new_high_count += 1
            base_total += 1

        p_b = base_new_low_count / base_total if base_total > 0 else 0
        p_d = base_new_high_count / base_total if base_total > 0 else 0

        v_segs = mf_segs[mf_segs["variety_id"] == vid]

        bottom_rise = v_segs[
            (v_segs["direction"] == "up") &
            (v_segs["start_zone"].isin(["极端负值", "负值区"])) &
            (v_segs["duration"] >= trend_min_days)
        ]
        a_total, a_new_low = 0, 0
        for _, seg in bottom_rise.iterrows():
            t_idx = int(seg["idx_end"])
            if t_idx >= n or t_idx < lookback_window or t_idx + future_window >= n:
                continue
            past_min = np.min(closes[t_idx - lookback_window + 1: t_idx + 1])
            future_min = np.min(closes[t_idx + 1: t_idx + 1 + future_window])
            a_total += 1
            if future_min < past_min:
                a_new_low += 1
        p_b_given_a = a_new_low / a_total if a_total > 0 else np.nan

        top_fall = v_segs[
            (v_segs["direction"] == "down") &
            (v_segs["start_zone"].isin(["极端正值", "正值区"])) &
            (v_segs["duration"] >= trend_min_days)
        ]
        c_total, c_new_high = 0, 0
        for _, seg in top_fall.iterrows():
            t_idx = int(seg["idx_end"])
            if t_idx >= n or t_idx < lookback_window or t_idx + future_window >= n:
                continue
            past_max = np.max(closes[t_idx - lookback_window + 1: t_idx + 1])
            future_max = np.max(closes[t_idx + 1: t_idx + 1 + future_window])
            c_total += 1
            if future_max > past_max:
                c_new_high += 1
        p_d_given_c = c_new_high / c_total if c_total > 0 else np.nan

        fisher_p_h2 = np.nan
        if a_total > 0 and base_total > 0:
            try:
                _, fisher_p_h2 = stats.fisher_exact(
                    [[a_new_low, a_total - a_new_low],
                     [base_new_low_count, base_total - base_new_low_count]],
                    alternative="less")
            except Exception:
                pass

        fisher_p_h3 = np.nan
        if c_total > 0 and base_total > 0:
            try:
                _, fisher_p_h3 = stats.fisher_exact(
                    [[c_new_high, c_total - c_new_high],
                     [base_new_high_count, base_total - base_new_high_count]],
                    alternative="less")
            except Exception:
                pass

        results.append({
            "variety_id": vid, "variety_name": name,
            "sector": NAME_TO_SECTOR.get(name, "其他"),
            "base_total": base_total,
            "P_B_base": p_b, "P_D_base": p_d,
            "H2_n_events": a_total, "H2_n_new_low": a_new_low,
            "P_B_given_A": p_b_given_a, "H2_fisher_p": fisher_p_h2,
            "H3_n_events": c_total, "H3_n_new_high": c_new_high,
            "P_D_given_C": p_d_given_c, "H3_fisher_p": fisher_p_h3,
        })

    return pd.DataFrame(results)


# ═══════════════════════════════════════════════════════════════
# 阶段四：趋势跟踪策略设计与回测
# ═══════════════════════════════════════════════════════════════

def run_phase4(df: pd.DataFrame, seg_df: pd.DataFrame) -> pd.DataFrame:
    mf_segs = seg_df[seg_df["field"] == "main_force"]
    rt_segs = seg_df[seg_df["field"] == "retail"]
    bt_records = []

    for vid, g in df.groupby("variety_id"):
        g = g.sort_values("trade_date").reset_index(drop=True)
        name = VARIETIES.get(vid, str(vid))
        sector = NAME_TO_SECTOR.get(name, "其他")
        closes = g["close_price"].values
        dates = g["trade_date"].values
        n = len(g)
        if n < 8:
            continue

        v_mf = mf_segs[mf_segs["variety_id"] == vid]
        v_rt = rt_segs[rt_segs["variety_id"] == vid]

        # ─── 策略 A: 趋势跟随信号 ───
        signal_a = np.zeros(n)
        for _, seg in v_mf.iterrows():
            start_idx = seg["idx_start"]
            end_idx = seg["idx_end"]
            if seg["direction"] == "up" and seg["start_zone"] in ["极端负值", "负值区", "中性区"]:
                for k in range(max(start_idx + 2, 0), min(end_idx + 1, n)):
                    signal_a[k] = 1
            elif seg["direction"] == "down" and seg["start_zone"] in ["极端正值", "正值区", "中性区"]:
                for k in range(max(start_idx + 2, 0), min(end_idx + 1, n)):
                    signal_a[k] = -1

        # ─── 策略 B: 新低保护信号（做多+止损） ───
        signal_b = np.zeros(n)
        for _, seg in v_mf.iterrows():
            if seg["direction"] == "up" and seg["start_zone"] in ["极端负值", "负值区"]:
                entry_idx = min(seg["idx_start"] + 2, n - 1)
                if entry_idx >= n:
                    continue
                stop_loss = np.min(closes[max(0, entry_idx - 4): entry_idx + 1])
                for k in range(entry_idx, min(seg["idx_end"] + 1, n)):
                    if closes[k] < stop_loss:
                        break
                    signal_b[k] = 1

        # ─── 策略 C: 主散共振策略 ───
        signal_c = np.zeros(n)
        for _, mf_seg in v_mf.iterrows():
            for _, rt_seg in v_rt.iterrows():
                overlap_start = max(mf_seg["idx_start"], rt_seg["idx_start"])
                overlap_end = min(mf_seg["idx_end"], rt_seg["idx_end"])
                if overlap_end <= overlap_start:
                    continue
                if mf_seg["direction"] == "up" and rt_seg["direction"] == "down":
                    for k in range(max(overlap_start + 2, 0), min(overlap_end + 1, n)):
                        signal_c[k] = 1
                elif mf_seg["direction"] == "down" and rt_seg["direction"] == "up":
                    for k in range(max(overlap_start + 2, 0), min(overlap_end + 1, n)):
                        signal_c[k] = -1

        # 计算各策略的绩效
        daily_ret = np.diff(closes) / closes[:-1]

        for strat_name, signal in [("策略A_趋势跟随", signal_a),
                                   ("策略B_新低保护", signal_b),
                                   ("策略C_主散共振", signal_c)]:
            pos = signal[:-1]
            strat_ret = pos * daily_ret
            trades = int(np.sum(pos != 0))
            if trades == 0:
                bt_records.append({
                    "variety_id": vid, "variety_name": name, "sector": sector,
                    "strategy": strat_name, "n_trades": 0, "win_rate": np.nan,
                    "total_return": 0, "avg_return": 0, "profit_loss_ratio": np.nan,
                    "max_drawdown": 0, "signal_freq": 0,
                    "new_low_prob_after_long": np.nan,
                })
                continue

            wins = int(np.sum(strat_ret[pos != 0] > 0))
            win_rate = wins / trades
            total_ret = float(np.sum(strat_ret))
            avg_ret = float(np.mean(strat_ret[pos != 0]))

            win_rets = strat_ret[strat_ret > 0]
            loss_rets = strat_ret[strat_ret < 0]
            avg_win = float(np.mean(win_rets)) if len(win_rets) > 0 else 0
            avg_loss = float(np.mean(np.abs(loss_rets))) if len(loss_rets) > 0 else 1e-9
            plr = avg_win / avg_loss if avg_loss > 0 else np.inf

            cum = np.cumsum(strat_ret)
            max_dd = float(np.min(cum - np.maximum.accumulate(cum)))

            signal_freq = trades / (n - 1)

            # 做多信号后未来5日新低概率
            long_indices = np.where(pos == 1)[0]
            new_low_count = 0
            new_low_total = 0
            for idx in long_indices:
                if idx < 5 or idx + 5 >= n:
                    continue
                past_min = np.min(closes[idx - 4: idx + 1])
                future_min = np.min(closes[idx + 1: idx + 6])
                new_low_total += 1
                if future_min < past_min:
                    new_low_count += 1
            new_low_prob = new_low_count / new_low_total if new_low_total > 0 else np.nan

            bt_records.append({
                "variety_id": vid, "variety_name": name, "sector": sector,
                "strategy": strat_name, "n_trades": trades, "win_rate": win_rate,
                "total_return": total_ret, "avg_return": avg_ret,
                "profit_loss_ratio": plr, "max_drawdown": max_dd,
                "signal_freq": signal_freq,
                "new_low_prob_after_long": new_low_prob,
            })

    bt_df = pd.DataFrame(bt_records)
    print(f"\n[阶段四] 策略回测完成 ({len(bt_df)} 条记录)")

    for strat in ["策略A_趋势跟随", "策略B_新低保护", "策略C_主散共振"]:
        sdf = bt_df[bt_df["strategy"] == strat]
        valid = sdf[sdf["n_trades"] > 0]
        if len(valid) == 0:
            print(f"  {strat}: 无有效交易")
            continue
        avg_wr = valid["win_rate"].mean()
        avg_ret = valid["total_return"].mean()
        n_pos = (valid["total_return"] > 0).sum()
        print(f"  {strat}: 平均胜率 {avg_wr:.2%}, 平均总收益 {avg_ret:.4f}, "
              f"盈利品种 {n_pos}/{len(valid)}")

    # 按板块
    for strat in ["策略A_趋势跟随", "策略B_新低保护", "策略C_主散共振"]:
        sdf = bt_df[(bt_df["strategy"] == strat) & (bt_df["n_trades"] > 0)]
        if len(sdf) == 0:
            continue
        print(f"\n  --- {strat} 按板块 ---")
        for sector, gp in sdf.groupby("sector"):
            print(f"    {sector}: 平均胜率 {gp['win_rate'].mean():.2%}, "
                  f"平均收益 {gp['total_return'].mean():.4f}, N={len(gp)}")

    return bt_df


# ═══════════════════════════════════════════════════════════════
# 阶段五：可视化
# ═══════════════════════════════════════════════════════════════

def plot_trend_annotated(df: pd.DataFrame, seg_df: pd.DataFrame, conc_df: pd.DataFrame):
    """趋势标注双轴图：选取共振最强/最弱各5个品种"""
    mf_conc = conc_df[conc_df["field"] == "main_force"]
    if len(mf_conc) == 0:
        return

    variety_match = mf_conc.groupby("variety_id")["direction_match"].mean()
    top_ids = variety_match.sort_values(ascending=False).head(5).index.tolist()
    bottom_ids = variety_match.sort_values(ascending=True).head(5).index.tolist()
    show_ids = list(dict.fromkeys(top_ids + bottom_ids))[:10]

    mf_segs = seg_df[seg_df["field"] == "main_force"]

    n_plots = len(show_ids)
    cols = min(n_plots, 2)
    rows = (n_plots + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(16, 4 * rows))
    if n_plots == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    for idx, vid in enumerate(show_ids):
        if idx >= len(axes):
            break
        g = df[df["variety_id"] == vid].sort_values("trade_date")
        name = VARIETIES.get(vid, str(vid))
        match_rate = variety_match.get(vid, 0)

        ax1 = axes[idx]
        ax2 = ax1.twinx()

        ax1.plot(g["trade_date"], g["close_price"], "k-", linewidth=1.2, label="收盘价")
        ax2.plot(g["trade_date"], g["main_force"], color="gray", linewidth=0.8,
                 alpha=0.5, label="main_force")

        v_segs = mf_segs[mf_segs["variety_id"] == vid]
        for _, seg in v_segs.iterrows():
            color = "#2e7d32" if seg["direction"] == "up" else "#c62828"
            alpha = 0.25
            ax2.axvspan(pd.Timestamp(seg["date_start"]),
                        pd.Timestamp(seg["date_end"]),
                        color=color, alpha=alpha)

        ax1.set_title(f"{name} (方向一致率={match_rate:.0%})", fontsize=10)
        ax1.set_ylabel("收盘价")
        ax2.set_ylabel("main_force")
        ax1.tick_params(axis="x", rotation=45, labelsize=7)

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc="upper left")

    for idx in range(len(show_ids), len(axes)):
        axes[idx].set_visible(False)

    plt.suptitle("趋势标注双轴图 (绿=主力上升趋势, 红=主力下降趋势)", fontsize=13, y=1.01)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "trend_annotated_top10.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  → 保存: output2/trend_annotated_top10.png")


def plot_cond_prob_comparison(prob_df: pd.DataFrame):
    """条件概率对比柱状图"""
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))

    # H2: P(创新低|主力回升) vs P(创新低|无条件)
    ax = axes[0]
    valid = prob_df[prob_df["H2_n_events"] > 0].sort_values("P_B_given_A")
    if len(valid) > 0:
        x = np.arange(len(valid))
        w = 0.35
        ax.barh(x - w / 2, valid["P_B_base"], w, label="P(创新低|无条件)", color="#ef5350", alpha=0.7)
        ax.barh(x + w / 2, valid["P_B_given_A"], w, label="P(创新低|主力底部回升)", color="#42a5f5", alpha=0.7)
        ax.set_yticks(x)
        ax.set_yticklabels(valid["variety_name"], fontsize=7)
        ax.set_xlabel("概率")
        ax.set_title("H2: 主力底部回升的保护效应", fontsize=11)
        ax.legend(fontsize=8)

    # H3: P(创新高|主力回落) vs P(创新高|无条件)
    ax = axes[1]
    valid = prob_df[prob_df["H3_n_events"] > 0].sort_values("P_D_given_C")
    if len(valid) > 0:
        x = np.arange(len(valid))
        w = 0.35
        ax.barh(x - w / 2, valid["P_D_base"], w, label="P(创新高|无条件)", color="#66bb6a", alpha=0.7)
        ax.barh(x + w / 2, valid["P_D_given_C"], w, label="P(创新高|主力顶部回落)", color="#ffa726", alpha=0.7)
        ax.set_yticks(x)
        ax.set_yticklabels(valid["variety_name"], fontsize=7)
        ax.set_xlabel("概率")
        ax.set_title("H3: 主力顶部回落的保护效应", fontsize=11)
        ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "cond_prob_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  → 保存: output2/cond_prob_comparison.png")


def plot_backtest_comparison(bt_df: pd.DataFrame):
    """策略对比汇总图"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # (1) 三策略胜率对比
    ax = axes[0][0]
    for strat in bt_df["strategy"].unique():
        sdf = bt_df[(bt_df["strategy"] == strat) & (bt_df["n_trades"] > 0)]
        ax.scatter(sdf["win_rate"], sdf["total_return"], label=strat, s=40, alpha=0.7)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.axvline(0.5, color="black", linewidth=0.5, linestyle="--")
    ax.set_xlabel("胜率")
    ax.set_ylabel("总收益")
    ax.set_title("各策略: 胜率 vs 总收益")
    ax.legend(fontsize=8)

    # (2) 各策略平均收益对比
    ax = axes[0][1]
    avg_by_strat = bt_df[bt_df["n_trades"] > 0].groupby("strategy")["total_return"].mean()
    colors = ["#1976d2", "#388e3c", "#f57c00"]
    avg_by_strat.plot(kind="bar", ax=ax, color=colors[:len(avg_by_strat)])
    ax.set_title("各策略平均收益对比")
    ax.set_ylabel("平均总收益")
    ax.tick_params(axis="x", rotation=15)

    # (3) 按板块的策略A表现
    ax = axes[1][0]
    strat_a = bt_df[(bt_df["strategy"] == "策略A_趋势跟随") & (bt_df["n_trades"] > 0)]
    if len(strat_a) > 0:
        sector_perf = strat_a.groupby("sector").agg(
            win_rate=("win_rate", "mean"),
            total_return=("total_return", "mean"),
            count=("variety_id", "count"),
        )
        sector_perf.sort_values("total_return").plot(
            kind="barh", y="total_return", ax=ax,
            color=["#d32f2f" if v < 0 else "#388e3c" for v in
                   sector_perf.sort_values("total_return")["total_return"]],
            legend=False,
        )
        ax.set_title("策略A 各板块平均收益")
        ax.set_xlabel("平均收益")

    # (4) 趋势持续天数 vs 收益的关系
    ax = axes[1][1]
    strat_a = bt_df[(bt_df["strategy"] == "策略A_趋势跟随") & (bt_df["n_trades"] > 0)]
    if len(strat_a) > 0:
        for sector in strat_a["sector"].unique():
            sdf = strat_a[strat_a["sector"] == sector]
            ax.scatter(sdf["signal_freq"], sdf["total_return"],
                       label=sector, s=40, alpha=0.7)
        ax.set_xlabel("信号频率 (交易日占比)")
        ax.set_ylabel("总收益")
        ax.set_title("信号频率 vs 总收益")
        ax.axhline(0, color="black", linewidth=0.5)
        ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "backtest_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  → 保存: output2/backtest_comparison.png")


def plot_sector_heatmap(conc_df: pd.DataFrame, prob_df: pd.DataFrame):
    """板块热力图"""
    mf_conc = conc_df[conc_df["field"] == "main_force"]
    if len(mf_conc) == 0:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # 共振度热力图
    ax = axes[0]
    sector_conc = mf_conc.groupby("sector").agg(
        direction_match=("direction_match", "mean"),
        overlap_ratio=("overlap_ratio", "mean"),
        n_segments=("direction_match", "count"),
    )
    data = sector_conc[["direction_match", "overlap_ratio"]].values
    im = ax.imshow(data, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)
    ax.set_yticks(range(len(sector_conc)))
    ax.set_yticklabels(sector_conc.index, fontsize=9)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["方向一致率", "趋势重叠度"], fontsize=9)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, f"{data[i, j]:.0%}", ha="center", va="center", fontsize=10)
    ax.set_title("各板块趋势共振度", fontsize=11)
    plt.colorbar(im, ax=ax, shrink=0.7)

    # 条件概率效应热力图
    ax = axes[1]
    valid_h2 = prob_df[prob_df["H2_n_events"] > 0]
    if len(valid_h2) > 0:
        valid_h2 = valid_h2.copy()
        valid_h2["H2_effect"] = valid_h2["P_B_base"] - valid_h2["P_B_given_A"]
        sector_effect = valid_h2.groupby("sector")["H2_effect"].mean()

        valid_h3 = prob_df[prob_df["H3_n_events"] > 0].copy()
        if len(valid_h3) > 0:
            valid_h3["H3_effect"] = valid_h3["P_D_base"] - valid_h3["P_D_given_C"]
            sector_h3 = valid_h3.groupby("sector")["H3_effect"].mean()
        else:
            sector_h3 = pd.Series(dtype=float)

        all_sectors = sorted(set(sector_effect.index) | set(sector_h3.index))
        data2 = np.array([
            [sector_effect.get(s, 0) for s in all_sectors],
            [sector_h3.get(s, 0) for s in all_sectors],
        ]).T
        im2 = ax.imshow(data2, cmap="RdYlGn", aspect="auto", vmin=-0.5, vmax=0.5)
        ax.set_yticks(range(len(all_sectors)))
        ax.set_yticklabels(all_sectors, fontsize=9)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["H2效应\n(底部保护)", "H3效应\n(顶部保护)"], fontsize=9)
        for i in range(data2.shape[0]):
            for j in range(data2.shape[1]):
                ax.text(j, i, f"{data2[i, j]:+.0%}", ha="center", va="center", fontsize=10)
        ax.set_title("各板块条件概率效应 (正=保护有效)", fontsize=11)
        plt.colorbar(im2, ax=ax, shrink=0.7)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "sector_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  → 保存: output2/sector_heatmap.png")


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  计划2：基于主力资金趋势的价格共振研究")
    print("=" * 60)

    df = load_data()
    print(f"[数据加载] {len(df)} 行, {df['variety_id'].nunique()} 个品种")

    # 阶段一
    seg_df = run_phase1(df)

    # 阶段二
    conc_df = run_phase2(df, seg_df)

    # 阶段三
    prob_df = run_phase3(df, seg_df)

    # 敏感性分析
    sens_df = run_sensitivity(df, _run_phase1_with_params, _run_phase3_silent)

    # 阶段四
    bt_df = run_phase4(df, seg_df)

    # 阶段五
    print(f"\n[阶段五] 生成可视化...")
    plot_trend_annotated(df, seg_df, conc_df)
    plot_cond_prob_comparison(prob_df)
    plot_backtest_comparison(bt_df)
    plot_sector_heatmap(conc_df, prob_df)

    # 保存 CSV
    seg_df.to_csv(OUTPUT_DIR / "trend_segments.csv", index=False, encoding="utf-8-sig")
    conc_df.to_csv(OUTPUT_DIR / "concordance_results.csv", index=False, encoding="utf-8-sig")
    prob_df.to_csv(OUTPUT_DIR / "conditional_prob.csv", index=False, encoding="utf-8-sig")
    sens_df.to_csv(OUTPUT_DIR / "sensitivity_analysis.csv", index=False, encoding="utf-8-sig")
    bt_df.to_csv(OUTPUT_DIR / "backtest_trend.csv", index=False, encoding="utf-8-sig")
    print("  → 保存: CSV 数据文件")

    # ─── 详细结果汇总 ───
    print("\n" + "=" * 60)
    print("  详细结果汇总")
    print("=" * 60)

    # 趋势段统计
    mf_seg = seg_df[seg_df["field"] == "main_force"]
    print(f"\n--- main_force 趋势段统计 ---")
    print(f"  总段数: {len(mf_seg)}")
    print(f"  上升段: {len(mf_seg[mf_seg['direction'] == 'up'])}, "
          f"下降段: {len(mf_seg[mf_seg['direction'] == 'down'])}")
    print(f"  平均持续天数: {mf_seg['duration'].mean():.1f}")
    print(f"  每品种平均段数: {len(mf_seg) / df['variety_id'].nunique():.1f}")

    # 共振分析汇总
    mf_conc = conc_df[conc_df["field"] == "main_force"] if len(conc_df) > 0 else pd.DataFrame()
    if len(mf_conc) > 0:
        print(f"\n--- 趋势共振汇总 (main_force) ---")
        print(f"  整体方向一致率: {mf_conc['direction_match'].mean():.2%}")
        print(f"  整体趋势重叠度: {mf_conc['overlap_ratio'].mean():.2%}")

        print(f"\n  按品种 TOP10 方向一致率:")
        v_match = mf_conc.groupby("variety_name")["direction_match"].mean().sort_values(ascending=False)
        for name, val in v_match.head(10).items():
            n_seg = len(mf_conc[mf_conc["variety_name"] == name])
            print(f"    {name}: {val:.0%} ({n_seg} 段)")

    # 条件概率汇总
    print(f"\n--- 条件概率检验汇总 ---")
    valid_h2 = prob_df[prob_df["H2_n_events"] > 0]
    if len(valid_h2) > 0:
        print(f"  H2 (底部回升保护):")
        for _, r in valid_h2.iterrows():
            effect = r["P_B_base"] - r["P_B_given_A"] if not np.isnan(r["P_B_given_A"]) else np.nan
            sig = "★" if r["H2_fisher_p"] < 0.05 else ""
            print(f"    {r['variety_name']}: P(新低|回升)={r['P_B_given_A']:.0%} vs "
                  f"P(新低|无条件)={r['P_B_base']:.0%}, "
                  f"效应={effect:+.0%}, p={r['H2_fisher_p']:.3f} {sig}")

    valid_h3 = prob_df[prob_df["H3_n_events"] > 0]
    if len(valid_h3) > 0:
        print(f"  H3 (顶部回落保护):")
        for _, r in valid_h3.iterrows():
            effect = r["P_D_base"] - r["P_D_given_C"] if not np.isnan(r["P_D_given_C"]) else np.nan
            sig = "★" if r["H3_fisher_p"] < 0.05 else ""
            print(f"    {r['variety_name']}: P(新高|回落)={r['P_D_given_C']:.0%} vs "
                  f"P(新高|无条件)={r['P_D_base']:.0%}, "
                  f"效应={effect:+.0%}, p={r['H3_fisher_p']:.3f} {sig}")

    # 策略回测汇总
    print(f"\n--- 策略回测 TOP 品种 ---")
    for strat in bt_df["strategy"].unique():
        sdf = bt_df[(bt_df["strategy"] == strat) & (bt_df["n_trades"] > 0)]
        if len(sdf) == 0:
            continue
        print(f"\n  {strat}:")
        top5 = sdf.sort_values("total_return", ascending=False).head(5)
        for _, r in top5.iterrows():
            print(f"    {r['variety_name']} [{r['sector']}]: 胜率={r['win_rate']:.1%}, "
                  f"总收益={r['total_return']:+.4f}, 盈亏比={r['profit_loss_ratio']:.2f}")

    # 敏感性分析汇总
    print(f"\n--- 敏感性分析汇总 ---")
    print(sens_df.to_string(index=False))

    print("\n" + "=" * 60)
    print("  计划2分析完成! 输出文件在 output2/ 目录")
    print("=" * 60)


if __name__ == "__main__":
    main()
