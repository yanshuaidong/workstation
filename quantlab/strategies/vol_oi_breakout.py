"""
增仓放量突破策略族 (Volume-OI Breakout)

核心理念：三重过滤捕捉高质量趋势日
  1. 价格突破：收盘价突破 N 日高/低点
  2. 成交量放大：今日成交量 > N 日均量 × K 倍
  3. 持仓量增加：今日OI > 昨日OI × (1 + 阈值)

多头入场：突破N日高点 + 放量 + 增仓
空头入场：跌破N日低点 + 放量 + 增仓

适用场景：3-10 日的单边趋势交易，信号少但质量高
"""
import backtrader as bt


class VolOIBreakoutDual(bt.Strategy):
    """
    增仓放量突破策略（多空双向版本）
    
    入场条件（三重过滤）：
      1. 价格突破 N 日最高/最低价
      2. 成交量 > N 日均量 × vol_mult（放量）
      3. 持仓量变化 > oi_threshold（增仓）
    
    出场条件：
      1. 跌破/突破 M 日低/高点
      2. 持有超过最大天数
      3. 止损（ATR 倍数）
    
    参数:
        n_break: 突破周期
        n_exit: 平仓周期
        vol_period: 成交量均线周期
        vol_mult: 成交量放大倍数（如 1.5 表示 1.5 倍于均量）
        oi_threshold: 持仓量增长阈值（如 0.02 表示增长 2%）
        atr_period: ATR 计算周期
        max_hold: 最大持有天数
        stop_atr_mult: 止损 ATR 倍数
        print_log: 是否打印日志
    
    推荐参数范围:
        n_break: 3, 5, 7
        n_exit: 3, 5
        vol_period: 5, 10, 20
        vol_mult: 1.2, 1.5, 2.0
        oi_threshold: 0.01, 0.02, 0.03 (1%, 2%, 3%)
        max_hold: 5, 7, 10
        stop_atr_mult: 1.5, 2.0, 2.5
    """
    params = dict(
        n_break=5,          # N: 突破周期
        n_exit=3,           # M: 平仓周期
        vol_period=10,      # 成交量均线周期
        vol_mult=1.5,       # 成交量放大倍数
        oi_threshold=0.02,  # 持仓量增长阈值 (2%)
        atr_period=14,      # ATR 周期
        max_hold=7,         # 最大持有天数
        stop_atr_mult=2.0,  # 止损 ATR 倍数
        print_log=False,
    )
    
    def __init__(self):
        # 价格突破指标
        self.highest = bt.indicators.Highest(self.data.high, period=self.p.n_break)
        self.lowest = bt.indicators.Lowest(self.data.low, period=self.p.n_break)
        
        # 平仓用的高低点
        self.highest_exit = bt.indicators.Highest(self.data.high, period=self.p.n_exit)
        self.lowest_exit = bt.indicators.Lowest(self.data.low, period=self.p.n_exit)
        
        # 成交量均线
        self.vol_ma = bt.indicators.SMA(self.data.volume, period=self.p.vol_period)
        
        # ATR
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
    
    def _check_volume_condition(self):
        """检查放量条件：今日成交量 > N日均量 × K"""
        if self.vol_ma[0] <= 0:
            return False
        return self.data.volume[0] > self.vol_ma[0] * self.p.vol_mult
    
    def _check_oi_condition(self):
        """检查增仓条件：今日OI > 昨日OI × (1 + 阈值)"""
        # 使用 openinterest 数据
        if len(self.data) < 2:
            return False
        
        oi_today = self.data.openinterest[0]
        oi_yesterday = self.data.openinterest[-1]
        
        if oi_yesterday <= 0:
            return False
        
        # 计算持仓量变化率
        oi_change = (oi_today - oi_yesterday) / oi_yesterday
        return oi_change > self.p.oi_threshold
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            # 检查放量和增仓条件
            vol_ok = self._check_volume_condition()
            oi_ok = self._check_oi_condition()
            
            # 多头入场：突破N日高点 + 放量 + 增仓
            if (self.data.close[0] > self.highest[-1] and vol_ok and oi_ok):
                self.order = self.buy()
                self.position_type = 1
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                
                vol_ratio = self.data.volume[0] / self.vol_ma[0] if self.vol_ma[0] > 0 else 0
                oi_change = ((self.data.openinterest[0] - self.data.openinterest[-1]) 
                            / self.data.openinterest[-1] * 100) if self.data.openinterest[-1] > 0 else 0
                
                self.log(f'【增仓放量做多】价格={self.data.close[0]:.2f}, '
                        f'{self.p.n_break}日高点={self.highest[-1]:.2f}, '
                        f'量比={vol_ratio:.2f}, OI变化={oi_change:.2f}%')
            
            # 空头入场：跌破N日低点 + 放量 + 增仓
            elif (self.data.close[0] < self.lowest[-1] and vol_ok and oi_ok):
                self.order = self.sell()
                self.position_type = -1
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                
                vol_ratio = self.data.volume[0] / self.vol_ma[0] if self.vol_ma[0] > 0 else 0
                oi_change = ((self.data.openinterest[0] - self.data.openinterest[-1]) 
                            / self.data.openinterest[-1] * 100) if self.data.openinterest[-1] > 0 else 0
                
                self.log(f'【增仓放量做空】价格={self.data.close[0]:.2f}, '
                        f'{self.p.n_break}日低点={self.lowest[-1]:.2f}, '
                        f'量比={vol_ratio:.2f}, OI变化={oi_change:.2f}%')
        
        else:
            hold_days = len(self) - self.entry_bar
            exit_reason = None
            
            if self.position_type == 1:  # 多头持仓
                stop_price = self.entry_price - self.p.stop_atr_mult * self.atr[0]
                
                if self.data.close[0] < self.lowest_exit[-1]:
                    exit_reason = f'跌破{self.p.n_exit}日低点'
                elif hold_days >= self.p.max_hold:
                    exit_reason = f'持有{hold_days}天达上限'
                elif self.data.close[0] < stop_price:
                    exit_reason = f'触发止损(止损价={stop_price:.2f})'
            
            else:  # 空头持仓 (position_type == -1)
                stop_price = self.entry_price + self.p.stop_atr_mult * self.atr[0]
                
                if self.data.close[0] > self.highest_exit[-1]:
                    exit_reason = f'突破{self.p.n_exit}日高点'
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


