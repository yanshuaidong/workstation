#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货市场涨跌幅TOP10合约数据获取
数据来源：从MySQL数据库的 hist_* 表中查询计算

指标说明：
- 量比：当日成交量 / 过去5日平均成交量，反映当日成交活跃程度
- 持仓日变化：(今日持仓 - 昨日持仓) / 昨日持仓 * 100%
- 持仓5日变化：(今日持仓 - 5日前持仓) / 5日前持仓 * 100%
"""

import json
from datetime import datetime, timedelta
import os
import sys
import pymysql
import sqlite3
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# 阿里云MySQL数据库配置（news_red_telegraph、news_process_tracking）
MYSQL_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}

# 本地SQLite数据库路径（analysis_task）
SQLITE_DB_PATH = Path(__file__).parent.parent / "db" / "crawler.db"

# contracts_main.json 路径（品种名称映射，当前文件夹下）
CONTRACTS_JSON_PATH = Path(__file__).parent / "contracts_main.json"


def load_symbol_name_mapping():
    """
    加载 contracts_main.json，建立 symbol -> name 的映射
    
    Returns:
        dict: {symbol_lower: name} 的映射字典
    """
    try:
        if not CONTRACTS_JSON_PATH.exists():
            logger.warning(f"contracts_main.json 不存在: {CONTRACTS_JSON_PATH}")
            return {}
        
        with open(CONTRACTS_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        mapping = {}
        for contract in data.get("contracts_main", []):
            symbol = contract.get("symbol", "").lower()
            name = contract.get("name", "")
            if symbol and name:
                mapping[symbol] = name
        
        logger.debug(f"已加载 {len(mapping)} 个品种名称映射")
        return mapping
    except Exception as e:
        logger.error(f"加载 contracts_main.json 失败: {e}")
        return {}


def calculate_volume_ratio(today_volume, hist_volumes):
    """
    计算量比（Volume Ratio）
    量比 = 当日成交量 / 过去N日平均成交量
    
    Args:
        today_volume: 当日成交量
        hist_volumes: 历史成交量列表（最近5日，不包含今日）
    
    Returns:
        float: 量比值，如果无法计算返回 None
    """
    if not hist_volumes or today_volume is None:
        return None
    
    # 过滤掉无效值
    valid_volumes = [v for v in hist_volumes if v and v > 0]
    if not valid_volumes:
        return None
    
    avg_volume = sum(valid_volumes) / len(valid_volumes)
    if avg_volume == 0:
        return None
    
    return round(today_volume / avg_volume, 2)


def calculate_oi_change_rate(today_oi, yesterday_oi):
    """
    计算持仓量日变化率
    持仓日变化率 = (今日持仓 - 昨日持仓) / 昨日持仓 * 100%
    
    Args:
        today_oi: 今日持仓量
        yesterday_oi: 昨日持仓量
    
    Returns:
        float: 持仓量日变化率（百分比），如果无法计算返回 None
    """
    if today_oi is None or yesterday_oi is None or yesterday_oi == 0:
        return None
    
    return round((today_oi - yesterday_oi) / yesterday_oi * 100, 2)


def calculate_oi_5day_change_rate(today_oi, oi_5day_ago):
    """
    计算持仓量5日变化率
    持仓5日变化率 = (今日持仓 - 5日前持仓) / 5日前持仓 * 100%
    
    Args:
        today_oi: 今日持仓量
        oi_5day_ago: 5日前持仓量
    
    Returns:
        float: 持仓量5日变化率（百分比），如果无法计算返回 None
    """
    if today_oi is None or oi_5day_ago is None or oi_5day_ago == 0:
        return None
    
    return round((today_oi - oi_5day_ago) / oi_5day_ago * 100, 2)


def interpret_volume_ratio(volume_ratio):
    """
    解读量比指标
    
    Args:
        volume_ratio: 量比值
    
    Returns:
        tuple: (强弱等级, 描述文本)
        强弱等级: 2=显著放量, 1=放量, 0=正常, -1=缩量, -2=显著缩量
    """
    if volume_ratio is None:
        return (0, "数据不足")
    
    # 量比 = 当日成交量 / 5日均量，用百分比形式更直观
    pct = volume_ratio * 100
    
    if volume_ratio >= 3.0:
        return (2, f"显著放量(为5日均量的{pct:.0f}%)")
    elif volume_ratio >= 2.0:
        return (2, f"放量明显(为5日均量的{pct:.0f}%)")
    elif volume_ratio >= 1.5:
        return (1, f"温和放量(为5日均量的{pct:.0f}%)")
    elif volume_ratio >= 0.8:
        return (0, f"成交正常(为5日均量的{pct:.0f}%)")
    elif volume_ratio >= 0.5:
        return (-1, f"温和缩量(为5日均量的{pct:.0f}%)")
    else:
        return (-2, f"显著缩量(为5日均量的{pct:.0f}%)")


def interpret_oi_change(oi_day_change, oi_5day_change):
    """
    解读持仓量变化
    
    Args:
        oi_day_change: 持仓量日变化率（%）
        oi_5day_change: 持仓量5日变化率（%）
    
    Returns:
        tuple: (强弱等级, 描述文本)
        强弱等级: 2=大幅增仓, 1=增仓, 0=平稳, -1=减仓, -2=大幅减仓
    """
    # 优先使用日变化率判断
    change = oi_day_change if oi_day_change is not None else oi_5day_change
    
    if change is None:
        return (0, "数据不足")
    
    # 构建描述文本
    day_text = f"日变{oi_day_change:+.1f}%" if oi_day_change is not None else ""
    five_day_text = f"5日变{oi_5day_change:+.1f}%" if oi_5day_change is not None else ""
    
    if day_text and five_day_text:
        detail = f"{day_text}, {five_day_text}"
    else:
        detail = day_text or five_day_text
    
    # 日变化判断
    if oi_day_change is not None:
        if oi_day_change >= 5:
            return (2, f"大幅增仓({detail})")
        elif oi_day_change >= 2:
            return (1, f"增仓({detail})")
        elif oi_day_change <= -5:
            return (-2, f"大幅减仓({detail})")
        elif oi_day_change <= -2:
            return (-1, f"减仓({detail})")
        else:
            return (0, f"持仓平稳({detail})")
    
    # 如果日变化无数据，使用5日变化
    if oi_5day_change is not None:
        if oi_5day_change >= 10:
            return (2, f"5日大幅增仓({detail})")
        elif oi_5day_change >= 5:
            return (1, f"5日增仓({detail})")
        elif oi_5day_change <= -10:
            return (-2, f"5日大幅减仓({detail})")
        elif oi_5day_change <= -5:
            return (-1, f"5日减仓({detail})")
        else:
            return (0, f"5日持仓平稳({detail})")
    
    return (0, "数据不足")


def fetch_futures_top10():
    """
    从数据库获取期货市场今日涨跌幅数据
    查询所有 hist_* 表，获取今日的涨跌幅数据，并计算量价仓指标
    
    Returns:
        list: 数据列表，格式为 [
            {
                "symbol": "合约代码",
                "name": "品种名称",
                "price": "价格",
                "change_pct": 涨跌幅,
                "volume": 成交量,
                "open_interest": 持仓量,
                "volume_ratio": 量比,
                "oi_day_change": 持仓日变化率,
                "oi_5day_change": 持仓5日变化率,
                "volume_desc": 成交量描述,
                "oi_desc": 持仓量描述
            },
            ...
        ]
    """
    conn = None
    cursor = None
    
    try:
        # 加载品种名称映射
        symbol_name_mapping = load_symbol_name_mapping()
        
        logger.info("正在连接数据库...")
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # 获取今天的日期
        today = datetime.now().strftime('%Y-%m-%d')
        # 计算历史日期范围（获取最近10个交易日用于计算指标）
        date_start = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
        logger.info(f"查询日期: {today}，历史数据起始: {date_start}")
        
        # 1. 获取所有 hist_ 开头的表
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME LIKE 'hist_%%'
        """, (MYSQL_CONFIG['database'],))
        
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"找到 {len(tables)} 个期货数据表")
        
        if not tables:
            logger.warning("数据库中没有找到期货数据表")
            return None
        
        # 2. 从每个表查询今日数据及历史数据
        all_data = []
        for table_name in tables:
            # 从表名提取品种代码（去掉 hist_ 前缀）
            symbol_lower = table_name.replace('hist_', '')
            symbol = symbol_lower.upper()
            
            # 获取品种中文名称
            name = symbol_name_mapping.get(symbol_lower, symbol)
            
            try:
                # 查询最近10个交易日的数据，按日期降序排列
                cursor.execute(f"""
                    SELECT trade_date, close_price, change_pct, volume, open_interest 
                    FROM {table_name} 
                    WHERE trade_date >= %s
                    ORDER BY trade_date DESC
                    LIMIT 10
                """, (date_start,))
                
                rows = cursor.fetchall()
                if not rows:
                    continue
                
                # 检查第一条是否是今日数据
                latest_row = rows[0]
                if str(latest_row[0]) != today:
                    logger.debug(f"{symbol} 今日无数据，最新日期: {latest_row[0]}")
                    continue
                
                # 今日数据
                close_price = latest_row[1] if latest_row[1] is not None else 0
                change_pct = float(latest_row[2]) if latest_row[2] is not None else 0
                today_volume = latest_row[3] if latest_row[3] is not None else 0
                today_oi = latest_row[4] if latest_row[4] is not None else 0
                
                # 历史数据（不包含今日）
                hist_rows = rows[1:]  # 昨日及之前的数据
                
                # 计算量比（使用5日平均）
                hist_volumes = [r[3] for r in hist_rows[:5] if r[3] is not None]
                volume_ratio = calculate_volume_ratio(today_volume, hist_volumes)
                
                # 计算持仓量日变化率（与昨日对比）
                yesterday_oi = hist_rows[0][4] if hist_rows and hist_rows[0][4] is not None else None
                oi_day_change = calculate_oi_change_rate(today_oi, yesterday_oi)
                
                # 计算持仓量5日变化率（与5日前对比）
                oi_5day_ago = hist_rows[4][4] if len(hist_rows) >= 5 and hist_rows[4][4] is not None else None
                oi_5day_change = calculate_oi_5day_change_rate(today_oi, oi_5day_ago)
                
                # 生成描述文本
                volume_level, volume_desc = interpret_volume_ratio(volume_ratio)
                oi_level, oi_desc = interpret_oi_change(oi_day_change, oi_5day_change)
                
                # 构建数据字典
                data_item = {
                    "symbol": symbol,
                    "name": name,
                    "price": str(close_price),
                    "change_pct": change_pct,
                    "volume": today_volume,
                    "open_interest": today_oi,
                    "volume_ratio": volume_ratio,
                    "oi_day_change": oi_day_change,
                    "oi_5day_change": oi_5day_change,
                    "volume_level": volume_level,
                    "oi_level": oi_level,
                    "volume_desc": volume_desc,
                    "oi_desc": oi_desc
                }
                all_data.append(data_item)
                
            except Exception as e:
                logger.debug(f"查询表 {table_name} 失败: {e}")
                continue
        
        logger.info(f"获取到 {len(all_data)} 个品种的今日数据")
        
        return all_data
        
    except Exception as e:
        logger.error(f"数据库查询失败: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def filter_top10(data):
    """
    筛选涨跌幅前10名合约
    规则：
    1. 涨幅必须超过1%（>1）
    2. 跌幅必须大于-1%（<-1）
    3. 取涨幅最大的5个和跌幅最大的5个
    
    数据格式: [
        {
            "symbol": "合约代码",
            "name": "品种名称",
            "price": "价格",
            "change_pct": 涨跌幅,
            "volume": 成交量,
            "open_interest": 持仓量,
            "volume_ratio": 量比,
            "oi_day_change": 持仓日变化率,
            "oi_5day_change": 持仓5日变化率,
            "volume_desc": 成交量描述,
            "oi_desc": 持仓量描述
        },
        ...
    ]
    """
    if not data or not isinstance(data, list):
        return None
    
    # 过滤有效数据
    valid_data = []
    for item in data:
        if isinstance(item, dict) and "change_pct" in item:
            try:
                change_pct = float(item["change_pct"])
                valid_data.append({
                    "contract": item.get("symbol", ""),
                    "name": item.get("name", item.get("symbol", "")),
                    "price": item.get("price", "0"),
                    "change_pct": change_pct,
                    "volume": item.get("volume", 0),
                    "open_interest": item.get("open_interest", 0),
                    "volume_ratio": item.get("volume_ratio"),
                    "oi_day_change": item.get("oi_day_change"),
                    "oi_5day_change": item.get("oi_5day_change"),
                    "volume_level": item.get("volume_level", 0),
                    "oi_level": item.get("oi_level", 0),
                    "volume_desc": item.get("volume_desc", "数据不足"),
                    "oi_desc": item.get("oi_desc", "数据不足")
                })
            except (ValueError, KeyError):
                continue
    
    # 分离涨幅和跌幅数据
    gainers = [item for item in valid_data if item["change_pct"] > 1.0]  # 涨幅>1%
    losers = [item for item in valid_data if item["change_pct"] < -1.0]  # 跌幅<-1%
    
    # 排序：涨幅从大到小，跌幅从小到大
    gainers.sort(key=lambda x: x["change_pct"], reverse=True)
    losers.sort(key=lambda x: x["change_pct"])
    
    # 取前5个
    top_gainers = gainers[:5]
    top_losers = losers[:5]
    
    # 组合结果
    result = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S"),
        "summary": {
            "total_contracts": len(valid_data),
            "gainers_count": len(top_gainers),
            "losers_count": len(top_losers)
        },
        "top_gainers": top_gainers,
        "top_losers": top_losers
    }
    
    return result


