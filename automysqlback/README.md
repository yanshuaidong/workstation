# 期货数据系统后端 (AutoMySQLBack)

## 项目简介
期货数据更新系统后端服务，提供期货历史数据获取、技术指标计算、财联社新闻管理等功能。

## 技术栈
- **后端**: Flask + PyMySQL + APScheduler
- **数据源**: akshare (期货数据)
- **数据库**: MySQL (阿里云RDS)
- **存储**: 阿里云OSS (新闻截图)
- **部署**: Docker

## 核心功能
- 期货主连合约历史数据自动更新
- 技术指标计算 (MACD/RSI/KDJ/布林带)
- 多空推荐策略生成
- 财联社新闻数据管理
- 分时行情数据查询

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
| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| DB_HOST | 数据库主机 | xxx.mysql.rds.aliyuncs.com |
| DB_USER | 数据库用户 | xxx |
| DB_PASSWORD | 数据库密码 | - |
| DB_NAME | 数据库名 | futures |
| OSS_ACCESS_KEY_ID | OSS访问密钥ID | - |
| OSS_ACCESS_KEY_SECRET | OSS访问密钥 | - |

## API 端点

### 系统设置
- `GET /api/settings` - 获取系统设置
- `POST /api/settings` - 更新系统设置

### 合约管理
- `POST /api/contracts/update-list` - 更新合约列表
- `GET /api/contracts/list` - 获取数据库中的合约列表
- `GET /api/contracts/list-update-log` - 获取合约列表更新记录

### 历史数据
- `POST /api/history/update-all` - 批量更新历史数据
- `POST /api/history/retry-single` - 重试单个合约历史数据更新
- `GET /api/history/logs` - 获取历史数据更新日志
- `POST /api/history/recalculate-indicators` - 重新计算现有数据的技术指标
- `GET /api/history/data` - 获取指定合约的历史数据

### 分时行情
- `GET /api/intraday/contracts` - 获取可用的期货合约列表（用于分时行情查询）
- `GET /api/intraday/data` - 获取分时行情数据

### 推荐记录
- `POST /api/recommendations/record` - 手动记录当日推荐
- `GET /api/recommendations/list` - 获取推荐记录列表

### 财联社新闻
- `GET /api/news/stats` - 获取新闻统计信息
- `GET /api/news/list` - 分页查询财联社新闻（包含搜索和筛选功能）
- `POST /api/news/create` - 创建新闻
- `GET /api/news/detail/<int:news_id>` - 获取新闻详情
- `PUT /api/news/update/<int:news_id>` - 更新新闻
- `DELETE /api/news/delete/<int:news_id>` - 删除新闻

### OSS存储
- `POST /api/oss/upload-url` - 获取OSS上传签名URL
- `POST /api/oss/access-url` - 获取OSS访问URL

## 注意事项
- 默认端口: **7001**
- 爬虫功能已迁移到 `spiderx` 项目
- 生产环境需配置完整的环境变量
- 定时任务默认关闭，需在系统设置中启用
