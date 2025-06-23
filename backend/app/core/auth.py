import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app

class AuthManager:
    """JWT认证管理器"""
    
    @staticmethod
    def generate_token(user_id: str, username: str) -> str:
        """生成JWT token"""
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(days=7),  # 7天过期
            'iat': datetime.utcnow()  # 签发时间
        }
        
        try:
            # 尝试新版本的PyJWT API
            token = jwt.encode(
                payload, 
                current_app.config['JWT_SECRET_KEY'], 
                algorithm='HS256'
            )
            # 新版本返回string，旧版本返回bytes
            if isinstance(token, bytes):
                token = token.decode('utf-8')
            return token
        except AttributeError:
            # 如果失败，尝试导入PyJWT而不是jwt
            import PyJWT
            token = PyJWT.encode(
                payload, 
                current_app.config['JWT_SECRET_KEY'], 
                algorithm='HS256'
            )
            if isinstance(token, bytes):
                token = token.decode('utf-8')
            return token
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """验证JWT token"""
        try:
            try:
                # 尝试标准导入
                payload = jwt.decode(
                    token, 
                    current_app.config['JWT_SECRET_KEY'], 
                    algorithms=['HS256']
                )
            except AttributeError:
                # 如果失败，尝试PyJWT
                import PyJWT
                payload = PyJWT.decode(
                    token, 
                    current_app.config['JWT_SECRET_KEY'], 
                    algorithms=['HS256']
                )
            
            return {
                'valid': True,
                'user_id': payload['user_id'],
                'username': payload['username']
            }
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token已过期'}
        except jwt.InvalidTokenError:
            return {'valid': False, 'error': 'Token无效'}
        except Exception as e:
            return {'valid': False, 'error': f'Token验证失败: {str(e)}'}

def login_required(f):
    """装饰器：要求用户登录"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求头获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': '缺少认证token'}), 401
        
        try:
            # Authorization: Bearer <token>
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({'error': 'Token格式错误'}), 401
        
        # 验证token
        result = AuthManager.verify_token(token)
        if not result['valid']:
            return jsonify({'error': result['error']}), 401
        
        # 将用户信息添加到请求上下文
        request.current_user = {
            'user_id': result['user_id'],
            'username': result['username']
        }
        
        return f(*args, **kwargs)
    return decorated_function