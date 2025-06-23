from langchain_community.document_loaders import CSVLoader  # CSV加载器
from langchain_openai import OpenAIEmbeddings  # 嵌入模型
from langchain_community.vectorstores import FAISS  # 向量数据库
from config_utils import load_openai_key  # 密钥加载
import os

def generate_vector_store():
    """生成向量存储"""
    try:
        # 检查数据文件是否存在
        csv_file = "./data/company_overview.csv"
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"Data file not found: {csv_file}")
        
        print(f"📊 Loading data from: {csv_file}")
        
        # 从CSV加载公司数据
        loader = CSVLoader(file_path=csv_file)
        documents = loader.load()
        
        print(f"✅ Loaded {len(documents)} documents")
        
        # 初始化嵌入模型
        embeddings_model = OpenAIEmbeddings(openai_api_key=load_openai_key())
        
        print("🔄 Creating vector store...")
        
        # 创建并保存向量库
        vectorstore = FAISS.from_documents(documents, embeddings_model)
        vectorstore_bytes = vectorstore.serialize_to_bytes()  # 序列化为字节
        
        # 确保tmp目录存在
        os.makedirs('./tmp', exist_ok=True)
        
        # 保存到文件
        with open('./tmp/faiss_vectorstore.pkl', 'wb') as f:
            f.write(vectorstore_bytes)  # 保存到文件
        
        print("✅ Vector store saved successfully to ./tmp/faiss_vectorstore.pkl")
        
    except Exception as e:
        print(f"❌ Error generating vector store: {str(e)}")
        raise

if __name__ == "__main__":
    generate_vector_store()