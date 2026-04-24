INITIAL_CAPITAL = 30000.0
LEVERAGE = 10.0
MAX_SLOTS = 3
SIZE_PCT = 1 / 3
BACKGROUND_WINDOW = 4
TRIGGER_WINDOW = 3
TURN_WINDOW = 3
MOMENTUM_LOOKBACK = 30

TARGET_POOL = [
    ("沪铜", "有色金属"),
    ("沪铝", "有色金属"),
    ("沪锌", "有色金属"),
    ("沪金", "贵金属"),
    ("铁矿石", "黑色系"),
    ("焦煤", "黑色系"),
    ("PTA", "化工能化"),
    ("甲醇", "化工能化"),
    ("橡胶", "化工能化"),
    ("豆粕", "油脂油料"),
    ("棕榈油", "油脂油料"),
    ("玉米", "农产品"),
]

TARGET_VARIETIES = [name for name, _ in TARGET_POOL]
SECTOR_BY_VARIETY = dict(TARGET_POOL)
