# AutoMySQLBack

期货数据系统后端服务，基于 Flask 提供 REST API，负责系统设置、合约与历史行情、财联社新闻、阿里云 OSS、持仓、品种事件和量化交易看板相关能力。

服务默认监听 `7001` 端口，统一以 `/api` 作为接口前缀，数据存储使用 MySQL，新闻截图等对象文件使用阿里云 OSS。

## 功能概览

- 系统设置读取与更新
- 主连合约列表查询
- 合约历史行情查询
- 财联社新闻 CRUD、校验流转、跟踪流转
- OSS 预签名上传与访问地址生成
- 期货持仓 CRUD、状态切换、统计
- 品种事件 CRUD 与近期事件聚合
- Trading 模块信号、操作建议、持仓、资金曲线、池子配置、市场上下文、K 线数据查询

## 技术栈

- Python 3.10
- Flask 2.3
- Flask-CORS
- PyMySQL
- APScheduler
- requests
- oss2
- python-dotenv
- pandas / numpy / ta

依赖定义见 [requirements.txt](D:/ysd/workstation/automysqlback/requirements.txt)。

## 项目结构

```text
automysqlback/
├── app.py
├── start.py
├── Dockerfile
├── requirements.txt
├── mac.devrun.sh
├── win.devrun.bat
├── logs/
├── routes/
│   ├── __init__.py
│   ├── contracts_routes.py
│   ├── news_routes.py
│   ├── positions_routes.py
│   ├── events_routes.py
│   └── trading_routes.py
├── tests/
│   └── test_assistant_signal_explanations.py
└── README.md
```

## 运行方式

### 本地启动

```bash
cd automysqlback
pip install -r requirements.txt
python start.py
```

启动后服务监听：

```text
http://127.0.0.1:7001
```

### macOS 启动脚本

```bash
cd automysqlback
./mac.devrun.sh
```

脚本会创建或复用 `.venv`，按 `requirements.txt` 安装依赖后启动服务。

### Windows 启动脚本

```bat
cd automysqlback
win.devrun.bat
```

脚本会创建或复用 `.venv`，按 `requirements.txt` 安装依赖后启动服务。

### Docker 启动

```bash
docker build -t automysqlback .
docker run -d -p 7001:7001 \
  -e DB_HOST=your_db_host \
  -e DB_USER=your_db_user \
  -e DB_PASSWORD=your_db_password \
  -e DB_NAME=futures \
  automysqlback
```

容器镜像定义见 [Dockerfile](D:/ysd/workstation/automysqlback/Dockerfile)，健康检查地址为 `GET /api/settings`。

## 环境变量

### 数据库

| 变量名 | 说明 |
| --- | --- |
| `DB_HOST` | MySQL 主机地址 |
| `DB_PORT` | MySQL 端口，默认 `3306` |
| `DB_USER` | MySQL 用户名 |
| `DB_PASSWORD` | MySQL 密码 |
| `DB_NAME` | 数据库名，默认 `futures` |
| `ENVIRONMENT` | 运行环境标识，默认 `development` |

### OSS

| 变量名 | 说明 |
| --- | --- |
| `OSS_ENDPOINT` | OSS Endpoint |
| `OSS_BUCKET` | Bucket 名称 |
| `OSS_ACCESS_KEY_ID` | Access Key ID |
| `OSS_ACCESS_KEY_SECRET` | Access Key Secret |
| `OSS_BASE_URL` | 公开访问基础地址 |

生产环境下应显式配置数据库连接参数。涉及新闻截图上传、预签名访问等能力时，需要完整配置 OSS 参数。

## 启动行为

### 配置加载

应用启动时按以下顺序查找环境文件：

1. `.env`
2. `env.production`

找到第一个存在的文件后即加载并停止继续查找。

### 数据库初始化

`start.py` 启动时会调用 `init_database()`，自动创建以下表：

- `contracts_main`
- `system_config`
- `contract_list_update_log`
- `history_update_log`
- `recommendation_log`
- `news_red_telegraph`
- `news_process_tracking`
- `futures_positions`

同时会初始化：

- `system_config` 默认配置记录
- `contract_list_update_log` 默认日志记录

### 定时任务

应用启动后会启动 `BackgroundScheduler`。当 `system_config.auto_update_enabled = 1` 时，系统会按照 `daily_update_time` 触发自动更新任务，并向以下地址发起请求：

```text
POST http://localhost:7002/api/history/update-all
```

请求体包含最近 30 天的日期范围。

### 日志目录

启动脚本会确保 [logs](D:/ysd/workstation/automysqlback/logs) 目录存在，用于本地运行时日志输出。

## 接口约定

- 基础前缀：`/api`
- 默认端口：`7001`
- 返回格式：

```json
{
  "code": 0,
  "message": "获取成功",
  "data": {}
}
```

约定说明：

- `code = 0` 表示成功
- `code = 1` 表示失败

## 接口清单

### 系统设置

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/settings` | 获取系统配置 |
| `POST` | `/api/settings` | 更新系统配置并重载定时任务 |

### 合约与历史行情

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/contracts/list` | 查询已激活主连合约列表 |
| `GET` | `/api/history/data` | 查询指定合约历史数据，参数：`symbol`、`start_date`、`end_date` |

