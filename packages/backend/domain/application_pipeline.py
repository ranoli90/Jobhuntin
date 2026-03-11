"""
Application pipeline view for visualizing application stages and progress.

Provides:
  - Pipeline view with drag-and-drop stage management
  - Kanban-style board for application tracking
  - Stage analytics and conversion metrics
  - Bulk operations across pipeline stages
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from shared.logging_config import get_logger
from shared.sql_utils import escape_ilike

logger = get_logger("sorce.pipeline")

# Pipeline stages configuration
PIPELINE_STAGES = [
    {
        "id": "draft",
        "name": "Draft",
        "description": "Applications being prepared",
        "color": "#64748B",  # slate-500
        "order": 1,
    },
    {
        "id": "applying",
        "name": "Applying",
        "description": "Currently being submitted",
        "color": "#3B82F6",  # blue-500
        "order": 2,
    },
    {
        "id": "submitted",
        "name": "Submitted",
        "description": "Successfully submitted",
        "color": "#10B981",  # emerald-500
        "order": 3,
    },
    {
        "id": "under_review",
        "name": "Under Review",
        "description": "Being reviewed by employer",
        "color": "#F59E0B",  # amber-500
        "order": 4,
    },
    {
        "id": "interview",
        "name": "Interview",
        "description": "Interview scheduled/in progress",
        "color": "#8B5CF6",  # violet-500
        "order": 5,
    },
    {
        "id": "offer",
        "name": "Offer",
        "description": "Offer received/considered",
        "color": "#06B6D4",  # cyan-500
        "order": 6,
    },
    {
        "id": "accepted",
        "name": "Accepted",
        "description": "Offer accepted",
        "color": "#84CC16",  # lime-500
        "order": 7,
    },
    {
        "id": "rejected",
        "name": "Rejected",
        "description": "Application rejected",
        "color": "#EF4444",  # red-500
        "order": 8,
    },
    {
        "id": "withdrawn",
        "name": "Withdrawn",
        "description": "Application withdrawn",
        "color": "#6B7280",  # gray-500
        "order": 9,
    },
]


class PipelineStage(BaseModel):
    """Pipeline stage configuration."""

    id: str
    name: str
    description: str
    color: str
    order: int
    application_count: int = 0
    conversion_rate: float = 0.0


class PipelineApplication(BaseModel):
    """Application in pipeline view."""

    id: str
    company: str
    job_title: str
    current_stage: str
    stage_order: int
    last_activity: datetime
    priority: str = "normal"  # low, normal, high
    tags: List[str] = []
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    location: Optional[str] = None
    remote: bool = False
    days_in_stage: int = 0


class PipelineMetrics(BaseModel):
    """Pipeline performance metrics."""

    total_applications: int
    stage_distribution: Dict[str, int]
    conversion_rates: Dict[str, float]
    average_time_in_stage: Dict[str, float]
    rejection_rate: float
    offer_rate: float


class PipelineView(BaseModel):
    """Complete pipeline view."""

    stages: List[PipelineStage]
    applications: List[PipelineApplication]
    metrics: PipelineMetrics
    filters: Dict[str, Any] = {}
    sort_by: str = "last_activity"
    sort_order: str = "desc"


class ApplicationPipelineManager:
    """Manages application pipeline operations."""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def get_pipeline_view(
        self,
        tenant_id: str,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "last_activity",
        sort_order: str = "desc",
    ) -> PipelineView:
        """Get complete pipeline view for user."""

        async with self.db_pool.acquire() as conn:
            # Get applications with pipeline data
            query = """
            SELECT
                a.id,
                a.company,
                a.job_title,
                a.status,
                a.last_activity,
                a.priority,
                a.tags,
                a.salary_min,
                a.salary_max,
                a.location,
                a.remote,
                a.created_at,
                a.updated_at,
                j.title as job_title_full,
                c.name as company_name
            FROM applications a
            LEFT JOIN jobs j ON a.job_id = j.id
            LEFT JOIN companies c ON j.company_id = c.id
            WHERE a.tenant_id = $1 AND a.user_id = $2
            """

            params = [tenant_id, user_id]

            # Apply filters
            if filters:
                if "status" in filters:
                    query += " AND a.status = ANY($3)"
                    params.append(filters["status"])
                if "company" in filters:
                    query += " AND a.company ILIKE $%d" % (len(params) + 1)
                    params.append(f"%{escape_ilike(filters['company'])}%")
                if "priority" in filters:
                    query += " AND a.priority = $%d" % (len(params) + 1)
                    params.append(filters["priority"])

            # Apply sorting (whitelist sort_order to prevent SQL injection)
            valid_sort_fields = ["last_activity", "created_at", "company", "priority"]
            safe_order = sort_order.upper() if sort_order.upper() in ("ASC", "DESC") else "DESC"
            if sort_by in valid_sort_fields:
                query += f" ORDER BY a.{sort_by} {safe_order}"
            else:
                query += " ORDER BY a.last_activity DESC"

            rows = await conn.fetch(query, *params)

            # Map status to pipeline stage
            status_to_stage = {
                "DRAFT": "draft",
                "APPLYING": "applying",
                "APPLIED": "submitted",
                "HOLD": "under_review",
                "SUCCESS": "interview",
                "FAILED": "rejected",
                "REJECTED": "rejected",
                "WITHDRAWN": "withdrawn",
            }

            # Build pipeline applications
            applications = []
            stage_order_map = {stage["id"]: stage["order"] for stage in PIPELINE_STAGES}

            for row in rows:
                current_stage = status_to_stage.get(row["status"], "submitted")
                days_in_stage = self._calculate_days_in_stage(row)

                app = PipelineApplication(
                    id=str(row["id"]),
                    company=row["company_name"] or row["company"],
                    job_title=row["job_title_full"] or row["job_title"],
                    current_stage=current_stage,
                    stage_order=stage_order_map.get(current_stage, 3),
                    last_activity=row["last_activity"] or row["created_at"],
                    priority=row.get("priority", "normal"),
                    tags=row.get("tags", []) or [],
                    salary_min=row.get("salary_min"),
                    salary_max=row.get("salary_max"),
                    location=row.get("location"),
                    remote=row.get("remote", False),
                    days_in_stage=days_in_stage,
                )
                applications.append(app)

            # Build stages with counts
            stages = []
            stage_counts = {}
            for app in applications:
                stage_counts[app.current_stage] = (
                    stage_counts.get(app.current_stage, 0) + 1
                )

            for stage_config in PIPELINE_STAGES:
                stage = PipelineStage(
                    id=stage_config["id"],
                    name=stage_config["name"],
                    description=stage_config["description"],
                    color=stage_config["color"],
                    order=stage_config["order"],
                    application_count=stage_counts.get(stage_config["id"], 0),
                )
                stages.append(stage)

            # Calculate metrics
            metrics = await self._calculate_pipeline_metrics(
                conn, tenant_id, user_id, applications
            )

            return PipelineView(
                stages=stages,
                applications=applications,
                metrics=metrics,
                filters=filters or {},
                sort_by=sort_by,
                sort_order=sort_order,
            )

    async def update_application_stage(
        self,
        tenant_id: str,
        user_id: str,
        application_id: str,
        new_stage: str,
    ) -> bool:
        """Update application pipeline stage."""

        # Map pipeline stage back to status
        stage_to_status = {
            "draft": "DRAFT",
            "applying": "APPLYING",
            "submitted": "APPLIED",
            "under_review": "HOLD",
            "interview": "SUCCESS",
            "offer": "SUCCESS",
            "accepted": "SUCCESS",
            "rejected": "REJECTED",
            "withdrawn": "WITHDRAWN",
        }

        new_status = stage_to_status.get(new_stage, "APPLIED")

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE applications
                SET status = $1, updated_at = NOW()
                WHERE id = $2 AND tenant_id = $3 AND user_id = $4
                """,
                new_status,
                application_id,
                tenant_id,
                user_id,
            )

            logger.info(
                "Updated application %s stage to %s for user %s",
                application_id,
                new_stage,
                user_id,
            )

            return True

    async def bulk_update_stages(
        self,
        tenant_id: str,
        user_id: str,
        application_ids: List[str],
        new_stage: str,
    ) -> Dict[str, bool]:
        """Bulk update application stages."""

        results = {}
        for app_id in application_ids:
            try:
                success = await self.update_application_stage(
                    tenant_id, user_id, app_id, new_stage
                )
                results[app_id] = success
            except Exception as e:
                logger.error("Failed to update stage for %s: %s", app_id, e)
                results[app_id] = False

        return results

    def _calculate_days_in_stage(self, row: Dict[str, Any]) -> int:
        """Calculate days application has been in current stage."""
        if not row.get("last_activity"):
            return 0

        now = datetime.now(timezone.utc)
        last_activity = row["last_activity"].replace(tzinfo=timezone.utc)
        days = (now - last_activity).days
        return max(0, days)

    async def _calculate_pipeline_metrics(
        self,
        conn,
        tenant_id: str,
        user_id: str,
        applications: List[PipelineApplication],
    ) -> PipelineMetrics:
        """Calculate pipeline performance metrics."""

        total_apps = len(applications)

        # Stage distribution
        stage_distribution = {}
        for app in applications:
            stage_distribution[app.current_stage] = (
                stage_distribution.get(app.current_stage, 0) + 1
            )

        # Conversion rates (simplified)
        conversion_rates = {}
        total_submitted = stage_distribution.get("submitted", 0)
        if total_submitted > 0:
            conversion_rates["submitted_to_interview"] = (
                stage_distribution.get("interview", 0) / total_submitted
            )
            conversion_rates["submitted_to_offer"] = (
                stage_distribution.get("offer", 0) / total_submitted
            )

        # Average time in stage
        avg_time_in_stage = {}
        for stage_id in stage_distribution:
            stage_apps = [app for app in applications if app.current_stage == stage_id]
            if stage_apps:
                avg_time_in_stage[stage_id] = sum(
                    app.days_in_stage for app in stage_apps
                ) / len(stage_apps)

        # Rejection and offer rates
        rejection_rate = (
            stage_distribution.get("rejected", 0) / total_apps if total_apps > 0 else 0
        )
        offer_rate = (
            (stage_distribution.get("offer", 0) + stage_distribution.get("accepted", 0))
            / total_apps
            if total_apps > 0
            else 0
        )

        return PipelineMetrics(
            total_applications=total_apps,
            stage_distribution=stage_distribution,
            conversion_rates=conversion_rates,
            average_time_in_stage=avg_time_in_stage,
            rejection_rate=rejection_rate,
            offer_rate=offer_rate,
        )


# Factory function
def create_pipeline_manager(db_pool) -> ApplicationPipelineManager:
    """Create pipeline manager instance."""
    return ApplicationPipelineManager(db_pool)
