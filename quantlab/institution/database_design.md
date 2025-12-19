# 机构持仓分析数据库设计

## 设计原则

1. **按品种分表**：每个期货品种一个独立表，便于查询和管理
2. **每日一条记录**：同一品种的所有合约数据合并，按交易日存储
3. **简洁高效**：表结构简单，查询速度快
4. **时间序列**：以交易日期为主键，支持时间序列分析

---

## 核心设计思路

**每个品种一个表，表名 = 品种名称**

例如：
- `生猪` 表：存储生猪品种的每日持仓数据
- `苹果` 表：存储苹果品种的每日持仓数据
- `淀粉` 表：存储淀粉品种的每日持仓数据
- ...（共约80个品种，80个表）

**每个表的结构**：交易日期 + 4个核心字段（总多头、总空头、总多头变化、总空头变化）

---

## 数据库表结构设计

### 品种持仓表（每个品种一个表）

**表名规则**：直接使用品种名称作为表名，例如 `生猪`、`苹果`、`淀粉` 等

**表结构**（所有品种表结构相同）：

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `trade_date` | TEXT | PRIMARY KEY | 交易日期 (YYYY-MM-DD) |
| `total_buy` | INTEGER | NOT NULL | 总多头持仓（该品种所有合约的多头持仓之和） |
| `total_ss` | INTEGER | NOT NULL | 总空头持仓（该品种所有合约的空头持仓之和） |
| `total_buy_chge` | INTEGER | NOT NULL | 总多头变化（该品种所有合约的多头持仓变化之和） |
| `total_ss_chge` | INTEGER | NOT NULL | 总空头变化（该品种所有合约的空头持仓变化之和） |
| `created_at` | TEXT | - | 数据创建时间 |
| `updated_at` | TEXT | - | 数据更新时间 |

**示例表**：`生猪` 表

| trade_date | total_buy | total_ss | total_buy_chge | total_ss_chge | created_at | updated_at |
|------------|-----------|----------|----------------|---------------|------------|-------------|
| 2025-12-18 | 20543 | 35088 | -623 | 37 | 2025-12-19 10:00:00 | 2025-12-19 10:00:00 |
| 2025-12-19 | 21000 | 35200 | 457 | 112 | 2025-12-20 10:00:00 | 2025-12-20 10:00:00 |
| ... | ... | ... | ... | ... | ... | ... |

**说明**：
- 每个品种每天只有一条记录
- `trade_date` 作为主键，确保数据唯一性
- 同一品种的多个合约（如 lh2605, lh2607, lh2609 等）的数据会合并到这一条记录中
- 查询某个品种的历史数据时，直接查询对应表即可，非常高效

**索引**：
- `trade_date` 已作为主键，自动建立索引，无需额外索引

---

### 品种信息表（可选，用于管理）

**表名**：`varieties_info`

**用途**：存储所有品种的基本信息，便于管理和查询

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `variety_name` | TEXT | PRIMARY KEY | 品种名称（如：生猪、苹果） |
| `variety_family` | TEXT | - | 品种族分类（如：农副、谷物、原油） |
| `table_name` | TEXT | NOT NULL | 对应的持仓表名（通常等于variety_name） |
| `is_active` | INTEGER | DEFAULT 1 | 是否活跃（1=活跃，0=停用） |
| `created_at` | TEXT | - | 创建时间 |
| `updated_at` | TEXT | - | 更新时间 |

**说明**：
- 这个表是可选的，主要用于：
  - 记录有哪些品种
  - 品种的分类信息
  - 动态生成SQL查询时，知道要查询哪些表

---

### 3. 期货价格表（用于生成标签）

**方案A：统一价格表（推荐）**

**表名**：`futures_prices`

**用途**：存储所有品种的价格数据，用于计算目标变量（未来价格变化）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `trade_date` | TEXT | NOT NULL | 交易日期 (YYYY-MM-DD) |
| `variety_name` | TEXT | NOT NULL | 品种名称（需要与持仓表名匹配） |
| `contract_code` | TEXT | - | 主力合约代码（可选） |
| `open_price` | REAL | - | 开盘价 |
| `high_price` | REAL | - | 最高价 |
| `low_price` | REAL | - | 最低价 |
| `close_price` | REAL | NOT NULL | 收盘价 |
| `volume` | INTEGER | - | 成交量 |
| `open_interest` | INTEGER | - | 持仓量 |
| `change_pct` | REAL | - | 涨跌幅（%） |
| `created_at` | TEXT | - | 数据创建时间 |
| `updated_at` | TEXT | - | 数据更新时间 |

**唯一约束**：
- `PRIMARY KEY (trade_date, variety_name)` - 每个品种每天一条记录

**索引**：
- `(variety_name, trade_date)` - 用于按品种查询历史价格

