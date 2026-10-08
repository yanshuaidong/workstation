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
│   ├── ocr.py
│   └── vision_review.py     # DeepSeek 今日截图复核
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
├── logs/
└── backfill/                # 单日补采子功能（自包含：代码 + 配置 + 数据 + 日志）
    ├── backfill_day.py
    ├── config.json
    ├── README.md
    ├── data/
    │   ├── main_force/
    │   ├── retail/
    │   └── result.json
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

### 3. 配置 DeepSeek 图片复核

在项目根目录 `workstation/.env` 中配置已有的 `DEEPSEEK_KEY`（不是本子目录的数据库 `.env`）：

```ini
DEEPSEEK_KEY=你的密钥
# 可选，默认使用文档中支持图片输入的模型
DEEPSEEK_VISION_MODEL=deepseek-flash
```

程序通过绝对路径读取根目录配置，不依赖当前工作目录。系统环境变量优先。
读取复核配置不会将根目录的 `DB_*` 注入环境，不改变现有数据库配置。
API 使用 Python 标准库调用，无须额外安装 OpenAI SDK。

### 4. 首次校准

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

1. 截图主力 / 散户资金。
2. 基础 OCR 识别，保存 `data/result.ocr.json`。
3. DeepSeek 对照**原始截图**和 OCR 逐项核对数字、负号、小数点，全部通过后生成 `data/result.json`。
4. 将复核后的数值上传 `fut_variety` / `fut_strength`。
5. 通过 AkShare 自动同步当日 `fut_daily_close`，随后执行原有异常信号检测。

每批默认复核 5 个品种（10 张图），55 个品种需要 11 批请求；会产生模型 API 费用。
模型明确读到的值覆盖 OCR 值，包括补齐 OCR 未识别出的值。输出字段仍为
`id`、`key`、`main_force`、`retail`，与原上传模块兼容。

**失败保护和留档：**

- `data/result.ocr.json`：基础 OCR 原值。
- `data/result.review.json`：复核状态、各批回复、修改前后数值及失败原因。
- `data/result.json`：仅在所有品种复核通过后原子写入，作为上传输入。
- `data/result.previous.json`：开始今日采集（或 `ocr-only --today`）时将旧 `result.json` 移至此处，保留上一份结果。
  失败时不会恢复为可上传的 `result.json`，避免 `upload-only` 误用旧结果。

缺少密钥、截图缺失、模型无法确认数字、漏行/串品种、返回格式错误或 API 失败都会中止，
不会自动退回基础 OCR 上传。网络超时、HTTP 429 和 5xx 最多尝试 3 次，单次超时 90 秒。
模型也可能读错；双重识别能提供额外核对，但不保证绝对准确，关键数据仍建议对照截图抽查。

只截图、OCR 和复核，不写库：

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

### 单日补采（独立子功能）

遇到「某天漏采 + 夜盘导致软件最右列是半天数据」这种错位场景时，不要动 `history` 主流程，用 `backfill/` 子目录里的独立工具：

```bash
cd backfill
python backfill_day.py calibrate    # 框选目标日期竖线
python backfill_day.py all          # screenshot → ocr → upload
```

完整说明、配置字段、调参建议见 [`backfill/README.md`](./backfill/README.md)。

### 单独执行某一步

```bash
python main.py ocr-only
python main.py ocr-only --today
python main.py upload-only
```

说明：

- `ocr-only --today`：复用当前今日截图，重新做基础 OCR + DeepSeek 复核，不重新截图、不写库。
  复核失败后可用此命令重试；成功且确认截图属于目标交易日后，再执行 `upload-only`。
- `upload-only` 依赖已有 `data/result.json`，本身不再次调用模型。
- `history`、默认 `ocr-only` 和独立 `backfill/` 保持原行为，暂未接入 DeepSeek 复核。
- 如果推断为今日模式，上传 `fut_strength` 后会继续自动补齐当日 `fut_daily_close`
- 如果推断为历史模式，只上传 `fut_strength`，历史 close 仍需手动执行 `close-history`

### dry-run

```bash
python main.py --dry-run today
python main.py --dry-run history --days 30
python main.py --dry-run close-history --days 5
```

---

## 自动化测试

在 `database/fut_pulse/` 下执行：

```bash
python -m unittest discover -s tests -v
```

测试使用模拟的 API、截图采集和数据库步骤，并禁止真实 socket 连接。
覆盖符号/小数点修正、漏项与错位拒绝、重试、失败留档、结果原子写入和上传阻断。

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
        ├── [步骤2] collector/ocr.py           → data/result.ocr.json
        ├── [步骤2b] collector/vision_review.py → data/result.review.json + result.json
        ├── [步骤3] uploader/mysql.py          → MySQL (fut_variety / fut_strength)
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

### `backfill/`（单日补采子功能）

自包含：代码、配置、数据、日志全部在 `backfill/` 内，只复用主项目的 `collector / uploader / close_price` 模块和 `config/calibration.json`、`config/varieties.json`。流程图与使用细节见 [`backfill/README.md`](./backfill/README.md)。

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
A: 主流程写到 `logs/run_YYYYMMDD_HHMMSS.log`；`backfill/` 子功能写到 `backfill/logs/backfill_YYYYMMDD_HHMMSS.log`。

**Q: 漏采一天同时软件多出半天夜盘数据怎么办？**  
A: 进入 `backfill/` 子目录运行 `python backfill_day.py calibrate → all`，完整说明见 [`backfill/README.md`](./backfill/README.md)。这条链路不会动 `today / history` 的任何文件和数据。
