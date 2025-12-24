#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货多策略每日预测

每日运行，使用3个策略模型分别预测：
1. 大行情型 - 交易间隔2.9天，盈亏比2.57最高
2. 高阈值型 - 回撤4.6%最低，盈亏比2.47
3. 超严格型 - 胜率46.6%最高，夏普2.78最高

作者：量化工程师
"""

import json
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import joblib
import numpy as np
import pandas as pd
import pymysql

from futures_trend_ml import (
    load_history_from_db,
    make_features_v2,
    get_feature_columns,
)

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
                # 映射文件中的 key 就是 symbol（如 rbm, cum）
                name = info.get('name', symbol)
                # 去掉"主连"后缀，使名称更简洁
                if name.endswith('主连'):
                    name = name[:-2]
                symbol_to_name[symbol.lower()] = name
        except Exception as e:
            print(f"[警告] 加载品种映射文件失败: {e}")
    
    return symbol_to_name


# 全局变量，存储品种映射
FUTURES_NAME_MAP: Dict[str, str] = {}


def get_symbol_name(symbol: str) -> str:
    """
    获取品种的中文名称
    
    参数:
        symbol: 品种代码（如 rbm, cum）
    返回:
        中文名称，如果没找到则返回原代码
    """
    global FUTURES_NAME_MAP
    if not FUTURES_NAME_MAP:
        FUTURES_NAME_MAP = load_futures_mapping()
    
    return FUTURES_NAME_MAP.get(symbol.lower(), symbol)


# ==================================================
# 数据库配置
# ==================================================

DB_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}


def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)


def build_plain_text_content(
    all_signals: Dict[str, pd.DataFrame],
    strategies: Dict[str, Dict[str, Any]],
    latest_date: pd.Timestamp,
    df_consensus: pd.DataFrame
) -> str:
    """构建纯文本格式的预测内容"""
    lines = []
    
    lines.append("=" * 70)
    lines.append("期货多策略预测信号")
    lines.append("=" * 70)
    lines.append(f"预测日期: {latest_date.strftime('%Y-%m-%d')}")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # 统计信号
    total_long = 0
    total_short = 0
    
    for strategy_key in STRATEGY_ORDER:
        if strategy_key not in all_signals:
            continue
        
        df_signals = all_signals[strategy_key]
        meta = strategies[strategy_key]['meta']
        df_today = df_signals[df_signals['date'] == latest_date]
        
        long_count = df_today['long_signal'].sum()
        short_count = df_today['short_signal'].sum()
        total_long += long_count
        total_short += short_count
        
        lines.append("-" * 70)
        lines.append(f"[{meta['name']}] {SIGNAL_STRENGTH[strategy_key]}")
        lines.append(f"  说明: {meta['description']}")
        lines.append(f"  阈值: 多头>{meta['thresholds']['long']:.4f}, 空头>{meta['thresholds']['short']:.4f}")
        lines.append("-" * 70)
        
        if len(df_today) == 0:
            lines.append("  无信号")
            lines.append("")
            continue
        
        # 多头信号
        df_long = df_today[df_today['long_signal']].sort_values('p_long', ascending=False)
        if len(df_long) > 0:
            lines.append(f"  多头信号 ({len(df_long)}个):")
            lines.append(f"  {'品种':<14} {'概率':<10} {'收盘价':<12} {'强度':<10}")
            for _, row in df_long.iterrows():
                strength_pct = f"{row['long_strength']*100:.1f}%"
                symbol_name = get_symbol_name(row['symbol'])
                lines.append(f"  {symbol_name:<12} {row['p_long']:<10.4f} {row['close']:<12.2f} {strength_pct:<10}")
            lines.append("")
        
        # 空头信号
        df_short = df_today[df_today['short_signal']].sort_values('p_short', ascending=False)
        if len(df_short) > 0:
            lines.append(f"  空头信号 ({len(df_short)}个):")
            lines.append(f"  {'品种':<14} {'概率':<10} {'收盘价':<12} {'强度':<10}")
            for _, row in df_short.iterrows():
                strength_pct = f"{row['short_strength']*100:.1f}%"
                symbol_name = get_symbol_name(row['symbol'])
                lines.append(f"  {symbol_name:<12} {row['p_short']:<10.4f} {row['close']:<12.2f} {strength_pct:<10}")
            lines.append("")
    
    # 共识信号
    if len(df_consensus) > 0:
        lines.append("=" * 70)
        lines.append("多策略共识信号 (2个以上策略同时发出)")
        lines.append("=" * 70)
        lines.append(f"  {'品种':<14} {'方向':<8} {'共识数':<8} {'策略':<30}")
        for _, row in df_consensus.iterrows():
            symbol_name = get_symbol_name(row['symbol'])
            strategies_cn = get_strategy_names_cn(row['strategies'])
            lines.append(f"  {symbol_name:<12} {row['direction']:<8} {row['num_strategies']:<8} {strategies_cn}")
        lines.append("")
    
    # 统计摘要
    lines.append("=" * 70)
    lines.append(f"信号统计: 多头 {total_long} 个, 空头 {total_short} 个")
    lines.append("=" * 70)
    
    return '\n'.join(lines)


def save_prediction_to_db(
    all_signals: Dict[str, pd.DataFrame],
    strategies: Dict[str, Dict[str, Any]],
    latest_date: pd.Timestamp,
    df_consensus: pd.DataFrame
) -> None:
    """
    将预测结果保存到数据库
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        ctime = int(time.time())  # 秒级时间戳
        prediction_date = latest_date.strftime('%Y-%m-%d')
        title = f"期货多策略预测信号 - {prediction_date}"
        message_type = "futures_multi_strategy_prediction"
        
        # 构建纯文本格式内容
        prediction_content = build_plain_text_content(all_signals, strategies, latest_date, df_consensus)
        
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
# 配置
# ==================================================

