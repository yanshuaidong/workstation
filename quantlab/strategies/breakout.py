"""
短周期突破策略族

核心理念：Donchian 突破的短周期版本，捕捉 3-10 日单边走势。

多头入场信号：收盘价突破 N 日最高价
空头入场信号：收盘价跌破 N 日最低价
出场信号：
  1. 跌破/突破 M 日低/高点
  2. 持有超过最大天数
  3. 止损（ATR 倍数）
"""
import backtrader as bt


class ShortTermBreakoutDual(bt.Strategy):
    """
    短周期突破策略（多空双向版本）
    
    多头：收盘价突破 N 日最高价 → 做多
    空头：收盘价跌破 N 日最低价 → 做空
    
    参数:
        n_high: 突破周期（HH_N）
        n_low: 平仓周期（LL_M）
        atr_period: ATR 计算周期
        max_hold: 最大持有天数
        stop_atr_mult: 止损 ATR 倍数
        print_log: 是否打印日志
    """
    params = dict(
        n_high=5,           # N: 突破周期
        n_low=3,            # M: 平仓周期
        atr_period=14,      # L: ATR 周期
        max_hold=7,         # H: 最大持有天数
        stop_atr_mult=2.0,  # K: 止损 ATR 倍数
        print_log=False,
    )
    
    def __init__(self):
        # 指标
        self.highest = bt.indicators.Highest(self.data.high, period=self.p.n_high)
        self.lowest = bt.indicators.Lowest(self.data.low, period=self.p.n_low)
        self.highest_exit = bt.indicators.Highest(self.data.high, period=self.p.n_low)
        self.lowest_exit = bt.indicators.Lowest(self.data.low, period=self.p.n_high)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        # 状态: 1=多头, -1=空头, 0=空仓
        self.position_type = 0
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
            # 多头入场：收盘价突破 N 日最高
            if self.data.close[0] > self.highest[-1]:
                self.order = self.buy()
                self.position_type = 1
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.log(f'【做多】价格={self.data.close[0]:.2f}, '
                        f'{self.p.n_high}日高点={self.highest[-1]:.2f}')
            
            # 空头入场：收盘价跌破 N 日最低
            elif self.data.close[0] < self.lowest_exit[-1]:
                self.order = self.sell()
                self.position_type = -1
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.log(f'【做空】价格={self.data.close[0]:.2f}, '
                        f'{self.p.n_high}日低点={self.lowest_exit[-1]:.2f}')
        
        else:
            hold_days = len(self) - self.entry_bar
            exit_reason = None
            
            if self.position_type == 1:  # 多头持仓
                stop_price = self.entry_price - self.p.stop_atr_mult * self.atr[0]
                
                if self.data.close[0] < self.lowest[-1]:
                    exit_reason = f'跌破{self.p.n_low}日低点'
                elif hold_days >= self.p.max_hold:
                    exit_reason = f'持有{hold_days}天达上限'
                elif self.data.close[0] < stop_price:
                    exit_reason = f'触发止损(止损价={stop_price:.2f})'
            
            else:  # 空头持仓 (position_type == -1)
                stop_price = self.entry_price + self.p.stop_atr_mult * self.atr[0]
                
                if self.data.close[0] > self.highest_exit[-1]:
                    exit_reason = f'突破{self.p.n_low}日高点'
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


class ShortTermBreakout(bt.Strategy):
    """
    短周期突破策略
    
    参数:
        n_high: 突破周期（HH_N）
        n_low: 平仓周期（LL_M）
        atr_period: ATR 计算周期
        max_hold: 最大持有天数
        stop_atr_mult: 止损 ATR 倍数
        print_log: 是否打印日志
    
    推荐参数范围:
        n_high: 3, 5, 7, 10
        n_low: N/2 or N (如 3, 5)
        atr_period: 10, 14, 20
        max_hold: 5, 7, 10
        stop_atr_mult: 1.5, 2, 2.5
    """
    params = dict(
        n_high=5,           # N: 突破周期
        n_low=3,            # M: 平仓周期
        atr_period=14,      # L: ATR 周期
        max_hold=7,         # H: 最大持有天数
        stop_atr_mult=2.0,  # K: 止损 ATR 倍数
        print_log=False,    # 是否打印日志
    )
    
    def __init__(self):
        # 指标
        self.highest = bt.indicators.Highest(self.data.high, period=self.p.n_high)
        self.lowest = bt.indicators.Lowest(self.data.low, period=self.p.n_low)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        # 状态
        self.entry_price = None
        self.entry_bar = None
        self.order = None
    
    def log(self, txt, dt=None):
        """日志输出"""
        if self.p.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def next(self):
        if self.order:  # 有未完成订单，跳过
            return
        
        if not self.position:  # 无持仓
            # 多头入场：收盘价突破 N 日最高
            if self.data.close[0] > self.highest[-1]:
                self.order = self.buy()
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.log(f'买入信号: 价格={self.data.close[0]:.2f}, '
                        f'{self.p.n_high}日高点={self.highest[-1]:.2f}')
        
        else:  # 有持仓
            hold_days = len(self) - self.entry_bar
            stop_price = self.entry_price - self.p.stop_atr_mult * self.atr[0]
            
            # 出场条件
            exit_reason = None
            
            if self.data.close[0] < self.lowest[-1]:
                exit_reason = f'跌破{self.p.n_low}日低点'
            elif hold_days >= self.p.max_hold:
                exit_reason = f'持有{hold_days}天达上限'
            elif self.data.close[0] < stop_price:
                exit_reason = f'触发止损(止损价={stop_price:.2f})'
            
            if exit_reason:
                self.order = self.close()
                self.log(f'卖出信号: {exit_reason}, 价格={self.data.close[0]:.2f}')
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


class ShortTermBreakoutShort(bt.Strategy):
    """
    短周期突破策略（做空版本）
    
    入场信号：收盘价跌破 N 日最低价
    出场信号：
      1. 突破 M 日最高价
      2. 持有超过最大天数
      3. 止损（ATR 倍数）
    """
    params = dict(
        n_low=5,            # N: 突破周期（跌破N日低点）
        n_high=3,           # M: 平仓周期（突破M日高点）
        atr_period=14,      # L: ATR 周期
        max_hold=7,         # H: 最大持有天数
        stop_atr_mult=2.0,  # K: 止损 ATR 倍数
        print_log=False,
    )
    
    def __init__(self):
        self.highest = bt.indicators.Highest(self.data.high, period=self.p.n_high)
        self.lowest = bt.indicators.Lowest(self.data.low, period=self.p.n_low)
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
            # 空头入场：收盘价跌破 N 日最低
            if self.data.close[0] < self.lowest[-1]:
                self.order = self.sell()
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.log(f'做空信号: 价格={self.data.close[0]:.2f}')
        
        else:
            hold_days = len(self) - self.entry_bar
            stop_price = self.entry_price + self.p.stop_atr_mult * self.atr[0]
            
            exit_reason = None
            
            if self.data.close[0] > self.highest[-1]:
                exit_reason = f'突破{self.p.n_high}日高点'
            elif hold_days >= self.p.max_hold:
                exit_reason = f'持有{hold_days}天达上限'
            elif self.data.close[0] > stop_price:
                exit_reason = f'触发止损'
            
            if exit_reason:
                self.order = self.close()
                self.log(f'平空信号: {exit_reason}')
                self.entry_price = None
                self.entry_bar = None
    
    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None
