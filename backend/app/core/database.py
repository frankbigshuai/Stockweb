from flask_pymongo import PyMongo
import os

mongo = PyMongo()

def init_db(app):
    """初始化数据库连接"""
    try:
        # 检查环境变量
        mongodb_uri = os.environ.get('MONGO_URL')
        if not mongodb_uri:
            print("⚠️  警告: MONGO_URL 环境变量未设置")
            print("应用将在无数据库模式下运行")
            return mongo
        
        print(f"📊 原始 MongoDB URI: {mongodb_uri}")
        
        # 🔧 不添加数据库名，使用 Railway 默认配置
        print(f"📊 使用原始 MongoDB URI（不添加数据库名）")
        
        # 设置配置
        app.config['MONGO_URI'] = mongodb_uri
        
        print("📊 开始初始化 PyMongo...")
        mongo.init_app(app)
        print("📊 PyMongo 初始化完成")
        
        # 在应用上下文中测试
        with app.app_context():
            print(f"📊 检查 mongo.db: {type(mongo.db)}")
            
            if mongo.db is not None:
                # 测试数据库操作
                result = mongo.db.command('ping')
                print(f"📊 Flask-PyMongo ping 结果: {result}")
                
                # 🔧 列出可用的数据库
                try:
                    admin_db = mongo.cx.admin
                    databases = admin_db.command('listDatabases')
                    print(f"📊 可用数据库: {databases}")
                except Exception as list_err:
                    print(f"📊 无法列出数据库: {list_err}")
                
                print("✅ Flask-PyMongo 连接成功")
                
                # 创建索引
                create_indexes()
            else:
                print("❌ mongo.db 仍然是 None")
                raise Exception("Flask-PyMongo 初始化失败")
            
    except Exception as e:
        print(f"⚠️  MongoDB初始化失败: {e}")
        print("应用将在无数据库模式下继续运行")
    
    return mongo

def create_indexes():
    """创建数据库索引"""
    try:
        if mongo.db is None:
            print("⚠️  跳过索引创建：数据库未连接")
            return
        
        print("📊 开始创建数据库索引...")
        print(f"📊 当前数据库名: {mongo.db.name}")
        
        # 用户集合索引
        mongo.db.users.create_index([("username", 1)], unique=True)
        mongo.db.users.create_index([("email", 1)], unique=True)
        
        # 论坛帖子索引
        mongo.db.posts.create_index([("created_at", -1)])
        mongo.db.posts.create_index([("author_id", 1)])
        mongo.db.posts.create_index([("category", 1)])
        mongo.db.posts.create_index([("is_deleted", 1)])
        mongo.db.posts.create_index([("likes", -1)])
        mongo.db.posts.create_index([("views", -1)])
        
        # 评论索引
        mongo.db.comments.create_index([("post_id", 1)])
        mongo.db.comments.create_index([("author_id", 1)])
        mongo.db.comments.create_index([("created_at", 1)])
        
        # 点赞记录索引
        mongo.db.post_likes.create_index([("post_id", 1), ("user_id", 1)], unique=True)
        
        # 自选股索引
        mongo.db.user_favorites.create_index([("user_id", 1)])
        mongo.db.user_favorites.create_index([("symbol", 1)])
        mongo.db.user_favorites.create_index([("user_id", 1), ("symbol", 1)], unique=True)
        mongo.db.user_favorites.create_index([("added_at", -1)])
        
        print("✅ 数据库索引创建成功")
        
    except Exception as e:
        print(f"⚠️  索引创建失败: {e}")