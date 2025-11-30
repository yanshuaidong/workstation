#!/usr/bin/env python3
"""
爬虫调度器示例 - 演示 APScheduler 的基本用法

环境准备（推荐虚拟环境，但不强制）：
  python3 -m venv venv && source venv/bin/activate
  pip install apscheduler
"""

import logging
import os
import sys
import signal
from apscheduler.schedulers.blocking import BlockingScheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
PID_FILE = 'scheduler.pid'

# ==================== 任务函数 ====================

def hourly_task():
    """每小时执行的任务"""
    logger.info("🔄 每小时任务")
    # 在这里添加你的业务逻辑
    logger.info("✅ 完成")

def daily_task():
    """每天定时执行的任务"""
    logger.info("🔄 每日任务")
    # 在这里添加你的业务逻辑
    logger.info("✅ 完成")

def interval_task():
    """间隔执行的任务"""
    logger.info("🔄 间隔任务")
    # 在这里添加你的业务逻辑
    logger.info("✅ 完成")

# ==================== 信号处理 ====================

def signal_handler(signum, frame):
    """优雅退出"""
    logger.info(f"收到停止信号，退出中...")
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    sys.exit(0)

# ==================== 主程序 ====================

def main():
    logger.info('='*50)
    logger.info('🚀 调度器启动')
    logger.info('='*50)
    
    # 写入PID文件
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建调度器
    scheduler = BlockingScheduler()
    
    # 添加任务示例
    # 方式1: cron - 每小时整点执行
    scheduler.add_job(hourly_task, 'cron', hour='*', minute=0)
    
    # 方式2: cron - 每天9点、15点执行
    scheduler.add_job(daily_task, 'cron', hour='9,15', minute=0)
    
    # 方式3: interval - 每30分钟执行
    scheduler.add_job(interval_task, 'interval', minutes=30)
    
    # 更多示例（注释状态）：
    # scheduler.add_job(task, 'cron', day_of_week='mon-fri', hour=9)  # 工作日9点
    # scheduler.add_job(task, 'cron', day=1, hour=0)  # 每月1号0点
    # scheduler.add_job(task, 'interval', hours=2)  # 每2小时
    
    # 显示调度计划
    logger.info("📅 任务列表:")
    for job in scheduler.get_jobs():
        logger.info(f"  {job.id}: {job.next_run_time}")
    
    # 启动
    try:
        logger.info("⏰ 开始运行...\n")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        logger.info("👋 已停止")

if __name__ == '__main__':
    main()