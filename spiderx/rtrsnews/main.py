from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 数据存储目录
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


@app.route('/save-article', methods=['POST'])
def save_article():
    """
    接收文章数据并保存为 JSON 文件
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '没有接收到数据'}), 400
        
        # 验证必要字段
        if 'paragraphs' not in data:
            return jsonify({'error': '缺少 paragraphs 字段'}), 400
        
        # 生成文件名（使用时间戳）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'article_{timestamp}.json'
        filepath = os.path.join(DATA_DIR, filename)
        
        # 准备保存的数据
        save_data = {
            'url': data.get('url', ''),
            'title': data.get('title', ''),
            'paragraphs': data.get('paragraphs', []),
            'paragraph_count': len(data.get('paragraphs', [])),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'saved_at': datetime.now().isoformat()
        }
        
        # 保存到 JSON 文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        print(f'✓ 成功保存文章到: {filepath}')
        print(f'  - 段落数量: {save_data["paragraph_count"]}')
        print(f'  - 标题: {save_data["title"]}')
        
        return jsonify({
            'success': True,
            'message': '文章保存成功',
            'filename': filename,
            'paragraph_count': save_data['paragraph_count'],
            'filepath': filepath
        }), 200
        
    except Exception as e:
        print(f'✗ 保存文章时出错: {str(e)}')
        return jsonify({'error': str(e)}), 500


@app.route('/articles', methods=['GET'])
def list_articles():
    """
    列出所有已保存的文章
    """
    try:
        files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
        files.sort(reverse=True)  # 按时间倒序
        
        articles = []
        for filename in files:
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                article_data = json.load(f)
                articles.append({
                    'filename': filename,
                    'title': article_data.get('title', ''),
                    'url': article_data.get('url', ''),
                    'paragraph_count': article_data.get('paragraph_count', 0),
                    'saved_at': article_data.get('saved_at', '')
                })
        
        return jsonify({
            'success': True,
            'count': len(articles),
            'articles': articles
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/article/<filename>', methods=['GET'])
def get_article(filename):
    """
    获取指定文章的完整内容
    """
    try:
        filepath = os.path.join(DATA_DIR, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            article_data = json.load(f)
        
        return jsonify({
            'success': True,
            'article': article_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查端点
    """
    return jsonify({
        'status': 'running',
        'message': 'Reuters News Scraper API is running'
    }), 200


if __name__ == '__main__':
    print('=' * 60)
    print('Reuters News Scraper API Server')
    print('=' * 60)
    print(f'数据存储目录: {os.path.abspath(DATA_DIR)}')
    print('服务器启动在: http://localhost:1125')
    print('=' * 60)
    app.run(host='0.0.0.0', port=1125, debug=True)

