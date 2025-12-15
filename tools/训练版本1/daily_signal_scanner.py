#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货每日信号扫描工具 - 实盘辅助系统

功能：
1. 加载最新行情数据
2. 使用训练好的模型生成今日交易信号
3. 管理持仓和风控提醒
4. 输出可视化报告

使用方法：
    python daily_signal_scanner.py              # 扫描今日信号
    python daily_signal_scanner.py --date 2024-01-15  # 指定日期
    python daily_signal_scanner.py --portfolio  # 查看持仓管理

作者：量化工程师
"""

import argparse
import json
import sqlite3
import warnings
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from tabulate import tabulate

# 导入特征工程函数
from futures_trend_ml import (
    StrategyConfig,
    calculate_atr,
    compute_trend_features,
    get_active_contracts,
)

warnings.filterwarnings('ignore')


# ==================================================
# 配置
# ==================================================

@dataclass
class ScannerConfig:
    """扫描器配置"""
    # 数据库路径
    db_path: str = ""
    
    # 模型路径
    long_model_path: str = ""
    short_model_path: str = ""
    
    # 信号阈值（概率）- 基于回测 top 5% 阈值
    long_threshold: float = 0.5342  # 多头阈值（测试集 top 5%）
    short_threshold: float = 0.5245 # 空头阈值（测试集 top 5%）
    
    # 风控参数
    stop_loss_pct: float = 0.02     # 2% 止损
    take_profit_pct: float = 0.05   # 5% 止盈
    trailing_stop_pct: float = 0.015  # 1.5% 移动止损
    max_holding_days: int = 10
    
    # 持仓文件路径
    portfolio_path: str = ""
    
    # 预热天数（特征计算需要）
    warmup_days: int = 80


@dataclass
class Signal:
    """交易信号"""
    symbol: str
    direction: str  # 'LONG' or 'SHORT'
    probability: float
    current_price: float
    signal_date: str
    
    # 风控价位
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    
    # 额外信息
    trend_score: float = 0.0
    vol_contraction: float = 0.0
    rsi: float = 0.0


@dataclass
class Position:
    """持仓记录"""
    symbol: str
    direction: str  # 'LONG' or 'SHORT'
    entry_date: str
    entry_price: float
    current_price: float = 0.0
    peak_price: float = 0.0
    pnl_pct: float = 0.0
    holding_days: int = 0
    status: str = 'OPEN'  # 'OPEN', 'STOP_LOSS', 'TAKE_PROFIT', 'TRAILING_STOP'


# ==================================================
# 数据加载
# ==================================================

def load_latest_data(
    db_path: str,
    warmup_days: int = 80,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    从数据库加载最新数据（包含足够的预热期）
    
    参数:
        db_path: 数据库路径
        warmup_days: 预热天数
        end_date: 截止日期（默认为最新）
    """
    conn = sqlite3.connect(db_path)
    
    # 获取活跃合约
    symbols = get_active_contracts(conn)
    print(f"[数据] 发现 {len(symbols)} 个活跃合约")
    
    all_dfs = []
    
    for symbol in symbols:
        table_name = f"hist_{symbol.lower()}"
        
        try:
            # 检查表是否存在
            check_query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            if not conn.execute(check_query).fetchone():
                continue
            
            # 读取最近的数据
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
            
            # 重命名列
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
            
            # 按日期正序排列
            df = df.sort_values('date').reset_index(drop=True)
            
            all_dfs.append(df)
            
        except Exception as e:
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
    """
    为最新一天计算特征
    
    只返回每个品种最新一天的特征
    """
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
        
        # ===== 1. 价格动量 =====
        for period in [3, 5, 10, 20]:
            df_sym[f'feat_ret_{period}'] = close.pct_change(period)
        
        df_sym['feat_momentum_accel'] = df_sym['feat_ret_5'] - df_sym['feat_ret_5'].shift(5)
        
        # ===== 2. 突破信号 =====
        for period in [10, 20, 40]:
            rolling_high = high.rolling(period, min_periods=1).max()
            rolling_low = low.rolling(period, min_periods=1).min()
            range_hl = rolling_high - rolling_low
            
            df_sym[f'feat_price_pos_{period}'] = (close - rolling_low) / (range_hl + 1e-6)
            df_sym[f'feat_break_high_{period}'] = (close >= rolling_high.shift(1)).astype(int)
            df_sym[f'feat_break_low_{period}'] = (close <= rolling_low.shift(1)).astype(int)
            df_sym[f'feat_dist_high_{period}'] = (rolling_high - close) / (close + 1e-6)
            df_sym[f'feat_dist_low_{period}'] = (close - rolling_low) / (close + 1e-6)
        
        # ===== 3. 均线系统 =====
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
        
        # ===== 4. 波动率特征 =====
        returns = close.pct_change()
        
        for period in [5, 10, 20]:
            df_sym[f'feat_vol_{period}'] = returns.rolling(period, min_periods=1).std()
        
        df_sym['feat_vol_contraction'] = df_sym['feat_vol_5'] / (df_sym['feat_vol_20'] + 1e-6)
        
        df_sym['feat_atr_20'] = calculate_atr(df_sym, period=20)
        df_sym['feat_atr_ratio'] = df_sym['feat_atr_20'] / (close + 1e-6)
        df_sym['feat_atr_change'] = df_sym['feat_atr_20'].pct_change(5)
        
        # ===== 5. 趋势强度 =====
        slope_10, r2_10 = compute_trend_features(close, window=10)
        slope_20, r2_20 = compute_trend_features(close, window=20)
        
        df_sym['feat_trend_slope_10'] = slope_10
        df_sym['feat_trend_r2_10'] = r2_10
        df_sym['feat_trend_slope_20'] = slope_20
        df_sym['feat_trend_r2_20'] = r2_20
        
        df_sym['feat_trend_score_10'] = slope_10 * r2_10
        df_sym['feat_trend_score_20'] = slope_20 * r2_20
        
        # ===== 6. 成交量特征 =====
        vol_ma_5 = volume.rolling(5, min_periods=1).mean()
        vol_ma_20 = volume.rolling(20, min_periods=1).mean()
        
        df_sym['feat_vol_ratio_5'] = volume / (vol_ma_5 + 1e-6)
        df_sym['feat_vol_ratio_20'] = volume / (vol_ma_20 + 1e-6)
        df_sym['feat_vol_trend'] = vol_ma_5 / (vol_ma_20 + 1e-6)
        
        df_sym['feat_vol_breakout'] = (
            (volume > vol_ma_20 * 1.5) & 
            (abs(returns) > df_sym['feat_vol_20'])
        ).astype(int)
        
        # ===== 7. 持仓量特征 =====
        oi_ma_20 = oi.rolling(20, min_periods=1).mean()
        
        df_sym['feat_oi_ratio'] = oi / (oi_ma_20 + 1e-6)
        df_sym['feat_oi_chg_5'] = oi.pct_change(5)
        
        price_up = (close > close.shift(1)).astype(int)
        oi_up = (oi > oi.shift(1)).astype(int)
        
        df_sym['feat_price_oi_bull'] = (price_up & oi_up).astype(int)
        df_sym['feat_price_oi_bear'] = ((1 - price_up) & oi_up).astype(int)
        
        # ===== 8. K线形态 =====
        bar_range = high - low
        body = abs(close - open_price)
        
        df_sym['feat_body_ratio'] = body / (bar_range + 1e-6)
        df_sym['feat_close_pos'] = (close - low) / (bar_range + 1e-6)
        df_sym['feat_consec_up'] = (close > open_price).rolling(3).sum()
        df_sym['feat_consec_down'] = (close < open_price).rolling(3).sum()
        
        # ===== 9. RSI =====
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        avg_gain = gain.rolling(14, min_periods=1).mean()
        avg_loss = loss.rolling(14, min_periods=1).mean()
        
        rs = avg_gain / (avg_loss + 1e-6)
        df_sym['feat_rsi_14'] = 100 - (100 / (1 + rs))
        
        # ===== 10. 布林带 =====
        ma_20 = df_sym['MA_20']
        std_20 = close.rolling(20, min_periods=1).std()
        
        upper_band = ma_20 + 2 * std_20
        lower_band = ma_20 - 2 * std_20
        
        df_sym['feat_bb_pos'] = (close - lower_band) / (upper_band - lower_band + 1e-6)
        df_sym['feat_bb_break_up'] = (close > upper_band).astype(int)
        df_sym['feat_bb_break_down'] = (close < lower_band).astype(int)
        
        # 只保留最后一行
        feature_dfs.append(df_sym.iloc[[-1]])
    
    if not feature_dfs:
        return pd.DataFrame()
    
    df_feat = pd.concat(feature_dfs, ignore_index=True)
    
    # 处理异常值
    feature_cols = [col for col in df_feat.columns if col.startswith('feat_')]
    for col in feature_cols:
        df_feat[col] = df_feat[col].replace([np.inf, -np.inf], np.nan)
        df_feat[col] = df_feat[col].clip(-1e10, 1e10)
    
    return df_feat


