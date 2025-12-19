"""
train.py - LightGBM 模型训练脚本
用于训练股票量化策略模型

运行频率: 每月/每季度
功能: 从数据库读取数据 -> 计算特征 -> 训练模型 -> 保存到 models/model.pkl
"""

import sqlite3
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score
import joblib
import os
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# ============ 配置 ============
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'stock.db')
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'model.pkl')

# 时间划分
TRAIN_START = '2018-01-01'
TRAIN_END = '2022-12-31'
VAL_START = '2023-01-01'
VAL_END = '2023-12-31'
TEST_START = '2024-01-01'
TEST_END = '2024-12-31'

# 标签参数
FUTURE_DAYS = 20       # 未来观察期
MIN_GAIN = 0.20        # 最小涨幅 20%
MAX_DRAWDOWN = 0.10    # 最大回撤限制 10%

# 模型参数
PARAMS = {
    'objective': 'binary',
    'metric': 'auc',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'n_estimators': 500,
    'verbose': -1,
    'random_state': 42
}

# 特征列表
FEATURES = [
    # 价格动量（6个）
    'ret_5d', 'ret_10d', 'ret_20d', 'ret_60d',
    'high_5d_break', 'high_20d_break',
    # 均线（9个）
    'ma5', 'ma10', 'ma20', 'ma60',
    'close_to_ma5', 'close_to_ma20', 'ma5_to_ma20',
    'ma_trend', 'ma20_slope',
    # 波动率（4个）
    'atr_20', 'volatility_20', 'amplitude_mean_10', 'vol_contract',
    # 成交量（6个）
    'volume_ratio', 'volume_ma5', 'volume_ma20',
    'volume_trend', 'turnover_mean_10', 'amount_rank',
    # 技术指标（5个）
    'rsi_14', 'macd', 'macd_signal', 'macd_hist', 'macd_cross',
    # 位置（4个）
    'pct_from_high_60', 'pct_from_low_60',
    'price_position_60', 'days_since_high_20'
]


def get_stock_list(conn):
    """获取股票列表（排除北交所）"""
    query = """
    SELECT symbol, name, market 
    FROM stock_main 
    WHERE market != 'BJ'
    """
    df = pd.read_sql(query, conn)
    return df


def get_stock_history(conn, symbol):
    """获取单只股票的历史数据"""
    table_name = f'hist_{symbol}'
    try:
        query = f'SELECT * FROM "{table_name}" ORDER BY date'
        df = pd.read_sql(query, conn)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df
    except Exception as e:
        return None


def compute_features(df):
    """计算30个特征"""
    if len(df) < 60:
        return None
    
    df = df.copy()
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']
    amount = df['amount']
    turnover = df['turnover']
    amplitude = df['amplitude']
    
    # ====== 价格动量（6个）======
    df['ret_5d'] = close.pct_change(5)
    df['ret_10d'] = close.pct_change(10)
    df['ret_20d'] = close.pct_change(20)
    df['ret_60d'] = close.pct_change(60)
    df['high_5d_break'] = (close >= high.rolling(5).max()).astype(int)
    df['high_20d_break'] = (close >= high.rolling(20).max()).astype(int)
    
    # ====== 均线（9个）======
    df['ma5'] = close.rolling(5).mean()
    df['ma10'] = close.rolling(10).mean()
    df['ma20'] = close.rolling(20).mean()
    df['ma60'] = close.rolling(60).mean()
    df['close_to_ma5'] = (close - df['ma5']) / df['ma5']
    df['close_to_ma20'] = (close - df['ma20']) / df['ma20']
    df['ma5_to_ma20'] = (df['ma5'] - df['ma20']) / df['ma20']
    # ma_trend: ma5 > ma10 > ma20 则为 1
    df['ma_trend'] = ((df['ma5'] > df['ma10']) & (df['ma10'] > df['ma20'])).astype(int)
    # ma20_slope: ma20 的斜率（20日变化率）
    df['ma20_slope'] = df['ma20'].pct_change(20)
    
    # ====== 波动率（4个）======
    # ATR 20日
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['atr_20'] = true_range.rolling(20).mean() / close
    
    # 20日波动率（收益率标准差）
    df['volatility_20'] = close.pct_change().rolling(20).std()
    
    # 10日平均振幅
    df['amplitude_mean_10'] = amplitude.rolling(10).mean()
    
    # 成交量收缩（当前成交量与20日平均的比值）
    df['vol_contract'] = volume / volume.rolling(20).mean()
    
    # ====== 成交量（6个）======
    df['volume_ma5'] = volume.rolling(5).mean()
    df['volume_ma20'] = volume.rolling(20).mean()
    df['volume_ratio'] = df['volume_ma5'] / df['volume_ma20']
    df['volume_trend'] = (df['volume_ma5'] > df['volume_ma20']).astype(int)
    df['turnover_mean_10'] = turnover.rolling(10).mean()
    # 成交额排名（归一化到0-1）
    df['amount_rank'] = amount.rolling(60).apply(
        lambda x: (x.iloc[-1] - x.min()) / (x.max() - x.min() + 1e-9) if len(x) == 60 else np.nan, 
        raw=False
    )
    
    # ====== 技术指标（5个）======
    # RSI 14
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    # MACD金叉信号
    df['macd_cross'] = ((df['macd'] > df['macd_signal']) & 
                        (df['macd'].shift(1) <= df['macd_signal'].shift(1))).astype(int)
    
    # ====== 位置（4个）======
    high_60 = high.rolling(60).max()
    low_60 = low.rolling(60).min()
    df['pct_from_high_60'] = (close - high_60) / high_60
    df['pct_from_low_60'] = (close - low_60) / low_60
    df['price_position_60'] = (close - low_60) / (high_60 - low_60 + 1e-9)
    
    # 距离20日最高点天数
    def days_since_high(series):
        if len(series) < 20:
            return np.nan
        idx_max = series.iloc[-20:].idxmax()
        return len(series) - 1 - series.index.get_loc(idx_max)
    
    df['days_since_high_20'] = high.rolling(20).apply(
        lambda x: 19 - np.argmax(x) if len(x) == 20 else np.nan, raw=True
    )
    
    return df


