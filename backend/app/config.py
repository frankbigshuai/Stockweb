import os
from datetime import timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 🔧 修改这行：MONGO_URI → MONGODB_URI
    MONGO_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/stock_app'
    
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    
    # Alpha Vantage API配置
    ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')
    ALPHA_VANTAGE_BASE_URL = 'https://www.alphavantage.co/query'
    
    # 缓存配置
    CACHE_TIMEOUT = 300  # 5分钟缓存

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    
    # 🔧 修改这行也要改
    MONGO_URI = 'mongodb://localhost:27017/stock_app_test'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}