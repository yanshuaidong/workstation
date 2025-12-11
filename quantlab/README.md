# 传统短线趋势策略研究体系

基于 Backtrader 搭建的可复用短线趋势策略研究体系，包含 4 个经典策略族 + 组合风控 + 研究流程。

## 目录结构

```
quantlab/
├── core/                   # 通用模块
│   ├── __init__.py
│   ├── data_loader.py      # 数据加载器（从 futures.db 读取）
│   ├── backtest.py         # Backtrader 回测封装
│   ├── metrics.py          # 绩效指标计算
│   └── portfolio.py        # 组合风控
│
├── strategies/             # 策略族定义
│   ├── __init__.py
│   ├── breakout.py         # 短周期突破族
│   ├── ma_trend.py         # 均线趋势族
│   ├── momentum.py         # 动量持有族
│   ├── atr_channel.py      # ATR 通道族
│   └── vol_oi_breakout.py  # 增仓放量突破族（期货专用）
│
├── research/               # 研究结果输出
│   ├── experiments/        # 实验记录
│   └── results/            # 回测结果（csv、图表）
│
├── notebooks/              # Jupyter 探索分析
│
├── example_run.py          # 快速开始示例
├── param_optimize.py       # 参数优化脚本
├── requirements.txt        # 依赖
└── README.md               # 本文档
```

## 快速开始

### 1. 安装依赖

```bash
cd quantlab
pip install -r requirements.txt
```

### 2. 查看可用品种

```bash
python example_run.py --list
```

### 3. 单品种回测

```bash
# 默认使用螺纹钢 + 突破策略
python example_run.py

# 指定品种和策略
python example_run.py -s cum -t ma      # 铜 + 均线策略
python example_run.py -s aum -t momentum  # 黄金 + 动量策略
python example_run.py -s scm -t atr     # 原油 + ATR通道策略
python example_run.py -s rbm -t voloi   # 螺纹 + 增仓放量突破策略
```

### 4. 检查数据

```bash
python example_run.py -s rbm --check
```

### 5. 多品种测试

```bash
python example_run.py --multi -t breakout
```

### 6. 参数优化

```bash
# 优化单个策略
python param_optimize.py -s rbm -t breakout

# 优化所有策略
python param_optimize.py -s rbm -t all

# 全品种 + 全策略（自动跑训练期2018-2021 + 验证期2022-2023）
python param_optimize.py --all-symbols -t all

# 全品种 + 单个策略
python param_optimize.py --all-symbols -t breakout    # 只跑突破策略
python param_optimize.py --all-symbols -t ma          # 只跑均线策略
python param_optimize.py --all-symbols -t momentum    # 只跑动量策略
python param_optimize.py --all-symbols -t atr         # 只跑ATR策略
python param_optimize.py --all-symbols -t voloi       # 只跑增仓放量突破策略

# 调整数据过滤阈值（默认需要至少500条数据）
python param_optimize.py --all-symbols -t all --min-bars 300
```

## 策略说明

### 1. 短周期突破策略 (ShortTermBreakout)

**核心理念**：Donchian 突破的短周期版本，捕捉 3-10 日单边走势。

| 参数 | 说明 | 推荐范围 |
|------|------|----------|
| n_high | 突破周期 | 3, 5, 7, 10 |
| n_low | 平仓周期 | 3, 5 |
| max_hold | 最大持有天数 | 5, 7, 10 |
| stop_atr_mult | 止损 ATR 倍数 | 1.5, 2, 2.5 |

### 2. 短周期均线趋势策略 (ShortTermMATrend)

**核心理念**：短均线跟随，适合 3-10 日趋势。

| 参数 | 说明 | 推荐范围 |
|------|------|----------|
| ma_short | 短期均线周期 | 3, 4, 5 |
| ma_long | 长期均线周期 | 8, 10, 12, 15 |
| max_hold | 最大持有天数 | 5, 7, 10 |
| stop_atr_mult | 止损 ATR 倍数 | 1.5, 2, 2.5 |

### 3. 动量固定持有策略 (MomentumFixHold)

**核心理念**：用最近 N 日累计涨幅判断趋势，固定持有 3-10 日。

