#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货市场事件驱动筛选器
筛选逻辑：
- 涨幅>1% + 放量（比昨天成交量大）+ 增仓（比昨天持仓多），取涨幅最大的8个
- 跌幅<-1% + 放量（比昨天成交量大）+ 增仓（比昨天持仓多），取跌幅最大的8个

目的：为突发事件驱动交易策略筛选技术面符合条件的品种，生成AI分析提示词入库
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

# 阿里云MySQL数据库配置
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

# contracts_main.json 路径（使用futurestop10文件夹下的）
CONTRACTS_JSON_PATH = Path(__file__).parent.parent / "futurestop10" / "contracts_main.json"


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


def get_mysql_connection():
    """获取MySQL数据库连接"""
    return pymysql.connect(**MYSQL_CONFIG)


def get_sqlite_connection():
    """获取SQLite数据库连接"""
    if not SQLITE_DB_PATH.exists():
        logger.warning(f"⚠️ SQLite数据库不存在: {SQLITE_DB_PATH}")
        logger.info("正在自动初始化数据库...")
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


def fetch_futures_data():
    """
    从数据库获取期货市场今日及昨日数据
    用于判断放量和增仓
    
    Returns:
        list: 数据列表，包含今日和昨日的成交量、持仓量对比
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
        # 计算历史日期范围（获取最近5个交易日）
        date_start = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        logger.info(f"查询日期: {today}，历史数据起始: {date_start}")
        
        # 获取所有 hist_ 开头的表
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
        
        # 从每个表查询今日和昨日数据
        all_data = []
        for table_name in tables:
            # 从表名提取品种代码（去掉 hist_ 前缀）
            symbol_lower = table_name.replace('hist_', '')
            symbol = symbol_lower.upper()
            
            # 获取品种中文名称
            name = symbol_name_mapping.get(symbol_lower, symbol)
            
            try:
                # 查询最近几个交易日的数据，按日期降序排列
                cursor.execute(f"""
                    SELECT trade_date, close_price, change_pct, volume, open_interest 
                    FROM {table_name} 
                    WHERE trade_date >= %s
                    ORDER BY trade_date DESC
                    LIMIT 5
                """, (date_start,))
                
                rows = cursor.fetchall()
                if len(rows) < 2:
                    # 至少需要今日和昨日两天数据
                    continue
                
                # 检查第一条是否是今日数据
                latest_row = rows[0]
                if str(latest_row[0]) != today:
                    logger.debug(f"{symbol} 今日无数据，最新日期: {latest_row[0]}")
                    continue
                
                # 今日数据
                today_data = {
                    'date': str(latest_row[0]),
                    'close_price': float(latest_row[1]) if latest_row[1] is not None else 0,
                    'change_pct': float(latest_row[2]) if latest_row[2] is not None else 0,
                    'volume': int(latest_row[3]) if latest_row[3] is not None else 0,
                    'open_interest': int(latest_row[4]) if latest_row[4] is not None else 0
                }
                
                # 昨日数据
                yesterday_row = rows[1]
                yesterday_data = {
                    'date': str(yesterday_row[0]),
                    'volume': int(yesterday_row[3]) if yesterday_row[3] is not None else 0,
                    'open_interest': int(yesterday_row[4]) if yesterday_row[4] is not None else 0
                }
                
                # 判断放量：今日成交量 > 昨日成交量
                is_volume_increase = today_data['volume'] > yesterday_data['volume']
                
                # 判断增仓：今日持仓量 > 昨日持仓量
                is_oi_increase = today_data['open_interest'] > yesterday_data['open_interest']
                
                # 计算变化幅度
                volume_change = 0
                if yesterday_data['volume'] > 0:
                    volume_change = round((today_data['volume'] - yesterday_data['volume']) / yesterday_data['volume'] * 100, 2)
                
                oi_change = 0
                if yesterday_data['open_interest'] > 0:
                    oi_change = round((today_data['open_interest'] - yesterday_data['open_interest']) / yesterday_data['open_interest'] * 100, 2)
                
                # 构建数据字典
                data_item = {
                    "symbol": symbol,
                    "name": name,
                    "price": str(today_data['close_price']),
                    "change_pct": today_data['change_pct'],
                    "today_volume": today_data['volume'],
                    "yesterday_volume": yesterday_data['volume'],
                    "today_oi": today_data['open_interest'],
                    "yesterday_oi": yesterday_data['open_interest'],
                    "is_volume_increase": is_volume_increase,
                    "is_oi_increase": is_oi_increase,
                    "volume_change_pct": volume_change,
                    "oi_change_pct": oi_change
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


def filter_event_driven_contracts(data):
    """
    筛选事件驱动交易候选合约
    规则：
    1. 涨幅>1%，取涨幅榜前8，再从中筛选放量且增仓的
    2. 跌幅<-1%，取跌幅榜前8，再从中筛选放量且增仓的
    
    Args:
        data: 期货数据列表
        
    Returns:
        dict: 筛选结果
    """
    if not data or not isinstance(data, list):
        return None
    
    # 第一步：筛选涨幅>1%的，按涨幅排序取前8
    gainers_all = [item for item in data if item["change_pct"] > 1.0]
    gainers_all.sort(key=lambda x: x["change_pct"], reverse=True)
    gainers_top8 = gainers_all[:8]
    
    # 第二步：在前8中筛选放量且增仓的
    top_gainers = [
        item for item in gainers_top8
        if item["is_volume_increase"] and item["is_oi_increase"]
    ]
    
    # 第一步：筛选跌幅<-1%的，按跌幅排序取前8
    losers_all = [item for item in data if item["change_pct"] < -1.0]
    losers_all.sort(key=lambda x: x["change_pct"])  # 跌幅大的在前
    losers_top8 = losers_all[:8]
    
    # 第二步：在前8中筛选放量且增仓的
    top_losers = [
        item for item in losers_top8
        if item["is_volume_increase"] and item["is_oi_increase"]
    ]
    
    # 记录筛选统计
    logger.info(f"涨幅>1%的品种: {len(gainers_all)} 个")
    logger.info(f"涨幅榜前8: {len(gainers_top8)} 个")
    logger.info(f"前8中放量且增仓: {len(top_gainers)} 个")
    logger.info(f"跌幅<-1%的品种: {len(losers_all)} 个")
    logger.info(f"跌幅榜前8: {len(losers_top8)} 个")
    logger.info(f"前8中放量且增仓: {len(top_losers)} 个")
    
    # 组合结果
    result = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S"),
        "summary": {
            "total_contracts": len(data),
            "gainers_above_1pct": len(gainers_all),
            "gainers_top8": len(gainers_top8),
            "gainers_final": len(top_gainers),
            "losers_below_neg1pct": len(losers_all),
            "losers_top8": len(losers_top8),
            "losers_final": len(top_losers)
        },
        "top_gainers": top_gainers,
        "top_losers": top_losers
    }
    
    return result


def generate_single_prompt(item, direction):
    """
    为单个品种生成AI分析提示词
    
    Args:
        item: 品种数据
        direction: "多" 或 "空"
        
    Returns:
        str: 提示词
    """
    name = item.get('name', item['symbol'])
    symbol = item['symbol']
    change_pct = item['change_pct']
    volume_change = item.get('volume_change_pct', 0)
    oi_change = item.get('oi_change_pct', 0)
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    prompt = f"""{name}（{symbol}）今日{direction}方技术面异动明显：涨跌幅{change_pct:+.2f}%，放量{volume_change:+.2f}%，增仓{oi_change:+.2f}%。

