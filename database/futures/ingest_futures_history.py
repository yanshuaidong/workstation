#!/usr/bin/env python3
"""
期货历史数据入库工具

从 AkShare 获取期货主连历史行情数据并存入 SQLite 数据库
默认日期范围: 2018-01-01 ~ 2024-12-31

使用方法:
    # 获取单个品种 (使用默认日期)
    python ingest_futures_history.py --symbol aum
    
    # 获取多个品种
    python ingest_futures_history.py --symbol aum,cum,rbm
    
    # 获取所有品种
    python ingest_futures_history.py --all
    
    # 指定日期范围
    python ingest_futures_history.py --symbol aum --start 2023-01-01 --end 2023-12-31
    
    # 列出所有可用品种
    python ingest_futures_history.py --list
"""

import os
import json
import sqlite3
import argparse
from datetime import datetime
from typing import Optional, List, Dict, Any

import akshare as ak
import pandas as pd


# 脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 数据库路径
DB_PATH = os.path.join(SCRIPT_DIR, 'futures.db')
# 映射文件路径
MAPPING_PATH = os.path.join(SCRIPT_DIR, 'futures_mapping.json')
# 日志文件路径
LOG_PATH = os.path.join(SCRIPT_DIR, 'ingest_futures.log')


def write_log(message: str):
    """写入日志文件"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")


def load_mapping() -> Dict[str, Any]:
    """加载期货品种映射配置"""
    with open(MAPPING_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_db_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def create_history_table(conn: sqlite3.Connection, table_name: str):
    """
    创建历史行情数据表（如果不存在）
    
    Args:
        conn: 数据库连接
        table_name: 表名 (如 hist_aum)
    """
    sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        trade_date TEXT PRIMARY KEY,
        -- 价格数据
        open_price REAL,
        high_price REAL,
        low_price REAL,
        close_price REAL,
        price_change REAL,
        change_pct REAL,
        -- 成交数据
        volume INTEGER,
        open_interest INTEGER,
        turnover REAL,
        -- 技术指标 - MACD
        macd_dif REAL,
        macd_dea REAL,
        macd_histogram REAL,
        -- 技术指标 - RSI
        rsi_14 REAL,
        -- 技术指标 - KDJ
        kdj_k REAL,
        kdj_d REAL,
        kdj_j REAL,
        -- 技术指标 - 布林带
        bb_upper REAL,
        bb_middle REAL,
        bb_lower REAL,
        bb_width REAL,
        -- 其他
        recommendation TEXT,
        source_ts TEXT,
        ingest_ts TEXT
    )
    """
    conn.execute(sql)
    conn.commit()


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
        
        # 按日期范围过滤
        df_filtered = df[(df['trade_date'] >= start_date) & (df['trade_date'] <= end_date)]
        
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


