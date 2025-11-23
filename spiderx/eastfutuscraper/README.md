# 东方财富期货爬虫 - 快速开始指南

## 📋 前置要求

1. ✅ Python 3.7+
2. ✅ Chrome浏览器
3. ✅ ChromeDriver（与Chrome版本匹配）
4. ✅ MySQL数据库访问权限
5. ✅ `contracts_main.json` 文件（包含需要爬取的期货品种列表）

## 🚀 快速开始

### 第一步：安装依赖

```bash
cd spiderx/eastfutuscraper
pip install -r requirements.txt
```

依赖包包括：
- PyMySQL - MySQL数据库连接
- selenium - 浏览器自动化
- requests - HTTP请求
- aiohttp - 异步HTTP（如需要）
- pandas - 数据处理（如需要）

### 第二步：配置数据库连接

编辑 `main.py` 文件中的 `DB_CONFIG` 配置：

```python
DB_CONFIG = {
    'host': 'your_mysql_host',
    'port': 3306,
    'user': 'your_username',
    'password': 'your_password',
    'database': 'futures',
    'charset': 'utf8mb4'
}
```

### 第三步：准备过滤文件

确保 `contracts_main.json` 文件存在，格式如下：

```json
{
  "contracts_main": [
    {"symbol": "cum", ...},
    {"symbol": "aum", ...},
    ...
  ]
}
```

爬虫会根据此文件中的 `symbol` 字段过滤数据，只保存匹配的期货品种。

### 第四步：运行爬虫

```bash
python main.py
```

## 📊 运行流程

爬虫会按以下流程执行：

```
1. 加载 contracts_main.json 过滤条件
   ↓
2. 启动Chrome浏览器（使用Selenium）
   ↓
3. 依次访问5个交易所页面
   ├─ 上期所 (ID: 113)
   ├─ 上期能源 (ID: 142)
   ├─ 大商所 (ID: 114)
   ├─ 郑商所 (ID: 115)
   └─ 广期所 (ID: 225)
   ↓
4. 通过性能日志劫持API请求
   ├─ 第一次请求：获取数据总数
   └─ 第二次请求：修改pageSize参数，一次性获取所有数据
   ↓
5. 解析JSONP格式响应数据
   ↓
6. 根据 contracts_main.json 过滤有效品种
   ↓
7. 保存数据到MySQL数据库
   └─ 每个期货品种对应一个表（hist_{symbol}）
   └─ 使用当前日期作为交易日期（trade_date）
   └─ 如果当天数据已存在，则更新（ON DUPLICATE KEY UPDATE）
   ↓
8. 输出统计信息
```

## 💾 数据库存储

### 表结构

每个期货品种对应一个表，表名格式：`hist_{symbol}`（symbol为小写）

**表字段说明：**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| trade_date | DATE | 交易日期（主键） |
| open_price | DECIMAL(10,2) | 开盘价 |
| high_price | DECIMAL(10,2) | 最高价 |
| low_price | DECIMAL(10,2) | 最低价 |
| close_price | DECIMAL(10,2) | 收盘价 |
| volume | BIGINT | 成交量 |
| open_interest | BIGINT | 持仓量 |
| turnover | DECIMAL(20,2) | 成交额 |
| price_change | DECIMAL(10,2) | 涨跌额 |
| change_pct | DECIMAL(10,2) | 涨跌幅 |
| macd_dif | DECIMAL(10,4) | MACD快线（预留） |
| macd_dea | DECIMAL(10,4) | MACD慢线（预留） |
| macd_histogram | DECIMAL(10,4) | MACD柱状图（预留） |
| rsi_14 | DECIMAL(6,2) | RSI(14)（预留） |
| kdj_k | DECIMAL(6,2) | KDJ-K值（预留） |
| kdj_d | DECIMAL(6,2) | KDJ-D值（预留） |
| kdj_j | DECIMAL(6,2) | KDJ-J值（预留） |
| bb_upper | DECIMAL(10,2) | 布林带上轨（预留） |
| bb_middle | DECIMAL(10,2) | 布林带中轨（预留） |
| bb_lower | DECIMAL(10,2) | 布林带下轨（预留） |
| bb_width | DECIMAL(10,2) | 布林带宽度（预留） |
| recommendation | VARCHAR(20) | 推荐操作（预留） |
| source_ts | TIMESTAMP | 数据源时间戳 |
| ingest_ts | TIMESTAMP | 入库时间戳 |

