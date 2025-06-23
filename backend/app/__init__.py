from flask import Flask
from flask_cors import CORS
from .config import config
from .core.database import init_db

def create_app(config_name='development'):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    CORS(app)  # 允许所有跨域请求
    init_db(app)  # 初始化数据库
    
    # 注册蓝图
    from app.api import register_blueprints
    register_blueprints(app)
    
    return app