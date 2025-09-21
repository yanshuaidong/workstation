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
import ta
import numpy as np
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import sys
import requests

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
        
        # 5. 推荐记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendation_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE NOT NULL COMMENT '日期',
                long_names TEXT NULL COMMENT '推荐做多的品种中文名（逗号分隔）',
                short_names TEXT NULL COMMENT '推荐做空的品种中文名（逗号分隔）',
                total_long_count INT DEFAULT 0 COMMENT '做多品种数量',
                total_short_count INT DEFAULT 0 COMMENT '做空品种数量',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_date (date),
                INDEX idx_date (date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日多空推荐记录表'
        """)
        
        # 6. 财联社加红电报新闻表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_red_telegraph (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                ctime BIGINT UNIQUE NOT NULL COMMENT '新闻时间戳（用于去重）',
                title VARCHAR(500) NOT NULL COMMENT '新闻标题',
                content TEXT NOT NULL COMMENT '新闻内容',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_ctime (ctime),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财联社加红电报新闻表'
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
        
        # 迁移现有历史数据表，添加技术指标字段
        cursor.execute("SHOW TABLES LIKE 'hist_%'")
        all_hist_tables = [table[0] for table in cursor.fetchall()]
        
        # 过滤掉非期货历史数据表（如history_update_log等）
        # 只保留格式为 hist_{symbol} 的表，排除 history_update_log 等表
        existing_tables = []
        for table_name in all_hist_tables:
            # 排除特定的非期货历史数据表
            if table_name not in ['history_update_log']:
                # 检查表是否确实有期货历史数据表的结构（有trade_date字段）
                try:
                    cursor.execute(f"""
                        SELECT COUNT(*) 
                        FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA = DATABASE() 
                        AND TABLE_NAME = '{table_name}' 
                        AND COLUMN_NAME = 'trade_date'
                    """)
                    if cursor.fetchone()[0] > 0:
                        existing_tables.append(table_name)
                except Exception as e:
                    logger.warning(f"检查表{table_name}结构时出错: {e}")
        
        for table_name in existing_tables:
            # 检查是否已有技术指标字段
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = '{table_name}' 
                AND COLUMN_NAME = 'macd_dif'
            """)
            
            has_indicators = cursor.fetchone()[0] > 0
            
            # 检查是否已有推荐字段
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = '{table_name}' 
                AND COLUMN_NAME = 'recommendation'
            """)
            
            has_recommendation = cursor.fetchone()[0] > 0
            
            if not has_indicators:
                # 修改现有字段类型并添加技术指标字段和推荐字段
                cursor.execute(f"""
                    ALTER TABLE {table_name}
                    MODIFY COLUMN open_price DECIMAL(10,2) NOT NULL COMMENT '开盘价',
                    MODIFY COLUMN high_price DECIMAL(10,2) NOT NULL COMMENT '最高价',
                    MODIFY COLUMN low_price DECIMAL(10,2) NOT NULL COMMENT '最低价',
                    MODIFY COLUMN close_price DECIMAL(10,2) NOT NULL COMMENT '收盘价',
                    MODIFY COLUMN turnover DECIMAL(20,2) NOT NULL DEFAULT 0 COMMENT '成交额',
                    MODIFY COLUMN price_change DECIMAL(10,2) DEFAULT 0 COMMENT '涨跌',
                    MODIFY COLUMN change_pct DECIMAL(10,2) DEFAULT 0.00 COMMENT '涨跌幅',
                    ADD COLUMN macd_dif DECIMAL(10,4) NULL COMMENT 'MACD快线' AFTER change_pct,
                    ADD COLUMN macd_dea DECIMAL(10,4) NULL COMMENT 'MACD慢线' AFTER macd_dif,
                    ADD COLUMN macd_histogram DECIMAL(10,4) NULL COMMENT 'MACD柱状图' AFTER macd_dea,
                    ADD COLUMN rsi_14 DECIMAL(6,2) NULL COMMENT 'RSI(14)' AFTER macd_histogram,
                    ADD COLUMN kdj_k DECIMAL(6,2) NULL COMMENT 'KDJ-K值' AFTER rsi_14,
                    ADD COLUMN kdj_d DECIMAL(6,2) NULL COMMENT 'KDJ-D值' AFTER kdj_k,
                    ADD COLUMN kdj_j DECIMAL(6,2) NULL COMMENT 'KDJ-J值' AFTER kdj_d,
                    ADD COLUMN bb_upper DECIMAL(10,2) NULL COMMENT '布林带上轨' AFTER kdj_j,
                    ADD COLUMN bb_middle DECIMAL(10,2) NULL COMMENT '布林带中轨' AFTER bb_upper,
                    ADD COLUMN bb_lower DECIMAL(10,2) NULL COMMENT '布林带下轨' AFTER bb_middle,
                    ADD COLUMN bb_width DECIMAL(10,2) NULL COMMENT '布林带宽度' AFTER bb_lower,
                    ADD COLUMN recommendation VARCHAR(20) NULL COMMENT '推荐操作：做多/做空/观察' AFTER bb_width
                """)
                logger.info(f"已为表 {table_name} 添加技术指标字段和推荐字段")
            elif not has_recommendation:
                # 只添加推荐字段
                cursor.execute(f"""
                    ALTER TABLE {table_name}
                    ADD COLUMN recommendation VARCHAR(20) NULL COMMENT '推荐操作：做多/做空/观察' AFTER bb_width
                """)
                logger.info(f"已为表 {table_name} 添加推荐字段")
        
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
                open_price DECIMAL(10,2) NOT NULL COMMENT '开盘价',
                high_price DECIMAL(10,2) NOT NULL COMMENT '最高价',
                low_price DECIMAL(10,2) NOT NULL COMMENT '最低价',
                close_price DECIMAL(10,2) NOT NULL COMMENT '收盘价',
                volume BIGINT NOT NULL DEFAULT 0 COMMENT '成交量',
                open_interest BIGINT NOT NULL DEFAULT 0 COMMENT '持仓量',
                turnover DECIMAL(20,2) NOT NULL DEFAULT 0 COMMENT '成交额',
                price_change DECIMAL(10,2) DEFAULT 0 COMMENT '涨跌',
                change_pct DECIMAL(10,2) DEFAULT 0.00 COMMENT '涨跌幅',
                macd_dif DECIMAL(10,4) NULL COMMENT 'MACD快线',
                macd_dea DECIMAL(10,4) NULL COMMENT 'MACD慢线',
                macd_histogram DECIMAL(10,4) NULL COMMENT 'MACD柱状图',
                rsi_14 DECIMAL(6,2) NULL COMMENT 'RSI(14)',
                kdj_k DECIMAL(6,2) NULL COMMENT 'KDJ-K值',
                kdj_d DECIMAL(6,2) NULL COMMENT 'KDJ-D值',
                kdj_j DECIMAL(6,2) NULL COMMENT 'KDJ-J值',
                bb_upper DECIMAL(10,2) NULL COMMENT '布林带上轨',
                bb_middle DECIMAL(10,2) NULL COMMENT '布林带中轨',
                bb_lower DECIMAL(10,2) NULL COMMENT '布林带下轨',
                bb_width DECIMAL(10,2) NULL COMMENT '布林带宽度',
                recommendation VARCHAR(20) NULL COMMENT '推荐操作：做多/做空/观察',
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

def calculate_technical_indicators(df):
    """计算技术指标"""
    try:
        if df.empty or len(df) < 2:
            return df
        
        # 确保数据按日期排序
        df = df.sort_values('时间').reset_index(drop=True)
        
        # 转换价格数据为float类型
        price_cols = ['开盘', '最高', '最低', '收盘']
        for col in price_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 成交量转换
        df['成交量'] = pd.to_numeric(df.get('成交量', 0), errors='coerce').fillna(0)
        
        # 初始化技术指标列
        df['macd_dif'] = np.nan
        df['macd_dea'] = np.nan
        df['macd_histogram'] = np.nan
        df['rsi_14'] = np.nan
        df['kdj_k'] = np.nan
        df['kdj_d'] = np.nan
        df['kdj_j'] = np.nan
        df['bb_upper'] = np.nan
        df['bb_middle'] = np.nan
        df['bb_lower'] = np.nan
        df['bb_width'] = np.nan
        
        # 检查数据质量
        if df['收盘'].isna().all():
            logger.warning("收盘价数据全部为空，无法计算技术指标")
            return df
        
        # 1. 计算MACD (12,26,9)
        try:
            if len(df) >= 26:  # MACD至少需要26个数据点
                macd_data = ta.trend.MACD(close=df['收盘'], window_slow=26, window_fast=12, window_sign=9)
                df['macd_dif'] = macd_data.macd()
                df['macd_dea'] = macd_data.macd_signal()
                df['macd_histogram'] = macd_data.macd_diff()
        except Exception as e:
            logger.warning(f"MACD计算失败: {e}")
        
        # 2. 计算RSI (14)
        try:
            if len(df) >= 14:  # RSI需要至少14个数据点
                df['rsi_14'] = ta.momentum.RSIIndicator(close=df['收盘'], window=14).rsi()
        except Exception as e:
            logger.warning(f"RSI计算失败: {e}")
        
        # 3. 计算KDJ (9,3,3)
        try:
            if len(df) >= 9:  # KDJ需要至少9个数据点
                # 计算StochasticOscillator
                stoch = ta.momentum.StochasticOscillator(
                    high=df['最高'], 
                    low=df['最低'], 
                    close=df['收盘'], 
                    window=9, 
                    smooth_window=3
                )
                df['kdj_k'] = stoch.stoch()
                df['kdj_d'] = stoch.stoch_signal()
                # J = 3*K - 2*D
                df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        except Exception as e:
            logger.warning(f"KDJ计算失败: {e}")
        
        # 4. 计算布林带 (20,2)
        try:
            if len(df) >= 20:  # 布林带需要至少20个数据点
                bb = ta.volatility.BollingerBands(close=df['收盘'], window=20, window_dev=2)
                df['bb_upper'] = bb.bollinger_hband()
                df['bb_middle'] = bb.bollinger_mavg()
                df['bb_lower'] = bb.bollinger_lband()
                df['bb_width'] = bb.bollinger_wband()
        except Exception as e:
            logger.warning(f"布林带计算失败: {e}")
        
        return df
        
    except Exception as e:
        logger.error(f"技术指标计算失败: {e}")
        return df

def record_daily_recommendations(date_str):
    """
    记录指定日期的推荐操作到推荐记录表
    
    参数:
    - date_str: 日期字符串，格式为 'YYYY-MM-DD'
    """
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 获取所有主连合约
        cursor.execute("""
            SELECT symbol, name FROM contracts_main 
            WHERE is_active = 1 
            ORDER BY symbol
        """)
        contracts = cursor.fetchall()
        
        long_names = []  # 推荐做多的品种
        short_names = []  # 推荐做空的品种
        
        # 遍历每个合约，查询最新的推荐操作
        for contract in contracts:
            symbol = contract['symbol']
            name = contract['name']
            table_name = f"hist_{symbol}"
            
            try:
                # 查询指定日期的推荐操作
                cursor.execute(f"""
                    SELECT recommendation FROM {table_name}
                    WHERE trade_date = %s
                    LIMIT 1
                """, (date_str,))
                
                result = cursor.fetchone()
                if result and result['recommendation']:
                    recommendation = result['recommendation']
                    # 解析推荐操作（格式：做多 (3) 或 做空 (-2) 或 观察 (1)）
                    if recommendation.startswith('做多'):
                        # 提取分值，格式：做多 (3)
                        score_match = re.search(r'\(([+-]?\d+)\)', recommendation)
                        score = score_match.group(1) if score_match else '0'
                        long_names.append(f"{name}（{score}）")
                    elif recommendation.startswith('做空'):
                        # 提取分值，格式：做空 (-2)
                        score_match = re.search(r'\(([+-]?\d+)\)', recommendation)
                        score = score_match.group(1) if score_match else '0'
                        short_names.append(f"{name}（{score}）")
                    # 观察的不记录到推荐列表中
                        
            except Exception as e:
                logger.warning(f"查询合约 {symbol} 的推荐操作失败: {e}")
                continue
        
        # 构建存储格式：多品种1，品种2，空品种3，品种4
        long_names_str = '，'.join(long_names) if long_names else ''
        short_names_str = '，'.join(short_names) if short_names else ''
        
        # 插入或更新推荐记录
        cursor.execute("""
            INSERT INTO recommendation_log 
            (date, long_names, short_names, total_long_count, total_short_count)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            long_names = VALUES(long_names),
            short_names = VALUES(short_names),
            total_long_count = VALUES(total_long_count),
            total_short_count = VALUES(total_short_count),
            updated_at = NOW()
        """, (
            date_str,
            long_names_str,
            short_names_str,
            len(long_names),
            len(short_names)
        ))
        
        conn.commit()
        logger.info(f"成功记录 {date_str} 的推荐：做多 {len(long_names)} 个，做空 {len(short_names)} 个")
        return True
        
    except Exception as e:
        logger.error(f"记录每日推荐失败: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def calculate_recommendation(df, target_date_index):
    """
    基于技术指标计算推荐操作
    只为指定日期（通常是最新日期）计算推荐
    
    参数:
    - df: 包含技术指标的DataFrame
    - target_date_index: 要计算推荐的日期在DataFrame中的索引
    
    返回:
    - str: '做多', '做空', '观察'
    """
    try:
        if df.empty or target_date_index >= len(df) or target_date_index < 0:
            return '观察'
        
        # 获取目标日期的数据
        current_row = df.iloc[target_date_index]
        
        # 确保有足够的历史数据进行分析（至少需要5天数据）
        if target_date_index < 4:
            return '观察'
        
        # 获取前几天的数据用于趋势分析
        prev_row = df.iloc[target_date_index - 1] if target_date_index > 0 else current_row
        prev_2_row = df.iloc[target_date_index - 2] if target_date_index > 1 else current_row
        
        # 初始化评分系统
        bullish_score = 0  # 做多信号评分
        bearish_score = 0  # 做空信号评分
        
        # 1. MACD信号分析
        if pd.notna(current_row.get('macd_dif')) and pd.notna(current_row.get('macd_dea')):
            macd_dif = current_row['macd_dif']
            macd_dea = current_row['macd_dea']
            macd_histogram = current_row.get('macd_histogram', 0)
            
            # MACD金叉/死叉
            if pd.notna(prev_row.get('macd_dif')) and pd.notna(prev_row.get('macd_dea')):
                prev_dif = prev_row['macd_dif']
                prev_dea = prev_row['macd_dea']
                
                # 金叉：DIF上穿DEA
                if prev_dif <= prev_dea and macd_dif > macd_dea:
                    bullish_score += 3
                # 死叉：DIF下穿DEA
                elif prev_dif >= prev_dea and macd_dif < macd_dea:
                    bearish_score += 3
            
            # MACD柱状图趋势
            if macd_histogram > 0:
                bullish_score += 1
            elif macd_histogram < 0:
                bearish_score += 1
        
        # 2. RSI超买超卖分析
        if pd.notna(current_row.get('rsi_14')):
            rsi = current_row['rsi_14']
            
            if rsi < 30:  # 超卖
                bullish_score += 2
            elif rsi > 70:  # 超买
                bearish_score += 2
            elif 30 <= rsi <= 40:  # 偏超卖
                bullish_score += 1
            elif 60 <= rsi <= 70:  # 偏超买
                bearish_score += 1
        
        # 3. KDJ分析
        if (pd.notna(current_row.get('kdj_k')) and 
            pd.notna(current_row.get('kdj_d')) and 
            pd.notna(current_row.get('kdj_j'))):
            
            k = current_row['kdj_k']
            d = current_row['kdj_d']
            j = current_row['kdj_j']
            
            # KDJ金叉/死叉
            if pd.notna(prev_row.get('kdj_k')) and pd.notna(prev_row.get('kdj_d')):
                prev_k = prev_row['kdj_k']
                prev_d = prev_row['kdj_d']
                
                # K线上穿D线
                if prev_k <= prev_d and k > d:
                    bullish_score += 2
                # K线下穿D线
                elif prev_k >= prev_d and k < d:
                    bearish_score += 2
            
            # KDJ超买超卖
            if k < 20 and d < 20:  # 超卖
                bullish_score += 1
            elif k > 80 and d > 80:  # 超买
                bearish_score += 1
        
        # 4. 布林带分析
        if (pd.notna(current_row.get('bb_upper')) and 
            pd.notna(current_row.get('bb_middle')) and 
            pd.notna(current_row.get('bb_lower'))):
            
            close_price = current_row['收盘']
            bb_upper = current_row['bb_upper']
            bb_middle = current_row['bb_middle']
            bb_lower = current_row['bb_lower']
            
            # 价格突破布林带
            if close_price <= bb_lower:  # 触及下轨，可能反弹
                bullish_score += 2
            elif close_price >= bb_upper:  # 触及上轨，可能回调
                bearish_score += 2
            elif close_price > bb_middle:  # 在中轨上方
                bullish_score += 1
            elif close_price < bb_middle:  # 在中轨下方
                bearish_score += 1
        
        # 5. 价格趋势分析
        close_price = current_row['收盘']
        prev_close = prev_row['收盘'] if pd.notna(prev_row.get('收盘')) else close_price
        prev_2_close = prev_2_row['收盘'] if pd.notna(prev_2_row.get('收盘')) else close_price
        
        # 连续上涨
        if close_price > prev_close > prev_2_close:
            bullish_score += 1
        # 连续下跌
        elif close_price < prev_close < prev_2_close:
            bearish_score += 1
        
        # 6. 成交量分析（如果有数据）
        if pd.notna(current_row.get('成交量')) and pd.notna(prev_row.get('成交量')):
            volume = current_row['成交量']
            prev_volume = prev_row['成交量']
            
            # 放量上涨
            if close_price > prev_close and volume > prev_volume * 1.2:
                bullish_score += 1
            # 放量下跌
            elif close_price < prev_close and volume > prev_volume * 1.2:
                bearish_score += 1
        
        # 根据评分决定推荐
        score_diff = bullish_score - bearish_score
        
        if score_diff >= 3:  # 明显的做多信号
            return f'做多 ({score_diff})'
        elif score_diff <= -3:  # 明显的做空信号
            return f'做空 ({score_diff})'
        else:  # 信号不明确
            return f'观察 ({score_diff})'
            
    except Exception as e:
        logger.error(f"推荐计算失败: {e}")
        return '观察'

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
                
                # 计算技术指标
                logger.info(f"{symbol}({contract_name}) 开始计算技术指标")
                hist_df = calculate_technical_indicators(hist_df)
                logger.info(f"{symbol}({contract_name}) 技术指标计算完成")
                
                # 数据入库
                table_name = f"hist_{symbol}"
                success_rows = 0
                
                for idx, row in hist_df.iterrows():
                    try:
                        # 处理技术指标的NaN值
                        def handle_nan(value):
                            return None if pd.isna(value) else float(value)
                        
                        # 计算推荐操作（仅为最新日期，即最后一条记录）
                        recommendation = None
                        if idx == len(hist_df) - 1:  # 最后一条记录（最新日期）
                            recommendation = calculate_recommendation(hist_df, idx)
                            logger.info(f"{symbol} 最新日期 {row['时间']} 推荐操作: {recommendation}")
                        
                        cursor.execute(f"""
                            INSERT INTO {table_name} 
                            (trade_date, open_price, high_price, low_price, close_price, 
                             volume, open_interest, turnover, price_change, change_pct,
                             macd_dif, macd_dea, macd_histogram, rsi_14,
                             kdj_k, kdj_d, kdj_j,
                             bb_upper, bb_middle, bb_lower, bb_width, recommendation, source_ts)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
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
                            macd_dif = VALUES(macd_dif),
                            macd_dea = VALUES(macd_dea),
                            macd_histogram = VALUES(macd_histogram),
                            rsi_14 = VALUES(rsi_14),
                            kdj_k = VALUES(kdj_k),
                            kdj_d = VALUES(kdj_d),
                            kdj_j = VALUES(kdj_j),
                            bb_upper = VALUES(bb_upper),
                            bb_middle = VALUES(bb_middle),
                            bb_lower = VALUES(bb_lower),
                            bb_width = VALUES(bb_width),
                            recommendation = VALUES(recommendation),
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
                            row.get('涨跌幅', 0.0),
                            handle_nan(row.get('macd_dif')),
                            handle_nan(row.get('macd_dea')),
                            handle_nan(row.get('macd_histogram')),
                            handle_nan(row.get('rsi_14')),
                            handle_nan(row.get('kdj_k')),
                            handle_nan(row.get('kdj_d')),
                            handle_nan(row.get('kdj_j')),
                            handle_nan(row.get('bb_upper')),
                            handle_nan(row.get('bb_middle')),
                            handle_nan(row.get('bb_lower')),
                            handle_nan(row.get('bb_width')),
                            recommendation
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
                
                # 注意：推荐记录将在批量更新完成后统一处理
                
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
            
            # 批量更新完成后，记录当日推荐
            try:
                # 使用结束日期作为推荐记录的日期
                record_daily_recommendations(date_end)
                logger.info(f"已记录 {date_end} 的推荐操作")
            except Exception as e:
                logger.error(f"记录推荐操作失败: {e}")
        
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

