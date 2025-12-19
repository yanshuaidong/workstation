#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机构持仓数据更新脚本

功能：
1. 检查数据库中现有数据的最新日期
2. 从最新日期的下一天开始更新到今天
3. 如果数据库为空，从默认起始日期开始更新
4. 每天执行一次，保持数据最新

使用方法：
    python updata.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3

# 添加 quantlab/institution 到路径，以便导入 getdata 模块
SCRIPT_DIR = Path(__file__).parent  # database/institution/
WORKSPACE_DIR = SCRIPT_DIR.parent.parent  # workstation/
QUANTLAB_DIR = WORKSPACE_DIR / 'quantlab' / 'institution'
sys.path.insert(0, str(QUANTLAB_DIR))

# 导入 getdata 模块的功能
from getdata import (
    DB_PATH,
    init_database,
    get_db_connection,
    fetch_today_positions,
    save_positions_to_db,
    get_date_range
)


def get_all_table_names(conn: sqlite3.Connection) -> list:
    """
    获取数据库中所有的表名（品种表）
    
    Args:
        conn: 数据库连接
    
    Returns:
        表名列表
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    return tables


def get_latest_date_from_db(conn: sqlite3.Connection) -> str:
    """
    获取数据库中所有表的最新日期（取所有表中最新的那个日期）
    
    Args:
        conn: 数据库连接
    
    Returns:
        最新日期字符串 (YYYY-MM-DD)，如果数据库为空返回 None
    """
    tables = get_all_table_names(conn)
    
    if not tables:
        return None
    
    cursor = conn.cursor()
    latest_dates = []
    
    for table in tables:
        try:
            # 使用引号包裹表名，防止特殊字符
            cursor.execute(f'SELECT MAX(trade_date) FROM "{table}"')
            result = cursor.fetchone()
            if result and result[0]:
                latest_dates.append(result[0])
        except sqlite3.Error as e:
            print(f"  ⚠ 查询表 {table} 失败: {e}")
            continue
    
    if not latest_dates:
        return None
    
    # 返回所有表中最新的日期
    return max(latest_dates)


def get_table_date_range(conn: sqlite3.Connection, table_name: str) -> tuple:
    """
    获取指定表的日期范围
    
    Args:
        conn: 数据库连接
        table_name: 表名
    
    Returns:
        (最早日期, 最晚日期) 或 (None, None)
    """
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT MIN(trade_date), MAX(trade_date) FROM "{table_name}"')
        result = cursor.fetchone()
        return result if result else (None, None)
    except sqlite3.Error:
        return (None, None)


def print_database_status():
    """打印数据库当前状态"""
    print("\n" + "=" * 60)
    print("📊 数据库当前状态")
    print("=" * 60)
    
    with get_db_connection() as conn:
        tables = get_all_table_names(conn)
        
        if not tables:
            print("  数据库为空，尚无任何品种数据")
            return None
        
        print(f"  品种数量: {len(tables)}")
        print(f"  数据库路径: {DB_PATH}")
        
        # 获取最新日期
        latest_date = get_latest_date_from_db(conn)
        if latest_date:
            print(f"  最新数据日期: {latest_date}")
        
        # 显示部分品种的数据范围
        print("\n  部分品种数据范围（最多显示5个）:")
        for table in tables[:5]:
            min_date, max_date = get_table_date_range(conn, table)
            if min_date and max_date:
                cursor = conn.cursor()
                cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                count = cursor.fetchone()[0]
                print(f"    {table}: {min_date} ~ {max_date} ({count} 条记录)")
        
        if len(tables) > 5:
            print(f"    ... 还有 {len(tables) - 5} 个品种")
        
        return latest_date


def main():
    """主函数：增量更新数据"""
    print("=" * 60)
    print("🔄 机构持仓数据增量更新")
    print("=" * 60)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化数据库
    init_database()
    
    # 打印数据库状态
    latest_date = print_database_status()
    
    # 确定起始日期
    if latest_date:
        # 从最新日期的下一天开始
        start_date_obj = datetime.strptime(latest_date, '%Y-%m-%d') + timedelta(days=1)
        start_date = start_date_obj.strftime('%Y-%m-%d')
        print(f"\n✓ 检测到已有数据，从 {start_date} 开始更新")
    else:
        # 如果数据库为空，从默认日期开始（比如1年前）
        start_date_obj = datetime.now() - timedelta(days=365)
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
    
    with get_db_connection() as conn:
        for idx, target_date in enumerate(all_dates, 1):
            print(f"[{idx}/{len(all_dates)}] {target_date}", end=' ... ')
            
            # 获取数据（静默模式）
            data = fetch_today_positions(broker='国泰君安', date=target_date, verbose=False)
            
            if not data:
                print("✗ 获取失败")
                skip_count += 1
                continue
            
            # 检查数据有效性
            if data.get('code') != 0:
                print(f"✗ API错误: {data.get('msg', '未知')}")
                fail_count += 1
                continue
            
            data_info = data.get('data', {})
            positions = data_info.get('positions', {})
            
            # 检查是否有数据
            if isinstance(positions, (list, dict)) and len(positions) == 0:
                print("⚠ 无数据（非交易日）")
                skip_count += 1
                continue
            
            # 保存到数据库
            if save_positions_to_db(conn, data, target_date):
                print("✓ 已保存")
                success_count += 1
            else:
                print("✗ 保存失败")
                fail_count += 1
    
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
        print_database_status()
    
    print("\n✓ 更新完成！")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断执行")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ 执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

