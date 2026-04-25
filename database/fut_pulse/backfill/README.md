# 单日补采工具（backfill/）

`fut_pulse` 主流程 `today / history` 之外的独立补救子功能，专门处理一种错位场景。

## 这是什么 / 什么时候用

当东方财富软件上发生以下情况时使用本工具：

- 某个正常交易日漏采了（例如 4月24 忘了跑 `today`）
- 同时因为夜盘，**最右列**显示的是下一交易日的半天夜盘数据（非完整日）
- 真正想补的那天被"挤"到了右边第二列（或更靠左）

`history --days N` 会把最右列当成"最新交易日"，此时会把半天夜盘误当成你要的那天，直接错位。本工具让你**直接在屏幕上框选目标日期那根竖线**，只采集一天，每个合约单张截图，避免误对齐。

## 设计原则

- **自包含**：代码、配置、截图、结果、日志全部在本目录内
- **不污染主流程**：不动 `today / history / pipeline` 的任何文件和数据
- **最大化复用**：通过把 `fut_pulse/` 注入 `sys.path`，直接调用主项目的：
  - `collector.screenshot` / `collector.ocr`
  - `uploader.mysql` / `close_price.sync_close_prices`
  - `database.init_tables`
  - 主 `config/calibration.json`（列表/截图区域/步长）、`config/varieties.json`

## 目录结构

```text
backfill/
├── backfill_day.py      # 主脚本（CLI 入口）
├── config.json          # 本次补采的配置（由 calibrate 生成）
├── README.md            # 本文档
├── data/
│   ├── main_force/      # 主力资金截图（55 张）
│   ├── retail/          # 散户资金截图（55 张）
│   └── result.json      # OCR 结果
└── logs/                # backfill_YYYYMMDD_HHMMSS.log
```

## 使用

所有命令都在 **本目录（`fut_pulse/backfill/`）下**运行：

```bash
cd database/fut_pulse/backfill

# 1) 校准：框选目标日期竖线 + 输入 trade_date
python backfill_day.py calibrate

# 2) 采集：主力 + 散户（中间会提示切换图表）
python backfill_day.py screenshot

# 3) OCR：→ data/result.json
python backfill_day.py ocr

# 4) 上传：写 fut_strength + 同步该日 fut_daily_close
python backfill_day.py upload

# 一键跑完 2~4
python backfill_day.py all

# 只看操作计划不执行
python backfill_day.py --dry-run all
```

## 数据流程

```text
backfill_day.py all
  ├── [screenshot] collector.screenshot（按 config.json 的 hover_x/hover_y
  │                对每个合约点击 → 缓慢 hover → jiggle → 截图）
  │                                         → data/main_force/  data/retail/
  ├── [ocr]        collector.ocr            → data/result.json
  └── [upload]     uploader.mysql           → MySQL (fut_variety / fut_strength)
                   close_price.sync_close_prices → MySQL (fut_daily_close)
```

上传完成后的数据库状态与 `python main.py today` 在目标那天运行的结果**完全等价**。

## `config.json` 字段

```json
{
  "target_trade_date": "2026-04-24",
  "hover_x": 1140,
  "hover_y": 335,
  "hover_delay": 1.0,
  "hover_region": [1132, 570, 1148, 596],
  "move_duration": 0.4,
  "jiggle_pixels": 2,
  "pre_jiggle_wait": 0.2,
  "screenshot_subdirs": {
    "main_force": "main_force",
    "retail": "retail"
  }
}
```

| 字段 | 说明 | 默认 |
|------|------|------|
| `target_trade_date` | 要补采哪一天（YYYY-MM-DD） | — |
| `hover_x` / `hover_y` | 目标日期竖线在屏幕上的坐标 | 由 `calibrate` 框选得出 |
| `hover_region` | `calibrate` 时框选的原始区域 `[x1,y1,x2,y2]`，仅记录用 | — |
| `hover_delay` | hover 到位后等待 tooltip 弹出的秒数 | 1.0 |
| `move_duration` | 鼠标从列表"缓慢"移动到图表的秒数（太快软件不响应） | 0.4 |
| `jiggle_pixels` | 到位后做一次 ±N 像素的小抖动，强制触发 tooltip 重绘，填 0 关闭 | 2 |
| `pre_jiggle_wait` | 第一次到位到开始抖动之间的等待秒数 | 0.2 |
| `screenshot_subdirs` | `data/` 下主力/散户子目录名 | `main_force` / `retail` |

## 调参建议

**tooltip 不弹出 / 截图是空白**时，直接编辑 `config.json` 调大这几个值（不用重新校准）：

- `move_duration` `0.4` → `0.6 ~ 1.0`（让软件把鼠标进入事件吃到，优先调这个）
- `jiggle_pixels` `2` → `3 ~ 5`（抖动幅度大一点，让 tooltip 强制重绘）
- `hover_delay` `1.0` → `1.5 ~ 2.0`（tooltip 渲染慢时）

**hover X 坐标有漂移**（图表缩放 / 日期轴刻度变了）：重跑 `python backfill_day.py calibrate` 覆盖即可。

## 失败恢复

- **OCR 后某些品种数值错了**：手工改 `data/result.json`，再跑 `python backfill_day.py upload`
- **`fut_strength` 上传成功但 `fut_daily_close` 同步失败**：回到 `fut_pulse/` 根目录跑
  ```bash
  python main.py close-history --start 2026-04-24 --end 2026-04-24
  ```
- **想换一个补采日期**：重跑 `calibrate` 输入新日期即可，旧截图会被新截图覆盖；如果想保留，把 `data/main_force` 和 `data/retail` 先备份改名

## 依赖的主项目资源

本工具不能脱离 `fut_pulse/` 主项目独立运行，运行前需确保：

- `fut_pulse/config/calibration.json` 已完成主校准（列表区域、截图区域、合约总数等）
- `fut_pulse/config/varieties.json` 存在
- `fut_pulse/.env` 中的数据库连接可用
- `fut_pulse/requirements.txt` 中的依赖已安装（`pyautogui`、`cnocr`、`akshare`、`pymysql` 等）
