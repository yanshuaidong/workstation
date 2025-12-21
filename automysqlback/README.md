# 期货数据系统后端 (AutoMySQLBack)

## 项目简介

期货数据查询系统后端服务，提供期货合约列表查询、历史数据查询、财联社新闻管理、持仓管理等功能。

## 技术栈

- **后端框架**: Flask + Flask-CORS
- **数据库**: MySQL (阿里云RDS)
- **存储**: 阿里云OSS (新闻截图)
- **部署**: Docker

## 核心功能

- 期货主连合约列表查询
- 期货历史数据查询（数据来自阿里云 MySQL）
- 财联社新闻数据管理与跟踪流程
- 期货持仓管理

## 快速启动

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python start.py
```

### Docker 部署

```bash
# 构建镜像
docker build -t automysqlback .

# 运行容器
docker run -d -p 7001:7001 \
  -e DB_HOST=your_db_host \
  -e DB_USER=your_db_user \
  -e DB_PASSWORD=your_db_password \
  automysqlback
```

## 环境变量

| 变量名 | 描述 | 必填 |
|--------|------|------|
| DB_HOST | 数据库主机地址 | 是 |
| DB_PORT | 数据库端口 | 否 (默认3306) |
| DB_USER | 数据库用户名 | 是 |
| DB_PASSWORD | 数据库密码 | 是 |
| DB_NAME | 数据库名称 | 否 (默认futures) |
| OSS_ENDPOINT | OSS端点地址 | 是 |
| OSS_BUCKET | OSS存储桶名 | 是 |
| OSS_ACCESS_KEY_ID | OSS访问密钥ID | 是 |
| OSS_ACCESS_KEY_SECRET | OSS访问密钥 | 是 |

---

## API 接口文档

**基础信息**
- 默认端口: **7001**
- 统一响应格式: `{code: 0/1, message: string, data: object}`
- `code: 0` 表示成功，`code: 1` 表示失败

---

### 一、系统设置 (2个接口)

#### 1.1 获取系统设置
- **路径**: `GET /api/settings`
- **功能**: 获取系统配置信息
- **返回字段**:
  - `auto_update_enabled`: 是否开启自动更新
  - `daily_update_time`: 每日自动更新时间
  - `multithread_enabled`: 是否开启多线程
  - `concurrency`: 并发数量
  - `timeout_seconds`: 超时时间(秒)

#### 1.2 更新系统设置
- **路径**: `POST /api/settings`
- **功能**: 更新系统配置，并重新配置定时任务
- **请求参数**: JSON格式，包含上述配置字段

---

### 二、合约管理 (2个接口)

#### 2.1 获取合约列表
- **路径**: `GET /api/contracts/list`
- **功能**: 获取数据库中所有活跃的主连合约
- **返回**: `contracts` (合约数组), `total` (总数)

#### 2.2 获取历史数据
- **路径**: `GET /api/history/data`
- **功能**: 获取指定合约的历史数据（含技术指标）
- **请求参数**: `symbol` (必填), `start_date`, `end_date`
- **返回**: 价格、成交量、技术指标等

---

### 三、新闻管理 (11个接口)

#### 3.1 新闻统计
- **路径**: `GET /api/news/stats`
- **返回**: `total`, `today_count`, `latest_time`, `earliest_time`

#### 3.2 新闻列表
- **路径**: `GET /api/news/list`
- **功能**: 分页查询新闻，支持高级搜索
- **请求参数**:
  - `page`, `page_size`: 分页参数
  - `search`: 搜索关键字
  - `search_field`: 搜索字段 (title/content/message_type/market_react)
  - `message_label`: 标签筛选 (hard/soft/unknown)
  - `start_date`, `end_date`: 日期范围

#### 3.3 创建新闻
- **路径**: `POST /api/news/create`
- **请求参数**: `title` (必填), `content` (必填), `ctime`, `ai_analysis`, `message_score`, `message_label`, `message_type`, `market_react`, `screenshots`

#### 3.4 获取新闻详情
- **路径**: `GET /api/news/detail/<news_id>`

#### 3.5 更新新闻
- **路径**: `PUT /api/news/update/<news_id>`

#### 3.6 删除新闻
- **路径**: `DELETE /api/news/delete/<news_id>`
- **说明**: 同时删除关联的OSS文件和跟踪记录

#### 3.7 获取待校验新闻
- **路径**: `GET /api/news/process/unreviewed`
- **功能**: 获取最近30天内未校验的新闻

#### 3.8 标记已校验
- **路径**: `POST /api/news/process/review`
- **请求参数**: `tracking_id`

#### 3.9 获取跟踪列表
- **路径**: `GET /api/news/process/tracking-list`
- **功能**: 获取需要跟踪的硬消息列表（按3/7/14/28天分组）

#### 3.10 更新跟踪状态
- **路径**: `POST /api/news/process/update-tracking`
- **请求参数**: `tracking_id`, `track_type` (day3/day7/day14/day28)

#### 3.11 初始化跟踪记录
- **路径**: `POST /api/news/process/init-tracking`
- **功能**: 为现有新闻初始化跟踪记录（数据迁移用）

---

### 四、持仓管理 (7个接口)

#### 4.1 获取持仓列表
- **路径**: `GET /api/positions/list`
- **请求参数**: `status` (1=有仓/0=空仓), `direction` (LONG/SHORT), `symbol`

#### 4.2 创建持仓
- **路径**: `POST /api/positions/create`
- **请求参数**: `symbol` (必填), `direction` (必填), `status` (默认1)

#### 4.3 获取持仓详情
- **路径**: `GET /api/positions/detail/<position_id>`

#### 4.4 更新持仓
- **路径**: `PUT /api/positions/update/<position_id>`

#### 4.5 删除持仓
- **路径**: `DELETE /api/positions/delete/<position_id>`

#### 4.6 持仓统计
- **路径**: `GET /api/positions/stats`
- **返回**: `total`, `hold_count`, `flat_count`, `long_count`, `short_count`

#### 4.7 切换持仓状态
- **路径**: `POST /api/positions/toggle-status/<position_id>`
- **功能**: 在有仓/空仓之间切换

---

### 五、OSS文件管理 (2个接口)

#### 5.1 获取上传URL
- **路径**: `POST /api/oss/upload-url`
- **请求参数**: `news_id`, `filename`, `content_type` (默认image/png)
- **返回**: `upload_url`, `object_key`, `expires`

#### 5.2 获取访问URL
- **路径**: `POST /api/oss/access-url`
- **请求参数**: `object_key`, `expires` (默认3600秒)
- **返回**: `access_url`, `expires`

---

## 接口统计

| 模块 | 接口数量 | 说明 |
|------|---------|------|
| 系统设置 | 2 | 配置管理 |
| 合约管理 | 2 | 合约列表、历史数据查询 |
| 新闻管理 | 11 | 新闻CRUD、处理流程跟踪 |
| 持仓管理 | 7 | 持仓CRUD和统计 |
| OSS文件管理 | 2 | 文件上传和访问 |
| **总计** | **24** | - |

---

## 数据库表结构

| 表名 | 说明 |
|------|------|
| `contracts_main` | 期货主连合约列表 |
| `system_config` | 系统配置表 |
| `hist_{symbol}` | 各合约历史数据表 (动态创建) |
| `news_red_telegraph` | 财联社新闻主表 |
| `news_process_tracking` | 新闻处理流程跟踪表 |
| `futures_positions` | 期货持仓表 |

---

## 项目结构

```
automysqlback/
├── app.py              # 主入口，系统设置API，数据库初始化
├── start.py            # 启动脚本
├── routes/
│   ├── __init__.py
│   ├── contracts_routes.py   # 合约列表、历史数据模块
│   ├── news_routes.py        # 新闻、OSS模块
│   └── positions_routes.py   # 持仓模块
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 技术特点

1. **统一响应格式**: 所有接口使用 `{code, message, data}` 格式
2. **数据完整性**: 新闻删除时级联删除OSS文件和跟踪记录
3. **数据来源**: 所有期货数据从阿里云 MySQL 数据库读取

---

## 注意事项

- 定时任务默认关闭，需在系统设置中启用
- OSS文件按日期组织目录 (screenshots/YYYY/MM/DD/)
- 新闻处理流程：标签校验 → 定期跟踪 (3/7/14/28天)
- 爬虫功能已迁移到 `spiderx` 项目
- 期货数据获取功能已移除，所有数据从阿里云 MySQL 读取
