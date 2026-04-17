"""assistant 四条策略生成与入库。"""

from __future__ import annotations

from typing import Any

import pandas as pd

from assistant_db import dump_json, parse_date, parse_json, to_date_str
from assistant_settings import MECHANICAL_ACCOUNT, STRATEGY_LABELS, STRATEGY_PRIORITY


def _extract_indicator_value(record: dict[str, Any]) -> str:
    extra = parse_json(record.get("extra_json"))
    return str(extra.get("indicator_value") or record.get("indicator_value") or "")


def generate_operations(signals_df: pd.DataFrame) -> pd.DataFrame:
    """由信号表聚合出策略操作建议。"""
    if signals_df.empty:
        return pd.DataFrame(
            columns=[
                "signal_date",
                "variety_id",
                "variety_name",
                "strategy",
                "direction",
                "account_type",
                "executed",
                "priority",
                "extra_json",
            ]
        )

    normalized = signals_df.copy()
    normalized["signal_date"] = normalized["signal_date"].apply(parse_date)
    normalized["indicator_value"] = normalized.apply(
        lambda row: row.get("indicator_value") or _extract_indicator_value(row.to_dict()),
        axis=1,
    )

    grouped = {}
    for row in normalized.to_dict("records"):
        key = (row["signal_date"], int(row["variety_id"]), row["direction"])
        grouped.setdefault(key, {})[row["indicator"]] = row

    operations: list[dict[str, Any]] = []
    for (signal_date, variety_id, direction), indicator_map in grouped.items():
        magnitude = indicator_map.get("MF_Magnitude")
        divergence = indicator_map.get("MS_Divergence")
        duration = indicator_map.get("MF_Duration")
        composite = indicator_map.get("Composite_Score")

        composite_score = float(composite["strength"]) if composite is not None else 0.0
        variety_name = (
            magnitude
            or divergence
            or duration
            or composite
        )["variety_name"]

        if (
            magnitude is not None
            and divergence is not None
            and str(magnitude["indicator_value"]).startswith("高幅度")
            and str(divergence["indicator_value"]).startswith("强共振")
        ):
            strategy = "1A" if direction == "LONG" else "1B"
            operations.append(
                {
                    "signal_date": signal_date,
                    "variety_id": variety_id,
                    "variety_name": variety_name,
                    "strategy": strategy,
                    "direction": direction,
                    "account_type": MECHANICAL_ACCOUNT,
                    "executed": 0,
                    "priority": STRATEGY_PRIORITY[strategy],
                    "composite_score": composite_score,
                    "extra_json": {
                        "strategy_label": STRATEGY_LABELS[strategy],
                        "composite_score": composite_score,
                        "trigger_indicators": {
                            "MF_Magnitude": magnitude["indicator_value"],
                            "MS_Divergence": divergence["indicator_value"],
                        },
                    },
                }
            )

        if (
            duration is not None
            and divergence is not None
            and str(duration["indicator_value"]) == "D7"
            and str(divergence["indicator_value"]).startswith("强共振")
        ):
            strategy = "2B" if direction == "LONG" else "2A"
            operations.append(
                {
                    "signal_date": signal_date,
                    "variety_id": variety_id,
                    "variety_name": variety_name,
                    "strategy": strategy,
                    "direction": direction,
                    "account_type": MECHANICAL_ACCOUNT,
                    "executed": 0,
                    "priority": STRATEGY_PRIORITY[strategy],
                    "composite_score": composite_score,
                    "extra_json": {
                        "strategy_label": STRATEGY_LABELS[strategy],
                        "composite_score": composite_score,
                        "trigger_indicators": {
                            "MF_Duration": duration["indicator_value"],
                            "MS_Divergence": divergence["indicator_value"],
                        },
                    },
                }
            )

    operations_df = pd.DataFrame(operations)
    if operations_df.empty:
        return operations_df
    return operations_df.sort_values(
        ["signal_date", "priority", "composite_score"],
        ascending=[True, True, False],
    ).reset_index(drop=True)


def replace_operations(
    conn,
    operations_df: pd.DataFrame,
    start_date,
    end_date,
    account_type: str = MECHANICAL_ACCOUNT,
) -> int:
    """覆盖写入机械策略建议。"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            DELETE FROM assistant_operations
            WHERE signal_date >= %s
              AND signal_date <= %s
              AND account_type = %s
            """,
            (to_date_str(start_date), to_date_str(end_date), account_type),
        )

        if operations_df.empty:
            conn.commit()
            return 0

        sql = """
            INSERT INTO assistant_operations
                (signal_date, variety_id, variety_name, strategy,
                 direction, extra_json, account_type, executed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = [
            (
                to_date_str(row.signal_date),
                int(row.variety_id),
                row.variety_name,
                row.strategy,
                row.direction,
                dump_json(row.extra_json),
                row.account_type,
                int(row.executed),
            )
            for row in operations_df.itertuples(index=False)
        ]
        cursor.executemany(sql, params)
        conn.commit()
        return len(params)
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
