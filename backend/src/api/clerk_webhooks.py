"""
Clerk Webhook Handlers
Handles user creation, updates, and deletion from Clerk
"""

import os
import json
import hmac
import hashlib
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import logging

from ..core.service_manager import get_service_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Clerk webhook signature"""
    try:
        # Clerk sends signature as "v1,<signature>"
        if not signature.startswith('v1,'):
            return False
        
        signature = signature[3:]  # Remove "v1," prefix
        
        # Create expected signature
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False

@router.post("/clerk")
async def handle_clerk_webhook(
    request: Request,
    svix_id: str = Header(None, alias="svix-id"),
    svix_timestamp: str = Header(None, alias="svix-timestamp"),
    svix_signature: str = Header(None, alias="svix-signature")
):
    """Handle Clerk webhook events"""
    try:
        # Get webhook secret
        webhook_secret = os.getenv('CLERK_WEBHOOK_SECRET')
        if not webhook_secret:
            logger.error("CLERK_WEBHOOK_SECRET not configured")
            raise HTTPException(status_code=500, detail="Webhook secret not configured")
        
        # Get request body
        payload = await request.body()
        
        # Verify signature
        if not verify_webhook_signature(payload, svix_signature, webhook_secret):
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse event data
        try:
            event_data = json.loads(payload.decode())
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        event_type = event_data.get('type')
        event_object = event_data.get('data', {})
        
        logger.info(f"Received Clerk webhook: {event_type}")
        
        # Handle different event types
        if event_type == 'user.created':
            await handle_user_created(event_object)
        elif event_type == 'user.updated':
            await handle_user_updated(event_object)
        elif event_type == 'user.deleted':
            await handle_user_deleted(event_object)
        else:
            logger.info(f"Unhandled event type: {event_type}")
        
        return JSONResponse(content={"status": "success"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling Clerk webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def handle_user_created(user_data: Dict[str, Any]):
    """Handle user creation event"""
    try:
        clerk_user_id = user_data.get('id')
        if not clerk_user_id:
            logger.error("No user ID in user.created event")
            return
        
        # Extract user information
        email_addresses = user_data.get('email_addresses', [])
        primary_email = None
        for email in email_addresses:
            if email.get('id') == user_data.get('primary_email_address_id'):
                primary_email = email.get('email_address')
                break
        
        user_info = {
            'email': primary_email,
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'image_url': user_data.get('image_url')
        }
        
        # Get service manager and create user in Supabase
        service_manager = get_service_manager()
        supabase_service = service_manager.supabase_service
        user_id = await supabase_service.ensure_user_exists(clerk_user_id, user_info)
        
        logger.info(f"Created user in Supabase: {clerk_user_id} -> {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling user.created: {str(e)}")

async def handle_user_updated(user_data: Dict[str, Any]):
    """Handle user update event"""
    try:
        clerk_user_id = user_data.get('id')
        if not clerk_user_id:
            logger.error("No user ID in user.updated event")
            return
        
        # Extract updated user information
        email_addresses = user_data.get('email_addresses', [])
        primary_email = None
        for email in email_addresses:
            if email.get('id') == user_data.get('primary_email_address_id'):
                primary_email = email.get('email_address')
                break
        
        user_info = {
            'email': primary_email,
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'image_url': user_data.get('image_url')
        }
        
        # Get service manager and update user in Supabase
        service_manager = get_service_manager()
        supabase_service = service_manager.supabase_service
        
        try:
            result = supabase_service.client.table('users').update({
                'email': user_info['email'],
                'first_name': user_info['first_name'],
                'last_name': user_info['last_name'],
                'image_url': user_info['image_url'],
                'updated_at': 'now()'
            }).eq('clerk_user_id', clerk_user_id).execute()
            
            if result.data:
                logger.info(f"Updated user in Supabase: {clerk_user_id}")
            else:
                logger.warning(f"User not found for update: {clerk_user_id}")
                
        except Exception as e:
            logger.error(f"Error updating user in Supabase: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error handling user.updated: {str(e)}")

async def handle_user_deleted(user_data: Dict[str, Any]):
    """Handle user deletion event"""
    try:
        clerk_user_id = user_data.get('id')
        if not clerk_user_id:
            logger.error("No user ID in user.deleted event")
            return
        
        # Get service manager and delete user from Supabase (CASCADE will handle documents and chunks)
        service_manager = get_service_manager()
        supabase_service = service_manager.supabase_service
        
        try:
            result = supabase_service.client.table('users').delete().eq('clerk_user_id', clerk_user_id).execute()
            
            if result.data:
                logger.info(f"Deleted user from Supabase: {clerk_user_id}")
            else:
                logger.warning(f"User not found for deletion: {clerk_user_id}")
                
        except Exception as e:
            logger.error(f"Error deleting user from Supabase: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error handling user.deleted: {str(e)}")

@router.get("/clerk/test")
async def test_clerk_webhook():
    """Test endpoint for Clerk webhook setup"""
    webhook_secret = os.getenv('CLERK_WEBHOOK_SECRET')
    return {
        "status": "ok",
        "message": "Clerk webhook endpoint is working",
        "webhook_secret_configured": bool(webhook_secret),
        "webhook_secret_format": "correct" if webhook_secret and webhook_secret.startswith('whsec_') else "invalid",
        "endpoint_url": "/api/webhooks/clerk",
        "supported_events": ["user.created", "user.updated", "user.deleted"]
    }

@router.get("/clerk/simulate-user-created")
async def simulate_user_created():
    """Simulate a user.created event for testing"""
    try:
        # Simulate user creation
        test_user_data = {
            "id": "user_test123",
            "email_addresses": [
                {
                    "id": "email_test123",
                    "email_address": "test@example.com"
                }
            ],
            "primary_email_address_id": "email_test123",
            "first_name": "Test",
            "last_name": "User",
            "image_url": "https://example.com/avatar.jpg"
        }
        
        await handle_user_created(test_user_data)
        
        return {
            "status": "success",
            "message": "Test user created successfully",
            "user_id": test_user_data["id"]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }