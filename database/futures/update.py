#!/usr/bin/env python3
"""
期货历史数据增量更新工具

自动查询数据库中各品种的最新日期，并从 AkShare 获取增量数据更新到最新

使用方法:
    # 更新所有品种
    python update.py
    
    # 更新指定品种
    python update.py --symbol aum,cum,rbm
    
    # 预览模式（只显示需要更新的数据，不实际更新）
    python update.py --dry-run
    
    # 显示所有品种的最新数据日期
    python update.py --status
"""

import os
import json
import sqlite3
import argparse
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from contextlib import contextmanager

import akshare as ak
import pandas as pd


# 脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 数据库路径
DB_PATH = os.path.join(SCRIPT_DIR, 'futures.db')
# 映射文件路径（在 tools 目录下）
MAPPING_PATH = os.path.join(SCRIPT_DIR, '..', '..', 'tools', '获取期货数据', 'futures_mapping.json')
# 日志文件路径
LOG_PATH = os.path.join(SCRIPT_DIR, 'update.log')


def write_log(message: str):
    """写入日志文件"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")


def load_mapping() -> Dict[str, Any]:
    """加载期货品种映射配置"""
    with open(MAPPING_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


@contextmanager
def get_db_connection():
    """获取数据库连接（上下文管理器，自动关闭）"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    try:
        yield conn
    finally:
        conn.close()


