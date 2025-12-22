#!/usr/bin/env python3
"""
机构持仓数据定时更新调度器

功能：
- 在交易日（周一至周五）的下午5点自动更新机构持仓数据
- 直接调用 update.py 的 main 函数执行增量更新

环境准备：
  pip install apscheduler
"""

import logging
import os
import sys
import signal
import traceback
from apscheduler.schedulers.blocking import BlockingScheduler

# 导入更新模块
from update import main as run_update

# 脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(SCRIPT_DIR, 'scheduler.pid')
LOG_FILE = os.path.join(SCRIPT_DIR, 'scheduler.log')

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

def update_institution_data():
    """执行机构持仓数据更新任务"""
    logger.info("🔄 开始执行机构持仓数据更新任务...")
    
    try:
        # 直接调用 update.py 的 main 函数
        run_update()
        logger.info("✅ 机构持仓数据更新完成")
                
    except Exception as e:
        logger.error(f"❌ 机构持仓数据更新异常: {e}")
        logger.error(traceback.format_exc())


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
    logger.info('🚀 机构持仓数据调度器启动')
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
        update_institution_data,
        'cron',
        day_of_week='mon-fri',  # 周一到周五
        hour=17,                 # 下午5点
        minute=0,
        id='institution_daily_update'
    )
    
    # 显示调度计划
    logger.info("📅 任务列表:")
    for job in scheduler.get_jobs():
        logger.info(f"  {job.id}: {job.trigger}")
    
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
