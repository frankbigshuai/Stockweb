from bson import ObjectId
from datetime import datetime
from typing import Optional, List, Dict
from app.core.database import mongo

class Post:
    """论坛帖子模型"""
    
    @staticmethod
    def get_user_posts(user_id: str, page: int = 1, limit: int = 10) -> Dict:
        """获取用户的帖子列表"""
        try:
            skip = (page - 1) * limit
            
            # 构建查询条件 - 只查询当前用户的帖子
            query = {
                "author_id": ObjectId(user_id),
                "is_deleted": False
            }
            
            # 按创建时间倒序排列
            posts_cursor = mongo.db.posts.find(query).sort("created_at", -1).skip(skip).limit(limit)
            posts = []
            
            for post in posts_cursor:
                # 获取作者信息（就是当前用户）
                author = mongo.db.users.find_one({"_id": post["author_id"]})
                
                post_data = {
                    "id": str(post["_id"]),
                    "title": post["title"],
                    "content": post["content"],  # 返回完整内容，不截断
                    "author": {
                        "id": str(post["author_id"]),
                        "username": author["username"] if author else "已删除用户"
                    },
                    "category": post["category"],
                    "tags": post["tags"],
                    "likes": post["likes"],
                    "views": post["views"],
                    "comment_count": post["comment_count"],
                    "created_at": post["created_at"].isoformat(),
                    "updated_at": post["updated_at"].isoformat(),
                    "is_pinned": post.get("is_pinned", False)
                }
                posts.append(post_data)
            
            # 获取总数用于分页
            total = mongo.db.posts.count_documents(query)
            
            return {
                "posts": posts,
                "pagination": {
                    "current_page": page,
                    "total_pages": (total + limit - 1) // limit,
                    "total_posts": total,
                    "has_next": page * limit < total,
                    "has_prev": page > 1
                }
            }
            
        except Exception as e:
            print(f"获取用户帖子列表失败: {e}")
            return {"posts": [], "pagination": {}}
        
    @staticmethod
    def create(title: str, content: str, author_id: str, category: str = "general", 
                tags: List[str] = None) -> Optional[str]:
            """创建新帖子"""
            try:
                post_data = {
                    "title": title,
                    "content": content,
                    "author_id": ObjectId(author_id),
                    "category": category,
                    "tags": tags or [],
                    "likes": 0,
                    "views": 0,
                    "comment_count": 0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "is_pinned": False,
                    "is_deleted": False
                }
                
                result = mongo.db.posts.insert_one(post_data)
                return str(result.inserted_id)
                
            except Exception as e:
                print(f"创建帖子失败: {e}")
                return None
    
    @staticmethod
    def get_posts(page: int = 1, limit: int = 10, category: str = None, 
                  sort_by: str = "latest") -> Dict:
        """获取帖子列表"""
        try:
            skip = (page - 1) * limit
            
            # 构建查询条件
            query = {"is_deleted": False}
            if category and category != "all":
                query["category"] = category
            
            # 构建排序条件
            sort_options = {
                "latest": [("created_at", -1)],
                "popular": [("likes", -1), ("views", -1)],
                "most_commented": [("comment_count", -1)]
            }
            sort_criteria = sort_options.get(sort_by, [("created_at", -1)])
            
            # 执行查询
            posts_cursor = mongo.db.posts.find(query).sort(sort_criteria).skip(skip).limit(limit)
            posts = []
            
            for post in posts_cursor:
                # 获取作者信息
                author = mongo.db.users.find_one({"_id": post["author_id"]})
                
                post_data = {
                    "id": str(post["_id"]),
                    "title": post["title"],
                    "content": post["content"][:200] + "..." if len(post["content"]) > 200 else post["content"],
                    "author": {
                        "id": str(post["author_id"]),
                        "username": author["username"] if author else "已删除用户"
                    },
                    "category": post["category"],
                    "tags": post["tags"],
                    "likes": post["likes"],
                    "views": post["views"],
                    "comment_count": post["comment_count"],
                    "created_at": post["created_at"].isoformat(),
                    "is_pinned": post.get("is_pinned", False)
                }
                posts.append(post_data)
            
            # 获取总数用于分页
            total = mongo.db.posts.count_documents(query)
            
            return {
                "posts": posts,
                "pagination": {
                    "current_page": page,
                    "total_pages": (total + limit - 1) // limit,
                    "total_posts": total,
                    "has_next": page * limit < total,
                    "has_prev": page > 1
                }
            }
            
        except Exception as e:
            print(f"获取帖子列表失败: {e}")
            return {"posts": [], "pagination": {}}
    
    @staticmethod
    def get_post_detail(post_id: str) -> Optional[Dict]:
        """获取帖子详情"""
        try:
            # 增加浏览量
            mongo.db.posts.update_one(
                {"_id": ObjectId(post_id)},
                {"$inc": {"views": 1}}
            )
            
            post = mongo.db.posts.find_one({"_id": ObjectId(post_id), "is_deleted": False})
            if not post:
                return None
            
            # 获取作者信息
            author = mongo.db.users.find_one({"_id": post["author_id"]})
            
            return {
                "id": str(post["_id"]),
                "title": post["title"],
                "content": post["content"],
                "author": {
                    "id": str(post["author_id"]),
                    "username": author["username"] if author else "已删除用户"
                },
                "category": post["category"],
                "tags": post["tags"],
                "likes": post["likes"],
                "views": post["views"],
                "comment_count": post["comment_count"],
                "created_at": post["created_at"].isoformat(),
                "updated_at": post["updated_at"].isoformat(),
                "is_pinned": post.get("is_pinned", False)
            }
            
        except Exception as e:
            print(f"获取帖子详情失败: {e}")
            return None
    
    @staticmethod
    def update_post(post_id: str, author_id: str, **kwargs) -> bool:
        """更新帖子"""
        try:
            # 验证权限
            post = mongo.db.posts.find_one({"_id": ObjectId(post_id), "author_id": ObjectId(author_id)})
            if not post:
                return False
            
            update_data = {}
            if "title" in kwargs:
                update_data["title"] = kwargs["title"]
            if "content" in kwargs:
                update_data["content"] = kwargs["content"]
            if "category" in kwargs:
                update_data["category"] = kwargs["category"]
            if "tags" in kwargs:
                update_data["tags"] = kwargs["tags"]
            
            if update_data:
                update_data["updated_at"] = datetime.utcnow()
                
                result = mongo.db.posts.update_one(
                    {"_id": ObjectId(post_id)},
                    {"$set": update_data}
                )
                return result.modified_count > 0
            
            return False
            
        except Exception as e:
            print(f"更新帖子失败: {e}")
            return False
    
    @staticmethod
    def delete_post(post_id: str, author_id: str) -> bool:
        """删除帖子（软删除）"""
        try:
            result = mongo.db.posts.update_one(
                {"_id": ObjectId(post_id), "author_id": ObjectId(author_id)},
                {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            print(f"删除帖子失败: {e}")
            return False
    
    @staticmethod
    def toggle_like(post_id: str, user_id: str) -> Dict:
        """切换帖子点赞状态"""
        try:
            # 检查用户是否已经点赞
            like_record = mongo.db.post_likes.find_one({
                "post_id": ObjectId(post_id),
                "user_id": ObjectId(user_id)
            })
            
            if like_record:
                # 取消点赞
                mongo.db.post_likes.delete_one({"_id": like_record["_id"]})
                mongo.db.posts.update_one(
                    {"_id": ObjectId(post_id)},
                    {"$inc": {"likes": -1}}
                )
                return {"liked": False, "message": "取消点赞"}
            else:
                # 添加点赞
                mongo.db.post_likes.insert_one({
                    "post_id": ObjectId(post_id),
                    "user_id": ObjectId(user_id),
                    "created_at": datetime.utcnow()
                })
                mongo.db.posts.update_one(
                    {"_id": ObjectId(post_id)},
                    {"$inc": {"likes": 1}}
                )
                return {"liked": True, "message": "点赞成功"}
                
        except Exception as e:
            print(f"切换点赞状态失败: {e}")
            return {"error": str(e)}


class Comment:
    """评论模型"""
    
    @staticmethod
    def create(post_id: str, author_id: str, content: str, parent_id: str = None) -> Optional[str]:
        """创建评论"""
        try:
            comment_data = {
                "post_id": ObjectId(post_id),
                "author_id": ObjectId(author_id),
                "content": content,
                "parent_id": ObjectId(parent_id) if parent_id else None,
                "likes": 0,
                "created_at": datetime.utcnow(),
                "is_deleted": False
            }
            
            result = mongo.db.comments.insert_one(comment_data)
            
            # 更新帖子评论数
            mongo.db.posts.update_one(
                {"_id": ObjectId(post_id)},
                {"$inc": {"comment_count": 1}}
            )
            
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"创建评论失败: {e}")
            return None
    
    @staticmethod
    def get_comments(post_id: str) -> List[Dict]:
        """获取帖子的所有评论"""
        try:
            comments = mongo.db.comments.find({
                "post_id": ObjectId(post_id),
                "is_deleted": False
            }).sort("created_at", 1)
            
            result = []
            for comment in comments:
                # 获取作者信息
                author = mongo.db.users.find_one({"_id": comment["author_id"]})
                
                comment_data = {
                    "id": str(comment["_id"]),
                    "content": comment["content"],
                    "author": {
                        "id": str(comment["author_id"]),
                        "username": author["username"] if author else "已删除用户"
                    },
                    "likes": comment["likes"],
                    "created_at": comment["created_at"].isoformat(),
                    "parent_id": str(comment["parent_id"]) if comment["parent_id"] else None
                }
                result.append(comment_data)
            
            return result
            
        except Exception as e:
            print(f"获取评论失败: {e}")
            return []
    
    @staticmethod
    def delete_comment(comment_id: str, author_id: str) -> bool:
        """删除评论"""
        try:
            comment = mongo.db.comments.find_one({
                "_id": ObjectId(comment_id),
                "author_id": ObjectId(author_id)
            })
            
            if not comment:
                return False
            
            # 软删除评论
            result = mongo.db.comments.update_one(
                {"_id": ObjectId(comment_id)},
                {"$set": {"is_deleted": True}}
            )
            
            # 减少帖子评论数
            if result.modified_count > 0:
                mongo.db.posts.update_one(
                    {"_id": comment["post_id"]},
                    {"$inc": {"comment_count": -1}}
                )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"删除评论失败: {e}")
            return False


class Category:
    """论坛分类模型"""
    
    @staticmethod
    def get_categories() -> List[Dict]:
        """获取所有分类"""
        categories = [
            {"id": "general", "name": "综合讨论", "description": "一般性话题讨论"},
            {"id": "stocks", "name": "股票分析", "description": "个股分析和投资建议"},
            {"id": "market", "name": "市场观点", "description": "市场趋势和宏观分析"},
            {"id": "strategy", "name": "投资策略", "description": "投资方法和策略分享"},
            {"id": "news", "name": "财经新闻", "description": "财经新闻讨论"},
            {"id": "tech", "name": "技术分析", "description": "技术指标和图表分析"},
            {"id": "question", "name": "新手提问", "description": "投资入门问题"}
        ]
        return categories