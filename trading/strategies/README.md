# trading/strategies

> 独立的策略计算模块：从线上 MySQL 拉取原始数据 → 计算 A 通道信号 → 生成操作建议 → 执行自动化账户的开平仓 → 更新资金曲线。
>
> 定位：**数据 → 信号 → 决策 → 执行**的单向管道。不依赖 `test/` 实验代码，也不包含任何 HTTP 接口（对外服务由 `automysqlback/routes/trading_routes.py` 暴露）。

---

## 一、设计理念：三层信息漏斗

前端展示、后端接口、库表结构全部围绕这条决策链路组织。每一层都是可解释、可审计的过滤，不是黑箱：

```
【信号面板】全市场观察
  对 fut_variety 全部品种计算 A 通道信号，提供全局视野。
  即使池子外的品种不做，也能看到市场机会和风险。
        ↓ 过滤：只看池子 A 的品种
【操作建议】决策透明
  池子 A 中所有触发开仓信号的品种全部列出，包括落选的。
  每条记录附 reject_reason：capacity_full / sector_conflict / null(已选中)。
        ↓ 过滤：is_selected = 1 的记录
【持仓盈亏 / 资金曲线】执行记录
  自动化账户按建议实际开平仓的结果，可回溯来源 operation_id。
```

---

## 二、策略核心：A 通道信号

对每个品种每个交易日 `t`，计算 4 种信号与 1 个排序分。实现见 `signals.py::compute_signals`，逻辑严格对标实验期脚本 `test/plan2/scripts/backtest_portfolio_strict7_tp3.py::compute_signals_strict7_tp3`。

### 开仓信号（需要连续 7 个交易日数据，由 `cont7` 校验）

**A_OPEN_LONG**（A 通道开多）

- 背景期 `[t-6, t-3]`：`main_force` 四点全部 < 0，且 `bg4 - bg1 < 0`（整体仍在下行）
- 触发期 `[t-2, t]`：`main_force` 严格连续上升（`main_diff[t-1] > 0` 且 `main_diff[t] > 0`），同时 `retail` 严格连续下降（反向确认）

**A_OPEN_SHORT**（A 通道开空，与开多完全对称）

- 背景期四点全部 > 0 且 `bg4 - bg1 > 0`
- 触发期 `main_force` 3 连降 + `retail` 3 连升

### 平仓信号（需要连续 3 个交易日数据，由 `cont3` 校验）

- **A_CLOSE_LONG**：`m3 = main_force[t] - main_force[t-2] < 0`（主力 3 日拐头向下）
- **A_CLOSE_SHORT**：`m3 > 0`（3 日拐头向上）

> 不设止盈止损，只看主力拐头。

### 动量分位分 `main_score`（操作建议排序依据）

- `|m3|` 与品种自身过去 30 个交易日（不含 t）的 `|m3|` 序列比较
- `main_score = hist.le(current).sum() / 30`
- 历史不足 30 日置 NaN；NaN 品种排在候选最后，但仍可被选中
- 排序键：`(isnan(main_score), -main_score, variety_name 字典序)`

---

## 三、池子 A 与组合约束

**池子 A（12 个品种）**在 `settings.py::TARGET_POOL` 中定义，`create_tables.py` 首次运行时同步写入 `trading_pool` 表，之后可通过数据库直接调整 `is_active`，代码层无需改动。

| 板块 | 品种 |
|------|------|
| 有色金属 | 沪铜、沪铝、沪锌 |
| 贵金属 | 沪金 |
| 黑色系 | 铁矿石、焦煤 |
| 化工能化 | PTA、甲醇、橡胶 |
| 油脂油料 | 豆粕、棕榈油 |
| 农产品 | 玉米 |

**组合约束**（`operations.py::generate_operations`，严格按顺序）：

1. 只保留 `A_OPEN_LONG` / `A_OPEN_SHORT` 信号
2. 品种必须在 `trading_pool` 且 `is_active = 1`
3. 跳过当日已持仓品种
4. 跳过 `closed_today`（当日刚平仓的品种，防止当日反手）
5. 已满槽（`entry_capacity = 0`）→ 所有剩余信号标 `capacity_full` 落选
6. 当前持仓占用的板块 → `sector_conflict` 落选
7. 剩余候选按排序键排序，依次选入；同一板块第二个候选再次 `sector_conflict` 落选

落选和选中记录统一写入 `trading_operations`，通过 `is_selected` 和 `reject_reason` 区分，对前端完全透明。

---

## 四、模块结构与文件职责

```
trading/strategies/
├── README.md            # 本文件
├── cleanup_plan.md      # 老 assistant 模块（后端路由、前端视图、菜单）清理步骤
├── settings.py          # 常量：资金、杠杆、槽位、窗口、池子 A
├── db.py                # MySQL 连接（从 .env / env.production 加载）
├── data_loader.py       # fut_strength + fut_daily_close + fut_variety 拉取、数据完整性校验
├── signals.py           # A 通道 4 种信号 + main_score 计算，写 trading_signals
├── operations.py        # 池子 A 过滤 + 组合约束，写 trading_operations
├── account.py           # 自动化账户：平仓 → 开仓 → 资金曲线，写 trading_positions / trading_account_daily
├── create_tables.py     # 删除旧 assistant_* 表、建 trading_* 表、初始化池子和首条资金曲线
└── daily_run.py         # 每日入口，按固定顺序串联上述步骤
```

