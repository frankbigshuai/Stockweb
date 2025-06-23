# api_server.py - 完全兼容版本
from query_router import route_query
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

app = Flask(__name__)

# 🎯 为你的具体配置优化CORS
CORS(app, 
     origins=["http://127.0.0.1:5000", "http://localhost:5000", "*"],
     allow_headers=["Content-Type", "Authorization", "Accept"],
     methods=["GET", "POST", "OPTIONS"],
     supports_credentials=True)

logging.basicConfig(level=logging.INFO)

@app.route('/bot', methods=['POST', 'OPTIONS'])
def ask():
    """主要的查询端点"""
    # 处理CORS预检请求
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', 'http://127.0.0.1:5000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    # 记录请求来源
    origin = request.headers.get('Origin', 'Unknown')
    logging.info(f"收到来自 {origin} 的请求")
    
    data = request.json
    if not data:
        return jsonify({'error': 'JSON数据是必需的'}), 400
    
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'Query字段是必需的'}), 400
    
    try:
        logging.info(f"处理查询: {query}")
        response = route_query(query)
        
        # 创建响应
        result = jsonify({
            'response': response,
            'status': 'success',
            'query': query
        })
        
        # 确保CORS头正确设置
        result.headers.add('Access-Control-Allow-Origin', 'http://127.0.0.1:5000')
        
        return result
        
    except Exception as e:
        logging.error(f"查询处理错误: {str(e)}")
        error_response = jsonify({
            'error': str(e),
            'status': 'error'
        })
        error_response.headers.add('Access-Control-Allow-Origin', 'http://127.0.0.1:5000')
        return error_response, 500

@app.route('/health', methods=['GET'])
def health():
    """健康检查端点"""
    response = jsonify({
        'status': 'healthy', 
        'message': 'RAG API服务器正在运行',
        'endpoints': {
            'main': '/bot',
            'health': '/health',
            'test': '/test'
        }
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/test', methods=['GET', 'POST'])
def test():
    """测试端点"""
    response_data = {
        'message': '测试成功!',
        'method': request.method,
        'origin': request.headers.get('Origin', 'No origin'),
        'headers': dict(request.headers),
        'timestamp': str(pd.Timestamp.now()) if 'pd' in globals() else 'N/A'
    }
    
    response = jsonify(response_data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.errorhandler(404)
def not_found(error):
    response = jsonify({'error': '端点未找到', 'available_endpoints': ['/bot', '/health', '/test']})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 404

@app.errorhandler(500)
def internal_error(error):
    response = jsonify({'error': '服务器内部错误', 'message': str(error)})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 500

if __name__ == '__main__':
    print("🚀 启动RAG API服务器...")
    print("📊 RAG系统已就绪!")
    print("🌐 API地址: http://127.0.0.1:5001/bot")
    print("🏥 健康检查: http://127.0.0.1:5001/health")
    print("🧪 测试端点: http://127.0.0.1:5001/test")
    print("🎯 配置用于前端: http://127.0.0.1:5000")
    print("=" * 50)
    
    # 使用127.0.0.1确保地址一致性
    app.run(debug=True, host="127.0.0.1", port=5001, threaded=True)