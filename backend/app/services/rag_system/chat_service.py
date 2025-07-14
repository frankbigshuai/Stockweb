from query_router import route_query
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route('/bot', methods=['POST'])
def ask():
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        logging.info(f"Processing query: {query}")
        response = route_query(query)
        return jsonify({'response': response})
    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)