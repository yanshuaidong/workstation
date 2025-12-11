"""
快速开始示例 - 单品种回测
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.data_loader import create_bt_datafeed, get_available_symbols, load_symbol_data
from core.backtest import BacktestEngine, TradeConfig
from core.metrics import extract_metrics, print_metrics
# 双向策略（多空皆可）
from strategies.breakout import ShortTermBreakoutDual
from strategies.ma_trend import ShortTermMATrendDual
from strategies.momentum import MomentumFixHoldDual
from strategies.atr_channel import ATRChannelTrendDual
from strategies.vol_oi_breakout import VolOIBreakoutDual


def run_single_backtest(symbol: str = 'rbm', strategy_name: str = 'breakout'):
    """
    单品种单策略回测示例
    
    Args:
        symbol: 品种代码（如 'rbm', 'cum', 'aum'）
        strategy_name: 策略名称 ('breakout', 'ma', 'momentum', 'atr')
    """
    print("=" * 60)
    print(f" 单品种回测: {symbol.upper()}")
    print("=" * 60)
    
    # 1. 加载数据
    print(f"\n加载数据: {symbol}")
    try:
        data = create_bt_datafeed(symbol, start_date='2020-01-01', end_date='2023-12-31')
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None
    
    # 2. 创建回测引擎
    config = TradeConfig(initial_cash=1_000_000)
    engine = BacktestEngine(config)
    
    # 3. 添加数据和策略
    engine.add_data(data, name=symbol)
    
    strategy_map = {
        'breakout': (ShortTermBreakoutDual, {'n_high': 5, 'n_low': 3, 'max_hold': 7}),
        'ma': (ShortTermMATrendDual, {'ma_short': 5, 'ma_long': 10, 'max_hold': 7}),
        'momentum': (MomentumFixHoldDual, {'lookback': 5, 'threshold': 0.02, 'hold_days': 5}),
        'atr': (ATRChannelTrendDual, {'ma_period': 10, 'channel_mult': 2.0, 'max_hold': 10}),
        'voloi': (VolOIBreakoutDual, {'n_break': 5, 'n_exit': 3, 'vol_mult': 1.5, 'oi_threshold': 0.02, 'max_hold': 7}),
    }
    
    if strategy_name not in strategy_map:
        print(f"未知策略: {strategy_name}, 可选: {list(strategy_map.keys())}")
        return None
    
    strategy_cls, params = strategy_map[strategy_name]
    engine.add_strategy(strategy_cls, **params)
    print(f"使用策略: {strategy_cls.__name__}")
    print(f"策略参数: {params}")
    
    # 4. 运行回测
    print("\n运行回测...")
    result = engine.run(plot=False)
    
    # 5. 输出结果
    final_value = engine.get_final_value()
    initial_cash = engine.get_initial_cash()
    
    print(f"\n初始资金: {initial_cash:,.0f}")
    print(f"最终价值: {final_value:,.0f}")
    print(f"绝对收益: {final_value - initial_cash:,.0f}")
    
    metrics = extract_metrics(result)
    print_metrics(metrics, title=f"{symbol.upper()} - {strategy_cls.__name__}")
    
    return result, metrics


def run_multi_symbol_test(symbols: list = None, strategy_name: str = 'breakout'):
    """
    多品种回测
    
    Args:
        symbols: 品种代码列表
        strategy_name: 策略名称
    """
    if symbols is None:
        # 默认测试几个主要品种
        symbols = ['rbm', 'cum', 'aum', 'scm', 'im']
    
    print("=" * 60)
    print(f" 多品种回测测试 - {strategy_name}")
    print("=" * 60)
    
    results = {}
    for symbol in symbols:
        print(f"\n{'='*40}")
        print(f" 测试品种: {symbol.upper()}")
        print(f"{'='*40}")
        
        try:
            result, metrics = run_single_backtest(symbol, strategy_name)
            if result:
                results[symbol] = metrics
        except Exception as e:
            print(f"回测失败: {e}")
    
    # 汇总结果
    if results:
        print("\n" + "=" * 60)
        print(" 多品种回测汇总")
        print("=" * 60)
        
        import pandas as pd
        df = pd.DataFrame(results).T
        
        # 选择关键指标
        key_cols = ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'total_trades']
        key_cols = [c for c in key_cols if c in df.columns]
        
        print(df[key_cols].to_string())
    
    return results


def list_available_symbols():
    """列出所有可用品种"""
    print("=" * 60)
    print(" 可用品种列表")
    print("=" * 60)
    
    symbols = get_available_symbols()
    
    for i, s in enumerate(symbols, 1):
        print(f"  {i:3d}. {s['symbol']:8s} - {s['name']}")
    
    print(f"\n共 {len(symbols)} 个品种")
    return symbols


def quick_data_check(symbol: str):
    """快速检查数据"""
    print(f"\n数据检查: {symbol}")
    print("-" * 40)
    
    try:
        df = load_symbol_data(symbol)
        print(f"数据条数: {len(df)}")
        print(f"时间范围: {df.index.min()} ~ {df.index.max()}")
        print(f"\n前5行:")
        print(df.head())
        print(f"\n后5行:")
        print(df.tail())
        print(f"\n数据统计:")
        print(df.describe())
        return df
    except Exception as e:
        print(f"加载失败: {e}")
        return None


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='量化策略回测示例')
    parser.add_argument('--symbol', '-s', default='rbm', help='品种代码')
    parser.add_argument('--strategy', '-t', default='breakout', 
                       choices=['breakout', 'ma', 'momentum', 'atr', 'voloi'],
                       help='策略类型')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有品种')
    parser.add_argument('--check', '-c', action='store_true', help='检查数据')
    parser.add_argument('--multi', '-m', action='store_true', help='多品种测试')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_symbols()
    elif args.check:
        quick_data_check(args.symbol)
    elif args.multi:
        run_multi_symbol_test(strategy_name=args.strategy)
    else:
        run_single_backtest(args.symbol, args.strategy)
