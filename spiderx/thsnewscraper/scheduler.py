#!/usr/bin/env python3
"""
同花顺期货热点新闻爬虫调度器

长期运行，默认每 1 小时执行一次采集（抓取 + 写 MySQL）。
- 启动后立即执行第一次，之后按固定间隔执行
- 收到 SIGINT / SIGTERM 优雅退出
- 日志按日期写到 logs/ths_news_YYYY-MM-DD.log

间隔可用环境变量 THS_NEWS_INTERVAL_MINUTES 调整（分钟，默认 60），只用于本地联调。
"""

import logging
import os
import signal
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path

from main import crawl_once

DEFAULT_INTERVAL_MINUTES = 60


class ThsNewsScheduler:
    """同花顺期货热点新闻调度器"""

    def __init__(self, interval_minutes=None):
        self.start_time = datetime.now()
        self.interval_minutes = interval_minutes or self.read_interval_from_env()
        self.execution_count = 0
        self.shutdown_requested = False
        self.success_count = 0
        self.failure_count = 0

        self.logs_dir = Path(__file__).resolve().parent / "logs"
        self.logs_dir.mkdir(exist_ok=True)

        self.setup_logging()
        self.setup_signal_handlers()

    @staticmethod
    def read_interval_from_env():
        """读取 THS_NEWS_INTERVAL_MINUTES，非法值退回 60 分钟。"""
        raw = os.environ.get("THS_NEWS_INTERVAL_MINUTES", "").strip()
        if raw.isdigit() and int(raw) > 0:
            return int(raw)
        if raw:
            print(f"⚠️  THS_NEWS_INTERVAL_MINUTES={raw} 不是正整数，改用 {DEFAULT_INTERVAL_MINUTES} 分钟")
        return DEFAULT_INTERVAL_MINUTES

    def setup_logging(self):
        """文件 + 控制台双写，按日期命名日志文件。"""
        self.logger = logging.getLogger("ths_news_scheduler")
        self.logger.setLevel(logging.INFO)
        # 不要向 root 传播：root 也挂了同一个文件 handler，会写出重复行。
        self.logger.propagate = False
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        log_file = self.logs_dir / f"ths_news_{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        for handler in (file_handler, console_handler):
            handler.setLevel(logging.INFO)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # main.py 里的 logger 也走同一套输出
        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(file_handler)
        root.setLevel(logging.INFO)

        self.log_file = log_file

    def setup_signal_handlers(self):
        """注册优雅退出信号。"""
        def handler(signum, _frame):
            self.logger.info(f"收到信号 {signal.Signals(signum).name}，准备优雅退出...")
            print(f"🛑 收到停止信号 {signal.Signals(signum).name}，正在安全停止调度器...")
            self.shutdown_requested = True

        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)

    def switch_log_file_if_needed(self):
        """跨天时切到新的日志文件。"""
        expected = self.logs_dir / f"ths_news_{datetime.now().strftime('%Y-%m-%d')}.log"
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) != expected:
                self.logger.removeHandler(handler)
                handler.close()
                new_handler = logging.FileHandler(expected, encoding="utf-8")
                new_handler.setLevel(logging.INFO)
                new_handler.setFormatter(
                    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
                )
                self.logger.addHandler(new_handler)
                root = logging.getLogger()
                root.handlers.clear()
                root.addHandler(new_handler)
                self.log_file = expected
                self.logger.info(f"切换到新日志文件: {expected}")
                return

    def execute_once(self):
        """执行一次采集。返回是否成功，异常不退出调度器，只记录并继续下一轮。"""
        self.execution_count += 1
        try:
            self.logger.info(f"=== 开始第 {self.execution_count} 次采集 ===")
            result = crawl_once()
            self.success_count += 1
            self.logger.info(
                f"=== 第 {self.execution_count} 次采集完成：新增 {result['added']} 条，"
                f"重复 {result['duplicates']} 条，跳过 {result['skipped']} 条 ==="
            )
            return True
        except Exception as exc:
            # 单轮失败不停机：网络抖动、数据库短时不可用都应该自愈。
            self.failure_count += 1
            self.logger.error(f"第 {self.execution_count} 次采集失败: {exc}")
            self.logger.error(traceback.format_exc())
            return False

    def run(self):
        """调度主循环。"""
        self.logger.info("=" * 50)
        self.logger.info("同花顺期货新闻爬虫调度器启动")
        self.logger.info(f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"执行间隔: {self.interval_minutes} 分钟（长期运行，无次数上限）")
        self.logger.info(f"日志文件: {self.log_file}")
        self.logger.info("=" * 50)

        print("🚀 同花顺期货新闻爬虫调度器启动")
        print(f"📅 启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} | 长期运行（无期限）")
        print(f"⏰ 执行间隔: {self.interval_minutes} 分钟")
        print("=" * 60)

        self.execute_once()

        interval_seconds = self.interval_minutes * 60
        while not self.shutdown_requested:
            self.switch_log_file_if_needed()

            next_execution = self.start_time + timedelta(
                seconds=interval_seconds * self.execution_count
            )
            wait_seconds = (next_execution - datetime.now()).total_seconds()
            if wait_seconds > 0:
                self.logger.info(
                    f"等待 {wait_seconds / 60:.1f} 分钟后执行下次采集，"
                    f"下次执行时间: {next_execution.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                # 分段睡眠，停止信号最多等 1 秒
                for _ in range(int(wait_seconds)):
                    if self.shutdown_requested:
                        break
                    time.sleep(1)

            if self.shutdown_requested:
                break

            self.execute_once()
            elapsed_hours = (datetime.now() - self.start_time).total_seconds() / 3600
            heartbeat = (
                f"💓 已运行 {elapsed_hours:.1f}h | 成功 {self.success_count} 次 | "
                f"失败 {self.failure_count} 次"
            )
            print(heartbeat)
            self.logger.info(heartbeat)

        elapsed_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        self.logger.info("调度器已停止")
        self.logger.info(f"总执行次数: {self.execution_count}，成功 {self.success_count}，失败 {self.failure_count}")
        self.logger.info(f"实际运行时长: {elapsed_hours:.2f} 小时")
        print("🛑 调度器已安全停止")
        print(f"📊 总执行次数: {self.execution_count}（成功 {self.success_count} / 失败 {self.failure_count}）")
        print(f"⏱️  实际运行时长: {elapsed_hours:.2f} 小时")


def main():
    ThsNewsScheduler().run()


if __name__ == "__main__":
    main()
