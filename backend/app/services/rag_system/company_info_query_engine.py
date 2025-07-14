# company_info_query_engine.py - FAISS error handling and fallback version
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import StrOutputParser
from config_utils import load_openai_key
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
embeddings_model = None
vectorstore = None
llm = None
chain = None
fallback_mode = False

def initialize_llm():
    """Initialize LLM (always needed)"""
    global llm
    try:
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            openai_api_key=load_openai_key(),
            temperature=0.3,
            max_tokens=800,
            timeout=30
        )
        logger.info("✅ LLM initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize LLM: {e}")
        return False

def try_load_faiss_vectorstore():
    """Try to load FAISS vectorstore with comprehensive error handling"""
    global embeddings_model, vectorstore, fallback_mode
    
    try:
        # Check if FAISS can be imported
        from langchain_community.vectorstores import FAISS
        logger.info("✅ FAISS library imported")
        
        # Check vectorstore file
        vectorstore_path = './tmp/faiss_vectorstore.pkl'
        if not os.path.exists(vectorstore_path):
            logger.warning(f"⚠️ Vectorstore file not found: {vectorstore_path}")
            fallback_mode = True
            return False
        
        # Initialize embeddings
        embeddings_model = OpenAIEmbeddings(openai_api_key=load_openai_key())
        logger.info("✅ Embeddings model initialized")
        
        # Load vectorstore
        with open(vectorstore_path, 'rb') as f:
            vectorstore_bytes = f.read()
        
        vectorstore = FAISS.deserialize_from_bytes(
            embeddings=embeddings_model,
            serialized=vectorstore_bytes,
            allow_dangerous_deserialization=True
        )
        logger.info("✅ FAISS vectorstore loaded")
        
        # Test vectorstore with simple query
        test_results = vectorstore.similarity_search("test", k=1)
        logger.info(f"✅ FAISS test successful: {len(test_results)} results")
        
        fallback_mode = False
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️ FAISS library not available: {e}")
        fallback_mode = True
        return False
    except Exception as e:
        logger.warning(f"⚠️ FAISS vectorstore loading failed: {e}")
        fallback_mode = True
        return False

def setup_processing_chain():
    """Setup processing chain based on available components"""
    global chain
    
    try:
        if not fallback_mode and vectorstore:
            # Vector search chain
            template = """You are a knowledgeable financial assistant specializing in company information and market trends. 
Use the following information to answer the user's question in a natural, conversational manner. 
Keep your response concise, accurate, and focused.

Context: {context}
User's question: {question}

Your Answer:"""
            
            prompt = PromptTemplate.from_template(template)
            chain = (
                {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
            )
            logger.info("✅ Vector search chain setup completed")
        else:
            # Fallback LLM-only chain
            template = """You are a knowledgeable financial assistant specializing in company information and market trends.
Answer the user's question based on your training knowledge about companies, markets, and business.
Provide accurate, helpful information in a natural, conversational manner.

User's question: {question}

Your Answer:"""
            
            prompt = PromptTemplate.from_template(template)
            chain = prompt | llm | StrOutputParser()
            logger.info("✅ Fallback LLM chain setup completed")
        
    except Exception as e:
        logger.error(f"❌ Failed to setup processing chain: {e}")
        raise

def safe_vector_search(query, k=3):
    """Safely perform vector search with error handling"""
    try:
        if fallback_mode or not vectorstore:
            return []
        
        # Try vector search with error handling
        results = vectorstore.similarity_search(query, k=k)
        logger.info(f"✅ Vector search successful: {len(results)} results")
        return results
        
    except Exception as e:
        logger.warning(f"⚠️ Vector search failed: {e}")
        logger.info("🔄 Switching to fallback mode for this query")
        return []

def run_general_query(query):
    """Execute general query with robust error handling"""
    try:
        logger.info(f"🔍 Processing general query: {query[:50]}...")
        
        # Initialize components if not done
        if llm is None:
            if not initialize_llm():
                return "Sorry, the query system is currently unavailable."
        
        if chain is None:
            setup_processing_chain()
        
        # Try vector search if available
        if not fallback_mode:
            try:
                search_results = safe_vector_search(query)
                
                if search_results:
                    # Use vector search results
                    context = " ".join([result.page_content for result in search_results])
                    response = chain.invoke({"question": query, "context": context})
                    logger.info("✅ Vector search query completed")
                    return response
                else:
                    logger.info("🔄 No vector results, using fallback mode")
            except Exception as search_error:
                logger.warning(f"⚠️ Vector search error: {search_error}")
        
        # Fallback to LLM-only mode
        logger.info("🔄 Using LLM fallback mode")
        
        # Setup fallback chain if needed
        if fallback_mode or not vectorstore:
            fallback_template = """You are a knowledgeable financial assistant. Answer the user's question about companies, markets, or business topics based on your training knowledge.

User's question: {question}

Your Answer:"""
            
            fallback_prompt = PromptTemplate.from_template(fallback_template)
            fallback_chain = fallback_prompt | llm | StrOutputParser()
            
            response = fallback_chain.invoke({"question": query})
            logger.info("✅ Fallback query completed")
            return response
        else:
            response = chain.invoke({"question": query})
            logger.info("✅ General query completed")
            return response
        
    except Exception as e:
        logger.error(f"❌ General query processing failed: {e}")
        return f"Sorry, I encountered an error while processing your query. Please try again or ask a different question."

def get_engine_status():
    """Get engine status information"""
    return {
        'llm_available': llm is not None,
        'vectorstore_available': vectorstore is not None and not fallback_mode,
        'embeddings_available': embeddings_model is not None,
        'fallback_mode': fallback_mode,
        'mode': 'fallback' if fallback_mode else 'vector_search',
        'vectorstore_path_exists': os.path.exists('./tmp/faiss_vectorstore.pkl')
    }

# Initialize on module load
try:
    logger.info("🚀 Initializing company query engine...")
    
    # Always initialize LLM
    initialize_llm()
    
    # Try to load FAISS (with fallback)
    if try_load_faiss_vectorstore():
        logger.info("✅ FAISS vectorstore ready")
    else:
        logger.info("⚠️ Running in fallback mode (no FAISS)")
    
    # Setup processing chain
    setup_processing_chain()
    
    logger.info("✅ Company query engine initialization completed")
    
except Exception as e:
    logger.error(f"❌ Company query engine initialization failed: {e}")
    fallback_mode = True

# Main execution for testing
if __name__ == "__main__":
    print("🧪 Testing Company Query Engine...")
    print("=" * 50)
    
    # Show status
    status = get_engine_status()
    print(f"📊 Engine Status: {status}")
    
    # Test queries
    test_queries = [
        "What does Apple do?",
        "Tell me about Microsoft's business",
        "Apple news",
        "Who are Tesla's competitors?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: {query}")
        try:
            response = run_general_query(query)
            print(f"   Response: {response[:150]}...")
            print(f"   Status: ✅ Success")
        except Exception as e:
            print(f"   Error: ❌ {e}")
    
    print(f"\n{'='*50}")
    print("🎉 Testing completed!")