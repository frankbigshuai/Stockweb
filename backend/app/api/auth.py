from flask import Blueprint, request, jsonify, send_from_directory
from datetime import datetime
from ..models.user import User      # 改为相对导入
from ..core.auth import AuthManager, login_required    # 改为相对导入
import os

auth_bp = Blueprint('auth', __name__)

# 获取前端文件路径
FRONTEND_PATH = '/app/frontend'

@auth_bp.route('/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "healthy",
        "service": "Auth Service",
        "timestamp": datetime.utcnow().isoformat()
    })

# ---------------------- 注册路由 ----------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """处理注册页面和注册请求"""
    if request.method == 'GET':
        # 返回注册页面
        return send_from_directory(FRONTEND_PATH, 'register.html')
        
    # POST请求 - 处理注册
    data = request.get_json()
        
    # 参数验证
    if not data:
        return jsonify({"success": False, "error": "请求体不能为空"}), 400
        
    required_fields = ['username', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"success": False, "error": f"缺少必填字段: {field}"}), 400
        
    # 创建用户
    user_id = User.create(
        username=data['username'],
        email=data.get('email', ''),
        password=data['password']
    )
        
    if not user_id:
        return jsonify({"success": False, "error": "用户名或邮箱已存在"}), 400
            
    return jsonify({
        "success": True,
        "user_id": user_id,
        "message": "注册成功"
    }), 201

# ---------------------- 登录路由 ----------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """处理登录页面和登录请求"""
    if request.method == 'GET':
        # 返回登录页面
        return send_from_directory(FRONTEND_PATH, 'login.html')
    
    # POST请求 - 处理登录
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"success": False, "error": "用户名和密码不能为空"}), 400
    
    # 验证登录
    user_id = User.verify_login(data['username'], data['password'])
    
    if user_id:
        # 记录登录历史
        User.record_login(user_id, request.remote_addr)
        
        # 生成JWT token
        token = AuthManager.generate_token(user_id, data['username'])
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "username": data['username'],
            "token": token,  # 返回token给前端
            "message": "登录成功"
        }), 200
    
    return jsonify({
        "success": False,
        "error": "用户名或密码错误"
    }), 401

# ---------------------- 验证token路由 ----------------------
@auth_bp.route('/verify', methods=['POST'])
def verify_token():
    """验证token是否有效"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'valid': False, 'error': '缺少token'}), 401
    
    try:
        token = auth_header.split(' ')[1]
        result = AuthManager.verify_token(token)
        
        if result['valid']:
            # 获取最新的用户信息
            profile = User.get_profile(result['user_id'])
            return jsonify({
                'valid': True,
                'user': profile
            }), 200
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 401

# ---------------------- 登出路由 ----------------------
@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """登出（主要是前端清除token）"""
    return jsonify({
        "success": True,
        "message": "登出成功"
    }), 200

@auth_bp.route('/test')
def test():
    """测试路由"""
    return jsonify({"message": "Test route is working"})