@app.route('/api/history/recalculate-indicators', methods=['POST'])
def recalculate_indicators():
    """重新计算现有数据的技术指标"""
    data = request.get_json()
    symbol = data.get('symbol')  # 可选，如果不提供则处理所有合约
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 获取要处理的合约列表
        if symbol:
            cursor.execute("SELECT symbol FROM contracts_main WHERE symbol = %s AND is_active = 1", (symbol,))
        else:
            cursor.execute("SELECT symbol FROM contracts_main WHERE is_active = 1")
        
        symbols = [row['symbol'] for row in cursor.fetchall()]
        
        if not symbols:
            return jsonify({
                'code': 1,
                'message': '没有找到需要处理的合约'
            })
        
        def recalculate_task():
            """重新计算技术指标的后台任务"""
            success_count = 0
            total_count = len(symbols)
            
            for contract_symbol in symbols:
                try:
                    logger.info(f"开始重新计算 {contract_symbol} 的技术指标")
                    
                    # 从数据库读取历史数据
                    conn_task = get_db_connection()
                    cursor_task = conn_task.cursor(pymysql.cursors.DictCursor)
                    
                    table_name = f"hist_{contract_symbol}"
                    cursor_task.execute(f"""
                        SELECT trade_date as 时间, open_price as 开盘, high_price as 最高, 
                               low_price as 最低, close_price as 收盘, volume as 成交量,
                               open_interest as 持仓量, turnover as 成交额, 
                               price_change as 涨跌, change_pct as 涨跌幅
                        FROM {table_name} 
                        ORDER BY trade_date ASC
                    """)
                    
                    rows = cursor_task.fetchall()
                    if not rows:
                        logger.warning(f"{contract_symbol} 没有历史数据")
                        cursor_task.close()
                        conn_task.close()
                        continue
                    
                    # 转换为DataFrame
                    hist_df = pd.DataFrame(rows)
                    
                    # 计算技术指标
                    hist_df = calculate_technical_indicators(hist_df)
                    
                    # 更新数据库
                    for idx, row in hist_df.iterrows():
                        def handle_nan(value):
                            return None if pd.isna(value) else float(value)
                        
                        cursor_task.execute(f"""
                            UPDATE {table_name} SET
                            macd_dif = %s, macd_dea = %s, macd_histogram = %s,
                            rsi_14 = %s, kdj_k = %s, kdj_d = %s, kdj_j = %s,
                            bb_upper = %s, bb_middle = %s, bb_lower = %s, bb_width = %s,
                            ingest_ts = NOW()
                            WHERE trade_date = %s
                        """, (
                            handle_nan(row.get('macd_dif')),
                            handle_nan(row.get('macd_dea')),
                            handle_nan(row.get('macd_histogram')),
                            handle_nan(row.get('rsi_14')),
                            handle_nan(row.get('kdj_k')),
                            handle_nan(row.get('kdj_d')),
                            handle_nan(row.get('kdj_j')),
                            handle_nan(row.get('bb_upper')),
                            handle_nan(row.get('bb_middle')),
                            handle_nan(row.get('bb_lower')),
                            handle_nan(row.get('bb_width')),
                            row['时间']
                        ))
                    
                    conn_task.commit()
                    cursor_task.close()
                    conn_task.close()
                    
                    success_count += 1
                    logger.info(f"{contract_symbol} 技术指标重新计算完成 ({success_count}/{total_count})")
                    
                except Exception as e:
                    logger.error(f"{contract_symbol} 技术指标重新计算失败: {e}")
            
            logger.info(f"技术指标重新计算完成: {success_count}/{total_count}")
        
        # 在后台线程中执行
        threading.Thread(target=recalculate_task, daemon=True).start()
        
        return jsonify({
            'code': 0,
            'message': '技术指标重新计算已启动',
            'data': {
                'total_contracts': len(symbols),
                'target_symbol': symbol or '全部合约'
            }
        })
        
    except Exception as e:
        logger.error(f"启动技术指标重新计算失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'启动失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/api/history/data', methods=['GET'])
def get_history_data():
    """获取指定合约的历史数据"""
    symbol = request.args.get('symbol')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not symbol:
        return jsonify({
            'code': 1,
            'message': '缺少合约代码参数'
        })
    
    # 设置默认日期范围（最近一个月）
    if not start_date or not end_date:
        end_date = datetime.now().date().strftime('%Y-%m-%d')
        start_date = (datetime.now().date() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 验证合约是否存在
        cursor.execute("SELECT name FROM contracts_main WHERE symbol = %s AND is_active = 1", (symbol,))
        contract_info = cursor.fetchone()
        
        if not contract_info:
            return jsonify({
                'code': 1,
                'message': f'合约 {symbol} 不存在或未激活'
            })
        
        # 查询历史数据
        table_name = f"hist_{symbol}"
        cursor.execute(f"""
            SELECT 
                trade_date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                open_interest,
                turnover,
                price_change,
                change_pct,
                macd_dif,
                macd_dea,
                macd_histogram,
                rsi_14,
                kdj_k,
                kdj_d,
                kdj_j,
                bb_upper,
                bb_middle,
                bb_lower,
                bb_width,
                recommendation
            FROM {table_name}
            WHERE trade_date >= %s AND trade_date <= %s
            ORDER BY trade_date DESC
            LIMIT 500
        """, (start_date, end_date))
        
        history_data = cursor.fetchall()
        
        # 转换数据格式
        formatted_data = []
        for row in history_data:
            formatted_data.append({
                'date': row['trade_date'].strftime('%Y-%m-%d') if row['trade_date'] else None,
                'price': {
                    'open': float(row['open_price']) if row['open_price'] else 0,
                    'high': float(row['high_price']) if row['high_price'] else 0,
                    'low': float(row['low_price']) if row['low_price'] else 0,
                    'close': float(row['close_price']) if row['close_price'] else 0
                },
                'volume': {
                    'shares': int(row['volume']) if row['volume'] else 0,
                    'open_interest': int(row['open_interest']) if row['open_interest'] else 0,
                    'turnover': float(row['turnover']) if row['turnover'] else 0
                },
                'change': {
                    'price_change': float(row['price_change']) if row['price_change'] else 0,
                    'change_pct': float(row['change_pct']) if row['change_pct'] else 0
                },
                'indicators': {
                    'macd': {
                        'dif': float(row['macd_dif']) if row['macd_dif'] else None,
                        'dea': float(row['macd_dea']) if row['macd_dea'] else None,
                        'histogram': float(row['macd_histogram']) if row['macd_histogram'] else None
                    },
                    'rsi': float(row['rsi_14']) if row['rsi_14'] else None,
                    'kdj': {
                        'k': float(row['kdj_k']) if row['kdj_k'] else None,
                        'd': float(row['kdj_d']) if row['kdj_d'] else None,
                        'j': float(row['kdj_j']) if row['kdj_j'] else None
                    },
                    'bollinger': {
                        'upper': float(row['bb_upper']) if row['bb_upper'] else None,
                        'middle': float(row['bb_middle']) if row['bb_middle'] else None,
                        'lower': float(row['bb_lower']) if row['bb_lower'] else None,
                        'width': float(row['bb_width']) if row['bb_width'] else None
                    }
                },
                'recommendation': row['recommendation'] if row['recommendation'] else None,
                # 原始数据用于表格显示
                'raw': {
                    'trade_date': row['trade_date'].strftime('%Y-%m-%d') if row['trade_date'] else '',
                    'open_price': float(row['open_price']) if row['open_price'] else 0,
                    'high_price': float(row['high_price']) if row['high_price'] else 0,
                    'low_price': float(row['low_price']) if row['low_price'] else 0,
                    'close_price': float(row['close_price']) if row['close_price'] else 0,
                    'volume': int(row['volume']) if row['volume'] else 0,
                    'open_interest': int(row['open_interest']) if row['open_interest'] else 0,
                    'turnover': float(row['turnover']) if row['turnover'] else 0,
                    'price_change': float(row['price_change']) if row['price_change'] else 0,
                    'change_pct': float(row['change_pct']) if row['change_pct'] else 0,
                    'macd_dif': float(row['macd_dif']) if row['macd_dif'] else None,
                    'macd_dea': float(row['macd_dea']) if row['macd_dea'] else None,
                    'macd_histogram': float(row['macd_histogram']) if row['macd_histogram'] else None,
                    'rsi_14': float(row['rsi_14']) if row['rsi_14'] else None,
                    'kdj_k': float(row['kdj_k']) if row['kdj_k'] else None,
                    'kdj_d': float(row['kdj_d']) if row['kdj_d'] else None,
                    'kdj_j': float(row['kdj_j']) if row['kdj_j'] else None,
                    'bb_upper': float(row['bb_upper']) if row['bb_upper'] else None,
                    'bb_middle': float(row['bb_middle']) if row['bb_middle'] else None,
                    'bb_lower': float(row['bb_lower']) if row['bb_lower'] else None,
                    'bb_width': float(row['bb_width']) if row['bb_width'] else None,
                    'recommendation': row['recommendation'] if row['recommendation'] else None
                }
            })
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'symbol': symbol,
                'name': contract_info['name'],
                'start_date': start_date,
                'end_date': end_date,
                'total_records': len(formatted_data),
                'data': formatted_data
            }
        })
        
    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
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