| 参数 | 说明 | 推荐范围 |
|------|------|----------|
| lookback | 动量回看周期 | 3, 5, 7 |
| threshold | 入场阈值 | 1%, 2%, 3% |
| hold_days | 固定持有天数 | 3, 5, 7, 10 |
| stop_atr_mult | 止损 ATR 倍数 | 1.5, 2, 2.5 |

### 4. ATR 通道策略 (ATRChannelTrend)

**核心理念**：用 ATR 做价格通道，捕捉波动放大后的趋势。

| 参数 | 说明 | 推荐范围 |
|------|------|----------|
| ma_period | 基础均线周期 | 10, 20 |
| atr_period | ATR 周期 | 10, 14, 20 |
| channel_mult | 通道 ATR 倍数 | 1.5, 2, 2.5 |
| max_hold | 最大持有天数 | 5, 7, 10 |

### 5. 增仓放量突破策略 (VolOIBreakout) 🆕

**核心理念**：三重过滤捕捉高质量趋势日（期货专用），利用持仓量数据。

**入场条件（三重过滤）**：
1. **价格突破**：收盘价突破 N 日最高/最低价
2. **成交量放大**：今日成交量 > N 日均量 × K 倍
3. **持仓量增加**：今日OI > 昨日OI × (1 + 阈值)

**特点**：信号少但质量高，只交易"增仓放量突破"的强趋势日。

| 参数 | 说明 | 推荐范围 |
|------|------|----------|
| n_break | 突破周期 | 3, 5, 7 |
| n_exit | 平仓周期 | 3, 5 |
| vol_mult | 成交量放大倍数 | 1.2, 1.5, 2.0 |
| oi_threshold | 持仓量增长阈值 | 0.01, 0.02, 0.03 (1%, 2%, 3%) |
| max_hold | 最大持有天数 | 5, 7, 10 |
| stop_atr_mult | 止损 ATR 倍数 | 1.5, 2.0, 2.5 |

**策略变种**：
- `VolOIBreakoutDual`：多空双向版本
- `VolOIBreakout`：仅做多版本
- `VolOIBreakoutRelaxed`：放宽版本（OI条件较松，信号较多）

## 研究流程

### 时间划分

| 阶段 | 时间范围 | 用途 |
|------|----------|------|
| 训练期 | 2018-2021 | 参数调优 |
| 验证期 | 2022-2023 | 选择稳健参数 |
| 测试期 | 2024 | 最终评估 |

### 稳健性检查

- 参数平面是否存在"连续的不错区域"
- 不同品种上表现是否一致
- 样本外是否稳定

## 代码示例

### Python 调用

```python
from quantlab.core import create_bt_datafeed, BacktestEngine, TradeConfig
from quantlab.core import extract_metrics, print_metrics
from quantlab.strategies import ShortTermBreakout

# 加载数据
data = create_bt_datafeed('rbm', start_date='2020-01-01', end_date='2023-12-31')

# 创建回测引擎
config = TradeConfig(initial_cash=1_000_000)
engine = BacktestEngine(config)

# 添加数据和策略
engine.add_data(data, name='rbm')
engine.add_strategy(ShortTermBreakout, n_high=5, n_low=3, max_hold=7)

# 运行回测
result = engine.run()

# 查看结果
metrics = extract_metrics(result)
print_metrics(metrics)
```

## 可用品种

从数据库加载，共 76 个主连品种：

| 类别 | 品种示例 |
|------|----------|
| 黑色 | rbm (螺纹), hcm (热卷), im (铁矿), jm (焦炭) |
| 有色 | cum (铜), alm (铝), znm (锌), nim (镍) |
| 能化 | scm (原油), fum (燃油), tam (PTA), mam (甲醇) |
| 农产 | cm (玉米), mm (豆粕), srm (白糖), cfm (棉花) |
| 贵金属 | aum (黄金), agm (白银) |
| 金融 | ifm (沪深300), icm (中证500), tm (十债) |

## 数据说明

- 数据时间范围：2018-01-01 ~ 2024-12-31
- 数据来源：`../database/futures/futures.db`
- 部分品种上市较晚，数据条数可能不足


# 默认（自动检测，保留1核）
python param_optimize.py --all-symbols -t voloi

# 指定进程数（比如只用4个）
python param_optimize.py --all-symbols -t voloi -j 4

# 保守一点（只用2个进程）
python param_optimize.py --all-symbols -t voloi -j 2