from langchain_community.document_loaders import CSVLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from config_utils import load_openai_key
import os

def generate_vector_store():
    """Generates the vector store"""
    try:
        # Check if the data file exists
        csv_file = "./data/company_overview.csv"
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"Data file not found: {csv_file}")
        
        print(f"📊 Loading data from: {csv_file}")
        
        # Load company data from CSV
        loader = CSVLoader(file_path=csv_file)
        documents = loader.load()
        
        print(f"✅ Loaded {len(documents)} documents")
        
        # Initialize the embedding model
        embeddings_model = OpenAIEmbeddings(openai_api_key=load_openai_key())
        
        print("🔄 Creating vector store...")
        
        # Create and save the vector library
        vectorstore = FAISS.from_documents(documents, embeddings_model)
        vectorstore_bytes = vectorstore.serialize_to_bytes()
        
        # Ensure the tmp directory exists
        os.makedirs('./tmp', exist_ok=True)
        
        # Save to file
        with open('./tmp/faiss_vectorstore.pkl', 'wb') as f:
            f.write(vectorstore_bytes)
        
        print("✅ Vector store saved successfully to ./tmp/faiss_vectorstore.pkl")
        
    except Exception as e:
        print(f"❌ Error generating vector store: {str(e)}")
        raise

if __name__ == "__main__":
    generate_vector_store()