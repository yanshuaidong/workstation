#!/usr/bin/env python3
"""
MySQL 数据库配置和表结构创建示例
仅提供可复用的核心部分：数据库配置 + 表结构创建示例

news_red_telegraph: 存储新闻原始数据及AI分析结果表
news_process_tracking: 跟踪新闻的处理流程状态表
"""

import pymysql
import logging

# ==================== 数据库配置示例 ====================

# 真实数据库配置（写死在代码里面）
DB_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}

# 获取数据库连接的标准方法
def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)


# ==================== 表结构创建示例 ====================

def create_tables():
    """
    创建数据库表结构 - 真实示例

    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        logging.info("开始创建数据库表...")
        
        # ========== 表1: 新闻主表 news_red_telegraph ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_red_telegraph (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                ctime BIGINT UNIQUE NOT NULL COMMENT '消息创建时间戳',
                title VARCHAR(500) NOT NULL COMMENT '新闻标题',
                content TEXT NOT NULL COMMENT '新闻内容',
                ai_analysis MEDIUMTEXT COMMENT 'AI分析结果（软硬消息判断）',
                message_score TINYINT UNSIGNED COMMENT '消息评分（0-10）',
                message_label ENUM('hard','soft','unknown') DEFAULT 'unknown' COMMENT '消息标签',
                message_type VARCHAR(64) COMMENT '消息类型',
                market_react VARCHAR(255) COMMENT '市场反应',
                screenshots JSON COMMENT '截图数据',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        logging.info("✓ 表 news_red_telegraph 创建成功")
        
        # ========== 表2: 消息处理流程跟踪表 news_process_tracking ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_process_tracking (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                news_id BIGINT NOT NULL COMMENT '关联news_red_telegraph表的id',
                ctime BIGINT NOT NULL COMMENT '消息创建时间（冗余字段，方便查询）',
                
                -- 第一阶段：标签校验状态
                is_reviewed TINYINT(1) NOT NULL DEFAULT '0' COMMENT '是否已完成标签校验',
                
                -- 第二阶段：定期跟踪状态（4个关键时间节点）
                track_day3_done TINYINT(1) NOT NULL DEFAULT '0' COMMENT '3天跟踪是否完成',
                track_day7_done TINYINT(1) NOT NULL DEFAULT '0' COMMENT '7天跟踪是否完成',
                track_day14_done TINYINT(1) NOT NULL DEFAULT '0' COMMENT '14天跟踪是否完成',
                track_day28_done TINYINT(1) NOT NULL DEFAULT '0' COMMENT '28天跟踪是否完成',
                
                -- 系统字段
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                UNIQUE KEY uk_news_id (news_id),
                KEY idx_ctime (ctime),
                KEY idx_review_status (is_reviewed, ctime),
                KEY idx_track_day3 (track_day3_done, ctime),
                KEY idx_track_day7 (track_day7_done, ctime),
                KEY idx_track_day14 (track_day14_done, ctime),
                KEY idx_track_day28 (track_day28_done, ctime)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息处理流程跟踪表'
        """)
        logging.info("✓ 表 news_process_tracking 创建成功")
        
        conn.commit()
        logging.info("所有表创建完成")
        
    except Exception as e:
        logging.error(f"表创建失败: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

