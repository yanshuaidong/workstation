# 期货资金强度采集系统

自动截图 → OCR 识别 → 上传 MySQL 的完整数据采集流程。  
支持**当天单日采集**与**连续多日历史采集**两种模式。

---

## 目录结构

```
getdata/
├── collector/
│   ├── screenshot.py   # 截图自动化（today / history 两种模式）
│   └── ocr.py          # OCR 识别（含置信度校验）
├── uploader/
│   └── mysql.py        # MySQL 上传（含连接重试）
├── config/
│   ├── calibration.json    # 屏幕几何校准参数（首次需校准生成）
│   ├── varieties.json      # 品种列表（可直接编辑增减品种）
│   └── holidays.json       # 节假日列表（可选，用于精确排除节假日）
├── data/               # 截图与 OCR 结果输出目录
├── logs/               # 运行日志（每次运行独立一个文件）
├── pipeline.py         # 流程编排（截图 → OCR → 上传）
├── main.py             # 统一入口
├── .env                # 数据库连接（不提交到版本库）
└── .env.example        # 数据库连接配置示例
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库连接

```bash
cp .env.example .env
# 编辑 .env，填写真实的数据库连接信息
```

### 3. 首次校准（必须）

启动东方财富客户端并切换到目标页面，然后运行：

```bash
python main.py calibrate
```

校准菜单选项：
- **选项1**：框选合约列表区域 + 截图数据区域（当天模式必须）
- **选项2**：框选日期轴相邻两日区域（历史模式必须）
- **选项3**：测试截图，验证区域是否正确

校准结果自动保存到 `config/calibration.json`。

---

## 日常使用

### 采集当天数据

```bash
python main.py today
```

完整流程：截图（主力+散户）→ OCR → 上传 MySQL

```bash
python main.py today --no-upload    # 仅截图+OCR，不上传
```

### 采集历史多日数据

```bash
python main.py history --days 30               # 最近30个交易日
python main.py history --start 2026-03-01 --end 2026-04-10  # 指定日期范围
python main.py history --days 30 --no-upload   # 仅截图+OCR，不上传
python main.py history --no-screenshot         # 已有截图，仅OCR+上传
```

### 单独执行某一步

```bash
python main.py ocr-only             # 对已有历史截图重新跑OCR
python main.py ocr-only --today     # 对已有今日截图重新跑OCR
python main.py upload-only          # 将已有 data/result.json 上传
```

### 测试运行（不执行实际操作）

```bash
python main.py --dry-run today
python main.py --dry-run history --days 30
```

---

## 配置文件说明

### `config/calibration.json` — 屏幕几何参数

通过 `python main.py calibrate` 自动生成，通常无需手动编辑。

| 字段 | 说明 |
|------|------|
| `list_region` | 合约列表区域 `[x1, y1, x2, y2]` |
| `screenshot_region` | 数据截图区域 `[x1, y1, x2, y2]` |
| `visible_count` | 列表中同时可见的合约数量 |
| `total_count` | 合约总数量 |
| `item_height` | 单个合约行的像素高度 |
| `click_x` | 点击列表时的 X 坐标 |
| `screenshot_subdirs` | 今日截图存放的子目录名 |
| `history_screenshot_subdirs` | 历史截图存放的子目录名 |
| `history_count` | 历史模式默认采集天数（`--days` 未指定时使用） |
| `history_hover_delay` | hover 后等待截图的秒数（tooltip 出现较慢时调大） |
| `history_date_step_x` | 日期轴相邻两日的像素间距 |
| `history_latest_date_x` | 最新日期的 X 坐标 |
| `history_date_bar_y` | 日期轴 hover 的 Y 坐标 |

### `config/varieties.json` — 品种列表

JSON 数组，每项包含 `id`、`name`、`key` 三个字段。  
可直接编辑增减品种，`id` 须与东方财富列表中的顺序一致（从1开始）。

### `config/holidays.json` — 节假日（可选）

若要精确排除节假日（如春节、国庆），创建此文件：

```json
["2026-01-01", "2026-02-04", "2026-02-05", "2026-02-06"]
```

不创建此文件时，系统只排除周末。

### `.env` — 数据库连接

```ini
DB_HOST=your_host
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=futures
```

**注意：请勿将 `.env` 提交到版本库。**

---

## 数据流程

```
main.py
  └── pipeline.py
        ├── [步骤1] collector/screenshot.py → data/screenshots/*.png
        ├── [步骤2] collector/ocr.py        → data/result.json
        └── [步骤3] uploader/mysql.py       → MySQL (fut_variety / fut_strength)
```

每次运行的详细日志保存在 `logs/run_YYYYMMDD_HHMMSS.log`。

---

## 常见问题

**Q: OCR 识别率低，很多值为 null？**  
A: 先用 `python main.py calibrate` 选项3测试截图，确认截图区域对准数值；适当调大 `history_hover_delay`（历史模式）。

**Q: 历史模式 hover 日期偏移？**  
A: 在 `config/calibration.json` 中微调 `history_date_step_x`（每天像素间距）和 `history_latest_date_x`（最新日期X坐标）。

**Q: 上传失败后如何重试？**  
A: 截图和 OCR 结果已保存，直接运行 `python main.py upload-only` 重试上传。

**Q: 想只更新部分日期的数据？**  
A: 使用 `python main.py history --start 2026-04-07 --end 2026-04-10`，已存在的记录会自动跳过（INSERT IGNORE）。