# ==================================================
# 信号生成
# ==================================================

def generate_signals(
    df_feat: pd.DataFrame,
    long_model: Any,
    short_model: Any,
    config: ScannerConfig
) -> List[Signal]:
    """
    生成今日交易信号
    """
    feature_cols = [col for col in df_feat.columns if col.startswith('feat_')]
    
    # 检查特征完整性
    valid_mask = df_feat[feature_cols].notna().all(axis=1)
    df_valid = df_feat[valid_mask].copy()
    
    if len(df_valid) == 0:
        return []
    
    X = df_valid[feature_cols].values
    
    # 预测概率
    p_long = long_model.predict_proba(X)[:, 1]
    p_short = short_model.predict_proba(X)[:, 1]
    
    df_valid['p_long'] = p_long
    df_valid['p_short'] = p_short
    
    signals = []
    
    for _, row in df_valid.iterrows():
        symbol = row['symbol']
        current_price = row['close']
        signal_date = str(row['date'].date()) if hasattr(row['date'], 'date') else str(row['date'])[:10]
        
        # 多头信号
        if row['p_long'] >= config.long_threshold:
            stop_loss = current_price * (1 - config.stop_loss_pct)
            take_profit = current_price * (1 + config.take_profit_pct)
            
            signals.append(Signal(
                symbol=symbol,
                direction='LONG',
                probability=row['p_long'],
                current_price=current_price,
                signal_date=signal_date,
                stop_loss_price=stop_loss,
                take_profit_price=take_profit,
                trend_score=row.get('feat_trend_score_20', 0),
                vol_contraction=row.get('feat_vol_contraction', 0),
                rsi=row.get('feat_rsi_14', 50)
            ))
        
        # 空头信号
        if row['p_short'] >= config.short_threshold:
            stop_loss = current_price * (1 + config.stop_loss_pct)
            take_profit = current_price * (1 - config.take_profit_pct)
            
            signals.append(Signal(
                symbol=symbol,
                direction='SHORT',
                probability=row['p_short'],
                current_price=current_price,
                signal_date=signal_date,
                stop_loss_price=stop_loss,
                take_profit_price=take_profit,
                trend_score=row.get('feat_trend_score_20', 0),
                vol_contraction=row.get('feat_vol_contraction', 0),
                rsi=row.get('feat_rsi_14', 50)
            ))
    
    # 按概率排序
    signals = sorted(signals, key=lambda x: x.probability, reverse=True)
    
    return signals


