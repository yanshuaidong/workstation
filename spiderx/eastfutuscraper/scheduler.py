#!/usr/bin/env python3
"""
东方财富期货数据爬虫调度器
运行14天（2周），仅在交易日（周一到周五）的下午4点执行
"""

import time
import logging
import os
import sys
import signal
import traceback
from datetime import datetime, timedelta
from pathlib import Path

# 导入主模块功能
from main import get_all_futures_data, save_all_data_to_db, load_contracts_filter, filter_futures_data


class FuturesScheduler:
    """期货数据爬虫调度器"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(days=14)  # 运行14天
        self.execution_hour = 16  # 下午4点执行
        self.execution_count = 0
        self.max_executions = 10  # 最多执行10次（2周的交易日）
        self.shutdown_requested = False  # 优雅退出标志
        
        # 创建logs目录
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # 设置日志
        self.setup_logging()
        
        # 设置信号处理
        self.setup_signal_handlers()
        
    def setup_logging(self):
        """设置日志配置"""
        # 创建logger
        self.logger = logging.getLogger('futures_scheduler')
        self.logger.setLevel(logging.INFO)
        
        # 清除已有的handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 文件handler - 按日期轮转
        current_date = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs_dir / f"futures_crawler_{current_date}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 控制台handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 设置主程序的logger也使用相同配置
        main_logger = logging.getLogger()
        main_logger.handlers.clear()
        main_logger.addHandler(file_handler)
        main_logger.setLevel(logging.INFO)
    
    def setup_signal_handlers(self):
        """设置信号处理器，用于优雅退出"""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            self.logger.info(f"收到信号 {signal_name}，准备优雅退出...")
            print(f"🛑 收到停止信号 {signal_name}，正在安全停止调度器...")
            self.shutdown_requested = True
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # kill命令
        
    def update_log_file_if_needed(self):
        """检查是否需要切换到新的日志文件"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        expected_log_file = self.logs_dir / f"futures_crawler_{current_date}.log"
        
        # 检查当前文件handler的文件名
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                current_log_file = Path(handler.baseFilename)
                if current_log_file != expected_log_file:
                    # 需要切换日志文件
                    self.logger.removeHandler(handler)
                    handler.close()
                    
                    # 创建新的文件handler
                    new_handler = logging.FileHandler(expected_log_file, encoding='utf-8')
                    new_handler.setLevel(logging.INFO)
                    formatter = logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
                    new_handler.setFormatter(formatter)
                    self.logger.addHandler(new_handler)
                    
                    # 更新主程序logger
                    main_logger = logging.getLogger()
                    main_logger.handlers.clear()
                    main_logger.addHandler(new_handler)
                    
                    self.logger.info(f"切换到新日志文件: {expected_log_file}")
                break
    
    def is_trading_day(self, check_date=None):
        """
        判断是否为交易日（周一到周五）
        
        Args:
            check_date: 要检查的日期，默认为当前日期
        
        Returns:
            bool: 是否为交易日
        """
        if check_date is None:
            check_date = datetime.now()
        
        # 0=周一, 6=周日
        weekday = check_date.weekday()
        return 0 <= weekday <= 4  # 周一到周五
    
    def get_next_execution_time(self, from_time=None):
        """
        计算下一次执行时间（下一个交易日的16:00）
        
        Args:
            from_time: 从哪个时间开始计算，默认为当前时间
        
        Returns:
            datetime: 下一次执行时间，如果没有则返回 None
        """
        if from_time is None:
            from_time = datetime.now()
        
        # 从明天开始查找
        check_date = from_time + timedelta(days=1)
        
        # 最多查找7天
        for _ in range(7):
            if check_date > self.end_time:
                return None
            
            if self.is_trading_day(check_date):
                # 找到下一个交易日，设置为16:00
                next_time = check_date.replace(hour=self.execution_hour, minute=0, second=0, microsecond=0)
                if next_time <= self.end_time:
                    return next_time
            
            check_date += timedelta(days=1)
        
        return None
    
    def should_execute_now(self):
        """
        判断当前是否应该执行任务
        
        Returns:
            bool: 是否应该执行
        """
        now = datetime.now()
        
        # 检查是否为交易日
        if not self.is_trading_day(now):
            return False
        
        # 检查是否到了执行时间（16:00-16:05之间都可以）
        if now.hour == self.execution_hour and 0 <= now.minute < 5:
            return True
        
        return False
    
    def print_heartbeat(self):
        """打印心跳信息到控制台"""
        current_time = datetime.now()
        elapsed = current_time - self.start_time
        remaining = self.end_time - current_time
        
        heartbeat_msg = (
            f"💓 心跳 #{self.execution_count}/10 | "
            f"已运行: {elapsed.total_seconds() / 3600:.1f}h ({elapsed.days}天) | "
            f"剩余: {remaining.total_seconds() / 3600:.1f}h ({remaining.days}天) | "
            f"预计结束: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        print(heartbeat_msg)  # 直接打印到控制台
        self.logger.info(heartbeat_msg)
    
    def execute_crawl_task(self):
        """执行一次期货数据爬取任务"""
        try:
            self.logger.info(f"=== 开始第 {self.execution_count + 1} 次执行 ===")
            self.logger.info(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 1. 加载过滤条件
            self.logger.info("步骤1: 加载期货品种过滤条件...")
            valid_symbols = load_contracts_filter()
            
            # 2. 爬取所有交易所期货数据
            self.logger.info("步骤2: 开始爬取期货数据...")
            all_results = get_all_futures_data()
            
            if not all_results:
                self.logger.error("所有交易所数据获取失败！")
                return False
            
            # 3. 过滤数据并统计
            self.logger.info("步骤3: 过滤数据...")
            total_original = 0
            total_filtered = 0
            
            for exchange_id, result in all_results.items():
                exchange_name = result.get('exchange_name', exchange_id)
                
                # 过滤数据
                if valid_symbols:
                    result = filter_futures_data(result, valid_symbols)
                
                original_count = result.get('original_count', result.get('total', 0))
                filtered_count = result.get('filtered_count', len(result.get('list', [])))
                
                total_original += original_count
                total_filtered += filtered_count
                
                self.logger.info(f"{exchange_name}: 原始 {original_count} 条 -> 过滤后 {filtered_count} 条")
            
            self.logger.info(f"数据过滤完成: 总原始 {total_original} 条 -> 总过滤后 {total_filtered} 条")
            
            # 4. 保存数据到数据库
            self.logger.info("步骤4: 保存数据到数据库...")
            success_count, failed_count = save_all_data_to_db(all_results)
            self.logger.info(f"数据库保存完成: 成功 {success_count} 条, 失败 {failed_count} 条")
            
            # 5. 打印心跳
            self.print_heartbeat()
            
            self.execution_count += 1
            self.logger.info(f"=== 第 {self.execution_count} 次执行完成 ===")
            
            return True
            
        except Exception as e:
            error_msg = f"执行过程中发生异常: {e}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            
            # 控制台打印error并停止
            print("❌ ERROR: 程序执行异常，立即停止")
            print(f"错误详情: {error_msg}")
            
            return False
    
    def run(self):
        """运行调度器"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("东方财富期货数据爬虫调度器启动")
            self.logger.info(f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info(f"结束时间: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info(f"执行时间: 每个交易日（周一到周五）{self.execution_hour}:00")
            self.logger.info(f"预计执行次数: 最多 {self.max_executions} 次")
            self.logger.info("=" * 60)
            
            print(f"🚀 东方财富期货数据爬虫调度器启动")
            print(f"📅 运行期间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} ~ {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏰ 执行时间: 每个交易日（周一到周五）{self.execution_hour}:00")
            print(f"🔄 预计执行: 最多 {self.max_executions} 次")
            print("=" * 60)
            
            # 检查当前是否应该立即执行
            if self.should_execute_now():
                self.logger.info("当前时间符合执行条件，立即执行第一次任务")
                if not self.execute_crawl_task():
                    return
            else:
                current_time = datetime.now()
                # 检查今天是否还有机会执行
                if self.is_trading_day() and current_time.hour < self.execution_hour:
                    # 今天还没到执行时间
                    today_exec_time = current_time.replace(hour=self.execution_hour, minute=0, second=0, microsecond=0)
                    self.logger.info(f"今天是交易日，等待到 {today_exec_time.strftime('%H:%M:%S')} 执行")
                else:
                    # 今天不是交易日或已经过了执行时间，计算下一次执行时间
                    next_time = self.get_next_execution_time()
                    if next_time:
                        self.logger.info(f"下一次执行时间: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        self.logger.info("在运行周期内没有更多的交易日执行时间")
            
            # 主循环
            last_execution_date = None
            
            while (datetime.now() < self.end_time and 
                   self.execution_count < self.max_executions and 
                   not self.shutdown_requested):
                
                # 更新日志文件（如果需要）
                self.update_log_file_if_needed()
                
                current_time = datetime.now()
                current_date = current_time.date()
                
                # 检查是否为交易日
                if not self.is_trading_day(current_time):
                    # 非交易日，睡眠1小时后再检查
                    time.sleep(3600)
                    continue
                
                # 检查是否到了执行时间
                if current_time.hour == self.execution_hour and 0 <= current_time.minute < 5:
                    # 检查今天是否已经执行过
                    if last_execution_date != current_date:
                        self.logger.info(f"到达执行时间，开始执行任务...")
                        
                        if self.execute_crawl_task():
                            last_execution_date = current_date
                            
                            # 执行完成后，计算下一次执行时间
                            next_time = self.get_next_execution_time(current_time)
                            if next_time:
                                wait_seconds = (next_time - datetime.now()).total_seconds()
                                self.logger.info(f"下次执行时间: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
                                self.logger.info(f"等待 {wait_seconds / 3600:.1f} 小时...")
                            else:
                                self.logger.info("所有任务已完成，准备退出")
                                break
                        else:
                            # 执行失败，立即停止
                            return
                    else:
                        # 今天已经执行过，等待到明天
                        time.sleep(300)  # 睡眠5分钟
                else:
                    # 还没到执行时间
                    if current_time.hour < self.execution_hour:
                        # 今天还没到时间，计算需要等待多久
                        target_time = current_time.replace(hour=self.execution_hour, minute=0, second=0, microsecond=0)
                        wait_seconds = (target_time - current_time).total_seconds()
                        
                        if wait_seconds > 3600:
                            # 如果等待时间超过1小时，先睡眠1小时
                            time.sleep(3600)
                        else:
                            # 否则睡眠5分钟
                            time.sleep(300)
                    else:
                        # 今天已经过了执行时间，等待到明天
                        time.sleep(3600)
                
                # 检查停止信号
                if self.shutdown_requested:
                    break
            
            # 结束处理
            if self.shutdown_requested:
                self.logger.info("=" * 60)
                self.logger.info("调度器收到停止信号，优雅退出")
                self.logger.info(f"总执行次数: {self.execution_count}")
                self.logger.info(f"实际运行时长: {(datetime.now() - self.start_time).total_seconds() / 3600:.2f} 小时 ({(datetime.now() - self.start_time).days}天)")
                self.logger.info("=" * 60)
                
                print("🛑 调度器已安全停止")
                print(f"📊 总执行次数: {self.execution_count}")
                print(f"⏱️  实际运行时长: {(datetime.now() - self.start_time).total_seconds() / 3600:.2f} 小时 ({(datetime.now() - self.start_time).days}天)")
            else:
                self.logger.info("=" * 60)
                self.logger.info("调度器正常结束")
                self.logger.info(f"总执行次数: {self.execution_count}")
                self.logger.info(f"实际运行时长: {(datetime.now() - self.start_time).total_seconds() / 3600:.2f} 小时 ({(datetime.now() - self.start_time).days}天)")
                self.logger.info("=" * 60)
                
                print("✅ 调度器正常结束")
                print(f"📊 总执行次数: {self.execution_count}")
                print(f"⏱️  实际运行时长: {(datetime.now() - self.start_time).total_seconds() / 3600:.2f} 小时 ({(datetime.now() - self.start_time).days}天)")
            
        except KeyboardInterrupt:
            self.logger.info("收到键盘中断信号，调度器停止")
            print("⏹️  收到键盘中断信号，调度器停止")
        except Exception as e:
            error_msg = f"调度器运行异常: {e}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            print(f"❌ ERROR: {error_msg}")


def main():
    """主函数"""
    scheduler = FuturesScheduler()
    scheduler.run()


if __name__ == '__main__':
    main()

