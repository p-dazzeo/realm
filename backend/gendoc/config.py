"""
Configuration settings for the GenDoc service.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = Path(__file__).parent / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)

# Service configuration
HOST = os.getenv('GENDOC_HOST', '0.0.0.0')
PORT = int(os.getenv('GENDOC_PORT', '8000'))
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# LLM configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gpt-4')
MODEL_MAPPING = {
    'o4-mini': 'openai/o4-mini',
    'gpt-4o': 'openai/gpt-4o',
    
}

# File storage
STORAGE_DIR = Path(os.getenv('STORAGE_DIR', Path(__file__).parent / 'storage'))
STORAGE_DIR.mkdir(exist_ok=True)

# Prompt defaults
DEFAULT_SYSTEM_PROMPT = """You are REALM, an expert software documentation generator. 
Your task is to analyze code and produce high-quality, informative documentation.
Focus on clarity, technical accuracy, and providing useful context.""" 