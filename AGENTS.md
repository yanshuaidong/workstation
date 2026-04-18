# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

个人期货数据系统，包含前端、后端API、数据爬虫、量化分析四个子系统。

## Common Commands

### Docker 服务（nginx + workfront + automysqlback）

```bash
# 首次部署（拉取代码+构建+启动）
./deploy.sh deploy

# 启动/停止/重启
./deploy.sh start
./deploy.sh stop
./deploy.sh restart

# 查看状态和日志
./deploy.sh status
./deploy.sh logs [service_name]   # service_name: nginx / workfront / automysqlback
```

### 前端开发（workfront/）

```bash
cd workfront
npm run dev       # 本地开发服务器
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
./runall.sh    # 启动所有爬虫服务
./stopall.sh   # 停止所有爬虫服务
```

各爬虫单独操作：
```bash
cd spiderx/<service>
./start_scheduler.sh   # 调度类爬虫（clsnewscraper、eastfutuscraper、gthtposiscraper 等）
./start_server.sh      # HTTP 服务类（chatgpthelper、geminihelper、doubaohelper、bbgnews、rtrsnews）
./stop_scheduler.sh / ./stop_server.sh
```

### 数据库更新（database/ 和 quantlab/）

```bash
cd database
./runall.sh    # 启动所有数据库更新任务

cd quantlab
./runall.sh    # 启动量化预测服务
```

## Architecture

### 子系统总览

| 目录 | 技术栈 | 运行方式 | 说明 |
|------|--------|---------|------|
| `workfront/` | Vue 3 + Element Plus + ECharts | Docker | 前端 UI |
| `automysqlback/` | Flask + PyMySQL | Docker (port 7001) | 后端 REST API |
| `nginx/` | Nginx | Docker (port 80/443) | 反向代理 |
| `spiderx/` | Python | 本地 nohup | 各类爬虫 & AI 助手 |
| `database/` | Python | 本地定时 | 国泰期货数据拉取入库 |
| `quantlab/` | Python + scikit-learn | 本地定时 | 机器学习量化分析 |

### 请求路由（Nginx）

- `/`       → 前端静态资源（workfront 容器）
- `/api-a/` → 后端 API（automysqlback 容器，内部重写为 `/api/`）

### 后端 API 规范

- 统一响应格式：`{code: 0, message: "...", data: {...}}`（`code: 0` 成功，`code: 1` 失败）
- 主要路由模块在 `automysqlback/routes/`：
  - `contracts_routes.py`：合约列表、历史行情数据
  - `news_routes.py`：财联社新闻 CRUD + OSS 文件管理
  - `positions_routes.py`：持仓管理
  - `app.py`：系统设置、数据库初始化

### 数据存储

- **MySQL（阿里云 RDS）**：所有期货数据、新闻、持仓记录
- **阿里云 OSS**：新闻截图（路径格式：`screenshots/YYYY/MM/DD/`）
- 动态表：每个合约独立一张历史行情表，命名为 `hist_{symbol}`（小写）

### 爬虫服务端口（本地 HTTP 服务）

| 服务 | 端口 |
|------|------|
| bbgnews | 1123 |
| geminihelper | 1124 |
| rtrsnews | 1125 |
| chatgpthelper | 1126 |
| doubaohelper | 1127 |

### 环境配置

`.env` 文件（从 `env.production` 复制）用于 Docker 服务；spiderx 各子目录通常自带配置文件或读取同一 `.env`。

必填环境变量：`DB_HOST`、`DB_USER`、`DB_PASSWORD`、`OSS_ENDPOINT`、`OSS_BUCKET`、`OSS_ACCESS_KEY_ID`、`OSS_ACCESS_KEY_SECRET`
