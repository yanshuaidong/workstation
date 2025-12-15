# 期货单边行情识别与机器学习策略

基于传统机器学习（LightGBM）的期货单边行情识别与交易策略系统。

---

## 📁 项目结构

```
quantlab/
├── futures_trend_ml.py    # 主程序代码
├── 量化单边行情设计.md      # 设计文档
├── README.md              # 本说明文档
├── models/                # 模型保存目录（运行后生成）
│   ├── long_model_lgbm.pkl
│   └── short_model_lgbm.pkl
└── output/                # 输出目录（运行后生成）
    └── equity_curve.png
```

---

## 🚀 快速开始

### 1. 环境依赖

```bash
pip install pandas numpy scikit-learn lightgbm matplotlib joblib
```

**注意**：如果无法安装 LightGBM，程序会自动使用 `sklearn.ensemble.GradientBoostingClassifier` 替代。

### 2. 运行程序

```bash
cd quantlab
python futures_trend_ml.py
```

### 3. 数据要求

程序默认读取 `../database/futures/futures.db` SQLite 数据库。

数据库结构详见 `database/futures/README.md`。

---

## 📊 核心功能

### 1. 数据读取与整合

- 从 `contracts_main` 表读取所有活跃合约
- 遍历各合约的 `hist_{symbol}` 历史数据表
- 统一字段名称，合并为总 DataFrame
- 自动剔除数据量不足（< 250 交易日）的品种

### 2. 单边行情识别

**识别逻辑**：

- 窗口长度：3-10 个交易日
- 使用 ATR 自适应阈值判断趋势强度
- 限制最大逆向波动（回撤/反弹）
- 通过评分机制去除重叠段，保留高质量趋势

**阶段划分**：

将每个单边行情段按累计涨跌幅切分为：
- **前段** (0-33%)：趋势启动期
- **中段** (33-66%)：趋势延续期
- **后段** (66-100%)：趋势末期

### 3. 标签定义

| 标签值 | 含义 |
|-------|------|
| +1 | 上涨单边段的前/中段（做多信号） |
| -1 | 下跌单边段的前/中段（做空信号） |
| 0 | 其他（包括后段和非趋势期） |

### 4. 特征工程

共生成 **19 个特征**，全部使用历史数据，无未来信息泄露：

| 类别 | 特征 |
|-----|------|
| 价格动量 | feat_ret_3, feat_ret_5, feat_ret_10 |
| 突破指标 | feat_price_pos_20, feat_break_high_20, feat_break_low_20 |
| 均线趋势 | feat_ma_5_20_diff, feat_ma_5_20_ratio |
| 趋势拟合 | feat_trend_slope_10, feat_trend_r2_10 |
| 波动率 | feat_atr_20, feat_vol_5, feat_vol_20, feat_vol_ratio_5_20 |
| 成交量 | feat_vol_ratio |
| 持仓量 | feat_oi_ratio, feat_oi_chg_1, feat_oi_chg_3, feat_oi_chg_rate_3 |
| K线形态 | feat_close_pos_in_bar |

**预热期**：前 60 个交易日用于计算滚动指标，从第 61 日开始生成有效样本。

### 5. 数据集划分

采用**固定年份划分**（时间序列严格有序）：

| 数据集 | 时间范围 | 占比 |
|-------|---------|-----|
| 训练集 | 2018-01 ~ 2022-12 | ~71% |
| 验证集 | 2023-01 ~ 2023-12 | ~14% |
| 测试集 | 2024-01 ~ 2024-12 | ~14% |

### 6. 模型训练

**LightGBM 分类器**：

- 分别训练多头模型和空头模型
- 使用 `scale_pos_weight` 处理样本不平衡
- 验证集早停（early_stopping_rounds=50）
- 评估指标：AUC、Accuracy、Precision、Recall

**默认超参数**：

```python
{
    'num_leaves': 31,
    'max_depth': 6,
    'learning_rate': 0.05,
    'n_estimators': 500,
    'subsample': 0.8,
    'colsample_bytree': 0.8
}
```

### 7. 策略回测

**简单多头策略**：

- **开仓条件**：p_long > 0.6（多头概率超过阈值）
- **平仓条件**：
  - 持仓超过 10 天
  - 回撤超过 2 × ATR（止损）
- **费率**：双边 0.03%

**回测输出**：
- 总交易次数
- 胜率
- 平均单笔收益
- 累计收益 / 年化收益
- 最大回撤
- 净值曲线图

---

## 📈 输出示例

```
==================================================
期货单边行情识别与机器学习策略
==================================================

[数据加载] 发现 76 个活跃合约
[数据加载] 成功加载 52 个品种
[数据加载] 数据日期范围: 2018-01-02 ~ 2024-12-31
[数据加载] 总样本数: 85,000+

[标签生成] 共识别 2,500+ 个单边行情段
[标签生成] 标签分布:
  - label=-1 (空头信号): 12,000+ (14%)
  - label=0  (无信号):   60,000+ (72%)
  - label=+1 (多头信号): 13,000+ (14%)

[模型训练] 验证集评估:
  - AUC:       0.65+
  - Accuracy:  0.85+
  - Precision: 0.30+
  - Recall:    0.25+

==================================================
回测结果汇总
==================================================
总交易次数: 200+
胜率: 45%+
平均单笔收益: 0.5%+
年化收益: 15%+
最大回撤: 8%
```

---

## 🔧 自定义配置

### 修改识别参数

在 `identify_trend_segments()` 函数中调整：

```python
k1 = 2.0              # ATR 倍数阈值（越大越严格）
max_reverse_ratio = 0.4  # 最大逆向波动比例
min_length = 3        # 最小行情长度
max_length = 10       # 最大行情长度
```

### 修改回测参数

在 `simple_backtest()` 函数中调整：

```python
threshold_long = 0.6      # 开仓概率阈值
max_holding_days = 10     # 最大持仓天数
stop_loss_atr_mult = 2.0  # 止损 ATR 倍数
fee_rate = 0.0003         # 手续费率
```

---

## 📝 API 参考

### 主要函数

| 函数 | 功能 |
|-----|------|
| `load_history_from_db(db_path)` | 从数据库加载历史数据 |
| `assign_labels(df_all)` | 识别单边行情并打标签 |
| `make_features(df)` | 生成特征 |
| `split_data_by_year(df)` | 按年份划分数据集 |
| `train_long_model(...)` | 训练多头模型 |
| `train_short_model(...)` | 训练空头模型 |
| `predict_proba(df, model, cols)` | 预测概率 |
| `simple_backtest(...)` | 简单策略回测 |

---

## ⚠️ 注意事项

1. **禁止使用深度学习框架**：本项目只使用传统机器学习（LightGBM/sklearn）
2. **时间序列数据**：必须按时间顺序划分数据集，禁止随机打乱
3. **特征泄露**：所有特征只使用过去信息，不会引入未来数据
4. **回测局限**：简化回测未考虑流动性、滑点等真实交易因素
5. **数据质量**：部分品种数据较短（如氧化铝 374 条），已自动剔除

---

## 📄 许可证

本项目仅供学习研究使用，不构成任何投资建议。

