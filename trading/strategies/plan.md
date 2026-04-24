# trading/strategies 迁移计划

> 本次迁移是一次策略升级，将 `test/assistant/` 的实验性代码迁移到 `trading/strategies/` 生产级独立模块。
> 核心变化：信号指标体系全面替换为 plan2 A通道逻辑；去掉 LLM 账户，只保留自动化账户。

## 权威参考（实现时以这两个文件为准，防止理解偏差）

| 文件 | 说明 |
|------|------|
| `test/plan2/核心逻辑.md` | 策略逻辑的文字规范，所有条件定义的权威来源 |
| `test/plan2/scripts/backtest_portfolio_strict7_tp3.py` | 实验期完整策略代码，`compute_signals_strict7_tp3` 和 `simulate_portfolio` 是信号计算和组合模拟的精确实现参考 |

**实现原则**：遇到计划描述模糊时，直接对照上述代码；不得凭理解推断，以代码行为准。

## 设计理念：三层信息漏斗

三个面板是层层递进的决策链路，每一层都可解释，不是黑箱：

```
【信号面板】全市场观察
  对全部品种计算 A通道信号，提供全局视野。
  即使池子外的品种我不做，也能看到市场机会和风险。
        ↓ 过滤：只看池子A的品种
【操作建议】决策透明
  池子A所有触发信号的品种全部列出，包括落选的。
  每条记录说明：为什么入选 / 为什么落选（槽位满、板块冲突、分位分靠后）。
  决策过程完全可审计，不是只看结果。
        ↓ 过滤：实际执行的
【持仓盈亏】执行记录
  从操作建议中实际执行的操作记录，展示真实持仓和盈亏。
  可回溯每笔操作来自哪条操作建议。
```

---

## 一、背景与核心变化对比

| 维度 | 老系统（test/assistant） | 新系统（trading/strategies） |
|------|--------------------------|------------------------------|
| 信号指标 | 7个独立指标（MF_Edge3/MF_Accel等） | **plan2 A通道信号**（开多/开空/平多/平空） |
| 信号范围 | 全部品种 | **全部品种**（全品种都计算A通道信号） |
| 操作建议 | 全品种按 Composite_Score 筛选 | 仅池子A（12个品种）+ 组合约束过滤 |
| 账户类型 | mechanical + llm 双账户 | 只有"自动化账户"，去掉 LLM |
| 开仓逻辑 | Composite_Score 阈值触发 | plan2 A通道：背景4日 + 触发3日 + 主散反向确认 |
| 平仓逻辑 | 持有天数超时（MAX_HOLD_DAYS=5） | 只看主力3日拐头，不设止盈止损 |
| 池子A配置 | 无 | 存数据库，可动态配置 |
| 历史数据 | 立即删除旧 assistant_* 表 | 新建 trading_* 表，全新开始 |
| 前端路由 | /assistant | /trading |

---

## 二、新信号体系：plan2 A通道

### 信号类型（共4种，对全部品种计算）

| 信号类型 | 含义 |
|----------|------|
| `A_OPEN_LONG` | A通道开多触发 |
| `A_OPEN_SHORT` | A通道开空触发 |
| `A_CLOSE_LONG` | A通道平多触发（主力3日拐头向下） |
| `A_CLOSE_SHORT` | A通道平空触发（主力3日拐头向上） |

### A-开多触发条件
背景期（闭区间 `[t-6, t-3]`，4个数据点，记为 bg1=mf[t-6], bg2=mf[t-5], bg3=mf[t-4], bg4=mf[t-3]）：
1. bg1, bg2, bg3, bg4 全部 < 0
2. `bg4 - bg1 < 0`（背景期整体仍在下行）

触发期（`[t-2, t]`，3个数据点）：
3. `main_force` 严格连续上升：`mf[t-2] < mf[t-1] < mf[t]`（代码实现：`main_diff[t-1] > 0 & main_diff[t] > 0`）
4. `retail` 严格连续下降：`rt[t-2] > rt[t-1] > rt[t]`（代码实现：`retail_diff[t-1] < 0 & retail_diff[t] < 0`）

> 共需最近连续7个交易日数据（代码中 `cont7` 校验连续性）。

### A-开空触发条件（与开多完全对称）
背景期（bg1..bg4 同上）：
1. bg1, bg2, bg3, bg4 全部 > 0
2. `bg4 - bg1 > 0`（背景期整体仍在上行）

