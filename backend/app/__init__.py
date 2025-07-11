def create_app(config_name='development'):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # ❌ 删除或注释掉这些测试路由：
    # @app.route('/')
    # def hello():
    #     return "Hello World! App is running!"
    
    # @app.route('/health')
    # def health():
    #     return {"status": "ok", "message": "App is healthy"}
    
    # ✅ 保留其他配置
    app.config.from_object(config[config_name])
    CORS(app)
    init_db(app)
    
    try:
        from .api import register_blueprints
        register_blueprints(app)
        print("✅ API蓝图注册成功")
    except Exception as e:
        print(f"⚠️  API蓝图注册失败: {e}")
    
    return app