def get_mysql_connection():
    """获取MySQL数据库连接"""
    return pymysql.connect(**MYSQL_CONFIG)


def get_sqlite_connection():
    """获取SQLite数据库连接"""
    if not SQLITE_DB_PATH.exists():
        logger.warning(f"⚠️ SQLite数据库不存在: {SQLITE_DB_PATH}")
        logger.info("正在自动初始化数据库...")
        # 尝试自动初始化数据库
        try:
            db_dir = SQLITE_DB_PATH.parent
            sys.path.insert(0, str(db_dir))
            from init_db import init_db  # type: ignore
            init_db()
            logger.info("✅ 数据库初始化成功")
        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}")
            raise
    
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row  # 支持字典式访问
    return conn


def format_volume_number(volume):
    """
    格式化成交量数字，使其更易读
    """
    if volume is None:
        return "N/A"
    if volume >= 10000:
        return f"{volume/10000:.1f}万手"
    return f"{volume}手"


def format_content(filtered_data):
    """
    格式化涨跌幅数据为内容文本（包含量价仓分析）
    """
    lines = []
    lines.append(f"【期货涨跌幅TOP10统计】")
    lines.append(f"日期: {filtered_data['date']} {filtered_data['time']}")
    lines.append(f"总合约数: {filtered_data['summary']['total_contracts']}")
    lines.append("")
    
    # 指标说明
    lines.append("【指标说明】")
    lines.append("• 量比：当日成交量/5日均量，>1.5放量，<0.8缩量")
    lines.append("• 持仓变化：正值增仓（多空博弈加剧），负值减仓（趋势可能减弱）")
    lines.append("")
    
    # 涨幅TOP5
    lines.append("=" * 70)
    lines.append("【涨幅TOP5】（涨幅>1%）")
    lines.append("=" * 70)
    for i, item in enumerate(filtered_data['top_gainers'], 1):
        name = item.get('name', item['contract'])
        volume_desc = item.get('volume_desc', '')
        oi_desc = item.get('oi_desc', '')
        
        lines.append(f"{i}. {name}({item['contract']})")
        lines.append(f"   价格: {item['price']} | 涨幅: +{item['change_pct']:.2f}%")
        lines.append(f"   成交: {volume_desc} | 持仓: {oi_desc}")
        lines.append("")
    
    # 跌幅TOP5
    lines.append("=" * 70)
    lines.append("【跌幅TOP5】（跌幅<-1%）")
    lines.append("=" * 70)
    for i, item in enumerate(filtered_data['top_losers'], 1):
        name = item.get('name', item['contract'])
        volume_desc = item.get('volume_desc', '')
        oi_desc = item.get('oi_desc', '')
        
        lines.append(f"{i}. {name}({item['contract']})")
        lines.append(f"   价格: {item['price']} | 跌幅: {item['change_pct']:.2f}%")
        lines.append(f"   成交: {volume_desc} | 持仓: {oi_desc}")
        lines.append("")
    
    return "\n".join(lines)


