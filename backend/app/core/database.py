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
        
        # 🔧 关键修复：添加数据库名
        if not mongodb_uri.endswith('/'):
            mongodb_uri += '/'
        if '?' in mongodb_uri:
            # 如果有查询参数，在数据库名后添加
            mongodb_uri = mongodb_uri.replace('?', 'stockweb?')
        else:
            # 如果没有查询参数，直接添加数据库名
            mongodb_uri += 'stockweb'
        
        print(f"📊 修改后的 MongoDB URI: {mongodb_uri}")
        
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
                print("✅ Flask-PyMongo 连接成功")
                
                # 创建索引
                create_indexes()
            else:
                print("❌ mongo.db 仍然是 None，尝试其他方法...")
                raise Exception("Flask-PyMongo 初始化失败")
            
    except Exception as e:
        print(f"⚠️  MongoDB初始化失败: {e}")
        print("📊 尝试使用原生 pymongo 作为备用方案...")
        
        # 🔧 备用方案：使用原生 pymongo
        try:
            setup_native_mongo(app, mongodb_uri)
        except Exception as backup_error:
            print(f"⚠️  备用方案也失败: {backup_error}")
            print("应用将在无数据库模式下继续运行")
    
    return mongo

def setup_native_mongo(app, mongodb_uri):
    """备用方案：使用原生 pymongo"""
    from pymongo import MongoClient
    
    print("📊 设置原生 pymongo 连接...")
    client = MongoClient(mongodb_uri)
    
    # 获取数据库
    db_name = 'stockweb'
    db = client[db_name]
    
    # 测试连接
    db.command('ping')
    print("✅ 原生 pymongo 连接成功")
    
    # 将数据库对象存储到应用配置中
    app.config['NATIVE_MONGO_CLIENT'] = client
    app.config['NATIVE_MONGO_DB'] = db
    
    # 创建索引
    create_native_indexes(db)
    
    print("📊 原生 pymongo 设置完成")

def create_native_indexes(db):
    """为原生 pymongo 创建索引"""
    try:
        print("📊 开始创建数据库索引（原生方式）...")
        
        # 用户集合索引
        db.users.create_index([("username", 1)], unique=True)
        db.users.create_index([("email", 1)], unique=True)
        
        # 其他索引...
        db.posts.create_index([("created_at", -1)])
        db.posts.create_index([("author_id", 1)])
        
        print("✅ 原生方式数据库索引创建成功")
        
    except Exception as e:
        print(f"⚠️  原生索引创建失败: {e}")

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
        
        # 论坛帖子索引
        mongo.db.posts.create_index([("created_at", -1)])
        mongo.db.posts.create_index([("author_id", 1)])
        mongo.db.posts.create_index([("category", 1)])
        mongo.db.posts.create_index([("is_deleted", 1)])
        mongo.db.posts.create_index([("likes", -1)])
        mongo.db.posts.create_index([("views", -1)])
        
        # 其他索引...
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