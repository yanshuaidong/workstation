#!/usr/bin/env python3
"""
GitHub Webhook 自动部署服务器
监听GitHub推送事件，自动触发部署更新

使用方法:
1. 在服务器上运行: python3 webhook-server.py
2. 在GitHub仓库设置中添加Webhook: http://your-server-ip:9000/webhook
3. 设置Secret为环境变量WEBHOOK_SECRET的值

端口: 9000
"""

import os
import sys
import json
import hmac
import hashlib
import subprocess
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 配置
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'your-webhook-secret-here')
PROJECT_PATH = os.environ.get('PROJECT_PATH', '/opt/futures-system')
ALLOWED_BRANCHES = ['main', 'master']
PORT = int(os.environ.get('WEBHOOK_PORT', 9000))

class WebhookHandler(BaseHTTPRequestHandler):
    
    def do_POST(self):
        if self.path != '/webhook':
            self.send_response(404)
            self.end_headers()
            return
        
        try:
            # 读取请求数据
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # 验证签名
            if not self.verify_signature(post_data):
                logger.warning("Invalid signature")
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b'Invalid signature')
                return
            
            # 解析JSON数据
            try:
                payload = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError:
                logger.error("Invalid JSON payload")
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Invalid JSON')
                return
            
            # 检查事件类型
            event_type = self.headers.get('X-GitHub-Event', '')
            if event_type != 'push':
                logger.info(f"Ignoring event type: {event_type}")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Event ignored')
                return
            
            # 检查分支
            ref = payload.get('ref', '')
            branch = ref.split('/')[-1] if ref.startswith('refs/heads/') else ''
            
            if branch not in ALLOWED_BRANCHES:
                logger.info(f"Ignoring branch: {branch}")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Branch ignored')
                return
            
            # 获取提交信息
            commits = payload.get('commits', [])
            if not commits:
                logger.info("No commits in payload")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'No commits')
                return
            
            latest_commit = commits[-1]
            commit_id = latest_commit.get('id', '')[:8]
            commit_message = latest_commit.get('message', '')
            author = latest_commit.get('author', {}).get('name', 'Unknown')
            
            logger.info(f"Received push to {branch}: {commit_id} - {commit_message} by {author}")
            
            # 触发部署
            self.trigger_deployment(branch, commit_id, commit_message, author)
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Deployment triggered')
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f'Error: {str(e)}'.encode())
    
    def verify_signature(self, payload):
        """验证GitHub Webhook签名"""
        signature = self.headers.get('X-Hub-Signature-256', '')
        if not signature:
            return False
        
        expected_signature = 'sha256=' + hmac.new(
            WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def trigger_deployment(self, branch, commit_id, commit_message, author):
        """触发部署更新"""
        try:
            logger.info(f"Starting deployment for {branch}...")
            
            # 切换到项目目录
            os.chdir(PROJECT_PATH)
            
            # 执行更新脚本
            result = subprocess.run(
                ['./update.sh', branch],
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode == 0:
                logger.info("Deployment successful")
                logger.info(f"Output: {result.stdout}")
            else:
                logger.error("Deployment failed")
                logger.error(f"Error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("Deployment timeout")
        except Exception as e:
            logger.error(f"Deployment error: {e}")
    
    def do_GET(self):
        """健康检查端点"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'project_path': PROJECT_PATH,
                'allowed_branches': ALLOWED_BRANCHES
            }
            
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """重写日志方法"""
        logger.info(f"{self.client_address[0]} - {format % args}")

def main():
    """启动Webhook服务器"""
    if not os.path.exists(PROJECT_PATH):
        logger.error(f"Project path does not exist: {PROJECT_PATH}")
        sys.exit(1)
    
    if not os.path.exists(os.path.join(PROJECT_PATH, 'update.sh')):
        logger.error(f"Update script not found: {PROJECT_PATH}/update.sh")
        sys.exit(1)
    
    server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
    logger.info(f"Webhook server starting on port {PORT}")
    logger.info(f"Project path: {PROJECT_PATH}")
    logger.info(f"Allowed branches: {ALLOWED_BRANCHES}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped")
        server.server_close()

if __name__ == '__main__':
    main()
