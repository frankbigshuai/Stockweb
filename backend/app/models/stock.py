from typing import Optional, Dict, List
from app.services.stock_service import AlphaVantageService

class Stock:
    """股票数据模型"""
    
    @staticmethod
    def _get_stock_service() -> AlphaVantageService:
        """获取股票服务实例"""
        return AlphaVantageService()
    
    @staticmethod
    def get_top_performers_paginated(category: str = 'top_gainers', page: int = 1, limit: int = 20) -> Optional[Dict]:
        """获取分页的表现最佳股票"""
        try:
            service = Stock._get_stock_service()
            return service.get_paginated_stocks(category, page, limit)
            
        except Exception as e:
            print(f"获取分页股票数据失败: {e}")
            return None
    
    @staticmethod
    def get_stock_quote(symbol: str) -> Optional[Dict]:
        """获取股票报价"""
        try:
            service = Stock._get_stock_service()
            return service.get_quote(symbol)
            
        except Exception as e:
            print(f"获取股票报价失败: {e}")
            return None
    
    @staticmethod
    def search_stocks(query: str) -> List[Dict]:
        """搜索股票"""
        try:
            service = Stock._get_stock_service()
            return service.search_stocks(query)
            
        except Exception as e:
            print(f"搜索股票失败: {e}")
            return []
        
    @staticmethod
    def get_stock_news(symbol: str) -> Optional[Dict]:
        """获取股票新闻"""
        try:
            service = Stock._get_stock_service()
            return service.get_stock_news(symbol)
        except Exception as e:
            print(f"获取股票新闻失败: {e}")
            return None
        