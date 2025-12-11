"""
N 日动量 + 固定持有策略族

核心理念：用最近 N 日累计涨幅判断趋势，固定持有 3-10 日。

多头入场信号：N 日动量（ROC）超过正阈值
空头入场信号：N 日动量（ROC）低于负阈值
出场信号：
  1. 固定持有到期
  2. 止损（ATR 倍数）
"""
import backtrader as bt


class MomentumFixHoldDual(bt.Strategy):
    """
    动量固定持有策略（多空双向版本）
    
    多头：k 日动量 > 正阈值 → 做多
    空头：k 日动量 < 负阈值 → 做空
    
    参数:
        lookback: 动量回看周期
        threshold: 入场阈值（百分比，如 0.02 表示 2%）
        hold_days: 固定持有天数
        atr_period: ATR 计算周期
        stop_atr_mult: 止损 ATR 倍数
        print_log: 是否打印日志
    """
    params = dict(
        lookback=5,
        threshold=0.02,     # T: 正阈值 2%，负阈值自动为 -2%
        hold_days=5,
        atr_period=14,
        stop_atr_mult=2.0,
        print_log=False,
    )
    
    def __init__(self):
        self.momentum = bt.indicators.ROC(self.data.close, period=self.p.lookback)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        self.position_type = 0  # 1=多头, -1=空头, 0=空仓
        self.entry_price = None
        self.entry_bar = None
        self.order = None
    
    def log(self, txt, dt=None):
        if self.p.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            momentum_pct = self.momentum[0] / 100  # ROC 返回百分比值
            
            # 多头入场：动量超过正阈值
            if momentum_pct > self.p.threshold:
                self.order = self.buy()
                self.position_type = 1
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.log(f'【动量做多】价格={self.data.close[0]:.2f}, '
                        f'{self.p.lookback}日动量={momentum_pct*100:.2f}%')
            
            # 空头入场：动量低于负阈值
            elif momentum_pct < -self.p.threshold:
                self.order = self.sell()
                self.position_type = -1
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.log(f'【动量做空】价格={self.data.close[0]:.2f}, '
                        f'{self.p.lookback}日动量={momentum_pct*100:.2f}%')
        
        else:
            hold_days = len(self) - self.entry_bar
            exit_reason = None
            
            if self.position_type == 1:  # 多头持仓
                stop_price = self.entry_price - self.p.stop_atr_mult * self.atr[0]
                
                if hold_days >= self.p.hold_days:
                    exit_reason = f'持有{hold_days}天到期'
                elif self.data.close[0] < stop_price:
                    exit_reason = f'触发止损(止损价={stop_price:.2f})'
            
            else:  # 空头持仓
                stop_price = self.entry_price + self.p.stop_atr_mult * self.atr[0]
                
                if hold_days >= self.p.hold_days:
                    exit_reason = f'持有{hold_days}天到期'
                elif self.data.close[0] > stop_price:
                    exit_reason = f'触发止损(止损价={stop_price:.2f})'
            
            if exit_reason:
                self.order = self.close()
                direction = '平多' if self.position_type == 1 else '平空'
                self.log(f'【{direction}】{exit_reason}, 价格={self.data.close[0]:.2f}')
                self.position_type = 0
                self.entry_price = None
                self.entry_bar = None
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行: 价格={order.executed.price:.2f}')
            else:
                self.log(f'卖出执行: 价格={order.executed.price:.2f}')
        
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None
    
    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(f'交易完成: 毛利={trade.pnl:.2f}, 净利={trade.pnlcomm:.2f}')


