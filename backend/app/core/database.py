from flask_pymongo import PyMongo
import os

mongo = PyMongo()

def init_db(app):
    """初始化数据库连接"""
    try:
        # 🔧 修改这行：MONGODB_URI → MONGO_URL
        mongodb_uri = os.environ.get('MONGO_URL')
        if not mongodb_uri:
            print("⚠️  警告: MONGO_URL 环境变量未设置")  # 🔧 修改这行
            print("应用将在无数据库模式下运行")
            return mongo
        
        # 设置连接字符串
        app.config['MONGO_URI'] = mongodb_uri
        mongo.init_app(app)
        
        # 测试连接（设置短超时）
        with app.app_context():
            # 设置较短的超时时间
            mongo.db.command('ping', maxTimeMS=5000)  # 5秒超时
            print("✅ MongoDB连接成功")
            
            # 创建索引
            create_indexes()
            
    except Exception as e:
        print(f"⚠️  MongoDB连接失败: {e}")
        print("应用将在无数据库模式下继续运行")
        # 不要抛出异常，让应用继续启动
        # raise e  ← 注释掉这行！
    
    return mongo

def create_indexes():
    """创建数据库索引"""
    try:
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
        print(f"⚠️  索引创建警告: {e}")
        # 索引可能已经存在或数据库不可用，不抛出异常