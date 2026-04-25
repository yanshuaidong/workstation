# 期货数据系统后端 (AutoMySQLBack)

## 项目简介

期货数据查询与业务后端服务，提供系统设置、合约与历史数据查询、财联社新闻与 OSS、持仓、品种事件，以及辅助决策（信号、操作建议、账户曲线、市场上下文等）相关 HTTP API。默认通过 MySQL 读取数据；新闻截图等业务使用阿里云 OSS。

## 技术栈

- **后端**：Flask、Flask-CORS
- **依赖库（见 `requirements.txt`）**：PyMySQL、pandas、numpy、APScheduler、requests、oss2、python-dotenv、`ta`、cryptography
- **数据**：MySQL（连接信息由环境变量或本地配置提供）
- **对象存储**：阿里云 OSS（新闻截图、预签名上传等）
- **部署**：Docker（镜像内监听 7001；`Dockerfile` 含健康检查 `GET /api/settings`）

## 核心能力模块

- 系统设置（`/api/settings`）
- 期货合约列表与历史数据（`/api/contracts/*`、`/api/history/data`）
- 财联社新闻 CRUD、处理与跟踪（`/api/news/*`），以及 OSS 预签名（`/api/oss/*`）
- 期货持仓 CRUD 与统计（`/api/positions/*`）
- 品种事件 CRUD 与近期事件（`/api/events/*`）
- 辅助决策：信号、操作建议、持仓与历史持仓、资金曲线与账户摘要、市场上下文、品种列表与 K 线（`/api/assistant/*`）

## 快速启动

### 依赖与入口

```bash
pip install -r requirements.txt
python start.py
```

服务监听 `0.0.0.0:7001`（见 `start.py`）。

### macOS：同目录脚本

```bash
cd automysqlback
./mac.devrun.sh
```

脚本会创建或复用 `.venv`、按 `requirements.txt` 安装/更新依赖（通过时间戳判断）、再执行 `python start.py`。默认开发地址：`http://127.0.0.1:7001`。

### Windows：同目录脚本

```bat
cd automysqlback
win.devrun.bat
```

`win.devrun.bat` 用于 Windows 环境的一键本地启动：会自动创建或复用 `.venv`、按需安装/更新 `requirements.txt` 依赖，然后启动 `start.py`（默认地址：`http://127.0.0.1:7001`）。

### Docker

```bash
docker build -t automysqlback .
docker run -d -p 7001:7001 \
  -e DB_HOST=your_db_host \
  -e DB_USER=your_db_user \
  -e DB_PASSWORD=your_db_password \
  automysqlback
```

按需传入 `DB_*`、OSS 及 `ENVIRONMENT` 等变量（见下表）。

## 环境变量

| 变量名 | 说明 |
|--------|------|
| `DB_HOST` | 数据库主机 |
| `DB_PORT` | 端口，默认 `3306` |
| `DB_USER` | 用户名 |
| `DB_PASSWORD` | 密码 |
| `DB_NAME` | 库名，默认 `futures` |
| `ENVIRONMENT` | 运行环境标识，默认 `development`；非开发且缺少关键 `DB_*` 时进程会退出 |
| `OSS_ENDPOINT` | OSS Endpoint |
| `OSS_BUCKET` | Bucket 名 |
| `OSS_ACCESS_KEY_ID` | 访问 Key |
| `OSS_ACCESS_KEY_SECRET` | 访问 Secret |
| `OSS_BASE_URL` | 可选，公网访问基 URL |

启动时会校验 `DB_HOST`、`DB_USER`、`DB_PASSWORD`、`DB_NAME` 是否设置；OSS 相关在调用 OSS/新闻截图链路时使用（见 `app.py` 中 `OSS_CONFIG`）。

本地配置：存在时依次加载当前目录下的 `.env`、`env.production`（见 `app.py` 中 `load_env_config`）。

---

## API 说明

**公共约定**

- 默认端口：**7001**
- 统一响应：`{ "code": 0 \| 1, "message": string, "data": object }`（成功为 `0`，失败为 `1`）

---

### 一、系统设置（2）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/settings` | 读取系统配置 |
| POST | `/api/settings` | 更新系统配置并刷新定时任务相关设置 |

---

### 二、合约与历史数据（2）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/contracts/list` | 合约列表 |
| GET | `/api/history/data` | 历史数据（查询参数含 `symbol` 等） |

---

### 三、新闻（11）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/news/stats` | 新闻统计 |
| GET | `/api/news/list` | 分页与筛选列表 |
| POST | `/api/news/create` | 创建 |
| GET | `/api/news/detail/<news_id>` | 详情 |
| PUT | `/api/news/update/<news_id>` | 更新 |
| DELETE | `/api/news/delete/<news_id>` | 删除（含关联 OSS/跟踪等逻辑，见实现） |
| GET | `/api/news/process/unreviewed` | 待校验新闻 |
| POST | `/api/news/process/review` | 标记已校验 |
| GET | `/api/news/process/tracking-list` | 跟踪列表 |
| POST | `/api/news/process/update-tracking` | 更新跟踪节点 |
| POST | `/api/news/process/init-tracking` | 初始化跟踪记录 |