触发期：
3. `main_force` 严格连续下降：`main_diff[t-1] < 0 & main_diff[t] < 0`
4. `retail` 严格连续上升：`retail_diff[t-1] > 0 & retail_diff[t] > 0`

### A-平多触发条件
- 最近3日连续（代码 `cont3`）且 `main_force[t] - main_force[t-2] < 0`（3日拐头向下）

### A-平空触发条件
- 最近3日连续（代码 `cont3`）且 `main_force[t] - main_force[t-2] > 0`（3日拐头向上）

### 动量分位分（用于操作建议排序）
- `m3(t) = main_force[t] - main_force[t-2]`
- 取该品种过去30个交易日（**不含 t**）的 `|m3|` 历史序列
- `main_score(v, t) = rank(|m3(v, t)|) / 30`（即 `hist.le(current).sum() / 30`）
- 历史不足30日时置 NaN；**NaN 品种排在最后，但仍可被选中**（若有剩余槽位且无其他候选）
- 排序键（代码实现）：`(isnan, -score, variety_name_字典序)`

---

## 三、三个面板的数据流

```
全部品种（fut_variety）
    │
    ▼
【 signals.py 】对每个品种每日计算 A通道信号
    │
    ├─── 信号面板（全品种）
    │    展示当日全部品种的 A_OPEN / A_CLOSE 信号提醒
    │
    ├─── 操作建议（池子A）
    │    过滤条件：品种在 trading_pool（is_active=1）
    │             + 组合约束（最多3槽、板块不重叠、main_score排序）
    │
    └─── 持仓盈亏
         自动化账户实际执行的结果
         平仓信号触发 → 程序自动平仓
```

---

## 四、池子A品种（12个，来自 plan2）

| 板块 | 品种 |
|------|------|
| 有色金属 | 沪铜、沪铝、沪锌 |
| 贵金属 | 沪金 |
| 黑色系 | 铁矿石、焦煤 |
| 化工能化 | PTA、甲醇、橡胶 |
| 油脂油料 | 豆粕、棕榈油 |
| 农产品 | 玉米 |

入池原则：`main~close` 同向率在 S=3 下二项检验 p<0.05，且 `main~retail` 反向率 >= 70%，板块均衡抽样。

---

## 五、新表结构设计

### 删除旧表（立即执行）
```sql
DROP TABLE IF EXISTS assistant_signals;
DROP TABLE IF EXISTS assistant_operations;
DROP TABLE IF EXISTS assistant_positions;
DROP TABLE IF EXISTS assistant_account_daily;
```

### 新建表

#### 5.1 `trading_pool`（池子A品种配置）
```sql
CREATE TABLE trading_pool (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    variety_id   INT NOT NULL,
    variety_name VARCHAR(20),
    sector       VARCHAR(20) NOT NULL COMMENT '板块，用于组合约束',
    is_active    TINYINT(1) DEFAULT 1 COMMENT '是否在池子A中',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_variety (variety_id)
) COMMENT='池子A品种配置，可动态调整';
```

#### 5.2 `trading_signals`（每日A通道信号，全品种）
```sql
CREATE TABLE trading_signals (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    signal_date  DATE NOT NULL,
    variety_id   INT NOT NULL,
    variety_name VARCHAR(20),
    signal_type  VARCHAR(20) NOT NULL COMMENT 'A_OPEN_LONG/A_OPEN_SHORT/A_CLOSE_LONG/A_CLOSE_SHORT',
    main_score   FLOAT COMMENT '动量分位分（仅 OPEN 信号有值）',
    extra_json   JSON COMMENT '计算明细（main_force序列、retail序列等）',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_date_variety_signal (signal_date, variety_id, signal_type),
    KEY idx_date_variety (signal_date, variety_id)
) COMMENT='每日A通道信号记录（全品种）';
```

#### 5.3 `trading_operations`（操作建议，仅池子A品种）
```sql
CREATE TABLE trading_operations (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    signal_date   DATE NOT NULL,
    variety_id    INT NOT NULL,
    variety_name  VARCHAR(20),
    sector        VARCHAR(20) COMMENT '板块',
    signal_type   VARCHAR(20) NOT NULL COMMENT 'A_OPEN_LONG/A_OPEN_SHORT',
    main_score    FLOAT COMMENT '动量分位分，决定优先级',
    is_selected   TINYINT(1) DEFAULT 0 COMMENT '是否通过组合约束被选中执行',
    reject_reason VARCHAR(30) COMMENT 'capacity_full/sector_conflict/score_rank/null（已选中）',
    extra_json    JSON,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_date_variety_signal (signal_date, variety_id, signal_type),
    KEY idx_date (signal_date)
) COMMENT='操作建议（仅池子A品种，含组合约束结果）';
```

