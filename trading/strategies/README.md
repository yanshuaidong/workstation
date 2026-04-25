# trading/strategies

`trading/strategies` 是交易策略批处理模块，负责按日完成以下链路：

1. 从 MySQL 读取品种维表、主力/散户强度和收盘价
2. 对全市场品种计算 A 通道信号
3. 对池子 A 品种生成操作建议
4. 按信号执行自动账户的平仓和开仓
5. 更新账户资金曲线

模块不提供 HTTP 接口，只负责写入策略结果表；对外查询由后端接口读取这些表。

## 目录结构

```text
trading/strategies/
├── README.md
├── account.py
├── create_tables.py
├── daily_run.py
├── data_loader.py
├── db.py
├── operations.py
├── settings.py
└── signals.py
```

各文件职责如下：

- `db.py`：从项目根目录的 `.env` 或 `env.production` 读取数据库配置，返回 PyMySQL 连接
- `data_loader.py`：读取 `fut_variety`、`fut_strength`、`fut_daily_close`，并做当日数据完整性检查
- `signals.py`：计算 A 通道开平仓信号、动量分位分，并写入 `trading_signals`
- `operations.py`：根据池子 A、仓位上限和板块约束生成操作建议，写入 `trading_operations`
- `account.py`：执行平仓、开仓并更新 `trading_account_daily` 和 `trading_positions`
- `create_tables.py`：创建策略相关数据表、初始化池子 A 和账户起始记录
- `daily_run.py`：每日批处理入口，按固定顺序串联全部步骤

## 配置常量

`settings.py` 中定义了当前策略的固定参数：

```python
INITIAL_CAPITAL = 30000.0
LEVERAGE = 10.0
MAX_SLOTS = 3
SIZE_PCT = 1 / 3
BACKGROUND_WINDOW = 5
TRIGGER_WINDOW = 3
TURN_WINDOW = 3
MOMENTUM_LOOKBACK = 30
```

池子 A 固定为 12 个品种：

| 品种 | 板块 |
|------|------|
| 沪铜 | 有色金属 |
| 沪铝 | 有色金属 |
| 沪锌 | 有色金属 |
| 沪金 | 贵金属 |
| 铁矿石 | 黑色系 |
| 焦煤 | 黑色系 |
| PTA | 化工能化 |
| 甲醇 | 化工能化 |
| 橡胶 | 化工能化 |
| 豆粕 | 油脂油料 |
| 棕榈油 | 油脂油料 |
| 玉米 | 农产品 |

## 数据读取与完整性检查

### 上游数据表

策略模块依赖以下只读表：

- `fut_variety`
- `fut_strength`
- `fut_daily_close`

### 单品种数据装载

`load_variety_data()` 会分别读取某个品种的：

- `fut_strength.trade_date, main_force, retail`
- `fut_daily_close.trade_date, close_price AS close`

随后按 `trade_date` 做内连接，并删除空值，得到该品种的完整时序数据。

### 每日完整性检查

`check_data_completeness(conn, trade_date)` 的逻辑是：

- 统计 `fut_strength` 在指定日期有数据的品种数
- 找出 `fut_variety` 中哪些品种在该日期缺少 `fut_strength`
- 只要池子 A 中有任一品种缺失当日 `fut_strength`，当日批处理就终止

当前检查只校验池子 A 的 `fut_strength` 是否齐全，不校验 `fut_daily_close`。

## 信号计算逻辑

### 连续性标记

`signals.py` 先对每个品种构造：

- `date_cont`：当前记录与上一条记录的日期差是否小于等于 7 天
- `cont7`：最近 7 条记录是否满足连续性要求
- `cont3`：最近 3 条记录是否满足连续性要求

这里的连续性判断基于相邻记录的自然日间隔，不要求数据库中逐日有记录。

### 开仓信号

对交易日 `t`：

- 背景窗口使用 `main_force[t-6] ~ main_force[t-2]`
- 触发窗口使用 `main_diff[t-1], main_diff[t]` 和 `retail_diff[t-1], retail_diff[t]`

`A_OPEN_LONG` 条件：