### 新闻

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/news/stats` | 查询新闻统计信息 |
| `GET` | `/api/news/list` | 分页查询新闻列表，支持搜索与筛选 |
| `POST` | `/api/news/create` | 创建新闻，并同步创建跟踪记录 |
| `GET` | `/api/news/detail/<news_id>` | 查询新闻详情 |
| `PUT` | `/api/news/update/<news_id>` | 更新新闻 |
| `DELETE` | `/api/news/delete/<news_id>` | 删除新闻及其关联截图对象 |
| `GET` | `/api/news/process/unreviewed` | 获取最近 30 天待校验新闻 |
| `POST` | `/api/news/process/review` | 标记新闻为已校验 |
| `GET` | `/api/news/process/tracking-list` | 获取 3/7/14/28 天跟踪列表 |
| `POST` | `/api/news/process/update-tracking` | 更新跟踪节点完成状态 |
| `POST` | `/api/news/process/init-tracking` | 为未建档新闻补建跟踪记录 |

### OSS

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/oss/upload-url` | 生成预签名上传地址 |
| `POST` | `/api/oss/access-url` | 生成预签名访问地址 |

截图对象路径按日期组织，格式如下：

```text
screenshots/YYYY/MM/DD/<filename>
```

### 持仓

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/positions/list` | 查询持仓列表，支持 `status`、`direction`、`symbol` 筛选 |
| `POST` | `/api/positions/create` | 创建持仓记录 |
| `GET` | `/api/positions/detail/<position_id>` | 查询持仓详情 |
| `PUT` | `/api/positions/update/<position_id>` | 更新持仓记录 |
| `DELETE` | `/api/positions/delete/<position_id>` | 删除持仓记录 |
| `GET` | `/api/positions/stats` | 查询持仓统计 |
| `POST` | `/api/positions/toggle-status/<position_id>` | 切换有仓/空仓状态 |

### 品种事件

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/events/list` | 查询指定品种事件列表，参数：`symbol`、`start_date`、`end_date` |
| `POST` | `/api/events/create` | 创建事件 |
| `GET` | `/api/events/detail/<event_id>` | 查询事件详情 |
| `PUT` | `/api/events/update/<event_id>` | 更新事件 |
| `DELETE` | `/api/events/delete/<event_id>` | 删除事件 |
| `GET` | `/api/events/recent` | 查询近期新增事件，参数：`days`、`limit` |

### Trading

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/trading/signals` | 查询信号面板，参数：`date`、`variety_name`、`signal_type` |
| `GET` | `/api/trading/operations` | 查询操作建议，参数：`date`、`variety_name`、`is_selected` |
| `GET` | `/api/trading/positions` | 查询当前开放持仓及浮动盈亏 |
| `GET` | `/api/trading/positions/history` | 查询已平仓历史，参数：`limit` |
| `GET` | `/api/trading/account/curve` | 查询资金曲线，参数：`start_date`、`end_date` |
| `GET` | `/api/trading/account/summary` | 查询账户摘要，参数：`date` |
| `GET` | `/api/trading/pool` | 查询池子 A 品种列表、启用状态、板块列表 |
| `PATCH` | `/api/trading/pool/variety/<variety_id>` | 更新池子 A 中单个品种的 `sector` 与 `is_active` |
| `GET` | `/api/trading/market-context` | 查询市场上下文，参数：`variety_id`、`days`、`end_date` |
| `GET` | `/api/trading/variety-list` | 查询带 `contracts_symbol` 的品种列表 |
| `GET` | `/api/trading/variety-kline` | 查询品种 K 线与主力/散户序列，参数：`variety_id`、`start_date`、`end_date` |

## 接口数量

| 模块 | 数量 |
| --- | --- |
| 系统设置 | 2 |
| 合约与历史行情 | 2 |
| 新闻 | 11 |
| OSS | 2 |
| 持仓 | 7 |
| 品种事件 | 6 |
| Trading | 11 |
| 合计 | 41 |

## 数据表说明

### 启动时自动初始化的表

| 表名 | 说明 |
| --- | --- |
| `contracts_main` | 主连合约列表 |
| `system_config` | 系统配置 |
| `contract_list_update_log` | 合约列表更新日志 |
| `history_update_log` | 历史数据更新日志 |
| `recommendation_log` | 每日推荐日志 |
| `news_red_telegraph` | 财联社新闻主表 |
| `news_process_tracking` | 新闻处理与跟踪表 |
| `futures_positions` | 业务持仓表 |

### 接口直接依赖的业务表

| 表名 | 说明 |
| --- | --- |
| `futures_events` | 品种事件表 |
| `trading_signals` | 信号面板数据 |
| `trading_operations` | 操作建议数据 |
| `trading_positions` | Trading 持仓与历史持仓 |
| `trading_account_daily` | 账户日度权益曲线 |
| `trading_pool` | 池子 A 配置 |
| `fut_variety` | 品种维表 |
| `fut_strength` | 主力/散户指标序列 |
| `fut_daily_close` | 日线收盘价序列 |
| `hist_{symbol}` | 各合约历史行情表，表名按合约代码动态拼接 |

## 开发入口

- 应用入口：[start.py](D:/ysd/workstation/automysqlback/start.py)
- Flask 应用与初始化逻辑：[app.py](D:/ysd/workstation/automysqlback/app.py)
- 路由注册入口：[routes/__init__.py](D:/ysd/workstation/automysqlback/routes/__init__.py)

各模块代码位置：

- 合约与历史行情：[routes/contracts_routes.py](D:/ysd/workstation/automysqlback/routes/contracts_routes.py)
- 新闻与 OSS：[routes/news_routes.py](D:/ysd/workstation/automysqlback/routes/news_routes.py)
- 持仓：[routes/positions_routes.py](D:/ysd/workstation/automysqlback/routes/positions_routes.py)
- 品种事件：[routes/events_routes.py](D:/ysd/workstation/automysqlback/routes/events_routes.py)
- Trading：[routes/trading_routes.py](D:/ysd/workstation/automysqlback/routes/trading_routes.py)
