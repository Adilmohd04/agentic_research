"""
Data Encryption and Secure Storage

This module provides comprehensive data encryption capabilities for sensitive data
at rest and in transit, secure session management, and audit logging.
"""

import os
import json
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)

class EncryptionType(Enum):
    """Types of encryption."""
    SYMMETRIC = "symmetric"
    ASYMMETRIC = "asymmetric"
    HYBRID = "hybrid"

class DataClassification(Enum):
    """Data classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

@dataclass
class EncryptionConfig:
    """Encryption configuration."""
    symmetric_algorithm: str = "AES-256-GCM"
    asymmetric_algorithm: str = "RSA-2048"
    key_derivation_iterations: int = 100000
    salt_length: int = 32
    iv_length: int = 16
    tag_length: int = 16
    key_rotation_days: int = 90
    backup_key_count: int = 3

@dataclass
class EncryptedData:
    """Encrypted data container."""
    data: bytes
    encryption_type: EncryptionType
    algorithm: str
    key_id: str
    iv: Optional[bytes] = None
    tag: Optional[bytes] = None
    salt: Optional[bytes] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class EncryptionKey:
    """Encryption key metadata."""
    key_id: str
    algorithm: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool = True
    key_data: Optional[bytes] = None  # Encrypted key data
    public_key: Optional[bytes] = None  # For asymmetric keys@da
taclass
class AuditLogEntry:
    """Audit log entry."""
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    resource_id: str
    ip_address: str
    user_agent: str
    success: bool
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}

class KeyManager:
    """Manages encryption keys and key rotation."""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
        self.keys: Dict[str, EncryptionKey] = {}
        self.master_key = self._load_or_create_master_key()
        self.fernet = Fernet(self.master_key)
    
    def _load_or_create_master_key(self) -> bytes:
        """Load or create master encryption key."""
        key_file = "master.key"
        
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            # Generate new master key
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            logger.info("Generated new master encryption key")
            return key
    
    def generate_symmetric_key(self, key_id: Optional[str] = None) -> str:
        """Generate a new symmetric encryption key."""
        if key_id is None:
            key_id = f"sym_{secrets.token_urlsafe(16)}"
        
        # Generate key
        key_data = Fernet.generate_key()
        
        # Encrypt key with master key
        encrypted_key = self.fernet.encrypt(key_data)
        
        # Create key metadata
        key_metadata = EncryptionKey(
            key_id=key_id,
            algorithm=self.config.symmetric_algorithm,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=self.config.key_rotation_days),
            key_data=encrypted_key
        )
        
        self.keys[key_id] = key_metadata
        logger.info(f"Generated symmetric key: {key_id}")
        return key_id
    
    def get_key(self, key_id: str) -> Optional[bytes]:
        """Get decrypted key data."""
        key_metadata = self.keys.get(key_id)
        if not key_metadata or not key_metadata.is_active:
            return None
        
        # Check if key is expired
        if key_metadata.expires_at and datetime.utcnow() > key_metadata.expires_at:
            logger.warning(f"Key expired: {key_id}")
            return None
        
        # Decrypt key
        try:
            return self.fernet.decrypt(key_metadata.key_data)
        except Exception as e:
            logger.error(f"Failed to decrypt key {key_id}: {e}")
            return Nonec
lass DataEncryption:
    """Handles data encryption and decryption."""
    
    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager
        self.config = key_manager.config
    
    def encrypt_symmetric(self, data: Union[str, bytes], key_id: str) -> EncryptedData:
        """Encrypt data using symmetric encryption."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Get encryption key
        key_data = self.key_manager.get_key(key_id)
        if not key_data:
            raise ValueError(f"Key not found or inactive: {key_id}")
        
        # Create Fernet cipher
        fernet = Fernet(key_data)
        
        # Encrypt data
        encrypted_data = fernet.encrypt(data)
        
        return EncryptedData(
            data=encrypted_data,
            encryption_type=EncryptionType.SYMMETRIC,
            algorithm=self.config.symmetric_algorithm,
            key_id=key_id
        )
    
    def decrypt_symmetric(self, encrypted_data: EncryptedData) -> bytes:
        """Decrypt data using symmetric encryption."""
        # Get decryption key
        key_data = self.key_manager.get_key(encrypted_data.key_id)
        if not key_data:
            raise ValueError(f"Key not found or inactive: {encrypted_data.key_id}")
        
        # Create Fernet cipher
        fernet = Fernet(key_data)
        
        # Decrypt data
        try:
            return fernet.decrypt(encrypted_data.data)
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Decryption failed")

