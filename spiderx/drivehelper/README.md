# 📊 期货市场事件驱动筛选器

## 📋 功能说明

每天自动筛选中国期货市场中**技术面异动明显**的合约，用于突发事件驱动交易策略：

### 筛选规则：

1. **涨幅榜**：涨幅>1% 的品种，取涨幅最大的前8个，再从中筛选**放量且增仓**的
2. **跌幅榜**：跌幅<-1% 的品种，取跌幅最大的前8个，再从中筛选**放量且增仓**的

### 技术指标定义：

- **放量**：今日成交量 > 昨日成交量
- **增仓**：今日持仓量 > 昨日持仓量

### 输出结果：

- 为每个符合条件的品种生成AI分析提示词
- 任务统一入库到本地SQLite数据库（`spiderx/db/crawler.db`）
- 交给AI助手（ChatGPT/Gemini/Doubao）分析当日突发事件和交易机会

## 🎯 应用场景

用于**事件驱动短线交易策略**：

- ✅ 自动发现技术面异动品种（涨跌幅>1%且放量增仓）
- ✅ AI搜索当日相关突发事件或重要消息
- ✅ 分析事件对价格的影响和持续性
- ✅ 辅助制定3-10天的短线交易计划
- ✅ 识别市场热点和联动效应

## 📊 数据库结构

### 数据来源（MySQL - 阿里云）

从阿里云MySQL的`futures`数据库读取期货历史数据：

- **表名格式**：`hist_<品种代码>`（如：`hist_cu`、`hist_ag`）
- **查询字段**：
  - `trade_date`：交易日期
  - `close_price`：收盘价
  - `change_pct`：涨跌幅（%）
  - `volume`：成交量
  - `open_interest`：持仓量

### 数据输出（SQLite - 本地）

将AI分析任务保存到本地SQLite数据库：

- **数据库路径**：`spiderx/db/crawler.db`
- **表名**：`analysis_task`

**字段说明**：

| 字段 | 说明 |
|------|------|
| title | 任务标题（含日期和品种数量） |
| prompt | AI分析提示词（包含品种信息和技术指标） |
| news_time | 任务创建时间（格式：YYYY-MM-DD HH:MM:SS） |
| gemini_analyzed | 是否已被Gemini分析（0=未分析） |
| chatgpt_analyzed | 是否已被ChatGPT分析（0=未分析） |
| doubao_analyzed | 是否已被豆包分析（0=未分析） |

## ⏰ 定时任务

**执行时间**：每周一到周五 17:40（期货收盘后）  
**执行条件**：仅在期货交易日执行  
**运行周期**：运行40天（约28-30个交易日）

## 🚀 使用方法

### 1. 安装依赖

```bash
cd spiderx/drivehelper
pip install -r requirements.txt
```

### 2. 测试运行

```bash
# 手动执行一次，测试功能
# 如果本地数据库不存在会自动初始化
python main.py
```

> 💡 **提示**：本地SQLite数据库（`spiderx/db/crawler.db`）不存在时会自动初始化，无需手动操作

### 3. 启动定时任务

```bash
# 启动调度器
chmod +x start_scheduler.sh
./start_scheduler.sh
```

### 4. 查看日志

```bash
# 查看调度器日志
tail -f logs/drivehelper_$(date +%Y-%m).log

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
【事件驱动筛选结果】
日期: 2026-02-08 17:40:15
总合约数: 63
涨幅>1%: 12 个 → 前8: 8 个 → 放量增仓: 3 个
跌幅<-1%: 8 个 → 前8: 8 个 → 放量增仓: 2 个

==================================================
【做多候选】涨幅榜前8 + 放量 + 增仓
--------------------------------------------------
1. 焦煤(JM)
   涨幅: +4.72% | 价格: 1064.5
   放量: +23.5% | 增仓: +12.8%

2. 氧化铝(AO)
   涨幅: +3.32% | 价格: 2552.0
   放量: +18.2% | 增仓: +8.5%

==================================================
【做空候选】跌幅榜前8 + 放量 + 增仓
--------------------------------------------------
1. 白银(AG)
   跌幅: -3.06% | 价格: 14437.0
   放量: +15.3% | 增仓: +6.2%
```

