# api_server.py - Railway Deployment Version
from query_router import route_query
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os

app = Flask(__name__)

# 🔧 Update CORS configuration to support Railway deployment
CORS(app, 
     origins=[
         "https://stockweb-production.up.railway.app",  # Your stockweb domain
         "https://stockweb-ai-production.up.railway.app",  # Your stockai domain (self-access)
         "http://127.0.0.1:5000", 
         "http://localhost:5000",
         "*"  # Use * during development, recommended to remove in production
     ],
     allow_headers=["Content-Type", "Authorization", "Accept"],
     methods=["GET", "POST", "OPTIONS"],
     supports_credentials=True)

logging.basicConfig(level=logging.INFO)

@app.route('/bot', methods=['POST', 'OPTIONS'])
def ask():
    """Main query endpoint"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    origin = request.headers.get('Origin', 'Unknown')
    logging.info(f"Received request from {origin}")
    
    data = request.json
    if not data:
        return jsonify({'error': 'JSON data is required'}), 400
    
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'Query field is required'}), 400
    
    try:
        logging.info(f"Processing query: {query}")
        response = route_query(query)
        
        result = jsonify({
            'response': response,
            'status': 'success',
            'query': query
        })
        
        result.headers.add('Access-Control-Allow-Origin', '*')
        return result
        
    except Exception as e:
        logging.error(f"Query processing error: {str(e)}")
        error_response = jsonify({
            'error': str(e),
            'status': 'error'
        })
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    response = jsonify({
        'status': 'healthy', 
        'message': 'RAG API server is running',
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
    """Test endpoint"""
    response_data = {
        'message': 'Test successful!',
        'method': request.method,
        'origin': request.headers.get('Origin', 'No origin'),
        'timestamp': 'Railway Deployment Version'
    }
    
    response = jsonify(response_data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.errorhandler(404)
def not_found(error):
    response = jsonify({'error': 'Endpoint not found', 'available_endpoints': ['/bot', '/health', '/test']})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 404

@app.errorhandler(500)
def internal_error(error):
    response = jsonify({'error': 'Internal server error', 'message': str(error)})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 500

if __name__ == '__main__':
    print("🚀 Starting RAG API server...")
    print("📊 RAG system ready!")
    print("🌐 API address: /bot")
    print("🏥 Health check: /health")
    print("🧪 Test endpoint: /test")
    print("=" * 50)
    
    # Railway deployment configuration
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host="0.0.0.0", port=port, threaded=True)