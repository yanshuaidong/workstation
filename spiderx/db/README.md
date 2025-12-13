# 🗄️ 共享数据库 (crawler.db)

> **系统定位**: 数据中转站，连接「新闻采集」和「双AI分析」系统的**桥梁**

## 🔗 系统关联

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                              新闻自动化处理流水线 (双AI分析)                             │
├───────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  ┌──────────────┐     │
│   │  BBGNews     │      │     DB       │      │ GeminiHelper │  │ChatGPTHelper │     │
│   │   采集端     │ ───► │  (本数据库)  │ ───► │   分析端     │  │   分析端     │     │
│   │  端口:1123   │      │  crawler.db  │      │  端口:1124   │  │  端口:1126   │     │
│   └──────────────┘      └──────────────┘      └──────────────┘  └──────────────┘     │
│         │                      │                      │                │              │
│         │                      │                      │                │              │
│       写入                   存储              Gemini分析        ChatGPT分析          │
│   bloomberg_news         analysis_task    gemini_analyzed=0   chatgpt_analyzed=0     │
│   analysis_task                           gemini_result       chatgpt_result         │
│                                                                                       │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

**数据流转**：
1. **BBGNews** 写入 `bloomberg_news`（原始新闻）和 `analysis_task`（筛选后任务）
2. **GeminiHelper** 读取 `gemini_analyzed=0` 的任务，分析后更新 `gemini_result`
3. **ChatGPTHelper** 读取 `chatgpt_analyzed=0` 的任务，分析后更新 `chatgpt_result`
4. 当两个AI都分析完成后，`is_analyzed` 自动设为1

## 📊 表结构

### bloomberg_news 表
> 存储从Bloomberg插件接收的原始新闻（处理后会删除）

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| id | INTEGER | 自增 | 主键 |
| published_at | DATETIME | - | 新闻发布时间（唯一索引，用于去重） |
| headline | TEXT | - | 新闻标题 |
| brand | TEXT | '' | 新闻类型/品牌 |
| url | TEXT | - | 新闻链接（完整URL） |
| status | INTEGER | 0 | 状态：0-未处理，1-已处理 |
| created_at | DATETIME | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | CURRENT_TIMESTAMP | 更新时间 |

**索引**：
- `idx_published_at` - 按发布时间倒序
- `idx_status` - 按状态
- `idx_created_at` - 按创建时间倒序
- `idx_unique_published_at` - 唯一索引（去重）

---

### analysis_task 表
> 存储待分析的任务（双AI分析核心交互表）

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| id | INTEGER | 自增 | 主键（task_id引用） |
| title | TEXT | - | 任务标题，如【彭博社2025年12月06日0点到6点新闻】 |
| prompt | TEXT | - | AI筛选结果 + 分析指令 |
| news_time | DATETIME | - | 新闻时间段开始时间 |
| **gemini_result** | TEXT | '' | Gemini分析结果（由GeminiHelper填充） |
| **chatgpt_result** | TEXT | '' | ChatGPT分析结果（由ChatGPTHelper填充） |
| **gemini_analyzed** | INTEGER | 0 | Gemini分析状态：0-待分析，1-已分析 |
| **chatgpt_analyzed** | INTEGER | 0 | ChatGPT分析状态：0-待分析，1-已分析 |
| is_analyzed | INTEGER | 0 | 全部完成状态：两个AI都分析完后自动设为1 |
| created_at | DATETIME | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | CURRENT_TIMESTAMP | 更新时间 |

**索引**：
- `idx_analysis_task_is_analyzed` - 按分析状态
- `idx_analysis_task_created_at` - 按创建时间倒序

**双AI分析流程**：
1. 新任务创建时：`gemini_analyzed=0`, `chatgpt_analyzed=0`, `is_analyzed=0`
2. Gemini完成后：`gemini_analyzed=1`, `gemini_result=内容`
3. ChatGPT完成后：`chatgpt_analyzed=1`, `chatgpt_result=内容`
4. 两个都完成后：`is_analyzed=1`

---

### reuters_news 表
> 存储路透社新闻（结构与bloomberg_news类似，预留扩展）

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| id | INTEGER | 自增 | 主键 |
| published_time | DATETIME | - | 新闻发布时间（唯一索引） |
| title | TEXT | - | 新闻标题 |
| url | TEXT | - | 新闻链接 |
| status | INTEGER | 0 | 状态：0-未处理，1-已处理 |
| created_at | DATETIME | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | CURRENT_TIMESTAMP | 更新时间 |

