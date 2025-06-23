from langchain_openai import OpenAIEmbeddings  # OpenAI嵌入模型
from langchain_community.vectorstores import FAISS  # 向量数据库
from langchain.prompts import PromptTemplate  # 提示模板
from langchain_openai import ChatOpenAI  # OpenAI聊天模型
from langchain.schema.runnable import RunnablePassthrough  # 链式处理
from langchain.schema import StrOutputParser  # 输出解析
from config_utils import load_openai_key  # 加载API密钥

# 初始化嵌入模型
embeddings_model = OpenAIEmbeddings(openai_api_key=load_openai_key())

# 加载预训练的向量数据库
with open('./tmp/faiss_vectorstore.pkl', 'rb') as f:
    vectorstore_bytes = f.read()
vectorstore = FAISS.deserialize_from_bytes(
    embeddings=embeddings_model, 
    serialized=vectorstore_bytes, 
    allow_dangerous_deserialization=True
)

# 🔄 切换到最便宜的gpt-3.5-turbo模型
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",  # ✅ 从gpt-4o改为gpt-3.5-turbo  
    openai_api_key=load_openai_key(),
    temperature=0.3,  # 适中的创造性
    max_tokens=800,   # 控制输出长度，节省费用
    timeout=30        # 设置超时时间
)

# 优化的回答模板 - 更简洁明确
template = """
You are a knowledgeable financial assistant specializing in company information and market trends. 
Use the following information to answer the user's question in a natural, conversational manner. 
Keep your response concise, accurate, and focused.

Context: {context}
User's question: {question}

Your Answer:"""

prompt = PromptTemplate.from_template(template)  # 创建模板实例

# 构建处理链
chain = (
    {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
    | prompt  # 应用模板
    | llm  # 调用模型
    | StrOutputParser()  # 解析输出
)

def run_general_query(query):
    """执行通用查询"""
    try:
        # 向量相似度搜索，只取前3个结果以提高效率
        results = vectorstore.similarity_search(query, k=3)  
        
        if not results:
            return "抱歉，我没有找到相关的公司信息。请尝试更具体的问题。"
        
        # 合并前3个结果的内容
        top_results_content = " ".join([result.page_content for result in results])
        
        # 生成回答
        response = chain.invoke({"question": query, "context": top_results_content})
        return response
        
    except Exception as e:
        print(f"General query error: {str(e)}")
        return f"处理查询时出现错误：{str(e)}"

if __name__ == "__main__":
    # 测试查询
    query = "What companies have a comparable business model to Microsoft?"
    response = run_general_query(query)
    print(response)