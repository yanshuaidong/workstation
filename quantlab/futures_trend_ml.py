#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货单边行情识别与机器学习策略

功能：
1. 从 SQLite 数据库读取期货主连日线数据
2. 识别 3-10 日单边行情并打标签
3. 特征工程（只使用过去信息）
4. 使用 LightGBM 训练二分类模型
5. 简单多头策略回测

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
# 一、数据类定义
# ==================================================

@dataclass
class TrendSegment:
    """单边行情段信息"""
    symbol: str           # 品种代码
    t_start_idx: int      # 起始索引
    t_end_idx: int        # 结束索引
    direction: int        # 方向：+1上涨，-1下跌
    length: int           # 段长度（交易日数）
    total_return: float   # 总收益率
    max_reverse: float    # 最大逆向波动
    score: float          # 趋势评分


@dataclass
class PhaseInfo:
    """单边行情阶段信息"""
    symbol: str
    t_start_idx: int
    t_end_idx: int
    direction: int
    phase: str            # 'early', 'mid', 'late'


# ==================================================
# 二、数据读取与整合
# ==================================================

def get_active_contracts(conn: sqlite3.Connection) -> List[str]:
    """
    从 contracts_main 中获取所有活跃合约代码
    
    参数:
        conn: SQLite 数据库连接
        
    返回:
        活跃合约的 symbol 列表
    """
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
        列：date, symbol, open, high, low, close, volume, open_interest
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
# 三、单边行情识别与打标签
# ==================================================