- `cont7 = True`
- `bg1 ~ bg5` 全部小于 0
- `bg5` 严格小于 `bg1 ~ bg4`
- `main_force` 连续两日上升
- `retail` 连续两日下降

`A_OPEN_SHORT` 条件：

- `cont7 = True`
- `bg1 ~ bg5` 全部大于 0
- `bg5` 严格大于 `bg1 ~ bg4`
- `main_force` 连续两日下降
- `retail` 连续两日上升

### 平仓信号

定义：

- `m3 = main_force[t] - main_force[t-2]`

初始平仓条件：

- `A_CLOSE_LONG`：`cont3 = True` 且 `m3 < 0`
- `A_CLOSE_SHORT`：`cont3 = True` 且 `m3 > 0`

随后会经过两层状态过滤：

1. `compute_signals()` 内部先用状态机过滤，只在本品种此前出现过对应开仓信号的情况下保留平仓信号
2. `save_signals()` 写库前再读取 `trading_signal_state` 中该品种在当日前的最新状态；如果数据库快照里没有对应方向的激活状态，则不会把该平仓信号写入 `trading_signals`

信号写入完成后，`save_signals()` 会同步更新 `trading_signal_state`，把该品种在当日结束后的状态写成 `none / long / short`。

### 动量分位分 `main_score`

`main_score` 只用于开仓信号排序，计算方式为：

- 取当前 `abs(m3)`
- 与该品种之前最多 30 条记录的 `abs(m3)` 历史序列比较
- 若历史有效样本少于 30，则记为 `NaN`
- 否则计算 `hist.le(current).sum() / 30`

开仓候选在排序时按以下键值排序：

1. `main_score` 是否为 `NaN`
2. `main_score` 从大到小
3. `variety_name` 升序

### 信号写表行为

`run_signals_for_all()` 会遍历 `fut_variety` 全部品种，逐个加载数据并计算信号。

`save_signals()` 的写表规则：

- 只处理目标日期对应的最后一条记录
- 写入前先删除该品种该日期在 `trading_signals` 中的旧记录
- 开仓信号写入 `main_score`
- 平仓信号不写 `main_score`
- `extra_json` 中保存用于前端解释的窗口数据、背景值、触发值和条件判断结果

## 操作建议生成逻辑

`generate_operations(conn, signal_date)` 的输入来自三部分：

- 当日 `trading_signals` 中的开仓信号
- `trading_pool` 中 `is_active = 1` 的池子 A 品种
- `trading_positions` 中的历史持仓状态

具体流程如下：

1. 删除 `trading_operations` 当日全部旧记录，保证重跑时结果覆盖
2. 读取在 `signal_date` 之前已经开仓且仍为 `open` 的持仓，作为当前占用槽位
3. 读取当日已经平仓的品种集合，避免同日反手
4. 从当日开仓信号里筛出候选，候选必须同时满足：
   - 品种在 `trading_pool` 且 `is_active = 1`
   - 品种当前没有历史开放持仓
   - 品种不在 `closed_today`
5. 计算可开仓槽位：`entry_capacity = MAX_SLOTS - 当前开放持仓数`
6. 先排除与当前持仓板块重复的候选，这部分写入 `reject_reason='sector_conflict'`
7. 对剩余候选按 `main_score` 排序，依次选入：
   - 已用过的板块不可重复
   - 超过剩余槽位的候选写入 `reject_reason='capacity_full'`
   - 同板块后续候选写入 `reject_reason='sector_conflict'`
8. 将选中和落选结果统一写入 `trading_operations`

需要注意：

- 非池子 A 品种不会进入 `trading_operations`
- 已持仓品种不会写入 `trading_operations`
- 当日刚平仓的品种不会写入 `trading_operations`
- 当可用槽位 `<= 0` 时，当前候选会全部写成 `capacity_full`

## 账户执行逻辑

账户执行顺序固定为：

1. `execute_close_signals()`
2. `execute_open_operations()`
3. `update_account_daily()`

### 平仓

`execute_close_signals()` 会：