## 🔄 数据流程

```
BBGNews采集
    │
    ├──► bloomberg_news表 (status=0)
    │         │
    │         ▼ 定时AI筛选
    │         │
    │         ▼ 标记 status=1 并删除
    │
    └──► analysis_task表 (gemini_analyzed=0, chatgpt_analyzed=0)
                  │
          ┌───────┴───────┐
          │               │
          ▼               ▼
    GeminiHelper    ChatGPTHelper
    (端口:1124)      (端口:1126)
          │               │
          ▼               ▼
    gemini_result   chatgpt_result
    gemini_analyzed=1  chatgpt_analyzed=1
          │               │
          └───────┬───────┘
                  │
                  ▼
         两个都完成后 is_analyzed=1
```

## 🚀 初始化数据库

```bash
cd spiderx/db
python init_db.py
```

输出示例：
```
✅ 数据库初始化成功：/path/to/spiderx/db/crawler.db
📊 数据库位置：/path/to/spiderx/db/crawler.db
📋 已创建表：bloomberg_news, reuters_news, analysis_task
```

## 📋 常用查询

```bash
# 进入SQLite命令行
sqlite3 crawler.db

# 查看待处理的Bloomberg新闻数量
SELECT COUNT(*) FROM bloomberg_news WHERE status = 0;

# 查看 Gemini 待分析的任务
SELECT id, title, news_time FROM analysis_task WHERE gemini_analyzed = 0;

# 查看 ChatGPT 待分析的任务
SELECT id, title, news_time FROM analysis_task WHERE chatgpt_analyzed = 0;

# 查看双AI分析状态
SELECT id, title, gemini_analyzed, chatgpt_analyzed, is_analyzed 
FROM analysis_task ORDER BY id DESC LIMIT 10;

# 查看已完成双AI分析的任务
SELECT id, title, news_time FROM analysis_task WHERE is_analyzed = 1 ORDER BY id DESC LIMIT 10;

# 对比两个AI的分析结果预览
SELECT id, title, 
       substr(gemini_result, 1, 100) as gemini_preview,
       substr(chatgpt_result, 1, 100) as chatgpt_preview 
FROM analysis_task WHERE is_analyzed = 1;

# 查看只有一个AI完成的任务
SELECT id, title, gemini_analyzed, chatgpt_analyzed 
FROM analysis_task 
WHERE (gemini_analyzed = 1 AND chatgpt_analyzed = 0) 
   OR (gemini_analyzed = 0 AND chatgpt_analyzed = 1);

# 退出
.quit
```

## ⚠️ 注意事项

1. **初始化/迁移**: 必须先运行 `init_db.py` 初始化或迁移数据库，再启动服务
2. **文件位置**: 数据库文件 `crawler.db` 位于 `spiderx/db/` 目录
3. **共享访问**: BBGNews (1123)、GeminiHelper (1124)、ChatGPTHelper (1126) 都会访问此数据库
4. **数据清理**: `bloomberg_news` 表数据处理后会自动删除，`analysis_task` 数据会保留
5. **双AI独立**: Gemini和ChatGPT互不影响，各自读取自己未分析的任务

## 🔧 路径引用

三个服务中引用数据库的路径：

```python
# BBGNews (main.py)
DB_DIR = Path(__file__).parent.parent / "db"
DB_PATH = DB_DIR / "crawler.db"

# GeminiHelper (main.py)
LOCAL_DB_PATH = os.path.join(os.path.dirname(__file__), '../db/crawler.db')

# ChatGPTHelper (main.py)
LOCAL_DB_PATH = os.path.join(os.path.dirname(__file__), '../db/crawler.db')
```

## 🔄 数据库迁移

如果已有旧版数据库，运行迁移脚本自动添加新字段：

```bash
cd spiderx/db
python init_db.py migrate
```

迁移会自动：
- 添加 `gemini_result`, `chatgpt_result` 字段
- 添加 `gemini_analyzed`, `chatgpt_analyzed` 字段
- 将旧的 `ai_result` 数据迁移到 `gemini_result`

定时执行时间
服务	执行时间点	间隔
Gemini	4点、8点、12点、16点、20点、24点	每4小时
ChatGPT	2点、6点、10点、14点、18点、22点	每4小时
