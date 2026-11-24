import os
from dotenv import load_dotenv


dotenv_dir='./../../Ik_assignments/chat_bot/prod_small' #Environment variables path.
env_path=os.path.join(dotenv_dir,'.env')
# Load environment variables from .env file
load_dotenv(env_path)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPEN_ROUTER_KEY')
HF_KEY = os.getenv('HF_KEY')

print("env_path:", dotenv_dir)

print("OPENAI_API_KEY:", OPENAI_API_KEY)

print("TAVILY_API_KEY:", TAVILY_API_KEY)
print("OPENROUTER_API_KEY:", OPENROUTER_API_KEY)
print("HF_KEY:", HF_KEY)

def get_openai_api_key():
    return OPENAI_API_KEY
def get_tavily_api_key():
    return TAVILY_API_KEY
def get_openrouter_api_key():
    return OPENROUTER_API_KEY
def get_hf_key():
    return HF_KEY
