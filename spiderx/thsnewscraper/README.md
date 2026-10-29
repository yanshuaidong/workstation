# 同花顺期货热点新闻爬虫（thsnewscraper）

抓取同花顺「期货热点」榜单，去重写入云端 MySQL 的 `fut_news` 表，供期货项目的 `/news` 页面直接读取。

```
同花顺热点接口 ──► 本爬虫（每小时） ──► MySQL futures.fut_news ──► 期货站 /news
```

期货站**不再**在页面上点「获取数据」，也不再自己抓新闻：页面只读这张表。表结构见 [fut_news-table.md](fut_news-table.md)。

## 目录

| 文件 | 作用 |
| --- | --- |
| `main.py` | 抓取 + 过滤 + 写库；CLI 入口 |
| `scheduler.py` | 长期运行，每 1 小时调用一次 `crawl_once()` |
| `fut_news-table.md` | 表结构说明（期货项目里有一份完全相同的副本） |
| `start_scheduler.sh` / `stop_scheduler.sh` | 后台启停 |
| `requirements.txt` | PyMySQL + requests |

## 环境准备

```bash
cd spiderx/thsnewscraper
pip install -r requirements.txt
```

数据库连接**不写在这个目录里**，由 `spiderx/db/mysql_config.py` 解析 `spiderx` 上一级的 `.env`：

```ini
DB_HOST=rm-xxxx.mysql.rds.aliyuncs.com
DB_PORT=3306
DB_USER=ysd
DB_PASSWORD=******
DB_NAME=futures
```

`ENV_PATH = Path(__file__).resolve().parents[2] / ".env"`，也就是 `<spiderx 的上级目录>/.env`。部署到服务器后如果目录层级变了，要么把 `.env` 放到同样的相对位置，要么用同名环境变量覆盖（`DB_*` 环境变量优先）。

## 表已建好

`fut_news` 表已于 2026-10-29 在云端 MySQL `futures` 库建好，并用真实数据验证过写入与去重。换环境、换库或误删时，按 [fut_news-table.md](fut_news-table.md) 里的建表语句执行一遍即可——建表是一次性动作，仓库里不保留建表脚本。

```bash
python main.py check              # 确认能连库、表存在
python main.py once               # 抓一轮写入
```

## 运行

| 命令 | 作用 |
| --- | --- |
| `python main.py once` | 抓一次并写库（默认行为，不传参数也一样） |
| `python main.py check` | 只检查连接和表，不抓取 |
| `python main.py schedule` | 调度模式：立即抓一次，之后每小时一次 |

后台启停（生产用）：

```bash
./start_scheduler.sh   # nohup 后台运行 main.py schedule
./stop_scheduler.sh    # SIGTERM 优雅退出
tail -f nohup.out
tail -f logs/ths_news_$(date +%Y-%m-%d).log
```

也可以用 `spiderx/runall.sh` 和其它四个爬虫一起拉起（`runall.sh` 的 `SERVICES` 列表里已经加了 `thsnewscraper`）。

首次部署到 Linux 后，如果脚本没有可执行位，先 `chmod +x start_scheduler.sh stop_scheduler.sh`。

单轮失败**不会**让调度器退出：网络抖动或数据库短时不可用只记日志，下一轮继续。这样开机自启后能自愈，不用人盯。

## 采集规则

上游接口：`GET https://ftapi.10jqka.com.cn/futgwapi/domain/news/content/hot_list/v1/list`

- 一次性返回榜单当前这一屏（约 30 条，条数与内容由上游决定），**没有翻页参数**；"历史"完全靠本地累积。
- 请求带 `Origin` / `Referer = https://goodsfu.10jqka.com.cn/`（伪装成同花顺自家页面）、`no-cache` 头和 Chrome UA；`allow_redirects=False`；超时 20 秒。
- 校验：HTTP 200、`code == 0`、`data` 是数组，否则整轮失败，一个字都不写。

逐行过滤（`normalize_rows`），不满足的计入「跳过」：

| 条件 | 结果 |
| --- | --- |
| `title` 不是非空字符串 | 丢 |
| `url` 不是 `https` | 丢 |
| URL 带用户名/密码，或带显式端口（`:443` 除外） | 丢 |
| 主机名不是 `10jqka.com.cn` / `*.10jqka.com.cn` | 丢 |

域名规则的原因：`url` 会被期货站直接放进 `<iframe>`，只允许内嵌同花顺自己的 https 页面。

入库用 `INSERT ... ON DUPLICATE KEY UPDATE id = id`：

- 唯一键是 `url`，重复的只做空更新——**不改标题、不动 `read_at`、不换 `id`**；
- 整批一个事务，`rowcount == 1` 算新增、`== 0` 算重复；
- `kind` 在爬虫里按 URL 前缀判定（`deep` / `community` / `news`），期货站不重复判断。

## 日志

- `nohup.out`：进程的标准输出（调度器启动横幅、心跳）。
- `logs/ths_news_YYYY-MM-DD.log`：按日期切分的详细日志。
- 每轮日志都有「采集完成：共 N 条，新增 X 条，重复 Y 条，跳过 Z 条」。

## 排错

| 现象 | 原因 / 处理 |
| --- | --- |
| `表 fut_news 不存在` | 还没建表，按 `fut_news-table.md` 里的建表语句建一次 |
| `未找到环境变量文件: …\.env` | `.env` 不在 `spiderx` 的上级目录，见「环境准备」 |
| `新闻接口返回 HTTP 403/5xx` | 上游风控或改版；看是否需要更新请求头 |
| `热点接口返回失败，code=…` | 上游业务错误码，通常改版，检查接口返回体 |
| `新闻接口未返回有效的标题与新闻链接` | 上游有数据但全被规则过滤，多半是 URL 域名变了 |
| `数据库连接失败` | 检查 `.env`、RDS 白名单、网络 |
| 每次都「新增 0 条」 | 正常：热点榜单这一小时没变化 |

## 不要做的事

- **不要在两个地方各写一套字段映射**：列名与顺序只认 `fut_news-table.md`，期货站 `news-store.js` 里的 SELECT 列要跟着改。
- **不要在爬虫里写 `read_at`**：那是期货站的字段，爬虫碰到它就是抢别人的状态。
- **不要用 `TRUNCATE` 清表**：会把期货站的阅读记录一起清掉。
- 上游没有历史翻页，想补更早的新闻只能靠长期运行慢慢积累。
