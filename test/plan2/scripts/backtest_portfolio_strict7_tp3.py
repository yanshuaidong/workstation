"""
策略 2：跨板块分散 · 主力跟随组合策略

实现口径：
- 12 个品种，全部只跑 A 通道
- 严格 7 日开仓：4 日主力背景 + 3 日主力/散户触发
- 3 日 main_force 拐头离场
- 组合层加入 3 槽位、板块互斥、主力动量分位排序
- 同一品种平仓后当天不反手；同日平仓释放的槽位不允许被同日新信号填入

同时输出三个对照：
- 去掉板块互斥，仅保留 3 槽限制
- 去掉 3 槽限制，仅保留板块互斥（按 6 个板块槽位等权）
- 12 品种各自独立跑单品种策略后做静态等权
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_DATA = ROOT / "artifacts" / "data"
DOCS_DIR = ROOT / "docs"
DB = ROOT.parent / "database" / "local_fut_pulse.sqlite"

TARGET_POOL: list[tuple[str, str]] = [
    ("沪铜", "有色金属"),
    ("沪铝", "有色金属"),
    ("沪锌", "有色金属"),
    ("沪金", "贵金属"),
    ("铁矿石", "黑色系"),
    ("焦煤", "黑色系"),
    ("PTA", "化工能化"),
    ("甲醇", "化工能化"),
    ("橡胶", "化工能化"),
    ("豆粕", "油脂油料"),
    ("棕榈油", "油脂油料"),
    ("玉米", "农产品"),
]
TARGET_VARIETIES = [name for name, _ in TARGET_POOL]
SECTOR_BY_VARIETY = dict(TARGET_POOL)
SECTORS = list(dict.fromkeys(sector for _, sector in TARGET_POOL))
MOMENTUM_LOOKBACK = 30


@dataclass(frozen=True)
class PortfolioConfig:
    strategy_name: str
    max_slots: int
    weight_slots: int
    sector_mutex: bool


def load_varieties(con: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT id, name, key FROM fut_variety ORDER BY id", con)


def load_df(con: sqlite3.Connection, variety_id: int) -> pd.DataFrame:
    strength = pd.read_sql_query(
        (
            "SELECT trade_date, main_force, retail "
            "FROM fut_strength WHERE variety_id=? ORDER BY trade_date"
        ),
        con,
        params=(variety_id,),
    )
    close = pd.read_sql_query(
        (
            "SELECT trade_date, close_price AS close "
            "FROM fut_daily_close WHERE variety_id=? ORDER BY trade_date"
        ),
        con,
        params=(variety_id,),
    )
    df = strength.merge(close, on="trade_date", how="inner").dropna()
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    return df.sort_values("trade_date").reset_index(drop=True)


def mark_breakpoints(dates: pd.Series) -> pd.Series:
    diffs = dates.diff().dt.days.fillna(1)
    return diffs.le(7)


def compute_max_drawdown(curve: pd.Series) -> float:
    peak = curve.cummax()
    drawdown = curve / peak - 1.0
    return float(drawdown.min())


def trade_return(side: int, entry_price: float, exit_price: float) -> float:
    return float(side * (exit_price - entry_price) / entry_price)


def compute_signals_strict7_tp3(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["date_cont"] = mark_breakpoints(out["trade_date"])
    out["main_diff"] = out["main_force"].diff()
    out["retail_diff"] = out["retail"].diff()

    cont7 = out["date_cont"].astype(int).rolling(6, min_periods=6).sum().eq(6)
    cont3 = out["date_cont"].astype(int).rolling(2, min_periods=2).sum().eq(2)

    bg1 = out["main_force"].shift(6)
    bg2 = out["main_force"].shift(5)
    bg3 = out["main_force"].shift(4)
    bg4 = out["main_force"].shift(3)

    trigger_main_up = out["main_diff"].shift(1).gt(0) & out["main_diff"].gt(0)
    trigger_main_down = out["main_diff"].shift(1).lt(0) & out["main_diff"].lt(0)
    trigger_retail_down = out["retail_diff"].shift(1).lt(0) & out["retail_diff"].lt(0)
    trigger_retail_up = out["retail_diff"].shift(1).gt(0) & out["retail_diff"].gt(0)

    long_bg = bg1.lt(0) & bg2.lt(0) & bg3.lt(0) & bg4.lt(0) & (bg4 - bg1).lt(0)
    short_bg = bg1.gt(0) & bg2.gt(0) & bg3.gt(0) & bg4.gt(0) & (bg4 - bg1).gt(0)

    out["long_signal"] = cont7 & long_bg & trigger_main_up & trigger_retail_down
    out["short_signal"] = cont7 & short_bg & trigger_main_down & trigger_retail_up

    out["m3"] = out["main_force"] - out["main_force"].shift(2)
    out["abs_m3"] = out["m3"].abs()
    out["tp3_delta_main"] = out["m3"]
    out["exit_long_signal"] = cont3 & out["tp3_delta_main"].lt(0)
    out["exit_short_signal"] = cont3 & out["tp3_delta_main"].gt(0)

    scores: list[float] = []
    abs_m3 = out["abs_m3"]
    for i in range(len(out)):
        current = abs_m3.iloc[i]
        hist = abs_m3.iloc[max(0, i - MOMENTUM_LOOKBACK) : i].dropna()
        if pd.isna(current) or len(hist) < MOMENTUM_LOOKBACK:
            scores.append(np.nan)
            continue
        scores.append(float(hist.le(current).sum() / MOMENTUM_LOOKBACK))
    out["main_score"] = scores

    out["close_return"] = out["close"].pct_change().fillna(0.0)
    return out


def backtest_single_strategy(df: pd.DataFrame, variety_name: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    data = compute_signals_strict7_tp3(df).copy()
    data["position_after_close"] = 0

    trades: list[dict] = []
    position = 0
    entry_idx: int | None = None
    entry_price: float | None = None
    entry_date = None

    for i, row in data.iterrows():
        closed_today = False

        if position == 1 and row["exit_long_signal"]:
            exit_price = float(row["close"])
            trades.append(
                {
                    "strategy_name": "单品种",
                    "variety_name": variety_name,
                    "sector": SECTOR_BY_VARIETY[variety_name],
                    "side": "long",
                    "entry_date": entry_date,
                    "exit_date": row["trade_date"],
                    "entry_price": float(entry_price),
                    "exit_price": exit_price,
                    "holding_days": i - int(entry_idx),
                    "pnl_ratio": trade_return(1, float(entry_price), exit_price),
                    "exit_reason": "tp3_main_turn_down",
                }
            )
            position = 0
            entry_idx = None
            entry_price = None
            entry_date = None
            closed_today = True

        elif position == -1 and row["exit_short_signal"]:
            exit_price = float(row["close"])
            trades.append(
                {
                    "strategy_name": "单品种",
                    "variety_name": variety_name,
                    "sector": SECTOR_BY_VARIETY[variety_name],
                    "side": "short",
                    "entry_date": entry_date,
                    "exit_date": row["trade_date"],
                    "entry_price": float(entry_price),
                    "exit_price": exit_price,
                    "holding_days": i - int(entry_idx),
                    "pnl_ratio": trade_return(-1, float(entry_price), exit_price),
                    "exit_reason": "tp3_main_turn_up",
                }
            )
            position = 0
            entry_idx = None
            entry_price = None
            entry_date = None
            closed_today = True

        if position == 0 and not closed_today:
            if row["long_signal"]:
                position = 1
                entry_idx = i
                entry_price = float(row["close"])
                entry_date = row["trade_date"]
            elif row["short_signal"]:
                position = -1
                entry_idx = i
                entry_price = float(row["close"])
                entry_date = row["trade_date"]

        data.at[i, "position_after_close"] = position

    if position != 0:
        last_row = data.iloc[-1]
        exit_price = float(last_row["close"])
        trades.append(
            {
                "strategy_name": "单品种",
                "variety_name": variety_name,
                "sector": SECTOR_BY_VARIETY[variety_name],
                "side": "long" if position == 1 else "short",
                "entry_date": entry_date,
                "exit_date": last_row["trade_date"],
                "entry_price": float(entry_price),
                "exit_price": exit_price,
                "holding_days": len(data) - 1 - int(entry_idx),
                "pnl_ratio": trade_return(position, float(entry_price), exit_price),
                "exit_reason": "final_close",
            }
        )

    data["position_prev"] = data["position_after_close"].shift(1).fillna(0).astype(int)
    data["strategy_daily_return"] = data["position_prev"] * data["close_return"]
    data["equity_curve"] = (1.0 + data["strategy_daily_return"]).cumprod()
    data["benchmark_curve"] = (1.0 + data["close_return"]).cumprod()

    trades_df = pd.DataFrame(trades)
    summary = {
        "strategy_name": "单品种",
        "variety_name": variety_name,
        "trade_count": int(len(trades_df)),
        "win_rate": float(trades_df["pnl_ratio"].gt(0).mean()) if len(trades_df) else np.nan,
        "avg_trade_return": float(trades_df["pnl_ratio"].mean()) if len(trades_df) else np.nan,
        "median_holding_days": float(trades_df["holding_days"].median()) if len(trades_df) else np.nan,
        "strategy_return": float(data["equity_curve"].iloc[-1] - 1.0),
        "buy_hold_return": float(data["benchmark_curve"].iloc[-1] - 1.0),
        "excess_return": float(data["equity_curve"].iloc[-1] - data["benchmark_curve"].iloc[-1]),
        "max_drawdown": compute_max_drawdown(data["equity_curve"]),
        "signal_long_days": int(data["long_signal"].sum()),
        "signal_short_days": int(data["short_signal"].sum()),
    }
    return data, trades_df, summary


def validate_aligned_dates(signal_map: dict[str, pd.DataFrame]) -> pd.DatetimeIndex:
    base_dates = pd.DatetimeIndex(signal_map[TARGET_VARIETIES[0]]["trade_date"])
    for variety_name in TARGET_VARIETIES[1:]:
        dates = pd.DatetimeIndex(signal_map[variety_name]["trade_date"])
        if not base_dates.equals(dates):
            raise ValueError(f"{variety_name} 的交易日与基准品种不一致，无法直接做组合回测。")
    return base_dates


def simulate_portfolio(
    signal_map: dict[str, pd.DataFrame],
    config: PortfolioConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    dates = validate_aligned_dates(signal_map)
    holdings: dict[str, dict] = {}
    trades: list[dict] = []
    daily_rows: list[dict] = []

    for i, trade_date in enumerate(dates):
        start_holdings = {name: pos.copy() for name, pos in holdings.items()}
        start_sectors = {SECTOR_BY_VARIETY[name] for name in start_holdings}
        entry_capacity = config.max_slots - len(start_holdings)
        closed_today: set[str] = set()

        closed_count = 0
        for variety_name, pos in list(start_holdings.items()):
            row = signal_map[variety_name].iloc[i]
            if pos["side"] == 1 and bool(row["exit_long_signal"]):
                exit_price = float(row["close"])
                trades.append(
                    {
                        "strategy_name": config.strategy_name,
                        "variety_name": variety_name,
                        "sector": SECTOR_BY_VARIETY[variety_name],
                        "side": "long",
                        "entry_date": pos["entry_date"],
                        "exit_date": trade_date,
                        "entry_price": float(pos["entry_price"]),
                        "exit_price": exit_price,
                        "holding_days": i - int(pos["entry_idx"]),
                        "pnl_ratio": trade_return(1, float(pos["entry_price"]), exit_price),
                        "entry_main_score": pos["main_score"],
                        "exit_reason": "tp3_main_turn_down",
                    }
                )
                holdings.pop(variety_name, None)
                closed_today.add(variety_name)
                closed_count += 1
            elif pos["side"] == -1 and bool(row["exit_short_signal"]):
                exit_price = float(row["close"])
                trades.append(
                    {
                        "strategy_name": config.strategy_name,
                        "variety_name": variety_name,
                        "sector": SECTOR_BY_VARIETY[variety_name],
                        "side": "short",
                        "entry_date": pos["entry_date"],
                        "exit_date": trade_date,
                        "entry_price": float(pos["entry_price"]),
                        "exit_price": exit_price,
                        "holding_days": i - int(pos["entry_idx"]),
                        "pnl_ratio": trade_return(-1, float(pos["entry_price"]), exit_price),
                        "entry_main_score": pos["main_score"],
                        "exit_reason": "tp3_main_turn_up",
                    }
                )
                holdings.pop(variety_name, None)
                closed_today.add(variety_name)
                closed_count += 1

        sector_reject_count = 0
        capacity_reject_count = 0
        selected_candidates: list[dict] = []
        raw_signals: list[dict] = []

        for variety_name in TARGET_VARIETIES:
            if variety_name in start_holdings or variety_name in closed_today:
                continue
            row = signal_map[variety_name].iloc[i]
            side = 0
            if bool(row["long_signal"]):
                side = 1
            elif bool(row["short_signal"]):
                side = -1
            if side == 0:
                continue
            raw_signals.append(
                {
                    "variety_name": variety_name,
                    "sector": SECTOR_BY_VARIETY[variety_name],
                    "side": side,
                    "close": float(row["close"]),
                    "main_score": float(row["main_score"]) if pd.notna(row["main_score"]) else np.nan,
                }
            )

        if entry_capacity <= 0:
            capacity_reject_count = len(raw_signals)
        else:
            filtered_signals: list[dict] = []
            for candidate in raw_signals:
                if config.sector_mutex and candidate["sector"] in start_sectors:
                    sector_reject_count += 1
                    continue
                filtered_signals.append(candidate)

            filtered_signals.sort(
                key=lambda x: (
                    pd.isna(x["main_score"]),
                    -(x["main_score"] if pd.notna(x["main_score"]) else 0.0),
                    x["variety_name"],
                )
            )

            used_sectors = set(start_sectors)
            for candidate in filtered_signals:
                if config.sector_mutex and candidate["sector"] in used_sectors:
                    sector_reject_count += 1
                    continue
                if len(selected_candidates) >= entry_capacity:
                    capacity_reject_count += 1
                    continue
                selected_candidates.append(candidate)
                used_sectors.add(candidate["sector"])

        for candidate in selected_candidates:
            holdings[candidate["variety_name"]] = {
                "side": candidate["side"],
                "entry_idx": i,
                "entry_date": trade_date,
                "entry_price": candidate["close"],
                "main_score": candidate["main_score"],
            }

        daily_row = {
            "trade_date": trade_date,
            "strategy_name": config.strategy_name,
            "opened_count": len(selected_candidates),
            "closed_count": closed_count,
            "occupied_slots_after_close": len(holdings),
            "sector_reject_count": sector_reject_count,
            "capacity_reject_count": capacity_reject_count,
            "holdings_after_close": "; ".join(
                f"{name}:{'L' if holdings[name]['side'] == 1 else 'S'}" for name in sorted(holdings)
            ),
        }

        for variety_name in TARGET_VARIETIES:
            position = holdings[variety_name]["side"] if variety_name in holdings else 0
            daily_row[f"{variety_name}_position_after_close"] = position
            daily_row[f"{variety_name}_close_return"] = float(signal_map[variety_name].iloc[i]["close_return"])
        daily_rows.append(daily_row)

    if holdings:
        last_date = dates[-1]
        for variety_name, pos in sorted(holdings.items()):
            last_row = signal_map[variety_name].iloc[-1]
            exit_price = float(last_row["close"])
            trades.append(
                {
                    "strategy_name": config.strategy_name,
                    "variety_name": variety_name,
                    "sector": SECTOR_BY_VARIETY[variety_name],
                    "side": "long" if pos["side"] == 1 else "short",
                    "entry_date": pos["entry_date"],
                    "exit_date": last_date,
                    "entry_price": float(pos["entry_price"]),
                    "exit_price": exit_price,
                    "holding_days": len(dates) - 1 - int(pos["entry_idx"]),
                    "pnl_ratio": trade_return(int(pos["side"]), float(pos["entry_price"]), exit_price),
                    "entry_main_score": pos["main_score"],
                    "exit_reason": "final_close",
                }
            )

    daily_df = pd.DataFrame(daily_rows)
    weighted_cols: list[str] = []
    for variety_name in TARGET_VARIETIES:
        prev_col = f"{variety_name}_position_prev"
        ret_col = f"{variety_name}_weighted_return"
        daily_df[prev_col] = (
            daily_df[f"{variety_name}_position_after_close"].shift(1).fillna(0).astype(int)
        )
        daily_df[ret_col] = (
            daily_df[prev_col] * daily_df[f"{variety_name}_close_return"] / config.weight_slots
        )
        weighted_cols.append(ret_col)

    daily_df["portfolio_daily_return"] = daily_df[weighted_cols].sum(axis=1)
    daily_df["equity_curve"] = (1.0 + daily_df["portfolio_daily_return"]).cumprod()
    daily_df["occupied_slots_prev"] = daily_df[
        [f"{name}_position_prev" for name in TARGET_VARIETIES]
    ].abs().sum(axis=1)

    trades_df = pd.DataFrame(trades).sort_values(
        ["entry_date", "variety_name", "side"],
        ignore_index=True,
    )

    sector_rows = []
    for sector in SECTORS:
        names = [name for name, sec in TARGET_POOL if sec == sector]
        held_days = int(
            daily_df[[f"{name}_position_after_close" for name in names]].abs().sum(axis=1).gt(0).sum()
        )
        sector_rows.append(
            {
                "strategy_name": config.strategy_name,
                "sector": sector,
                "held_days": held_days,
                "exposure_share": held_days / len(daily_df),
            }
        )
    sector_exposure_df = pd.DataFrame(sector_rows).sort_values("held_days", ascending=False)

    contribution_rows = []
    for variety_name in TARGET_VARIETIES:
        contribution_rows.append(
            {
                "strategy_name": config.strategy_name,
                "variety_name": variety_name,
                "sector": SECTOR_BY_VARIETY[variety_name],
                "return_contribution": float(daily_df[f"{variety_name}_weighted_return"].sum()),
                "held_days": int(daily_df[f"{variety_name}_position_after_close"].abs().sum()),
                "trade_count": int((trades_df["variety_name"] == variety_name).sum()) if len(trades_df) else 0,
            }
        )
    contribution_df = pd.DataFrame(contribution_rows).sort_values(
        "return_contribution",
        ascending=False,
    )

    summary = {
        "strategy_name": config.strategy_name,
        "trade_count": int(len(trades_df)),
        "win_rate": float(trades_df["pnl_ratio"].gt(0).mean()) if len(trades_df) else np.nan,
        "avg_trade_return": float(trades_df["pnl_ratio"].mean()) if len(trades_df) else np.nan,
        "median_holding_days": float(trades_df["holding_days"].median()) if len(trades_df) else np.nan,
        "strategy_return": float(daily_df["equity_curve"].iloc[-1] - 1.0),
        "max_drawdown": compute_max_drawdown(daily_df["equity_curve"]),
        "avg_occupied_slots": float(daily_df["occupied_slots_after_close"].mean()),
        "avg_invested_ratio": float(daily_df["occupied_slots_prev"].mean() / config.weight_slots),
        "sector_reject_count": int(daily_df["sector_reject_count"].sum()),
        "capacity_reject_count": int(daily_df["capacity_reject_count"].sum()),
        "signal_count": int(
            sum(
                signal_map[name]["long_signal"].sum() + signal_map[name]["short_signal"].sum()
                for name in TARGET_VARIETIES
            )
        ),
        "final_equity": float(daily_df["equity_curve"].iloc[-1]),
    }
    return daily_df, trades_df, sector_exposure_df, contribution_df, summary


def build_independent_equal_weight(
    single_curves: dict[str, pd.DataFrame],
    single_summaries: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    portfolio = pd.DataFrame({"trade_date": single_curves[TARGET_VARIETIES[0]]["trade_date"]})
    daily_cols = []
    for variety_name in TARGET_VARIETIES:
        col = f"{variety_name}_daily_return"
        portfolio[col] = single_curves[variety_name]["strategy_daily_return"].to_numpy()
        daily_cols.append(col)

    portfolio["portfolio_daily_return"] = portfolio[daily_cols].mean(axis=1)
    portfolio["equity_curve"] = (1.0 + portfolio["portfolio_daily_return"]).cumprod()

    summary = {
        "strategy_name": "12品种独立等权",
        "trade_count": int(single_summaries["trade_count"].sum()),
        "win_rate": float(single_summaries["win_rate"].mean()),
        "avg_trade_return": float(single_summaries["avg_trade_return"].mean()),
        "median_holding_days": float(single_summaries["median_holding_days"].median()),
        "strategy_return": float(portfolio["equity_curve"].iloc[-1] - 1.0),
        "max_drawdown": compute_max_drawdown(portfolio["equity_curve"]),
        "avg_occupied_slots": np.nan,
        "avg_invested_ratio": 1.0,
        "sector_reject_count": 0,
        "capacity_reject_count": 0,
        "signal_count": int(single_summaries["signal_long_days"].sum() + single_summaries["signal_short_days"].sum()),
        "final_equity": float(portfolio["equity_curve"].iloc[-1]),
    }
    return portfolio, summary


def build_strategy_summary_markdown(summary_df: pd.DataFrame) -> str:
    def fmt_pct(value: float) -> str:
        if pd.isna(value):
            return ""
        return f"{value * 100:.2f}%"

    def fmt_num(value: float) -> str:
        if pd.isna(value):
            return ""
        return f"{value:.2f}"

    lines = [
        "# 策略 2 组合回测摘要",
        "",
        "口径：12 品种、A 通道、严格 7 日开仓、3 日主力拐头离场；组合层按不同约束版本做对照。",
        "",
        "| 组合版本 | 收益率 | 最大回撤 | 交易次数 | 胜率 | 单笔平均收益 | 日均持仓槽位 | 板块互斥拒单 | 槽位不足拒单 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in summary_df.iterrows():
        lines.append(
            f"| {row['strategy_name']} | {fmt_pct(row['strategy_return'])} | "
            f"{fmt_pct(row['max_drawdown'])} | {int(row['trade_count'])} | "
            f"{fmt_pct(row['win_rate'])} | {fmt_pct(row['avg_trade_return'])} | "
            f"{fmt_num(row['avg_occupied_slots'])} | {int(row['sector_reject_count'])} | "
            f"{int(row['capacity_reject_count'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    con = sqlite3.connect(DB)
    variety_map = load_varieties(con).set_index("name")

    missing = [name for name in TARGET_VARIETIES if name not in variety_map.index]
    if missing:
        raise ValueError(f"数据库缺少这些品种：{missing}")

    signal_map: dict[str, pd.DataFrame] = {}
    single_curves: dict[str, pd.DataFrame] = {}
    single_summaries: list[dict] = []
    single_trades_list: list[pd.DataFrame] = []

    for variety_name in TARGET_VARIETIES:
        variety_id = int(variety_map.loc[variety_name, "id"])
        df = load_df(con, variety_id)
        signal_map[variety_name] = compute_signals_strict7_tp3(df)

        curve_df, trades_df, summary = backtest_single_strategy(df, variety_name)
        single_curves[variety_name] = curve_df
        single_summaries.append(summary)
        single_trades_list.append(trades_df)

    con.close()

    configs = [
        PortfolioConfig("策略2_完整约束", max_slots=3, weight_slots=3, sector_mutex=True),
        PortfolioConfig("策略2_仅3槽_无板块互斥", max_slots=3, weight_slots=3, sector_mutex=False),
        PortfolioConfig("策略2_仅板块互斥_6板块槽位", max_slots=len(SECTORS), weight_slots=len(SECTORS), sector_mutex=True),
    ]

    strategy_daily_list: list[pd.DataFrame] = []
    strategy_trades_list: list[pd.DataFrame] = []
    sector_exposure_list: list[pd.DataFrame] = []
    contribution_list: list[pd.DataFrame] = []
    strategy_summaries: list[dict] = []

    for config in configs:
        daily_df, trades_df, sector_df, contrib_df, summary = simulate_portfolio(signal_map, config)
        strategy_daily_list.append(daily_df)
        strategy_trades_list.append(trades_df)
        sector_exposure_list.append(sector_df)
        contribution_list.append(contrib_df)
        strategy_summaries.append(summary)

    single_summary_df = pd.DataFrame(single_summaries).sort_values("strategy_return", ascending=False)
    single_trades_df = pd.concat(single_trades_list, ignore_index=True)

    independent_daily_df, independent_summary = build_independent_equal_weight(single_curves, single_summary_df)
    strategy_daily_list.append(independent_daily_df.assign(strategy_name="12品种独立等权"))
    strategy_summaries.append(independent_summary)

    jiaomei_row = single_summary_df[single_summary_df["variety_name"] == "焦煤"].iloc[0]
    strategy_summaries.append(
        {
            "strategy_name": "焦煤_单品种",
            "trade_count": int(jiaomei_row["trade_count"]),
            "win_rate": float(jiaomei_row["win_rate"]),
            "avg_trade_return": float(jiaomei_row["avg_trade_return"]),
            "median_holding_days": float(jiaomei_row["median_holding_days"]),
            "strategy_return": float(jiaomei_row["strategy_return"]),
            "max_drawdown": float(jiaomei_row["max_drawdown"]),
            "avg_occupied_slots": 1.0,
            "avg_invested_ratio": 1.0,
            "sector_reject_count": 0,
            "capacity_reject_count": 0,
            "signal_count": int(jiaomei_row["signal_long_days"] + jiaomei_row["signal_short_days"]),
            "final_equity": float(jiaomei_row["strategy_return"] + 1.0),
        }
    )

    strategy_summary_df = pd.DataFrame(strategy_summaries).sort_values(
        "strategy_return",
        ascending=False,
        ignore_index=True,
    )
    strategy_daily_df = pd.concat(strategy_daily_list, ignore_index=True)
    strategy_trades_df = pd.concat(strategy_trades_list, ignore_index=True)
    sector_exposure_df = pd.concat(sector_exposure_list, ignore_index=True)
    contribution_df = pd.concat(contribution_list, ignore_index=True)

    ARTIFACT_DATA.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    strategy_summary_path = ARTIFACT_DATA / "portfolio_strict7_tp3_strategy_summary.csv"
    strategy_daily_path = ARTIFACT_DATA / "portfolio_strict7_tp3_strategy_daily.csv"
    strategy_trades_path = ARTIFACT_DATA / "portfolio_strict7_tp3_strategy_trades.csv"
    sector_exposure_path = ARTIFACT_DATA / "portfolio_strict7_tp3_sector_exposure.csv"
    contribution_path = ARTIFACT_DATA / "portfolio_strict7_tp3_contribution.csv"
    single_summary_path = ARTIFACT_DATA / "portfolio_strict7_tp3_single_summary.csv"
    single_trades_path = ARTIFACT_DATA / "portfolio_strict7_tp3_single_trades.csv"
    summary_md_path = DOCS_DIR / "portfolio_strict7_tp3_summary.md"

    strategy_summary_df.to_csv(strategy_summary_path, index=False)
    strategy_daily_df.to_csv(strategy_daily_path, index=False)
    strategy_trades_df.to_csv(strategy_trades_path, index=False)
    sector_exposure_df.to_csv(sector_exposure_path, index=False)
    contribution_df.to_csv(contribution_path, index=False)
    single_summary_df.to_csv(single_summary_path, index=False)
    single_trades_df.to_csv(single_trades_path, index=False)
    summary_md_path.write_text(build_strategy_summary_markdown(strategy_summary_df), encoding="utf-8")

    print("=" * 108)
    print("策略 2：跨板块分散 · 主力跟随组合策略")
    print("=" * 108)
    print(
        strategy_summary_df[
            [
                "strategy_name",
                "trade_count",
                "win_rate",
                "avg_trade_return",
                "strategy_return",
                "max_drawdown",
                "avg_occupied_slots",
                "sector_reject_count",
                "capacity_reject_count",
            ]
        ].to_string(index=False, float_format=lambda x: f"{x:.4f}")
    )
    print()
    print("交付物：")
    print(f"  - {strategy_summary_path}")
    print(f"  - {strategy_daily_path}")
    print(f"  - {strategy_trades_path}")
    print(f"  - {sector_exposure_path}")
    print(f"  - {contribution_path}")
    print(f"  - {single_summary_path}")
    print(f"  - {single_trades_path}")
    print(f"  - {summary_md_path}")


if __name__ == "__main__":
    main()
