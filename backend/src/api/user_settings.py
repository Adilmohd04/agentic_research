"""
User Settings API Endpoints
Handles user-specific settings like API keys, preferences, etc.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..core.service_manager import get_service_manager
from ..security.encryption import EncryptionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user-settings"])

# Initialize encryption service for API keys
encryption_service = EncryptionService()

class UserSettings(BaseModel):
    openrouter_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    preferred_model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    theme: Optional[str] = "light"
    notifications: Optional[bool] = True

def get_user_id(x_user_id: str = Header(None, alias="X-User-ID")):
    """Extract user ID from header"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    return x_user_id

@router.get("/settings")
async def get_user_settings(user_id: str = Depends(get_user_id)):
    """Get user settings"""
    try:
        # Get service manager
        service_manager = get_service_manager()
        supabase_service = service_manager.supabase_service
        
        # Ensure user exists in database
        internal_user_id = await supabase_service.ensure_user_exists(user_id)
        
        # Get user settings from Supabase
        result = supabase_service.client.table('users').select('*').eq('clerk_user_id', user_id).execute()
        
        if not result.data:
            # Return default settings if user not found
            return {
                "openrouter_api_key": "",
                "openai_api_key": "",
                "anthropic_api_key": "",
                "preferred_model": "sonoma-sky-alpha",
                "temperature": 0.7,
                "max_tokens": 2000,
                "theme": "light",
                "notifications": True
            }
        
        user_data = result.data[0]
        settings = user_data.get('settings', {})
        
        # Return settings (decrypt and mask API keys for security)
        def decrypt_and_mask_key(key_data):
            if not key_data or isinstance(key_data, str):
                return mask_api_key(key_data or '')
            try:
                from ..security.encryption import EncryptedData, EncryptionType
                encrypted_data = EncryptedData(
                    data=bytes.fromhex(key_data['encrypted_data']),
                    encryption_type=EncryptionType.SYMMETRIC,
                    algorithm=key_data['algorithm'],
                    key_id=key_data['key_id']
                )
                decrypted_key = encryption_service.decrypt_data(encrypted_data).decode('utf-8')
                return mask_api_key(decrypted_key)
            except Exception as e:
                logger.error(f"Failed to decrypt API key: {e}")
                return ""
        
        return {
            "openrouter_api_key": decrypt_and_mask_key(settings.get('openrouter_api_key')),
            "openai_api_key": decrypt_and_mask_key(settings.get('openai_api_key')),
            "anthropic_api_key": decrypt_and_mask_key(settings.get('anthropic_api_key')),
            "preferred_model": settings.get('preferred_model', 'sonoma-sky-alpha'),
            "temperature": settings.get('temperature', 0.7),
            "max_tokens": settings.get('max_tokens', 2000),
            "theme": settings.get('theme', 'light'),
            "notifications": settings.get('notifications', True)
        }
        
    except Exception as e:
        logger.error(f"Error getting user settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get settings")

