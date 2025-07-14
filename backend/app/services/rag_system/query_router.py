# query_router.py - Enhanced version with AlphaVantage news integration
from langchain_openai import ChatOpenAI
from company_info_query_engine import run_general_query
from pandas_data_analyzer import run_analytical_query
from config_utils import load_openai_key
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import news handler
try:
    from news_handler import handle_news_query
    NEWS_HANDLER_AVAILABLE = True
    logger.info("✅ News handler imported successfully")
except ImportError as e:
    NEWS_HANDLER_AVAILABLE = False
    logger.warning(f"⚠️ News handler not available: {e}")

# Lightweight classification model
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    openai_api_key=load_openai_key(),
    temperature=0,
    max_tokens=50,
    timeout=15
)

def classify_question(query):
    """Enhanced question classification with news handling"""
    query_lower = query.lower()
    
    # Clear analytical keywords
    analytical_keywords = [
        'price', 'stock price', 'share price', 'cost',
        'earnings', 'revenue', 'profit', 'sales',
        'cash flow', 'financial data',
        'average', 'mean', 'calculate', 'compute',
        'data', 'statistics', 'numbers', 'figure',
        'compare', 'comparison', 'analysis',
        'chart', 'graph', 'trend', 'performance',
        'how much', 'how many', 'what is the price',
        'show me data', 'latest data', 'current data'
    ]
    
    # Clear general keywords
    general_keywords = [
        'what does', 'tell me about', 'who is', 'describe',
        'business model', 'business', 'company',
        'products', 'services', 'industry', 'sector',
        'competitor', 'competitors', 'competition',
        'overview', 'introduction', 'about',
        'founded', 'headquarters', 'ceo', 'history',
        'what is', 'explain', 'how does', 'why does'
    ]
    
    # 🆕 News keywords - special handling
    news_keywords = [
        'news', 'latest news', 'recent news', 'current news',
        'updates', 'announcements', 'recent developments',
        'breaking news', 'headlines', 'press release',
        'today news', 'this week', 'recent articles'
    ]
    
    # Check for news queries first
    news_score = sum(1 for keyword in news_keywords if keyword in query_lower)
    if news_score > 0:
        logger.info("📰 Classification: news (special handling)")
        return "news"
    
    # Calculate matching scores for other categories
    analytical_score = sum(1 for keyword in analytical_keywords if keyword in query_lower)
    general_score = sum(1 for keyword in general_keywords if keyword in query_lower)
    
    logger.info(f"Keyword matching - Analytical: {analytical_score}, General: {general_score}")
    
    # Special rules: queries with specific numeric words lean toward analytical
    if any(word in query_lower for word in ['$', 'dollar', 'million', 'billion', '%', 'percent']):
        analytical_score += 2
    
    # Decision logic
    if analytical_score > general_score:
        logger.info("📊 Classification: analytical (by keywords)")
        return "analytical"
    elif general_score > analytical_score:
        logger.info("📋 Classification: general (by keywords)")
        return "general"
    
    # If scores are equal, use LLM
    try:
        prompt = f"""Classify this question as "analytical", "general", or "news":

Question: "{query}"

Rules:
- analytical: asks for specific data, prices, financial information, statistical analysis
- general: asks for company introduction, business model, products/services, industry information  
- news: asks for recent news, updates, current events, latest developments

Answer with one word only:"""
        
        response = llm.invoke(prompt)
        classification = response.content.strip().lower()
        
        if "analytical" in classification:
            logger.info("📊 Classification: analytical (by LLM)")
            return "analytical"
        elif "news" in classification:
            logger.info("📰 Classification: news (by LLM)")
            return "news"
        else:
            logger.info("📋 Classification: general (by LLM)")
            return "general"
            
    except Exception as e:
        logger.warning(f"❌ LLM classification failed: {e}, defaulting to general")
        return "general"

