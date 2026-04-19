# 辅助决策（Assistant）

本目录 `test/assistant/` 是个人期货数据工作站中与「辅助决策」相关的批处理与计算代码所在位置。同一条业务链还包括 `automysqlback/` 内的 REST 接口与 `workfront/` 内的「辅助决策」前端页面。

---

## 1. 本模块做什么

- 从 MySQL 表 `fut_strength`、`fut_daily_close` 读取行情与资金强度数据，在本地 Python 流程中计算指标与策略输出，结果写回 MySQL 中 `assistant_*` 表。
- 机械类账户（`account_type='mechanical'`）由批处理中的规则引擎按日更新持仓与净值；LLM 相关记录（`account_type='llm'`）通过命令行工具写入。
- 批处理会生成供本地 AI 工具阅读的 Markdown 提示词文件，并把每次通过 CLI 写入的决策追加到 JSON Lines 归档。
- 用户通过前端「辅助决策」菜单查看信号、操作建议、持仓、资金曲线，以及带品种映射的 K 线与主力/散户指数图。

---

## 2. 仓库内位置

| 部分 | 路径 |
|------|------|
| 每日批处理与 CLI | `test/assistant/src/` |
| LLM 提示词与调用归档（运行后生成） | `test/assistant/logs/llm/` |
| Flask 路由（蓝图挂载在 `/api` 下） | `automysqlback/routes/assistant_routes.py` |
| 前端布局与子页 | `workfront/src/views/assistant/` |
| 前端请求的接口前缀 | `workfront/src/api.js` 中 `BASE_URL_API_A`（默认 `/api-a`，由开发代理转发至后端） |

---

## 3. 依赖的数据库表（输入）

- `fut_strength`：按品种、交易日的资金强度字段（含主力、散户等）。
- `fut_daily_close`：按品种、交易日的收盘价；与 `fut_strength` 按 `variety_id` + `trade_date` 对齐使用。

上述数据由 `database/fut_pulse/` 等流程写入；本模块取「最新交易日」等逻辑依赖 `fut_daily_close` 中存在目标日期数据。

K 线类接口依赖 `fut_variety.contracts_symbol` 与 `contracts_main` / `hist_{symbol}` 体系；仅当某品种在 `fut_variety` 中配置了非空的 `contracts_symbol` 时，该品种会出现在「品种列表」接口返回中。

---

## 4. 本模块专用表（输出）

建表脚本：`test/assistant/src/create_tables.py`（一次性执行，在项目根目录读取 `.env` / `env.production`）。创建的表包括：

- `assistant_signals`：按日、品种、指标记录信号。
- `assistant_operations`：策略触发的操作建议；`account_type` 区分 `mechanical` / `llm`。
- `assistant_positions`：模拟持仓，含开平仓价格、状态、`account_type`。
- `assistant_account_daily`：按日账户净值等，按 `(record_date, account_type)` 唯一。

---

## 5. 批处理与命令行

- **每日流程**：`test/assistant/src/daily_run.py`  
  - 拉取市场数据，生成信号写入 `assistant_signals`，生成操作建议写入 `assistant_operations`。  
  - 可选 `--execute-mechanical` 执行机械账户当日处理；可选 `--force-replay` 强制重放当日机械执行。  
  - 支持 `--signal-date` 单日或 `--start-date` / `--end-date` 区间回放。  
  - 运行后生成 `test/assistant/logs/llm/YYYY-MM-DD-prompt.md`（LLM 提示词）。
- **LLM 决策写入**：`test/assistant/src/write_llm_decision.py`，通过 `open_long` / `open_short` / `close` / `hold` 等参数把一条决策写入数据库，并追加 `test/assistant/logs/llm/YYYY-MM-DD-calls.jsonl`。

源码中还包含 `data_loader.py`、`signals.py`、`strategies.py`、`paper_account.py`、`decision_mechanical.py`、`decision_llm.py`、`assistant_db.py`、`assistant_settings.py` 等，由 `daily_run.py` 与决策流程引用。

---

## 6. HTTP 接口（Flask）

蓝图 `assistant_bp` 在 `automysqlback/app.py` 中以 `url_prefix='/api'` 注册。对外路径形如：

- `GET /api/assistant/signals`
- `GET /api/assistant/operations`
- `GET /api/assistant/positions`
- `GET /api/assistant/positions/history`
- `GET /api/assistant/account/curve`
- `GET /api/assistant/account/summary`
- `GET /api/assistant/market-context`（查询参数含 `variety_id`；`days` 默认 10，范围 3～60，返回收盘价与主力、散户序列）
- `GET /api/assistant/variety-list`
- `GET /api/assistant/variety-kline`

---

## 7. 前端「辅助决策」

- 路由前缀：`/assistant`（见 `workfront/src/router/index.js`），默认重定向到 `/assistant/signals`。
- 子页标签：信号面板、操作建议、持仓盈亏、资金曲线、K 线展示（见 `workfront/src/views/assistant/index.vue`）。
- 布局页顶部展示机械账户与 LLM 账户的摘要（净值日期、持仓数、当日盈亏等），数据来自 `GET .../assistant/account/summary`。
- 「信号面板」行展开后的图表组件使用 `GET .../assistant/market-context` 的数据：默认展示若干交易日的**收盘价折线**与主力、散户曲线，不是完整 OHLC K 线。
- 「K 线展示」子页使用 `variety-list` 与 `variety-kline`，展示期货 K 线及主力、散户指数（实现文件为 `KlineView.vue`）。

---

## 8. 与仓库内其他文档的关系

- `test/assistant/使用手册.md`：面向操作者的步骤说明（命令与接口列表）。
- `test/assistant/辅助方案设计.md`、`test/assistant/添加一个展示的功能.md`：历史设计与方案记录。
- `test/assistant/关于数据收集的补充.md`：说明 `fut_pulse` 与 `fut_daily_close` 等行为，与 assistant 读取的输入表相关。

本 README 不重复论证设计取舍，仅描述当前仓库中已落地的目录、表、脚本、接口与页面入口。