class MomentumFixHold(bt.Strategy):
    """
    动量固定持有策略
    
    参数:
        lookback: 动量回看周期
        threshold: 入场阈值（百分比，如 0.02 表示 2%）
        hold_days: 固定持有天数
        atr_period: ATR 计算周期
        stop_atr_mult: 止损 ATR 倍数
        print_log: 是否打印日志
    
    推荐参数范围:
        lookback: 3, 5, 7
        threshold: 0.01, 0.02, 0.03 (1%, 2%, 3%)
        hold_days: 3, 5, 7, 10
        atr_period: 10, 14, 20
        stop_atr_mult: 1.5, 2, 2.5
    """
    params = dict(
        lookback=5,         # k: 动量回看周期
        threshold=0.02,     # T_up: 入场阈值（2%）
        hold_days=5,        # H: 固定持有天数
        atr_period=14,      # ATR 周期
        stop_atr_mult=2.0,  # K: 止损 ATR 倍数
        print_log=False,
    )
    
    def __init__(self):
        # 动量指标：k 日收益率（ROC 返回百分比，需要 /100）
        self.momentum = bt.indicators.ROC(self.data.close, period=self.p.lookback)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        # 状态
        self.entry_price = None
        self.entry_bar = None
        self.order = None
    
    def log(self, txt, dt=None):
        if self.p.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            # 多头入场：k 日动量超过阈值
            momentum_pct = self.momentum[0] / 100  # ROC 返回的是百分比值
            
            if momentum_pct > self.p.threshold:
                self.order = self.buy()
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.log(f'动量买入: 价格={self.data.close[0]:.2f}, '
                        f'{self.p.lookback}日动量={momentum_pct*100:.2f}%')
        
        else:
            hold_days = len(self) - self.entry_bar
            stop_price = self.entry_price - self.p.stop_atr_mult * self.atr[0]
            
            exit_reason = None
            
            if hold_days >= self.p.hold_days:
                exit_reason = f'持有{hold_days}天到期'
            elif self.data.close[0] < stop_price:
                exit_reason = f'触发止损(止损价={stop_price:.2f})'
            
            if exit_reason:
                self.order = self.close()
                self.log(f'卖出: {exit_reason}, 价格={self.data.close[0]:.2f}')
                self.entry_price = None
                self.entry_bar = None
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行: 价格={order.executed.price:.2f}')
            else:
                self.log(f'卖出执行: 价格={order.executed.price:.2f}')
        
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None
    
    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(f'交易完成: 毛利={trade.pnl:.2f}, 净利={trade.pnlcomm:.2f}')


class MomentumReversal(bt.Strategy):
    """
    动量反转策略（超跌反弹）
    
    入场信号：N 日动量低于负阈值（超跌）
    出场信号：固定持有到期 或 止损
    """
    params = dict(
        lookback=5,
        threshold=-0.03,    # 下跌 3% 视为超跌
        hold_days=3,        # 持有天数较短
        atr_period=14,
        stop_atr_mult=1.5,
        print_log=False,
    )
    
    def __init__(self):
        self.momentum = bt.indicators.ROC(self.data.close, period=self.p.lookback)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        self.entry_price = None
        self.entry_bar = None
        self.order = None
    
    def log(self, txt, dt=None):
        if self.p.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            momentum_pct = self.momentum[0] / 100
            
            # 超跌买入
            if momentum_pct < self.p.threshold:
                self.order = self.buy()
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.log(f'超跌买入: 动量={momentum_pct*100:.2f}%')
        
        else:
            hold_days = len(self) - self.entry_bar
            stop_price = self.entry_price - self.p.stop_atr_mult * self.atr[0]
            
            should_exit = (
                hold_days >= self.p.hold_days or
                self.data.close[0] < stop_price
            )
            
            if should_exit:
                self.order = self.close()
                self.entry_price = None
                self.entry_bar = None
    
    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None


class DualMomentum(bt.Strategy):
    """
    双动量策略
    
    同时考虑绝对动量（自身涨跌）和相对强度
    入场：短期动量 > 0 且 短期动量 > 长期动量
    """
    params = dict(
        short_lookback=5,
        long_lookback=20,
        threshold=0.01,
        hold_days=5,
        atr_period=14,
        stop_atr_mult=2.0,
        print_log=False,
    )
    
    def __init__(self):
        self.mom_short = bt.indicators.ROC(self.data.close, period=self.p.short_lookback)
        self.mom_long = bt.indicators.ROC(self.data.close, period=self.p.long_lookback)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        self.entry_price = None
        self.entry_bar = None
        self.order = None
    
    def log(self, txt, dt=None):
        if self.p.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            mom_short_pct = self.mom_short[0] / 100
            mom_long_pct = self.mom_long[0] / 100
            
            # 短期动量为正，且短期强于长期
            if mom_short_pct > self.p.threshold and mom_short_pct > mom_long_pct:
                self.order = self.buy()
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.log(f'双动量买入: 短期={mom_short_pct*100:.2f}%, '
                        f'长期={mom_long_pct*100:.2f}%')
        
        else:
            hold_days = len(self) - self.entry_bar
            stop_price = self.entry_price - self.p.stop_atr_mult * self.atr[0]
            
            should_exit = (
                hold_days >= self.p.hold_days or
                self.data.close[0] < stop_price
            )
            
            if should_exit:
                self.order = self.close()
                self.entry_price = None
                self.entry_bar = None
    
    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None
