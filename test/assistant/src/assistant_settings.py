"""assistant 模块共享常量。"""

INITIAL_CAPITAL = 30000.0
DEFAULT_SIZE_PCT = 0.3
MAX_POSITIONS = 3
LEVERAGE = 10.0
MAX_HOLD_DAYS = 5
ROLLING_WINDOW_DAYS = 63
LLM_CONTEXT_DAYS = 10

MECHANICAL_ACCOUNT = "mechanical"
LLM_ACCOUNT = "llm"

STRATEGY_PRIORITY = {
    "1A": 1,
    "1B": 1,
    "2A": 2,
    "2B": 2,
}

STRATEGY_LABELS = {
    "1A": "高幅度主散共振做多",
    "1B": "高幅度主散共振做空",
    "2A": "D7 主散共振做空",
    "2B": "D7 主散共振做多",
}

