"""本地 AI 写入 LLM 决策的 CLI 工具。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from assistant_db import cli_fail, dump_json, get_db_connection, get_latest_trade_date, parse_date, to_date_str
from assistant_settings import DEFAULT_SIZE_PCT, INITIAL_CAPITAL, LLM_ACCOUNT, MAX_POSITIONS
from data_loader import load_market_data
from paper_account import (
    available_slots,
    calculate_position_pnl_pct,
    close_position,
    get_open_position_by_variety,
    get_open_positions,
    get_market_row,
    open_position,
    upsert_account_snapshot,
    build_market_map,
)


LOG_DIR = Path(__file__).resolve().parents[1] / "logs" / "llm"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def parse_args():
    parser = argparse.ArgumentParser(description="写入一条 LLM 决策")
    parser.add_argument("--signal-date", help="交易日，默认取 fut_daily_close 最新日期")
    parser.add_argument(
        "--action",
        required=True,
        choices=["open_long", "open_short", "close", "hold"],
        help="决策动作",
    )
    parser.add_argument("--variety_id", type=int, required=True, help="品种 ID")
    parser.add_argument("--variety_name", required=True, help="品种名")
    parser.add_argument("--size_pct", type=float, default=DEFAULT_SIZE_PCT, help="仓位比例")
    parser.add_argument("--strategy", default="", help="策略标识")
    parser.add_argument("--reasoning", required=True, help="决策原因")
    return parser.parse_args()


def append_log(signal_date, payload: dict) -> Path:
    log_path = LOG_DIR / f"{to_date_str(signal_date)}-calls.jsonl"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return log_path


def insert_operation(conn, signal_date, variety_id, variety_name, strategy, direction, extra_json):
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO assistant_operations
                (signal_date, variety_id, variety_name, strategy,
                 direction, extra_json, account_type, executed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
            """,
            (
                to_date_str(signal_date),
                int(variety_id),
                variety_name,
                strategy,
                direction,
                dump_json(extra_json),
                LLM_ACCOUNT,
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def main():
    args = parse_args()
    conn = get_db_connection()
    try:
        signal_date = parse_date(args.signal_date) if args.signal_date else get_latest_trade_date(conn)
        market_df = load_market_data(
            start_date=signal_date,
            end_date=signal_date,
            lookback_days=15,
            variety_ids=[args.variety_id],
            conn=conn,
        )
        market_map = build_market_map(market_df)
        market_row = get_market_row(market_map, args.variety_id, signal_date)
        if market_row is None and args.action != "hold":
            cli_fail(f"{args.variety_name} 在 {to_date_str(signal_date)} 无行情数据")

        payload = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "signal_date": to_date_str(signal_date),
            "account_type": LLM_ACCOUNT,
            "action": args.action,
            "variety_id": args.variety_id,
            "variety_name": args.variety_name,
            "size_pct": args.size_pct,
            "strategy": args.strategy,
            "reasoning": args.reasoning,
        }

        if args.action in ("open_long", "open_short"):
            if available_slots(conn, LLM_ACCOUNT) <= 0:
                cli_fail(f"LLM 账户已满仓，最多 {MAX_POSITIONS} 个持仓")
            existing = get_open_position_by_variety(conn, LLM_ACCOUNT, args.variety_id)
            if existing:
                cli_fail(f"{args.variety_name} 已有未平仓记录，不能重复开仓")

            direction = "LONG" if args.action == "open_long" else "SHORT"
            operation_id = insert_operation(
                conn,
                signal_date,
                args.variety_id,
                args.variety_name,
                args.strategy or direction.lower(),
                direction,
                {
                    "action": args.action,
                    "reasoning": args.reasoning,
                    "size_pct": args.size_pct,
                },
            )
            position_id = open_position(
                conn,
                account_type=LLM_ACCOUNT,
                variety_id=args.variety_id,
                variety_name=args.variety_name,
                direction=direction,
                open_date=signal_date,
                open_price=float(market_row["close_price"]),
                size_pct=args.size_pct,
                strategy=args.strategy or direction.lower(),
            )
            snapshot = upsert_account_snapshot(conn, LLM_ACCOUNT, signal_date, market_df)
            payload.update(
                {
                    "operation_id": operation_id,
                    "position_id": position_id,
                    "open_price": float(market_row["close_price"]),
                    "snapshot_equity": snapshot["equity"],
                }
            )

        elif args.action == "close":
            existing = get_open_position_by_variety(conn, LLM_ACCOUNT, args.variety_id)
            if not existing:
                cli_fail(f"{args.variety_name} 没有可平的未平仓记录")

            pnl_pct = calculate_position_pnl_pct(existing, float(market_row["close_price"]))
            operation_id = insert_operation(
                conn,
                signal_date,
                args.variety_id,
                args.variety_name,
                args.strategy or "manual_close",
                existing["direction"],
                {
                    "action": args.action,
                    "reasoning": args.reasoning,
                    "close_price": float(market_row["close_price"]),
                    "pnl_pct": round(pnl_pct, 4),
                },
            )
            close_position(
                conn,
                int(existing["id"]),
                signal_date,
                float(market_row["close_price"]),
                pnl_pct,
            )
            snapshot = upsert_account_snapshot(conn, LLM_ACCOUNT, signal_date, market_df)
            payload.update(
                {
                    "operation_id": operation_id,
                    "position_id": int(existing["id"]),
                    "close_price": float(market_row["close_price"]),
                    "pnl_pct": round(pnl_pct, 4),
                    "snapshot_equity": snapshot["equity"],
                }
            )

        else:
            open_positions = get_open_positions(conn, LLM_ACCOUNT)
            payload["open_positions"] = len(open_positions)

        log_path = append_log(signal_date, payload)
        print(
            json.dumps(
                {
                    "ok": True,
                    "action": args.action,
                    "variety_id": args.variety_id,
                    "variety_name": args.variety_name,
                    "signal_date": to_date_str(signal_date),
                    "log_path": str(log_path),
                },
                ensure_ascii=False,
            )
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()

