"""Scheduler lifetime tests without importing network/database dependencies."""
import ast
from datetime import datetime, timedelta
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SCHEDULERS = {
    'clsnewscraper': 'NewsScheduler',
    'eastfutuscraper': 'FuturesScheduler',
    'futurestop10': 'FuturesTop10Scheduler',
    'gthtposiscraper': 'PositionScheduler',
}


def load_class(service, name):
    path = ROOT / 'spiderx' / service / 'scheduler.py'
    tree = ast.parse(path.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
    namespace = {'datetime': datetime, 'timedelta': timedelta, 'Path': Path,
                 'time': Mock(), 'traceback': __import__('traceback')}
    exec(compile(ast.Module(body=[cls], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace[name], namespace


class SchedulerLifetimeTests(unittest.TestCase):
    def test_initialization_has_no_deadline_or_execution_cap(self):
        for service, name in SCHEDULERS.items():
            with self.subTest(service=service):
                cls, _ = load_class(service, name)
                with patch.object(cls, 'setup_logging'), patch.object(cls, 'setup_signal_handlers'), patch.object(Path, 'mkdir'):
                    scheduler = cls()
                self.assertFalse(hasattr(scheduler, 'end_time'))
                self.assertFalse(hasattr(scheduler, 'max_executions'))

    def test_daily_schedulers_find_next_weekday_after_old_deadline(self):
        for service, name in SCHEDULERS.items():
            if service == 'clsnewscraper':
                continue
            with self.subTest(service=service):
                cls, _ = load_class(service, name)
                scheduler = cls.__new__(cls)
                scheduler.start_time = datetime(2026, 1, 1)
                scheduler.end_time = scheduler.start_time + timedelta(days=40)
                scheduler.execution_hour = 16
                scheduler.execution_minute = 30
                result = scheduler.get_next_execution_time(datetime(2026, 10, 23, 20))
                self.assertIsNotNone(result)
                self.assertEqual(result.date(), datetime(2026, 10, 26).date())
                self.assertEqual(result.hour, 16)

    def test_loop_runs_beyond_old_limits_and_respects_shutdown(self):
        for service, name in SCHEDULERS.items():
            with self.subTest(service=service):
                cls, ns = load_class(service, name)
                scheduler = cls.__new__(cls)
                scheduler.start_time = datetime.now() - timedelta(days=100)
                scheduler.end_time = scheduler.start_time + timedelta(days=40)
                scheduler.max_executions = 30
                scheduler.execution_count = 1000
                scheduler.execution_hour = 16
                scheduler.execution_minute = 30
                scheduler.interval_hours = 1
                scheduler.max_retries = 3
                scheduler.shutdown_requested = False
                scheduler.logger = Mock()
                scheduler.should_execute_now = Mock(return_value=False)
                scheduler.get_next_execution_time = Mock(return_value=datetime.now() + timedelta(days=1))
                scheduler.is_trading_day = Mock(return_value=False)
                scheduler.execute_crawl_and_analyze = Mock(return_value=True)

                def stop(*args):
                    scheduler.shutdown_requested = True
                    return True

                scheduler.update_log_file_if_needed = Mock(side_effect=stop)
                scheduler.interruptible_sleep = Mock(side_effect=stop)
                ns['time'].sleep.side_effect = stop
                with patch('builtins.print'):
                    scheduler.run()
                scheduler.update_log_file_if_needed.assert_called_once()
                scheduler.update_log_file_if_needed.reset_mock()
                scheduler.shutdown_requested = True
                with patch('builtins.print'):
                    scheduler.run()
                scheduler.update_log_file_if_needed.assert_not_called()


if __name__ == '__main__':
    unittest.main()
