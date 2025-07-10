from flask import Flask
from flask_cors import CORS
from .config import config  # 恢复这行
# from .core.database import init_db

def create_app(config_name='development'):
    """应用工厂函数"""
    app = Flask(__name__)
    
    @app.route('/')
    def hello():
        return "Hello World! App is running!"
    
    @app.route('/health')
    def health():
        return {"status": "ok", "message": "App is healthy"}
    
    # 恢复配置加载
    app.config.from_object(config[config_name])  # 恢复这行
    
    CORS(app)
    
    # 仍然注释数据库和API
    # init_db(app)
    # from app.api import register_blueprints
    # register_blueprints(app)
    
    return app