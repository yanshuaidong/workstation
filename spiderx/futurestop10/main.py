#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货市场涨跌幅TOP10合约数据获取
数据来源：从MySQL数据库的 hist_* 表中查询计算
"""

import json
from datetime import datetime
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


def fetch_futures_top10():
    """
    从数据库获取期货市场今日涨跌幅数据
    查询所有 hist_* 表，获取今日的涨跌幅数据
    
    Returns:
        list: 数据列表，格式为 [[合约代码, 价格, 涨跌幅, 品种名称], ...]
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
        logger.info(f"查询日期: {today}")
        
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
        
        # 2. 从每个表查询今日数据
        all_data = []
        for table_name in tables:
            # 从表名提取品种代码（去掉 hist_ 前缀）
            symbol_lower = table_name.replace('hist_', '')
            symbol = symbol_lower.upper()
            
            # 获取品种中文名称
            name = symbol_name_mapping.get(symbol_lower, symbol)
            
            try:
                cursor.execute(f"""
                    SELECT close_price, change_pct 
                    FROM {table_name} 
                    WHERE trade_date = %s
                """, (today,))
                
                row = cursor.fetchone()
                if row:
                    close_price = row[0] if row[0] is not None else 0
                    change_pct = float(row[1]) if row[1] is not None else 0
                    all_data.append([symbol, str(close_price), change_pct, name])
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
    
    数据格式: [["合约代码", "价格", "涨跌幅", "品种名称"], ...]
    """
    if not data or not isinstance(data, list):
        return None
    
    # 过滤有效数据并转换涨跌幅为浮点数
    valid_data = []
    for item in data:
        if len(item) >= 3:
            try:
                contract = item[0]  # 合约代码
                price = item[1]     # 价格
                change_pct = float(item[2])  # 涨跌幅
                name = item[3] if len(item) >= 4 else contract  # 品种名称
                valid_data.append({
                    "contract": contract,
                    "price": price,
                    "change_pct": change_pct,
                    "name": name
                })
            except (ValueError, IndexError):
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


def format_content(filtered_data):
    """
    格式化涨跌幅数据为内容文本
    """
    lines = []
    lines.append(f"【期货涨跌幅TOP10统计】")
    lines.append(f"日期: {filtered_data['date']} {filtered_data['time']}")
    lines.append(f"总合约数: {filtered_data['summary']['total_contracts']}")
    lines.append("")
    
    # 涨幅TOP5
    lines.append("=" * 60)
    lines.append("【涨幅TOP5】（涨幅>1%）")
    lines.append("=" * 60)
    for i, item in enumerate(filtered_data['top_gainers'], 1):
        name = item.get('name', item['contract'])
        lines.append(f"{i}. {name}({item['contract']}) | 价格: {item['price']} | 涨幅: +{item['change_pct']:.2f}%")
    
    lines.append("")
    
    # 跌幅TOP5
    lines.append("=" * 60)
    lines.append("【跌幅TOP5】（跌幅<-1%）")
    lines.append("=" * 60)
    for i, item in enumerate(filtered_data['top_losers'], 1):
        name = item.get('name', item['contract'])
        lines.append(f"{i}. {name}({item['contract']}) | 价格: {item['price']} | 跌幅: {item['change_pct']:.2f}%")
    
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

【第二部分：短线交易评分】
针对每个涨跌TOP5品种，给出3-10天短线交易推荐评分（1-10分）：

评分标准（综合考虑）：
- 新闻驱动强度：有明确重大利好/利空 → 高分；仅市场情绪炒作 → 低分
- 价格波动幅度：涨跌幅越大，短线机会越明显 → 相对高分
- 持续性判断：基本面支撑强 → 高分；纯技术性或情绪性 → 低分
- 风险评估：消息真实可靠、趋势明确 → 高分；传闻多、不确定性大 → 低分

对每个品种给出：
- 推荐评分：X/10分
- 交易方向：做多/做空
- 推荐理由：简要说明评分依据（50字以内）
- 风险提示：主要风险点（30字以内）

【输出格式】
一、新闻驱动分析
（涨幅品种）
[品种1]: [搜索到的新闻摘要] → [驱动因素判断]
...

（跌幅品种）
[品种1]: [搜索到的新闻摘要] → [驱动因素判断]
...

二、短线交易推荐（3-10天）
涨幅品种：
1. [品种] | 评分：X/10分 | 方向：做多 | 理由：... | 风险：...

跌幅品种：
1. [品种] | 评分：X/10分 | 方向：做空 | 理由：... | 风险：...

三、整体市场研判
[基于新闻搜索结果，总结今日市场整体情绪和短线机会]

⚠️ 再次强调：必须使用浏览器搜索工具查询新闻，严禁凭空想象！如果确实查不到相关新闻，请明确说明。"""
        
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
            logger.info("\n" + "=" * 60)
            logger.info("【涨幅TOP5】")
            logger.info("-" * 60)
            for i, item in enumerate(filtered_data['top_gainers'], 1):
                name = item.get('name', item['contract'])
                logger.info(f"{i}. {name}({item['contract']}) | 价格: {item['price']} | 涨幅: +{item['change_pct']:.2f}%")
            
            # 显示跌幅TOP5
            logger.info("\n" + "=" * 60)
            logger.info("【跌幅TOP5】")
            logger.info("-" * 60)
            for i, item in enumerate(filtered_data['top_losers'], 1):
                name = item.get('name', item['contract'])
                logger.info(f"{i}. {name}({item['contract']}) | 价格: {item['price']} | 跌幅: {item['change_pct']:.2f}%")
            
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
