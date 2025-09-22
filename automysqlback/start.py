#!/usr/bin/env python3
"""
期货数据系统后端启动脚本
- 轻量级版本（已移除浏览器支持）
- 启动Flask应用
"""

import os
import sys
import subprocess
import logging
import time
from pathlib import Path


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 浏览器环境检测功能已移除 - 爬虫功能已迁移到 spiderx 项目

def optimize_system():
    """优化系统设置"""
    try:
        # 设置内存优化参数
        os.environ['MALLOC_ARENA_MAX'] = '2'
        os.environ['PYTHONHASHSEED'] = '0'
        
        # 创建日志目录
        log_dir = Path('./logs')
        log_dir.mkdir(exist_ok=True)
        
        logger.info("✓ 系统优化完成")
        return True
        
    except Exception as e:
        logger.warning(f"系统优化失败: {e}")
        return False

def main():
    """主启动函数"""
    logger.info("=== 期货数据系统后端启动（轻量级版本）===")
    logger.info("注意：爬虫功能已迁移到 spiderx 项目，请在本地运行")
    
    # 系统优化
    optimize_system()
    
    # 启动Flask应用
    logger.info("启动Flask应用...")
    try:
        # 导入并运行app
        from app import app, init_database, scheduler, setup_scheduler
        import atexit
        
        # 初始化数据库
        logger.info("初始化数据库...")
        init_database()
        
        # 启动定时任务调度器
        logger.info("启动定时任务调度器...")
        scheduler.start()
        setup_scheduler()
        
        # 注册关闭时的清理函数
        atexit.register(lambda: scheduler.shutdown())
        
        logger.info("✓ 后端服务启动成功")
        logger.info("监听地址: 0.0.0.0:7001")
        
        # 启动Flask应用
        app.run(host='0.0.0.0', port=7001, debug=False, threaded=True)
        
    except Exception as e:
        logger.error(f"Flask应用启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()