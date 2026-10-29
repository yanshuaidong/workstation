#!/usr/bin/env python3
"""
同花顺期货热点新闻爬虫

功能：
1. 抓取同花顺期货热点榜 JSON 接口（一次一屏，上游没有翻页参数）
2. 按标题 / URL 规则过滤，只保留同花顺自己的 https 页面
3. 按 URL 去重写入云端 MySQL 的 fut_news 表（重复 URL 不改标题、不动已读状态）
4. 每小时执行一次，供期货项目 /news 页面直接读取

表结构见同目录 fut_news-table.md。

使用方法:
  python main.py once       - 抓一次并写库（默认，不传参数也是这个）
  python main.py schedule   - 调度模式：立即抓一次，之后每小时一次
  python main.py check      - 只检查数据库连接和表结构，不抓取

环境变量：
  数据库连接从 spiderx 上层的 .env 读取（DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME），
  由 db/mysql_config.py 统一解析，不在本文件里写死。
  THS_NEWS_INTERVAL_MINUTES 可选，调度间隔，默认 60 分钟。
"""

import logging
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

import pymysql
import requests

SPIDERX_DIR = Path(__file__).resolve().parent.parent
if str(SPIDERX_DIR) not in sys.path:
    sys.path.insert(0, str(SPIDERX_DIR))

from db.mysql_config import get_mysql_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Windows 控制台默认是 GBK，打印 emoji 会直接抛 UnicodeEncodeError 把进程打死。
# 这里只放宽错误处理（编码不变），服务器是 UTF-8，行为不受影响。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(errors="replace")
        except (ValueError, OSError):
            pass

# ==================== 配置参数 ====================

TABLE = "fut_news"

# 同花顺期货热点榜。上游没有分页参数，一次返回榜单当前这一屏（约 30 条，会变）。
HOT_LIST_URL = "https://ftapi.10jqka.com.cn/futgwapi/domain/news/content/hot_list/v1/list"

# 只内嵌同花顺自己的 https 页面：url 后面会被期货站直接放进 iframe。
NEWS_ROOT_DOMAIN = "10jqka.com.cn"

# 长文与专题单独归入第三个标签页，其余都算普通新闻。
DEEP_TOPIC_PREFIX = "https://news.10jqka.com.cn/deep-topic/"
COMMUNITY_DETAIL_PREFIX = "https://fupage.10jqka.com.cn/community/m/detail.html"
SPECIAL_KINDS = ("deep", "community")

# 请求超时（秒）。上游正常在 1 秒内返回，20 秒是兜底。
REQUEST_TIMEOUT = 20

# 列宽上限，与 fut_news 表定义一致，超长截断而不是让 MySQL 报错。
COLUMN_LIMITS = {"url": 512, "title": 500, "tag": 64, "color": 32, "hot_value": 64}

# 数据库配置（从 spiderx 上层 .env 读取）
DB_CONFIG = get_mysql_config()

# ==================== 时间与字段 ====================


def utc_stamp(offset_seconds=0):
    """返回 UTC 的 'YYYY-MM-DD HH:MM:SS.mmm'，直接写 DATETIME(3)，不经会话时区转换。"""
    moment = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
    return moment.strftime("%Y-%m-%d %H:%M:%S.%f")[:23]


def clip(value, field):
    """按列宽截断，None 原样返回。"""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:COLUMN_LIMITS[field]]


def kind_from_url(url):
    """按 URL 前缀判定新闻类型。判定只在这里做一次，期货站不再二次判断。"""
    if not isinstance(url, str):
        return "news"
    if url.startswith(DEEP_TOPIC_PREFIX):
        return "deep"
    if url.startswith(COMMUNITY_DETAIL_PREFIX):
        return "community"
    return "news"


def normalize_url(raw):
    """只接受同花顺自己的 https 页面，其余返回 None。"""
    if not isinstance(raw, str):
        return None
    url = raw.strip()
    if not url:
        return None
    try:
        parts = urlsplit(url)
        port = parts.port          # 端口写错时这里会抛 ValueError
    except ValueError:
        return None
    if parts.scheme != "https":
        return None
    if parts.username or parts.password:
        return None
    # 显式端口一律拒绝，:443 和省略等价所以放行。
    if port not in (None, 443):
        return None
    host = (parts.hostname or "").lower()
    if host != NEWS_ROOT_DOMAIN and not host.endswith("." + NEWS_ROOT_DOMAIN):
        return None
    return url


def normalize_rows(payload):
    """
    把上游 data 数组转成可入库的行。

    返回 (rows, skipped)：rows 是 dict 列表，skipped 是被规则丢掉的行数。
    """
    rows = []
    skipped = 0
    for item in payload:
        if not isinstance(item, dict):
            skipped += 1
            continue

        title = item.get("title")
        if not isinstance(title, str) or not title.strip():
            skipped += 1
            continue

        url = normalize_url(item.get("url"))
        if url is None:
            skipped += 1
            continue

        hot_value = item.get("hot_value")
        sorts = item.get("sorts")
        rows.append({
            "url": url[:COLUMN_LIMITS["url"]],
            "title": clip(title, "title"),
            "tag": clip(item.get("tag"), "tag"),
            "color": clip(item.get("color"), "color"),
            "sorts": sorts if isinstance(sorts, (int, float)) and not isinstance(sorts, bool) else None,
            "hot_value": None if hot_value is None else str(hot_value)[:COLUMN_LIMITS["hot_value"]],
            "kind": kind_from_url(url),
        })
    return rows, skipped