# ==================================================
# 持仓管理
# ==================================================

def load_portfolio(filepath: str) -> List[Position]:
    """加载持仓文件"""
    if not Path(filepath).exists():
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return [Position(**p) for p in data]


def save_portfolio(positions: List[Position], filepath: str) -> None:
    """保存持仓文件"""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    data = [asdict(p) for p in positions]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"[持仓] 已保存至: {filepath}")


def update_portfolio(
    positions: List[Position],
    df_latest: pd.DataFrame,
    config: ScannerConfig
) -> Tuple[List[Position], List[Dict]]:
    """
    更新持仓状态，检查风控
    
    返回: (更新后的持仓, 需要处理的提醒列表)
    """
    alerts = []
    updated_positions = []
    
    # 获取最新价格
    latest_prices = {}
    for symbol in df_latest['symbol'].unique():
        sym_data = df_latest[df_latest['symbol'] == symbol]
        if len(sym_data) > 0:
            row = sym_data.iloc[-1]
            latest_prices[symbol] = {
                'close': row['close'],
                'high': row['high'],
                'low': row['low'],
                'date': row['date']
            }
    
    for pos in positions:
        if pos.status != 'OPEN':
            continue
        
        if pos.symbol not in latest_prices:
            updated_positions.append(pos)
            continue
        
        price_info = latest_prices[pos.symbol]
        current_price = price_info['close']
        high_price = price_info['high']
        low_price = price_info['low']
        
        # 更新持仓信息
        pos.current_price = current_price
        
        entry_date = datetime.strptime(pos.entry_date, '%Y-%m-%d')
        current_date = datetime.strptime(str(price_info['date'])[:10], '%Y-%m-%d')
        pos.holding_days = (current_date - entry_date).days
        
        # 计算收益
        if pos.direction == 'LONG':
            pos.pnl_pct = (current_price - pos.entry_price) / pos.entry_price
            pos.peak_price = max(pos.peak_price, high_price)
            max_return = (pos.peak_price - pos.entry_price) / pos.entry_price
        else:
            pos.pnl_pct = (pos.entry_price - current_price) / pos.entry_price
            pos.peak_price = min(pos.peak_price, low_price) if pos.peak_price > 0 else low_price
            max_return = (pos.entry_price - pos.peak_price) / pos.entry_price
        
        # 检查风控条件
        alert = None
        
        # 止损
        if pos.pnl_pct <= -config.stop_loss_pct:
            pos.status = 'STOP_LOSS'
            alert = {
                'type': '🔴 止损',
                'symbol': pos.symbol,
                'direction': pos.direction,
                'message': f'亏损 {pos.pnl_pct*100:.2f}% 触发止损',
                'action': '建议平仓'
            }
        
        # 止盈
        elif pos.pnl_pct >= config.take_profit_pct:
            pos.status = 'TAKE_PROFIT'
            alert = {
                'type': '🟢 止盈',
                'symbol': pos.symbol,
                'direction': pos.direction,
                'message': f'盈利 {pos.pnl_pct*100:.2f}% 触发止盈',
                'action': '建议平仓'
            }
        
        # 移动止损
        elif max_return > 0 and (max_return - pos.pnl_pct) >= config.trailing_stop_pct:
            pos.status = 'TRAILING_STOP'
            alert = {
                'type': '🟡 移动止损',
                'symbol': pos.symbol,
                'direction': pos.direction,
                'message': f'从最高收益 {max_return*100:.2f}% 回撤至 {pos.pnl_pct*100:.2f}%',
                'action': '建议平仓'
            }
        
        # 最大持仓天数
        elif pos.holding_days >= config.max_holding_days:
            alert = {
                'type': '⏰ 超时',
                'symbol': pos.symbol,
                'direction': pos.direction,
                'message': f'持仓 {pos.holding_days} 天，已达最大限制',
                'action': '建议评估是否平仓'
            }
        
        if alert:
            alerts.append(alert)
        
        updated_positions.append(pos)
    
    return updated_positions, alerts


