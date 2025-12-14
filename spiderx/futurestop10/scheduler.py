#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货涨跌幅TOP10定时任务调度器

执行时间：每周一到周五 下午17:30（期货收盘后）
功能：
1. 获取期货涨跌幅TOP10数据
2. 入库到MySQL（news_red_telegraph、news_process_tracking）
3. 创建AI分析任务（analysis_task）
"""

import logging
import os
import sys
import signal
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# 导入主程序
from main import main as run_main

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


def is_futures_trading_day():
    """
    判断是否是期货交易日
    规则：周一到周五（排除周末）
    注意：这里简化处理，实际应该排除法定节假日
    """
    today = datetime.now()
    weekday = today.weekday()  # 0=周一, 6=周日
    
    # 周一到周五
    if 0 <= weekday <= 4:
        logger.info(f"今天是工作日 (周{weekday + 1})，执行任务")
        return True
    else:
        logger.info(f"今天是周末 (周{weekday + 1})，跳过任务")
        return False


def futures_top10_task():
    """
    期货涨跌幅TOP10任务
    """
    logger.info("=" * 60)
    logger.info("🔄 开始执行期货涨跌幅TOP10任务")
    logger.info("=" * 60)
    
    # 检查是否是交易日
    if not is_futures_trading_day():
        logger.info("⏭️  非交易日，跳过任务")
        return
    
    try:
        # 执行主程序
        run_main()
        logger.info("✅ 任务执行完成")
    except Exception as e:
        logger.error(f"❌ 任务执行失败: {e}", exc_info=True)
    
    logger.info("=" * 60)


def job_listener(event):
    """
    任务监听器：记录任务执行状态
    """
    if event.exception:
        logger.error(f"任务执行出错: {event.exception}")
    else:
        logger.info(f"任务执行成功: {event.job_id}")


def signal_handler(signum, frame):
    """优雅退出"""
    logger.info(f"收到停止信号 ({signum})，正在退出...")
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
        logger.info("已删除PID文件")
    sys.exit(0)


def main():
    logger.info('=' * 60)
    logger.info('🚀 期货涨跌幅TOP10定时任务调度器启动')
    logger.info('=' * 60)
    
    # 写入PID文件
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        logger.info(f"📝 PID文件已创建: {PID_FILE}")
    except Exception as e:
        logger.error(f"创建PID文件失败: {e}")
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建调度器
    scheduler = BlockingScheduler()
    
    # 添加任务监听器
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    
    # 添加定时任务：每周一到周五 下午17:30执行
    scheduler.add_job(
        futures_top10_task,
        'cron',
        day_of_week='mon-fri',  # 周一到周五
        hour=17,                 # 17点（下午5点）
        minute=30,               # 30分
        id='futures_top10_task',
        name='期货涨跌幅TOP10数据采集'
    )
    
    logger.info("📅 定时任务配置:")
    logger.info("  任务: 期货涨跌幅TOP10数据采集")
    logger.info("  执行时间: 每周一到周五 17:30")
    logger.info("  下次执行: " + str(scheduler.get_jobs()[0].next_run_time))
    
    # 是否立即执行一次（可选，用于测试）
    import_immediately = os.getenv('RUN_IMMEDIATELY', 'false').lower() == 'true'
    if import_immediately:
        logger.info("🏃 检测到立即执行标志，马上执行一次任务...")
        futures_top10_task()
    
    # 启动调度器
    try:
        logger.info("⏰ 调度器运行中...\n")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        logger.info("👋 调度器已停止")


if __name__ == '__main__':
    main()

