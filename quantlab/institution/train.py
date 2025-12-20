#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
融合模型：趋势ML特征 + 国泰君安持仓特征

特点：
1. 完整保留 futures_trend_ml.py 的技术特征体系
2. 加入国泰君安持仓特征（净持仓、进攻信号、增仓强度等）
3. 训练数据从2022年开始（匹配国泰持仓数据时间范围）

作者：量化工程师
日期：2024
"""

import json
import sqlite3
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import RobustScaler

# 尝试导入 LightGBM
try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except (ImportError, OSError) as e:
    HAS_LIGHTGBM = False
    warnings.warn(f"LightGBM 加载失败 ({e})，将使用 sklearn 替代")
    from sklearn.ensemble import GradientBoostingClassifier

warnings.filterwarnings('ignore')

# 设置 matplotlib 中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


# ==================================================
# 一、配置参数
# ==================================================

@dataclass
class StrategyConfig:
    """策略配置参数"""
    # 标签参数
    future_days: int = 5           # 预测未来N天
    long_threshold: float = 0.03   # 多头收益阈值 3%
    short_threshold: float = 0.03  # 空头收益阈值 3%
    
    # 特征参数
    warmup_period: int = 60        # 预热期
    
    # 数据划分（从2022年开始，匹配国泰持仓数据）
    train_start: str = '2022-01-01'
    train_end: str = '2023-12-31'
    valid_end: str = '2024-06-30'
    
    # 交易参数
    signal_percentile: float = 95  # 信号阈值百分位（top 5%，更严格筛选）
    max_holding_days: int = 10     # 最大持仓天数
    stop_loss_pct: float = 0.02    # 固定止损比例 2%
    take_profit_pct: float = 0.05  # 固定止盈比例 5%
    trailing_stop_pct: float = 0.015  # 移动止损比例 1.5%
    fee_rate: float = 0.0003       # 手续费率
    
    # 仓位管理
    max_positions: int = 5         # 最大同时持仓数量
    position_size: float = 0.2     # 单笔仓位占比
    
    # ===== 信号质量筛选（激进模式专用）=====
    require_gtja_attack: bool = False    # 是否要求国泰进攻信号
    min_attack_streak: int = 0           # 最小连续进攻天数
    prefer_high_volatility: bool = False # 是否优先高波动品种


def get_aggressive_config() -> StrategyConfig:
    """
    小资金激进版配置（5万以下）
    
    核心理念：
    - 宁缺毋滥，只做最强信号（Top 3%）
    - 集中火力，单品种重仓（80%仓位）
    - 追求爆发力，提高收益目标
    - 给好机会更多空间（放宽止损，提高止盈）
    """
    return StrategyConfig(
        # 标签：提高收益阈值，只训练识别大机会
        future_days=5,
        long_threshold=0.04,       # 4%起步，只做大机会
        short_threshold=0.04,
        
        warmup_period=60,
        train_start='2022-01-01',
        train_end='2023-12-31',
        valid_end='2024-06-30',
        
        # 交易：极致精选
        signal_percentile=97,      # Top 3%，只做最强信号
        max_holding_days=15,       # 允许更长持仓，让利润奔跑
        stop_loss_pct=0.025,       # 2.5%止损，给好机会一点容错
        take_profit_pct=0.08,      # 8%止盈，目标更高
        trailing_stop_pct=0.02,    # 2%移动止损
        fee_rate=0.0003,
        
        # 仓位：集中火力
        max_positions=1,           # 只做一个品种，满仓干！
        position_size=0.8,         # 80%仓位
        
        # 信号质量：要求国泰进攻共振
        require_gtja_attack=True,  # 必须有国泰进攻信号
        min_attack_streak=1,       # 至少1天连续进攻
        prefer_high_volatility=True
    )


def get_conservative_config() -> StrategyConfig:
    """
    大资金稳健版配置（50万以上）
    
    核心理念：
    - 分散持仓，控制单笔风险
    - 稳健增长，低回撤
    """
    return StrategyConfig(
        future_days=5,
        long_threshold=0.03,
        short_threshold=0.03,
        
        warmup_period=60,
        train_start='2022-01-01',
        train_end='2023-12-31',
        valid_end='2024-06-30',
        
        signal_percentile=90,      # Top 10%
        max_holding_days=10,
        stop_loss_pct=0.02,
        take_profit_pct=0.05,
        trailing_stop_pct=0.015,
        fee_rate=0.0003,
        
        max_positions=5,
        position_size=0.2,
        
        require_gtja_attack=False,
        min_attack_streak=0,
        prefer_high_volatility=False
    )


# 路径配置
PROJECT_ROOT = Path(__file__).parent.parent.parent
FUTURES_DB = PROJECT_ROOT / "database" / "futures" / "futures.db"
INSTITUTION_DB = PROJECT_ROOT / "database" / "institution" / "institution.db"
MAPPING_FILE = PROJECT_ROOT / "database" / "institution" / "mapping.json"

MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ==================================================
# 二、数据加载
# ==================================================

def load_mapping() -> dict:
    """加载期货表名到机构持仓表名的映射"""
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('mappings', {})


def get_futures_data(table_name: str) -> pd.DataFrame:
    """从期货数据库读取历史价格数据"""
    conn = sqlite3.connect(FUTURES_DB)
    try:
        table_name_lower = table_name.lower()
        sql = f"""
        SELECT 
            trade_date as date,
            open_price as open,
            high_price as high,
            low_price as low,
            close_price as close,
            volume,
            open_interest
        FROM {table_name_lower}
        ORDER BY trade_date
        """
        df = pd.read_sql(sql, conn)
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        return pd.DataFrame()
    finally:
        conn.close()


def get_institution_data(variety_name: str) -> pd.DataFrame:
    """从机构持仓数据库读取持仓数据"""
    conn = sqlite3.connect(INSTITUTION_DB)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (variety_name,)
        )
        if not cursor.fetchone():
            return pd.DataFrame()
        
        sql = f"""
        SELECT 
            trade_date as date,
            total_buy,
            total_ss,
            total_buy_chge,
            total_ss_chge
        FROM "{variety_name}"
        ORDER BY trade_date
        """
        df = pd.read_sql(sql, conn)
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        return pd.DataFrame()
    finally:
        conn.close()


def load_all_data(min_days: int = 200) -> pd.DataFrame:
    """
    加载所有品种的融合数据（期货价格 + 国泰持仓）
    """
    print("=" * 60)
    print("开始加载融合数据...")
    print("=" * 60)
    
    mapping = load_mapping()
    all_data = []
    skipped = []
    
    for futures_table, institution_table in mapping.items():
        # 读取期货数据
        df_futures = get_futures_data(futures_table)
        if df_futures.empty:
            skipped.append((futures_table, "期货数据不存在"))
            continue
        
        # 读取机构持仓数据
        df_institution = get_institution_data(institution_table)
        if df_institution.empty:
            skipped.append((futures_table, "持仓数据不存在"))
            continue
        
        # 合并数据
        df = pd.merge(df_futures, df_institution, on='date', how='inner')
        
        if len(df) < min_days:
            skipped.append((futures_table, f"数据不足({len(df)}条)"))
            continue
        
        df['symbol'] = institution_table
        all_data.append(df)
        print(f"  ✓ {institution_table}: {len(df)} 条数据")
    
    if not all_data:
        raise ValueError("没有可用的数据！")
    
    df_all = pd.concat(all_data, ignore_index=True)
    df_all = df_all.sort_values(['symbol', 'date']).reset_index(drop=True)
    
    print(f"\n合计: {len(df_all):,} 条数据, {len(all_data)} 个品种")
    print(f"跳过: {len(skipped)} 个品种")
    print(f"日期范围: {df_all['date'].min().date()} ~ {df_all['date'].max().date()}")
    
    return df_all


# ==================================================
# 三、标签生成
# ==================================================

def calculate_future_returns(df_symbol: pd.DataFrame, future_days: int = 5) -> pd.DataFrame:
    """计算未来N天的收益指标"""
    df = df_symbol.copy()
    
    # 未来N天最高价
    df['future_high'] = df['high'].shift(-1).rolling(window=future_days).max().shift(-future_days + 1)
    # 未来N天最低价
    df['future_low'] = df['low'].shift(-1).rolling(window=future_days).min().shift(-future_days + 1)
    # 未来N天收盘价
    df['future_close'] = df['close'].shift(-future_days)
    
    # 最大上涨幅度（做多最大收益）
    df['max_up_return'] = (df['future_high'] - df['close']) / df['close']
    # 最大下跌幅度（做空最大收益）
    df['max_down_return'] = (df['close'] - df['future_low']) / df['close']
    # 实际N天后收益
    df['future_return'] = (df['future_close'] - df['close']) / df['close']
    
    return df


def assign_labels(df_all: pd.DataFrame, config: StrategyConfig) -> pd.DataFrame:
    """生成标签"""
    print(f"\n[标签生成] 预测未来 {config.future_days} 天")
    print(f"[标签生成] 多头阈值: {config.long_threshold*100:.1f}%, 空头阈值: {config.short_threshold*100:.1f}%")
    
    df = df_all.copy()
    result_dfs = []
    
    for symbol in df['symbol'].unique():
        mask = df['symbol'] == symbol
        df_sym = df[mask].copy()
        df_sym = calculate_future_returns(df_sym, config.future_days)
        result_dfs.append(df_sym)
    
    df = pd.concat(result_dfs, ignore_index=True)
    
    # 生成标签
    df['label_long'] = (df['max_up_return'] >= config.long_threshold).astype(int)
    df['label_short'] = (df['max_down_return'] >= config.short_threshold).astype(int)
    
    # 统计
    valid_mask = df['label_long'].notna() & df['label_short'].notna()
    total_valid = valid_mask.sum()
    long_count = df.loc[valid_mask, 'label_long'].sum()
    short_count = df.loc[valid_mask, 'label_short'].sum()
    
    print(f"[标签生成] 有效样本: {total_valid:,}")
    print(f"[标签生成] 多头信号: {int(long_count):,} ({long_count/total_valid*100:.2f}%)")
    print(f"[标签生成] 空头信号: {int(short_count):,} ({short_count/total_valid*100:.2f}%)")
    
    return df


# ==================================================
# 四、特征工程（融合版：趋势ML + 国泰持仓）
# ==================================================

def calculate_atr(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """计算 ATR"""
    high, low, close = df['high'], df['low'], df['close']
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=1).mean()


def compute_trend_features(close: pd.Series, window: int = 10) -> Tuple[pd.Series, pd.Series]:
    """计算趋势斜率和 R²"""
    slopes, r2s = [], []
    
    for i in range(len(close)):
        if i < window - 1:
            slopes.append(np.nan)
            r2s.append(np.nan)
        else:
            y = close.iloc[i-window+1:i+1].values
            x = np.arange(window).reshape(-1, 1)
            
            if np.any(np.isnan(y)):
                slopes.append(np.nan)
                r2s.append(np.nan)
                continue
            
            y_mean, y_std = y.mean(), y.std()
            if y_std < 1e-10:
                slopes.append(0)
                r2s.append(0)
                continue
            
            y_norm = (y - y_mean) / y_std
            model = LinearRegression()
            model.fit(x, y_norm)
            slopes.append(model.coef_[0])
            r2s.append(model.score(x, y_norm))
    
    return pd.Series(slopes, index=close.index), pd.Series(r2s, index=close.index)


def make_features_fusion(df: pd.DataFrame, warmup_period: int = 60) -> pd.DataFrame:
    """
    融合特征工程：趋势ML完整特征 + 国泰持仓特征
    """
    print(f"\n[特征工程] 生成融合特征，预热期: {warmup_period} 天")
    
    df = df.copy()
    feature_dfs = []
    
    for symbol in df['symbol'].unique():
        mask = df['symbol'] == symbol
        df_sym = df[mask].copy()
        
        close = df_sym['close']
        high = df_sym['high']
        low = df_sym['low']
        open_price = df_sym['open']
        volume = df_sym['volume']
        oi = df_sym['open_interest']
        
        # ========================================
        # Part 1: 趋势ML技术特征（完整保留）
        # ========================================
        
        # ===== 1. 价格动量（多周期）=====
        for period in [3, 5, 10, 20]:
            df_sym[f'feat_ret_{period}'] = close.pct_change(period)
        
        # 动量加速度
        df_sym['feat_momentum_accel'] = df_sym['feat_ret_5'] - df_sym['feat_ret_5'].shift(5)
        
        # ===== 2. 突破信号（多周期）=====
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
        
        # 均线排列
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
        
        # 价格偏离均线
        df_sym['feat_price_ma20_dev'] = (close - df_sym['MA_20']) / (df_sym['MA_20'] + 1e-6)
        df_sym['feat_price_ma60_dev'] = (close - df_sym['MA_60']) / (df_sym['MA_60'] + 1e-6)
        
        # ===== 4. 波动率特征 =====
        returns = close.pct_change()
        for period in [5, 10, 20]:
            df_sym[f'feat_vol_{period}'] = returns.rolling(period, min_periods=1).std()
        
        # 波动率收缩
        df_sym['feat_vol_contraction'] = df_sym['feat_vol_5'] / (df_sym['feat_vol_20'] + 1e-6)
        
        # ATR
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
        
        # 放量突破
        df_sym['feat_vol_breakout'] = (
            (volume > vol_ma_20 * 1.5) & 
            (abs(returns) > df_sym['feat_vol_20'])
        ).astype(int)
        
        # ===== 7. 持仓量特征（市场整体）=====
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
        
        # ========================================
        # Part 2: 国泰君安持仓特征（精简版 - 聚焦主动进攻）
        # ========================================
        # 
        # 核心逻辑（来自实盘经验）：
        # - 净持仓 = 多头 - 空头（正=净多头，负=净空头）
        # - 主动做多 = 净多头 + 净增仓为正（方向一致才是进攻）
        # - 主动做空 = 净空头 + 净增仓为负（方向一致才是进攻）
        # - 关键指标 = 净增仓 / 昨日净持仓（进攻强度，如20%增量）
        #
        
        # 基础持仓数据
        total_buy = df_sym['total_buy']
        total_ss = df_sym['total_ss']
        total_buy_chge = df_sym['total_buy_chge']
        total_ss_chge = df_sym['total_ss_chge']
        
        # ===== 1. 净持仓（核心方向判断）=====
        net_position = total_buy - total_ss
        net_change = total_buy_chge - total_ss_chge
        net_position_prev = net_position.shift(1)
        
        # ===== 2. 主动进攻信号（方向一致才有效）=====
        # 多头进攻：净多头 AND 净增仓 > 0（在加仓做多）
        is_long_attack = (net_position > 0) & (net_change > 0)
        # 空头进攻：净空头 AND 净增仓 < 0（在加仓做空）
        is_short_attack = (net_position < 0) & (net_change < 0)
        
        df_sym['feat_gtja_long_attack'] = is_long_attack.astype(int)
        df_sym['feat_gtja_short_attack'] = is_short_attack.astype(int)
        
        # ===== 3. 进攻强度（核心指标：净增仓/昨日净持仓）=====
        # 多头进攻强度：净增仓 / 昨日净持仓（如从10000增到12000，强度=20%）
        df_sym['feat_gtja_long_intensity'] = 0.0
        mask_long_valid = is_long_attack & (net_position_prev.abs() > 100)
        df_sym.loc[mask_long_valid, 'feat_gtja_long_intensity'] = (
            net_change[mask_long_valid] / net_position_prev[mask_long_valid].abs()
        )
        
        # 空头进攻强度：|净增仓| / |昨日净持仓|
        df_sym['feat_gtja_short_intensity'] = 0.0
        mask_short_valid = is_short_attack & (net_position_prev.abs() > 100)
        df_sym.loc[mask_short_valid, 'feat_gtja_short_intensity'] = (
            net_change[mask_short_valid].abs() / net_position_prev[mask_short_valid].abs()
        )
        
        # ===== 4. 进攻持续性（连续进攻天数）=====
        # 连续多头进攻
        long_attack_group = (is_long_attack != is_long_attack.shift()).cumsum()
        df_sym['feat_gtja_long_streak'] = df_sym.groupby(long_attack_group)['feat_gtja_long_attack'].cumsum()
        
        # 连续空头进攻
        short_attack_group = (is_short_attack != is_short_attack.shift()).cumsum()
        df_sym['feat_gtja_short_streak'] = df_sym.groupby(short_attack_group)['feat_gtja_short_attack'].cumsum()
        
        # ===== 5. 累计进攻强度（近3日）=====
        df_sym['feat_gtja_long_intensity_3d'] = df_sym['feat_gtja_long_intensity'].rolling(3).sum()
        df_sym['feat_gtja_short_intensity_3d'] = df_sym['feat_gtja_short_intensity'].rolling(3).sum()
        
        # ===== 6. 净持仓规模（过滤小仓位）=====
        # 净持仓占市场总持仓比例
        df_sym['feat_gtja_net_ratio'] = net_position / (oi + 1e-6)
        
        # ===== 7. 进攻 × 技术共振（高质量信号）=====
        # 多头进攻 + 均线多头排列
        df_sym['feat_gtja_long_with_ma'] = (
            is_long_attack & (df_sym['feat_ma_align_bull'] == 1)
        ).astype(int)
        
        # 空头进攻 + 均线空头排列
        df_sym['feat_gtja_short_with_ma'] = (
            is_short_attack & (df_sym['feat_ma_align_bear'] == 1)
        ).astype(int)
        
        # 多头进攻 + 价格突破高点
        df_sym['feat_gtja_long_with_break'] = (
            is_long_attack & (df_sym['feat_break_high_20'] == 1)
        ).astype(int)
        
        # 空头进攻 + 价格突破低点
        df_sym['feat_gtja_short_with_break'] = (
            is_short_attack & (df_sym['feat_break_low_20'] == 1)
        ).astype(int)
        
        feature_dfs.append(df_sym)
    
    # 合并所有品种
    df_feat = pd.concat(feature_dfs, ignore_index=True)
    
    # 获取特征列
    feature_cols = [col for col in df_feat.columns if col.startswith('feat_')]
    
    # 移除预热期
    df_feat = df_feat.groupby('symbol').apply(
        lambda x: x.iloc[warmup_period:] if len(x) > warmup_period else x.iloc[0:0]
    ).reset_index(drop=True)
    
    # 处理无穷值和极端值
    for col in feature_cols:
        df_feat[col] = df_feat[col].replace([np.inf, -np.inf], np.nan)
        df_feat[col] = df_feat[col].clip(-1e10, 1e10)
    
    # 删除包含NaN的行
    required_cols = feature_cols + ['label_long', 'label_short']
    initial_len = len(df_feat)
    df_feat = df_feat.dropna(subset=required_cols)
    
    print(f"[特征工程] 生成 {len(feature_cols)} 个特征")
    print(f"[特征工程] 技术特征: {len([c for c in feature_cols if not 'gtja' in c])} 个")
    print(f"[特征工程] 国泰持仓特征: {len([c for c in feature_cols if 'gtja' in c])} 个")
    print(f"[特征工程] 有效样本: {initial_len:,} → {len(df_feat):,}")
    
    return df_feat


def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """获取所有特征列名"""
    return [col for col in df.columns if col.startswith('feat_')]


# ==================================================
# 五、数据集划分
# ==================================================

def split_data(
    df: pd.DataFrame,
    config: StrategyConfig
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """按时间划分数据集"""
    df_train = df[(df['date'] >= config.train_start) & (df['date'] <= config.train_end)]
    df_valid = df[(df['date'] > config.train_end) & (df['date'] <= config.valid_end)]
    df_test = df[df['date'] > config.valid_end]
    
    print(f"\n[数据划分] 训练集: {len(df_train):,} ({df_train['date'].min().date()} ~ {df_train['date'].max().date()})")
    print(f"[数据划分] 验证集: {len(df_valid):,} ({df_valid['date'].min().date()} ~ {df_valid['date'].max().date()})")
    print(f"[数据划分] 测试集: {len(df_test):,} ({df_test['date'].min().date()} ~ {df_test['date'].max().date()})")
    
    return df_train, df_valid, df_test


# ==================================================
# 六、模型训练
# ==================================================

def train_model(
    df_train: pd.DataFrame,
    df_valid: pd.DataFrame,
    feature_cols: List[str],
    label_col: str = 'label_long',
    model_name: str = "模型"
) -> Tuple[Any, float]:
    """训练 LightGBM 模型"""
    print(f"\n[模型训练] 开始训练{model_name}...")
    
    X_train = df_train[feature_cols].values
    y_train = df_train[label_col].values
    X_valid = df_valid[feature_cols].values
    y_valid = df_valid[label_col].values
    
    # 类别权重
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos_weight = neg_count / max(pos_count, 1)
    
    print(f"[模型训练] 正样本: {pos_count:,} ({pos_count/(pos_count+neg_count)*100:.2f}%)")
    print(f"[模型训练] scale_pos_weight: {scale_pos_weight:.2f}")
    
    # 模型参数（沿用趋势ML的参数）
    params = {
        'num_leaves': 63,
        'max_depth': 8,
        'learning_rate': 0.03,
        'n_estimators': 1000,
        'subsample': 0.7,
        'colsample_bytree': 0.7,
        'reg_alpha': 0.1,
        'reg_lambda': 0.1,
        'scale_pos_weight': scale_pos_weight,
        'random_state': 42,
        'n_jobs': -1,
        'verbosity': -1
    }
    
    if HAS_LIGHTGBM:
        model = lgb.LGBMClassifier(**params)
        model.fit(
            X_train, y_train,
            eval_set=[(X_valid, y_valid)],
            callbacks=[lgb.early_stopping(100, verbose=False)]
        )
    else:
        model = GradientBoostingClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.1, random_state=42
        )
        model.fit(X_train, y_train)
    
    # 验证集预测
    y_pred_proba = model.predict_proba(X_valid)[:, 1]
    
    # AUC
    auc = roc_auc_score(y_valid, y_pred_proba) if y_valid.sum() > 0 else 0
    print(f"[模型训练] 验证集 AUC: {auc:.4f}")
    
    # 找最佳阈值
    best_threshold, best_f1 = 0.5, 0
    for thresh in np.arange(0.3, 0.9, 0.01):
        y_pred = (y_pred_proba >= thresh).astype(int)
        if y_pred.sum() == 0:
            continue
        precision = precision_score(y_valid, y_pred, zero_division=0)
        recall = recall_score(y_valid, y_pred, zero_division=0)
        if precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
            if f1 > best_f1:
                best_f1 = f1
                best_threshold = thresh
    
    # 最佳阈值评估
    y_pred = (y_pred_proba >= best_threshold).astype(int)
    precision = precision_score(y_valid, y_pred, zero_division=0)
    recall = recall_score(y_valid, y_pred, zero_division=0)
    
    print(f"[模型训练] 最佳阈值: {best_threshold:.4f}")
    print(f"[模型训练] Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {best_f1:.4f}")
    print(f"[模型训练] 预测正样本: {y_pred.sum():,}")
    
    return model, best_threshold


# ==================================================
# 七、回测系统
# ==================================================

@dataclass
class Trade:
    """交易记录"""
    symbol: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    holding_days: int
    return_pct: float
    direction: int
    exit_reason: str


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    entry_date: pd.Timestamp
    entry_price: float
    direction: int
    peak_price: float


def backtest(
    df_test: pd.DataFrame,
    p_long: pd.Series,
    p_short: pd.Series,
    config: StrategyConfig,
    long_threshold: float,
    short_threshold: float,
) -> Tuple[List[Trade], pd.DataFrame]:
    """回测系统"""
    print(f"\n[回测] 开始回测...")
    print(f"[回测] 多头阈值: {long_threshold:.4f}, 空头阈值: {short_threshold:.4f}")
    
    df = df_test.copy()
    df['p_long'] = p_long.values
    df['p_short'] = p_short.values
    
    all_dates = sorted(df['date'].unique())
    trades = []
    positions: Dict[str, Position] = {}
    daily_returns = []
    
    for date in all_dates:
        df_today = df[df['date'] == date]
        daily_pnl = 0.0
        
        # 1. 检查持仓
        symbols_to_close = []
        for symbol, pos in positions.items():
            sym_data = df_today[df_today['symbol'] == symbol]
            if len(sym_data) == 0:
                continue
            
            row = sym_data.iloc[0]
            current_price = row['close']
            high_price = row['high']
            low_price = row['low']
            holding_days = (date - pos.entry_date).days
            
            exit_reason = None
            exit_price = current_price
            
            if pos.direction == 1:  # 多头
                pos.peak_price = max(pos.peak_price, high_price)
                return_pct = (current_price - pos.entry_price) / pos.entry_price
                max_return_pct = (pos.peak_price - pos.entry_price) / pos.entry_price
                
                if return_pct >= config.take_profit_pct:
                    exit_reason = 'take_profit'
                    exit_price = pos.entry_price * (1 + config.take_profit_pct)
                elif return_pct <= -config.stop_loss_pct:
                    exit_reason = 'stop_loss'
                    exit_price = pos.entry_price * (1 - config.stop_loss_pct)
                elif max_return_pct > 0 and (max_return_pct - return_pct) >= config.trailing_stop_pct:
                    exit_reason = 'trailing_stop'
                elif holding_days >= config.max_holding_days:
                    exit_reason = 'max_days'
            else:  # 空头
                pos.peak_price = min(pos.peak_price, low_price)
                return_pct = (pos.entry_price - current_price) / pos.entry_price
                max_return_pct = (pos.entry_price - pos.peak_price) / pos.entry_price
                
                if return_pct >= config.take_profit_pct:
                    exit_reason = 'take_profit'
                    exit_price = pos.entry_price * (1 - config.take_profit_pct)
                elif return_pct <= -config.stop_loss_pct:
                    exit_reason = 'stop_loss'
                    exit_price = pos.entry_price * (1 + config.stop_loss_pct)
                elif max_return_pct > 0 and (max_return_pct - return_pct) >= config.trailing_stop_pct:
                    exit_reason = 'trailing_stop'
                elif holding_days >= config.max_holding_days:
                    exit_reason = 'max_days'
            
            if exit_reason:
                if pos.direction == 1:
                    final_return = (exit_price - pos.entry_price) / pos.entry_price
                else:
                    final_return = (pos.entry_price - exit_price) / pos.entry_price
                final_return -= config.fee_rate * 2
                
                trades.append(Trade(
                    symbol=symbol, entry_date=pos.entry_date, exit_date=date,
                    entry_price=pos.entry_price, exit_price=exit_price,
                    holding_days=holding_days, return_pct=final_return,
                    direction=pos.direction, exit_reason=exit_reason
                ))
                daily_pnl += final_return * config.position_size
                symbols_to_close.append(symbol)
        
        for symbol in symbols_to_close:
            del positions[symbol]
        
        # 2. 开新仓
        if len(positions) < config.max_positions:
            signals = []
            for _, row in df_today.iterrows():
                symbol = row['symbol']
                if symbol in positions:
                    continue
                
                # 激进模式：额外筛选条件
                if config.require_gtja_attack:
                    # 多头信号要求有国泰多头进攻
                    long_attack_ok = row.get('feat_gtja_long_attack', 0) == 1
                    # 空头信号要求有国泰空头进攻
                    short_attack_ok = row.get('feat_gtja_short_attack', 0) == 1
                    
                    # 检查连续进攻天数
                    if config.min_attack_streak > 0:
                        long_streak = row.get('feat_gtja_long_streak', 0)
                        short_streak = row.get('feat_gtja_short_streak', 0)
                        long_attack_ok = long_attack_ok and long_streak >= config.min_attack_streak
                        short_attack_ok = short_attack_ok and short_streak >= config.min_attack_streak
                else:
                    long_attack_ok = True
                    short_attack_ok = True
                
                # 获取波动率用于排序
                volatility = row.get('feat_atr_ratio', 0)
                
                if row['p_long'] >= long_threshold and long_attack_ok:
                    signals.append({
                        'symbol': symbol, 'direction': 1, 
                        'probability': row['p_long'], 'price': row['close'], 
                        'date': date, 'volatility': volatility,
                        'attack_streak': row.get('feat_gtja_long_streak', 0)
                    })
                if row['p_short'] >= short_threshold and short_attack_ok:
                    signals.append({
                        'symbol': symbol, 'direction': -1,
                        'probability': row['p_short'], 'price': row['close'], 
                        'date': date, 'volatility': volatility,
                        'attack_streak': row.get('feat_gtja_short_streak', 0)
                    })
            
            # 排序：激进模式优先高波动+高概率，稳健模式仅按概率
            if config.prefer_high_volatility:
                # 综合评分：概率权重0.6 + 波动率权重0.3 + 进攻持续性权重0.1
                signals = sorted(signals, key=lambda x: (
                    x['probability'] * 0.6 + 
                    min(x.get('volatility', 0) * 10, 0.3) +  # 波动率归一化
                    min(x.get('attack_streak', 0) * 0.05, 0.1)  # 连续进攻加分
                ), reverse=True)
            else:
                signals = sorted(signals, key=lambda x: x['probability'], reverse=True)
            
            for sig in signals:
                if len(positions) >= config.max_positions:
                    break
                if sig['symbol'] in positions:
                    continue
                positions[sig['symbol']] = Position(
                    symbol=sig['symbol'], entry_date=sig['date'],
                    entry_price=sig['price'], direction=sig['direction'],
                    peak_price=sig['price']
                )
                daily_pnl -= config.fee_rate * config.position_size
        
        daily_returns.append({'date': date, 'daily_return': daily_pnl, 'num_positions': len(positions)})
    
    equity = pd.DataFrame(daily_returns)
    equity['cum_return'] = (1 + equity['daily_return']).cumprod()
    
    print(f"[回测] 完成，共 {len(trades)} 笔交易")
    return trades, equity


def analyze_results(trades: List[Trade], equity: pd.DataFrame) -> Dict[str, Any]:
    """分析回测结果"""
    if not trades:
        return {}
    
    returns = [t.return_pct for t in trades]
    total_trades = len(trades)
    win_trades = sum(1 for r in returns if r > 0)
    win_rate = win_trades / total_trades
    
    avg_return = np.mean(returns)
    avg_win = np.mean([r for r in returns if r > 0]) if win_trades > 0 else 0
    avg_loss = np.mean([r for r in returns if r <= 0]) if (total_trades - win_trades) > 0 else 0
    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
    
    long_trades = [t for t in trades if t.direction == 1]
    short_trades = [t for t in trades if t.direction == -1]
    long_win_rate = sum(1 for t in long_trades if t.return_pct > 0) / len(long_trades) if long_trades else 0
    short_win_rate = sum(1 for t in short_trades if t.return_pct > 0) / len(short_trades) if short_trades else 0
    
    # 净值统计
    if len(equity) > 0:
        cum_equity = equity['cum_return'].values
        total_return = cum_equity[-1] - 1
        peak = np.maximum.accumulate(cum_equity)
        drawdown = (peak - cum_equity) / peak
        max_drawdown = drawdown.max()
        days = len(equity)
        annual_return = (1 + total_return) ** (250 / max(days, 1)) - 1 if total_return > -1 else -1
        daily_returns = equity['daily_return'].values
        sharpe = np.mean(daily_returns) / (np.std(daily_returns) + 1e-6) * np.sqrt(250)
    else:
        total_return = max_drawdown = annual_return = sharpe = 0
    
    # 单笔极值（小资金激进模式关注）
    max_single_win = max(returns) if returns else 0
    max_single_loss = min(returns) if returns else 0
    
    # 连胜/连亏统计
    win_streak, loss_streak, current_win, current_loss = 0, 0, 0, 0
    for r in returns:
        if r > 0:
            current_win += 1
            current_loss = 0
            win_streak = max(win_streak, current_win)
        else:
            current_loss += 1
            current_win = 0
            loss_streak = max(loss_streak, current_loss)
    
    return {
        '总交易': total_trades, '多头': len(long_trades), '空头': len(short_trades),
        '胜率': win_rate, '多头胜率': long_win_rate, '空头胜率': short_win_rate,
        '平均收益': avg_return, '平均盈利': avg_win, '平均亏损': avg_loss,
        '盈亏比': profit_factor, '累计收益': total_return, '年化收益': annual_return,
        '最大回撤': max_drawdown, '夏普比率': sharpe,
        '单笔最大盈利': max_single_win, '单笔最大亏损': max_single_loss,
        '最长连胜': win_streak, '最长连亏': loss_streak
    }


def print_results(results: Dict[str, Any]) -> None:
    """打印结果"""
    print("\n" + "=" * 60)
    print("📊 回测结果")
    print("=" * 60)
    
    # 分组显示
    groups = {
        '📈 交易统计': ['总交易', '多头', '空头'],
        '🎯 胜率分析': ['胜率', '多头胜率', '空头胜率'],
        '💰 收益分析': ['平均收益', '平均盈利', '平均亏损', '盈亏比'],
        '📊 整体表现': ['累计收益', '年化收益', '最大回撤', '夏普比率'],
        '⚡ 极值统计': ['单笔最大盈利', '单笔最大亏损', '最长连胜', '最长连亏']
    }
    
    for group_name, keys in groups.items():
        print(f"\n{group_name}")
        for key in keys:
            if key not in results:
                continue
            value = results[key]
            if isinstance(value, float):
                if '率' in key or '收益' in key or '回撤' in key or '盈利' in key or '亏损' in key:
                    print(f"  {key}: {value*100:.2f}%")
                else:
                    print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")


def plot_results(equity: pd.DataFrame, results: Dict, feature_cols: List[str], 
                 model, save_dir: Path) -> None:
    """绘制结果图表"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 净值曲线
    ax1 = axes[0, 0]
    ax1.plot(equity['date'], equity['cum_return'], 'b-', linewidth=1.5)
    ax1.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
    ax1.set_title(f'策略净值 | 累计收益: {results.get("累计收益", 0)*100:.2f}%')
    ax1.set_ylabel('净值')
    ax1.grid(True, alpha=0.3)
    
    # 回撤
    ax2 = axes[0, 1]
    cum_eq = equity['cum_return'].values
    peak = np.maximum.accumulate(cum_eq)
    dd = (peak - cum_eq) / peak
    ax2.fill_between(equity['date'], 0, -dd * 100, color='red', alpha=0.3)
    ax2.set_title(f'回撤 | 最大回撤: {results.get("最大回撤", 0)*100:.2f}%')
    ax2.set_ylabel('回撤 %')
    ax2.grid(True, alpha=0.3)
    
    # 指标
    ax3 = axes[1, 0]
    metrics = ['胜率', '多头胜率', '空头胜率', '夏普比率']
    values = [results.get(m, 0) for m in metrics]
    colors = ['green' if v > 0.5 else 'orange' for v in values]
    bars = ax3.bar(metrics, values, color=colors)
    ax3.set_title('关键指标')
    ax3.set_ylim(0, max(values) * 1.3 if max(values) > 0 else 1)
    for bar, val in zip(bars, values):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{val:.2f}', ha='center', fontsize=10)
    
    # 特征重要性
    ax4 = axes[1, 1]
    if hasattr(model, 'feature_importances_'):
        importance = model.feature_importances_
        indices = np.argsort(importance)[::-1][:15]
        ax4.barh(range(len(indices)), importance[indices][::-1], color='steelblue')
        ax4.set_yticks(range(len(indices)))
        ax4.set_yticklabels([feature_cols[i] for i in indices[::-1]], fontsize=8)
        ax4.set_title('Top 15 特征重要性')
    
    plt.tight_layout()
    plt.savefig(save_dir / 'backtest_result.png', dpi=150, bbox_inches='tight')
    print(f"\n[图表] 已保存至: {save_dir / 'backtest_result.png'}")
    plt.close()


