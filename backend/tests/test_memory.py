"""
Unit tests for the shared memory and context management system
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime, timedelta

from src.core.memory import (
    SharedMemory, Message, AgentContext, TaskRecord, ContextCompressor
)


@pytest.fixture
async def temp_memory():
    """Create a temporary memory instance for testing"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    memory = SharedMemory(db_path=db_path)
    await memory._init_database()
    
    yield memory
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_message():
    """Create a sample message for testing"""
    return Message(
        id="msg-123",
        role="user",
        content="Hello, how can you help me with research?",
        timestamp=datetime.now(),
        metadata={"source": "web_ui", "user_id": "user-456"},
        citations=None
    )


class TestSharedMemory:
    """Test SharedMemory functionality"""
    
    @pytest.mark.asyncio
    async def test_add_and_get_message(self, temp_memory, sample_message):
        """Test adding and retrieving messages"""
        session_id = "session-123"
        
        # Add message
        await temp_memory.add_message(session_id, sample_message)
        
        # Retrieve messages
        messages = await temp_memory.get_conversation_history(session_id)
        
        assert len(messages) == 1
        assert messages[0].id == sample_message.id
        assert messages[0].content == sample_message.content
    
    @pytest.mark.asyncio
    async def test_memory_stats(self, temp_memory, sample_message):
        """Test memory statistics"""
        session_id = "session-stats"
        
        # Add some data
        await temp_memory.add_message(session_id, sample_message)
        
        # Get stats
        stats = await temp_memory.get_memory_stats()
        
        assert 'total_messages' in stats
        assert 'active_agents' in stats
        assert 'tasks_by_status' in stats
        assert 'cache_sizes' in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])