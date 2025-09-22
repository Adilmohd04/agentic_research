"""
Unit tests for Encryption System

Tests the data encryption and secure storage functionality including
key management, data encryption/decryption, and audit logging.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open

from backend.src.security.encryption import (
    EncryptionService,
    KeyManager,
    DataEncryption,
    SecureStorage,
    AuditLogger,
    EncryptionConfig,
    EncryptionType,
    DataClassification,
    EncryptedData,
    EncryptionKey,
    AuditLogEntry
)


class TestEncryptionConfig:
    """Test EncryptionConfig dataclass."""
    
    def test_default_config(self):
        """Test default encryption configuration."""
        config = EncryptionConfig()
        
        assert config.symmetric_algorithm == "AES-256-GCM"
        assert config.asymmetric_algorithm == "RSA-2048"
        assert config.key_derivation_iterations == 100000
        assert config.salt_length == 32
        assert config.key_rotation_days == 90
    
    def test_custom_config(self):
        """Test custom encryption configuration."""
        config = EncryptionConfig(
            symmetric_algorithm="AES-128-GCM",
            key_rotation_days=30,
            salt_length=16
        )
        
        assert config.symmetric_algorithm == "AES-128-GCM"
        assert config.key_rotation_days == 30
        assert config.salt_length == 16


class TestKeyManager:
    """Test KeyManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory to avoid creating files in project root
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            yield temp_dir
            os.chdir(original_cwd)
    
    @pytest.fixture
    def key_manager(self, temp_dir):
        """Create KeyManager instance for testing."""
        config = EncryptionConfig()
        return KeyManager(config)
    
    def test_master_key_creation(self, key_manager):
        """Test master key creation."""
        assert key_manager.master_key is not None
        assert len(key_manager.master_key) > 0
        assert key_manager.fernet is not None
    
    def test_generate_symmetric_key(self, key_manager):
        """Test symmetric key generation."""
        key_id = key_manager.generate_symmetric_key()
        
        assert key_id is not None
        assert key_id in key_manager.keys
        
        key_metadata = key_manager.keys[key_id]
        assert key_metadata.algorithm == key_manager.config.symmetric_algorithm
        assert key_metadata.is_active is True
        assert key_metadata.key_data is not None
    
    def test_generate_symmetric_key_with_id(self, key_manager):
        """Test symmetric key generation with custom ID."""
        custom_id = "test_key_123"
        key_id = key_manager.generate_symmetric_key(custom_id)
        
        assert key_id == custom_id
        assert custom_id in key_manager.keys
    
    def test_get_key_valid(self, key_manager):
        """Test getting valid key."""
        key_id = key_manager.generate_symmetric_key()
        key_data = key_manager.get_key(key_id)
        
        assert key_data is not None
        assert len(key_data) > 0
    
    def test_get_key_invalid(self, key_manager):
        """Test getting invalid key."""
        key_data = key_manager.get_key("nonexistent_key")
        
        assert key_data is None
    
    def test_get_key_expired(self, key_manager):
        """Test getting expired key."""
        key_id = key_manager.generate_symmetric_key()
        
        # Manually expire the key
        key_metadata = key_manager.keys[key_id]
        key_metadata.expires_at = datetime.utcnow() - timedelta(days=1)
        
        key_data = key_manager.get_key(key_id)
        
        assert key_data is None


