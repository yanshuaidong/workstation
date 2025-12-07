# Reuters 路透社新闻采集系统

路透社新闻自动采集和处理系统，包含浏览器插件和后端服务。

## 📋 系统架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  浏览器插件      │────▶│  后端服务        │────▶│  数据库          │
│  (API拦截)      │     │  (Flask/1125)   │     │  (SQLite/MySQL) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │
         │                       ▼
         │              ┌─────────────────┐
         └─────────────▶│  定时任务        │
                        │  (5/11/17/23点)  │
                        └─────────────────┘
```

## 🎯 功能说明

### 浏览器插件
- 拦截 Reuters Commodities 页面的 API 请求
- 提取新闻数据：标题、发布时间、URL
- 自动发送到本地后端服务

### 后端服务
- 接收插件发送的新闻数据
- 存储到 SQLite 数据库 `reuters_news` 表
- 定时任务在 **5点、11点、17点、23点** 执行（与彭博社错开1小时）
- AI 筛选期货相关新闻
- 保存结果到 MySQL 和 `analysis_task` 表

## 📁 文件结构

```
rtrsnews/
├── main.py              # 后端服务主程序
├── manifest.json        # 插件配置文件
├── background.js        # 后台服务脚本
├── content-main.js      # API拦截脚本（MAIN world）
├── content-bridge.js    # 数据发送脚本（ISOLATED world）
├── popup.html           # 插件弹窗界面
├── popup.js             # 弹窗交互逻辑
├── icon.png             # 插件图标
├── requirements.txt     # Python依赖
├── start_scheduler.sh   # 启动脚本
├── stop_scheduler.sh    # 停止脚本
└── README.md            # 说明文档
```

## 🚀 快速开始

### 1. 启动后端服务

```bash
cd spiderx/rtrsnews

# 启动服务
./start_scheduler.sh

# 停止服务
./stop_scheduler.sh
```

### 2. 安装浏览器插件

1. 打开 Chrome 浏览器，访问 `chrome://extensions/`
2. 开启"开发者模式"
3. 点击"加载已解压的扩展程序"
4. 选择 `rtrsnews` 目录

### 3. 使用插件

1. 访问 [Reuters Markets Commodities](https://www.reuters.com/markets/commodities/)
2. 插件会自动拦截 API 请求并发送数据
3. 点击插件图标可以：
   - 启动/停止定时刷新任务
   - 查看执行记录
   - 手动测试处理

## 🔗 API 接口

| 接口 | 方法 | 说明 |
|-----|------|------|
| `/api/capture` | POST | 接收插件发送的新闻数据 |
| `/api/health` | GET | 健康检查 |
| `/api/stats` | GET | 获取统计信息 |
| `/api/process_test` | POST | 测试处理（立即处理所有待处理新闻） |

## 📊 数据库表结构

### reuters_news 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增ID |
| published_time | DATETIME | 新闻发布时间（唯一，用于去重） |
| title | TEXT | 新闻标题 |
| url | TEXT | 新闻完整URL |
| status | INTEGER | 状态：0-未处理，1-已处理 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## ⏰ 定时任务

与彭博社（6/12/18/0点）错开1小时：

| 时间 | 处理范围 |
|-----|---------|
| 5:00 | 23点到5点的新闻 |
| 11:00 | 5点到11点的新闻 |
| 17:00 | 11点到17点的新闻 |
| 23:00 | 17点到23点的新闻 |

## 🔧 拦截的 API

```
https://www.reuters.com/pf/api/v3/content/fetch/articles-by-section-alias-or-id-v1?query=...
```

参数说明：
- `section_id`: `/markets/commodities`
- `size`: 返回条数
- `orderby`: 排序方式

## 📝 日志

- 服务日志：`reuters_service.log`
- 查看日志：`tail -f reuters_service.log`

## 🔍 调试

1. 打开 Chrome 开发者工具（F12）
2. 查看 Console 标签页的日志
3. 后台脚本日志在 `chrome://extensions/` 点击插件的"服务工作进程"查看

## ⚠️ 注意事项

1. 确保后端服务在端口 **1125** 运行
2. 插件只在 `https://www.reuters.com/*` 域名下生效
3. 定时任务需要保持 Chrome 浏览器运行
4. 数据去重基于 `published_time` 字段