# 策略顺序（按信号严格程度排序）
STRATEGY_ORDER = ['strict', 'high_threshold', 'big_trend']

# 信号强度描述
SIGNAL_STRENGTH = {
    'strict': '[高置信]',
    'high_threshold': '[中置信]',
    'big_trend': '[趋势型]'
}

# 策略中文名称映射
STRATEGY_NAME_MAP = {
    'strict': '超严格型',
    'high_threshold': '高阈值型',
    'big_trend': '大行情型'
}


def get_strategy_names_cn(strategies_str: str) -> str:
    """
    将策略英文名转换为中文名
    
    参数:
        strategies_str: 逗号分隔的策略英文名，如 "strict, high_threshold"
    返回:
        中文名称，如 "超严格型, 高阈值型"
    """
    strategy_keys = [s.strip() for s in strategies_str.split(',')]
    cn_names = [STRATEGY_NAME_MAP.get(key, key) for key in strategy_keys]
    return ', '.join(cn_names)


# ==================================================
# 模型加载
# ==================================================

def load_strategy_models(model_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    加载所有策略模型和配置
    
    返回:
        {strategy_key: {'long_model': model, 'short_model': model, 'meta': dict}}
    """
    strategies = {}
    
    # 加载总配置
    strategies_json = model_dir / 'strategies.json'
    if not strategies_json.exists():
        raise FileNotFoundError(f"未找到策略配置文件: {strategies_json}")
    
    with open(strategies_json, 'r', encoding='utf-8') as f:
        all_meta = json.load(f)
    
    for strategy_key in all_meta.keys():
        strategy_dir = model_dir / strategy_key
        
        if not strategy_dir.exists():
            print(f"[警告] 策略目录不存在: {strategy_dir}")
            continue
        
        # 加载模型
        long_model_path = strategy_dir / 'long_model.pkl'
        short_model_path = strategy_dir / 'short_model.pkl'
        meta_path = strategy_dir / 'meta.json'
        
        if not all(p.exists() for p in [long_model_path, short_model_path, meta_path]):
            print(f"[警告] 策略 {strategy_key} 文件不完整，跳过")
            continue
        
        long_model = joblib.load(long_model_path)
        short_model = joblib.load(short_model_path)
        
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        strategies[strategy_key] = {
            'long_model': long_model,
            'short_model': short_model,
            'meta': meta
        }
        
        print(f"[加载] {meta['name']} 模型加载完成")
    
    return strategies


# ==================================================
# 预测
# ==================================================

def predict_signals(
    df_latest: pd.DataFrame,
    strategies: Dict[str, Dict[str, Any]],
    feature_cols: List[str]
) -> Dict[str, pd.DataFrame]:
    """
    使用所有策略进行预测
    
    参数:
        df_latest: 最新数据（已包含特征）
        strategies: 策略模型字典
        feature_cols: 特征列名
        
    返回:
        {strategy_key: 信号DataFrame}
    """
    all_signals = {}
    
    for strategy_key, strategy_data in strategies.items():
        meta = strategy_data['meta']
        long_model = strategy_data['long_model']
        short_model = strategy_data['short_model']
        
        # 获取阈值
        long_threshold = meta['thresholds']['long']
        short_threshold = meta['thresholds']['short']
        
        # 预测概率
        X = df_latest[feature_cols].values
        p_long = long_model.predict_proba(X)[:, 1]
        p_short = short_model.predict_proba(X)[:, 1]
        
        # 筛选信号
        df_pred = df_latest[['date', 'symbol', 'close', 'volume']].copy()
        df_pred['p_long'] = p_long
        df_pred['p_short'] = p_short
        df_pred['long_threshold'] = long_threshold
        df_pred['short_threshold'] = short_threshold
        
        # 多头信号
        df_pred['long_signal'] = p_long >= long_threshold
        # 空头信号
        df_pred['short_signal'] = p_short >= short_threshold
        
        # 只保留有信号的
        df_signals = df_pred[df_pred['long_signal'] | df_pred['short_signal']].copy()
        
        # 添加信号类型
        def get_signal_type(row):
            if row['long_signal'] and row['short_signal']:
                return '多空' if row['p_long'] > row['p_short'] else '空多'
            elif row['long_signal']:
                return '多头'
            else:
                return '空头'
        
        df_signals['signal_type'] = df_signals.apply(get_signal_type, axis=1)
        
        # 计算信号强度（概率超过阈值的比例）
        df_signals['long_strength'] = (df_signals['p_long'] - long_threshold) / (1 - long_threshold)
        df_signals['short_strength'] = (df_signals['p_short'] - short_threshold) / (1 - short_threshold)
        
        all_signals[strategy_key] = df_signals
    
    return all_signals


def get_latest_data(db_path: str, lookback_days: int = 120) -> pd.DataFrame:
    """
    获取最新数据用于预测
    
    参数:
        db_path: 数据库路径
        lookback_days: 回溯天数（用于特征计算）
    """
    # 加载所有数据
    df_all = load_history_from_db(db_path, min_days=lookback_days)
    
    # 只保留最近 lookback_days 的数据
    max_date = df_all['date'].max()
    cutoff_date = max_date - pd.Timedelta(days=lookback_days)
    df_recent = df_all[df_all['date'] >= cutoff_date].copy()
    
    return df_recent


# ==================================================
# 输出格式化
# ==================================================

def format_signal_output(
    all_signals: Dict[str, pd.DataFrame],
    strategies: Dict[str, Dict[str, Any]],
    latest_date: pd.Timestamp
) -> str:
    """格式化输出信号"""
    lines = []
    lines.append("=" * 70)
    lines.append(f"期货多策略预测信号 - {latest_date.strftime('%Y-%m-%d')}")
    lines.append("=" * 70)
    
    # 统计各策略信号数量
    total_long = 0
    total_short = 0
    
    for strategy_key in STRATEGY_ORDER:
        if strategy_key not in all_signals:
            continue
        
        df_signals = all_signals[strategy_key]
        meta = strategies[strategy_key]['meta']
        
        # 只看最新日期的信号
        df_today = df_signals[df_signals['date'] == latest_date]
        
        long_count = df_today['long_signal'].sum()
        short_count = df_today['short_signal'].sum()
        total_long += long_count
        total_short += short_count
        
        lines.append(f"\n{'─' * 70}")
        lines.append(f"【{meta['name']}】 {SIGNAL_STRENGTH[strategy_key]}")
        lines.append(f"   {meta['description']}")
        lines.append(f"   阈值: 多头>{meta['thresholds']['long']:.4f}, 空头>{meta['thresholds']['short']:.4f}")
        lines.append(f"{'─' * 70}")
        
        if len(df_today) == 0:
            lines.append("   无信号")
            continue
        
        # 分别输出多头和空头信号
        df_long = df_today[df_today['long_signal']].sort_values('p_long', ascending=False)
        df_short = df_today[df_today['short_signal']].sort_values('p_short', ascending=False)
        
        if len(df_long) > 0:
            lines.append(f"\n   多头信号 ({len(df_long)}个):")
            lines.append(f"      {'品种':<12} {'概率':<10} {'价格':<12} {'强度':<10}")
            for _, row in df_long.iterrows():
                strength_pct = f"{row['long_strength']*100:.1f}%"
                symbol_name = get_symbol_name(row['symbol'])
                lines.append(f"      {symbol_name:<10} {row['p_long']:<10.4f} {row['close']:<12.2f} {strength_pct:<10}")
        
        if len(df_short) > 0:
            lines.append(f"\n   空头信号 ({len(df_short)}个):")
            lines.append(f"      {'品种':<12} {'概率':<10} {'价格':<12} {'强度':<10}")
            for _, row in df_short.iterrows():
                strength_pct = f"{row['short_strength']*100:.1f}%"
                symbol_name = get_symbol_name(row['symbol'])
                lines.append(f"      {symbol_name:<10} {row['p_short']:<10.4f} {row['close']:<12.2f} {strength_pct:<10}")
    
    lines.append(f"\n{'=' * 70}")
    lines.append(f"信号统计: 多头 {total_long} 个, 空头 {total_short} 个")
    lines.append("=" * 70)
    
    return '\n'.join(lines)


def get_consensus_signals(
    all_signals: Dict[str, pd.DataFrame],
    latest_date: pd.Timestamp,
    min_strategies: int = 2
) -> pd.DataFrame:
    """
    获取多策略共识信号（多个策略同时发出信号的品种）
    
    参数:
        all_signals: 各策略信号
        latest_date: 最新日期
        min_strategies: 最少需要多少个策略同时发出信号
    """
    # 收集所有策略的信号
    long_votes = {}  # symbol -> [strategy_keys]
    short_votes = {}
    
    for strategy_key, df_signals in all_signals.items():
        df_today = df_signals[df_signals['date'] == latest_date]
        
        for _, row in df_today.iterrows():
            symbol = row['symbol']
            
            if row['long_signal']:
                if symbol not in long_votes:
                    long_votes[symbol] = []
                long_votes[symbol].append(strategy_key)
            
            if row['short_signal']:
                if symbol not in short_votes:
                    short_votes[symbol] = []
                short_votes[symbol].append(strategy_key)
    
    # 筛选共识信号
    consensus = []
    
    for symbol, strategies_list in long_votes.items():
        if len(strategies_list) >= min_strategies:
            consensus.append({
                'symbol': symbol,
                'direction': '多头',
                'num_strategies': len(strategies_list),
                'strategies': ', '.join(strategies_list)
            })
    
    for symbol, strategies_list in short_votes.items():
        if len(strategies_list) >= min_strategies:
            consensus.append({
                'symbol': symbol,
                'direction': '空头',
                'num_strategies': len(strategies_list),
                'strategies': ', '.join(strategies_list)
            })
    
    df_consensus = pd.DataFrame(consensus)
    if len(df_consensus) > 0:
        df_consensus = df_consensus.sort_values('num_strategies', ascending=False)
    
    return df_consensus


# ==================================================
# 主程序
# ==================================================

def main():
    """主程序入口"""
    print("=" * 70)
    print("期货多策略每日预测")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 路径配置
    script_dir = Path(__file__).parent
    db_path = script_dir.parent.parent / 'database' / 'futures' / 'futures.db'
    model_dir = script_dir / 'models' / 'multi_strategy'
    output_dir = script_dir / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 检查数据库
    if not db_path.exists():
        print(f"[错误] 数据库不存在: {db_path}")
        return
    
    # 检查模型目录
    if not model_dir.exists():
        print(f"[错误] 模型目录不存在: {model_dir}")
        print("请先运行 train_multi_strategy.py 训练模型")
        return
    
    # 1. 加载策略模型
    print("\n[步骤1] 加载策略模型...")
    try:
        strategies = load_strategy_models(model_dir)
    except FileNotFoundError as e:
        print(f"[错误] {e}")
        return
    
    if not strategies:
        print("[错误] 没有可用的策略模型")
        return
    
    print(f"成功加载 {len(strategies)} 个策略")
    
    # 2. 加载最新数据
    print("\n[步骤2] 加载最新数据...")
    df_recent = get_latest_data(str(db_path), lookback_days=120)
    latest_date = df_recent['date'].max()
    print(f"最新数据日期: {latest_date.strftime('%Y-%m-%d')}")
    
    # 3. 生成特征
    print("\n[步骤3] 生成特征...")
    df_feat = make_features_v2(df_recent, warmup_period=60, for_prediction=True)
    feature_cols = get_feature_columns(df_feat)
    print(f"特征数量: {len(feature_cols)}")
    
    # 只保留最新日期的数据用于预测
    df_latest = df_feat[df_feat['date'] == latest_date].copy()
    print(f"待预测品种数: {len(df_latest)}")
    
    if len(df_latest) == 0:
        print("[错误] 最新日期没有可用数据")
        return
    
    # 4. 预测
    print("\n[步骤4] 多策略预测...")
    all_signals = predict_signals(df_latest, strategies, feature_cols)
    
    # 5. 输出结果
    print("\n[步骤5] 输出预测结果...")
    output_text = format_signal_output(all_signals, strategies, latest_date)
    print(output_text)
    
    # 6. 共识信号
    df_consensus = get_consensus_signals(all_signals, latest_date, min_strategies=2)
    if len(df_consensus) > 0:
        print(f"\n{'=' * 70}")
        print("多策略共识信号（2个以上策略同时发出）")
        print("=" * 70)
        print(f"  {'品种':<12} {'方向':<6} {'共识数':<8} {'策略':<30}")
        for _, row in df_consensus.iterrows():
            symbol_name = get_symbol_name(row['symbol'])
            strategies_cn = get_strategy_names_cn(row['strategies'])
            print(f"  {symbol_name:<10} {row['direction']:<6} {row['num_strategies']:<8} {strategies_cn}")
    else:
        print("\n暂无多策略共识信号")
    
    # 7. 保存预测结果到数据库
    print("\n[步骤6] 保存预测结果到数据库...")
    save_prediction_to_db(all_signals, strategies, latest_date, df_consensus)
    
    print("\n" + "=" * 70)
    print("预测完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()

