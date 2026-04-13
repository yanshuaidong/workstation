"""
计划3：资金曲线微分特征与价格趋势关系研究
从微积分视角切入：提取 main_force / retail 的一阶导（斜率）和二阶导（加速度），
研究这些微分特征与价格趋势之间的量化关系，设计并回测 D~G 四种微分信号策略。
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
OUTPUT_DIR = BASE_DIR / "output3"
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
# 阶段一：离散微分特征计算
# ═══════════════════════════════════════════════════════════════

def calc_derivative_features(df: pd.DataFrame) -> pd.DataFrame:
    """对每个品种的 main_force 和 retail 计算一阶导、二阶导及派生特征"""
    all_rows = []

    for vid, g in df.groupby("variety_id"):
        g = g.sort_values("trade_date").reset_index(drop=True)
        n = len(g)
        if n < 4:
            continue

        mf = g["main_force"].values.astype(float)
        rt = g["retail"].values.astype(float)
        prices = g["close_price"].values.astype(float)
        price_ret = np.full(n, np.nan)
        price_ret[1:] = np.diff(prices) / prices[:-1]

        # 未来 1/3/5 日收益率
        fut_ret_1 = np.full(n, np.nan)
        fut_ret_3 = np.full(n, np.nan)
        fut_ret_5 = np.full(n, np.nan)
        for t in range(n):
            if t + 1 < n:
                fut_ret_1[t] = (prices[t + 1] - prices[t]) / prices[t]
            if t + 3 < n:
                fut_ret_3[t] = (prices[t + 3] - prices[t]) / prices[t]
            if t + 5 < n:
                fut_ret_5[t] = (prices[t + 5] - prices[t]) / prices[t]

        for field, vals in [("main", mf), ("retail", rt)]:
            slope_1 = np.full(n, np.nan)
            slope_2 = np.full(n, np.nan)
            accel = np.full(n, np.nan)
            accel_smooth = np.full(n, np.nan)

            # slope_1: f[t] - f[t-1]
            slope_1[1:] = np.diff(vals)

            # slope_2: (f[t+1] - f[t-1]) / 2  (中心差分)
            for t in range(1, n - 1):
                slope_2[t] = (vals[t + 1] - vals[t - 1]) / 2.0

            # accel: slope_1[t] - slope_1[t-1] = f[t] - 2*f[t-1] + f[t-2]
            for t in range(2, n):
                accel[t] = slope_1[t] - slope_1[t - 1]

            # accel_smooth: slope_2[t] - slope_2[t-1]
            for t in range(2, n - 1):
                if not np.isnan(slope_2[t]) and not np.isnan(slope_2[t - 1]):
                    accel_smooth[t] = slope_2[t] - slope_2[t - 1]

            # 移动均值平滑
            slope_ma3 = pd.Series(slope_1).rolling(3, min_periods=1).mean().values
            slope_ma5 = pd.Series(slope_1).rolling(5, min_periods=1).mean().values

            slope_sign = np.sign(slope_1)
            accel_sign = np.sign(accel)

            # 四象限状态
            quadrant = np.full(n, "", dtype=object)
            for t in range(n):
                ss = slope_sign[t]
                acs = accel_sign[t]
                if np.isnan(ss) or np.isnan(acs):
                    quadrant[t] = "未知"
                elif ss > 0 and acs > 0:
                    quadrant[t] = "加速上升"
                elif ss > 0 and acs < 0:
                    quadrant[t] = "减速上升"
                elif ss < 0 and acs < 0:
                    quadrant[t] = "加速下降"
                elif ss < 0 and acs > 0:
                    quadrant[t] = "减速下降"
                elif ss == 0:
                    quadrant[t] = "持平"
                else:
                    quadrant[t] = "匀速"

            prefix = field
            for t in range(n):
                if t == 0 and len(all_rows) < n * vid:
                    pass
                row_key = (vid, t)
                row_data = {
                    f"{prefix}_slope_1": slope_1[t],
                    f"{prefix}_slope_2": slope_2[t],
                    f"{prefix}_accel": accel[t],
                    f"{prefix}_accel_smooth": accel_smooth[t],
                    f"{prefix}_slope_ma3": slope_ma3[t],
                    f"{prefix}_slope_ma5": slope_ma5[t],
                    f"{prefix}_slope_sign": slope_sign[t],
                    f"{prefix}_accel_sign": accel_sign[t],
                    f"{prefix}_quadrant": quadrant[t],
                }
                if field == "main":
                    row_data.update({
                        "variety_id": vid,
                        "variety_name": g.iloc[t]["variety_name"],
                        "sector": g.iloc[t]["sector"],
                        "trade_date": g.iloc[t]["trade_date"],
                        "main_force": mf[t],
                        "retail": rt[t],
                        "close_price": prices[t],
                        "price_return": price_ret[t],
                        "fut_ret_1": fut_ret_1[t],
                        "fut_ret_3": fut_ret_3[t],
                        "fut_ret_5": fut_ret_5[t],
                    })
                    all_rows.append(row_data)
                else:
                    all_rows[len(all_rows) - n + t].update(row_data)

    feat_df = pd.DataFrame(all_rows)

    # 主散斜率差
    feat_df["slope_diff"] = feat_df["main_slope_1"] - feat_df["retail_slope_1"]
    feat_df["slope_diverge"] = (
        np.sign(feat_df["main_slope_1"]) != np.sign(feat_df["retail_slope_1"])
    ).astype(int)
    feat_df["diverge_strength"] = np.where(
        feat_df["slope_diverge"] == 1,
        feat_df["main_slope_1"].abs() + feat_df["retail_slope_1"].abs(),
        0,
    )

    print(f"[阶段一] 微分特征计算完成: {len(feat_df)} 行, {feat_df['variety_id'].nunique()} 个品种")

    # 四象限分布统计
    quad_cols = ["main_quadrant", "retail_quadrant"]
    for col in quad_cols:
        vc = feat_df[col].value_counts()
        print(f"  {col} 分布:")
        for q, cnt in vc.items():
            print(f"    {q}: {cnt} ({cnt / len(feat_df):.1%})")

    return feat_df


# ═══════════════════════════════════════════════════════════════
# 阶段二：微分特征与价格关联分析
# ═══════════════════════════════════════════════════════════════

def run_correlation_analysis(feat_df: pd.DataFrame) -> pd.DataFrame:
    """2.1 基础相关性分析"""
    corr_pairs = [
        ("main_slope_1", "price_return", "主力斜率 vs 当日收益率"),
        ("main_slope_1", "fut_ret_1", "主力斜率 vs 次日收益率"),
        ("main_slope_2", "fut_ret_1", "跳点斜率 vs 次日收益率"),
        ("main_accel", "fut_ret_1", "加速度 vs 次日收益率"),
        ("retail_slope_1", "fut_ret_1", "散户斜率 vs 次日收益率"),
        ("slope_diff", "fut_ret_1", "主散斜率差 vs 次日收益率"),
        ("main_slope_ma3", "fut_ret_1", "主力3日平滑斜率 vs 次日收益率"),
        ("main_slope_ma5", "fut_ret_1", "主力5日平滑斜率 vs 次日收益率"),
    ]

    records = []
    for vid, g in feat_df.groupby("variety_id"):
        name = g.iloc[0]["variety_name"]
        sector = g.iloc[0]["sector"]
        for x_col, y_col, desc in corr_pairs:
            valid = g[[x_col, y_col]].dropna()
            if len(valid) < 5:
                continue
            r, p = stats.pearsonr(valid[x_col], valid[y_col])
            records.append({
                "variety_id": vid,
                "variety_name": name,
                "sector": sector,
                "x_feature": x_col,
                "y_feature": y_col,
                "description": desc,
                "pearson_r": r,
                "p_value": p,
                "n_obs": len(valid),
            })

    corr_df = pd.DataFrame(records)

    print(f"\n[阶段二-2.1] 相关性分析完成 ({len(corr_df)} 组)")
    for desc in corr_df["description"].unique():
        sub = corr_df[corr_df["description"] == desc]
        avg_r = sub["pearson_r"].mean()
        n_sig = (sub["p_value"] < 0.05).sum()
        print(f"  {desc}: 平均r={avg_r:.4f}, 显著品种={n_sig}/{len(sub)}")

    return corr_df


def run_quadrant_returns(feat_df: pd.DataFrame) -> pd.DataFrame:
    """2.2 四象限条件收益率分析"""
    quadrants = ["加速上升", "减速上升", "加速下降", "减速下降"]
    records = []

    for vid, g in feat_df.groupby("variety_id"):
        name = g.iloc[0]["variety_name"]
        sector = g.iloc[0]["sector"]

        for q in quadrants:
            mask = g["main_quadrant"] == q
            sub = g[mask]
            if len(sub) < 2:
                records.append({
                    "variety_id": vid, "variety_name": name, "sector": sector,
                    "quadrant": q, "n_days": len(sub),
                    "avg_fut_ret_1": np.nan, "avg_fut_ret_3": np.nan,
                    "positive_prob_1": np.nan, "positive_prob_3": np.nan,
                })
                continue

            fr1 = sub["fut_ret_1"].dropna()
            fr3 = sub["fut_ret_3"].dropna()

            records.append({
                "variety_id": vid, "variety_name": name, "sector": sector,
                "quadrant": q, "n_days": len(sub),
                "avg_fut_ret_1": fr1.mean() if len(fr1) > 0 else np.nan,
                "avg_fut_ret_3": fr3.mean() if len(fr3) > 0 else np.nan,
                "positive_prob_1": (fr1 > 0).mean() if len(fr1) > 0 else np.nan,
                "positive_prob_3": (fr3 > 0).mean() if len(fr3) > 0 else np.nan,
            })

    quad_df = pd.DataFrame(records)

    # 汇总统计
    print(f"\n[阶段二-2.2] 四象限条件收益率分析完成")
    for q in quadrants:
        sub = quad_df[quad_df["quadrant"] == q]
        valid = sub.dropna(subset=["avg_fut_ret_1"])
        if len(valid) == 0:
            continue
        avg_r1 = valid["avg_fut_ret_1"].mean()
        avg_r3 = valid["avg_fut_ret_3"].mean()
        avg_pp = valid["positive_prob_1"].mean()
        print(f"  {q}: 平均次日收益={avg_r1:.4%}, 平均3日收益={avg_r3:.4%}, "
              f"正收益概率={avg_pp:.2%}, N={valid['n_days'].sum()}")

    # Kruskal-Wallis 检验
    all_groups = []
    for q in quadrants:
        vals = feat_df[feat_df["main_quadrant"] == q]["fut_ret_1"].dropna().values
        if len(vals) > 0:
            all_groups.append(vals)

    if len(all_groups) >= 2:
        h_stat, kw_p = stats.kruskal(*all_groups)
        print(f"\n  Kruskal-Wallis 检验: H={h_stat:.3f}, p={kw_p:.6f}")

        # 两两对比
        pairs = [("加速上升", "加速下降"), ("减速上升", "加速上升"),
                 ("减速下降", "加速下降")]
        for q1, q2 in pairs:
            g1 = feat_df[feat_df["main_quadrant"] == q1]["fut_ret_1"].dropna()
            g2 = feat_df[feat_df["main_quadrant"] == q2]["fut_ret_1"].dropna()
            if len(g1) >= 3 and len(g2) >= 3:
                u_stat, mw_p = stats.mannwhitneyu(g1, g2, alternative="two-sided")
                print(f"  {q1} vs {q2}: U={u_stat:.1f}, p={mw_p:.6f}, "
                      f"均值差={g1.mean() - g2.mean():.4%}")

    return quad_df


def run_inflection_analysis(feat_df: pd.DataFrame) -> pd.DataFrame:
    """2.3 拐点检测与价格反转分析"""
    records = []

    for vid, g in feat_df.groupby("variety_id"):
        g = g.sort_values("trade_date").reset_index(drop=True)
        name = g.iloc[0]["variety_name"]
        sector = g.iloc[0]["sector"]
        n = len(g)

        slope = g["main_slope_1"].values
        accel = g["main_accel"].values
        prices = g["close_price"].values

        for t in range(2, n - 1):
            if np.isnan(accel[t]) or np.isnan(accel[t - 1]):
                continue
            if np.isnan(slope[t]):
                continue

            inflection_type = None

            # 上升拐点：加速上升 → 减速上升
            if accel[t - 1] > 0 and accel[t] < 0 and slope[t] > 0:
                inflection_type = "上升拐点"
            # 下降拐点：加速下降 → 减速下降
            elif accel[t - 1] < 0 and accel[t] > 0 and slope[t] < 0:
                inflection_type = "下降拐点"

            # 趋势启动点：减速下降 → 加速上升
            if t >= 2 and not np.isnan(slope[t - 1]):
                if (slope[t - 1] < 0 and accel[t - 1] > 0 and
                        slope[t] > 0 and accel[t] > 0):
                    inflection_type = "趋势启动点"
                elif (slope[t - 1] > 0 and accel[t - 1] < 0 and
                      slope[t] < 0 and accel[t] < 0):
                    inflection_type = "趋势终结点"

            if inflection_type is None:
                continue

            fr1 = (prices[t + 1] - prices[t]) / prices[t] if t + 1 < n else np.nan
            fr3 = (prices[min(t + 3, n - 1)] - prices[t]) / prices[t] if t + 3 <= n else np.nan
            fr5 = (prices[min(t + 5, n - 1)] - prices[t]) / prices[t] if t + 5 <= n else np.nan

            records.append({
                "variety_id": vid,
                "variety_name": name,
                "sector": sector,
                "trade_date": g.iloc[t]["trade_date"],
                "inflection_type": inflection_type,
                "slope_at_point": slope[t],
                "accel_at_point": accel[t],
                "price_at_point": prices[t],
                "fut_ret_1": fr1,
                "fut_ret_3": fr3,
                "fut_ret_5": fr5,
            })

    infl_df = pd.DataFrame(records)

    print(f"\n[阶段二-2.3] 拐点检测完成: {len(infl_df)} 个拐点")
    if len(infl_df) > 0:
        # 无条件基准
        base_fr1 = feat_df["fut_ret_1"].dropna().mean()
        print(f"  无条件基准: 平均次日收益={base_fr1:.4%}")

        for itype in infl_df["inflection_type"].unique():
            sub = infl_df[infl_df["inflection_type"] == itype]
            avg1 = sub["fut_ret_1"].dropna().mean()
            avg3 = sub["fut_ret_3"].dropna().mean()
            avg5 = sub["fut_ret_5"].dropna().mean()
            print(f"  {itype} ({len(sub)}个): "
                  f"1日={avg1:.4%}, 3日={avg3:.4%}, 5日={avg5:.4%}")

            # 拐点后价格是否确实反转
            if itype in ("上升拐点", "趋势终结点"):
                reversal_rate = (sub["fut_ret_1"].dropna() < 0).mean()
                print(f"    → 后续下跌比例: {reversal_rate:.2%}")
            elif itype in ("下降拐点", "趋势启动点"):
                reversal_rate = (sub["fut_ret_1"].dropna() > 0).mean()
                print(f"    → 后续上涨比例: {reversal_rate:.2%}")

    return infl_df


# ═══════════════════════════════════════════════════════════════
# 阶段三：主力与散户微分特征的对比分析
# ═══════════════════════════════════════════════════════════════

def run_divergence_analysis(feat_df: pd.DataFrame) -> pd.DataFrame:
    """3.1 & 3.2 主散斜率背离分析"""
    records = []

    # 分场景分析：主散斜率同向/背离时的收益率
    scenarios = [
        ("主多散空", lambda r: r["main_slope_sign"] > 0 and r["retail_slope_sign"] < 0),
        ("主空散多", lambda r: r["main_slope_sign"] < 0 and r["retail_slope_sign"] > 0),
        ("双方做多", lambda r: r["main_slope_sign"] > 0 and r["retail_slope_sign"] > 0),
        ("双方做空", lambda r: r["main_slope_sign"] < 0 and r["retail_slope_sign"] < 0),
    ]

    for vid, g in feat_df.groupby("variety_id"):
        name = g.iloc[0]["variety_name"]
        sector = g.iloc[0]["sector"]
        valid = g.dropna(subset=["main_slope_sign", "retail_slope_sign", "fut_ret_1"])

        for scenario_name, cond_func in scenarios:
            mask = valid.apply(cond_func, axis=1)
            sub = valid[mask]
            if len(sub) < 2:
                records.append({
                    "variety_id": vid, "variety_name": name, "sector": sector,
                    "scenario": scenario_name, "n_days": len(sub),
                    "avg_fut_ret_1": np.nan, "avg_fut_ret_3": np.nan,
                    "positive_prob": np.nan,
                })
                continue

            records.append({
                "variety_id": vid, "variety_name": name, "sector": sector,
                "scenario": scenario_name, "n_days": len(sub),
                "avg_fut_ret_1": sub["fut_ret_1"].mean(),
                "avg_fut_ret_3": sub["fut_ret_3"].dropna().mean() if len(sub["fut_ret_3"].dropna()) > 0 else np.nan,
                "positive_prob": (sub["fut_ret_1"] > 0).mean(),
            })

    div_df = pd.DataFrame(records)

    print(f"\n[阶段三] 主散微分背离分析完成")
    for sc in ["主多散空", "主空散多", "双方做多", "双方做空"]:
        sub = div_df[(div_df["scenario"] == sc) & (div_df["n_days"] >= 2)]
        if len(sub) == 0:
            continue
        avg_r = sub["avg_fut_ret_1"].mean()
        avg_pp = sub["positive_prob"].mean()
        total_days = sub["n_days"].sum()
        print(f"  {sc}: 平均次日收益={avg_r:.4%}, 正收益概率={avg_pp:.2%}, "
              f"总天数={total_days}")

    # 主散加速度对比
    print(f"\n  --- 主散加速度特征对比 ---")
    accel_scenarios = [
        ("主力加速+散户减速",
         feat_df["main_accel"].notna() & feat_df["retail_accel"].notna() &
         (feat_df["main_accel"] > 0) & (feat_df["retail_accel"] < 0)),
        ("主力减速+散户加速",
         feat_df["main_accel"].notna() & feat_df["retail_accel"].notna() &
         (feat_df["main_accel"] < 0) & (feat_df["retail_accel"] > 0)),
        ("双方加速",
         feat_df["main_accel"].notna() & feat_df["retail_accel"].notna() &
         (feat_df["main_accel"] > 0) & (feat_df["retail_accel"] > 0)),
    ]
    for label, mask in accel_scenarios:
        sub = feat_df[mask]
        fr1 = sub["fut_ret_1"].dropna()
        if len(fr1) > 0:
            print(f"  {label}: 平均次日收益={fr1.mean():.4%}, "
                  f"正收益概率={(fr1 > 0).mean():.2%}, N={len(fr1)}")

    # 背离持续天数分析
    print(f"\n  --- 背离持续天数与后续收益 ---")
    for vid, g in feat_df.groupby("variety_id"):
        g = g.sort_values("trade_date").reset_index(drop=True)
        g_local = g.copy()
        g_local["diverge_streak"] = 0
        streak = 0
        for i in range(len(g_local)):
            if g_local.iloc[i]["slope_diverge"] == 1:
                streak += 1
            else:
                streak = 0
            g_local.iloc[i, g_local.columns.get_loc("diverge_streak")] = streak
        feat_df.loc[g_local.index, "diverge_streak"] = g_local["diverge_streak"].values

    for dur in [1, 2, 3]:
        sub = feat_df[feat_df["diverge_streak"] >= dur]
        fr1 = sub["fut_ret_1"].dropna()
        if len(fr1) > 0:
            print(f"  背离持续≥{dur}天: 平均次日收益={fr1.mean():.4%}, N={len(fr1)}")

    return div_df


# ═══════════════════════════════════════════════════════════════
# 阶段四：微分信号策略设计与回测
# ═══════════════════════════════════════════════════════════════

def run_backtest(feat_df: pd.DataFrame) -> pd.DataFrame:
    """策略 D~G 回测"""
    bt_records = []

    for vid, g in feat_df.groupby("variety_id"):
        g = g.sort_values("trade_date").reset_index(drop=True)
        name = g.iloc[0]["variety_name"]
        sector = g.iloc[0]["sector"]
        n = len(g)
        if n < 8:
            continue

        prices = g["close_price"].values
        daily_ret = np.full(n, np.nan)
        daily_ret[1:] = np.diff(prices) / prices[:-1]

        quadrant = g["main_quadrant"].values
        slope_sign = g["main_slope_sign"].values
        accel_val = g["main_accel"].values
        slope_1 = g["main_slope_1"].values
        slope_ma3 = g["main_slope_ma3"].values
        retail_slope = g["retail_slope_1"].values
        retail_slope_sign = g["retail_slope_sign"].values
        slope_diff = g["slope_diff"].values

        # ─── 策略 D: 加速度信号策略 ───
        signal_d = np.zeros(n)
        for t in range(3, n):
            if quadrant[t] in ("加速上升",) and quadrant[t - 1] in ("加速上升",):
                signal_d[t] = 1
            elif quadrant[t] in ("加速下降",) and quadrant[t - 1] in ("加速下降",):
                signal_d[t] = -1

        # ─── 策略 E: 拐点反转策略 ───
        signal_e = np.zeros(n)
        for t in range(2, n):
            if np.isnan(slope_sign[t]) or np.isnan(slope_sign[t - 1]):
                continue
            if np.isnan(accel_val[t]) or np.isnan(accel_val[t - 1]):
                continue

            # 趋势启动点 → 做多 (持仓5天)
            if (slope_sign[t - 1] < 0 and accel_val[t - 1] > 0 and
                    slope_sign[t] > 0 and accel_val[t] > 0):
                for k in range(t, min(t + 5, n)):
                    if signal_e[k] == 0:
                        signal_e[k] = 1

            # 趋势终结点 → 做空 (持仓5天)
            if (slope_sign[t - 1] > 0 and accel_val[t - 1] < 0 and
                    slope_sign[t] < 0 and accel_val[t] < 0):
                for k in range(t, min(t + 5, n)):
                    if signal_e[k] == 0:
                        signal_e[k] = -1

        # ─── 策略 F: 主散微分背离策略 ───
        signal_f = np.zeros(n)
        for t in range(3, n):
            if np.isnan(slope_sign[t]) or np.isnan(retail_slope_sign[t]):
                continue
            main_pos = slope_sign[t] > 0 and slope_sign[t - 1] > 0
            retail_neg = retail_slope_sign[t] < 0 and retail_slope_sign[t - 1] < 0
            main_neg = slope_sign[t] < 0 and slope_sign[t - 1] < 0
            retail_pos = retail_slope_sign[t] > 0 and retail_slope_sign[t - 1] > 0

            if main_pos and retail_neg:
                signal_f[t] = 1
            elif main_neg and retail_pos:
                signal_f[t] = -1

        # ─── 策略 G: 综合微分信号策略 ───
        signal_g = np.zeros(n)
        valid_mask = (~np.isnan(slope_ma3)) & (~np.isnan(accel_val)) & (~np.isnan(slope_diff))
        valid_idx = np.where(valid_mask)[0]

        if len(valid_idx) > 3:
            s1 = slope_ma3[valid_idx]
            s2 = accel_val[valid_idx]
            s3 = slope_diff[valid_idx]

            def safe_normalize(arr):
                std = np.std(arr)
                if std < 1e-12:
                    return np.zeros_like(arr)
                return (arr - np.mean(arr)) / std

            n1 = safe_normalize(s1)
            n2 = safe_normalize(s2)
            n3 = safe_normalize(s3)

            score = (n1 + n2 + n3) / 3.0
            threshold = 0.5

            for i, idx in enumerate(valid_idx):
                if score[i] > threshold:
                    signal_g[idx] = 1
                elif score[i] < -threshold:
                    signal_g[idx] = -1

        # 回测各策略
        for strat_name, signal in [
            ("策略D_加速度信号", signal_d),
            ("策略E_拐点反转", signal_e),
            ("策略F_主散背离", signal_f),
            ("策略G_综合微分", signal_g),
        ]:
            pos = signal[:-1]
            ret = daily_ret[1:]
            strat_ret = pos * ret
            valid_ret = strat_ret[~np.isnan(strat_ret)]
            trades = int(np.sum(pos != 0))

            if trades == 0:
                bt_records.append({
                    "variety_id": vid, "variety_name": name, "sector": sector,
                    "strategy": strat_name, "n_trades": 0, "win_rate": np.nan,
                    "total_return": 0, "avg_return": 0, "profit_loss_ratio": np.nan,
                    "max_drawdown": 0, "signal_freq": 0,
                })
                continue

            active_ret = strat_ret[pos != 0]
            active_ret = active_ret[~np.isnan(active_ret)]
            if len(active_ret) == 0:
                bt_records.append({
                    "variety_id": vid, "variety_name": name, "sector": sector,
                    "strategy": strat_name, "n_trades": trades, "win_rate": np.nan,
                    "total_return": 0, "avg_return": 0, "profit_loss_ratio": np.nan,
                    "max_drawdown": 0, "signal_freq": trades / (n - 1),
                })
                continue

            wins = int(np.sum(active_ret > 0))
            win_rate = wins / len(active_ret)
            total_ret = float(np.nansum(valid_ret))
            avg_ret = float(np.mean(active_ret))

            win_rets = active_ret[active_ret > 0]
            loss_rets = active_ret[active_ret < 0]
            avg_win = float(np.mean(win_rets)) if len(win_rets) > 0 else 0
            avg_loss = float(np.mean(np.abs(loss_rets))) if len(loss_rets) > 0 else 1e-9
            plr = avg_win / avg_loss if avg_loss > 1e-9 else np.inf

            cum = np.nancumsum(valid_ret)
            max_dd = float(np.min(cum - np.maximum.accumulate(cum)))

            bt_records.append({
                "variety_id": vid, "variety_name": name, "sector": sector,
                "strategy": strat_name, "n_trades": trades, "win_rate": win_rate,
                "total_return": total_ret, "avg_return": avg_ret,
                "profit_loss_ratio": plr, "max_drawdown": max_dd,
                "signal_freq": trades / (n - 1),
            })

    bt_df = pd.DataFrame(bt_records)

    print(f"\n[阶段四] 策略回测完成 ({len(bt_df)} 条记录)")
    for strat in bt_df["strategy"].unique():
        sdf = bt_df[(bt_df["strategy"] == strat) & (bt_df["n_trades"] > 0)]
        if len(sdf) == 0:
            print(f"  {strat}: 无有效交易")
            continue
        avg_wr = sdf["win_rate"].mean()
        avg_ret = sdf["total_return"].mean()
        n_pos = (sdf["total_return"] > 0).sum()
        print(f"  {strat}: 平均胜率={avg_wr:.2%}, 平均总收益={avg_ret:.4f}, "
              f"盈利品种={n_pos}/{len(sdf)}")

    # 按板块
    for strat in bt_df["strategy"].unique():
        sdf = bt_df[(bt_df["strategy"] == strat) & (bt_df["n_trades"] > 0)]
        if len(sdf) == 0:
            continue
        print(f"\n  --- {strat} 按板块 ---")
        for sector, gp in sdf.groupby("sector"):
            print(f"    {sector}: 平均胜率={gp['win_rate'].mean():.2%}, "
                  f"平均收益={gp['total_return'].mean():.4f}, N={len(gp)}")

    # 与计划1/2对比
    print(f"\n  === 与计划1/2策略对比 ===")
    print(f"  计划1 综合信号: 平均胜率=51.74%, 盈利品种=31/55 (56%)")
    print(f"  计划2 策略A:    平均胜率=52.01%, 盈利品种=35/55 (64%)")
    for strat in bt_df["strategy"].unique():
        sdf = bt_df[(bt_df["strategy"] == strat) & (bt_df["n_trades"] > 0)]
        if len(sdf) == 0:
            continue
        avg_wr = sdf["win_rate"].mean()
        n_pos = (sdf["total_return"] > 0).sum()
        print(f"  计划3 {strat}: 平均胜率={avg_wr:.2%}, 盈利品种={n_pos}/{len(sdf)} "
              f"({n_pos / len(sdf):.0%})")

    return bt_df


# ═══════════════════════════════════════════════════════════════
# 阶段五：可视化
# ═══════════════════════════════════════════════════════════════

def plot_derivative_timeseries(feat_df: pd.DataFrame):
    """微分特征时序图（TOP10品种）"""
    # 选取相关性最强的品种
    variety_abs_corr = feat_df.groupby("variety_id").apply(
        lambda g: g[["main_slope_1", "fut_ret_1"]].dropna().apply(
            lambda x: abs(stats.pearsonr(x.iloc[:, 0], x.iloc[:, 1])[0])
            if len(x) >= 5 else 0, axis=1
        ).mean() if len(g[["main_slope_1", "fut_ret_1"]].dropna()) >= 5 else 0
    )
    # Fallback: just pick the first 10 varieties with most data
    top_ids = feat_df.groupby("variety_id").size().sort_values(ascending=False).head(10).index.tolist()

    fig, axes = plt.subplots(10, 4, figsize=(28, 40))

    quadrant_colors = {
        "加速上升": "#2e7d32", "减速上升": "#81c784",
        "加速下降": "#c62828", "减速下降": "#ef9a9a",
        "持平": "#9e9e9e", "匀速": "#9e9e9e", "未知": "#e0e0e0",
    }

    for row, vid in enumerate(top_ids[:10]):
        g = feat_df[feat_df["variety_id"] == vid].sort_values("trade_date")
        name = g.iloc[0]["variety_name"]
        dates = g["trade_date"]

        # (1) 价格
        ax = axes[row][0]
        ax.plot(dates, g["close_price"], "k-", linewidth=1)
        ax.set_ylabel("价格", fontsize=8)
        ax.set_title(f"{name} - 收盘价", fontsize=9)
        ax.tick_params(axis="x", rotation=45, labelsize=6)

        # (2) main_force 原值
        ax = axes[row][1]
        ax.plot(dates, g["main_force"], "b-", linewidth=0.8, alpha=0.7)
        ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
        ax.set_ylabel("main_force", fontsize=8)
        ax.set_title(f"{name} - 主力资金", fontsize=9)
        ax.tick_params(axis="x", rotation=45, labelsize=6)

        # (3) 一阶导（斜率）
        ax = axes[row][2]
        colors = [quadrant_colors.get(q, "#9e9e9e") for q in g["main_quadrant"]]
        ax.bar(dates, g["main_slope_1"], color=colors, width=0.8)
        ax.axhline(0, color="gray", linewidth=0.5)
        ax.set_ylabel("slope_1", fontsize=8)
        ax.set_title(f"{name} - 一阶导(斜率)", fontsize=9)
        ax.tick_params(axis="x", rotation=45, labelsize=6)

        # (4) 二阶导（加速度）
        ax = axes[row][3]
        ax.bar(dates, g["main_accel"], color=colors, width=0.8)
        ax.axhline(0, color="gray", linewidth=0.5)
        ax.set_ylabel("accel", fontsize=8)
        ax.set_title(f"{name} - 二阶导(加速度)", fontsize=9)
        ax.tick_params(axis="x", rotation=45, labelsize=6)

    plt.suptitle("TOP10 品种微分特征时序图\n(绿色=上升, 红色=下降, 深色=加速, 浅色=减速)",
                 fontsize=14, y=1.0)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "derivative_timeseries_top10.png", dpi=120, bbox_inches="tight")
    plt.close()
    print("  → 保存: output3/derivative_timeseries_top10.png")


def plot_quadrant_heatmap(quad_df: pd.DataFrame):
    """四象限条件收益热力图"""
    quadrants = ["加速上升", "减速上升", "减速下降", "加速下降"]
    pivot = quad_df.pivot_table(
        index="variety_name", columns="quadrant",
        values="avg_fut_ret_1", aggfunc="mean"
    )
    pivot = pivot.reindex(columns=quadrants)
    pivot = pivot.dropna(how="all")
    pivot = pivot.sort_values("加速上升", ascending=False, na_position="last")

    fig, ax = plt.subplots(figsize=(10, max(16, len(pivot) * 0.35)))
    data = pivot.values * 100
    vmax = max(abs(np.nanmin(data)), abs(np.nanmax(data)), 0.5)
    im = ax.imshow(data, cmap="RdYlGn", aspect="auto", vmin=-vmax, vmax=vmax)
    ax.set_yticks(range(len(pivot)))
    ax.set_yticklabels(pivot.index, fontsize=7)
    ax.set_xticks(range(len(quadrants)))
    ax.set_xticklabels(quadrants, fontsize=9)

    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.2f}%", ha="center", va="center", fontsize=6)

    ax.set_title("四象限条件下平均次日收益率 (%)", fontsize=12)
    plt.colorbar(im, ax=ax, shrink=0.5, label="次日收益率 (%)")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "quadrant_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  → 保存: output3/quadrant_heatmap.png")


def plot_inflection_overlay(feat_df: pd.DataFrame, infl_df: pd.DataFrame):
    """价格曲线拐点标注图"""
    if len(infl_df) == 0:
        return

    # 选取拐点最多的品种
    top_varieties = infl_df["variety_id"].value_counts().head(6).index.tolist()

    n_plots = len(top_varieties)
    cols = min(n_plots, 2)
    rows = (n_plots + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(16, 5 * rows))
    if n_plots == 1:
        axes = np.array([axes])
    axes = np.array(axes).flatten()

    markers = {
        "上升拐点": ("v", "#f44336", 80),
        "下降拐点": ("^", "#4caf50", 80),
        "趋势启动点": ("o", "#2196f3", 100),
        "趋势终结点": ("s", "#ff9800", 100),
    }

    for idx, vid in enumerate(top_varieties):
        if idx >= len(axes):
            break
        g = feat_df[feat_df["variety_id"] == vid].sort_values("trade_date")
        name = g.iloc[0]["variety_name"]
        v_infl = infl_df[infl_df["variety_id"] == vid]

        ax = axes[idx]
        ax.plot(g["trade_date"], g["close_price"], "k-", linewidth=1, alpha=0.8)

        for itype, (marker, color, size) in markers.items():
            pts = v_infl[v_infl["inflection_type"] == itype]
            if len(pts) > 0:
                ax.scatter(pts["trade_date"], pts["price_at_point"],
                           marker=marker, c=color, s=size, zorder=5,
                           label=f"{itype}({len(pts)})", edgecolors="black", linewidths=0.5)

        ax.set_title(f"{name} - 拐点标注 ({len(v_infl)}个)", fontsize=10)
        ax.legend(fontsize=7, loc="best")
        ax.tick_params(axis="x", rotation=45, labelsize=7)

    for idx in range(len(top_varieties), len(axes)):
        axes[idx].set_visible(False)

    plt.suptitle("价格曲线拐点标注图", fontsize=13, y=1.01)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "inflection_overlay.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  → 保存: output3/inflection_overlay.png")


def plot_divergence_bands(feat_df: pd.DataFrame):
    """主散斜率背离区间图"""
    top_ids = feat_df.groupby("variety_id").size().sort_values(ascending=False).head(6).index.tolist()

    n_plots = len(top_ids)
    cols = min(n_plots, 2)
    rows = (n_plots + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(16, 5 * rows))
    axes = np.array(axes).flatten()

    for idx, vid in enumerate(top_ids):
        if idx >= len(axes):
            break
        g = feat_df[feat_df["variety_id"] == vid].sort_values("trade_date")
        name = g.iloc[0]["variety_name"]

        ax1 = axes[idx]
        ax2 = ax1.twinx()

        ax1.plot(g["trade_date"], g["main_slope_1"], "b-", linewidth=1, label="主力斜率")
        ax1.plot(g["trade_date"], g["retail_slope_1"], "r-", linewidth=1, label="散户斜率")
        ax1.axhline(0, color="gray", linewidth=0.5, linestyle="--")

        # 背离区间着色
        diverge = g["slope_diverge"].values
        dates = g["trade_date"].values
        for t in range(len(dates)):
            if diverge[t] == 1:
                ax1.axvspan(dates[t], dates[min(t + 1, len(dates) - 1)],
                            color="#ffe0b2", alpha=0.5)

        ax2.plot(g["trade_date"], g["close_price"], "k--", linewidth=0.8,
                 alpha=0.5, label="收盘价")

        ax1.set_title(f"{name} - 主散斜率 (橙色=背离区间)", fontsize=10)
        ax1.set_ylabel("斜率")
        ax2.set_ylabel("价格")
        ax1.tick_params(axis="x", rotation=45, labelsize=7)

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc="upper left")

    for idx in range(len(top_ids), len(axes)):
        axes[idx].set_visible(False)

    plt.suptitle("主散斜率背离区间图", fontsize=13, y=1.01)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "divergence_bands.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  → 保存: output3/divergence_bands.png")


def plot_strategy_comparison(bt_df: pd.DataFrame):
    """三轮计划全策略对比"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # (1) 策略 D~G 胜率 vs 收益散点图
    ax = axes[0][0]
    colors_map = {"策略D_加速度信号": "#1976d2", "策略E_拐点反转": "#388e3c",
                  "策略F_主散背离": "#f57c00", "策略G_综合微分": "#7b1fa2"}
    for strat in bt_df["strategy"].unique():
        sdf = bt_df[(bt_df["strategy"] == strat) & (bt_df["n_trades"] > 0)]
        c = colors_map.get(strat, "gray")
        ax.scatter(sdf["win_rate"], sdf["total_return"], label=strat, s=40,
                   alpha=0.7, c=c)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.axvline(0.5, color="black", linewidth=0.5, linestyle="--")
    ax.set_xlabel("胜率")
    ax.set_ylabel("总收益")
    ax.set_title("计划3策略: 胜率 vs 总收益")
    ax.legend(fontsize=8)

    # (2) 各策略平均指标对比（含计划1/2）
    ax = axes[0][1]
    strat_summary = []
    for strat in bt_df["strategy"].unique():
        sdf = bt_df[(bt_df["strategy"] == strat) & (bt_df["n_trades"] > 0)]
        if len(sdf) > 0:
            strat_summary.append({
                "策略": strat.replace("策略", "P3-"),
                "平均胜率": sdf["win_rate"].mean(),
                "平均收益": sdf["total_return"].mean(),
            })
    strat_summary.append({"策略": "P1-综合信号", "平均胜率": 0.5174, "平均收益": 0.040})
    strat_summary.append({"策略": "P2-趋势A", "平均胜率": 0.5201, "平均收益": 0.0599})

    sum_df = pd.DataFrame(strat_summary)
    x = np.arange(len(sum_df))
    w = 0.35
    ax.bar(x - w / 2, sum_df["平均胜率"], w, label="平均胜率", color="#42a5f5")
    ax.bar(x + w / 2, sum_df["平均收益"], w, label="平均收益", color="#66bb6a")
    ax.set_xticks(x)
    ax.set_xticklabels(sum_df["策略"], fontsize=7, rotation=30)
    ax.axhline(0.5, color="red", linewidth=0.5, linestyle="--", alpha=0.5)
    ax.legend(fontsize=8)
    ax.set_title("全策略对比 (P1/P2/P3)")

    # (3) 按板块的策略G表现
    ax = axes[1][0]
    strat_g = bt_df[(bt_df["strategy"] == "策略G_综合微分") & (bt_df["n_trades"] > 0)]
    if len(strat_g) > 0:
        sector_perf = strat_g.groupby("sector").agg(
            win_rate=("win_rate", "mean"),
            total_return=("total_return", "mean"),
            count=("variety_id", "count"),
        )
        colors = ["#d32f2f" if v < 0 else "#388e3c"
                  for v in sector_perf.sort_values("total_return")["total_return"]]
        sector_perf.sort_values("total_return").plot(
            kind="barh", y="total_return", ax=ax, color=colors, legend=False)
        ax.set_title("策略G 各板块平均收益")
        ax.set_xlabel("平均收益")

    # (4) 信号触发频率对比
    ax = axes[1][1]
    freq_data = []
    for strat in bt_df["strategy"].unique():
        sdf = bt_df[(bt_df["strategy"] == strat) & (bt_df["n_trades"] > 0)]
        if len(sdf) > 0:
            freq_data.append({
                "策略": strat,
                "平均信号频率": sdf["signal_freq"].mean(),
                "平均胜率": sdf["win_rate"].mean(),
            })
    if freq_data:
        freq_df = pd.DataFrame(freq_data)
        ax.barh(freq_df["策略"], freq_df["平均信号频率"],
                color=["#1976d2", "#388e3c", "#f57c00", "#7b1fa2"][:len(freq_df)])
        ax.set_xlabel("信号频率 (交易日占比)")
        ax.set_title("各策略信号触发频率")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "strategy_comparison_all.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  → 保存: output3/strategy_comparison_all.png")


