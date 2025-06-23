# query_router.py - 强化版本
from langchain_openai import ChatOpenAI
from company_info_query_engine import run_general_query
from pandas_data_analyzer import run_analytical_query
from config_utils import load_openai_key
import logging
import time

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 轻量级分类模型
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    openai_api_key=load_openai_key(),
    temperature=0,
    max_tokens=50,
    timeout=15
)

def classify_question(query):
    """智能问题分类"""
    query_lower = query.lower()
    
    # 明确的分析类关键词
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
    
    # 明确的通用类关键词
    general_keywords = [
        'what does', 'tell me about', 'who is', 'describe',
        'business model', 'business', 'company',
        'products', 'services', 'industry', 'sector',
        'competitor', 'competitors', 'competition',
        'overview', 'introduction', 'about',
        'founded', 'headquarters', 'ceo', 'history',
        'what is', 'explain', 'how does', 'why does'
    ]
    
    # 计算匹配分数
    analytical_score = sum(1 for keyword in analytical_keywords if keyword in query_lower)
    general_score = sum(1 for keyword in general_keywords if keyword in query_lower)
    
    logger.info(f"关键词匹配 - 分析类: {analytical_score}, 通用类: {general_score}")
    
    # 特殊规则：包含具体数字相关的词汇偏向分析类
    if any(word in query_lower for word in ['$', 'dollar', 'million', 'billion', '%', 'percent']):
        analytical_score += 2
    
    # 决策逻辑
    if analytical_score > general_score:
        logger.info("📊 分类: analytical (通过关键词)")
        return "analytical"
    elif general_score > analytical_score:
        logger.info("📋 分类: general (通过关键词)")
        return "general"
    
    # 如果分数相等，使用LLM
    try:
        prompt = f"""分类这个问题为 "analytical" 或 "general":

问题: "{query}"

规则:
- analytical: 询问具体数据、价格、财务信息、统计分析
- general: 询问公司介绍、业务模式、产品服务、行业信息

只回答一个词:"""
        
        response = llm.invoke(prompt)
        classification = response.content.strip().lower()
        
        if "analytical" in classification:
            logger.info("📊 分类: analytical (通过LLM)")
            return "analytical"
        else:
            logger.info("📋 分类: general (通过LLM)")
            return "general"
            
    except Exception as e:
        logger.warning(f"❌ LLM分类失败: {e}, 默认为general")
        return "general"

def route_query(query):
    """查询路由主函数"""
    start_time = time.time()
    
    try:
        # 输入验证
        if not query or not query.strip():
            return "请提供一个有效的问题。"
        
        query = query.strip()
        logger.info(f"🎯 处理查询: {query}")
        
        # 分类问题
        question_type = classify_question(query)
        logger.info(f"🔀 路由到: {question_type}")
        
        # 路由到相应处理器
        if question_type == "analytical":
            try:
                logger.info("📊 调用数据分析引擎...")
                response = run_analytical_query(query)
                
                # 检查分析响应质量
                if response and len(response.strip()) > 10:
                    # 如果响应看起来像错误消息或备用响应，也尝试通用查询
                    if any(phrase in response.lower() for phrase in 
                          ['抱歉', 'sorry', '无法', 'cannot', '不可用', 'unavailable']):
                        logger.info("🔄 分析响应似乎有问题，尝试通用查询作为补充")
                        try:
                            general_response = run_general_query(query)
                            if general_response and len(general_response.strip()) > 10:
                                return f"根据我的数据分析：{response}\n\n补充信息：{general_response}"
                        except:
                            pass
                    
                    return response
                else:
                    logger.warning("⚠️ 分析响应为空或过短，尝试通用查询")
                    return run_general_query(query)
                
            except Exception as analytical_error:
                logger.error(f"❌ 分析查询失败: {analytical_error}")
                
                # 尝试通用查询作为备用
                try:
                    logger.info("🔄 尝试通用查询作为备用")
                    general_response = run_general_query(query)
                    return f"数据分析暂时不可用，基于我的知识回答：\n\n{general_response}"
                except:
                    return "抱歉，当前无法处理您的查询。请稍后重试或询问其他问题。"
        else:
            # 通用查询
            try:
                logger.info("📋 调用通用查询引擎...")
                return run_general_query(query)
            except Exception as general_error:
                logger.error(f"❌ 通用查询失败: {general_error}")
                return "抱歉，处理您的问题时遇到了错误。请尝试重新表述您的问题。"
            
    except Exception as e:
        logger.error(f"❌ 路由错误: {str(e)}")
        execution_time = time.time() - start_time
        return f"抱歉，处理您的问题时遇到了系统错误（耗时: {execution_time:.1f}秒）。请稍后重试。"

def test_routing():
    """测试路由功能"""
    test_queries = [
        ("What is Apple's stock price?", "analytical"),
        ("Tell me about Microsoft", "general"),
        ("Calculate average revenue", "analytical"),
        ("What does Google do?", "general"),
        ("Show me earnings data", "analytical"),
        ("Who are Tesla's competitors?", "general")
    ]
    
    print("🧪 测试查询路由...")
    
    for query, expected in test_queries:
        try:
            print(f"\n🔍 测试: '{query}'")
            predicted = classify_question(query)
            result = route_query(query)
            
            status = "✅" if predicted == expected else "⚠️"
            print(f"{status} 分类: {predicted} (期望: {expected})")
            print(f"📝 响应: {result[:100]}...")
            
        except Exception as e:
            print(f"❌ 测试失败: {query} - {e}")

if __name__ == "__main__":
    test_routing()