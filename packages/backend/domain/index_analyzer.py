"""
Index Analyzer for Phase 15.1 Database & Performance
"""

from __future__ import annotations

import asyncio
import json
import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from shared.logging_config import get_logger

logger = get_logger("sorce.index_analyzer")


class IndexType(Enum):
    """Types of database indexes."""

    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"
    GIST = "gist"
    SP_GIST = "spgist"
    BRIN = "brin"
    BITMAP = "bitmap"


class IndexStatus(Enum):
    """Index status."""

    ACTIVE = "active"
    UNUSED = "unused"
    INVALID = "invalid"
    REBUILDING = "rebuilding"


class IndexRecommendationType(Enum):
    """Types of index recommendations."""

    CREATE = "create"
    DROP = "drop"
    REBUILD = "rebuild"
    REORGANIZE = "reorganize"


@dataclass
class IndexInfo:
    """Index information."""

    index_name: str
    table_name: str
    index_type: IndexType
    column_names: List[str]
    is_unique: bool
    is_primary: bool
    is_partial: bool
    size_bytes: int
    size_pages: int
    scans: int
    tuples_read: int
    tuples_returned: int
    last_used: Optional[datetime]
    status: IndexStatus
    definition: str
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class IndexUsageStats:
    """Index usage statistics."""

    index_name: str
    table_name: str
    total_scans: int
    total_tuples_read: int
    total_tuples_returned: int
    avg_scan_time_ms: float
    avg_tuples_per_scan: float
    selectivity_ratio: float
    usage_frequency: float
    efficiency_score: float
    last_scan: Optional[datetime]
    period_start: datetime
    period_end: datetime


@dataclass
class IndexRecommendation:
    """Index recommendation."""

    id: str
    tenant_id: str
    recommendation_type: IndexRecommendationType
    index_name: Optional[str]
    table_name: str
    column_names: List[str]
    index_type: IndexType
    priority: str  # low, medium, high, critical
    impact_score: float
    implementation_cost: str  # low, medium, high
    reasoning: str
    sql_statement: Optional[str]
    estimated_benefit: str
    risks: List[str] = field(default_factory=list)
    created_at: datetime = datetime.now(timezone.utc)


@dataclass
class IndexAnalysis:
    """Index analysis result."""

    id: str
    tenant_id: str
    table_name: str
    total_indexes: int
    unused_indexes: List[IndexInfo]
    underutilized_indexes: List[IndexInfo]
    missing_indexes: List[IndexRecommendation]
    duplicate_indexes: List[List[IndexInfo]]
    oversized_indexes: List[IndexInfo]
    fragmentation_score: float
    optimization_potential: float
    recommendations: List[IndexRecommendation]
    created_at: datetime = datetime.now(timezone.utc)


