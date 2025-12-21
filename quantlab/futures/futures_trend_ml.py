#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货单边行情识别与机器学习策略 V2.0

改进点：
1. 标签重定义：预测"未来N天最大收益是否超过阈值"
2. 增强特征：波动率收缩、突破信号、多周期特征、资金流向
3. 优化阈值：使用更严格的 top 5% 阈值
4. 改进风控：添加止盈、移动止损
5. 双向交易：同时使用多空信号

作者：量化工程师
日期：2024
"""

import sqlite3
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    precision_score,
    recall_score,
    roc_auc_score,
)

# 尝试导入 LightGBM
try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except (ImportError, OSError) as e:
    HAS_LIGHTGBM = False
    warnings.warn(f"LightGBM 加载失败 ({e})，将使用 sklearn 的 GradientBoostingClassifier 替代")
    from sklearn.ensemble import GradientBoostingClassifier

# 忽略警告
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
    
    # 数据划分
    train_end: str = '2022-12-31'
    valid_end: str = '2023-12-31'
    
    # 交易参数
    signal_percentile: float = 95  # 信号阈值百分位（top 5%）
    max_holding_days: int = 10     # 最大持仓天数
    stop_loss_pct: float = 0.02    # 固定止损比例 2%
    take_profit_pct: float = 0.05  # 固定止盈比例 5%
    trailing_stop_pct: float = 0.015  # 移动止损比例 1.5%
    fee_rate: float = 0.0003       # 手续费率
    
    # 仓位管理
    max_positions: int = 5         # 最大同时持仓数量
    position_size: float = 0.2     # 单笔仓位占比


# ==================================================
# 二、数据读取与整合
# ==================================================

def get_active_contracts(conn: sqlite3.Connection) -> List[str]:
    """从 contracts_main 中获取所有活跃合约代码"""
    query = "SELECT symbol FROM contracts_main WHERE is_active = 1"
    cursor = conn.execute(query)
    symbols = [row[0] for row in cursor.fetchall()]
    return symbols


def load_history_from_db(db_path: str, min_days: int = 250) -> pd.DataFrame:
    """
    从 SQLite 数据库加载所有活跃合约的历史数据
    
    参数:
        db_path: 数据库文件路径
        min_days: 最少交易日数，低于此数量的品种将被剔除
        
    返回:
        包含所有活跃合约历史数据的 DataFrame
    """
    conn = sqlite3.connect(db_path)
    
    # 获取活跃合约列表
    symbols = get_active_contracts(conn)
    print(f"[数据加载] 发现 {len(symbols)} 个活跃合约")
    
    all_dfs = []
    skipped_symbols = []
    
    for symbol in symbols:
        table_name = f"hist_{symbol.lower()}"
        
        try:
            # 检查表是否存在
            check_query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            if not conn.execute(check_query).fetchone():
                skipped_symbols.append((symbol, "表不存在"))
                continue
            
            # 读取数据
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql_query(query, conn)
            
            # 检查数据量
            if len(df) < min_days:
                skipped_symbols.append((symbol, f"数据不足({len(df)}条)"))
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
            
            # 只保留需要的列
            df = df[['date', 'open', 'high', 'low', 'close', 'volume', 'open_interest']]
            df['symbol'] = symbol
            
            all_dfs.append(df)
            
        except Exception as e:
            skipped_symbols.append((symbol, str(e)))
            continue
    
    conn.close()
    
    if not all_dfs:
        raise ValueError("没有找到有效的历史数据")
    
    # 合并所有数据
    df_all = pd.concat(all_dfs, ignore_index=True)
    
    # 转换日期类型
    df_all['date'] = pd.to_datetime(df_all['date'])
    
    # 按 symbol 和 date 排序
    df_all = df_all.sort_values(['symbol', 'date']).reset_index(drop=True)
    
    # 打印统计信息
    print(f"[数据加载] 成功加载 {len(all_dfs)} 个品种")
    print(f"[数据加载] 跳过 {len(skipped_symbols)} 个品种: {skipped_symbols[:5]}...")
    print(f"[数据加载] 数据日期范围: {df_all['date'].min().date()} ~ {df_all['date'].max().date()}")
    print(f"[数据加载] 总样本数: {len(df_all):,}")
    
    return df_all


# ==================================================
# 三、标签生成（改进版）
# ==================================================

def calculate_future_returns(df_symbol: pd.DataFrame, future_days: int = 5) -> pd.DataFrame:
    """
    计算未来N天的收益指标
    
    参数:
        df_symbol: 单个品种的 DataFrame
        future_days: 预测未来天数
        
    返回:
        添加了未来收益指标的 DataFrame
    """
    df = df_symbol.copy()
    
    # 未来N天最高价（用于计算最大潜在收益）
    df['future_high'] = df['high'].shift(-1).rolling(window=future_days).max().shift(-future_days + 1)
    
    # 未来N天最低价（用于计算最大潜在亏损）
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


def assign_labels_v2(
    df_all: pd.DataFrame, 
    config: StrategyConfig,
    verbose: bool = True
) -> pd.DataFrame:
    """
    生成标签（改进版）
    
    标签定义：
    - label_long = 1：未来N天最大上涨幅度 >= long_threshold
    - label_short = 1：未来N天最大下跌幅度 >= short_threshold
    
    参数:
        df_all: 包含所有品种数据的 DataFrame
        config: 策略配置
        verbose: 是否打印详细信息
        
    返回:
        添加了标签列的 DataFrame
    """
    if verbose:
        print(f"\n[标签生成] 预测未来 {config.future_days} 天")
        print(f"[标签生成] 多头阈值: {config.long_threshold*100:.1f}%, 空头阈值: {config.short_threshold*100:.1f}%")
    
    df = df_all.copy()
    
    # 按品种分组计算未来收益
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
    
    # 为了兼容性，保留原始 label 列（多头为主）
    df['label'] = df['label_long']
    
    if verbose:
        # 移除 NaN 后统计
        valid_mask = df['label_long'].notna() & df['label_short'].notna()
        total_valid = valid_mask.sum()
        
        long_count = df.loc[valid_mask, 'label_long'].sum()
        short_count = df.loc[valid_mask, 'label_short'].sum()
        
        print(f"[标签生成] 有效样本数: {total_valid:,}")
        print(f"[标签生成] 多头信号 (label_long=1): {int(long_count):,} ({long_count/total_valid*100:.2f}%)")
        print(f"[标签生成] 空头信号 (label_short=1): {int(short_count):,} ({short_count/total_valid*100:.2f}%)")
    
    return df


# ==================================================
# 四、特征工程（增强版）
# ==================================================

def calculate_atr(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """计算 ATR (Average True Range)"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr = tr.rolling(window=period, min_periods=1).mean()
    return atr