def add_position(
    positions: List[Position],
    signal: Signal
) -> List[Position]:
    """从信号添加新持仓"""
    # 检查是否已存在
    for pos in positions:
        if pos.symbol == signal.symbol and pos.status == 'OPEN':
            print(f"[警告] {signal.symbol} 已有持仓，跳过")
            return positions
    
    new_pos = Position(
        symbol=signal.symbol,
        direction=signal.direction,
        entry_date=signal.signal_date,
        entry_price=signal.current_price,
        current_price=signal.current_price,
        peak_price=signal.current_price,
        pnl_pct=0.0,
        holding_days=0,
        status='OPEN'
    )
    
    positions.append(new_pos)
    print(f"[持仓] 添加: {signal.symbol} {signal.direction} @ {signal.current_price:.2f}")
    
    return positions


# ==================================================
# 报告输出
# ==================================================

def print_signals_report(signals: List[Signal], top_n: int = 10) -> None:
    """打印信号报告"""
    print("\n" + "=" * 70)
    print("📊 今日交易信号")
    print("=" * 70)
    
    if not signals:
        print("  暂无符合条件的信号")
        return
    
    # 分离多空信号
    long_signals = [s for s in signals if s.direction == 'LONG']
    short_signals = [s for s in signals if s.direction == 'SHORT']
    
    print(f"\n多头信号: {len(long_signals)} 个 | 空头信号: {len(short_signals)} 个")
    
    # 显示 Top N
    print(f"\n🔺 多头信号 Top {min(top_n, len(long_signals))}:")
    if long_signals:
        table_data = []
        for s in long_signals[:top_n]:
            table_data.append([
                s.symbol,
                f"{s.probability:.2%}",
                f"{s.current_price:.2f}",
                f"{s.stop_loss_price:.2f}",
                f"{s.take_profit_price:.2f}",
                f"{s.rsi:.1f}"
            ])
        
        headers = ['品种', '概率', '现价', '止损', '止盈', 'RSI']
        print(tabulate(table_data, headers=headers, tablefmt='simple'))
    else:
        print("  无")
    
    print(f"\n🔻 空头信号 Top {min(top_n, len(short_signals))}:")
    if short_signals:
        table_data = []
        for s in short_signals[:top_n]:
            table_data.append([
                s.symbol,
                f"{s.probability:.2%}",
                f"{s.current_price:.2f}",
                f"{s.stop_loss_price:.2f}",
                f"{s.take_profit_price:.2f}",
                f"{s.rsi:.1f}"
            ])
        
        headers = ['品种', '概率', '现价', '止损', '止盈', 'RSI']
        print(tabulate(table_data, headers=headers, tablefmt='simple'))
    else:
        print("  无")


