"""
中长线均线策略回测

最朴素的均线买卖策略，用于对比短线量化策略的收益表现。

策略说明：
1. 双均线策略（金叉死叉）
   - 入场：短均线上穿长均线（金叉）→ 做多
   - 出场：短均线下穿长均线（死叉）→ 平仓
   - 经典参数：MA20/MA60, MA10/MA30, MA5/MA20

2. 三均线策略
   - 入场：短 > 中 > 长（多头排列刚形成）
   - 出场：短 < 中（排列打破）
   - 经典参数：MA5/MA20/MA60

3. 单均线策略（价格突破均线）
   - 入场：价格上穿均线
   - 出场：价格下穿均线
   - 经典参数：MA60, MA120, MA250

特点：
- 无最大持有天数限制（完全跟随趋势）
- 无 ATR 止损（简单粗暴）
- 持仓时间可能很长（中长线）
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from itertools import product
import pandas as pd
import backtrader as bt

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.data_loader import create_bt_datafeed, get_available_symbols, load_symbol_data
from core.backtest import BacktestEngine, TradeConfig
from core.metrics import extract_metrics, print_metrics


# ============================================================================
# 策略定义
# ============================================================================

class DualMA(bt.Strategy):
    """
    经典双均线策略（金叉死叉）
    
    - 金叉做多，死叉平仓
    - 没有止损，没有最大持有天数
    - 纯粹跟随均线交叉信号
    """
    params = dict(
        ma_short=20,   # 短期均线
        ma_long=60,    # 长期均线
        use_ema=False, # 是否使用 EMA
        print_log=False,
    )
    
    def __init__(self):
        MA = bt.indicators.EMA if self.p.use_ema else bt.indicators.SMA
        self.ma_short = MA(self.data.close, period=self.p.ma_short)
        self.ma_long = MA(self.data.close, period=self.p.ma_long)
        self.crossover = bt.indicators.CrossOver(self.ma_short, self.ma_long)
        
        self.order = None
        self.entry_price = None
        self.entry_date = None
    
    def log(self, txt, dt=None):
        if self.p.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            # 金叉做多
            if self.crossover[0] > 0:
                self.order = self.buy()
                self.entry_price = self.data.close[0]
                self.entry_date = self.datas[0].datetime.date(0)
                self.log(f'【金叉买入】价格={self.data.close[0]:.2f}, '
                        f'MA{self.p.ma_short}={self.ma_short[0]:.2f}, '
                        f'MA{self.p.ma_long}={self.ma_long[0]:.2f}')
        else:
            # 死叉卖出
            if self.crossover[0] < 0:
                self.order = self.close()
                hold_days = (self.datas[0].datetime.date(0) - self.entry_date).days
                pnl_pct = (self.data.close[0] - self.entry_price) / self.entry_price * 100
                self.log(f'【死叉卖出】价格={self.data.close[0]:.2f}, '
                        f'持有{hold_days}天, 收益={pnl_pct:.2f}%')
                self.entry_price = None
                self.entry_date = None
    
    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None


class DualMADual(bt.Strategy):
    """
    双均线策略（多空双向版本）
    
    - 金叉做多，死叉做空
    - 始终持有仓位
    """
    params = dict(
        ma_short=20,
        ma_long=60,
        use_ema=False,
        print_log=False,
    )
    
    def __init__(self):
        MA = bt.indicators.EMA if self.p.use_ema else bt.indicators.SMA
        self.ma_short = MA(self.data.close, period=self.p.ma_short)
        self.ma_long = MA(self.data.close, period=self.p.ma_long)
        self.crossover = bt.indicators.CrossOver(self.ma_short, self.ma_long)
        
        self.order = None
        self.position_type = 0  # 1=多, -1=空
    
    def log(self, txt, dt=None):
        if self.p.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def next(self):
        if self.order:
            return
        
        if self.crossover[0] > 0:  # 金叉
            if self.position_type == -1:
                self.close()  # 平空
            self.order = self.buy()
            self.position_type = 1
            self.log(f'【金叉做多】价格={self.data.close[0]:.2f}')
        
        elif self.crossover[0] < 0:  # 死叉
            if self.position_type == 1:
                self.close()  # 平多
            self.order = self.sell()
            self.position_type = -1
            self.log(f'【死叉做空】价格={self.data.close[0]:.2f}')
    
    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None


class TripleMA(bt.Strategy):
    """
    三均线策略（长线版）
    
    - 入场：短 > 中 > 长（多头排列）
    - 出场：短 < 中（排列打破）
    """
    params = dict(
        ma_short=5,
        ma_mid=20,
        ma_long=60,
        use_ema=False,
        print_log=False,
    )
    
    def __init__(self):
        MA = bt.indicators.EMA if self.p.use_ema else bt.indicators.SMA
        self.ma_short = MA(self.data.close, period=self.p.ma_short)
        self.ma_mid = MA(self.data.close, period=self.p.ma_mid)
        self.ma_long = MA(self.data.close, period=self.p.ma_long)
        
        self.order = None
        self.entry_price = None
    
    def log(self, txt, dt=None):
        if self.p.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            # 多头排列刚形成
            if (self.ma_short[0] > self.ma_mid[0] > self.ma_long[0] and
                self.ma_short[-1] <= self.ma_mid[-1]):
                self.order = self.buy()
                self.entry_price = self.data.close[0]
                self.log(f'【多头排列买入】价格={self.data.close[0]:.2f}')
        else:
            # 排列打破
            if self.ma_short[0] < self.ma_mid[0]:
                self.order = self.close()
                pnl_pct = (self.data.close[0] - self.entry_price) / self.entry_price * 100
                self.log(f'【排列打破卖出】价格={self.data.close[0]:.2f}, 收益={pnl_pct:.2f}%')
                self.entry_price = None
    
    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None


class SingleMA(bt.Strategy):
    """
    单均线策略（价格突破均线）
    
    - 入场：价格上穿均线
    - 出场：价格下穿均线
    """
    params = dict(
        ma_period=60,
        use_ema=False,
        print_log=False,
    )
    
    def __init__(self):
        MA = bt.indicators.EMA if self.p.use_ema else bt.indicators.SMA
        self.ma = MA(self.data.close, period=self.p.ma_period)
        self.crossover = bt.indicators.CrossOver(self.data.close, self.ma)
        
        self.order = None
        self.entry_price = None
    
    def log(self, txt, dt=None):
        if self.p.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            # 价格上穿均线
            if self.crossover[0] > 0:
                self.order = self.buy()
                self.entry_price = self.data.close[0]
                self.log(f'【突破MA{self.p.ma_period}买入】价格={self.data.close[0]:.2f}, '
                        f'MA={self.ma[0]:.2f}')
        else:
            # 价格下穿均线
            if self.crossover[0] < 0:
                self.order = self.close()
                pnl_pct = (self.data.close[0] - self.entry_price) / self.entry_price * 100
                self.log(f'【跌破MA{self.p.ma_period}卖出】价格={self.data.close[0]:.2f}, '
                        f'收益={pnl_pct:.2f}%')
                self.entry_price = None
    
    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None


class BuyAndHold(bt.Strategy):
    """
    买入持有策略（基准）
    
    第一天买入，一直持有到最后
    """
    params = dict(print_log=False)
    
    def __init__(self):
        self.order = None
        self.bought = False
    
    def log(self, txt, dt=None):
        if self.p.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def next(self):
        if not self.bought and not self.order:
            self.order = self.buy()
            self.bought = True
            self.log(f'【买入持有】价格={self.data.close[0]:.2f}')
    
    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None


# ============================================================================
# 回测运行函数
# ============================================================================

def run_backtest(symbol: str, strategy_cls, params: dict,
                 start_date: str = '2018-01-01', end_date: str = '2024-12-31',
                 initial_cash: float = 1_000_000, print_log: bool = False):
    """
    运行单次回测
    """
    try:
        data = create_bt_datafeed(symbol, start_date=start_date, end_date=end_date)
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None, None
    
    config = TradeConfig(initial_cash=initial_cash)
    engine = BacktestEngine(config)
    engine.add_data(data, name=symbol)
    
    params['print_log'] = print_log
    engine.add_strategy(strategy_cls, **params)
    
    result = engine.run(plot=False)
    metrics = extract_metrics(result)
    
    return result, metrics


def compare_strategies(symbol: str = 'rbm',
                       start_date: str = '2018-01-01',
                       end_date: str = '2024-12-31'):
    """
    对比所有中长线均线策略
    """
    print("=" * 70)
    print(f" 中长线均线策略对比 - {symbol.upper()}")
    print(f" 时间范围: {start_date} ~ {end_date}")
    print("=" * 70)
    
    strategies = [
        # (名称, 策略类, 参数)
        ('买入持有(基准)', BuyAndHold, {}),
        ('单均线MA60', SingleMA, {'ma_period': 60}),
        ('单均线MA120', SingleMA, {'ma_period': 120}),
        ('双均线MA10/MA30', DualMA, {'ma_short': 10, 'ma_long': 30}),
        ('双均线MA20/MA60', DualMA, {'ma_short': 20, 'ma_long': 60}),
        ('双均线MA30/MA120', DualMA, {'ma_short': 30, 'ma_long': 120}),
        ('三均线MA5/20/60', TripleMA, {'ma_short': 5, 'ma_mid': 20, 'ma_long': 60}),
        ('三均线MA10/30/120', TripleMA, {'ma_short': 10, 'ma_mid': 30, 'ma_long': 120}),
        ('EMA双均线MA20/MA60', DualMA, {'ma_short': 20, 'ma_long': 60, 'use_ema': True}),
    ]
    
    results = []
    for name, strategy_cls, params in strategies:
        print(f"\n运行: {name}...")
        _, metrics = run_backtest(
            symbol, strategy_cls, params,
            start_date=start_date, end_date=end_date
        )
        if metrics:
            metrics['strategy'] = name
            results.append(metrics)
            print(f"  → 收益率: {metrics.get('total_return', 0)*100:.2f}%, "
                  f"夏普: {metrics.get('sharpe_ratio', 0):.2f}, "
                  f"最大回撤: {metrics.get('max_drawdown', 0)*100:.2f}%")
    
    # 汇总表格
    if results:
        df = pd.DataFrame(results)
        df = df.set_index('strategy')
        
        # 选择关键指标
        cols = ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'total_trades']
        cols = [c for c in cols if c in df.columns]
        
        print("\n" + "=" * 70)
        print(" 策略对比汇总")
        print("=" * 70)
        
        # 格式化显示
        display_df = df[cols].copy()
        if 'total_return' in display_df.columns:
            display_df['total_return'] = display_df['total_return'].apply(lambda x: f"{x*100:.2f}%")
        if 'max_drawdown' in display_df.columns:
            display_df['max_drawdown'] = display_df['max_drawdown'].apply(lambda x: f"{x*100:.2f}%")
        if 'win_rate' in display_df.columns:
            display_df['win_rate'] = display_df['win_rate'].apply(lambda x: f"{x*100:.1f}%")
        if 'sharpe_ratio' in display_df.columns:
            display_df['sharpe_ratio'] = display_df['sharpe_ratio'].apply(lambda x: f"{x:.2f}")
        
        print(display_df.to_string())
        
        return df
    
    return None


def param_scan(symbol: str = 'rbm',
               start_date: str = '2018-01-01',
               end_date: str = '2024-12-31'):
    """
    双均线参数扫描
    """
    print("=" * 70)
    print(f" 双均线参数扫描 - {symbol.upper()}")
    print("=" * 70)
    
    # 参数网格
    short_periods = [5, 10, 15, 20, 30]
    long_periods = [20, 30, 60, 90, 120, 180, 250]
    
    results = []
    total = sum(1 for s in short_periods for l in long_periods if s < l)
    current = 0
    
    for ma_short in short_periods:
        for ma_long in long_periods:
            if ma_short >= ma_long:
                continue
            
            current += 1
            print(f"\r进度: {current}/{total} - MA{ma_short}/MA{ma_long}", end='', flush=True)
            
            _, metrics = run_backtest(
                symbol, DualMA,
                {'ma_short': ma_short, 'ma_long': ma_long},
                start_date=start_date, end_date=end_date
            )
            
            if metrics:
                metrics['ma_short'] = ma_short
                metrics['ma_long'] = ma_long
                metrics['params'] = f'MA{ma_short}/MA{ma_long}'
                results.append(metrics)
    
    print()  # 换行
    
    if results:
        df = pd.DataFrame(results)
        
        # 按夏普比率排序
        df = df.sort_values('sharpe_ratio', ascending=False)
        
        print("\n" + "=" * 70)
        print(" 参数扫描结果 (按夏普比率排序前10)")
        print("=" * 70)
        
        cols = ['params', 'total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'total_trades']
        cols = [c for c in cols if c in df.columns]
        
        display_df = df[cols].head(10).copy()
        if 'total_return' in display_df.columns:
            display_df['total_return'] = display_df['total_return'].apply(lambda x: f"{x*100:.2f}%")
        if 'max_drawdown' in display_df.columns:
            display_df['max_drawdown'] = display_df['max_drawdown'].apply(lambda x: f"{x*100:.2f}%")
        if 'win_rate' in display_df.columns:
            display_df['win_rate'] = display_df['win_rate'].apply(lambda x: f"{x*100:.1f}%")
        
        print(display_df.to_string(index=False))
        
        return df
    
    return None


def multi_symbol_test(symbols: list = None,
                      start_date: str = '2018-01-01',
                      end_date: str = '2024-12-31'):
    """
    多品种测试
    """
    if symbols is None:
        symbols = ['rbm', 'cum', 'aum', 'scm', 'im', 'jm', 'hcm', 'alm', 'znm', 'agm']
    
    print("=" * 70)
    print(f" 多品种中长线均线策略测试")
    print(f" 品种: {', '.join(symbols)}")
    print("=" * 70)
    
    # 使用 MA20/MA60 双均线策略
    results = []
    
    for symbol in symbols:
        print(f"\n测试 {symbol.upper()}...")
        
        try:
            # 买入持有基准
            _, benchmark_metrics = run_backtest(
                symbol, BuyAndHold, {},
                start_date=start_date, end_date=end_date
            )
            
            # MA20/MA60 策略
            _, strategy_metrics = run_backtest(
                symbol, DualMA, {'ma_short': 20, 'ma_long': 60},
                start_date=start_date, end_date=end_date
            )
            
            if benchmark_metrics and strategy_metrics:
                results.append({
                    'symbol': symbol.upper(),
                    'benchmark_return': benchmark_metrics.get('total_return', 0),
                    'strategy_return': strategy_metrics.get('total_return', 0),
                    'strategy_sharpe': strategy_metrics.get('sharpe_ratio', 0),
                    'strategy_mdd': strategy_metrics.get('max_drawdown', 0),
                    'strategy_trades': strategy_metrics.get('total_trades', 0),
                    'outperform': strategy_metrics.get('total_return', 0) > benchmark_metrics.get('total_return', 0)
                })
                
                print(f"  基准: {benchmark_metrics.get('total_return', 0)*100:.2f}%, "
                      f"策略: {strategy_metrics.get('total_return', 0)*100:.2f}%")
        
        except Exception as e:
            print(f"  失败: {e}")
    
    if results:
        df = pd.DataFrame(results)
        
        print("\n" + "=" * 70)
        print(" 多品种对比汇总 (MA20/MA60 vs 买入持有)")
        print("=" * 70)
        
        # 格式化
        display_df = df.copy()
        display_df['benchmark_return'] = display_df['benchmark_return'].apply(lambda x: f"{x*100:.2f}%")
        display_df['strategy_return'] = display_df['strategy_return'].apply(lambda x: f"{x*100:.2f}%")
        display_df['strategy_mdd'] = display_df['strategy_mdd'].apply(lambda x: f"{x*100:.2f}%")
        display_df['strategy_sharpe'] = display_df['strategy_sharpe'].apply(lambda x: f"{x:.2f}")
        display_df['outperform'] = display_df['outperform'].apply(lambda x: '✓' if x else '✗')
        
        print(display_df.to_string(index=False))
        
        # 统计
        outperform_count = sum(r['outperform'] for r in results)
        print(f"\n跑赢买入持有: {outperform_count}/{len(results)} 个品种")
        
        return df
    
    return None


def single_test(symbol: str = 'rbm', strategy_name: str = 'dual_ma',
                start_date: str = '2018-01-01', end_date: str = '2024-12-31',
                print_log: bool = False):
    """
    单个策略详细测试
    """
    strategy_map = {
        'buy_hold': (BuyAndHold, {}, '买入持有'),
        'single_60': (SingleMA, {'ma_period': 60}, '单均线MA60'),
        'single_120': (SingleMA, {'ma_period': 120}, '单均线MA120'),
        'dual_ma': (DualMA, {'ma_short': 20, 'ma_long': 60}, '双均线MA20/MA60'),
        'triple_ma': (TripleMA, {'ma_short': 5, 'ma_mid': 20, 'ma_long': 60}, '三均线MA5/20/60'),
        'ema': (DualMA, {'ma_short': 20, 'ma_long': 60, 'use_ema': True}, 'EMA双均线'),
    }
    
    if strategy_name not in strategy_map:
        print(f"未知策略: {strategy_name}")
        print(f"可选: {list(strategy_map.keys())}")
        return
    
    strategy_cls, params, display_name = strategy_map[strategy_name]
    
    print("=" * 70)
    print(f" 单策略测试: {display_name} - {symbol.upper()}")
    print(f" 时间范围: {start_date} ~ {end_date}")
    print("=" * 70)
    
    result, metrics = run_backtest(
        symbol, strategy_cls, params,
        start_date=start_date, end_date=end_date,
        print_log=print_log
    )
    
    if metrics:
        print_metrics(metrics, title=f"{symbol.upper()} - {display_name}")
    
    return result, metrics


# ============================================================================
# 主函数
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='中长线均线策略回测')
    parser.add_argument('--symbol', '-s', default='rbm', help='品种代码')
    parser.add_argument('--start', default='2018-01-01', help='开始日期')
    parser.add_argument('--end', default='2024-12-31', help='结束日期')
    
    parser.add_argument('--compare', '-c', action='store_true', help='对比所有策略')
    parser.add_argument('--scan', action='store_true', help='参数扫描')
    parser.add_argument('--multi', '-m', action='store_true', help='多品种测试')
    
    parser.add_argument('--strategy', '-t', default='dual_ma',
                       choices=['buy_hold', 'single_60', 'single_120', 'dual_ma', 'triple_ma', 'ema'],
                       help='单策略测试')
    parser.add_argument('--log', '-l', action='store_true', help='打印交易日志')
    
    args = parser.parse_args()
    
    if args.compare:
        compare_strategies(args.symbol, args.start, args.end)
    elif args.scan:
        param_scan(args.symbol, args.start, args.end)
    elif args.multi:
        multi_symbol_test(start_date=args.start, end_date=args.end)
    else:
        single_test(args.symbol, args.strategy, args.start, args.end, args.log)
