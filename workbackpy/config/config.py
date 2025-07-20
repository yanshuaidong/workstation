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
    
    # API 配置
    API_VERSION = 'v1'
    API_TITLE = 'Flask API Service'
    API_DESCRIPTION = 'Flask 后端 API 服务'
    
    # CORS 配置
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:8080').split(',')
    
    # 其他配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    JSONIFY_PRETTYPRINT_REGULAR = True

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