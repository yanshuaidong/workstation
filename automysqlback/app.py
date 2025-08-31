"""
期货数据更新系统后端服务
技术栈：Flask + akshare + pandas + MySQL + APScheduler
端口：7002
数据库：阿里云RDS MySQL
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import threading
import time
import concurrent.futures
import json
import traceback
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 数据库配置
DB_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}

# 全局变量
scheduler = BackgroundScheduler()

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def init_database():
    """初始化数据库表结构"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. 主连合约表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contracts_main (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL UNIQUE COMMENT '合约代码，如cum',
                name VARCHAR(50) NOT NULL COMMENT '合约中文名称，如沪铜主连',
                exchange VARCHAR(20) NOT NULL COMMENT '交易所简称',
                is_active TINYINT(1) DEFAULT 1 COMMENT '是否活跃',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_symbol (symbol),
                INDEX idx_exchange (exchange)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='期货主连合约列表'
        """)
        
        # 2. 系统配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                id INT AUTO_INCREMENT PRIMARY KEY,
                auto_update_enabled TINYINT(1) DEFAULT 0 COMMENT '是否开启自动更新',
                daily_update_time TIME DEFAULT '17:00:00' COMMENT '每日自动更新时间',
                multithread_enabled TINYINT(1) DEFAULT 1 COMMENT '是否开启多线程',
                concurrency INT DEFAULT 5 COMMENT '并发数量',
                timeout_seconds INT DEFAULT 60 COMMENT '超时时间(秒)',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表'
        """)
        
        # 3. 合约列表更新记录表（只有一条记录）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contract_list_update_log (
                id INT PRIMARY KEY DEFAULT 1,
                last_update_time TIMESTAMP NULL COMMENT '上次更新时间',
                update_method ENUM('manual', 'auto') DEFAULT 'manual' COMMENT '更新方式',
                duration_ms INT DEFAULT 0 COMMENT '花费时间(毫秒)',
                status ENUM('success', 'failure') DEFAULT 'success' COMMENT '状态',
                error_message TEXT NULL COMMENT '失败信息',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合约列表更新记录表'
        """)
        
        # 4. 主连历史数据更新日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history_update_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                contract_symbol VARCHAR(20) NOT NULL COMMENT '合约代码',
                name VARCHAR(50) NOT NULL COMMENT '合约中文名称',
                target_table VARCHAR(50) NOT NULL COMMENT '目标表名',
                start_time TIMESTAMP NULL COMMENT '开始时间',
                end_time TIMESTAMP NULL COMMENT '结束时间',
                data_start_date DATE NULL COMMENT '期货开始时间',
                data_end_date DATE NULL COMMENT '期货结束时间',
                status ENUM('success', 'failure') DEFAULT 'failure' COMMENT '状态',
                error_message TEXT NULL COMMENT '错误信息',
                retry_count INT DEFAULT 0 COMMENT '重试次数',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_contract (contract_symbol),
                INDEX idx_status (status),
                INDEX idx_contract_symbol (contract_symbol)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='主连历史数据更新日志表'
        """)
        
        conn.commit()
        
        # 初始化默认配置（如果不存在）
        cursor.execute("SELECT COUNT(*) FROM system_config")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO system_config 
                (auto_update_enabled, daily_update_time, multithread_enabled, concurrency, timeout_seconds)
                VALUES (0, '17:00:00', 1, 5, 60)
            """)
        
        # 初始化合约列表更新记录（如果不存在）
        cursor.execute("SELECT COUNT(*) FROM contract_list_update_log")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO contract_list_update_log (id, update_method, status)
                VALUES (1, 'manual', 'success')
            """)
        
        # 检查并添加 name 字段到 history_update_log 表（数据库迁移）
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'history_update_log' 
            AND COLUMN_NAME = 'name'
        """)
        if cursor.fetchone()[0] == 0:
            # 添加 name 字段
            cursor.execute("""
                ALTER TABLE history_update_log 
                ADD COLUMN name VARCHAR(50) NOT NULL DEFAULT '' COMMENT '合约中文名称' 
                AFTER contract_symbol
            """)
            logger.info("已为 history_update_log 表添加 name 字段")
            
            # 更新现有记录的 name 字段
            cursor.execute("""
                UPDATE history_update_log h 
                JOIN contracts_main c ON h.contract_symbol = c.symbol 
                SET h.name = c.name
            """)
            logger.info("已更新现有记录的合约名称")
        
        conn.commit()
        logger.info("数据库表初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def create_history_table(symbol):
    """为新的主连合约创建历史数据表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    table_name = f"hist_{symbol}"
    try:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                trade_date DATE PRIMARY KEY COMMENT '交易日期',
                open_price INT NOT NULL COMMENT '开盘价',
                high_price INT NOT NULL COMMENT '最高价',
                low_price INT NOT NULL COMMENT '最低价',
                close_price INT NOT NULL COMMENT '收盘价',
                volume BIGINT NOT NULL DEFAULT 0 COMMENT '成交量',
                open_interest BIGINT NOT NULL DEFAULT 0 COMMENT '持仓量',
                turnover BIGINT NOT NULL DEFAULT 0 COMMENT '成交额',
                price_change INT DEFAULT 0 COMMENT '价格变动',
                change_pct DECIMAL(8,2) DEFAULT 0.00 COMMENT '涨跌幅',
                source_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '数据源时间戳',
                ingest_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '入库时间戳',
                INDEX idx_trade_date (trade_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='期货历史数据_{symbol}'
        """)
        conn.commit()
        logger.info(f"创建历史数据表: {table_name}")
        return True
    except Exception as e:
        logger.error(f"创建表{table_name}失败: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def filter_main_contracts(contracts_df):
    """筛选主连合约"""
    if contracts_df.empty:
        return pd.DataFrame()
    
    # 需要排除的低成交量主连合约
    excluded_contracts = [
        '粳稻主连',
        '晚籼稻主连',
        '普麦主连',
        '早籼稻主连',
        '强麦主连',
        '动力煤主连'
    ]
    
    # 筛选包含"主连"的合约，排除"次主连"和指定的低成交量合约
    main_contracts = contracts_df[
        (contracts_df['合约中文代码'].str.contains('主连')) & 
        (~contracts_df['合约中文代码'].str.contains('次主连')) &
        (~contracts_df['合约中文代码'].isin(excluded_contracts))
    ].copy()
    
    return main_contracts

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """获取系统设置"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("SELECT * FROM system_config LIMIT 1")
        config = cursor.fetchone()
        
        if config:
            # 转换时间格式
            daily_update_time = str(config['daily_update_time'])
            if len(daily_update_time) == 8:  # HH:MM:SS
                daily_update_time = daily_update_time[:5]  # 只要 HH:MM
            
            return jsonify({
                'code': 0,
                'message': '获取成功',
                'data': {
                    'auto_update_enabled': bool(config['auto_update_enabled']),
                    'daily_update_time': daily_update_time,
                    'multithread_enabled': bool(config['multithread_enabled']),
                    'concurrency': config['concurrency'],
                    'timeout_seconds': config['timeout_seconds']
                }
            })
        else:
            return jsonify({
                'code': 1,
                'message': '配置不存在'
            })
        
    except Exception as e:
        logger.error(f"获取设置失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """更新系统设置"""
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE system_config SET 
            auto_update_enabled = %s,
            daily_update_time = %s,
            multithread_enabled = %s,
            concurrency = %s,
            timeout_seconds = %s,
            updated_at = NOW()
        """, (
            data.get('auto_update_enabled', 0),
            data.get('daily_update_time', '17:00:00'),
            data.get('multithread_enabled', 1),
            data.get('concurrency', 5),
            data.get('timeout_seconds', 60)
        ))
        
        conn.commit()
        
        # 重新配置定时任务
        setup_scheduler()
        
        return jsonify({
            'code': 0,
            'message': '设置已更新',
            'data': data
        })
        
    except Exception as e:
        logger.error(f"更新设置失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'更新失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/api/contracts/update-list', methods=['POST'])
def update_contracts_list():
    """更新合约列表"""
    start_time = time.time()
    error_message = None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取公开接口数据
        logger.info("开始获取期货合约列表")
        contracts_df = ak.futures_hist_table_em()
        main_contracts = filter_main_contracts(contracts_df)
        
        if main_contracts.empty:
            raise ValueError("没有找到主连合约数据")
        
        # 清空并重新插入合约数据
        cursor.execute("DELETE FROM contracts_main")
        
        new_count = 0
        existing_tables = set()
        
        # 获取现有的历史数据表
        cursor.execute("SHOW TABLES LIKE 'hist_%'")
        for (table_name,) in cursor.fetchall():
            existing_tables.add(table_name)
        
        for _, row in main_contracts.iterrows():
            symbol = row['合约代码']
            name = row['合约中文代码']
            exchange = row['市场简称']
            
            # 插入合约记录
            cursor.execute("""
                INSERT INTO contracts_main (symbol, name, exchange) 
                VALUES (%s, %s, %s)
            """, (symbol, name, exchange))
            new_count += 1
            
            # 检查并创建对应的历史数据表
            table_name = f"hist_{symbol}"
            if table_name not in existing_tables:
                create_history_table(symbol)
                logger.info(f"为新合约 {symbol} 创建历史数据表")
        
        # 初始化历史更新日志
        cursor.execute("DELETE FROM history_update_log")
        for _, row in main_contracts.iterrows():
            symbol = row['合约代码']
            cursor.execute("""
                INSERT INTO history_update_log 
                (contract_symbol, name, target_table, status)
                VALUES (%s, %s, %s, 'failure')
            """, (symbol, row['合约中文代码'], f"hist_{symbol}"))
        
        conn.commit()
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # 更新合约列表更新记录
        cursor.execute("""
            UPDATE contract_list_update_log SET 
            last_update_time = NOW(),
            update_method = 'manual',
            duration_ms = %s,
            status = 'success',
            error_message = NULL,
            updated_at = NOW()
            WHERE id = 1
        """, (duration_ms,))
        
        conn.commit()
        
        return jsonify({
            'code': 0,
            'message': '合约列表更新成功',
            'data': {
                'new_count': new_count,
                'duration_ms': duration_ms
            }
        })
        
    except Exception as e:
        error_message = str(e)
        duration_ms = int((time.time() - start_time) * 1000)
        
        # 记录失败
        try:
            cursor.execute("""
                UPDATE contract_list_update_log SET 
                last_update_time = NOW(),
                update_method = 'manual',
                duration_ms = %s,
                status = 'failure',
                error_message = %s,
                updated_at = NOW()
                WHERE id = 1
            """, (duration_ms, error_message))
            conn.commit()
        except:
            pass
        
        logger.error(f"更新合约列表失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'更新失败: {error_message}'
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/api/contracts/list', methods=['GET'])
def get_contracts_list():
    """获取数据库中的合约列表"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT symbol, name, exchange, is_active 
            FROM contracts_main 
            WHERE is_active = 1 
            ORDER BY symbol
        """)
        
        contracts = cursor.fetchall()
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'contracts': contracts,
                'total': len(contracts)
            }
        })
        
    except Exception as e:
        logger.error(f"获取合约列表失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/api/contracts/list-update-log', methods=['GET'])
def get_list_update_log():
    """获取合约列表更新记录"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("SELECT * FROM contract_list_update_log WHERE id = 1")
        log = cursor.fetchone()
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': log
        })
        
    except Exception as e:
        logger.error(f"获取合约列表更新记录失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

def fetch_and_store_history_with_retry(symbol, start_date, end_date, timeout_seconds, max_retries=3):
    """获取并存储单个合约的历史数据（带重试）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    start_time = time.time()
    retry_count = 0
    
    try:
        # 更新开始状态
        cursor.execute("""
            UPDATE history_update_log SET 
            start_time = NOW(),
            data_start_date = %s,
            data_end_date = %s,
            status = 'failure',
            error_message = NULL,
            updated_at = NOW()
            WHERE contract_symbol = %s
        """, (start_date, end_date, symbol))
        conn.commit()
        
        while retry_count < max_retries:
            try:
                current_timeout = timeout_seconds + (retry_count * 30)  # 每次重试增加30秒
                logger.info(f"开始获取 {symbol} 的历史数据: {start_date} 到 {end_date}，第{retry_count+1}次尝试，超时时间: {current_timeout}秒")
                
                # 获取合约的中文名称用于 akshare 调用
                conn_inner = get_db_connection()
                cursor_inner = conn_inner.cursor(pymysql.cursors.DictCursor)
                try:
                    cursor_inner.execute("SELECT name FROM contracts_main WHERE symbol = %s", (symbol,))
                    contract_result = cursor_inner.fetchone()
                    if not contract_result:
                        raise ValueError(f"合约 {symbol} 不存在于数据库中")
                    
                    contract_name = contract_result['name']
                    logger.info(f"获取 {symbol}({contract_name}) 历史数据: {start_date} 到 {end_date}")
                finally:
                    cursor_inner.close()
                    conn_inner.close()
                
                # 获取历史数据 - 使用中文名称
                try:
                    hist_df = ak.futures_hist_em(
                        symbol=contract_name,  # 使用中文名称
                        period='daily',
                        start_date=start_date.replace('-', ''),
                        end_date=end_date.replace('-', '')
                    )
                except Exception as ak_error:
                    logger.error(f"{symbol}({contract_name}) akshare接口调用失败: {type(ak_error).__name__}: {str(ak_error)}")
                    raise ak_error
                
                logger.info(f"{symbol}({contract_name}) 数据获取完成: {hist_df.shape[0]} 行数据")
                
                if hist_df.empty:
                    raise ValueError(f"合约 {symbol} 在指定日期范围内没有数据")
                
                # 验证必需的列是否存在
                required_columns = ['时间', '开盘', '最高', '最低', '收盘']
                missing_columns = [col for col in required_columns if col not in hist_df.columns]
                if missing_columns:
                    raise ValueError(f"数据框缺少必需的列: {missing_columns}")
                
                # 数据入库
                table_name = f"hist_{symbol}"
                success_rows = 0
                
                for idx, row in hist_df.iterrows():
                    try:
                        cursor.execute(f"""
                            INSERT INTO {table_name} 
                            (trade_date, open_price, high_price, low_price, close_price, 
                             volume, open_interest, turnover, price_change, change_pct, source_ts)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                            ON DUPLICATE KEY UPDATE
                            open_price = VALUES(open_price),
                            high_price = VALUES(high_price),
                            low_price = VALUES(low_price),
                            close_price = VALUES(close_price),
                            volume = VALUES(volume),
                            open_interest = VALUES(open_interest),
                            turnover = VALUES(turnover),
                            price_change = VALUES(price_change),
                            change_pct = VALUES(change_pct),
                            ingest_ts = NOW()
                        """, (
                            row['时间'],
                            row['开盘'],
                            row['最高'],
                            row['最低'],
                            row['收盘'],
                            row.get('成交量', 0),
                            row.get('持仓量', 0),
                            row.get('成交额', 0),
                            row.get('涨跌', 0),
                            row.get('涨跌幅', 0.0)
                        ))
                        success_rows += 1
                    except Exception as row_error:
                        logger.error(f"{symbol} 插入第{success_rows+1}行数据失败: {row_error}")
                
                conn.commit()
                
                # 更新成功状态
                cursor.execute("""
                    UPDATE history_update_log SET 
                    end_time = NOW(),
                    status = 'success',
                    error_message = NULL,
                    retry_count = %s,
                    updated_at = NOW()
                    WHERE contract_symbol = %s
                """, (retry_count, symbol))
                conn.commit()
                
                logger.info(f"成功更新 {symbol}: {success_rows} 行数据，重试次数: {retry_count}")
                return True
                
            except Exception as e:
                retry_count += 1
                error_msg = f"第{retry_count}次尝试失败: {str(e)}"
                logger.warning(f"{symbol} {error_msg}")
                
                if retry_count >= max_retries:
                    # 所有重试都失败了
                    final_error_msg = f"重试{max_retries}次后仍失败: {str(e)}"
                    logger.error(f"{symbol} 最终失败: {final_error_msg}")
                    cursor.execute("""
                        UPDATE history_update_log SET 
                        end_time = NOW(),
                        status = 'failure',
                        error_message = %s,
                        retry_count = %s,
                        updated_at = NOW()
                        WHERE contract_symbol = %s
                    """, (final_error_msg, retry_count, symbol))
                    conn.commit()
                    return False
                else:
                    # 等待一段时间后重试
                    logger.info(f"{symbol} 等待5秒后进行第{retry_count+1}次重试")
                    time.sleep(5)
        
        return False
        
    except Exception as e:
        # 更新失败状态
        cursor.execute("""
            UPDATE history_update_log SET 
            end_time = NOW(),
            status = 'failure',
            error_message = %s,
            retry_count = %s,
            updated_at = NOW()
            WHERE contract_symbol = %s
        """, (str(e), retry_count, symbol))
        conn.commit()
        logger.error(f"{symbol} 处理失败: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()

@app.route('/api/history/update-all', methods=['POST'])
def update_all_history():
    """批量更新所有主连历史数据"""
    data = request.get_json()
    date_start = data.get('date_start')
    date_end = data.get('date_end')
    
    if not date_start or not date_end:
        return jsonify({
            'code': 1,
            'message': '缺少日期参数'
        })
    
    # 获取系统配置
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("SELECT * FROM system_config LIMIT 1")
        config = cursor.fetchone()
        
        if not config:
            return jsonify({
                'code': 1,
                'message': '系统配置不存在'
            })
        
        # 获取所有主连合约
        cursor.execute("SELECT symbol FROM contracts_main WHERE is_active = 1")
        symbols = [row['symbol'] for row in cursor.fetchall()]
        
        if not symbols:
            return jsonify({
                'code': 1,
                'message': '没有找到需要更新的合约'
            })
        
        # 后台执行更新任务
        def run_update_task():
            timeout_seconds = config['timeout_seconds']
            multithread = config['multithread_enabled']
            concurrency = config['concurrency']
            
            if multithread and concurrency > 1:
                # 多线程执行
                with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures = []
                    for symbol in symbols:
                        future = executor.submit(
                            fetch_and_store_history_with_retry, 
                            symbol, date_start, date_end, timeout_seconds
                        )
                        futures.append(future)
                    
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"任务执行异常: {e}")
            else:
                # 单线程执行
                for symbol in symbols:
                    try:
                        fetch_and_store_history_with_retry(symbol, date_start, date_end, timeout_seconds)
                    except Exception as e:
                        logger.error(f"任务执行异常: {e}")
            
            logger.info("批量更新历史数据完成")
        
        # 在后台线程中执行
        threading.Thread(target=run_update_task, daemon=True).start()
        
        return jsonify({
            'code': 0,
            'message': '历史数据更新已启动',
            'data': {
                'total_contracts': len(symbols),
                'date_range': f"{date_start} 至 {date_end}"
            }
        })
        
    except Exception as e:
        logger.error(f"启动批量更新失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'启动失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/api/history/retry-single', methods=['POST'])
def retry_single_history():
    """重试单个合约历史数据更新"""
    data = request.get_json()
    symbol = data.get('symbol')
    date_start = data.get('date_start')
    date_end = data.get('date_end')
    
    if not symbol or not date_start or not date_end:
        return jsonify({
            'code': 1,
            'message': '缺少必要参数'
        })
    
    # 获取系统配置
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("SELECT timeout_seconds FROM system_config LIMIT 1")
        config = cursor.fetchone()
        timeout_seconds = config['timeout_seconds'] if config else 60
        
        # 后台执行重试任务
        def run_retry_task():
            fetch_and_store_history_with_retry(symbol, date_start, date_end, timeout_seconds)
        
        threading.Thread(target=run_retry_task, daemon=True).start()
        
        return jsonify({
            'code': 0,
            'message': f'{symbol} 重试已启动'
        })
        
    except Exception as e:
        logger.error(f"启动重试失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'启动重试失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/api/history/logs', methods=['GET'])
def get_history_logs():
    """获取历史数据更新日志"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT contract_symbol, name, target_table, start_time, end_time, 
                   data_start_date, data_end_date, status, error_message, 
                   retry_count, created_at, updated_at 
            FROM history_update_log 
            ORDER BY contract_symbol
        """)
        
        logs = cursor.fetchall()
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': logs
        })
        
    except Exception as e:
        logger.error(f"获取历史日志失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

def auto_update_task():
    """自动更新任务"""
    logger.info("执行自动更新任务")
    
    try:
        # 默认更新近一个月的数据
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # 调用更新接口
        import requests
        response = requests.post('http://localhost:7002/api/history/update-all', json={
            'date_start': start_date.strftime('%Y-%m-%d'),
            'date_end': end_date.strftime('%Y-%m-%d')
        })
        logger.info(f"自动更新响应: {response.status_code}")
    except Exception as e:
        logger.error(f"自动更新失败: {e}")

def setup_scheduler():
    """设置定时任务"""
    global scheduler
    
    try:
        # 清除现有任务
        if scheduler.running:
            scheduler.remove_all_jobs()
        
        # 获取配置
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM system_config LIMIT 1")
        config = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if config and config['auto_update_enabled']:
            # 解析时间
            time_str = str(config['daily_update_time'])
            if len(time_str) == 8:  # HH:MM:SS
                time_parts = time_str.split(':')
            else:  # HH:MM
                time_parts = time_str.split(':')
            
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            
            # 添加定时任务
            scheduler.add_job(
                func=auto_update_task,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='daily_update',
                name='每日自动更新期货数据'
            )
            logger.info(f"定时任务已设置: 每天 {time_str}")
        else:
            logger.info("自动更新已禁用")
    except Exception as e:
        logger.error(f"设置定时任务失败: {e}")



if __name__ == '__main__':
    # 初始化数据库
    init_database()
    
    # 启动定时任务调度器
    scheduler.start()
    setup_scheduler()
    
    # 注册关闭时的清理函数
    atexit.register(lambda: scheduler.shutdown())
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=7002, debug=True)
