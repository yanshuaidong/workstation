from flask import Flask, jsonify, request
from flask_cors import CORS
from config.config import Config
from routes.api import api_bp
from utils.response_handler import ResponseHandler

def create_app():
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(Config)
    
    # 启用 CORS - 允许多个来源访问
    CORS(app, origins=[
        'http://localhost:8080', 
        'http://127.0.0.1:8080',
        'http://localhost:3000',
        'http://127.0.0.1:3000'
    ], supports_credentials=True)
    
    # 注册蓝图
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 全局错误处理
    @app.errorhandler(404)
    def not_found(error):
        return ResponseHandler.error("API 端点不存在", 404)
    
    @app.errorhandler(500)
    def internal_error(error):
        return ResponseHandler.error("服务器内部错误", 500)
    
    # 根路径欢迎页面
    @app.route('/')
    def welcome():
        return ResponseHandler.success("欢迎使用 Flask API 服务", {
            "service": "Flask API Service",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "api_test": "/api/test",
                "examples": "/api/examples"
            },
            "documentation": "查看 README.md 了解更多信息"
        })
    
    # 健康检查端点
    @app.route('/health')
    def health_check():
        return ResponseHandler.success("服务运行正常", {"status": "healthy"})
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000) 