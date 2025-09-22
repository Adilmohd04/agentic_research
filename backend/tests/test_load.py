"""
Load testing for concurrent user scenarios and system scalability.
"""

import pytest
import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
import statistics

from src.core.memory import shared_memory
from src.core.performance import performance_manager, LRUCache
from src.core.error_handler import error_handler
from src.security.auth import AuthenticationService


class TestLoadTesting:
    """Load testing for system scalability."""
    
    @pytest.mark.slow
    def test_cache_load_performance(self):
        """Test cache performance under high load."""
        cache = LRUCache(max_size=1000)
        
        def cache_worker(worker_id, operations=1000):
            """Worker function for cache operations."""
            start_time = time.time()
            
            for i in range(operations):
                key = f"worker_{worker_id}_key_{i}"
                value = f"worker_{worker_id}_value_{i}"
                
                # Write operation
                cache.put(key, value)
                
                # Read operation
                retrieved = cache.get(key)
                assert retrieved == value
                
                # Read random key (might miss)
                cache.get(f"random_key_{i}")
            
            end_time = time.time()
            return end_time - start_time
        
        # Run concurrent workers
        num_workers = 10
        operations_per_worker = 500
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(cache_worker, i, operations_per_worker)
                for i in range(num_workers)
            ]
            
            execution_times = []
            for future in as_completed(futures):
                execution_times.append(future.result())
        
        # Analyze performance
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        print(f"Cache Load Test Results:")
        print(f"Workers: {num_workers}")
        print(f"Operations per worker: {operations_per_worker}")
        print(f"Average execution time: {avg_time:.2f}s")
        print(f"Max execution time: {max_time:.2f}s")
        
        # Performance assertions
        assert avg_time < 5.0, f"Average execution time too high: {avg_time}s"
        assert max_time < 10.0, f"Max execution time too high: {max_time}s"
        
        # Check cache stats
        stats = cache.get_stats()
        print(f"Cache hit rate: {stats.hit_rate:.2%}")
        assert stats.hit_rate > 0.5, "Cache hit rate too low"
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_memory_system_load(self):
        """Test memory system under high concurrent load."""
        await shared_memory._init_database()
        
        async def memory_worker(worker_id, operations=100):
            """Worker function for memory operations."""
            start_time = time.time()
            
            for i in range(operations):
                # Store conversation
                await shared_memory.store_conversation({
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": f"Message {i} from worker {worker_id}",
                    "timestamp": f"2024-01-01T{i:02d}:00:00Z"
                })
                
                # Occasionally retrieve history
                if i % 10 == 0:
                    await shared_memory.get_conversation_history(limit=5)
            
            end_time = time.time()
            return end_time - start_time
        
        # Run concurrent workers
        num_workers = 5
        operations_per_worker = 50
        
        tasks = [
            memory_worker(i, operations_per_worker)
            for i in range(num_workers)
        ]
        
        execution_times = await asyncio.gather(*tasks)
        
        # Analyze performance
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        print(f"Memory System Load Test Results:")
        print(f"Workers: {num_workers}")
        print(f"Operations per worker: {operations_per_worker}")
        print(f"Average execution time: {avg_time:.2f}s")
        print(f"Max execution time: {max_time:.2f}s")
        
        # Performance assertions
        assert avg_time < 10.0, f"Average execution time too high: {avg_time}s"
        assert max_time < 20.0, f"Max execution time too high: {max_time}s"
        
        # Check memory stats
        stats = await shared_memory.get_memory_stats()
        expected_messages = num_workers * operations_per_worker
        assert stats["total_messages"] >= expected_messages * 0.9  # Allow some margin
    
    @pytest.mark.slow
    def test_metrics_collection_load(self):
        """Test metrics collection under high load."""
        collector = performance_manager.metrics_collector
        
        def metrics_worker(worker_id, operations=1000):
            """Worker function for metrics operations."""
            start_time = time.time()
            
            for i in range(operations):
                # Record different types of metrics
                collector.record_metric(f"test_metric_{worker_id}", float(i), {"worker": str(worker_id)})
                collector.increment_counter(f"counter_{worker_id}")
                collector.set_gauge(f"gauge_{worker_id}", float(i * 10))
                
                if i % 100 == 0:
                    collector.record_histogram(f"histogram_{worker_id}", float(i))
            
            end_time = time.time()
            return end_time - start_time
        
        # Run concurrent workers
        num_workers = 8
        operations_per_worker = 500
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(metrics_worker, i, operations_per_worker)
                for i in range(num_workers)
            ]
            
            execution_times = []
            for future in as_completed(futures):
                execution_times.append(future.result())
        
        # Analyze performance
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        print(f"Metrics Collection Load Test Results:")
        print(f"Workers: {num_workers}")
        print(f"Operations per worker: {operations_per_worker}")
        print(f"Average execution time: {avg_time:.2f}s")
        print(f"Max execution time: {max_time:.2f}s")
        
        # Performance assertions
        assert avg_time < 3.0, f"Average execution time too high: {avg_time}s"
        assert max_time < 6.0, f"Max execution time too high: {max_time}s"
        
        # Check metrics summary
        summary = collector.get_summary()
        assert summary["total_metrics"] > 0
        assert len(summary["counters"]) > 0
        assert len(summary["gauges"]) > 0
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_error_handling_load(self):
        """Test error handling system under high load."""
        # Clear previous errors
        error_handler.clear_error_log()
        
        async def error_worker(worker_id, operations=100):
            """Worker function for error generation."""
            start_time = time.time()
            
            for i in range(operations):
                error_types = [ValueError, RuntimeError, KeyError, TypeError]
                error_type = error_types[i % len(error_types)]
                
                try:
                    raise error_type(f"Test error {i} from worker {worker_id}")
                except Exception as e:
                    await error_handler.handle_error(
                        e,
                        component=f"load_test_worker_{worker_id}",
                        user_id=f"test_user_{worker_id}"
                    )
            
            end_time = time.time()
            return end_time - start_time
        
        # Run concurrent workers
        num_workers = 5
        operations_per_worker = 50
        
        tasks = [
            error_worker(i, operations_per_worker)
            for i in range(num_workers)
        ]
        
        execution_times = await asyncio.gather(*tasks)
        
        # Analyze performance
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        print(f"Error Handling Load Test Results:")
        print(f"Workers: {num_workers}")
        print(f"Operations per worker: {operations_per_worker}")
        print(f"Average execution time: {avg_time:.2f}s")
        print(f"Max execution time: {max_time:.2f}s")
        
        # Performance assertions
        assert avg_time < 5.0, f"Average execution time too high: {avg_time}s"
        assert max_time < 10.0, f"Max execution time too high: {max_time}s"
        
        # Check error statistics
        stats = error_handler.get_error_statistics()
        expected_errors = num_workers * operations_per_worker
        assert stats["total_errors"] >= expected_errors * 0.9  # Allow some margin
    
    @pytest.mark.slow
    def test_authentication_load(self):
        """Test authentication system under load."""
        auth_service = AuthenticationService()
        
        def auth_worker(worker_id, operations=100):
            """Worker function for authentication operations."""
            start_time = time.time()
            successful_auths = 0
            
            for i in range(operations):
                try:
                    # Try to authenticate (will mostly fail, but tests the system)
                    user = auth_service.user_manager.authenticate_user("admin", "admin123!")
                    if user:
                        successful_auths += 1
                        
                        # Create token
                        token = auth_service.token_manager.create_access_token(user)
                        
                        # Verify token
                        auth_service.token_manager.verify_token(token)
                        
                except Exception as e:
                    # Expected for invalid credentials
                    pass
            
            end_time = time.time()
            return end_time - start_time, successful_auths
        
        # Run concurrent workers
        num_workers = 10
        operations_per_worker = 50
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(auth_worker, i, operations_per_worker)
                for i in range(num_workers)
            ]
            
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        
        execution_times = [r[0] for r in results]
        successful_auths = [r[1] for r in results]
        
        # Analyze performance
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        total_successful = sum(successful_auths)
        
        print(f"Authentication Load Test Results:")
        print(f"Workers: {num_workers}")
        print(f"Operations per worker: {operations_per_worker}")
        print(f"Average execution time: {avg_time:.2f}s")
        print(f"Max execution time: {max_time:.2f}s")
        print(f"Total successful authentications: {total_successful}")
        
        # Performance assertions
        assert avg_time < 3.0, f"Average execution time too high: {avg_time}s"
        assert max_time < 6.0, f"Max execution time too high: {max_time}s"
        assert total_successful > 0, "No successful authentications"