def handle_news_query_with_fallback(query):
    """Handle news queries with AlphaVantage API or fallback"""
    try:
        if NEWS_HANDLER_AVAILABLE:
            # Use real-time news API
            logger.info("📰 Using AlphaVantage news API")
            return handle_news_query(query)
        else:
            # Fallback to disclaimer
            logger.info("📰 Using news fallback (API not available)")
            return handle_news_fallback(query)
    except Exception as e:
        logger.error(f"❌ News handling failed: {e}")
        return handle_news_fallback(query)

def handle_news_fallback(query):
    """Fallback news handler when API is not available"""
    # Extract company name if possible
    company_keywords = {
        'apple': 'Apple Inc.',
        'microsoft': 'Microsoft',
        'google': 'Google/Alphabet',
        'amazon': 'Amazon',
        'tesla': 'Tesla',
        'meta': 'Meta',
        'nvidia': 'NVIDIA'
    }
    
    company_mentioned = None
    for keyword, company_name in company_keywords.items():
        if keyword in query.lower():
            company_mentioned = company_name
            break
    
    if company_mentioned:
        return f"""⚠️ **Real-time news currently unavailable**

I'm unable to access current news for {company_mentioned} at the moment due to API configuration.

📰 **For the latest {company_mentioned} news, please check:**
• Official {company_mentioned} website and investor relations
• Financial news: Bloomberg, Reuters, CNBC, Yahoo Finance
• SEC filings (for publicly traded companies)
• Company's official social media accounts

💡 **Tip**: Search for "{company_mentioned} news" on Google News for the most recent updates.

🔧 **Technical Note**: To enable real-time news, configure ALPHA_VANTAGE_API_KEY in environment variables."""
    else:
        return """📰 **News Query Detected**

Please specify which company you'd like news about. For example:
• "Apple news"
• "Tesla recent news"
• "Microsoft latest updates"

🔧 **Note**: Real-time news requires Alpha Vantage API configuration."""

def route_query(query):
    """Enhanced query routing with news handling"""
    start_time = time.time()
    
    try:
        # Input validation
        if not query or not query.strip():
            return "Please provide a valid question."
        
        query = query.strip()
        logger.info(f"🎯 Processing query: {query}")
        
        # Classify question
        question_type = classify_question(query)
        logger.info(f"🔀 Routing to: {question_type}")
        
        # Route to appropriate handler
        if question_type == "analytical":
            try:
                logger.info("📊 Calling analytical engine...")
                response = run_analytical_query(query)
                
                if response and len(response.strip()) > 10:
                    return response
                else:
                    logger.warning("⚠️ Analytical response empty, trying general query")
                    return run_general_query(query)
                
            except Exception as analytical_error:
                logger.error(f"❌ Analytical query failed: {analytical_error}")
                return run_general_query(query)
        
        elif question_type == "news":
            return handle_news_query_with_fallback(query)
        
        else:  # general
            try:
                logger.info("📋 Calling general query engine...")
                return run_general_query(query)
            except Exception as general_error:
                logger.error(f"❌ General query failed: {general_error}")
                return "Sorry, an error occurred while processing your question. Please try rephrasing your question."
            
    except Exception as e:
        logger.error(f"❌ Routing error: {str(e)}")
        execution_time = time.time() - start_time
        return f"Sorry, an error occurred while processing your question (execution time: {execution_time:.1f}s). Please try again later."

# Test function
if __name__ == "__main__":
    print("🧪 Testing Enhanced Query Router...")
    print("=" * 50)
    
    # Test news handling
    test_queries = [
        "Apple news",
        "Latest Tesla news", 
        "What is Apple's stock price?",
        "Tell me about Microsoft",
        "Recent Microsoft developments"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")
        classification = classify_question(query)
        print(f"📋 Classification: {classification}")
        
        result = route_query(query)
        print(f"📝 Response: {result[:200]}...")
        
    print(f"\n{'='*50}")
    print("🎉 Testing completed!")