### 关键常量（`settings.py`）

```python
INITIAL_CAPITAL = 30000.0
LEVERAGE = 10.0
MAX_SLOTS = 3
SIZE_PCT = 1 / 3
BACKGROUND_WINDOW = 4
TRIGGER_WINDOW = 3
TURN_WINDOW = 3
MOMENTUM_LOOKBACK = 30
```

### 账户执行细节（`account.py`）

每日执行顺序固定：**先平仓 → 再开仓 → 更新资金曲线**。

- 平仓：从 `trading_signals` 读当日 `A_CLOSE_LONG / A_CLOSE_SHORT`，对 `status='open'` 且方向匹配的持仓以当日收盘价平仓，`pnl_pct` 存无杠杆收益率
  - 多头：`(close - open) / open`
  - 空头：`(open - close) / open`
- 开仓：读 `trading_operations` 中 `is_selected = 1` 的记录，以当日收盘价开仓，关联 `operation_id` 便于回溯
- 资金曲线：
  - `daily_pnl = Σ prev_equity × size_pct × daily_ret × LEVERAGE`
  - `position_val = Σ prev_equity × size_pct × (1 + float_ret × LEVERAGE)`
  - `equity = cash + position_val`

---

## 五、数据表

所有表名以 `trading_` 前缀，通过 `create_tables.py` 一次性建表。旧 `assistant_*` 四张表在同一脚本中先被 DROP。

| 表名 | 作用 | 写入方 |
|------|------|--------|
| `trading_pool` | 池子 A 品种配置（板块、is_active） | `create_tables.py` 初始化，之后手工维护 |
| `trading_signals` | 全品种每日 A 通道信号 + main_score | `signals.py` |
| `trading_operations` | 池子 A 操作建议，含 `is_selected` + `reject_reason` | `operations.py` |
| `trading_positions` | 自动化账户持仓（最多 3 槽），`operation_id` 可回溯建议 | `account.py` |
| `trading_account_daily` | 每日资金曲线（equity / cash / position_val / daily_pnl） | `account.py` |

上游依赖表（只读）：`fut_variety`、`fut_strength`、`fut_daily_close`。这些由 `database/fut_pulse` 负责维护。

---

## 六、运行方式

### 配置

`.env` 从项目根目录加载（优先 `.env`，其次 `env.production`），必填：

```
DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
```

### 首次初始化

```bash
# 项目根目录执行（将 workstation/ 加入 PYTHONPATH）
python -m trading.strategies.create_tables
```

该脚本会：

1. DROP 掉 4 张旧 `assistant_*` 表
2. 建立 5 张 `trading_*` 表
3. 从 `fut_variety` 映射品种 id，将 `TARGET_POOL` 写入 `trading_pool`
4. 插入首条 `trading_account_daily` 记录：`equity = cash = INITIAL_CAPITAL`，作为资金曲线起点

### 每日运行

```bash
# 当日
python -m trading.strategies.daily_run

# 指定日期（回放/补录）
python -m trading.strategies.daily_run 2026-04-25
```

流程：

1. `check_data_completeness`：池子 A 品种当日 `fut_strength` 必须齐全，否则中止
2. `run_signals_for_all`：对全部 `fut_variety` 计算信号 → `trading_signals`
3. `generate_operations`：过滤 + 组合约束 → `trading_operations`
4. `execute_close_signals`：按平仓信号平仓 → `trading_positions`（`closed_today` 集合防反手）
5. `execute_open_operations`：按选中建议开仓 → `trading_positions`
6. `update_account_daily` → `trading_account_daily`

> 手动触发，不使用 crontab —— 上游 `fut_strength` 数据需要人工确认采集完成后再跑。

---

## 七、对外集成点

本模块**不直接对外**，所有对外读取由后端 HTTP 接口完成：

- 后端：`automysqlback/routes/trading_routes.py`（蓝图 `trading_bp`，已在 `automysqlback/app.py` 注册），提供 `/api/trading/*` 下 10 个接口：
  - `signals` / `operations` / `positions` / `positions/history` / `account/curve` / `account/summary` / `pool` / `market-context` / `variety-list` / `variety-kline`
- 前端：`workfront/src/views/trading/`（Tab：信号面板 / 操作建议 / 持仓盈亏 / 资金曲线 / K线），路由 `/trading`
- Nginx：请求经 `/api-a/` 前缀反向代理到后端（见仓库根 `CLAUDE.md`）

---

## 八、遗留待办

- `cleanup_plan.md`：老 `/assistant` 后端路由、前端视图、菜单与路由项的删除步骤，**在新系统稳定跑过完整一轮后**再执行，属不可逆操作
- `test/assistant/` 和 `test/plan2/` 目录保留作为实验参考，不清理
