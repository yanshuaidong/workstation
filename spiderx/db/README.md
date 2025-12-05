# crawler.db 数据库表结构

## analysis_task 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增ID |
| title | TEXT | 任务标题 |
| prompt | TEXT | 提示词/分析内容 |
| news_time | DATETIME | 新闻时间 |
| ai_result | TEXT | AI分析结果 |
| is_analyzed | INTEGER | 是否已分析（0/1） |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## bloomberg_news 表

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| id | INTEGER | - | 主键，自增ID |
| published_at | DATETIME | - | 新闻发布日期（必填） |
| headline | TEXT | - | 新闻标题（必填） |
| brand | TEXT | '' | 新闻类型/品牌 |
| url | TEXT | - | 新闻地址（必填） |
| status | INTEGER | 0 | 状态：0-未处理，1-已处理 |
| created_at | DATETIME | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | CURRENT_TIMESTAMP | 更新时间 |

### 索引
- `idx_published_at`: 按新闻发布日期倒序
- `idx_status`: 按状态
- `idx_created_at`: 按创建时间倒序