def plot_sector_radar(bt_df: pd.DataFrame, corr_df: pd.DataFrame,
                      quad_df: pd.DataFrame, infl_df: pd.DataFrame):
    """板块雷达图"""
    sectors = ["黑色系", "有色金属", "能源化工", "农产品", "其他"]

    metrics = {}
    for sector in sectors:
        # 斜率信号强度
        corr_sub = corr_df[(corr_df["sector"] == sector) &
                           (corr_df["x_feature"] == "main_slope_1") &
                           (corr_df["y_feature"] == "fut_ret_1")]
        slope_strength = abs(corr_sub["pearson_r"].mean()) if len(corr_sub) > 0 else 0

        # 加速度预测力
        corr_accel = corr_df[(corr_df["sector"] == sector) &
                             (corr_df["x_feature"] == "main_accel") &
                             (corr_df["y_feature"] == "fut_ret_1")]
        accel_power = abs(corr_accel["pearson_r"].mean()) if len(corr_accel) > 0 else 0

        # 拐点准确率
        s_infl = infl_df[infl_df["sector"] == sector]
        if len(s_infl) > 0:
            correct = 0
            total = 0
            for _, row in s_infl.iterrows():
                if pd.isna(row["fut_ret_1"]):
                    continue
                total += 1
                if row["inflection_type"] in ("下降拐点", "趋势启动点") and row["fut_ret_1"] > 0:
                    correct += 1
                elif row["inflection_type"] in ("上升拐点", "趋势终结点") and row["fut_ret_1"] < 0:
                    correct += 1
            infl_acc = correct / total if total > 0 else 0
        else:
            infl_acc = 0

        # 策略G收益
        g_sub = bt_df[(bt_df["strategy"] == "策略G_综合微分") &
                      (bt_df["sector"] == sector) & (bt_df["n_trades"] > 0)]
        strat_ret = g_sub["total_return"].mean() if len(g_sub) > 0 else 0

        metrics[sector] = [slope_strength, accel_power, infl_acc, max(strat_ret, 0)]

    labels = ["斜率信号强度", "加速度预测力", "拐点准确率", "策略G收益"]
    n_labels = len(labels)
    angles = np.linspace(0, 2 * np.pi, n_labels, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    colors = ["#1976d2", "#388e3c", "#f57c00", "#7b1fa2", "#616161"]

    for i, sector in enumerate(sectors):
        values = metrics[sector]
        # 归一化到 [0, 1]
        max_vals = [max(metrics[s][j] for s in sectors) for j in range(n_labels)]
        norm_values = [v / m if m > 0 else 0 for v, m in zip(values, max_vals)]
        norm_values += norm_values[:1]
        ax.plot(angles, norm_values, "o-", linewidth=1.5, color=colors[i], label=sector)
        ax.fill(angles, norm_values, alpha=0.1, color=colors[i])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_title("各板块微分特征表现雷达图", fontsize=12, y=1.08)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "sector_radar.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  → 保存: output3/sector_radar.png")


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  计划3：资金曲线微分特征与价格趋势关系研究")
    print("=" * 60)

    df = load_data()
    print(f"[数据加载] {len(df)} 行, {df['variety_id'].nunique()} 个品种")

    # 阶段一：微分特征计算
    feat_df = calc_derivative_features(df)

    # 阶段二：关联分析
    corr_df = run_correlation_analysis(feat_df)
    quad_df = run_quadrant_returns(feat_df)
    infl_df = run_inflection_analysis(feat_df)

    # 阶段三：主散对比
    div_df = run_divergence_analysis(feat_df)

    # 阶段四：策略回测
    bt_df = run_backtest(feat_df)

    # 阶段五：可视化
    print(f"\n[阶段五] 生成可视化...")
    plot_derivative_timeseries(feat_df)
    plot_quadrant_heatmap(quad_df)
    plot_inflection_overlay(feat_df, infl_df)
    plot_divergence_bands(feat_df)
    plot_strategy_comparison(bt_df)
    plot_sector_radar(bt_df, corr_df, quad_df, infl_df)

    # 保存 CSV
    feat_df.to_csv(OUTPUT_DIR / "derivative_features.csv", index=False, encoding="utf-8-sig")
    quad_df.to_csv(OUTPUT_DIR / "quadrant_returns.csv", index=False, encoding="utf-8-sig")
    infl_df.to_csv(OUTPUT_DIR / "inflection_points.csv", index=False, encoding="utf-8-sig")
    div_df.to_csv(OUTPUT_DIR / "divergence_analysis.csv", index=False, encoding="utf-8-sig")
    corr_df.to_csv(OUTPUT_DIR / "correlation_derivatives.csv", index=False, encoding="utf-8-sig")
    bt_df.to_csv(OUTPUT_DIR / "backtest_derivative.csv", index=False, encoding="utf-8-sig")
    print("  → 保存: 所有 CSV 数据文件")

    # ─── 详细结果汇总 ───
    print("\n" + "=" * 60)
    print("  详细结果汇总")
    print("=" * 60)

    # 微分特征相关性 TOP10
    print(f"\n--- 微分特征与次日收益相关性 TOP10 品种 ---")
    slope_corr = corr_df[(corr_df["x_feature"] == "main_slope_1") &
                         (corr_df["y_feature"] == "fut_ret_1")]
    top_corr = slope_corr.sort_values("pearson_r", key=abs, ascending=False).head(10)
    for _, r in top_corr.iterrows():
        sig = "★" if r["p_value"] < 0.05 else ""
        print(f"  {r['variety_name']} [{r['sector']}]: r={r['pearson_r']:.4f}, "
              f"p={r['p_value']:.4f} {sig}")

    # 四象限对比
    print(f"\n--- 四象限条件收益率汇总 (全品种) ---")
    for q in ["加速上升", "减速上升", "减速下降", "加速下降"]:
        sub = quad_df[(quad_df["quadrant"] == q) & (quad_df["n_days"] >= 2)]
        if len(sub) > 0:
            print(f"  {q}: 平均次日收益={sub['avg_fut_ret_1'].mean():.4%}, "
                  f"正收益概率={sub['positive_prob_1'].mean():.2%}")

    # 拐点统计
    print(f"\n--- 拐点统计汇总 ---")
    if len(infl_df) > 0:
        for itype in infl_df["inflection_type"].unique():
            sub = infl_df[infl_df["inflection_type"] == itype]
            print(f"  {itype}: {len(sub)}个, 平均1日={sub['fut_ret_1'].dropna().mean():.4%}, "
                  f"平均3日={sub['fut_ret_3'].dropna().mean():.4%}, "
                  f"平均5日={sub['fut_ret_5'].dropna().mean():.4%}")

    # 策略TOP5
    print(f"\n--- 策略回测 TOP5 品种 ---")
    for strat in bt_df["strategy"].unique():
        sdf = bt_df[(bt_df["strategy"] == strat) & (bt_df["n_trades"] > 0)]
        if len(sdf) == 0:
            continue
        print(f"\n  {strat}:")
        top5 = sdf.sort_values("total_return", ascending=False).head(5)
        for _, r in top5.iterrows():
            print(f"    {r['variety_name']} [{r['sector']}]: 胜率={r['win_rate']:.1%}, "
                  f"总收益={r['total_return']:+.4f}, 盈亏比={r['profit_loss_ratio']:.2f}")

    print("\n" + "=" * 60)
    print("  计划3分析完成! 输出文件在 output3/ 目录")
    print("=" * 60)


if __name__ == "__main__":
    main()
