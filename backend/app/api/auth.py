from flask import Blueprint, request, jsonify, send_from_directory
from datetime import datetime
from ..models.user import User      # Relative import
from ..core.auth import AuthManager, login_required    # Relative import
import os

auth_bp = Blueprint('auth', __name__)

# Get frontend file path
FRONTEND_PATH = '/app/frontend'

@auth_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Auth Service",
        "timestamp": datetime.utcnow().isoformat()
    })

# ---------------------- Register Route ----------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handles the registration page and registration requests"""
    if request.method == 'GET':
        # Return the registration page
        return send_from_directory(FRONTEND_PATH, 'register.html')
        
    # POST request - Handle registration
    data = request.get_json()
        
    # Parameter validation
    if not data:
        return jsonify({"success": False, "error": "Request body cannot be empty"}), 400
        
    required_fields = ['username', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400
        
    # Create user
    user_id = User.create(
        username=data['username'],
        email=data.get('email', ''),
        password=data['password']
    )
        
    if not user_id:
        return jsonify({"success": False, "error": "Username or email already exists"}), 400
            
    return jsonify({
        "success": True,
        "user_id": user_id,
        "message": "Registration successful"
    }), 201

# ---------------------- Login Route ----------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles the login page and login requests"""
    if request.method == 'GET':
        # Return the login page
        return send_from_directory(FRONTEND_PATH, 'login.html')
    
    # POST request - Handle login
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"success": False, "error": "Username and password cannot be empty"}), 400
    
    # Verify login
    user_id = User.verify_login(data['username'], data['password'])
    
    if user_id:
        # Record login history
        User.record_login(user_id, request.remote_addr)
        
        # Generate JWT token
        token = AuthManager.generate_token(user_id, data['username'])
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "username": data['username'],
            "token": token,  # Return token to frontend
            "message": "Login successful"
        }), 200
    
    return jsonify({
        "success": False,
        "error": "Invalid username or password"
    }), 401

# ---------------------- Verify Token Route ----------------------
@auth_bp.route('/verify', methods=['POST'])
def verify_token():
    """Verifies if the token is valid"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'valid': False, 'error': 'Token missing'}), 401
    
    try:
        token = auth_header.split(' ')[1]
        result = AuthManager.verify_token(token)
        
        if result['valid']:
            # Get the latest user information
            profile = User.get_profile(result['user_id'])
            return jsonify({
                'valid': True,
                'user': profile
            }), 200
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 401

# ---------------------- Logout Route ----------------------
@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout (mainly for frontend to clear token)"""
    return jsonify({
        "success": True,
        "message": "Logout successful"
    }), 200

@auth_bp.route('/test')
def test():
    """Test route"""
    return jsonify({"message": "Test route is working"})
