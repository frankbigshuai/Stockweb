from langchain_openai import OpenAIEmbeddings  # OpenAI嵌入模型
from langchain.prompts import PromptTemplate  # 提示模板
from langchain_openai import ChatOpenAI  # OpenAI聊天模型
from langchain.schema.runnable import RunnablePassthrough  # 链式处理
from langchain.schema import StrOutputParser  # 输出解析
from config_utils import load_openai_key  # 加载API密钥

# 🔧 全局变量，延迟初始化
_vectorstore = None
_embeddings_model = None
_llm = None
_chain = None

def _initialize_components():
    """延迟初始化所有组件"""
    global _vectorstore, _embeddings_model, _llm, _chain
    
    if _vectorstore is not None:
        return  # 已经初始化过了
    
    try:
        print("🔄 初始化AI组件...")
        
        # 🔧 尝试导入和加载FAISS
        try:
            from langchain_community.vectorstores import FAISS
            
            # 初始化嵌入模型
            _embeddings_model = OpenAIEmbeddings(openai_api_key=load_openai_key())
            
            # 加载预训练的向量数据库
            with open('./tmp/faiss_vectorstore.pkl', 'rb') as f:
                vectorstore_bytes = f.read()
            _vectorstore = FAISS.deserialize_from_bytes(
                embeddings=_embeddings_model, 
                serialized=vectorstore_bytes, 
                allow_dangerous_deserialization=True
            )
            print("✅ FAISS向量数据库加载成功")
            
        except Exception as faiss_error:
            print(f"⚠️ FAISS加载失败: {faiss_error}")
            print("🔄 切换到简化模式")
            _vectorstore = None
            _embeddings_model = None
        
        # 初始化LLM（无论是否有FAISS都需要）
        _llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            openai_api_key=load_openai_key(),
            temperature=0.3,
            max_tokens=800,
            timeout=30
        )
        
        # 根据是否有向量数据库创建不同的链
        if _vectorstore:
            # 有向量数据库的模板
            template = """
You are a knowledgeable financial assistant specializing in company information and market trends. 
Use the following information to answer the user's question in a natural, conversational manner. 
Keep your response concise, accurate, and focused.

Context: {context}
User's question: {question}

Your Answer:"""
            
            prompt = PromptTemplate.from_template(template)
            _chain = (
                {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
                | prompt
                | _llm
                | StrOutputParser()
            )
        else:
            # 没有向量数据库的简化模板
            template = """
You are a knowledgeable financial assistant and investment advisor. 
Answer the user's question based on your financial knowledge and expertise.
Keep your response concise, accurate, and practical.
If discussing specific investments, remind users that investing carries risks.

User's question: {question}

Your Answer:"""
            
            prompt = PromptTemplate.from_template(template)
            _chain = (
                {"question": RunnablePassthrough()}
                | prompt
                | _llm
                | StrOutputParser()
            )
        
        print("✅ AI组件初始化完成")
        
    except Exception as e:
        print(f"❌ AI组件初始化失败: {e}")
        # 创建最简单的备用链
        _llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            openai_api_key=load_openai_key(),
            temperature=0.3
        )

def run_general_query(query):
    """执行通用查询"""
    try:
        # 确保组件已初始化
        _initialize_components()
        
        if _vectorstore:
            # 使用向量数据库查询
            print("🔍 使用向量数据库查询")
            results = _vectorstore.similarity_search(query, k=3)
            
            if not results:
                context = "没有找到相关的公司信息。"
            else:
                context = " ".join([result.page_content for result in results])
            
            response = _chain.invoke({"question": query, "context": context})
            
        else:
            # 简化查询模式
            print("🔍 使用简化查询模式")
            if _chain:
                response = _chain.invoke({"question": query})
            else:
                # 最后的备用方案
                response = _llm.invoke(f"作为投资顾问，请回答：{query}")
                response = response.content if hasattr(response, 'content') else str(response)
        
        return response
        
    except Exception as e:
        print(f"❌ 查询处理错误: {str(e)}")
        return f"抱歉，处理您的查询时出现错误。请稍后再试。错误信息：{str(e)}"

if __name__ == "__main__":
    # 测试查询
    query = "What companies have a comparable business model to Microsoft?"
    response = run_general_query(query)
    print(response)