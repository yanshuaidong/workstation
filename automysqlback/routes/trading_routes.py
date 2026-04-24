"""
trading 量化策略模块接口
包含：信号面板、操作建议、持仓盈亏、资金曲线、市场上下文、品种列表/K线
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta

import pymysql
from flask import Blueprint, current_app, jsonify, request

trading_bp = Blueprint("trading", __name__)
logger = logging.getLogger(__name__)

INITIAL_CAPITAL = 30000.0
LEVERAGE = 10.0


def _get_conn():
    return current_app.config["get_db_connection"]()


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
    return {}


def _latest_date(cursor, table, col):
    cursor.execute(f"SELECT MAX({col}) AS d FROM {table}")
    row = cursor.fetchone()
    return _date_str(row["d"]) if row and row.get("d") else None


def _ok(data=None, message="获取成功"):
    return jsonify({"code": 0, "message": message, "data": data or {}})


def _err(message, code=1):
    return jsonify({"code": code, "message": message})


# ──────────────────────────────────────────────
# 信号面板（全品种）
# ──────────────────────────────────────────────

@trading_bp.route("/trading/signals", methods=["GET"])
def get_trading_signals():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        signal_date = request.args.get("date", "").strip() or _latest_date(cursor, "trading_signals", "signal_date")
        variety_name = request.args.get("variety_name", "").strip()
        signal_type = request.args.get("signal_type", "").strip()

        clauses = []
        params = []
        if signal_date:
            clauses.append("signal_date=%s")
            params.append(signal_date)
        if variety_name:
            clauses.append("variety_name LIKE %s")
            params.append(f"%{variety_name}%")
        if signal_type:
            clauses.append("signal_type=%s")
            params.append(signal_type)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        cursor.execute(
            f"SELECT id, signal_date, variety_id, variety_name, signal_type, main_score, "
            f"extra_json, created_at FROM trading_signals {where} "
            f"ORDER BY signal_date DESC, signal_type, variety_name",
            params,
        )
        rows = cursor.fetchall()
        signals = [
            {
                "id": r["id"],
                "signal_date": _date_str(r["signal_date"]),
                "variety_id": r["variety_id"],
                "variety_name": r["variety_name"],
                "signal_type": r["signal_type"],
                "main_score": float(r["main_score"]) if r["main_score"] is not None else None,
                "extra_json": _parse_json(r["extra_json"]),
                "created_at": r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if r["created_at"] else "",
            }
            for r in rows
        ]
        return _ok({"date": signal_date, "signals": signals, "total": len(signals)})
    except Exception as exc:
        logger.error("获取信号失败: %s", exc)
        return _err(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


# ──────────────────────────────────────────────
# 操作建议（池子A）
# ──────────────────────────────────────────────

@trading_bp.route("/trading/operations", methods=["GET"])
def get_trading_operations():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        signal_date = request.args.get("date", "").strip() or _latest_date(cursor, "trading_operations", "signal_date")
        variety_name = request.args.get("variety_name", "").strip()
        is_selected = request.args.get("is_selected", "").strip()

        clauses = []
        params = []
        if signal_date:
            clauses.append("signal_date=%s")
            params.append(signal_date)
        if variety_name:
            clauses.append("variety_name LIKE %s")
            params.append(f"%{variety_name}%")
        if is_selected != "":
            clauses.append("is_selected=%s")
            params.append(int(is_selected))

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        cursor.execute(
            f"SELECT id, signal_date, variety_id, variety_name, sector, signal_type, "
            f"main_score, is_selected, reject_reason, extra_json, created_at "
            f"FROM trading_operations {where} "
            f"ORDER BY is_selected DESC, main_score DESC, variety_name",
            params,
        )
        rows = cursor.fetchall()
        ops = [
            {
                "id": r["id"],
                "signal_date": _date_str(r["signal_date"]),
                "variety_id": r["variety_id"],
                "variety_name": r["variety_name"],
                "sector": r["sector"],
                "signal_type": r["signal_type"],
                "main_score": float(r["main_score"]) if r["main_score"] is not None else None,
                "is_selected": int(r["is_selected"] or 0),
                "reject_reason": r["reject_reason"],
                "extra_json": _parse_json(r["extra_json"]),
                "created_at": r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if r["created_at"] else "",
            }
            for r in rows
        ]
        return _ok({"date": signal_date, "operations": ops, "total": len(ops)})
    except Exception as exc:
        logger.error("获取操作建议失败: %s", exc)
        return _err(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


# ──────────────────────────────────────────────
# 持仓（当前 + 历史）
# ──────────────────────────────────────────────

@trading_bp.route("/trading/positions", methods=["GET"])
def get_trading_positions():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(
            """
            SELECT
                p.id, p.operation_id, p.variety_id, p.variety_name, p.sector,
                p.direction, p.open_date, p.open_price, p.size_pct,
                latest.trade_date AS latest_trade_date,
                latest.close_price AS current_price,
                latest.main_force, latest.retail
            FROM trading_positions p
            LEFT JOIN (
                SELECT s.variety_id, s.trade_date, s.main_force, s.retail, c.close_price
                FROM fut_strength s
                INNER JOIN fut_daily_close c
                    ON s.variety_id=c.variety_id AND s.trade_date=c.trade_date
                INNER JOIN (
                    SELECT variety_id, MAX(trade_date) AS latest_trade_date
                    FROM fut_strength GROUP BY variety_id
                ) mx ON s.variety_id=mx.variety_id AND s.trade_date=mx.latest_trade_date
            ) latest ON p.variety_id=latest.variety_id
            WHERE p.status='open'
            ORDER BY p.open_date, p.id
            """
        )
        rows = cursor.fetchall()

        positions = []
        for r in rows:
            cur_price = float(r["current_price"]) if r["current_price"] is not None else None
            open_price = float(r["open_price"])
            direction_sign = 1 if r["direction"] == "LONG" else -1
            floating_pnl_pct = None
            floating_pnl_amount = None
            if cur_price is not None and open_price:
                raw_ret = direction_sign * (cur_price - open_price) / open_price
                floating_pnl_pct = raw_ret * LEVERAGE * 100
                floating_pnl_amount = INITIAL_CAPITAL * float(r["size_pct"]) * floating_pnl_pct / 100
            positions.append({
                "id": r["id"],
                "operation_id": r["operation_id"],
                "variety_id": r["variety_id"],
                "variety_name": r["variety_name"],
                "sector": r["sector"],
                "direction": r["direction"],
                "open_date": _date_str(r["open_date"]),
                "open_price": open_price,
                "current_price": cur_price,
                "size_pct": float(r["size_pct"]),
                "latest_trade_date": _date_str(r["latest_trade_date"]),
                "main_force": float(r["main_force"]) if r["main_force"] is not None else None,
                "retail": float(r["retail"]) if r["retail"] is not None else None,
                "floating_pnl_pct": round(floating_pnl_pct, 4) if floating_pnl_pct is not None else None,
                "floating_pnl_amount": round(floating_pnl_amount, 4) if floating_pnl_amount is not None else None,
            })
        return _ok({"positions": positions, "total": len(positions)})
    except Exception as exc:
        logger.error("获取持仓失败: %s", exc)
        return _err(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@trading_bp.route("/trading/positions/history", methods=["GET"])
def get_trading_positions_history():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        limit = min(max(int(request.args.get("limit", 100)), 1), 500)
        cursor.execute(
            "SELECT id, operation_id, variety_id, variety_name, sector, direction, "
            "open_date, open_price, close_date, close_price, size_pct, pnl_pct, created_at "
            "FROM trading_positions WHERE status='closed' "
            "ORDER BY close_date DESC, id DESC LIMIT %s",
            (limit,),
        )
        rows = cursor.fetchall()
        history = [
            {
                "id": r["id"],
                "operation_id": r["operation_id"],
                "variety_id": r["variety_id"],
                "variety_name": r["variety_name"],
                "sector": r["sector"],
                "direction": r["direction"],
                "open_date": _date_str(r["open_date"]),
                "open_price": float(r["open_price"]),
                "close_date": _date_str(r["close_date"]),
                "close_price": float(r["close_price"]) if r["close_price"] is not None else None,
                "size_pct": float(r["size_pct"]),
                "pnl_pct": float(r["pnl_pct"]) if r["pnl_pct"] is not None else None,
                "created_at": r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if r["created_at"] else "",
            }
            for r in rows
        ]
        return _ok({"history": history, "total": len(history)})
    except Exception as exc:
        logger.error("获取历史持仓失败: %s", exc)
        return _err(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


# ──────────────────────────────────────────────
# 资金曲线
# ──────────────────────────────────────────────

@trading_bp.route("/trading/account/curve", methods=["GET"])
def get_trading_account_curve():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        start_date = request.args.get("start_date", "").strip()
        end_date = request.args.get("end_date", "").strip()

        clauses = []
        params = []
        if start_date:
            clauses.append("record_date>=%s")
            params.append(start_date)
        if end_date:
            clauses.append("record_date<=%s")
            params.append(end_date)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        cursor.execute(
            f"SELECT record_date, equity, cash, position_val, daily_pnl "
            f"FROM trading_account_daily {where} ORDER BY record_date",
            params,
        )
        rows = cursor.fetchall()
        curve = [
            {
                "record_date": _date_str(r["record_date"]),
                "equity": float(r["equity"]),
                "cash": float(r["cash"]),
                "position_val": float(r["position_val"]),
                "daily_pnl": float(r["daily_pnl"]),
            }
            for r in rows
        ]
        return _ok({"curve": curve, "total": len(curve)})
    except Exception as exc:
        logger.error("获取资金曲线失败: %s", exc)
        return _err(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@trading_bp.route("/trading/account/summary", methods=["GET"])
def get_trading_account_summary():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        requested_date = request.args.get("date", "").strip()
        if requested_date:
            cursor.execute(
                "SELECT record_date, equity, cash, position_val, daily_pnl "
                "FROM trading_account_daily WHERE record_date<=%s "
                "ORDER BY record_date DESC LIMIT 1",
                (requested_date,),
            )
        else:
            cursor.execute(
                "SELECT record_date, equity, cash, position_val, daily_pnl "
                "FROM trading_account_daily ORDER BY record_date DESC LIMIT 1"
            )
        snapshot = cursor.fetchone()

        cursor.execute("SELECT COUNT(1) AS cnt FROM trading_positions WHERE status='open'")
        open_cnt = cursor.fetchone()["cnt"]

        if snapshot:
            summary = {
                "record_date": _date_str(snapshot["record_date"]),
                "equity": float(snapshot["equity"]),
                "cash": float(snapshot["cash"]),
                "position_val": float(snapshot["position_val"]),
                "daily_pnl": float(snapshot["daily_pnl"]),
                "open_positions": int(open_cnt),
            }
        else:
            summary = {
                "record_date": None,
                "equity": INITIAL_CAPITAL,
                "cash": INITIAL_CAPITAL,
                "position_val": 0.0,
                "daily_pnl": 0.0,
                "open_positions": 0,
            }
        return _ok({"summary": summary})
    except Exception as exc:
        logger.error("获取账户摘要失败: %s", exc)
        return _err(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


# ──────────────────────────────────────────────
# 池子A品种列表
# ──────────────────────────────────────────────

@trading_bp.route("/trading/pool", methods=["GET"])
def get_trading_pool():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(
            "SELECT id, variety_id, variety_name, sector, is_active, created_at "
            "FROM trading_pool ORDER BY sector, variety_name"
        )
        rows = cursor.fetchall()
        pool = [
            {
                "id": r["id"],
                "variety_id": r["variety_id"],
                "variety_name": r["variety_name"],
                "sector": r["sector"],
                "is_active": int(r["is_active"]),
                "created_at": r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if r["created_at"] else "",
            }
            for r in rows
        ]
        return _ok({"pool": pool, "total": len(pool)})
    except Exception as exc:
        logger.error("获取池子A失败: %s", exc)
        return _err(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


# ──────────────────────────────────────────────
# 市场上下文（主力/散户/收盘价序列）
# ──────────────────────────────────────────────

@trading_bp.route("/trading/market-context", methods=["GET"])
def get_trading_market_context():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        variety_id = request.args.get("variety_id", "").strip()
        if not variety_id:
            return _err("缺少 variety_id 参数")
        days = min(max(int(request.args.get("days", 10)), 3), 60)
        end_date = request.args.get("end_date", "").strip()
        if not end_date:
            cursor.execute(
                "SELECT MAX(trade_date) AS d FROM fut_strength WHERE variety_id=%s",
                (int(variety_id),),
            )
            row = cursor.fetchone()
            end_date = _date_str(row["d"]) if row and row.get("d") else None

        cursor.execute(
            """
            SELECT s.variety_id,
                   COALESCE(v.name, CAST(s.variety_id AS CHAR)) AS variety_name,
                   s.trade_date, s.main_force, s.retail, c.close_price
            FROM fut_strength s
            INNER JOIN fut_daily_close c
                ON s.variety_id=c.variety_id AND s.trade_date=c.trade_date
            LEFT JOIN fut_variety v ON s.variety_id=v.id
            WHERE s.variety_id=%s AND s.trade_date<=%s
            ORDER BY s.trade_date DESC LIMIT %s
            """,
            (int(variety_id), end_date, days),
        )
        rows = list(reversed(cursor.fetchall()))
        series = [
            {
                "trade_date": _date_str(r["trade_date"]),
                "main_force": float(r["main_force"]),
                "retail": float(r["retail"]),
                "close_price": float(r["close_price"]),
            }
            for r in rows
        ]
        variety_name = rows[0]["variety_name"] if rows else ""
        return _ok({"variety_id": int(variety_id), "variety_name": variety_name,
                    "end_date": end_date, "days": days, "series": series})
    except Exception as exc:
        logger.error("获取市场上下文失败: %s", exc)
        return _err(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


# ──────────────────────────────────────────────
# 品种列表 + K线
# ──────────────────────────────────────────────

@trading_bp.route("/trading/variety-list", methods=["GET"])
def get_trading_variety_list():
    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(
            "SELECT id, name, contracts_symbol FROM fut_variety "
            "WHERE contracts_symbol IS NOT NULL AND contracts_symbol != '' ORDER BY id"
        )
        rows = cursor.fetchall()
        return _ok({"varieties": [
            {"id": r["id"], "name": r["name"], "contracts_symbol": r["contracts_symbol"]}
            for r in rows
        ]})
    except Exception as exc:
        logger.error("获取品种列表失败: %s", exc)
        return _err(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()


@trading_bp.route("/trading/variety-kline", methods=["GET"])
def get_trading_variety_kline():
    variety_id = request.args.get("variety_id")
    if not variety_id:
        return _err("variety_id 不能为空")

    today = date.today()
    default_start = (today - timedelta(days=60)).isoformat()
    start_date = request.args.get("start_date") or default_start
    end_date = request.args.get("end_date") or today.isoformat()

    conn = _get_conn()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(
            "SELECT id, name, contracts_symbol FROM fut_variety WHERE id=%s",
            (int(variety_id),),
        )
        variety = cursor.fetchone()
        if not variety or not variety["contracts_symbol"]:
            return _err("品种不存在或未配置 contracts_symbol")

        symbol = variety["contracts_symbol"].lower()
        table = f"hist_{symbol}"

        cursor.execute(
            f"SELECT trade_date, open_price, high_price, low_price, close_price, volume "
            f"FROM {table} WHERE trade_date>=%s AND trade_date<=%s ORDER BY trade_date ASC",
            (start_date, end_date),
        )
        kline_rows = cursor.fetchall()

        cursor.execute(
            "SELECT trade_date, main_force, retail FROM fut_strength "
            "WHERE variety_id=%s AND trade_date>=%s AND trade_date<=%s ORDER BY trade_date ASC",
            (int(variety_id), start_date, end_date),
        )
        strength_rows = cursor.fetchall()
        strength_map = {_date_str(r["trade_date"]): r for r in strength_rows}

        kline = []
        strength = []
        for r in kline_rows:
            dt = _date_str(r["trade_date"])
            kline.append({
                "trade_date": dt,
                "open": float(r["open_price"]),
                "high": float(r["high_price"]),
                "low": float(r["low_price"]),
                "close": float(r["close_price"]),
                "volume": int(r["volume"]),
            })
            s = strength_map.get(dt)
            strength.append({
                "trade_date": dt,
                "main_force": float(s["main_force"]) if s and s["main_force"] is not None else None,
                "retail": float(s["retail"]) if s and s["retail"] is not None else None,
            })
        return _ok({"variety": {"id": variety["id"], "name": variety["name"]},
                    "kline": kline, "strength": strength})
    except Exception as exc:
        logger.error("获取品种K线失败: %s", exc)
        return _err(f"获取失败: {exc}")
    finally:
        cursor.close()
        conn.close()
