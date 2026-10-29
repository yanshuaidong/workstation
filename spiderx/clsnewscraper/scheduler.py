#!/usr/bin/env python3
"""
财联社新闻爬虫调度器
长期运行，每1小时执行一次完整流程（爬取+AI分析）
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
from main import crawl_cls_news, analyze_latest_news, analyze_news_scoring, analyze_news_labeling


class NewsScheduler:
    """新闻爬虫调度器"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.interval_hours = 1  # 每1小时执行一次
        self.execution_count = 0
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
        self.logger = logging.getLogger('scheduler')
        self.logger.setLevel(logging.INFO)
        
        # 清除已有的handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 文件handler - 按日期轮转
        current_date = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs_dir / f"news_crawler_{current_date}.log"
        
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
        expected_log_file = self.logs_dir / f"news_crawler_{current_date}.log"
        
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
    
    def print_heartbeat(self):
        """打印心跳信息到控制台"""
        current_time = datetime.now()
        elapsed = current_time - self.start_time
        heartbeat_msg = (
            f"💓 心跳 #{self.execution_count + 1} | "
            f"已运行: {elapsed.total_seconds() / 3600:.1f}h | 长期运行（无期限）"
        )
        
        print(heartbeat_msg)  # 直接打印到控制台
        self.logger.info(heartbeat_msg)
    
    def execute_crawl_and_analyze(self):
        """执行一次完整的爬取和分析流程"""
        try:
            self.logger.info(f"=== 开始第 {self.execution_count + 1} 次执行 ===")
            
            # 1. 爬取新闻
            self.logger.info("步骤1: 开始爬取新闻...")
            new_count, duplicate_count, total_count = crawl_cls_news()
            self.logger.info(f"爬取完成: 总获取 {total_count} 条, 新增 {new_count} 条, 重复 {duplicate_count} 条")
            
            # 2. 完整AI处理（固定处理20条最新新闻）
            self.logger.info("步骤2: 开始完整AI处理...")
            analyze_count = 20  # 固定处理20条
            
            # 2.1 软硬分析
            success1, failure1 = analyze_latest_news(analyze_count)
            self.logger.info(f"软硬分析完成: 成功 {success1} 条, 失败 {failure1} 条")
            
            # 2.2 评分
            success2, failure2 = analyze_news_scoring(analyze_count)
            self.logger.info(f"AI评分完成: 成功 {success2} 条, 失败 {failure2} 条")
            
            # 2.3 标签
            success3, failure3 = analyze_news_labeling(analyze_count)
            self.logger.info(f"AI标签完成: 成功 {success3} 条, 失败 {failure3} 条")
            
            # 3. 打印心跳
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
            self.logger.info("=" * 50)
            self.logger.info("财联社新闻爬虫调度器启动")
            self.logger.info(f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("运行模式: 长期运行，无期限和次数上限")
            self.logger.info(f"执行间隔: {self.interval_hours} 小时")
            self.logger.info("=" * 50)
            
            print(f"🚀 财联社新闻爬虫调度器启动")
            print(f"📅 启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} | 长期运行（无期限）")
            print(f"⏰ 执行间隔: {self.interval_hours} 小时")
            print("=" * 60)
            
            # 立即执行第一次
            if not self.execute_crawl_and_analyze():
                return
            
            # 循环执行
            while not self.shutdown_requested:
                
                # 更新日志文件（如果需要）
                self.update_log_file_if_needed()
                
                # 计算下次执行时间
                next_execution = self.start_time + timedelta(hours=self.interval_hours * self.execution_count)
                current_time = datetime.now()
                
                if next_execution > current_time:
                    sleep_seconds = (next_execution - current_time).total_seconds()
                    self.logger.info(f"等待 {sleep_seconds / 3600:.2f} 小时后执行下次任务...")
                    self.logger.info(f"下次执行时间: {next_execution.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # 分段睡眠，便于响应停止信号
                    for _ in range(int(sleep_seconds)):
                        if self.shutdown_requested:
                            break
                        time.sleep(1)
                
                # 检查停止信号
                if self.shutdown_requested:
                    break
                    
                # 执行任务
                if not self.execute_crawl_and_analyze():
                    return  # 异常时立即停止
            
            # 结束处理
            if self.shutdown_requested:
                self.logger.info("=" * 50)
                self.logger.info("调度器收到停止信号，优雅退出")
                self.logger.info(f"总执行次数: {self.execution_count}")
                self.logger.info(f"实际运行时长: {(datetime.now() - self.start_time).total_seconds() / 3600:.2f} 小时")
                self.logger.info("=" * 50)
                
                print("🛑 调度器已安全停止")
                print(f"📊 总执行次数: {self.execution_count}")
                print(f"⏱️  实际运行时长: {(datetime.now() - self.start_time).total_seconds() / 3600:.2f} 小时")
            else:
                self.logger.info("=" * 50)
                self.logger.info("调度器正常结束")
                self.logger.info(f"总执行次数: {self.execution_count}")
                self.logger.info(f"实际运行时长: {(datetime.now() - self.start_time).total_seconds() / 3600:.2f} 小时")
                self.logger.info("=" * 50)
                
                print("✅ 调度器正常结束")
                print(f"📊 总执行次数: {self.execution_count}")
                print(f"⏱️  实际运行时长: {(datetime.now() - self.start_time).total_seconds() / 3600:.2f} 小时")
            
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
    scheduler = NewsScheduler()
    scheduler.run()


if __name__ == '__main__':
    main()
