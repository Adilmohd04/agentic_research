"""
Performance Optimization and Monitoring System

This module provides comprehensive performance optimization including caching layers,
metrics collection, load balancing, and performance monitoring for the Agentic Research Copilot.
"""

import asyncio
import time
import logging
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from functools import wraps
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor
import weakref

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    unit: str = "ms"

@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    size: int = 0
    max_size: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    timestamp: datetime

class LRUCache:
    """Thread-safe LRU cache implementation."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: Optional[int] = None):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Any] = {}
        self._access_order: deque = deque()
        self._timestamps: Dict[str, datetime] = {}
        self._lock = threading.RLock()
        self._stats = CacheStats(max_size=max_size)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return None
            
            # Check TTL
            if self.ttl_seconds and key in self._timestamps:
                if datetime.utcnow() - self._timestamps[key] > timedelta(seconds=self.ttl_seconds):
                    self._remove_key(key)
                    self._stats.misses += 1
                    return None
            
            # Move to end (most recently used)
            self._access_order.remove(key)
            self._access_order.append(key)
            
            self._stats.hits += 1
            return self._cache[key]
    
    def put(self, key: str, value: Any):
        """Put value in cache."""
        with self._lock:
            # If key exists, update
            if key in self._cache:
                self._cache[key] = value
                self._timestamps[key] = datetime.utcnow()
                self._access_order.remove(key)
                self._access_order.append(key)
                return
            
            # If at capacity, evict LRU
            while len(self._cache) >= self.max_size:
                if self._access_order:
                    lru_key = self._access_order.popleft()
                    self._remove_key(lru_key)
            
            # Add new entry
            self._cache[key] = value
            self._timestamps[key] = datetime.utcnow()
            self._access_order.append(key)
            self._stats.size += 1
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._timestamps.clear()
            self._stats.size = 0
    
    def _remove_key(self, key: str):
        """Remove key from cache."""
        if key in self._cache:
            del self._cache[key]
            if key in self._timestamps:
                del self._timestamps[key]
            if key in self._access_order:
                self._access_order.remove(key)
            self._stats.size -= 1
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                size=self._stats.size,
                max_size=self._stats.max_size
            )

class CacheManager:
    """Manages multiple cache instances."""
    
    def __init__(self):
        self._caches: Dict[str, LRUCache] = {}
        self._default_cache = LRUCache(max_size=1000, ttl_seconds=3600)
    
    def create_cache(self, name: str, max_size: int = 1000, ttl_seconds: Optional[int] = None) -> LRUCache:
        """Create a named cache instance."""
        cache = LRUCache(max_size=max_size, ttl_seconds=ttl_seconds)
        self._caches[name] = cache
        logger.info(f"Created cache '{name}' with max_size={max_size}, ttl={ttl_seconds}")
        return cache
    
    def get_cache(self, name: str) -> LRUCache:
        """Get cache by name, create if doesn't exist."""
        if name == "default":
            return self._default_cache
        if name not in self._caches:
            return self.create_cache(name)
        return self._caches[name]
    
    def get_all_stats(self) -> Dict[str, CacheStats]:
        """Get statistics for all caches."""
        stats = {"default": self._default_cache.get_stats()}
        for name, cache in self._caches.items():
            stats[name] = cache.get_stats()
        return stats
    
    def clear_all(self):
        """Clear all caches."""
        self._default_cache.clear()
        for cache in self._caches.values():
            cache.clear()
        logger.info("All caches cleared")

class MetricsCollector:
    """Collects and stores performance metrics."""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self._metrics: deque = deque(maxlen=max_metrics)
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, unit: str = "ms"):
        """Record a performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            unit=unit
        )
        
        with self._lock:
            self._metrics.append(metric)
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        with self._lock:
            self._counters[name] += value
        self.record_metric(f"{name}_total", self._counters[name], tags, "count")
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, unit: str = ""):
        """Set a gauge metric."""
        with self._lock:
            self._gauges[name] = value
        self.record_metric(name, value, tags, unit)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram value."""
        with self._lock:
            self._histograms[name].append(value)
            # Keep only recent 1000 values
            if len(self._histograms[name]) > 1000:
                self._histograms[name] = self._histograms[name][-1000:]
        
        self.record_metric(f"{name}_histogram", value, tags)
    
    def get_metrics(self, name_filter: Optional[str] = None, since: Optional[datetime] = None) -> List[PerformanceMetric]:
        """Get metrics with optional filtering."""
        with self._lock:
            metrics = list(self._metrics)
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        if name_filter:
            metrics = [m for m in metrics if name_filter in m.name]
        
        return metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        with self._lock:
            return {
                "total_metrics": len(self._metrics),
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histogram_counts": {name: len(values) for name, values in self._histograms.items()}
            }

