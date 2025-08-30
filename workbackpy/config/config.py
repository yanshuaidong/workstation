import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # 数据库配置
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    
    # 服务器配置 - 重要：端口配置在这里读取
    # 如果需要改变端口，请修改 .env 文件中的 PORT 值，或者修改下面的默认值
    HOST = os.environ.get('HOST') or '0.0.0.0'  # 服务器监听的主机地址
    PORT = int(os.environ.get('PORT') or 7001)   # 服务器运行的端口号，默认 7001
    
    # API 配置
    API_VERSION = 'v1'
    API_TITLE = 'Flask API Service'
    API_DESCRIPTION = 'Flask 后端 API 服务'
    
    # CORS 配置 - 跨域资源共享配置
    # 如果前端运行在不同端口，需要在环境变量 CORS_ORIGINS 中添加
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:8080').split(',')
    
    # 其他配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大上传文件大小：16MB
    JSONIFY_PRETTYPRINT_REGULAR = True      # JSON 响应格式化输出

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 