# ==================================================
# 八、主程序
# ==================================================

def main(mode: str = 'aggressive'):
    """
    主程序入口
    
    Args:
        mode: 策略模式
            - 'aggressive': 小资金激进模式（5万以下，集中重仓）
            - 'conservative': 大资金稳健模式（50万以上，分散持仓）
    """
    print("=" * 60)
    print("🔥 融合模型：趋势ML特征 + 国泰君安持仓特征")
    print("=" * 60)
    
    # 根据模式选择配置
    if mode == 'aggressive':
        config = get_aggressive_config()
        print("\n💥 当前模式: 小资金激进版")
        print("   - Top 3% 极致精选信号")
        print("   - 单品种80%重仓出击")
        print("   - 要求国泰进攻共振")
        print("   - 目标收益 4%+，止盈 8%")
    else:
        config = get_conservative_config()
        print("\n🛡️ 当前模式: 大资金稳健版")
        print("   - Top 10% 信号筛选")
        print("   - 分散5仓位，每仓20%")
    
    print(f"\n📊 策略参数:")
    print(f"  信号阈值: Top {100-config.signal_percentile:.0f}%")
    print(f"  最大持仓: {config.max_positions} 个")
    print(f"  单笔仓位: {config.position_size*100:.0f}%")
    print(f"  止损/止盈: {config.stop_loss_pct*100:.1f}% / {config.take_profit_pct*100:.1f}%")
    print(f"  要求国泰进攻: {'是' if config.require_gtja_attack else '否'}")
    
    print(f"\n数据库路径:")
    print(f"  期货: {FUTURES_DB}")
    print(f"  持仓: {INSTITUTION_DB}")
    print(f"模型保存: {MODEL_DIR}")
    
    # 1. 加载数据
    df_all = load_all_data(min_days=200)
    
    # 2. 生成标签
    df_labeled = assign_labels(df_all, config)
    
    # 3. 特征工程
    df_feat = make_features_fusion(df_labeled, warmup_period=config.warmup_period)
    
    # 4. 数据划分
    df_train, df_valid, df_test = split_data(df_feat, config)
    
    # 5. 训练模型
    feature_cols = get_feature_columns(df_feat)
    
    print(f"\n[特征统计]")
    tech_feats = [c for c in feature_cols if 'gtja' not in c]
    gtja_feats = [c for c in feature_cols if 'gtja' in c]
    print(f"  技术特征: {len(tech_feats)} 个")
    print(f"  国泰特征: {len(gtja_feats)} 个")
    print(f"  总计: {len(feature_cols)} 个")
    
    # 多头模型
    long_model, long_threshold = train_model(
        df_train, df_valid, feature_cols, 'label_long', '多头模型'
    )
    joblib.dump(long_model, MODEL_DIR / 'long_model.pkl')
    
    # 空头模型
    short_model, short_threshold = train_model(
        df_train, df_valid, feature_cols, 'label_short', '空头模型'
    )
    joblib.dump(short_model, MODEL_DIR / 'short_model.pkl')
    
    # 保存配置
    model_config = {
        'features': feature_cols,
        'long_threshold': long_threshold,
        'short_threshold': short_threshold,
        'train_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'signal_percentile': config.signal_percentile,
        'config': {
            'future_days': config.future_days,
            'long_threshold': config.long_threshold,
            'short_threshold': config.short_threshold,
            'max_positions': config.max_positions,
            'stop_loss_pct': config.stop_loss_pct,
            'take_profit_pct': config.take_profit_pct,
            'require_gtja_attack': config.require_gtja_attack
        }
    }
    with open(MODEL_DIR / 'config.json', 'w', encoding='utf-8') as f:
        json.dump(model_config, f, ensure_ascii=False, indent=2)
    
    # 6. 测试集回测
    print("\n" + "=" * 60)
    print("📈 测试集回测")
    print("=" * 60)
    
    # 预测
    X_test = df_test[feature_cols].values
    p_long = pd.Series(long_model.predict_proba(X_test)[:, 1], index=df_test.index)
    p_short = pd.Series(short_model.predict_proba(X_test)[:, 1], index=df_test.index)
    
    # AUC
    auc_long = roc_auc_score(df_test['label_long'], p_long)
    auc_short = roc_auc_score(df_test['label_short'], p_short)
    print(f"\n[测试集] 多头AUC: {auc_long:.4f}, 空头AUC: {auc_short:.4f}")
    
    # 使用百分位阈值
    percentile = config.signal_percentile
    test_long_thresh = np.percentile(p_long, percentile)
    test_short_thresh = np.percentile(p_short, percentile)
    print(f"[测试集] Top {100-percentile:.0f}% 阈值 - 多头: {test_long_thresh:.4f}, 空头: {test_short_thresh:.4f}")
    
    # 回测
    trades, equity = backtest(
        df_test, p_long, p_short, config,
        long_threshold=test_long_thresh,
        short_threshold=test_short_thresh
    )
    
    # 分析结果
    results = analyze_results(trades, equity)
    print_results(results)
    
    # 绘图
    if len(equity) > 0:
        plot_results(equity, results, feature_cols, long_model, OUTPUT_DIR)
    
    # 特征重要性
    if hasattr(long_model, 'feature_importances_'):
        print("\n" + "=" * 60)
        print("🔑 Top 15 重要特征")
        print("=" * 60)
        importance = (long_model.feature_importances_ + short_model.feature_importances_) / 2
        indices = np.argsort(importance)[::-1][:15]
        for i, idx in enumerate(indices):
            feat = feature_cols[idx]
            tag = "📊 国泰" if 'gtja' in feat else "📈 技术"
            print(f"  {i+1:2d}. {tag} {feat}: {importance[idx]:.1f}")
    
    print(f"\n✅ 训练完成! 模型已保存至 {MODEL_DIR}")
    
    return {
        'config': config,
        'long_model': long_model,
        'short_model': short_model,
        'trades': trades,
        'equity': equity,
        'results': results
    }


if __name__ == "__main__":
    import sys
    # 命令行参数：python train_fusion.py [aggressive|conservative]
    # 默认使用激进模式（小资金）
    mode = sys.argv[1] if len(sys.argv) > 1 else 'aggressive'
    if mode not in ['aggressive', 'conservative']:
        print(f"未知模式: {mode}，使用默认激进模式")
        mode = 'aggressive'
    main(mode=mode)