**注意：** 当前代码只保存基础价格数据（开盘、最高、最低、收盘、成交量等），技术指标字段为预留字段。

### 数据覆盖逻辑

- 使用 `INSERT ... ON DUPLICATE KEY UPDATE` 实现覆盖逻辑
- 如果当天的数据已存在，则更新价格和成交量等字段
- 交易日期（trade_date）为主键，使用当前系统日期

### 示例表名

```
hist_cum   - 沪铜主连
hist_aum   - 沪金主连
hist_rbm   - 螺纹钢主连
hist_im    - 铁矿石主连
...
```

## 📈 数据字段映射

API返回字段 → 数据库字段：

| API字段 | 数据库字段 | 说明 |
|---------|-----------|------|
| dm | symbol | 期货代码（用于匹配和表名） |
| o | open_price | 今开 |
| h | high_price | 最高 |
| l | low_price | 最低 |
| p | close_price | 最新价（收盘价） |
| vol | volume | 成交量 |
| cje | turnover | 成交额 |
| ccl | open_interest | 持仓量 |
| zde | price_change | 涨跌额 |
| zdf | change_pct | 涨跌幅 |

## ⏰ 定时执行建议

### 使用cron（Linux/Mac）

```bash
# 编辑crontab
crontab -e

# 每天15:30执行（期货收盘后）
30 15 * * * cd /path/to/spiderx/eastfutuscraper && python main.py >> logs/scraper_$(date +\%Y\%m\%d).log 2>&1
```

### 使用Windows任务计划程序

1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器：每天 15:30
4. 操作：启动程序
   - 程序：`python.exe`
   - 参数：`main.py`
   - 起始位置：`D:\ysd\workstation\spiderx\eastfutuscraper`

## 🔍 故障排查

### 问题1：找不到ChromeDriver

**错误信息：**
```
selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable needs to be in PATH.
```

**解决方法：**
1. 下载ChromeDriver：https://chromedriver.chromium.org/
2. 确保版本与Chrome浏览器匹配
3. 将chromedriver添加到系统PATH，或放在项目目录下

### 问题2：数据库连接失败

**错误信息：**
```
✗ 数据库连接失败: (2003, "Can't connect to MySQL server...")
```

**解决方法：**
1. 检查 `main.py` 中的 `DB_CONFIG` 配置是否正确
2. 确认数据库服务器可访问
3. 验证用户名和密码
4. 检查防火墙设置
5. 确认数据库 `futures` 已创建

### 问题3：没有找到任何数据

**可能原因：**
1. `contracts_main.json` 文件不存在或格式错误
2. 过滤条件太严格，没有匹配的品种
3. API请求失败

**解决方法：**
```bash
# 检查contracts_main.json文件
cat contracts_main.json

# 确保文件包含有效的合约数据，格式正确
# 检查日志中的错误信息
```

### 问题4：部分数据插入失败

**检查步骤：**
1. 查看日志中的错误信息
2. 确认数据库表是否自动创建成功
3. 检查数据类型是否匹配
4. 验证数据库用户权限（需要CREATE TABLE权限）
5. 检查symbol字段是否为空或格式不正确

### 问题5：未在日志中找到API请求

**可能原因：**
1. 页面加载时间不够
2. 网络请求被拦截
3. API地址发生变化

**解决方法：**
1. 增加等待时间（修改 `time.sleep(5)` 的值）
2. 检查Chrome浏览器是否正常启动
3. 确认网络连接正常
4. 查看浏览器控制台是否有错误

## 📝 常见使用场景

### 场景1：首次运行

```bash
# 1. 检查配置文件
# - 确认 DB_CONFIG 配置正确
# - 确认 contracts_main.json 存在且格式正确

# 2. 运行爬虫
python main.py

# 3. 查看结果
# - 检查控制台输出的统计信息
# - 登录数据库查看数据表是否创建
# - 查询当天的数据是否保存成功
```

### 场景2：每日定时更新

爬虫会自动覆盖当天的数据，无需特殊处理。每天运行一次即可。

### 场景3：手动补充失败日期的数据

**注意：** 当前代码使用系统当前日期作为交易日期，如果需要补充历史日期数据，需要修改代码中的 `trade_date` 赋值逻辑。