def save_to_database(filtered_data):
    """
    保存数据到数据库
    1. MySQL: news_red_telegraph 和 news_process_tracking（阿里云）
    2. SQLite: analysis_task（本地）
    """
    if filtered_data is None:
        logger.error("没有数据可保存")
        return False
    
    mysql_conn = None
    mysql_cursor = None
    sqlite_conn = None
    sqlite_cursor = None
    news_id = None
    
    try:
        # 生成ctime（当前时间戳，秒级）
        ctime = int(datetime.now().timestamp())
        
        # 生成标题
        today = datetime.now()
        title = f"期货市场涨跌幅TOP10统计 {today.strftime('%Y年%m月%d日')}"
        analysis_title = f"{title}分析"  # 用于analysis_task的标题
        
        # 格式化内容
        content = format_content(filtered_data)
        
        # ========== 第一部分：MySQL数据库操作 ==========
        logger.info("正在连接MySQL数据库...")
        mysql_conn = get_mysql_connection()
        mysql_cursor = mysql_conn.cursor()
        
        # 1. 插入 news_red_telegraph 表
        logger.info("正在插入 news_red_telegraph 表...")
        mysql_cursor.execute("""
            INSERT INTO news_red_telegraph 
            (ctime, title, content, ai_analysis, message_score, message_label, message_type, market_react)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            ctime,
            title,
            content,
            "暂无分析",
            6,  # 默认评分
            "hard",  # 默认标签
            "每日涨跌TOP5统计",
            None  # market_react 留空
        ))
        
        news_id = mysql_cursor.lastrowid
        logger.info(f"✅ news_red_telegraph 插入成功，ID: {news_id}")
        
        # 2. 插入 news_process_tracking 表
        logger.info("正在插入 news_process_tracking 表...")
        mysql_cursor.execute("""
            INSERT INTO news_process_tracking 
            (news_id, ctime, is_reviewed)
            VALUES (%s, %s, %s)
        """, (
            news_id,
            ctime,
            0  # 默认未审核
        ))
        logger.info(f"✅ news_process_tracking 插入成功")
        
        # 提交MySQL事务
        mysql_conn.commit()
        logger.info("✅ MySQL数据入库成功")
        
        # ========== 第二部分：SQLite数据库操作 ==========
        logger.info("正在连接SQLite数据库...")
        sqlite_conn = get_sqlite_connection()
        sqlite_cursor = sqlite_conn.cursor()
        
        # 3. 创建AI分析任务到 analysis_task 表（本地SQLite）
        logger.info("正在创建AI分析任务（本地数据库）...")
        
        # 生成AI分析提示词
        prompt = f"""【中国期货市场涨跌幅TOP10异动分析任务】

=== 今日数据 ===
{content}

=== 量价仓指标说明 ===
• 量比：当日成交量 / 5日平均成交量
  - >2.0: 显著放量（市场关注度高）
  - 1.5-2.0: 放量（资金活跃度提升）
  - 0.8-1.5: 正常（市场平稳运行）
  - 0.5-0.8: 缩量（观望情绪浓）
  - <0.5: 显著缩量（市场参与度低）

• 持仓变化率：
  - 正值（增仓）：新资金入场，多空博弈加剧
  - 负值（减仓）：资金离场，趋势动能可能减弱

=== 分析任务要求 ===

【第一部分：新闻驱动分析】（必须使用浏览器搜索工具）
⚠️ 重要提示：严禁凭空想象和胡编乱造！必须使用浏览器搜索工具查询今日相关新闻！

1. 新闻搜索（必须执行）：
   - 针对涨幅TOP5和跌幅TOP5的每个品种，使用浏览器搜索工具查询今日（{filtered_data['date']}）的相关新闻
   - 搜索关键词示例："[品种名称] {filtered_data['date']} 期货 涨跌"、"[品种名称] 最新消息"
   - 重点关注：官方政策、供需变化、产业链事件、宏观经济数据、突发事件等

2. 新闻真实性判断：
   - 区分"市场小作文"（未经证实的传闻、市场情绪炒作）vs "真实重大事件"（官方发布、权威媒体报道）
   - 如果搜索到的新闻较少或不相关，明确说明：这可能只是市场的正常波动，无明显新闻驱动

3. 驱动因素总结：
   - 涨幅品种：归纳共性驱动因素（如：政策利好、供应短缺、需求激增、资金炒作等）
   - 跌幅品种：归纳共性压制因素（如：政策利空、供应过剩、需求下滑、技术面压力等）
   - 行业关联性：是否存在某个产业链或板块的集体异动

【第二部分：重点品种评分】⚠️ 只评有"硬事件"的品种！
不是所有TOP10品种都值得评分，只对搜索到"硬事件"的品种进行详细评分。

=== 评分标准 ===
总分10分 = 消息面硬度（5分）+ 技术面配合（5分）

1. 消息面硬度（占比50%，满分5分）：
   - 5分：硬事件（有数字+有时间+有来源+已发生，满足3条以上）
   - 4分：较硬事件（满足2条）
   - 3分：一般事件（仅1条，但逻辑清晰）
   - 1-2分：软事件（模糊预期、传闻、旧闻）
   - 0分：无消息驱动

2. 技术面配合（占比50%，满分5分）：
   - 增仓：+1.5分（持仓变化率>0）
   - 放量：+1.5分（量比>1.5）
   - 大K线：+2分（涨幅>2%为大阳线，跌幅>2%为大阴线）
   
⚠️ 重要原则：消息够"硬"就可以推荐！
即使技术面暂时没有完全配合（如还没放量、还没增仓），只要事件足够硬，也值得关注和推荐。
因为硬事件往往是行情的启动点，技术面会随后跟上。

=== 输出要求 ===
只对有"硬事件"驱动的品种进行评分，其他品种简要说明"无硬事件驱动"即可跳过。

对有硬事件的品种给出：
- 综合评分：X/10分（消息面X分 + 技术面X分）
- 交易方向：做多/做空
- 消息面：[硬事件核心内容，必须有数字/时间/来源]
- 技术面：[增仓/减仓、放量/缩量、K线形态]
- 推荐理由：[为什么值得交易]

【第三部分：可执行交易推荐】⚠️ 核心逻辑：硬事件驱动！
从TOP10中筛选出有"硬事件"驱动的品种，作为今日可执行的短线交易标的。

=== 筛选逻辑（消息面优先）===
1. 【必要条件】消息面必须是"硬事件"（这是入场的核心理由！）
2. 【加分条件】技术面配合：增仓 + 放量 + 大阳线/大阴线（配合越好，仓位越重）

⚠️ 只要消息够硬，即使技术面暂时表现一般，也可以推荐！
   - 硬事件 + 技术面完全配合 → 强烈推荐（可重仓）
   - 硬事件 + 技术面部分配合 → 推荐（可轻仓）
   - 硬事件 + 技术面暂无配合 → 可关注（等待技术面确认再加仓）

=== "硬事件"判断标准 ===
✅ 可交易的"硬事件"特征（必须同时满足2条以上）：
   • 有具体数字：产量削减X吨、关税X%、产量下降X%、金额X亿等
   • 有明确时间：X月X日生效、X年X月执行等
   • 有可查来源：路透社、官方政策、权威媒体、上市公司公告等
   • 事件已发生：总统被捕、矿山停产、事故已发生等确定性事件
   • 逻辑链清晰：消息→影响→价格方向，一目了然

❌ 不可交易的"软事件"特征（有任一条即排除）：
   • 无具体数字：只有"可能"、"预期"、"或将"等模糊表述
   • 时间不明确：没有具体执行时间节点
   • 来源不可靠：市场传闻、小作文、未经证实的消息
   • 旧闻炒作：之前的消息延续，不做延伸只做启动
   • 嘴炮言论：政客口头表态但无实际行动

=== 硬事件判断示例 ===
【可交易示例】
1. 沪镍：印尼2026年镍矿配额计划削减至2.5亿湿吨（路透社报道）→ 有数字+有来源+看起来就很真
2. 碳酸锂：电池出口退税2026-04-01下调至6%，2027-01-01取消 → 有时间+有额度+有逻辑
3. 黄金：美国2月1日对欧洲加征10%关税，6月升至25%；欧盟准备反制930亿欧元 → 有数字+有时间
4. 原油：委内瑞拉总统马杜罗被捕，地区局势动荡 → 事件已发生+确定性高
5. 铜：格拉斯伯格矿2025年9月泥石流事故停产，预计2026年铜产量下降35% → 有数字+官方+已发生

【不可交易示例】
1. 欧线：红海通航"不确定"，以色列对伊朗"强硬信号" → 没有具体的点，太模糊
2. PTA：库存低位、价差修复"预期"、"潜在"停车 → 都是预期，没有实际消息
3. 碳酸锂：之前宜春注销采矿权的消息 → 旧闻，不做延伸只做启动
4. 乙二醇：开工高位、待投产多 → 没有爆点，对主力不够诱惑
5. 黄金：川普说要买格林兰岛 → 嘴炮而已，没实质行动

=== 输出要求 ===
从TOP10中筛选有"硬事件"驱动的品种进行推荐。
如果没有硬事件驱动的品种，明确说明"今日无硬事件驱动的可执行标的"。

【输出格式】
一、新闻驱动分析
（涨幅品种）
[品种1]: [搜索到的新闻摘要] → [硬事件✅/软事件❌] → [驱动因素判断]
...

（跌幅品种）
[品种1]: [搜索到的新闻摘要] → [硬事件✅/软事件❌] → [驱动因素判断]
...

二、重点品种评分（仅评有硬事件的品种）
⚠️ 无硬事件的品种直接跳过，不做详细评分

【有硬事件驱动的品种】
1. [品种] | 总分：X/10分（消息面X分 + 技术面X分）| 方向：做多/做空
   消息面(X/5分)：[硬事件核心内容，必须有数字/时间/来源]
   技术面(X/5分)：增仓[是/否] + 放量[量比X] + K线[涨跌幅X%]
   推荐理由：[为什么值得交易]

【无硬事件的品种】（简要说明）
[品种2]、[品种3]...：无硬事件驱动，跳过评分

三、今日可执行推荐（硬事件驱动）
⚠️ 核心逻辑：只要消息够硬，就值得推荐！技术面配合度决定仓位大小。

【强烈推荐 ★★★】硬事件 + 技术面完全配合（增仓+放量+大K线）→ 可重仓
[品种名称]
├─ 硬事件：[一句话描述，必须包含具体数字/时间/来源]
├─ 技术面：✅增仓[X%] ✅放量[量比X] ✅大K线[涨跌幅X%]
├─ 方向：做多/做空
├─ 仓位建议：可重仓
└─ 风险提示：[30字以内]

【推荐 ★★】硬事件 + 技术面部分配合 → 可轻仓
[品种名称]
├─ 硬事件：[一句话描述，必须包含具体数字/时间/来源]
├─ 技术面：[✅/❌增仓] [✅/❌放量] [✅/❌大K线]（说明哪些配合哪些未配合）
├─ 方向：做多/做空
├─ 仓位建议：轻仓试探
└─ 风险提示：[30字以内]

【可关注 ★】硬事件 + 技术面暂无配合 → 等待确认
[品种名称]
├─ 硬事件：[一句话描述，必须包含具体数字/时间/来源]
├─ 技术面：❌暂无配合（说明具体情况）
├─ 方向：做多/做空
├─ 操作建议：关注，等技术面确认后再入场
└─ 关注要点：[等待什么信号再入场]

【无推荐情况】
如无硬事件驱动的品种，输出：
"今日无硬事件驱动的可执行标的。TOP10品种的消息面均为软事件/无消息驱动，不具备短线交易价值。"

⚠️ 再次强调：
1. 必须使用浏览器搜索工具查询新闻，严禁凭空想象！
2. 消息面硬度是入场的核心理由，技术面决定仓位大小！
3. 硬事件是行情启动点，即使技术面暂时没配合也值得关注！"""
        
        sqlite_cursor.execute("""
            INSERT INTO analysis_task 
            (title, prompt, news_time, gemini_analyzed)
            VALUES (?, ?, ?, ?)
        """, (
            analysis_title,
            prompt,
            today.strftime('%Y-%m-%d %H:%M:%S'),
            1  # gemini_analyzed设为1，表示不需要Gemini分析
        ))
        
        task_id = sqlite_cursor.lastrowid
        logger.info(f"✅ analysis_task 插入成功（本地数据库），任务ID: {task_id}")
        
        # 提交SQLite事务
        sqlite_conn.commit()
        logger.info("✅ SQLite数据入库成功")
        
        logger.info("=" * 50)
        logger.info("✅ 所有数据入库完成！")
        logger.info(f"   MySQL news_id: {news_id}")
        logger.info(f"   SQLite task_id: {task_id}")
        logger.info("=" * 50)
        return True
        
    except pymysql.err.IntegrityError as e:
        logger.warning(f"MySQL数据已存在（ctime重复），跳过插入: {e}")
        if mysql_conn:
            mysql_conn.rollback()
        return False
    except sqlite3.IntegrityError as e:
        logger.warning(f"SQLite数据已存在，跳过插入: {e}")
        if sqlite_conn:
            sqlite_conn.rollback()
        return False
    except Exception as e:
        logger.error(f"数据库操作失败: {e}", exc_info=True)
        if mysql_conn:
            mysql_conn.rollback()
        if sqlite_conn:
            sqlite_conn.rollback()
        return False
    finally:
        if mysql_cursor:
            mysql_cursor.close()
        if mysql_conn:
            mysql_conn.close()
        if sqlite_cursor:
            sqlite_cursor.close()
        if sqlite_conn:
            sqlite_conn.close()


def save_to_json(filtered_data, filename=None):
    """
    保存数据到JSON文件（仅用于测试）
    """
    if filtered_data is None:
        logger.warning("没有数据可保存")
        return False
    
    # 创建data目录（如果不存在）
    os.makedirs("data", exist_ok=True)
    
    # 生成文件名
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/futures_top10_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)
        logger.info(f"测试数据已保存到: {filename}")
        return True
    except Exception as e:
        logger.error(f"保存文件失败: {e}")
        return False


def main():
    """
    主函数
    """
    logger.info("=" * 50)
    logger.info("期货市场涨跌幅TOP10数据获取")
    logger.info("=" * 50)
    
    # 获取原始数据
    raw_data = fetch_futures_top10()
    
    if raw_data:
        # 筛选TOP10
        logger.info("正在筛选涨跌幅TOP10...")
        filtered_data = filter_top10(raw_data)
        
        if filtered_data:
            # 显示结果
            logger.info("\n" + "=" * 50)
            logger.info("数据统计:")
            logger.info(f"日期: {filtered_data['date']} {filtered_data['time']}")
            logger.info(f"总合约数: {filtered_data['summary']['total_contracts']}")
            logger.info(f"涨幅>1%的合约: {filtered_data['summary']['gainers_count']} 个（取前5）")
            logger.info(f"跌幅<-1%的合约: {filtered_data['summary']['losers_count']} 个（取前5）")
            
            # 显示涨幅TOP5
            logger.info("\n" + "=" * 70)
            logger.info("【涨幅TOP5】")
            logger.info("-" * 70)
            for i, item in enumerate(filtered_data['top_gainers'], 1):
                name = item.get('name', item['contract'])
                volume_desc = item.get('volume_desc', '')
                oi_desc = item.get('oi_desc', '')
                logger.info(f"{i}. {name}({item['contract']}) | 价格: {item['price']} | 涨幅: +{item['change_pct']:.2f}%")
                logger.info(f"   成交: {volume_desc} | 持仓: {oi_desc}")
            
            # 显示跌幅TOP5
            logger.info("\n" + "=" * 70)
            logger.info("【跌幅TOP5】")
            logger.info("-" * 70)
            for i, item in enumerate(filtered_data['top_losers'], 1):
                name = item.get('name', item['contract'])
                volume_desc = item.get('volume_desc', '')
                oi_desc = item.get('oi_desc', '')
                logger.info(f"{i}. {name}({item['contract']}) | 价格: {item['price']} | 跌幅: {item['change_pct']:.2f}%")
                logger.info(f"   成交: {volume_desc} | 持仓: {oi_desc}")
            
            # 入库到MySQL数据库
            logger.info("\n" + "=" * 50)
            logger.info("正在保存数据到阿里云MySQL数据库...")
            if save_to_database(filtered_data):
                logger.info("✅ 数据入库成功！")
            else:
                logger.error("❌ 数据入库失败")
            
            # 保存本地JSON文件（仅用于测试）
            # save_to_json(filtered_data, "data/futures_top10_latest.json")
        else:
            logger.error("数据筛选失败")
    else:
        logger.error("数据获取失败")
    
    logger.info("\n" + "=" * 50)


if __name__ == "__main__":
    main()
