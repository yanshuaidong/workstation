"""
参数网格搜索与优化（支持多进程并行）
"""
import sys
import os
from pathlib import Path
from itertools import product
import pandas as pd
from datetime import datetime
from multiprocessing import Pool, cpu_count
import warnings

# 忽略 backtrader 的警告
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent))

from core.data_loader import create_bt_datafeed
from core.backtest import BacktestEngine, TradeConfig
from core.metrics import extract_metrics, print_metrics


# ============== 多进程辅助函数 ==============

def _run_single_param_combo(args):
    """
    单个参数组合的回测（多进程 worker 函数）
    
    Args:
        args: (strategy_name, params, param_names, symbol_data_dict)
    
    Returns:
        dict: 该参数组合在所有品种上的综合结果
    """
    import backtrader as bt
    
    strategy_name, params, param_names, symbol_data_dict = args
    
    # 动态导入策略类
    strategy_cls = _get_strategy_class(strategy_name)
    
    symbol_metrics = []
    positive_count = 0
    
    for symbol, data_df in symbol_data_dict.items():
        try:
            data = bt.feeds.PandasData(
                dataname=data_df.copy(),
                datetime=None,
                open='open', high='high', low='low', close='close',
                volume='volume', openinterest='openinterest'
            )
            
            config = TradeConfig(initial_cash=1_000_000)
            engine = BacktestEngine(config)
            engine.add_data(data, name=symbol)
            engine.add_strategy(strategy_cls, **params)
            
            result = engine.run()
            metrics = extract_metrics(result)
            
            symbol_metrics.append({
                'symbol': symbol,
                'sharpe': metrics.get('sharpe_ratio', 0),
                'return': metrics.get('total_return', 0),
                'drawdown': metrics.get('max_drawdown', 0),
                'win_rate': metrics.get('win_rate', 0),
                'trades': metrics.get('total_trades', 0),
            })
            
            if metrics.get('total_return', 0) > 0:
                positive_count += 1
                
        except Exception:
            pass
    
    if not symbol_metrics:
        return None
    
    df_metrics = pd.DataFrame(symbol_metrics)
    
    return {
        **params,
        'avg_sharpe': df_metrics['sharpe'].mean(),
        'avg_return': df_metrics['return'].mean(),
        'avg_drawdown': df_metrics['drawdown'].mean(),
        'avg_win_rate': df_metrics['win_rate'].mean(),
        'total_trades': df_metrics['trades'].sum(),
        'positive_ratio': positive_count / len(symbol_metrics),
        'tested_symbols': len(symbol_metrics),
    }


def _get_strategy_class(strategy_name: str):
    """根据策略名称获取策略类"""
    if strategy_name == 'breakout':
        from strategies.breakout import ShortTermBreakout
        return ShortTermBreakout
    elif strategy_name == 'ma':
        from strategies.ma_trend import ShortTermMATrend
        return ShortTermMATrend
    elif strategy_name == 'momentum':
        from strategies.momentum import MomentumFixHold
        return MomentumFixHold
    elif strategy_name == 'atr':
        from strategies.atr_channel import ATRChannelTrend
        return ATRChannelTrend
    elif strategy_name == 'voloi':
        from strategies.vol_oi_breakout import VolOIBreakoutDual
        return VolOIBreakoutDual
    else:
        raise ValueError(f"未知策略: {strategy_name}")