请搜索{today_str}当天与{name}相关的突发事件或重要消息。

输出要求：
1. 如果找到当日事件：说明事件名称和简要内容
2. 如果没有当日事件：说明可能的原因推测"""
    return prompt


def generate_batch_prompt(filtered_data):
    """
    生成批量分析的提示词（包含所有筛选出的品种）
    
    Args:
        filtered_data: 筛选后的数据
        
    Returns:
        str: 批量分析提示词
    """
    date = filtered_data['date']
    
    # 构建品种列表
    gainers_list = []
    for item in filtered_data['top_gainers']:
        gainers_list.append(f"- {item['name']}({item['symbol']}): {item['change_pct']:+.2f}%")
    
    losers_list = []
    for item in filtered_data['top_losers']:
        losers_list.append(f"- {item['name']}({item['symbol']}): {item['change_pct']:.2f}%")
    
    prompt = f"""以下期货品种在{date}出现技术面异动（涨跌幅榜前8且放量增仓）：

做多候选：
{chr(10).join(gainers_list) if gainers_list else '无'}

做空候选：
{chr(10).join(losers_list) if losers_list else '无'}

请分别搜索每个品种当天的突发事件或重要消息，说明：
1. 如果有当日事件：事件名称和简要内容
2. 如果没有当日事件：可能的原因推测"""
    return prompt


def save_to_database(filtered_data):
    """
    保存AI分析任务到SQLite数据库
    如果有符合条件的品种，创建一个包含所有品种的批量分析任务
    
    Args:
        filtered_data: 筛选后的数据
        
    Returns:
        bool: 是否成功
    """
    if filtered_data is None:
        logger.error("没有数据可保存")
        return False
    
    # 检查是否有符合条件的品种
    if not filtered_data['top_gainers'] and not filtered_data['top_losers']:
        logger.warning("没有符合筛选条件的品种，跳过入库")
        return False
    
    sqlite_conn = None
    sqlite_cursor = None
    
    try:
        logger.info("正在连接SQLite数据库...")
        sqlite_conn = get_sqlite_connection()
        sqlite_cursor = sqlite_conn.cursor()
        
        today = datetime.now()
        
        # 统计符合条件的品种数量
        total_symbols = len(filtered_data['top_gainers']) + len(filtered_data['top_losers'])
        
        # 创建一个批量分析任务（包含所有品种）
        batch_prompt = generate_batch_prompt(filtered_data)
        batch_title = f"期货事件驱动分析({total_symbols}个品种) - {today.strftime('%Y-%m-%d')}"
        
        sqlite_cursor.execute("""
            INSERT INTO analysis_task 
            (title, prompt, news_time, gemini_analyzed, chatgpt_analyzed, doubao_analyzed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            batch_title,
            batch_prompt,
            today.strftime('%Y-%m-%d %H:%M:%S'),
            0,
            0,
            0
        ))
        logger.info(f"✅ 创建分析任务: {batch_title}")
        
        # 提交事务
        sqlite_conn.commit()
        
        logger.info("=" * 50)
        logger.info(f"✅ 已创建1个分析任务，包含 {total_symbols} 个品种")
        logger.info(f"   做多候选: {len(filtered_data['top_gainers'])} 个")
        logger.info(f"   做空候选: {len(filtered_data['top_losers'])} 个")
        logger.info("=" * 50)
        
        return True
        
    except sqlite3.IntegrityError as e:
        logger.warning(f"SQLite数据已存在，跳过插入: {e}")
        if sqlite_conn:
            sqlite_conn.rollback()
        return False
    except Exception as e:
        logger.error(f"数据库操作失败: {e}", exc_info=True)
        if sqlite_conn:
            sqlite_conn.rollback()
        return False
    finally:
        if sqlite_cursor:
            sqlite_cursor.close()
        if sqlite_conn:
            sqlite_conn.close()


