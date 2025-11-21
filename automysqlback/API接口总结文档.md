# 期货数据更新系统 API 接口总结文档

## 概述

本文档总结了 `app.py` 中定义的所有 RESTful API 接口。系统共包含 **27个接口**，分为7个功能模块。

**基础信息：**
- 技术栈：Flask + akshare + pandas + MySQL + APScheduler
- 数据库：阿里云RDS MySQL
- 文件存储：阿里云OSS
- 统一响应格式：`{code: 0/1, message: string, data: object}`

---

## 一、系统设置模块 (2个接口)

### 1.1 获取系统设置
- **路径**: `GET /api/settings`
- **功能**: 获取系统配置信息
- **返回数据**:
  - `auto_update_enabled`: 是否开启自动更新
  - `daily_update_time`: 每日自动更新时间
  - `multithread_enabled`: 是否开启多线程
  - `concurrency`: 并发数量
  - `timeout_seconds`: 超时时间(秒)

### 1.2 更新系统设置
- **路径**: `POST /api/settings`
- **功能**: 更新系统配置，并重新配置定时任务
- **请求参数**: JSON格式，包含上述配置字段
- **说明**: 更新后会自动调用 `setup_scheduler()` 重新配置定时任务

---

## 二、合约管理模块 (3个接口)

### 2.1 更新合约列表
- **路径**: `POST /api/contracts/update-list`
- **功能**: 从公开接口获取期货合约列表并更新到数据库
- **处理流程**:
  1. 调用 `ak.futures_hist_table_em()` 获取合约数据
  2. 筛选主连合约（排除次主连和低成交量合约）
  3. 清空并重新插入合约数据
  4. 为新合约创建对应的历史数据表
  5. 初始化历史更新日志
  6. 记录更新日志
- **返回数据**:
  - `new_count`: 新增合约数量
  - `duration_ms`: 更新耗时（毫秒）

### 2.2 获取合约列表
- **路径**: `GET /api/contracts/list`
- **功能**: 获取数据库中所有活跃的主连合约列表
- **返回数据**:
  - `contracts`: 合约数组（包含symbol, name, exchange, is_active）
  - `total`: 合约总数

### 2.3 获取合约列表更新记录
- **路径**: `GET /api/contracts/list-update-log`
- **功能**: 获取最近一次合约列表更新的记录
- **返回数据**: 包含更新时间、更新方式、耗时、状态、错误信息等

---

## 三、历史数据模块 (5个接口)

### 3.1 批量更新所有主连历史数据
- **路径**: `POST /api/history/update-all`
- **功能**: 批量更新所有主连合约的历史数据
- **请求参数**:
  - `date_start`: 开始日期 (YYYY-MM-DD)
  - `date_end`: 结束日期 (YYYY-MM-DD)
- **处理流程**:
  1. 获取系统配置（超时时间、多线程设置、并发数）
  2. 获取所有活跃合约
  3. 后台执行更新任务（支持多线程/单线程）
  4. 更新完成后自动记录当日推荐
- **说明**: 异步执行，立即返回启动状态

### 3.2 重试单个合约历史数据更新
- **路径**: `POST /api/history/retry-single`
- **功能**: 重试单个合约的历史数据更新
- **请求参数**:
  - `symbol`: 合约代码
  - `date_start`: 开始日期
  - `date_end`: 结束日期
- **说明**: 后台异步执行，支持自动重试（最多3次）

### 3.3 获取历史数据更新日志
- **路径**: `GET /api/history/logs`
- **功能**: 获取所有合约的历史数据更新日志
- **返回数据**: 包含合约代码、名称、目标表、开始/结束时间、数据日期范围、状态、错误信息、重试次数等

### 3.4 重新计算技术指标
- **路径**: `POST /api/history/recalculate-indicators`
- **功能**: 重新计算现有数据的技术指标
- **请求参数**:
  - `symbol`: 合约代码（可选，不提供则处理所有合约）
- **处理指标**: MACD、RSI、KDJ、布林带
- **说明**: 后台异步执行

### 3.5 获取指定合约的历史数据
- **路径**: `GET /api/history/data`
- **功能**: 获取指定合约的历史数据（包含技术指标和推荐操作）
- **请求参数**:
  - `symbol`: 合约代码（必填）
  - `start_date`: 开始日期（可选，默认最近30天）
  - `end_date`: 结束日期（可选，默认今天）
- **返回数据**: 
  - 价格数据（开盘、最高、最低、收盘）
  - 成交量数据（成交量、持仓量、成交额）
  - 涨跌数据（涨跌、涨跌幅）
  - 技术指标（MACD、RSI、KDJ、布林带）
  - 推荐操作（做多/做空/观察）
- **限制**: 最多返回500条记录

---

## 四、分时行情模块 (2个接口)

### 4.1 获取分时合约列表
- **路径**: `GET /api/intraday/contracts`
- **功能**: 获取可用于分时行情查询的期货合约列表
- **处理流程**:
  1. 依次获取6个交易所的主力合约数据（dce, czce, shfe, gfex, cffex, ine）
  2. 解析合约代码并匹配中文名称
  3. 按交易所和品种名称排序
