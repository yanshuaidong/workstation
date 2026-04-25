"""
自动化账户执行模块。
每日执行顺序：先平仓 → 再开仓 → 更新资金曲线。
pnl_pct 存储无杠杆收益率，资金曲线 daily_pnl 乘以 LEVERAGE。
"""
from __future__ import annotations

import logging
from datetime import date

import pymysql

from .settings import INITIAL_CAPITAL, LEVERAGE, SIZE_PCT

logger = logging.getLogger(__name__)


def _get_close_price(conn: pymysql.Connection, variety_id: int, trade_date: date) -> float | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT close_price FROM fut_daily_close WHERE variety_id=%s AND trade_date=%s",
            (variety_id, trade_date),
        )
        row = cur.fetchone()
    return float(row["close_price"]) if row else None


def _get_prev_close(conn: pymysql.Connection, variety_id: int, trade_date: date) -> float | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT close_price FROM fut_daily_close "
            "WHERE variety_id=%s AND trade_date<%s ORDER BY trade_date DESC LIMIT 1",
            (variety_id, trade_date),
        )
        row = cur.fetchone()
    return float(row["close_price"]) if row else None


def execute_close_signals(conn: pymysql.Connection, signal_date: date) -> set[int]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT variety_id, signal_type FROM trading_signals "
            "WHERE signal_date=%s AND signal_type IN ('A_CLOSE_LONG','A_CLOSE_SHORT')",
            (signal_date,),
        )
        close_signals = {int(r["variety_id"]): r["signal_type"] for r in cur.fetchall()}

        cur.execute(
            "SELECT id, variety_id, direction, open_price "
            "FROM trading_positions WHERE status='open'"
        )
        open_positions = cur.fetchall()

    # 读取阶段：计算所有平仓参数，不写库
    updates: list[tuple] = []
    closed_today: set[int] = set()
    for pos in open_positions:
        vid = int(pos["variety_id"])
        if vid not in close_signals:
            continue
        sig_type = close_signals[vid]
        direction = pos["direction"]
        if direction == "LONG" and sig_type != "A_CLOSE_LONG":
            continue
        if direction == "SHORT" and sig_type != "A_CLOSE_SHORT":
            continue

        close_price = _get_close_price(conn, vid, signal_date)
        if close_price is None:
            logger.warning("品种 %s 当日无收盘价，跳过平仓", vid)
            continue

        open_price = float(pos["open_price"])
        if direction == "LONG":
            pnl_pct = (close_price - open_price) / open_price
        else:
            pnl_pct = (open_price - close_price) / open_price

        updates.append((signal_date, close_price, pnl_pct, pos["id"]))
        closed_today.add(vid)
        logger.info("平仓 variety_id=%s direction=%s pnl_pct=%.4f", vid, direction, pnl_pct)

    # 写入阶段：批量提交，保证原子性
    if updates:
        with conn.cursor() as cur:
            for args in updates:
                cur.execute(
                    "UPDATE trading_positions SET status='closed', close_date=%s, "
                    "close_price=%s, pnl_pct=%s WHERE id=%s",
                    args,
                )
        conn.commit()

    return closed_today


def execute_open_operations(conn: pymysql.Connection, signal_date: date, closed_today: set[int]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, variety_id, variety_name, sector, signal_type "
            "FROM trading_operations "
            "WHERE signal_date=%s AND is_selected=1",
            (signal_date,),
        )
        selected = cur.fetchall()

    # 读取阶段：准备所有开仓参数，不写库
    inserts: list[tuple] = []
    for op in selected:
        vid = int(op["variety_id"])
        if vid in closed_today:
            continue

        # 幂等保护：该品种当日已有 open 持仓则跳过，防止重跑时重复开仓
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM trading_positions "
                "WHERE variety_id=%s AND open_date=%s AND status='open'",
                (vid, signal_date),
            )
            if cur.fetchone()["cnt"] > 0:
                logger.debug("品种 %s 当日已有持仓，跳过重复开仓", vid)
                continue

        close_price = _get_close_price(conn, vid, signal_date)
        if close_price is None:
            logger.warning("品种 %s 当日无收盘价，跳过开仓", vid)
            continue

        direction = "LONG" if op["signal_type"] == "A_OPEN_LONG" else "SHORT"
        inserts.append((
            op["id"], vid, op["variety_name"], op["sector"], direction,
            signal_date, close_price, SIZE_PCT,
        ))
        logger.info("开仓 variety_id=%s direction=%s price=%.4f", vid, direction, close_price)

    # 写入阶段：批量提交，保证原子性
    if inserts:
        with conn.cursor() as cur:
            for args in inserts:
                cur.execute(
                    """
                    INSERT INTO trading_positions
                        (operation_id, variety_id, variety_name, sector, direction,
                         open_date, open_price, size_pct, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'open')
                    """,
                    args,
                )
        conn.commit()


