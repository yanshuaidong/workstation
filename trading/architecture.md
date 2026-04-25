# 量化策略架构

本文档汇总量化策略链路上的四个子系统：数据采集、策略计算、后端 API、前端可视化，以及它们共享的数据库表结构。

## 总体链路

```text
[东方财富截图 / AkShare]
        │
        ▼
database/fut_pulse        采集主力散户强度 + 日收盘价
        │  (fut_variety / fut_strength / fut_daily_close)
        ▼
trading/strategies        每日批处理：信号 → 操作建议 → 自动账户
        │  (trading_signals / trading_operations / trading_positions /
        │   trading_account_daily / trading_pool / trading_signal_state)
        ▼
automysqlback             Flask REST API，统一前缀 /api，端口 7001
        │
        ▼
workfront                 Vue 3 前端，通过 /api-a 经 Nginx 反代访问后端
```

数据流向是单向的：采集层只写入基础数据表，策略层只读基础表并写入策略结果表，后端只读这两类表对外暴露查询接口，前端只通过后端接口访问。策略层不提供任何 HTTP 接口。

## 1. 数据库设计

### 1.1 基础数据表（由 `database/fut_pulse` 维护）

| 表名 | 作用 | 关键字段 |
|------|------|----------|
| `fut_variety` | 品种维表 | `id`、`name`、`key` |
| `fut_strength` | 主力 / 散户资金强度日序列 | `variety_id`、`trade_date`、`main_force`、`retail` |
| `fut_daily_close` | 期货主连日收盘价 | `variety_id`、`trade_date`、`close_price`、`collected_at` |

三张表均由 `fut_pulse` 在运行时自动建表，是策略层唯一的只读输入。

### 1.2 策略结果表（由 `trading/strategies/create_tables.py` 创建）

| 表名 | 作用 |
|------|------|
| `trading_pool` | 池子 A 品种配置（全市场品种镜像，默认 12 个激活 + 板块 + `is_active`） |
| `trading_signals` | 每日全品种信号（开仓 / 平仓 / `main_score` / `extra_json`） |
| `trading_operations` | 每日操作建议与落选原因（`is_selected`、`reject_reason`） |
| `trading_positions` | 自动账户持仓与已平仓记录（`status='open'/'closed'`、`pnl_pct`） |
| `trading_account_daily` | 每日账户权益、现金、持仓市值、日盈亏 |
| `trading_signal_state` | 每个品种的信号状态快照，主键 `(variety_id, state_date)` |

### 1.3 后端业务表（与策略链路并存）

| 表名 | 模块 |
|------|------|
| `contracts_main` / `history_update_log` / `hist_{symbol}` | 合约与历史行情 |
| `system_config` / `contract_list_update_log` / `recommendation_log` | 系统设置与运行日志 |
| `news_red_telegraph` / `news_process_tracking` | 财联社新闻与跟踪 |
| `futures_positions` | 业务持仓（与策略账户的 `trading_positions` 区分） |
| `futures_events` | 品种事件 |

策略链路只关心 `fut_*` 与 `trading_*` 两组表，其余表不参与每日批处理。

## 2. 数据采集：`database/fut_pulse`

详见 [`database/fut_pulse/README.md`](../database/fut_pulse/README.md)。

承担两类基础数据的入库：

- `fut_strength`：通过截图 + OCR 识别东方财富主力 / 散户资金强度
- `fut_daily_close`：通过 AkShare 拉取主连日收盘价

### 关键命令

| 命令 | 作用 |
|------|------|
| `python main.py today` | 当日截图 → OCR → 上传 `fut_strength` → 自动补当日 `fut_daily_close` |
| `python main.py history --start ... --end ...` | 历史强度回填，仅写 `fut_strength` |
| `python main.py close-history --start ... --end ...` | 历史收盘价回填，仅写 `fut_daily_close` |
| `python main.py calibrate` | 首次校准截图坐标 |

链路设计上，`history` 只负责强度，历史 close 单独通过 `close-history` 调用 AkShare，两条链路解耦以便单独重试。

### 输入输出

- 输入：东方财富客户端截图 + AkShare API
- 输出：`fut_variety` / `fut_strength` / `fut_daily_close`
- 配置：`config/varieties.json`、`close_price.py` 中的 `CLOSE_API_SYMBOL_MAP`、可选 `config/holidays.json`

## 3. 策略计算：`trading/strategies`

详见 [`trading/strategies/README.md`](./strategies/README.md)。

### 3.1 模块结构

