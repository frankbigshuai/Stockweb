def register_blueprints(app):
    """注册所有蓝图"""
    from app.api.main import main_bp
    from app.api.auth import auth_bp
    from app.api.user import user_bp
    from app.api.static import static_bp
    from app.api.stocks import stocks_bp 
    from app.api.forum import forum_bp # 新增
    
    # 注册蓝图
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(user_bp, url_prefix='/api/v1/users')
    app.register_blueprint(stocks_bp, url_prefix='/api/v1/stocks')  # 新增
    app.register_blueprint(forum_bp, url_prefix='/api/v1/forum')
    app.register_blueprint(static_bp)