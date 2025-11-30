#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini Helper 后端服务
功能：
1. 读取 prompts.json 配置
2. 为每条 prompt 加上中文日期
3. 接收插件发送的 Gemini 响应结果
4. 将结果写入阿里云数据库
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import os
import json
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# ==================== 配置 ====================

# 结果文件路径
RESULT_FILE = os.path.join(os.path.dirname(__file__), 'result.md')

# prompts.json 文件路径
PROMPTS_FILE = os.path.join(os.path.dirname(__file__), 'prompts.json')

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
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)


def save_to_database(title, content):
    """
    将结果保存到数据库
    
    Args:
        title: 标题（格式：中文日期 + promptList.title）
        content: AI 返回的内容
    
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
        
        print(f"[数据库] 成功保存: news_id={news_id}, title={title}")
        
        return {
            'success': True,
            'message': '数据已保存到数据库',
            'news_id': news_id
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"[数据库] 保存失败: {e}")
        return {
            'success': False,
            'message': f'数据库保存失败: {str(e)}'
        }
        
    finally:
        if conn:
            cursor.close()
            conn.close()


# ==================== API 接口 ====================

@app.route('/get-prompts', methods=['GET'])
def get_prompts():
    """
    获取 prompt 列表（已加工）
    返回格式：
    {
      "success": true,
      "promptList": [
        {
          "title": "股票新闻",
          "prompt": "今天是2025年11月1日\n今天有哪些重点股票新闻..."
        }
      ]
    }
    """
    try:
        # 读取 prompts.json
        if not os.path.exists(PROMPTS_FILE):
            return jsonify({
                'success': False,
                'message': f'prompts.json 文件不存在: {PROMPTS_FILE}'
            }), 404
        
        with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        prompt_list = data.get('promptList', [])
        
        # 获取当前中文日期
        now = datetime.now()
        chinese_date = f"今天是{now.year}年{now.month}月{now.day}日"
        
        # 为每条 prompt 加上日期前缀
        processed_list = []
        for item in prompt_list:
            processed_item = {
                'title': item['title'],
                'prompt': f"{chinese_date}\n{item['prompt']}"
            }
            processed_list.append(processed_item)
        
        print(f"[API] 成功返回 {len(processed_list)} 条 prompt")
        
        return jsonify({
            'success': True,
            'promptList': processed_list,
            'chinese_date': chinese_date
        }), 200
        
    except Exception as e:
        print(f"[API] 读取 prompts 失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/save-result', methods=['POST'])
def save_result():
    """
    接收并保存 Gemini 的响应结果
    请求格式：
    {
      "title": "2025年11月1日股票新闻",
      "content": "AI 返回的内容"
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
        
        print(f"[API] 收到保存请求 - 标题: {title}, 内容长度: {len(content)}")
        
        # 保存到数据库
        db_result = save_to_database(title, content)
        
        if not db_result['success']:
            return jsonify(db_result), 500
        
        # 同时保存到文件（备份）
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_content = f"\n\n{'='*80}\n"
        formatted_content += f"保存时间: {timestamp}\n"
        formatted_content += f"标题: {title}\n"
        formatted_content += f"{'='*80}\n\n"
        formatted_content += content
        formatted_content += f"\n\n{'='*80}\n"
        
        with open(RESULT_FILE, 'a', encoding='utf-8') as f:
            f.write(formatted_content)
        
        print(f"[{timestamp}] 成功保存结果: {title}")
        
        return jsonify({
            'success': True,
            'message': '结果已保存到数据库和文件',
            'news_id': db_result.get('news_id'),
            'file': RESULT_FILE
        }), 200
        
    except Exception as e:
        print(f"[API] 保存结果时出错: {str(e)}")
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
    print("="*80)
    print("Gemini Helper 后端服务启动中...")
    print(f"结果将保存到: {RESULT_FILE}")
    print(f"Prompts 配置文件: {PROMPTS_FILE}")
    print(f"数据库: {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    print("服务地址: http://localhost:1124")
    print("="*80)
    
    # 测试数据库连接
    if test_db_connection():
        print("✅ 数据库连接成功")
    else:
        print("⚠️  数据库连接失败，请检查配置")
    
    print("="*80)
    
    app.run(host='0.0.0.0', port=1124, debug=True)