@app.route('/api/intraday/contracts', methods=['GET'])
def get_intraday_contracts():
    """获取可用的期货合约列表（用于分时行情查询）"""
    try:
        logger.info("开始获取分时合约列表 - 依次获取 6个交易所数据")
        
        # 期货合约代码到中文名称的映射表
        contract_mapping = {
            # 上海期货交易所 SHFE
            'rb': '螺纹钢', 'hc': '热轧卷板', 'bu': '石油沥青', 'ru': '天然橡胶', 'br': '合成橡胶',
            'fu': '燃料油', 'sp': '纸浆', 'cu': '铜', 'al': '铝', 'ao': '氧化铝', 'pb': '铅',
            'zn': '锌', 'sn': '锡', 'ni': '镍', 'ss': '不锈钢', 'au': '黄金', 'ag': '白银',
            'wr': '线材',
            # 上海国际能源交易中心 INE
            'nr': '20号胶', 'lu': '低硫燃料油', 'bc': '国际铜', 'sc': '原油', 'ec': '集运指数(欧线)',
            # 大连商品交易所 DCE
            'a': '黄大豆1号', 'b': '黄大豆2号', 'c': '黄玉米', 'cs': '玉米淀粉', 'm': '豆粕',
            'y': '豆油', 'p': '棕榈油', 'i': '铁矿石', 'j': '焦炭', 'jm': '焦煤', 'l': '聚乙烯',
            'v': '聚氯乙烯', 'pp': '聚丙烯', 'eg': '乙二醇', 'rr': '粳米', 'eb': '苯乙烯',
            'pg': '液化石油气', 'jd': '鸡蛋', 'fb': '纤维板', 'bb': '胶合板', 'lh': '生猪',
            'lg': '原木',
            # 郑州商品交易所 CZCE
            'RM': '菜粕', 'OI': '菜籽油', 'CF': '一号棉花', 'TA': '精对苯二甲酸', 'PX': '对二甲苯',
            'SR': '白砂糖', 'MA': '甲醇', 'FG': '玻璃', 'ZC': '动力煤', 'CY': '棉纱',
            'SA': '纯碱', 'SH': '烧碱', 'PF': '短纤', 'PR': '瓶片', 'JR': '粳稻',
            'RS': '菜籽', 'PM': '普通小麦', 'WH': '强麦', 'RI': '早籼稻', 'LR': '晚籼稻',
            'SF': '硅铁', 'SM': '锰硅', 'AP': '苹果', 'CJ': '红枣', 'UR': '尿素', 'PK': '花生',
            # 广州期货交易所 GFEX
            'SI': '工业硅', 'LC': '碳酸锂', 'PS': '多晶硅',
            # 中国金融期货交易所 CFFEX
            'IF': '沪深300指数', 'IH': '上证50指数', 'IC': '中证500指数', 'IM': '中证1000指数',
            'TS': '2年期国债', 'TF': '5年期国债', 'T': '10年期国债', 'TL': '30年期国债'
        }
        
        # 获取6个交易所的主力合约数据
        exchanges = ['dce', 'czce', 'shfe', 'gfex', 'cffex', 'ine']
        all_contracts = []
        
        for exchange in exchanges:
            try:
                logger.info(f"正在获取 {exchange.upper()} 交易所主力合约")
                contracts_text = ak.match_main_contract(symbol=exchange)
                logger.info(f"{exchange}_text 类型: {type(contracts_text)}")
                logger.info(f"{exchange}_text 内容: {repr(contracts_text)}")
                
                if contracts_text and isinstance(contracts_text, str):
                    # 解析合约代码，格式如: "FU2601,SC2510,AL2510,..."
                    contract_codes = [code.strip() for code in contracts_text.split(',') if code.strip()]
                    
                    for contract_code in contract_codes:
                        # 提取品种代码（去掉数字部分）
                        variety_code = ''.join([c for c in contract_code if c.isalpha()]).upper()
                        
                        # 查找对应的中文名称（不区分大小写匹配）
                        chinese_name = None
                        for key, value in contract_mapping.items():
                            if key.upper() == variety_code.upper():
                                chinese_name = value
                                break
                        
                        # 如果没找到匹配，使用原始品种代码
                        if chinese_name is None:
                            chinese_name = variety_code
                        
                        all_contracts.append({
                            'symbol': contract_code,
                            'name': chinese_name,
                            'variety_code': variety_code,
                            'exchange': exchange.upper()
                        })
                        
                        logger.info(f"解析合约: {contract_code} -> {chinese_name} ({exchange.upper()})")
                
            except Exception as e:
                logger.error(f"获取 {exchange} 交易所数据失败: {e}")
                continue
        
        # 按交易所和品种名称排序
        all_contracts.sort(key=lambda x: (x['exchange'], x['name']))
        
        logger.info(f"总共获取到 {len(all_contracts)} 个主力合约")
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'contracts': all_contracts,
                'total': len(all_contracts)
            }
        })

    except Exception as e:
        logger.error(f"获取分时合约列表失败: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })

@app.route('/api/recommendations/record', methods=['POST'])
def record_recommendations():
    """手动记录当日推荐"""
    data = request.get_json()
    date_str = data.get('date')
    
    if not date_str:
        # 如果没有提供日期，使用当前日期
        date_str = datetime.now().date().strftime('%Y-%m-%d')
    
    try:
        success = record_daily_recommendations(date_str)
        
        if success:
            return jsonify({
                'code': 0,
                'message': f'成功记录 {date_str} 的推荐操作'
            })
        else:
            return jsonify({
                'code': 1,
                'message': f'记录 {date_str} 的推荐操作失败'
            })
    except Exception as e:
        logger.error(f"记录推荐操作失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'记录失败: {str(e)}'
        })