- 读取当日 `trading_signals` 中的 `A_CLOSE_LONG / A_CLOSE_SHORT`
- 查找当前全部 `status='open'` 的持仓
- 方向匹配时，使用当日 `fut_daily_close.close_price` 平仓
- 将持仓更新为 `status='closed'`，同时写入 `close_date`、`close_price`、`pnl_pct`

`pnl_pct` 为不带杠杆的收益率：

- 多头：`(close_price - open_price) / open_price`
- 空头：`(open_price - close_price) / open_price`

函数返回当日已平仓品种集合，用于后续阻止同日再次开仓。

### 开仓

`execute_open_operations()` 会读取当日 `trading_operations` 中 `is_selected = 1` 的记录，并按以下规则开仓：

- 当日已平仓的品种直接跳过
- 若同一品种在同一开仓日已经存在 `status='open'` 的记录，则跳过，避免重跑时重复开仓
- 使用当日 `fut_daily_close.close_price` 作为开仓价
- `signal_type = A_OPEN_LONG` 时开多，否则开空
- 新持仓写入 `trading_positions`，`size_pct` 固定为 `SIZE_PCT`

### 资金曲线

`update_account_daily()` 会读取最近一条 `trading_account_daily` 作为上一日权益基准：

- `prev_equity`
- `prev_cash`

随后遍历当前全部 `status='open'` 的持仓，逐个计算：

- `daily_ret = direction_sign * (cur_price - prev_price) / prev_price`
- `daily_pnl += prev_equity * size_pct * daily_ret * LEVERAGE`
- `float_ret = direction_sign * (cur_price - open_price) / open_price`
- `position_val += prev_equity * size_pct * (1 + float_ret * LEVERAGE)`

最终账户值按当前实现写为：

- 有持仓时：`cash = prev_equity - position_val`
- 无持仓时：`cash = prev_equity`
- `equity = cash + position_val`

结果按 `record_date` 写入 `trading_account_daily`，若当日已存在记录则覆盖更新。

## 数据表

`create_tables.py` 会创建以下 6 张策略表：

| 表名 | 作用 |
|------|------|
| `trading_pool` | 池子 A 品种配置 |
| `trading_signals` | 每日全品种信号 |
| `trading_operations` | 每日操作建议与落选原因 |
| `trading_positions` | 自动账户持仓与已平仓记录 |
| `trading_account_daily` | 每日账户权益、现金、持仓市值、日盈亏 |
| `trading_signal_state` | 每个品种的信号状态快照 |

其中：

- `trading_pool` 按 `TARGET_POOL` 初始化
- `trading_account_daily` 首次初始化时写入一条起始记录，日期为执行初始化脚本当天
- `trading_signal_state` 以 `(variety_id, state_date)` 为主键，供信号层快速确认历史状态

## 初始化与运行

### 环境变量

数据库连接从项目根目录读取：

1. `.env`
2. `env.production`

需要提供：

```text
DB_HOST
DB_PORT
DB_USER
DB_PASSWORD
DB_NAME
```

### 初始化

在项目根目录执行：

```bash
python -m trading.strategies.create_tables
```

脚本会：

1. 删除 `assistant_signals`、`assistant_operations`、`assistant_positions`、`assistant_account_daily`
2. 创建 6 张 `trading_*` 表
3. 执行已实现的增量迁移
4. 初始化 `trading_pool`
5. 初始化 `trading_account_daily`

### 每日运行

```bash
python -m trading.strategies.daily_run
python -m trading.strategies.daily_run 2026-04-25
```

执行顺序固定为：

1. `check_data_completeness`
2. `run_signals_for_all`
3. `generate_operations`
4. `execute_close_signals`
5. `execute_open_operations`
6. `update_account_daily`

`daily_run.py` 在运行前会把仓库根目录加入 `sys.path`，因此推荐从项目根目录以模块方式执行。

## 对外读取

策略模块的结果表供后端接口读取。当前仓库中的接口入口位于：

- `automysqlback/routes/trading_routes.py`

前端和 API 查询使用这些结果表，不直接调用 `trading/strategies` 内部函数。
