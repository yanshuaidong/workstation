#!/usr/bin/env python3
"""
爬虫调度器示例
演示如何使用 APScheduler 创建定时任务调度器

功能说明：
1. 支持多种调度方式（cron、interval）
2. 优雅退出机制（信号处理）
3. 日志记录
4. PID文件管理
"""

import time
import logging
import os
import sys
import signal
import traceback
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

# ==================== 配置部分 ====================

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# PID文件路径
PID_FILE = 'scheduler.pid'

# ==================== 任务函数 ====================

def example_task_1():
    """示例任务1 - 每小时执行"""
    logger.info("🔄 执行任务1：每小时任务")
    try:
        # 这里写你的任务逻辑
        logger.info("✅ 任务1执行成功")
    except Exception as e:
        logger.error(f"❌ 任务1执行失败: {e}")

def example_task_2():
    """示例任务2 - 每天特定时间执行"""
    logger.info("🔄 执行任务2：每天定时任务")
    try:
        # 这里写你的任务逻辑
        logger.info("✅ 任务2执行成功")
    except Exception as e:
        logger.error(f"❌ 任务2执行失败: {e}")

def example_task_3():
    """示例任务3 - 每隔N分钟执行"""
    logger.info("🔄 执行任务3：间隔任务")
    try:
        # 这里写你的任务逻辑
        logger.info("✅ 任务3执行成功")
    except Exception as e:
        logger.error(f"❌ 任务3执行失败: {e}")

# ==================== 信号处理 ====================

def signal_handler(signum, frame):
    """信号处理器，用于优雅退出"""
    signal_name = signal.Signals(signum).name
    logger.info(f"收到信号 {signal_name}，准备优雅退出...")
    
    # 删除PID文件
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
        logger.info("已删除PID文件")
    
    logger.info("调度器已停止")
    sys.exit(0)

# ==================== 主程序 ====================

def main():
    """主函数"""
    logger.info('='*60)
    logger.info('🚀 调度器启动')
    logger.info(f'⏰ 启动时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    logger.info('='*60)
    
    # 写入PID文件
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    logger.info(f"📝 PID: {os.getpid()}")
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill命令
    logger.info("信号处理器已注册")
    
    # 创建调度器
    scheduler = BlockingScheduler()
    
    # ==================== 添加任务 ====================
    
    # 方式1: cron方式 - 每小时的第0分钟执行
    scheduler.add_job(
        example_task_1, 
        'cron', 
        hour='*', 
        minute=0,
        id='task1'
    )
    logger.info("📌 任务1已添加: 每小时执行")
    
    # 方式2: cron方式 - 每天特定时间执行（例如：每天9点、15点）
    scheduler.add_job(
        example_task_2,
        'cron',
        hour='9,15',
        minute=0,
        id='task2'
    )
    logger.info("📌 任务2已添加: 每天9点、15点执行")
    
    # 方式3: interval方式 - 每隔30分钟执行
    scheduler.add_job(
        example_task_3,
        'interval',
        minutes=30,
        id='task3'
    )
    logger.info("📌 任务3已添加: 每30分钟执行")
    
    # 打印所有任务的下次执行时间
    logger.info("\n" + "="*60)
    logger.info("📅 任务调度计划:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.id}: 下次执行 {job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60 + "\n")
    
    # 启动调度器（阻塞运行）
    try:
        logger.info("⏰ 调度器开始运行...")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        # 清理
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        logger.info("👋 调度器已停止")

if __name__ == '__main__':
    main()