def compute_trend_features(close: pd.Series, window: int = 10) -> Tuple[pd.Series, pd.Series]:
    """计算趋势斜率和 R²"""
    slopes = []
    r2s = []
    
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
            
            y_mean = y.mean()
            y_std = y.std()
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


def make_features_v2(df: pd.DataFrame, warmup_period: int = 60, for_prediction: bool = False) -> pd.DataFrame:
    """
    生成机器学习特征（增强版）
    
    新增特征：
    - 波动率收缩指标
    - 多周期突破信号
    - 资金流向指标
    - 价格形态特征
    
    参数：
        df: 输入数据
        warmup_period: 预热期天数
        for_prediction: 是否用于预测（True时不检查标签列）
    """
    print(f"\n[特征工程] 开始生成特征，预热期: {warmup_period} 天")
    
    df = df.copy()
    
    # 按品种分组计算特征
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
        
        # ===== 1. 价格动量（多周期）=====
        for period in [3, 5, 10, 20]:
            df_sym[f'feat_ret_{period}'] = close.pct_change(period)
        
        # 动量加速度（二阶导数）
        df_sym['feat_momentum_accel'] = df_sym['feat_ret_5'] - df_sym['feat_ret_5'].shift(5)
        
        # ===== 2. 突破信号（多周期）=====
        for period in [10, 20, 40]:
            rolling_high = high.rolling(period, min_periods=1).max()
            rolling_low = low.rolling(period, min_periods=1).min()
            range_hl = rolling_high - rolling_low
            
            # 价格在区间中的位置
            df_sym[f'feat_price_pos_{period}'] = (close - rolling_low) / (range_hl + 1e-6)
            
            # 突破信号（二值）
            df_sym[f'feat_break_high_{period}'] = (close >= rolling_high.shift(1)).astype(int)
            df_sym[f'feat_break_low_{period}'] = (close <= rolling_low.shift(1)).astype(int)
            
            # 距离高低点的相对距离
            df_sym[f'feat_dist_high_{period}'] = (rolling_high - close) / (close + 1e-6)
            df_sym[f'feat_dist_low_{period}'] = (close - rolling_low) / (close + 1e-6)
        
        # ===== 3. 均线系统 =====
        ma_periods = [5, 10, 20, 40, 60]
        for period in ma_periods:
            df_sym[f'MA_{period}'] = close.rolling(period, min_periods=1).mean()
        
        # 均线多头/空头排列
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
        
        # 价格偏离均线程度
        df_sym['feat_price_ma20_dev'] = (close - df_sym['MA_20']) / (df_sym['MA_20'] + 1e-6)
        df_sym['feat_price_ma60_dev'] = (close - df_sym['MA_60']) / (df_sym['MA_60'] + 1e-6)
        
        # ===== 4. 波动率特征 =====
        returns = close.pct_change()
        
        for period in [5, 10, 20]:
            df_sym[f'feat_vol_{period}'] = returns.rolling(period, min_periods=1).std()
        
        # 波动率收缩（短期波动率 / 长期波动率）- 收缩后可能突破
        df_sym['feat_vol_contraction'] = df_sym['feat_vol_5'] / (df_sym['feat_vol_20'] + 1e-6)
        
        # ATR 及其变化
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
        
        # 趋势得分（斜率 * R²）
        df_sym['feat_trend_score_10'] = slope_10 * r2_10
        df_sym['feat_trend_score_20'] = slope_20 * r2_20
        
        # ===== 6. 成交量特征 =====
        vol_ma_5 = volume.rolling(5, min_periods=1).mean()
        vol_ma_20 = volume.rolling(20, min_periods=1).mean()
        
        df_sym['feat_vol_ratio_5'] = volume / (vol_ma_5 + 1e-6)
        df_sym['feat_vol_ratio_20'] = volume / (vol_ma_20 + 1e-6)
        df_sym['feat_vol_trend'] = vol_ma_5 / (vol_ma_20 + 1e-6)
        
        # 放量突破信号
        df_sym['feat_vol_breakout'] = (
            (volume > vol_ma_20 * 1.5) & 
            (abs(returns) > df_sym['feat_vol_20'])
        ).astype(int)
        
        # ===== 7. 持仓量特征 =====
        oi_ma_20 = oi.rolling(20, min_periods=1).mean()
        
        df_sym['feat_oi_ratio'] = oi / (oi_ma_20 + 1e-6)
        df_sym['feat_oi_chg_5'] = oi.pct_change(5)
        
        # 持仓量变化方向与价格变化方向
        price_up = (close > close.shift(1)).astype(int)
        oi_up = (oi > oi.shift(1)).astype(int)
        
        # 价涨仓增（资金流入做多）
        df_sym['feat_price_oi_bull'] = (price_up & oi_up).astype(int)
        # 价跌仓增（资金流入做空）
        df_sym['feat_price_oi_bear'] = ((1 - price_up) & oi_up).astype(int)
        
        # ===== 8. K线形态 =====
        bar_range = high - low
        body = abs(close - open_price)
        
        # 实体占比
        df_sym['feat_body_ratio'] = body / (bar_range + 1e-6)
        
        # 收盘位置
        df_sym['feat_close_pos'] = (close - low) / (bar_range + 1e-6)
        
        # 连续阳/阴线
        df_sym['feat_consec_up'] = (close > open_price).rolling(3).sum()
        df_sym['feat_consec_down'] = (close < open_price).rolling(3).sum()
        
        # ===== 9. 相对强弱 =====
        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        avg_gain = gain.rolling(14, min_periods=1).mean()
        avg_loss = loss.rolling(14, min_periods=1).mean()
        
        rs = avg_gain / (avg_loss + 1e-6)
        df_sym['feat_rsi_14'] = 100 - (100 / (1 + rs))
        
        # ===== 10. 波动率突破（Bollinger 突破）=====
        ma_20 = df_sym['MA_20']
        std_20 = close.rolling(20, min_periods=1).std()
        
        upper_band = ma_20 + 2 * std_20
        lower_band = ma_20 - 2 * std_20
        
        df_sym['feat_bb_pos'] = (close - lower_band) / (upper_band - lower_band + 1e-6)
        df_sym['feat_bb_break_up'] = (close > upper_band).astype(int)
        df_sym['feat_bb_break_down'] = (close < lower_band).astype(int)
        
        feature_dfs.append(df_sym)
    
    # 合并所有品种
    df_feat = pd.concat(feature_dfs, ignore_index=True)
    
    # 获取所有特征列
    feature_cols = [col for col in df_feat.columns if col.startswith('feat_')]
    
    # 移除预热期的数据
    df_feat = df_feat.groupby('symbol').apply(
        lambda x: x.iloc[warmup_period:] if len(x) > warmup_period else x.iloc[0:0]
    ).reset_index(drop=True)
    
    # 处理无穷大值和极端值
    inf_count = 0
    for col in feature_cols:
        # 统计无穷值数量
        inf_mask = np.isinf(df_feat[col])
        inf_count += inf_mask.sum()
        # 将无穷大替换为 NaN
        df_feat[col] = df_feat[col].replace([np.inf, -np.inf], np.nan)
        # 限制极端值范围（防止 float32 溢出）
        df_feat[col] = df_feat[col].clip(-1e10, 1e10)
    
    if inf_count > 0:
        print(f"[特征工程] 处理了 {inf_count:,} 个无穷值")
    
    # 删除包含 NaN 的行（预测模式只检查特征，训练模式还要检查标签）
    if for_prediction:
        required_cols = feature_cols
    else:
        required_cols = feature_cols + ['label_long', 'label_short']
    initial_len = len(df_feat)
    df_feat = df_feat.dropna(subset=required_cols)
    
    print(f"[特征工程] 生成 {len(feature_cols)} 个特征")
    print(f"[特征工程] 移除无效数据后样本数: {initial_len:,} → {len(df_feat):,}")
    
    return df_feat


