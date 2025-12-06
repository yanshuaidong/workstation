"""
数据库初始化模块
用于创建和初始化 SQLite 数据库及相关表结构
"""
import os
import sqlite3
from pathlib import Path

# 数据库路径配置（在当前目录下创建）
DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "crawler.db"


def init_db():
    """
    初始化数据库，创建必要的表结构
    """
    try:
        # 连接数据库（如果文件不存在会自动创建）
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 创建 bloomberg_news 表
        # 字段说明：
        # - published_at: 新闻发布日期
        # - headline: 新闻标题
        # - brand: 新闻类型/品牌
        # - url: 新闻地址
        # - status: 状态（0-未处理，1-已处理）
        # - created_at: 创建时间
        # - updated_at: 更新时间
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bloomberg_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            published_at DATETIME NOT NULL,
            headline TEXT NOT NULL,
            brand TEXT DEFAULT '',
            url TEXT NOT NULL,
            status INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 创建 bloomberg_news 表的索引以提高查询效率
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_published_at 
        ON bloomberg_news(published_at DESC);
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_status 
        ON bloomberg_news(status);
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_at 
        ON bloomberg_news(created_at DESC);
        """)
        
        # 创建 published_at 唯一索引用于去重
        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_published_at 
        ON bloomberg_news(published_at);
        """)

        # 创建 analysis_task 表
        # 字段说明：
        # - title: 任务标题
        # - prompt: 提示词/分析内容
        # - news_time: 新闻时间
        # - ai_result: AI分析结果
        # - is_analyzed: 是否已分析（0/1）
        # - created_at: 创建时间
        # - updated_at: 更新时间
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_task (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            prompt TEXT NOT NULL,
            news_time DATETIME,
            ai_result TEXT DEFAULT '',
            is_analyzed INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # 创建 analysis_task 表的索引
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_analysis_task_is_analyzed 
        ON analysis_task(is_analyzed);
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_analysis_task_created_at 
        ON analysis_task(created_at DESC);
        """)

        conn.commit()
        print(f"✅ 数据库初始化成功：{DB_PATH}")
        print(f"📊 数据库位置：{DB_PATH.absolute()}")
        
        # 显示表信息
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 已创建表：{', '.join([t[0] for t in tables])}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败：{e}")
        return False


def get_db_connection():
    """
    获取数据库连接
    
    Returns:
        sqlite3.Connection: 数据库连接对象
    """
    if not DB_PATH.exists():
        print("⚠️  数据库文件不存在，正在初始化...")
        init_db()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 支持字典式访问
    return conn


if __name__ == "__main__":
    init_db()
