from flask import Blueprint, request, jsonify
from ..models.forum import Post, Comment, Category    # 改为相对导入
from ..core.auth import login_required    
import os

forum_bp = Blueprint('forum', __name__)

# ==================== 只保留API路由，移除HTML页面路由 ====================
# HTML页面路由现在由 static_bp 处理

@forum_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    try:
        categories = Category.get_categories()
        return jsonify({
            "success": True,
            "data": categories
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@forum_bp.route('/posts', methods=['GET'])
def get_posts():
    """获取帖子列表"""
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        category = request.args.get('category', 'all')
        sort_by = request.args.get('sort', 'latest')
        
        result = Post.get_posts(page=page, limit=limit, category=category, sort_by=sort_by)
        
        return jsonify({
            "success": True,
            "data": result
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@forum_bp.route('/posts', methods=['POST'])
@login_required
def create_post():
    """创建新帖子"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data or not data.get('title') or not data.get('content'):
            return jsonify({
                "success": False,
                "error": "标题和内容不能为空"
            }), 400
        
        # 获取当前用户ID
        user_id = request.current_user['user_id']
        
        # 创建帖子
        post_id = Post.create(
            title=data['title'],
            content=data['content'],
            author_id=user_id,
            category=data.get('category', 'general'),
            tags=data.get('tags', [])
        )
        
        if post_id:
            return jsonify({
                "success": True,
                "data": {"post_id": post_id},
                "message": "发帖成功"
            }), 201
        else:
            return jsonify({
                "success": False,
                "error": "发帖失败"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@forum_bp.route('/posts/<post_id>', methods=['GET'])
def get_post_detail(post_id):
    """获取帖子详情"""
    try:
        post = Post.get_post_detail(post_id)
        
        if not post:
            return jsonify({
                "success": False,
                "error": "帖子不存在"
            }), 404
        
        return jsonify({
            "success": True,
            "data": post
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@forum_bp.route('/posts/<post_id>', methods=['PUT'])
@login_required
def update_post(post_id):
    """更新帖子"""
    try:
        data = request.get_json()
        user_id = request.current_user['user_id']
        
        if not data:
            return jsonify({
                "success": False,
                "error": "请求数据不能为空"
            }), 400
        
        success = Post.update_post(post_id, user_id, **data)
        
        if success:
            return jsonify({
                "success": True,
                "message": "更新成功"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "更新失败或无权限"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@forum_bp.route('/posts/<post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    """删除帖子"""
    try:
        user_id = request.current_user['user_id']
        success = Post.delete_post(post_id, user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "删除成功"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "删除失败或无权限"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@forum_bp.route('/posts/<post_id>/like', methods=['POST'])
@login_required
def toggle_post_like(post_id):
    """切换帖子点赞"""
    try:
        user_id = request.current_user['user_id']
        result = Post.toggle_like(post_id, user_id)
        
        if "error" in result:
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 500
        
        return jsonify({
            "success": True,
            "data": result
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@forum_bp.route('/posts/<post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    """获取帖子评论"""
    try:
        comments = Comment.get_comments(post_id)
        
        return jsonify({
            "success": True,
            "data": comments
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@forum_bp.route('/posts/<post_id>/comments', methods=['POST'])
@login_required
def create_comment(post_id):
    """创建评论"""
    try:
        data = request.get_json()
        
        if not data or not data.get('content'):
            return jsonify({
                "success": False,
                "error": "评论内容不能为空"
            }), 400
        
        user_id = request.current_user['user_id']
        
        comment_id = Comment.create(
            post_id=post_id,
            author_id=user_id,
            content=data['content'],
            parent_id=data.get('parent_id')
        )
        
        if comment_id:
            return jsonify({
                "success": True,
                "data": {"comment_id": comment_id},
                "message": "评论成功"
            }), 201
        else:
            return jsonify({
                "success": False,
                "error": "评论失败"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@forum_bp.route('/comments/<comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    """删除评论"""
    try:
        user_id = request.current_user['user_id']
        success = Comment.delete_comment(comment_id, user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "删除成功"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "删除失败或无权限"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@forum_bp.route('/my-posts', methods=['GET'])
@login_required
def get_my_posts():
    """获取我的帖子API"""
    try:
        user_id = request.current_user['user_id']
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        
        # 调用 Post 模型的方法获取用户帖子
        result = Post.get_user_posts(user_id, page, limit)
        
        return jsonify({
            "success": True,
            "data": result
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@forum_bp.route('/debug/database')
def debug_database():
    """查看数据库状态（仅用于开发）"""
    try:
        from ..core.database import mongo  # ✅ 改为相对导入
        
        stats = {
            "users_count": mongo.db.users.count_documents({}),
            "posts_count": mongo.db.posts.count_documents({}),
            "comments_count": mongo.db.comments.count_documents({}),
            "post_likes_count": mongo.db.post_likes.count_documents({})
        }
        
        return jsonify({
            "success": True,
            "database_stats": stats
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500