@app.route('/api/recommendations/list', methods=['GET'])
def get_recommendations_list():
    """获取推荐记录列表"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 设置默认日期范围（最近一个月）
    if not start_date or not end_date:
        end_date = datetime.now().date().strftime('%Y-%m-%d')
        start_date = (datetime.now().date() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                date,
                long_names,
                short_names,
                total_long_count,
                total_short_count,
                created_at,
                updated_at
            FROM recommendation_log 
            WHERE date >= %s AND date <= %s
            ORDER BY date DESC
        """, (start_date, end_date))
        
        recommendations = cursor.fetchall()
        
        # 格式化数据
        formatted_data = []
        for rec in recommendations:
            formatted_data.append({
                'date': rec['date'].strftime('%Y-%m-%d') if rec['date'] else '',
                'long_names': rec['long_names'] or '',
                'short_names': rec['short_names'] or '',
                'total_long_count': rec['total_long_count'] or 0,
                'total_short_count': rec['total_short_count'] or 0,
                'created_at': rec['created_at'].strftime('%Y-%m-%d %H:%M:%S') if rec['created_at'] else '',
                'updated_at': rec['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if rec['updated_at'] else '',
                # 格式化显示文本
                'display_text': f"{rec['date'].strftime('%m月%d日') if rec['date'] else ''} " +
                               (f"多：{rec['long_names']}" if rec['long_names'] else "多：无") +
                               (f"，空：{rec['short_names']}" if rec['short_names'] else "，空：无")
            })
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'recommendations': formatted_data,
                'total': len(formatted_data),
                'start_date': start_date,
                'end_date': end_date
            }
        })
        
    except Exception as e:
        logger.error(f"获取推荐记录失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/api/intraday/data', methods=['GET'])
def get_intraday_data():
    """获取分时行情数据"""
    symbol = request.args.get('symbol')
    period = request.args.get('period', '60')  # 默认60分钟
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not symbol:
        return jsonify({
            'code': 1,
            'message': '缺少合约代码参数'
        })
    
    # 设置默认日期范围（最近3天）
    if not start_date or not end_date:
        end_date = datetime.now().date().strftime('%Y-%m-%d')
        start_date = (datetime.now().date() - timedelta(days=3)).strftime('%Y-%m-%d')
    
    try:
        logger.info(f"获取分时数据: {symbol}, 周期: {period}, 日期范围: {start_date} 到 {end_date}")
        
        # 调用akshare获取分时数据
        logger.info(f"正在调用 ak.futures_zh_minute_sina(symbol='{symbol}', period='{period}')")
        intraday_df = ak.futures_zh_minute_sina(symbol=symbol, period=period)
        logger.info(f"akshare返回数据类型: {type(intraday_df)}")
        
        if intraday_df is None:
            logger.error(f"akshare返回了None，合约: {symbol}")
            return jsonify({
                'code': 1,
                'message': f'合约 {symbol} 获取数据失败，akshare返回None'
            })
        
        logger.info(f"获取到数据形状: {intraday_df.shape}")
        if not intraday_df.empty:
            logger.info(f"数据列名: {list(intraday_df.columns)}")
            logger.info(f"前3行数据:\n{intraday_df.head(3)}")
        
        if intraday_df.empty:
            logger.warning(f"合约 {symbol} 返回空数据")
            return jsonify({
                'code': 1,
                'message': f'合约 {symbol} 没有分时数据'
            })
        
        # 转换datetime列为字符串格式
        intraday_df['datetime'] = pd.to_datetime(intraday_df['datetime'])
        
        # 根据日期范围过滤数据
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date) + timedelta(days=1)  # 包含结束日期
        
        filtered_df = intraday_df[
            (intraday_df['datetime'] >= start_datetime) & 
            (intraday_df['datetime'] < end_datetime)
        ]
        
        # 转换为前端需要的格式
        formatted_data = []
        for idx, row in filtered_df.iterrows():
            formatted_data.append({
                'datetime': row['datetime'].strftime('%Y-%m-%d %H:%M:%S'),
                'price': {
                    'open': float(row['open']) if pd.notna(row['open']) else 0,
                    'high': float(row['high']) if pd.notna(row['high']) else 0,
                    'low': float(row['low']) if pd.notna(row['low']) else 0,
                    'close': float(row['close']) if pd.notna(row['close']) else 0
                },
                'volume': int(row['volume']) if pd.notna(row['volume']) else 0,
                'hold': int(row['hold']) if pd.notna(row['hold']) else 0,
                # 原始数据用于表格显示
                'raw': {
                    'datetime': row['datetime'].strftime('%Y-%m-%d %H:%M:%S'),
                    'open': float(row['open']) if pd.notna(row['open']) else 0,
                    'high': float(row['high']) if pd.notna(row['high']) else 0,
                    'low': float(row['low']) if pd.notna(row['low']) else 0,
                    'close': float(row['close']) if pd.notna(row['close']) else 0,
                    'volume': int(row['volume']) if pd.notna(row['volume']) else 0,
                    'hold': int(row['hold']) if pd.notna(row['hold']) else 0
                }
            })
        
        # 按时间倒序排列（最新的在前面）
        formatted_data.reverse()
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'symbol': symbol,
                'period': period,
                'start_date': start_date,
                'end_date': end_date,
                'total_records': len(formatted_data),
                'data': formatted_data
            }
        })
        
    except Exception as e:
        logger.error(f"获取分时数据失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })

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

# ========== 财联社新闻API接口 ==========

def save_news_to_db(news_data):
    """保存新闻数据到数据库"""
    if not news_data:
        return 0, 0
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    new_count = 0
    duplicate_count = 0
    
    try:
        for news_item in news_data:
            ctime = news_item.get('ctime')
            title = news_item.get('title', '')
            content = news_item.get('content', '')
            
            if not ctime or not title:
                continue
                
            try:
                # 清理HTML标签
                title = re.sub(r'<[^>]+>', '', title)
                content = re.sub(r'<[^>]+>', '', content)
                
                cursor.execute("""
                    INSERT INTO news_red_telegraph (ctime, title, content)
                    VALUES (%s, %s, %s)
                """, (ctime, title, content))
                
                new_count += 1
                logger.info(f"保存新闻: {title[:50]}...")
                
            except pymysql.IntegrityError as e:
                if e.args[0] == 1062:  # Duplicate entry
                    duplicate_count += 1
                    logger.debug(f"新闻已存在，跳过: {title[:50]}...")
                else:
                    logger.error(f"保存新闻时出错: {e}")
        
        conn.commit()
        logger.info(f"新闻保存完成: 新增{new_count}条, 重复{duplicate_count}条")
        return new_count, duplicate_count
        
    except Exception as e:
        logger.error(f"保存新闻数据失败: {e}")
        conn.rollback()
        return 0, 0
    finally:
        cursor.close()
        conn.close()

@app.route('/api/news/crawl', methods=['POST'])
def crawl_cls_news():
    """爬取财联社加红电报新闻"""
    def crawl_task():
        """后台爬取任务"""
        crawler = None
        try:
            logger.info("开始财联社新闻爬取任务")
            
            # 创建爬虫实例
            crawler = ClsNewsCrawler(headless=True)
            crawler.setup_driver()
            
            # 爬取新闻
            news_data = crawler.crawl_news()
            
            if news_data:
                # 保存到数据库
                new_count, duplicate_count = save_news_to_db(news_data)
                logger.info(f"爬取任务完成: 获取{len(news_data)}条新闻, 新增{new_count}条, 重复{duplicate_count}条")
            else:
                logger.warning("未获取到新闻数据")
                
        except Exception as e:
            logger.error(f"爬取任务执行失败: {e}")
            logger.error(traceback.format_exc())
        finally:
            if crawler:
                crawler.close()
    
    try:
        # 在后台线程中执行爬取任务
        threading.Thread(target=crawl_task, daemon=True).start()
        
        return jsonify({
            'code': 0,
            'message': '财联社新闻爬取已启动，请稍后查看结果'
        })
        
    except Exception as e:
        logger.error(f"启动爬取任务失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'启动爬取任务失败: {str(e)}'
        })