- **返回数据**:
  - `contracts`: 合约数组（包含symbol, name, variety_code, exchange）
  - `total`: 合约总数

### 4.2 获取分时行情数据
- **路径**: `GET /api/intraday/data`
- **功能**: 获取期货合约的分时行情数据
- **请求参数**:
  - `symbol`: 合约代码（必填）
  - `period`: 周期（默认60分钟，可选：1, 5, 15, 30, 60等）
  - `start_date`: 开始日期（可选，默认最近3天）
  - `end_date`: 结束日期（可选，默认今天）
- **返回数据**: 
  - 价格数据（开盘、最高、最低、收盘）
  - 成交量、持仓量
  - 时间戳
- **说明**: 数据按时间倒序排列（最新的在前面）

---

## 五、推荐记录模块 (2个接口)

### 5.1 手动记录当日推荐
- **路径**: `POST /api/recommendations/record`
- **功能**: 手动记录指定日期的推荐操作
- **请求参数**:
  - `date`: 日期字符串（可选，不提供则使用当前日期）
- **处理流程**:
  1. 查询所有活跃合约在指定日期的推荐操作
  2. 解析推荐操作（做多/做空/观察）和分值
  3. 汇总并存储到推荐记录表
- **返回数据**: 成功/失败状态

### 5.2 获取推荐记录列表
- **路径**: `GET /api/recommendations/list`
- **功能**: 获取推荐记录列表
- **请求参数**:
  - `start_date`: 开始日期（可选，默认最近30天）
  - `end_date`: 结束日期（可选，默认今天）
- **返回数据**:
  - `recommendations`: 推荐记录数组
    - `date`: 日期
    - `long_names`: 做多品种列表（逗号分隔）
    - `short_names`: 做空品种列表（逗号分隔）
    - `total_long_count`: 做多品种数量
    - `total_short_count`: 做空品种数量
    - `display_text`: 格式化显示文本
  - `total`: 记录总数

---

## 六、新闻管理模块 (13个接口)

### 6.1 新闻统计信息
- **路径**: `GET /api/news/stats`
- **功能**: 获取财联社新闻的统计信息
- **返回数据**:
  - `total`: 总新闻数
  - `today_count`: 今日新闻数
  - `latest_time`: 最新新闻时间
  - `earliest_time`: 最早新闻时间

### 6.2 分页查询新闻列表
- **路径**: `GET /api/news/list`
- **功能**: 分页查询财联社新闻，支持高级搜索和筛选
- **请求参数**:
  - `page`: 页码（默认1）
  - `page_size`: 每页数量（默认10，最大100）
  - `search`: 搜索关键字
  - `search_field`: 搜索字段（title/content/message_type/market_react，默认title）
  - `message_label`: 消息标签筛选（hard/soft/unknown）
  - `start_date`: 开始日期（YYYY-MM-DD）
  - `end_date`: 结束日期（YYYY-MM-DD）
- **返回数据**:
  - `news_list`: 新闻列表（包含所有字段）
  - `pagination`: 分页信息
  - `filters`: 当前筛选条件

### 6.3 创建新闻
- **路径**: `POST /api/news/create`
- **功能**: 创建新的财联社新闻记录
- **请求参数**:
  - `title`: 标题（必填）
  - `content`: 内容（必填）
  - `ctime`: 时间戳（可选，不提供则使用当前时间）
  - `ai_analysis`: AI分析/备注
  - `message_score`: 消息评分（0-100）
  - `message_label`: 消息标签（hard/soft/unknown）
  - `message_type`: 消息类型
  - `market_react`: 市场反应
  - `screenshots`: 截图URL数组
- **返回数据**: 新创建的新闻ID

### 6.4 获取新闻详情
- **路径**: `GET /api/news/detail/<news_id>`
- **功能**: 获取指定新闻的详细信息
- **返回数据**: 包含所有新闻字段，截图会自动生成访问URL

### 6.5 更新新闻
- **路径**: `PUT /api/news/update/<news_id>`
- **功能**: 更新新闻信息
- **请求参数**: JSON格式，包含需要更新的字段
- **可更新字段**: title, content, ai_analysis, message_score, message_label, message_type, market_react, screenshots

### 6.6 删除新闻
- **路径**: `DELETE /api/news/delete/<news_id>`
- **功能**: 删除新闻记录
- **处理流程**:
  1. 删除OSS上的截图文件
  2. 删除数据库记录（级联删除跟踪记录）
- **说明**: 删除新闻时会同时删除相关的OSS文件和跟踪记录

### 6.7 获取待校验新闻
- **路径**: `GET /api/news/process/unreviewed`
- **功能**: 获取待校验的新闻列表（最近30天内未校验的新闻）
- **返回数据**:
  - `total_unreviewed`: 待校验总数
  - `current_news`: 下一条待校验的新闻详情