def compute_label(df, future_days=20, min_gain=0.20, max_drawdown=0.10):
    """
    计算标签：
    正样本 (label=1)：未来20个交易日最大涨幅 >= 20% 且达到最高点前最大回撤 < 10%
    负样本 (label=0)：其他情况
    """
    labels = []
    close = df['close'].values
    
    for i in range(len(df)):
        if i + future_days >= len(df):
            labels.append(np.nan)
            continue
        
        current_price = close[i]
        future_prices = close[i+1:i+1+future_days]
        
        # 计算未来最大涨幅
        max_price = np.max(future_prices)
        max_gain = (max_price - current_price) / current_price
        
        if max_gain < min_gain:
            labels.append(0)
            continue
        
        # 找到达到最高点的位置
        max_idx = np.argmax(future_prices)
        
        # 计算达到最高点前的最大回撤
        if max_idx == 0:
            # 第一天就是最高点，没有回撤
            max_dd = 0
        else:
            prices_before_peak = future_prices[:max_idx+1]
            running_max = np.maximum.accumulate(np.concatenate([[current_price], prices_before_peak[:-1]]))
            drawdowns = (running_max - prices_before_peak) / running_max
            max_dd = np.max(drawdowns) if len(drawdowns) > 0 else 0
        
        if max_dd < max_drawdown:
            labels.append(1)
        else:
            labels.append(0)
    
    df['label'] = labels
    return df


def prepare_data(conn, stock_list, start_date, end_date):
    """准备训练数据"""
    all_data = []
    
    print(f"开始处理数据 ({start_date} ~ {end_date})...")
    total = len(stock_list)
    
    for idx, row in stock_list.iterrows():
        symbol = row['symbol']
        name = row['name']
        
        if (idx + 1) % 500 == 0:
            print(f"  处理进度: {idx+1}/{total} ({(idx+1)/total*100:.1f}%)")
        
        # 获取历史数据
        df = get_stock_history(conn, symbol)
        if df is None or len(df) < 100:
            continue
        
        # 过滤ST股票
        if 'ST' in name or 'st' in name:
            continue
        
        # 计算特征
        df = compute_features(df)
        if df is None:
            continue
        
        # 计算标签
        df = compute_label(df, FUTURE_DAYS, MIN_GAIN, MAX_DRAWDOWN)
        
        # 过滤日期范围
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        if len(df) == 0:
            continue
        
        # 过滤日均成交额 < 2000万的
        df = df[df['amount'] >= 20000000]
        
        # 添加股票信息
        df['symbol'] = symbol
        df['name'] = name
        
        all_data.append(df[['date', 'symbol', 'name'] + FEATURES + ['label']])
    
    if len(all_data) == 0:
        return pd.DataFrame()
    
    result = pd.concat(all_data, ignore_index=True)
    result = result.dropna(subset=['label'])
    result = result.replace([np.inf, -np.inf], np.nan)
    result = result.dropna(subset=FEATURES)
    
    return result