# ==================== 数据库操作 ====================


def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)


def save_rows(rows):
    """
    一个事务写入整批。

    命中去重键时执行 id = id 的空更新：不改标题、不动 read_at、不换 id。
    返回 (新增条数, 重复条数)。
    """
    if not rows:
        return 0, 0

    insert_sql = f"""
        INSERT INTO {TABLE}
            (url, title, tag, color, sorts, hot_value, kind, collected_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE id = id
    """
    # 同一批用同一个时间：这批新闻属于同一次采集。
    collected_at = utc_stamp()

    conn = get_db_connection()
    cursor = conn.cursor()
    added = 0
    try:
        conn.begin()
        for row in rows:
            cursor.execute(insert_sql, (
                row["url"], row["title"], row["tag"], row["color"],
                row["sorts"], row["hot_value"], row["kind"], collected_at,
            ))
            # 1 = 新插入，0 = 撞唯一键后空更新（重复）
            if cursor.rowcount == 1:
                added += 1
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    return added, len(rows) - added


def check_database():
    """检查连接与表结构，不抓取。返回 (总数, 最近采集时间)。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT COUNT(*) AS total, MAX(collected_at) AS last_collected FROM {TABLE}")
        row = cursor.fetchone()
        return row[0], row[1]
    finally:
        cursor.close()
        conn.close()

# ==================== 抓取 ====================


def fetch_hot_list():
    """请求热点榜单，返回上游 data 数组。任何异常都转成中文 RuntimeError。"""
    headers = {
        "Accept": "application/json",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        # 伪装成同花顺自家页面在调用，少这套头容易被拒。
        "Origin": "https://goodsfu.10jqka.com.cn",
        "Referer": "https://goodsfu.10jqka.com.cn/",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36"
        ),
    }

    try:
        response = requests.get(
            HOT_LIST_URL, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"请求热点接口失败: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(f"热点接口返回 HTTP {response.status_code}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("热点接口返回的不是 JSON") from exc

    if not isinstance(payload, dict) or payload.get("code") != 0:
        code = payload.get("code") if isinstance(payload, dict) else None
        raise RuntimeError(f"热点接口返回失败，code={code}")

    data = payload.get("data")
    if not isinstance(data, list):
        raise RuntimeError("热点接口返回格式异常：data 不是数组")
    return data


def crawl_once():
    """
    完整跑一轮：抓取 → 过滤 → 入库。

    返回 dict：received / skipped / added / duplicates，口径与旧版一致。
    """
    payload = fetch_hot_list()
    received = len(payload)
    rows, skipped = normalize_rows(payload)

    # 上游有数据但一条都不合法，说明接口改版或触发了风控，不能当成功。
    if received > 0 and not rows:
        raise RuntimeError("新闻接口未返回有效的标题与新闻链接")

    added, duplicates = save_rows(rows)
    result = {
        "received": received,
        "skipped": skipped,
        "added": added,
        "duplicates": duplicates,
    }
    logger.info(
        f"采集完成：共 {result['received']} 条，新增 {result['added']} 条，"
        f"重复 {result['duplicates']} 条，跳过 {result['skipped']} 条"
    )
    return result

# ==================== 主程序入口 ====================


def print_usage():
    print("使用方法:")
    print("  python main.py once       - 抓一次并写库（默认）")
    print("  python main.py schedule   - 调度模式：立即抓一次，之后每小时一次")
    print("  python main.py check      - 只检查数据库连接和表结构，不抓取")
    print("")
    print("数据库连接读取 spiderx 上层的 .env（DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME）。")
    print("表结构见同目录 fut_news-table.md。")


def main():
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "once"

    if command in ("-h", "--help", "help"):
        print_usage()
        return 0

    if command == "check":
        try:
            total, last_collected = check_database()
        except pymysql.err.ProgrammingError as exc:
            if exc.args and exc.args[0] == 1146:
                logger.error(f"表 {TABLE} 不存在，请按 fut_news-table.md 里的建表语句建表")
                return 1
            logger.error(f"数据库检查失败: {exc}")
            return 1
        except Exception as exc:
            logger.error(f"数据库检查失败: {exc}")
            return 1
        logger.info(f"数据库连接正常：{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        logger.info(f"表 {TABLE} 共 {total} 条，最近采集时间（UTC）：{last_collected}")
        return 0

    if command == "schedule":
        from scheduler import ThsNewsScheduler
        ThsNewsScheduler().run()
        return 0

    if command == "once":
        try:
            crawl_once()
        except pymysql.err.ProgrammingError as exc:
            if exc.args and exc.args[0] == 1146:
                logger.error(f"表 {TABLE} 不存在，请按 fut_news-table.md 里的建表语句建表")
                return 1
            logger.error(f"写库失败: {exc}")
            logger.error(traceback.format_exc())
            return 1
        except Exception as exc:
            logger.error(f"本轮采集失败: {exc}")
            logger.error(traceback.format_exc())
            return 1
        return 0

    print(f"未知命令: {command}")
    print("")
    print_usage()
    return 1


if __name__ == "__main__":
    sys.exit(main())
