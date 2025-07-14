# news_handler.py - AlphaVantage news integration for RAG system
import os
import requests
import json
import time
from typing import Dict, List, Optional
import logging
from langchain_openai import ChatOpenAI
from config_utils import load_openai_key

logger = logging.getLogger(__name__)

class SimpleAlphaVantageService:
    """Simplified AlphaVantage service for RAG system"""
    
    def __init__(self):
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = 'https://www.alphavantage.co/query'
        self._cache = {}  # Simple in-memory cache
        
        # Initialize LLM for news summarization
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            openai_api_key=load_openai_key(),
            temperature=0.3,
            max_tokens=800,
            timeout=30
        )
    
    def _make_request(self, params: Dict) -> Dict:
        """Sends an API request"""
        if not self.api_key:
            raise Exception("ALPHA_VANTAGE_API_KEY not configured")
            
        params['apikey'] = self.api_key
        
        logger.info(f"Requesting Alpha Vantage API: {params['function']}")
        
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
            logger.error(f"Request failed: {e}")
            raise Exception(f"Network request failed: {e}")
    
    def _get_cached_data(self, key: str, expires_in: int = 1800) -> Optional[Dict]:
        """Retrieves cached data (30 minutes default for news)"""
        if key in self._cache:
            cached_item = self._cache[key]
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
    
    def get_stock_news(self, symbol: str) -> Dict:
        """Retrieves stock news from Alpha Vantage"""
        cache_key = f"news_{symbol.upper()}"
        
        # Check cache - news cache 30 minutes
        cached_data = self._get_cached_data(cache_key, expires_in=1800)
        if cached_data:
            logger.info(f"Using cached news data: {symbol}")
            return cached_data
        
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': symbol.upper(),
            'limit': 10  # Get 10 news articles
        }
        
        try:
            data = self._make_request(params)
            
            if 'feed' not in data:
                logger.warning(f"News data is empty: {symbol}")
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
            logger.info(f"Successfully fetched and cached news: {symbol}, {len(processed_news['feed'])} articles")
            
            return processed_news
        
        except Exception as e:
            logger.error(f"Failed to get stock news: {e}")
            raise e

