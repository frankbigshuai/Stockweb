import requests
import json
import time
from typing import Dict, List, Optional
from flask import current_app

class AlphaVantageService:
    def __init__(self):
        self.api_key = current_app.config.get('ALPHA_VANTAGE_API_KEY')
        self.base_url = 'https://www.alphavantage.co/query'
        self._cache = {}  # 简单内存缓存
        
    def _make_request(self, params: Dict) -> Dict:
        """发送API请求"""
        params['apikey'] = self.api_key
        
        print(f"请求Alpha Vantage API: {params}")
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # 检查API错误
            if 'Error Message' in data:
                raise Exception(f"API错误: {data['Error Message']}")
            elif 'Information' in data:
                raise Exception(f"API限制: {data['Information']}")
                
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            raise Exception(f"网络请求失败: {e}")
        
    
    
    def _get_cached_data(self, key: str, expires_in: int = 600) -> Optional[Dict]:
        """获取缓存数据"""
        if key in self._cache:
            cached_item = self._cache[key]
            # 使用传入的过期时间
            if time.time() - cached_item['timestamp'] < expires_in:
                return cached_item['data']
            else:
                del self._cache[key]
        return None
    
    def _set_cache_data(self, key: str, data: Dict):
        """设置缓存数据"""
        self._cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def get_top_gainers_losers_full(self) -> Dict:
        """获取完整的涨跌幅排行榜数据（带缓存）"""
        cache_key = "top_gainers_losers_full"
        
        # 检查缓存
        cached_data = self._get_cached_data(cache_key, expires_in=600)
        if cached_data:
            print("使用缓存的排行榜数据")
            return cached_data
        
        # 调用API获取新数据
        params = {
            'function': 'TOP_GAINERS_LOSERS'
        }
        
        try:
            data = self._make_request(params)
            
            if 'top_gainers' not in data:
                print(f"API返回数据格式异常: {list(data.keys())}")
                raise Exception("API返回数据格式不正确")
            
            # 处理和标准化数据
            processed_data = {
                'last_updated': data.get('last_updated', ''),
                'top_gainers': self._process_stock_list(data.get('top_gainers', [])),
                'top_losers': self._process_stock_list(data.get('top_losers', [])),
                'most_actively_traded': self._process_stock_list(data.get('most_actively_traded', []))
            }
            
            # 缓存数据
            self._set_cache_data(cache_key, processed_data)
            
            print(f"成功获取排行榜数据: 涨幅榜{len(processed_data['top_gainers'])}只, 跌幅榜{len(processed_data['top_losers'])}只, 成交量榜{len(processed_data['most_actively_traded'])}只")
            
            return processed_data
            
        except Exception as e:
            print(f"获取排行榜数据失败: {e}")
            raise e
    
    def _process_stock_list(self, stock_list: List[Dict]) -> List[Dict]:
        """处理股票列表数据，标准化格式"""
        processed_stocks = []
        
        for stock in stock_list:
            try:
                # Alpha Vantage API返回的字段名可能不同，需要适配
                processed_stock = {
                    'ticker': stock.get('ticker', ''),
                    'price': self._safe_float(stock.get('price', '0')),
                    'change_amount': self._safe_float(stock.get('change_amount', '0')),
                    'change_percent': stock.get('change_percentage', '0%').replace('%', ''),
                    'volume': self._safe_int(stock.get('volume', '0'))
                }
                
                # 确保数据完整
                if processed_stock['ticker']:
                    processed_stocks.append(processed_stock)
                    
            except Exception as e:
                print(f"处理股票数据失败: {stock}, 错误: {e}")
                continue
        
        return processed_stocks
    
    def _safe_float(self, value) -> float:
        """安全转换为浮点数"""
        try:
            if isinstance(value, str):
                # 移除可能的货币符号和逗号
                value = value.replace('$', '').replace(',', '')
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _safe_int(self, value) -> int:
        """安全转换为整数"""
        try:
            if isinstance(value, str):
                value = value.replace(',', '')
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    def get_paginated_stocks(self, category: str, page: int = 1, limit: int = 20) -> Dict:
        """获取分页的股票数据"""
        try:
            # 获取完整数据
            full_data = self.get_top_gainers_losers_full()
            
            # 根据分类获取对应的股票列表
            if category not in full_data:
                raise Exception(f"不支持的分类: {category}")
            
            stock_list = full_data[category]
            total_stocks = len(stock_list)
            
            # 计算分页
            start_idx = (page - 1) * limit
            end_idx = min(start_idx + limit, total_stocks)
            paginated_stocks = stock_list[start_idx:end_idx]
            
            # 构建分页信息
            pagination_info = {
                'current_page': page,
                'total_items': total_stocks,
                'items_per_page': limit,
                'total_pages': (total_stocks + limit - 1) // limit,
                'has_next': end_idx < total_stocks,
                'has_prev': page > 1,
                'start_index': start_idx + 1,
                'end_index': end_idx
            }
            
            return {
                'stocks': paginated_stocks,
                'pagination': pagination_info,
                'category': category,
                'last_updated': full_data.get('last_updated', '')
            }
            
        except Exception as e:
            print(f"获取分页股票数据失败: {e}")
            raise e
    
    def get_quote(self, symbol: str) -> Dict:
        """获取股票实时报价"""
        cache_key = f"quote_{symbol.upper()}"
        
        # 检查缓存
        cached_data = self._get_cached_data(cache_key, expires_in=600)
        if cached_data:
            return cached_data
        
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol.upper()
        }
        
        data = self._make_request(params)
        
        if 'Global Quote' not in data or not data['Global Quote']:
            raise Exception(f"No data found for symbol: {symbol}")
        
        quote_data = data['Global Quote']
        
        # 格式化返回数据
        result = {
            'symbol': quote_data.get('01. symbol', symbol.upper()),
            'price': self._safe_float(quote_data.get('05. price', 0)),
            'change': self._safe_float(quote_data.get('09. change', 0)),
            'change_percent': quote_data.get('10. change percent', '0%').replace('%', ''),
            'volume': self._safe_int(quote_data.get('06. volume', 0)),
            'latest_trading_day': quote_data.get('07. latest trading day', ''),
            'previous_close': self._safe_float(quote_data.get('08. previous close', 0)),
            'open': self._safe_float(quote_data.get('02. open', 0)),
            'high': self._safe_float(quote_data.get('03. high', 0)),
            'low': self._safe_float(quote_data.get('04. low', 0))
        }
        
        # 缓存结果
        self._set_cache_data(cache_key, result)
        return result
    
    def search_stocks(self, query: str) -> List[Dict]:
        """搜索股票"""
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': query
        }
        
        try:
            data = self._make_request(params)
            
            if 'bestMatches' not in data:
                return []
            
            results = []
            for match in data['bestMatches'][:10]:  # 限制10个结果
                results.append({
                    'symbol': match.get('1. symbol', ''),
                    'name': match.get('2. name', ''),
                    'type': match.get('3. type', ''),
                    'region': match.get('4. region', ''),
                    'currency': match.get('8. currency', '')
                })
            
            return results
            
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
        
    def get_company_overview(self, symbol: str) -> Dict:
        """获取公司概况"""
        cache_key = f"overview_{symbol.upper()}"
        
        # 检查缓存
        cached_data = self._get_cached_data(cache_key, expires_in=86400)
        if cached_data:
            return cached_data
        
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol.upper()
        }
        
        try:
            data = self._make_request(params)
            
            if not data or 'Symbol' not in data:
                print(f"公司概况数据为空: {symbol}")
                return {}
            
            # 缓存结果（1小时）
            self._cache[cache_key] = {
                'data': data,
                'timestamp': time.time()
            }
            
            return data
            
        except Exception as e:
            print(f"获取公司概况失败: {e}")
            return {}   
        
    def get_stock_news(self, symbol: str) -> Dict:
        """获取股票新闻"""
        cache_key = f"news_{symbol.upper()}"
        
        # 检查缓存 - 新闻缓存30分钟
        cached_data = self._get_cached_data(cache_key, expires_in=1800)
        if cached_data:
            print(f"使用缓存的新闻数据: {symbol}")
            return cached_data
        
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': symbol.upper(),
            'limit': 20  # 获取20条新闻
        }
        
        try:
            data = self._make_request(params)
            
            if 'feed' not in data:
                print(f"新闻数据为空: {symbol}")
                return {}
            
            # 处理新闻数据
            processed_news = {
                'feed': [],
                'items': data.get('items', '0'),
                'sentiment_score_definition': data.get('sentiment_score_definition', '')
            }
            
            # 处理每条新闻
            for article in data.get('feed', []):
                processed_article = {
                    'title': article.get('title', ''),
                    'summary': article.get('summary', ''),
                    'url': article.get('url', ''),
                    'time_published': article.get('time_published', ''),
                    'source': article.get('source', ''),
                    'source_domain': article.get('source_domain', ''),
                    'overall_sentiment_score': article.get('overall_sentiment_score', 0),
                    'overall_sentiment_label': article.get('overall_sentiment_label', 'Neutral'),
                    'ticker_sentiment': article.get('ticker_sentiment', [])
                }
                processed_news['feed'].append(processed_article)
            
            # 缓存结果
            self._set_cache_data(cache_key, processed_news)
            print(f"成功获取并缓存新闻: {symbol}, 共{len(processed_news['feed'])}条")
            
            return processed_news
            
        except Exception as e:
            print(f"获取股票新闻失败: {e}")
            raise e
            
            