# ==================================================
# 五、数据集划分
# ==================================================

def split_data_by_year(
    df: pd.DataFrame,
    train_end: str = '2022-12-31',
    valid_end: str = '2023-12-31'
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """按固定年份划分数据集"""
    df_train = df[df['date'] <= train_end]
    df_valid = df[(df['date'] > train_end) & (df['date'] <= valid_end)]
    df_test = df[df['date'] > valid_end]
    
    print(f"\n[数据划分] 训练集: {len(df_train):,} 样本 ({df_train['date'].min().date()} ~ {df_train['date'].max().date()})")
    print(f"[数据划分] 验证集: {len(df_valid):,} 样本 ({df_valid['date'].min().date()} ~ {df_valid['date'].max().date()})")
    print(f"[数据划分] 测试集: {len(df_test):,} 样本 ({df_test['date'].min().date()} ~ {df_test['date'].max().date()})")
    
    return df_train, df_valid, df_test


def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """获取所有特征列名"""
    return [col for col in df.columns if col.startswith('feat_')]


# ==================================================
# 六、模型训练（改进版）
# ==================================================

def train_model(
    df_train: pd.DataFrame,
    df_valid: pd.DataFrame,
    feature_cols: List[str],
    label_col: str = 'label_long',
    model_name: str = "模型",
    params: Optional[Dict[str, Any]] = None
) -> Tuple[Any, float]:
    """
    训练 LightGBM 模型（通用函数）
    
    参数:
        df_train: 训练集
        df_valid: 验证集
        feature_cols: 特征列名列表
        label_col: 标签列名
        model_name: 模型名称（用于打印）
        params: 模型参数（可选）
        
    返回:
        (训练好的模型, 最佳阈值)
    """
    print(f"\n[模型训练] 开始训练{model_name}...")
    
    # 准备数据
    X_train = df_train[feature_cols].values
    y_train = df_train[label_col].values
    
    X_valid = df_valid[feature_cols].values
    y_valid = df_valid[label_col].values
    
    # 计算类别权重
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos_weight = neg_count / max(pos_count, 1)
    
    print(f"[模型训练] 训练集正样本: {pos_count:,}, 负样本: {neg_count:,}")
    print(f"[模型训练] 正样本占比: {pos_count/(pos_count+neg_count)*100:.2f}%")
    print(f"[模型训练] scale_pos_weight: {scale_pos_weight:.2f}")
    
    # 模型参数
    default_params = {
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
    
    if params:
        default_params.update(params)
    
    if HAS_LIGHTGBM:
        model = lgb.LGBMClassifier(**default_params)
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_valid, y_valid)],
            callbacks=[lgb.early_stopping(100, verbose=False)]
        )
    else:
        sklearn_params = {
            'n_estimators': 300,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'random_state': 42
        }
        model = GradientBoostingClassifier(**sklearn_params)
        model.fit(X_train, y_train)
    
    # 验证集预测
    y_pred_proba = model.predict_proba(X_valid)[:, 1]
    
    # 打印概率分布
    print(f"\n[模型训练] 验证集概率分布:")
    percentiles = [0, 25, 50, 75, 90, 95, 99, 100]
    for p in percentiles:
        val = np.percentile(y_pred_proba, p) if p < 100 else y_pred_proba.max()
        print(f"  - {p}%:  {val:.4f}")
    
    # 计算 AUC
    auc = roc_auc_score(y_valid, y_pred_proba) if y_valid.sum() > 0 else 0
    print(f"\n[模型训练] 验证集 AUC: {auc:.4f}")
    
    # 找最佳阈值（最大化 F1）
    best_threshold = 0.5
    best_f1 = 0
    
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
    
    # 使用最佳阈值评估
    y_pred = (y_pred_proba >= best_threshold).astype(int)
    acc = accuracy_score(y_valid, y_pred)
    precision = precision_score(y_valid, y_pred, zero_division=0)
    recall = recall_score(y_valid, y_pred, zero_division=0)
    
    print(f"\n[模型训练] 最佳阈值: {best_threshold:.4f}")
    print(f"[模型训练] 验证集评估:")
    print(f"  - Accuracy:  {acc:.4f}")
    print(f"  - Precision: {precision:.4f}")
    print(f"  - Recall:    {recall:.4f}")
    print(f"  - F1:        {best_f1:.4f}")
    print(f"  - 预测正样本数: {y_pred.sum():,}")
    
    return model, best_threshold


