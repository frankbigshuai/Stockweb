from flask import Blueprint, jsonify, request, send_from_directory
from app.models.user import User
from app.core.auth import login_required
import os

user_bp = Blueprint('user', __name__)

# 前端路径
FRONTEND_PATH = '/Users/yuntianzeng/Desktop/Summerprojects/stockweb/frontend'

# HTML页面路由
@user_bp.route('/profile.html')
def profile_page():
    """用户资料页面"""
    return send_from_directory(FRONTEND_PATH, 'profile.html')

# API路由
@user_bp.route('/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    """获取指定用户资料（公开接口）"""
    profile = User.get_profile(user_id)
    if profile:
        return jsonify(profile), 200
    return jsonify({"error": "用户不存在"}), 404

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_current_user_profile():
    """获取当前用户的资料"""
    user_id = request.current_user['user_id']
    profile = User.get_profile(user_id)
    
    if profile:
        profile['favorites'] = User.get_favorites(user_id)
        return jsonify({
            "success": True,
            "data": profile
        }), 200
    
    return jsonify({"error": "用户不存在"}), 404

@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_current_user_profile():
    """更新当前用户的资料"""
    user_id = request.current_user['user_id']
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "请求数据不能为空"}), 400
    
    success = User.update_profile(user_id, **data)
    
    if success:
        return jsonify({
            "success": True,
            "message": "资料更新成功"
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": "更新失败"
        }), 400

@user_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """修改密码"""
    user_id = request.current_user['user_id']
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "error": "请求数据不能为空"}), 400
    
    old_password = data.get('oldPassword')
    new_password = data.get('newPassword')
    
    if not old_password or not new_password:
        return jsonify({"success": False, "error": "旧密码和新密码不能为空"}), 400
    
    if len(new_password) < 6:
        return jsonify({"success": False, "error": "新密码长度至少6位"}), 400
    
    success = User.change_password(user_id, old_password, new_password)
    
    if success:
        return jsonify({
            "success": True,
            "message": "密码修改成功"
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": "当前密码错误"
        }), 400

@user_bp.route('/favorites', methods=['GET'])
@login_required
def get_user_favorites():
    """获取用户自选股列表"""
    try:
        user_id = request.current_user['user_id']
        
        # 🔧 修复：使用带详情的方法
        favorites = User.get_favorite_stocks_with_details(user_id)
        
        # 🔧 修复：如果获取详情失败，回退到基本列表
        if not favorites:
            basic_favorites = User.get_favorite_stocks(user_id)
            favorites = [{"symbol": symbol, "price": "N/A", "change": "N/A", "change_percent": "N/A"} 
                        for symbol in basic_favorites]
        
        print(f"返回自选股数据: {favorites}")  # 调试日志
        
        return jsonify({
            "success": True,
            "data": favorites
        }), 200
        
    except Exception as e:
        print(f"获取自选股失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    
    
@user_bp.route('/favorites/<symbol>', methods=['POST'])
@login_required
def add_favorite_stock(symbol):
    """添加自选股"""
    try:
        user_id = request.current_user['user_id']
        success = User.add_favorite_stock(user_id, symbol)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"已添加 {symbol.upper()} 到自选股"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "添加失败"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@user_bp.route('/favorites/<symbol>', methods=['DELETE'])
@login_required
def remove_favorite_stock(symbol):
    """移除自选股"""
    try:
        user_id = request.current_user['user_id']
        success = User.remove_favorite_stock(user_id, symbol)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"已从自选股中移除 {symbol.upper()}"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "移除失败"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@user_bp.route('/favorites/<symbol>/check', methods=['GET'])
@login_required
def check_favorite_status(symbol):
    """检查股票是否为自选股"""
    try:
        user_id = request.current_user['user_id']
        is_favorite = User.is_favorite_stock(user_id, symbol)
        
        return jsonify({
            "success": True,
            "is_favorite": is_favorite
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500