def param_grid_search(
    symbol: str,
    strategy_cls,
    param_grid: dict,
    start_date: str = '2018-01-01',
    end_date: str = '2021-12-31',
    initial_cash: float = 1_000_000,
    verbose: bool = True
) -> pd.DataFrame:
    """
    参数网格搜索
    
    Args:
        symbol: 品种代码
        strategy_cls: 策略类
        param_grid: 参数网格 {'param1': [v1, v2], 'param2': [v1, v2]}
        start_date: 回测开始日期
        end_date: 回测结束日期
        initial_cash: 初始资金
        verbose: 是否打印进度
    
    Returns:
        pd.DataFrame: 优化结果
    """
    # 加载数据
    data_df = None
    try:
        from core.data_loader import load_symbol_data
        data_df = load_symbol_data(symbol, start_date, end_date)
        if verbose:
            print(f"加载数据: {symbol}, {len(data_df)} 条记录")
    except Exception as e:
        print(f"加载数据失败: {e}")
        return pd.DataFrame()
    
    # 生成参数组合
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    combinations = list(product(*param_values))
    
    if verbose:
        print(f"参数组合数: {len(combinations)}")
    
    results = []
    
    for i, values in enumerate(combinations, 1):
        params = dict(zip(param_names, values))
        
        if verbose and i % 10 == 0:
            print(f"进度: {i}/{len(combinations)}")
        
        try:
            # 每次创建新的数据对象
            import backtrader as bt
            data = bt.feeds.PandasData(
                dataname=data_df.copy(),
                datetime=None,
                open='open',
                high='high',
                low='low',
                close='close',
                volume='volume',
                openinterest='openinterest'
            )
            
            config = TradeConfig(initial_cash=initial_cash)
            engine = BacktestEngine(config)
            engine.add_data(data, name=symbol)
            engine.add_strategy(strategy_cls, **params)
            
            result = engine.run()
            metrics = extract_metrics(result)
            
            # 添加参数信息
            record = {**params, **metrics}
            record['final_value'] = engine.get_final_value()
            results.append(record)
            
        except Exception as e:
            if verbose:
                print(f"参数 {params} 运行失败: {e}")
    
    df = pd.DataFrame(results)
    
    # 按 Sharpe Ratio 排序
    if 'sharpe_ratio' in df.columns:
        df = df.sort_values('sharpe_ratio', ascending=False)
    
    return df


def run_breakout_optimization(symbol: str = 'rbm'):
    """短周期突破策略参数优化"""
    from strategies.breakout import ShortTermBreakout
    
    param_grid = {
        'n_high': [3, 5, 7, 10],
        'n_low': [3, 5],
        'max_hold': [5, 7, 10],
        'stop_atr_mult': [1.5, 2.0, 2.5],
    }
    
    print("=" * 60)
    print(f" 短周期突破策略参数优化 - {symbol.upper()}")
    print("=" * 60)
    
    # 训练期优化
    print("\n【训练期: 2018-2021】")
    df_train = param_grid_search(
        symbol=symbol,
        strategy_cls=ShortTermBreakout,
        param_grid=param_grid,
        start_date='2018-01-01',
        end_date='2021-12-31'
    )
    
    if df_train.empty:
        print("训练期优化失败")
        return None
    
    # 显示前10个最佳参数
    print("\n训练期 Top 10 参数组合:")
    display_cols = ['n_high', 'n_low', 'max_hold', 'stop_atr_mult', 
                   'sharpe_ratio', 'total_return', 'max_drawdown', 'win_rate', 'total_trades']
    display_cols = [c for c in display_cols if c in df_train.columns]
    print(df_train[display_cols].head(10).to_string())
    
    # 选择最佳参数进行验证期测试
    best_params = df_train.iloc[0][['n_high', 'n_low', 'max_hold', 'stop_atr_mult']].to_dict()
    # 将整数参数转换回 int 类型（从 DataFrame 提取会变成 float）
    for key in ['n_high', 'n_low', 'max_hold']:
        best_params[key] = int(best_params[key])
    
    print(f"\n最佳参数: {best_params}")
    
    # 验证期测试
    print("\n【验证期: 2022-2023】")
    df_valid = param_grid_search(
        symbol=symbol,
        strategy_cls=ShortTermBreakout,
        param_grid={k: [v] for k, v in best_params.items()},
        start_date='2022-01-01',
        end_date='2023-12-31'
    )
    
    if not df_valid.empty:
        print("\n验证期结果:")
        print(df_valid[display_cols].to_string())
    
    # 保存结果
    output_dir = Path(__file__).parent / 'research' / 'results'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'breakout_opt_{symbol}_{timestamp}.csv'
    df_train.to_csv(output_file, index=False)
    print(f"\n结果已保存: {output_file}")
    
    return df_train


