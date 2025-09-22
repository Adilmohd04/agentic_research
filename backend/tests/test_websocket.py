"""
Tests for WebSocket functionality
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from src.main import app
from src.websocket.connection_manager import ConnectionManager


class TestConnectionManager:
    """Test WebSocket connection manager"""
    
    @pytest.fixture
    def connection_manager(self):
        return ConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        class MockWebSocket:
            def __init__(self):
                self.messages = []
                self.closed = False
            
            async def accept(self):
                pass
            
            async def send_text(self, message: str):
                if not self.closed:
                    self.messages.append(message)
            
            async def close(self):
                self.closed = True
        
        return MockWebSocket()
    
    @pytest.mark.asyncio
    async def test_connection_management(self, connection_manager, mock_websocket):
        """Test WebSocket connection and disconnection"""
        
        session_id = "test-session"
        user_id = "test-user"
        
        # Test connection
        await connection_manager.connect(mock_websocket, session_id, user_id)
        
        # Verify connection is tracked
        assert session_id in connection_manager.active_connections
        assert mock_websocket in connection_manager.active_connections[session_id]
        assert mock_websocket in connection_manager.connection_info
        
        # Test disconnection
        await connection_manager.disconnect(mock_websocket)
        
        # Verify connection is removed
        assert session_id not in connection_manager.active_connections or not connection_manager.active_connections[session_id]
        assert mock_websocket not in connection_manager.connection_info
    
    @pytest.mark.asyncio
    async def test_message_broadcasting(self, connection_manager, mock_websocket):
        """Test message broadcasting to session"""
        
        session_id = "test-session"
        await connection_manager.connect(mock_websocket, session_id)
        
        # Broadcast message
        test_message = {"type": "test", "content": "Hello World"}
        await connection_manager.broadcast_to_session(session_id, test_message)
        
        # Verify message was sent
        assert len(mock_websocket.messages) > 0
        
        # Check if test message was sent (it might not be the first message due to connection confirmation)
        messages_content = [json.loads(msg) for msg in mock_websocket.messages]
        test_message_sent = any(msg.get("type") == "test" for msg in messages_content)
        assert test_message_sent
    
    @pytest.mark.asyncio
    async def test_agent_status_subscription(self, connection_manager, mock_websocket):
        """Test agent status subscription"""
        
        await connection_manager.subscribe_to_agent_status(mock_websocket)
        
        # Verify websocket is in subscribers
        assert mock_websocket in connection_manager.agent_status_subscribers
        
        # Test broadcasting agent status
        status_update = {"agents": 4, "active": 2}
        await connection_manager.broadcast_agent_status(status_update)
        
        # Verify status update was sent
        assert len(mock_websocket.messages) > 0
    
    @pytest.mark.asyncio
    async def test_message_handling(self, connection_manager, mock_websocket):
        """Test WebSocket message handling"""
        
        session_id = "test-session"
        await connection_manager.connect(mock_websocket, session_id)
        
        # Test ping message
        ping_message = {"type": "ping"}
        await connection_manager.handle_message(mock_websocket, ping_message)
        
        # Should receive pong response
        messages = [json.loads(msg) for msg in mock_websocket.messages]
        pong_received = any(msg.get("type") == "pong" for msg in messages)
        assert pong_received
    
    def test_connection_stats(self, connection_manager):
        """Test connection statistics"""
        
        stats = connection_manager.get_connection_stats()
        
        assert "total_connections" in stats
        assert "active_sessions" in stats
        assert "agent_status_subscribers" in stats
        assert "task_progress_subscribers" in stats
        assert "sessions" in stats


class TestWebSocketIntegration:
    """Test WebSocket integration with FastAPI"""
    
    def test_websocket_endpoint_exists(self):
        """Test that WebSocket endpoints are properly configured"""
        
        client = TestClient(app)
        
        # Test that the app has WebSocket routes
        websocket_routes = [route for route in app.routes if hasattr(route, 'path') and route.path.startswith('/ws')]
        assert len(websocket_routes) > 0
    
    @pytest.mark.asyncio
    async def test_websocket_connection_flow(self):
        """Test WebSocket connection flow"""
        
        # This is a simplified test - in practice you'd use WebSocket test client
        from src.websocket.connection_manager import connection_manager
        
        # Test connection manager directly
        class MockWebSocket:
            def __init__(self):
                self.messages = []
            
            async def accept(self):
                pass
            
            async def send_text(self, message: str):
                self.messages.append(message)
        
        mock_ws = MockWebSocket()
        session_id = "integration-test"
        
        # Test connection
        await connection_manager.connect(mock_ws, session_id)
        
        # Test sending message
        await connection_manager.send_agent_response(
            session_id=session_id,
            agent_id="test-agent",
            content="Test response"
        )
        
        # Verify messages were sent
        assert len(mock_ws.messages) > 0
        
        # Cleanup
        await connection_manager.disconnect(mock_ws)


class TestRealtimeAPI:
    """Test real-time API endpoints"""
    
    def test_connection_stats_endpoint(self):
        """Test connection stats API endpoint"""
        
        client = TestClient(app)
        response = client.get("/api/realtime/connections/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "stats" in data
    
    def test_broadcast_endpoints(self):
        """Test broadcast API endpoints"""
        
        client = TestClient(app)
        
        # Test session broadcast
        response = client.post(
            "/api/realtime/broadcast/session/test-session",
            json={"type": "test", "message": "Hello"}
        )
        assert response.status_code == 200
        
        # Test agent status broadcast
        response = client.post(
            "/api/realtime/broadcast/agent-status",
            json={"agents": 4, "active": 2}
        )
        assert response.status_code == 200
        
        # Test task progress broadcast
        response = client.post(
            "/api/realtime/broadcast/task-progress",
            json={"task_id": "123", "progress": 50}
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])