```text
trading/strategies/
├── db.py                     数据库连接
├── data_loader.py            读取 fut_variety / fut_strength / fut_daily_close + 完整性检查
├── signals.py                计算 A 通道开平仓信号 + main_score，写 trading_signals / trading_signal_state
├── operations.py             生成池子 A 操作建议，写 trading_operations
├── account.py                自动账户平仓 → 开仓 → 资金曲线
├── settings.py               策略常量、默认池子 A、VARIETY_SECTORS 全品种板块映射
├── create_tables.py          建表、初始化池子、sync_pool_with_varieties 同步入口
├── backfill_pool_sectors.py  一次性迁移脚本：回填老库空 sector、补齐全品种镜像
└── daily_run.py              每日批处理入口
```

### 3.2 核心常量

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

池子 A 默认激活 12 个品种，覆盖有色金属、贵金属、黑色系、化工能化、油脂油料、农产品 6 个板块；`trading_pool` 中同时镜像 `fut_variety` 所有品种（其余以 `is_active=0` 持有），由前端「池子管理」页面通过 `PATCH /api/trading/pool/variety/<id>` 动态切换启用状态。`trading/strategies/daily_run.py` 启动时会调用 `sync_pool_with_varieties`，保证 `fut_pulse` 新增品种下一批处理就自动纳入可管理列表。

### 3.3 每日批处理顺序

```text
daily_run.py
  ├── check_data_completeness   池子 A 当日 fut_strength 必须齐全，否则终止
  ├── run_signals_for_all       全品种计算 A_OPEN_LONG/SHORT、A_CLOSE_LONG/SHORT
  ├── generate_operations       基于池子 A、MAX_SLOTS、板块约束筛选开仓候选
  ├── execute_close_signals     按当日收盘价平仓，更新 pnl_pct 并返回 closed_today
  ├── execute_open_operations   按 is_selected 开仓，跳过 closed_today 与已开放持仓
  └── update_account_daily      逐持仓累计日盈亏，写入资金曲线
```

### 3.4 信号要点

- 开仓信号要求 `cont7=True`、背景窗口 `bg1~bg5` 全部同号且 `bg5` 严格突出，并要求 `main_force` 与 `retail` 在触发窗口连续两日反向变化
- 平仓信号基于 `m3 = main_force[t] - main_force[t-2]`，并经过 `compute_signals` 内部状态机 + `trading_signal_state` 数据库快照两层过滤
- `main_score` 是 `abs(m3)` 在该品种最近 30 条记录中的分位数，仅用于开仓候选排序，平仓信号不写入 `main_score`

### 3.5 操作建议筛选规则

1. 候选必须在 `trading_pool` 且 `is_active = 1`
2. 已有开放持仓的品种、当日已平仓品种直接排除
3. 与当前持仓板块冲突的候选写入 `reject_reason='sector_conflict'`
4. 剩余候选按 `main_score` 排序，超过 `MAX_SLOTS - 当前持仓数` 的写入 `capacity_full`，同板块后续候选写入 `sector_conflict`

### 3.6 账户执行

- 平仓价 / 开仓价均使用当日 `fut_daily_close.close_price`
- `pnl_pct` 不带杠杆，资金曲线计算时再乘 `LEVERAGE`
- 每日权益按 `prev_equity` 为基准累计：`daily_pnl += prev_equity * size_pct * daily_ret * LEVERAGE`
- 当日已存在 `trading_account_daily` 记录时覆盖更新，保证脚本可重跑

### 3.7 运行入口

```bash
python -m trading.strategies.create_tables   # 首次初始化
python -m trading.strategies.daily_run       # 当日批处理
python -m trading.strategies.daily_run 2026-04-25
```

## 4. 后端：`automysqlback`

详见 [`automysqlback/README.md`](../automysqlback/README.md)。

Flask 服务监听 `7001`，统一前缀 `/api`，统一响应格式 `{code, message, data}`。Trading 模块的接口集中在 [`automysqlback/routes/trading_routes.py`](../automysqlback/routes/trading_routes.py)，全部为只读查询，绝不调用 `trading/strategies` 内部函数。

