"""
短周期均线趋势策略族

核心理念：短均线跟随，适合 3-10 日趋势。

多头入场信号：短期均线上穿长期均线（金叉）
空头入场信号：短期均线下穿长期均线（死叉）
出场信号：
  1. 反向交叉
  2. 持有超过最大天数
  3. 止损（ATR 倍数）
"""
import backtrader as bt


class ShortTermMATrendDual(bt.Strategy):
    """
    短周期均线趋势策略（多空双向版本）
    
    多头：金叉（短均线上穿长均线）→ 做多
    空头：死叉（短均线下穿长均线）→ 做空
    
    参数:
        ma_short: 短期均线周期
        ma_long: 长期均线周期
        atr_period: ATR 计算周期
        max_hold: 最大持有天数
        stop_atr_mult: 止损 ATR 倍数
        print_log: 是否打印日志
    """
    params = dict(
        ma_short=5,
        ma_long=10,
        atr_period=14,
        max_hold=7,
        stop_atr_mult=2.0,
        print_log=False,
    )
    
    def __init__(self):
        self.ma_short = bt.indicators.SMA(self.data.close, period=self.p.ma_short)
        self.ma_long = bt.indicators.SMA(self.data.close, period=self.p.ma_long)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        self.crossover = bt.indicators.CrossOver(self.ma_short, self.ma_long)
        
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
            # 金叉做多
            if self.crossover[0] > 0:
                self.order = self.buy()
                self.position_type = 1
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.log(f'【金叉做多】价格={self.data.close[0]:.2f}, '
                        f'MA{self.p.ma_short}={self.ma_short[0]:.2f}, '
                        f'MA{self.p.ma_long}={self.ma_long[0]:.2f}')
            
            # 死叉做空
            elif self.crossover[0] < 0:
                self.order = self.sell()
                self.position_type = -1
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.log(f'【死叉做空】价格={self.data.close[0]:.2f}, '
                        f'MA{self.p.ma_short}={self.ma_short[0]:.2f}, '
                        f'MA{self.p.ma_long}={self.ma_long[0]:.2f}')
        
        else:
            hold_days = len(self) - self.entry_bar
            exit_reason = None
            
            if self.position_type == 1:  # 多头持仓
                stop_price = self.entry_price - self.p.stop_atr_mult * self.atr[0]
                
                if self.crossover[0] < 0:
                    exit_reason = '死叉'
                elif hold_days >= self.p.max_hold:
                    exit_reason = f'持有{hold_days}天达上限'
                elif self.data.close[0] < stop_price:
                    exit_reason = f'触发止损(止损价={stop_price:.2f})'
            
            else:  # 空头持仓
                stop_price = self.entry_price + self.p.stop_atr_mult * self.atr[0]
                
                if self.crossover[0] > 0:
                    exit_reason = '金叉'
                elif hold_days >= self.p.max_hold:
                    exit_reason = f'持有{hold_days}天达上限'
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


class ShortTermMATrend(bt.Strategy):
    """
    短周期均线趋势策略
    
    参数:
        ma_short: 短期均线周期
        ma_long: 长期均线周期
        atr_period: ATR 计算周期
        max_hold: 最大持有天数
        stop_atr_mult: 止损 ATR 倍数
        print_log: 是否打印日志
    
    推荐参数范围:
        ma_short: 3, 4, 5
        ma_long: 8, 10, 12, 15
        atr_period: 10, 14, 20
        max_hold: 5, 7, 10
        stop_atr_mult: 1.5, 2, 2.5
    """
    params = dict(
        ma_short=5,         # n1: 短期均线周期
        ma_long=10,         # n2: 长期均线周期
        atr_period=14,      # L: ATR 周期
        max_hold=7,         # H: 最大持有天数
        stop_atr_mult=2.0,  # K: 止损 ATR 倍数
        print_log=False,
    )
    
    def __init__(self):
        # 指标
        self.ma_short = bt.indicators.SMA(self.data.close, period=self.p.ma_short)
        self.ma_long = bt.indicators.SMA(self.data.close, period=self.p.ma_long)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        # 金叉死叉信号
        self.crossover = bt.indicators.CrossOver(self.ma_short, self.ma_long)
        
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
            # 多头入场：短均线上穿长均线（金叉）
            if self.crossover[0] > 0:
                self.order = self.buy()
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.log(f'金叉买入: 价格={self.data.close[0]:.2f}, '
                        f'MA{self.p.ma_short}={self.ma_short[0]:.2f}, '
                        f'MA{self.p.ma_long}={self.ma_long[0]:.2f}')
        
        else:
            hold_days = len(self) - self.entry_bar
            stop_price = self.entry_price - self.p.stop_atr_mult * self.atr[0]
            
            exit_reason = None
            
            if self.crossover[0] < 0:
                exit_reason = '死叉'
            elif hold_days >= self.p.max_hold:
                exit_reason = f'持有{hold_days}天达上限'
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


class ShortTermMATrendEMA(bt.Strategy):
    """
    短周期 EMA 趋势策略（使用指数移动平均线）
    """
    params = dict(
        ma_short=5,
        ma_long=10,
        atr_period=14,
        max_hold=7,
        stop_atr_mult=2.0,
        print_log=False,
    )
    
    def __init__(self):
        # 使用 EMA 替代 SMA
        self.ma_short = bt.indicators.EMA(self.data.close, period=self.p.ma_short)
        self.ma_long = bt.indicators.EMA(self.data.close, period=self.p.ma_long)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        self.crossover = bt.indicators.CrossOver(self.ma_short, self.ma_long)
        
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
            if self.crossover[0] > 0:
                self.order = self.buy()
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.log(f'EMA金叉买入: 价格={self.data.close[0]:.2f}')
        
        else:
            hold_days = len(self) - self.entry_bar
            stop_price = self.entry_price - self.p.stop_atr_mult * self.atr[0]
            
            should_exit = (
                self.crossover[0] < 0 or
                hold_days >= self.p.max_hold or
                self.data.close[0] < stop_price
            )
            
            if should_exit:
                self.order = self.close()
                self.entry_price = None
                self.entry_bar = None
    
    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None


class TripleMA(bt.Strategy):
    """
    三均线策略
    
    入场：短期均线 > 中期均线 > 长期均线
    出场：短期均线 < 中期均线 或 触发止损
    """
    params = dict(
        ma_short=5,
        ma_mid=10,
        ma_long=20,
        atr_period=14,
        max_hold=10,
        stop_atr_mult=2.0,
        print_log=False,
    )
    
    def __init__(self):
        self.ma_short = bt.indicators.SMA(self.data.close, period=self.p.ma_short)
        self.ma_mid = bt.indicators.SMA(self.data.close, period=self.p.ma_mid)
        self.ma_long = bt.indicators.SMA(self.data.close, period=self.p.ma_long)
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
            # 多头排列：短 > 中 > 长
            if (self.ma_short[0] > self.ma_mid[0] > self.ma_long[0] and
                self.ma_short[-1] <= self.ma_mid[-1]):  # 刚刚形成多头排列
                self.order = self.buy()
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.log(f'三均线多头排列买入: 价格={self.data.close[0]:.2f}')
        
        else:
            hold_days = len(self) - self.entry_bar
            stop_price = self.entry_price - self.p.stop_atr_mult * self.atr[0]
            
            should_exit = (
                self.ma_short[0] < self.ma_mid[0] or
                hold_days >= self.p.max_hold or
                self.data.close[0] < stop_price
            )
            
            if should_exit:
                self.order = self.close()
                self.entry_price = None
                self.entry_bar = None
    
    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None
