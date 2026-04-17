"""assistant 每日总入口。"""

from __future__ import annotations

import argparse
import json
from datetime import timedelta

from assistant_db import get_db_connection, get_latest_trade_date, parse_date, to_date_str
from data_loader import load_market_data
from decision_llm import generate_llm_prompt
from decision_mechanical import process_mechanical_account_for_date
from signals import generate_signals, replace_signals
from strategies import generate_operations, replace_operations


def parse_args():
    parser = argparse.ArgumentParser(description="运行 assistant 每日流程")
    parser.add_argument("--signal-date", help="仅处理指定交易日")
    parser.add_argument("--start-date", help="开始日期，支持回放")
    parser.add_argument("--end-date", help="结束日期，默认与开始日期相同")
    parser.add_argument(
        "--execute-mechanical",
        action="store_true",
        help="执行机械账户开平仓；不加时仅生成信号/建议/LLM prompt",
    )
    parser.add_argument(
        "--force-replay",
        action="store_true",
        help="强制重放机械账户当日执行（谨慎使用）",
    )
    return parser.parse_args()


def resolve_dates(args, conn):
    if args.signal_date:
        signal_date = parse_date(args.signal_date)
        return signal_date, signal_date
    if args.start_date:
        start_date = parse_date(args.start_date)
        end_date = parse_date(args.end_date) if args.end_date else start_date
        return start_date, end_date
    latest = get_latest_trade_date(conn)
    return latest, latest


def main():
    args = parse_args()
    conn = get_db_connection()
    try:
        start_date, end_date = resolve_dates(args, conn)
        market_df = load_market_data(
            start_date=start_date - timedelta(days=7),
            end_date=end_date,
            lookback_days=120,
            conn=conn,
        )

        signals_df = generate_signals(market_df, start_date=start_date, end_date=end_date)
        inserted_signals = replace_signals(conn, signals_df, start_date, end_date)

        operations_df = generate_operations(signals_df)
        inserted_operations = replace_operations(conn, operations_df, start_date, end_date)

        mechanical_results = []
        if args.execute_mechanical:
            trade_dates = sorted(
                {
                    row.date()
                    for row in market_df["trade_date"]
                    if start_date <= row.date() <= end_date
                }
            )
            for trade_date in trade_dates:
                mechanical_results.append(
                    process_mechanical_account_for_date(
                        conn,
                        trade_date,
                        market_df,
                        force=args.force_replay,
                    )
                )

        prompt_path = generate_llm_prompt(conn, end_date, market_df)
        summary = {
            "start_date": to_date_str(start_date),
            "end_date": to_date_str(end_date),
            "signals": inserted_signals,
            "operations": inserted_operations,
            "mechanical_results": mechanical_results,
            "llm_prompt": str(prompt_path),
        }
        print(json.dumps(summary, ensure_ascii=False, default=str, indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