### 4.1 Trading 接口清单

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/trading/signals` | 信号面板，参数 `date` / `variety_name` / `signal_type` |
| `GET` | `/api/trading/operations` | 操作建议，参数 `date` / `variety_name` / `is_selected` |
| `GET` | `/api/trading/positions` | 当前开放持仓及浮动盈亏 |
| `GET` | `/api/trading/positions/history` | 已平仓历史，参数 `limit` |
| `GET` | `/api/trading/account/curve` | 资金曲线，参数 `start_date` / `end_date` |
| `GET` | `/api/trading/account/summary` | 账户摘要，参数 `date` |
| `GET` | `/api/trading/pool` | 池子 A 列表、启用状态、板块列表 |
| `PATCH` | `/api/trading/pool/variety/<variety_id>` | 更新池子 A 中单个品种的 `sector` 与 `is_active` |
| `GET` | `/api/trading/market-context` | 市场上下文，参数 `variety_id` / `days` / `end_date` |
| `GET` | `/api/trading/variety-list` | 含 `contracts_symbol` 的品种列表 |
| `GET` | `/api/trading/variety-kline` | 品种 K 线 + 主力 / 散户序列 |

### 4.2 数据来源映射

| 接口 | 读取的策略 / 基础表 |
|------|---------------------|
| `/api/trading/signals` | `trading_signals` |
| `/api/trading/operations` | `trading_operations` |
| `/api/trading/positions` | `trading_positions`（`status='open'`）+ `fut_daily_close` |
| `/api/trading/positions/history` | `trading_positions`（`status='closed'`） |
| `/api/trading/account/*` | `trading_account_daily` |
| `/api/trading/pool` | `trading_pool` + `fut_variety` |
| `/api/trading/market-context` / `variety-kline` | `fut_variety` + `fut_strength` + `fut_daily_close` |

### 4.3 启动行为

- 启动时按 `.env` → `env.production` 顺序加载配置
- `init_database()` 自动建表（仅业务表，不创建 `trading_*` 与 `fut_*`）
- `BackgroundScheduler` 根据 `system_config` 触发自动更新任务（与策略链路无关）

## 5. 前端：`workfront`

详见 [`workfront/README.md`](../workfront/README.md)。

Vue 3 + Element Plus + ECharts，通过相对路径 `/api-a` 调用后端，开发环境由 `vue.config.js` 代理转发，生产环境由 Nginx 将 `/api-a/` 重写为 `/api/`。

### 5.1 量化策略相关路由

| 路径 | 视图 | 数据来源 |
|------|------|----------|
| `/trading/signals` | 信号面板 | `/api/trading/signals` |
| `/trading/operations` | 操作建议 | `/api/trading/operations` |
| `/trading/positions` | 持仓盈亏 | `/api/trading/positions` + `/positions/history` |
| `/trading/curve` | 资金曲线 | `/api/trading/account/curve` + `/summary` |
| `/trading/kline` | 品种 K 线 | `/api/trading/variety-kline` + `/variety-list` |
| `/trading/pool` | 池子管理 | `/api/trading/pool`（`PATCH` 更新启用状态与板块） |

### 5.2 视图位置

```text
workfront/src/views/trading/
├── index.vue              Trading 模块容器
├── SignalsView.vue        信号面板
├── OperationsView.vue     操作建议
├── PositionsView.vue      持仓盈亏
├── CurveView.vue          资金曲线
├── KlineView.vue          K 线展示
└── PoolView.vue           池子管理
```

接口地址集中在 [`workfront/src/api.js`](../workfront/src/api.js)，路由注册位于 [`workfront/src/router/index.js`](../workfront/src/router/index.js)。

## 6. 部署与请求路由

Docker 服务由 `deploy.sh` 统一编排（`nginx` + `workfront` + `automysqlback`），`spiderx` / `database` / `quantlab` 在宿主机以本地脚本运行。

Nginx 路由规则：

- `/` → 前端静态资源（workfront 容器）
- `/api-a/` → 后端 API（automysqlback 容器，内部重写为 `/api/`）

策略层不暴露任何端口，仅通过数据库与后端解耦。每日批处理需要在宿主机或定时任务中调用：

```bash
python -m trading.strategies.daily_run
```

## 7. 子系统职责边界

| 子系统 | 写表 | 读表 | 对外接口 |
|--------|------|------|----------|
| `database/fut_pulse` | `fut_variety` / `fut_strength` / `fut_daily_close` | — | 无（命令行） |
| `trading/strategies` | `trading_*` 6 张表 | `fut_*` 3 张表 + `trading_*` | 无（命令行） |
| `automysqlback` | 业务表（新闻、持仓、事件等） | `trading_*` + `fut_*` + 业务表 | REST `/api` |
| `workfront` | — | — | 浏览器 UI |

这一边界保证了：策略逻辑变更不影响后端接口形态，后端接口变更不影响策略批处理，采集层故障只阻断当日 `check_data_completeness`，不会污染历史结果表。