def update_account_daily(conn: pymysql.Connection, signal_date: date) -> None:
    # 只取当天之前的最新一行，避免同一天重跑时把今天已写入的 equity 当作 prev_equity
    with conn.cursor() as cur:
        cur.execute(
            "SELECT equity FROM trading_account_daily "
            "WHERE record_date<%s ORDER BY record_date DESC LIMIT 1",
            (signal_date,),
        )
        last = cur.fetchone()
        prev_equity = float(last["equity"]) if last else INITIAL_CAPITAL

        # 仍开放的持仓：贡献 daily_pnl + position_val
        cur.execute(
            "SELECT variety_id, direction, open_price, open_date, size_pct "
            "FROM trading_positions WHERE status='open'"
        )
        open_pos = cur.fetchall()

        # 今日刚平仓的持仓：也要把 base_price→close_price 这段 daily_pnl 计入
        # execute_close_signals 已将 status 改为 closed，这里单独捡回来
        cur.execute(
            "SELECT variety_id, direction, open_price, open_date, close_price, size_pct "
            "FROM trading_positions WHERE status='closed' AND close_date=%s",
            (signal_date,),
        )
        closed_today = cur.fetchall()

    daily_pnl = 0.0
    position_val = 0.0

    def _daily_ret(pos, end_price: float) -> float | None:
        """base_price 对今日开仓用 open_price（当日 daily_ret=0），其余用昨日收盘。"""
        direction_sign = 1 if pos["direction"] == "LONG" else -1
        if pos["open_date"] == signal_date:
            base_price = float(pos["open_price"])
        else:
            prev_price = _get_prev_close(conn, int(pos["variety_id"]), signal_date)
            if prev_price is None or prev_price == 0:
                return None
            base_price = prev_price
        if base_price == 0:
            return None
        return direction_sign * (end_price - base_price) / base_price

    for pos in open_pos:
        vid = int(pos["variety_id"])
        cur_price = _get_close_price(conn, vid, signal_date)
        if cur_price is None:
            continue

        size_pct = float(pos["size_pct"])
        open_price = float(pos["open_price"])

        ret = _daily_ret(pos, cur_price)
        if ret is not None:
            daily_pnl += prev_equity * size_pct * ret * LEVERAGE

        direction_sign = 1 if pos["direction"] == "LONG" else -1
        float_ret = direction_sign * (cur_price - open_price) / open_price
        position_val += prev_equity * size_pct * (1 + float_ret * LEVERAGE)

    for pos in closed_today:
        close_price = float(pos["close_price"])
        size_pct = float(pos["size_pct"])

        ret = _daily_ret(pos, close_price)
        if ret is not None:
            daily_pnl += prev_equity * size_pct * ret * LEVERAGE

    # equity 严格按 daily_pnl 累计，不再被 prev_equity 锁死
    equity = prev_equity + daily_pnl
    cash = equity - position_val

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO trading_account_daily (record_date, equity, cash, position_val, daily_pnl)
            VALUES (%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                equity=VALUES(equity), cash=VALUES(cash),
                position_val=VALUES(position_val), daily_pnl=VALUES(daily_pnl)
            """,
            (signal_date, equity, cash, position_val, daily_pnl),
        )
    conn.commit()
    logger.info(
        "资金曲线更新 date=%s equity=%.2f daily_pnl=%.2f position_val=%.2f cash=%.2f",
        signal_date, equity, daily_pnl, position_val, cash,
    )
