# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

个人期货数据系统，包含前端、后端API、数据爬虫、数据采集、量化策略五个子系统。

## Common Commands

### 部署

```bash
cd /root/workstation
git pull
bash deploy.sh deploy
```

部署脚本其他命令：
```bash
bash deploy.sh build           # 构建前端 + 安装后端依赖（不重启）
bash deploy.sh start           # 启动后端服务 + 重载 Nginx
bash deploy.sh stop            # 停止后端服务
bash deploy.sh restart         # 重启后端 + 重载 Nginx
bash deploy.sh status          # 查看服务状态和健康检查
bash deploy.sh logs            # 查看后端日志（journalctl -u workstation-backend -f）
bash deploy.sh install-service # 安装/更新 systemd 服务
bash deploy.sh install-nginx   # 安装/更新 Nginx 配置
```

### 前端开发（workfront/）

```bash
cd workfront
npm run dev       # 本地开发服务器（端口 8080，代理 /api-a -> localhost:7001）
npm run build     # 生产构建
npm run lint      # lint 检查
```

### 后端本地开发（automysqlback/）

```bash
cd automysqlback
pip install -r requirements.txt
python start.py   # 启动 Flask，监听 7001 端口
```

### 爬虫服务（spiderx/）——本地运行，不在 Docker 内

```bash
cd spiderx
./runall.sh    # 启动 bbgnews、chatgpthelper、clsnewscraper、drivehelper、eastfutuscraper、futurestop10、gthtposiscraper、rtrsnews
./stopall.sh   # 停止所有爬虫服务
```

> **注意：** `geminihelper` 和 `doubaohelper` 未被 `runall.sh` 管理，需单独启停。

各爬虫单独操作：
```bash
cd spiderx/<service>
./start_scheduler.sh   # 调度类爬虫（clsnewscraper、eastfutuscraper、gthtposiscraper、drivehelper、futurestop10 等）
./start_server.sh      # HTTP 服务类（chatgpthelper、geminihelper、doubaohelper、bbgnews、rtrsnews）
./stop_scheduler.sh / ./stop_server.sh
```

### 数据采集（database/）

```bash
cd database
./runall.sh    # 启动 fut_pulse、futures、institution、stock 四组数据采集任务
```

### 量化策略（trading/）

```bash
cd trading/strategies
python daily_run.py   # 执行每日策略批处理（信号计算 + 操作建议生成）
```

## Architecture

### 子系统总览

| 目录 | 技术栈 | 运行方式 | 说明 |
|------|--------|---------|------|
| `workfront/` | Vue 3 + Element Plus + ECharts | systemd / npm | 前端 UI |
| `automysqlback/` | Flask + PyMySQL | systemd (port 7001) | 后端 REST API |
| `nginx/` | Nginx | systemd (port 80) | 反向代理 |
| `spiderx/` | Python | 本地 nohup | 各类爬虫 & AI 助手 |
| `database/` | Python | 本地定时 | 期货市场数据采集入库 |
| `trading/` | Python | 本地定时 | 量化策略引擎（信号 + 操作建议） |

### 请求路由（Nginx）

- `/`       → 前端静态资源（`/var/www/workstation/dist`）
- `/api-a/` → 后端 API（`127.0.0.1:7001`，Nginx 内部重写为 `/api/`）
- `/health` → 健康检查

### 后端 API 规范

- 统一响应格式：`{code: 0, message: "...", data: {...}}`（`code: 0` 成功，`code: 1` 失败）
- 主要路由模块在 `automysqlback/routes/`：
  - `contracts_routes.py`：合约列表、历史行情数据
  - `news_routes.py`：财联社新闻 CRUD + OSS 文件管理
  - `positions_routes.py`：持仓管理
  - `events_routes.py`：品种事件管理
  - `trading_routes.py`：交易策略查询（信号、操作建议、持仓曲线、K线、池子管理）
  - `app.py`：系统设置、数据库初始化、蓝图注册

### 数据存储

- **MySQL（阿里云 RDS）**：所有期货数据、新闻、持仓记录、策略数据
- **阿里云 OSS**：新闻截图（路径格式：`screenshots/YYYY/MM/DD/`）
- 动态表：每个合约独立一张历史行情表，命名为 `hist_{symbol}`（小写）

### 数据采集模块（database/）

| 子模块 | 说明 |
|--------|------|
| `fut_pulse/` | 主力/散户资金强度 + 日收盘价（AkShare + 截图OCR） |
| `futures/` | 主连合约历史数据拉取、更新、回填 |
| `institution/` | 机构持仓数据 |
| `stock/` | 股票数据（含 ~1GB SQLite 本地库） |

### 量化策略模块（trading/strategies/）

| 文件 | 说明 |
|------|------|
| `daily_run.py` | 每日批处理入口 |
| `signals.py` | 信号计算引擎 |
| `operations.py` | 操作建议生成 |
| `account.py` | 账户管理、开仓/平仓执行 |
| `data_loader.py` | 读取 `fut_*` 基础数据 |
| `settings.py` | 策略常量、品种板块映射 |
| `db.py` | 数据库连接 |
| `create_tables.py` | `trading_*` 表模式初始化 |

### 爬虫服务端口（本地 HTTP 服务）

| 服务 | 端口 |
|------|------|
| bbgnews | 1123 |
| geminihelper | 1124 |
| rtrsnews | 1125 |
| chatgpthelper | 1126 |
| doubaohelper | 1127 |

### 环境配置

`.env` 文件（从 `env.production` 复制）用于部署和运行时配置；spiderx 各子目录通常自带配置文件或读取同一 `.env`。

必填环境变量：`DB_HOST`、`DB_USER`、`DB_PASSWORD`、`OSS_ENDPOINT`、`OSS_BUCKET`、`OSS_ACCESS_KEY_ID`、`OSS_ACCESS_KEY_SECRET`