class SystemMonitor:
    """Monitors system resource usage."""
    
    def __init__(self, collection_interval: int = 60):
        self.collection_interval = collection_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._metrics_collector: Optional[MetricsCollector] = None
        self._last_network_stats = None
    
    def start(self, metrics_collector: MetricsCollector):
        """Start system monitoring."""
        if self._running:
            return
        
        self._metrics_collector = metrics_collector
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("System monitoring started")
    
    def stop(self):
        """Stop system monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("System monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                metrics = self._collect_system_metrics()
                self._record_metrics(metrics)
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_available_mb = memory.available / (1024 * 1024)
        
        # Disk usage
        disk_usage = psutil.disk_usage('/')
        disk_usage_percent = disk_usage.percent
        
        # Network stats
        network = psutil.net_io_counters()
        network_bytes_sent = network.bytes_sent
        network_bytes_recv = network.bytes_recv
        
        # Connection count
        try:
            connections = len(psutil.net_connections())
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            connections = 0
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_usage_percent=disk_usage_percent,
            network_bytes_sent=network_bytes_sent,
            network_bytes_recv=network_bytes_recv,
            active_connections=connections,
            timestamp=datetime.utcnow()
        )
    
    def _record_metrics(self, metrics: SystemMetrics):
        """Record system metrics."""
        if not self._metrics_collector:
            return
        
        self._metrics_collector.set_gauge("system.cpu_percent", metrics.cpu_percent, unit="%")
        self._metrics_collector.set_gauge("system.memory_percent", metrics.memory_percent, unit="%")
        self._metrics_collector.set_gauge("system.memory_used_mb", metrics.memory_used_mb, unit="MB")
        self._metrics_collector.set_gauge("system.memory_available_mb", metrics.memory_available_mb, unit="MB")
        self._metrics_collector.set_gauge("system.disk_usage_percent", metrics.disk_usage_percent, unit="%")
        self._metrics_collector.set_gauge("system.network_bytes_sent", metrics.network_bytes_sent, unit="bytes")
        self._metrics_collector.set_gauge("system.network_bytes_recv", metrics.network_bytes_recv, unit="bytes")
        self._metrics_collector.set_gauge("system.active_connections", metrics.active_connections, unit="connections")

class LoadBalancer:
    """Simple round-robin load balancer for distributing requests."""
    
    def __init__(self, workers: List[Any]):
        self.workers = workers
        self.current_index = 0
        self._lock = threading.Lock()
        self.worker_stats = {id(worker): {"requests": 0, "errors": 0} for worker in workers}
    
    def get_next_worker(self) -> Any:
        """Get next worker using round-robin algorithm."""
        with self._lock:
            worker = self.workers[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.workers)
            self.worker_stats[id(worker)]["requests"] += 1
            return worker
    
    def record_error(self, worker: Any):
        """Record an error for a worker."""
        with self._lock:
            self.worker_stats[id(worker)]["errors"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics."""
        with self._lock:
            return {
                "total_workers": len(self.workers),
                "worker_stats": dict(self.worker_stats)
            }

class ConnectionPool:
    """Generic connection pool for managing resources."""
    
    def __init__(self, factory: Callable, max_size: int = 10, timeout: float = 30.0):
        self.factory = factory
        self.max_size = max_size
        self.timeout = timeout
        self._pool: deque = deque()
        self._in_use: weakref.WeakSet = weakref.WeakSet()
        self._created_count = 0
        self._lock = threading.Lock()
    
    def acquire(self) -> Any:
        """Acquire a connection from the pool."""
        with self._lock:
            # Try to get from pool
            while self._pool:
                conn = self._pool.popleft()
                if self._is_connection_valid(conn):
                    self._in_use.add(conn)
                    return conn
            
            # Create new connection if under limit
            if self._created_count < self.max_size:
                conn = self.factory()
                self._created_count += 1
                self._in_use.add(conn)
                return conn
            
            # Pool exhausted
            raise RuntimeError("Connection pool exhausted")
    
    def release(self, conn: Any):
        """Release a connection back to the pool."""
        with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)
                if self._is_connection_valid(conn):
                    self._pool.append(conn)
    
    def _is_connection_valid(self, conn: Any) -> bool:
        """Check if connection is still valid."""
        # Override in subclasses for specific validation
        return True
    
    def get_stats(self) -> Dict[str, int]:
        """Get connection pool statistics."""
        with self._lock:
            return {
                "pool_size": len(self._pool),
                "in_use": len(self._in_use),
                "created_count": self._created_count,
                "max_size": self.max_size
            }

