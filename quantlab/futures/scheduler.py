#!/usr/bin/env python3
"""
期货多策略预测调度器
运行40天，仅在交易日（周一到周五）的下午17:10执行
"""

import time
import logging
import signal
import traceback
from datetime import datetime, timedelta
from pathlib import Path

# 导入主模块功能
from predict import main as run_predict


class FuturesPredictScheduler:
    """期货多策略预测调度器"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(days=40)  # 运行40天
        self.execution_hour = 17  # 下午5点
        self.execution_minute = 10  # 10分
        self.execution_count = 0
        self.max_executions = 30  # 最多执行30次（40天约28-30个交易日）
        self.shutdown_requested = False  # 优雅退出标志
        
        # 创建logs目录
        self.logs_dir = Path(__file__).parent / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # 设置日志
        self.setup_logging()
        
        # 设置信号处理
        self.setup_signal_handlers()
    
    def interruptible_sleep(self, seconds):
        """
        可中断的睡眠函数，每秒检查一次是否需要停止
        
        Args:
            seconds: 总睡眠时间（秒）
        
        Returns:
            bool: 是否被中断（True 表示收到停止信号）
        """
        for _ in range(int(seconds)):
            if self.shutdown_requested:
                return True
            time.sleep(1)
        return False
        
    def setup_logging(self):
        """设置日志配置"""
        # 创建logger
        self.logger = logging.getLogger('futures_predict_scheduler')
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # 禁止传播到根logger，避免重复输出
        
        # 清除已有的handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 文件handler - 按月轮转
        current_month = datetime.now().strftime('%Y-%m')
        log_file = self.logs_dir / f"futures_predict_{current_month}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 设置格式（简化格式，去掉logger名称）
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
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
        expected_log_file = self.logs_dir / f"futures_predict_{current_month}.log"
        
        # 检查当前文件handler的文件名
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                current_log_file = Path(handler.baseFilename)
                if current_log_file != expected_log_file:
                    # 需要切换日志文件（跨月）
                    self.logger.removeHandler(handler)
                    handler.close()
                    
                    # 创建新的文件handler
                    new_handler = logging.FileHandler(expected_log_file, encoding='utf-8')
                    new_handler.setLevel(logging.INFO)
                    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                    new_handler.setFormatter(formatter)
                    self.logger.addHandler(new_handler)
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
        计算下一次执行时间（下一个交易日的17:10）
        
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
                # 找到下一个交易日，设置为17:10
                next_time = check_date.replace(
                    hour=self.execution_hour, 
                    minute=self.execution_minute, 
                    second=0, 
                    microsecond=0
                )
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
        
        # 检查是否到了执行时间（17:10-17:15之间都可以）
        if now.hour == self.execution_hour and self.execution_minute <= now.minute < self.execution_minute + 5:
            return True
        
        return False
    
    def print_heartbeat(self):
        """打印心跳信息到控制台"""
        heartbeat_msg = f"已执行 {self.execution_count}/{self.max_executions} 次"
        print(f"💓 {heartbeat_msg}")  # 直接打印到控制台
    
    def execute_predict_task(self):
        """执行一次期货预测任务"""
        try:
            current_date = datetime.now().strftime('%Y-%m-%d')
            self.logger.info(f"[{current_date}] 开始执行第 {self.execution_count + 1} 次任务")
            
            # 直接调用预测函数
            run_predict()
            
            self.execution_count += 1
            self.logger.info(f"[{current_date}] 预测任务完成")
            print(f"✅ [{current_date}] 期货预测完成")
            
            self.print_heartbeat()
            return True
            
        except Exception as e:
            self.logger.error(f"执行异常: {e}\n{traceback.format_exc()}")
            print(f"❌ ERROR: {e}")
            return False
    
    def run(self):
        """运行调度器"""
        try:
            self.logger.info(f"调度器启动 | 运行至 {self.end_time.strftime('%Y-%m-%d')} | 每交易日 {self.execution_hour}:{self.execution_minute:02d} 执行")
            
            print(f"🚀 期货多策略预测调度器启动")
            print(f"📅 运行期间: {self.start_time.strftime('%Y-%m-%d')} ~ {self.end_time.strftime('%Y-%m-%d')}")
            print(f"⏰ 执行时间: 每个交易日 {self.execution_hour}:{self.execution_minute:02d}")
            
            # 检查当前是否应该立即执行
            if self.should_execute_now():
                if not self.execute_predict_task():
                    return
            else:
                # 计算下一次执行时间
                current_time = datetime.now()
                if self.is_trading_day() and (current_time.hour < self.execution_hour or 
                    (current_time.hour == self.execution_hour and current_time.minute < self.execution_minute)):
                    print(f"⏳ 等待今日 {self.execution_hour}:{self.execution_minute:02d} 执行")
                else:
                    next_time = self.get_next_execution_time()
                    if next_time:
                        print(f"⏳ 下次执行: {next_time.strftime('%Y-%m-%d %H:%M')}")
            
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
                    # 非交易日，睡眠1小时后再检查（可中断）
                    if self.interruptible_sleep(3600):
                        break
                    continue
                
                # 检查是否到了执行时间
                if (current_time.hour == self.execution_hour and 
                    self.execution_minute <= current_time.minute < self.execution_minute + 5):
                    # 检查今天是否已经执行过
                    if last_execution_date != current_date:
                        if self.execute_predict_task():
                            last_execution_date = current_date
                            
                            # 执行完成后，计算下一次执行时间
                            next_time = self.get_next_execution_time(current_time)
                            if not next_time:
                                break
                        else:
                            # 执行失败，继续等待下次
                            pass
                    else:
                        # 今天已经执行过，等待到明天
                        if self.interruptible_sleep(300):  # 睡眠5分钟（可中断）
                            break
                else:
                    # 还没到执行时间
                    target_time = current_time.replace(
                        hour=self.execution_hour, 
                        minute=self.execution_minute, 
                        second=0, 
                        microsecond=0
                    )
                    
                    if current_time < target_time:
                        # 今天还没到时间，计算需要等待多久
                        wait_seconds = (target_time - current_time).total_seconds()
                        
                        if wait_seconds > 3600:
                            # 如果等待时间超过1小时，先睡眠1小时（可中断）
                            if self.interruptible_sleep(3600):
                                break
                        else:
                            # 否则睡眠5分钟（可中断）
                            if self.interruptible_sleep(300):
                                break
                    else:
                        # 今天已经过了执行时间，等待到明天（可中断）
                        if self.interruptible_sleep(3600):
                            break
                
                # 检查停止信号
                if self.shutdown_requested:
                    break
            
            # 结束处理
            run_days = (datetime.now() - self.start_time).days
            if self.shutdown_requested:
                self.logger.info(f"调度器停止 | 总执行 {self.execution_count} 次 | 运行 {run_days} 天")
                print(f"🛑 调度器已停止 | 执行 {self.execution_count} 次")
            else:
                self.logger.info(f"调度器结束 | 总执行 {self.execution_count} 次 | 运行 {run_days} 天")
                print(f"✅ 调度器结束 | 执行 {self.execution_count} 次")
            
        except KeyboardInterrupt:
            self.logger.info("键盘中断，调度器停止")
            print("⏹️ 键盘中断，调度器停止")
        except Exception as e:
            self.logger.error(f"调度器异常: {e}\n{traceback.format_exc()}")
            print(f"❌ ERROR: {e}")


def main():
    """主函数"""
    scheduler = FuturesPredictScheduler()
    scheduler.run()


if __name__ == '__main__':
    main()