**说明**：
- 可以从现有的 `database/futures/futures.db` 中获取数据
- 需要将合约代码映射到品种名称
- 建议使用主力合约的价格作为代表

**方案B：按品种分表（可选）**

如果价格数据量很大，也可以按品种分表，表名格式：`{variety_name}_price`

例如：`生猪_price`、`苹果_price` 等

表结构与方案A相同，只是每个品种一个独立表。

---

### 4. 标签表（用于机器学习）

**方案A：统一标签表（推荐）**

**表名**：`ml_labels`

**用途**：存储目标变量（未来价格变化），用于监督学习

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `trade_date` | TEXT | NOT NULL | 特征日期（T日） |
| `variety_name` | TEXT | NOT NULL | 品种名称 |
| `label_1d` | REAL | - | 1日后价格变化率 = (T+1日收盘价 - T日收盘价) / T日收盘价 |
| `label_3d` | REAL | - | 3日后价格变化率 |
| `label_5d` | REAL | - | 5日后价格变化率 |
| `label_10d` | REAL | - | 10日后价格变化率 |
| `label_20d` | REAL | - | 20日后价格变化率 |
| `future_price_1d` | REAL | - | T+1日收盘价（用于验证） |
| `future_price_3d` | REAL | - | T+3日收盘价 |
| `future_price_5d` | REAL | - | T+5日收盘价 |
| `future_price_10d` | REAL | - | T+10日收盘价 |
| `future_price_20d` | REAL | - | T+20日收盘价 |
| `created_at` | TEXT | - | 数据创建时间 |

**唯一约束**：
- `PRIMARY KEY (trade_date, variety_name)`

**索引**：
- `(variety_name, trade_date)` - 用于训练数据关联

**说明**：
- 标签可以从 `futures_prices` 表计算得出
- 支持多个预测周期（1日、3日、5日等）
- 可以同时训练多个模型，预测不同周期的价格变化

**方案B：按品种分表（可选）**

如果标签数据量很大，也可以按品种分表，表名格式：`{variety_name}_labels`

---

## 数据流转关系

```
API原始数据（JSON）
  ↓ 聚合（同一品种的多个合约合并）
品种持仓表（如：生猪表）
  ├─ trade_date
  ├─ total_buy
  ├─ total_ss
  ├─ total_buy_chge
  └─ total_ss_chge
  ↓ 特征工程（训练时动态计算）
  ├─ 做多强度 = total_buy / (total_buy + total_ss)
  ├─ 做空强度 = total_ss / (total_buy + total_ss)
  ├─ 单日做多强度变化 = 今日强度 - 昨日强度
  ├─ 历史均值（MA5/MA10/MA20）
  └─ 其他衍生特征
  ↓ 合并价格数据
futures_prices 表
  ↓ 计算标签
ml_labels 表
  ↓ 合并特征+标签
训练样本（用于LightGBM）
```

---

## 特征工程建议

### 核心特征（基于品种持仓表计算）

从每个品种的持仓表中，可以计算以下特征：

#### 1. 基础强度特征
- **做多强度** = `total_buy / (total_buy + total_ss)`
- **做空强度** = `total_ss / (total_buy + total_ss)`
- **净持仓强度** = `(total_buy - total_ss) / (total_buy + total_ss)`

#### 2. 单日变化特征
- **单日做多强度变化** = 今日做多强度 - 昨日做多强度
- **单日做空强度变化** = 今日做空强度 - 昨日做空强度
- **单日多头持仓变化率** = `total_buy_chge / 昨日total_buy`
- **单日空头持仓变化率** = `total_ss_chge / 昨日total_ss`

#### 3. 历史统计特征（需要查询历史数据）
- **做多强度MA5/MA10/MA20** = 过去N天的做多强度均值
- **做空强度MA5/MA10/MA20** = 过去N天的做空强度均值
- **净持仓强度MA5/MA10/MA20** = 过去N天的净持仓强度均值
- **做多强度标准差** = 过去N天的做多强度标准差
- **净持仓MA5/MA10/MA20** = 过去N天的净持仓均值

#### 4. 相对强度特征
- **做多强度相对MA5偏离度** = (今日做多强度 - MA5) / MA5
- **做多强度相对MA10偏离度** = (今日做多强度 - MA10) / MA10
- **净持仓强度相对MA5偏离度** = (今日净持仓强度 - MA5) / MA5

#### 5. 趋势特征
- **做多强度5日趋势** = 线性回归斜率（过去5天的做多强度）
- **做多强度10日趋势** = 线性回归斜率（过去10天的做多强度）
- **净持仓强度5日趋势** = 线性回归斜率（过去5天的净持仓强度）

### 特征计算方式

**建议：训练时动态计算**

1. 从品种持仓表读取历史数据（例如：过去30天）
2. 动态计算所有特征
3. 与价格表和标签表合并
4. 生成训练样本

**优点**：
- 特征工程灵活，易于迭代
- 不需要维护额外的特征表
- 存储空间小

