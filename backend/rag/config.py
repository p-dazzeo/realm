"""
Configuration settings for the RAG service.
"""
import os
import sys
import logging
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
LOG_LEVEL_STR = os.getenv('LOG_LEVEL', 'DEBUG')  

# Convert LOG_LEVEL string to logging level
numeric_level = getattr(logging, LOG_LEVEL_STR.upper(), None)
if not isinstance(numeric_level, int):
    print(f"*** WARNING: Invalid log level: {LOG_LEVEL_STR}, setting to DEBUG ***", file=sys.stderr)
    numeric_level = logging.DEBUG
    LOG_LEVEL_STR = 'DEBUG'
else:
    print(f"*** Numeric log level: {numeric_level} (DEBUG={logging.DEBUG}, INFO={logging.INFO}) ***", file=sys.stderr)

# Ensure LOG_LEVEL is set to the actual numeric value for debugging
LOG_LEVEL = numeric_level

# LLM configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gpt-4o')
MODEL_MAPPING = {
    'o4-mini': 'openai/o4-mini',
    'gpt-4o': 'openai/gpt-4o',
    'text-embedding-3-small': 'openai/text-embedding-3-small'
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