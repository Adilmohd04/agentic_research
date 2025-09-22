"""
AI Service with OpenRouter Integration for RAG System
"""

import os
import asyncio
import httpx
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging
from .config import get_settings

logger = logging.getLogger(__name__)

class AIService:
    """Unified AI service supporting OpenRouter, OpenAI, and Anthropic"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # Available models through OpenRouter
        self.available_models = {
            # Featured Model - Sonoma Sky Alpha
            "sonoma-sky-alpha": "openrouter/sonoma-sky-alpha",
            
            # OpenAI Models
            "gpt-4": "openai/gpt-4",
            "gpt-4-turbo": "openai/gpt-4-turbo",
            "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
            
            # Anthropic Models
            "claude-3-opus": "anthropic/claude-3-opus",
            "claude-3-sonnet": "anthropic/claude-3-sonnet",
            "claude-3-haiku": "anthropic/claude-3-haiku",
            
            # Other Popular Models
            "llama-2-70b": "meta-llama/llama-2-70b-chat",
            "mixtral-8x7b": "mistralai/mixtral-8x7b-instruct",
            "gemini-pro": "google/gemini-pro",
            
            # Specialized Models
            "code-llama": "codellama/codellama-70b-instruct",
            "nous-hermes": "nousresearch/nous-hermes-2-mixtral-8x7b-dpo"
        }
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        context_documents: Optional[List[Dict]] = None,
        user_api_keys: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Generate AI response with optional RAG context"""
        
        try:
            # Use Sonoma Sky Alpha as default if none specified
            if not model:
                model = os.getenv('DEFAULT_LLM_MODEL', 'sonoma-sky-alpha')
            
            # Resolve model name
            resolved_model = self.available_models.get(model, model)
            
            # Add RAG context if provided
            if context_documents:
                enhanced_messages = self._add_rag_context(messages, context_documents)
            else:
                enhanced_messages = messages
            
            # Choose API based on available keys (user keys take priority)
            user_openrouter_key = user_api_keys.get('openrouter_api_key') if user_api_keys else None
            user_openai_key = user_api_keys.get('openai_api_key') if user_api_keys else None
            
            if user_openrouter_key or self.settings.openrouter_api_key:
                api_key = user_openrouter_key or self.settings.openrouter_api_key
                response = await self._call_openrouter(
                    enhanced_messages, resolved_model, temperature, max_tokens, api_key
                )
            elif (user_openai_key or self.settings.openai_api_key) and "openai" in resolved_model:
                api_key = user_openai_key or self.settings.openai_api_key
                response = await self._call_openai(
                    enhanced_messages, resolved_model.split("/")[-1], temperature, max_tokens, api_key
                )
            else:
                # Fallback to mock response
                response = await self._mock_response(enhanced_messages)
            
            return {
                "response": response.get("content", ""),
                "model_used": resolved_model,
                "tokens_used": response.get("tokens_used", 0),
                "context_used": len(context_documents) if context_documents else 0,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"AI generation error: {str(e)}")
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again.",
                "error": str(e),
                "status": "error",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _call_openrouter(
        self, 
        messages: List[Dict], 
        model: str, 
        temperature: float, 
        max_tokens: int,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call OpenRouter API"""
        
        used_api_key = api_key or self.settings.openrouter_api_key
        headers = {
            "Authorization": f"Bearer {used_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",  # Optional
            "X-Title": "AI Agenting Research Platform"  # Optional
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        response = await self.client.post(
            f"{self.settings.openrouter_base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "tokens_used": data.get("usage", {}).get("total_tokens", 0)
            }
        else:
            raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
    
    async def _call_openai(
        self, 
        messages: List[Dict], 
        model: str, 
        temperature: float, 
        max_tokens: int,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call OpenAI API directly"""
        
        used_api_key = api_key or self.settings.openai_api_key
        headers = {
            "Authorization": f"Bearer {used_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = await self.client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "tokens_used": data.get("usage", {}).get("total_tokens", 0)
            }
        else:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
    
    async def _mock_response(self, messages: List[Dict]) -> Dict[str, Any]:
        """Generate mock response when no API keys are available"""
        
        last_message = messages[-1]["content"] if messages else "Hello"
        
        mock_responses = [
            f"I understand you're asking about: '{last_message[:100]}...' I'm currently running in demo mode without API access. Please configure your OpenRouter or OpenAI API key to get real AI responses.",
            "This is a simulated response. To get actual AI-powered answers, please add your API keys to the configuration.",
            f"Mock AI Response: I can see you mentioned '{last_message[:50]}...' - In production mode with proper API keys, I would provide detailed, contextual responses."
        ]
        
        import random
        return {
            "content": random.choice(mock_responses),
            "tokens_used": 0
        }
    
    def _add_rag_context(self, messages: List[Dict], context_documents: List[Dict]) -> List[Dict]:
        """Add RAG context to conversation"""
        
        if not context_documents:
            return messages
        
        # Create context string from documents
        context_parts = []
        for doc in context_documents[:5]:  # Limit to top 5 documents
            context_parts.append(f"Source: {doc.get('title', 'Unknown')}\n{doc.get('content', '')}")
        
        context_text = "\n\n---\n\n".join(context_parts)
        
        # Create system message with context
        system_message = {
            "role": "system",
            "content": f"""You are an AI research assistant with access to relevant documents. Use the following context to provide accurate, well-sourced answers. Always cite your sources when referencing the provided documents.

CONTEXT DOCUMENTS:
{context_text}

Instructions:
1. Use the context documents to provide accurate information
2. Cite sources when referencing specific information
3. If the context doesn't contain relevant information, say so clearly
4. Provide comprehensive but concise answers
5. Maintain a professional, helpful tone"""
        }
        
        # Insert system message at the beginning
        enhanced_messages = [system_message] + messages
        
        return enhanced_messages
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using free open-source models"""
        try:
            from .free_embedding_service import get_embedding_service
            embedding_service = get_embedding_service()
            return await embedding_service.generate_embeddings(texts)
        except Exception as e:
            logger.error(f"Embedding generation error: {str(e)}")
            # Return zero vectors as fallback
            dimension = int(os.getenv('EMBEDDING_DIMENSION', '384'))
            return [[0.0] * dimension for _ in texts]
    
    async def _openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API"""
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "text-embedding-ada-002",
            "input": texts
        }
        
        response = await self.client.post(
            "https://api.openai.com/v1/embeddings",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            return [item["embedding"] for item in data["data"]]
        else:
            raise Exception(f"OpenAI Embeddings API error: {response.status_code}")
    
    async def _local_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local sentence transformers"""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embeddings = model.encode(texts)
            return embeddings.tolist()
        except ImportError:
            logger.warning("SentenceTransformers not available, using zero vectors")
            return [[0.0] * 384 for _ in texts]
    
    def get_available_models(self) -> Dict[str, str]:
        """Get list of available models"""
        return self.available_models
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get AI service status"""
        return {
            "openrouter_configured": bool(self.settings.openrouter_api_key),
            "openai_configured": bool(self.settings.openai_api_key),
            "anthropic_configured": bool(self.settings.anthropic_api_key),
            "default_model": self.settings.default_model,
            "available_models": len(self.available_models),
            "service_status": "operational"
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global AI service instance
ai_service = AIService()

async def get_ai_service() -> AIService:
    """Get AI service instance"""
    return ai_service