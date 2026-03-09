"""
Query Optimizer for Phase 15.1 Database & Performance
"""

from __future__ import annotations

import asyncio
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from shared.logging_config import get_logger

logger = get_logger("sorce.query_optimizer")


class QueryOptimizationType(Enum):
    """Types of query optimizations."""

    INDEX_OPTIMIZATION = "index_optimization"
    QUERY_REWRITE = "query_rewrite"
    PARTITION_PRUNING = "partition_pruning"
    JOIN_OPTIMIZATION = "join_optimization"
    SUBQUERY_OPTIMIZATION = "subquery_optimization"
    AGGREGATION_OPTIMIZATION = "aggregation_optimization"
    PREDICATE_OPTIMIZATION = "predicate_optimization"
    CTE_OPTIMIZATION = "cte_optimization"


class OptimizationPriority(Enum):
    """Optimization priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QueryAnalysis:
    """Query analysis result."""

    id: str
    tenant_id: str
    original_query: str
    normalized_query: str
    execution_plan: Dict[str, Any]
    performance_metrics: Dict[str, float]
    identified_issues: List[Dict[str, Any]]
    optimization_opportunities: List[Dict[str, Any]]
    complexity_score: float
    estimated_cost: float
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class QueryOptimization:
    """Query optimization recommendation."""

    id: str
    tenant_id: str
    query_id: str
    optimization_type: QueryOptimizationType
    original_query: str
    optimized_query: str
    description: str
    performance_improvement: float
    implementation_complexity: str  # low, medium, high
    priority: OptimizationPriority
    reasoning: str
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class IndexRecommendation:
    """Index recommendation."""

    id: str
    tenant_id: str
    table_name: str
    column_names: List[str]
    index_type: str  # btree, hash, gin, gist
    estimated_improvement: float
    storage_overhead: float
    priority: OptimizationPriority
    query_patterns: List[str]
    created_at: datetime = datetime.now(timezone.utc)


class QueryOptimizer:
    """Advanced query optimization and analysis system."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._optimization_rules = self._initialize_optimization_rules()
        self._query_patterns = self._initialize_query_patterns()
        self._index_analyzer = None  # Will be initialized separately
        self._analysis_cache: Dict[str, QueryAnalysis] = {}
        self._optimization_cache: Dict[str, List[QueryOptimization]] = {}

        # Start background optimization
        asyncio.create_task(self._start_optimization_monitoring())

    async def analyze_query(
        self,
        tenant_id: str,
        query: str,
        parameters: Optional[List[Any]] = None,
    ) -> QueryAnalysis:
        """Analyze a SQL query for optimization opportunities."""
        try:
            # Normalize query
            normalized_query = self._normalize_query(query)

            # Get execution plan
            execution_plan = await self._get_execution_plan(query, parameters)

            # Calculate performance metrics
            performance_metrics = await self._calculate_performance_metrics(
                query, parameters, execution_plan
            )

            # Identify issues
            identified_issues = await self._identify_query_issues(
                query, execution_plan, performance_metrics
            )

            # Find optimization opportunities
            optimization_opportunities = await self._find_optimization_opportunities(
                query, execution_plan, identified_issues
            )

            # Calculate complexity and cost
            complexity_score = self._calculate_query_complexity(query, execution_plan)
            estimated_cost = execution_plan.get("Total Cost", 0)

            # Create analysis
            analysis = QueryAnalysis(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                original_query=query,
                normalized_query=normalized_query,
                execution_plan=execution_plan,
                performance_metrics=performance_metrics,
                identified_issues=identified_issues,
                optimization_opportunities=optimization_opportunities,
                complexity_score=complexity_score,
                estimated_cost=estimated_cost,
            )

            # Save analysis
            await self._save_query_analysis(analysis)

            # Update cache
            self._analysis_cache[f"{tenant_id}:{hash(normalized_query)}"] = analysis

            logger.info(
                f"Query analysis completed: complexity={complexity_score:.2f}, cost={estimated_cost}"
            )
            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze query: {e}")
            raise

    async def optimize_query(
        self,
        tenant_id: str,
        query: str,
        optimization_types: Optional[List[QueryOptimizationType]] = None,
    ) -> List[QueryOptimization]:
        """Generate query optimizations."""
        try:
            # First analyze the query
            analysis = await self.analyze_query(tenant_id, query)

            # Generate optimizations
            optimizations = []

            if not optimization_types:
                optimization_types = list(QueryOptimizationType)

            for opt_type in optimization_types:
                try:
                    optimization = await self._generate_optimization(
                        tenant_id, analysis, opt_type
                    )
                    if optimization:
                        optimizations.append(optimization)
                except Exception as e:
                    logger.error(
                        f"Failed to generate {opt_type.value} optimization: {e}"
                    )

            # Sort by priority and performance improvement
            optimizations.sort(
                key=lambda opt: (
                    self._priority_score(opt.priority),
                    opt.performance_improvement,
                ),
                reverse=True,
            )

            # Save optimizations
            for optimization in optimizations:
                await self._save_query_optimization(optimization)

            # Update cache
            cache_key = f"{tenant_id}:{hash(analysis.normalized_query)}"
            self._optimization_cache[cache_key] = optimizations

            logger.info(f"Generated {len(optimizations)} query optimizations")
            return optimizations

        except Exception as e:
            logger.error(f"Failed to optimize query: {e}")
            raise

    async def recommend_indexes(
        self,
        tenant_id: str,
        table_name: Optional[str] = None,
        query_patterns: Optional[List[str]] = None,
    ) -> List[IndexRecommendation]:
        """Generate index recommendations."""
        try:
            recommendations = []

            if query_patterns:
                # Analyze specific query patterns
                for pattern in query_patterns:
                    pattern_recommendations = (
                        await self._analyze_query_pattern_for_indexes(
                            tenant_id, pattern
                        )
                    )
                    recommendations.extend(pattern_recommendations)
            else:
                # Analyze all tables or specific table
                if table_name:
                    table_recommendations = await self._analyze_table_for_indexes(
                        tenant_id, table_name
                    )
                    recommendations.extend(table_recommendations)
                else:
                    # Analyze all user tables
                    tables = await self._get_user_tables(tenant_id)
                    for table in tables:
                        table_recommendations = await self._analyze_table_for_indexes(
                            tenant_id, table
                        )
                        recommendations.extend(table_recommendations)

            # Remove duplicates and sort by priority
            unique_recommendations = self._deduplicate_index_recommendations(
                recommendations
            )
            unique_recommendations.sort(
                key=lambda rec: (
                    self._priority_score(rec.priority),
                    rec.estimated_improvement,
                ),
                reverse=True,
            )

            # Save recommendations
            for recommendation in unique_recommendations:
                await self._save_index_recommendation(recommendation)

            logger.info(
                f"Generated {len(unique_recommendations)} index recommendations"
            )
            return unique_recommendations

        except Exception as e:
            logger.error(f"Failed to recommend indexes: {e}")
            raise

    async def get_optimization_report(
        self,
        tenant_id: str,
        time_period_hours: int = 24,
    ) -> Dict[str, Any]:
        """Get comprehensive optimization report."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=time_period_hours
            )

            # Get query analyses
            analyses = await self._get_query_analyses(tenant_id, cutoff_time)

            # Get optimizations
            optimizations = await self._get_query_optimizations(tenant_id, cutoff_time)

            # Get index recommendations
            index_recommendations = await self._get_index_recommendations(
                tenant_id, cutoff_time
            )

            # Calculate statistics
            statistics = await self._calculate_optimization_statistics(
                analyses, optimizations, index_recommendations
            )

            # Get top slow queries
            slow_queries = await self._get_slow_queries(tenant_id, cutoff_time)

            # Get optimization trends
            trends = await self._get_optimization_trends(tenant_id, time_period_hours)

            report = {
                "period_hours": time_period_hours,
                "query_analyses": len(analyses),
                "optimizations_generated": len(optimizations),
                "index_recommendations": len(index_recommendations),
                "statistics": statistics,
                "slow_queries": slow_queries,
                "optimization_trends": trends,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            return report

        except Exception as e:
            logger.error(f"Failed to get optimization report: {e}")
            return {}

    def _initialize_optimization_rules(self) -> Dict[str, Any]:
        """Initialize optimization rules."""
        return {
            "slow_query_threshold": 1000.0,  # 1 second
            "high_cost_threshold": 10000.0,
            "complexity_threshold": 0.7,
            "index_usage_threshold": 0.1,  # 10% usage
            "join_optimization_threshold": 3,  # 3+ tables
            "subquery_depth_threshold": 2,
            "aggregation_size_threshold": 10000,  # rows
        }

    def _initialize_query_patterns(self) -> Dict[str, List[str]]:
        """Initialize common query patterns."""
        return {
            "select_patterns": [
                r"SELECT\s+\*\s+FROM",  # SELECT *
                r"SELECT\s+.+\s+FROM\s+.+\s+WHERE\s+.+\s+ORDER\s+BY",
                r"SELECT\s+.+\s+FROM\s+.+\s+JOIN\s+.+\s+ON",
                r"SELECT\s+.+\s+FROM\s+.+\s+WHERE\s+.+\s+IN\s*\(",
            ],
            "join_patterns": [
                r"JOIN\s+.+\s+ON",
                r"LEFT\s+JOIN",
                r"RIGHT\s+JOIN",
                r"INNER\s+JOIN",
                r"OUTER\s+JOIN",
            ],
            "aggregation_patterns": [
                r"GROUP\s+BY",
                r"COUNT\s*\(",
                r"SUM\s*\(",
                r"AVG\s*\(",
                r"MAX\s*\(",
                r"MIN\s*\(",
            ],
            "subquery_patterns": [
                r"SELECT\s+.+\s+FROM\s+\(",
                r"WHERE\s+.+\s+IN\s*\(",
                r"WHERE\s+.+\s+EXISTS\s*\(",
                r"FROM\s+\(",
            ],
        }

    async def _start_optimization_monitoring(self) -> None:
        """Start background optimization monitoring."""
        try:
            while True:
                await asyncio.sleep(1800)  # Run every 30 minutes

                # Monitor slow queries
                await self._monitor_slow_queries()

                # Update optimization recommendations
                await self._update_optimization_recommendations()

                # Check index usage
                await self._check_index_usage()

        except Exception as e:
            logger.error(f"Background optimization monitoring failed: {e}")

    def _normalize_query(self, query: str) -> str:
        """Normalize SQL query for comparison."""
        try:
            # Remove extra whitespace
            normalized = re.sub(r"\s+", " ", query.strip())

            # Convert to uppercase for keywords
            keywords = [
                "SELECT",
                "FROM",
                "WHERE",
                "JOIN",
                "ON",
                "GROUP",
                "BY",
                "ORDER",
                "HAVING",
                "UNION",
                "INSERT",
                "UPDATE",
                "DELETE",
            ]
            for keyword in keywords:
                normalized = re.sub(
                    rf"\b{keyword}\b", keyword, normalized, flags=re.IGNORECASE
                )

            # Remove parameter values
            normalized = re.sub(r"'[^']*'", "'?'", normalized)
            normalized = re.sub(r"\b\d+\b", "?", normalized)

            return normalized

        except Exception as e:
            logger.error(f"Failed to normalize query: {e}")
            return query

    async def _get_execution_plan(
        self,
        query: str,
        parameters: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """Get query execution plan."""
        try:
            explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE, BUFFERS) {query}"

            async with self.db_pool.acquire() as conn:
                if parameters:
                    result = await conn.fetchrow(explain_query, *parameters)
                else:
                    result = await conn.fetchrow(explain_query)

                if result and result[0]:
                    plan_data = json.loads(result[0])
                    return plan_data[0] if isinstance(plan_data, list) else plan_data

                return {}

        except Exception as e:
            logger.error(f"Failed to get execution plan: {e}")
            return {}

    async def _calculate_performance_metrics(
        self,
        query: str,
        parameters: Optional[List[Any]],
        execution_plan: Dict[str, Any],
    ) -> Dict[str, float]:
        """Calculate performance metrics from execution plan."""
        try:
            metrics = {}

            # Extract execution time
            execution_time = execution_plan.get("Execution Time", 0)
            planning_time = execution_plan.get("Planning Time", 0)
            total_time = execution_plan.get("Total Cost", 0)

            metrics["execution_time_ms"] = float(execution_time)
            metrics["planning_time_ms"] = float(planning_time)
            metrics["total_cost"] = float(total_time)

            # Extract buffer information
            buffers = execution_plan.get("Buffers", {})
            if buffers:
                shared_hit = buffers.get("Shared Hit Blocks", 0)
                shared_read = buffers.get("Shared Read Blocks", 0)
                shared_dirtied = buffers.get("Shared Dirtied Blocks", 0)
                temp_read = buffers.get("Temp Read Blocks", 0)
                temp_written = buffers.get("Temp Written Blocks", 0)

                total_blocks = (
                    shared_hit + shared_read + shared_dirtied + temp_read + temp_written
                )
                if total_blocks > 0:
                    metrics["cache_hit_ratio"] = shared_hit / total_blocks
                    metrics["temp_io_ratio"] = (temp_read + temp_written) / total_blocks
                else:
                    metrics["cache_hit_ratio"] = 0.0
                    metrics["temp_io_ratio"] = 0.0

            # Count operations
            operations = self._count_plan_operations(execution_plan)
            metrics["operation_count"] = operations

            # Calculate depth
            depth = self._calculate_plan_depth(execution_plan)
            metrics["plan_depth"] = depth

            return metrics

        except Exception as e:
            logger.error(f"Failed to calculate performance metrics: {e}")
            return {}

    def _count_plan_operations(self, plan: Dict[str, Any]) -> int:
        """Count operations in execution plan."""
        try:
            count = 1  # Count current operation

            if "Plans" in plan:
                for subplan in plan["Plans"]:
                    count += self._count_plan_operations(subplan)

            return count

        except Exception as e:
            logger.error(f"Failed to count plan operations: {e}")
            return 0

    def _calculate_plan_depth(self, plan: Dict[str, Any]) -> int:
        """Calculate depth of execution plan."""
        try:
            max_depth = 0

            if "Plans" in plan:
                for subplan in plan["Plans"]:
                    depth = 1 + self._calculate_plan_depth(subplan)
                    max_depth = max(max_depth, depth)

            return max_depth

        except Exception as e:
            logger.error(f"Failed to calculate plan depth: {e}")
            return 0

    async def _identify_query_issues(
        self,
        query: str,
        execution_plan: Dict[str, Any],
        performance_metrics: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """Identify query performance issues."""
        try:
            issues = []

            # Check for slow execution
            execution_time = performance_metrics.get("execution_time_ms", 0)
            if execution_time > self._optimization_rules["slow_query_threshold"]:
                issues.append(
                    {
                        "type": "slow_execution",
                        "severity": "high",
                        "description": f"Query execution time {execution_time:.2f}ms exceeds threshold",
                        "value": execution_time,
                        "threshold": self._optimization_rules["slow_query_threshold"],
                    }
                )

            # Check for high cost
            total_cost = performance_metrics.get("total_cost", 0)
            if total_cost > self._optimization_rules["high_cost_threshold"]:
                issues.append(
                    {
                        "type": "high_cost",
                        "severity": "medium",
                        "description": f"Query cost {total_cost:.2f} exceeds threshold",
                        "value": total_cost,
                        "threshold": self._optimization_rules["high_cost_threshold"],
                    }
                )

            # Check for low cache hit ratio
            cache_hit_ratio = performance_metrics.get("cache_hit_ratio", 1.0)
            if cache_hit_ratio < 0.8:
                issues.append(
                    {
                        "type": "low_cache_hit",
                        "severity": "medium",
                        "description": f"Cache hit ratio {cache_hit_ratio:.2f} is below optimal",
                        "value": cache_hit_ratio,
                        "threshold": 0.8,
                    }
                )

            # Check for high temp IO
            temp_io_ratio = performance_metrics.get("temp_io_ratio", 0)
            if temp_io_ratio > 0.1:
                issues.append(
                    {
                        "type": "high_temp_io",
                        "severity": "high",
                        "description": f"Temp IO ratio {temp_io_ratio:.2f} indicates disk usage",
                        "value": temp_io_ratio,
                        "threshold": 0.1,
                    }
                )

            # Check for SELECT *
            if "SELECT *" in query.upper():
                issues.append(
                    {
                        "type": "select_star",
                        "severity": "low",
                        "description": "SELECT * can be inefficient",
                        "recommendation": "Specify only required columns",
                    }
                )

            # Check for missing WHERE clause
            if "WHERE" not in query.upper() and "FROM" in query.upper():
                issues.append(
                    {
                        "type": "missing_where",
                        "severity": "medium",
                        "description": "Query without WHERE clause may scan entire table",
                        "recommendation": "Add appropriate WHERE clause",
                    }
                )

            # Check for implicit joins
            if "WHERE" in query.upper() and "JOIN" not in query.upper():
                where_clause = (
                    query.upper().split("WHERE")[1].split("ORDER")[0].split("GROUP")[0]
                )
                if "." in where_clause and "=" in where_clause:
                    issues.append(
                        {
                            "type": "implicit_join",
                            "severity": "medium",
                            "description": "Implicit joins in WHERE clause",
                            "recommendation": "Use explicit JOIN syntax",
                        }
                    )

            return issues

        except Exception as e:
            logger.error(f"Failed to identify query issues: {e}")
            return []

    async def _find_optimization_opportunities(
        self,
        query: str,
        execution_plan: Dict[str, Any],
        issues: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Find optimization opportunities."""
        try:
            opportunities = []

            # Index opportunities
            index_opportunities = await self._find_index_opportunities(execution_plan)
            opportunities.extend(index_opportunities)

            # Join optimization opportunities
            join_opportunities = await self._find_join_opportunities(
                query, execution_plan
            )
            opportunities.extend(join_opportunities)

            # Subquery optimization opportunities
            subquery_opportunities = await self._find_subquery_opportunities(
                query, execution_plan
            )
            opportunities.extend(subquery_opportunities)

            # Aggregation optimization opportunities
            aggregation_opportunities = await self._find_aggregation_opportunities(
                query, execution_plan
            )
            opportunities.extend(aggregation_opportunities)

            # Sort by potential impact
            opportunities.sort(key=lambda opp: opp.get("impact_score", 0), reverse=True)

            return opportunities

        except Exception as e:
            logger.error(f"Failed to find optimization opportunities: {e}")
            return []

    async def _find_index_opportunities(
        self,
        execution_plan: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Find index optimization opportunities."""
        try:
            opportunities = []

            # Look for Seq Scan nodes
            self._find_seq_scans(execution_plan, opportunities)

            # Look for Sort nodes without indexes
            self._find_sort_opportunities(execution_plan, opportunities)

            # Look for Hash Join without proper indexes
            self._find_hash_join_opportunities(execution_plan, opportunities)

            return opportunities

        except Exception as e:
            logger.error(f"Failed to find index opportunities: {e}")
            return []

    def _find_seq_scans(
        self, plan: Dict[str, Any], opportunities: List[Dict[str, Any]]
    ) -> None:
        """Find sequential scan opportunities."""
        try:
            if plan.get("Node Type") == "Seq Scan":
                relation_name = plan.get("Relation Name", "")
                alias = plan.get("Alias", "")
                table_name = alias or relation_name

                # Check if this is a large table scan
                actual_rows = plan.get("Actual Rows", 0)
                if actual_rows > 1000:  # Threshold for large scan
                    opportunities.append(
                        {
                            "type": "index_opportunity",
                            "subtype": "seq_scan",
                            "table_name": table_name,
                            "rows_scanned": actual_rows,
                            "impact_score": min(1.0, actual_rows / 10000),
                            "description": f"Sequential scan on {table_name} affecting {actual_rows} rows",
                            "recommendation": f"Consider adding index on {table_name}",
                        }
                    )

            # Recursively check subplans
            if "Plans" in plan:
                for subplan in plan["Plans"]:
                    self._find_seq_scans(subplan, opportunities)

        except Exception as e:
            logger.error(f"Failed to find seq scans: {e}")

    def _find_sort_opportunities(
        self, plan: Dict[str, Any], opportunities: List[Dict[str, Any]]
    ) -> None:
        """Find sort optimization opportunities."""
        try:
            if plan.get("Node Type") == "Sort":
                # Check if sort could benefit from index
                sort_method = plan.get("Sort Method", "")
                if sort_method == "external":
                    opportunities.append(
                        {
                            "type": "index_opportunity",
                            "subtype": "external_sort",
                            "impact_score": 0.8,
                            "description": "External sort indicates disk usage",
                            "recommendation": "Consider adding index to support ORDER BY",
                        }
                    )

            # Recursively check subplans
            if "Plans" in plan:
                for subplan in plan["Plans"]:
                    self._find_sort_opportunities(subplan, opportunities)

        except Exception as e:
            logger.error(f"Failed to find sort opportunities: {e}")

    def _find_hash_join_opportunities(
        self, plan: Dict[str, Any], opportunities: List[Dict[str, Any]]
    ) -> None:
        """Find hash join optimization opportunities."""
        try:
            if plan.get("Node Type") == "Hash Join":
                # Check if hash join could be optimized with indexes
                hash_cond = plan.get("Hash Cond", "")
                if hash_cond:
                    opportunities.append(
                        {
                            "type": "index_opportunity",
                            "subtype": "hash_join",
                            "condition": hash_cond,
                            "impact_score": 0.6,
                            "description": "Hash join might benefit from better indexes",
                            "recommendation": "Consider indexes on join columns",
                        }
                    )

            # Recursively check subplans
            if "Plans" in plan:
                for subplan in plan["Plans"]:
                    self._find_hash_join_opportunities(subplan, opportunities)

        except Exception as e:
            logger.error(f"Failed to find hash join opportunities: {e}")

    async def _find_join_opportunities(
        self,
        query: str,
        execution_plan: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Find join optimization opportunities."""
        try:
            opportunities = []

            # Count joins in query
            join_count = len(re.findall(r"\bJOIN\b", query, re.IGNORECASE))
            if join_count > self._optimization_rules["join_optimization_threshold"]:
                opportunities.append(
                    {
                        "type": "join_optimization",
                        "subtype": "many_joins",
                        "join_count": join_count,
                        "impact_score": min(1.0, join_count / 10),
                        "description": f"Query has {join_count} joins which may be inefficient",
                        "recommendation": "Consider breaking into smaller queries or optimizing join order",
                    }
                )

            # Look for nested loops
            self._find_nested_loop_opportunities(execution_plan, opportunities)

            return opportunities

        except Exception as e:
            logger.error(f"Failed to find join opportunities: {e}")
            return []

    def _find_nested_loop_opportunities(
        self, plan: Dict[str, Any], opportunities: List[Dict[str, Any]]
    ) -> None:
        """Find nested loop join opportunities."""
        try:
            if plan.get("Node Type") == "Nested Loop":
                # Check if nested loop is inefficient
                actual_rows = plan.get("Actual Rows", 0)
                if actual_rows > 10000:  # Large result set
                    opportunities.append(
                        {
                            "type": "join_optimization",
                            "subtype": "nested_loop",
                            "rows_processed": actual_rows,
                            "impact_score": min(1.0, actual_rows / 100000),
                            "description": f"Nested loop processing {actual_rows} rows",
                            "recommendation": "Consider hash join or merge join",
                        }
                    )

            # Recursively check subplans
            if "Plans" in plan:
                for subplan in plan["Plans"]:
                    self._find_nested_loop_opportunities(subplan, opportunities)

        except Exception as e:
            logger.error(f"Failed to find nested loop opportunities: {e}")

    async def _find_subquery_opportunities(
        self,
        query: str,
        execution_plan: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Find subquery optimization opportunities."""
        try:
            opportunities = []

            # Check for correlated subqueries
            if "WHERE" in query.upper() and "SELECT" in query.upper():
                # Simple heuristic for correlated subqueries
                where_part = (
                    query.upper().split("WHERE")[1].split("ORDER")[0].split("GROUP")[0]
                )
                if where_part.count("SELECT") > 0:
                    opportunities.append(
                        {
                            "type": "subquery_optimization",
                            "subtype": "correlated_subquery",
                            "impact_score": 0.7,
                            "description": "Possible correlated subquery detected",
                            "recommendation": "Consider rewriting as JOIN or EXISTS",
                        }
                    )

            # Check for IN subqueries
            if " IN (" in query.upper() and "SELECT" in query.upper():
                opportunities.append(
                    {
                        "type": "subquery_optimization",
                        "subtype": "in_subquery",
                        "impact_score": 0.5,
                        "description": "IN subquery detected",
                        "recommendation": "Consider JOIN or EXISTS alternative",
                    }
                )

            return opportunities

        except Exception as e:
            logger.error(f"Failed to find subquery opportunities: {e}")
            return []

    async def _find_aggregation_opportunities(
        self,
        query: str,
        execution_plan: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Find aggregation optimization opportunities."""
        try:
            opportunities = []

            # Check for aggregation without indexes
            if "GROUP BY" in query.upper():
                # Look for Hash Aggregate in plan
                if not self._has_hash_aggregate(execution_plan):
                    opportunities.append(
                        {
                            "type": "aggregation_optimization",
                            "subtype": "group_by",
                            "impact_score": 0.6,
                            "description": "GROUP BY without efficient aggregation",
                            "recommendation": "Consider indexes on GROUP BY columns",
                        }
                    )

            # Check for COUNT(*) without WHERE
            if "COUNT(*)" in query.upper() and "WHERE" not in query.upper():
                opportunities.append(
                    {
                        "type": "aggregation_optimization",
                        "subtype": "count_star",
                        "impact_score": 0.4,
                        "description": "COUNT(*) without WHERE clause",
                        "recommendation": "Consider COUNT(1) or add WHERE clause",
                    }
                )

            return opportunities

        except Exception as e:
            logger.error(f"Failed to find aggregation opportunities: {e}")
            return []

    def _has_hash_aggregate(self, plan: Dict[str, Any]) -> bool:
        """Check if plan has hash aggregate."""
        try:
            if plan.get("Node Type") == "Hash Aggregate":
                return True

            if "Plans" in plan:
                for subplan in plan["Plans"]:
                    if self._has_hash_aggregate(subplan):
                        return True

            return False

        except Exception as e:
            logger.error(f"Failed to check hash aggregate: {e}")
            return False

    def _calculate_query_complexity(
        self, query: str, execution_plan: Dict[str, Any]
    ) -> float:
        """Calculate query complexity score."""
        try:
            complexity = 0.0

            # Base complexity for query type
            if "SELECT" in query.upper():
                complexity += 0.1
            elif "INSERT" in query.upper():
                complexity += 0.2
            elif "UPDATE" in query.upper():
                complexity += 0.3
            elif "DELETE" in query.upper():
                complexity += 0.3

            # Joins increase complexity
            join_count = len(re.findall(r"\bJOIN\b", query, re.IGNORECASE))
            complexity += join_count * 0.15

            # Subqueries increase complexity
            subquery_count = query.upper().count("(SELECT")
            complexity += subquery_count * 0.1

            # Aggregations increase complexity
            agg_count = len(
                re.findall(r"\b(COUNT|SUM|AVG|MAX|MIN)\s*\(", query, re.IGNORECASE)
            )
            complexity += agg_count * 0.05

            # Plan depth affects complexity
            plan_depth = self._calculate_plan_depth(execution_plan)
            complexity += plan_depth * 0.1

            # Normalize to 0-1 range
            return min(1.0, complexity)

        except Exception as e:
            logger.error(f"Failed to calculate query complexity: {e}")
            return 0.5

    def _priority_score(self, priority: OptimizationPriority) -> float:
        """Convert priority to numeric score."""
        scores = {
            OptimizationPriority.LOW: 0.25,
            OptimizationPriority.MEDIUM: 0.5,
            OptimizationPriority.HIGH: 0.75,
            OptimizationPriority.CRITICAL: 1.0,
        }
        return scores.get(priority, 0.5)

    async def _generate_optimization(
        self,
        tenant_id: str,
        analysis: QueryAnalysis,
        optimization_type: QueryOptimizationType,
    ) -> Optional[QueryOptimization]:
        """Generate specific optimization."""
        try:
            if optimization_type == QueryOptimizationType.QUERY_REWRITE:
                return await self._generate_query_rewrite_optimization(
                    tenant_id, analysis
                )
            elif optimization_type == QueryOptimizationType.INDEX_OPTIMIZATION:
                return await self._generate_index_optimization(tenant_id, analysis)
            elif optimization_type == QueryOptimizationType.JOIN_OPTIMIZATION:
                return await self._generate_join_optimization(tenant_id, analysis)
            elif optimization_type == QueryOptimizationType.SUBQUERY_OPTIMIZATION:
                return await self._generate_subquery_optimization(tenant_id, analysis)
            elif optimization_type == QueryOptimizationType.AGGREGATION_OPTIMIZATION:
                return await self._generate_aggregation_optimization(
                    tenant_id, analysis
                )
            else:
                return None

        except Exception as e:
            logger.error(
                f"Failed to generate {optimization_type.value} optimization: {e}"
            )
            return None

    async def _generate_query_rewrite_optimization(
        self,
        tenant_id: str,
        analysis: QueryAnalysis,
    ) -> Optional[QueryOptimization]:
        """Generate query rewrite optimization."""
        try:
            original_query = analysis.original_query
            optimized_query = original_query

            # Apply common optimizations
            optimizations_applied = []

            # Replace SELECT * with specific columns if possible
            if "SELECT *" in original_query.upper():
                # This is a simplified approach - in practice, you'd analyze the schema
                optimized_query = optimized_query.replace(
                    "SELECT *", "SELECT id, created_at"
                )
                optimizations_applied.append("Replaced SELECT * with specific columns")

            # Remove unnecessary ORDER BY if not needed
            if (
                "ORDER BY" in optimized_query.upper()
                and "LIMIT" not in optimized_query.upper()
            ):
                optimized_query = re.sub(
                    r"\s+ORDER\s+BY\s+[^;]+", "", optimized_query, flags=re.IGNORECASE
                )
                optimizations_applied.append("Removed unnecessary ORDER BY")

            # If no changes were made, return None
            if optimized_query == original_query:
                return None

            return QueryOptimization(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                query_id=analysis.id,
                optimization_type=QueryOptimizationType.QUERY_REWRITE,
                original_query=original_query,
                optimized_query=optimized_query,
                description="Query rewritten for better performance",
                performance_improvement=0.2,  # Estimated
                implementation_complexity="low",
                priority=OptimizationPriority.MEDIUM,
                reasoning=f"Applied optimizations: {', '.join(optimizations_applied)}",
            )

        except Exception as e:
            logger.error(f"Failed to generate query rewrite optimization: {e}")
            return None

    async def _generate_index_optimization(
        self,
        tenant_id: str,
        analysis: QueryAnalysis,
    ) -> Optional[QueryOptimization]:
        """Generate index optimization."""
        try:
            # Look for sequential scan opportunities
            seq_scan_opportunities = [
                opp
                for opp in analysis.optimization_opportunities
                if opp.get("type") == "index_opportunity"
                and opp.get("subtype") == "seq_scan"
            ]

            if not seq_scan_opportunities:
                return None

            best_opportunity = seq_scan_opportunities[0]
            table_name = best_opportunity.get("table_name", "")

            return QueryOptimization(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                query_id=analysis.id,
                optimization_type=QueryOptimizationType.INDEX_OPTIMIZATION,
                original_query=analysis.original_query,
                optimized_query=analysis.original_query,  # Query unchanged, just need index
                description=f"Add index on {table_name} to improve query performance",
                performance_improvement=best_opportunity.get("impact_score", 0.5),
                implementation_complexity="medium",
                priority=OptimizationPriority.HIGH,
                reasoning=f"Sequential scan on {table_name} affecting {best_opportunity.get('rows_scanned', 0)} rows",
            )

        except Exception as e:
            logger.error(f"Failed to generate index optimization: {e}")
            return None

    async def _generate_join_optimization(
        self,
        tenant_id: str,
        analysis: QueryAnalysis,
    ) -> Optional[QueryOptimization]:
        """Generate join optimization."""
        try:
            join_opportunities = [
                opp
                for opp in analysis.optimization_opportunities
                if opp.get("type") == "join_optimization"
            ]

            if not join_opportunities:
                return None

            best_opportunity = join_opportunities[0]

            return QueryOptimization(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                query_id=analysis.id,
                optimization_type=QueryOptimizationType.JOIN_OPTIMIZATION,
                original_query=analysis.original_query,
                optimized_query=analysis.original_query,  # Placeholder - would need actual optimization
                description=best_opportunity.get(
                    "description", "Optimize join operations"
                ),
                performance_improvement=best_opportunity.get("impact_score", 0.3),
                implementation_complexity="medium",
                priority=OptimizationPriority.MEDIUM,
                reasoning=best_opportunity.get(
                    "recommendation", "Join optimization needed"
                ),
            )

        except Exception as e:
            logger.error(f"Failed to generate join optimization: {e}")
            return None

    async def _generate_subquery_optimization(
        self,
        tenant_id: str,
        analysis: QueryAnalysis,
    ) -> Optional[QueryOptimization]:
        """Generate subquery optimization."""
        try:
            subquery_opportunities = [
                opp
                for opp in analysis.optimization_opportunities
                if opp.get("type") == "subquery_optimization"
            ]

            if not subquery_opportunities:
                return None

            best_opportunity = subquery_opportunities[0]

            return QueryOptimization(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                query_id=analysis.id,
                optimization_type=QueryOptimizationType.SUBQUERY_OPTIMIZATION,
                original_query=analysis.original_query,
                optimized_query=analysis.original_query,  # Placeholder - would need actual optimization
                description=best_opportunity.get(
                    "description", "Optimize subquery usage"
                ),
                performance_improvement=best_opportunity.get("impact_score", 0.4),
                implementation_complexity="medium",
                priority=OptimizationPriority.MEDIUM,
                reasoning=best_opportunity.get(
                    "recommendation", "Subquery optimization needed"
                ),
            )

        except Exception as e:
            logger.error(f"Failed to generate subquery optimization: {e}")
            return None

    async def _generate_aggregation_optimization(
        self,
        tenant_id: str,
        analysis: QueryAnalysis,
    ) -> Optional[QueryOptimization]:
        """Generate aggregation optimization."""
        try:
            agg_opportunities = [
                opp
                for opp in analysis.optimization_opportunities
                if opp.get("type") == "aggregation_optimization"
            ]

            if not agg_opportunities:
                return None

            best_opportunity = agg_opportunities[0]

            return QueryOptimization(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                query_id=analysis.id,
                optimization_type=QueryOptimizationType.AGGREGATION_OPTIMIZATION,
                original_query=analysis.original_query,
                optimized_query=analysis.original_query,  # Placeholder - would need actual optimization
                description=best_opportunity.get(
                    "description", "Optimize aggregation operations"
                ),
                performance_improvement=best_opportunity.get("impact_score", 0.3),
                implementation_complexity="low",
                priority=OptimizationPriority.LOW,
                reasoning=best_opportunity.get(
                    "recommendation", "Aggregation optimization needed"
                ),
            )

        except Exception as e:
            logger.error(f"Failed to generate aggregation optimization: {e}")
            return None

    async def _save_query_analysis(self, analysis: QueryAnalysis) -> None:
        """Save query analysis to database."""
        try:
            query = """
                INSERT INTO query_analyses (
                    id, tenant_id, original_query, normalized_query, execution_plan,
                    performance_metrics, identified_issues, optimization_opportunities,
                    complexity_score, estimated_cost, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """

            params = [
                analysis.id,
                analysis.tenant_id,
                analysis.original_query,
                analysis.normalized_query,
                json.dumps(analysis.execution_plan),
                json.dumps(analysis.performance_metrics),
                json.dumps(analysis.identified_issues),
                json.dumps(analysis.optimization_opportunities),
                analysis.complexity_score,
                analysis.estimated_cost,
                analysis.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save query analysis: {e}")

    async def _save_query_optimization(self, optimization: QueryOptimization) -> None:
        """Save query optimization to database."""
        try:
            query = """
                INSERT INTO query_optimizations (
                    id, tenant_id, query_id, optimization_type, original_query,
                    optimized_query, description, performance_improvement,
                    implementation_complexity, priority, reasoning, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """

            params = [
                optimization.id,
                optimization.tenant_id,
                optimization.query_id,
                optimization.optimization_type.value,
                optimization.original_query,
                optimization.optimized_query,
                optimization.description,
                optimization.performance_improvement,
                optimization.implementation_complexity,
                optimization.priority.value,
                optimization.reasoning,
                optimization.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save query optimization: {e}")

    async def _save_index_recommendation(
        self, recommendation: IndexRecommendation
    ) -> None:
        """Save index recommendation to database."""
        try:
            query = """
                INSERT INTO index_recommendations (
                    id, tenant_id, table_name, column_names, index_type,
                    estimated_improvement, storage_overhead, priority,
                    query_patterns, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """

            params = [
                recommendation.id,
                recommendation.tenant_id,
                recommendation.table_name,
                json.dumps(recommendation.column_names),
                recommendation.index_type,
                recommendation.estimated_improvement,
                recommendation.storage_overhead,
                recommendation.priority.value,
                json.dumps(recommendation.query_patterns),
                recommendation.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save index recommendation: {e}")

    async def _get_user_tables(self, tenant_id: str) -> List[str]:
        """Get user tables for analysis."""
        try:
            query = """
                SELECT tablename FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY tablename
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query)
                return [row[0] for row in results]

        except Exception as e:
            logger.error(f"Failed to get user tables: {e}")
            return []

    async def _analyze_table_for_indexes(
        self,
        tenant_id: str,
        table_name: str,
    ) -> List[IndexRecommendation]:
        """Analyze a specific table for index recommendations."""
        try:
            recommendations = []

            # Get table statistics
            stats_query = """
                SELECT 
                    pg_size_pretty(pg_total_relation_size($1)) as size,
                    pg_total_relation_size($1) as size_bytes,
                    (SELECT count(*) FROM $1) as row_count
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(stats_query, table_name)

                if not result:
                    return recommendations

                row_count = result[2]

                # Get column statistics
                columns_query = """
                    SELECT 
                        column_name,
                        data_type,
                        n_distinct,
                        null_frac
                    FROM pg_stats 
                    WHERE tablename = $1
                    ORDER BY column_name
                """

                columns = await conn.fetch(columns_query, table_name)

                # Analyze each column for index potential
                for col in columns:
                    col_name = col[0]
                    data_type = col[1]
                    n_distinct = col[2]
                    null_frac = col[3]

                    # Skip columns with too many nulls
                    if null_frac > 0.8:
                        continue

                    # Check for good index candidates
                    if self._is_good_index_candidate(
                        col_name, data_type, n_distinct, row_count
                    ):
                        recommendation = IndexRecommendation(
                            id=str(uuid.uuid4()),
                            tenant_id=tenant_id,
                            table_name=table_name,
                            column_names=[col_name],
                            index_type="btree",
                            estimated_improvement=0.3,
                            storage_overhead=self._estimate_index_storage(row_count),
                            priority=OptimizationPriority.MEDIUM,
                            query_patterns=[f"WHERE {col_name} = ?"],
                        )
                        recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            logger.error(f"Failed to analyze table {table_name} for indexes: {e}")
            return []

    def _is_good_index_candidate(
        self,
        column_name: str,
        data_type: str,
        n_distinct: int,
        row_count: int,
    ) -> bool:
        """Check if column is a good index candidate."""
        try:
            # Skip certain column types
            if data_type in ["json", "jsonb", "text", "bytea"]:
                return False

            # Check selectivity
            if n_distinct > 0 and row_count > 0:
                selectivity = n_distinct / row_count
                # Good selectivity is between 0.1 and 0.9
                if 0.1 <= selectivity <= 0.9:
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to check index candidate: {e}")
            return False

    def _estimate_index_storage(self, row_count: int) -> float:
        """Estimate index storage overhead in MB."""
        try:
            # Rough estimation: 8 bytes per row for index entry
            index_size_bytes = row_count * 8
            return index_size_bytes / (1024 * 1024)  # Convert to MB

        except Exception as e:
            logger.error(f"Failed to estimate index storage: {e}")
            return 0.0

    def _deduplicate_index_recommendations(
        self,
        recommendations: List[IndexRecommendation],
    ) -> List[IndexRecommendation]:
        """Remove duplicate index recommendations."""
        try:
            seen = set()
            unique_recommendations = []

            for rec in recommendations:
                # Create a key based on table and columns
                key = (rec.table_name, tuple(sorted(rec.column_names)))
                if key not in seen:
                    seen.add(key)
                    unique_recommendations.append(rec)

            return unique_recommendations

        except Exception as e:
            logger.error(f"Failed to deduplicate index recommendations: {e}")
            return recommendations

    async def _monitor_slow_queries(self) -> None:
        """Monitor slow queries and generate optimizations."""
        try:
            # Get slow queries from pg_stat_statements
            slow_queries_query = """
                SELECT 
                    query,
                    mean_exec_time,
                    calls,
                    total_exec_time
                FROM pg_stat_statements 
                WHERE mean_exec_time > $1
                ORDER BY mean_exec_time DESC
                LIMIT 10
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(
                    slow_queries_query, self._optimization_rules["slow_query_threshold"]
                )

                for row in results:
                    query = row[0]
                    mean_time = float(row[1])
                    calls = int(row[2])

                    # Generate optimizations for slow queries
                    try:
                        await self.optimize_query(
                            tenant_id="system",  # System-level monitoring
                            query=query,
                            optimization_types=[
                                QueryOptimizationType.INDEX_OPTIMIZATION,
                                QueryOptimizationType.QUERY_REWRITE,
                            ],
                        )
                    except Exception as e:
                        logger.error(f"Failed to optimize slow query: {e}")

        except Exception as e:
            logger.error(f"Failed to monitor slow queries: {e}")

    async def _update_optimization_recommendations(self) -> None:
        """Update optimization recommendations based on current data."""
        try:
            # This would analyze recent query patterns and update recommendations
            # For now, it's a placeholder
            pass

        except Exception as e:
            logger.error(f"Failed to update optimization recommendations: {e}")

    async def _check_index_usage(self) -> None:
        """Check index usage statistics."""
        try:
            # Get unused indexes
            unused_indexes_query = """
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes 
                WHERE idx_scan = 0
                ORDER BY schemaname, tablename, indexname
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(unused_indexes_query)

                for row in results:
                    logger.warning(
                        f"Unused index: {row[0]}.{row[1]}.{row[2]} "
                        f"(scans: {row[3]}, reads: {row[4]})"
                    )

        except Exception as e:
            logger.error(f"Failed to check index usage: {e}")

    async def _get_query_analyses(
        self,
        tenant_id: str,
        cutoff_time: datetime,
    ) -> List[QueryAnalysis]:
        """Get query analyses for report."""
        try:
            query = """
                SELECT * FROM query_analyses 
                WHERE tenant_id = $1 AND created_at > $2
                ORDER BY created_at DESC
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, tenant_id, cutoff_time)

                analyses = []
                for row in results:
                    analysis = QueryAnalysis(
                        id=row[0],
                        tenant_id=row[1],
                        original_query=row[2],
                        normalized_query=row[3],
                        execution_plan=json.loads(row[4]) if row[4] else {},
                        performance_metrics=json.loads(row[5]) if row[5] else {},
                        identified_issues=json.loads(row[6]) if row[6] else [],
                        optimization_opportunities=json.loads(row[7]) if row[7] else {},
                        complexity_score=row[8],
                        estimated_cost=row[9],
                        created_at=row[10],
                    )
                    analyses.append(analysis)

                return analyses

        except Exception as e:
            logger.error(f"Failed to get query analyses: {e}")
            return []

    async def _get_query_optimizations(
        self,
        tenant_id: str,
        cutoff_time: datetime,
    ) -> List[QueryOptimization]:
        """Get query optimizations for report."""
        try:
            query = """
                SELECT * FROM query_optimizations 
                WHERE tenant_id = $1 AND created_at > $2
                ORDER BY created_at DESC
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, tenant_id, cutoff_time)

                optimizations = []
                for row in results:
                    optimization = QueryOptimization(
                        id=row[0],
                        tenant_id=row[1],
                        query_id=row[2],
                        optimization_type=QueryOptimizationType(row[3]),
                        original_query=row[4],
                        optimized_query=row[5],
                        description=row[6],
                        performance_improvement=row[7],
                        implementation_complexity=row[8],
                        priority=OptimizationPriority(row[9]),
                        reasoning=row[10],
                        created_at=row[11],
                    )
                    optimizations.append(optimization)

                return optimizations

        except Exception as e:
            logger.error(f"Failed to get query optimizations: {e}")
            return []

    async def _get_index_recommendations(
        self,
        tenant_id: str,
        cutoff_time: datetime,
    ) -> List[IndexRecommendation]:
        """Get index recommendations for report."""
        try:
            query = """
                SELECT * FROM index_recommendations 
                WHERE tenant_id = $1 AND created_at > $2
                ORDER BY created_at DESC
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, tenant_id, cutoff_time)

                recommendations = []
                for row in results:
                    recommendation = IndexRecommendation(
                        id=row[0],
                        tenant_id=row[1],
                        table_name=row[2],
                        column_names=json.loads(row[3]) if row[3] else [],
                        index_type=row[4],
                        estimated_improvement=row[5],
                        storage_overhead=row[6],
                        priority=OptimizationPriority(row[7]),
                        query_patterns=json.loads(row[8]) if row[8] else [],
                        created_at=row[9],
                    )
                    recommendations.append(recommendation)

                return recommendations

        except Exception as e:
            logger.error(f"Failed to get index recommendations: {e}")
            return []

    async def _calculate_optimization_statistics(
        self,
        analyses: List[QueryAnalysis],
        optimizations: List[QueryOptimization],
        index_recommendations: List[IndexRecommendation],
    ) -> Dict[str, Any]:
        """Calculate optimization statistics."""
        try:
            stats = {}

            # Query analysis statistics
            if analyses:
                complexities = [a.complexity_score for a in analyses]
                costs = [a.estimated_cost for a in analyses]

                stats["query_analyses"] = {
                    "total_analyses": len(analyses),
                    "avg_complexity": sum(complexities) / len(complexities),
                    "avg_cost": sum(costs) / len(costs),
                    "max_complexity": max(complexities),
                    "max_cost": max(costs),
                }

            # Optimization statistics
            if optimizations:
                improvements = [o.performance_improvement for o in optimizations]
                priorities = [o.priority.value for o in optimizations]

                stats["optimizations"] = {
                    "total_optimizations": len(optimizations),
                    "avg_improvement": sum(improvements) / len(improvements),
                    "max_improvement": max(improvements),
                    "priority_distribution": {
                        "low": priorities.count("low"),
                        "medium": priorities.count("medium"),
                        "high": priorities.count("high"),
                        "critical": priorities.count("critical"),
                    },
                }

            # Index recommendation statistics
            if index_recommendations:
                improvements = [r.estimated_improvement for r in index_recommendations]
                overheads = [r.storage_overhead for r in index_recommendations]

                stats["index_recommendations"] = {
                    "total_recommendations": len(index_recommendations),
                    "avg_improvement": sum(improvements) / len(improvements),
                    "total_storage_overhead": sum(overheads),
                    "avg_storage_overhead": sum(overheads) / len(overheads),
                }

            return stats

        except Exception as e:
            logger.error(f"Failed to calculate optimization statistics: {e}")
            return {}

    async def _get_slow_queries(
        self,
        tenant_id: str,
        cutoff_time: datetime,
    ) -> List[Dict[str, Any]]:
        """Get slow queries for report."""
        try:
            query = """
                SELECT 
                    query,
                    mean_exec_time,
                    calls,
                    total_exec_time
                FROM pg_stat_statements 
                WHERE mean_exec_time > $1
                ORDER BY mean_exec_time DESC
                LIMIT 10
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, 1000)  # 1 second threshold

                slow_queries = []
                for row in results:
                    slow_queries.append(
                        {
                            "query": row[0][:200] + "..."
                            if len(row[0]) > 200
                            else row[0],
                            "mean_exec_time": float(row[1]),
                            "calls": int(row[2]),
                            "total_exec_time": float(row[3]),
                        }
                    )

                return slow_queries

        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []

    async def _get_optimization_trends(
        self,
        tenant_id: str,
        time_period_hours: int,
    ) -> Dict[str, Any]:
        """Get optimization trends over time."""
        try:
            # This would analyze trends in optimizations over time
            # For now, return placeholder data
            return {
                "query_complexity_trend": "stable",
                "optimization_effectiveness": "improving",
                "index_usage_trend": "stable",
            }

        except Exception as e:
            logger.error(f"Failed to get optimization trends: {e}")
            return {}


# Factory function
def create_query_optimizer(db_pool) -> QueryOptimizer:
    """Create query optimizer instance."""
    return QueryOptimizer(db_pool)
