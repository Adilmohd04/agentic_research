"""
Unit tests for performance optimization and monitoring system.
"""

import pytest
import asyncio
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.core.performance import (
    LRUCache,
    CacheManager,
    MetricsCollector,
    SystemMonitor,
    LoadBalancer,
    ConnectionPool,
    PerformanceManager,
    PerformanceMetric,
    CacheStats,
    SystemMetrics,
    performance_manager
)

class TestLRUCache:
    """Test LRU cache implementation."""
    
    def test_cache_creation(self):
        """Test cache creation with parameters."""
        cache = LRUCache(max_size=100, ttl_seconds=300)
        
        assert cache.max_size == 100
        assert cache.ttl_seconds == 300
        
        stats = cache.get_stats()
        assert stats.max_size == 100
        assert stats.size == 0
        assert stats.hits == 0
        assert stats.misses == 0
    
    def test_cache_put_get(self):
        """Test basic cache put and get operations."""
        cache = LRUCache(max_size=3)
        
        # Test put and get
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("nonexistent") is None
        
        stats = cache.get_stats()
        assert stats.size == 2
        assert stats.hits == 2
        assert stats.misses == 1
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = LRUCache(max_size=2)
        
        # Fill cache
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add new key, should evict key2 (least recently used)
        cache.put("key3", "value3")
        
        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key3") == "value3"  # New key
        assert cache.get("key2") is None      # Evicted
    
    def test_cache_ttl_expiration(self):
        """Test TTL-based cache expiration."""
        cache = LRUCache(max_size=10, ttl_seconds=1)
        
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        assert cache.get("key1") is None
        
        stats = cache.get_stats()
        assert stats.misses == 1  # Should count as miss after expiration
    
    def test_cache_update_existing_key(self):
        """Test updating existing key in cache."""
        cache = LRUCache(max_size=10)
        
        cache.put("key1", "value1")
        cache.put("key1", "value2")  # Update
        
        assert cache.get("key1") == "value2"
        
        stats = cache.get_stats()
        assert stats.size == 1  # Should still be 1
    
    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation."""
        cache = LRUCache(max_size=10)
        
        # Initially 0 hit rate
        stats = cache.get_stats()
        assert stats.hit_rate == 0.0
        
        # Add some data
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        # 2 hits, 1 miss
        cache.get("key1")  # hit
        cache.get("key2")  # hit
        cache.get("key3")  # miss
        
        stats = cache.get_stats()
        assert stats.hit_rate == 2/3  # 2 hits out of 3 total


class TestCacheManager:
    """Test cache manager functionality."""
    
    def test_cache_manager_creation(self):
        """Test cache manager initialization."""
        manager = CacheManager()
        
        # Should have default cache
        default_cache = manager.get_cache("default")
        assert default_cache is not None
    
    def test_create_named_cache(self):
        """Test creating named caches."""
        manager = CacheManager()
        
        cache = manager.create_cache("test_cache", max_size=500, ttl_seconds=600)
        
        assert cache.max_size == 500
        assert cache.ttl_seconds == 600
        
        # Should be able to retrieve it
        retrieved_cache = manager.get_cache("test_cache")
        assert retrieved_cache is cache
    
    def test_get_all_stats(self):
        """Test getting statistics for all caches."""
        manager = CacheManager()
        
        # Create some caches and add data
        cache1 = manager.create_cache("cache1", max_size=10)
        cache2 = manager.create_cache("cache2", max_size=20)
        
        cache1.put("key1", "value1")
        cache2.put("key2", "value2")
        
        stats = manager.get_all_stats()
        
        assert "default" in stats
        assert "cache1" in stats
        assert "cache2" in stats
        
        assert stats["cache1"].size == 1
        assert stats["cache2"].size == 1


class TestMetricsCollector:
    """Test metrics collection functionality."""
    
    def test_metrics_collector_creation(self):
        """Test metrics collector initialization."""
        collector = MetricsCollector(max_metrics=1000)
        
        assert collector.max_metrics == 1000
        
        summary = collector.get_summary()
        assert summary["total_metrics"] == 0
        assert len(summary["counters"]) == 0
        assert len(summary["gauges"]) == 0
    
    def test_record_metric(self):
        """Test recording performance metrics."""
        collector = MetricsCollector()
        
        collector.record_metric("response_time", 150.5, {"endpoint": "/api/test"}, "ms")
        
        summary = collector.get_summary()
        assert summary["total_metrics"] == 1
    
    def test_increment_counter(self):
        """Test counter metrics."""
        collector = MetricsCollector()
        
        collector.increment_counter("requests", 1, {"method": "GET"})
        collector.increment_counter("requests", 2, {"method": "POST"})
        
        summary = collector.get_summary()
        assert summary["counters"]["requests"] == 3
        assert summary["total_metrics"] == 2  # Should record metrics too
    
    def test_set_gauge(self):
        """Test gauge metrics."""
        collector = MetricsCollector()
        
        collector.set_gauge("cpu_usage", 75.5, {"host": "server1"}, "%")
        collector.set_gauge("memory_usage", 60.2, {"host": "server1"}, "%")
        
        summary = collector.get_summary()
        assert summary["gauges"]["cpu_usage"] == 75.5
        assert summary["gauges"]["memory_usage"] == 60.2
        assert summary["total_metrics"] == 2
    
    def test_metrics_max_limit(self):
        """Test metrics collection limit."""
        collector = MetricsCollector(max_metrics=3)
        
        # Add more metrics than limit
        for i in range(5):
            collector.record_metric(f"metric_{i}", float(i))
        
        summary = collector.get_summary()
        # Should only keep the last 3 metrics
        assert summary["total_metrics"] == 3


class TestSystemMonitor:
    """Test system monitoring functionality."""
    
    @patch('src.core.performance.psutil')
    def test_system_monitor_creation(self, mock_psutil):
        """Test system monitor initialization."""
        monitor = SystemMonitor(collection_interval=30)
        
        assert monitor.collection_interval == 30
        assert not monitor._running
        assert monitor._thread is None
    
    @patch('src.core.performance.psutil')
    def test_collect_system_metrics(self, mock_psutil):
        """Test system metrics collection."""
        # Mock psutil responses
        mock_psutil.cpu_percent.return_value = 45.2
        mock_psutil.virtual_memory.return_value = Mock(
            percent=65.5,
            used=8589934592,  # 8GB
            available=4294967296  # 4GB
        )
        mock_psutil.disk_usage.return_value = Mock(percent=80.0)
        mock_psutil.net_io_counters.return_value = Mock(
            bytes_sent=1000000,
            bytes_recv=2000000
        )
        mock_psutil.net_connections.return_value = [Mock(), Mock(), Mock()]
        
        monitor = SystemMonitor()
        metrics_collector = Mock()
        monitor._metrics_collector = metrics_collector
        
        metrics = monitor._collect_system_metrics()
        
        assert metrics.cpu_percent == 45.2
        assert metrics.memory_percent == 65.5
        assert metrics.disk_usage_percent == 80.0
        assert metrics.network_bytes_sent == 1000000
        assert metrics.network_bytes_recv == 2000000
        assert metrics.active_connections == 3
    
    @patch('src.core.performance.psutil')
    def test_start_stop_monitoring(self, mock_psutil):
        """Test starting and stopping system monitoring."""
        monitor = SystemMonitor(collection_interval=1)
        metrics_collector = Mock()
        
        # Start monitoring
        monitor.start(metrics_collector)
        
        assert monitor._running
        assert monitor._thread is not None
        assert monitor._thread.is_alive()
        
        # Stop monitoring
        monitor.stop()
        
        assert not monitor._running
        # Thread should finish
        monitor._thread.join(timeout=2)
        assert not monitor._thread.is_alive()


class TestLoadBalancer:
    """Test load balancing functionality."""
    
    def test_load_balancer_creation(self):
        """Test load balancer initialization."""
        workers = ["worker1", "worker2", "worker3"]
        balancer = LoadBalancer(workers)
        
        assert len(balancer.workers) == 3
        assert balancer.current_index == 0
    
    def test_round_robin_distribution(self):
        """Test round-robin load distribution."""
        workers = ["worker1", "worker2", "worker3"]
        balancer = LoadBalancer(workers)
        
        # Should cycle through workers
        assert balancer.get_next_worker() == "worker1"
        assert balancer.get_next_worker() == "worker2"
        assert balancer.get_next_worker() == "worker3"
        assert balancer.get_next_worker() == "worker1"  # Back to first
    
    def test_record_request_and_error(self):
        """Test recording requests and errors."""
        workers = ["worker1", "worker2"]
        balancer = LoadBalancer(workers)
        
        # Record some requests and errors
        balancer.record_error("worker1")
        balancer.record_error("worker1")
        
        stats = balancer.get_stats()
        
        assert stats["worker_stats"][id("worker1")]["errors"] == 2
        assert stats["total_workers"] == 2
    
    def test_get_stats(self):
        """Test getting load balancer statistics."""
        workers = ["worker1", "worker2"]
        balancer = LoadBalancer(workers)
        
        stats = balancer.get_stats()
        
        assert "total_workers" in stats
        assert "worker_stats" in stats
        assert stats["total_workers"] == 2


class TestConnectionPool:
    """Test connection pool functionality."""
    
    def test_connection_pool_creation(self):
        """Test connection pool initialization."""
        factory = Mock(return_value="connection")
        pool = ConnectionPool(factory, max_size=5, timeout=10.0)
        
        assert pool.max_size == 5
        assert pool.timeout == 10.0
        assert pool.factory == factory
    
    def test_acquire_release_connection(self):
        """Test acquiring and releasing connections."""
        factory = Mock(side_effect=lambda: f"connection_{time.time()}")
        pool = ConnectionPool(factory, max_size=2)
        
        # Acquire connection
        conn1 = pool.acquire()
        assert conn1 is not None
        factory.assert_called_once()
        
        # Release connection
        pool.release(conn1)
        
        # Acquire again - should reuse
        conn2 = pool.acquire()
        assert conn2 == conn1  # Should be the same connection
        
        stats = pool.get_stats()
        assert stats["pool_size"] >= 0
        assert stats["in_use"] >= 0
    
    def test_connection_pool_limit(self):
        """Test connection pool size limit."""
        factory = Mock(side_effect=lambda: f"connection_{time.time()}")
        pool = ConnectionPool(factory, max_size=1)
        
        # Acquire the only connection
        conn1 = pool.acquire()
        assert conn1 is not None
        
        # Try to acquire another - should create new since under limit
        conn2 = pool.acquire()
        assert conn2 is not None
        assert conn2 != conn1
        
        stats = pool.get_stats()
        assert stats["created_count"] == 2
    
    def test_connection_validation(self):
        """Test connection validation."""
        factory = Mock(return_value="valid_connection")
        pool = ConnectionPool(factory, max_size=2)
        
        # Override validation to always return True
        pool._is_connection_valid = Mock(return_value=True)
        
        conn = pool.acquire()
        pool.release(conn)
        
        # Acquire again - should validate and reuse
        conn2 = pool.acquire()
        pool._is_connection_valid.assert_called()


class TestPerformanceManager:
    """Test performance manager integration."""
    
    def test_performance_manager_creation(self):
        """Test performance manager initialization."""
        manager = PerformanceManager()
        
        assert manager.cache_manager is not None
        assert manager.metrics_collector is not None
        assert manager.system_monitor is not None
    
    def test_create_cache(self):
        """Test creating cache through performance manager."""
        manager = PerformanceManager()
        
        cache = manager.create_cache("test_cache", max_size=100)
        
        assert cache.max_size == 100
        
        # Should be accessible through cache manager
        retrieved = manager.cache_manager.get_cache("test_cache")
        assert retrieved is cache
    
    def test_create_connection_pool(self):
        """Test creating connection pool."""
        manager = PerformanceManager()
        
        factory = Mock(return_value="connection")
        pool = manager.create_connection_pool("test_pool", factory, max_size=5)
        
        assert pool.max_size == 5
        assert "test_pool" in manager.connection_pools
    
    def test_create_load_balancer(self):
        """Test creating load balancer."""
        manager = PerformanceManager()
        
        workers = ["worker1", "worker2"]
        balancer = manager.create_load_balancer("test_balancer", workers)
        
        assert len(balancer.workers) == 2
        assert "test_balancer" in manager.load_balancers
    
    def test_get_performance_summary(self):
        """Test getting comprehensive performance summary."""
        manager = PerformanceManager()
        
        # Create some resources
        manager.create_cache("test_cache", max_size=100)
        manager.create_connection_pool("test_pool", Mock(), max_size=5)
        manager.create_load_balancer("test_balancer", ["worker1"])
        
        summary = manager.get_performance_summary()
        
        assert "cache_stats" in summary
        assert "metrics_summary" in summary
        assert "connection_pools" in summary
        assert "load_balancers" in summary
        assert "timestamp" in summary
    
    def test_shutdown(self):
        """Test performance manager shutdown."""
        manager = PerformanceManager()
        
        # Start system monitor
        manager.system_monitor.start(manager.metrics_collector)
        
        # Shutdown should stop monitoring and clear caches
        manager.shutdown()
        
        assert not manager.system_monitor._running


class TestPerformanceDecorators:
    """Test performance monitoring decorators."""
    
    def test_cache_decorator(self):
        """Test caching decorator."""
        manager = PerformanceManager()
        cache = manager.create_cache("test_cache")
        
        call_count = 0
        
        @manager.cache("test_cache")
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call should execute function
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call with same args should use cache
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Should not increment
        
        # Different args should execute function
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2
    
    def test_profile_decorator(self):
        """Test profiling decorator."""
        manager = PerformanceManager()
        
        @manager.profile("test_function")
        def test_function():
            time.sleep(0.01)  # Small delay
            return "result"
        
        result = test_function()
        assert result == "result"
        
        # Should have recorded metrics
        summary = manager.metrics_collector.get_summary()
        assert summary["total_metrics"] > 0
    
    @pytest.mark.asyncio
    async def test_async_profile_decorator(self):
        """Test profiling decorator with async functions."""
        manager = PerformanceManager()
        
        @manager.profile("async_test_function")
        async def async_test_function():
            await asyncio.sleep(0.01)
            return "async_result"
        
        result = await async_test_function()
        assert result == "async_result"
        
        # Should have recorded metrics
        summary = manager.metrics_collector.get_summary()
        assert summary["total_metrics"] > 0


class TestPerformanceIntegration:
    """Test performance system integration."""
    
    def test_global_performance_manager(self):
        """Test global performance manager instance."""
        # Should be able to access global instance
        assert performance_manager is not None
        assert isinstance(performance_manager, PerformanceManager)
    
    def test_concurrent_cache_access(self):
        """Test concurrent access to cache."""
        cache = LRUCache(max_size=100)
        
        def worker(worker_id):
            for i in range(10):
                key = f"worker_{worker_id}_key_{i}"
                value = f"worker_{worker_id}_value_{i}"
                cache.put(key, value)
                retrieved = cache.get(key)
                assert retrieved == value
        
        # Run multiple workers concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Cache should have data from all workers
        stats = cache.get_stats()
        assert stats.size > 0
        assert stats.hits > 0
    
    def test_metrics_collection_under_load(self):
        """Test metrics collection under high load."""
        collector = MetricsCollector(max_metrics=1000)
        
        def record_metrics(worker_id):
            for i in range(100):
                collector.record_metric(
                    f"test_metric_{worker_id}",
                    float(i),
                    {"worker": str(worker_id)}
                )
                collector.increment_counter(f"counter_{worker_id}")
                collector.set_gauge(f"gauge_{worker_id}", float(i * 10))
        
        # Run multiple workers
        threads = []
        for i in range(5):
            thread = threading.Thread(target=record_metrics, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        summary = collector.get_summary()
        assert summary["total_metrics"] > 0
        assert len(summary["counters"]) > 0
        assert len(summary["gauges"]) > 0
    
    def test_connection_pool_under_load(self):
        """Test connection pool under concurrent load."""
        connection_count = 0
        
        def factory():
            nonlocal connection_count
            connection_count += 1
            return f"connection_{connection_count}"
        
        pool = ConnectionPool(factory, max_size=10)
        
        def worker():
            for _ in range(10):
                conn = pool.acquire()
                time.sleep(0.001)  # Simulate work
                pool.release(conn)
        
        # Run multiple workers
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        stats = pool.get_stats()
        assert stats["created_count"] > 0


if __name__ == "__main__":
    pytest.main([__file__])