def update_contracts_main(conn: sqlite3.Connection, symbol: str, name: str, exchange: str):
    """
    更新合约主表
    
    Args:
        conn: 数据库连接
        symbol: 合约代码 (如 aum)
        name: 合约名称
        exchange: 交易所代码
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 检查是否存在
    cursor = conn.cursor()
    cursor.execute("SELECT symbol FROM contracts_main WHERE symbol = ?", (symbol.upper(),))
    exists = cursor.fetchone() is not None
    
    if exists:
        # 更新
        cursor.execute("""
            UPDATE contracts_main 
            SET updated_at = ?
            WHERE symbol = ?
        """, (now, symbol.upper()))
    else:
        # 插入
        cursor.execute("""
            INSERT INTO contracts_main (symbol, name, exchange, is_active, created_at, updated_at)
            VALUES (?, ?, ?, 1, ?, ?)
        """, (symbol.upper(), name, exchange, now, now))
    
    conn.commit()


def ingest_symbol(symbol: str, start_date: str, end_date: str, mapping: Dict) -> bool:
    """
    入库单个品种的历史数据
    
    Args:
        symbol: 品种代码 (如 aum)
        start_date: 开始日期
        end_date: 结束日期
        mapping: 映射配置
        
    Returns:
        是否成功
    """
    futures_config = mapping.get('futures', {})
    
    # 尝试大小写匹配
    config = futures_config.get(symbol) or futures_config.get(symbol.lower()) or futures_config.get(symbol.upper())
    
    if not config:
        write_log(f"FAIL: {symbol} - 未找到品种配置")
        print(f"  ❌ {symbol} - 未找到配置")
        return False
    
    name = config['name']
    api_symbol = config['api_symbol']
    db_table = config['db_table']
    exchange = config['exchange']
    
    # 获取数据
    df = fetch_futures_data(api_symbol, start_date, end_date)
    
    if df is None or df.empty:
        write_log(f"FAIL: {symbol} ({name}) -> {db_table} - 无数据")
        print(f"  ⚠️ {symbol} ({name}) - 无数据")
        return False
    
    # 入库
    try:
        conn = get_db_connection()
        create_history_table(conn, db_table)
        count = insert_data(conn, db_table, df)
        update_contracts_main(conn, symbol, name, exchange)
        conn.close()
        
        write_log(f"OK: {symbol} ({name}) -> {db_table} - {count} 条")
        print(f"  ✅ {symbol} ({name}) -> {db_table} - {count} 条")
        return True
        
    except Exception as e:
        write_log(f"FAIL: {symbol} ({name}) -> {db_table} - {e}")
        print(f"  ❌ {symbol} ({name}) - 入库失败: {e}")
        return False


def list_symbols(mapping: Dict):
    """列出所有可用的期货品种"""
    print("\n📋 可用期货品种列表:")
    print("-" * 70)
    print(f"{'代码':<8} {'名称':<16} {'API Symbol':<10} {'交易所':<8} {'数据库表':<15}")
    print("-" * 70)
    
    futures = mapping.get('futures', {})
    exchanges = mapping.get('exchanges', {})
    
    for symbol, config in sorted(futures.items(), key=lambda x: x[0].lower()):
        exchange_name = exchanges.get(config['exchange'], config['exchange'])
        print(f"{symbol:<8} {config['name']:<16} {config['api_symbol']:<10} {exchange_name:<8} {config['db_table']:<15}")
    
    print("-" * 70)
    print(f"共 {len(futures)} 个品种")


def main():
    parser = argparse.ArgumentParser(
        description='期货历史数据入库工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 获取沪金主连数据 (使用默认日期 2018-01-01 ~ 2024-12-31)
  python ingest_futures_history.py --symbol aum
  
  # 获取多个品种
  python ingest_futures_history.py --symbol aum,cum,rbm
  
  # 获取所有品种
  python ingest_futures_history.py --all
  
  # 指定日期范围
  python ingest_futures_history.py --symbol aum --start 2023-01-01 --end 2023-12-31
  
  # 列出所有可用品种
  python ingest_futures_history.py --list
        """
    )
    
    parser.add_argument('--symbol', '-s', type=str,
                        help='品种代码，多个用逗号分隔 (如 aum,cum,rbm)')
    parser.add_argument('--start', type=str, default='2018-01-01',
                        help='开始日期 (YYYY-MM-DD), 默认: 2018-01-01')
    parser.add_argument('--end', type=str, default='2024-12-31',
                        help='结束日期 (YYYY-MM-DD), 默认: 2024-12-31')
    parser.add_argument('--all', '-a', action='store_true',
                        help='获取所有品种')
    parser.add_argument('--list', '-l', action='store_true',
                        help='列出所有可用品种')
    
    args = parser.parse_args()
    
    # 加载映射配置
    try:
        mapping = load_mapping()
    except FileNotFoundError:
        print(f"❌ 映射文件不存在: {MAPPING_PATH}")
        return 1
    except json.JSONDecodeError as e:
        print(f"❌ 映射文件格式错误: {e}")
        return 1
    
    # 列出品种
    if args.list:
        list_symbols(mapping)
        return 0
    
    # 检查参数
    if not args.symbol and not args.all:
        parser.print_help()
        print("\n❌ 请指定 --symbol 或 --all")
        return 1
    
    # 确定要处理的品种列表
    if args.all:
        symbols = list(mapping.get('futures', {}).keys())
        print(f"\n🚀 开始获取所有 {len(symbols)} 个品种的历史数据...")
    else:
        symbols = [s.strip() for s in args.symbol.split(',')]
        print(f"\n🚀 开始获取 {len(symbols)} 个品种的历史数据...")
    
    print(f"   日期范围: {args.start} ~ {args.end}")
    print(f"   数据库: {DB_PATH}")
    print(f"   日志文件: {LOG_PATH}")
    print("=" * 60)
    
    # 写入日志头
    write_log("=" * 50)
    write_log(f"开始入库: {len(symbols)} 个品种, 日期: {args.start} ~ {args.end}")
    
    # 处理每个品种
    success_count = 0
    fail_count = 0
    failed_symbols = []
    
    for symbol in symbols:
        if ingest_symbol(symbol, args.start, args.end, mapping):
            success_count += 1
        else:
            fail_count += 1
            failed_symbols.append(symbol)
    
    # 写入汇总日志
    write_log(f"完成: 成功 {success_count}, 失败 {fail_count}")
    if failed_symbols:
        write_log(f"失败列表: {', '.join(failed_symbols)}")
    write_log("=" * 50)
    
    # 执行 WAL checkpoint，合并 WAL 文件到主数据库
    try:
        conn = get_db_connection()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()
    except Exception as e:
        write_log(f"WAL checkpoint 失败: {e}")
    
    # 汇总
    print("=" * 60)
    print(f"✅ 完成! 成功: {success_count}, 失败: {fail_count}")
    if failed_symbols:
        print(f"❌ 失败品种: {', '.join(failed_symbols)}")
    
    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    exit(main())