def run_ma_optimization(symbol: str = 'rbm'):
    """均线趋势策略参数优化"""
    from strategies.ma_trend import ShortTermMATrend
    
    param_grid = {
        'ma_short': [3, 4, 5],
        'ma_long': [8, 10, 12, 15],
        'max_hold': [5, 7, 10],
        'stop_atr_mult': [1.5, 2.0, 2.5],
    }
    
    print("=" * 60)
    print(f" 均线趋势策略参数优化 - {symbol.upper()}")
    print("=" * 60)
    
    df = param_grid_search(
        symbol=symbol,
        strategy_cls=ShortTermMATrend,
        param_grid=param_grid,
        start_date='2018-01-01',
        end_date='2021-12-31'
    )
    
    if df.empty:
        print("优化失败")
        return None
    
    print("\nTop 10 参数组合:")
    display_cols = ['ma_short', 'ma_long', 'max_hold', 'stop_atr_mult',
                   'sharpe_ratio', 'total_return', 'max_drawdown', 'win_rate', 'total_trades']
    display_cols = [c for c in display_cols if c in df.columns]
    print(df[display_cols].head(10).to_string())
    
    # 保存结果
    output_dir = Path(__file__).parent / 'research' / 'results'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'ma_opt_{symbol}_{timestamp}.csv'
    df.to_csv(output_file, index=False)
    print(f"\n结果已保存: {output_file}")
    
    return df


def run_momentum_optimization(symbol: str = 'rbm'):
    """动量持有策略参数优化"""
    from strategies.momentum import MomentumFixHold
    
    param_grid = {
        'lookback': [3, 5, 7],
        'threshold': [0.01, 0.02, 0.03],
        'hold_days': [3, 5, 7, 10],
        'stop_atr_mult': [1.5, 2.0, 2.5],
    }
    
    print("=" * 60)
    print(f" 动量持有策略参数优化 - {symbol.upper()}")
    print("=" * 60)
    
    df = param_grid_search(
        symbol=symbol,
        strategy_cls=MomentumFixHold,
        param_grid=param_grid,
        start_date='2018-01-01',
        end_date='2021-12-31'
    )
    
    if df.empty:
        print("优化失败")
        return None
    
    print("\nTop 10 参数组合:")
    display_cols = ['lookback', 'threshold', 'hold_days', 'stop_atr_mult',
                   'sharpe_ratio', 'total_return', 'max_drawdown', 'win_rate', 'total_trades']
    display_cols = [c for c in display_cols if c in df.columns]
    print(df[display_cols].head(10).to_string())
    
    # 保存结果
    output_dir = Path(__file__).parent / 'research' / 'results'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'momentum_opt_{symbol}_{timestamp}.csv'
    df.to_csv(output_file, index=False)
    print(f"\n结果已保存: {output_file}")
    
    return df


def run_atr_optimization(symbol: str = 'rbm'):
    """ATR通道策略参数优化"""
    from strategies.atr_channel import ATRChannelTrend
    
    param_grid = {
        'ma_period': [10, 20],
        'atr_period': [10, 14, 20],
        'channel_mult': [1.5, 2.0, 2.5],
        'max_hold': [5, 7, 10],
    }
    
    print("=" * 60)
    print(f" ATR通道策略参数优化 - {symbol.upper()}")
    print("=" * 60)
    
    df = param_grid_search(
        symbol=symbol,
        strategy_cls=ATRChannelTrend,
        param_grid=param_grid,
        start_date='2018-01-01',
        end_date='2021-12-31'
    )
    
    if df.empty:
        print("优化失败")
        return None
    
    print("\nTop 10 参数组合:")
    display_cols = ['ma_period', 'atr_period', 'channel_mult', 'max_hold',
                   'sharpe_ratio', 'total_return', 'max_drawdown', 'win_rate', 'total_trades']
    display_cols = [c for c in display_cols if c in df.columns]
    print(df[display_cols].head(10).to_string())
    
    # 保存结果
    output_dir = Path(__file__).parent / 'research' / 'results'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'atr_opt_{symbol}_{timestamp}.csv'
    df.to_csv(output_file, index=False)
    print(f"\n结果已保存: {output_file}")
    
    return df