class IndexAnalyzer:
    """Advanced database index analysis and optimization system."""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._analysis_cache: Dict[str, IndexAnalysis] = {}
        self._recommendation_cache: Dict[str, List[IndexRecommendation]] = {}
        self._index_patterns = self._initialize_index_patterns()
        self._query_patterns = self._initialize_query_patterns()

        # Start background analysis
        asyncio.create_task(self._start_index_monitoring())

    async def analyze_table_indexes(
        self,
        tenant_id: str,
        table_name: str,
        include_usage_stats: bool = True,
    ) -> IndexAnalysis:
        """Analyze indexes for a specific table."""
        try:
            # Get table indexes
            indexes = await self._get_table_indexes(tenant_id, table_name)

            # Get usage statistics
            usage_stats = {}
            if include_usage_stats:
                usage_stats = await self._get_index_usage_stats(tenant_id, table_name)

            # Identify unused indexes
            unused_indexes = await self._identify_unused_indexes(indexes, usage_stats)

            # Identify underutilized indexes
            underutilized_indexes = await self._identify_underutilized_indexes(
                indexes, usage_stats
            )

            # Find missing indexes
            missing_indexes = await self._identify_missing_indexes(
                tenant_id, table_name
            )

            # Find duplicate indexes
            duplicate_indexes = await self._identify_duplicate_indexes(indexes)

            # Find oversized indexes
            oversized_indexes = await self._identify_oversized_indexes(indexes)

            # Calculate fragmentation score
            fragmentation_score = await self._calculate_fragmentation_score(table_name)

            # Calculate optimization potential
            optimization_potential = await self._calculate_optimization_potential(
                unused_indexes, underutilized_indexes, missing_indexes
            )

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                tenant_id,
                table_name,
                unused_indexes,
                underutilized_indexes,
                missing_indexes,
                duplicate_indexes,
                oversized_indexes,
            )

            # Create analysis
            analysis = IndexAnalysis(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                table_name=table_name,
                total_indexes=len(indexes),
                unused_indexes=unused_indexes,
                underutilized_indexes=underutilized_indexes,
                missing_indexes=missing_indexes,
                duplicate_indexes=duplicate_indexes,
                oversized_indexes=oversized_indexes,
                fragmentation_score=fragmentation_score,
                optimization_potential=optimization_potential,
                recommendations=recommendations,
            )

            # Save analysis
            await self._save_index_analysis(analysis)

            # Update cache
            cache_key = f"{tenant_id}:{table_name}"
            self._analysis_cache[cache_key] = analysis

            logger.info(
                f"Index analysis completed for {table_name}: "
                f"{len(indexes)} indexes, {len(unused_indexes)} unused, "
                f"{len(missing_indexes)} missing"
            )

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze table indexes for {table_name}: {e}")
            raise

    async def analyze_database_indexes(
        self,
        tenant_id: str,
        table_filter: Optional[str] = None,
    ) -> Dict[str, IndexAnalysis]:
        """Analyze indexes for all tables or filtered tables."""
        try:
            # Get tables to analyze
            if table_filter:
                tables = [table_filter]
            else:
                tables = await self._get_user_tables(tenant_id)

            analyses = {}

            # Analyze each table
            for table_name in tables:
                try:
                    analysis = await self.analyze_table_indexes(tenant_id, table_name)
                    analyses[table_name] = analysis
                except Exception as e:
                    logger.error(f"Failed to analyze table {table_name}: {e}")
                    continue

            logger.info(
                f"Database index analysis completed: {len(analyses)} tables analyzed"
            )
            return analyses

        except Exception as e:
            logger.error(f"Failed to analyze database indexes: {e}")
            raise

    async def get_index_recommendations(
        self,
        tenant_id: str,
        table_name: Optional[str] = None,
        recommendation_type: Optional[IndexRecommendationType] = None,
        priority: Optional[str] = None,
    ) -> List[IndexRecommendation]:
        """Get index recommendations."""
        try:
            recommendations = []

            if table_name:
                # Get recommendations for specific table
                cache_key = f"{tenant_id}:{table_name}"
                if cache_key in self._analysis_cache:
                    analysis = self._analysis_cache[cache_key]
                    recommendations.extend(analysis.recommendations)
                else:
                    # Generate fresh analysis
                    analysis = await self.analyze_table_indexes(tenant_id, table_name)
                    recommendations.extend(analysis.recommendations)
            else:
                # Get recommendations for all tables
                analyses = await self.analyze_database_indexes(tenant_id)
                for analysis in analyses.values():
                    recommendations.extend(analysis.recommendations)

            # Filter by type
            if recommendation_type:
                recommendations = [
                    r
                    for r in recommendations
                    if r.recommendation_type == recommendation_type
                ]

            # Filter by priority
            if priority:
                recommendations = [r for r in recommendations if r.priority == priority]

            # Sort by impact score
            recommendations.sort(key=lambda r: r.impact_score, reverse=True)

            return recommendations

        except Exception as e:
            logger.error(f"Failed to get index recommendations: {e}")
            return []

    async def implement_recommendation(
        self,
        tenant_id: str,
        recommendation_id: str,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """Implement an index recommendation."""
        try:
            # Get recommendation
            recommendation = await self._get_recommendation_by_id(
                recommendation_id, tenant_id
            )
            if not recommendation:
                raise ValueError("Recommendation not found")

            result = {}

            if recommendation.recommendation_type == IndexRecommendationType.CREATE:
                result = await self._implement_create_index(recommendation, dry_run)
            elif recommendation.recommendation_type == IndexRecommendationType.DROP:
                result = await self._implement_drop_index(recommendation, dry_run)
            elif recommendation.recommendation_type == IndexRecommendationType.REBUILD:
                result = await self._implement_rebuild_index(recommendation, dry_run)
            elif (
                recommendation.recommendation_type == IndexRecommendationType.REORGANIZE
            ):
                result = await self._implement_reorganize_index(recommendation, dry_run)

            return {
                "recommendation_id": recommendation_id,
                "recommendation_type": recommendation.recommendation_type.value,
                "dry_run": dry_run,
                "result": result,
                "executed_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to implement recommendation {recommendation_id}: {e}")
            raise

    async def get_index_health_report(
        self,
        tenant_id: str,
        time_period_days: int = 7,
    ) -> Dict[str, Any]:
        """Get comprehensive index health report."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=time_period_days)

            # Get all analyses
            analyses = await self._get_index_analyses(tenant_id, cutoff_time)

            # Calculate overall statistics
            total_tables = len(analyses)
            total_indexes = sum(a.total_indexes for a in analyses.values())
            total_unused = sum(len(a.unused_indexes) for a in analyses.values())
            total_missing = sum(len(a.missing_indexes) for a in analyses.values())
            avg_fragmentation = (
                sum(a.fragmentation_score for a in analyses.values()) / len(analyses)
                if analyses
                else 0
            )
            avg_optimization_potential = (
                sum(a.optimization_potential for a in analyses.values()) / len(analyses)
                if analyses
                else 0
            )

            # Get recommendations
            recommendations = await self.get_index_recommendations(tenant_id)

            # Group recommendations by type
            recommendations_by_type = defaultdict(list)
            for rec in recommendations:
                recommendations_by_type[rec.recommendation_type.value].append(rec)

            # Get top problematic tables
            problematic_tables = sorted(
                analyses.items(),
                key=lambda x: x[1].optimization_potential,
                reverse=True,
            )[:10]

            report = {
                "period_days": time_period_days,
                "summary": {
                    "total_tables": total_tables,
                    "total_indexes": total_indexes,
                    "unused_indexes": total_unused,
                    "missing_indexes": total_missing,
                    "avg_fragmentation_score": avg_fragmentation,
                    "avg_optimization_potential": avg_optimization_potential,
                },
                "recommendations_by_type": {
                    k: len(v) for k, v in recommendations_by_type.items()
                },
                "total_recommendations": len(recommendations),
                "problematic_tables": [
                    {
                        "table_name": table,
                        "optimization_potential": analysis.optimization_potential,
                        "unused_count": len(analysis.unused_indexes),
                        "missing_count": len(analysis.missing_indexes),
                        "fragmentation_score": analysis.fragmentation_score,
                    }
                    for table, analysis in problematic_tables
                ],
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            return report

        except Exception as e:
            logger.error(f"Failed to generate index health report: {e}")
            return {}

    def _initialize_index_patterns(self) -> Dict[str, List[str]]:
        """Initialize common index patterns."""
        return {
            "primary_key": [
                r"PRIMARY KEY",
                r"CONSTRAINT.+PRIMARY KEY",
            ],
            "unique": [
                r"UNIQUE INDEX",
                r"CONSTRAINT.+UNIQUE",
            ],
            "foreign_key": [
                r"FOREIGN KEY",
                r"REFERENCES",
            ],
            "composite": [
                r"INDEX\s+\w+\s*\([^)]+\)",
                r"INDEX\s+\w+\s*\([^,]+,",
            ],
            "partial": [
                r"WHERE\s+\w+\s*IS\s*NOT\s*NULL",
                r"WHERE\s+\w+\s*=\s*",
            ],
        }

    def _initialize_query_patterns(self) -> Dict[str, List[str]]:
        """Initialize query patterns for index analysis."""
        return {
            "select_where": [
                r"SELECT\s+.+\s+FROM\s+.+\s+WHERE\s+",
                r"WHERE\s+\w+\s*=",
                r"WHERE\s+\w+\s*IN\s*\(",
                r"WHERE\s+\w+\s*LIKE",
            ],
            "join": [
                r"JOIN\s+.+\s+ON",
                r"LEFT\s+JOIN",
                r"RIGHT\s+JOIN",
                r"INNER\s+JOIN",
            ],
            "order_by": [
                r"ORDER\s+BY\s+",
                r"GROUP\s+BY\s+",
            ],
            "range_queries": [
                r"WHERE\s+\w+\s*>\s*",
                r"WHERE\s+\w+\s*<\s*",
                r"WHERE\s+\w+\s*BETWEEN",
            ],
        }

    async def _start_index_monitoring(self) -> None:
        """Start background index monitoring."""
        try:
            while True:
                await asyncio.sleep(3600)  # Run every hour

                # Monitor index usage
                await self._monitor_index_usage()

                # Update recommendations
                await self._update_recommendations()

                # Check for index issues
                await self._check_index_issues()

        except Exception as e:
            logger.error(f"Background index monitoring failed: {e}")

    async def _get_table_indexes(
        self, tenant_id: str, table_name: str
    ) -> List[IndexInfo]:
        """Get all indexes for a table."""
        try:
            # Get index information from PostgreSQL
            query = """
                SELECT 
                    i.schemaname,
                    i.tablename,
                    i.indexname,
                    i.indexdef,
                    idx.indisunique,
                    idx.indisprimary,
                    pg_size_pretty(pg_relation_size(idx.indexrelid::regclass)) as size,
                    pg_relation_size(idx.indexrelid::regclass) as size_bytes,
                    pg_relation_size(idx.indexrelid::regclass) / 8192 as size_pages,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch,
                    am.last_used
                FROM pg_indexes i
                JOIN pg_class idx ON i.indexrelid = idx.oid
                LEFT JOIN pg_stat_user_indexes ON idx.oid = pg_stat_user_indexes.indexrelid
                LEFT JOIN pg_stat_all_indexes ON idx.oid = pg_stat_all_indexes.indexrelid
                WHERE i.tablename = $1
                ORDER BY i.indexname
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, table_name)

                indexes = []
                for row in results:
                    # Parse column names from index definition
                    column_names = self._parse_index_columns(row[3])

                    # Determine index type
                    index_type = self._determine_index_type(row[3])

                    # Parse last used timestamp
                    last_used = None
                    if row[12]:
                        try:
                            last_used = datetime.fromisoformat(row[12])
                        except (ValueError, TypeError):
                            pass

                    index_info = IndexInfo(
                        index_name=row[2],
                        table_name=table_name,
                        index_type=index_type,
                        column_names=column_names,
                        is_unique=row[4],
                        is_primary=row[5],
                        is_partial="WHERE" in row[3].upper(),
                        size_bytes=int(row[7]) if row[7] else 0,
                        size_pages=int(row[8]) if row[8] else 0,
                        scans=int(row[9]) if row[9] else 0,
                        tuples_read=int(row[10]) if row[10] else 0,
                        tuples_returned=int(row[11]) if row[11] else 0,
                        last_used=last_used,
                        status=IndexStatus.ACTIVE,
                        definition=row[3],
                    )

                    indexes.append(index_info)

                return indexes

        except Exception as e:
            logger.error(f"Failed to get table indexes for {table_name}: {e}")
            return []

    def _parse_index_columns(self, index_definition: str) -> List[str]:
        """Parse column names from index definition."""
        try:
            # Extract columns from CREATE INDEX or PRIMARY KEY definition
            match = re.search(r"\(([^)]+)\)", index_definition)
            if match:
                columns_str = match.group(1)
                # Split by comma and clean up
                columns = []
                for col in columns_str.split(","):
                    col = col.strip()
                    # Remove any function calls or expressions
                    if "(" not in col and ")" not in col:
                        columns.append(col)
                    else:
                        # For complex expressions, try to extract the column name
                        col_match = re.search(r"\b\w+\b", col)
                        if col_match:
                            columns.append(col_match.group(0))
                return columns

            return []

        except Exception as e:
            logger.error(f"Failed to parse index columns: {e}")
            return []

    def _determine_index_type(self, index_definition: str) -> IndexType:
        """Determine index type from definition."""
        try:
            definition_upper = index_definition.upper()

            if "USING GIN" in definition_upper:
                return IndexType.GIN
            elif "USING GIST" in definition_upper:
                return IndexType.GIST
            elif "USING SPGIST" in definition_upper:
                return IndexType.SP_GIST
            elif "USING BRIN" in definition_upper:
                return IndexType.BRIN
            elif "USING HASH" in definition_upper:
                return IndexType.HASH
            elif "USING BITMAP" in definition_upper:
                return IndexType.BITMAP
            else:
                return IndexType.BTREE  # Default

        except Exception as e:
            logger.error(f"Failed to determine index type: {e}")
            return IndexType.BTREE

    async def _get_index_usage_stats(
        self, tenant_id: str, table_name: str
    ) -> Dict[str, IndexUsageStats]:
        """Get index usage statistics."""
        try:
            query = """
                SELECT 
                    indexrelname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch,
                    (SELECT EXTRACT(EPOCH FROM (now() - last_used)) * 1000) as last_used_ms
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                AND indexrelname IN (
                    SELECT indexname FROM pg_indexes WHERE tablename = $1
                )
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, table_name)

                usage_stats = {}
                period_start = datetime.now(timezone.utc) - timedelta(days=7)
                period_end = datetime.now(timezone.utc)

                for row in results:
                    index_name = row[0]
                    scans = int(row[1]) if row[1] else 0
                    tuples_read = int(row[2]) if row[2] else 0
                    tuples_returned = int(row[3]) if row[3] else 0

                    # Calculate derived metrics
                    avg_scan_time_ms = 10.0  # Estimated
                    avg_tuples_per_scan = tuples_read / scans if scans > 0 else 0
                    selectivity_ratio = (
                        tuples_returned / tuples_read if tuples_read > 0 else 0
                    )
                    usage_frequency = scans / 7.0  # Per day
                    efficiency_score = (
                        min(1.0, (tuples_returned / scans) / 1000) if scans > 0 else 0
                    )

                    stats = IndexUsageStats(
                        index_name=index_name,
                        table_name=table_name,
                        total_scans=scans,
                        total_tuples_read=tuples_read,
                        total_tuples_returned=tuples_returned,
                        avg_scan_time_ms=avg_scan_time_ms,
                        avg_tuples_per_scan=avg_tuples_per_scan,
                        selectivity_ratio=selectivity_ratio,
                        usage_frequency=usage_frequency,
                        efficiency_score=efficiency_score,
                        last_scan=datetime.now(timezone.utc)
                        - timedelta(milliseconds=row[4])
                        if row[4]
                        else None,
                        period_start=period_start,
                        period_end=period_end,
                    )

                    usage_stats[index_name] = stats

                return usage_stats

        except Exception as e:
            logger.error(f"Failed to get index usage stats for {table_name}: {e}")
            return {}

    async def _identify_unused_indexes(
        self,
        indexes: List[IndexInfo],
        usage_stats: Dict[str, IndexUsageStats],
    ) -> List[IndexInfo]:
        """Identify unused indexes."""
        try:
            unused_indexes = []

            for index in indexes:
                # Skip primary key indexes
                if index.is_primary:
                    continue

                # Check usage statistics
                stats = usage_stats.get(index.index_name)
                if not stats:
                    # No usage stats, assume unused
                    unused_indexes.append(index)
                    continue

                # Check if index has been used recently
                if stats.total_scans == 0:
                    unused_indexes.append(index)
                elif (
                    stats.last_scan
                    and (datetime.now(timezone.utc) - stats.last_scan).days > 30
                ):
                    unused_indexes.append(index)
                elif stats.usage_frequency < 0.1:  # Less than 0.1 scans per day
                    unused_indexes.append(index)

            return unused_indexes

        except Exception as e:
            logger.error(f"Failed to identify unused indexes: {e}")
            return []

    async def _identify_underutilized_indexes(
        self,
        indexes: List[IndexInfo],
        usage_stats: Dict[str, IndexUsageStats],
    ) -> List[IndexInfo]:
        """Identify underutilized indexes."""
        try:
            underutilized_indexes = []

            for index in indexes:
                # Skip primary key indexes
                if index.is_primary:
                    continue

                # Check usage statistics
                stats = usage_stats.get(index.index_name)
                if not stats:
                    continue

                # Check efficiency score
                if stats.efficiency_score < 0.3:  # Low efficiency
                    underutilized_indexes.append(index)
                elif stats.usage_frequency < 1.0:  # Less than 1 scan per day
                    underutilized_indexes.append(index)
                elif stats.avg_tuples_per_scan < 10:  # Returns few tuples per scan
                    underutilized_indexes.append(index)

            return underutilized_indexes

        except Exception as e:
            logger.error(f"Failed to identify underutilized indexes: {e}")
            return []

    async def _identify_missing_indexes(
        self,
        tenant_id: str,
        table_name: str,
    ) -> List[IndexRecommendation]:
        """Identify missing indexes."""
        try:
            recommendations = []

            # Get table statistics
            table_stats = await self._get_table_statistics(table_name)
            if not table_stats:
                return recommendations

            # Get query patterns from pg_stat_statements
            query_patterns = await self._get_query_patterns_for_table(table_name)

            # Analyze WHERE clauses for missing indexes
            for pattern in query_patterns:
                if pattern.get("type") == "where_clause":
                    columns = pattern.get("columns", [])
                    if len(columns) == 1:
                        # Single column index recommendation
                        col_name = columns[0]
                        if self._should_create_index(col_name, table_stats):
                            rec = IndexRecommendation(
                                id=str(uuid.uuid4()),
                                tenant_id=tenant_id,
                                recommendation_type=IndexRecommendationType.CREATE,
                                index_name=None,
                                table_name=table_name,
                                column_names=[col_name],
                                index_type=IndexType.BTREE,
                                priority="medium",
                                impact_score=0.7,
                                implementation_cost="low",
                                reasoning=f"WHERE clause frequently uses {col_name}",
                                sql_statement=f"CREATE INDEX idx_{table_name}_{col_name} ON {table_name} ({col_name})",
                                estimated_benefit="Improved query performance for {col_name} filters",
                            )
                            recommendations.append(rec)
                    elif len(columns) > 1:
                        # Composite index recommendation
                        if self._should_create_composite_index(columns, table_stats):
                            col_list = ", ".join(columns)
                            index_name = f"idx_{table_name}_{'_'.join(columns)}"
                            rec = IndexRecommendation(
                                id=str(uuid.uuid4()),
                                tenant_id=tenant_id,
                                recommendation_type=IndexRecommendationType.CREATE,
                                index_name=index_name,
                                table_name=table_name,
                                column_names=columns,
                                index_type=IndexType.BTREE,
                                priority="high",
                                impact_score=0.8,
                                implementation_cost="medium",
                                reasoning=f"WHERE clause frequently uses combination of {col_list}",
                                sql_statement=f"CREATE INDEX {index_name} ON {table_name} ({col_list})",
                                estimated_benefit="Improved query performance for multi-column filters",
                            )
                            recommendations.append(rec)

            # Check for ORDER BY indexes
            for pattern in query_patterns:
                if pattern.get("type") == "order_by":
                    columns = pattern.get("columns", [])
                    if columns and not self._has_existing_index(table_name, columns):
                        col_list = ", ".join(columns)
                        index_name = f"idx_{table_name}_{'_'.join(columns)}"
                        rec = IndexRecommendation(
                            id=str(uuid.uuid4()),
                            tenant_id=tenant_id,
                            recommendation_type=IndexRecommendationType.CREATE,
                            index_name=index_name,
                            table_name=table_name,
                            column_names=columns,
                            index_type=IndexType.BTREE,
                            priority="medium",
                            impact_score=0.6,
                            implementation_cost="low",
                            reasoning=f"ORDER BY clause uses {col_list}",
                            sql_statement=f"CREATE INDEX {index_name} ON {table_name} ({col_list})",
                            estimated_benefit="Improved sorting performance",
                        )
                        recommendations.append(rec)

            return recommendations

        except Exception as e:
            logger.error(f"Failed to identify missing indexes: {e}")
            return []

    async def _identify_duplicate_indexes(
        self,
        indexes: List[IndexInfo],
    ) -> List[List[IndexInfo]]:
        """Identify duplicate indexes."""
        try:
            duplicate_groups = []

            # Group indexes by column combinations
            column_groups = defaultdict(list)
            for index in indexes:
                # Skip primary keys and unique indexes
                if index.is_primary or index.is_unique:
                    continue

                # Create a normalized key for column combination
                columns_key = tuple(sorted(index.column_names))
                column_groups[columns_key].append(index)

            # Find groups with multiple indexes
            for columns_key, group_indexes in column_groups.items():
                if len(group_indexes) > 1:
                    duplicate_groups.append(group_indexes)

            return duplicate_groups

        except Exception as e:
            logger.error(f"Failed to identify duplicate indexes: {e}")
            return []

    async def _identify_oversized_indexes(
        self,
        indexes: List[IndexInfo],
    ) -> List[IndexInfo]:
        """Identify oversized indexes."""
        try:
            oversized_indexes = []

            for index in indexes:
                # Consider indexes larger than 100MB as oversized
                if index.size_bytes > 100 * 1024 * 1024:  # 100 MB
                    oversized_indexes.append(index)
                elif index.size_pages > 10000:  # More than 10,000 pages
                    oversized_indexes.append(index)

            return oversized_indexes

        except Exception as e:
            logger.error(f"Failed to identify oversized indexes: {e}")
            return []

    async def _calculate_fragmentation_score(self, table_name: str) -> float:
        """Calculate index fragmentation score."""
        try:
            # Get table and index statistics
            query = """
                SELECT 
                    pg_size_pretty(pg_total_relation_size($1)) as table_size,
                    pg_size_pretty(pg_indexes_size($1)) as indexes_size,
                    (SELECT COUNT(*) FROM pg_stat_user_indexes WHERE schemaname = 'public' AND indexrelid IN (
                        SELECT indexrelid FROM pg_indexes WHERE tablename = $1
                    )) as index_count
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, table_name)

                if not result:
                    return 0.0

                # Simple fragmentation calculation based on index size vs table size
                # This is a simplified approach
                index_count = int(result[2]) if result[2] else 0
                if index_count == 0:
                    return 0.0

                # Higher fragmentation for more indexes relative to table size
                fragmentation_score = min(1.0, index_count / 20.0)

                return fragmentation_score

        except Exception as e:
            logger.error(
                f"Failed to calculate fragmentation score for {table_name}: {e}"
            )
            return 0.0

    async def _calculate_optimization_potential(
        self,
        unused_indexes: List[IndexInfo],
        underutilized_indexes: List[IndexInfo],
        missing_indexes: List[IndexRecommendation],
    ) -> float:
        """Calculate optimization potential score."""
        try:
            potential = 0.0

            # Potential from dropping unused indexes
            potential += len(unused_indexes) * 0.8

            # Potential from optimizing underutilized indexes
            potential += len(underutilized_indexes) * 0.5

            # Potential from creating missing indexes
            potential += len(missing_indexes) * 0.9

            return min(1.0, potential / 10.0)  # Normalize to 0-1 range

        except Exception as e:
            logger.error(f"Failed to calculate optimization potential: {e}")
            return 0.0

    async def _generate_recommendations(
        self,
        tenant_id: str,
        table_name: str,
        unused_indexes: List[IndexInfo],
        underutilized_indexes: List[IndexInfo],
        missing_indexes: List[IndexRecommendation],
        duplicate_indexes: List[List[IndexInfo]],
        oversized_indexes: List[IndexInfo],
    ) -> List[IndexRecommendation]:
        """Generate index recommendations."""
        try:
            recommendations = []

            # Drop unused indexes
            for index in unused_indexes:
                rec = IndexRecommendation(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    recommendation_type=IndexRecommendationType.DROP,
                    index_name=index.index_name,
                    table_name=table_name,
                    column_names=index.column_names,
                    index_type=index.index_type,
                    priority="low",
                    impact_score=0.3,
                    implementation_cost="low",
                    reasoning=f"Index {index.index_name} is unused",
                    sql_statement=f"DROP INDEX {index.index_name}",
                    estimated_benefit=f"Free {index.size_bytes / (1024 * 1024):.1f} MB of storage",
                    risks=["Potential performance impact if index is actually needed"],
                )
                recommendations.append(rec)

            # Rebuild underutilized indexes
            for index in underutilized_indexes:
                rec = IndexRecommendation(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    recommendation_type=IndexRecommendationType.REBUILD,
                    index_name=index.index_name,
                    table_name=table_name,
                    column_names=index.column_names,
                    index_type=index.index_type,
                    priority="medium",
                    impact_score=0.4,
                    implementation_cost="medium",
                    reasoning=f"Index {index.index_name} is underutilized",
                    sql_statement=f"REINDEX INDEX {index.index_name}",
                    estimated_benefit="Improved index performance and reduced storage",
                    risks=["Temporary performance impact during rebuild"],
                )
                recommendations.append(rec)

            # Add missing index recommendations
            recommendations.extend(missing_indexes)

            # Handle duplicate indexes
            for duplicate_group in duplicate_indexes:
                # Keep the most efficient index and drop others
                best_index = max(
                    duplicate_group, key=lambda i: i.scans if i.scans else 0
                )
                for index in duplicate_group:
                    if index != best_index:
                        rec = IndexRecommendation(
                            id=str(uuid.uuid4()),
                            tenant_id=tenant_id,
                            recommendation_type=IndexRecommendationType.DROP,
                            index_name=index.index_name,
                            table_name=table_name,
                            column_names=index.column_names,
                            index_type=index.index_type,
                            priority="low",
                            impact_score=0.2,
                            implementation_cost="low",
                            reasoning=f"Duplicate index {index.index_name} (redundant with {best_index.index_name})",
                            sql_statement=f"DROP INDEX {index.index_name}",
                            estimated_benefit=f"Free {index.size_bytes / (1024 * 1024):.1f} MB of storage",
                            risks=[
                                "Potential performance impact if index is actually needed"
                            ],
                        )
                        recommendations.append(rec)

            # Reorganize oversized indexes
            for index in oversized_indexes:
                rec = IndexRecommendation(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    recommendation_type=IndexRecommendationType.REORGANIZE,
                    index_name=index.index_name,
                    table_name=table_name,
                    column_names=index.column_names,
                    index_type=index.index_type,
                    priority="medium",
                    impact_score=0.5,
                    implementation_cost="high",
                    reasoning=f"Index {index.index_name} is oversized ({index.size_bytes / (1024 * 1024):.1f} MB)",
                    sql_statement=f"REINDEX INDEX {index.index_name}",
                    estimated_benefit="Reduced storage and improved performance",
                    risks=["Temporary performance impact during reorganization"],
                )
                recommendations.append(rec)

            # Sort by impact score
            recommendations.sort(key=lambda r: r.impact_score, reverse=True)

            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return []

    async def _save_index_analysis(self, analysis: IndexAnalysis) -> None:
        """Save index analysis to database."""
        try:
            query = """
                INSERT INTO index_analyses (
                    id, tenant_id, table_name, total_indexes, unused_indexes,
                    underutilized_indexes, missing_indexes, duplicate_indexes,
                    oversized_indexes, fragmentation_score, optimization_potential,
                    recommendations, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """

            params = [
                analysis.id,
                analysis.tenant_id,
                analysis.table_name,
                analysis.total_indexes,
                json.dumps(analysis.unused_indexes),
                json.dumps(analysis.underutilized_indexes),
                json.dumps(analysis.missing_indexes),
                json.dumps(analysis.duplicate_indexes),
                json.dumps(analysis.oversized_indexes),
                analysis.fragmentation_score,
                analysis.optimization_potential,
                json.dumps(analysis.recommendations),
                analysis.created_at,
            ]

            async with self.db_pool.acquire() as conn:
                await conn.execute(query, *params)

        except Exception as e:
            logger.error(f"Failed to save index analysis: {e}")

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

    async def _get_table_statistics(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get table statistics."""
        try:
            query = """
                SELECT 
                    n_tup_ins,
                    n_tup_upd,
                    n_tup_del,
                    n_live_tup,
                    n_dead_tup
                FROM pg_stat_user_tables 
                WHERE schemaname = 'public' AND relname = $1
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, table_name)

                if result:
                    return {
                        "inserts": result[0],
                        "updates": result[1],
                        "deletes": result[2],
                        "live_rows": result[3],
                        "dead_rows": result[4],
                    }

                return None

        except Exception as e:
            logger.error(f"Failed to get table statistics for {table_name}: {e}")
            return None

    async def _get_query_patterns_for_table(
        self, table_name: str
    ) -> List[Dict[str, Any]]:
        """Get query patterns for a table from pg_stat_statements."""
        try:
            query = """
                SELECT 
                    query,
                    calls,
                    mean_exec_time
                FROM pg_stat_statements 
                WHERE query LIKE $1 || '%'
                ORDER BY calls DESC
                LIMIT 20
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, f"%{table_name}%")

                patterns = []
                for row in results:
                    query_text = row[0].upper()

                    # Extract WHERE clause columns
                    where_match = re.search(
                        r"WHERE\s+(.+?)(?:\s+ORDER\s+BY|\s+GROUP\s+BY|\s+LIMIT|$)",
                        query_text,
                    )
                    if where_match:
                        where_clause = where_match.group(1)
                        columns = self._extract_columns_from_clause(where_clause)
                        if columns:
                            patterns.append(
                                {
                                    "type": "where_clause",
                                    "columns": columns,
                                    "calls": int(row[1]),
                                    "avg_time": float(row[2]),
                                }
                            )

                    # Extract ORDER BY columns
                    order_match = re.search(
                        r"ORDER\s+BY\s+(.+?)(?:\s+LIMIT|$)", query_text
                    )
                    if order_match:
                        order_clause = order_match.group(1)
                        columns = self._extract_columns_from_clause(order_clause)
                        if columns:
                            patterns.append(
                                {
                                    "type": "order_by",
                                    "columns": columns,
                                    "calls": int(row[1]),
                                    "avg_time": float(row[2]),
                                }
                            )

                return patterns

        except Exception as e:
            logger.error(f"Failed to get query patterns for {table_name}: {e}")
            return []

    def _extract_columns_from_clause(self, clause: str) -> List[str]:
        """Extract column names from SQL clause."""
        try:
            # Remove functions and expressions
            clause = re.sub(r"\([^)]*\)", "", clause)

            # Split by common separators
            columns = []
            for part in re.split(r"[,+\s]+", clause):
                part = part.strip()
                if part and not any(
                    op in part
                    for op in ["=", ">", "<", ">=", "<=", "!=", "LIKE", "IN", "IS"]
                ):
                    columns.append(part)

            return list(set(columns))  # Remove duplicates

        except Exception as e:
            logger.error(f"Failed to extract columns from clause: {e}")
            return []

    def _should_create_index(
        self, column_name: str, table_stats: Dict[str, Any]
    ) -> bool:
        """Check if index should be created for a column."""
        try:
            # Skip certain column types
            skip_types = ["json", "jsonb", "text", "bytea"]
            if any(skip_type in column_name.lower() for skip_type in skip_types):
                return False

            # Check cardinality
            if table_stats and table_stats.get("live_rows", 0) > 1000:
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to check if index should be created: {e}")
            return False

    def _should_create_composite_index(
        self, columns: List[str], table_stats: Dict[str, Any]
    ) -> bool:
        """Check if composite index should be created."""
        try:
            # Need at least 2 columns
            if len(columns) < 2:
                return False

            # Skip if too many columns (performance impact)
            if len(columns) > 5:
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to check if composite index should be created: {e}")
            return False

    def _has_existing_index(self, table_name: str, columns: List[str]) -> bool:
        """Check if index already exists for given columns."""
        try:
            # This would check against existing indexes
            # For now, return False (assume no check)
            return False

        except Exception as e:
            logger.error(f"Failed to check existing index: {e}")
            return False

    async def _get_recommendation_by_id(
        self,
        recommendation_id: str,
        tenant_id: str,
    ) -> Optional[IndexRecommendation]:
        """Get recommendation by ID."""
        try:
            query = """
                SELECT * FROM index_recommendations 
                WHERE id = $1 AND tenant_id = $2
            """

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, recommendation_id, tenant_id)

                if result:
                    return IndexRecommendation(
                        id=result[0],
                        tenant_id=result[1],
                        recommendation_type=IndexRecommendationType(result[2]),
                        index_name=result[3],
                        table_name=result[4],
                        column_names=json.loads(result[5]) if result[5] else [],
                        index_type=IndexType(result[6]),
                        priority=result[7],
                        impact_score=result[8],
                        implementation_cost=result[9],
                        reasoning=result[10],
                        sql_statement=result[11],
                        estimated_benefit=result[12],
                        risks=json.loads(result[13]) if result[13] else [],
                        created_at=result[14],
                    )

                return None

        except Exception as e:
            logger.error(f"Failed to get recommendation by ID: {e}")
            return None

    async def _implement_create_index(
        self,
        recommendation: IndexRecommendation,
        dry_run: bool,
    ) -> Dict[str, Any]:
        """Implement CREATE INDEX recommendation."""
        try:
            if dry_run:
                return {
                    "success": True,
                    "message": "Dry run: Index would be created",
                    "sql": recommendation.sql_statement,
                }

            # Execute CREATE INDEX
            async with self.db_pool.acquire() as conn:
                await conn.execute(recommendation.sql_statement)

            return {
                "success": True,
                "message": "Index created successfully",
                "index_name": recommendation.index_name,
            }

        except Exception as e:
            logger.error(f"Failed to implement CREATE INDEX: {e}")
            return {"success": False, "error": str(e)}

    async def _implement_drop_index(
        self,
        recommendation: IndexRecommendation,
        dry_run: bool,
    ) -> Dict[str, Any]:
        """Implement DROP INDEX recommendation."""
        try:
            if dry_run:
                return {
                    "success": True,
                    "message": "Dry run: Index would be dropped",
                    "sql": recommendation.sql_statement,
                }

            # Execute DROP INDEX
            async with self.db_pool.acquire() as conn:
                await conn.execute(recommendation.sql_statement)

            return {
                "success": True,
                "message": "Index dropped successfully",
                "index_name": recommendation.index_name,
            }

        except Exception as e:
            logger.error(f"Failed to implement DROP INDEX: {e}")
            return {"success": False, "error": str(e)}

    async def _implement_rebuild_index(
        self,
        recommendation: IndexRecommendation,
        dry_run: bool,
    ) -> Dict[str, Any]:
        """Implement REINDEX INDEX recommendation."""
        try:
            if dry_run:
                return {
                    "success": True,
                    "message": "Dry run: Index would be rebuilt",
                    "sql": recommendation.sql_statement,
                }

            # Execute REINDEX
            async with self.db_pool.acquire() as conn:
                await conn.execute(recommendation.sql_statement)

            return {
                "success": True,
                "message": "Index rebuilt successfully",
                "index_name": recommendation.index_name,
            }

        except Exception as e:
            logger.error(f"Failed to implement REINDEX INDEX: {e}")
            return {"success": False, "error": str(e)}

    async def _implement_reorganize_index(
        self,
        recommendation: IndexRecommendation,
        dry_run: bool,
    ) -> Dict[str, Any]:
        """Implement index reorganization."""
        try:
            if dry_run:
                return {
                    "success": True,
                    "message": "Dry run: Index would be reorganized",
                    "sql": recommendation.sql_statement,
                }

            # For reorganization, we typically use VACUUM FULL or REINDEX
            async with self.db_pool.acquire() as conn:
                await conn.execute(f"VACUUM FULL {recommendation.table_name}")

            return {
                "success": True,
                "message": "Index reorganized successfully",
                "table_name": recommendation.table_name,
            }

        except Exception as e:
            logger.error(f"Failed to implement index reorganization: {e}")
            return {"success": False, "error": str(e)}

    async def _get_index_analyses(
        self,
        tenant_id: str,
        cutoff_time: datetime,
    ) -> Dict[str, IndexAnalysis]:
        """Get index analyses for report."""
        try:
            query = """
                SELECT * FROM index_analyses 
                WHERE tenant_id = $1 AND created_at > $2
                ORDER BY created_at DESC
            """

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, tenant_id, cutoff_time)

                analyses = {}
                for row in results:
                    analysis = IndexAnalysis(
                        id=row[0],
                        tenant_id=row[1],
                        table_name=row[2],
                        total_indexes=row[3],
                        unused_indexes=json.loads(row[4]) if row[4] else [],
                        underutilized_indexes=json.loads(row[5]) if row[5] else [],
                        missing_indexes=json.loads(row[6]) if row[6] else [],
                        duplicate_indexes=json.loads(row[7]) if row[7] else [],
                        oversized_indexes=json.loads(row[8]) if row[8] else [],
                        fragmentation_score=row[9],
                        optimization_potential=row[10],
                        recommendations=json.loads(row[11]) if row[11] else [],
                        created_at=row[12],
                    )
                    analyses[analysis.table_name] = analysis

                return analyses

        except Exception as e:
            logger.error(f"Failed to get index analyses: {e}")
            return {}

    async def _monitor_index_usage(self) -> None:
        """Monitor index usage and update statistics."""
        try:
            # This would collect index usage statistics
            # For now, it's a placeholder
            pass

        except Exception as e:
            logger.error(f"Failed to monitor index usage: {e}")

    async def _update_recommendations(self) -> None:
        """Update index recommendations based on current data."""
        try:
            # This would update existing recommendations
            # For now, it's a placeholder
            pass

        except Exception as e:
            logger.error(f"Failed to update recommendations: {e}")

    async def _check_index_issues(self) -> None:
        """Check for index-related issues."""
        try:
            # This would check for index fragmentation, bloat, etc.
            # For now, it's a placeholder
            pass

        except Exception as e:
            logger.error(f"Failed to check index issues: {e}")


# Factory function
def create_index_analyzer(db_pool) -> IndexAnalyzer:
    """Create index analyzer instance."""
    return IndexAnalyzer(db_pool)
