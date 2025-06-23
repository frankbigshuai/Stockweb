from query_router import route_query  # 导入查询路由模块
from flask import Flask, request, jsonify  # Flask框架相关
from flask_cors import CORS  # 跨域支持
import logging  # 添加日志

app = Flask(__name__)  # 创建Flask应用实例
CORS(app)  # 启用跨域

# 配置日志
logging.basicConfig(level=logging.INFO)

@app.route('/bot', methods=['POST'])  # 定义POST接口
def ask():
    data = request.json  # 获取JSON格式请求数据
    query = data.get('query', '')  # 提取查询内容
    
    if not query:  # 空查询检查
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        logging.info(f"Processing query: {query}")  # 记录查询
        response = route_query(query)  # 调用路由处理查询
        return jsonify({'response': response})  # 返回成功响应
    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")  # 记录错误
        return jsonify({'error': str(e)})  # 异常处理

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)  # 启动服务