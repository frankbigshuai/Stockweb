import requests
import json
import time
from typing import Dict, List, Optional
from flask import current_app

class AlphaVantageService:
    def __init__(self):
        self.api_key = current_app.config.get('ALPHA_VANTAGE_API_KEY')
        self.base_url = 'https://www.alphavantage.co/query'
        self._cache = {}  # Simple in-memory cache
        
    def _make_request(self, params: Dict) -> Dict:
        """Sends an API request"""
        params['apikey'] = self.api_key
        
        print(f"Requesting Alpha Vantage API: {params}")
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                raise Exception(f"API Error: {data['Error Message']}")
            elif 'Information' in data:
                raise Exception(f"API Limit: {data['Information']}")
                
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise Exception(f"Network request failed: {e}")
        
    
    
    def _get_cached_data(self, key: str, expires_in: int = 600) -> Optional[Dict]:
        """Retrieves cached data"""
        if key in self._cache:
            cached_item = self._cache[key]
            # Use the provided expiration time
            if time.time() - cached_item['timestamp'] < expires_in:
                return cached_item['data']
            else:
                del self._cache[key]
        return None
    
    def _set_cache_data(self, key: str, data: Dict):
        """Sets cached data"""
        self._cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def get_top_gainers_losers_full(self) -> Dict:
        """Retrieves full top gainers and losers data (with caching)"""
        cache_key = "top_gainers_losers_full"
        
        # Check cache
        cached_data = self._get_cached_data(cache_key, expires_in=600)
        if cached_data:
            print("Using cached top gainers/losers data")
            return cached_data
        
        # Call API for new data
        params = {
            'function': 'TOP_GAINERS_LOSERS'
        }
        
        try:
            data = self._make_request(params)
            
            if 'top_gainers' not in data:
                print(f"API returned data in unexpected format: {list(data.keys())}")
                raise Exception("API returned data in incorrect format")
            
            # Process and standardize data
            processed_data = {
                'last_updated': data.get('last_updated', ''),
                'top_gainers': self._process_stock_list(data.get('top_gainers', [])),
                'top_losers': self._process_stock_list(data.get('top_losers', [])),
                'most_actively_traded': self._process_stock_list(data.get('most_actively_traded', []))
            }
            
            # Cache data
            self._set_cache_data(cache_key, processed_data)
            
            print(f"Successfully fetched top gainers/losers data: {len(processed_data['top_gainers'])} gainers, {len(processed_data['top_losers'])} losers, {len(processed_data['most_actively_traded'])} actively traded")
            
            return processed_data
            
        except Exception as e:
            print(f"Failed to fetch top gainers/losers data: {e}")
            raise e
    
    def _process_stock_list(self, stock_list: List[Dict]) -> List[Dict]:
        """Processes stock list data, standardizing the format"""
        processed_stocks = []
        
        for stock in stock_list:
            try:
                # Alpha Vantage API returns different field names, needs adaptation
                processed_stock = {
                    'ticker': stock.get('ticker', ''),
                    'price': self._safe_float(stock.get('price', '0')),
                    'change_amount': self._safe_float(stock.get('change_amount', '0')),
                    'change_percent': stock.get('change_percentage', '0%').replace('%', ''),
                    'volume': self._safe_int(stock.get('volume', '0'))
                }
                
                # Ensure data is complete
                if processed_stock['ticker']:
                    processed_stocks.append(processed_stock)
                    
            except Exception as e:
                print(f"Failed to process stock data: {stock}, Error: {e}")
                continue
        
        return processed_stocks
    
    def _safe_float(self, value) -> float:
        """Safely converts to float"""
        try:
            if isinstance(value, str):
                # Remove potential currency symbols and commas
                value = value.replace('$', '').replace(',', '')
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _safe_int(self, value) -> int:
        """Safely converts to integer"""
        try:
            if isinstance(value, str):
                value = value.replace(',', '')
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    def get_paginated_stocks(self, category: str, page: int = 1, limit: int = 20) -> Dict:
        """Retrieves paginated stock data"""
        try:
            # Get full data
            full_data = self.get_top_gainers_losers_full()
            
            # Get the corresponding stock list based on category
            if category not in full_data:
                raise Exception(f"Unsupported category: {category}")
            
            stock_list = full_data[category]
            total_stocks = len(stock_list)
            
            # Calculate pagination
            start_idx = (page - 1) * limit
            end_idx = min(start_idx + limit, total_stocks)
            paginated_stocks = stock_list[start_idx:end_idx]
            
            # Build pagination information
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
            print(f"Failed to retrieve paginated stock data: {e}")
            raise e
    
    def get_quote(self, symbol: str) -> Dict:
        """Retrieves real-time stock quote"""
        cache_key = f"quote_{symbol.upper()}"
        
        # Check cache
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
        
        # Format returned data
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
        
        # Cache the result
        self._set_cache_data(cache_key, result)
        return result
    
    def search_stocks(self, query: str) -> List[Dict]:
        """Searches for stocks"""
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': query
        }
        
        try:
            data = self._make_request(params)
            
            if 'bestMatches' not in data:
                return []
            
            results = []
            for match in data['bestMatches'][:10]:  # Limit to 10 results
                results.append({
                    'symbol': match.get('1. symbol', ''),
                    'name': match.get('2. name', ''),
                    'type': match.get('3. type', ''),
                    'region': match.get('4. region', ''),
                    'currency': match.get('8. currency', '')
                })
            
            return results
            
        except Exception as e:
            print(f"Search failed: {e}")
            return []
        
    def get_company_overview(self, symbol: str) -> Dict:
        """Retrieves company overview"""
        cache_key = f"overview_{symbol.upper()}"
        
        # Check cache
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
                print(f"Company overview data is empty: {symbol}")
                return {}
            
            # Cache the result (1 hour)
            self._cache[cache_key] = {
                'data': data,
                'timestamp': time.time()
            }
            
            return data
            
        except Exception as e:
            print(f"Failed to get company overview: {e}")
            return {}   
        
    def get_stock_news(self, symbol: str) -> Dict:
        """Retrieves stock news"""
        cache_key = f"news_{symbol.upper()}"
        
        # Check cache - news cache 30 minutes
        cached_data = self._get_cached_data(cache_key, expires_in=1800)
        if cached_data:
            print(f"Using cached news data: {symbol}")
            return cached_data
        
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': symbol.upper(),
            'limit': 20  # Get 20 news articles
        }
        
        try:
            data = self._make_request(params)
            
            if 'feed' not in data:
                print(f"News data is empty: {symbol}")
                return {}
            
            # Process news data
            processed_news = {
                'feed': [],
                'items': data.get('items', '0'),
                'sentiment_score_definition': data.get('sentiment_score_definition', '')
            }
            
            # Process each article
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
            
            # Cache the result
            self._set_cache_data(cache_key, processed_news)
            print(f"Successfully fetched and cached news: {symbol}, {len(processed_news['feed'])} articles")
            
            return processed_news
            
        except Exception as e:
            print(f"Failed to get stock news: {e}")
            raise e