class TestDataEncryption:
    """Test DataEncryption class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            yield temp_dir
            os.chdir(original_cwd)
    
    @pytest.fixture
    def data_encryption(self, temp_dir):
        """Create DataEncryption instance for testing."""
        config = EncryptionConfig()
        key_manager = KeyManager(config)
        return DataEncryption(key_manager)
    
    def test_encrypt_decrypt_symmetric_string(self, data_encryption):
        """Test symmetric encryption/decryption with string data."""
        original_data = "Hello, World! This is a test message."
        key_id = data_encryption.key_manager.generate_symmetric_key()
        
        # Encrypt data
        encrypted_data = data_encryption.encrypt_symmetric(original_data, key_id)
        
        assert isinstance(encrypted_data, EncryptedData)
        assert encrypted_data.encryption_type == EncryptionType.SYMMETRIC
        assert encrypted_data.key_id == key_id
        assert encrypted_data.data != original_data.encode('utf-8')
        
        # Decrypt data
        decrypted_data = data_encryption.decrypt_symmetric(encrypted_data)
        
        assert decrypted_data.decode('utf-8') == original_data
    
    def test_encrypt_decrypt_symmetric_bytes(self, data_encryption):
        """Test symmetric encryption/decryption with bytes data."""
        original_data = b"Binary data \x00\x01\x02\x03"
        key_id = data_encryption.key_manager.generate_symmetric_key()
        
        # Encrypt data
        encrypted_data = data_encryption.encrypt_symmetric(original_data, key_id)
        
        assert isinstance(encrypted_data, EncryptedData)
        assert encrypted_data.data != original_data
        
        # Decrypt data
        decrypted_data = data_encryption.decrypt_symmetric(encrypted_data)
        
        assert decrypted_data == original_data
    
    def test_encrypt_with_invalid_key(self, data_encryption):
        """Test encryption with invalid key."""
        original_data = "Test data"
        invalid_key_id = "nonexistent_key"
        
        with pytest.raises(ValueError, match="Key not found or inactive"):
            data_encryption.encrypt_symmetric(original_data, invalid_key_id)
    
    def test_decrypt_with_invalid_key(self, data_encryption):
        """Test decryption with invalid key."""
        # Create encrypted data with valid key
        original_data = "Test data"
        key_id = data_encryption.key_manager.generate_symmetric_key()
        encrypted_data = data_encryption.encrypt_symmetric(original_data, key_id)
        
        # Modify key_id to invalid one
        encrypted_data.key_id = "nonexistent_key"
        
        with pytest.raises(ValueError, match="Key not found or inactive"):
            data_encryption.decrypt_symmetric(encrypted_data)


class TestSecureStorage:
    """Test SecureStorage class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            yield temp_dir
            os.chdir(original_cwd)
    
    @pytest.fixture
    def secure_storage(self, temp_dir):
        """Create SecureStorage instance for testing."""
        config = EncryptionConfig()
        key_manager = KeyManager(config)
        return SecureStorage(key_manager)
    
    def test_store_retrieve_string(self, secure_storage):
        """Test storing and retrieving string data."""
        key = "test_key"
        data = "This is test data"
        
        # Store data
        success = secure_storage.store(key, data)
        assert success is True
        
        # Retrieve data
        retrieved_data = secure_storage.retrieve(key)
        assert retrieved_data is not None
        assert retrieved_data.decode('utf-8') == data
    
    def test_store_retrieve_dict(self, secure_storage):
        """Test storing and retrieving dictionary data."""
        key = "test_dict"
        data = {"name": "John", "age": 30, "city": "New York"}
        
        # Store data
        success = secure_storage.store(key, data)
        assert success is True
        
        # Retrieve data
        retrieved_data = secure_storage.retrieve(key)
        assert retrieved_data is not None
        
        import json
        retrieved_dict = json.loads(retrieved_data.decode('utf-8'))
        assert retrieved_dict == data
    
    def test_store_with_classification(self, secure_storage):
        """Test storing data with different classifications."""
        key = "classified_data"
        data = "Top secret information"
        
        # Store with restricted classification
        success = secure_storage.store(
            key, 
            data, 
            classification=DataClassification.RESTRICTED
        )
        assert success is True
        
        # Retrieve data
        retrieved_data = secure_storage.retrieve(key)
        assert retrieved_data is not None
        assert retrieved_data.decode('utf-8') == data
    
    def test_retrieve_nonexistent(self, secure_storage):
        """Test retrieving non-existent data."""
        retrieved_data = secure_storage.retrieve("nonexistent_key")
        assert retrieved_data is None
    
    def test_delete_data(self, secure_storage):
        """Test deleting stored data."""
        key = "delete_test"
        data = "Data to be deleted"
        
        # Store data
        secure_storage.store(key, data)
        
        # Verify data exists
        assert secure_storage.retrieve(key) is not None
        
        # Delete data
        success = secure_storage.delete(key)
        assert success is True
        
        # Verify data is gone
        assert secure_storage.retrieve(key) is None
    
    def test_delete_nonexistent(self, secure_storage):
        """Test deleting non-existent data."""
        success = secure_storage.delete("nonexistent_key")
        assert success is False


