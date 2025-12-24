#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日预测脚本：基于融合模型生成交易信号

使用方法：
    python predict.py              # 显示今日信号
    python predict.py --top 10     # 显示前10个信号
    python predict.py --json       # 输出JSON格式

前置条件：
    1. 确保 database/futures/futures.db 已更新到最新日期
    2. 确保 database/institution/institution.db 已更新到最新日期
    3. 确保 models/ 目录下已有训练好的模型

作者：量化工程师
日期：2024
"""

import json
import sqlite3
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
import pymysql
from sklearn.linear_model import LinearRegression

warnings.filterwarnings('ignore')


# ==================================================
# 品种名称映射
# ==================================================

def load_futures_mapping() -> Dict[str, str]:
    """
    加载期货品种映射表，返回 {symbol: 中文名称} 的字典
    """
    script_dir = Path(__file__).parent
    mapping_path = script_dir.parent.parent / 'database' / 'futures' / 'futures_mapping.json'
    
    symbol_to_name = {}
    
    if mapping_path.exists():
        try:
            with open(mapping_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for symbol, info in data.get('futures', {}).items():
                name = info.get('name', symbol)
                # 去掉"主连"后缀
                if name.endswith('主连'):
                    name = name[:-2]
                symbol_to_name[symbol.lower()] = name
        except Exception as e:
            print(f"[警告] 加载品种映射文件失败: {e}")
    
    return symbol_to_name


# 全局变量
FUTURES_NAME_MAP: Dict[str, str] = {}


def get_symbol_name(symbol: str) -> str:
    """获取品种的中文名称"""
    global FUTURES_NAME_MAP
    if not FUTURES_NAME_MAP:
        FUTURES_NAME_MAP = load_futures_mapping()
    
    # 尝试多种匹配方式
    symbol_lower = symbol.lower()
    if symbol_lower in FUTURES_NAME_MAP:
        return FUTURES_NAME_MAP[symbol_lower]
    
    # 尝试添加 'm' 后缀匹配（如 rb -> rbm）
    if symbol_lower + 'm' in FUTURES_NAME_MAP:
        return FUTURES_NAME_MAP[symbol_lower + 'm']
    
    return symbol


# ==================================================
# MySQL数据库配置
# ==================================================

MYSQL_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}


def get_mysql_connection():
    """获取MySQL数据库连接"""
    return pymysql.connect(**MYSQL_CONFIG)


def build_plain_text_content(signals: List[Dict], prediction_date: str) -> str:
    """构建纯文本格式的预测内容"""
    lines = []
    
    lines.append("=" * 70)
    lines.append("机构持仓预测信号")
    lines.append("=" * 70)
    lines.append(f"预测日期: {prediction_date}")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    if not signals:
        lines.append("今日无推荐信号")
        return '\n'.join(lines)
    
    # 分离多头和空头信号
    long_signals = [s for s in signals if s['direction'] == '做多']
    short_signals = [s for s in signals if s['direction'] == '做空']
    
    # 多头信号
    if long_signals:
        lines.append("-" * 70)
        lines.append(f"做多信号 ({len(long_signals)}个)")
        lines.append("-" * 70)
        lines.append(f"  {'品种':<14} {'概率':<10} {'收盘价':<12} {'国泰进攻':<10} {'连续天数':<10} {'均线多排':<10}")
        for sig in long_signals:
            symbol_name = get_symbol_name(sig['symbol'])
            attack = "是" if sig.get('gtja_long_attack', 0) else "-"
            streak = str(sig.get('gtja_long_streak', 0)) if sig.get('gtja_long_streak', 0) else "-"
            ma_align = "是" if sig.get('ma_align_bull', 0) else "-"
            prob_str = f"{sig['probability']*100:.1f}%"
            lines.append(f"  {symbol_name:<12} {prob_str:<10} {sig['close']:<12.2f} {attack:<10} {streak:<10} {ma_align:<10}")
        lines.append("")
    
    # 空头信号
    if short_signals:
        lines.append("-" * 70)
        lines.append(f"做空信号 ({len(short_signals)}个)")
        lines.append("-" * 70)
        lines.append(f"  {'品种':<14} {'概率':<10} {'收盘价':<12} {'国泰进攻':<10} {'连续天数':<10} {'均线空排':<10}")
        for sig in short_signals:
            symbol_name = get_symbol_name(sig['symbol'])
            attack = "是" if sig.get('gtja_short_attack', 0) else "-"
            streak = str(sig.get('gtja_short_streak', 0)) if sig.get('gtja_short_streak', 0) else "-"
            ma_align = "是" if sig.get('ma_align_bear', 0) else "-"
            prob_str = f"{sig['probability']*100:.1f}%"
            lines.append(f"  {symbol_name:<12} {prob_str:<10} {sig['close']:<12.2f} {attack:<10} {streak:<10} {ma_align:<10}")
        lines.append("")
    
    # 统计摘要
    lines.append("=" * 70)
    lines.append(f"信号统计: 做多 {len(long_signals)} 个, 做空 {len(short_signals)} 个")
    lines.append("=" * 70)
    
    return '\n'.join(lines)


def save_prediction_to_db(signals: List[Dict], prediction_date: str) -> None:
    """
    将预测结果保存到数据库
    
    参数:
        signals: 预测信号列表
        prediction_date: 预测日期（格式：YYYY-MM-DD）
    """
    conn = get_mysql_connection()
    cursor = conn.cursor()
    
    try:
        ctime = int(time.time())  # 秒级时间戳
        title = f"机构持仓预测信号 - {prediction_date}"
        message_type = "institution_position_prediction"
        
        # 构建纯文本格式内容
        prediction_content = build_plain_text_content(signals, prediction_date)
        
        # 插入 news_red_telegraph 表
        insert_news_sql = """
            INSERT INTO news_red_telegraph 
            (ctime, title, content, ai_analysis, message_score, message_label, message_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_news_sql, (
            ctime,
            title,
            prediction_content,
            None,  # ai_analysis
            7,     # message_score
            'hard',  # message_label
            message_type
        ))
        
        # 获取刚插入的记录ID
        news_id = cursor.lastrowid
        
        # 插入 news_process_tracking 表
        insert_tracking_sql = """
            INSERT INTO news_process_tracking 
            (news_id, ctime, is_reviewed, track_day3_done, track_day7_done, track_day14_done, track_day28_done)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_tracking_sql, (
            news_id,
            ctime,
            0,  # is_reviewed
            0,  # track_day3_done
            0,  # track_day7_done
            0,  # track_day14_done
            0   # track_day28_done
        ))
        
        conn.commit()
        print(f"[数据库] 预测结果已保存，news_id: {news_id}")
        
    except Exception as e:
        conn.rollback()
        print(f"[数据库] 保存失败: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

# ==================================================
# 路径配置
# ==================================================
PROJECT_ROOT = Path(__file__).parent.parent.parent
FUTURES_DB = PROJECT_ROOT / "database" / "futures" / "futures.db"
INSTITUTION_DB = PROJECT_ROOT / "database" / "institution" / "institution.db"
MAPPING_FILE = PROJECT_ROOT / "database" / "institution" / "mapping.json"

MODEL_DIR = Path(__file__).parent / "models"
CONFIG_FILE = MODEL_DIR / "config.json"
LONG_MODEL_FILE = MODEL_DIR / "long_model.pkl"
SHORT_MODEL_FILE = MODEL_DIR / "short_model.pkl"


# ==================================================
# 数据加载
# ==================================================

def load_mapping() -> dict:
    """加载期货表名到机构持仓表名的映射"""
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('mappings', {})


def get_futures_data(table_name: str, days: int = 100) -> pd.DataFrame:
    """从期货数据库读取最近N天的价格数据"""
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
        ORDER BY trade_date DESC
        LIMIT {days}
        """
        df = pd.read_sql(sql, conn)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def get_institution_data(variety_name: str, days: int = 100) -> pd.DataFrame:
    """从机构持仓数据库读取最近N天的持仓数据"""
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
        ORDER BY trade_date DESC
        LIMIT {days}
        """
        df = pd.read_sql(sql, conn)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def load_latest_data(min_days: int = 80) -> pd.DataFrame:
    """加载所有品种的最新数据"""
    mapping = load_mapping()
    all_data = []
    
    for futures_table, institution_table in mapping.items():
        df_futures = get_futures_data(futures_table, days=100)
        if df_futures.empty:
            continue
        
        df_institution = get_institution_data(institution_table, days=100)
        if df_institution.empty:
            continue
        
        df = pd.merge(df_futures, df_institution, on='date', how='inner')
        
        if len(df) < min_days:
            continue
        
        df['symbol'] = institution_table
        all_data.append(df)
    
    if not all_data:
        raise ValueError("没有可用的数据！请检查数据库是否已更新。")
    
    df_all = pd.concat(all_data, ignore_index=True)
    df_all = df_all.sort_values(['symbol', 'date']).reset_index(drop=True)
    
    return df_all


# ==================================================
# 特征工程（与 train.py 保持一致）
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


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    生成融合特征：趋势ML完整特征 + 国泰持仓特征
    （与 train.py 中 make_features_fusion 保持一致）
    """
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
        # Part 1: 趋势ML技术特征
        # ========================================
        
        # 1. 价格动量
        for period in [3, 5, 10, 20]:
            df_sym[f'feat_ret_{period}'] = close.pct_change(period)
        df_sym['feat_momentum_accel'] = df_sym['feat_ret_5'] - df_sym['feat_ret_5'].shift(5)
        
        # 2. 突破信号
        for period in [10, 20, 40]:
            rolling_high = high.rolling(period, min_periods=1).max()
            rolling_low = low.rolling(period, min_periods=1).min()
            range_hl = rolling_high - rolling_low
            
            df_sym[f'feat_price_pos_{period}'] = (close - rolling_low) / (range_hl + 1e-6)
            df_sym[f'feat_break_high_{period}'] = (close >= rolling_high.shift(1)).astype(int)
            df_sym[f'feat_break_low_{period}'] = (close <= rolling_low.shift(1)).astype(int)
            df_sym[f'feat_dist_high_{period}'] = (rolling_high - close) / (close + 1e-6)
            df_sym[f'feat_dist_low_{period}'] = (close - rolling_low) / (close + 1e-6)
        
        # 3. 均线系统
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
        
        # 4. 波动率特征
        returns = close.pct_change()
        for period in [5, 10, 20]:
            df_sym[f'feat_vol_{period}'] = returns.rolling(period, min_periods=1).std()
        
        df_sym['feat_vol_contraction'] = df_sym['feat_vol_5'] / (df_sym['feat_vol_20'] + 1e-6)
        df_sym['feat_atr_20'] = calculate_atr(df_sym, period=20)
        df_sym['feat_atr_ratio'] = df_sym['feat_atr_20'] / (close + 1e-6)
        df_sym['feat_atr_change'] = df_sym['feat_atr_20'].pct_change(5)
        
        # 5. 趋势强度
        slope_10, r2_10 = compute_trend_features(close, window=10)
        slope_20, r2_20 = compute_trend_features(close, window=20)
        
        df_sym['feat_trend_slope_10'] = slope_10
        df_sym['feat_trend_r2_10'] = r2_10
        df_sym['feat_trend_slope_20'] = slope_20
        df_sym['feat_trend_r2_20'] = r2_20
        df_sym['feat_trend_score_10'] = slope_10 * r2_10
        df_sym['feat_trend_score_20'] = slope_20 * r2_20
        
        # 6. 成交量特征
        vol_ma_5 = volume.rolling(5, min_periods=1).mean()
        vol_ma_20 = volume.rolling(20, min_periods=1).mean()
        
        df_sym['feat_vol_ratio_5'] = volume / (vol_ma_5 + 1e-6)
        df_sym['feat_vol_ratio_20'] = volume / (vol_ma_20 + 1e-6)
        df_sym['feat_vol_trend'] = vol_ma_5 / (vol_ma_20 + 1e-6)
        df_sym['feat_vol_breakout'] = (
            (volume > vol_ma_20 * 1.5) & 
            (abs(returns) > df_sym['feat_vol_20'])
        ).astype(int)
        
        # 7. 持仓量特征
        oi_ma_20 = oi.rolling(20, min_periods=1).mean()
        df_sym['feat_oi_ratio'] = oi / (oi_ma_20 + 1e-6)
        df_sym['feat_oi_chg_5'] = oi.pct_change(5)
        
        price_up = (close > close.shift(1)).astype(int)
        oi_up = (oi > oi.shift(1)).astype(int)
        df_sym['feat_price_oi_bull'] = (price_up & oi_up).astype(int)
        df_sym['feat_price_oi_bear'] = ((1 - price_up) & oi_up).astype(int)
        
        # 8. K线形态
        bar_range = high - low
        body = abs(close - open_price)
        
        df_sym['feat_body_ratio'] = body / (bar_range + 1e-6)
        df_sym['feat_close_pos'] = (close - low) / (bar_range + 1e-6)
        df_sym['feat_consec_up'] = (close > open_price).rolling(3).sum()
        df_sym['feat_consec_down'] = (close < open_price).rolling(3).sum()
        
        # 9. RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        avg_gain = gain.rolling(14, min_periods=1).mean()
        avg_loss = loss.rolling(14, min_periods=1).mean()
        rs = avg_gain / (avg_loss + 1e-6)
        df_sym['feat_rsi_14'] = 100 - (100 / (1 + rs))
        
        # 10. 布林带
        ma_20 = df_sym['MA_20']
        std_20 = close.rolling(20, min_periods=1).std()
        upper_band = ma_20 + 2 * std_20
        lower_band = ma_20 - 2 * std_20
        
        df_sym['feat_bb_pos'] = (close - lower_band) / (upper_band - lower_band + 1e-6)
        df_sym['feat_bb_break_up'] = (close > upper_band).astype(int)
        df_sym['feat_bb_break_down'] = (close < lower_band).astype(int)
        
        # ========================================
        # Part 2: 国泰君安持仓特征
        # ========================================
        
        total_buy = df_sym['total_buy']
        total_ss = df_sym['total_ss']
        total_buy_chge = df_sym['total_buy_chge']
        total_ss_chge = df_sym['total_ss_chge']
        
        # 净持仓
        net_position = total_buy - total_ss
        net_change = total_buy_chge - total_ss_chge
        net_position_prev = net_position.shift(1)
        
        # 主动进攻信号
        is_long_attack = (net_position > 0) & (net_change > 0)
        is_short_attack = (net_position < 0) & (net_change < 0)
        
        df_sym['feat_gtja_long_attack'] = is_long_attack.astype(int)
        df_sym['feat_gtja_short_attack'] = is_short_attack.astype(int)
        
        # 进攻强度
        df_sym['feat_gtja_long_intensity'] = 0.0
        mask_long_valid = is_long_attack & (net_position_prev.abs() > 100)
        df_sym.loc[mask_long_valid, 'feat_gtja_long_intensity'] = (
            net_change[mask_long_valid] / net_position_prev[mask_long_valid].abs()
        )
        
        df_sym['feat_gtja_short_intensity'] = 0.0
        mask_short_valid = is_short_attack & (net_position_prev.abs() > 100)
        df_sym.loc[mask_short_valid, 'feat_gtja_short_intensity'] = (
            net_change[mask_short_valid].abs() / net_position_prev[mask_short_valid].abs()
        )
        
        # 进攻持续性
        long_attack_group = (is_long_attack != is_long_attack.shift()).cumsum()
        df_sym['feat_gtja_long_streak'] = df_sym.groupby(long_attack_group)['feat_gtja_long_attack'].cumsum()
        
        short_attack_group = (is_short_attack != is_short_attack.shift()).cumsum()
        df_sym['feat_gtja_short_streak'] = df_sym.groupby(short_attack_group)['feat_gtja_short_attack'].cumsum()
        
        # 累计进攻强度
        df_sym['feat_gtja_long_intensity_3d'] = df_sym['feat_gtja_long_intensity'].rolling(3).sum()
        df_sym['feat_gtja_short_intensity_3d'] = df_sym['feat_gtja_short_intensity'].rolling(3).sum()
        
        # 净持仓规模
        df_sym['feat_gtja_net_ratio'] = net_position / (oi + 1e-6)
        
        # 进攻 × 技术共振
        df_sym['feat_gtja_long_with_ma'] = (
            is_long_attack & (df_sym['feat_ma_align_bull'] == 1)
        ).astype(int)
        
        df_sym['feat_gtja_short_with_ma'] = (
            is_short_attack & (df_sym['feat_ma_align_bear'] == 1)
        ).astype(int)
        
        df_sym['feat_gtja_long_with_break'] = (
            is_long_attack & (df_sym['feat_break_high_20'] == 1)
        ).astype(int)
        
        df_sym['feat_gtja_short_with_break'] = (
            is_short_attack & (df_sym['feat_break_low_20'] == 1)
        ).astype(int)
        
        feature_dfs.append(df_sym)
    
    df_feat = pd.concat(feature_dfs, ignore_index=True)
    
    # 处理无穷值
    feature_cols = [col for col in df_feat.columns if col.startswith('feat_')]
    for col in feature_cols:
        df_feat[col] = df_feat[col].replace([np.inf, -np.inf], np.nan)
        df_feat[col] = df_feat[col].clip(-1e10, 1e10)
    
    return df_feat