def run_voloi_optimization(symbol: str = 'rbm'):
    """增仓放量突破策略参数优化（多空双向改进版）"""
    from strategies.vol_oi_breakout import VolOIBreakoutDual

    param_grid = {
        # 核心参数
        'n_break': [5, 7, 10],
        'n_exit': [3, 5],
        'vol_mult': [1.5, 2.0],
        'oi_lookback': [3, 5],
        'oi_threshold': [0.02, 0.03, 0.05],
        'max_hold': [7, 10],
        'stop_atr_mult': [1.5, 2.0],
        # 改进参数
        'trend_period': [20, 30],
        'use_trend_filter': [True],
        'use_trailing_stop': [True],
        'trail_atr_mult': [1.5, 2.0],
        'profit_protect': [1.5, 2.0],
    }
    
    print("=" * 60)
    print(f" 增仓放量突破策略参数优化（改进版） - {symbol.upper()}")
    print("=" * 60)
    
    df = param_grid_search(
        symbol=symbol,
        strategy_cls=VolOIBreakoutDual,
        param_grid=param_grid,
        start_date='2018-01-01',
        end_date='2021-12-31'
    )
    
    if df.empty:
        print("优化失败")
        return None
    
    print("\nTop 10 参数组合:")
    display_cols = ['n_break', 'n_exit', 'vol_mult', 'oi_lookback', 'oi_threshold', 
                   'max_hold', 'stop_atr_mult', 'trend_period', 'trail_atr_mult',
                   'sharpe_ratio', 'total_return', 'max_drawdown', 'win_rate', 'total_trades']
    display_cols = [c for c in display_cols if c in df.columns]
    print(df[display_cols].head(10).to_string())
    
    # 保存结果
    output_dir = Path(__file__).parent / 'research' / 'results'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'voloi_opt_{symbol}_{timestamp}.csv'
    df.to_csv(output_file, index=False)
    print(f"\n结果已保存: {output_file}")
    
    return df


def get_strategy_config(strategy: str):
    """获取策略类和参数网格"""
    if strategy == 'breakout':
        from strategies.breakout import ShortTermBreakout
        return ShortTermBreakout, {
            'n_high': [3, 5, 7, 10],
            'n_low': [3, 5],
            'max_hold': [5, 7, 10],
            'stop_atr_mult': [1.5, 2.0, 2.5],
        }, ['n_high', 'n_low', 'max_hold', 'stop_atr_mult']
    elif strategy == 'ma':
        from strategies.ma_trend import ShortTermMATrend
        return ShortTermMATrend, {
            'ma_short': [3, 4, 5],
            'ma_long': [8, 10, 12, 15],
            'max_hold': [5, 7, 10],
            'stop_atr_mult': [1.5, 2.0, 2.5],
        }, ['ma_short', 'ma_long', 'max_hold', 'stop_atr_mult']
    elif strategy == 'momentum':
        from strategies.momentum import MomentumFixHold
        return MomentumFixHold, {
            'lookback': [3, 5, 7],
            'threshold': [0.01, 0.02, 0.03],
            'hold_days': [3, 5, 7, 10],
            'stop_atr_mult': [1.5, 2.0, 2.5],
        }, ['lookback', 'threshold', 'hold_days', 'stop_atr_mult']
    elif strategy == 'atr':
        from strategies.atr_channel import ATRChannelTrend
        return ATRChannelTrend, {
            'ma_period': [10, 20],
            'atr_period': [10, 14, 20],
            'channel_mult': [1.5, 2.0, 2.5],
            'max_hold': [5, 7, 10],
        }, ['ma_period', 'atr_period', 'channel_mult', 'max_hold']
    elif strategy == 'voloi':
        from strategies.vol_oi_breakout import VolOIBreakoutDual
        return VolOIBreakoutDual, {
            # 核心参数
            'n_break': [5, 7, 10],
            'n_exit': [3, 5],
            'vol_mult': [1.5, 2.0],
            'oi_lookback': [3, 5],
            'oi_threshold': [0.02, 0.03, 0.05],
            'max_hold': [7, 10],
            'stop_atr_mult': [1.5, 2.0],
            # 改进参数
            'trend_period': [20, 30],
            'use_trend_filter': [True],          # 启用趋势过滤
            'use_trailing_stop': [True],         # 启用跟踪止损
            'trail_atr_mult': [1.5, 2.0],
            'profit_protect': [1.5, 2.0],
        }, ['n_break', 'n_exit', 'vol_mult', 'oi_lookback', 'oi_threshold', 
            'max_hold', 'stop_atr_mult', 'trend_period', 'trail_atr_mult', 'profit_protect']
    else:
        raise ValueError(f"未知策略: {strategy}")


