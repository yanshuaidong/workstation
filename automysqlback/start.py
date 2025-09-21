#!/usr/bin/env python3
"""
期货数据系统后端启动脚本
- 检查浏览器环境
- 启动虚拟显示
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

def check_browser_environment():
    """检查浏览器运行环境"""
    logger.info("检查浏览器运行环境...")
    
    # 检查chromium是否存在
    chrome_bin = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
    if not os.path.exists(chrome_bin):
        logger.error(f"Chromium浏览器不存在: {chrome_bin}")
        return False
    
    # 检查chromedriver是否存在
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
    if not os.path.exists(chromedriver_path):
        logger.error(f"ChromeDriver不存在: {chromedriver_path}")
        return False
    
    logger.info(f"✓ Chromium浏览器: {chrome_bin}")
    logger.info(f"✓ ChromeDriver: {chromedriver_path}")
    
    # 检查chromedriver版本
    try:
        result = subprocess.run([chromedriver_path, '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"✓ ChromeDriver版本: {result.stdout.strip()}")
        else:
            logger.warning(f"ChromeDriver版本检查失败: {result.stderr}")
    except Exception as e:
        logger.warning(f"无法获取ChromeDriver版本: {e}")
    
    return True

def setup_virtual_display():
    """设置虚拟显示（Xvfb）"""
    display = os.environ.get('DISPLAY', ':99')
    
    try:
        # 检查是否已有DISPLAY
        if 'DISPLAY' not in os.environ:
            os.environ['DISPLAY'] = display
        
        # 启动Xvfb虚拟显示
        logger.info(f"启动虚拟显示: {display}")
        subprocess.Popen([
            'Xvfb', display, 
            '-screen', '0', '1280x720x24',
            '-ac', '+extension', 'GLX',
            '+render', '-noreset'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 等待Xvfb启动
        time.sleep(2)
        logger.info(f"✓ 虚拟显示已启动: {display}")
        return True
        
    except Exception as e:
        logger.warning(f"虚拟显示启动失败: {e}")
        logger.info("将使用headless模式运行浏览器")
        return False

def optimize_system():
    """优化系统设置"""
    try:
        # 设置内存优化参数
        os.environ['MALLOC_ARENA_MAX'] = '2'
        os.environ['PYTHONHASHSEED'] = '0'
        
        # 创建日志目录
        log_dir = Path('/app/logs')
        log_dir.mkdir(exist_ok=True)
        
        logger.info("✓ 系统优化完成")
        return True
        
    except Exception as e:
        logger.warning(f"系统优化失败: {e}")
        return False

def main():
    """主启动函数"""
    logger.info("=== 期货数据系统后端启动 ===")
    
    # 1. 检查浏览器环境
    if not check_browser_environment():
        logger.error("浏览器环境检查失败，退出")
        sys.exit(1)
    
    # 2. 设置虚拟显示
    setup_virtual_display()
    
    # 3. 系统优化
    optimize_system()
    
    # 4. 启动Flask应用
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