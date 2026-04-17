# 期货资金强度与收盘价采集系统

当前 `fut_pulse` 已经同时负责两类基础数据：

- `fut_strength`：主力 / 散户资金强度
- `fut_daily_close`：期货主连日收盘价

其中：

- `today` 会在上传强度数据后，自动补齐当日 `fut_daily_close`
- 历史 close 通过独立命令 `close-history` 处理

---

## 目录结构

```text
fut_pulse/
├── collector/
│   ├── screenshot.py
│   └── ocr.py
├── config/
│   ├── calibration.json
│   ├── varieties.json
│   └── holidays.json
├── database/
│   ├── __init__.py
│   └── init_tables.py
├── uploader/
│   └── mysql.py
├── close_price.py
├── pipeline.py
├── main.py
├── requirements.txt
├── .env
├── data/
└── logs/
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库连接

在 `database/fut_pulse/.env` 中填写：

```ini
DB_HOST=your_host
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=futures
```

### 3. 首次校准

启动东方财富客户端并切到目标页面后执行：

```bash
python main.py calibrate
```

---

## 日常命令

### 当天采集

```bash
python main.py today
```

实际流程：

1. 截图主力 / 散户资金
2. OCR 识别
3. 上传 `fut_variety` / `fut_strength`
4. 通过 AkShare 自动同步当日 `fut_daily_close`

只截图和 OCR，不写库：

```bash
python main.py today --no-upload
```

### 历史强度采集

```bash
python main.py history --days 30
python main.py history --start 2026-03-01 --end 2026-04-10
python main.py history --days 30 --no-upload
python main.py history --no-screenshot
```

注意：

- `history` 只处理截图 / OCR / `fut_strength`
- 历史 `fut_daily_close` 不会在 `history` 里自动补齐
- 历史 close 请单独执行 `close-history`

### 历史收盘价回填

```bash
python main.py close-history --days 30
python main.py close-history --start 2026-03-01 --end 2026-04-10
python main.py close-history --start 2026-03-01 --end 2026-04-10 --symbol rbm,cum
python main.py --dry-run close-history --days 5
```

`close-history` 会：

- 读取 `config/varieties.json`
- 使用 `close_price.py` 内部固定映射表找到 AkShare `api_symbol`
- 每个品种只请求一次主连历史
- 将目标日期范围内的 `close_price` 幂等写入 `fut_daily_close`

### 单独执行某一步

```bash
python main.py ocr-only
python main.py ocr-only --today
python main.py upload-only
```

说明：

- `upload-only` 依赖已有 `data/result.json`
- 如果推断为今日模式，上传 `fut_strength` 后会继续自动补齐当日 `fut_daily_close`
- 如果推断为历史模式，只上传 `fut_strength`，历史 close 仍需手动执行 `close-history`

### dry-run

```bash
python main.py --dry-run today
python main.py --dry-run history --days 30
python main.py --dry-run close-history --days 5
```

---

## 自动建表

系统运行时会自动检查并创建以下三张基础表：

- `fut_variety`
- `fut_strength`
- `fut_daily_close`

其中 `fut_daily_close` 结构固定包含：

- `variety_id`
- `trade_date`
- `close_price`
- `collected_at`

---

## 数据流程

### `today`

```text
main.py today
  └── pipeline.py
        ├── [步骤1] collector/screenshot.py → data/screenshots/*.png
        ├── [步骤2] collector/ocr.py        → data/result.json
        ├── [步骤3] uploader/mysql.py       → MySQL (fut_variety / fut_strength)
        └── [步骤4] close_price.py          → MySQL (fut_daily_close)
```

### `history`

```text
main.py history
  └── pipeline.py
        ├── [步骤1] collector/screenshot.py
        ├── [步骤2] collector/ocr.py
        └── [步骤3] uploader/mysql.py       → MySQL (fut_variety / fut_strength)
```

### `close-history`

```text
main.py close-history
  └── close_price.py                        → MySQL (fut_daily_close)
```

---

## 配置说明

### `config/varieties.json`

这是 `fut_pulse` 的主品种清单，字段包括：

- `id`
- `name`
- `key`

### `close_price.py` 固定映射

收盘价同步不再运行时读取外部映射文件，而是直接使用 `close_price.py` 中写死的 `CLOSE_API_SYMBOL_MAP`。

因此如果你以后给 `varieties.json` 新增品种，必须同步补这份映射，否则 close 同步会直接报错并终止。

### `config/holidays.json`

可选文件，用于精确排除节假日：

```json
["2026-01-01", "2026-02-04", "2026-02-05"]
```

---

## 常见问题

**Q: `today` 跑完后会不会自动有收盘价？**  
A: 会。`today` 在 `fut_strength` 上传成功后，会自动同步当日 `fut_daily_close`。

**Q: `history` 跑完后为什么 assistant 还是缺少 close？**  
A: 因为 `history` 只负责强度链路。历史收盘价请单独执行 `python main.py close-history ...`。

**Q: 上传失败后如何重试？**  
A: 如果是今日模式，直接执行 `python main.py upload-only`。它会先上传 `fut_strength`，再自动补今日 close。  
A: 如果是历史模式，先执行 `python main.py upload-only` 上传强度，再执行 `python main.py close-history ...` 补历史 close。

**Q: 为什么不把历史 close 直接塞进 `history` 命令？**  
A: 因为 `history` 是截图 / OCR 驱动，历史 close 是纯 AkShare API 拉取，两条链路拆开后更稳定，也更方便单独重试。

**Q: 哪里看运行日志？**  
A: 每次运行都会写到 `logs/run_YYYYMMDD_HHMMSS.log`。
