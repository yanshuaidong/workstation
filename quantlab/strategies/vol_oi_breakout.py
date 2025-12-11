"""
增仓放量突破策略族 (Volume-OI Breakout)

核心理念：多重过滤捕捉高质量趋势日
  1. 价格突破：收盘价突破 N 日高/低点
  2. 成交量放大：今日成交量 > N 日均量 × K 倍
  3. 持仓量增加：累计OI变化 > 阈值
  4. 趋势过滤：均线判断大方向（改进版）
  5. 波动率过滤：确保有足够的波动空间（改进版）

多头入场：突破N日高点 + 放量 + 增仓 + 趋势向上
空头入场：跌破N日低点 + 放量 + 增仓 + 趋势向下

适用场景：3-10 日的单边趋势交易，信号少但质量高
"""
import backtrader as bt


class VolOIBreakoutDual(bt.Strategy):
    """
    增仓放量突破策略（多空双向改进版）
    
    【改进点】：
      1. 加入趋势过滤器（均线方向）- 只顺势交易
      2. 加入跟踪止损 - 盈利后动态保护利润
      3. 累计OI判断 - 使用多日OI变化，更稳健
      4. 波动率过滤 - ATR占价格比例，确保有行情
      5. 盈利保护 - 达到一定盈利后保本出场
    
    入场条件（五重过滤）：
      1. 价格突破 N 日最高/最低价
      2. 成交量 > N 日均量 × vol_mult（放量）
      3. 累计持仓量变化 > oi_threshold（增仓）
      4. 价格在趋势均线正确一侧（趋势过滤）
      5. ATR/价格 > 最小波动率（波动率过滤）
    
    出场条件：
      1. 跌破/突破 M 日低/高点
      2. 持有超过最大天数
      3. 初始止损（ATR 倍数）
      4. 跟踪止损（盈利后抬高止损位）
      5. 盈利保护（达到目标后保本）
    """
    params = dict(
        n_break=5,              # N: 突破周期
        n_exit=3,               # M: 平仓周期
        vol_period=10,          # 成交量均线周期
        vol_mult=1.5,           # 成交量放大倍数
        oi_lookback=3,          # OI 回看天数（累计）
        oi_threshold=0.02,      # 持仓量增长阈值 (2%)
        atr_period=14,          # ATR 周期
        max_hold=10,            # 最大持有天数
        stop_atr_mult=2.0,      # 初始止损 ATR 倍数
        # 改进参数
        trend_period=20,        # 趋势均线周期
        use_trend_filter=True,  # 是否使用趋势过滤
        min_atr_pct=0.01,       # 最小ATR百分比（波动率过滤）
        use_trailing_stop=True, # 是否使用跟踪止损
        trail_atr_mult=1.5,     # 跟踪止损 ATR 倍数
        profit_protect=1.5,     # 盈利保护：盈利达到N倍ATR后保本
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
        
        # 趋势均线（改进：趋势过滤）
        self.trend_ma = bt.indicators.SMA(self.data.close, period=self.p.trend_period)
        
        # 状态变量
        self.position_type = 0  # 1=多头, -1=空头, 0=空仓
        self.entry_price = None
        self.entry_bar = None
        self.entry_atr = None   # 入场时的ATR，用于计算止损
        self.highest_since_entry = None  # 入场后最高价（跟踪止损用）
        self.lowest_since_entry = None   # 入场后最低价（跟踪止损用）
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
        """检查累计增仓条件：最近N日OI累计变化 > 阈值"""
        if len(self.data) < self.p.oi_lookback + 1:
            return False
        
        oi_today = self.data.openinterest[0]
        oi_n_days_ago = self.data.openinterest[-self.p.oi_lookback]
        
        if oi_n_days_ago <= 0:
            return False
        
        # 计算累计持仓量变化率
        oi_change = (oi_today - oi_n_days_ago) / oi_n_days_ago
        return oi_change > self.p.oi_threshold
    
    def _check_trend_condition(self, direction):
        """
        检查趋势条件
        direction: 1=做多, -1=做空
        """
        if not self.p.use_trend_filter:
            return True
        
        if direction == 1:  # 做多需要价格在均线上方
            return self.data.close[0] > self.trend_ma[0]
        else:  # 做空需要价格在均线下方
            return self.data.close[0] < self.trend_ma[0]
    
    def _check_volatility_condition(self):
        """检查波动率条件：ATR/价格 > 最小阈值"""
        if self.data.close[0] <= 0:
            return False
        atr_pct = self.atr[0] / self.data.close[0]
        return atr_pct > self.p.min_atr_pct
    
    def _calculate_stop_price(self):
        """计算当前止损价（支持跟踪止损）"""
        if self.entry_price is None or self.entry_atr is None:
            return None
        
        if self.position_type == 1:  # 多头
            # 初始止损
            initial_stop = self.entry_price - self.p.stop_atr_mult * self.entry_atr
            
            if self.p.use_trailing_stop and self.highest_since_entry is not None:
                # 跟踪止损：从最高点回撤
                trail_stop = self.highest_since_entry - self.p.trail_atr_mult * self.atr[0]
                
                # 盈利保护：如果盈利超过阈值，至少保本
                profit = self.highest_since_entry - self.entry_price
                if profit > self.p.profit_protect * self.entry_atr:
                    breakeven_stop = self.entry_price + 0.1 * self.entry_atr  # 保本+小利
                    trail_stop = max(trail_stop, breakeven_stop)
                
                return max(initial_stop, trail_stop)
            return initial_stop
        
        else:  # 空头
            # 初始止损
            initial_stop = self.entry_price + self.p.stop_atr_mult * self.entry_atr
            
            if self.p.use_trailing_stop and self.lowest_since_entry is not None:
                # 跟踪止损：从最低点反弹
                trail_stop = self.lowest_since_entry + self.p.trail_atr_mult * self.atr[0]
                
                # 盈利保护
                profit = self.entry_price - self.lowest_since_entry
                if profit > self.p.profit_protect * self.entry_atr:
                    breakeven_stop = self.entry_price - 0.1 * self.entry_atr
                    trail_stop = min(trail_stop, breakeven_stop)
                
                return min(initial_stop, trail_stop)
            return initial_stop
    
    def next(self):
        if self.order:
            return
        
        # 更新持仓后的最高/最低价（跟踪止损用）
        if self.position:
            if self.position_type == 1:
                if self.highest_since_entry is None:
                    self.highest_since_entry = self.data.high[0]
                else:
                    self.highest_since_entry = max(self.highest_since_entry, self.data.high[0])
            elif self.position_type == -1:
                if self.lowest_since_entry is None:
                    self.lowest_since_entry = self.data.low[0]
                else:
                    self.lowest_since_entry = min(self.lowest_since_entry, self.data.low[0])
        
        if not self.position:
            # 检查所有入场条件
            vol_ok = self._check_volume_condition()
            oi_ok = self._check_oi_condition()
            volatility_ok = self._check_volatility_condition()
            
            # 多头入场：突破N日高点 + 放量 + 增仓 + 趋势向上 + 波动率足够
            if (self.data.close[0] > self.highest[-1] and 
                vol_ok and oi_ok and volatility_ok and
                self._check_trend_condition(1)):
                
                self.order = self.buy()
                self.position_type = 1
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.entry_atr = self.atr[0]
                self.highest_since_entry = self.data.high[0]
                self.lowest_since_entry = None
                
                vol_ratio = self.data.volume[0] / self.vol_ma[0] if self.vol_ma[0] > 0 else 0
                self.log(f'【做多】价格={self.data.close[0]:.2f}, '
                        f'高点={self.highest[-1]:.2f}, 量比={vol_ratio:.2f}')
            
            # 空头入场：跌破N日低点 + 放量 + 增仓 + 趋势向下 + 波动率足够
            elif (self.data.close[0] < self.lowest[-1] and 
                  vol_ok and oi_ok and volatility_ok and
                  self._check_trend_condition(-1)):
                
                self.order = self.sell()
                self.position_type = -1
                self.entry_price = self.data.close[0]
                self.entry_bar = len(self)
                self.entry_atr = self.atr[0]
                self.lowest_since_entry = self.data.low[0]
                self.highest_since_entry = None
                
                vol_ratio = self.data.volume[0] / self.vol_ma[0] if self.vol_ma[0] > 0 else 0
                self.log(f'【做空】价格={self.data.close[0]:.2f}, '
                        f'低点={self.lowest[-1]:.2f}, 量比={vol_ratio:.2f}')
        
        else:
            hold_days = len(self) - self.entry_bar
            exit_reason = None
            stop_price = self._calculate_stop_price()
            
            if self.position_type == 1:  # 多头持仓
                if self.data.close[0] < self.lowest_exit[-1]:
                    exit_reason = f'跌破{self.p.n_exit}日低点'
                elif hold_days >= self.p.max_hold:
                    exit_reason = f'持有{hold_days}天达上限'
                elif stop_price and self.data.close[0] < stop_price:
                    exit_reason = f'止损(价={stop_price:.2f})'
            
            else:  # 空头持仓
                if self.data.close[0] > self.highest_exit[-1]:
                    exit_reason = f'突破{self.p.n_exit}日高点'
                elif hold_days >= self.p.max_hold:
                    exit_reason = f'持有{hold_days}天达上限'
                elif stop_price and self.data.close[0] > stop_price:
                    exit_reason = f'止损(价={stop_price:.2f})'
            
            if exit_reason:
                self.order = self.close()
                direction = '平多' if self.position_type == 1 else '平空'
                pnl = (self.data.close[0] - self.entry_price) * self.position_type
                self.log(f'【{direction}】{exit_reason}, 价格={self.data.close[0]:.2f}, 盈亏={pnl:.2f}')
                self._reset_position_state()
    
    def _reset_position_state(self):
        """重置持仓状态"""
        self.position_type = 0
        self.entry_price = None
        self.entry_bar = None
        self.entry_atr = None
        self.highest_since_entry = None
        self.lowest_since_entry = None
    
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
