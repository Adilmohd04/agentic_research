"""
Free Open-Source Embedding Service
Uses sentence-transformers for cost-effective embeddings
"""

import os
import logging
from typing import List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class FreeEmbeddingService:
    """Free embedding service using sentence-transformers"""
    
    def __init__(self):
        self.model_name = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
        self.dimension = int(os.getenv('EMBEDDING_DIMENSION', '384'))
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self._load_model()
        else:
            logger.warning("sentence-transformers not available. Install with: pip install sentence-transformers")
    
    def _load_model(self):
        """Load the embedding model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded successfully. Dimension: {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            self.model = None
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        if not self.model:
            logger.warning("Embedding model not available, returning zero vectors")
            return [[0.0] * self.dimension for _ in texts]
        
        try:
            # Run embedding generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                self.executor,
                self._encode_texts,
                texts
            )
            
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return [[0.0] * self.dimension for _ in texts]
    
    def _encode_texts(self, texts: List[str]):
        """Synchronous encoding function for thread pool"""
        return self.model.encode(texts, convert_to_numpy=True)
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0]
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension
    
    def get_model_info(self) -> dict:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "available": self.model is not None,
            "cost": "free",
            "provider": "sentence-transformers"
        }
    
    async def health_check(self) -> dict:
        """Check service health"""
        try:
            if not self.model:
                return {
                    "status": "unhealthy",
                    "error": "Model not loaded",
                    "available": False
                }
            
            # Test with a simple embedding
            test_embedding = await self.generate_single_embedding("test")
            
            return {
                "status": "healthy",
                "model": self.model_name,
                "dimension": len(test_embedding),
                "available": True,
                "test_successful": len(test_embedding) == self.dimension
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "available": False
            }

# Global instance
_embedding_service = None

def get_embedding_service() -> FreeEmbeddingService:
    """Get global embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = FreeEmbeddingService()
    return _embedding_service