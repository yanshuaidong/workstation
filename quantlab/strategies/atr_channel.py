"""
ATR 通道趋势策略族

核心理念：用 ATR 做价格通道，捕捉波动放大后的趋势。

多头入场信号：收盘价突破上轨（MA + ATR * 倍数）
空头入场信号：收盘价跌破下轨（MA - ATR * 倍数）
出场信号：
  1. 回归均线
  2. 突破/跌破反向轨道
  3. 持有超过最大天数
"""
import backtrader as bt


class ATRChannelTrendDual(bt.Strategy):
    """
    ATR 通道策略（多空双向版本）
    
    多头：突破上轨 → 做多
    空头：跌破下轨 → 做空
    
    参数:
        ma_period: 基础均线周期
        atr_period: ATR 计算周期
        channel_mult: 通道 ATR 倍数
        max_hold: 最大持有天数
        print_log: 是否打印日志
    """
    params = dict(
        ma_period=10,
        atr_period=14,
        channel_mult=2.0,
        max_hold=10,
        print_log=False,
    )
    
    def __init__(self):
        self.ma = bt.indicators.SMA(self.data.close, period=self.p.ma_period)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        self.upper = self.ma + self.p.channel_mult * self.atr
        self.lower = self.ma - self.p.channel_mult * self.atr
        
        self.position_type = 0  # 1=多头, -1=空头, 0=空仓
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
            # 多头入场：突破上轨
            if self.data.close[0] > self.upper[-1]:
                self.order = self.buy()
                self.position_type = 1
                self.entry_bar = len(self)
                self.log(f'【突破上轨做多】价格={self.data.close[0]:.2f}, '
                        f'上轨={self.upper[-1]:.2f}')
            
            # 空头入场：跌破下轨
            elif self.data.close[0] < self.lower[-1]:
                self.order = self.sell()
                self.position_type = -1
                self.entry_bar = len(self)
                self.log(f'【跌破下轨做空】价格={self.data.close[0]:.2f}, '
                        f'下轨={self.lower[-1]:.2f}')
        
        else:
            hold_days = len(self) - self.entry_bar
            exit_reason = None
            
            if self.position_type == 1:  # 多头持仓
                if self.data.close[0] < self.ma[0]:
                    exit_reason = '跌回均线'
                elif self.data.close[0] < self.lower[0]:
                    exit_reason = '跌破下轨'
                elif hold_days >= self.p.max_hold:
                    exit_reason = f'持有{hold_days}天达上限'
            
            else:  # 空头持仓
                if self.data.close[0] > self.ma[0]:
                    exit_reason = '涨回均线'
                elif self.data.close[0] > self.upper[0]:
                    exit_reason = '突破上轨'
                elif hold_days >= self.p.max_hold:
                    exit_reason = f'持有{hold_days}天达上限'
            
            if exit_reason:
                self.order = self.close()
                direction = '平多' if self.position_type == 1 else '平空'
                self.log(f'【{direction}】{exit_reason}, 价格={self.data.close[0]:.2f}')
                self.position_type = 0
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


class ATRChannelTrend(bt.Strategy):
    """
    ATR 通道策略
    
    参数:
        ma_period: 基础均线周期
        atr_period: ATR 计算周期
        channel_mult: 通道 ATR 倍数
        max_hold: 最大持有天数
        print_log: 是否打印日志
    
    推荐参数范围:
        ma_period: 10, 20
        atr_period: 10, 14, 20
        channel_mult: 1.5, 2, 2.5
        max_hold: 5, 7, 10
    """
    params = dict(
        ma_period=10,       # MA 周期
        atr_period=14,      # ATR 周期
        channel_mult=2.0,   # C: 通道 ATR 倍数
        max_hold=10,        # H: 最大持有天数
        print_log=False,
    )
    
    def __init__(self):
        # 指标
        self.ma = bt.indicators.SMA(self.data.close, period=self.p.ma_period)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        # 通道
        self.upper = self.ma + self.p.channel_mult * self.atr
        self.lower = self.ma - self.p.channel_mult * self.atr
        
        # 状态
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
            # 多头入场：突破上轨
            if self.data.close[0] > self.upper[-1]:
                self.order = self.buy()
                self.entry_bar = len(self)
                self.log(f'突破上轨买入: 价格={self.data.close[0]:.2f}, '
                        f'上轨={self.upper[-1]:.2f}')
        
        else:
            hold_days = len(self) - self.entry_bar
            
            exit_reason = None
            
            if self.data.close[0] < self.ma[0]:
                exit_reason = '跌回均线'
            elif self.data.close[0] < self.lower[0]:
                exit_reason = '跌破下轨'
            elif hold_days >= self.p.max_hold:
                exit_reason = f'持有{hold_days}天达上限'
            
            if exit_reason:
                self.order = self.close()
                self.log(f'卖出: {exit_reason}, 价格={self.data.close[0]:.2f}')
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


class KeltnerChannel(bt.Strategy):
    """
    Keltner 通道策略
    
    使用 EMA 作为中轨，ATR 作为通道宽度
    """
    params = dict(
        ema_period=20,
        atr_period=10,
        channel_mult=2.0,
        max_hold=10,
        print_log=False,
    )
    
    def __init__(self):
        self.ema = bt.indicators.EMA(self.data.close, period=self.p.ema_period)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        self.upper = self.ema + self.p.channel_mult * self.atr
        self.lower = self.ema - self.p.channel_mult * self.atr
        
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
            # 突破上轨买入
            if self.data.close[0] > self.upper[-1]:
                self.order = self.buy()
                self.entry_bar = len(self)
                self.log(f'Keltner突破买入: 价格={self.data.close[0]:.2f}')
        
        else:
            hold_days = len(self) - self.entry_bar
            
            should_exit = (
                self.data.close[0] < self.ema[0] or
                self.data.close[0] < self.lower[0] or
                hold_days >= self.p.max_hold
            )
            
            if should_exit:
                self.order = self.close()
                self.entry_bar = None
    
    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None


class ATRBreakoutWithTrail(bt.Strategy):
    """
    ATR 通道突破 + 移动止损
    
    入场：突破上轨
    出场：移动止损（跟踪最高价 - ATR * 倍数）
    """
    params = dict(
        ma_period=10,
        atr_period=14,
        channel_mult=2.0,
        trail_mult=1.5,     # 移动止损 ATR 倍数
        max_hold=15,
        print_log=False,
    )
    
    def __init__(self):
        self.ma = bt.indicators.SMA(self.data.close, period=self.p.ma_period)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        self.upper = self.ma + self.p.channel_mult * self.atr
        
        self.entry_bar = None
        self.highest_since_entry = None
        self.order = None
    
    def log(self, txt, dt=None):
        if self.p.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            if self.data.close[0] > self.upper[-1]:
                self.order = self.buy()
                self.entry_bar = len(self)
                self.highest_since_entry = self.data.high[0]
                self.log(f'ATR突破买入: 价格={self.data.close[0]:.2f}')
        
        else:
            # 更新最高价
            if self.data.high[0] > self.highest_since_entry:
                self.highest_since_entry = self.data.high[0]
            
            hold_days = len(self) - self.entry_bar
            
            # 移动止损价
            trail_stop = self.highest_since_entry - self.p.trail_mult * self.atr[0]
            
            should_exit = (
                self.data.close[0] < trail_stop or
                hold_days >= self.p.max_hold
            )
            
            if should_exit:
                self.order = self.close()
                self.log(f'移动止损卖出: 价格={self.data.close[0]:.2f}, '
                        f'止损价={trail_stop:.2f}')
                self.entry_bar = None
                self.highest_since_entry = None
    
    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None