### 场景4：查看历史数据

```sql
-- 查看沪铜主连最近10天的数据
SELECT * FROM hist_cum 
ORDER BY trade_date DESC 
LIMIT 10;

-- 统计所有品种的数据量
SELECT 
    TABLE_NAME,
    TABLE_ROWS
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'futures' 
    AND TABLE_NAME LIKE 'hist_%'
ORDER BY TABLE_ROWS DESC;

-- 检查今天是否有数据
SELECT 
    'hist_cum' as contract,
    COUNT(*) as records,
    MAX(trade_date) as latest_date
FROM hist_cum
WHERE trade_date = CURDATE();

-- 查看所有品种今天的数据
SELECT 
    TABLE_NAME,
    (SELECT COUNT(*) FROM information_schema.COLUMNS 
     WHERE TABLE_NAME = t.TABLE_NAME AND TABLE_SCHEMA = 'futures') as columns,
    TABLE_ROWS
FROM information_schema.TABLES t
WHERE TABLE_SCHEMA = 'futures' 
    AND TABLE_NAME LIKE 'hist_%';
```

## 📊 运行输出示例

成功运行后会输出类似以下信息：

```
============================================================
--- 数据获取成功 ---
============================================================
上期所 (ID: 113):
  原始数据: 45 条
  过滤后: 12 条

大商所 (ID: 114):
  原始数据: 38 条
  过滤后: 15 条

...

------------------------------------------------------------
总计:
  所有交易所数: 5
  原始数据总数: 200 条
  过滤后总数: 63 条
============================================================

============================================================
--- 开始保存数据到数据库 ---
============================================================
------------------------------------------------------------
数据库保存结果:
  成功: 63 条
  失败: 0 条
============================================================
```

## 🎯 最佳实践

1. **定时执行**：建议在每天15:30（期货收盘后）执行
2. **日志管理**：定期清理日志文件，或配置日志轮转
3. **数据备份**：定期备份数据库
4. **监控告警**：配置失败通知（邮件/短信/钉钉等）
5. **错误重试**：如果失败，可在30分钟后重试
6. **数据验证**：定期检查数据完整性，确认每天都有数据更新

## ⚙️ 高级配置

### 启用无头模式

如果需要后台运行，可以取消注释 `main.py` 中的无头模式配置：

```python
# chrome_options.add_argument("--headless")
```

### 调整等待时间

如果网络较慢或API响应较慢，可以增加等待时间：

```python
time.sleep(5)  # 增加此值，例如改为 10
```

### 自定义过滤逻辑

修改 `filter_futures_data` 函数可以实现自定义的过滤逻辑。

## 🆘 需要帮助？

如遇到其他问题，请检查：

1. 📄 日志输出：查看控制台输出的详细错误信息
2. 📖 代码注释：阅读 `main.py` 中的函数注释
3. 🔍 数据库日志：检查MySQL错误日志
4. 🌐 网络连接：确认可以访问东方财富网站

---

**版本信息**
- 爬虫版本：v1.0
- 支持交易所：5个（上期所、大商所、郑商所、上期能源、广期所）
- 数据存储：MySQL数据库
- 最后更新：2025-01-XX

# 东方财富期货数据爬虫调度器

## 功能说明

本调度器专门为期货数据爬取设计，具有以下特点：

- **运行周期**: 14天（2周）
- **执行规则**: 仅在交易日（周一到周五）执行
- **执行时间**: 每天下午16:00（收盘后1小时）
- **预计执行次数**: 10次（本周5天 + 下周5天）

## 使用方法

### 1. 启动调度器

在 macOS/Linux 系统上：

```bash
cd spiderx/eastfutuscraper
./start_scheduler.sh
```

如果提示权限不足，先添加执行权限：

```bash
chmod +x start_scheduler.sh stop_scheduler.sh
```

### 2. 停止调度器

```bash
./stop_scheduler.sh
```

### 3. 查看运行状态

#### 实时查看控制台输出

```bash
tail -f nohup.out
```

#### 查看详细日志

```bash
tail -f logs/futures_crawler_$(date +%Y-%m-%d).log
```

#### 查看进程状态

```bash
ps aux | grep scheduler.py
```

## 调度逻辑说明

