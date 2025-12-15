# 期货数据库表结构说明

本文档描述 `futures.db` SQLite 数据库的表结构设计。

---

## 📋 表概览

| 表名 | 说明 | 记录特点 |
|------|------|----------|
| `contracts_main` | 期货合约主表 | 每个合约一条记录 |
| `hist_{symbol}` | 合约历史行情表 | 每个交易日一条记录 |

---

## 1. contracts_main - 期货合约主表

存储所有期货合约的基本信息。

### 表结构

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `symbol` | TEXT | PRIMARY KEY | 合约代码（如 AU0, CU0） |
| `name` | TEXT | NOT NULL | 合约名称（如 沪金主连） |
| `exchange` | TEXT | - | 交易所代码（如 SHFE, DCE） |
| `is_active` | INTEGER | DEFAULT 1 | 是否活跃（1=活跃, 0=非活跃） |
| `created_at` | TEXT | - | 创建时间 |
| `updated_at` | TEXT | - | 更新时间 |


---

## 2. hist_{symbol} - 历史行情数据表

为每个合约创建独立的历史数据表，表名格式为 `hist_` + 合约代码小写（如 `hist_aum`）。

### 表结构

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `trade_date` | TEXT | PRIMARY KEY | 交易日期（YYYY-MM-DD） |

#### 价格数据

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `open_price` | REAL | 开盘价 |
| `high_price` | REAL | 最高价 |
| `low_price` | REAL | 最低价 |
| `close_price` | REAL | 收盘价 |
| `volume` | INTEGER | 成交量（手） |
| `open_interest` | INTEGER | 持仓量（手） |
| `source_ts` | TEXT | 数据源时间戳 |
| `ingest_ts` | TEXT | 数据入库时间戳 |


---

## 📝 备注

1. **表名命名规则**: 历史数据表名统一使用小写，格式为 `hist_{symbol小写}`
2. **时间格式**: 所有时间字段存储为 TEXT 类型，格式为 `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`
3. **数值精度**: 价格类字段使用 REAL 类型（双精度浮点）
4. **主键设计**: 
   - `contracts_main` 使用 `symbol` 作为主键
   - `hist_*` 表使用 `trade_date` 作为主键
5. **SQLite优化**: 数据库启用 WAL 模式和 NORMAL 同步级别以提高性能


使用方法：
# 查看所有品种的数据状态
python update.py --status

# 预览模式（不实际更新）
python update.py --dry-run

# 更新所有品种
python update.py

# 只更新指定品种
python update.py --symbol aum,cum,rbm
