from flask import Flask
from flask_cors import CORS
from .config import config
from .core.database import init_db

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
    app.config.from_object(config[config_name])
    
    CORS(app)
    
    # 数据库初始化
    init_db(app)
    
    # 恢复API蓝图注册
    try:
        from app.api import register_blueprints
        register_blueprints(app)
        print("✅ API蓝图注册成功")
    except Exception as e:
        print(f"⚠️  API蓝图注册失败: {e}")
        print("应用将在基础模式下运行")
        # 不抛出异常，让应用继续运行
    
    return app