### 1. 启动时机判断

调度器启动后会自动判断：
- 如果当前是交易日且时间在 16:00-16:05 之间，立即执行
- 如果当前是交易日但未到16:00，等待到16:00执行
- 如果当前是非交易日或已过16:00，等待到下一个交易日16:00执行

### 2. 交易日识别

- **交易日**: 周一到周五（0-4）
- **非交易日**: 周六、周日

**注意**: 本调度器暂不识别法定节假日，如遇节假日期间需要手动停止调度器。

### 3. 执行流程

每次执行包括以下步骤：

1. 加载期货品种过滤条件（从 `contracts_main.json`）
2. 爬取所有交易所期货数据（上期所、上期能源、大商所、郑商所、广期所）
3. 根据过滤条件筛选数据
4. 将数据保存到数据库（hist_<symbol> 表）
5. 记录执行日志

### 4. 运行周期示例

假设在 2024年1月8日（周一）启动：

```
第1次: 2024-01-08 16:00 (周一) ✓
第2次: 2024-01-09 16:00 (周二) ✓
第3次: 2024-01-10 16:00 (周三) ✓
第4次: 2024-01-11 16:00 (周四) ✓
第5次: 2024-01-12 16:00 (周五) ✓
      2024-01-13 周六 (跳过)
      2024-01-14 周日 (跳过)
第6次: 2024-01-15 16:00 (周一) ✓
第7次: 2024-01-16 16:00 (周二) ✓
第8次: 2024-01-17 16:00 (周三) ✓
第9次: 2024-01-18 16:00 (周四) ✓
第10次: 2024-01-19 16:00 (周五) ✓

总计: 10次执行，覆盖2周的交易日数据
```

## 文件说明

### scheduler.py
核心调度程序，负责：
- 时间管理和任务调度
- 交易日判断
- 任务执行和异常处理
- 日志记录

### start_scheduler.sh
启动脚本，功能：
- 检查Python环境
- 检测操作系统（macOS使用caffeinate防止休眠）
- 后台启动调度器
- 保存进程ID到 `scheduler.pid`

### stop_scheduler.sh
停止脚本，功能：
- 优雅停止调度器进程
- 如需要则强制停止
- 清理pid文件

### logs/
日志目录，包含：
- `futures_crawler_YYYY-MM-DD.log`: 按日期存储的详细日志
- 自动按日期切换日志文件

## 注意事项

### 1. macOS 防休眠

macOS 系统会自动使用 `caffeinate` 命令防止系统休眠，确保调度器长时间运行不中断。

### 2. 数据库连接

确保数据库配置正确（在 `main.py` 中配置），调度器需要能够正常连接数据库。

### 3. 依赖环境

确保已安装所有依赖：

```bash
pip install -r requirements.txt
```

主要依赖：
- selenium
- requests
- pymysql

### 4. Chrome 浏览器

爬虫使用 Selenium + Chrome，确保系统已安装：
- Chrome 浏览器
- ChromeDriver（版本需匹配）

### 5. 停止建议

如遇法定节假日（如国庆、春节等），建议提前停止调度器：

```bash
./stop_scheduler.sh
```

节后再重新启动即可。

## 常见问题

### Q: 如何确认调度器在运行？

```bash
# 查看进程
ps aux | grep scheduler.py

# 查看最新日志
tail -f logs/futures_crawler_$(date +%Y-%m-%d).log
```

### Q: 如何强制停止？

```bash
# 找到进程ID
ps aux | grep scheduler.py

# 强制停止
kill -9 <PID>
```

### Q: 日志文件太大怎么办？

日志会按天自动切换，可以定期清理旧日志：

```bash
# 删除7天前的日志
find logs/ -name "futures_crawler_*.log" -mtime +7 -delete
```

### Q: 如何测试调度器？

可以修改 `scheduler.py` 中的执行时间进行测试：

```python
self.execution_hour = 当前时间的下一个小时  # 例如现在是14点，改为15
```

## 技术特性

- ✅ 优雅退出（支持 SIGINT、SIGTERM 信号）
- ✅ 自动日志轮转（按日期切换）
- ✅ 交易日智能识别
- ✅ 异常自动停止
- ✅ 心跳状态监控
- ✅ macOS 休眠防护

## 联系方式

如有问题，请查看日志文件或联系开发者。

