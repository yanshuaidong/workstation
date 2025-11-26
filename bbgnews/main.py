#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bloomberg数据接收服务
接收浏览器扩展劫持的数据并保存为JSON文件
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 数据保存目录
DATA_DIR = 'captured_data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

@app.route('/api/capture', methods=['POST', 'OPTIONS'])
def capture_data():
    """接收劫持的Bloomberg数据"""
    
    # 处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # 获取POST的JSON数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '没有接收到数据'
            }), 400
        
        # 生成当天的文件名（按日期）
        today = datetime.now().strftime('%Y%m%d')
        filename = f'bloomberg_data_{today}.json'
        filepath = os.path.join(DATA_DIR, filename)
        
        # 读取现有文件或创建新文件结构
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        else:
            existing_data = {
                'capturedData': [],
                'serverReceivedTime': datetime.now().isoformat()
            }
        
        # 获取新接收的数据列表
        new_items = data.get('capturedData', [])
        
        # 获取已存在的所有publishedAt值（用于去重）
        existing_published_at = {
            item.get('publishedAt') 
            for item in existing_data['capturedData'] 
            if item.get('publishedAt')
        }
        
        # 过滤掉重复的数据
        added_count = 0
        for item in new_items:
            published_at = item.get('publishedAt')
            if published_at and published_at not in existing_published_at:
                existing_data['capturedData'].append(item)
                existing_published_at.add(published_at)
                added_count += 1
        
        # 更新服务器接收时间
        existing_data['serverReceivedTime'] = datetime.now().isoformat()
        
        # 保存到JSON文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
        
        print(f'✅ 数据已保存: {filename}')
        print(f'📊 新增: {added_count} 条 | 总计: {len(existing_data["capturedData"])} 条')
        print(f'🔗 URL: {data.get("capturedUrl", "未知")}')
        
        return jsonify({
            'success': True,
            'message': '数据保存成功',
            'filename': filename,
            'added': added_count,
            'total': len(existing_data['capturedData'])
        }), 200
        
    except Exception as e:
        print(f'❌ 错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'service': 'Bloomberg数据接收服务',
        'port': 1123,
        'time': datetime.now().isoformat()
    })

@app.route('/api/list', methods=['GET'])
def list_files():
    """列出所有保存的文件"""
    try:
        files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
        files.sort(reverse=True)  # 最新的在前面
        
        return jsonify({
            'success': True,
            'count': len(files),
            'files': files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print('='*60)
    print('🚀 Bloomberg数据接收服务启动')
    print(f'📍 监听端口: 1123')
    print(f'💾 数据保存目录: {os.path.abspath(DATA_DIR)}')
    print(f'🔗 接口地址: http://localhost:1123/api/capture')
    print(f'💚 健康检查: http://localhost:1123/api/health')
    print('='*60)
    
    app.run(host='0.0.0.0', port=1123, debug=True)