## 🔧 配置说明

### MySQL数据库配置（阿里云）

位于 `main.py` 中的 `MYSQL_CONFIG`：

```python
MYSQL_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}
```

### SQLite数据库配置（本地）

位于 `main.py` 中的 `SQLITE_DB_PATH`：

```python
SQLITE_DB_PATH = Path(__file__).parent.parent / "db" / "crawler.db"
# 实际路径: spiderx/db/crawler.db
```

### 品种名称映射

使用 `spiderx/futurestop10/contracts_main.json` 文件：

```python
CONTRACTS_JSON_PATH = Path(__file__).parent.parent / "futurestop10" / "contracts_main.json"
```

该文件提供了期货品种代码到中文名称的映射（如：`cu` → 铜，`ag` → 白银）。

### 定时任务配置

位于 `scheduler.py` 中：

```python
self.execution_hour = 17      # 下午5点
self.execution_minute = 40    # 40分
self.end_time = self.start_time + timedelta(days=40)  # 运行40天
self.max_executions = 30      # 最多执行30次
```

## ⚠️ 注意事项

1. **数据库自动初始化**：本地SQLite数据库不存在时会自动初始化（调用`spiderx/db/init_db.py`）
2. **数据依赖**：
   - 依赖阿里云MySQL的`hist_*`表（期货历史数据）
   - 依赖`contracts_main.json`文件（品种名称映射）
3. **交易日判断**：目前仅排除周末（周一到周五执行），未排除法定节假日
4. **筛选逻辑**：
   - 先按涨跌幅筛选（>1%或<-1%）
   - 再取涨跌幅榜前8
   - 最后在前8中筛选放量且增仓的
5. **任务生成**：只有当有符合条件的品种时才会创建AI分析任务
6. **网络稳定性**：确保服务器能访问阿里云MySQL数据库

## 📦 文件说明

```
spiderx/drivehelper/
├── main.py                 # 主程序：数据筛选和任务生成
├── scheduler.py            # 定时任务调度器
├── start_scheduler.sh      # 启动脚本
├── stop_scheduler.sh       # 停止脚本
├── start.sh                # 手动执行脚本（单次运行）
├── requirements.txt        # Python依赖
├── logs/                   # 日志目录（自动创建）
│   └── drivehelper_YYYY-MM.log  # 按月轮转的日志文件
├── scheduler.pid           # 调度器进程ID文件（运行时）
├── nohup.out               # 标准输出日志
└── README.md              # 本文档
```

## 🔄 AI分析流程

1. **数据筛选**：调度器定时执行筛选任务（17:40）
2. **任务生成**：为符合条件的品种生成AI分析提示词
3. **任务入库**：写入SQLite的`analysis_task`表
4. **AI分析**：AI助手读取任务并分析：
   - 搜索当日相关新闻和突发事件
   - 分析技术面异动的原因
   - 评估事件驱动的持续性
   - 给出短线交易建议
5. **标记完成**：分析完成后更新对应的`*_analyzed`字段

## 📈 筛选策略说明

### 为什么要"放量增仓"？

- **放量**：表示市场关注度提升，资金参与度高
- **增仓**：表示主力资金介入，不是纯粹投机
- **涨跌幅>1%**：过滤掉正常波动，聚焦异动品种
- **取前8**：聚焦涨跌幅最大的品种，市场动因更明显

### 典型应用场景：

1. **突发事件**：政策变化、供需冲击、产区天气等
2. **行业联动**：上下游产业链共振（如：原油→化工品）
3. **资金轮动**：热点板块切换（如：有色金属集体拉升）
4. **市场情绪**：恐慌性抛售或追涨（需AI辨别真实性）

## 🔗 相关项目

- **期货涨跌幅TOP10采集器**：`spiderx/futurestop10/`（采集涨跌幅数据）
- **AI分析助手**：
  - ChatGPT Helper
  - Gemini Helper
  - Doubao Helper

## 📄 依赖版本

```
pymysql>=1.1.0
```

Python版本要求：Python 3.7+
