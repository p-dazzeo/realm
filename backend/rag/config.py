"""
Configuration settings for the RAG service.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = Path(__file__).parent / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)

# Service configuration
HOST = os.getenv('RAG_HOST', '0.0.0.0')
PORT = int(os.getenv('RAG_PORT', '8001'))
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# LLM configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gpt-4o')
MODEL_MAPPING = {
    'o4-mini': 'openai/o4-mini',
    'gpt-4o': 'openai/gpt-4o',

}

# ChromaDB configuration
CHROMA_DATA_DIR = Path(os.getenv('CHROMA_DATA_DIR', Path(__file__).parent / 'data'))
CHROMA_DATA_DIR.mkdir(exist_ok=True)

# Vector DB settings
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '200'))

# File storage
STORAGE_DIR = Path(os.getenv('STORAGE_DIR', Path(__file__).parent / 'storage'))
STORAGE_DIR.mkdir(exist_ok=True)

# System prompt for RAG
RAG_SYSTEM_PROMPT = """You are REALM, an expert code assistant.  
Your task is to answer questions about code by using the provided context. 
Always base your answers on the context provided, and if you're unsure or the context doesn't contain 
the necessary information, say so clearly. Provide accurate, technically precise responses.""" 