### 四、OSS（2）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/oss/upload-url` | 预签名上传 URL |
| POST | `/api/oss/access-url` | 预签名访问 URL |

---

### 五、持仓（7）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/positions/list` | 列表 |
| POST | `/api/positions/create` | 创建 |
| GET | `/api/positions/detail/<position_id>` | 详情 |
| PUT | `/api/positions/update/<position_id>` | 更新 |
| DELETE | `/api/positions/delete/<position_id>` | 删除 |
| GET | `/api/positions/stats` | 统计 |
| POST | `/api/positions/toggle-status/<position_id>` | 切换有仓/空仓 |

---

### 六、品种事件（6）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/events/list` | 列表（需 `symbol` 等，见 `events_routes.py`） |
| POST | `/api/events/create` | 创建 |
| GET | `/api/events/detail/<event_id>` | 详情 |
| PUT | `/api/events/update/<event_id>` | 更新 |
| DELETE | `/api/events/delete/<event_id>` | 删除 |
| GET | `/api/events/recent` | 近期事件 |

数据表：`futures_events`（见 `events_routes.py`）。

---

### 七、辅助决策 Assistant（9）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/assistant/signals` | 信号列表；查询参数如 `date`、`variety_id`、`variety_name`、`indicator`、`direction` |
| GET | `/api/assistant/operations` | 操作建议；查询参数如 `date`、`account_type`（默认 `mechanical`）、`variety_id`、`strategy`、`direction` |
| GET | `/api/assistant/positions` | 当前开放持仓；可选 `account_type` |
| GET | `/api/assistant/positions/history` | 已平仓历史；可选 `account_type`、`limit`（1–500，默认 100） |
| GET | `/api/assistant/account/curve` | 资金曲线；可选 `start_date`、`end_date`、`account_type` |
| GET | `/api/assistant/account/summary` | 账户摘要；可选 `date` |
| GET | `/api/assistant/market-context` | 市场上下文；必填 `variety_id`；可选 `days`（3–60，默认 10）、`end_date` |
| GET | `/api/assistant/variety-list` | 含 `contracts_symbol` 的品种列表 |
| GET | `/api/assistant/variety-kline` | 品种 K 线与主力/散户指标；必填 `variety_id`；可选 `start_date`、`end_date` |

相关数据表包括但不限于：`assistant_signals`、`assistant_operations`、`assistant_positions`、`assistant_account_daily`、`fut_variety`、`fut_strength`、`fut_daily_close`，以及按品种拼表名的 `hist_{contracts_symbol}`（见 `assistant_routes.py`）。

---

## 接口数量汇总

| 模块 | 数量 |
|------|------|
| 系统设置 | 2 |
| 合约与历史 | 2 |
| 新闻 | 11 |
| OSS | 2 |
| 持仓 | 7 |
| 事件 | 6 |
| 辅助决策 | 9 |
| **合计** | **39** |

---

## 数据库表（与当前代码的对应关系）

**应用启动时 `init_database()` 会创建的表**（见 `app.py`）

| 表名 | 说明 |
|------|------|
| `contracts_main` | 主连合约 |
| `system_config` | 系统配置 |
| `contract_list_update_log` | 合约列表更新记录 |
| `history_update_log` | 主连历史更新日志 |
| `recommendation_log` | 每日多空推荐记录 |
| `news_red_telegraph` | 财联社新闻主表 |
| `news_process_tracking` | 新闻处理跟踪 |
| `futures_positions` | 期货持仓（业务持仓模块） |

**不在上述初始化中创建、由接口查询使用的表（示例）**

| 表名 | 说明 |
|------|------|
| `futures_events` | 品种事件 |
| `assistant_*`、`fut_*` | 辅助决策与行情/品种维表 |
| `hist_{symbol}` | 各品种历史 K 线（表名随品种动态） |

---

## 目录结构

```
automysqlback/
├── app.py                 # Flask 应用、系统设置 API、数据库初始化、调度器
├── start.py               # 启动入口
├── mac.devrun.sh          # macOS 本地一键启动脚本
├── win.devrun.bat         # Windows 本地一键启动脚本
├── requirements.txt
├── Dockerfile
├── routes/
│   ├── __init__.py
│   ├── contracts_routes.py
│   ├── news_routes.py
│   ├── positions_routes.py
│   ├── events_routes.py
│   └── assistant_routes.py
└── README.md
```

---

## 行为与运维说明（当前实现）

- 定时任务是否启用及参数由 `system_config` 决定（默认自动更新关闭，见 `init_database` 插入的默认值）。
- OSS 对象路径组织方式见 `news_routes` 与 OSS 相关逻辑（如按日期分目录）。
- 新闻处理包含标签校验与多时点跟踪（如 3/7/14/28 天），与 `news_process_tracking` 字段一致。