class TestStressScenarios:
    """Stress testing for extreme scenarios."""
    
    @pytest.mark.slow
    def test_memory_pressure_scenario(self):
        """Test system behavior under memory pressure."""
        # Create multiple large caches
        caches = []
        for i in range(5):
            cache = performance_manager.create_cache(f"stress_cache_{i}", max_size=1000)
            caches.append(cache)
        
        # Fill caches with data
        for cache_idx, cache in enumerate(caches):
            for i in range(1000):
                key = f"stress_key_{cache_idx}_{i}"
                value = f"stress_value_{cache_idx}_{i}" * 100  # Large values
                cache.put(key, value)
        
        # Verify system is still responsive
        test_cache = caches[0]
        test_cache.put("test_key", "test_value")
        assert test_cache.get("test_key") == "test_value"
        
        # Check cache stats
        for cache in caches:
            stats = cache.get_stats()
            assert stats.size > 0
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_rapid_error_generation(self):
        """Test system behavior with rapid error generation."""
        error_handler.clear_error_log()
        
        # Generate many errors rapidly
        num_errors = 1000
        
        async def rapid_error_generation():
            for i in range(num_errors):
                try:
                    if i % 4 == 0:
                        raise ValueError(f"Rapid error {i}")
                    elif i % 4 == 1:
                        raise RuntimeError(f"Rapid error {i}")
                    elif i % 4 == 2:
                        raise KeyError(f"Rapid error {i}")
                    else:
                        raise TypeError(f"Rapid error {i}")
                except Exception as e:
                    await error_handler.handle_error(e, component="stress_test")
        
        start_time = time.time()
        await rapid_error_generation()
        end_time = time.time()
        
        execution_time = end_time - start_time
        print(f"Rapid error generation: {num_errors} errors in {execution_time:.2f}s")
        print(f"Rate: {num_errors/execution_time:.2f} errors/second")
        
        # Verify system handled all errors
        stats = error_handler.get_error_statistics()
        assert stats["total_errors"] >= num_errors * 0.95  # Allow small margin
        
        # System should still be responsive
        await error_handler.handle_error(Exception("Test after stress"), component="post_stress")
    
    @pytest.mark.slow
    def test_connection_pool_stress(self):
        """Test connection pool under stress."""
        def mock_connection_factory():
            return f"connection_{time.time()}"
        
        pool = performance_manager.create_connection_pool(
            "stress_pool", 
            mock_connection_factory, 
            max_size=20
        )
        
        def pool_worker(worker_id, operations=200):
            """Worker that rapidly acquires and releases connections."""
            for i in range(operations):
                try:
                    conn = pool.acquire()
                    # Simulate work
                    time.sleep(0.001)
                    pool.release(conn)
                except Exception as e:
                    # Pool exhaustion is expected under stress
                    pass
        
        # Run many concurrent workers
        num_workers = 15
        operations_per_worker = 100
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(pool_worker, i, operations_per_worker)
                for i in range(num_workers)
            ]
            
            # Wait for completion
            for future in as_completed(futures):
                future.result()
        
        # Check pool stats
        stats = pool.get_stats()
        print(f"Connection pool stats after stress test: {stats}")
        assert stats["created_count"] > 0
        assert stats["created_count"] <= pool.max_size * 2  # Allow some overhead


