from flask import Blueprint, send_from_directory
import os

static_bp = Blueprint('static', __name__)

# 设置正确的前端路径
FRONTEND_PATH = '/Users/yuntianzeng/Desktop/Summerprojects/stockweb/frontend'

@static_bp.route('/css/<path:filename>')
def css_files(filename):
    """提供CSS文件"""
    css_dir = os.path.join(FRONTEND_PATH, 'css')
    return send_from_directory(css_dir, filename)

@static_bp.route('/js/<path:filename>')
def js_files(filename):
    """提供JS文件"""
    js_dir = os.path.join(FRONTEND_PATH, 'js')
    return send_from_directory(js_dir, filename)

@static_bp.route('/static/<path:filename>')
def static_files(filename):
    """提供其他静态文件"""
    return send_from_directory(FRONTEND_PATH, filename)

# 现有的路由
@static_bp.route('/api/v1/users/profiles.html')
def profile_page():
    """用户资料页面"""
    return send_from_directory(FRONTEND_PATH, 'profiles.html')

@static_bp.route('/stocks.html')
def stocks_page():
    """股票列表页面"""
    return send_from_directory(FRONTEND_PATH, 'stocks.html')

# 添加论坛页面路由
@static_bp.route('/api/v1/forum/forum.html')
def forum_main_page():
    """论坛主页"""
    return send_from_directory(FRONTEND_PATH, 'forum.html')

@static_bp.route('/api/v1/forum/create-post.html')
def create_post_page():
    """发帖页面"""
    return send_from_directory(FRONTEND_PATH, 'create-post.html')

@static_bp.route('/api/v1/forum/post-detail.html')
def post_detail_page():
    """帖子详情页面"""
    return send_from_directory(FRONTEND_PATH, 'post-detail.html')

@static_bp.route('/stock-detail.html')
def stock_detail_page():
    """股票详情页面"""
    return send_from_directory(FRONTEND_PATH, 'stock-detail.html')

@static_bp.route('/compare.html')
def compare_page():
    """股票比较页面"""
    return send_from_directory(FRONTEND_PATH, 'compare.html')

@static_bp.route('/images/<path:filename>')
def image_files(filename):
    """提供图片文件"""
    images_dir = os.path.join(FRONTEND_PATH, 'images')
    return send_from_directory(images_dir, filename)

@static_bp.route('/api/v1/forum/my-posts.html')
def my_posts_page():
    """我的帖子页面"""
    return send_from_directory(FRONTEND_PATH, 'my-posts.html')