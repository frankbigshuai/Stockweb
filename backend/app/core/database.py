from pymongo import MongoClient
from flask import current_app, g
import os

# 全局数据库客户端
mongo_client = None
mongo_db = None

def init_db(app):
    """初始化数据库连接"""
    global mongo_client, mongo_db
    
    try:
        # 检查环境变量
        mongodb_uri = os.environ.get('MONGO_URL')
        if not mongodb_uri:
            print("⚠️  警告: MONGO_URL 环境变量未设置")
            print("应用将在无数据库模式下运行")
            return None
        
        print(f"📊 MongoDB URI: {mongodb_uri[:50]}...")
        
        # 🔧 使用原生 pymongo
        print("📊 使用原生 pymongo 连接...")
        mongo_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        
        # 测试连接
        mongo_client.admin.command('ping')
        print("✅ pymongo 连接测试成功")
        
        # 🔧 使用默认数据库（从 URI 解析）或创建新数据库
        if '/' in mongodb_uri and mongodb_uri.count('/') >= 3:
            # URI 中包含数据库名
            db_name = mongodb_uri.split('/')[-1].split('?')[0]
            if db_name:
                mongo_db = mongo_client[db_name]
                print(f"📊 使用 URI 中的数据库: {db_name}")
            else:
                mongo_db = mongo_client['stockweb']
                print("📊 使用默认数据库: stockweb")
        else:
            mongo_db = mongo_client['stockweb']
            print("📊 创建新数据库: stockweb")
        
        # 测试数据库操作
        result = mongo_db.command('ping')
        print(f"📊 数据库操作测试: {result}")
        
        # 将数据库对象保存到 Flask app
        app.config['MONGO_CLIENT'] = mongo_client
        app.config['MONGO_DB'] = mongo_db
        
        # 创建索引
        create_indexes()
        
        print("✅ 数据库初始化完成")
        
    except Exception as e:
        print(f"⚠️  数据库初始化失败: {e}")
        import traceback
        print(f"📊 完整错误: {traceback.format_exc()}")
        print("应用将在无数据库模式下继续运行")
        mongo_client = None
        mongo_db = None

def get_db():
    """获取数据库连接"""
    global mongo_db
    return mongo_db

def create_indexes():
    """创建数据库索引"""
    global mongo_db
    
    try:
        if mongo_db is None:
            print("⚠️  跳过索引创建：数据库未连接")
            return
        
        print("📊 开始创建数据库索引...")
        
        # 用户集合索引
        mongo_db.users.create_index([("username", 1)], unique=True)
        mongo_db.users.create_index([("email", 1)], unique=True)
        
        # 论坛帖子索引
        mongo_db.posts.create_index([("created_at", -1)])
        mongo_db.posts.create_index([("author_id", 1)])
        mongo_db.posts.create_index([("category", 1)])
        mongo_db.posts.create_index([("is_deleted", 1)])
        mongo_db.posts.create_index([("likes", -1)])
        mongo_db.posts.create_index([("views", -1)])
        
        # 评论索引
        mongo_db.comments.create_index([("post_id", 1)])
        mongo_db.comments.create_index([("author_id", 1)])
        mongo_db.comments.create_index([("created_at", 1)])
        
        # 点赞记录索引
        mongo_db.post_likes.create_index([("post_id", 1), ("user_id", 1)], unique=True)
        
        # 自选股索引
        mongo_db.user_favorites.create_index([("user_id", 1)])
        mongo_db.user_favorites.create_index([("symbol", 1)])
        mongo_db.user_favorites.create_index([("user_id", 1), ("symbol", 1)], unique=True)
        mongo_db.user_favorites.create_index([("added_at", -1)])
        
        print("✅ 数据库索引创建成功")
        
    except Exception as e:
        print(f"⚠️  索引创建失败: {e}")

# 为了向后兼容，提供一个 mock mongo 对象
class MockMongo:
    def __init__(self):
        pass
    
    @property
    def db(self):
        return get_db()

mongo = MockMongo()