class TestPerformanceBenchmarks:
    """Performance benchmarks for system components."""
    
    def test_cache_performance_benchmark(self):
        """Benchmark cache performance."""
        cache = LRUCache(max_size=10000)
        
        # Benchmark write performance
        start_time = time.time()
        for i in range(10000):
            cache.put(f"key_{i}", f"value_{i}")
        write_time = time.time() - start_time
        
        # Benchmark read performance
        start_time = time.time()
        for i in range(10000):
            cache.get(f"key_{i}")
        read_time = time.time() - start_time
        
        print(f"Cache Performance Benchmark:")
        print(f"Write time for 10k items: {write_time:.3f}s ({10000/write_time:.0f} ops/sec)")
        print(f"Read time for 10k items: {read_time:.3f}s ({10000/read_time:.0f} ops/sec)")
        
        # Performance assertions
        assert write_time < 1.0, f"Write performance too slow: {write_time}s"
        assert read_time < 0.5, f"Read performance too slow: {read_time}s"
    
    @pytest.mark.asyncio
    async def test_memory_performance_benchmark(self):
        """Benchmark memory system performance."""
        await shared_memory._init_database()
        
        # Benchmark write performance
        num_messages = 1000
        start_time = time.time()
        
        for i in range(num_messages):
            await shared_memory.store_conversation({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Benchmark message {i}",
                "timestamp": f"2024-01-01T{i:04d}:00:00Z"
            })
        
        write_time = time.time() - start_time
        
        # Benchmark read performance
        start_time = time.time()
        for i in range(100):  # Sample reads
            await shared_memory.get_conversation_history(limit=10)
        read_time = time.time() - start_time
        
        print(f"Memory System Performance Benchmark:")
        print(f"Write time for {num_messages} messages: {write_time:.3f}s ({num_messages/write_time:.0f} ops/sec)")
        print(f"Read time for 100 queries: {read_time:.3f}s ({100/read_time:.0f} ops/sec)")
        
        # Performance assertions
        assert write_time < 10.0, f"Write performance too slow: {write_time}s"
        assert read_time < 2.0, f"Read performance too slow: {read_time}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])