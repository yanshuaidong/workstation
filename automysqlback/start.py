#!/usr/bin/env python3
"""
期货数据系统后端启动脚本
- 检查浏览器环境（仅生产环境）
- 启动虚拟显示（仅生产环境）
- 启动Flask应用
"""

import os
import sys
import subprocess
import logging
import time
from pathlib import Path

# 加载环境变量
try:
    from dotenv import load_dotenv
    # 查找当前目录的.env文件
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logging.info(f"已加载环境配置文件: {env_path}")
    else:
        logging.warning(f".env文件不存在: {env_path}")
except ImportError:
    logging.warning("python-dotenv未安装，将使用系统环境变量")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_development_environment():
    """检测是否为开发环境"""
    environment = os.environ.get('ENVIRONMENT', '').lower()
    return environment in ['development', 'dev']

def is_production_environment():
    """检测是否为生产环境"""
    environment = os.environ.get('ENVIRONMENT', '').lower()
    return environment in ['production', 'prod']

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
        if is_production_environment():
            log_dir = Path('/app/logs')
        else:
            log_dir = Path('./logs')
        log_dir.mkdir(exist_ok=True)
        
        logger.info("✓ 系统优化完成")
        return True
        
    except Exception as e:
        logger.warning(f"系统优化失败: {e}")
        return False

def main():
    """主启动函数"""
    logger.info("=== 期货数据系统后端启动 ===")
    
    # 获取环境配置
    environment = os.environ.get('ENVIRONMENT', '').lower()
    
    if not environment:
        logger.warning("未设置ENVIRONMENT环境变量，默认使用开发环境模式")
        environment = 'development'
    
    logger.info(f"当前运行环境: {environment}")
    
    if is_development_environment():
        logger.info("开发环境模式 - 跳过浏览器环境检查和虚拟显示设置")
        logger.info("注意：开发环境下爬虫功能将不可用")
    elif is_production_environment():
        logger.info("生产环境模式 - 进行完整的环境初始化")
        
        # 1. 检查浏览器环境
        if not check_browser_environment():
            logger.error("浏览器环境检查失败，退出")
            sys.exit(1)
        
        # 2. 设置虚拟显示
        setup_virtual_display()
    else:
        logger.error(f"未知的环境配置: {environment}")
        logger.error("ENVIRONMENT环境变量必须设置为 'development' 或 'production'")
        sys.exit(1)
    
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