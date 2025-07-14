
import yaml
import os
from dotenv import load_dotenv

def load_openai_key(filepath=None):
    """
    Loads the API key, prioritizing environment variables, then YAML file.
    """
    # 1. Load .env file
    load_dotenv()
    
    # 2. Try to read from environment variables
    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY')
    if api_key:
        print("✅ API Key loaded from environment variables")
        return api_key
    
    # 3. Compatible with existing YAML file method
    if filepath is None:
        filepath = "./secret.yml"
        
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as file:
                config = yaml.safe_load(file)
            print("✅ API Key loaded from YAML file")
            return config.get("OPENAI_KEY") or config.get("OPENAI_API_KEY")
        except Exception as e:
            print(f"❌ Failed to load from YAML: {e}")
    
    # 4. Raise error if not found
    raise ValueError(
        "OPENAI API key not found. Please set OPENAI_API_KEY in .env file or create secret.yml"
    )

# Cost estimation function
def estimate_cost(input_tokens, output_tokens, model="gpt-3.5-turbo"):
    """Estimates API call cost (USD)"""
    prices = {
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4": {"input": 0.03, "output": 0.06}
    }
    
    if model in prices:
        cost = (input_tokens * prices[model]["input"] + 
                output_tokens * prices[model]["output"]) / 1000
        return round(cost, 6)
    return 0

if __name__ == "__main__":
    try:
        key = load_openai_key()
        print(f"🔑 API Key: {key[:10]}...")
        
        # Test cost estimation
        cost = estimate_cost(100, 50, "gpt-3.5-turbo")
        print(f"💰 Estimated cost for 100 input + 50 output tokens: ${cost}")
        
    except ValueError as e:
        print(f"❌ Error: {e}")