def print_portfolio_report(positions: List[Position], alerts: List[Dict]) -> None:
    """打印持仓报告"""
    print("\n" + "=" * 70)
    print("📈 持仓管理")
    print("=" * 70)
    
    # 打印提醒
    if alerts:
        print("\n⚠️  风控提醒:")
        for alert in alerts:
            print(f"  {alert['type']} [{alert['symbol']}] {alert['direction']}")
            print(f"     {alert['message']}")
            print(f"     → {alert['action']}")
        print()
    
    # 打印持仓
    open_positions = [p for p in positions if p.status == 'OPEN']
    closed_positions = [p for p in positions if p.status != 'OPEN']
    
    print(f"\n📋 当前持仓 ({len(open_positions)} 个):")
    if open_positions:
        table_data = []
        for p in open_positions:
            pnl_str = f"{p.pnl_pct*100:+.2f}%"
            if p.pnl_pct > 0:
                pnl_str = f"🟢 {pnl_str}"
            elif p.pnl_pct < 0:
                pnl_str = f"🔴 {pnl_str}"
            
            table_data.append([
                p.symbol,
                p.direction,
                f"{p.entry_price:.2f}",
                f"{p.current_price:.2f}",
                pnl_str,
                p.holding_days,
                p.entry_date
            ])
        
        headers = ['品种', '方向', '入场价', '现价', '盈亏', '天数', '开仓日期']
        print(tabulate(table_data, headers=headers, tablefmt='simple'))
    else:
        print("  暂无持仓")
    
    # 统计
    if open_positions:
        total_pnl = sum(p.pnl_pct for p in open_positions) / len(open_positions)
        print(f"\n持仓平均收益: {total_pnl*100:+.2f}%")


def save_signals_to_csv(signals: List[Signal], filepath: str) -> None:
    """保存信号到 CSV"""
    if not signals:
        return
    
    df = pd.DataFrame([asdict(s) for s in signals])
    df.to_csv(filepath, index=False, encoding='utf-8')
    print(f"[导出] 信号已保存至: {filepath}")


