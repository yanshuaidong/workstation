#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多策略每日信号扫描工具

功能：
1. 同时使用3组策略模型预测
2. 对比各策略信号，找出共识信号
3. 输出综合分析报告

策略组：
- 大行情型 (big_trend): 交易间隔2.9天，盈亏比最高
- 高阈值型 (high_threshold): 回撤最低，风控最佳
- 超严格型 (strict): 胜率最高，夏普最高

使用方法：
    python daily_signal_scanner_multi.py              # 扫描今日信号
    python daily_signal_scanner_multi.py --date 2024-01-15  # 指定日期
    python daily_signal_scanner_multi.py --consensus   # 只显示共识信号

作者：量化工程师
"""

import argparse
import json
import sqlite3
import warnings
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import joblib
import numpy as np
import pandas as pd
from tabulate import tabulate

# 导入特征工程函数
from futures_trend_ml import (
    calculate_atr,
    compute_trend_features,
    get_active_contracts,
)

warnings.filterwarnings('ignore')


# ==================================================
# 数据类
# ==================================================

@dataclass
class StrategySignal:
    """单策略信号"""
    symbol: str
    direction: str  # 'LONG' or 'SHORT'
    probability: float
    current_price: float
    
    
@dataclass
class MultiStrategySignal:
    """多策略综合信号"""
    symbol: str
    direction: str
    current_price: float
    signal_date: str
    
    # 各策略概率
    big_trend_prob: float = 0.0
    high_threshold_prob: float = 0.0
    strict_prob: float = 0.0
    
    # 信号触发情况
    big_trend_signal: bool = False
    high_threshold_signal: bool = False
    strict_signal: bool = False
    
    # 共识度 (1-3)
    consensus_count: int = 0
    
    # 综合评分
    avg_probability: float = 0.0
    
    # 推荐止损止盈（取各策略最保守的）
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    
    # 额外指标
    rsi: float = 50.0
    trend_score: float = 0.0


# ==================================================
# 数据加载
# ==================================================

def load_latest_data(
    db_path: str,
    warmup_days: int = 80,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """从数据库加载最新数据"""
    conn = sqlite3.connect(db_path)
    
    symbols = get_active_contracts(conn)
    print(f"[数据] 发现 {len(symbols)} 个活跃合约")
    
    all_dfs = []
    
    for symbol in symbols:
        table_name = f"hist_{symbol.lower()}"
        
        try:
            check_query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            if not conn.execute(check_query).fetchone():
                continue
            
            if end_date:
                query = f"""
                    SELECT * FROM {table_name} 
                    WHERE trade_date <= '{end_date}'
                    ORDER BY trade_date DESC 
                    LIMIT {warmup_days + 10}
                """
            else:
                query = f"""
                    SELECT * FROM {table_name} 
                    ORDER BY trade_date DESC 
                    LIMIT {warmup_days + 10}
                """
            
            df = pd.read_sql_query(query, conn)
            
            if len(df) < warmup_days:
                continue
            
            df = df.rename(columns={
                'trade_date': 'date',
                'open_price': 'open',
                'high_price': 'high',
                'low_price': 'low',
                'close_price': 'close',
                'volume': 'volume',
                'open_interest': 'open_interest'
            })
            
            df = df[['date', 'open', 'high', 'low', 'close', 'volume', 'open_interest']]
            df['symbol'] = symbol
            df = df.sort_values('date').reset_index(drop=True)
            
            all_dfs.append(df)
            
        except Exception:
            continue
    
    conn.close()
    
    if not all_dfs:
        raise ValueError("没有找到有效数据")
    
    df_all = pd.concat(all_dfs, ignore_index=True)
    df_all['date'] = pd.to_datetime(df_all['date'])
    
    latest_date = df_all['date'].max()
    print(f"[数据] 最新数据日期: {latest_date.date()}")
    print(f"[数据] 共 {df_all['symbol'].nunique()} 个品种")
    
    return df_all


# ==================================================
# 特征计算
# ==================================================

def compute_features_for_latest(df: pd.DataFrame) -> pd.DataFrame:
    """为最新一天计算特征"""
    df = df.copy()
    feature_dfs = []
    
    for symbol in df['symbol'].unique():
        mask = df['symbol'] == symbol
        df_sym = df[mask].copy()
        
        if len(df_sym) < 60:
            continue
        
        close = df_sym['close']
        high = df_sym['high']
        low = df_sym['low']
        open_price = df_sym['open']
        volume = df_sym['volume']
        oi = df_sym['open_interest']
        
        # 价格动量
        for period in [3, 5, 10, 20]:
            df_sym[f'feat_ret_{period}'] = close.pct_change(period)
        df_sym['feat_momentum_accel'] = df_sym['feat_ret_5'] - df_sym['feat_ret_5'].shift(5)
        
        # 突破信号
        for period in [10, 20, 40]:
            rolling_high = high.rolling(period, min_periods=1).max()
            rolling_low = low.rolling(period, min_periods=1).min()
            range_hl = rolling_high - rolling_low
            
            df_sym[f'feat_price_pos_{period}'] = (close - rolling_low) / (range_hl + 1e-6)
            df_sym[f'feat_break_high_{period}'] = (close >= rolling_high.shift(1)).astype(int)
            df_sym[f'feat_break_low_{period}'] = (close <= rolling_low.shift(1)).astype(int)
            df_sym[f'feat_dist_high_{period}'] = (rolling_high - close) / (close + 1e-6)
            df_sym[f'feat_dist_low_{period}'] = (close - rolling_low) / (close + 1e-6)
        
        # 均线系统
        ma_periods = [5, 10, 20, 40, 60]
        for period in ma_periods:
            df_sym[f'MA_{period}'] = close.rolling(period, min_periods=1).mean()
        
        df_sym['feat_ma_align_bull'] = (
            (df_sym['MA_5'] > df_sym['MA_10']) & 
            (df_sym['MA_10'] > df_sym['MA_20']) & 
            (df_sym['MA_20'] > df_sym['MA_40'])
        ).astype(int)
        
        df_sym['feat_ma_align_bear'] = (
            (df_sym['MA_5'] < df_sym['MA_10']) & 
            (df_sym['MA_10'] < df_sym['MA_20']) & 
            (df_sym['MA_20'] < df_sym['MA_40'])
        ).astype(int)
        
        df_sym['feat_price_ma20_dev'] = (close - df_sym['MA_20']) / (df_sym['MA_20'] + 1e-6)
        df_sym['feat_price_ma60_dev'] = (close - df_sym['MA_60']) / (df_sym['MA_60'] + 1e-6)
        
        # 波动率特征
        returns = close.pct_change()
        for period in [5, 10, 20]:
            df_sym[f'feat_vol_{period}'] = returns.rolling(period, min_periods=1).std()
        df_sym['feat_vol_contraction'] = df_sym['feat_vol_5'] / (df_sym['feat_vol_20'] + 1e-6)
        
        df_sym['feat_atr_20'] = calculate_atr(df_sym, period=20)
        df_sym['feat_atr_ratio'] = df_sym['feat_atr_20'] / (close + 1e-6)
        df_sym['feat_atr_change'] = df_sym['feat_atr_20'].pct_change(5)
        
        # 趋势强度
        slope_10, r2_10 = compute_trend_features(close, window=10)
        slope_20, r2_20 = compute_trend_features(close, window=20)
        
        df_sym['feat_trend_slope_10'] = slope_10
        df_sym['feat_trend_r2_10'] = r2_10
        df_sym['feat_trend_slope_20'] = slope_20
        df_sym['feat_trend_r2_20'] = r2_20
        df_sym['feat_trend_score_10'] = slope_10 * r2_10
        df_sym['feat_trend_score_20'] = slope_20 * r2_20
        
        # 成交量特征
        vol_ma_5 = volume.rolling(5, min_periods=1).mean()
        vol_ma_20 = volume.rolling(20, min_periods=1).mean()
        
        df_sym['feat_vol_ratio_5'] = volume / (vol_ma_5 + 1e-6)
        df_sym['feat_vol_ratio_20'] = volume / (vol_ma_20 + 1e-6)
        df_sym['feat_vol_trend'] = vol_ma_5 / (vol_ma_20 + 1e-6)
        df_sym['feat_vol_breakout'] = (
            (volume > vol_ma_20 * 1.5) & (abs(returns) > df_sym['feat_vol_20'])
        ).astype(int)
        
        # 持仓量特征
        oi_ma_20 = oi.rolling(20, min_periods=1).mean()
        df_sym['feat_oi_ratio'] = oi / (oi_ma_20 + 1e-6)
        df_sym['feat_oi_chg_5'] = oi.pct_change(5)
        
        price_up = (close > close.shift(1)).astype(int)
        oi_up = (oi > oi.shift(1)).astype(int)
        df_sym['feat_price_oi_bull'] = (price_up & oi_up).astype(int)
        df_sym['feat_price_oi_bear'] = ((1 - price_up) & oi_up).astype(int)
        
        # K线形态
        bar_range = high - low
        body = abs(close - open_price)
        df_sym['feat_body_ratio'] = body / (bar_range + 1e-6)
        df_sym['feat_close_pos'] = (close - low) / (bar_range + 1e-6)
        df_sym['feat_consec_up'] = (close > open_price).rolling(3).sum()
        df_sym['feat_consec_down'] = (close < open_price).rolling(3).sum()
        
        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        avg_gain = gain.rolling(14, min_periods=1).mean()
        avg_loss = loss.rolling(14, min_periods=1).mean()
        rs = avg_gain / (avg_loss + 1e-6)
        df_sym['feat_rsi_14'] = 100 - (100 / (1 + rs))
        
        # 布林带
        ma_20 = df_sym['MA_20']
        std_20 = close.rolling(20, min_periods=1).std()
        upper_band = ma_20 + 2 * std_20
        lower_band = ma_20 - 2 * std_20
        df_sym['feat_bb_pos'] = (close - lower_band) / (upper_band - lower_band + 1e-6)
        df_sym['feat_bb_break_up'] = (close > upper_band).astype(int)
        df_sym['feat_bb_break_down'] = (close < lower_band).astype(int)
        
        feature_dfs.append(df_sym.iloc[[-1]])
    
    if not feature_dfs:
        return pd.DataFrame()
    
    df_feat = pd.concat(feature_dfs, ignore_index=True)
    
    feature_cols = [col for col in df_feat.columns if col.startswith('feat_')]
    for col in feature_cols:
        df_feat[col] = df_feat[col].replace([np.inf, -np.inf], np.nan)
        df_feat[col] = df_feat[col].clip(-1e10, 1e10)
    
    return df_feat


# ==================================================
# 多策略信号生成
# ==================================================

def load_strategy_models(model_dir: Path) -> Dict[str, Dict]:
    """加载所有策略模型"""
    strategies = {}
    
    # 加载策略配置
    strategies_file = model_dir / 'strategies.json'
    if not strategies_file.exists():
        raise FileNotFoundError(f"未找到策略配置文件: {strategies_file}")
    
    with open(strategies_file, 'r', encoding='utf-8') as f:
        strategies_meta = json.load(f)
    
    for strategy_key, meta in strategies_meta.items():
        strategy_dir = model_dir / strategy_key
        
        try:
            long_model = joblib.load(strategy_dir / 'long_model.pkl')
            short_model = joblib.load(strategy_dir / 'short_model.pkl')
            
            strategies[strategy_key] = {
                'name': meta['name'],
                'description': meta['description'],
                'config': meta['config'],
                'thresholds': meta['thresholds'],
                'long_model': long_model,
                'short_model': short_model
            }
            
            print(f"[模型] 加载成功: {meta['name']}")
            
        except Exception as e:
            print(f"[警告] 加载 {strategy_key} 失败: {e}")
    
    return strategies


def generate_multi_strategy_signals(
    df_feat: pd.DataFrame,
    strategies: Dict[str, Dict]
) -> List[MultiStrategySignal]:
    """使用多策略生成信号"""
    
    feature_cols = [col for col in df_feat.columns if col.startswith('feat_')]
    
    # 检查特征完整性
    valid_mask = df_feat[feature_cols].notna().all(axis=1)
    df_valid = df_feat[valid_mask].copy()
    
    if len(df_valid) == 0:
        return []
    
    X = df_valid[feature_cols].values
    
    # 对每个策略预测
    predictions = {}
    for strategy_key, strategy in strategies.items():
        p_long = strategy['long_model'].predict_proba(X)[:, 1]
        p_short = strategy['short_model'].predict_proba(X)[:, 1]
        predictions[strategy_key] = {
            'p_long': p_long,
            'p_short': p_short,
            'long_threshold': strategy['thresholds']['long'],
            'short_threshold': strategy['thresholds']['short'],
            'config': strategy['config']
        }
    
    # 汇总信号
    signals_dict = {}  # (symbol, direction) -> MultiStrategySignal
    
    for idx, row in df_valid.reset_index(drop=True).iterrows():
        symbol = row['symbol']
        current_price = row['close']
        signal_date = str(row['date'].date()) if hasattr(row['date'], 'date') else str(row['date'])[:10]
        
        # 检查各策略的多头信号
        for direction in ['LONG', 'SHORT']:
            key = (symbol, direction)
            
            if key not in signals_dict:
                signals_dict[key] = MultiStrategySignal(
                    symbol=symbol,
                    direction=direction,
                    current_price=current_price,
                    signal_date=signal_date,
                    rsi=row.get('feat_rsi_14', 50),
                    trend_score=row.get('feat_trend_score_20', 0)
                )
            
            sig = signals_dict[key]
            
            for strategy_key, pred in predictions.items():
                if direction == 'LONG':
                    prob = pred['p_long'][idx]
                    threshold = pred['long_threshold']
                    is_signal = prob >= threshold
                else:
                    prob = pred['p_short'][idx]
                    threshold = pred['short_threshold']
                    is_signal = prob >= threshold
                
                # 更新各策略概率
                if strategy_key == 'big_trend':
                    sig.big_trend_prob = prob
                    sig.big_trend_signal = is_signal
                elif strategy_key == 'high_threshold':
                    sig.high_threshold_prob = prob
                    sig.high_threshold_signal = is_signal
                elif strategy_key == 'strict':
                    sig.strict_prob = prob
                    sig.strict_signal = is_signal
    
    # 计算共识度和平均概率
    result_signals = []
    
    for key, sig in signals_dict.items():
        # 计算共识度
        sig.consensus_count = sum([
            sig.big_trend_signal,
            sig.high_threshold_signal,
            sig.strict_signal
        ])
        
        # 只保留至少有一个策略触发的信号
        if sig.consensus_count == 0:
            continue
        
        # 计算平均概率（只计算触发的策略）
        probs = []
        if sig.big_trend_signal:
            probs.append(sig.big_trend_prob)
        if sig.high_threshold_signal:
            probs.append(sig.high_threshold_prob)
        if sig.strict_signal:
            probs.append(sig.strict_prob)
        
        sig.avg_probability = np.mean(probs) if probs else 0
        
        # 计算止损止盈（取最保守的）
        configs = []
        if sig.big_trend_signal:
            configs.append(strategies['big_trend']['config'])
        if sig.high_threshold_signal:
            configs.append(strategies['high_threshold']['config'])
        if sig.strict_signal:
            configs.append(strategies['strict']['config'])
        
        if configs:
            # 止损取最小，止盈取最小
            min_stop_loss = min(c['stop_loss_pct'] for c in configs)
            min_take_profit = min(c['take_profit_pct'] for c in configs)
            
            if sig.direction == 'LONG':
                sig.stop_loss_price = sig.current_price * (1 - min_stop_loss)
                sig.take_profit_price = sig.current_price * (1 + min_take_profit)
            else:
                sig.stop_loss_price = sig.current_price * (1 + min_stop_loss)
                sig.take_profit_price = sig.current_price * (1 - min_take_profit)
        
        result_signals.append(sig)
    
    # 按共识度和平均概率排序
    result_signals = sorted(
        result_signals, 
        key=lambda x: (x.consensus_count, x.avg_probability), 
        reverse=True
    )
    
    return result_signals


# ==================================================
# 报告输出
# ==================================================

def print_multi_strategy_report(
    signals: List[MultiStrategySignal],
    show_consensus_only: bool = False,
    top_n: int = 15
) -> None:
    """打印多策略信号报告"""
    
    print("\n" + "=" * 90)
    print("📊 多策略信号对比分析")
    print("=" * 90)
    
    # 策略说明
    print("\n策略说明:")
    print("  🔵 大行情型 (B): 交易间隔2.9天，盈亏比2.57最高")
    print("  🟢 高阈值型 (H): 回撤4.6%最低，风控最佳")
    print("  🟡 超严格型 (S): 胜率46.6%最高，夏普2.78最高")
    print("\n  ⭐ 共识度: 多个策略同时推荐的品种，信号质量更高")
    
    if not signals:
        print("\n  暂无符合条件的信号")
        return
    
    # 统计
    consensus_3 = [s for s in signals if s.consensus_count == 3]
    consensus_2 = [s for s in signals if s.consensus_count == 2]
    consensus_1 = [s for s in signals if s.consensus_count == 1]
    
    print(f"\n信号统计:")
    print(f"  - 三策略共识 (⭐⭐⭐): {len(consensus_3)} 个")
    print(f"  - 双策略共识 (⭐⭐): {len(consensus_2)} 个")
    print(f"  - 单策略信号 (⭐): {len(consensus_1)} 个")
    
    # 分离多空
    long_signals = [s for s in signals if s.direction == 'LONG']
    short_signals = [s for s in signals if s.direction == 'SHORT']
    
    print(f"\n方向分布: 多头 {len(long_signals)} 个 | 空头 {len(short_signals)} 个")
    
    # 如果只显示共识信号
    if show_consensus_only:
        signals = [s for s in signals if s.consensus_count >= 2]
        print(f"\n[仅显示共识度>=2的信号]")
    
    # 显示多头信号
    print(f"\n{'='*90}")
    print(f"🔺 多头信号 (Top {min(top_n, len(long_signals))})")
    print(f"{'='*90}")
    
    if long_signals:
        _print_signal_table([s for s in long_signals][:top_n])
    else:
        print("  无")
    
    # 显示空头信号
    print(f"\n{'='*90}")
    print(f"🔻 空头信号 (Top {min(top_n, len(short_signals))})")
    print(f"{'='*90}")
    
    if short_signals:
        _print_signal_table([s for s in short_signals][:top_n])
    else:
        print("  无")
    
    # 重点推荐（三策略共识）
    if consensus_3:
        print(f"\n{'='*90}")
        print("⭐⭐⭐ 重点推荐（三策略共识）")
        print(f"{'='*90}")
        _print_signal_table(consensus_3)


def _print_signal_table(signals: List[MultiStrategySignal]) -> None:
    """打印信号表格"""
    table_data = []
    
    for s in signals:
        # 策略触发标记
        strategy_marks = ""
        if s.big_trend_signal:
            strategy_marks += "🔵"
        if s.high_threshold_signal:
            strategy_marks += "🟢"
        if s.strict_signal:
            strategy_marks += "🟡"
        
        # 共识度星级
        consensus_stars = "⭐" * s.consensus_count
        
        table_data.append([
            s.symbol,
            consensus_stars,
            strategy_marks,
            f"{s.current_price:.2f}",
            f"{s.big_trend_prob:.2%}" if s.big_trend_signal else f"({s.big_trend_prob:.2%})",
            f"{s.high_threshold_prob:.2%}" if s.high_threshold_signal else f"({s.high_threshold_prob:.2%})",
            f"{s.strict_prob:.2%}" if s.strict_signal else f"({s.strict_prob:.2%})",
            f"{s.stop_loss_price:.2f}",
            f"{s.take_profit_price:.2f}",
            f"{s.rsi:.0f}"
        ])
    
    headers = ['品种', '共识', '策略', '现价', '大行情', '高阈值', '超严格', '止损', '止盈', 'RSI']
    print(tabulate(table_data, headers=headers, tablefmt='simple'))
    print("\n说明: 括号内为未触发信号的概率值")


def save_signals_to_csv(signals: List[MultiStrategySignal], filepath: str) -> None:
    """保存信号到 CSV"""
    if not signals:
        return
    
    data = []
    for s in signals:
        data.append({
            'symbol': s.symbol,
            'direction': s.direction,
            'consensus_count': s.consensus_count,
            'current_price': s.current_price,
            'signal_date': s.signal_date,
            'big_trend_prob': s.big_trend_prob,
            'big_trend_signal': s.big_trend_signal,
            'high_threshold_prob': s.high_threshold_prob,
            'high_threshold_signal': s.high_threshold_signal,
            'strict_prob': s.strict_prob,
            'strict_signal': s.strict_signal,
            'avg_probability': s.avg_probability,
            'stop_loss_price': s.stop_loss_price,
            'take_profit_price': s.take_profit_price,
            'rsi': s.rsi,
            'trend_score': s.trend_score
        })
    
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"[导出] 信号已保存至: {filepath}")


# ==================================================
# 主程序
# ==================================================

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='多策略每日信号扫描工具')
    parser.add_argument('--date', type=str, default=None, help='指定扫描日期 (YYYY-MM-DD)')
    parser.add_argument('--consensus', action='store_true', help='只显示共识信号 (>=2策略)')
    parser.add_argument('--export', action='store_true', help='导出信号到 CSV')
    parser.add_argument('--top', type=int, default=15, help='显示 Top N 信号')
    
    args = parser.parse_args()
    
    # 配置路径
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / 'database' / 'futures' / 'futures.db'
    model_dir = script_dir / 'models' / 'multi_strategy'
    
    print("=" * 90)
    print("🔍 多策略每日信号扫描工具")
    print("=" * 90)
    print(f"数据库: {db_path}")
    print(f"模型目录: {model_dir}")
    print(f"扫描日期: {args.date or '最新'}")
    
    # 加载模型
    try:
        strategies = load_strategy_models(model_dir)
        if len(strategies) < 3:
            print(f"[警告] 只加载了 {len(strategies)} 个策略，建议先运行 train_multi_strategy.py")
    except FileNotFoundError as e:
        print(f"\n[错误] {e}")
        print("请先运行 python train_multi_strategy.py 训练模型")
        return
    
    # 加载最新数据
    print("\n[数据] 加载中...")
    df_latest = load_latest_data(str(db_path), warmup_days=80, end_date=args.date)
    
    # 计算特征
    print("\n[特征] 计算中...")
    df_feat = compute_features_for_latest(df_latest)
    print(f"[特征] 完成，{len(df_feat)} 个品种")
    
    # 生成多策略信号
    print("\n[信号] 多策略预测中...")
    signals = generate_multi_strategy_signals(df_feat, strategies)
    
    # 输出报告
    print_multi_strategy_report(
        signals, 
        show_consensus_only=args.consensus,
        top_n=args.top
    )
    
    # 导出 CSV
    if args.export and signals:
        output_dir = script_dir / 'output'
        output_dir.mkdir(exist_ok=True)
        date_str = args.date or str(datetime.now().date())
        save_signals_to_csv(signals, str(output_dir / f'multi_signals_{date_str}.csv'))
    
    print("\n" + "=" * 90)
    print("✅ 扫描完成!")
    print("=" * 90)
    print("\n提示:")
    print("  - ⭐⭐⭐ 三策略共识信号质量最高，优先考虑")
    print("  - 🔵大行情 + 🟢高阈值 共识：适合追求低回撤的稳健交易")
    print("  - 🔵大行情 + 🟡超严格 共识：适合追求高胜率的精准交易")


if __name__ == "__main__":
    main()