def predict_proba(
    df: pd.DataFrame,
    model: Any,
    feature_cols: List[str]
) -> pd.Series:
    """使用模型预测概率"""
    X = df[feature_cols].values
    proba = model.predict_proba(X)[:, 1]
    return pd.Series(proba, index=df.index)


def save_model(model: Any, filepath: str) -> None:
    """保存模型到文件"""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, filepath)
    print(f"[模型保存] 模型已保存至: {filepath}")


def load_model(filepath: str) -> Any:
    """从文件加载模型"""
    return joblib.load(filepath)


# ==================================================
# 七、回测系统（改进版）
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
    direction: int  # 1: 多头, -1: 空头
    exit_reason: str  # 'take_profit', 'stop_loss', 'trailing_stop', 'max_days', 'signal_exit'


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    entry_idx: int
    entry_date: pd.Timestamp
    entry_price: float
    direction: int
    peak_price: float  # 最高价（多头）或最低价（空头）


def backtest_v2(
    df_test: pd.DataFrame,
    p_long: pd.Series,
    p_short: pd.Series,
    config: StrategyConfig,
    long_threshold: float,
    short_threshold: float,
) -> Tuple[List[Trade], pd.DataFrame]:
    """
    改进版回测系统
    
    特点：
    - 支持多空双向交易
    - 固定止盈止损 + 移动止损
    - 仓位管理
    - 信号优先级排序
    """
    print(f"\n[回测] 开始回测...")
    print(f"[回测] 多头阈值: {long_threshold:.4f}, 空头阈值: {short_threshold:.4f}")
    print(f"[回测] 止盈: {config.take_profit_pct*100:.1f}%, 止损: {config.stop_loss_pct*100:.1f}%, 移动止损: {config.trailing_stop_pct*100:.1f}%")
    
    df = df_test.copy()
    df['p_long'] = p_long.values
    df['p_short'] = p_short.values
    
    # 按日期排序
    all_dates = sorted(df['date'].unique())
    
    trades = []
    positions: Dict[str, Position] = {}  # symbol -> Position
    
    # 每日净值记录
    daily_returns = []
    
    for date in all_dates:
        df_today = df[df['date'] == date]
        daily_pnl = 0.0
        
        # 1. 检查现有持仓是否需要平仓
        symbols_to_close = []
        
        for symbol, pos in positions.items():
            # 获取该品种今日数据
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
                # 更新峰值
                pos.peak_price = max(pos.peak_price, high_price)
                
                # 收益率
                return_pct = (current_price - pos.entry_price) / pos.entry_price
                max_return_pct = (pos.peak_price - pos.entry_price) / pos.entry_price
                
                # 检查止盈
                if return_pct >= config.take_profit_pct:
                    exit_reason = 'take_profit'
                    exit_price = pos.entry_price * (1 + config.take_profit_pct)
                
                # 检查止损
                elif return_pct <= -config.stop_loss_pct:
                    exit_reason = 'stop_loss'
                    exit_price = pos.entry_price * (1 - config.stop_loss_pct)
                
                # 检查移动止损（从最高点回撤超过阈值）
                elif max_return_pct > 0 and (max_return_pct - return_pct) >= config.trailing_stop_pct:
                    exit_reason = 'trailing_stop'
                
                # 检查最大持仓天数
                elif holding_days >= config.max_holding_days:
                    exit_reason = 'max_days'
                    
            else:  # 空头
                # 更新谷值
                pos.peak_price = min(pos.peak_price, low_price)
                
                # 收益率（空头）
                return_pct = (pos.entry_price - current_price) / pos.entry_price
                max_return_pct = (pos.entry_price - pos.peak_price) / pos.entry_price
                
                # 检查止盈
                if return_pct >= config.take_profit_pct:
                    exit_reason = 'take_profit'
                    exit_price = pos.entry_price * (1 - config.take_profit_pct)
                
                # 检查止损
                elif return_pct <= -config.stop_loss_pct:
                    exit_reason = 'stop_loss'
                    exit_price = pos.entry_price * (1 + config.stop_loss_pct)
                
                # 检查移动止损
                elif max_return_pct > 0 and (max_return_pct - return_pct) >= config.trailing_stop_pct:
                    exit_reason = 'trailing_stop'
                
                # 检查最大持仓天数
                elif holding_days >= config.max_holding_days:
                    exit_reason = 'max_days'
            
            if exit_reason:
                # 计算最终收益
                if pos.direction == 1:
                    final_return = (exit_price - pos.entry_price) / pos.entry_price
                else:
                    final_return = (pos.entry_price - exit_price) / pos.entry_price
                
                final_return -= config.fee_rate * 2
                
                trades.append(Trade(
                    symbol=symbol,
                    entry_date=pos.entry_date,
                    exit_date=date,
                    entry_price=pos.entry_price,
                    exit_price=exit_price,
                    holding_days=holding_days,
                    return_pct=final_return,
                    direction=pos.direction,
                    exit_reason=exit_reason
                ))
                
                daily_pnl += final_return * config.position_size
                symbols_to_close.append(symbol)
        
        # 移除已平仓的持仓
        for symbol in symbols_to_close:
            del positions[symbol]
        
        # 2. 检查新开仓信号
        if len(positions) < config.max_positions:
            # 获取今日所有品种的信号
            signals = []
            
            for _, row in df_today.iterrows():
                symbol = row['symbol']
                
                # 跳过已持仓的品种
                if symbol in positions:
                    continue
                
                # 多头信号
                if row['p_long'] >= long_threshold:
                    signals.append({
                        'symbol': symbol,
                        'direction': 1,
                        'probability': row['p_long'],
                        'price': row['close'],
                        'date': date
                    })
                
                # 空头信号
                if row['p_short'] >= short_threshold:
                    signals.append({
                        'symbol': symbol,
                        'direction': -1,
                        'probability': row['p_short'],
                        'price': row['close'],
                        'date': date
                    })
            
            # 按概率排序，优先开仓概率高的
            signals = sorted(signals, key=lambda x: x['probability'], reverse=True)
            
            # 开仓
            for sig in signals:
                if len(positions) >= config.max_positions:
                    break
                
                # 同一品种不能同时多空
                if sig['symbol'] in positions:
                    continue
                
                positions[sig['symbol']] = Position(
                    symbol=sig['symbol'],
                    entry_idx=0,
                    entry_date=sig['date'],
                    entry_price=sig['price'],
                    direction=sig['direction'],
                    peak_price=sig['price']
                )
                
                # 扣除开仓手续费
                daily_pnl -= config.fee_rate * config.position_size
        
        # 记录每日收益
        daily_returns.append({
            'date': date,
            'daily_return': daily_pnl,
            'num_positions': len(positions)
        })
    
    # 计算净值曲线
    equity = pd.DataFrame(daily_returns)
    equity['cum_return'] = (1 + equity['daily_return']).cumprod()
    
    print(f"[回测] 完成，共 {len(trades)} 笔交易")
    
    return trades, equity