class VolOIBreakout(bt.Strategy):
    """
    增仓放量突破策略（仅做多版本）
    
    入场条件：
      1. 收盘价突破 N 日最高价
      2. 成交量 > N 日均量 × vol_mult
      3. 持仓量变化 > oi_threshold
    
    出场条件：
      1. 跌破 M 日低点
      2. 持有超过最大天数
      3. 止损（ATR 倍数）
    """
    params = dict(
        n_break=5,
        n_exit=3,
        vol_period=10,
        vol_mult=1.5,
        oi_threshold=0.02,
        atr_period=14,
        max_hold=7,
        stop_atr_mult=2.0,
        print_log=False,
    )
    
    def __init__(self):
        self.highest = bt.indicators.Highest(self.data.high, period=self.p.n_break)
        self.lowest = bt.indicators.Lowest(self.data.low, period=self.p.n_exit)
        self.vol_ma = bt.indicators.SMA(self.data.volume, period=self.p.vol_period)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        self.entry_price = None
        self.entry_bar = None
        self.order = None
    
    def log(self, txt, dt=None):
        if self.p.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def _check_volume_condition(self):
        """检查放量条件"""
        if self.vol_ma[0] <= 0:
            return False
        return self.data.volume[0] > self.vol_ma[0] * self.p.vol_mult
    
    def _check_oi_condition(self):
        """检查增仓条件"""
        if len(self.data) < 2:
            return False
        
        oi_today = self.data.openinterest[0]
        oi_yesterday = self.data.openinterest[-1]
        
        if oi_yesterday <= 0:
            return False
        
        oi_change = (oi_today - oi_yesterday) / oi_yesterday
        return oi_change > self.p.oi_threshold
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            vol_ok = self._check_volume_condition()
            oi_ok = self._check_oi_condition()
            
            # 多头入场：突破 + 放量 + 增仓
            if (self.data.close[0] > self.highest[-1] and vol_ok and oi_ok):
                self.order = self.buy()
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                
                vol_ratio = self.data.volume[0] / self.vol_ma[0] if self.vol_ma[0] > 0 else 0
                self.log(f'买入信号: 价格={self.data.close[0]:.2f}, 量比={vol_ratio:.2f}')
        
        else:
            hold_days = len(self) - self.entry_bar
            stop_price = self.entry_price - self.p.stop_atr_mult * self.atr[0]
            
            exit_reason = None
            
            if self.data.close[0] < self.lowest[-1]:
                exit_reason = f'跌破{self.p.n_exit}日低点'
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


