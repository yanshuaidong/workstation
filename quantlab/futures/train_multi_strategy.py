#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多策略模型训练 - 同时训练3组参数的模型

策略组：
1. 大行情型 - 交易间隔2.9天，盈亏比2.57最高
2. 高阈值型 - 回撤4.6%最低，盈亏比2.47
3. 超严格型 - 胜率46.6%最高，夏普2.78最高

作者：量化工程师
"""

import warnings
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, List
import json

import numpy as np
import pandas as pd

from futures_trend_ml import (
    StrategyConfig,
    load_history_from_db,
    assign_labels_v2,
    make_features_v2,
    split_data_by_year,
    get_feature_columns,
    train_model,
    save_model,
)

warnings.filterwarnings('ignore')


# ==================================================
# 策略配置
# ==================================================

STRATEGY_CONFIGS = {
    "big_trend": {
        "name": "大行情型",
        "description": "交易间隔2.9天，盈亏比2.57最高，适合捕捉大趋势",
        "config": {
            "future_days": 15,
            "long_threshold": 0.10,      # 10% 收益阈值
            "short_threshold": 0.10,
            "signal_percentile": 99,     # top 1%
            "max_holding_days": 25,
            "stop_loss_pct": 0.04,       # 4% 止损
            "take_profit_pct": 0.15,     # 15% 止盈
            "trailing_stop_pct": 0.03,
            "max_positions": 1
        }
    },
    "high_threshold": {
        "name": "高阈值型",
        "description": "回撤4.6%最低，盈亏比2.47，风险控制最佳",
        "config": {
            "future_days": 10,
            "long_threshold": 0.08,      # 8% 收益阈值
            "short_threshold": 0.08,
            "signal_percentile": 99,     # top 1%
            "max_holding_days": 20,
            "stop_loss_pct": 0.035,      # 3.5% 止损
            "take_profit_pct": 0.12,     # 12% 止盈
            "trailing_stop_pct": 0.03,
            "max_positions": 1
        }
    },
    "strict": {
        "name": "超严格型",
        "description": "胜率46.6%最高，夏普2.78最高，信号最精准",
        "config": {
            "future_days": 7,
            "long_threshold": 0.07,      # 7% 收益阈值
            "short_threshold": 0.07,
            "signal_percentile": 99.7,   # top 0.3%
            "max_holding_days": 20,
            "stop_loss_pct": 0.03,       # 3% 止损
            "take_profit_pct": 0.10,     # 10% 止盈
            "trailing_stop_pct": 0.025,
            "max_positions": 1
        }
    }
}


def train_strategy(
    df_all: pd.DataFrame,
    strategy_key: str,
    strategy_info: Dict,
    model_dir: Path
) -> Dict[str, Any]:
    """训练单个策略"""
    print(f"\n{'='*70}")
    print(f"训练策略: {strategy_info['name']}")
    print(f"描述: {strategy_info['description']}")
    print(f"{'='*70}")
    
    cfg = strategy_info['config']
    
    # 创建配置
    config = StrategyConfig(
        future_days=cfg['future_days'],
        long_threshold=cfg['long_threshold'],
        short_threshold=cfg['short_threshold'],
        warmup_period=60,
        train_end='2022-12-31',
        valid_end='2023-12-31',
        signal_percentile=cfg['signal_percentile'],
        max_holding_days=cfg['max_holding_days'],
        stop_loss_pct=cfg['stop_loss_pct'],
        take_profit_pct=cfg['take_profit_pct'],
        trailing_stop_pct=cfg['trailing_stop_pct'],
        max_positions=cfg['max_positions'],
        position_size=0.2
    )
    
    print(f"\n参数设置:")
    print(f"  - 预测周期: {config.future_days} 天")
    print(f"  - 收益阈值: {config.long_threshold*100:.1f}%")
    print(f"  - 信号百分位: {config.signal_percentile}%")
    print(f"  - 止盈: {config.take_profit_pct*100:.1f}%")
    print(f"  - 止损: {config.stop_loss_pct*100:.1f}%")
    
    # 生成标签
    df_labeled = assign_labels_v2(df_all.copy(), config, verbose=True)
    
    # 特征工程
    df_feat = make_features_v2(df_labeled, warmup_period=config.warmup_period)
    
    # 数据集划分
    df_train, df_valid, df_test = split_data_by_year(
        df_feat,
        train_end=config.train_end,
        valid_end=config.valid_end
    )
    
    # 获取特征列
    feature_cols = get_feature_columns(df_feat)
    
    # 训练多头模型
    long_model, long_threshold = train_model(
        df_train, df_valid, feature_cols,
        label_col='label_long',
        model_name=f'{strategy_info["name"]}-多头'
    )
    
    # 训练空头模型
    short_model, short_threshold = train_model(
        df_train, df_valid, feature_cols,
        label_col='label_short',
        model_name=f'{strategy_info["name"]}-空头'
    )
    
    # 计算测试集阈值
    from futures_trend_ml import predict_proba
    p_long_test = predict_proba(df_test, long_model, feature_cols)
    p_short_test = predict_proba(df_test, short_model, feature_cols)
    
    test_long_threshold = np.percentile(p_long_test, config.signal_percentile)
    test_short_threshold = np.percentile(p_short_test, config.signal_percentile)
    
    print(f"\n[阈值] 测试集多头阈值 (top {100-config.signal_percentile:.1f}%): {test_long_threshold:.4f}")
    print(f"[阈值] 测试集空头阈值 (top {100-config.signal_percentile:.1f}%): {test_short_threshold:.4f}")
    
    # 保存模型
    strategy_model_dir = model_dir / strategy_key
    strategy_model_dir.mkdir(parents=True, exist_ok=True)
    
    save_model(long_model, str(strategy_model_dir / 'long_model.pkl'))
    save_model(short_model, str(strategy_model_dir / 'short_model.pkl'))
    
    # 保存策略配置和阈值
    strategy_meta = {
        'name': strategy_info['name'],
        'description': strategy_info['description'],
        'config': cfg,
        'thresholds': {
            'long': float(test_long_threshold),
            'short': float(test_short_threshold)
        },
        'feature_cols': feature_cols
    }
    
    with open(strategy_model_dir / 'meta.json', 'w', encoding='utf-8') as f:
        json.dump(strategy_meta, f, ensure_ascii=False, indent=2)
    
    print(f"\n[保存] 模型已保存至: {strategy_model_dir}")
    
    return strategy_meta


def main():
    """主程序"""
    print("=" * 70)
    print("多策略模型训练系统")
    print("=" * 70)
    print("\n将训练以下3组策略:")
    for key, info in STRATEGY_CONFIGS.items():
        print(f"  - {info['name']}: {info['description']}")
    
    # 路径配置
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / 'database' / 'futures' / 'futures.db'
    model_dir = script_dir / 'models' / 'multi_strategy'
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载数据（只加载一次）
    print("\n" + "=" * 70)
    print("数据加载")
    print("=" * 70)
    df_all = load_history_from_db(str(db_path), min_days=250)
    
    # 训练每个策略
    all_meta = {}
    for strategy_key, strategy_info in STRATEGY_CONFIGS.items():
        meta = train_strategy(df_all.copy(), strategy_key, strategy_info, model_dir)
        all_meta[strategy_key] = meta
    
    # 保存总配置
    with open(model_dir / 'strategies.json', 'w', encoding='utf-8') as f:
        json.dump(all_meta, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print("训练完成！")
    print("=" * 70)
    print(f"\n模型保存目录: {model_dir}")
    print("\n各策略阈值汇总:")
    for key, meta in all_meta.items():
        print(f"\n  {meta['name']}:")
        print(f"    - 多头阈值: {meta['thresholds']['long']:.4f}")
        print(f"    - 空头阈值: {meta['thresholds']['short']:.4f}")
    
    print("\n接下来运行 daily_signal_scanner_multi.py 进行每日信号扫描")


if __name__ == "__main__":
    main()