#### 5.4 `trading_positions`（持仓，自动化账户）
```sql
CREATE TABLE trading_positions (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    operation_id INT COMMENT '关联 trading_operations.id，可追溯来源建议',
    variety_id   INT NOT NULL,
    variety_name VARCHAR(20),
    sector       VARCHAR(20) COMMENT '板块',
    direction    VARCHAR(10) NOT NULL COMMENT 'LONG/SHORT',
    open_date    DATE NOT NULL,
    open_price   FLOAT NOT NULL,
    close_date   DATE,
    close_price  FLOAT,
    size_pct     FLOAT DEFAULT 0.3333 COMMENT '每槽1/3权重（无杠杆）',
    status       VARCHAR(10) DEFAULT 'open' COMMENT 'open/closed',
    pnl_pct      FLOAT COMMENT '无杠杆收益率：多头=(close-open)/open，空头=(open-close)/open',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_status (status)
) COMMENT='自动化账户持仓（单账户，最多3槽）';
```

#### 5.5 `trading_account_daily`（资金曲线，自动化账户）
```sql
CREATE TABLE trading_account_daily (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    record_date  DATE NOT NULL,
    equity       FLOAT NOT NULL,
    cash         FLOAT NOT NULL,
    position_val FLOAT DEFAULT 0,
    daily_pnl    FLOAT DEFAULT 0,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_date (record_date)
) COMMENT='自动化账户每日净值曲线（单账户）';
```

---

## 六、trading/strategies/ 模块结构

```
trading/strategies/
├── plan.md              # 本文件（迁移计划）
├── settings.py          # 常量：账户资金、杠杆、槽位数、各窗口长度
├── db.py                # MySQL 连接（从 .env 读取，不依赖 test/ 任何代码）
├── data_loader.py       # 从线上 MySQL 拉取 fut_strength + fut_daily_close + fut_variety
├── signals.py           # A通道信号计算（全品种，4种信号类型 + main_score）
├── operations.py        # 操作建议生成：池子A过滤 + 组合约束 + main_score排序
├── account.py           # 自动化账户：开平仓执行、资金曲线更新
├── create_tables.py     # 删旧表 + 建新表脚本
└── daily_run.py         # 每日入口
```

### 6.1 settings.py 关键常量
```python
INITIAL_CAPITAL = 30000.0    # 3万初始资金
LEVERAGE = 10.0
MAX_SLOTS = 3                # 最多同时持仓3个品种
SIZE_PCT = 1 / 3             # 每槽1/3资金
BACKGROUND_WINDOW = 4        # A通道背景窗口
TRIGGER_WINDOW = 3           # A通道触发窗口
TURN_WINDOW = 3              # 拐头离场窗口
MOMENTUM_LOOKBACK = 30       # 动量分位回看天数
```

### 6.2 signals.py 核心逻辑
```
对每个品种，每个交易日 t：
  取最近 max(7, MOMENTUM_LOOKBACK+2) 天数据

  计算 A-开多/开空：
    背景期 [t-6, t-3]：main_force 全部同符号 + 背景期整体方向确认
    触发期 [t-2, t]：  main_force 严格3连升/降 + retail 严格反向3连

  计算 A-平多/平空：
    [t-2, t]：main_force[t] - main_force[t-2] 拐头方向判断

  计算 main_score：
    m3 = main_force[t] - main_force[t-2]
    取过去30个交易日的 |m3| 序列求分位
```

### 6.3 operations.py 组合约束逻辑
```
输入：当日全品种信号（trading_signals）+ trading_pool + 当前持仓

过滤步骤（严格按此顺序，对应实验代码 simulate_portfolio）：
  1. 只保留 signal_type 为 A_OPEN_LONG 或 A_OPEN_SHORT 的信号
  2. 只保留品种在 trading_pool（is_active=1）的信号
  3. 跳过当日已持仓的品种（variety in holdings）
  4. 跳过当日已平仓的品种（variety in closed_today，防止当日反手）
  5. 当前持仓数 = 3（entry_capacity=0）→ 所有剩余信号标记落选（capacity_reject）
  6. 对剩余候选按板块检查（start_sectors，即日内平仓前的板块集）：
     已被占用的板块 → 板块冲突落选（sector_reject）
  7. 按排序键 (isnan(main_score), -main_score, variety_name字典序) 排序
  8. 依次选入，选入时同步更新 used_sectors，同板块第二个信号也落选
  9. 写入 trading_operations，is_selected=1 为选中，0 为落选（附 reject_reason）
```

