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
        
        # 🔧 添加调试信息
        print(f"📊 MongoDB URI 前30字符: {mongodb_uri[:30]}...")
        print(f"📊 URI 总长度: {len(mongodb_uri)}")
        
        # 设置连接字符串
        app.config['MONGO_URI'] = mongodb_uri
        
        # 🔧 添加调试信息
        print("📊 开始初始化 PyMongo...")
        mongo.init_app(app)
        print("📊 PyMongo 初始化完成")
        
        # 测试连接
        with app.app_context():
            # 🔧 检查 mongo.db 是否存在
            print(f"📊 mongo.db 状态: {type(mongo.db)}")
            if mongo.db is None:
                print("❌ mongo.db 是 None！PyMongo 初始化可能失败")
                return mongo
            
            # 🔧 尝试更简单的连接测试
            print("📊 尝试连接测试...")
            result = mongo.db.command('ping', maxTimeMS=10000)  # 增加到10秒
            print(f"📊 Ping 结果: {result}")
            print("✅ MongoDB连接成功")
            
            # 创建索引
            create_indexes()
            
    except Exception as e:
        print(f"⚠️  MongoDB连接失败: {e}")
        print(f"📊 错误类型: {type(e)}")
        
        # 🔧 打印完整错误信息
        import traceback
        print(f"📊 完整错误: {traceback.format_exc()}")
        
        print("应用将在无数据库模式下继续运行")
    
    return mongo

def create_indexes():
    """创建数据库索引"""
    try:
        # 检查 mongo.db 
        if mongo.db is None:
            print("⚠️  跳过索引创建：mongo.db 是 None")
            return
            
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