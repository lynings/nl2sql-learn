import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # PostgreSQL 配置
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "text2sql")
    
    # ChromaDB 配置
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")

    # OpenAI 配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4-turbo-preview")
    print(OPENAI_MODEL_NAME)

    # 应用配置
    CONFIG_DIR = os.getenv("CONFIG_DIR", os.path.join(os.path.dirname(__file__), "../config"))

settings = Settings() 