### 6.4 account.py 执行逻辑
```
每日执行顺序：
  1. 先检查平仓信号
     → 从 trading_signals 读当日 A_CLOSE_LONG / A_CLOSE_SHORT 信号
     → 对当前持仓中匹配的品种执行平仓（当日收盘价）
     → 平仓品种加入 closed_today 集合，当日不得再开仓

  2. 再执行开仓
     → 读 trading_operations 中当日 is_selected=1 的记录
     → 以信号当日收盘价开仓

  3. 更新 trading_account_daily（资金曲线）
     → equity = cash + 所有持仓浮动市值（持仓方向 × 当日收益率）
     → daily_pnl = 各持仓 (当日收盘价 - 昨日收盘价) × 方向 × size_pct × LEVERAGE 之和

pnl_pct 计算（平仓时写入 trading_positions）：
  多头：pnl_pct = (close_price - open_price) / open_price
  空头：pnl_pct = (open_price - close_price) / open_price
  注意：pnl_pct 存储的是无杠杆收益率，杠杆在 account_daily 资金曲线中单独放大
  （实验代码 trade_return：side * (exit - entry) / entry，与此一致）
```

---

## 七、后端 API 迁移

在 `automysqlback/routes/` 新增 `trading_routes.py`，注册 `trading_bp`。
同时在 `app.py` 中**移除** `assistant_bp`，**注册** `trading_bp`。

| 新接口 | 说明 |
|--------|------|
| GET /trading/signals | 全品种A通道信号，按日期查询 |
| GET /trading/operations | 池子A操作建议（含是否被选中） |
| GET /trading/positions | 当前持仓（自动化账户） |
| GET /trading/positions/history | 历史持仓 |
| GET /trading/account/curve | 资金曲线 |
| GET /trading/account/summary | 账户摘要（权益、当日盈亏、持仓数） |
| GET /trading/pool | 池子A品种列表 |
| GET /trading/market-context | 品种主力/散户/收盘价序列（不变） |
| GET /trading/variety-list | 品种列表（不变） |
| GET /trading/variety-kline | K线+主力散户（不变） |

---

## 八、前端迁移

新建 `workfront/src/views/trading/` 目录：

```
workfront/src/views/trading/
├── index.vue            # Tab 布局（信号面板 / 操作建议 / 持仓盈亏 / K线）
├── SignalsView.vue      # 全品种A通道信号提醒（展示4种信号类型）
├── OperationsView.vue   # 池子A操作建议（展示是否被选中、main_score排序）
├── PositionsView.vue    # 持仓盈亏（当前持仓 + 历史持仓）
├── CurveView.vue        # 资金曲线（单账户）
└── KlineView.vue        # K线展示（保持不变）
```

路由变更：删除 `/assistant`，新增 `/trading`。

---

## 九、执行顺序

```
Step 1  建新表（运行 create_tables.py）
        → DROP assistant_* 四张旧表
        → CREATE trading_pool / trading_signals / trading_operations
                 trading_positions / trading_account_daily

Step 2  初始化池子A数据
        → 在 trading_pool 中录入12个品种（对应 fut_variety 的 variety_id）

Step 3  实现 Python 模块
        db.py → settings.py → data_loader.py
        → signals.py（A通道4种信号 + main_score）
        → operations.py（池子A过滤 + 组合约束）
        → account.py（开平仓 + 资金曲线）
        → daily_run.py

Step 4  后端 API
        新增 trading_routes.py
        app.py：替换 assistant_bp → trading_bp

Step 5  前端页面
        新建 trading/ 下5个组件
        路由从 /assistant 切换到 /trading

Step 6  验证
        运行 daily_run.py 验证信号/操作建议/持仓数据正常
        检查前端三个面板展示正确
```

---

## 十、已确认事项

1. **初始资金**：`INITIAL_CAPITAL = 30000`（3万）
2. **daily_run.py 触发方式**：手动执行（因依赖数据的手动采集，不使用 crontab）
3. **首次回放**：不需要，从当前日期起全新开始记录资金曲线
4. **资金曲线初始化**：`create_tables.py` 执行后需插入第一条 `trading_account_daily` 记录：`equity=30000, cash=30000, position_val=0, daily_pnl=0`
5. **daily_run.py 数据完整性校验**：运行前检查当日 `fut_strength` 记录数与预期品种数是否一致，若不足则中止并报错，不写入任何信号
