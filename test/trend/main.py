"""
期货资金强弱与价格关系研究
基于 local_fut_pulse.sqlite 数据，分析主力/散户资金指标与价格走势的关系
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
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

with open(BASE_DIR / "varieties.json", "r", encoding="utf-8") as f:
    VARIETIES = {v["id"]: v["name"] for v in json.load(f)}


# ═══════════════════════════════════════════════════════════════
# 阶段一：数据预处理与特征工程
# ═══════════════════════════════════════════════════════════════

def load_and_prepare() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)

    sql = """
    SELECT
        s.variety_id,
        s.trade_date,
        s.main_force,
        s.retail,
        c.close_price
    FROM fut_strength s
    INNER JOIN fut_daily_close c
        ON s.variety_id = c.variety_id AND s.trade_date = c.trade_date
    ORDER BY s.variety_id, s.trade_date
    """
    df = pd.read_sql(sql, conn)
    conn.close()

    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df["variety_name"] = df["variety_id"].map(VARIETIES)

    # 按品种分组计算派生指标
    derived = []
    for vid, g in df.groupby("variety_id"):
        g = g.sort_values("trade_date").copy()
        g["price_return"] = g["close_price"].pct_change()
        g["price_return_next"] = g["price_return"].shift(-1)
        g["main_force_delta"] = g["main_force"].diff()
        g["retail_delta"] = g["retail"].diff()
        g["force_spread"] = g["main_force"] - g["retail"]
        g["force_spread_delta"] = g["force_spread"].diff()

        # z-score 标准化（跨品种可比）
        for col in ["main_force", "retail", "force_spread"]:
            mu, sigma = g[col].mean(), g[col].std()
            g[f"{col}_z"] = (g[col] - mu) / sigma if sigma > 0 else 0.0

        derived.append(g)

    df = pd.concat(derived, ignore_index=True)
    df = df.dropna(subset=["price_return"])  # 首行无收益率
    print(f"[阶段一] 数据预处理完成: {len(df)} 行, {df['variety_id'].nunique()} 个品种")
    return df


# ═══════════════════════════════════════════════════════════════
# 阶段二：相关性与领先-滞后分析
# ═══════════════════════════════════════════════════════════════

def correlation_analysis(df: pd.DataFrame) -> dict:
    results = {}

    # --- 2.1 同期相关性 ---
    corr_records = []
    for vid, g in df.groupby("variety_id"):
        if len(g) < 10:
            continue
        name = VARIETIES.get(vid, str(vid))
        row = {"variety_id": vid, "variety_name": name, "n": len(g)}
        for feat in ["main_force", "retail", "force_spread"]:
            r_pearson, p_pearson = stats.pearsonr(g[feat], g["price_return"])
            r_spearman, p_spearman = stats.spearmanr(g[feat], g["price_return"])
            row[f"{feat}_pearson_r"] = r_pearson
            row[f"{feat}_pearson_p"] = p_pearson
            row[f"{feat}_spearman_r"] = r_spearman
            row[f"{feat}_spearman_p"] = p_spearman
        corr_records.append(row)

    corr_df = pd.DataFrame(corr_records)
    results["同期相关性"] = corr_df
    print(f"\n[阶段二] 同期相关性分析完成 ({len(corr_df)} 品种)")

    # 统计显著品种数量
    sig_level = 0.05
    for feat in ["main_force", "retail", "force_spread"]:
        n_sig = (corr_df[f"{feat}_pearson_p"] < sig_level).sum()
        avg_r = corr_df[f"{feat}_pearson_r"].mean()
        print(f"  {feat}: 平均 Pearson r = {avg_r:.4f}, 显著品种 {n_sig}/{len(corr_df)}")

    # --- 2.2 领先-滞后分析 ---
    lead_lag_records = []
    for vid, g in df.groupby("variety_id"):
        if len(g) < 10:
            continue
        name = VARIETIES.get(vid, str(vid))
        g = g.sort_values("trade_date").reset_index(drop=True)
        row = {"variety_id": vid, "variety_name": name}
        for lag in range(1, 4):
            future_ret = g["price_return"].shift(-lag)
            valid = g["main_force_delta"].notna() & future_ret.notna()
            if valid.sum() < 8:
                continue
            r, p = stats.pearsonr(
                g.loc[valid, "main_force_delta"], future_ret[valid]
            )
            row[f"mf_delta_vs_ret_t+{lag}_r"] = r
            row[f"mf_delta_vs_ret_t+{lag}_p"] = p

            r2, p2 = stats.pearsonr(
                g.loc[valid, "retail_delta"], future_ret[valid]
            )
            row[f"retail_delta_vs_ret_t+{lag}_r"] = r2
            row[f"retail_delta_vs_ret_t+{lag}_p"] = p2
        lead_lag_records.append(row)

    lead_lag_df = pd.DataFrame(lead_lag_records)
    results["领先滞后"] = lead_lag_df
    print(f"  领先-滞后分析完成 ({len(lead_lag_df)} 品种)")

    for lag in range(1, 4):
        col = f"mf_delta_vs_ret_t+{lag}_r"
        if col in lead_lag_df.columns:
            avg = lead_lag_df[col].mean()
            n_sig = (lead_lag_df[f"mf_delta_vs_ret_t+{lag}_p"] < sig_level).sum()
            print(f"  main_force_delta → return(t+{lag}): 平均 r = {avg:.4f}, 显著 {n_sig}/{len(lead_lag_df)}")

    # --- 2.3 Granger 因果检验 (简化版：基于 OLS) ---
    granger_records = []
    for vid, g in df.groupby("variety_id"):
        if len(g) < 15:
            continue
        g = g.sort_values("trade_date").reset_index(drop=True)
        name = VARIETIES.get(vid, str(vid))
        row = {"variety_id": vid, "variety_name": name}

        y = g["price_return"].values[2:]
        y_lag1 = g["price_return"].shift(1).values[2:]
        mf_lag1 = g["main_force_delta"].shift(1).values[2:]
        rt_lag1 = g["retail_delta"].shift(1).values[2:]

        valid = np.isfinite(y) & np.isfinite(y_lag1) & np.isfinite(mf_lag1) & np.isfinite(rt_lag1)
        if valid.sum() < 10:
            granger_records.append(row)
            continue

        y_v, y_lag1_v, mf_lag1_v, rt_lag1_v = y[valid], y_lag1[valid], mf_lag1[valid], rt_lag1[valid]

        # 受限模型: ret_t = a + b * ret_{t-1}
        X_r = np.column_stack([np.ones(len(y_v)), y_lag1_v])
        # 非受限模型: ret_t = a + b * ret_{t-1} + c * mf_delta_{t-1}
        X_u_mf = np.column_stack([np.ones(len(y_v)), y_lag1_v, mf_lag1_v])
        X_u_rt = np.column_stack([np.ones(len(y_v)), y_lag1_v, rt_lag1_v])

        try:
            rss_r = np.sum((y_v - X_r @ np.linalg.lstsq(X_r, y_v, rcond=None)[0]) ** 2)
            n_obs = len(y_v)

            rss_u_mf = np.sum((y_v - X_u_mf @ np.linalg.lstsq(X_u_mf, y_v, rcond=None)[0]) ** 2)
            f_mf = ((rss_r - rss_u_mf) / 1) / (rss_u_mf / (n_obs - 3))
            p_mf = 1 - stats.f.cdf(f_mf, 1, n_obs - 3)
            row["granger_mf_F"] = f_mf
            row["granger_mf_p"] = p_mf

            rss_u_rt = np.sum((y_v - X_u_rt @ np.linalg.lstsq(X_u_rt, y_v, rcond=None)[0]) ** 2)
            f_rt = ((rss_r - rss_u_rt) / 1) / (rss_u_rt / (n_obs - 3))
            p_rt = 1 - stats.f.cdf(f_rt, 1, n_obs - 3)
            row["granger_rt_F"] = f_rt
            row["granger_rt_p"] = p_rt
        except Exception:
            pass
        granger_records.append(row)

    granger_df = pd.DataFrame(granger_records)
    results["Granger因果"] = granger_df
    if "granger_mf_p" in granger_df.columns:
        n_sig_mf = (granger_df["granger_mf_p"] < sig_level).sum()
        n_sig_rt = (granger_df["granger_rt_p"] < sig_level).sum()
        print(f"  Granger 因果: main_force→price 显著 {n_sig_mf}/{len(granger_df)}, retail→price 显著 {n_sig_rt}/{len(granger_df)}")

    # --- 2.4 相关性热力图 ---
    plot_correlation_heatmap(corr_df)

    return results


def plot_correlation_heatmap(corr_df: pd.DataFrame):
    fig, axes = plt.subplots(1, 3, figsize=(20, 14))
    feats = ["main_force", "retail", "force_spread"]
    titles = ["主力资金 vs 收益率", "散户资金 vs 收益率", "主散剪刀差 vs 收益率"]

    for ax, feat, title in zip(axes, feats, titles):
        data = corr_df.set_index("variety_name")[f"{feat}_pearson_r"].sort_values()
        colors = ["#d32f2f" if v < 0 else "#388e3c" for v in data.values]
        ax.barh(range(len(data)), data.values, color=colors)
        ax.set_yticks(range(len(data)))
        ax.set_yticklabels(data.index, fontsize=7)
        ax.set_title(title, fontsize=12)
        ax.axvline(0, color="black", linewidth=0.5)
        ax.set_xlabel("Pearson r")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "correlation_heatmap.png", dpi=150)
    plt.close()
    print("  → 保存: output/correlation_heatmap.png")


# ═══════════════════════════════════════════════════════════════
# 阶段三：量化交易指标构建
# ═══════════════════════════════════════════════════════════════

def build_indicators(df: pd.DataFrame) -> pd.DataFrame:
    enhanced = []
    for vid, g in df.groupby("variety_id"):
        g = g.sort_values("trade_date").copy()

        # FMS: 资金动量得分 (3日均值)
        g["FMS"] = g["main_force_delta"].rolling(3, min_periods=1).mean()

        # RCI: 散户反向信号 (百分位极值)
        retail_pct = g["retail"].rank(pct=True)
        g["RCI"] = 0.0
        g.loc[retail_pct > 0.9, "RCI"] = -1.0  # 散户极度看多 → 看空信号
        g.loc[retail_pct < 0.1, "RCI"] = 1.0   # 散户极度看空 → 看多信号

        # FRD: 主散背离度
        mf_sign = np.sign(g["main_force"])
        rt_sign = np.sign(g["retail"])
        g["FRD"] = (mf_sign != rt_sign).astype(float) * np.abs(g["force_spread"])

        # FLPI: 资金领先价格指数 (使用 main_force_delta 的 1 期滞后加权)
        g["FLPI"] = g["main_force_delta"].shift(1).fillna(0)

        # 综合交易信号: 归一化各信号后等权平均
        signals = pd.DataFrame()
        for col in ["FMS", "FLPI"]:
            s = g[col]
            mu, sigma = s.mean(), s.std()
            signals[col] = (s - mu) / sigma if sigma > 0 else 0.0
        signals["RCI"] = g["RCI"]

        frd_s = g["FRD"]
        mu_f, sigma_f = frd_s.mean(), frd_s.std()
        signals["FRD"] = ((frd_s - mu_f) / sigma_f * mf_sign) if sigma_f > 0 else 0.0

        g["composite_signal"] = signals.mean(axis=1).clip(-1, 1)

        enhanced.append(g)

    df = pd.concat(enhanced, ignore_index=True)
    print(f"\n[阶段三] 指标构建完成: FMS, RCI, FRD, FLPI, composite_signal")
    return df


# ═══════════════════════════════════════════════════════════════
# 阶段四：回测验证
# ═══════════════════════════════════════════════════════════════

SECTOR_MAP = {
    "黑色系": ["铁矿石", "螺纹钢", "热卷", "锰硅", "焦煤"],
    "有色金属": ["沪铜", "沪铝", "沪锌", "沪铅", "沪锡", "沪镍", "沪金", "沪银", "氧化铝", "工业硅", "碳酸锂", "多晶硅"],
    "能源化工": ["PTA", "对二甲苯", "聚丙烯", "苯乙烯", "纯苯", "烧碱", "尿素", "橡胶", "丁二烯胶",
                "甲醇", "PVC", "纯碱", "玻璃", "塑料", "乙二醇", "沥青", "LPG", "燃油", "低硫燃油"],
    "农产品": ["豆一", "豆二", "豆油", "豆粕", "菜油", "菜粕", "棕榈油", "玉米", "鸡蛋", "棉花",
              "白糖", "苹果", "红枣", "花生", "生猪"],
    "其他": ["纸浆", "原木", "上证", "欧线集运"],
}

NAME_TO_SECTOR = {}
for sector, names in SECTOR_MAP.items():
    for n in names:
        NAME_TO_SECTOR[n] = sector


def backtest(df: pd.DataFrame) -> pd.DataFrame:
    bt_records = []

    for vid, g in df.groupby("variety_id"):
        g = g.sort_values("trade_date").copy()
        name = VARIETIES.get(vid, str(vid))
        sector = NAME_TO_SECTOR.get(name, "其他")

        # 仅使用有次日收益率的行
        valid = g.dropna(subset=["price_return_next", "composite_signal"])
        if len(valid) < 5:
            continue

        signal = valid["composite_signal"].values
        ret_next = valid["price_return_next"].values

        # --- 策略1: 综合信号 (阈值=0.2) ---
        threshold = 0.2
        positions = np.where(signal > threshold, 1, np.where(signal < -threshold, -1, 0))
        strat_ret = positions * ret_next
        trades = np.sum(positions != 0)
        if trades > 0:
            wins = np.sum(strat_ret > 0)
            win_rate = wins / trades
            total_ret = np.sum(strat_ret)
            avg_win = np.mean(strat_ret[strat_ret > 0]) if np.any(strat_ret > 0) else 0
            avg_loss = np.mean(np.abs(strat_ret[strat_ret < 0])) if np.any(strat_ret < 0) else 1e-9
            profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else np.inf

            cum = np.cumsum(strat_ret)
            max_dd = np.min(cum - np.maximum.accumulate(cum))
        else:
            win_rate = total_ret = profit_loss_ratio = 0
            max_dd = 0

        # --- 策略2: 随机基准 ---
        np.random.seed(vid)
        rand_pos = np.random.choice([-1, 0, 1], size=len(ret_next), p=[0.3, 0.4, 0.3])
        rand_ret = np.sum(rand_pos * ret_next)

        # --- 策略3: 简单趋势跟踪 (前日涨做多/跌做空) ---
        prev_ret = valid["price_return"].values
        trend_pos = np.where(prev_ret > 0, 1, np.where(prev_ret < 0, -1, 0))
        trend_ret = np.sum(trend_pos * ret_next)

        bt_records.append({
            "variety_id": vid,
            "variety_name": name,
            "sector": sector,
            "n_trades": int(trades),
            "win_rate": win_rate,
            "total_return": total_ret,
            "profit_loss_ratio": profit_loss_ratio,
            "max_drawdown": max_dd,
            "random_return": rand_ret,
            "trend_return": trend_ret,
        })

    bt_df = pd.DataFrame(bt_records)
    print(f"\n[阶段四] 回测完成 ({len(bt_df)} 品种)")

    better_than_random = (bt_df["total_return"] > bt_df["random_return"]).sum()
    better_than_trend = (bt_df["total_return"] > bt_df["trend_return"]).sum()
    avg_wr = bt_df["win_rate"].mean()
    print(f"  平均胜率: {avg_wr:.2%}")
    print(f"  优于随机策略: {better_than_random}/{len(bt_df)}")
    print(f"  优于趋势跟踪: {better_than_trend}/{len(bt_df)}")

    # 按板块汇总
    print("\n  按板块汇总:")
    for sector, sdf in bt_df.groupby("sector"):
        print(f"    {sector}: 平均胜率 {sdf['win_rate'].mean():.2%}, "
              f"平均收益 {sdf['total_return'].mean():.4f}, "
              f"品种数 {len(sdf)}")

    return bt_df


# ═══════════════════════════════════════════════════════════════
# 阶段五：可视化与输出
# ═══════════════════════════════════════════════════════════════

def plot_top_varieties(df: pd.DataFrame, corr_df: pd.DataFrame):
    """选取相关性最强的6个品种画双轴图"""
    top6 = corr_df.reindex(
        corr_df["main_force_pearson_r"].abs().sort_values(ascending=False).index
    ).head(6)

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()

    for idx, (_, row) in enumerate(top6.iterrows()):
        vid = row["variety_id"]
        name = row["variety_name"]
        g = df[df["variety_id"] == vid].sort_values("trade_date")

        ax1 = axes[idx]
        ax2 = ax1.twinx()

        ax1.plot(g["trade_date"], g["close_price"], "b-", linewidth=1.2, label="收盘价")
        ax2.plot(g["trade_date"], g["main_force"], "r--", linewidth=0.9, alpha=0.8, label="主力资金")
        ax2.plot(g["trade_date"], g["retail"], "g:", linewidth=0.9, alpha=0.8, label="散户资金")

        ax1.set_title(f"{name} (r={row['main_force_pearson_r']:.3f})", fontsize=11)
        ax1.set_ylabel("收盘价", color="blue")
        ax2.set_ylabel("资金强弱")
        ax1.tick_params(axis="x", rotation=45, labelsize=7)

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc="upper left")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "top6_dual_axis.png", dpi=150)
    plt.close()
    print("  → 保存: output/top6_dual_axis.png")


def plot_signal_overlay(df: pd.DataFrame, corr_df: pd.DataFrame):
    """在价格图上叠加综合信号"""
    top4 = corr_df.reindex(
        corr_df["main_force_pearson_r"].abs().sort_values(ascending=False).index
    ).head(4)

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes = axes.flatten()

    for idx, (_, row) in enumerate(top4.iterrows()):
        vid = row["variety_id"]
        name = row["variety_name"]
        g = df[df["variety_id"] == vid].sort_values("trade_date")

        ax = axes[idx]
        ax2 = ax.twinx()

        ax.plot(g["trade_date"], g["close_price"], "k-", linewidth=1.2, label="收盘价")

        sig = g["composite_signal"].values
        dates = g["trade_date"].values
        colors = np.where(sig > 0.2, "green", np.where(sig < -0.2, "red", "gray"))
        ax2.bar(dates, sig, color=colors, alpha=0.4, width=0.8, label="综合信号")

        ax.set_title(f"{name} - 价格与交易信号", fontsize=11)
        ax.set_ylabel("收盘价")
        ax2.set_ylabel("综合信号")
        ax2.set_ylim(-1.5, 1.5)
        ax.tick_params(axis="x", rotation=45, labelsize=7)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "signal_overlay.png", dpi=150)
    plt.close()
    print("  → 保存: output/signal_overlay.png")


def plot_backtest_summary(bt_df: pd.DataFrame):
    fig, axes = plt.subplots(1, 3, figsize=(18, 8))

    # 胜率分布
    ax = axes[0]
    for sector in bt_df["sector"].unique():
        sdf = bt_df[bt_df["sector"] == sector]
        ax.scatter(sdf["win_rate"], sdf["total_return"], label=sector, s=50, alpha=0.7)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.axvline(0.5, color="black", linewidth=0.5, linestyle="--")
    ax.set_xlabel("胜率")
    ax.set_ylabel("总收益")
    ax.set_title("策略表现: 胜率 vs 总收益")
    ax.legend(fontsize=8)

    # 策略对比
    ax = axes[1]
    comparison = pd.DataFrame({
        "综合信号策略": bt_df["total_return"].values,
        "随机策略": bt_df["random_return"].values,
        "趋势跟踪": bt_df["trend_return"].values,
    })
    comparison.mean().plot(kind="bar", ax=ax, color=["#1976d2", "#757575", "#ff9800"])
    ax.set_title("策略平均收益对比")
    ax.set_ylabel("平均收益")
    ax.tick_params(axis="x", rotation=0)

    # 按板块收益
    ax = axes[2]
    sector_ret = bt_df.groupby("sector")["total_return"].mean().sort_values()
    sector_ret.plot(kind="barh", ax=ax, color=["#d32f2f" if v < 0 else "#388e3c" for v in sector_ret.values])
    ax.set_title("各板块平均策略收益")
    ax.set_xlabel("平均收益")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "backtest_summary.png", dpi=150)
    plt.close()
    print("  → 保存: output/backtest_summary.png")


def plot_lead_lag_heatmap(lead_lag_df: pd.DataFrame):
    """领先滞后关系热力图"""
    cols_r = [c for c in lead_lag_df.columns if c.endswith("_r") and "mf_delta" in c]
    cols_r_rt = [c for c in lead_lag_df.columns if c.endswith("_r") and "retail_delta" in c]

    if not cols_r:
        return

    fig, axes = plt.subplots(1, 2, figsize=(16, 12))

    for ax, cols, title in [
        (axes[0], cols_r, "主力资金变化 → 未来收益率"),
        (axes[1], cols_r_rt, "散户资金变化 → 未来收益率"),
    ]:
        plot_data = lead_lag_df.set_index("variety_name")[cols].dropna()
        if plot_data.empty:
            continue
        plot_data.columns = [c.replace("mf_delta_vs_ret_", "").replace("retail_delta_vs_ret_", "").replace("_r", "") for c in plot_data.columns]
        plot_data = plot_data.sort_values(plot_data.columns[0])

        im = ax.imshow(plot_data.values, cmap="RdYlGn", aspect="auto", vmin=-0.6, vmax=0.6)
        ax.set_yticks(range(len(plot_data)))
        ax.set_yticklabels(plot_data.index, fontsize=6)
        ax.set_xticks(range(len(plot_data.columns)))
        ax.set_xticklabels(plot_data.columns, fontsize=9)
        ax.set_title(title, fontsize=11)
        plt.colorbar(im, ax=ax, shrink=0.5)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "lead_lag_heatmap.png", dpi=150)
    plt.close()
    print("  → 保存: output/lead_lag_heatmap.png")


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  期货资金强弱与价格关系研究")
    print("=" * 60)

    # 阶段一
    df = load_and_prepare()

    # 阶段二
    results = correlation_analysis(df)
    corr_df = results["同期相关性"]
    lead_lag_df = results["领先滞后"]
    granger_df = results["Granger因果"]

    # 阶段三
    df = build_indicators(df)

    # 阶段四
    bt_df = backtest(df)

    # 阶段五
    print(f"\n[阶段五] 生成可视化...")
    plot_top_varieties(df, corr_df)
    plot_signal_overlay(df, corr_df)
    plot_backtest_summary(bt_df)
    plot_lead_lag_heatmap(lead_lag_df)

    # 保存数据到 CSV
    corr_df.to_csv(OUTPUT_DIR / "correlation_results.csv", index=False, encoding="utf-8-sig")
    lead_lag_df.to_csv(OUTPUT_DIR / "lead_lag_results.csv", index=False, encoding="utf-8-sig")
    granger_df.to_csv(OUTPUT_DIR / "granger_results.csv", index=False, encoding="utf-8-sig")
    bt_df.to_csv(OUTPUT_DIR / "backtest_results.csv", index=False, encoding="utf-8-sig")
    print("  → 保存: CSV 数据文件")

    # 打印详细统计供后续分析
    print("\n" + "=" * 60)
    print("  详细结果汇总")
    print("=" * 60)

    print("\n--- 同期相关性 TOP 10 (|main_force Pearson r| 最大) ---")
    top10 = corr_df.reindex(corr_df["main_force_pearson_r"].abs().sort_values(ascending=False).index).head(10)
    for _, r in top10.iterrows():
        print(f"  {r['variety_name']:6s}: main_force r={r['main_force_pearson_r']:+.3f} (p={r['main_force_pearson_p']:.3f}), "
              f"retail r={r['retail_pearson_r']:+.3f} (p={r['retail_pearson_p']:.3f}), "
              f"spread r={r['force_spread_pearson_r']:+.3f}")

    print("\n--- 领先-滞后 TOP 10 (|mf_delta → ret(t+1)| 最大) ---")
    col_t1 = "mf_delta_vs_ret_t+1_r"
    if col_t1 in lead_lag_df.columns:
        top10_ll = lead_lag_df.dropna(subset=[col_t1]).reindex(
            lead_lag_df[col_t1].abs().sort_values(ascending=False).index
        ).head(10)
        for _, r in top10_ll.iterrows():
            vals = [f"t+{i}: {r.get(f'mf_delta_vs_ret_t+{i}_r', float('nan')):+.3f}" for i in range(1, 4)]
            print(f"  {r['variety_name']:6s}: {', '.join(vals)}")

    print("\n--- Granger 因果显著品种 (p<0.05) ---")
    if "granger_mf_p" in granger_df.columns:
        sig_g = granger_df[granger_df["granger_mf_p"] < 0.05]
        for _, r in sig_g.iterrows():
            print(f"  {r['variety_name']:6s}: main_force→price F={r['granger_mf_F']:.2f} p={r['granger_mf_p']:.4f}")
    sig_g_rt = granger_df[granger_df.get("granger_rt_p", pd.Series(dtype=float)) < 0.05] if "granger_rt_p" in granger_df.columns else pd.DataFrame()
    if len(sig_g_rt) > 0:
        for _, r in sig_g_rt.iterrows():
            print(f"  {r['variety_name']:6s}: retail→price F={r['granger_rt_F']:.2f} p={r['granger_rt_p']:.4f}")

    print("\n--- 回测 TOP 10 (总收益最高) ---")
    bt_top = bt_df.sort_values("total_return", ascending=False).head(10)
    for _, r in bt_top.iterrows():
        print(f"  {r['variety_name']:6s} [{r['sector']}]: 胜率={r['win_rate']:.1%}, "
              f"总收益={r['total_return']:+.4f}, 盈亏比={r['profit_loss_ratio']:.2f}, "
              f"最大回撤={r['max_drawdown']:+.4f}")

    print("\n--- 回测 BOTTOM 5 (总收益最低) ---")
    bt_bottom = bt_df.sort_values("total_return").head(5)
    for _, r in bt_bottom.iterrows():
        print(f"  {r['variety_name']:6s} [{r['sector']}]: 胜率={r['win_rate']:.1%}, "
              f"总收益={r['total_return']:+.4f}")

    print("\n" + "=" * 60)
    print("  分析完成! 输出文件在 output/ 目录")
    print("=" * 60)


if __name__ == "__main__":
    main()