# ==================================================
# 主程序
# ==================================================

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='期货每日信号扫描工具')
    parser.add_argument('--date', type=str, default=None, help='指定扫描日期 (YYYY-MM-DD)')
    parser.add_argument('--portfolio', action='store_true', help='只查看持仓')
    parser.add_argument('--add', type=str, default=None, help='添加持仓 (格式: symbol,direction,price)')
    parser.add_argument('--remove', type=str, default=None, help='移除持仓 (品种代码)')
    parser.add_argument('--export', action='store_true', help='导出信号到 CSV')
    parser.add_argument('--top', type=int, default=10, help='显示 Top N 信号')
    
    args = parser.parse_args()
    
    # 配置路径
    script_dir = Path(__file__).parent
    
    config = ScannerConfig(
        db_path=str(script_dir.parent / 'database' / 'futures' / 'futures.db'),
        long_model_path=str(script_dir / 'models' / 'long_model_lgbm.pkl'),
        short_model_path=str(script_dir / 'models' / 'short_model_lgbm.pkl'),
        portfolio_path=str(script_dir / 'portfolio' / 'positions.json'),
        long_threshold=0.5342,  # 来自回测结果（测试集 top 5%）
        short_threshold=0.5245  # 来自回测结果（测试集 top 5%）
    )
    
    print("=" * 70)
    print("🔍 期货每日信号扫描工具")
    print("=" * 70)
    print(f"数据库: {config.db_path}")
    print(f"扫描日期: {args.date or '最新'}")
    
    # 加载模型
    try:
        long_model = joblib.load(config.long_model_path)
        short_model = joblib.load(config.short_model_path)
        print(f"[模型] 加载成功")
    except Exception as e:
        print(f"[错误] 模型加载失败: {e}")
        print("请先运行 futures_trend_ml.py 训练模型")
        return
    
    # 加载最新数据
    df_latest = load_latest_data(
        config.db_path,
        warmup_days=config.warmup_days,
        end_date=args.date
    )
    
    # 加载持仓
    positions = load_portfolio(config.portfolio_path)
    
    # 处理持仓命令
    if args.add:
        parts = args.add.split(',')
        if len(parts) == 3:
            symbol, direction, price = parts
            signal = Signal(
                symbol=symbol.upper(),
                direction=direction.upper(),
                probability=1.0,
                current_price=float(price),
                signal_date=str(datetime.now().date())
            )
            positions = add_position(positions, signal)
            save_portfolio(positions, config.portfolio_path)
        else:
            print("[错误] 格式错误，应为: symbol,direction,price")
        return
    
    if args.remove:
        positions = [p for p in positions if p.symbol.upper() != args.remove.upper()]
        save_portfolio(positions, config.portfolio_path)
        print(f"[持仓] 已移除: {args.remove}")
        return
    
    # 更新持仓状态
    positions, alerts = update_portfolio(positions, df_latest, config)
    
    # 只查看持仓
    if args.portfolio:
        print_portfolio_report(positions, alerts)
        save_portfolio(positions, config.portfolio_path)
        return
    
    # 计算特征
    print("\n[特征] 计算中...")
    df_feat = compute_features_for_latest(df_latest)
    print(f"[特征] 完成，{len(df_feat)} 个品种")
    
    # 生成信号
    print("\n[信号] 生成中...")
    signals = generate_signals(df_feat, long_model, short_model, config)
    
    # 输出报告
    print_signals_report(signals, top_n=args.top)
    print_portfolio_report(positions, alerts)
    
    # 保存持仓
    save_portfolio(positions, config.portfolio_path)
    
    # 导出 CSV
    if args.export and signals:
        output_dir = script_dir / 'output'
        output_dir.mkdir(exist_ok=True)
        date_str = args.date or str(datetime.now().date())
        save_signals_to_csv(signals, str(output_dir / f'signals_{date_str}.csv'))
    
    print("\n" + "=" * 70)
    print("✅ 扫描完成!")
    print("=" * 70)


if __name__ == "__main__":
    main()

