"""
Configuration settings for the Agentic Research Copilot
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Database settings
    database_url: str = "sqlite:///./data/app.db"
    memory_db_path: str = "data/memory.db"
    
    # Redis settings
    redis_url: str = "redis://localhost:6379"
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # AI/LLM settings
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_model: str = "openai/gpt-3.5-turbo"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    max_tokens: int = 2000
    temperature: float = 0.7
    
    # Memory settings
    max_conversation_tokens: int = 4000
    memory_cleanup_days: int = 30
    context_compression_enabled: bool = True
    
    # Agent settings
    max_concurrent_tasks: int = 5
    agent_timeout_seconds: int = 300
    agent_retry_attempts: int = 3
    
    # Vector database settings
    vector_db_url: str = "http://localhost:8080"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_dimension: int = 384
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings