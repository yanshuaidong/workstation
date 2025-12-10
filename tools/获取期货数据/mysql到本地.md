# 期货数据 MySQL → SQLite 同步计划

从阿里云 MySQL 同步到本地 SQLite

数据库：futures

---

## 一、需要同步的表

### 1. 合约列表表（contracts_main）

| 字段 | 类型 | 说明 |
|------|------|------|
| symbol | VARCHAR(20) | 合约代码（主键）|
| name | VARCHAR(50) | 合约中文名称 |
| exchange | VARCHAR(20) | 交易所 |
| is_active | TINYINT(1) | 是否激活 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 2. 合约历史数据表（hist_{symbol}）

每个合约有独立的历史数据表，表名格式：`hist_` + 合约代码（如 `hist_AU0`、`hist_CU0`）

| 字段 | 类型 | 说明 |
|------|------|------|
| trade_date | DATE | 交易日期（主键）|
| open_price | DECIMAL(10,2) | 开盘价 |
| high_price | DECIMAL(10,2) | 最高价 |
| low_price | DECIMAL(10,2) | 最低价 |
| close_price | DECIMAL(10,2) | 收盘价 |
| volume | BIGINT | 成交量 |
| open_interest | BIGINT | 持仓量 |
| turnover | DECIMAL(20,2) | 成交额 |
| price_change | DECIMAL(10,2) | 涨跌 |
| change_pct | DECIMAL(10,2) | 涨跌幅 |
| macd_dif | DECIMAL(10,4) | MACD快线 |
| macd_dea | DECIMAL(10,4) | MACD慢线 |
| macd_histogram | DECIMAL(10,4) | MACD柱状图 |
| rsi_14 | DECIMAL(6,2) | RSI(14) |
| kdj_k | DECIMAL(6,2) | KDJ-K值 |
| kdj_d | DECIMAL(6,2) | KDJ-D值 |
| kdj_j | DECIMAL(6,2) | KDJ-J值 |
| bb_upper | DECIMAL(10,2) | 布林带上轨 |
| bb_middle | DECIMAL(10,2) | 布林带中轨 |
| bb_lower | DECIMAL(10,2) | 布林带下轨 |
| bb_width | DECIMAL(10,2) | 布林带宽度 |
| recommendation | VARCHAR(20) | 推荐操作 |
| source_ts | TIMESTAMP | 数据源时间戳 |
| ingest_ts | TIMESTAMP | 入库时间戳 |

### 3. 推荐记录表（recommendation_log）（可选）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 自增主键 |
| date | DATE | 日期（唯一索引）|
| long_names | TEXT | 做多品种列表 |
| short_names | TEXT | 做空品种列表 |
| total_long_count | INT | 做多数量 |
| total_short_count | INT | 做空数量 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

---

## 二、同步方案

### 2.1 同步策略

```
┌─────────────────────────────────────────────────────────────┐
│                    同步流程                                  │
├─────────────────────────────────────────────────────────────┤
│  1. 连接阿里云 MySQL                                         │
│         ↓                                                    │
│  2. 读取 contracts_main 表，获取所有合约列表                   │
│         ↓                                                    │
│  3. 遍历每个合约，查询对应的 hist_{symbol} 表                  │
│         ↓                                                    │
│  4. 写入本地 SQLite 数据库                                    │
│         ↓                                                    │
│  5. 记录同步状态和时间戳                                       │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 增量同步 vs 全量同步

| 模式 | 适用场景 | 说明 |
|------|---------|------|
| 全量同步 | 首次同步 | 删除本地数据，完整复制 MySQL 数据 |
| 增量同步 | 日常更新 | 只同步新增/修改的数据（按 trade_date 判断）|

---

## 三、实现步骤

### 步骤 1：创建 SQLite 数据库结构

- [ ] 创建 `futures.db` 数据库文件
- [ ] 创建 `contracts_main` 表
- [ ] 动态创建 `hist_{symbol}` 表（根据合约列表）
- [ ] 创建 `sync_log` 表（记录同步日志）

### 步骤 2：实现同步脚本

- [ ] 连接 MySQL（使用 pymysql）
- [ ] 连接 SQLite（使用 sqlite3）
- [ ] 同步合约列表：`contracts_main`
- [ ] 遍历同步历史数据：`hist_{symbol}`
- [ ] 支持增量/全量同步模式
- [ ] 添加进度显示和日志输出

### 步骤 3：命令行接口

```bash
# 全量同步
python mysql_to_sqlite.py --mode full

# 增量同步（默认最近7天）
python mysql_to_sqlite.py --mode incremental

# 增量同步（指定日期范围）
python mysql_to_sqlite.py --mode incremental --start-date 2024-01-01 --end-date 2024-12-01

# 只同步合约列表
python mysql_to_sqlite.py --mode contracts-only

# 同步指定合约
python mysql_to_sqlite.py --symbol AU0,CU0,AG0
```

---

## 四、输出文件

```
database/futures/
├── README.md              # 本文档
├── mysql_to_sqlite.py     # 同步脚本
├── futures.db             # SQLite 数据库文件（同步后生成）
└── sync.log               # 同步日志
```

---

## 五、预估数据量

| 数据类型 | 预估记录数 | 说明 |
|----------|-----------|------|
| 合约数量 | ~60个 | 主连合约（排除低成交量品种）|
| 每合约历史数据 | ~2000条 | 约8年日线数据 |
| 总历史数据 | ~120,000条 | 60个合约 × 2000条 |
| SQLite 文件大小 | ~30-50 MB | 估算 |

---

## 六、MySQL 连接配置

需要从 automysqlback 项目获取数据库连接配置：

```python
DB_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}
```

---

## 七、待确认事项

请确认以下问题：

1. **同步频率**：每天定时同步？还是手动触发？
2. **数据范围**：是否需要同步全部历史数据？还是只同步最近N天？
3. **推荐记录表**：是否需要同步 `recommendation_log` 表？
4. **其他表**：是否需要同步 `history_update_log`、`contract_list_update_log` 等日志表？

---

## 八、下一步行动

确认计划后，我将：

1. 创建 `mysql_to_sqlite.py` 同步脚本
2. 实现完整的同步功能
3. 测试并验证数据完整性