@router.post("/settings")
async def save_user_settings(
    settings: UserSettings,
    user_id: str = Depends(get_user_id)
):
    """Save user settings"""
    try:
        # Get service manager
        service_manager = get_service_manager()
        supabase_service = service_manager.supabase_service
        
        # Ensure user exists in database
        internal_user_id = await supabase_service.ensure_user_exists(user_id)
        
        # Prepare settings data (encrypt API keys before storing)
        settings_data = {}
        if settings.openrouter_api_key is not None and settings.openrouter_api_key.strip():
            encrypted_key = encryption_service.encrypt_data(settings.openrouter_api_key)
            settings_data['openrouter_api_key'] = {
                'encrypted_data': encrypted_key.data.hex(),
                'key_id': encrypted_key.key_id,
                'algorithm': encrypted_key.algorithm
            }
        if settings.openai_api_key is not None and settings.openai_api_key.strip():
            encrypted_key = encryption_service.encrypt_data(settings.openai_api_key)
            settings_data['openai_api_key'] = {
                'encrypted_data': encrypted_key.data.hex(),
                'key_id': encrypted_key.key_id,
                'algorithm': encrypted_key.algorithm
            }
        if settings.anthropic_api_key is not None and settings.anthropic_api_key.strip():
            encrypted_key = encryption_service.encrypt_data(settings.anthropic_api_key)
            settings_data['anthropic_api_key'] = {
                'encrypted_data': encrypted_key.data.hex(),
                'key_id': encrypted_key.key_id,
                'algorithm': encrypted_key.algorithm
            }
        if settings.preferred_model is not None:
            settings_data['preferred_model'] = settings.preferred_model
        if settings.temperature is not None:
            settings_data['temperature'] = settings.temperature
        if settings.max_tokens is not None:
            settings_data['max_tokens'] = settings.max_tokens
        if settings.theme is not None:
            settings_data['theme'] = settings.theme
        if settings.notifications is not None:
            settings_data['notifications'] = settings.notifications
        
        # Get current settings
        current_result = supabase_service.client.table('users').select('settings').eq('clerk_user_id', user_id).execute()
        current_settings = {}
        if current_result.data:
            current_settings = current_result.data[0].get('settings', {})
        
        # Merge with existing settings
        merged_settings = {**current_settings, **settings_data}
        
        # Update user settings in Supabase
        result = supabase_service.client.table('users').update({
            'settings': merged_settings,
            'updated_at': 'now()'
        }).eq('clerk_user_id', user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to save settings")
        
        logger.info(f"Updated settings for user {user_id}")
        
        return {
            "message": "Settings saved successfully",
            "settings": {
                "openrouter_api_key": mask_api_key(merged_settings.get('openrouter_api_key', '')),
                "openai_api_key": mask_api_key(merged_settings.get('openai_api_key', '')),
                "anthropic_api_key": mask_api_key(merged_settings.get('anthropic_api_key', '')),
                "preferred_model": merged_settings.get('preferred_model', 'sonoma-sky-alpha'),
                "temperature": merged_settings.get('temperature', 0.7),
                "max_tokens": merged_settings.get('max_tokens', 2000),
                "theme": merged_settings.get('theme', 'light'),
                "notifications": merged_settings.get('notifications', True)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving user settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save settings")

@router.get("/api-key-status")
async def get_api_key_status(user_id: str = Depends(get_user_id)):
    """Check which API keys are configured for the user"""
    try:
        # Get service manager
        service_manager = get_service_manager()
        supabase_service = service_manager.supabase_service
        
        # Get user settings
        result = supabase_service.client.table('users').select('settings').eq('clerk_user_id', user_id).execute()
        
        if not result.data:
            return {
                "openrouter_configured": False,
                "openai_configured": False,
                "anthropic_configured": False,
                "any_configured": False
            }
        
        settings = result.data[0].get('settings', {})
        
        openrouter_configured = bool(settings.get('openrouter_api_key', '').strip())
        openai_configured = bool(settings.get('openai_api_key', '').strip())
        anthropic_configured = bool(settings.get('anthropic_api_key', '').strip())
        
        return {
            "openrouter_configured": openrouter_configured,
            "openai_configured": openai_configured,
            "anthropic_configured": anthropic_configured,
            "any_configured": openrouter_configured or openai_configured or anthropic_configured,
            "preferred_model": settings.get('preferred_model', 'sonoma-sky-alpha')
        }
        
    except Exception as e:
        logger.error(f"Error checking API key status: {str(e)}")
        return {
            "openrouter_configured": False,
            "openai_configured": False,
            "anthropic_configured": False,
            "any_configured": False
        }

@router.post("/test-api-key")
async def test_user_api_key(
    api_provider: str,
    user_id: str = Depends(get_user_id)
):
    """Test user's API key"""
    try:
        # Get service manager
        service_manager = get_service_manager()
        supabase_service = service_manager.supabase_service
        
        # Get user's API key
        result = supabase_service.client.table('users').select('settings').eq('clerk_user_id', user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User settings not found")
        
        settings = result.data[0].get('settings', {})
        
        if api_provider == "openrouter":
            api_key = settings.get('openrouter_api_key')
            if not api_key:
                raise HTTPException(status_code=400, detail="OpenRouter API key not configured")
            
            # Test OpenRouter API
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openrouter/sonoma-sky-alpha",
                        "messages": [{"role": "user", "content": "Test"}],
                        "max_tokens": 10
                    }
                )
                
                if response.status_code == 200:
                    return {"status": "success", "message": "OpenRouter API key is valid"}
                else:
                    return {"status": "error", "message": f"API test failed: {response.status_code}"}
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported API provider")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing API key: {str(e)}")
        raise HTTPException(status_code=500, detail="API key test failed")

def mask_api_key(api_key: str) -> str:
    """Mask API key for security (show only first 8 and last 4 characters)"""
    if not api_key or len(api_key) < 12:
        return ""
    return f"{api_key[:8]}...{api_key[-4:]}"

def decrypt_user_api_key(key_data) -> Optional[str]:
    """Decrypt user API key for actual use"""
    if not key_data:
        return None
    if isinstance(key_data, str):
        return key_data  # Legacy unencrypted key
    try:
        from ..security.encryption import EncryptedData, EncryptionType
        encrypted_data = EncryptedData(
            data=bytes.fromhex(key_data['encrypted_data']),
            encryption_type=EncryptionType.SYMMETRIC,
            algorithm=key_data['algorithm'],
            key_id=key_data['key_id']
        )
        return encryption_service.decrypt_data(encrypted_data).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to decrypt API key: {e}")
        return None