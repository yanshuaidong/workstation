# crawler.db 数据库表结构

## bloomberg_news 表

用于存储从浏览器插件接收的彭博社新闻数据。

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| id | INTEGER | - | 主键，自增ID |
| published_at | DATETIME | - | 新闻发布日期（必填，唯一，用于去重） |
| headline | TEXT | - | 新闻标题（必填） |
| brand | TEXT | '' | 新闻类型/品牌 |
| url | TEXT | - | 新闻地址（必填，完整URL） |
| status | INTEGER | 0 | 状态：0-未处理，1-已处理 |
| created_at | DATETIME | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | CURRENT_TIMESTAMP | 更新时间 |

### 索引
- `idx_published_at`: 按新闻发布日期倒序
- `idx_status`: 按状态
- `idx_created_at`: 按创建时间倒序
- `idx_unique_published_at`: 唯一索引，用于去重

---

## analysis_task 表

用于存储待分析的任务，由定时任务将筛选后的新闻写入此表。

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| id | INTEGER | - | 主键，自增ID |
| title | TEXT | - | 任务标题（如：【彭博社2025年12月06日0点到6点新闻】） |
| prompt | TEXT | - | 提示词/分析内容（AI筛选结果+分析指令） |
| news_time | DATETIME | - | 新闻时间段的开始时间 |
| ai_result | TEXT | '' | AI分析结果（由其他程序填充） |
| is_analyzed | INTEGER | 0 | 是否已分析：0-待分析，1-已分析 |
| created_at | DATETIME | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | CURRENT_TIMESTAMP | 更新时间 |

### 索引
- `idx_analysis_task_is_analyzed`: 按分析状态
- `idx_analysis_task_created_at`: 按创建时间倒序

---

## 数据流程

```
浏览器插件 -> bloomberg_news表(status=0) 
           -> 定时任务筛选 
           -> AI处理 
           -> analysis_task表 
           -> 标记bloomberg_news(status=1) 
           -> 删除已处理数据
```
