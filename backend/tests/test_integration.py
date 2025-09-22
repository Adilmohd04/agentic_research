"""
Integration tests for complete user workflows and system interactions.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.core.memory import shared_memory
from src.core.performance import performance_manager
from src.core.error_handler import error_handler
from src.security.auth import AuthenticationService
from src.api.auth import router as auth_router
from src.api.performance import router as performance_router
from src.api.error_handling import router as error_router


@pytest.fixture
def app():
    """Create test FastAPI app with all routers."""
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(performance_router)
    app.include_router(error_router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    """Get authentication token for testing."""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123!"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


class TestEndToEndWorkflows:
    """Test complete end-to-end user workflows."""
    
    def test_user_authentication_workflow(self, client):
        """Test complete user authentication workflow."""
        # 1. Login
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123!"}
        )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        token = login_data["access_token"]
        
        # 2. Get user info
        user_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert user_response.status_code == 200
        user_data = user_response.json()
        assert user_data["username"] == "admin"
        
        # 3. Get permissions
        perms_response = client.get(
            "/api/auth/permissions",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert perms_response.status_code == 200
        perms_data = perms_response.json()
        assert "permissions" in perms_data
        
        # 4. Logout
        logout_response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert logout_response.status_code == 200
    
    def test_performance_monitoring_workflow(self, client, auth_token):
        """Test performance monitoring workflow."""
        if not auth_token:
            pytest.skip("Authentication required")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 1. Get performance metrics
        metrics_response = client.get("/api/performance/metrics", headers=headers)
        assert metrics_response.status_code == 200
        
        # 2. Get cache statistics
        cache_response = client.get("/api/performance/cache/stats", headers=headers)
        assert cache_response.status_code == 200
        
        # 3. Get system metrics
        system_response = client.get("/api/performance/system/metrics", headers=headers)
        assert system_response.status_code == 200
        
        # 4. Get dashboard data
        dashboard_response = client.get("/api/performance/dashboard", headers=headers)
        assert dashboard_response.status_code == 200
    
    def test_error_handling_workflow(self, client, auth_token):
        """Test error handling and monitoring workflow."""
        if not auth_token:
            pytest.skip("Authentication required")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 1. Get error statistics
        stats_response = client.get("/api/errors/statistics", headers=headers)
        assert stats_response.status_code == 200
        
        # 2. Get circuit breaker status
        cb_response = client.get("/api/errors/circuit-breakers", headers=headers)
        assert cb_response.status_code == 200
        
        # 3. Get degraded services
        degraded_response = client.get("/api/errors/degraded-services", headers=headers)
        assert degraded_response.status_code == 200
        
        # 4. Health check
        health_response = client.get("/api/errors/health")
        assert health_response.status_code == 200


class TestSystemIntegration:
    """Test integration between different system components."""
    
    @pytest.mark.asyncio
    async def test_memory_and_performance_integration(self):
        """Test integration between memory system and performance monitoring."""
        # Initialize systems
        await shared_memory._init_database()
        
        # Store some data in memory
        await shared_memory.store_conversation({
            "role": "user",
            "content": "Test message",
            "timestamp": "2024-01-01T00:00:00Z"
        })
        
        # Get memory stats
        stats = await shared_memory.get_memory_stats()
        assert "total_messages" in stats
        
        # Check performance metrics
        perf_summary = performance_manager.get_performance_summary()
        assert "cache_stats" in perf_summary
        assert "metrics_summary" in perf_summary
    
    @pytest.mark.asyncio
    async def test_error_handling_and_performance_integration(self):
        """Test integration between error handling and performance systems."""
        # Create a test error
        test_error = Exception("Test integration error")
        
        # Handle error
        error_context = await error_handler.handle_error(
            test_error,
            component="integration_test",
            user_id="test_user"
        )
        
        assert error_context.component == "integration_test"
        assert error_context.user_id == "test_user"
        
        # Check error statistics
        error_stats = error_handler.get_error_statistics()
        assert error_stats["total_errors"] > 0
        
        # Check performance impact
        perf_summary = performance_manager.get_performance_summary()
        assert "metrics_summary" in perf_summary
    
    def test_cache_and_metrics_integration(self):
        """Test integration between caching and metrics collection."""
        # Create a cache
        cache = performance_manager.create_cache("integration_test", max_size=10)
        
        # Use the cache
        cache.put("test_key", "test_value")
        value = cache.get("test_key")
        assert value == "test_value"
        
        # Check cache stats
        cache_stats = performance_manager.cache_manager.get_all_stats()
        assert "integration_test" in cache_stats
        assert cache_stats["integration_test"].hits > 0
        
        # Check metrics
        metrics_summary = performance_manager.metrics_collector.get_summary()
        assert "total_metrics" in metrics_summary


class TestConcurrentOperations:
    """Test system behavior under concurrent load."""
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self):
        """Test concurrent memory operations."""
        await shared_memory._init_database()
        
        async def store_messages(worker_id):
            for i in range(10):
                await shared_memory.store_conversation({
                    "role": "user",
                    "content": f"Message {i} from worker {worker_id}",
                    "timestamp": "2024-01-01T00:00:00Z"
                })
        
        # Run concurrent operations
        tasks = [store_messages(i) for i in range(5)]
        await asyncio.gather(*tasks)
        
        # Check results
        stats = await shared_memory.get_memory_stats()
        assert stats["total_messages"] >= 50
    
    def test_concurrent_cache_operations(self):
        """Test concurrent cache operations."""
        cache = performance_manager.create_cache("concurrent_test", max_size=100)
        
        import threading
        
        def cache_worker(worker_id):
            for i in range(20):
                key = f"worker_{worker_id}_key_{i}"
                value = f"worker_{worker_id}_value_{i}"
                cache.put(key, value)
                retrieved = cache.get(key)
                assert retrieved == value
        
        # Run concurrent workers
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Check cache stats
        stats = cache.get_stats()
        assert stats.size > 0
        assert stats.hits > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self):
        """Test concurrent error handling."""
        async def generate_errors(worker_id):
            for i in range(5):
                try:
                    raise ValueError(f"Test error {i} from worker {worker_id}")
                except Exception as e:
                    await error_handler.handle_error(
                        e,
                        component=f"worker_{worker_id}",
                        user_id=f"user_{worker_id}"
                    )
        
        # Run concurrent error generation
        tasks = [generate_errors(i) for i in range(3)]
        await asyncio.gather(*tasks)
        
        # Check error statistics
        stats = error_handler.get_error_statistics()
        assert stats["total_errors"] >= 15


class TestDataConsistency:
    """Test data consistency across system components."""
    
    @pytest.mark.asyncio
    async def test_memory_data_consistency(self):
        """Test memory system data consistency."""
        await shared_memory._init_database()
        
        # Store test data
        test_messages = [
            {"role": "user", "content": "Message 1", "timestamp": "2024-01-01T00:00:00Z"},
            {"role": "assistant", "content": "Response 1", "timestamp": "2024-01-01T00:01:00Z"},
            {"role": "user", "content": "Message 2", "timestamp": "2024-01-01T00:02:00Z"},
        ]
        
        for msg in test_messages:
            await shared_memory.store_conversation(msg)
        
        # Retrieve and verify
        history = await shared_memory.get_conversation_history(limit=10)
        assert len(history) >= len(test_messages)
        
        # Check stats consistency
        stats = await shared_memory.get_memory_stats()
        assert stats["total_messages"] >= len(test_messages)
    
    def test_cache_data_consistency(self):
        """Test cache data consistency."""
        cache = performance_manager.create_cache("consistency_test", max_size=50)
        
        # Store test data
        test_data = {f"key_{i}": f"value_{i}" for i in range(20)}
        
        for key, value in test_data.items():
            cache.put(key, value)
        
        # Verify all data
        for key, expected_value in test_data.items():
            actual_value = cache.get(key)
            assert actual_value == expected_value
        
        # Check stats consistency
        stats = cache.get_stats()
        assert stats.size == len(test_data)
        assert stats.hits == len(test_data)
    
    def test_error_log_consistency(self):
        """Test error log data consistency."""
        # Clear previous errors
        error_handler.clear_error_log()
        
        # Generate test errors
        test_errors = [
            ValueError("Test error 1"),
            RuntimeError("Test error 2"),
            KeyError("Test error 3")
        ]
        
        import asyncio
        
        async def handle_errors():
            for i, error in enumerate(test_errors):
                await error_handler.handle_error(
                    error,
                    component=f"test_component_{i}",
                    user_id=f"test_user_{i}"
                )
        
        asyncio.run(handle_errors())
        
        # Verify error log consistency
        stats = error_handler.get_error_statistics()
        assert stats["total_errors"] == len(test_errors)


class TestSystemRecovery:
    """Test system recovery and resilience."""
    
    @pytest.mark.asyncio
    async def test_memory_system_recovery(self):
        """Test memory system recovery after errors."""
        await shared_memory._init_database()
        
        # Store some data
        await shared_memory.store_conversation({
            "role": "user",
            "content": "Test before error",
            "timestamp": "2024-01-01T00:00:00Z"
        })
        
        # Simulate error and recovery
        try:
            # This should work fine
            await shared_memory.store_conversation({
                "role": "user",
                "content": "Test after recovery",
                "timestamp": "2024-01-01T00:01:00Z"
            })
        except Exception as e:
            pytest.fail(f"Memory system should recover gracefully: {e}")
        
        # Verify system is still functional
        stats = await shared_memory.get_memory_stats()
        assert stats["total_messages"] >= 2
    
    def test_cache_system_recovery(self):
        """Test cache system recovery after errors."""
        cache = performance_manager.create_cache("recovery_test", max_size=10)
        
        # Store some data
        cache.put("test_key", "test_value")
        
        # Simulate recovery scenario
        try:
            # Clear cache (simulating error recovery)
            cache.clear()
            
            # Should still be functional
            cache.put("recovery_key", "recovery_value")
            value = cache.get("recovery_key")
            assert value == "recovery_value"
            
        except Exception as e:
            pytest.fail(f"Cache system should recover gracefully: {e}")
    
    def test_error_handler_recovery(self):
        """Test error handler recovery."""
        # Clear error log
        error_handler.clear_error_log()
        
        # Generate errors
        import asyncio
        
        async def test_recovery():
            try:
                # Handle some errors
                await error_handler.handle_error(Exception("Test error 1"))
                await error_handler.handle_error(Exception("Test error 2"))
                
                # Clear log (simulating recovery)
                error_handler.clear_error_log()
                
                # Should still be functional
                await error_handler.handle_error(Exception("Test error after recovery"))
                
                stats = error_handler.get_error_statistics()
                assert stats["total_errors"] == 1
                
            except Exception as e:
                pytest.fail(f"Error handler should recover gracefully: {e}")
        
        asyncio.run(test_recovery())


if __name__ == "__main__":
    pytest.main([__file__])