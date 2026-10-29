# fut_news 表结构说明（新闻表）

- **数据库**：`futures`（阿里云 RDS MySQL，与 `fut_strength`、`fut_variety` 同库）
- **写入方**：`spiderx/thsnewscraper`，每小时抓一次同花顺期货热点榜，只插入不存在的 URL
- **读取方**：期货项目 `display/server/news-store.js`，页面 `/news` 三个标签页都读这张表
- **版本**：v1（2026-10-29 建立）
- **本文件有两份**：`futures/doc/fut_news-table.md` 与 `spiderx/thsnewscraper/fut_news-table.md`，内容必须一致，改结构时两边一起改

## 建表语句

```sql
CREATE TABLE IF NOT EXISTS fut_news (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  url          VARCHAR(512) NOT NULL COMMENT '原文链接，去重键',
  title        VARCHAR(500) NOT NULL COMMENT '新闻标题',
  tag          VARCHAR(64)  DEFAULT NULL COMMENT '上游标签，如 专题',
  color        VARCHAR(32)  DEFAULT NULL COMMENT '上游标签颜色，如 red',
  sorts        DOUBLE       DEFAULT NULL COMMENT '上游排序权重，仅存档',
  hot_value    VARCHAR(64)  DEFAULT NULL COMMENT '上游热度值，字符串原样存档',
  kind         VARCHAR(16)  NOT NULL DEFAULT 'news' COMMENT 'news 普通新闻 / deep 深度研究 / community 社区长文',
  collected_at DATETIME(3)  NOT NULL COMMENT '爬虫入库时间，UTC',
  read_at      DATETIME(3)  DEFAULT NULL COMMENT '期货站标记已读的时间，UTC；NULL 表示未读',
  PRIMARY KEY (id),
  UNIQUE KEY uk_fut_news_url (url),
  KEY idx_fut_news_kind_id (kind, id),
  KEY idx_fut_news_read (read_at, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC
  COMMENT='同花顺期货热点新闻：爬虫写入，期货站读取';
```

`ROW_FORMAT=DYNAMIC` 不能省：`url` 是 `utf8mb4`，512 字符的唯一索引是 2048 字节，只有 DYNAMIC 行格式的 3072 字节键长上限放得下（MySQL 5.7 / 8.0 默认就是 DYNAMIC，显式写出来是为了避免库级默认值不是它时建表失败）。

## 字段

| 字段 | 类型 | 写入方 | 含义 |
| --- | --- | --- | --- |
| `id` | BIGINT UNSIGNED 自增 | MySQL | 主键，也是页面 `/api/news/:id/read` 里的编号 |
| `url` | VARCHAR(512)，唯一 | 爬虫 | 原文链接。**唯一键**，重复 URL 不重复入库 |
| `title` | VARCHAR(500) | 爬虫 | 标题，已去首尾空白，超长截断 |
| `tag` | VARCHAR(64) | 爬虫 | 上游 `tag`，可能为空，页面显示成小标签 |
| `color` | VARCHAR(32) | 爬虫 | 上游 `color`（如 `red`），目前只存档 |
| `sorts` | DOUBLE | 爬虫 | 上游 `sorts` 排序权重，目前只存档 |
| `hot_value` | VARCHAR(64) | 爬虫 | 上游 `hot_value`，一律按字符串存（上游会给 `"1.749410"`） |
| `kind` | VARCHAR(16) | 爬虫 | 见下方判定规则 |
| `collected_at` | DATETIME(3) | 爬虫 | 本次抓取写入时间，**UTC**，同一批用同一个值 |
| `read_at` | DATETIME(3) | 期货站 | 标记已读时间，**UTC**；写一次不再变 |

## 时间口径

- 两个时间列都是 **UTC 的 `DATETIME(3)`**，不带时区。`DATETIME` 而不是 `TIMESTAMP`：`TIMESTAMP` 会被会话时区转换，还有 2038 上限。
- 爬虫写入：`datetime.now(timezone.utc)` 格式化成 `YYYY-MM-DD HH:MM:SS.mmm`。
- 期货站写入 `read_at` 时用同样的 UTC 字符串，不用 MySQL 的 `NOW()`（`NOW()` 是会话时区的时间）。
- 期货站读取时用 mysql2 的 `dateStrings: true`，拿到原始字符串后补 `T`/`Z` 变成 ISO 时间给前端；前端统一按 `Asia/Shanghai` 显示。

