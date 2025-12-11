"""
回测配置与框架
"""
import backtrader as bt
from dataclasses import dataclass
from typing import Type, Optional


@dataclass
class TradeConfig:
    """交易假设配置"""
    # 信号在 T 日收盘生成，T+1 日开盘成交
    signal_delay: int = 1
    use_next_open: bool = True
    
    # 手续费（双边，按成交额比例）
    commission_rate: float = 0.0001  # 1bp
    
    # 滑点（按点数）
    slippage_points: int = 1
    
    # 初始资金
    initial_cash: float = 1_000_000
    
    # 仓位设置
    stake_size: int = 1  # 每次交易手数


class BacktestEngine:
    """统一回测入口"""
    
    def __init__(self, config: TradeConfig = None):
        self.config = config or TradeConfig()
        self.cerebro = bt.Cerebro()
        self._setup_broker()
    
    def _setup_broker(self):
        """配置 Broker"""
        self.cerebro.broker.setcash(self.config.initial_cash)
        self.cerebro.broker.setcommission(commission=self.config.commission_rate)
        
        # 设置滑点
        if self.config.slippage_points > 0:
            self.cerebro.broker.set_slippage_fixed(self.config.slippage_points)
    
    def add_data(self, data, name: str = None):
        """添加数据"""
        self.cerebro.adddata(data, name=name)
    
    def add_strategy(self, strategy_cls: Type[bt.Strategy], **kwargs):
        """添加策略"""
        self.cerebro.addstrategy(strategy_cls, **kwargs)
    
    def add_analyzers(self):
        """添加分析器"""
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', 
                                  riskfreerate=0.0, annualize=True)
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        self.cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    
    def run(self, plot: bool = False, plot_style: str = 'candlestick'):
        """
        执行回测
        
        Args:
            plot: 是否绘图
            plot_style: 绘图样式 ('candlestick', 'bar', 'line')
        
        Returns:
            策略实例（包含分析器结果）
        """
        self.add_analyzers()
        results = self.cerebro.run()
        
        if plot:
            self.cerebro.plot(style=plot_style)
        
        return results[0]  # 返回策略实例
    
    def get_final_value(self) -> float:
        """获取最终账户价值"""
        return self.cerebro.broker.getvalue()
    
    def get_initial_cash(self) -> float:
        """获取初始资金"""
        return self.config.initial_cash


class BaseStrategy(bt.Strategy):
    """
    策略基类，提供通用功能
    """
    
    def log(self, txt: str, dt=None):
        """日志输出"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行: 价格={order.executed.price:.2f}, '
                        f'成本={order.executed.value:.2f}, '
                        f'手续费={order.executed.comm:.2f}')
            else:
                self.log(f'卖出执行: 价格={order.executed.price:.2f}, '
                        f'成本={order.executed.value:.2f}, '
                        f'手续费={order.executed.comm:.2f}')
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单被取消/保证金不足/拒绝')
    
    def notify_trade(self, trade):
        """交易通知"""
        if not trade.isclosed:
            return
        
        self.log(f'交易利润: 毛利={trade.pnl:.2f}, 净利={trade.pnlcomm:.2f}')


# 参数优化辅助函数
def run_optimization(engine_class, strategy_cls, data, param_grid: dict, 
                     config: TradeConfig = None) -> list:
    """
    参数优化
    
    Args:
        engine_class: BacktestEngine 类
        strategy_cls: 策略类
        data: Backtrader 数据对象
        param_grid: 参数网格 {'param1': [v1, v2], 'param2': [v1, v2]}
        config: 交易配置
    
    Returns:
        list: 优化结果列表
    """
    from itertools import product
    from .metrics import extract_metrics
    
    results = []
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    
    for values in product(*param_values):
        params = dict(zip(param_names, values))
        
        engine = engine_class(config)
        engine.add_data(data)
        engine.add_strategy(strategy_cls, **params)
        
        try:
            result = engine.run()
            metrics = extract_metrics(result)
            metrics['params'] = params
            results.append(metrics)
        except Exception as e:
            print(f"参数 {params} 运行失败: {e}")
    
    return results
