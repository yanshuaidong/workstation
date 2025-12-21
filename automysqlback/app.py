"""
期货数据更新系统后端服务 - 主入口文件
技术栈：Flask + akshare + pandas + MySQL + APScheduler
数据库：阿里云RDS MySQL

系统架构：
- app.py: 主入口文件，包含系统设置、数据库初始化、定时任务调度
- contracts_routes.py: 合约管理模块（合约、历史数据、分时行情、推荐记录）
- news_routes.py: 新闻管理模块（新闻CRUD、处理流程、OSS文件管理）
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import os
import sys
import logging
import atexit
import oss2
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from pathlib import Path
import requests

# 导入蓝图模块
from routes import contracts_bp, news_bp, positions_bp, events_bp

# 加载环境变量
# 优先加载本地 .env 文件，支持多环境配置

def load_env_config():
    """智能加载环境配置"""
    env_files = [
        '.env',  # 本地配置文件
        'env.production',  # 生产环境配置
    ]
    
    for env_file in env_files:
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)
            print(f"已加载环境配置: {env_file}")
            return env_file
    
    print("未找到环境配置文件，使用默认配置")
    return None

# 加载环境配置
loaded_config = load_env_config()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 输出配置加载信息
if loaded_config:
    logger.info(f"环境配置已加载: {loaded_config}")
else:
    logger.warning("使用默认配置运行")

# 环境检测
environment = os.getenv('ENVIRONMENT', 'development')
logger.info(f"运行环境: {environment}")

# 配置验证
def validate_config():
    """验证关键配置项"""
    critical_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing_vars = []
    
    for var in critical_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"缺少关键环境变量: {missing_vars}")
        if environment == 'production':
            logger.error("生产环境不能缺少关键配置，请检查环境变量")
            sys.exit(1)
        else:
            logger.warning("开发环境缺少配置，将使用默认值")

# 验证配置
validate_config()

app = Flask(__name__)
CORS(app)

# 全局变量
scheduler = BackgroundScheduler()

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'ysd'),
    'password': os.getenv('DB_PASSWORD', 'Yan1234567'),
    'database': os.getenv('DB_NAME', 'futures'),
    'charset': 'utf8mb4'
}

# 阿里云OSS配置
OSS_CONFIG = {
    'endpoint': os.getenv('OSS_ENDPOINT', 'https://oss-cn-beijing.aliyuncs.com'),
    'bucket': os.getenv('OSS_BUCKET', 'news-screenshots'),
    'access_key_id': os.getenv('OSS_ACCESS_KEY_ID'),
    'access_key_secret': os.getenv('OSS_ACCESS_KEY_SECRET'),
    'base_url': os.getenv('OSS_BASE_URL', 'https://news-screenshots.oss-cn-beijing.aliyuncs.com')
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def get_oss_bucket():
    """获取OSS bucket对象"""
    auth = oss2.Auth(OSS_CONFIG['access_key_id'], OSS_CONFIG['access_key_secret'])
    bucket = oss2.Bucket(auth, OSS_CONFIG['endpoint'], OSS_CONFIG['bucket'])
    return bucket

# 将数据库连接函数和OSS函数传递给蓝图（通过app.config）
app.config['get_db_connection'] = get_db_connection
app.config['get_oss_bucket'] = get_oss_bucket

# 注册蓝图
app.register_blueprint(contracts_bp, url_prefix='/api')
app.register_blueprint(news_bp, url_prefix='/api')
app.register_blueprint(positions_bp, url_prefix='/api')
app.register_blueprint(events_bp, url_prefix='/api')

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
                ai_analysis MEDIUMTEXT DEFAULT NULL COMMENT '中文分析/备注（可写为什么改判定）',
                message_score TINYINT UNSIGNED DEFAULT NULL COMMENT '0-100，越高越好',
                message_label ENUM('hard','soft','unknown') NOT NULL DEFAULT 'unknown' COMMENT '消息类型标签',
                message_type VARCHAR(64) DEFAULT NULL COMMENT '如: 利好政策、并购落地、减持公告',
                market_react VARCHAR(255) DEFAULT NULL COMMENT '自由文本：大涨/大跌/没反应等',
                screenshots JSON DEFAULT NULL COMMENT '截图URL数组，如["https://...","..."]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_ctime (ctime),
                INDEX idx_created_at (created_at),
                INDEX idx_message_label (message_label),
                INDEX idx_message_score (message_score)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财联社加红电报新闻表'
        """)
        
        # 7. 消息处理流程跟踪表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_process_tracking (
                id BIGINT NOT NULL AUTO_INCREMENT,
                news_id BIGINT NOT NULL COMMENT '关联news_red_telegraph表的id',
                ctime BIGINT NOT NULL COMMENT '消息创建时间（冗余字段，方便查询）',
                
                -- 第一阶段：标签校验状态
                is_reviewed TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已完成标签校验',
                review_time TIMESTAMP NULL DEFAULT NULL COMMENT '校验完成时间',
                
                -- 第二阶段：定期跟踪状态（4个关键时间节点）
                track_day3_done TINYINT(1) NOT NULL DEFAULT 0 COMMENT '3天跟踪是否完成',
                track_day3_time TIMESTAMP NULL DEFAULT NULL COMMENT '3天跟踪完成时间',
                
                track_day7_done TINYINT(1) NOT NULL DEFAULT 0 COMMENT '7天跟踪是否完成',
                track_day7_time TIMESTAMP NULL DEFAULT NULL COMMENT '7天跟踪完成时间',
                
                track_day14_done TINYINT(1) NOT NULL DEFAULT 0 COMMENT '14天跟踪是否完成',
                track_day14_time TIMESTAMP NULL DEFAULT NULL COMMENT '14天跟踪完成时间',
                
                track_day28_done TINYINT(1) NOT NULL DEFAULT 0 COMMENT '28天跟踪是否完成',
                track_day28_time TIMESTAMP NULL DEFAULT NULL COMMENT '28天跟踪完成时间',
                
                -- 系统字段
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                PRIMARY KEY (id),
                UNIQUE KEY uk_news_id (news_id),
                KEY idx_ctime (ctime),
                KEY idx_review_status (is_reviewed, ctime),
                KEY idx_track_status (track_day3_done, track_day7_done, track_day14_done, track_day28_done),
                FOREIGN KEY (news_id) REFERENCES news_red_telegraph(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息处理流程跟踪表'
        """)
        
        # 8. 期货持仓表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS futures_positions (
                id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '主键，自增ID',
                symbol VARCHAR(64) NOT NULL COMMENT '品种：CU / SC / RB / 铜 / 石油 等',
                direction VARCHAR(64) NOT NULL COMMENT '方向：LONG / SHORT / 多 / 空 等',
                status TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '持仓状态：1=有仓(HOLD)，0=空仓(FLAT)',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_symbol (symbol),
                INDEX idx_direction (direction),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='期货持仓表'
        """)
        
        conn.commit()
        
        # 数据库迁移：检查并添加新字段（保持与原来的逻辑一致）
        # 这里省略详细的迁移代码，与原来的init_database函数保持一致
        
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
        
        conn.commit()
        logger.info("数据库表初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# ========== 系统设置API（保留在主入口文件中） ==========

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

# ========== 定时任务相关 ==========

def auto_update_task():
    """自动更新任务"""
    logger.info("执行自动更新任务")
    
    try:
        # 默认更新近一个月的数据
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # 调用更新接口
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

# ========== 应用启动 ==========

# 注意：应用启动逻辑已移至 start.py
# 如果直接运行此文件，将使用简化启动模式
if __name__ == '__main__':
    logger.warning("直接运行app.py，建议使用 'python start.py' 启动")
    
    # 初始化数据库
    init_database()
    
    # 启动定时任务调度器
    scheduler.start()
    setup_scheduler()
    
    # 注册关闭时的清理函数
    atexit.register(lambda: scheduler.shutdown())
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=7001, debug=True)

