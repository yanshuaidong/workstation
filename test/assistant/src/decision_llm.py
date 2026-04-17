"""生成供本地 AI 工具使用的 LLM 决策提示词。"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pymysql

from assistant_db import parse_date, parse_json, to_date_str
from assistant_settings import INITIAL_CAPITAL, LLM_ACCOUNT, LLM_CONTEXT_DAYS, MECHANICAL_ACCOUNT


LOG_DIR = Path(__file__).resolve().parents[1] / "logs" / "llm"
LOG_DIR.mkdir(parents=True, exist_ok=True)


RESEARCH_CONTEXT = """## 研究结论（固定背景知识）
- 策略 1A / 1B：当 `MF_Magnitude=高幅度` 且 `MS_Divergence=强共振` 时，分别候选做多 / 做空。
- 策略 2A / 2B：当 `MF_Duration=D7` 且 `MS_Divergence=强共振` 时，分别候选做空 / 做多。
- 滚动分位必须只看近 3 个月（约 63 个交易日），不要用全历史极值。
- 机械账户与 LLM 账户必须严格分开，两个账户独立记录净值和持仓。
- LLM 账户每次决策只能通过 `write_llm_decision.py` 写入，不要直接操作数据库。
"""


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_无数据_\n"
    header_line = "| " + " | ".join(headers) + " |"
    split_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join([header_line, split_line, *body_lines]) + "\n"


def _fetch_operations(conn, signal_date):
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(
            """
            SELECT signal_date, variety_id, variety_name, strategy, direction, extra_json
            FROM assistant_operations
            WHERE signal_date = %s
              AND account_type = %s
            ORDER BY created_at, id
            """,
            (to_date_str(signal_date), MECHANICAL_ACCOUNT),
        )
        rows = cursor.fetchall()
        for row in rows:
            row["extra_json"] = parse_json(row["extra_json"])
        return rows
    finally:
        cursor.close()


def _fetch_positions(conn, account_type: str):
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(
            """
            SELECT variety_id, variety_name, direction, open_date, open_price, size_pct, strategy
            FROM assistant_positions
            WHERE account_type = %s AND status = 'open'
            ORDER BY open_date, id
            """,
            (account_type,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()


def _fetch_latest_snapshot(conn, account_type: str):
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
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
        return cursor.fetchone()
    finally:
        cursor.close()


def generate_llm_prompt(
    conn,
    signal_date,
    market_df: pd.DataFrame,
    output_dir: Path | None = None,
) -> Path:
    """为指定交易日生成本地 LLM 决策提示词。"""
    signal_date = parse_date(signal_date)
    output_dir = output_dir or LOG_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    operations = _fetch_operations(conn, signal_date)
    llm_positions = _fetch_positions(conn, LLM_ACCOUNT)
    llm_snapshot = _fetch_latest_snapshot(conn, LLM_ACCOUNT)
    market_df = market_df.copy()
    market_df["trade_day"] = market_df["trade_date"].dt.date

    sections = [f"# LLM 辅助决策提示词\n\n生成日期：`{to_date_str(signal_date)}`\n", RESEARCH_CONTEXT]

    operation_rows = []
    for op in operations:
        trigger_indicators = op["extra_json"].get("trigger_indicators", {})
        operation_rows.append(
            [
                op["variety_name"],
                op["strategy"],
                op["direction"],
                op["extra_json"].get("strategy_label", ""),
                "; ".join(f"{k}={v}" for k, v in trigger_indicators.items()),
                f"{float(op['extra_json'].get('composite_score', 0.0)):.2f}",
            ]
        )
    sections.append(
        "## 今日触发信号\n"
        + _markdown_table(
            ["品种", "策略", "方向", "策略说明", "触发指标值", "Composite_Score"],
            operation_rows,
        )
    )

    sections.append("## 候选品种近10日数据")
    for op in operations:
        context_df = (
            market_df[market_df["variety_id"] == int(op["variety_id"])]
            .sort_values("trade_date")
            .tail(LLM_CONTEXT_DAYS)
        )
        rows = [
            [
                row.trade_date.strftime("%Y-%m-%d"),
                f"{float(row.main_force):.2f}",
                f"{float(row.retail):.2f}",
                f"{float(row.close_price):.2f}",
            ]
            for row in context_df.itertuples(index=False)
        ]
        sections.append(f"### {op['variety_name']}（{op['strategy']} / {op['direction']}）")
        sections.append(_markdown_table(["日期", "main_force", "retail", "close"], rows))

    snapshot_text = (
        f"最新净值：`{float(llm_snapshot['equity']):.2f}`  "
        f"可用现金：`{float(llm_snapshot['cash']):.2f}`  "
        f"持仓市值：`{float(llm_snapshot['position_val']):.2f}`  "
        f"当日盈亏：`{float(llm_snapshot['daily_pnl']):.2f}`"
        if llm_snapshot
        else f"当前尚无快照，默认本金 `{INITIAL_CAPITAL:.2f}`"
    )
    sections.append(f"## 当前 LLM 账户状态\n{snapshot_text}\n")

    position_rows = [
        [
            row["variety_name"],
            row["direction"],
            to_date_str(row["open_date"]),
            f"{float(row['open_price']):.2f}",
            f"{float(row['size_pct']) * 100:.0f}%",
            row.get("strategy") or "",
        ]
        for row in llm_positions
    ]
    sections.append(
        _markdown_table(
            ["品种", "方向", "开仓日", "开仓价", "仓位", "来源策略"],
            position_rows,
        )
    )

    sections.append(
        """## 操作指令
请对每个候选品种决定：`open_long` / `open_short` / `close` / `hold`。

写库必须通过以下 CLI：

```bash
python src/write_llm_decision.py \
  --signal-date """
        + to_date_str(signal_date)
        + """ \
  --action open_long \
  --variety_id 28 \
  --variety_name PTA \
  --size_pct 0.3 \
  --strategy "1A" \
  --reasoning "请填写完整推理"
```

规则：
- 每条决策必须填写 `reasoning`。
- 不要直接操作数据库。
- 同一品种只允许单方向持仓。
- `hold` 只记录到日志，不会写数据库表。
"""
    )

    prompt_path = output_dir / f"{to_date_str(signal_date)}-prompt.md"
    prompt_path.write_text("\n\n".join(sections).strip() + "\n", encoding="utf-8")
    return prompt_path

