from flask import Flask
from flask_cors import CORS
# 暂时注释可能有问题的导入
# from .config import config
# from .core.database import init_db

def create_app(config_name='development'):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 简单的健康检查路由
    @app.route('/')
    def hello():
        return "Hello World! App is running!"
    
    @app.route('/health')
    def health():
        return {"status": "ok", "message": "App is healthy"}
    
    # 基本配置
    app.config['SECRET_KEY'] = 'temp-secret-key'
    
    # 初始化 CORS
    CORS(app)
    
    # 暂时注释掉可能阻塞的部分
    # app.config.from_object(config[config_name])
    # init_db(app)  # 数据库初始化可能阻塞
    
    # 注册蓝图
    # from app.api import register_blueprints
    # register_blueprints(app)
    
    return app