def get_all_hist_tables(conn: sqlite3.Connection) -> List[str]:
    """获取所有历史数据表名"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'hist_%'")
    return [row[0] for row in cursor.fetchall()]


def get_latest_date(conn: sqlite3.Connection, table_name: str) -> Optional[str]:
    """
    获取指定表的最新交易日期
    
    Args:
        conn: 数据库连接
        table_name: 表名 (如 hist_aum)
        
    Returns:
        最新日期字符串 (YYYY-MM-DD) 或 None
    """
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT MAX(trade_date) FROM {table_name}")
        result = cursor.fetchone()
        return result[0] if result and result[0] else None
    except sqlite3.OperationalError:
        return None


def get_all_latest_dates(conn: sqlite3.Connection, mapping: Dict) -> Dict[str, Tuple[str, str, Optional[str]]]:
    """
    获取所有品种的最新日期
    
    Returns:
        Dict: {symbol: (name, table_name, latest_date)}
    """
    futures = mapping.get('futures', {})
    result = {}
    
    for symbol, config in futures.items():
        table_name = config['db_table']
        name = config['name']
        latest_date = get_latest_date(conn, table_name)
        result[symbol] = (name, table_name, latest_date)
    
    return result


def fetch_futures_data(api_symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """
    从 AkShare 获取期货历史数据
    
    Args:
        api_symbol: AkShare API 使用的代码 (如 AU0)
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        
    Returns:
        DataFrame 或 None
    """
    try:
        # 获取期货主连数据
        df = ak.futures_main_sina(symbol=api_symbol)
        
        if df is None or df.empty:
            return None
        
        # 重命名列（AkShare 返回中文列名）
        column_mapping = {
            '日期': 'trade_date',
            '开盘价': 'open_price',
            '最高价': 'high_price',
            '最低价': 'low_price',
            '收盘价': 'close_price',
            '成交量': 'volume',
            '持仓量': 'open_interest',
        }
        
        for cn_col, en_col in column_mapping.items():
            if cn_col in df.columns:
                df.rename(columns={cn_col: en_col}, inplace=True)
        
        # 格式化日期
        if 'trade_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')
        
        # 按日期范围过滤（只取开始日期之后的数据）
        df_filtered = df[(df['trade_date'] > start_date) & (df['trade_date'] <= end_date)]
        
        if df_filtered.empty:
            return None
        
        # 按日期排序
        df_filtered = df_filtered.sort_values('trade_date').reset_index(drop=True)
        
        # 添加入库时间戳
        df_filtered['ingest_ts'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return df_filtered
        
    except Exception as e:
        write_log(f"FETCH_ERROR: {api_symbol} - {e}")
        return None


def insert_data(conn: sqlite3.Connection, table_name: str, df: pd.DataFrame) -> int:
    """
    将数据插入数据库（使用 REPLACE 避免主键冲突）
    
    Args:
        conn: 数据库连接
        table_name: 表名
        df: 数据 DataFrame
        
    Returns:
        插入的记录数
    """
    # 只保留表中存在的列
    valid_columns = [
        'trade_date', 'open_price', 'high_price', 'low_price', 'close_price',
        'price_change', 'change_pct', 'volume', 'open_interest', 'turnover',
        'macd_dif', 'macd_dea', 'macd_histogram', 'rsi_14',
        'kdj_k', 'kdj_d', 'kdj_j',
        'bb_upper', 'bb_middle', 'bb_lower', 'bb_width',
        'recommendation', 'source_ts', 'ingest_ts'
    ]
    
    # 筛选存在的列
    columns_to_insert = [col for col in valid_columns if col in df.columns]
    df_to_insert = df[columns_to_insert].copy()
    
    # 构建 INSERT OR REPLACE 语句
    columns_str = ', '.join(columns_to_insert)
    placeholders = ', '.join(['?' for _ in columns_to_insert])
    sql = f"INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    
    # 批量插入
    cursor = conn.cursor()
    rows = df_to_insert.values.tolist()
    cursor.executemany(sql, rows)
    conn.commit()
    
    return len(rows)


def update_symbol(symbol: str, mapping: Dict, dry_run: bool = False) -> Tuple[bool, int, str]:
    """
    更新单个品种的数据
    
    Args:
        symbol: 品种代码 (如 aum)
        mapping: 映射配置
        dry_run: 是否预览模式
        
    Returns:
        (是否成功, 更新条数, 消息)
    """
    futures_config = mapping.get('futures', {})
    
    # 尝试大小写匹配
    config = futures_config.get(symbol) or futures_config.get(symbol.lower()) or futures_config.get(symbol.upper())
    
    if not config:
        return False, 0, f"未找到品种配置: {symbol}"
    
    name = config['name']
    api_symbol = config['api_symbol']
    db_table = config['db_table']
    
    # 获取数据库中的最新日期
    with get_db_connection() as conn:
        latest_date = get_latest_date(conn, db_table)
    
    if not latest_date:
        return False, 0, f"{symbol} ({name}) - 表不存在或无数据，请先运行初始入库"
    
    # 计算更新范围：从最新日期到今天
    today = datetime.now().strftime('%Y-%m-%d')
    
    if latest_date >= today:
        return True, 0, f"{symbol} ({name}) - 已是最新 ({latest_date})"
    
    if dry_run:
        return True, 0, f"{symbol} ({name}) - 需要更新: {latest_date} -> {today}"
    
    # 获取增量数据
    df = fetch_futures_data(api_symbol, latest_date, today)
    
    if df is None or df.empty:
        write_log(f"NO_NEW_DATA: {symbol} ({name}) - {latest_date} 之后无新数据")
        return True, 0, f"{symbol} ({name}) - 无新数据 ({latest_date})"
    
    # 插入数据
    try:
        with get_db_connection() as conn:
            count = insert_data(conn, db_table, df)
        
        new_latest = df['trade_date'].max()
        write_log(f"OK: {symbol} ({name}) -> {db_table} - 新增 {count} 条 ({latest_date} -> {new_latest})")
        return True, count, f"{symbol} ({name}) - 新增 {count} 条 ({latest_date} -> {new_latest})"
        
    except Exception as e:
        write_log(f"FAIL: {symbol} ({name}) - {e}")
        return False, 0, f"{symbol} ({name}) - 更新失败: {e}"


def show_status(mapping: Dict):
    """显示所有品种的数据状态"""
    with get_db_connection() as conn:
        all_dates = get_all_latest_dates(conn, mapping)
    
    print("\n📊 期货数据状态:")
    print("-" * 80)
    print(f"{'品种':<8} {'名称':<16} {'数据库表':<15} {'最新日期':<12} {'状态':<10}")
    print("-" * 80)
    
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    need_update = 0
    no_data = 0
    up_to_date = 0
    
    for symbol, (name, table_name, latest_date) in sorted(all_dates.items(), key=lambda x: x[0].lower()):
        if latest_date is None:
            status = "❌ 无数据"
            no_data += 1
        elif latest_date >= yesterday:
            status = "✅ 最新"
            up_to_date += 1
        else:
            days_behind = (datetime.strptime(today, '%Y-%m-%d') - datetime.strptime(latest_date, '%Y-%m-%d')).days
            status = f"⚠️ 落后{days_behind}天"
            need_update += 1
        
        date_str = latest_date if latest_date else "-"
        print(f"{symbol:<8} {name:<16} {table_name:<15} {date_str:<12} {status:<10}")
    
    print("-" * 80)
    print(f"📈 统计: 最新 {up_to_date}, 需更新 {need_update}, 无数据 {no_data}, 共 {len(all_dates)} 个品种")


def main():
    parser = argparse.ArgumentParser(
        description='期货历史数据增量更新工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 更新所有品种
  python update.py
  
  # 更新指定品种
  python update.py --symbol aum,cum,rbm
  
  # 预览模式（只显示需要更新的数据，不实际更新）
  python update.py --dry-run
  
  # 显示所有品种的最新数据日期
  python update.py --status
        """
    )
    
    parser.add_argument('--symbol', '-s', type=str,
                        help='品种代码，多个用逗号分隔 (如 aum,cum,rbm)')
    parser.add_argument('--status', action='store_true',
                        help='显示所有品种的数据状态')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='预览模式，不实际更新数据')
    
    args = parser.parse_args()
    
    # 检查数据库文件是否存在
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return 1
    
    # 加载映射配置
    try:
        mapping = load_mapping()
    except FileNotFoundError:
        print(f"❌ 映射文件不存在: {MAPPING_PATH}")
        return 1
    except json.JSONDecodeError as e:
        print(f"❌ 映射文件格式错误: {e}")
        return 1
    
    # 显示状态
    if args.status:
        show_status(mapping)
        return 0
    
    # 确定要更新的品种
    if args.symbol:
        symbols = [s.strip() for s in args.symbol.split(',')]
    else:
        # 获取数据库中已有的表，只更新这些品种
        with get_db_connection() as conn:
            tables = get_all_hist_tables(conn)
        
        # 从表名提取品种代码 (hist_aum -> aum)
        futures_config = mapping.get('futures', {})
        symbols = []
        for symbol, config in futures_config.items():
            if config['db_table'] in tables:
                symbols.append(symbol)
    
    if not symbols:
        print("❌ 没有找到需要更新的品种")
        return 1
    
    # 开始更新
    mode = "[预览模式] " if args.dry_run else ""
    print(f"\n🔄 {mode}开始更新 {len(symbols)} 个品种...")
    print(f"   数据库: {DB_PATH}")
    print(f"   日志文件: {LOG_PATH}")
    print("=" * 70)
    
    # 写入日志头
    if not args.dry_run:
        write_log("=" * 50)
        write_log(f"开始增量更新: {len(symbols)} 个品种")
    
    success_count = 0
    fail_count = 0
    total_new_records = 0
    failed_symbols = []
    
    for symbol in symbols:
        success, count, message = update_symbol(symbol, mapping, args.dry_run)
        print(f"  {message}")
        
        if success:
            success_count += 1
            total_new_records += count
        else:
            fail_count += 1
            failed_symbols.append(symbol)
    
    # 写入汇总日志
    if not args.dry_run:
        write_log(f"完成: 成功 {success_count}, 失败 {fail_count}, 新增 {total_new_records} 条")
        if failed_symbols:
            write_log(f"失败列表: {', '.join(failed_symbols)}")
        write_log("=" * 50)
        
        # 执行 WAL checkpoint，合并 WAL 文件到主数据库
        try:
            with get_db_connection() as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except Exception as e:
            write_log(f"WAL checkpoint 失败: {e}")
    
    # 汇总
    print("=" * 70)
    print(f"✅ 完成! 成功: {success_count}, 失败: {fail_count}, 新增记录: {total_new_records} 条")
    if failed_symbols:
        print(f"❌ 失败品种: {', '.join(failed_symbols)}")
    
    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    exit(main())
