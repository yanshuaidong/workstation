#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini Helper 后端服务
功能：
1. 从本地 SQLite 数据库读取待分析任务
2. 接收插件发送的 Gemini 响应结果
3. 将结果写入阿里云 MySQL 数据库
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import sqlite3
import os
import json
import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# ==================== 日志配置 ====================

# 日志文件路径
LOG_FILE = os.path.join(os.path.dirname(__file__), 'gemini_helper.log')

# 创建日志记录器
logger = logging.getLogger('gemini_helper')
logger.setLevel(logging.DEBUG)

# 日志格式
log_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 文件处理器（带日志轮转，最大10MB，保留5个备份）
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=10*1024*1024,
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(log_formatter)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_formatter)

# 添加处理器
logger.addHandler(file_handler)
logger.addHandler(console_handler)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# ==================== 配置 ====================

# 本地数据库路径（crawler.db）
LOCAL_DB_PATH = os.path.join(os.path.dirname(__file__), '../db/crawler.db')

# 数据库配置（阿里云）
DB_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}


# ==================== 数据库操作 ====================

def get_db_connection():
    """获取阿里云数据库连接"""
    return pymysql.connect(**DB_CONFIG)


def get_local_db_connection():
    """获取本地 SQLite 数据库连接"""
    if not os.path.exists(LOCAL_DB_PATH):
        raise FileNotFoundError(f"本地数据库不存在: {LOCAL_DB_PATH}")
    # 设置30秒超时，避免与ChatGPT服务并发写入时锁冲突
    conn = sqlite3.connect(LOCAL_DB_PATH, timeout=30)
    # 启用WAL模式提高并发性能
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def get_unanalyzed_tasks():
    """
    从本地数据库获取 Gemini 未分析的任务
    
    Returns:
        dict: 包含任务列表的字典
    """
    conn = None
    try:
        conn = get_local_db_connection()
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row  # 使结果可以像字典一样访问
        
        # 查询 Gemini 未分析的任务（只检查 gemini_analyzed 字段）
        query_sql = """
            SELECT id, title, prompt, news_time, created_at
            FROM analysis_task
            WHERE gemini_analyzed = 0
            ORDER BY news_time DESC, created_at DESC
        """
        cursor.execute(query_sql)
        rows = cursor.fetchall()
        
        # 转换为字典列表
        tasks = []
        for row in rows:
            tasks.append({
                'id': row[0],
                'title': row[1],
                'prompt': row[2],
                'news_time': row[3],
                'created_at': row[4]
            })
        
        logger.info(f"从本地数据库获取到 {len(tasks)} 个 Gemini 待分析任务")
        
        return {
            'success': True,
            'count': len(tasks),
            'tasks': tasks
        }
        
    except Exception as e:
        logger.error(f"查询本地数据库失败: {e}")
        return {
            'success': False,
            'message': f'查询本地数据库失败: {str(e)}',
            'count': 0,
            'tasks': []
        }
        
    finally:
        if conn:
            conn.close()


