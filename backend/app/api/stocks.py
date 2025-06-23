# 🔧 修复1: stocks.py - 确保路由与前端调用匹配
from flask import Blueprint, request, jsonify
from app.models.stock import Stock
import traceback

stocks_bp = Blueprint('stocks', __name__)

@stocks_bp.route('/test')
def test_stocks_api():
    """测试股票API是否工作"""
    return jsonify({
        "success": True,
        "message": "股票API工作正常",
        "timestamp": "2025-05-27"
    }), 200

# 🔧 修复：路由路径要匹配前端调用
@stocks_bp.route('/detail/<symbol>')
def get_stock_detail(symbol):
    """获取股票详细信息 - 匹配前端 /api/v1/stocks/detail/${symbol}"""
    try:
        print(f"获取股票详情: {symbol}")
        
        # 获取基本报价信息
        quote_data = Stock.get_stock_quote(symbol)
        
        if not quote_data:
            return jsonify({
                "success": False,
                "error": f"未找到股票 {symbol} 的数据"
            }), 404
        
        # 获取公司概况信息
        try:
            service = Stock._get_stock_service()
            overview_data = service.get_company_overview(symbol)
        except Exception as e:
            print(f"获取公司概况失败: {e}")
            overview_data = {}
        
        # 整合数据
        detailed_data = {
            **quote_data,
            'company_name': overview_data.get('Name', symbol),
            'description': overview_data.get('Description', '') if overview_data.get('Description') not in [None, 'None', ''] else '',
            'sector': overview_data.get('Sector', 'N/A'),
            'industry': overview_data.get('Industry', 'N/A'),
            'market_cap': overview_data.get('MarketCapitalization', 'N/A'),
            'pe_ratio': overview_data.get('PERatio', 'N/A'),
            'dividend_yield': overview_data.get('DividendYield', 'N/A'),
            'beta': overview_data.get('Beta', 'N/A'),
            '52_week_high': overview_data.get('52WeekHigh', 'N/A'),
            '52_week_low': overview_data.get('52WeekLow', 'N/A'),
            'analysts_target_price': overview_data.get('AnalystTargetPrice', 'N/A'),
            'eps': overview_data.get('EPS', 'N/A'),
            'revenue_ttm': overview_data.get('RevenueTTM', 'N/A'),
            'profit_margin': overview_data.get('ProfitMargin', 'N/A')
        }
        
        return jsonify({
            "success": True,
            "data": detailed_data
        }), 200
        
    except Exception as e:
        print(f"获取股票详情失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取股票详情失败: {str(e)}"
        }), 500

@stocks_bp.route('/top-performers')
def get_top_performers():
    """获取表现最佳股票（支持分页）"""
    try:
        print("=== 股票API被调用 ===")
        
        # 获取参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        category = request.args.get('category', 'top_gainers')
        
        print(f"请求参数: page={page}, limit={limit}, category={category}")
        
        # 验证参数
        if page < 1:
            page = 1
        if limit > 50:
            limit = 50
            
        valid_categories = ['top_gainers', 'top_losers', 'most_actively_traded']
        if category not in valid_categories:
            return jsonify({
                "success": False,
                "error": f"无效的分类，支持的分类: {', '.join(valid_categories)}"
            }), 400
        
        print("开始获取股票数据...")
        
        # 先尝试获取真实数据
        try:
            data = Stock.get_top_performers_paginated(category=category, page=page, limit=limit)
            print(f"股票数据获取结果: {data is not None}")
            
            if data:
                print(f"返回数据包含 {len(data.get('stocks', []))} 只股票")
                return jsonify({
                    "success": True,
                    "data": data
                }), 200
            else:
                print("股票数据为空，可能是API限制")
                # 返回模拟数据作为备选
                mock_data = generate_mock_data(category, page, limit)
                return jsonify({
                    "success": True,
                    "data": mock_data,
                    "note": "使用模拟数据（API可能受限）"
                }), 200
                
        except Exception as api_error:
            print(f"API调用失败: {api_error}")
            print(f"完整错误: {traceback.format_exc()}")
            
            # API失败时返回模拟数据
            mock_data = generate_mock_data(category, page, limit)
            return jsonify({
                "success": True,
                "data": mock_data,
                "note": f"使用模拟数据（API错误: {str(api_error)}）"
            }), 200
        
    except ValueError as e:
        print(f"参数错误: {e}")
        return jsonify({
            "success": False,
            "error": "参数格式错误"
        }), 400
    except Exception as e:
        print(f"未知错误: {e}")
        print(f"完整错误: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": f"服务器内部错误: {str(e)}"
        }), 500

def generate_mock_data(category, page, limit):
    """生成模拟数据"""
    print(f"生成模拟数据: category={category}, page={page}, limit={limit}")
    
    # 模拟股票数据
    mock_stocks = []
    stock_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'UBER', 'ZOOM']
    
    start_idx = (page - 1) * limit
    for i in range(limit):
        symbol_idx = (start_idx + i) % len(stock_symbols)
        symbol = stock_symbols[symbol_idx]
        
        if category == 'top_gainers':
            change_percent = 5 + (i * 0.5)  # 递减的涨幅
            price = 100 + (i * 5)
        elif category == 'top_losers':
            change_percent = -(2 + (i * 0.3))  # 递增的跌幅
            price = 80 + (i * 3)
        else:  # most_actively_traded
            change_percent = (i % 2 - 0.5) * 4  # 交替正负
            price = 90 + (i * 4)
            
        change_amount = price * (change_percent / 100)
        
        mock_stocks.append({
            'ticker': f"{symbol}{i+1}" if i > 0 else symbol,
            'price': round(price, 2),
            'change_amount': round(change_amount, 2),
            'change_percent': round(change_percent, 2),
            'volume': 1000000 + (i * 100000)
        })
    
    # 模拟分页信息
    total_items = 100  # 假设总共100只股票
    total_pages = (total_items + limit - 1) // limit
    
    pagination = {
        'current_page': page,
        'total_items': total_items,
        'items_per_page': limit,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1,
        'start_index': start_idx + 1,
        'end_index': min(start_idx + limit, total_items)
    }
    
    return {
        'stocks': mock_stocks,
        'pagination': pagination,
        'category': category,
        'last_updated': '2025-05-27 16:00:00 US/Eastern'
    }

@stocks_bp.route('/quote/<symbol>')
def get_stock_quote(symbol):
    """获取股票报价"""
    try:
        print(f"获取股票报价: {symbol}")
        data = Stock.get_stock_quote(symbol)
        
        if data:
            return jsonify({
                "success": True,
                "data": data
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": f"未找到股票 {symbol} 的数据"
            }), 404
            
    except Exception as e:
        print(f"获取股票报价失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@stocks_bp.route('/search')
def search_stocks():
    """搜索股票"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({
                "success": True,
                "data": []
            }), 200
        
        results = Stock.search_stocks(query)
        
        return jsonify({
            "success": True,
            "data": results
        }), 200
        
    except Exception as e:
        print(f"搜索股票失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@stocks_bp.route('/news/<symbol>')
def get_stock_news(symbol):
    """获取股票相关新闻"""
    try:
        print(f"获取股票新闻: {symbol}")
        
        news_data = Stock.get_stock_news(symbol)
        
        if news_data and 'feed' in news_data:
            return jsonify({
                "success": True,
                "data": news_data
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": f"未找到 {symbol} 的新闻数据"
            }), 404
            
    except Exception as e:
        print(f"获取股票新闻失败: {e}")
        return jsonify({
            "success": False,
            "error": f"获取新闻失败: {str(e)}"
        }), 500