def analyze_backtest_results(trades: List[Trade], equity: pd.DataFrame) -> Dict[str, Any]:
    """分析回测结果"""
    if not trades:
        return {}
    
    returns = [t.return_pct for t in trades]
    
    # 基本统计
    total_trades = len(trades)
    win_trades = sum(1 for r in returns if r > 0)
    win_rate = win_trades / total_trades if total_trades > 0 else 0
    
    avg_return = np.mean(returns)
    avg_win = np.mean([r for r in returns if r > 0]) if win_trades > 0 else 0
    avg_loss = np.mean([r for r in returns if r <= 0]) if (total_trades - win_trades) > 0 else 0
    
    # 盈亏比
    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
    
    avg_holding_days = np.mean([t.holding_days for t in trades])
    
    # 按方向统计
    long_trades = [t for t in trades if t.direction == 1]
    short_trades = [t for t in trades if t.direction == -1]
    
    long_win_rate = sum(1 for t in long_trades if t.return_pct > 0) / len(long_trades) if long_trades else 0
    short_win_rate = sum(1 for t in short_trades if t.return_pct > 0) / len(short_trades) if short_trades else 0
    
    # 按退出原因统计
    exit_reasons = {}
    for t in trades:
        if t.exit_reason not in exit_reasons:
            exit_reasons[t.exit_reason] = {'count': 0, 'total_return': 0}
        exit_reasons[t.exit_reason]['count'] += 1
        exit_reasons[t.exit_reason]['total_return'] += t.return_pct
    
    # 净值曲线统计
    if len(equity) > 0 and 'cum_return' in equity.columns:
        cum_equity = equity['cum_return'].values
        total_return = cum_equity[-1] - 1
    
    # 最大回撤
        peak = np.maximum.accumulate(cum_equity)
        drawdown = (peak - cum_equity) / peak
        max_drawdown = drawdown.max()
    
        # 年化收益
        days = len(equity)
        annual_return = (1 + total_return) ** (250 / max(days, 1)) - 1 if total_return > -1 else -1
        
        # 夏普比率（假设无风险利率为 0）
        daily_returns = equity['daily_return'].values
        sharpe_ratio = np.mean(daily_returns) / (np.std(daily_returns) + 1e-6) * np.sqrt(250)
    else:
        total_return = 0
        max_drawdown = 0
        annual_return = 0
        sharpe_ratio = 0
    
    results = {
        '总交易次数': total_trades,
        '多头交易': len(long_trades),
        '空头交易': len(short_trades),
        '盈利次数': win_trades,
        '胜率': win_rate,
        '多头胜率': long_win_rate,
        '空头胜率': short_win_rate,
        '平均单笔收益': avg_return,
        '平均盈利': avg_win,
        '平均亏损': avg_loss,
        '盈亏比': profit_factor,
        '累计收益': total_return,
        '年化收益': annual_return,
        '最大回撤': max_drawdown,
        '夏普比率': sharpe_ratio,
        '平均持仓天数': avg_holding_days,
        '退出原因分布': exit_reasons
    }
    
    return results


