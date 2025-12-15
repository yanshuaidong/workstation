#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数优化测试 V2 - 极低频交易参数

目标：
1. 日均交易 0.2-0.33 笔（3-5天交易一次）
2. 捕捉更大的单边行情
3. 适合散户的低频策略
"""

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd

# 导入主策略模块
from futures_trend_ml import (
    StrategyConfig,
    load_history_from_db,
    assign_labels_v2,
    make_features_v2,
    split_data_by_year,
    get_feature_columns,
    train_model,
    predict_proba,
    backtest_v2,
    analyze_backtest_results,
)

warnings.filterwarnings('ignore')


@dataclass
class ParamSet:
    """参数组合"""
    name: str
    future_days: int = 5
    long_threshold: float = 0.03
    short_threshold: float = 0.03
    signal_percentile: float = 95
    max_holding_days: int = 10
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.05
    trailing_stop_pct: float = 0.015
    max_positions: int = 5
    position_size: float = 0.2


def run_backtest_with_params(df_all: pd.DataFrame, params: ParamSet) -> Dict[str, Any]:
    """使用指定参数运行回测"""
    print(f"\n{'='*60}")
    print(f"参数组: {params.name}")
    print(f"{'='*60}")
    
    # 创建配置
    config = StrategyConfig(
        future_days=params.future_days,
        long_threshold=params.long_threshold,
        short_threshold=params.short_threshold,
        warmup_period=60,
        train_end='2022-12-31',
        valid_end='2023-12-31',
        signal_percentile=params.signal_percentile,
        max_holding_days=params.max_holding_days,
        stop_loss_pct=params.stop_loss_pct,
        take_profit_pct=params.take_profit_pct,
        trailing_stop_pct=params.trailing_stop_pct,
        max_positions=params.max_positions,
        position_size=params.position_size
    )
    
    print(f"\n参数设置:")
    print(f"  - 预测周期: {params.future_days} 天")
    print(f"  - 收益阈值: {params.long_threshold*100:.1f}%")
    print(f"  - 信号百分位: {params.signal_percentile}%")
    print(f"  - 止盈: {params.take_profit_pct*100:.1f}%")
    print(f"  - 止损: {params.stop_loss_pct*100:.1f}%")
    print(f"  - 最大持仓天数: {params.max_holding_days}")
    print(f"  - 最大持仓数量: {params.max_positions}")
    
    # 生成标签
    df_labeled = assign_labels_v2(df_all, config, verbose=False)
    
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
    long_model, _ = train_model(
        df_train, df_valid, feature_cols,
        label_col='label_long',
        model_name='多头模型'
    )
    
    # 训练空头模型
    short_model, _ = train_model(
        df_train, df_valid, feature_cols,
        label_col='label_short',
        model_name='空头模型'
    )
    
    # 测试集预测
    p_long = predict_proba(df_test, long_model, feature_cols)
    p_short = predict_proba(df_test, short_model, feature_cols)
    
    # 使用严格阈值
    test_long_threshold = np.percentile(p_long, params.signal_percentile)
    test_short_threshold = np.percentile(p_short, params.signal_percentile)
    
    print(f"\n[回测] 多头阈值: {test_long_threshold:.4f}")
    print(f"[回测] 空头阈值: {test_short_threshold:.4f}")
    
    # 回测
    trades, equity = backtest_v2(
        df_test, p_long, p_short, config,
        long_threshold=test_long_threshold,
        short_threshold=test_short_threshold
    )
    
    # 分析结果
    results = analyze_backtest_results(trades, equity)
    
    # 计算每日交易频率
    if len(equity) > 0:
        trading_days = len(equity)
        trades_per_day = len(trades) / trading_days if trading_days > 0 else 0
        days_per_trade = trading_days / len(trades) if len(trades) > 0 else float('inf')
    else:
        trading_days = 0
        trades_per_day = 0
        days_per_trade = float('inf')
    
    # 汇总结果
    summary = {
        'param_name': params.name,
        'future_days': params.future_days,
        'return_threshold': params.long_threshold,
        'signal_percentile': params.signal_percentile,
        'take_profit': params.take_profit_pct,
        'max_holding_days': params.max_holding_days,
        'max_positions': params.max_positions,
        'total_trades': len(trades),
        'trading_days': trading_days,
        'trades_per_day': trades_per_day,
        'days_per_trade': days_per_trade,  # 新增：每笔交易间隔天数
        'win_rate': results.get('胜率', 0),
        'profit_factor': results.get('盈亏比', 0),
        'total_return': results.get('累计收益', 0),
        'annual_return': results.get('年化收益', 0),
        'max_drawdown': results.get('最大回撤', 0),
        'sharpe_ratio': results.get('夏普比率', 0),
        'avg_holding_days': results.get('平均持仓天数', 0),
        'long_trades': results.get('多头交易', 0),
        'short_trades': results.get('空头交易', 0),
        'long_win_rate': results.get('多头胜率', 0),
        'short_win_rate': results.get('空头胜率', 0),
    }
    
    return summary


def print_comparison_table(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """打印对比表格"""
    df = pd.DataFrame(results)
    
    # 格式化显示
    print("\n" + "=" * 120)
    print("参数对比结果汇总（极低频策略）")
    print("=" * 120)
    
    # 选择关键指标
    key_cols = [
        'param_name', 'total_trades', 'days_per_trade', 'win_rate', 
        'profit_factor', 'total_return', 'annual_return', 'max_drawdown', 
        'sharpe_ratio', 'avg_holding_days'
    ]
    
    df_display = df[key_cols].copy()
    
    # 格式化
    df_display['win_rate'] = df_display['win_rate'].apply(lambda x: f"{x*100:.1f}%")
    df_display['profit_factor'] = df_display['profit_factor'].apply(lambda x: f"{x:.2f}")
    df_display['total_return'] = df_display['total_return'].apply(lambda x: f"{x*100:.1f}%")
    df_display['annual_return'] = df_display['annual_return'].apply(lambda x: f"{x*100:.1f}%")
    df_display['max_drawdown'] = df_display['max_drawdown'].apply(lambda x: f"{x*100:.1f}%")
    df_display['sharpe_ratio'] = df_display['sharpe_ratio'].apply(lambda x: f"{x:.2f}")
    df_display['days_per_trade'] = df_display['days_per_trade'].apply(lambda x: f"{x:.1f}天")
    df_display['avg_holding_days'] = df_display['avg_holding_days'].apply(lambda x: f"{x:.1f}")
    
    # 重命名列
    df_display.columns = [
        '参数组', '总交易', '交易间隔', '胜率', '盈亏比',
        '累计收益', '年化收益', '最大回撤', '夏普比率', '持仓天数'
    ]
    
    print(df_display.to_string(index=False))
    
    return df


def main():
    """主函数"""
    print("=" * 60)
    print("期货策略参数优化 V2 - 极低频交易")
    print("目标：3-5天交易一次")
    print("=" * 60)
    
    # 数据库路径
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / 'database' / 'futures' / 'futures.db'
    
    # 加载数据（只加载一次）
    print("\n[数据加载]...")
    df_all = load_history_from_db(str(db_path), min_days=250)
    
    # 定义极低频参数组合
    param_sets = [
        # 基准：之前的精选型
        ParamSet(
            name="精选型(基准)",
            future_days=7,
            long_threshold=0.05,
            short_threshold=0.05,
            signal_percentile=99,
            max_holding_days=15,
            stop_loss_pct=0.025,
            take_profit_pct=0.08,
            trailing_stop_pct=0.02,
            max_positions=2
        ),
        
        # 极低频1：只持1个仓位
        ParamSet(
            name="单仓精选",
            future_days=7,
            long_threshold=0.06,
            short_threshold=0.06,
            signal_percentile=99.5,   # top 0.5%
            max_holding_days=20,
            stop_loss_pct=0.03,
            take_profit_pct=0.10,
            trailing_stop_pct=0.025,
            max_positions=1           # 只持1个仓位
        ),
        
        # 极低频2：更高阈值
        ParamSet(
            name="高阈值型",
            future_days=10,
            long_threshold=0.08,      # 8%收益阈值
            short_threshold=0.08,
            signal_percentile=99,
            max_holding_days=20,
            stop_loss_pct=0.035,
            take_profit_pct=0.12,
            trailing_stop_pct=0.03,
            max_positions=1
        ),
        
        # 极低频3：超严格信号
        ParamSet(
            name="超严格型",
            future_days=7,
            long_threshold=0.07,
            short_threshold=0.07,
            signal_percentile=99.7,   # top 0.3%
            max_holding_days=20,
            stop_loss_pct=0.03,
            take_profit_pct=0.10,
            trailing_stop_pct=0.025,
            max_positions=1
        ),
        
        # 极低频4：长周期大行情
        ParamSet(
            name="大行情型",
            future_days=15,
            long_threshold=0.10,      # 10%收益阈值
            short_threshold=0.10,
            signal_percentile=99,
            max_holding_days=25,
            stop_loss_pct=0.04,
            take_profit_pct=0.15,
            trailing_stop_pct=0.03,
            max_positions=1
        ),
        
        # 极低频5：平衡型（稍宽松但仍低频）
        ParamSet(
            name="平衡低频",
            future_days=10,
            long_threshold=0.06,
            short_threshold=0.06,
            signal_percentile=99.3,   # top 0.7%
            max_holding_days=18,
            stop_loss_pct=0.03,
            take_profit_pct=0.10,
            trailing_stop_pct=0.025,
            max_positions=1
        ),
        
        # 极低频6：纯大趋势
        ParamSet(
            name="纯大趋势",
            future_days=20,           # 预测20天
            long_threshold=0.12,      # 12%收益阈值
            short_threshold=0.12,
            signal_percentile=98,
            max_holding_days=30,
            stop_loss_pct=0.05,
            take_profit_pct=0.18,
            trailing_stop_pct=0.04,
            max_positions=1
        ),
    ]
    
    # 运行所有参数组合
    results = []
    for params in param_sets:
        try:
            summary = run_backtest_with_params(df_all.copy(), params)
            results.append(summary)
        except Exception as e:
            print(f"[错误] {params.name} 运行失败: {e}")
            continue
    
    # 打印对比结果
    df_results = print_comparison_table(results)
    
    # 保存结果
    output_dir = script_dir / 'output'
    output_dir.mkdir(exist_ok=True)
    
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_dir / 'param_optimization_v2_results.csv', index=False, encoding='utf-8-sig')
    print(f"\n[保存] 结果已保存至: {output_dir / 'param_optimization_v2_results.csv'}")
    
    # 筛选满足条件的参数组（3-5天交易一次）
    print("\n" + "=" * 60)
    print("推荐分析（目标：3-5天交易一次）")
    print("=" * 60)
    
    # 筛选日均交易 <= 0.33 的参数组
    qualified = [r for r in results if r['trades_per_day'] <= 0.35]
    
    if qualified:
        print(f"\n满足条件的参数组（交易间隔 >= 3天）:")
        for r in sorted(qualified, key=lambda x: x['total_return'], reverse=True):
            print(f"\n  {r['param_name']}:")
            print(f"    - 总交易: {r['total_trades']} 笔")
            print(f"    - 交易间隔: {r['days_per_trade']:.1f} 天")
            print(f"    - 胜率: {r['win_rate']*100:.1f}%")
            print(f"    - 盈亏比: {r['profit_factor']:.2f}")
            print(f"    - 累计收益: {r['total_return']*100:.1f}%")
            print(f"    - 最大回撤: {r['max_drawdown']*100:.1f}%")
            print(f"    - 夏普比率: {r['sharpe_ratio']:.2f}")
    else:
        print("\n没有满足条件的参数组，建议进一步提高阈值")
    
    # 综合评分
    print("\n" + "-" * 60)
    print("按综合评分排名（收益/回撤 × 夏普 / 日均交易）:")
    
    for r in results:
        if r['max_drawdown'] > 0 and r['trades_per_day'] > 0:
            r['score'] = (r['total_return'] / r['max_drawdown']) * r['sharpe_ratio'] / r['trades_per_day']
        else:
            r['score'] = 0
    
    results_sorted = sorted(results, key=lambda x: x['score'], reverse=True)
    
    for i, r in enumerate(results_sorted, 1):
        interval = f"{r['days_per_trade']:.1f}天" if r['days_per_trade'] < 100 else "极少"
        print(f"{i}. {r['param_name']}: 评分={r['score']:.1f}, "
              f"收益={r['total_return']*100:.1f}%, 回撤={r['max_drawdown']*100:.1f}%, "
              f"交易间隔={interval}")
    
    return results


if __name__ == "__main__":
    main()