# ==================================================
# 预测核心
# ==================================================

def load_models():
    """加载模型和配置"""
    if not LONG_MODEL_FILE.exists():
        raise FileNotFoundError(f"多头模型不存在: {LONG_MODEL_FILE}")
    if not SHORT_MODEL_FILE.exists():
        raise FileNotFoundError(f"空头模型不存在: {SHORT_MODEL_FILE}")
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"配置文件不存在: {CONFIG_FILE}")
    
    long_model = joblib.load(LONG_MODEL_FILE)
    short_model = joblib.load(SHORT_MODEL_FILE)
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return long_model, short_model, config


def predict_today(top_n: int = 10) -> List[Dict]:
    """
    预测今日信号
    
    Returns:
        List[Dict]: 按信号强度排序的推荐列表
    """
    # 1. 加载模型
    long_model, short_model, config = load_models()
    feature_cols = config['features']
    signal_percentile = config.get('signal_percentile', 95)
    
    print("=" * 60)
    print(f"每日信号预测 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print(f"模型训练日期: {config.get('train_date', 'N/A')}")
    print(f"信号阈值: Top {100 - signal_percentile:.0f}%")
    
    # 2. 加载最新数据
    print("\n[数据] 加载最新数据...")
    df_all = load_latest_data(min_days=80)
    latest_date = df_all['date'].max()
    print(f"[数据] 最新日期: {latest_date.strftime('%Y-%m-%d')}")
    print(f"[数据] 品种数量: {df_all['symbol'].nunique()}")
    
    # 3. 生成特征
    print("[特征] 计算特征...")
    df_feat = make_features(df_all)
    
    # 4. 取每个品种的最新一条数据
    df_latest = df_feat.sort_values('date').groupby('symbol').tail(1).reset_index(drop=True)
    print(f"[预测] 待预测品种: {len(df_latest)}")
    
    # 5. 检查特征完整性
    missing_cols = set(feature_cols) - set(df_latest.columns)
    if missing_cols:
        print(f"[警告] 缺少特征: {missing_cols}")
        return []
    
    # 6. 填充NaN
    X = df_latest[feature_cols].fillna(0).values
    
    # 7. 预测
    p_long = long_model.predict_proba(X)[:, 1]
    p_short = short_model.predict_proba(X)[:, 1]
    
    # 8. 计算阈值（使用全部预测值的百分位数）
    long_threshold = np.percentile(p_long, signal_percentile)
    short_threshold = np.percentile(p_short, signal_percentile)
    
    # 9. 生成信号
    signals = []
    for i, row in df_latest.iterrows():
        symbol = row['symbol']
        
        # 多头信号
        if p_long[i] >= long_threshold:
            signals.append({
                'symbol': symbol,
                'direction': '做多',
                'probability': float(p_long[i]),
                'close': float(row['close']),
                'date': row['date'].strftime('%Y-%m-%d'),
                'gtja_long_attack': int(row.get('feat_gtja_long_attack', 0)),
                'gtja_long_streak': int(row.get('feat_gtja_long_streak', 0)),
                'ma_align_bull': int(row.get('feat_ma_align_bull', 0)),
                'trend_score': float(row.get('feat_trend_score_20', 0)),
            })
        
        # 空头信号
        if p_short[i] >= short_threshold:
            signals.append({
                'symbol': symbol,
                'direction': '做空',
                'probability': float(p_short[i]),
                'close': float(row['close']),
                'date': row['date'].strftime('%Y-%m-%d'),
                'gtja_short_attack': int(row.get('feat_gtja_short_attack', 0)),
                'gtja_short_streak': int(row.get('feat_gtja_short_streak', 0)),
                'ma_align_bear': int(row.get('feat_ma_align_bear', 0)),
                'trend_score': float(row.get('feat_trend_score_20', 0)),
            })
    
    # 10. 按概率排序
    signals = sorted(signals, key=lambda x: x['probability'], reverse=True)
    
    return signals[:top_n]


def print_signals(signals: List[Dict]) -> None:
    """打印信号列表"""
    if not signals:
        print("\n今日无推荐信号")
        return
    
    # 分离多头和空头信号
    long_signals = [s for s in signals if s['direction'] == '做多']
    short_signals = [s for s in signals if s['direction'] == '做空']
    
    print("\n" + "=" * 70)
    print("今日推荐信号")
    print("=" * 70)
    
    if long_signals:
        print("\n" + "-" * 70)
        print(f"做多信号 ({len(long_signals)}个)")
        print("-" * 70)
        print(f"  {'序号':<6} {'品种':<12} {'概率':<10} {'收盘价':<12} {'国泰进攻':<10} {'连续天数':<10} {'均线多排':<10}")
        for i, sig in enumerate(long_signals, 1):
            symbol_name = get_symbol_name(sig['symbol'])
            attack = "是" if sig.get('gtja_long_attack', 0) else "-"
            streak = str(sig.get('gtja_long_streak', 0)) if sig.get('gtja_long_streak', 0) > 0 else "-"
            ma_ok = "是" if sig.get('ma_align_bull', 0) else "-"
            prob_str = f"{sig['probability']*100:.1f}%"
            print(f"  {i:<6} {symbol_name:<10} {prob_str:<10} {sig['close']:<12.2f} {attack:<10} {streak:<10} {ma_ok:<10}")
    
    if short_signals:
        print("\n" + "-" * 70)
        print(f"做空信号 ({len(short_signals)}个)")
        print("-" * 70)
        print(f"  {'序号':<6} {'品种':<12} {'概率':<10} {'收盘价':<12} {'国泰进攻':<10} {'连续天数':<10} {'均线空排':<10}")
        for i, sig in enumerate(short_signals, 1):
            symbol_name = get_symbol_name(sig['symbol'])
            attack = "是" if sig.get('gtja_short_attack', 0) else "-"
            streak = str(sig.get('gtja_short_streak', 0)) if sig.get('gtja_short_streak', 0) > 0 else "-"
            ma_ok = "是" if sig.get('ma_align_bear', 0) else "-"
            prob_str = f"{sig['probability']*100:.1f}%"
            print(f"  {i:<6} {symbol_name:<10} {prob_str:<10} {sig['close']:<12.2f} {attack:<10} {streak:<10} {ma_ok:<10}")


# ==================================================
# 主程序
# ==================================================

def main():
    """主程序入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='每日信号预测')
    parser.add_argument('--top', type=int, default=10, help='显示前N个信号 (默认: 10)')
    parser.add_argument('--json', action='store_true', help='输出JSON格式')
    args = parser.parse_args()
    
    try:
        signals = predict_today(top_n=args.top)
        
        if args.json:
            print(json.dumps(signals, ensure_ascii=False, indent=2))
        else:
            print_signals(signals)
            print(f"\n预测完成，共 {len(signals)} 个信号")
        
        # 保存预测结果到数据库
        if signals:
            prediction_date = signals[0].get('date', datetime.now().strftime('%Y-%m-%d'))
            print("\n[步骤] 保存预测结果到数据库...")
            save_prediction_to_db(signals, prediction_date)
        else:
            print("\n无信号，跳过数据库保存")
    
    except FileNotFoundError as e:
        print(f"[错误] {e}")
        print("请先运行 train.py 训练模型")
    except Exception as e:
        print(f"[错误] 预测失败: {e}")
        raise


if __name__ == "__main__":
    main()

