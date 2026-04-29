from __future__ import annotations

from datetime import date
import unittest

import numpy as np
import pandas as pd

from trading.strategies.account import execute_close_signals
from trading.strategies.signals import save_signals


class FakeCursor:
    def __init__(self, conn: FakeConnection) -> None:
        self.conn = conn
        self.last_sql = ""

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, sql: str, args=None) -> None:
        self.last_sql = " ".join(sql.split())
        if self.last_sql.startswith("INSERT INTO trading_signals"):
            self.conn.inserted_signals.append(args)
            self.conn.lastrowid = len(self.conn.inserted_signals)
        elif self.last_sql.startswith("UPDATE trading_positions SET"):
            self.conn.position_updates.append(args)

    def fetchone(self):
        if "FROM trading_signals" in self.last_sql and "signal_role='open'" in self.last_sql:
            return self.conn.related_open_row
        if "FROM fut_daily_close" in self.last_sql:
            return {"close_price": 9780.0}
        return None

    def fetchall(self):
        if "FROM trading_signals" in self.last_sql and "signal_role='close'" in self.last_sql:
            return self.conn.close_signals
        if "FROM trading_positions" in self.last_sql and "status='open'" in self.last_sql:
            return self.conn.open_positions
        return []


class FakeConnection:
    def __init__(self) -> None:
        self.inserted_signals: list[tuple] = []
        self.position_updates: list[tuple] = []
        self.related_open_row: dict | None = None
        self.close_signals: list[dict] = []
        self.open_positions: list[dict] = []
        self.lastrowid = 0
        self.commits = 0

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def commit(self) -> None:
        self.commits += 1


class SignalStateBoundaryTest(unittest.TestCase):
    def test_save_signals_persists_theoretical_close_with_own_cycle_metadata(self) -> None:
        signal_date = date(2026, 4, 29)
        signal_df = pd.DataFrame(
            [
                {
                    "trade_date": pd.Timestamp(signal_date),
                    "main_force": 7.47,
                    "retail": 4.72,
                    "main_diff": -6.45,
                    "retail_diff": -0.50,
                    "m3": -10.75,
                    "cont3": True,
                    "A_OPEN_LONG": False,
                    "A_OPEN_SHORT": False,
                    "A_CLOSE_LONG": True,
                    "A_CLOSE_SHORT": False,
                    "main_score": np.nan,
                    "signal_role": "close",
                    "direction": "LONG",
                    "cycle_id": "20-LONG-2026-04-23",
                    "related_open_date": date(2026, 4, 23),
                    "theory_state_before": "long",
                    "theory_state_after": "none",
                }
            ]
        )
        conn = FakeConnection()
        conn.related_open_row = {"id": 88}

        inserted = save_signals(conn, signal_date, 20, "棕榈油", signal_df)

        self.assertEqual(inserted, 1)
        self.assertEqual(len(conn.inserted_signals), 1)
        self.assertEqual(conn.inserted_signals[0][3], "A_CLOSE_LONG")
        self.assertEqual(conn.inserted_signals[0][4], "close")
        self.assertEqual(conn.inserted_signals[0][5], "LONG")
        self.assertEqual(conn.inserted_signals[0][6], "20-LONG-2026-04-23")
        self.assertEqual(conn.inserted_signals[0][7], 88)

    def test_real_close_matches_actual_position_cycle_not_theoretical_close_only(self) -> None:
        conn = FakeConnection()
        conn.close_signals = [
            {
                "id": 101,
                "variety_id": 20,
                "direction": "LONG",
                "signal_type": "A_CLOSE_LONG",
                "cycle_id": "20-LONG-2026-04-23",
            },
            {
                "id": 102,
                "variety_id": 24,
                "direction": "LONG",
                "signal_type": "A_CLOSE_LONG",
                "cycle_id": "24-LONG-2026-04-16",
            },
        ]
        conn.open_positions = [
            {
                "id": 3,
                "variety_id": 20,
                "direction": "LONG",
                "open_price": 9781.0,
                "theory_cycle_id": "20-LONG-2026-04-23",
            }
        ]

        closed_today = execute_close_signals(conn, date(2026, 4, 29))

        self.assertEqual(closed_today, {20})
        self.assertEqual(len(conn.position_updates), 1)
        self.assertEqual(conn.position_updates[0][0], date(2026, 4, 29))
        self.assertEqual(conn.position_updates[0][1], 9780.0)
        self.assertEqual(conn.position_updates[0][3], 101)
        self.assertEqual(conn.position_updates[0][4], 3)


if __name__ == "__main__":
    unittest.main()