def print_result(filtered_data):
    """
    打印筛选结果
    """
    if not filtered_data:
        logger.error("无数据可显示")
        return
    
    summary = filtered_data['summary']
    
    logger.info("\n" + "=" * 70)
    logger.info("【事件驱动筛选结果】")
    logger.info(f"日期: {filtered_data['date']} {filtered_data['time']}")
    logger.info(f"总合约数: {summary['total_contracts']}")
    logger.info(f"涨幅>1%: {summary['gainers_above_1pct']} 个 → 前8: {summary['gainers_top8']} 个 → 放量增仓: {summary['gainers_final']} 个")
    logger.info(f"跌幅<-1%: {summary['losers_below_neg1pct']} 个 → 前8: {summary['losers_top8']} 个 → 放量增仓: {summary['losers_final']} 个")
    
    # 显示做多候选
    logger.info("\n" + "=" * 70)
    logger.info("【做多候选】涨幅榜前8 + 放量 + 增仓")
    logger.info("-" * 70)
    if filtered_data['top_gainers']:
        for i, item in enumerate(filtered_data['top_gainers'], 1):
            logger.info(f"{i}. {item['name']}({item['symbol']})")
            logger.info(f"   涨幅: +{item['change_pct']:.2f}% | 价格: {item['price']}")
            logger.info(f"   放量: {item['volume_change_pct']:+.2f}% | 增仓: {item['oi_change_pct']:+.2f}%")
    else:
        logger.info("   无符合条件的品种")
    
    # 显示做空候选
    logger.info("\n" + "=" * 70)
    logger.info("【做空候选】跌幅榜前8 + 放量 + 增仓")
    logger.info("-" * 70)
    if filtered_data['top_losers']:
        for i, item in enumerate(filtered_data['top_losers'], 1):
            logger.info(f"{i}. {item['name']}({item['symbol']})")
            logger.info(f"   跌幅: {item['change_pct']:.2f}% | 价格: {item['price']}")
            logger.info(f"   放量: {item['volume_change_pct']:+.2f}% | 增仓: {item['oi_change_pct']:+.2f}%")
    else:
        logger.info("   无符合条件的品种")


def main():
    """
    主函数
    """
    logger.info("=" * 50)
    logger.info("期货市场事件驱动筛选器")
    logger.info("筛选条件: 涨跌幅>1%/<-1% + 放量 + 增仓")
    logger.info("=" * 50)
    
    # 获取原始数据
    raw_data = fetch_futures_data()
    
    if raw_data:
        # 筛选符合条件的品种
        logger.info("正在筛选事件驱动候选品种...")
        filtered_data = filter_event_driven_contracts(raw_data)
        
        if filtered_data:
            # 显示结果
            print_result(filtered_data)
            
            # 入库到SQLite数据库
            logger.info("\n" + "=" * 50)
            logger.info("正在创建AI分析任务...")
            if save_to_database(filtered_data):
                logger.info("✅ 分析任务创建成功！")
            else:
                logger.warning("⚠️ 分析任务创建失败或无符合条件的品种")
        else:
            logger.error("数据筛选失败")
    else:
        logger.error("数据获取失败")
    
    logger.info("\n" + "=" * 50)


if __name__ == "__main__":
    main()
