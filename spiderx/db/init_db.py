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

        # 创建 reuters_news 表（路透社新闻）
        # 字段说明：
        # - published_time: 新闻发布时间
        # - title: 新闻标题
        # - url: 新闻地址（完整URL）
        # - status: 状态（0-未处理，1-已处理）
        # - created_at: 创建时间
        # - updated_at: 更新时间
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reuters_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            published_time DATETIME NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            status INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 创建 reuters_news 表的索引以提高查询效率
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reuters_published_time 
        ON reuters_news(published_time DESC);
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reuters_status 
        ON reuters_news(status);
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reuters_created_at 
        ON reuters_news(created_at DESC);
        """)
        
        # 创建 published_time 唯一索引用于去重
        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_reuters_published_time 
        ON reuters_news(published_time);
        """)

        # 创建 analysis_task 表
        # 字段说明：
        # - title: 任务标题
        # - prompt: 提示词/分析内容
        # - news_time: 新闻时间
        # - gemini_result: Gemini AI分析结果
        # - chatgpt_result: ChatGPT AI分析结果
        # - doubao_result: 豆包 AI分析结果
        # - gemini_analyzed: Gemini是否已分析（0/1）
        # - chatgpt_analyzed: ChatGPT是否已分析（0/1）
        # - doubao_analyzed: 豆包是否已分析（0/1）
        # - is_analyzed: 是否全部分析完成（三个AI都分析完后自动设为1）
        # - created_at: 创建时间
        # - updated_at: 更新时间
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_task (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            prompt TEXT NOT NULL,
            news_time DATETIME,
            gemini_result TEXT DEFAULT '',
            chatgpt_result TEXT DEFAULT '',
            doubao_result TEXT DEFAULT '',
            gemini_analyzed INTEGER DEFAULT 0,
            chatgpt_analyzed INTEGER DEFAULT 0,
            doubao_analyzed INTEGER DEFAULT 0,
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


def migrate_db():
    """
    数据库迁移：为现有的 analysis_task 表添加三AI支持字段
    如果字段已存在则跳过
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_task';")
        if not cursor.fetchone():
            print("⚠️  analysis_task 表不存在，跳过迁移")
            conn.close()
            return False
        
        # 获取现有列
        cursor.execute("PRAGMA table_info(analysis_task);")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # 需要添加的新列（三个AI）
        new_columns = [
            ("gemini_result", "TEXT DEFAULT ''"),
            ("chatgpt_result", "TEXT DEFAULT ''"),
            ("doubao_result", "TEXT DEFAULT ''"),
            ("gemini_analyzed", "INTEGER DEFAULT 0"),
            ("chatgpt_analyzed", "INTEGER DEFAULT 0"),
            ("doubao_analyzed", "INTEGER DEFAULT 0"),
        ]
        
        added_columns = []
        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                cursor.execute(f"ALTER TABLE analysis_task ADD COLUMN {col_name} {col_type};")
                added_columns.append(col_name)
                print(f"   添加字段: {col_name}")
        
        # 如果有旧的 ai_result 字段，将其数据迁移到 gemini_result
        if 'ai_result' in existing_columns and 'gemini_result' in added_columns:
            cursor.execute("""
                UPDATE analysis_task 
                SET gemini_result = ai_result, 
                    gemini_analyzed = is_analyzed
                WHERE ai_result != '' AND ai_result IS NOT NULL;
            """)
            print("📦 已将旧的 ai_result 数据迁移到 gemini_result")
        
        conn.commit()
        
        if added_columns:
            print(f"✅ 数据库迁移成功：添加了 {len(added_columns)} 个新字段")
        else:
            print("ℹ️  数据库已是最新版本，无需迁移")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库迁移失败：{e}")
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
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        # 执行迁移
        migrate_db()
    else:
        # 初始化或迁移
        if DB_PATH.exists():
            print("📊 数据库已存在，执行迁移...")
            migrate_db()
        else:
            init_db()
