"""
Centralized Service Manager
Manages all service instances to avoid duplicates and improve performance
"""

import logging
from typing import Optional, Dict, Any
from .supabase_vector import SupabaseVectorService
from .ai_service import AIService
from .free_embedding_service import FreeEmbeddingService

logger = logging.getLogger(__name__)

class ServiceManager:
    """Singleton service manager for all application services"""
    
    _instance: Optional['ServiceManager'] = None
    _supabase_service: Optional[SupabaseVectorService] = None
    _ai_service: Optional[AIService] = None
    _embedding_service: Optional[FreeEmbeddingService] = None
    _voice_service: Optional['VoiceService'] = None
    
    def __new__(cls) -> 'ServiceManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def supabase_service(self) -> SupabaseVectorService:
        """Get or create Supabase Vector service instance"""
        if self._supabase_service is None:
            logger.info("Initializing Supabase Vector Service")
            self._supabase_service = SupabaseVectorService()
        return self._supabase_service
    
    @property
    def ai_service(self) -> AIService:
        """Get or create AI service instance"""
        if self._ai_service is None:
            logger.info("Initializing AI Service")
            self._ai_service = AIService()
        return self._ai_service
    
    @property
    def embedding_service(self) -> FreeEmbeddingService:
        """Get or create embedding service instance"""
        if self._embedding_service is None:
            logger.info("Initializing Free Embedding Service")
            from .free_embedding_service import get_embedding_service
            self._embedding_service = get_embedding_service()
        return self._embedding_service
    
    @property
    def voice_service(self):
        """Get or create voice service instance"""
        if self._voice_service is None:
            logger.info("Initializing Voice Service")
            from ..voice.voice_service import get_voice_service
            self._voice_service = get_voice_service()
        return self._voice_service
    
    async def get_user_api_keys(self, user_id: str) -> Dict[str, str]:
        """Get user's API keys from database (centralized method) - decrypts keys for use"""
        try:
            result = self.supabase_service.client.table('users').select('settings').eq('clerk_user_id', user_id).execute()
            
            if result.data:
                settings = result.data[0].get('settings', {})
                
                # Import decrypt function
                from ..api.user_settings import decrypt_user_api_key
                
                return {
                    'openrouter_api_key': decrypt_user_api_key(settings.get('openrouter_api_key')) or '',
                    'openai_api_key': decrypt_user_api_key(settings.get('openai_api_key')) or '',
                    'anthropic_api_key': decrypt_user_api_key(settings.get('anthropic_api_key')) or ''
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting user API keys: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for all services"""
        try:
            # Check Supabase Vector service
            supabase_health = await self.supabase_service.health_check()
            
            # Check embedding service
            embedding_health = await self.embedding_service.health_check()
            
            # Check AI service status
            ai_status = self.ai_service.get_service_status()
            
            # Check voice service
            voice_health = await self.voice_service.health_check()
            
            return {
                "status": "healthy" if all([
                    supabase_health.get("status") == "healthy",
                    embedding_health.get("status") == "healthy",
                    ai_status.get("service_status") == "operational"
                ]) else "degraded",
                "services": {
                    "supabase_vector": supabase_health,
                    "embedding": embedding_health,
                    "ai": ai_status,
                    "voice": voice_health
                },
                "timestamp": supabase_health.get("timestamp")
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "services": {
                    "supabase_vector": {"status": "error"},
                    "embedding": {"status": "error"},
                    "ai": {"status": "error"},
                    "voice": {"status": "error"}
                }
            }
    
    async def close_all(self):
        """Close all service connections"""
        try:
            if self._ai_service:
                await self._ai_service.close()
            logger.info("All services closed successfully")
        except Exception as e:
            logger.error(f"Error closing services: {str(e)}")

# Global service manager instance
_service_manager: Optional[ServiceManager] = None

def get_service_manager() -> ServiceManager:
    """Get the global service manager instance"""
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager()
    return _service_manager

# Convenience functions for backward compatibility
async def get_ai_service() -> AIService:
    """Get AI service instance"""
    return get_service_manager().ai_service

def get_supabase_service() -> SupabaseVectorService:
    """Get Supabase Vector service instance"""
    return get_service_manager().supabase_service

def get_embedding_service() -> FreeEmbeddingService:
    """Get embedding service instance"""
    return get_service_manager().embedding_service