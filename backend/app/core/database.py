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
        
        print(f"📊 MongoDB URI 前30字符: {mongodb_uri[:30]}...")
        print(f"📊 URI 总长度: {len(mongodb_uri)}")
        
        # 🔧 修改配置方式 - 移除可能导致问题的配置
        app.config['MONGO_URI'] = mongodb_uri
        # 移除这两行，它们可能导致问题
        # app.config['MONGO_CONNECT'] = False
        # app.config['MONGO_AUTO_START_REQUEST'] = False
        
        print("📊 开始初始化 PyMongo...")
        mongo.init_app(app)
        print("📊 PyMongo 初始化完成")
        
        # 🔧 在应用上下文中测试连接
        with app.app_context():
            # 测试 Flask-PyMongo 是否正常工作
            print(f"📊 检查 mongo.db: {type(mongo.db)}")
            
            if mongo.db is not None:
                # 测试数据库操作
                result = mongo.db.command('ping')
                print(f"📊 Flask-PyMongo ping 结果: {result}")
                print("✅ Flask-PyMongo 连接成功")
                
                # 立即创建索引
                create_indexes()
            else:
                print("❌ mongo.db 仍然是 None")
                
                # 🔧 备用方案：直接测试原始连接
                from pymongo import MongoClient
                client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
                client.admin.command('ping')
                print("✅ 原始 MongoDB 连接测试成功，但 Flask-PyMongo 有问题")
                client.close()
            
    except Exception as e:
        print(f"⚠️  MongoDB初始化失败: {e}")
        print(f"📊 错误类型: {type(e)}")
        import traceback
        print(f"📊 完整错误: {traceback.format_exc()}")
        print("应用将在无数据库模式下继续运行")
    
    return mongo

def create_indexes():
    """创建数据库索引"""
    try:
        if mongo.db is None:
            print("⚠️  跳过索引创建：数据库未连接")
            return
        
        print("📊 开始创建数据库索引...")
        
        # 用户集合索引
        mongo.db.users.create_index([("username", 1)], unique=True)
        mongo.db.users.create_index([("email", 1)], unique=True)
        
        # 其他索引保持不变...
        mongo.db.posts.create_index([("created_at", -1)])
        mongo.db.posts.create_index([("author_id", 1)])
        mongo.db.posts.create_index([("category", 1)])
        mongo.db.posts.create_index([("is_deleted", 1)])
        mongo.db.posts.create_index([("likes", -1)])
        mongo.db.posts.create_index([("views", -1)])
        
        mongo.db.comments.create_index([("post_id", 1)])
        mongo.db.comments.create_index([("author_id", 1)])
        mongo.db.comments.create_index([("created_at", 1)])
        
        mongo.db.post_likes.create_index([("post_id", 1), ("user_id", 1)], unique=True)
        
        mongo.db.user_favorites.create_index([("user_id", 1)])
        mongo.db.user_favorites.create_index([("symbol", 1)])
        mongo.db.user_favorites.create_index([("user_id", 1), ("symbol", 1)], unique=True)
        mongo.db.user_favorites.create_index([("added_at", -1)])
        
        print("✅ 数据库索引创建成功")
        
    except Exception as e:
        print(f"⚠️  索引创建失败: {e}")