"""
LLM integration for the RAG service.
"""
import logging
from typing import Dict, List, Any

from litellm import completion
import litellm
from backend.rag import config
from shared.models import RAGRequest, RAGResponse

logger = logging.getLogger(__name__)

# Initialize LiteLLM with API keys from environment
if config.OPENAI_API_KEY:
    litellm.api_key = config.OPENAI_API_KEY


def generate_rag_response(request: RAGRequest, context_docs: List[Dict[str, Any]]) -> RAGResponse:
    """
    Generate a response using RAG with LiteLLM.
    
    Args:
        request: RAG request parameters
        context_docs: Context documents from vector search
        
    Returns:
        RAG response with generated answer and sources
    """
    logger.info(f"Generating RAG response for query: {request.query}")
    
    # Map the model name to LiteLLM format
    model_name = config.MODEL_MAPPING.get(request.model_name, request.model_name)
    # Log context documents
    logger.debug(f"******************** LLM DEBUG: Retrieved {len(context_docs)} context documents ********************")
    for i, doc in enumerate(context_docs):
        file_path = doc['metadata'].get('file_path', 'unknown')
        logger.debug(f"Context doc {i+1}: file={file_path}, score={doc.get('relevance_score', 'N/A')}")
    
    # Prepare context from documents
    context = ""
    for i, doc in enumerate(context_docs):
        context += f"\nDocument {i+1} (from {doc['metadata']['file_path']}):\n{doc['content']}\n"
    
    # Prepare the messages for LLM
    system_prompt = config.RAG_SYSTEM_PROMPT
    user_prompt = f"Question: {request.query}\n\nContext:\n{context}\n\nPlease answer the question based on the provided context."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        # Call LiteLLM for completion
        response = completion(
            model=model_name,
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        
        # Extract the generated answer
        answer = response.choices[0].message.content
        # Convert the usage object to a dictionary
        usage_dict = None
        if response.usage:
            usage_dict = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        
        # Create the response
        rag_response = RAGResponse(
            answer=answer,
            sources=context_docs,
            token_usage=usage_dict
        )
        
        return rag_response
        
    except Exception as e:
        logger.error(f"Error generating RAG response: {str(e)}")
        raise 