class NewsQueryHandler:
    """Handles news queries using AlphaVantage API"""
    
    def __init__(self):
        self.alpha_service = SimpleAlphaVantageService()
        
        # Company symbol mapping
        self.company_symbols = {
            'apple': 'AAPL',
            'microsoft': 'MSFT',
            'google': 'GOOGL',
            'alphabet': 'GOOGL',
            'amazon': 'AMZN',
            'tesla': 'TSLA',
            'meta': 'META',
            'facebook': 'META',
            'nvidia': 'NVDA',
            'netflix': 'NFLX',
            'adobe': 'ADBE',
            'salesforce': 'CRM',
            'oracle': 'ORCL',
            'intel': 'INTC',
            'ibm': 'IBM'
        }
    
    def extract_company_symbol(self, query: str) -> Optional[str]:
        """Extract company symbol from query"""
        query_lower = query.lower()
        
        for company_name, symbol in self.company_symbols.items():
            if company_name in query_lower:
                return symbol
        
        # Check if query contains a stock symbol directly
        words = query_lower.split()
        for word in words:
            if word.upper() in self.company_symbols.values():
                return word.upper()
        
        return None
    
    def handle_news_query(self, query: str) -> str:
        """Handle news queries with real-time data"""
        try:
            logger.info(f"🗞️ Processing news query: {query}")
            
            # Extract company symbol
            symbol = self.extract_company_symbol(query)
            
            if not symbol:
                return self._handle_general_news_query(query)
            
            # Get news from Alpha Vantage
            try:
                news_data = self.alpha_service.get_stock_news(symbol)
                
                if not news_data or not news_data.get('feed'):
                    return f"📰 No recent news found for {symbol}. The company might not have recent news coverage or the symbol might be incorrect."
                
                # Summarize news using LLM
                return self._summarize_company_news(symbol, news_data)
                
            except Exception as api_error:
                logger.warning(f"Alpha Vantage API failed: {api_error}")
                return self._handle_api_fallback(symbol, query)
        
        except Exception as e:
            logger.error(f"News query handling failed: {e}")
            return "Sorry, I encountered an error while fetching news. Please try again later."
    
    def _summarize_company_news(self, symbol: str, news_data: Dict) -> str:
        """Summarize company news using LLM"""
        try:
            articles = news_data.get('feed', [])[:5]  # Top 5 articles
            
            if not articles:
                return f"📰 No recent news articles found for {symbol}."
            
            # Prepare articles for summarization
            articles_text = ""
            for i, article in enumerate(articles, 1):
                title = article.get('title', 'No title')
                summary = article.get('summary', 'No summary')[:200]  # Limit summary length
                source = article.get('source', 'Unknown source')
                sentiment = article.get('overall_sentiment_label', 'Neutral')
                time_published = article.get('time_published', 'Unknown time')
                
                articles_text += f"\n{i}. **{title}**\n   Source: {source} | Published: {time_published} | Sentiment: {sentiment}\n   Summary: {summary}...\n"
            
            # LLM summarization prompt
            prompt = f"""Please provide a concise summary of recent news about {symbol} based on the following articles:

{articles_text}

Please:
1. Highlight the most important developments
2. Mention the overall sentiment if notable
3. Keep the summary informative but concise (2-3 paragraphs max)
4. Focus on the most recent and significant news

Summary:"""
            
            summary_response = self.alpha_service.llm.invoke(prompt)
            
            # Format final response
            return f"""📰 **Recent {symbol} News Summary**:

{summary_response.content}

📊 **Data Source**: Alpha Vantage News API | **Articles Analyzed**: {len(articles)}
📅 **Last Updated**: {time.strftime('%Y-%m-%d %H:%M UTC')}

*Note: This is an AI-generated summary of recent news articles*"""
            
        except Exception as e:
            logger.error(f"News summarization failed: {e}")
            return f"📰 Found {len(articles)} recent articles for {symbol}, but summarization failed. Please try again."
    
    def _handle_general_news_query(self, query: str) -> str:
        """Handle general news queries without specific company"""
        return """📰 **News Query Detected**

Please specify which company you'd like news about. For example:
• "Apple news" or "AAPL news"
• "Tesla recent news"
• "Microsoft latest updates"

I can provide recent news summaries for major publicly traded companies using real-time data from Alpha Vantage.

**Supported companies include**: Apple, Microsoft, Google, Amazon, Tesla, Meta, NVIDIA, Netflix, Adobe, and many more."""
    
    def _handle_api_fallback(self, symbol: str, query: str) -> str:
        """Fallback when API is unavailable"""
        return f"""📰 **News Service Temporarily Unavailable**

I'm unable to access real-time news for {symbol} at the moment.

🔍 **For the latest {symbol} news, please check**:
• Official company investor relations page
• Financial news sites: Bloomberg, Reuters, CNBC, Yahoo Finance
• SEC filings (for publicly traded companies)
• Google News search for "{symbol} news"

⚙️ **Technical Note**: Our real-time news service requires Alpha Vantage API configuration."""

# Global news handler instance
news_handler = NewsQueryHandler()

def handle_news_query(query: str) -> str:
    """Main entry point for news queries"""
    return news_handler.handle_news_query(query)

# Test function
if __name__ == "__main__":
    print("🧪 Testing News Handler...")
    print("=" * 50)
    
    test_queries = [
        "Apple news",
        "TSLA recent news",
        "Microsoft latest updates",
        "general news"
    ]
    
    for query in test_queries:
        print(f"\n📰 Testing: {query}")
        try:
            result = handle_news_query(query)
            print(f"Result: {result[:200]}...")
        except Exception as e:
            print(f"Error: {e}")