def train_model(train_data, val_data):
    """训练 LightGBM 模型"""
    X_train = train_data[FEATURES]
    y_train = train_data['label']
    X_val = val_data[FEATURES]
    y_val = val_data['label']
    
    print(f"\n训练集大小: {len(train_data)}")
    print(f"验证集大小: {len(val_data)}")
    print(f"训练集正样本比例: {y_train.mean():.4f}")
    print(f"验证集正样本比例: {y_val.mean():.4f}")
    
    # 创建数据集
    train_set = lgb.Dataset(X_train, label=y_train)
    val_set = lgb.Dataset(X_val, label=y_val, reference=train_set)
    
    # 训练模型
    print("\n开始训练模型...")
    model = lgb.train(
        PARAMS,
        train_set,
        num_boost_round=PARAMS['n_estimators'],
        valid_sets=[train_set, val_set],
        valid_names=['train', 'valid'],
        callbacks=[
            lgb.early_stopping(stopping_rounds=50),
            lgb.log_evaluation(period=100)
        ]
    )
    
    return model


def evaluate_model(model, data, dataset_name):
    """评估模型性能"""
    X = data[FEATURES]
    y = data['label']
    
    y_pred_proba = model.predict(X)
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    auc = roc_auc_score(y, y_pred_proba)
    acc = accuracy_score(y, y_pred)
    precision = precision_score(y, y_pred, zero_division=0)
    recall = recall_score(y, y_pred, zero_division=0)
    f1 = f1_score(y, y_pred, zero_division=0)
    
    print(f"\n{dataset_name} 评估结果:")
    print(f"  AUC:       {auc:.4f}")
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    
    return {
        'auc': auc,
        'accuracy': acc,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }


def show_feature_importance(model):
    """显示特征重要性"""
    importance = model.feature_importance(importance_type='gain')
    feature_importance = pd.DataFrame({
        'feature': FEATURES,
        'importance': importance
    }).sort_values('importance', ascending=False)
    
    print("\n特征重要性 TOP 15:")
    print("-" * 40)
    for idx, row in feature_importance.head(15).iterrows():
        print(f"  {row['feature']:25s} {row['importance']:10.2f}")
    
    return feature_importance


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 LightGBM 量化模型训练")
    print("=" * 60)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 连接数据库
    print(f"\n📂 连接数据库: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    
    # 获取股票列表
    stock_list = get_stock_list(conn)
    print(f"📊 股票数量: {len(stock_list)} (排除北交所)")
    
    # 准备数据
    print("\n" + "=" * 60)
    print("📈 准备训练数据 (2018-2022)")
    train_data = prepare_data(conn, stock_list, TRAIN_START, TRAIN_END)
    
    print("\n" + "=" * 60)
    print("📈 准备验证数据 (2023)")
    val_data = prepare_data(conn, stock_list, VAL_START, VAL_END)
    
    print("\n" + "=" * 60)
    print("📈 准备测试数据 (2024)")
    test_data = prepare_data(conn, stock_list, TEST_START, TEST_END)
    
    conn.close()
    
    if len(train_data) == 0 or len(val_data) == 0:
        print("❌ 数据准备失败，数据量不足")
        return
    
    # 训练模型
    print("\n" + "=" * 60)
    model = train_model(train_data, val_data)
    
    # 评估模型
    print("\n" + "=" * 60)
    print("📊 模型评估")
    train_metrics = evaluate_model(model, train_data, "训练集")
    val_metrics = evaluate_model(model, val_data, "验证集")
    if len(test_data) > 0:
        test_metrics = evaluate_model(model, test_data, "测试集")
    
    # 显示特征重要性
    show_feature_importance(model)
    
    # 保存模型
    print("\n" + "=" * 60)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({
        'model': model,
        'features': FEATURES,
        'params': PARAMS,
        'train_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'val_auc': val_metrics['auc']
    }, MODEL_PATH)
    print(f"✅ 模型已保存到: {MODEL_PATH}")
    
    print("\n" + "=" * 60)
    print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == '__main__':
    main()

