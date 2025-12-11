"""
组合风控模块
"""
import backtrader as bt
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class PortfolioConfig:
    """组合风控配置"""
    # 单笔风险
    risk_per_trade: float = 0.02  # 单笔风险占总资金比例 (R)
    
    # 最大持仓
    max_positions: int = 5  # 最大同时持仓数
    max_position_per_symbol: float = 0.2  # 单品种最大仓位比例
    
    # 总体风险
    max_total_risk: float = 0.1  # 总风险上限
    max_drawdown_stop: float = 0.15  # 组合回撤止损
    
    # 资金分配
    equal_weight: bool = True  # 等权重分配


class PositionSizer(bt.Sizer):
    """
    基于 ATR 的仓位计算器
    
    仓位 = (总资金 * 单笔风险) / (ATR * ATR倍数)
    """
    params = dict(
        risk_per_trade=0.02,  # 单笔风险
        atr_mult=2.0,         # ATR 倍数（止损距离）
        atr_period=14,
    )
    
    def _getsizing(self, comminfo, cash, data, isbuy):
        if not isbuy:
            return self.broker.getposition(data).size
        
        # 获取 ATR（需要策略中有 atr 指标）
        try:
            atr = data._owner.atr[0]  # 从策略中获取 ATR
        except:
            atr = data.close[0] * 0.02  # 默认使用 2% 作为 ATR 估计
        
        if atr <= 0:
            return 0
        
        # 计算风险金额
        risk_amount = cash * self.p.risk_per_trade
        
        # 计算止损距离
        stop_distance = atr * self.p.atr_mult
        
        # 计算仓位（股数/手数）
        size = int(risk_amount / stop_distance)
        
        return max(1, size)


class EqualWeightSizer(bt.Sizer):
    """
    等权重仓位计算器
    
    仓位 = 总资金 / 最大持仓数 / 当前价格
    """
    params = dict(
        max_positions=5,
    )
    
    def _getsizing(self, comminfo, cash, data, isbuy):
        if not isbuy:
            return self.broker.getposition(data).size
        
        # 等权重分配
        allocation = cash / self.p.max_positions
        
        # 计算可买入数量
        price = data.close[0]
        size = int(allocation / price)
        
        return max(1, size)


class MultiSymbolStrategy(bt.Strategy):
    """
    多品种策略基类
    
    用于同时交易多个品种
    """
    params = dict(
        max_positions=5,
        risk_per_trade=0.02,
        print_log=False,
    )
    
    def __init__(self):
        self.orders = {}  # {data: order}
        self.positions_info = {}  # {data: {'entry_price': x, 'entry_bar': y}}
        
        # 为每个数据创建指标
        self.indicators = {}
        for data in self.datas:
            self.indicators[data] = self._create_indicators(data)
    
    def _create_indicators(self, data):
        """子类实现：创建指标"""
        raise NotImplementedError
    
    def _check_entry_signal(self, data) -> bool:
        """子类实现：检查入场信号"""
        raise NotImplementedError
    
    def _check_exit_signal(self, data) -> bool:
        """子类实现：检查出场信号"""
        raise NotImplementedError
    
    def log(self, txt, dt=None):
        if self.p.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def next(self):
        for data in self.datas:
            if self.orders.get(data):
                continue
            
            pos = self.getposition(data)
            
            if not pos:
                # 检查是否还能开新仓
                current_positions = sum(1 for d in self.datas if self.getposition(d).size > 0)
                if current_positions >= self.p.max_positions:
                    continue
                
                if self._check_entry_signal(data):
                    self.orders[data] = self.buy(data=data)
                    self.positions_info[data] = {
                        'entry_price': data.close[0],
                        'entry_bar': len(self)
                    }
                    self.log(f'{data._name} 买入信号')
            
            else:
                if self._check_exit_signal(data):
                    self.orders[data] = self.close(data=data)
                    self.positions_info.pop(data, None)
                    self.log(f'{data._name} 卖出信号')
    
    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            for data, o in list(self.orders.items()):
                if o == order:
                    self.orders[data] = None
                    break


class MultiSymbolBreakout(MultiSymbolStrategy):
    """多品种突破策略"""
    params = dict(
        n_high=5,
        n_low=3,
        atr_period=14,
        max_hold=7,
        stop_atr_mult=2.0,
        max_positions=5,
        risk_per_trade=0.02,
        print_log=False,
    )
    
    def _create_indicators(self, data):
        return {
            'highest': bt.indicators.Highest(data.high, period=self.p.n_high),
            'lowest': bt.indicators.Lowest(data.low, period=self.p.n_low),
            'atr': bt.indicators.ATR(data, period=self.p.atr_period),
        }
    
    def _check_entry_signal(self, data) -> bool:
        ind = self.indicators[data]
        return data.close[0] > ind['highest'][-1]
    
    def _check_exit_signal(self, data) -> bool:
        ind = self.indicators[data]
        info = self.positions_info.get(data, {})
        
        if not info:
            return False
        
        hold_days = len(self) - info['entry_bar']
        stop_price = info['entry_price'] - self.p.stop_atr_mult * ind['atr'][0]
        
        return (
            data.close[0] < ind['lowest'][-1] or
            hold_days >= self.p.max_hold or
            data.close[0] < stop_price
        )


def run_multi_symbol_backtest(symbols: List[str], strategy_cls, strategy_params: dict = None,
                               start_date: str = '2020-01-01', end_date: str = '2023-12-31',
                               initial_cash: float = 1_000_000):
    """
    运行多品种回测
    
    Args:
        symbols: 品种列表
        strategy_cls: 策略类
        strategy_params: 策略参数
        start_date: 开始日期
        end_date: 结束日期
        initial_cash: 初始资金
    """
    from core.data_loader import load_multi_symbols
    from core.backtest import TradeConfig, BacktestEngine
    from core.metrics import extract_metrics, print_metrics
    
    print("=" * 60)
    print(" 多品种组合回测")
    print("=" * 60)
    print(f"品种: {symbols}")
    print(f"时间: {start_date} ~ {end_date}")
    
    # 加载数据
    feeds = load_multi_symbols(symbols, start_date, end_date)
    
    if not feeds:
        print("没有可用数据")
        return None
    
    # 创建回测引擎
    config = TradeConfig(initial_cash=initial_cash)
    engine = BacktestEngine(config)
    
    # 添加数据
    for symbol, data in feeds.items():
        engine.add_data(data, name=symbol)
    
    # 添加策略
    params = strategy_params or {}
    engine.add_strategy(strategy_cls, **params)
    
    # 添加仓位计算器
    engine.cerebro.addsizer(EqualWeightSizer, max_positions=params.get('max_positions', 5))
    
    # 运行回测
    print("\n运行回测...")
    result = engine.run()
    
    # 输出结果
    final_value = engine.get_final_value()
    print(f"\n初始资金: {initial_cash:,.0f}")
    print(f"最终价值: {final_value:,.0f}")
    
    metrics = extract_metrics(result)
    print_metrics(metrics, title="多品种组合")
    
    return result, metrics


if __name__ == '__main__':
    # 测试多品种回测
    symbols = ['rbm', 'cum', 'aum']
    
    result = run_multi_symbol_backtest(
        symbols=symbols,
        strategy_cls=MultiSymbolBreakout,
        strategy_params={
            'n_high': 5,
            'n_low': 3,
            'max_hold': 7,
            'max_positions': 3,
        }
    )
