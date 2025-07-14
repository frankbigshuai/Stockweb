from langchain_openai import ChatOpenAI
from company_info_query_engine import run_general_query
from pandas_data_analyzer import run_analytical_query
from config_utils import load_openai_key
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lightweight classification model
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    openai_api_key=load_openai_key(),
    temperature=0,
    max_tokens=50,
    timeout=15
)

def classify_question(query):
    """Intelligently classifies the question"""
    query_lower = query.lower()
    
    # Explicit analytical keywords
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
    
    # Explicit general keywords
    general_keywords = [
        'what does', 'tell me about', 'who is', 'describe',
        'business model', 'business', 'company',
        'products', 'services', 'industry', 'sector',
        'competitor', 'competitors', 'competition',
        'overview', 'introduction', 'about',
        'founded', 'headquarters', 'ceo', 'history',
        'what is', 'explain', 'how does', 'why does'
    ]
    
    # Calculate match scores
    analytical_score = sum(1 for keyword in analytical_keywords if keyword in query_lower)
    general_score = sum(1 for keyword in general_keywords if keyword in query_lower)
    
    logger.info(f"Keyword matching - Analytical: {analytical_score}, General: {general_score}")
    
    # Special rule: words related to specific numbers bias towards analytical
    if any(word in query_lower for word in ['$', 'dollar', 'million', 'billion', '%', 'percent']):
        analytical_score += 2
    
    # Decision logic
    if analytical_score > general_score:
        logger.info("📊 Classification: analytical (via keywords)")
        return "analytical"
    elif general_score > analytical_score:
        logger.info("📋 Classification: general (via keywords)")
        return "general"
    
    # If scores are equal, use LLM
    try:
        prompt = f"""Classify this question as "analytical" or "general":

Question: "{query}"

Rules:
- analytical: asks for specific data, prices, financial information, statistical analysis
- general: asks for company introductions, business models, products/services, industry information

Answer with only one word:"""
        
        response = llm.invoke(prompt)
        classification = response.content.strip().lower()
        
        if "analytical" in classification:
            logger.info("📊 Classification: analytical (via LLM)")
            return "analytical"
        else:
            logger.info("📋 Classification: general (via LLM)")
            return "general"
            
    except Exception as e:
        logger.warning(f"❌ LLM classification failed: {e}, defaulting to general")
        return "general"

def route_query(query):
    """Main query routing function"""
    start_time = time.time()
    
    try:
        # Input validation
        if not query or not query.strip():
            return "Please provide a valid question."
        
        query = query.strip()
        logger.info(f"🎯 Processing query: {query}")
        
        # Classify the question
        question_type = classify_question(query)
        logger.info(f"🔀 Routing to: {question_type}")
        
        # Route to the appropriate handler
        if question_type == "analytical":
            try:
                logger.info("📊 Calling data analysis engine...")
                response = run_analytical_query(query)
                
                # Check analytical response quality
                if response and len(response.strip()) > 10:
                    # If the response looks like an error message or a fallback, also try general query
                    if any(phrase in response.lower() for phrase in 
                          ['sorry', 'unable to', 'cannot', 'not available', 'no data found']):
                        logger.info("🔄 Analytical response seems problematic, trying general query as supplement")
                        try:
                            general_response = run_general_query(query)
                            if general_response and len(general_response.strip()) > 10:
                                return f"Based on my data analysis: {response}\n\nSupplementary information: {general_response}"
                        except:
                            pass
                    
                    return response
                else:
                    logger.warning("⚠️ Analytical response is empty or too short, trying general query")
                    return run_general_query(query)
                
            except Exception as analytical_error:
                logger.error(f"❌ Analytical query failed: {analytical_error}")
                
                # Try general query as a fallback
                try:
                    logger.info("🔄 Trying general query as fallback")
                    general_response = run_general_query(query)
                    return f"Data analysis is temporarily unavailable, answering based on my knowledge:\n\n{general_response}"
                except:
                    return "Sorry, I am currently unable to process your query. Please try again later or ask a different question."
        else:
            # General query
            try:
                logger.info("📋 Calling general query engine...")
                return run_general_query(query)
            except Exception as general_error:
                logger.error(f"❌ General query failed: {general_error}")
                return "Sorry, an error occurred while processing your question. Please try rephrasing your question."
            
    except Exception as e:
        logger.error(f"❌ Routing error: {str(e)}")
        execution_time = time.time() - start_time
        return f"Sorry, a system error occurred while processing your question (Time taken: {execution_time:.1f} seconds). Please try again later."

def test_routing():
    """Tests the routing functionality"""
    test_queries = [
        ("What is Apple's stock price?", "analytical"),
        ("Tell me about Microsoft", "general"),
        ("Calculate average revenue", "analytical"),
        ("What does Google do?", "general"),
        ("Show me earnings data", "analytical"),
        ("Who are Tesla's competitors?", "general")
    ]
    
    print("🧪 Testing query routing...")
    
    for query, expected in test_queries:
        try:
            print(f"\n🔍 Testing: '{query}'")
            predicted = classify_question(query)
            result = route_query(query)
            
            status = "✅" if predicted == expected else "⚠️"
            print(f"{status} Classification: {predicted} (Expected: {expected})")
            print(f"📝 Response: {result[:100]}...")
            
        except Exception as e:
            print(f"❌ Test failed: {query} - {e}")

if __name__ == "__main__":
    test_routing()