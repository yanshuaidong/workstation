#!/usr/bin/env python3
"""
股票数据定时更新调度器

功能：
- 在交易日（周一至周五）的下午5点自动更新股票数据
- 调用 updata.py 执行增量更新

环境准备：
  pip install apscheduler
"""

import logging
import os
import sys
import signal
import subprocess
from apscheduler.schedulers.blocking import BlockingScheduler

# 脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(SCRIPT_DIR, 'scheduler.pid')
LOG_FILE = os.path.join(SCRIPT_DIR, 'scheduler.log')
UPDATE_SCRIPT = os.path.join(SCRIPT_DIR, 'updata.py')  # 注意：文件名是 updata.py

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ==================== 任务函数 ====================

def update_stock_data():
    """执行股票数据更新任务"""
    logger.info("🔄 开始执行股票数据更新任务...")
    
    try:
        # 检查 Python 解释器
        python_cmd = sys.executable
        
        # 调用 updata.py
        result = subprocess.run(
            [python_cmd, UPDATE_SCRIPT],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            timeout=7200  # 2小时超时（股票数据量大）
        )
        
        if result.returncode == 0:
            logger.info("✅ 股票数据更新完成")
            # 记录部分输出
            if result.stdout:
                for line in result.stdout.strip().split('\n')[-10:]:
                    logger.info(f"  {line}")
        else:
            logger.error(f"❌ 股票数据更新失败 (退出码: {result.returncode})")
            if result.stderr:
                logger.error(f"错误信息: {result.stderr[:500]}")
                
    except subprocess.TimeoutExpired:
        logger.error("❌ 股票数据更新超时 (>2小时)")
    except Exception as e:
        logger.error(f"❌ 股票数据更新异常: {e}")


# ==================== 信号处理 ====================

def signal_handler(signum, frame):
    """优雅退出"""
    logger.info(f"收到停止信号，退出中...")
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    sys.exit(0)


# ==================== 主程序 ====================

def main():
    logger.info('=' * 50)
    logger.info('🚀 股票数据调度器启动')
    logger.info('=' * 50)
    
    # 写入PID文件
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建调度器
    scheduler = BlockingScheduler()
    
    # 添加定时任务：周一至周五（交易日）下午5点执行
    scheduler.add_job(
        update_stock_data,
        'cron',
        day_of_week='mon-fri',  # 周一到周五
        hour=17,                 # 下午5点
        minute=0,
        id='stock_daily_update'
    )
    
    # 显示调度计划
    logger.info("📅 任务列表:")
    for job in scheduler.get_jobs():
        logger.info(f"  {job.id}: 下次执行 {job.next_run_time}")
    
    logger.info("⏰ 调度器运行中 (周一至周五 17:00 执行更新)...")
    logger.info("")
    
    # 启动
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        logger.info("👋 调度器已停止")


if __name__ == '__main__':
    main()

