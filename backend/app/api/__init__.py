def register_blueprints(app):
    """注册所有蓝图"""
    from .main import main_bp          # 改为相对导入
    from .auth import auth_bp          # 改为相对导入
    from .user import user_bp          # 改为相对导入
    from .static import static_bp      # 改为相对导入
    from .stocks import stocks_bp      # 改为相对导入
    from .forum import forum_bp        # 改为相对导入
    
    # 注册蓝图
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(user_bp, url_prefix='/api/v1/users')
    app.register_blueprint(stocks_bp, url_prefix='/api/v1/stocks')
    app.register_blueprint(forum_bp, url_prefix='/api/v1/forum')
    app.register_blueprint(static_bp)