### 6.8 标记新闻为已校验
- **路径**: `POST /api/news/process/review`
- **功能**: 标记新闻为已完成标签校验
- **请求参数**:
  - `tracking_id`: 跟踪记录ID
- **说明**: 更新 `is_reviewed` 和 `review_time` 字段

### 6.9 获取跟踪列表
- **路径**: `GET /api/news/process/tracking-list`
- **功能**: 获取需要跟踪的新闻列表（按天数分组）
- **返回数据**:
  - `day3_list`: 3天跟踪列表（距今3天及以上的硬消息，且3天跟踪未完成）
  - `day7_list`: 7天跟踪列表
  - `day14_list`: 14天跟踪列表
  - `day28_list`: 28天跟踪列表
  - `summary`: 统计信息（总数、各时间点数量）
- **说明**: 只返回硬消息（message_label='hard'）且到达跟踪时间点的消息

### 6.10 更新跟踪状态
- **路径**: `POST /api/news/process/update-tracking`
- **功能**: 更新指定时间点的跟踪状态
- **请求参数**:
  - `tracking_id`: 跟踪记录ID
  - `track_type`: 跟踪类型（day3/day7/day14/day28）
- **说明**: 更新对应的 `track_*_done` 和 `track_*_time` 字段

### 6.11 初始化跟踪记录
- **路径**: `POST /api/news/process/init-tracking`
- **功能**: 为现有新闻初始化跟踪记录（数据迁移用）
- **处理流程**: 查找没有跟踪记录的新闻，为其创建跟踪记录
- **返回数据**: 创建的记录数量

---

## 七、OSS文件管理模块 (2个接口)

### 7.1 获取OSS上传签名URL
- **路径**: `POST /api/oss/upload-url`
- **功能**: 生成OSS上传文件的签名URL
- **请求参数**:
  - `news_id`: 新闻ID（必填）
  - `filename`: 文件名（必填）
  - `content_type`: 文件类型（默认image/png）
- **返回数据**:
  - `upload_url`: 上传URL（带签名）
  - `object_key`: OSS对象键
  - `expires`: 过期时间（秒）
- **说明**: 文件按月份组织目录结构（screenshots/YYYY/MM/DD/）

### 7.2 获取OSS访问URL
- **路径**: `POST /api/oss/access-url`
- **功能**: 生成OSS文件的访问签名URL
- **请求参数**:
  - `object_key`: OSS对象键（必填）
  - `expires`: 过期时间（默认3600秒）
- **返回数据**:
  - `access_url`: 访问URL（带签名）
  - `expires`: 过期时间
- **说明**: 会检查对象是否存在，不存在则返回错误

---

## 接口统计汇总

| 模块 | 接口数量 | 说明 |
|------|---------|------|
| 系统设置 | 2 | 配置管理 |
| 合约管理 | 3 | 合约列表更新和查询 |
| 历史数据 | 5 | 历史数据更新、查询、技术指标计算 |
| 分时行情 | 2 | 分时数据查询 |
| 推荐记录 | 2 | 推荐操作记录和查询 |
| 新闻管理 | 13 | 新闻CRUD、统计、处理流程跟踪 |
| OSS文件管理 | 2 | 文件上传和访问 |
| **总计** | **27** | - |

---

## 技术特点

1. **异步处理**: 批量更新、重试、技术指标计算等耗时操作采用后台线程异步执行
2. **重试机制**: 历史数据更新支持自动重试（最多3次，每次重试超时时间递增）
3. **多线程支持**: 批量更新支持多线程并发执行，可配置并发数
4. **数据完整性**: 新闻删除时会级联删除OSS文件和跟踪记录
5. **统一响应格式**: 所有接口使用统一的JSON响应格式（code, message, data）
6. **错误处理**: 完善的异常捕获和错误日志记录
7. **数据验证**: 关键接口包含参数验证和业务逻辑校验

---

## 数据库表依赖关系

- `contracts_main` ← 合约管理模块
- `system_config` ← 系统设置模块
- `hist_{symbol}` ← 历史数据模块（动态表）
- `recommendation_log` ← 推荐记录模块
- `news_red_telegraph` ← 新闻管理模块（主表）
- `news_process_tracking` ← 新闻管理模块（跟踪表，外键关联news_red_telegraph）
- `contract_list_update_log` ← 合约管理模块
- `history_update_log` ← 历史数据模块

---

## 注意事项

1. **定时任务**: 系统设置更新后会自动重新配置定时任务
2. **数据更新**: 批量更新历史数据完成后会自动记录当日推荐
3. **文件存储**: OSS文件按月份组织目录，便于管理和清理
4. **跟踪流程**: 新闻处理流程分为两个阶段：标签校验 → 定期跟踪（3/7/14/28天）
5. **技术指标**: 历史数据更新时会自动计算MACD、RSI、KDJ、布林带等技术指标
6. **推荐算法**: 基于技术指标综合评分，生成做多/做空/观察推荐

---

*文档生成时间: 2025-01-17*
*基于代码文件: automysqlback/app.py*

