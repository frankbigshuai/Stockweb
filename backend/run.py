import os
from backend.app import create_app

# 获取配置名称，默认为development
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # 打印所有路由
    print("\n=== 所有可用路由 ===")
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        if methods:
            print(f"{methods:20s} {rule}")
    print("==================\n")
    
    app.run(debug=True, port=5000)