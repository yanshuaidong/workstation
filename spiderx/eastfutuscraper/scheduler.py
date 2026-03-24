#!/usr/bin/env python3
"""
东方财富期货数据爬虫调度器
运行40天，仅在交易日（周一到周五）的下午4点执行
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
from main import (
    get_all_futures_data, save_all_data_to_db,
    load_contracts_filter, filter_futures_data,
    fallback_akshare_crawl,
)


class FuturesScheduler:
    """期货数据爬虫调度器"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(days=40)
        self.execution_hour = 16
        self.execution_count = 0
        self.max_executions = 30
        self.shutdown_requested = False
        
        self.max_retries = 3
        self.retry_delays = [60, 180, 300]  # 重试间隔：1分钟、3分钟、5分钟
        
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
        self.logger.propagate = False  # 防止日志向上传播导致重复
        
        # 清除已有的handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 文件handler - 按月轮转
        current_month = datetime.now().strftime('%Y-%m')
        log_file = self.logs_dir / f"futures_crawler_{current_month}.log"
        self.current_log_month = current_month  # 记录当前日志月份
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 控制台handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 设置格式 - 简化格式，移除重复的 logger 名称
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 设置主程序的logger（用于捕获 main.py 的日志）
        main_logger = logging.getLogger('__main__')
        main_logger.handlers.clear()
        main_logger.addHandler(file_handler)
        main_logger.addHandler(console_handler)
        main_logger.setLevel(logging.INFO)
        main_logger.propagate = False
    
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
        """检查是否需要切换到新的日志文件（按月切换）"""
        current_month = datetime.now().strftime('%Y-%m')
        
        # 检查月份是否变化
        if current_month == self.current_log_month:
            return  # 同一个月，无需切换
        
        # 月份变化，需要切换日志文件
        new_log_file = self.logs_dir / f"futures_crawler_{current_month}.log"
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # 更新 self.logger 的文件 handler
        for handler in self.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                self.logger.removeHandler(handler)
                handler.close()
        
        new_handler = logging.FileHandler(new_log_file, encoding='utf-8')
        new_handler.setLevel(logging.INFO)
        new_handler.setFormatter(formatter)
        self.logger.addHandler(new_handler)
        
        # 更新主程序 logger 的文件 handler
        main_logger = logging.getLogger('__main__')
        for handler in main_logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                main_logger.removeHandler(handler)
                handler.close()
        main_logger.addHandler(new_handler)
        
        self.current_log_month = current_month
    
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
    
    def print_status(self):
        """打印状态信息"""
        remaining = self.end_time - datetime.now()
        self.logger.info(f"进度: {self.execution_count}/{self.max_executions}, 剩余{remaining.days}天")
    
    def execute_crawl_task(self):
        """
        执行一次期货数据爬取任务，带重试机制。
        
        Returns:
            bool: True=成功, False=所有重试均失败
        """
        self.execution_count += 1
        task_tag = f"[第{self.execution_count}次]"
        self.logger.info(f"{task_tag} 开始执行 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        for attempt in range(1, self.max_retries + 1):
            attempt_tag = f"{task_tag}[尝试{attempt}/{self.max_retries}]"
            
            if attempt > 1:
                delay = self.retry_delays[min(attempt - 2, len(self.retry_delays) - 1)]
                self.logger.info(f"{attempt_tag} 等待 {delay} 秒后重试...")
                time.sleep(delay)
                if self.shutdown_requested:
                    self.logger.info(f"{attempt_tag} 收到退出信号，放弃重试")
                    return False
                self.logger.info(f"{attempt_tag} 开始重试")
            
            try:
                valid_symbols = load_contracts_filter()
                if not valid_symbols:
                    self.logger.warning(f"{attempt_tag} 合约过滤列表为空，将保存全量数据")
                else:
                    self.logger.info(f"{attempt_tag} 已加载 {len(valid_symbols)} 个合约过滤条件")
                
                crawl_start = time.time()
                all_results = get_all_futures_data()
                crawl_elapsed = time.time() - crawl_start
                
                success_exchanges = list(all_results.keys()) if all_results else []
                self.logger.info(
                    f"{attempt_tag} 爬取耗时 {crawl_elapsed:.1f}s, "
                    f"成功交易所: {success_exchanges if success_exchanges else '无'}"
                )
                
                if not all_results:
                    self.logger.error(f"{attempt_tag} 所有交易所数据获取失败")
                    continue
                
                total_original = 0
                total_filtered = 0
                
                for exchange_id, result in all_results.items():
                    if valid_symbols:
                        result = filter_futures_data(result, valid_symbols)
                    
                    original_count = result.get('original_count', result.get('total', 0))
                    filtered_count = result.get('filtered_count', len(result.get('list', [])))
                    
                    total_original += original_count
                    total_filtered += filtered_count
                
                db_start = time.time()
                success_count, failed_count = save_all_data_to_db(all_results)
                db_elapsed = time.time() - db_start
                
                self.logger.info(
                    f"{task_tag} 完成: 爬取{total_original}条, 过滤后{total_filtered}条, "
                    f"入库成功{success_count}条, 失败{failed_count}条 (入库耗时 {db_elapsed:.1f}s)"
                )
                return True
                
            except Exception as e:
                self.logger.error(f"{attempt_tag} 执行异常: {e}")
                self.logger.error(traceback.format_exc())
        
        self.logger.warning(f"{task_tag} Selenium {self.max_retries}次重试全部失败，启动 AkShare 降级方案")
        
        try:
            target_date = datetime.now().strftime('%Y-%m-%d')
            ok, fail, skip = fallback_akshare_crawl(target_date)
            
            if ok > 0:
                self.logger.info(
                    f"{task_tag} AkShare 降级成功: 写入 {ok} 条, 跳过 {skip} 条, 失败 {fail} 条"
                )
                return True
            else:
                self.logger.error(f"{task_tag} AkShare 降级也未获取到数据 (跳过 {skip}, 失败 {fail})")
                return False
        except Exception as e:
            self.logger.error(f"{task_tag} AkShare 降级异常: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    def run(self):
        """运行调度器"""
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        try:
            self.logger.info(
                f"调度器启动 | 运行至{self.end_time.strftime('%Y-%m-%d')} | "
                f"每交易日{self.execution_hour}:00执行 | "
                f"每次最多重试{self.max_retries}次 | 连续失败上限{max_consecutive_failures}次"
            )
            
            # 检查当前是否应该立即执行
            if self.should_execute_now():
                if self.execute_crawl_task():
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    self.logger.warning(f"本次爬取失败，连续失败次数: {consecutive_failures}/{max_consecutive_failures}")
            
            next_time = self.get_next_execution_time()
            if next_time:
                self.logger.info(f"下次执行: {next_time.strftime('%Y-%m-%d %H:%M')}")
            
            # 主循环
            last_execution_date = None
            
            while (datetime.now() < self.end_time and 
                   self.execution_count < self.max_executions and 
                   not self.shutdown_requested):
                
                if consecutive_failures >= max_consecutive_failures:
                    self.logger.error(
                        f"连续失败 {consecutive_failures} 次达到上限，调度器停止。"
                        "请检查网络、Chrome 环境或目标网站是否有变更。"
                    )
                    break
                
                self.update_log_file_if_needed()
                
                current_time = datetime.now()
                current_date = current_time.date()
                
                if not self.is_trading_day(current_time):
                    time.sleep(3600)
                    continue
                
                if current_time.hour == self.execution_hour and 0 <= current_time.minute < 5:
                    if last_execution_date != current_date:
                        last_execution_date = current_date
                        if self.execute_crawl_task():
                            consecutive_failures = 0
                            next_time = self.get_next_execution_time(current_time)
                            if next_time:
                                self.logger.info(f"下次执行: {next_time.strftime('%Y-%m-%d %H:%M')}")
                            else:
                                self.logger.info("已无下一个执行时间，调度器即将结束")
                                break
                        else:
                            consecutive_failures += 1
                            self.logger.warning(
                                f"本次爬取失败，连续失败次数: {consecutive_failures}/{max_consecutive_failures}"
                            )
                            next_time = self.get_next_execution_time(current_time)
                            if next_time:
                                self.logger.info(f"下次执行: {next_time.strftime('%Y-%m-%d %H:%M')}")
                    else:
                        time.sleep(300)
                else:
                    if current_time.hour < self.execution_hour:
                        target_time = current_time.replace(hour=self.execution_hour, minute=0, second=0, microsecond=0)
                        wait_seconds = (target_time - current_time).total_seconds()
                        time.sleep(min(wait_seconds, 3600))
                    else:
                        time.sleep(3600)
                
                if self.shutdown_requested:
                    break
            
            elapsed_days = (datetime.now() - self.start_time).days
            if self.shutdown_requested:
                self.logger.info(f"调度器停止 | 执行{self.execution_count}次 | 运行{elapsed_days}天")
            else:
                self.logger.info(
                    f"调度器完成 | 执行{self.execution_count}次 | 运行{elapsed_days}天 | "
                    f"连续失败{consecutive_failures}次"
                )
            
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，调度器停止")
        except Exception as e:
            self.logger.error(f"调度器异常: {e}")
            self.logger.error(traceback.format_exc())


def main():
    """主函数"""
    scheduler = FuturesScheduler()
    scheduler.run()


if __name__ == '__main__':
    main()

