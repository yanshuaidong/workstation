"""
期货数据更新系统 - 路由模块包
包含所有的API路由蓝图
"""

from .contracts_routes import contracts_bp
from .news_routes import news_bp
from .positions_routes import positions_bp
from .events_routes import events_bp

__all__ = ['contracts_bp', 'news_bp', 'positions_bp', 'events_bp']