## kind 判定规则（按 URL 前缀，爬虫侧执行）

| URL 前缀 | kind | 页面位置 |
| --- | --- | --- |
| `https://news.10jqka.com.cn/deep-topic/` | `deep` | 深度专题 · 深度研究 |
| `https://fupage.10jqka.com.cn/community/m/detail.html` | `community` | 深度专题 · 社区长文 |
| 其余 | `news` | 逐条阅读 + 历史列表 |

判定只在爬虫里做一次（`main.py` 的 `kind_from_url`），期货站不做二次判断，避免两套规则漂移。

## 入库规则

- 一次抓取 = 一个事务。全部成功才 `COMMIT`，中途出错 `ROLLBACK`，不会留下半批数据。
- 写入语句固定为：

```sql
INSERT INTO fut_news (url, title, tag, color, sorts, hot_value, kind, collected_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE id = id
```

- 命中唯一键时 `id = id` 是空更新：**不改标题、不动 `read_at`、不换 `id`**。所以反复抓同一批热点不会把读过的文章变回未读，也不会打乱历史列表顺序（列表按 `id DESC` 排序）。
- `ON DUPLICATE KEY UPDATE` 而不是 `INSERT IGNORE`：`INSERT IGNORE` 会把主键冲突之外的错误（比如数据截断）也吞掉，静默丢数据。
- 计数口径：`rowcount == 1` 记为新增，`== 0` 记为重复，累加成「新增 N 条 / 重复 M 条」。

## 上游字段映射

`GET https://ftapi.10jqka.com.cn/futgwapi/domain/news/content/hot_list/v1/list` 返回：

```json
{"code":0,"msg":"success","data":[{"title":"…","url":"https://…","tag":"专题","color":"red","sorts":2,"hot_value":"0"}]}
```

只有同时满足下面条件的行才入库，其余计入「跳过」：

1. `title` 是非空字符串；
2. `url` 是 `https`；
3. URL 不带用户名/密码、不带显式端口；
4. 主机名是 `10jqka.com.cn` 或 `*.10jqka.com.cn`。

第 3、4 条是为了后面能把 `url` 直接塞进页面的 `<iframe>`：只允许内嵌同花顺自己的 https 页面。

## 权限

| 账号 | 需要 | 用途 |
| --- | --- | --- |
| 爬虫用的账号（`DB_USER`） | `SELECT, INSERT, UPDATE` | 建表后写入与去重 |
| 期货站用的账号（同一个 `DB_USER`） | `SELECT, UPDATE` | 读列表、写 `read_at` |

两张表共用一个 `ysd` 账号，权限已经够用；如果以后给期货站换成只读账号，要单独放行 `fut_news` 的 `UPDATE`，否则「标为已读」会 503。

## 常用查询

```sql
-- 总数、未读数、最近一次采集时间
SELECT COUNT(*) AS total, COUNT(read_at) AS read_count, MAX(collected_at) AS last_collected FROM fut_news;

-- 最新 10 条
SELECT id, kind, collected_at, read_at, title FROM fut_news ORDER BY id DESC LIMIT 10;

-- 按类型统计
SELECT kind, COUNT(*) AS total, COUNT(read_at) AS read_count FROM fut_news GROUP BY kind;

-- 每小时的新增条数（看爬虫有没有在干活）
SELECT DATE_FORMAT(collected_at, '%Y-%m-%d %H:00') AS hour, COUNT(*) AS n
FROM fut_news GROUP BY hour ORDER BY hour DESC LIMIT 24;

-- 确认唯一键存在
SHOW INDEX FROM fut_news WHERE Key_name = 'uk_fut_news_url';
```

## 维护约定

- 加列用 `ALTER TABLE fut_news ADD COLUMN ...`，列一律可空或有默认值，**不要新增 `NOT NULL` 且无默认值的列**：爬虫仍在按旧字段清单写入，会直接失败。
- 不要改 `url` 的唯一键属性；去重完全依赖它。
- 不要用 `TRUNCATE`：期货站的已读状态存在 `read_at` 上，清表等于把阅读记录也清了。
- 改完结构同步更新两份说明文件，以及期货项目 `display/server/news-store.js` 里的列名。