class TimingContext:
    """Context manager for timing code execution."""
    
    def __init__(self, name: str, metrics_collector: MetricsCollector, tags: Optional[Dict[str, str]] = None):
        self.name = name
        self.metrics_collector = metrics_collector
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (time.perf_counter() - self.start_time) * 1000  # Convert to ms
            self.metrics_collector.record_histogram(f"{self.name}.duration", duration, self.tags)

class PerformanceProfiler:
    """Performance profiler for function execution timing."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
    
    def time_block(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing code blocks."""
        return TimingContext(name, self.metrics_collector, tags)
    
    def profile(self, name: Optional[str] = None, tags: Optional[Dict[str, str]] = None):
        """Decorator for profiling function execution."""
        def decorator(func: Callable):
            profile_name = name or f"{func.__module__}.{func.__name__}"
            
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    start_time = time.perf_counter()
                    try:
                        self.metrics_collector.increment_counter(f"{profile_name}.calls", tags=tags)
                        result = await func(*args, **kwargs)
                        return result
                    finally:
                        duration = (time.perf_counter() - start_time) * 1000  # Convert to ms
                        self.metrics_collector.record_histogram(f"{profile_name}.duration", duration, tags)
                
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    start_time = time.perf_counter()
                    try:
                        self.metrics_collector.increment_counter(f"{profile_name}.calls", tags=tags)
                        result = func(*args, **kwargs)
                        return result
                    finally:
                        duration = (time.perf_counter() - start_time) * 1000  # Convert to ms
                        self.metrics_collector.record_histogram(f"{profile_name}.duration", duration, tags)
                
                return sync_wrapper
        
        return decorator

class PerformanceManager:
    """Main performance management system."""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.metrics_collector = MetricsCollector()
        self.system_monitor = SystemMonitor()
        self.profiler = PerformanceProfiler(self.metrics_collector)
        self.connection_pools: Dict[str, ConnectionPool] = {}
        self.load_balancers: Dict[str, LoadBalancer] = {}
    
    def create_cache(self, name: str, max_size: int = 1000, ttl_seconds: Optional[int] = None) -> LRUCache:
        """Create a named cache."""
        return self.cache_manager.create_cache(name, max_size, ttl_seconds)
    
    def create_connection_pool(self, name: str, factory: Callable, max_size: int = 10) -> ConnectionPool:
        """Create a named connection pool."""
        pool = ConnectionPool(factory, max_size)
        self.connection_pools[name] = pool
        logger.info(f"Created connection pool '{name}' with max_size={max_size}")
        return pool
    
    def create_load_balancer(self, name: str, workers: List[Any]) -> LoadBalancer:
        """Create a named load balancer."""
        balancer = LoadBalancer(workers)
        self.load_balancers[name] = balancer
        logger.info(f"Created load balancer '{name}' with {len(workers)} workers")
        return balancer
    
    def cache(self, cache_name: str = "default", ttl_seconds: Optional[int] = None):
        """Decorator for caching function results."""
        def decorator(func: Callable):
            cache_instance = self.cache_manager.get_cache(cache_name)
            
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    # Create cache key from function name and arguments
                    key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
                    cache_key = hashlib.md5(key_data.encode()).hexdigest()
                    
                    # Try to get from cache
                    result = cache_instance.get(cache_key)
                    if result is not None:
                        return result
                    
                    # Execute function and cache result
                    result = await func(*args, **kwargs)
                    cache_instance.put(cache_key, result)
                    return result
                
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    # Create cache key from function name and arguments
                    key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
                    cache_key = hashlib.md5(key_data.encode()).hexdigest()
                    
                    # Try to get from cache
                    result = cache_instance.get(cache_key)
                    if result is not None:
                        return result
                    
                    # Execute function and cache result
                    result = func(*args, **kwargs)
                    cache_instance.put(cache_key, result)
                    return result
                
                return sync_wrapper
        
        return decorator
    
    def profile(self, name: Optional[str] = None, tags: Optional[Dict[str, str]] = None):
        """Decorator for profiling function execution."""
        return self.profiler.profile(name, tags)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        return {
            "cache_stats": self.cache_manager.get_all_stats(),
            "metrics_summary": self.metrics_collector.get_summary(),
            "connection_pools": {
                name: pool.get_stats() for name, pool in self.connection_pools.items()
            },
            "load_balancers": {
                name: balancer.get_stats() for name, balancer in self.load_balancers.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def shutdown(self):
        """Shutdown performance manager."""
        self.system_monitor.stop()
        self.cache_manager.clear_all()
        logger.info("Performance manager shutdown complete")

# Global performance manager instance
performance_manager = PerformanceManager()