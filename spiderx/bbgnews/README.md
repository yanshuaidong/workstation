# 📰 Bloomberg 新闻采集系统

> **系统定位**: 新闻数据采集与AI筛选模块，是「新闻自动化处理流水线」的**上游**组件

## 🔗 系统关联

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         新闻自动化处理流水线                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐             │
│   │  BBGNews     │      │     DB       │      │ GeminiHelper │             │
│   │  (本系统)    │ ───► │  共享数据库   │ ───► │   AI分析     │             │
│   │  端口:1123   │      │  crawler.db  │      │  端口:1124   │             │
│   └──────────────┘      └──────────────┘      └──────────────┘             │
│         │                      │                      │                     │
│         ▼                      ▼                      ▼                     │
│    采集+AI筛选           数据中转站             深度AI分析                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**协作关系**：
1. **BBGNews** → 采集新闻 → AI筛选期货相关 → 写入 `analysis_task` 表
2. **GeminiHelper** → 读取 `analysis_task` 表 → Gemini深度分析 → 更新分析结果

## 🎯 核心功能

| 组件 | 功能 | 执行频率 |
|------|------|----------|
| Chrome插件 | 定时刷新Bloomberg页面，拦截新闻API | 每60分钟 |
| Python服务 | 接收存储、AI筛选、数据分发 | 每天4次（6/12/18/24点） |

## 📊 数据流转

```
Bloomberg页面
    ↓ Chrome插件拦截API
    ↓ POST /api/capture
Python服务 (端口1123)
    ↓ 存入 bloomberg_news 表
    ↓ 定时任务触发 (6/12/18/24点)
    ↓ AI筛选期货相关新闻
    ├─► MySQL: news_red_telegraph + news_process_tracking
    └─► SQLite: analysis_task (供GeminiHelper消费)
```

## 🚀 快速启动

### 前置条件
- Python 3.7+
- Chrome浏览器
- 已初始化数据库（运行 `spiderx/db/init_db.py`）

### 启动步骤

```bash
# 1. 先确保数据库已初始化
cd spiderx/db && python init_db.py

# 2. 安装依赖
cd spiderx/bbgnews && pip install -r requirements.txt

# 3. 启动Python服务
# Linux/Mac
./start_scheduler.sh

# Windows
python main.py

# 4. 安装Chrome插件
# chrome://extensions/ → 开发者模式 → 加载已解压的扩展程序 → 选择 bbgnews 目录
```

## 📋 API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/capture` | POST | 接收插件发送的新闻数据 |
| `/api/health` | GET | 健康检查 |
| `/api/stats` | GET | 统计信息（待处理/已处理数量） |
| `/api/process_now` | POST | 手动触发AI筛选（测试用） |
| `/api/process_test` | POST | 测试处理所有待处理新闻 |

### 健康检查示例
```bash
curl http://localhost:1123/api/health
```

## 📂 目录结构

```
bbgnews/
├── main.py                 # ⭐ Python核心服务
├── manifest.json           # Chrome扩展配置
├── background.js           # 插件后台（定时刷新）
├── content-main.js         # API拦截（MAIN world）
├── content-bridge.js       # 数据桥接（ISOLATED world）
├── popup.html/js           # 插件控制界面
├── start_scheduler.sh      # 启动脚本
├── stop_scheduler.sh       # 停止脚本
├── bloomberg_service.log   # 服务日志
└── requirements.txt        # Python依赖
```

## 🔧 配置说明

### 定时任务时间点
- **0-6点新闻** → 6点处理
- **6-12点新闻** → 12点处理
- **12-18点新闻** → 18点处理
- **18-24点新闻** → 24点（0点）处理

### AI筛选策略
- 筛选期货相关新闻（原油、黄金、铜、大豆等）
- 翻译成中文标题
- 格式：`【XX期货相关】【中文标题】新闻URL`

### 重试机制
- 第一次：60秒超时
- 第二次：120秒超时
- 失败后放弃本次处理

## 🗄️ 数据库说明

### 写入的表

| 表名 | 数据库 | 说明 |
|------|--------|------|
| `bloomberg_news` | SQLite | 原始新闻暂存（处理后删除） |
| `analysis_task` | SQLite | 分析任务（供GeminiHelper消费） |
| `news_red_telegraph` | MySQL | 新闻主表 |
| `news_process_tracking` | MySQL | 处理跟踪表 |

### 数据去重
- 基于 `published_at` 字段唯一索引
- 使用 `INSERT OR IGNORE` 自动去重

## ⚠️ 注意事项

1. **启动顺序**: 先初始化数据库 → 启动本服务 → 安装插件
2. **端口占用**: 确保1123端口可用
3. **插件状态**: 通过popup界面启动定时任务后才会自动刷新
4. **日志监控**: 查看 `bloomberg_service.log` 了解运行状态

## 🐛 故障排查

### 插件无法拦截数据
- 检查是否在Bloomberg网站
- 确认popup中定时任务已启动
- 查看浏览器控制台错误信息

### 定时任务未执行
```bash
# 查看统计信息
curl http://localhost:1123/api/stats

# 手动触发测试
curl -X POST http://localhost:1123/api/process_test
```

### 查看日志
```bash
# Linux/Mac
tail -f bloomberg_service.log

# Windows
Get-Content bloomberg_service.log -Wait
```
