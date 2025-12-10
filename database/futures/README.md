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

### 示例数据

```
symbol | name     | exchange | is_active | created_at          | updated_at
-------|----------|----------|-----------|---------------------|---------------------
AU0    | 沪金主连  | SHFE     | 1         | 2024-01-01 00:00:00 | 2024-11-30 12:00:00
CU0    | 沪铜主连  | SHFE     | 1         | 2024-01-01 00:00:00 | 2024-11-30 12:00:00
```

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
| `price_change` | REAL | 价格变化（涨跌额） |
| `change_pct` | REAL | 涨跌幅（%） |

#### 成交数据

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `volume` | INTEGER | 成交量（手） |
| `open_interest` | INTEGER | 持仓量（手） |
| `turnover` | REAL | 成交额（元） |

#### 技术指标 - MACD

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `macd_dif` | REAL | DIF 快线（12日EMA - 26日EMA） |
| `macd_dea` | REAL | DEA 慢线（DIF的9日EMA） |
| `macd_histogram` | REAL | MACD柱状图（DIF - DEA） |

#### 技术指标 - RSI

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `rsi_14` | REAL | 14日相对强弱指数 |

#### 技术指标 - KDJ

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `kdj_k` | REAL | K值（快速随机指标） |
| `kdj_d` | REAL | D值（K值的3日移动平均） |
| `kdj_j` | REAL | J值（3K - 2D） |

#### 技术指标 - 布林带 (Bollinger Bands)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `bb_upper` | REAL | 上轨（中轨 + 2倍标准差） |
| `bb_middle` | REAL | 中轨（20日移动平均线） |
| `bb_lower` | REAL | 下轨（中轨 - 2倍标准差） |
| `bb_width` | REAL | 带宽（(上轨-下轨)/中轨） |

#### 其他字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `recommendation` | TEXT | 交易建议/推荐 |
| `source_ts` | TEXT | 数据源时间戳 |
| `ingest_ts` | TEXT | 数据入库时间戳 |

### 示例数据

```
trade_date | open_price | high_price | low_price | close_price | volume  | change_pct
-----------|------------|------------|-----------|-------------|---------|------------
2024-11-29 | 610.50     | 615.20     | 608.30    | 614.80      | 125680  | 0.85
2024-11-28 | 608.20     | 612.00     | 605.50    | 610.00      | 118320  | 0.32
```

---

## 📊 表关系图

```
┌─────────────────────┐
│   contracts_main    │
├─────────────────────┤
│ symbol (PK)         │──────┐
│ name                │      │
│ exchange            │      │
│ is_active           │      │
│ created_at          │      │    ┌───────────────────────┐
│ updated_at          │      │    │     hist_{symbol}      │
└─────────────────────┘      │    ├───────────────────────┤
                             └───>│ trade_date (PK)       │
                                  │ open_price            │
                                  │ high_price            │
                                  │ low_price             │
                                  │ close_price           │
                                  │ volume                │
                                  │ open_interest         │
                                  │ ...技术指标...         │
                                  │ recommendation        │
                                  └───────────────────────┘
```

---

## 📝 备注

1. **表名命名规则**: 历史数据表名统一使用小写，格式为 `hist_{symbol小写}`
2. **时间格式**: 所有时间字段存储为 TEXT 类型，格式为 `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`
3. **数值精度**: 价格类字段使用 REAL 类型（双精度浮点）
4. **主键设计**: 
   - `contracts_main` 使用 `symbol` 作为主键
   - `hist_*` 表使用 `trade_date` 作为主键
5. **SQLite优化**: 数据库启用 WAL 模式和 NORMAL 同步级别以提高性能
