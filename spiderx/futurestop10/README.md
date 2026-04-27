# 📊 期货涨跌幅TOP10数据采集

## 📋 功能说明

每天自动获取中国期货市场中，**涨幅最大前5个**和**跌幅最大前5个**合约（共10个），并：
1. 筛选规则：涨幅>1%，跌幅<-1%
2. 入库到阿里云MySQL数据库（2个表）
3. 在本地SQLite创建AI分析任务
4. 交给ChatGPT Helper使用浏览器搜索工具分析市场动因

## 🎯 应用场景

辅助交易决策与复盘：
- ✅ 快速了解当天受市场关注的品种（涨跌幅>1%）
- ✅ AI通过浏览器搜索分析涨跌原因和新闻驱动
- ✅ 识别行业联动和市场情绪（区分真实事件vs市场小作文）
- ✅ 获得3-10天短线交易评分建议（1-10分）
- ✅ 发现交易机会和风险点

## 📊 数据库结构（双数据库架构）

### 🔄 数据库分布

- **阿里云MySQL**: `news_red_telegraph` + `news_process_tracking`（远程存储）
- **本地SQLite**: `analysis_task`（位于 `spiderx/db/crawler.db`）

### 1. news_red_telegraph 表 ⭐ MySQL（阿里云）
存储期货涨跌TOP10统计数据

| 字段 | 说明 |
|------|------|
| ctime | 入库时间戳（秒级） |
| title | 标题（含年月日） |
| content | 涨跌幅TOP10详细数据（格式化文本） |
| ai_analysis | AI分析结果（默认：暂无分析） |
| message_type | 消息类型：每日涨跌TOP5统计 |
| message_label | 消息标签：hard |
| message_score | 消息评分：6 |
| market_react | 市场反应（默认：NULL） |

### 2. news_process_tracking 表 ⭐ MySQL（阿里云）
跟踪数据处理状态

| 字段 | 说明 |
|------|------|
| news_id | 关联news_red_telegraph表的id |
| ctime | 消息创建时间戳（秒级） |
| is_reviewed | 是否已审核（默认：0） |

### 3. analysis_task 表 ⭐ SQLite（本地）
AI分析任务（位于 `spiderx/db/crawler.db`）

| 字段 | 说明 |
|------|------|
| title | 任务标题（含"分析"后缀） |
| prompt | AI分析提示词（包含新闻搜索要求） |
| news_time | 新闻时间（格式：YYYY-MM-DD HH:MM:SS） |
| gemini_analyzed | 是否需要Gemini分析（1=跳过Gemini） |

## ⏰ 定时任务

**执行时间**: 每周一到周五 16:00（期货收盘后）
**执行条件**: 仅在期货交易日执行

## 🚀 使用方法

### 1. 安装依赖

```bash
cd spiderx/futurestop10
pip install -r requirements.txt
```

### 2. 测试运行

```bash
# 手动执行一次，测试功能
# 如果本地数据库不存在会自动初始化
python main.py
```

> 💡 **提示**: 本地SQLite数据库（`spiderx/db/crawler.db`）不存在时会自动初始化，无需手动操作

### 3. 启动定时任务

```bash
# 启动调度器
chmod +x start_scheduler.sh
./start_scheduler.sh
```

### 4. 查看日志

```bash
# 查看调度器日志
tail -f scheduler.log

# 查看标准输出
tail -f nohup.out
```

### 5. 停止任务

```bash
# 停止调度器
chmod +x stop_scheduler.sh
./stop_scheduler.sh
```

## 📝 输出示例

```
==================================================
【涨幅TOP5】（涨幅>1%）
==================================================
1. jm2605       | 价格:       1064.5 | 涨幅: +4.72%
2. ao2601       | 价格:       2552.0 | 涨幅: +3.32%
3. sh2603       | 价格:       2179.0 | 涨幅: +3.27%
4. j2601        | 价格:       1508.5 | 涨幅: +2.27%
5. v2601        | 价格:       4315.0 | 涨幅: +2.25%

==================================================
【跌幅TOP5】（跌幅<-1%）
==================================================
1. ag2602       | 价格:      14437.0 | 跌幅: -3.06%
2. bc2601       | 价格:      81910.0 | 跌幅: -3.05%
3. cu2601       | 价格:      91550.0 | 跌幅: -2.69%
4. al2602       | 价格:      21775.0 | 跌幅: -1.78%
5. zn2601       | 价格:      23305.0 | 跌幅: -1.27%
```

## 🔧 配置说明

### 数据库配置（双数据库）


#### SQLite配置（本地）
位于 `main.py` 中的 `SQLITE_DB_PATH`：

```python
SQLITE_DB_PATH = Path(__file__).parent.parent / "db" / "crawler.db"
# 实际路径: spiderx/db/crawler.db
```

### 定时任务配置
位于 `scheduler.py` 中：

```python
scheduler.add_job(
    futures_top10_task,
    'cron',
    day_of_week='mon-fri',  # 周一到周五
    hour=16,                 # 16点（下午4点）
    minute=0
)
```

## ⚠️ 注意事项

1. **数据库自动初始化**: 本地SQLite数据库不存在时会自动初始化（调用`spiderx/db/init_db.py`）
2. **双数据库架构**: 
   - MySQL（阿里云）：存储涨跌幅数据和处理状态
   - SQLite（本地）：存储AI分析任务
3. **交易日判断**: 目前仅排除周末（周一到周五执行），未排除法定节假日
4. **数据去重**: 通过`ctime`字段（时间戳）保证同一时间只入库一次
5. **Cookie有效期**: API请求的Cookie可能需要定期更新
6. **网络稳定性**: 确保服务器能访问：
   - API接口（jiaoyikecha.com）
   - 阿里云MySQL数据库
7. **AI分析配置**: `gemini_analyzed=1`表示跳过Gemini，由ChatGPT Helper处理

## 📦 文件说明

```
spiderx/futurestop10/
├── main.py                 # 主程序：数据获取和入库
├── scheduler.py            # 定时任务调度器
├── start_scheduler.sh      # 启动脚本
├── stop_scheduler.sh       # 停止脚本
├── requirements.txt        # Python依赖
├── scheduler.log           # 调度器日志
├── scheduler.pid           # 进程ID文件
└── README.md              # 本文档
```

## 🔄 AI分析流程

1. **数据采集**: 调度器定时获取涨跌幅数据
2. **数据入库**: 写入MySQL的2个表（`news_red_telegraph`、`news_process_tracking`）
3. **任务创建**: 在SQLite的`analysis_task`表创建AI分析任务
4. **AI分析**: ChatGPT Helper读取任务并使用浏览器搜索工具进行市场分析
5. **结果保存**: 分析结果写回数据库

> 💡 **说明**: `gemini_analyzed=1` 表示跳过Gemini分析，由ChatGPT Helper处理

## 📈 数据流转

```
API接口 (jiaoyikecha.com)
   │
   ▼
获取原始数据（SSE流式）
   │
   ▼
筛选TOP10（涨幅>1%取前5，跌幅<-1%取前5）
   │
   ├──► 阿里云MySQL (futures数据库)
   │     ├── news_red_telegraph（涨跌幅数据 + 格式化内容）
   │     └── news_process_tracking（处理状态跟踪）
   │
   └──► 本地SQLite (spiderx/db/crawler.db)
         └── analysis_task（AI分析任务）
                  │    ↑
                  │    └── gemini_analyzed=1（跳过Gemini）
                  ▼
             ChatGPT Helper
             ├── 使用浏览器搜索工具
             ├── 查询相关新闻
             ├── 分析驱动因素
             └── 生成交易评分
```