class VolOIBreakoutRelaxed(bt.Strategy):
    """
    增仓放量突破策略（放宽版本）
    
    适用于信号过少的情况，放宽 OI 条件：
      - OI 条件：只要求 OI 不减少（而非增长超过阈值）
    
    或者使用累计增仓：
      - 检查最近 N 日 OI 累计是否增加
    """
    params = dict(
        n_break=5,
        n_exit=3,
        vol_period=10,
        vol_mult=1.3,           # 放宽：1.3 倍
        oi_lookback=3,          # OI 回看周期
        oi_threshold=0.0,       # 只要求 OI 不减少
        atr_period=14,
        max_hold=7,
        stop_atr_mult=2.0,
        print_log=False,
    )
    
    def __init__(self):
        self.highest = bt.indicators.Highest(self.data.high, period=self.p.n_break)
        self.lowest = bt.indicators.Lowest(self.data.low, period=self.p.n_break)
        self.highest_exit = bt.indicators.Highest(self.data.high, period=self.p.n_exit)
        self.lowest_exit = bt.indicators.Lowest(self.data.low, period=self.p.n_exit)
        self.vol_ma = bt.indicators.SMA(self.data.volume, period=self.p.vol_period)
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        
        self.position_type = 0
        self.entry_price = None
        self.entry_bar = None
        self.order = None
    
    def log(self, txt, dt=None):
        if self.p.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
    
    def _check_volume_condition(self):
        if self.vol_ma[0] <= 0:
            return False
        return self.data.volume[0] > self.vol_ma[0] * self.p.vol_mult
    
    def _check_oi_condition(self):
        """检查累计增仓条件：最近 N 日 OI 累计变化 > 阈值"""
        if len(self.data) < self.p.oi_lookback + 1:
            return False
        
        oi_today = self.data.openinterest[0]
        oi_n_days_ago = self.data.openinterest[-self.p.oi_lookback]
        
        if oi_n_days_ago <= 0:
            return False
        
        oi_change = (oi_today - oi_n_days_ago) / oi_n_days_ago
        return oi_change >= self.p.oi_threshold
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            vol_ok = self._check_volume_condition()
            oi_ok = self._check_oi_condition()
            
            if (self.data.close[0] > self.highest[-1] and vol_ok and oi_ok):
                self.order = self.buy()
                self.position_type = 1
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.log(f'【放宽版做多】价格={self.data.close[0]:.2f}')
            
            elif (self.data.close[0] < self.lowest[-1] and vol_ok and oi_ok):
                self.order = self.sell()
                self.position_type = -1
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.log(f'【放宽版做空】价格={self.data.close[0]:.2f}')
        
        else:
            hold_days = len(self) - self.entry_bar
            exit_reason = None
            
            if self.position_type == 1:
                stop_price = self.entry_price - self.p.stop_atr_mult * self.atr[0]
                if self.data.close[0] < self.lowest_exit[-1]:
                    exit_reason = '跌破低点'
                elif hold_days >= self.p.max_hold:
                    exit_reason = '持有到期'
                elif self.data.close[0] < stop_price:
                    exit_reason = '止损'
            else:
                stop_price = self.entry_price + self.p.stop_atr_mult * self.atr[0]
                if self.data.close[0] > self.highest_exit[-1]:
                    exit_reason = '突破高点'
                elif hold_days >= self.p.max_hold:
                    exit_reason = '持有到期'
                elif self.data.close[0] > stop_price:
                    exit_reason = '止损'
            
            if exit_reason:
                self.order = self.close()
                self.log(f'【平仓】{exit_reason}')
                self.position_type = 0
                self.entry_price = None
                self.entry_bar = None
    
    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None
