#!/usr/bin/env python3
"""
期货数据 MySQL → SQLite 同步脚本

功能：
- 从阿里云 MySQL 同步数据到本地 SQLite
- 支持全量同步和增量同步
- 同步表：contracts_main、hist_{symbol}

使用方法：
    # 全量同步（首次使用）
    python mysql_to_sqlite.py --mode full
    
    # 增量同步
    python mysql_to_sqlite.py --mode incremental
    
    # 指定日期范围同步
    python mysql_to_sqlite.py --mode full --start-date 2024-01-01 --end-date 2024-11-30
    
    # 只同步合约列表
    python mysql_to_sqlite.py --mode contracts-only
    
    # 同步指定合约
    python mysql_to_sqlite.py --symbol AU0,CU0,AG0
"""

import os
import sys
import argparse
import sqlite3
import pymysql
from datetime import datetime, timedelta
import logging
from typing import List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sync.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 数据库配置
MYSQL_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}

# SQLite 数据库路径
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'futures.db')

# 默认数据范围
DEFAULT_START_DATE = '2025-01-01'
DEFAULT_END_DATE = '2025-11-30'


class MySQLToSQLiteSync:
    """MySQL 到 SQLite 同步类"""
    
    def __init__(self, sqlite_path: str = SQLITE_DB_PATH):
        self.sqlite_path = sqlite_path
        self.mysql_conn = None
        self.sqlite_conn = None
        
    def connect_mysql(self):
        """连接 MySQL 数据库"""
        try:
            self.mysql_conn = pymysql.connect(**MYSQL_CONFIG)
            logger.info("✓ MySQL 连接成功")
            return True
        except Exception as e:
            logger.error(f"✗ MySQL 连接失败: {e}")
            return False
    
    def connect_sqlite(self):
        """连接 SQLite 数据库"""
        try:
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.execute("PRAGMA journal_mode=WAL")
            self.sqlite_conn.execute("PRAGMA synchronous=NORMAL")
            logger.info(f"✓ SQLite 连接成功: {self.sqlite_path}")
            return True
        except Exception as e:
            logger.error(f"✗ SQLite 连接失败: {e}")
            return False
    
    def close_connections(self):
        """关闭数据库连接"""
        if self.mysql_conn:
            self.mysql_conn.close()
            logger.info("MySQL 连接已关闭")
        if self.sqlite_conn:
            self.sqlite_conn.close()
            logger.info("SQLite 连接已关闭")
    
    def create_sqlite_tables(self):
        """创建 SQLite 表结构"""
        cursor = self.sqlite_conn.cursor()
        
        # 创建 contracts_main 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contracts_main (
                symbol TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                exchange TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # 创建同步日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_type TEXT NOT NULL,
                table_name TEXT,
                start_time TEXT,
                end_time TEXT,
                records_synced INTEGER DEFAULT 0,
                status TEXT,
                error_message TEXT
            )
        """)
        
        self.sqlite_conn.commit()
        logger.info("✓ SQLite 基础表结构创建完成")
    
    def create_history_table(self, symbol: str):
        """为指定合约创建历史数据表"""
        cursor = self.sqlite_conn.cursor()
        table_name = f"hist_{symbol}"
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                trade_date TEXT PRIMARY KEY,
                open_price REAL,
                high_price REAL,
                low_price REAL,
                close_price REAL,
                volume INTEGER,
                open_interest INTEGER,
                turnover REAL,
                price_change REAL,
                change_pct REAL,
                macd_dif REAL,
                macd_dea REAL,
                macd_histogram REAL,
                rsi_14 REAL,
                kdj_k REAL,
                kdj_d REAL,
                kdj_j REAL,
                bb_upper REAL,
                bb_middle REAL,
                bb_lower REAL,
                bb_width REAL,
                recommendation TEXT,
                source_ts TEXT,
                ingest_ts TEXT
            )
        """)
        
        self.sqlite_conn.commit()
    
    def get_all_contracts(self) -> List[dict]:
        """从 MySQL 获取所有合约列表"""
        cursor = self.mysql_conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT symbol, name, exchange, is_active, created_at, updated_at 
            FROM contracts_main 
            WHERE is_active = 1
            ORDER BY symbol
        """)
        contracts = cursor.fetchall()
        cursor.close()
        return contracts
    
    def get_history_tables(self) -> List[str]:
        """获取 MySQL 中所有 hist_* 表名"""
        cursor = self.mysql_conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'hist_%'")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
    
    def sync_contracts(self, full_sync: bool = True):
        """同步合约列表"""
        logger.info("=" * 50)
        logger.info("开始同步合约列表 (contracts_main)")
        
        start_time = datetime.now()
        cursor_sqlite = self.sqlite_conn.cursor()
        
        try:
            if full_sync:
                # 全量同步：清空本地表
                cursor_sqlite.execute("DELETE FROM contracts_main")
                logger.info("  全量模式：已清空本地 contracts_main 表")
            
            # 获取 MySQL 数据
            contracts = self.get_all_contracts()
            logger.info(f"  从 MySQL 获取到 {len(contracts)} 个合约")
            
            # 插入数据
            synced_count = 0
            for contract in contracts:
                cursor_sqlite.execute("""
                    INSERT OR REPLACE INTO contracts_main 
                    (symbol, name, exchange, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    contract['symbol'],
                    contract['name'],
                    contract['exchange'],
                    contract['is_active'],
                    str(contract['created_at']) if contract['created_at'] else None,
                    str(contract['updated_at']) if contract['updated_at'] else None
                ))
                synced_count += 1
            
            self.sqlite_conn.commit()
            
            # 记录同步日志
            end_time = datetime.now()
            cursor_sqlite.execute("""
                INSERT INTO sync_log (sync_type, table_name, start_time, end_time, records_synced, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'full' if full_sync else 'incremental',
                'contracts_main',
                str(start_time),
                str(end_time),
                synced_count,
                'success'
            ))
            self.sqlite_conn.commit()
            
            logger.info(f"✓ 合约列表同步完成: {synced_count} 条记录")
            return contracts
            
        except Exception as e:
            logger.error(f"✗ 合约列表同步失败: {e}")
            # 记录失败日志
            cursor_sqlite.execute("""
                INSERT INTO sync_log (sync_type, table_name, start_time, end_time, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'full' if full_sync else 'incremental',
                'contracts_main',
                str(start_time),
                str(datetime.now()),
                'failure',
                str(e)
            ))
            self.sqlite_conn.commit()
            return []
    
    def sync_history_table(self, symbol: str, start_date: str, end_date: str, full_sync: bool = True):
        """同步单个合约的历史数据表"""
        table_name = f"hist_{symbol}"
        start_time = datetime.now()
        
        cursor_mysql = self.mysql_conn.cursor(pymysql.cursors.DictCursor)
        cursor_sqlite = self.sqlite_conn.cursor()
        
        try:
            # 检查 MySQL 表是否存在，并获取实际表名（处理大小写问题）
            cursor_mysql.execute(f"SHOW TABLES LIKE '{table_name}'")
            result = cursor_mysql.fetchone()
            if not result:
                # 尝试小写表名
                table_name_lower = f"hist_{symbol.lower()}"
                cursor_mysql.execute(f"SHOW TABLES LIKE '{table_name_lower}'")
                result = cursor_mysql.fetchone()
                if not result:
                    logger.warning(f"  跳过 {table_name}: MySQL 表不存在")
                    return 0
            
            # 使用实际的表名（可能是不同的大小写）
            mysql_table_name = result[0]
            logger.debug(f"  MySQL 实际表名: {mysql_table_name}")
            
            # 创建 SQLite 表
            self.create_history_table(symbol)
            
            if full_sync:
                # 全量同步：清空本地表
                cursor_sqlite.execute(f"DELETE FROM {table_name}")
            
            # 构建查询条件（使用实际的 MySQL 表名）
            if full_sync:
                # 全量同步：按日期范围
                query = f"""
                    SELECT * FROM {mysql_table_name}
                    WHERE trade_date >= %s AND trade_date <= %s
                    ORDER BY trade_date
                """
                cursor_mysql.execute(query, (start_date, end_date))
            else:
                # 增量同步：获取本地最新日期，然后同步更新的数据
                cursor_sqlite.execute(f"SELECT MAX(trade_date) FROM {table_name}")
                local_result = cursor_sqlite.fetchone()
                local_max_date = local_result[0] if local_result and local_result[0] else start_date
                
                query = f"""
                    SELECT * FROM {mysql_table_name}
                    WHERE trade_date > %s AND trade_date <= %s
                    ORDER BY trade_date
                """
                cursor_mysql.execute(query, (local_max_date, end_date))
            
            rows = cursor_mysql.fetchall()
            
            if not rows:
                logger.info(f"  {table_name}: 无新数据")
                return 0
            
            # 插入数据
            synced_count = 0
            for row in rows:
                cursor_sqlite.execute(f"""
                    INSERT OR REPLACE INTO {table_name}
                    (trade_date, open_price, high_price, low_price, close_price,
                     volume, open_interest, turnover, price_change, change_pct,
                     macd_dif, macd_dea, macd_histogram, rsi_14,
                     kdj_k, kdj_d, kdj_j,
                     bb_upper, bb_middle, bb_lower, bb_width,
                     recommendation, source_ts, ingest_ts)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(row['trade_date']) if row['trade_date'] else None,
                    float(row['open_price']) if row['open_price'] else None,
                    float(row['high_price']) if row['high_price'] else None,
                    float(row['low_price']) if row['low_price'] else None,
                    float(row['close_price']) if row['close_price'] else None,
                    int(row['volume']) if row['volume'] else None,
                    int(row['open_interest']) if row['open_interest'] else None,
                    float(row['turnover']) if row['turnover'] else None,
                    float(row['price_change']) if row['price_change'] else None,
                    float(row['change_pct']) if row['change_pct'] else None,
                    float(row['macd_dif']) if row['macd_dif'] else None,
                    float(row['macd_dea']) if row['macd_dea'] else None,
                    float(row['macd_histogram']) if row['macd_histogram'] else None,
                    float(row['rsi_14']) if row['rsi_14'] else None,
                    float(row['kdj_k']) if row['kdj_k'] else None,
                    float(row['kdj_d']) if row['kdj_d'] else None,
                    float(row['kdj_j']) if row['kdj_j'] else None,
                    float(row['bb_upper']) if row['bb_upper'] else None,
                    float(row['bb_middle']) if row['bb_middle'] else None,
                    float(row['bb_lower']) if row['bb_lower'] else None,
                    float(row['bb_width']) if row['bb_width'] else None,
                    row['recommendation'] if row['recommendation'] else None,
                    str(row['source_ts']) if row['source_ts'] else None,
                    str(row['ingest_ts']) if row['ingest_ts'] else None
                ))
                synced_count += 1
            
            self.sqlite_conn.commit()
            
            # 记录同步日志
            cursor_sqlite.execute("""
                INSERT INTO sync_log (sync_type, table_name, start_time, end_time, records_synced, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'full' if full_sync else 'incremental',
                table_name,
                str(start_time),
                str(datetime.now()),
                synced_count,
                'success'
            ))
            self.sqlite_conn.commit()
            
            return synced_count
            
        except Exception as e:
            logger.error(f"  ✗ {table_name} 同步失败: {e}")
            # 记录失败日志
            try:
                cursor_sqlite.execute("""
                    INSERT INTO sync_log (sync_type, table_name, start_time, end_time, status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    'full' if full_sync else 'incremental',
                    table_name,
                    str(start_time),
                    str(datetime.now()),
                    'failure',
                    str(e)
                ))
                self.sqlite_conn.commit()
            except:
                pass
            return 0
        finally:
            cursor_mysql.close()
    
    def sync_history_table_direct(self, table_name: str, start_date: str, end_date: str, full_sync: bool = True):
        """直接使用表名同步历史数据（不构造表名）"""
        start_time = datetime.now()
        
        cursor_mysql = self.mysql_conn.cursor(pymysql.cursors.DictCursor)
        cursor_sqlite = self.sqlite_conn.cursor()
        
        try:
            # 创建 SQLite 表（使用相同的表名）
            cursor_sqlite.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    trade_date TEXT PRIMARY KEY,
                    open_price REAL,
                    high_price REAL,
                    low_price REAL,
                    close_price REAL,
                    volume INTEGER,
                    open_interest INTEGER,
                    turnover REAL,
                    price_change REAL,
                    change_pct REAL,
                    macd_dif REAL,
                    macd_dea REAL,
                    macd_histogram REAL,
                    rsi_14 REAL,
                    kdj_k REAL,
                    kdj_d REAL,
                    kdj_j REAL,
                    bb_upper REAL,
                    bb_middle REAL,
                    bb_lower REAL,
                    bb_width REAL,
                    recommendation TEXT,
                    source_ts TEXT,
                    ingest_ts TEXT
                )
            """)
            self.sqlite_conn.commit()
            
            if full_sync:
                # 全量同步：清空本地表
                cursor_sqlite.execute(f"DELETE FROM {table_name}")
            
            # 构建查询
            if full_sync:
                query = f"""
                    SELECT * FROM {table_name}
                    WHERE trade_date >= %s AND trade_date <= %s
                    ORDER BY trade_date
                """
                cursor_mysql.execute(query, (start_date, end_date))
            else:
                # 增量同步
                cursor_sqlite.execute(f"SELECT MAX(trade_date) FROM {table_name}")
                local_result = cursor_sqlite.fetchone()
                local_max_date = local_result[0] if local_result and local_result[0] else start_date
                
                query = f"""
                    SELECT * FROM {table_name}
                    WHERE trade_date > %s AND trade_date <= %s
                    ORDER BY trade_date
                """
                cursor_mysql.execute(query, (local_max_date, end_date))
            
            rows = cursor_mysql.fetchall()
            
            if not rows:
                logger.info(f"  {table_name}: 无新数据")
                return 0
            
            # 插入数据
            synced_count = 0
            for row in rows:
                cursor_sqlite.execute(f"""
                    INSERT OR REPLACE INTO {table_name}
                    (trade_date, open_price, high_price, low_price, close_price,
                     volume, open_interest, turnover, price_change, change_pct,
                     macd_dif, macd_dea, macd_histogram, rsi_14,
                     kdj_k, kdj_d, kdj_j,
                     bb_upper, bb_middle, bb_lower, bb_width,
                     recommendation, source_ts, ingest_ts)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(row['trade_date']) if row['trade_date'] else None,
                    float(row['open_price']) if row['open_price'] else None,
                    float(row['high_price']) if row['high_price'] else None,
                    float(row['low_price']) if row['low_price'] else None,
                    float(row['close_price']) if row['close_price'] else None,
                    int(row['volume']) if row['volume'] else None,
                    int(row['open_interest']) if row['open_interest'] else None,
                    float(row['turnover']) if row['turnover'] else None,
                    float(row['price_change']) if row['price_change'] else None,
                    float(row['change_pct']) if row['change_pct'] else None,
                    float(row['macd_dif']) if row['macd_dif'] else None,
                    float(row['macd_dea']) if row['macd_dea'] else None,
                    float(row['macd_histogram']) if row['macd_histogram'] else None,
                    float(row['rsi_14']) if row['rsi_14'] else None,
                    float(row['kdj_k']) if row['kdj_k'] else None,
                    float(row['kdj_d']) if row['kdj_d'] else None,
                    float(row['kdj_j']) if row['kdj_j'] else None,
                    float(row['bb_upper']) if row['bb_upper'] else None,
                    float(row['bb_middle']) if row['bb_middle'] else None,
                    float(row['bb_lower']) if row['bb_lower'] else None,
                    float(row['bb_width']) if row['bb_width'] else None,
                    row['recommendation'] if row['recommendation'] else None,
                    str(row['source_ts']) if row['source_ts'] else None,
                    str(row['ingest_ts']) if row['ingest_ts'] else None
                ))
                synced_count += 1
            
            self.sqlite_conn.commit()
            
            # 记录同步日志
            cursor_sqlite.execute("""
                INSERT INTO sync_log (sync_type, table_name, start_time, end_time, records_synced, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'full' if full_sync else 'incremental',
                table_name,
                str(start_time),
                str(datetime.now()),
                synced_count,
                'success'
            ))
            self.sqlite_conn.commit()
            
            return synced_count
            
        except Exception as e:
            logger.error(f"  ✗ {table_name} 同步失败: {e}")
            try:
                cursor_sqlite.execute("""
                    INSERT INTO sync_log (sync_type, table_name, start_time, end_time, status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    'full' if full_sync else 'incremental',
                    table_name,
                    str(start_time),
                    str(datetime.now()),
                    'failure',
                    str(e)
                ))
                self.sqlite_conn.commit()
            except:
                pass
            return 0
        finally:
            cursor_mysql.close()
    
    def sync_all_history(self, start_date: str, end_date: str, 
                        full_sync: bool = True, symbols: Optional[List[str]] = None):
        """同步所有合约的历史数据"""
        logger.info("=" * 50)
        logger.info("开始同步历史数据")
        logger.info(f"  日期范围: {start_date} 至 {end_date}")
        logger.info(f"  同步模式: {'全量同步' if full_sync else '增量同步'}")
        
        # 获取要同步的合约列表
        if symbols:
            contracts = [{'symbol': s.strip()} for s in symbols]
            logger.info(f"  指定合约: {', '.join(symbols)}")
        else:
            # 从本地 SQLite 获取合约列表
            cursor = self.sqlite_conn.cursor()
            cursor.execute("SELECT symbol FROM contracts_main WHERE is_active = 1")
            contracts = [{'symbol': row[0]} for row in cursor.fetchall()]
            logger.info(f"  合约数量: {len(contracts)}")
        
        if not contracts:
            logger.warning("没有找到需要同步的合约")
            return
        
        total_count = len(contracts)
        success_count = 0
        total_records = 0
        
        for idx, contract in enumerate(contracts, 1):
            symbol = contract['symbol']
            # 表名统一使用小写
            table_name = f"hist_{symbol.lower()}"
            progress = f"[{idx}/{total_count}]"
            
            logger.info(f"{progress} 同步 {table_name}...")
            
            synced = self.sync_history_table_direct(table_name, start_date, end_date, full_sync)
            
            if synced > 0:
                success_count += 1
                total_records += synced
                logger.info(f"  ✓ {table_name}: {synced} 条记录")
            elif synced == 0:
                success_count += 1  # 无新数据也算成功
        
        logger.info("=" * 50)
        logger.info(f"历史数据同步完成")
        logger.info(f"  成功合约: {success_count}/{total_count}")
        logger.info(f"  同步记录: {total_records} 条")
    
    def run_full_sync(self, start_date: str, end_date: str, symbols: Optional[List[str]] = None):
        """执行全量同步"""
        logger.info("=" * 60)
        logger.info("开始全量同步")
        logger.info(f"数据范围: {start_date} 至 {end_date}")
        logger.info("=" * 60)
        
        # 连接数据库
        if not self.connect_mysql():
            return False
        if not self.connect_sqlite():
            return False
        
        try:
            # 创建表结构
            self.create_sqlite_tables()
            
            # 同步合约列表
            self.sync_contracts(full_sync=True)
            
            # 同步历史数据
            self.sync_all_history(start_date, end_date, full_sync=True, symbols=symbols)
            
            logger.info("=" * 60)
            logger.info("✓ 全量同步完成")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"✗ 全量同步失败: {e}")
            return False
        finally:
            self.close_connections()
    
    def run_incremental_sync(self, start_date: str, end_date: str, symbols: Optional[List[str]] = None):
        """执行增量同步"""
        logger.info("=" * 60)
        logger.info("开始增量同步")
        logger.info(f"数据范围: {start_date} 至 {end_date}")
        logger.info("=" * 60)
        
        # 连接数据库
        if not self.connect_mysql():
            return False
        if not self.connect_sqlite():
            return False
        
        try:
            # 创建表结构（如果不存在）
            self.create_sqlite_tables()
            
            # 增量同步合约列表（添加新合约）
            self.sync_contracts(full_sync=False)
            
            # 增量同步历史数据
            self.sync_all_history(start_date, end_date, full_sync=False, symbols=symbols)
            
            logger.info("=" * 60)
            logger.info("✓ 增量同步完成")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"✗ 增量同步失败: {e}")
            return False
        finally:
            self.close_connections()
    
    def run_contracts_only(self):
        """只同步合约列表"""
        logger.info("=" * 60)
        logger.info("只同步合约列表")
        logger.info("=" * 60)
        
        if not self.connect_mysql():
            return False
        if not self.connect_sqlite():
            return False
        
        try:
            self.create_sqlite_tables()
            self.sync_contracts(full_sync=True)
            
            logger.info("=" * 60)
            logger.info("✓ 合约列表同步完成")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"✗ 合约列表同步失败: {e}")
            return False
        finally:
            self.close_connections()
    
    def show_sync_status(self):
        """显示同步状态"""
        if not self.connect_sqlite():
            return
        
        cursor = self.sqlite_conn.cursor()
        
        print("\n" + "=" * 60)
        print("同步状态")
        print("=" * 60)
        
        # 合约数量
        cursor.execute("SELECT COUNT(*) FROM contracts_main")
        contract_count = cursor.fetchone()[0]
        print(f"合约数量: {contract_count}")
        
        # 历史数据表统计
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'hist_%'")
        hist_tables = cursor.fetchall()
        print(f"历史数据表: {len(hist_tables)} 个")
        
        # 最近同步记录
        print("\n最近同步记录:")
        cursor.execute("""
            SELECT sync_type, table_name, start_time, records_synced, status 
            FROM sync_log 
            ORDER BY id DESC 
            LIMIT 10
        """)
        logs = cursor.fetchall()
        
        for log in logs:
            sync_type, table_name, start_time, records, status = log
            status_icon = "✓" if status == 'success' else "✗"
            print(f"  {status_icon} [{sync_type}] {table_name}: {records} 条 ({start_time})")
        
        print("=" * 60)
        
        self.close_connections()


def main():
    parser = argparse.ArgumentParser(
        description='期货数据 MySQL → SQLite 同步工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 全量同步（首次使用）
  python mysql_to_sqlite.py --mode full
  
  # 增量同步
  python mysql_to_sqlite.py --mode incremental
  
  # 指定日期范围
  python mysql_to_sqlite.py --mode full --start-date 2024-01-01 --end-date 2024-11-30
  
  # 只同步合约列表
  python mysql_to_sqlite.py --mode contracts-only
  
  # 同步指定合约
  python mysql_to_sqlite.py --symbol AU0,CU0,AG0
  
  # 查看同步状态
  python mysql_to_sqlite.py --status
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['full', 'incremental', 'contracts-only'],
        default='full',
        help='同步模式: full=全量, incremental=增量, contracts-only=只同步合约列表'
    )
    
    parser.add_argument(
        '--start-date',
        default=DEFAULT_START_DATE,
        help=f'开始日期 (默认: {DEFAULT_START_DATE})'
    )
    
    parser.add_argument(
        '--end-date',
        default=DEFAULT_END_DATE,
        help=f'结束日期 (默认: {DEFAULT_END_DATE})'
    )
    
    parser.add_argument(
        '--symbol',
        help='指定同步的合约代码，多个用逗号分隔 (如: AU0,CU0,AG0)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='显示同步状态'
    )
    
    parser.add_argument(
        '--db-path',
        default=SQLITE_DB_PATH,
        help=f'SQLite 数据库路径 (默认: {SQLITE_DB_PATH})'
    )
    
    args = parser.parse_args()
    
    # 创建同步实例
    syncer = MySQLToSQLiteSync(sqlite_path=args.db_path)
    
    # 显示状态
    if args.status:
        syncer.show_sync_status()
        return
    
    # 解析合约列表
    symbols = None
    if args.symbol:
        symbols = [s.strip() for s in args.symbol.split(',')]
    
    # 执行同步
    if args.mode == 'full':
        syncer.run_full_sync(args.start_date, args.end_date, symbols)
    elif args.mode == 'incremental':
        syncer.run_incremental_sync(args.start_date, args.end_date, symbols)
    elif args.mode == 'contracts-only':
        syncer.run_contracts_only()


if __name__ == '__main__':
    main()
