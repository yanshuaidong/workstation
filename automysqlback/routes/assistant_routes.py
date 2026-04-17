"""
assistant 辅助决策模块接口
包含：信号、策略建议、持仓、资金曲线、市场上下文
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime

import pymysql
from flask import Blueprint, current_app, jsonify, request


assistant_bp = Blueprint("assistant", __name__)
logger = logging.getLogger(__name__)

INITIAL_CAPITAL = 30000.0
LEVERAGE = 10.0
MAX_HOLD_DAYS = 5
ACCOUNT_TYPES = ("mechanical", "llm")


def _parse_date(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    return None


def _date_str(value):
    parsed = _parse_date(value)
    return parsed.isoformat() if parsed else None


def _parse_json(value):
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return {}
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {"raw": value}
    return {"raw": value}


def _get_conn():
    return current_app.config["get_db_connection"]()


def _latest_table_date(cursor, table_name, column_name):
    cursor.execute(f"SELECT MAX({column_name}) AS latest_date FROM {table_name}")
    row = cursor.fetchone()
    return _date_str(row["latest_date"]) if row and row.get("latest_date") else None


def _success(data=None, message="获取成功"):
    return jsonify({"code": 0, "message": message, "data": data or {}})


def _error(message, code=1):
    return jsonify({"code": code, "message": message})


def _build_like_filter(field_name, value):
    return f"{field_name} LIKE %s", f"%{value.strip()}%"


@assistant_bp.route("/assistant/signals", methods=["GET"])
def get_assistant_signals():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        signal_date = request.args.get("date", "").strip() or _latest_table_date(cursor, "assistant_signals", "signal_date")
        variety_id = request.args.get("variety_id", "").strip()
        variety_name = request.args.get("variety_name", "").strip()
        indicator = request.args.get("indicator", "").strip()
        direction = request.args.get("direction", "").strip()

        where_clauses = []
        params = []
        if signal_date:
            where_clauses.append("signal_date = %s")
            params.append(signal_date)
        if variety_id:
            where_clauses.append("variety_id = %s")
            params.append(int(variety_id))
        if variety_name:
            clause, value = _build_like_filter("variety_name", variety_name)
            where_clauses.append(clause)
            params.append(value)
        if indicator:
            where_clauses.append("indicator = %s")
            params.append(indicator)
        if direction:
            where_clauses.append("direction = %s")
            params.append(direction)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        cursor.execute(
            f"""
            SELECT
                id, signal_date, variety_id, variety_name, indicator,
                direction, triggered, strength, extra_json, created_at
            FROM assistant_signals
            {where_sql}
            ORDER BY signal_date DESC, variety_id, indicator, direction
            """,
            params,
        )
        rows = cursor.fetchall()

        signals = []
        for row in rows:
            extra = _parse_json(row["extra_json"])
            signals.append(
                {
                    "id": row["id"],
                    "signal_date": _date_str(row["signal_date"]),
                    "variety_id": row["variety_id"],
                    "variety_name": row["variety_name"],
                    "indicator": row["indicator"],
                    "direction": row["direction"],
                    "triggered": int(row["triggered"] or 0),
                    "strength": float(row["strength"]) if row["strength"] is not None else None,
                    "indicator_value": extra.get("indicator_value", ""),
                    "extra_json": extra,
                    "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row["created_at"] else "",
                }
            )

        return _success(
            {
                "date": signal_date,
                "signals": signals,
                "total": len(signals),
            }
        )
    except Exception as exc:
        logger.error("获取辅助信号失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@assistant_bp.route("/assistant/operations", methods=["GET"])
def get_assistant_operations():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        signal_date = request.args.get("date", "").strip() or _latest_table_date(cursor, "assistant_operations", "signal_date")
        account_type = request.args.get("account_type", "mechanical").strip() or "mechanical"
        variety_id = request.args.get("variety_id", "").strip()
        variety_name = request.args.get("variety_name", "").strip()
        strategy = request.args.get("strategy", "").strip()
        direction = request.args.get("direction", "").strip()

        where_clauses = []
        params = []
        if signal_date:
            where_clauses.append("signal_date = %s")
            params.append(signal_date)
        if account_type:
            where_clauses.append("account_type = %s")
            params.append(account_type)
        if variety_id:
            where_clauses.append("variety_id = %s")
            params.append(int(variety_id))
        if variety_name:
            clause, value = _build_like_filter("variety_name", variety_name)
            where_clauses.append(clause)
            params.append(value)
        if strategy:
            where_clauses.append("strategy = %s")
            params.append(strategy)
        if direction:
            where_clauses.append("direction = %s")
            params.append(direction)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        cursor.execute(
            f"""
            SELECT
                id, signal_date, variety_id, variety_name, strategy,
                direction, extra_json, account_type, executed, created_at
            FROM assistant_operations
            {where_sql}
            ORDER BY signal_date DESC, created_at DESC, id DESC
            """,
            params,
        )
        rows = cursor.fetchall()

        operations = []
        for row in rows:
            extra = _parse_json(row["extra_json"])
            operations.append(
                {
                    "id": row["id"],
                    "signal_date": _date_str(row["signal_date"]),
                    "variety_id": row["variety_id"],
                    "variety_name": row["variety_name"],
                    "strategy": row["strategy"],
                    "direction": row["direction"],
                    "account_type": row["account_type"],
                    "executed": int(row["executed"] or 0),
                    "strategy_label": extra.get("strategy_label", ""),
                    "trigger_indicators": extra.get("trigger_indicators", {}),
                    "composite_score": float(extra.get("composite_score", 0.0)),
                    "extra_json": extra,
                    "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row["created_at"] else "",
                }
            )

        return _success(
            {
                "date": signal_date,
                "account_type": account_type,
                "operations": operations,
                "total": len(operations),
            }
        )
    except Exception as exc:
        logger.error("获取操作建议失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@assistant_bp.route("/assistant/positions", methods=["GET"])
def get_assistant_positions():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        account_type = request.args.get("account_type", "").strip()
        where_clauses = ["p.status = 'open'"]
        params = []
        if account_type:
            where_clauses.append("p.account_type = %s")
            params.append(account_type)

        cursor.execute(
            f"""
            SELECT
                p.id,
                p.account_type,
                p.variety_id,
                p.variety_name,
                p.direction,
                p.open_date,
                p.open_price,
                p.size_pct,
                p.strategy,
                latest.trade_date AS latest_trade_date,
                latest.close_price AS current_price,
                latest.main_force,
                latest.retail,
                (
                    SELECT COUNT(1)
                    FROM fut_daily_close fd
                    WHERE fd.variety_id = p.variety_id
                      AND fd.trade_date >= p.open_date
                      AND fd.trade_date <= latest.trade_date
                ) AS holding_days
            FROM assistant_positions p
            LEFT JOIN (
                SELECT
                    s.variety_id,
                    s.trade_date,
                    s.main_force,
                    s.retail,
                    c.close_price
                FROM fut_strength s
                INNER JOIN fut_daily_close c
                    ON s.variety_id = c.variety_id
                   AND s.trade_date = c.trade_date
                INNER JOIN (
                    SELECT variety_id, MAX(trade_date) AS latest_trade_date
                    FROM fut_strength
                    GROUP BY variety_id
                ) latest_lookup
                    ON s.variety_id = latest_lookup.variety_id
                   AND s.trade_date = latest_lookup.latest_trade_date
            ) latest
                ON p.variety_id = latest.variety_id
            WHERE {" AND ".join(where_clauses)}
            ORDER BY p.account_type, p.open_date, p.id
            """,
            params,
        )
        rows = cursor.fetchall()

        positions = []
        for row in rows:
            current_price = float(row["current_price"]) if row["current_price"] is not None else None
            open_price = float(row["open_price"])
            direction_sign = 1 if row["direction"] == "LONG" else -1
            floating_pnl_pct = None
            floating_pnl_amount = None
            if current_price is not None and open_price:
                raw_return = direction_sign * ((current_price - open_price) / open_price)
                floating_pnl_pct = raw_return * LEVERAGE * 100
                floating_pnl_amount = INITIAL_CAPITAL * float(row["size_pct"]) * floating_pnl_pct / 100

            holding_days = int(row["holding_days"] or 0)
            positions.append(
                {
                    "id": row["id"],
                    "account_type": row["account_type"],
                    "variety_id": row["variety_id"],
                    "variety_name": row["variety_name"],
                    "direction": row["direction"],
                    "open_date": _date_str(row["open_date"]),
                    "open_price": open_price,
                    "current_price": current_price,
                    "size_pct": float(row["size_pct"]),
                    "strategy": row["strategy"],
                    "latest_trade_date": _date_str(row["latest_trade_date"]),
                    "main_force": float(row["main_force"]) if row["main_force"] is not None else None,
                    "retail": float(row["retail"]) if row["retail"] is not None else None,
                    "holding_days": holding_days,
                    "remaining_days": max(0, MAX_HOLD_DAYS - holding_days),
                    "floating_pnl_pct": round(floating_pnl_pct, 4) if floating_pnl_pct is not None else None,
                    "floating_pnl_amount": round(floating_pnl_amount, 4) if floating_pnl_amount is not None else None,
                }
            )

        return _success(
            {
                "account_type": account_type or "all",
                "positions": positions,
                "total": len(positions),
            }
        )
    except Exception as exc:
        logger.error("获取当前持仓失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@assistant_bp.route("/assistant/positions/history", methods=["GET"])
def get_assistant_position_history():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        account_type = request.args.get("account_type", "").strip()
        limit = min(max(int(request.args.get("limit", 100)), 1), 500)

        where_clauses = ["status = 'closed'"]
        params = []
        if account_type:
            where_clauses.append("account_type = %s")
            params.append(account_type)

        cursor.execute(
            f"""
            SELECT
                id, account_type, variety_id, variety_name, direction,
                open_date, open_price, close_date, close_price,
                size_pct, pnl_pct, strategy, created_at
            FROM assistant_positions
            WHERE {" AND ".join(where_clauses)}
            ORDER BY close_date DESC, id DESC
            LIMIT %s
            """,
            [*params, limit],
        )
        rows = cursor.fetchall()

        history = []
        for row in rows:
            history.append(
                {
                    "id": row["id"],
                    "account_type": row["account_type"],
                    "variety_id": row["variety_id"],
                    "variety_name": row["variety_name"],
                    "direction": row["direction"],
                    "open_date": _date_str(row["open_date"]),
                    "open_price": float(row["open_price"]),
                    "close_date": _date_str(row["close_date"]),
                    "close_price": float(row["close_price"]) if row["close_price"] is not None else None,
                    "size_pct": float(row["size_pct"]),
                    "pnl_pct": float(row["pnl_pct"]) if row["pnl_pct"] is not None else None,
                    "strategy": row["strategy"],
                    "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S") if row["created_at"] else "",
                }
            )

        return _success(
            {
                "account_type": account_type or "all",
                "history": history,
                "total": len(history),
            }
        )
    except Exception as exc:
        logger.error("获取历史持仓失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@assistant_bp.route("/assistant/account/curve", methods=["GET"])
def get_assistant_account_curve():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        start_date = request.args.get("start_date", "").strip()
        end_date = request.args.get("end_date", "").strip()
        account_type = request.args.get("account_type", "").strip()

        where_clauses = []
        params = []
        if start_date:
            where_clauses.append("record_date >= %s")
            params.append(start_date)
        if end_date:
            where_clauses.append("record_date <= %s")
            params.append(end_date)
        if account_type:
            where_clauses.append("account_type = %s")
            params.append(account_type)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        cursor.execute(
            f"""
            SELECT record_date, account_type, equity, cash, position_val, daily_pnl
            FROM assistant_account_daily
            {where_sql}
            ORDER BY record_date, account_type
            """,
            params,
        )
        rows = cursor.fetchall()

        curves = {key: [] for key in ACCOUNT_TYPES}
        for row in rows:
            curves.setdefault(row["account_type"], []).append(
                {
                    "record_date": _date_str(row["record_date"]),
                    "equity": float(row["equity"]),
                    "cash": float(row["cash"]),
                    "position_val": float(row["position_val"]),
                    "daily_pnl": float(row["daily_pnl"]),
                }
            )

        return _success(
            {
                "account_type": account_type or "all",
                "curves": curves,
            }
        )
    except Exception as exc:
        logger.error("获取资金曲线失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@assistant_bp.route("/assistant/account/summary", methods=["GET"])
def get_assistant_account_summary():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        requested_date = request.args.get("date", "").strip()
        summary = {}
        for account_type in ACCOUNT_TYPES:
            if requested_date:
                cursor.execute(
                    """
                    SELECT record_date, equity, cash, position_val, daily_pnl
                    FROM assistant_account_daily
                    WHERE account_type = %s
                      AND record_date <= %s
                    ORDER BY record_date DESC
                    LIMIT 1
                    """,
                    (account_type, requested_date),
                )
            else:
                cursor.execute(
                    """
                    SELECT record_date, equity, cash, position_val, daily_pnl
                    FROM assistant_account_daily
                    WHERE account_type = %s
                    ORDER BY record_date DESC
                    LIMIT 1
                    """,
                    (account_type,),
                )
            snapshot = cursor.fetchone()
            if snapshot:
                cursor.execute(
                    """
                    SELECT COUNT(1) AS cnt
                    FROM assistant_positions
                    WHERE account_type = %s AND status = 'open'
                    """,
                    (account_type,),
                )
                open_positions = cursor.fetchone()["cnt"]
                summary[account_type] = {
                    "record_date": _date_str(snapshot["record_date"]),
                    "equity": float(snapshot["equity"]),
                    "cash": float(snapshot["cash"]),
                    "position_val": float(snapshot["position_val"]),
                    "daily_pnl": float(snapshot["daily_pnl"]),
                    "open_positions": int(open_positions),
                }
            else:
                summary[account_type] = {
                    "record_date": None,
                    "equity": INITIAL_CAPITAL,
                    "cash": INITIAL_CAPITAL,
                    "position_val": 0.0,
                    "daily_pnl": 0.0,
                    "open_positions": 0,
                }

        return _success({"summary": summary})
    except Exception as exc:
        logger.error("获取账户摘要失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@assistant_bp.route("/assistant/market-context", methods=["GET"])
def get_assistant_market_context():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        variety_id = request.args.get("variety_id", "").strip()
        if not variety_id:
            return _error("缺少 variety_id 参数")
        days = min(max(int(request.args.get("days", 10)), 3), 60)
        end_date = request.args.get("end_date", "").strip()
        if not end_date:
            cursor.execute(
                """
                SELECT MAX(trade_date) AS latest_date
                FROM fut_strength
                WHERE variety_id = %s
                """,
                (int(variety_id),),
            )
            row = cursor.fetchone()
            end_date = _date_str(row["latest_date"]) if row and row.get("latest_date") else None

        cursor.execute(
            """
            SELECT
                s.variety_id,
                COALESCE(v.name, CAST(s.variety_id AS CHAR)) AS variety_name,
                s.trade_date,
                s.main_force,
                s.retail,
                c.close_price
            FROM fut_strength s
            INNER JOIN fut_daily_close c
                ON s.variety_id = c.variety_id
               AND s.trade_date = c.trade_date
            LEFT JOIN fut_variety v
                ON s.variety_id = v.id
            WHERE s.variety_id = %s
              AND s.trade_date <= %s
            ORDER BY s.trade_date DESC
            LIMIT %s
            """,
            (int(variety_id), end_date, days),
        )
        rows = list(reversed(cursor.fetchall()))
        series = [
            {
                "trade_date": _date_str(row["trade_date"]),
                "main_force": float(row["main_force"]),
                "retail": float(row["retail"]),
                "close_price": float(row["close_price"]),
            }
            for row in rows
        ]
        variety_name = rows[0]["variety_name"] if rows else ""

        return _success(
            {
                "variety_id": int(variety_id),
                "variety_name": variety_name,
                "end_date": end_date,
                "days": days,
                "series": series,
            }
        )
    except Exception as exc:
        logger.error("获取市场上下文失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@assistant_bp.route("/assistant/variety-list", methods=["GET"])
def variety_list():
    """获取有 contracts_symbol 映射的品种列表（用于K线展示品种选择器）。"""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, name, contracts_symbol FROM fut_variety "
            "WHERE contracts_symbol IS NOT NULL AND contracts_symbol != '' "
            "ORDER BY id"
        )
        rows = cursor.fetchall()
        return _success({"varieties": [
            {"id": row["id"], "name": row["name"], "contracts_symbol": row["contracts_symbol"]}
            for row in rows
        ]})
    except Exception as exc:
        logger.error("获取品种列表失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@assistant_bp.route("/assistant/variety-kline", methods=["GET"])
def variety_kline():
    """
    获取品种K线 + 主力/散户指数。
    参数：variety_id（必填），start_date，end_date（可选，默认近60天）。
    K线以 hist_{contracts_symbol.lower()} 表为主，指数以 fut_strength LEFT JOIN。
    """
    variety_id = request.args.get("variety_id")
    if not variety_id:
        return _error("variety_id 不能为空")

    from datetime import timedelta
    today = date.today()
    default_start = (today - timedelta(days=60)).isoformat()
    start_date = request.args.get("start_date") or default_start
    end_date = request.args.get("end_date") or today.isoformat()

    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, name, contracts_symbol FROM fut_variety WHERE id = %s",
            (int(variety_id),)
        )
        variety = cursor.fetchone()
        if not variety or not variety["contracts_symbol"]:
            return _error("品种不存在或未配置 contracts_symbol")

        symbol = variety["contracts_symbol"].lower()
        table = f"hist_{symbol}"

        cursor.execute(
            f"SELECT trade_date, open_price, high_price, low_price, close_price, volume "
            f"FROM {table} "
            f"WHERE trade_date >= %s AND trade_date <= %s "
            f"ORDER BY trade_date ASC",
            (start_date, end_date),
        )
        kline_rows = cursor.fetchall()

        cursor.execute(
            "SELECT trade_date, main_force, retail FROM fut_strength "
            "WHERE variety_id = %s AND trade_date >= %s AND trade_date <= %s "
            "ORDER BY trade_date ASC",
            (int(variety_id), start_date, end_date),
        )
        strength_rows = cursor.fetchall()
        strength_map = {_date_str(r["trade_date"]): r for r in strength_rows}

        kline = []
        strength = []
        for row in kline_rows:
            dt = _date_str(row["trade_date"])
            kline.append({
                "trade_date": dt,
                "open":   float(row["open_price"]),
                "high":   float(row["high_price"]),
                "low":    float(row["low_price"]),
                "close":  float(row["close_price"]),
                "volume": int(row["volume"]),
            })
            s = strength_map.get(dt)
            strength.append({
                "trade_date": dt,
                "main_force": float(s["main_force"]) if s and s["main_force"] is not None else None,
                "retail":     float(s["retail"])     if s and s["retail"]     is not None else None,
            })

        return _success({
            "variety": {"id": variety["id"], "name": variety["name"]},
            "kline":   kline,
            "strength": strength,
        })
    except Exception as exc:
        logger.error("获取品种K线失败: %s", exc)
        return _error(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()