class TestAuditLogger:
    """Test AuditLogger class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            yield temp_dir
            os.chdir(original_cwd)
    
    @pytest.fixture
    def audit_logger(self, temp_dir):
        """Create AuditLogger instance for testing."""
        config = EncryptionConfig()
        key_manager = KeyManager(config)
        return AuditLogger(key_manager)
    
    def test_log_action(self, audit_logger):
        """Test logging an audit action."""
        # Log an action
        audit_logger.log_action(
            user_id="user123",
            action="login",
            resource="authentication",
            resource_id="session456",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            success=True,
            details={"method": "password"}
        )
        
        # Verify log was created
        assert len(audit_logger.audit_logs) == 1
        
        # Verify log is encrypted
        encrypted_log = audit_logger.audit_logs[0]
        assert isinstance(encrypted_log, EncryptedData)
        assert encrypted_log.encryption_type == EncryptionType.SYMMETRIC
    
    def test_multiple_log_entries(self, audit_logger):
        """Test logging multiple audit entries."""
        # Log multiple actions
        for i in range(3):
            audit_logger.log_action(
                user_id=f"user{i}",
                action="access_document",
                resource="document",
                resource_id=f"doc{i}",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                success=True
            )
        
        # Verify all logs were created
        assert len(audit_logger.audit_logs) == 3


class TestEncryptionService:
    """Test EncryptionService class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            yield temp_dir
            os.chdir(original_cwd)
    
    @pytest.fixture
    def encryption_service(self, temp_dir):
        """Create EncryptionService instance for testing."""
        return EncryptionService()
    
    def test_service_initialization(self, encryption_service):
        """Test encryption service initialization."""
        assert encryption_service.config is not None
        assert encryption_service.key_manager is not None
        assert encryption_service.data_encryption is not None
        assert encryption_service.secure_storage is not None
        assert encryption_service.audit_logger is not None
    
    def test_encrypt_decrypt_data(self, encryption_service):
        """Test encrypting and decrypting data through service."""
        original_data = "Service test data"
        
        # Encrypt data
        encrypted_data = encryption_service.encrypt_data(original_data)
        
        assert isinstance(encrypted_data, EncryptedData)
        assert encrypted_data.data != original_data.encode('utf-8')
        
        # Decrypt data
        decrypted_data = encryption_service.decrypt_data(encrypted_data)
        
        assert decrypted_data.decode('utf-8') == original_data
    
    def test_encrypt_with_custom_key(self, encryption_service):
        """Test encrypting with custom key."""
        original_data = "Custom key test"
        key_id = encryption_service.key_manager.generate_symmetric_key("custom_key")
        
        # Encrypt with custom key
        encrypted_data = encryption_service.encrypt_data(original_data, key_id)
        
        assert encrypted_data.key_id == key_id
        
        # Decrypt data
        decrypted_data = encryption_service.decrypt_data(encrypted_data)
        
        assert decrypted_data.decode('utf-8') == original_data
    
    def test_get_service_status(self, encryption_service):
        """Test getting service status."""
        status = encryption_service.get_service_status()
        
        assert "key_manager" in status
        assert "secure_storage" in status
        assert "audit_logger" in status
        
        assert "total_keys" in status["key_manager"]
        assert "active_keys" in status["key_manager"]
        assert "total_items" in status["secure_storage"]
        assert "total_logs" in status["audit_logger"]


class TestDataClasses:
    """Test data classes used in encryption system."""
    
    def test_encrypted_data_creation(self):
        """Test EncryptedData dataclass creation."""
        encrypted_data = EncryptedData(
            data=b"encrypted_bytes",
            encryption_type=EncryptionType.SYMMETRIC,
            algorithm="AES-256-GCM",
            key_id="test_key",
            iv=b"initialization_vector",
            tag=b"auth_tag"
        )
        
        assert encrypted_data.data == b"encrypted_bytes"
        assert encrypted_data.encryption_type == EncryptionType.SYMMETRIC
        assert encrypted_data.algorithm == "AES-256-GCM"
        assert encrypted_data.key_id == "test_key"
        assert encrypted_data.timestamp is not None
    
    def test_encryption_key_creation(self):
        """Test EncryptionKey dataclass creation."""
        key = EncryptionKey(
            key_id="test_key_123",
            algorithm="AES-256-GCM",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=90),
            key_data=b"encrypted_key_data"
        )
        
        assert key.key_id == "test_key_123"
        assert key.algorithm == "AES-256-GCM"
        assert key.is_active is True
        assert key.key_data == b"encrypted_key_data"
    
    def test_audit_log_entry_creation(self):
        """Test AuditLogEntry dataclass creation."""
        log_entry = AuditLogEntry(
            timestamp=datetime.utcnow(),
            user_id="user123",
            action="login",
            resource="authentication",
            resource_id="session456",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            success=True,
            details={"method": "password", "duration": 1.5}
        )
        
        assert log_entry.user_id == "user123"
        assert log_entry.action == "login"
        assert log_entry.success is True
        assert log_entry.details["method"] == "password"
        assert log_entry.details["duration"] == 1.5


if __name__ == "__main__":
    pytest.main([__file__])