def run_global_optimization(strategy: str = 'breakout', min_bars: int = 500, n_jobs: int = None):
    """
    全局参数优化：找出在所有品种上综合表现最好的一组参数（支持多进程并行）
    
    Args:
        strategy: 策略类型 ('breakout', 'ma', 'momentum', 'atr', 'voloi')
        min_bars: 最小数据条数，过滤掉数据不足的品种
        n_jobs: 并行进程数，默认为 CPU 核心数
    
    Returns:
        最优参数和综合结果
    """
    from core.data_loader import get_available_symbols, load_symbol_data
    
    if n_jobs is None:
        n_jobs = max(1, cpu_count() - 1)  # 保留一个核心
    
    print("=" * 70)
    print(f" 全局参数优化 - 策略: {strategy.upper()} (并行: {n_jobs} 进程)")
    print("=" * 70)
    
    # 1. 获取策略配置
    _, param_grid, param_names = get_strategy_config(strategy)
    
    # 2. 获取有效品种列表
    symbols = get_available_symbols()
    print(f"\n总共 {len(symbols)} 个品种")
    
    valid_symbols = []
    symbol_data_cache = {}  # 缓存数据
    
    for s in symbols:
        symbol = s['symbol'].lower()
        if symbol in symbol_data_cache:
            continue
        try:
            df = load_symbol_data(symbol, '2018-01-01', '2021-12-31')
            if len(df) >= min_bars:
                valid_symbols.append(symbol)
                symbol_data_cache[symbol] = df
            else:
                print(f"跳过 {symbol}: 数据不足 ({len(df)} < {min_bars})")
        except Exception as e:
            print(f"跳过 {symbol}: {e}")
    
    print(f"\n有效品种: {len(valid_symbols)} 个")
    
    # 3. 生成所有参数组合
    param_values = list(param_grid.values())
    combinations = list(product(*param_values))
    total_combos = len(combinations)
    total_backtests = total_combos * len(valid_symbols)
    
    print(f"参数组合数: {total_combos}")
    print(f"总回测次数: {total_combos} x {len(valid_symbols)} = {total_backtests}")
    print(f"\n开始并行计算...")
    
    # 4. 准备多进程任务
    tasks = []
    for values in combinations:
        params = dict(zip(param_names, values))
        tasks.append((strategy, params, param_names, symbol_data_cache))
    
    # 5. 多进程执行
    start_time = datetime.now()
    param_results = []
    
    # 使用 spawn 方法（macOS 兼容）
    from multiprocessing import get_context
    ctx = get_context('spawn')
    
    with ctx.Pool(processes=n_jobs) as pool:
        # 使用 imap_unordered 获取更快的结果
        for i, result in enumerate(pool.imap_unordered(_run_single_param_combo, tasks), 1):
            if result is not None:
                param_results.append(result)
            
            # 每完成 10% 打印一次进度
            if i % max(1, total_combos // 10) == 0 or i == total_combos:
                elapsed = (datetime.now() - start_time).total_seconds()
                speed = i / elapsed if elapsed > 0 else 0
                eta = (total_combos - i) / speed if speed > 0 else 0
                print(f"进度: {i}/{total_combos} ({100*i/total_combos:.1f}%) | "
                      f"速度: {speed:.1f} 组合/秒 | ETA: {eta:.0f}秒")
    
    elapsed_total = (datetime.now() - start_time).total_seconds()
    print(f"\n计算完成! 总耗时: {elapsed_total:.1f}秒 ({total_backtests/elapsed_total:.1f} 回测/秒)")
    
    # 6. 汇总排序
    df_results = pd.DataFrame(param_results)
    
    if len(df_results) > 0:
        df_results['score'] = (
            df_results['positive_ratio'] * 0.4 +
            (df_results['avg_sharpe'] - df_results['avg_sharpe'].min()) / 
            (df_results['avg_sharpe'].max() - df_results['avg_sharpe'].min() + 1e-10) * 0.3 +
            (df_results['avg_return'] - df_results['avg_return'].min()) / 
            (df_results['avg_return'].max() - df_results['avg_return'].min() + 1e-10) * 0.3
        )
        df_results = df_results.sort_values('score', ascending=False)
    
    # 7. 输出结果
    print("\n" + "=" * 70)
    print(" 全局优化结果 - Top 10 参数组合")
    print("=" * 70)
    
    display_cols = param_names + ['avg_sharpe', 'avg_return', 'avg_drawdown', 
                                   'positive_ratio', 'tested_symbols', 'score']
    print(df_results[display_cols].head(10).to_string())
    
    # 8. 最优参数
    best_params = None
    if len(df_results) > 0:
        best_row = df_results.iloc[0]
        best_params = {k: best_row[k] for k in param_names}
        for k in param_names:
            if isinstance(best_params[k], float) and best_params[k] == int(best_params[k]):
                best_params[k] = int(best_params[k])
        
        print("\n" + "=" * 70)
        print(" 最优参数")
        print("=" * 70)
        print(f"参数: {best_params}")
        print(f"平均夏普: {best_row['avg_sharpe']:.4f}")
        print(f"平均收益: {best_row['avg_return']:.6f}")
        print(f"平均回撤: {best_row['avg_drawdown']:.4f}")
        print(f"正收益品种比例: {best_row['positive_ratio']:.1%}")
        print(f"综合评分: {best_row['score']:.4f}")
    
    # 9. 保存结果
    output_dir = Path(__file__).parent / 'research' / 'results'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'global_opt_{strategy}_{timestamp}.csv'
    df_results.to_csv(output_file, index=False)
    print(f"\n结果已保存: {output_file}")
    
    if len(df_results) > 0:
        best_file = output_dir / f'best_params_{strategy}.json'
        import json
        with open(best_file, 'w') as f:
            json.dump({
                'strategy': strategy,
                'params': best_params,
                'metrics': {
                    'avg_sharpe': float(best_row['avg_sharpe']),
                    'avg_return': float(best_row['avg_return']),
                    'avg_drawdown': float(best_row['avg_drawdown']),
                    'positive_ratio': float(best_row['positive_ratio']),
                },
                'updated_at': timestamp,
            }, f, indent=2, ensure_ascii=False)
        print(f"最优参数已保存: {best_file}")
    
    return df_results, best_params


def run_all_symbols_optimization(strategy: str = 'all', min_bars: int = 500, n_jobs: int = None):
    """
    全品种优化（多进程并行）
    """
    print("=" * 70)
    print(" 全品种参数优化（多进程并行模式）")
    print("=" * 70 + "\n")
    
    if strategy == 'all':
        for s in ['breakout', 'ma', 'momentum', 'atr', 'voloi']:
            run_global_optimization(s, min_bars, n_jobs)
    else:
        run_global_optimization(strategy, min_bars, n_jobs)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='策略参数优化')
    parser.add_argument('--symbol', '-s', default='rbm', help='品种代码')
    parser.add_argument('--strategy', '-t', default='breakout',
                       choices=['breakout', 'ma', 'momentum', 'atr', 'voloi', 'all'],
                       help='策略类型')
    parser.add_argument('--all-symbols', '-A', action='store_true',
                       help='全品种优化（覆盖 -s 参数）')
    parser.add_argument('--min-bars', type=int, default=500,
                       help='最小数据条数（过滤数据不足的品种）')
    parser.add_argument('--jobs', '-j', type=int, default=None,
                       help='并行进程数（默认: CPU核心数-1）')
    
    args = parser.parse_args()
    
    if args.all_symbols:
        # 全品种模式（多进程并行）
        run_all_symbols_optimization(args.strategy, args.min_bars, args.jobs)
    elif args.strategy == 'all':
        run_breakout_optimization(args.symbol)
        run_ma_optimization(args.symbol)
        run_momentum_optimization(args.symbol)
        run_atr_optimization(args.symbol)
        run_voloi_optimization(args.symbol)
    elif args.strategy == 'breakout':
        run_breakout_optimization(args.symbol)
    elif args.strategy == 'ma':
        run_ma_optimization(args.symbol)
    elif args.strategy == 'momentum':
        run_momentum_optimization(args.symbol)
    elif args.strategy == 'atr':
        run_atr_optimization(args.symbol)
    elif args.strategy == 'voloi':
        run_voloi_optimization(args.symbol)
