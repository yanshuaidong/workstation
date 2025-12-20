#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机构持仓数据更新脚本（独立版本）

功能：
1. 从 jiaoyikecha.com 获取国泰君安的持仓数据
2. 检查数据库中现有数据的最新日期
3. 从最新日期的下一天开始增量更新到今天
4. 如果数据库为空，从默认起始日期开始更新

使用方法：
    python update.py
"""

import sqlite3
import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# 禁用 SSL 警告
import warnings
warnings.filterwarnings('ignore', module='urllib3')

# ============================================================
# 配置
# ============================================================
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / 'institution.db'

# API 配置
API_URL = 'https://www.jiaoyikecha.com/ajax/broker_positions.php?v=8bcd6872'
BROKER = '国泰君安'

# 默认起始日期（数据库为空时使用）
DEFAULT_START_DAYS_AGO = 365


# ============================================================
# 数据库操作
# ============================================================
def get_db_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_all_table_names(conn: sqlite3.Connection) -> List[str]:
    """获取数据库中所有的表名（品种表）"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
    """)
    return [row[0] for row in cursor.fetchall()]


def get_latest_date_from_db(conn: sqlite3.Connection) -> Optional[str]:
    """获取数据库中所有表的最新日期"""
    tables = get_all_table_names(conn)
    
    if not tables:
        return None
    
    cursor = conn.cursor()
    latest_dates = []
    
    for table in tables:
        try:
            cursor.execute(f'SELECT MAX(trade_date) FROM "{table}"')
            result = cursor.fetchone()
            if result and result[0]:
                latest_dates.append(result[0])
        except sqlite3.Error:
            continue
    
    return max(latest_dates) if latest_dates else None


def create_table_if_not_exists(conn: sqlite3.Connection, table_name: str):
    """如果表不存在则创建"""
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            trade_date TEXT PRIMARY KEY,
            total_buy INTEGER NOT NULL,
            total_ss INTEGER NOT NULL,
            total_buy_chge INTEGER NOT NULL,
            total_ss_chge INTEGER NOT NULL,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    conn.commit()


def save_position_data(conn: sqlite3.Connection, trade_date: str, 
                       name: str, total_buy: int, total_ss: int, 
                       total_buy_chge: int, total_ss_chge: int):
    """保存单个品种的持仓数据"""
    create_table_if_not_exists(conn, name)
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor = conn.cursor()
    
    cursor.execute(f'''
        INSERT OR REPLACE INTO "{name}" 
        (trade_date, total_buy, total_ss, total_buy_chge, total_ss_chge, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (trade_date, total_buy, total_ss, total_buy_chge, total_ss_chge, now, now))


# ============================================================
# 数据获取
# ============================================================
def fetch_positions(date: str, verbose: bool = True) -> Optional[Dict]:
    """
    获取指定日期的持仓数据
    
    Args:
        date: 日期字符串 (YYYY-MM-DD)
        verbose: 是否打印详细信息
    
    Returns:
        API 返回的 JSON 数据，失败返回 None
    """
    headers = {
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.jiaoyikecha.com',
        'pragma': 'no-cache',
        'referer': 'https://www.jiaoyikecha.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }
    
    data = {
        'date': date,
        'broker': BROKER
    }
    
    try:
        response = requests.post(API_URL, headers=headers, data=data, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            if verbose:
                print(f"请求失败，状态码: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        if verbose:
            print(f"请求异常: {e}")
        return None
    except json.JSONDecodeError:
        if verbose:
            print("响应不是有效的 JSON")
        return None


def process_and_save_data(conn: sqlite3.Connection, data: Dict, trade_date: str) -> int:
    """
    处理 API 返回的数据并保存到数据库
    
    Args:
        conn: 数据库连接
        data: API 返回的数据
        trade_date: 交易日期
    
    Returns:
        保存的品种数量
    """
    if not data or data.get('code') != 0:
        return 0
    
    data_info = data.get('data', {})
    positions = data_info.get('positions', {})
    
    if not positions:
        return 0
    
    # 处理 positions 可能是列表或字典的情况
    if isinstance(positions, list):
        positions_dict = {}
        for item in positions:
            name = item.get('name', '未知')
            if name not in positions_dict:
                positions_dict[name] = []
            positions_dict[name].append(item)
        positions = positions_dict
    
    saved_count = 0
    
    for name, contracts in positions.items():
        if not contracts:
            continue
        
        # 汇总该品种所有合约的持仓
        total_buy = 0
        total_ss = 0
        total_buy_chge = 0
        total_ss_chge = 0
        
        for contract in contracts:
            total_buy += contract.get('buy', 0) or 0
            total_ss += contract.get('ss', 0) or 0
            total_buy_chge += contract.get('buy_chge', 0) or 0
            total_ss_chge += contract.get('ss_chge', 0) or 0
        
        # 保存到数据库
        save_position_data(conn, trade_date, name, 
                          total_buy, total_ss, total_buy_chge, total_ss_chge)
        saved_count += 1
    
    conn.commit()
    return saved_count


# ============================================================
# 工具函数
# ============================================================
def get_date_range(start_date: str, end_date: str) -> List[str]:
    """生成日期范围列表"""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    return dates


def print_database_status(conn: sqlite3.Connection):
    """打印数据库当前状态"""
    print("\n" + "=" * 60)
    print("📊 数据库当前状态")
    print("=" * 60)
    
    tables = get_all_table_names(conn)
    
    if not tables:
        print("  数据库为空，尚无任何品种数据")
        return
    
    print(f"  品种数量: {len(tables)}")
    print(f"  数据库路径: {DB_PATH}")
    
    # 获取最新日期
    latest_date = get_latest_date_from_db(conn)
    if latest_date:
        print(f"  最新数据日期: {latest_date}")
    
    # 显示部分品种的数据范围
    print("\n  部分品种数据范围（最多显示5个）:")
    cursor = conn.cursor()
    for table in tables[:5]:
        try:
            cursor.execute(f'SELECT MIN(trade_date), MAX(trade_date), COUNT(*) FROM "{table}"')
            result = cursor.fetchone()
            if result and result[0]:
                print(f"    {table}: {result[0]} ~ {result[1]} ({result[2]} 条记录)")
        except sqlite3.Error:
            continue
    
    if len(tables) > 5:
        print(f"    ... 还有 {len(tables) - 5} 个品种")


# ============================================================
# 主函数
# ============================================================
def main():
    """主函数：增量更新数据"""
    print("=" * 60)
    print("🔄 机构持仓数据增量更新")
    print("=" * 60)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 连接数据库
    conn = get_db_connection()
    
    try:
        # 打印数据库状态
        print_database_status(conn)
        
        # 获取最新日期
        latest_date = get_latest_date_from_db(conn)
        
        # 确定起始日期
        if latest_date:
            start_date_obj = datetime.strptime(latest_date, '%Y-%m-%d') + timedelta(days=1)
            start_date = start_date_obj.strftime('%Y-%m-%d')
            print(f"\n✓ 检测到已有数据，从 {start_date} 开始更新")
        else:
            start_date_obj = datetime.now() - timedelta(days=DEFAULT_START_DAYS_AGO)
            start_date = start_date_obj.strftime('%Y-%m-%d')
            print(f"\n⚠ 数据库为空，从默认起始日期 {start_date} 开始")
        
        # 结束日期为今天
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 如果起始日期晚于今天，说明数据已经是最新的
        if start_date > end_date:
            print("\n" + "=" * 60)
            print("✓ 数据已是最新，无需更新")
            print("=" * 60)
            return
        
        print(f"\n📅 更新日期范围: {start_date} 至 {end_date}")
        
        # 获取所有需要更新的日期
        all_dates = get_date_range(start_date, end_date)
        print(f"📋 共 {len(all_dates)} 个日期需要处理")
        print()
        
        # 统计信息
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        # 开始更新
        print("=" * 60)
        print("开始更新数据...")
        print("=" * 60)
        
        for idx, target_date in enumerate(all_dates, 1):
            print(f"[{idx}/{len(all_dates)}] {target_date}", end=' ... ')
            
            # 获取数据
            data = fetch_positions(target_date, verbose=False)
            
            if not data:
                print("✗ 获取失败")
                fail_count += 1
                continue
            
            # 检查 API 返回码
            if data.get('code') != 0:
                print(f"✗ API错误: {data.get('msg', '未知')}")
                fail_count += 1
                continue
            
            # 检查是否有数据
            data_info = data.get('data', {})
            positions = data_info.get('positions', {})
            
            if isinstance(positions, (list, dict)) and len(positions) == 0:
                print("⚠ 无数据（非交易日）")
                skip_count += 1
                continue
            
            # 处理并保存数据
            saved_count = process_and_save_data(conn, data, target_date)
            
            if saved_count > 0:
                print(f"✓ 已保存 {saved_count} 个品种")
                success_count += 1
            else:
                print("⚠ 无有效数据")
                skip_count += 1
        
        # 打印更新统计
        print("\n" + "=" * 60)
        print("📊 更新完成统计")
        print("=" * 60)
        print(f"  ✓ 成功: {success_count} 个交易日")
        print(f"  ✗ 失败: {fail_count} 个")
        print(f"  ⚠ 跳过: {skip_count} 个（非交易日或无数据）")
        print(f"  📅 总计: {len(all_dates)} 个日期")
        print("=" * 60)
        
        # 再次打印数据库状态
        if success_count > 0:
            print_database_status(conn)
        
        print("\n✓ 更新完成！")
        
    finally:
        conn.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断执行")
    except Exception as e:
        print(f"\n\n✗ 执行出错: {e}")
        import traceback
        traceback.print_exc()