def print_backtest_results(results: Dict[str, Any]) -> None:
    """打印回测结果"""
    print("\n" + "=" * 60)
    print("回测结果汇总")
    print("=" * 60)
    
    for key, value in results.items():
        if key == '退出原因分布':
            print(f"\n{key}:")
            for reason, stats in value.items():
                avg_ret = stats['total_return'] / stats['count'] if stats['count'] > 0 else 0
                print(f"  - {reason}: {stats['count']} 笔, 平均收益 {avg_ret*100:.2f}%")
        elif isinstance(value, float):
            if '率' in key or '收益' in key or '回撤' in key:
                print(f"{key}: {value * 100:.2f}%")
            elif '比' in key:
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")


def plot_equity_curve(equity: pd.DataFrame, save_path: Optional[str] = None) -> None:
    """绘制净值曲线"""
    if len(equity) == 0:
        return
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), height_ratios=[3, 1])
    
    # 净值曲线
    ax1 = axes[0]
    ax1.plot(equity['date'], equity['cum_return'], 'b-', linewidth=1.5, label='策略净值')
    ax1.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
    ax1.set_title('策略净值曲线', fontsize=14)
    ax1.set_ylabel('净值', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 回撤曲线
    ax2 = axes[1]
    cum_equity = equity['cum_return'].values
    peak = np.maximum.accumulate(cum_equity)
    drawdown = (peak - cum_equity) / peak
    
    ax2.fill_between(equity['date'], 0, -drawdown * 100, color='red', alpha=0.3)
    ax2.set_title('回撤 (%)', fontsize=12)
    ax2.set_xlabel('日期', fontsize=12)
    ax2.set_ylabel('回撤 %', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[图表] 净值曲线已保存至: {save_path}")
    
    plt.show()


def plot_feature_importance(model: Any, feature_cols: List[str], save_path: Optional[str] = None, top_n: int = 20) -> None:
    """绘制特征重要性"""
    if HAS_LIGHTGBM and hasattr(model, 'feature_importances_'):
        importance = model.feature_importances_
        
        # 排序
        indices = np.argsort(importance)[::-1][:top_n]
        
        plt.figure(figsize=(10, 8))
        plt.barh(range(len(indices)), importance[indices][::-1], color='steelblue')
        plt.yticks(range(len(indices)), [feature_cols[i] for i in indices[::-1]])
        plt.xlabel('重要性')
        plt.title(f'Top {top_n} 特征重要性')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"[图表] 特征重要性已保存至: {save_path}")
    
    plt.show()


# ==================================================
# 八、主程序入口
# ==================================================

def main():
    """主程序入口"""
    print("=" * 60)
    print("期货单边行情识别与机器学习策略 V2.0")
    print("=" * 60)
    
    # ===== 1. 配置参数 =====
    config = StrategyConfig(
        future_days=5,
        long_threshold=0.03,      # 3% 收益阈值
        short_threshold=0.03,
        warmup_period=60,
        train_end='2022-12-31',
        valid_end='2023-12-31',
        signal_percentile=95,     # top 5%
        max_holding_days=10,
        stop_loss_pct=0.02,       # 2% 止损
        take_profit_pct=0.05,     # 5% 止盈
        trailing_stop_pct=0.015,  # 1.5% 移动止损
        max_positions=5,
        position_size=0.2
    )
    
    # 数据库路径
    script_dir = Path(__file__).parent
    db_path = script_dir.parent.parent / 'database' / 'futures' / 'futures.db'
    
    # 模型保存路径
    model_dir = script_dir / 'models'
    model_dir.mkdir(exist_ok=True)
    
    # 图表保存路径
    output_dir = script_dir / 'output'
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n数据库路径: {db_path}")
    print(f"模型保存目录: {model_dir}")
    
    # ===== 2. 加载数据 =====
    df_all = load_history_from_db(str(db_path), min_days=250)
    
    # ===== 3. 生成标签 =====
    df_labeled = assign_labels_v2(df_all, config, verbose=True)
    
    # ===== 4. 特征工程 =====
    df_feat = make_features_v2(df_labeled, warmup_period=config.warmup_period)
    
    # ===== 5. 数据集划分 =====
    df_train, df_valid, df_test = split_data_by_year(
        df_feat,
        train_end=config.train_end,
        valid_end=config.valid_end
    )
    
    # ===== 6. 训练模型 =====
    feature_cols = get_feature_columns(df_feat)
    
    # 训练多头模型
    long_model, long_threshold = train_model(
        df_train, df_valid, feature_cols,
        label_col='label_long',
        model_name='多头模型'
    )
    save_model(long_model, str(model_dir / 'long_model_lgbm.pkl'))
    
    # 训练空头模型
    short_model, short_threshold = train_model(
        df_train, df_valid, feature_cols,
        label_col='label_short',
        model_name='空头模型'
    )
    save_model(short_model, str(model_dir / 'short_model_lgbm.pkl'))
    
    # ===== 7. 测试集预测 =====
    print("\n" + "=" * 60)
    print("测试集回测")
    print("=" * 60)
    
    # 预测概率
    p_long = predict_proba(df_test, long_model, feature_cols)
    p_short = predict_proba(df_test, short_model, feature_cols)
    
    # 测试集 AUC
    y_test_long = df_test['label_long']
    y_test_short = df_test['label_short']
    
    auc_long = roc_auc_score(y_test_long, p_long) if y_test_long.sum() > 0 else 0
    auc_short = roc_auc_score(y_test_short, p_short) if y_test_short.sum() > 0 else 0
    
    print(f"\n[测试集] 多头模型 AUC: {auc_long:.4f}")
    print(f"[测试集] 空头模型 AUC: {auc_short:.4f}")
    
    # 使用严格阈值（top 5%）
    percentile = config.signal_percentile
    test_long_threshold = np.percentile(p_long, percentile)
    test_short_threshold = np.percentile(p_short, percentile)
    
    print(f"\n[回测] 使用 top {100-percentile:.0f}% 阈值")
    print(f"[回测] 多头阈值: {test_long_threshold:.4f}")
    print(f"[回测] 空头阈值: {test_short_threshold:.4f}")
    
    # 回测
    trades, equity = backtest_v2(
        df_test, p_long, p_short, config,
        long_threshold=test_long_threshold,
        short_threshold=test_short_threshold
    )
    
    # 分析结果
    results = analyze_backtest_results(trades, equity)
    print_backtest_results(results)
    
    # 绘制图表
    if len(equity) > 0:
        plot_equity_curve(equity, str(output_dir / 'equity_curve.png'))
    
    # 绘制特征重要性
    plot_feature_importance(long_model, feature_cols, str(output_dir / 'feature_importance.png'))
    
    print("\n" + "=" * 60)
    print("运行完成！")
    print("=" * 60)
    
    return {
        'config': config,
        'df_feat': df_feat,
        'long_model': long_model,
        'short_model': short_model,
        'trades': trades,
        'equity': equity,
        'results': results
    }


if __name__ == "__main__":
    main()
