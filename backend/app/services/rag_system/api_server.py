# api_server.py - Railway部署版本
from query_router import route_query
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os

app = Flask(__name__)

# 🔧 更新CORS配置以支持Railway部署
CORS(app, 
     origins=[
         "https://stockweb-production.up.railway.app",  # 你的stockweb域名
         "https://stockweb-ai-production.up.railway.app",  # 你的stockai域名（自己访问自己）
         "http://127.0.0.1:5000", 
         "http://localhost:5000",
         "*"  # 在开发阶段可以用*，生产环境建议移除
     ],
     allow_headers=["Content-Type", "Authorization", "Accept"],
     methods=["GET", "POST", "OPTIONS"],
     supports_credentials=True)

logging.basicConfig(level=logging.INFO)

@app.route('/bot', methods=['POST', 'OPTIONS'])
def ask():
    """主要的查询端点"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
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
        
        result = jsonify({
            'response': response,
            'status': 'success',
            'query': query
        })
        
        result.headers.add('Access-Control-Allow-Origin', '*')
        return result
        
    except Exception as e:
        logging.error(f"查询处理错误: {str(e)}")
        error_response = jsonify({
            'error': str(e),
            'status': 'error'
        })
        error_response.headers.add('Access-Control-Allow-Origin', '*')
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
        'timestamp': 'Railway部署版本'
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
    print("🌐 API地址: /bot")
    print("🏥 健康检查: /health")
    print("🧪 测试端点: /test")
    print("=" * 50)
    
    # Railway部署配置
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host="0.0.0.0", port=port, threaded=True)
