from flask import Blueprint, jsonify, send_from_directory
from datetime import datetime
import os

main_bp = Blueprint('main', __name__)

# 设置前端路径
FRONTEND_PATH = '/Users/yuntianzeng/Desktop/Summerprojects/stockweb/frontend'

@main_bp.route('/')
def index():
    """返回HTML首页"""
    return send_from_directory(FRONTEND_PATH, 'index.html')

@main_bp.route('/api')
def api_info():
    """API信息页面 - 移到 /api 路径"""
    return jsonify({
        "name": "Stock Web API", 
        "version": "1.0.0",
        "description": "股票信息分析平台API",
        "endpoints": {
            "auth": {
                "register": "POST /api/v1/auth/register",
                "login": "POST /api/v1/auth/login",
                "health": "GET /api/v1/auth/health"
            },
            "users": {
                "profile": "GET /api/v1/users/profile/<user_id>"
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    })

@main_bp.route('/health')
def health():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "Stock Web API",
        "timestamp": datetime.utcnow().isoformat()
    })