@app.route('/api/news/list', methods=['GET'])
def get_cls_news_list():
    """分页查询财联社新闻"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    
    # 限制分页参数
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 查询总数
        cursor.execute("SELECT COUNT(*) as total FROM news_red_telegraph")
        total = cursor.fetchone()['total']
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 查询新闻列表（按ctime倒序，最新的在前面）
        cursor.execute("""
            SELECT 
                id,
                ctime,
                title,
                content,
                FROM_UNIXTIME(ctime) as formatted_time,
                created_at,
                updated_at
            FROM news_red_telegraph 
            ORDER BY ctime DESC 
            LIMIT %s OFFSET %s
        """, (page_size, offset))
        
        news_list = cursor.fetchall()
        
        # 格式化数据
        formatted_news = []
        for news in news_list:
            formatted_news.append({
                'id': news['id'],
                'ctime': news['ctime'],
                'title': news['title'],
                'content': news['content'],
                'time': news['formatted_time'].strftime('%Y-%m-%d %H:%M:%S') if news['formatted_time'] else '',
                'created_at': news['created_at'].strftime('%Y-%m-%d %H:%M:%S') if news['created_at'] else '',
                'updated_at': news['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if news['updated_at'] else ''
            })
        
        # 计算分页信息
        total_pages = (total + page_size - 1) // page_size
        
        return jsonify({
            'code': 0,
            'message': '查询成功',
            'data': {
                'news_list': formatted_news,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': total_pages,
                    'has_prev': page > 1,
                    'has_next': page < total_pages
                }
            }
        })
        
    except Exception as e:
        logger.error(f"查询新闻列表失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'查询失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/api/news/stats', methods=['GET'])
def get_cls_news_stats():
    """获取新闻统计信息"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 总新闻数
        cursor.execute("SELECT COUNT(*) as total FROM news_red_telegraph")
        total = cursor.fetchone()['total']
        
        # 今日新闻数
        cursor.execute("""
            SELECT COUNT(*) as today_count 
            FROM news_red_telegraph 
            WHERE DATE(created_at) = CURDATE()
        """)
        today_count = cursor.fetchone()['today_count']
        
        # 最新新闻时间
        cursor.execute("""
            SELECT FROM_UNIXTIME(MAX(ctime)) as latest_time 
            FROM news_red_telegraph
        """)
        latest_result = cursor.fetchone()
        latest_time = latest_result['latest_time'].strftime('%Y-%m-%d %H:%M:%S') if latest_result['latest_time'] else ''
        
        # 最早新闻时间
        cursor.execute("""
            SELECT FROM_UNIXTIME(MIN(ctime)) as earliest_time 
            FROM news_red_telegraph
        """)
        earliest_result = cursor.fetchone()
        earliest_time = earliest_result['earliest_time'].strftime('%Y-%m-%d %H:%M:%S') if earliest_result['earliest_time'] else ''
        
        return jsonify({
            'code': 0,
            'message': '统计信息获取成功',
            'data': {
                'total': total,
                'today_count': today_count,
                'latest_time': latest_time,
                'earliest_time': earliest_time
            }
        })
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取统计信息失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