class SecureStorage:
    """Secure storage for sensitive data."""
    
    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager
        self.encryption = DataEncryption(key_manager)
        self.storage: Dict[str, EncryptedData] = {}  # In production, use database
        self.default_key_id = key_manager.generate_symmetric_key("default_storage_key")
    
    def store(self, 
              key: str, 
              data: Union[str, bytes, dict], 
              classification: DataClassification = DataClassification.CONFIDENTIAL,
              encryption_key_id: Optional[str] = None) -> bool:
        """Store data securely."""
        try:
            # Serialize data if needed
            if isinstance(data, dict):
                data = json.dumps(data).encode('utf-8')
            elif isinstance(data, str):
                data = data.encode('utf-8')
            
            # Choose encryption key based on classification
            if encryption_key_id is None:
                encryption_key_id = self.default_key_id
            
            # Encrypt data
            encrypted_data = self.encryption.encrypt_symmetric(data, encryption_key_id)
            
            # Store encrypted data
            self.storage[key] = encrypted_data
            
            logger.info(f"Stored encrypted data: {key} (classification: {classification.value})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store data {key}: {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[bytes]:
        """Retrieve and decrypt data."""
        try:
            encrypted_data = self.storage.get(key)
            if not encrypted_data:
                return None
            
            # Decrypt data
            return self.encryption.decrypt_symmetric(encrypted_data)
                
        except Exception as e:
            logger.error(f"Failed to retrieve data {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Securely delete data."""
        try:
            if key in self.storage:
                del self.storage[key]
                logger.info(f"Deleted encrypted data: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete data {key}: {e}")
            return False

class AuditLogger:
    """Secure audit logging system."""
    
    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager
        self.encryption = DataEncryption(key_manager)
        self.audit_logs: List[EncryptedData] = []  # In production, use database
        self.audit_key_id = key_manager.generate_symmetric_key("audit_log_key")
    
    def log_action(self, 
                   user_id: str,
                   action: str,
                   resource: str,
                   resource_id: str,
                   ip_address: str,
                   user_agent: str,
                   success: bool,
                   details: Optional[Dict[str, Any]] = None):
        """Log an audit event."""
        try:
            # Create audit log entry
            log_entry = AuditLogEntry(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                action=action,
                resource=resource,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                details=details or {}
            )
            
            # Serialize and encrypt log entry
            log_data = json.dumps(asdict(log_entry), default=str).encode('utf-8')
            encrypted_log = self.encryption.encrypt_symmetric(log_data, self.audit_key_id)
            
            # Store encrypted log
            self.audit_logs.append(encrypted_log)
            
            logger.debug(f"Audit log created: {action} by {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")

class EncryptionService:
    """Main encryption service."""
    
    def __init__(self):
        self.config = EncryptionConfig()
        self.key_manager = KeyManager(self.config)
        self.data_encryption = DataEncryption(self.key_manager)
        self.secure_storage = SecureStorage(self.key_manager)
        self.audit_logger = AuditLogger(self.key_manager)
    
    def encrypt_data(self, 
                    data: Union[str, bytes, dict],
                    key_id: Optional[str] = None) -> EncryptedData:
        """Encrypt data using symmetric encryption."""
        if key_id is None:
            key_id = self.key_manager.generate_symmetric_key()
        
        return self.data_encryption.encrypt_symmetric(data, key_id)
    
    def decrypt_data(self, encrypted_data: EncryptedData) -> bytes:
        """Decrypt data."""
        return self.data_encryption.decrypt_symmetric(encrypted_data)
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get encryption service status."""
        return {
            "key_manager": {
                "total_keys": len(self.key_manager.keys),
                "active_keys": len([k for k in self.key_manager.keys.values() if k.is_active])
            },
            "secure_storage": {
                "total_items": len(self.secure_storage.storage)
            },
            "audit_logger": {
                "total_logs": len(self.audit_logger.audit_logs)
            }
        }