def update_task_status(task_id, ai_result):
    """
    更新本地数据库中任务的 Gemini 分析状态
    
    Args:
        task_id: 任务ID
        ai_result: Gemini 分析结果
    
    Returns:
        dict: 包含成功状态和消息
    """
    conn = None
    try:
        conn = get_local_db_connection()
        cursor = conn.cursor()
        
        # 更新 Gemini 分析状态
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_sql = """
            UPDATE analysis_task
            SET gemini_analyzed = 1,
                gemini_result = ?,
                updated_at = ?
            WHERE id = ?
        """
        cursor.execute(update_sql, (ai_result, current_time, task_id))
        
        # 检查是否两个AI都已分析完成，如果是则标记 is_analyzed = 1
        cursor.execute("""
            UPDATE analysis_task
            SET is_analyzed = 1
            WHERE id = ? AND gemini_analyzed = 1 AND chatgpt_analyzed = 1
        """, (task_id,))
        
        conn.commit()
        
        # 检查是否全部完成
        cursor.execute("SELECT gemini_analyzed, chatgpt_analyzed FROM analysis_task WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if row:
            gemini_done, chatgpt_done = row[0], row[1]
            logger.info(f"任务 {task_id} 状态: Gemini={gemini_done}, ChatGPT={chatgpt_done}")
        
        logger.info(f"本地数据库 Gemini 分析状态已更新: task_id={task_id}")
        
        return {
            'success': True,
            'message': 'Gemini 分析状态已更新'
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"更新任务状态失败: {e}")
        return {
            'success': False,
            'message': f'更新任务状态失败: {str(e)}'
        }
        
    finally:
        if conn:
            conn.close()


def save_to_database(title, content, task_id=None):
    """
    将结果保存到阿里云数据库
    
    Args:
        title: 标题
        content: AI 返回的内容
        task_id: 本地数据库任务ID（如果有）
    
    Returns:
        dict: 包含成功状态和消息
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 当前时间戳（秒）
        current_timestamp = int(time.time())
        
        # 1. 插入到 news_red_telegraph 表
        insert_news_sql = """
            INSERT INTO news_red_telegraph 
            (ctime, title, content, ai_analysis, message_score, message_label, message_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_news_sql, (
            current_timestamp,
            title,
            content,
            '暂无分析',
            6,
            'hard',
            'gemini新闻'
        ))
        
        # 获取刚插入的新闻 ID
        news_id = cursor.lastrowid
        
        # 2. 插入到 news_process_tracking 表
        insert_tracking_sql = """
            INSERT INTO news_process_tracking 
            (news_id, ctime)
            VALUES (%s, %s)
        """
        cursor.execute(insert_tracking_sql, (news_id, current_timestamp))
        
        conn.commit()
        
        logger.info(f"阿里云数据库成功保存: news_id={news_id}, title={title}")
        
        # 如果有本地任务ID，更新本地数据库状态
        if task_id:
            update_result = update_task_status(task_id, content)
            if not update_result['success']:
                logger.warning(f"本地数据库更新失败: {update_result['message']}")
        
        return {
            'success': True,
            'message': '数据已保存到数据库',
            'news_id': news_id
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"数据库保存失败: {e}")
        return {
            'success': False,
            'message': f'数据库保存失败: {str(e)}'
        }
        
    finally:
        if conn:
            cursor.close()
            conn.close()


# ==================== API 接口 ====================

@app.route('/get-tasks', methods=['GET'])
def get_tasks():
    """
    获取待分析的任务列表（从本地数据库）
    返回格式：
    {
      "success": true,
      "count": 2,
      "tasks": [
        {
          "id": 1,
          "title": "标题",
          "prompt": "分析内容",
          "news_time": "2025-12-05 12:00:00",
          "created_at": "2025-12-05 12:00:00"
        }
      ]
    }
    """
    try:
        result = get_unanalyzed_tasks()
        
        if result['success']:
            logger.info(f"成功返回 {result['count']} 个待分析任务")
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'count': 0,
            'tasks': []
        }), 500


@app.route('/save-result', methods=['POST'])
def save_result():
    """
    接收并保存 Gemini 的响应结果
    请求格式：
    {
      "title": "2025年11月1日股票新闻",
      "content": "AI 返回的内容",
      "task_id": 123  // 可选，本地数据库任务ID
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '缺少请求数据'}), 400
        
        if 'title' not in data or 'content' not in data:
            return jsonify({'success': False, 'message': '缺少 title 或 content 字段'}), 400
        
        title = data['title']
        content = data['content']
        task_id = data.get('task_id')  # 可选参数
        
        logger.info(f"收到保存请求 - 标题: {title}, 内容长度: {len(content)}, 任务ID: {task_id}")
        
        # 保存到阿里云数据库（同时会更新本地数据库状态）
        db_result = save_to_database(title, content, task_id)
        
        if not db_result['success']:
            return jsonify(db_result), 500
        
        return jsonify({
            'success': True,
            'message': '结果已保存到数据库',
            'news_id': db_result.get('news_id')
        }), 200
        
    except Exception as e:
        logger.error(f"保存结果时出错: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    return jsonify({
        'status': 'running',
        'service': 'Gemini Helper Backend',
        'port': 1124,
        'db_connected': test_db_connection()
    }), 200


def test_db_connection():
    """测试数据库连接"""
    try:
        conn = get_db_connection()
        conn.close()
        return True
    except:
        return False


# ==================== 启动服务 ====================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Gemini Helper 后端服务启动中...")
    logger.info(f"日志文件: {LOG_FILE}")
    logger.info(f"本地数据库: {LOCAL_DB_PATH}")
    logger.info(f"阿里云数据库: {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    logger.info("服务地址: http://localhost:1124")
    logger.info("=" * 60)
    
    # 测试阿里云数据库连接
    if test_db_connection():
        logger.info("✅ 阿里云数据库连接成功")
    else:
        logger.warning("⚠️  阿里云数据库连接失败，请检查配置")
    
    # 测试本地数据库
    if os.path.exists(LOCAL_DB_PATH):
        logger.info("✅ 本地数据库文件存在")
    else:
        logger.warning("⚠️  本地数据库文件不存在")
    
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=1124, debug=True)