class ClsNewsCrawler:
    """财联社加红电报新闻爬虫"""
    
    def __init__(self, headless=True):
        self.driver = None
        self.headless = headless
        self.network_logs = []
        
    def setup_driver(self):
        """设置Chrome驱动"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 启用网络日志记录
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--log-level=0')
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        # 检查是否有远程Selenium服务URL
        selenium_remote_url = os.environ.get('SELENIUM_REMOTE_URL')
        
        try:
            if selenium_remote_url:
                logger.info(f"使用远程Selenium服务: {selenium_remote_url}")
                # 使用远程WebDriver
                self.driver = webdriver.Remote(
                    command_executor=selenium_remote_url,
                    options=chrome_options
                )
                logger.info("远程Selenium Chrome驱动初始化成功")
            else:
                logger.info("使用本地Chrome驱动")
                # 本地模式 - 尝试不同的Chrome路径
                chrome_paths = [
                    '/usr/bin/google-chrome-stable',
                    '/usr/bin/google-chrome',
                    '/usr/bin/chromium-browser',
                    '/usr/bin/chromium'
                ]
                
                for chrome_path in chrome_paths:
                    if os.path.exists(chrome_path):
                        logger.info(f"找到Chrome浏览器: {chrome_path}")
                        chrome_options.binary_location = chrome_path
                        break
                
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    logger.info("本地Chrome驱动初始化成功")
                except Exception as e:
                    logger.error(f"本地Chrome驱动初始化失败: {e}")
                    try:
                        from webdriver_manager.chrome import ChromeDriverManager
                        service = Service(ChromeDriverManager().install())
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                        logger.info("使用webdriver-manager初始化Chrome驱动成功")
                    except Exception as e2:
                        logger.error(f"webdriver-manager也失败: {e2}")
                        raise
        
        except Exception as e:
            logger.error(f"Chrome驱动初始化失败: {e}")
            raise
        
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(10)
    
    def get_network_logs(self):
        """获取网络请求日志"""
        try:
            logs = self.driver.get_log('performance')
            network_requests = []
            
            for log in logs:
                try:
                    message = json.loads(log['message'])
                    if message['message']['method'] == 'Network.responseReceived':
                        url = message['message']['params']['response']['url']
                        if 'cls.cn/v1/roll/get_roll_list' in url:
                            network_requests.append({
                                'url': url,
                                'timestamp': log['timestamp'],
                                'response': message['message']['params']['response']
                            })
                except (json.JSONDecodeError, KeyError):
                    continue
            
            return network_requests
        except Exception as e:
            logger.error(f"获取网络日志失败: {e}")
            return []
    
    def extract_params_from_url(self, url):
        """从URL中提取参数"""
        params = {}
        if '?' in url:
            query_string = url.split('?')[1]
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
        return params
    
    def click_jiahong_button(self):
        """点击加红按钮"""
        logger.info("开始寻找并点击'加红'按钮...")
        
        # 等待页面加载完成
        try:
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        except Exception as e:
            logger.warning(f"等待页面加载完成失败: {e}")
        
        # 多种选择器策略
        selectors = [
            "//a[contains(text(), '加红')]",
            "//h3[contains(@class, 'level-2-nav')]//a[contains(text(), '加红')]",
            "//h3[@class='f-l f-s-17 level-2-nav']//a[@class='p-r d-b w-94 c-p c-ef9524']",
            "//a[@class='p-r d-b w-94 c-p c-ef9524']",
            "//a[contains(@class, 'c-ef9524')]"
        ]
        
        for i, selector in enumerate(selectors):
            try:
                logger.info(f"尝试选择器 {i+1}: {selector}")
                elements = self.driver.find_elements(By.XPATH, selector)
                
                if elements:
                    element = elements[0]
                    logger.info(f"找到元素: {element.text[:50]}")
                    
                    # 滚动到元素位置
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(1)
                    
                    # 尝试点击
                    try:
                        element.click()
                        logger.info("成功点击'加红'按钮")
                        return True
                    except:
                        # 使用JavaScript点击
                        self.driver.execute_script("arguments[0].click();", element)
                        logger.info("使用JavaScript成功点击'加红'按钮")
                        return True
                        
            except Exception as e:
                logger.warning(f"选择器 {i+1} 执行失败: {e}")
                continue
        
        logger.error("未能找到或点击'加红'按钮")
        return False
    
    def make_api_request(self, url):
        """使用浏览器的cookies和headers发起API请求"""
        try:
            # 获取浏览器的cookies
            cookies = self.driver.get_cookies()
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            # 设置请求头
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json;charset=utf-8',
                'Pragma': 'no-cache',
                'Referer': 'https://www.cls.cn/telegraph',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            logger.info(f"发起API请求: {url[:100]}...")
            response = requests.get(url, headers=headers, cookies=cookie_dict, timeout=15)
            response.raise_for_status()
            
            json_data = response.json()
            logger.info("API请求成功")
            return json_data
            
        except Exception as e:
            logger.error(f"API请求失败: {e}")
            return None
    
    def crawl_news(self):
        """爬取财联社加红电报新闻"""
        try:
            logger.info("开始爬取财联社加红电报新闻")
            
            # 访问页面
            url = "https://www.cls.cn/telegraph"
            logger.info(f"访问页面: {url}")
            self.driver.get(url)
            
            # 等待页面加载
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info("页面加载完成，等待6秒...")
            time.sleep(6)
            
            # 点击加红按钮
            click_success = self.click_jiahong_button()
            
            if click_success:
                logger.info("点击成功，等待网络请求...")
                time.sleep(5)
            else:
                logger.warning("点击失败，尝试其他方式...")
                # 尝试滚动页面触发请求
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
            
            # 获取网络请求日志
            network_requests = self.get_network_logs()
            logger.info(f"捕获到 {len(network_requests)} 个网络请求")
            
            # 处理API数据
            news_data = []
            for request in network_requests:
                url = request['url']
                params = self.extract_params_from_url(url)
                
                if params.get('sign'):
                    logger.info(f"发现API请求，sign: {params.get('sign')}")
                    
                    # 尝试获取数据
                    try:
                        response = self.make_api_request(url)
                        if response and response.get('errno') == 0:
                            roll_data = response.get('data', {}).get('roll_data', [])
                            news_data.extend(roll_data)
                            logger.info(f"成功获取 {len(roll_data)} 条新闻")
                    except Exception as e:
                        logger.warning(f"API请求失败: {e}")
            
            return news_data
            
        except Exception as e:
            logger.error(f"爬取新闻失败: {e}")
            return []
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")



if __name__ == '__main__':
    # 初始化数据库
    init_database()
    
    # 启动定时任务调度器
    scheduler.start()
    setup_scheduler()
    
    # 注册关闭时的清理函数
    atexit.register(lambda: scheduler.shutdown())
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=7001, debug=True)
