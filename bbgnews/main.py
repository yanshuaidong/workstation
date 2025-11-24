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
        
        # 生成文件名（使用时间戳）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f'bloomberg_data_{timestamp}.json'
        filepath = os.path.join(DATA_DIR, filename)
        
        # 添加服务器接收时间
        data['serverReceivedTime'] = datetime.now().isoformat()
        
        # 保存到JSON文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 同时保存为latest.json（最新的一份）
        latest_filepath = os.path.join(DATA_DIR, 'latest.json')
        with open(latest_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f'✅ 数据已保存: {filename}')
        print(f'📦 数据大小: {data.get("dataSize", "未知")} bytes')
        print(f'🔗 URL: {data.get("capturedUrl", "未知")}')
        
        return jsonify({
            'success': True,
            'message': '数据保存成功',
            'filename': filename,
            'timestamp': timestamp
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

