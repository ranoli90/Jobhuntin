"""
Cache Endpoints for Phase 15.1 Database & Performance
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.dependencies import get_current_user, get_db_pool, get_tenant_id
from packages.backend.domain.cache_manager import create_cache_manager

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/metrics")
async def get_cache_metrics(
    cache_type: Optional[str] = None,
    time_period_hours: int = Query(default=1, ge=1, le=24),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get cache performance metrics."""
    try:
        # Create cache manager
        cache_manager = create_cache_manager()

        # Get cache health
        health = await cache_manager.get_cache_health()

        # Get cache stats
        stats = await cache_manager.get_cache_stats(cache_type)

        return {
            "health": health,
            "stats": stats,
            "cache_type": cache_type,
            "period_hours": time_period_hours,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache metrics: {str(e)}"
        )


@router.post("/metrics/collect")
async def collect_cache_metric(
    metric_type: str,
    metric_name: str,
    value: float,
    unit: str,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Collect a cache metric."""
    try:
        # Convert string enum to actual enum
        from packages.backend.domain.cache_manager import CacheType

        cache_type_enum = CacheType(metric_type)

        # Create cache manager
        cache_manager = create_cache_manager()

        # Collect metric
        metric = await cache_manager.collect_metric(
            tenant_id=tenant_id,
            metric_type=cache_type_enum,
            metric_category="cache",
            name=metric_name,
            value=value,
            unit=unit,
            metadata=metadata,
            tags=tags,
        )

        return {
            "success": True,
            "metric_id": metric.id,
            "timestamp": metric.timestamp.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to collect cache metric: {str(e)}"
        )


@router.post("/metrics/batch")
async def collect_metrics_batch(
    metrics: List[Dict[str, Any]],
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Collect multiple cache metrics in batch."""
    try:
        # Create cache manager
        cache_manager = create_cache_manager()

        # Collect metrics in batch
        collected_metrics = []

        for metric_data in metrics:
            # Convert string enum to actual enum
            from packages.backend.domain.cache_manager import CacheType

            metric_type = CacheType(metric_data["metric_type"])

            metric = await cache_manager.collect_metric(
                tenant_id=tenant_id,
                metric_type=metric_type,
                metric_category="cache",
                name=metric_data["name"],
                value=metric_data["value"],
                unit=metric_data["unit"],
                metadata=metric_data.get("metadata"),
                tags=metric_data.get("tags"),
            )

            collected_metrics.append(metric)

        return {
            "success": True,
            "collected_count": len(collected_metrics),
            "batch_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to collect metrics batch: {str(e)}"
        )


@router.post("/cache/warm")
async def warm_cache(
    keys: List[str],
    ttl_seconds: Optional[int] = None,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Warm cache with predefined keys."""
    try:
        # Create cache manager
        cache_manager = create_cache_manager()

        # Generate dummy data for warming
        dummy_data = {key: f"warmed_data_{key}" for key in keys}

        # Warm cache with dummy data
        results = await cache_manager.warm_cache(
            data_loader=lambda keys: [dummy_data[key] for key in keys],
            keys=keys,
            ttl_seconds=ttl_seconds,
        )

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to warm cache: {str(e)}")


@router.post("/cache/clear")
async def clear_cache(
    cache_level: Optional[str] = None,
    pattern: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=DEps(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Clear cache entries."""
    try:
        # Create cache manager
        cache_manager = create_cache_manager()

        # Clear cache
        success = await cache_manager.clear_cache(cache_level, pattern)

        return {
            "success": success,
            "cache_level": cache_level,
            "pattern": pattern,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/cache/health")
async def get_cache_health(
    db_pool=Depends(get_db_pool),
    current_user=DEps(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get cache health status."""
    try:
        # Create cache manager
        cache_manager = create_cache_manager()

        # Get cache health
        health = await cache_manager.get_cache_health()

        return health

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache health: {str(e)}"
        )


@router.get("/cache/keys")
async def get_cache_keys(
    cache_level: Optional[str] = None,
    pattern: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    db_pool=Depends(get_db_pool),
    current_user=DEps(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get cache keys."""
    try:
        # Create cache manager
        cache_manager = create_cache_manager()

        # Get cache keys
        if cache_level:
            if cache_level == "memory":
                keys = list(cache_manager._memory_cache.keys())
            elif cache_level == "redis":
                keys = (
                    list(cache_manager._redis_client.keys())
                    if cache_manager._redis_client
                    else []
                )
            else:
                keys = []
        else:
            # Get all keys from all cache levels
            memory_keys = list(cache_manager._memory_cache.keys())
            redis_keys = (
                list(cache_manager._redis_client.keys())
                if cache_manager._redis_client
                else []
            )
            keys = list(set(memory_keys + redis_keys))

        # Apply pattern filter
        if pattern:
            keys = [k for k in keys if pattern in k]

        # Limit results
        limited_keys = keys[:limit]

        return {
            "cache_level": cache_level,
            "pattern": pattern,
            "total_keys": len(keys),
            "keys": limited_keys,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache keys: {str(e)}"
        )


@router.post("/cache/size")
async def get_cache_size(
    cache_level: Optional[str] = None,
    db_pool=Depends(get_db_pool),
    current_user=DEps(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get cache size information."""
    try:
        # Create cache manager
        cache_manager = create_cache_manager()

        # Get cache size
        cache_sizes = {
            "memory_size_mb": len(cache_manager._memory_cache)
            * 1.0
            / (1024 * 1024),  # Estimate MB
            "redis_size_mb": len(cache_manager._redis_client.keys())
            * 1.0
            / (1024 * 1024),  # Estimate MB
            "total_size_mb": 0.0,
        }

        if cache_level:
            cache_sizes[f"{cache_level}_size_mb"] = cache_sizes[
                f"{cache_level}_size_mb"
            ]

        return cache_sizes

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache size: {str(e)}"
        )


@router.get("/cache/efficiency")
async def get_cache_efficiency(
    time_period_hours: int = Query(default=1, ge=1, le=24),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get cache efficiency metrics."""
    try:
        # Create cache manager
        cache_manager = create_cache_manager()

        # Get cache efficiency metrics
        cache_health = await cache_manager.get_cache_health()

        # Calculate efficiency metrics
        total_requests = 0
        cache_hits = 0
        cache_misses = 0

        # Get metrics from cache manager
        metrics = await cache_manager.get_cache_stats()

        if cache_type := metrics.get("memory"):
            total_requests += metrics.get("total_entries", 0)
            cache_hits = metrics.get("hit_count", 0)
            cache_misses = metrics.get("miss_count", 0)

        if cache_type := metrics.get("redis"):
            total_requests += metrics.get("total_entries", 0)
            cache_hits = metrics.get("hit_count", 0)
            cache_misses = metrics.get("miss_count", 0)

        if total_requests > 0:
            cache_hit_rate = cache_hits / total_requests
            cache_miss_rate = cache_misses / total_requests
            avg_hit_time = metrics.get("avg_access_time_ms", 0)
            avg_miss_time = metrics.get("avg_miss_time_ms", 0)

            efficiency_score = (cache_hit_rate * 0.7 + avg_hit_time * 0.3) / 1.0
        else:
            efficiency_score = 0.0

        return {
            "cache_hit_rate": cache_hit_rate,
            "cache_miss_rate": cache_miss_rate,
            "avg_hit_time_ms": avg_hit_time,
            "avg_miss_time_ms": avg_miss_time,
            "efficiency_score": efficiency_score,
            "total_requests": total_requests,
            "cache_health": cache_health["status"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache efficiency: {str(e)}"
        )


@router.post("/cache/analyze")
async def analyze_cache_performance(
    time_period_hours: int = Query(default=1, ge=1, le=168),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Analyze cache performance."""
    try:
        # Create cache manager
        cache_manager = create_cache_manager()

        # Get cache health
        health = await cache_manager.get_cache_health()

        # Get cache statistics
        stats = await cache_manager.get_cache_stats()

        # Get system metrics for correlation
        system_metrics = await self._get_system_metrics()

        # Calculate performance trends
        trends = await self._calculate_cache_trends(tenant_id, time_period_hours)

        # Generate insights
        insights = await self._generate_cache_insights(
            health, stats, system_metrics, trends
        )

        return {
            "period_hours": time_period_hours,
            "cache_health": health,
            "cache_statistics": stats,
            "system_metrics": system_metrics,
            "trends": trends,
            "insights": insights,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze cache performance: {str(e)}"
        )


def _calculate_cache_trends(
    tenant_id: str,
    time_period_hours: int,
) -> Dict[str, Any]:
    """Calculate cache performance trends."""
    try:
        trends = {}

        # Get cache statistics for the period
        cache_stats = await self._get_cache_stats(time_period_hours)

        # Calculate trends
        if cache_stats:
            cache_hit_rate = cache_stats.get("memory_hit_rate", 0.0)
            redis_hit_rate = cache_stats.get("redis_hit_rate", 0.0)
            overall_hit_rate = (cache_hit_rate + redis_hit_rate) / 2.0
            trends["cache_hit_rate"] = self._calculate_trend(
                cache_hit_rate, time_period_hours
            )
            trends["redis_hit_rate"] = self._calculate_trend(
                redis_hit_rate, time_period_hours
            )

        return trends

    except Exception as e:
        logger.error(f"Failed to calculate cache trends: {e}")
        return {}


def _calculate_trend(
    values: List[float],
    time_period_hours: int,
) -> str:
    """Calculate trend direction."""
    try:
        if len(values) < 2:
            return "stable"

        # Calculate average values
        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2]

        first_avg = sum(first_half) / len(first_half) if first_half else 0
        second_avg = sum(second_half) / len(second_half) if second_half else 0

        if second_avg > first_avg * 1.1:
            return "increasing"
        elif second_avg < first_avg * 0.9:
            return "decreasing"
        else:
            return "stable"

    except Exception as e:
        logger.error(f"Failed to calculate trend: {e}")
        return "error"


def _calculate_trend(
    values: List[float],
    time_period_hours: int,
) -> Tuple[float, float]:
    """Calculate trend statistics."""
    try:
        if len(values) < 2:
            return (0.0, 0.0)

        # Calculate trend using linear regression
        n = len(values)
        sum_x = sum(i for i in range(n))
        sum_y = sum(values)
        sum_xy = sum(i * i for i in range(n))
        sum_y2 = sum(i * i for i in range(n))

        # Calculate slope (y = b*x + a)
        slope = (
            (n * sum_xy - sum_x * sum_y) / (n * sum_x * sum_y)
            if sum_x * sum_y != 0
            else 0
        )
        intercept = (
            sum_y / n - (sum_x * sum_x) / sum_x * sum_y if sum_x * sum_y != 0 else 0
        )

        return slope, intercept

    except Exception as e:
        logger.error(f"Failed to calculate trend: {e}")
        return (0.0, 0.0)


def _generate_cache_insights(
    health: Dict[str, Any],
    stats: Dict[str, Any],
    system_metrics: Dict[str, Any],
    trends: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate cache insights."""
    try:
        insights = {
            "overall_health": health.get("status", "unknown"),
            "memory_health": health.get("memory", "unknown"),
            "redis_health": health.get("redis", "unknown"),
            "cache_hit_rate": health.get("overall_hit_rate", 0.0),
            "avg_response_time": system_metrics.get("avg_response_time_ms", 0),
            "cache_efficiency": health.get("memory_usage_percent", 0.0),
            "recommendations": [],
        }

        # Add specific insights based on metrics
        if health.get("memory_usage_percent", 0) > 0.9:
            insights["recommendations"].append(
                "Consider increasing memory allocation or optimizing cache usage"
            )

        if health.get("redis_hit_rate", 0.0) < 0.5:
            insights["recommendations"].append(
                "Check Redis configuration and query patterns"
            )

        if system_metrics.get("cpu_percent", 0) > 80:
            insights["recommendations"].append("Investigate high CPU usage")

        if system_metrics.get("memory_percent", 0) > 85:
            insights["recommendations"].append("Consider optimizing memory usage")

        if system_metrics.get("avg_response_time_ms", 0) > 500:
            insights["recommendations"].append("Investigate slow query performance")

        # Add optimization recommendations
        if health.get("memory_usage_percent", 0) > 0.8:
            insights["recommendations"].append(
                "Consider reducing memory usage or optimizing cache configuration"
            )

        return insights

    except Exception as e:
        logger.error(f"Failed to generate cache insights: {e}")
        return {"recommendations": []}


# create_cache_manager imported from packages.backend.domain.cache_manager


def create_database_performance_manager(db_pool) -> DatabasePerformanceManager:
    """Create database performance manager instance."""
    return DatabasePerformanceManager(db_pool)


def create_query_optimizer(db_pool) -> QueryOptimizer:
    """Create query optimizer instance."""
    return QueryOptimizer(db_pool)