**如果特征计算耗时**：
- 可以考虑建立特征表，表名格式：`{variety_name}_features`
- 定期更新特征值

---

## 关键设计点

### 1. 品种名称标准化
- 确保 `variety_name` 在 `variety_summary`、`futures_prices`、`ml_labels` 中保持一致
- 建议建立品种名称映射表（如果需要）

### 2. 日期处理
- 所有日期字段统一使用 `YYYY-MM-DD` 格式
- 注意处理非交易日（周末、节假日）

### 3. 缺失值处理
- 历史统计特征（MA、STD等）在数据不足时可能为NULL
- 训练时需要处理NULL值

### 4. 数据一致性
- 确保 `variety_summary` 可以从 `contracts_raw` 重新计算
- 定期校验数据一致性

---

## 特征工程建议

基于 `variety_summary` 表，可以计算以下特征：

### 核心特征（必须）
1. **做多强度** = total_buy / total_position
2. **做空强度** = total_ss / total_position
3. **净持仓强度** = net_position / total_position
4. **单日做多强度变化** = 今日做多强度 - 昨日做多强度
5. **单日做空强度变化** = 今日做空强度 - 昨日做空强度

### 扩展特征（推荐）
1. **历史均值**：过去N天的强度均值
2. **历史标准差**：过去N天的强度波动
3. **趋势**：强度的时间序列趋势（斜率）
4. **相对强度**：当前强度相对历史均值的偏离度
5. **持仓变化率**：增仓/减仓的幅度

### 特征选择
- 先用核心特征训练，观察效果
- 逐步添加扩展特征，避免过拟合
- 使用特征重要性分析（LightGBM自带）筛选有效特征

---

## 总结

### 核心表结构

**必须存储的表**：

1. ✅ **品种持仓表**（每个品种一个表）
   - 表名：品种名称（如：`生猪`、`苹果`、`淀粉`）
   - 结构：`trade_date`（主键）+ `total_buy` + `total_ss` + `total_buy_chge` + `total_ss_chge`
   - 说明：同一品种的多个合约数据合并，每天一条记录
   - 数量：约80个品种，80个表

2. ✅ **品种信息表**（可选，用于管理）
   - 表名：`varieties_info`
   - 用途：记录所有品种的基本信息和分类

3. ✅ **价格表**（统一表）
   - 表名：`futures_prices`
   - 用途：存储所有品种的价格数据，用于计算标签

4. ✅ **标签表**（统一表）
   - 表名：`ml_labels`
   - 用途：存储目标变量（未来价格变化率）

### 特征计算策略

**建议：训练时动态计算特征**

- 从品种持仓表读取历史数据
- 动态计算所有特征（强度、变化、历史统计等）
- 与价格表和标签表合并
- 生成训练样本

**优点**：
- 特征工程灵活，易于迭代
- 不需要维护额外的特征表
- 存储空间小
- 查询效率高（每个品种独立表）

### 数据存储示例

假设有3个品种：生猪、苹果、淀粉

**数据库中的表**：
```
生猪
├─ trade_date (主键)
├─ total_buy
├─ total_ss
├─ total_buy_chge
└─ total_ss_chge

苹果
├─ trade_date (主键)
├─ total_buy
├─ total_ss
├─ total_buy_chge
└─ total_ss_chge

淀粉
├─ trade_date (主键)
├─ total_buy
├─ total_ss
├─ total_buy_chge
└─ total_ss_chge

futures_prices (统一表)
├─ trade_date
├─ variety_name
└─ close_price (等价格字段)

ml_labels (统一表)
├─ trade_date
├─ variety_name
└─ label_1d, label_3d, label_5d (等标签字段)

varieties_info (可选)
├─ variety_name
└─ variety_family
```

### 查询示例

**查询生猪品种的历史持仓数据**：
```sql
SELECT * FROM 生猪 ORDER BY trade_date;
```

**查询生猪品种最近20天的数据（用于计算特征）**：
```sql
SELECT * FROM 生猪 
WHERE trade_date >= date('now', '-20 days')
ORDER BY trade_date;
```

**查询多个品种的持仓数据（用于训练）**：
```sql
-- 需要遍历所有品种表，或使用UNION ALL
SELECT '生猪' as variety_name, * FROM 生猪
UNION ALL
SELECT '苹果' as variety_name, * FROM 苹果
UNION ALL
SELECT '淀粉' as variety_name, * FROM 淀粉;
```

### 设计优势

1. **查询效率高**：每个品种独立表，查询单个品种历史数据非常快
2. **结构简单**：每个表只有5-6个字段，易于理解和管理
3. **扩展性好**：新增品种只需新建一个表
4. **数据清晰**：同一品种的所有合约数据已合并，无需额外聚合
5. **特征灵活**：训练时动态计算，便于特征工程迭代

