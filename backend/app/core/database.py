from flask_pymongo import PyMongo

mongo = PyMongo()

def init_db(app):
    """初始化数据库连接"""
    try:
        mongo.init_app(app)
        
        # 测试连接
        with app.app_context():
            # 尝试连接数据库
            mongo.db.command('ping')
            print("✓ MongoDB连接成功")
            
            # 创建索引
            create_indexes()
            
    except Exception as e:
        print(f"✗ MongoDB连接失败: {e}")
        print("请确保MongoDB服务正在运行")
        raise e
    
    return mongo

def create_indexes():
    """创建数据库索引"""
    try:
        # 用户集合索引
        mongo.db.users.create_index([("username", 1)], unique=True)
        mongo.db.users.create_index([("email", 1)], unique=True)
        
        # 论坛帖子索引
        mongo.db.posts.create_index([("created_at", -1)])  # 按时间排序
        mongo.db.posts.create_index([("author_id", 1)])    # 按作者查询
        mongo.db.posts.create_index([("category", 1)])     # 按分类查询
        mongo.db.posts.create_index([("is_deleted", 1)])   # 过滤已删除
        mongo.db.posts.create_index([("likes", -1)])       # 按点赞数排序
        mongo.db.posts.create_index([("views", -1)])       # 按浏览数排序
        
        # 评论索引
        mongo.db.comments.create_index([("post_id", 1)])   # 按帖子查询评论
        mongo.db.comments.create_index([("author_id", 1)]) # 按作者查询
        mongo.db.comments.create_index([("created_at", 1)]) # 按时间排序
        
        # 点赞记录索引
        mongo.db.post_likes.create_index([("post_id", 1), ("user_id", 1)], unique=True)
        
        # 【新增】自选股索引
        mongo.db.user_favorites.create_index([("user_id", 1)])  # 按用户查询
        mongo.db.user_favorites.create_index([("symbol", 1)])   # 按股票代码查询
        mongo.db.user_favorites.create_index([("user_id", 1), ("symbol", 1)], unique=True)  # 防重复
        mongo.db.user_favorites.create_index([("added_at", -1)])  # 按添加时间排序
        
        print("✓ 数据库索引创建成功")
        
    except Exception as e:
        print(f"⚠ 索引创建警告: {e}")
        # 索引可能已经存在，不需要抛出异常