def calculate_atr(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    计算 ATR (Average True Range)
    
    参数:
        df: 包含 high, low, close 列的 DataFrame
        period: ATR 周期
        
    返回:
        ATR 序列
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # ATR
    atr = tr.rolling(window=period, min_periods=1).mean()
    
    return atr


def identify_trend_segments(
    df_symbol: pd.DataFrame,
    k1: float = 2.0,
    max_reverse_ratio: float = 0.4,
    min_length: int = 3,
    max_length: int = 10
) -> List[TrendSegment]:
    """
    识别单边行情段
    
    参数:
        df_symbol: 单个品种的 DataFrame，按日期排序
        k1: 总幅度相对 ATR 的倍数阈值
        max_reverse_ratio: 最大逆向波动比例阈值
        min_length: 最小行情长度
        max_length: 最大行情长度
        
    返回:
        识别出的趋势段列表
    """
    df = df_symbol.reset_index(drop=True)
    symbol = df['symbol'].iloc[0]
    n = len(df)
    
    # 计算 ATR
    atr = calculate_atr(df, period=20)
    
    candidates = []
    
    # 遍历所有起点和窗口长度
    for t in range(n):
        for L in range(min_length, min(max_length + 1, n - t)):
            t_end = t + L - 1
            
            close_t = df['close'].iloc[t]
            close_end = df['close'].iloc[t_end]
            atr_t = atr.iloc[t]
            
            if close_t <= 0 or atr_t <= 0:
                continue
            
            # 计算上涨候选
            R_up = (close_end - close_t) / close_t
            
            # 计算下跌候选
            R_down = (close_t - close_end) / close_t
            
            # 区间内最低价和最高价
            low_min = df['low'].iloc[t:t_end+1].min()
            high_max = df['high'].iloc[t:t_end+1].max()
            
            # 波动自适应阈值
            threshold = k1 * atr_t / close_t
            
            # 检查上涨候选
            if R_up >= threshold:
                max_drawdown = (close_t - low_min) / close_t
                if max_drawdown <= max_reverse_ratio * R_up:
                    score = R_up / (1e-6 + max_drawdown)
                    candidates.append(TrendSegment(
                        symbol=symbol,
                        t_start_idx=t,
                        t_end_idx=t_end,
                        direction=1,
                        length=L,
                        total_return=R_up,
                        max_reverse=max_drawdown,
                        score=score
                    ))
            
            # 检查下跌候选
            if R_down >= threshold:
                max_rebound = (high_max - close_t) / close_t
                if max_rebound <= max_reverse_ratio * R_down:
                    score = R_down / (1e-6 + max_rebound)
                    candidates.append(TrendSegment(
                        symbol=symbol,
                        t_start_idx=t,
                        t_end_idx=t_end,
                        direction=-1,
                        length=L,
                        total_return=R_down,
                        max_reverse=max_rebound,
                        score=score
                    ))
    
    return candidates


def remove_overlapping_segments(candidates: List[TrendSegment]) -> List[TrendSegment]:
    """
    去除重叠的趋势段，保留评分最高的
    
    参数:
        candidates: 候选趋势段列表
        
    返回:
        去重后的趋势段列表
    """
    if not candidates:
        return []
    
    # 按 score 降序排序
    sorted_candidates = sorted(candidates, key=lambda x: x.score, reverse=True)
    
    selected = []
    
    for cand in sorted_candidates:
        # 检查是否与已选段重叠
        overlap = False
        for sel in selected:
            if cand.symbol == sel.symbol:
                # 检查时间重叠
                if not (cand.t_end_idx < sel.t_start_idx or cand.t_start_idx > sel.t_end_idx):
                    overlap = True
                    break
        
        if not overlap:
            selected.append(cand)
    
    return selected


def split_segments_into_phases(
    segments: List[TrendSegment],
    df_symbol: pd.DataFrame
) -> List[PhaseInfo]:
    """
    将单边段切成"前/中/后"阶段
    
    参数:
        segments: 趋势段列表
        df_symbol: 对应品种的 DataFrame
        
    返回:
        阶段信息列表
    """
    df = df_symbol.reset_index(drop=True)
    phases = []
    
    for seg in segments:
        t_start = seg.t_start_idx
        t_end = seg.t_end_idx
        direction = seg.direction
        
        # 计算累计涨跌幅
        close_start = df['close'].iloc[t_start]
        total_move = df['close'].iloc[t_end] - close_start
        
        if abs(total_move) < 1e-10:
            continue
        
        # 找到累计幅度达到 1/3 和 2/3 的位置
        threshold_1 = total_move / 3
        threshold_2 = total_move * 2 / 3
        
        date_1_idx = t_start
        date_2_idx = t_start
        
        for i in range(t_start, t_end + 1):
            cum_move = df['close'].iloc[i] - close_start
            if direction == 1:  # 上涨
                if cum_move >= threshold_1 and date_1_idx == t_start:
                    date_1_idx = i
                if cum_move >= threshold_2 and date_2_idx == t_start:
                    date_2_idx = i
            else:  # 下跌
                if cum_move <= threshold_1 and date_1_idx == t_start:
                    date_1_idx = i
                if cum_move <= threshold_2 and date_2_idx == t_start:
                    date_2_idx = i
        
        # 确保索引有效
        date_1_idx = max(t_start, min(date_1_idx, t_end))
        date_2_idx = max(date_1_idx, min(date_2_idx, t_end))
        
        # 添加各阶段
        # 前段：[t_start, date_1]
        for i in range(t_start, date_1_idx + 1):
            phases.append(PhaseInfo(
                symbol=seg.symbol,
                t_start_idx=i,
                t_end_idx=i,
                direction=direction,
                phase='early'
            ))
        
        # 中段：(date_1, date_2]
        for i in range(date_1_idx + 1, date_2_idx + 1):
            phases.append(PhaseInfo(
                symbol=seg.symbol,
                t_start_idx=i,
                t_end_idx=i,
                direction=direction,
                phase='mid'
            ))
        
        # 后段：(date_2, t_end]
        for i in range(date_2_idx + 1, t_end + 1):
            phases.append(PhaseInfo(
                symbol=seg.symbol,
                t_start_idx=i,
                t_end_idx=i,
                direction=direction,
                phase='late'
            ))
    
    return phases


def assign_labels(df_all: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    识别单边行情并为每个交易日打标签
    
    标签定义：
    - label = +1：上涨单边段的前段或中段
    - label = -1：下跌单边段的前段或中段
    - label = 0：其他（包括后段和无单边行情）
    
    参数:
        df_all: 包含所有品种数据的 DataFrame
        verbose: 是否打印详细信息
        
    返回:
        添加了 label 列的 DataFrame
    """
    df = df_all.copy()
    df['label'] = 0
    
    symbols = df['symbol'].unique()
    total_segments = 0
    
    if verbose:
        print(f"\n[标签生成] 开始处理 {len(symbols)} 个品种...")
    
    for symbol in symbols:
        # 获取该品种数据
        mask = df['symbol'] == symbol
        df_symbol = df[mask].copy()
        
        if len(df_symbol) < 20:
            continue
        
        # 识别趋势段
        candidates = identify_trend_segments(df_symbol)
        
        # 去除重叠
        segments = remove_overlapping_segments(candidates)
        
        if not segments:
            continue
        
        total_segments += len(segments)
        
        # 获取阶段信息
        phases = split_segments_into_phases(segments, df_symbol)
        
        # 构建索引映射
        original_indices = df_symbol.index.tolist()
        
        # 打标签
        for phase in phases:
            if phase.phase in ['early', 'mid']:
                idx = phase.t_start_idx
                if idx < len(original_indices):
                    original_idx = original_indices[idx]
                    df.loc[original_idx, 'label'] = phase.direction
    
    if verbose:
        label_counts = df['label'].value_counts().sort_index()
        print(f"[标签生成] 共识别 {total_segments} 个单边行情段")
        print(f"[标签生成] 标签分布:")
        print(f"  - label=-1 (空头信号): {label_counts.get(-1, 0):,} ({label_counts.get(-1, 0)/len(df)*100:.2f}%)")
        print(f"  - label=0  (无信号):   {label_counts.get(0, 0):,} ({label_counts.get(0, 0)/len(df)*100:.2f}%)")
        print(f"  - label=+1 (多头信号): {label_counts.get(1, 0):,} ({label_counts.get(1, 0)/len(df)*100:.2f}%)")
    
    return df


# ==================================================
# 四、特征工程
# ==================================================

def compute_trend_features(close: pd.Series, window: int = 10) -> Tuple[pd.Series, pd.Series]:
    """
    计算趋势斜率和 R²
    
    参数:
        close: 收盘价序列
        window: 滚动窗口大小
        
    返回:
        (斜率序列, R²序列)
    """
    slopes = []
    r2s = []
    
    for i in range(len(close)):
        if i < window - 1:
            slopes.append(np.nan)
            r2s.append(np.nan)
        else:
            y = close.iloc[i-window+1:i+1].values
            x = np.arange(window).reshape(-1, 1)
            
            # 检查是否包含 NaN 值
            if np.any(np.isnan(y)):
                slopes.append(np.nan)
                r2s.append(np.nan)
                continue
            
            # 标准化
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


def make_features(df: pd.DataFrame, warmup_period: int = 60) -> pd.DataFrame:
    """
    生成机器学习特征（只使用过去信息）
    
    参数:
        df: 包含基础价格数据和 label 的 DataFrame
        warmup_period: 预热期天数（前 N 天不生成特征）
        
    返回:
        添加了特征列的 DataFrame
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
        volume = df_sym['volume']
        oi = df_sym['open_interest']
        
        # ===== 1. 价格动量与突破 =====
        # 收益率
        df_sym['feat_ret_3'] = close.pct_change(3)
        df_sym['feat_ret_5'] = close.pct_change(5)
        df_sym['feat_ret_10'] = close.pct_change(10)
        
        # 20 日高低点
        df_sym['rolling_high_20'] = high.rolling(20, min_periods=1).max()
        df_sym['rolling_low_20'] = low.rolling(20, min_periods=1).min()
        
        # 收盘在 20 日区间中的位置
        range_20 = df_sym['rolling_high_20'] - df_sym['rolling_low_20']
        df_sym['feat_price_pos_20'] = (close - df_sym['rolling_low_20']) / (range_20 + 1e-6)
        
        # 突破 20 日新高/新低
        df_sym['feat_break_high_20'] = (close >= df_sym['rolling_high_20']).astype(int)
        df_sym['feat_break_low_20'] = (close <= df_sym['rolling_low_20']).astype(int)
        
        # ===== 2. 均线与趋势 =====
        df_sym['MA_3'] = close.rolling(3, min_periods=1).mean()
        df_sym['MA_5'] = close.rolling(5, min_periods=1).mean()
        df_sym['MA_10'] = close.rolling(10, min_periods=1).mean()
        df_sym['MA_20'] = close.rolling(20, min_periods=1).mean()
        
        df_sym['feat_ma_5_20_diff'] = df_sym['MA_5'] - df_sym['MA_20']
        df_sym['feat_ma_5_20_ratio'] = df_sym['MA_5'] / (df_sym['MA_20'] + 1e-6)
        
        # 趋势斜率和 R²
        slope, r2 = compute_trend_features(close, window=10)
        df_sym['feat_trend_slope_10'] = slope
        df_sym['feat_trend_r2_10'] = r2
        
        # ===== 3. 波动与 ATR =====
        df_sym['feat_atr_20'] = calculate_atr(df_sym, period=20)
        
        # 收益率的滚动标准差
        returns = close.pct_change()
        df_sym['feat_vol_5'] = returns.rolling(5, min_periods=1).std()
        df_sym['feat_vol_20'] = returns.rolling(20, min_periods=1).std()
        df_sym['feat_vol_ratio_5_20'] = df_sym['feat_vol_5'] / (df_sym['feat_vol_20'] + 1e-6)
        
        # ===== 4. 成交量与持仓量 =====
        df_sym['vol_ma_20'] = volume.rolling(20, min_periods=1).mean()
        df_sym['feat_vol_ratio'] = volume / (df_sym['vol_ma_20'] + 1e-6)
        
        df_sym['oi_ma_20'] = oi.rolling(20, min_periods=1).mean()
        df_sym['feat_oi_ratio'] = oi / (df_sym['oi_ma_20'] + 1e-6)
        df_sym['feat_oi_chg_1'] = oi.diff(1)
        df_sym['feat_oi_chg_3'] = oi.diff(3)
        df_sym['feat_oi_chg_rate_3'] = df_sym['feat_oi_chg_3'] / (df_sym['oi_ma_20'] + 1e-6)
        
        # ===== 5. K 线位置 =====
        bar_range = high - low
        df_sym['feat_close_pos_in_bar'] = (close - low) / (bar_range + 1e-6)
        
        # 保存特征
        feature_dfs.append(df_sym)
    
    # 合并所有品种
    df_feat = pd.concat(feature_dfs, ignore_index=True)
    
    # 获取所有特征列
    feature_cols = [col for col in df_feat.columns if col.startswith('feat_')]
    
    # 移除预热期的数据
    df_feat = df_feat.groupby('symbol').apply(
        lambda x: x.iloc[warmup_period:] if len(x) > warmup_period else x.iloc[0:0]
    ).reset_index(drop=True)
    
    # 删除包含 NaN 的行
    initial_len = len(df_feat)
    df_feat = df_feat.dropna(subset=feature_cols)
    
    print(f"[特征工程] 生成 {len(feature_cols)} 个特征")
    print(f"[特征工程] 移除预热期后样本数: {initial_len:,} → {len(df_feat):,}")
    
    return df_feat


# ==================================================
# 五、数据集划分
# ==================================================

def split_data_by_year(
    df: pd.DataFrame,
    train_end: str = '2022-12-31',
    valid_end: str = '2023-12-31'
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    按固定年份划分数据集
    
    参数:
        df: 包含特征的 DataFrame
        train_end: 训练集结束日期
        valid_end: 验证集结束日期
        
    返回:
        (训练集, 验证集, 测试集)
    """
    df_train = df[df['date'] <= train_end]
    df_valid = df[(df['date'] > train_end) & (df['date'] <= valid_end)]
    df_test = df[df['date'] > valid_end]
    
    print(f"\n[数据划分] 训练集: {len(df_train):,} 样本 ({df_train['date'].min().date()} ~ {df_train['date'].max().date()})")
    print(f"[数据划分] 验证集: {len(df_valid):,} 样本 ({df_valid['date'].min().date()} ~ {df_valid['date'].max().date()})")
    print(f"[数据划分] 测试集: {len(df_test):,} 样本 ({df_test['date'].min().date()} ~ {df_test['date'].max().date()})")
    
    return df_train, df_valid, df_test


def prepare_labels(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """
    准备多头和空头标签
    
    参数:
        df: 包含 label 列的 DataFrame
        
    返回:
        (y_long, y_short) - 多头标签和空头标签
    """
    y_long = (df['label'] == 1).astype(int)
    y_short = (df['label'] == -1).astype(int)
    
    return y_long, y_short


# ==================================================
# 六、模型训练
# ==================================================

def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """获取所有特征列名"""
    return [col for col in df.columns if col.startswith('feat_')]


def train_long_model(
    df_train: pd.DataFrame,
    df_valid: pd.DataFrame,
    feature_cols: List[str],
    params: Optional[Dict[str, Any]] = None
) -> Any:
    """
    训练多头 LightGBM 模型
    
    参数:
        df_train: 训练集
        df_valid: 验证集
        feature_cols: 特征列名列表
        params: 模型参数（可选）
        
    返回:
        训练好的模型
    """
    print("\n[模型训练] 开始训练多头模型...")
    
    # 准备数据
    X_train = df_train[feature_cols].values
    y_train, _ = prepare_labels(df_train)
    y_train = y_train.values
    
    X_valid = df_valid[feature_cols].values
    y_valid, _ = prepare_labels(df_valid)
    y_valid = y_valid.values
    
    # 计算类别权重
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos_weight = neg_count / max(pos_count, 1)
    
    print(f"[模型训练] 训练集正样本: {pos_count:,}, 负样本: {neg_count:,}")
    print(f"[模型训练] scale_pos_weight: {scale_pos_weight:.2f}")
    
    # 默认参数
    default_params = {
        'num_leaves': 31,
        'max_depth': 6,
        'learning_rate': 0.05,
        'n_estimators': 500,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'scale_pos_weight': scale_pos_weight,
        'random_state': 42,
        'n_jobs': -1,
        'verbosity': -1
    }
    
    if params:
        default_params.update(params)
    
    if HAS_LIGHTGBM:
        # 使用 LightGBM
        model = lgb.LGBMClassifier(**default_params)
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_valid, y_valid)],
            callbacks=[lgb.early_stopping(50, verbose=False)]
        )
    else:
        # 使用 sklearn GradientBoosting
        sklearn_params = {
            'n_estimators': 200,
            'max_depth': 5,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'random_state': 42
        }
        model = GradientBoostingClassifier(**sklearn_params)
        model.fit(X_train, y_train)
    
    # 评估模型
    y_pred_proba = model.predict_proba(X_valid)[:, 1]
    
    # 打印概率分布，帮助选择合适的阈值
    print(f"\n[模型训练] 验证集概率分布:")
    print(f"  - Min:  {y_pred_proba.min():.4f}")
    print(f"  - 25%:  {np.percentile(y_pred_proba, 25):.4f}")
    print(f"  - 50%:  {np.percentile(y_pred_proba, 50):.4f}")
    print(f"  - 75%:  {np.percentile(y_pred_proba, 75):.4f}")
    print(f"  - 90%:  {np.percentile(y_pred_proba, 90):.4f}")
    print(f"  - 95%:  {np.percentile(y_pred_proba, 95):.4f}")
    print(f"  - Max:  {y_pred_proba.max():.4f}")
    
    # 使用动态阈值：取正样本比例作为阈值参考
    pos_ratio = y_valid.mean()
    dynamic_threshold = np.percentile(y_pred_proba, (1 - pos_ratio) * 100)
    
    y_pred = (y_pred_proba > dynamic_threshold).astype(int)
    
    auc = roc_auc_score(y_valid, y_pred_proba) if y_valid.sum() > 0 else 0
    acc = accuracy_score(y_valid, y_pred)
    precision = precision_score(y_valid, y_pred, zero_division=0)
    recall = recall_score(y_valid, y_pred, zero_division=0)
    
    print(f"\n[模型训练] 验证集评估 (阈值={dynamic_threshold:.4f}):")
    print(f"  - AUC:       {auc:.4f}")
    print(f"  - Accuracy:  {acc:.4f}")
    print(f"  - Precision: {precision:.4f}")
    print(f"  - Recall:    {recall:.4f}")
    
    return model


def train_short_model(
    df_train: pd.DataFrame,
    df_valid: pd.DataFrame,
    feature_cols: List[str],
    params: Optional[Dict[str, Any]] = None
) -> Any:
    """
    训练空头 LightGBM 模型
    
    参数:
        df_train: 训练集
        df_valid: 验证集
        feature_cols: 特征列名列表
        params: 模型参数（可选）
        
    返回:
        训练好的模型
    """
    print("\n[模型训练] 开始训练空头模型...")
    
    # 准备数据
    X_train = df_train[feature_cols].values
    _, y_train = prepare_labels(df_train)
    y_train = y_train.values
    
    X_valid = df_valid[feature_cols].values
    _, y_valid = prepare_labels(df_valid)
    y_valid = y_valid.values
    
    # 计算类别权重
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos_weight = neg_count / max(pos_count, 1)
    
    print(f"[模型训练] 训练集正样本: {pos_count:,}, 负样本: {neg_count:,}")
    print(f"[模型训练] scale_pos_weight: {scale_pos_weight:.2f}")
    
    # 默认参数
    default_params = {
        'num_leaves': 31,
        'max_depth': 6,
        'learning_rate': 0.05,
        'n_estimators': 500,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
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
            callbacks=[lgb.early_stopping(50, verbose=False)]
        )
    else:
        sklearn_params = {
            'n_estimators': 200,
            'max_depth': 5,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'random_state': 42
        }
        model = GradientBoostingClassifier(**sklearn_params)
        model.fit(X_train, y_train)
    
    # 评估模型
    y_pred_proba = model.predict_proba(X_valid)[:, 1]
    
    # 打印概率分布
    print(f"\n[模型训练] 验证集概率分布:")
    print(f"  - Min:  {y_pred_proba.min():.4f}")
    print(f"  - 25%:  {np.percentile(y_pred_proba, 25):.4f}")
    print(f"  - 50%:  {np.percentile(y_pred_proba, 50):.4f}")
    print(f"  - 75%:  {np.percentile(y_pred_proba, 75):.4f}")
    print(f"  - 90%:  {np.percentile(y_pred_proba, 90):.4f}")
    print(f"  - 95%:  {np.percentile(y_pred_proba, 95):.4f}")
    print(f"  - Max:  {y_pred_proba.max():.4f}")
    
    # 使用动态阈值
    pos_ratio = y_valid.mean()
    dynamic_threshold = np.percentile(y_pred_proba, (1 - pos_ratio) * 100)
    
    y_pred = (y_pred_proba > dynamic_threshold).astype(int)
    
    auc = roc_auc_score(y_valid, y_pred_proba) if y_valid.sum() > 0 else 0
    acc = accuracy_score(y_valid, y_pred)
    precision = precision_score(y_valid, y_pred, zero_division=0)
    recall = recall_score(y_valid, y_pred, zero_division=0)
    
    print(f"\n[模型训练] 验证集评估 (阈值={dynamic_threshold:.4f}):")
    print(f"  - AUC:       {auc:.4f}")
    print(f"  - Accuracy:  {acc:.4f}")
    print(f"  - Precision: {precision:.4f}")
    print(f"  - Recall:    {recall:.4f}")
    
    return model


def predict_proba(
    df: pd.DataFrame,
    model: Any,
    feature_cols: List[str]
) -> pd.Series:
    """
    使用模型预测概率
    
    参数:
        df: 待预测数据
        model: 训练好的模型
        feature_cols: 特征列名列表
        
    返回:
        预测概率序列
    """
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
# 七、简单策略回测
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


def simple_backtest(
    df_test: pd.DataFrame,
    p_long: pd.Series,
    threshold_long: float = 0.6,
    max_holding_days: int = 10,
    stop_loss_atr_mult: float = 2.0,
    fee_rate: float = 0.0003
) -> Tuple[List[Trade], pd.DataFrame]:
    """
    简单多头策略回测
    
    参数:
        df_test: 测试集数据（需包含 date, symbol, close, feat_atr_20）
        p_long: 多头概率序列
        threshold_long: 开仓阈值
        max_holding_days: 最大持仓天数
        stop_loss_atr_mult: 止损 ATR 倍数
        fee_rate: 手续费率
        
    返回:
        (交易记录列表, 每日净值 DataFrame)
    """
    print(f"\n[回测] 开始回测，阈值={threshold_long}, 最大持仓={max_holding_days}天")
    
    df = df_test.copy()
    df['p_long'] = p_long.values
    
    # 按日期排序
    df = df.sort_values('date').reset_index(drop=True)
    
    trades = []
    
    # 遍历每个品种单独回测（简化处理）
    for symbol in df['symbol'].unique():
        df_sym = df[df['symbol'] == symbol].reset_index(drop=True)
        
        position = None  # 当前持仓信息
        
        for i in range(len(df_sym)):
            row = df_sym.iloc[i]
            
            if position is None:
                # 没有持仓，检查是否开仓
                if row['p_long'] > threshold_long:
                    position = {
                        'entry_idx': i,
                        'entry_date': row['date'],
                        'entry_price': row['close'],
                        'peak_price': row['close'],
                        'atr': row.get('feat_atr_20', row['close'] * 0.02)
                    }
            else:
                # 有持仓，检查是否平仓
                holding_days = i - position['entry_idx']
                current_price = row['close']
                
                # 更新峰值
                position['peak_price'] = max(position['peak_price'], current_price)
                
                # 检查止损
                drawdown = (position['peak_price'] - current_price)
                stop_loss_triggered = drawdown > stop_loss_atr_mult * position['atr']
                
                # 检查最大持仓天数
                max_days_reached = holding_days >= max_holding_days
                
                if stop_loss_triggered or max_days_reached:
                    # 平仓
                    return_pct = (current_price - position['entry_price']) / position['entry_price']
                    return_pct -= fee_rate * 2  # 开仓+平仓手续费
                    
                    trades.append(Trade(
                        symbol=symbol,
                        entry_date=position['entry_date'],
                        exit_date=row['date'],
                        entry_price=position['entry_price'],
                        exit_price=current_price,
                        holding_days=holding_days,
                        return_pct=return_pct,
                        direction=1
                    ))
                    
                    position = None
    
    # 计算每日净值
    if not trades:
        print("[回测] 没有交易发生")
        return trades, pd.DataFrame()
    
    # 简化的净值计算：假设每笔交易使用相同资金
    dates = df['date'].unique()
    equity = pd.DataFrame({'date': dates, 'equity': 1.0})
    equity = equity.set_index('date')
    
    for trade in trades:
        # 在平仓日计入收益
        if trade.exit_date in equity.index:
            daily_return = trade.return_pct / max(trade.holding_days, 1)
            
            # 将收益分摊到持仓期间
            trade_dates = pd.date_range(trade.entry_date, trade.exit_date)
            for d in trade_dates:
                if d in equity.index:
                    equity.loc[d, 'equity'] += daily_return / len(trade_dates)
    
    # 累计净值
    equity['cum_equity'] = equity['equity'].cumprod()
    
    return trades, equity.reset_index()


def analyze_backtest_results(trades: List[Trade], equity: pd.DataFrame) -> Dict[str, float]:
    """
    分析回测结果
    
    参数:
        trades: 交易记录列表
        equity: 每日净值 DataFrame
        
    返回:
        回测统计指标字典
    """
    if not trades:
        return {}
    
    returns = [t.return_pct for t in trades]
    
    # 基本统计
    total_trades = len(trades)
    win_trades = sum(1 for r in returns if r > 0)
    win_rate = win_trades / total_trades if total_trades > 0 else 0
    
    avg_return = np.mean(returns)
    total_return = np.prod([1 + r for r in returns]) - 1
    
    avg_holding_days = np.mean([t.holding_days for t in trades])
    
    # 最大回撤
    if len(equity) > 0 and 'cum_equity' in equity.columns:
        cum_equity = equity['cum_equity'].values
        peak = np.maximum.accumulate(cum_equity)
        drawdown = (peak - cum_equity) / peak
        max_drawdown = drawdown.max()
    else:
        max_drawdown = 0
    
    # 年化收益（假设 250 交易日/年）
    if len(equity) > 0:
        days = len(equity)
        annual_return = (1 + total_return) ** (250 / max(days, 1)) - 1
    else:
        annual_return = 0
    
    results = {
        '总交易次数': total_trades,
        '盈利次数': win_trades,
        '胜率': win_rate,
        '平均单笔收益': avg_return,
        '累计收益': total_return,
        '年化收益': annual_return,
        '最大回撤': max_drawdown,
        '平均持仓天数': avg_holding_days
    }
    
    return results


def print_backtest_results(results: Dict[str, float]) -> None:
    """打印回测结果"""
    print("\n" + "=" * 50)
    print("回测结果汇总")
    print("=" * 50)
    
    for key, value in results.items():
        if isinstance(value, float):
            if '率' in key or '收益' in key or '回撤' in key:
                print(f"{key}: {value * 100:.2f}%")
            else:
                print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")


def plot_equity_curve(equity: pd.DataFrame, save_path: Optional[str] = None) -> None:
    """
    绘制净值曲线
    
    参数:
        equity: 包含 date 和 cum_equity 列的 DataFrame
        save_path: 保存图片路径（可选）
    """
    if len(equity) == 0:
        return
    
    plt.figure(figsize=(12, 6))
    plt.plot(equity['date'], equity['cum_equity'], 'b-', linewidth=1.5)
    plt.title('策略净值曲线', fontsize=14)
    plt.xlabel('日期', fontsize=12)
    plt.ylabel('净值', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[图表] 净值曲线已保存至: {save_path}")
    
    plt.show()


# ==================================================
# 八、主程序入口
# ==================================================

def main():
    """主程序入口"""
    print("=" * 60)
    print("期货单边行情识别与机器学习策略")
    print("=" * 60)
    
    # ===== 1. 配置参数 =====
    # 数据库路径（相对于脚本位置）
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / 'database' / 'futures' / 'futures.db'
    
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
    
    # ===== 3. 识别单边行情并打标签 =====
    df_labeled = assign_labels(df_all, verbose=True)
    
    # ===== 4. 特征工程 =====
    df_feat = make_features(df_labeled, warmup_period=60)
    
    # ===== 5. 数据集划分 =====
    df_train, df_valid, df_test = split_data_by_year(
        df_feat,
        train_end='2022-12-31',
        valid_end='2023-12-31'
    )
    
    # ===== 6. 训练模型 =====
    feature_cols = get_feature_columns(df_feat)
    
    # 训练多头模型
    long_model = train_long_model(df_train, df_valid, feature_cols)
    save_model(long_model, str(model_dir / 'long_model_lgbm.pkl'))
    
    # 训练空头模型
    short_model = train_short_model(df_train, df_valid, feature_cols)
    save_model(short_model, str(model_dir / 'short_model_lgbm.pkl'))
    
    # ===== 7. 测试集预测与回测 =====
    print("\n" + "=" * 60)
    print("测试集回测")
    print("=" * 60)
    
    # 预测多头概率
    p_long = predict_proba(df_test, long_model, feature_cols)
    
    # 在测试集上评估
    y_test_long, _ = prepare_labels(df_test)
    auc_test = roc_auc_score(y_test_long, p_long) if y_test_long.sum() > 0 else 0
    print(f"\n[测试集] 多头模型 AUC: {auc_test:.4f}")
    
    # 打印测试集概率分布
    print(f"\n[测试集] 多头概率分布:")
    print(f"  - Min:  {p_long.min():.4f}")
    print(f"  - 25%:  {np.percentile(p_long, 25):.4f}")
    print(f"  - 50%:  {np.percentile(p_long, 50):.4f}")
    print(f"  - 75%:  {np.percentile(p_long, 75):.4f}")
    print(f"  - 90%:  {np.percentile(p_long, 90):.4f}")
    print(f"  - 95%:  {np.percentile(p_long, 95):.4f}")
    print(f"  - Max:  {p_long.max():.4f}")
    
    # 动态计算阈值：取 top 20% 的概率作为阈值（约等于正样本比例）
    pos_ratio = y_test_long.mean()
    dynamic_threshold = np.percentile(p_long, (1 - pos_ratio) * 100)
    print(f"\n[回测] 动态阈值 (top {pos_ratio*100:.1f}%): {dynamic_threshold:.4f}")
    
    # 简单回测
    trades, equity = simple_backtest(
        df_test,
        p_long,
        threshold_long=dynamic_threshold,
        max_holding_days=10,
        stop_loss_atr_mult=2.0
    )
    
    # 分析回测结果
    results = analyze_backtest_results(trades, equity)
    print_backtest_results(results)
    
    # 绘制净值曲线
    if len(equity) > 0:
        plot_equity_curve(equity, str(output_dir / 'equity_curve.png'))
    
    print("\n" + "=" * 60)
    print("运行完成！")
    print("=" * 60)
    
    return {
        'df_feat': df_feat,
        'long_model': long_model,
        'short_model': short_model,
        'trades': trades,
        'equity': equity,
        'results': results
    }


if __name__ == "__main__":
    main()

