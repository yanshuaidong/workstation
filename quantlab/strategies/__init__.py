"""
策略族模块
"""
# 双向策略（推荐）
from .breakout import ShortTermBreakoutDual
from .ma_trend import ShortTermMATrendDual
from .momentum import MomentumFixHoldDual
from .atr_channel import ATRChannelTrendDual
from .vol_oi_breakout import VolOIBreakoutDual, VolOIBreakoutRelaxed

# 原版单向策略（仅做多）
from .breakout import ShortTermBreakout
from .ma_trend import ShortTermMATrend
from .momentum import MomentumFixHold
from .atr_channel import ATRChannelTrend
from .vol_oi_breakout import VolOIBreakout

__all__ = [
    # 双向策略
    'ShortTermBreakoutDual',
    'ShortTermMATrendDual',
    'MomentumFixHoldDual',
    'ATRChannelTrendDual',
    'VolOIBreakoutDual',
    'VolOIBreakoutRelaxed',
    # 单向策略
    'ShortTermBreakout',
    'ShortTermMATrend',
    'MomentumFixHold',
    'ATRChannelTrend',
    'VolOIBreakout',
]
