"""
Enhanced application export functionality with multiple formats and filters.

Provides:
  - Export applications to CSV, Excel, PDF formats
  - Advanced filtering and custom field selection
  - Scheduled exports and email delivery
  - Export templates and branding options
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from shared.logging_config import get_logger
from shared.sql_utils import escape_ilike

logger = get_logger("sorce.application_export")

router = APIRouter(tags=["application_export"])

# Export formats
EXPORT_FORMATS = ["csv", "xlsx", "pdf", "json"]

# Default export fields
DEFAULT_FIELDS = [
    "company",
    "job_title",
    "status",
    "last_activity",
    "created_at",
    "salary_min",
    "salary_max",
    "location",
    "remote",
    "priority",
    "tags",
]

# All available fields
ALL_FIELDS = [
    "id",
    "company",
    "job_title",
    "status",
    "last_activity",
    "created_at",
    "updated_at",
    "salary_min",
    "salary_max",
    "location",
    "remote",
    "priority",
    "tags",
    "job_description",
    "company_description",
    "application_notes",
    "resume_used",
    "cover_letter_used",
    "source",
    "referral",
]


class ExportConfig(BaseModel):
    """Export configuration."""

    format: str = "csv"
    fields: List[str] = DEFAULT_FIELDS
    filters: Dict[str, Any] = {}
    include_headers: bool = True
    date_format: str = "%Y-%m-%d %H:%M:%S"
    filename_prefix: str = "applications"
    compress: bool = False


class ApplicationExportManager:
    """Manages application data export."""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def export_applications(
        self,
        tenant_id: str,
        user_id: str,
        config: ExportConfig,
    ) -> StreamingResponse:
        """Export applications with specified configuration."""

        # Validate format
        if config.format not in EXPORT_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format. Supported: {', '.join(EXPORT_FORMATS)}",
            )

        # Validate fields
        invalid_fields = set(config.fields) - set(ALL_FIELDS)
        if invalid_fields:
            raise HTTPException(
                status_code=400, detail=f"Invalid fields: {', '.join(invalid_fields)}"
            )

        # Get application data
        data = await self._get_application_data(tenant_id, user_id, config)

        # Generate export based on format
        if config.format == "csv":
            return await self._export_csv(data, config)
        elif config.format == "xlsx":
            return await self._export_excel(data, config)
        elif config.format == "json":
            return await self._export_json(data, config)
        elif config.format == "pdf":
            return await self._export_pdf(data, config)

        raise HTTPException(status_code=400, detail="Export format not implemented")

    async def _get_application_data(
        self,
        tenant_id: str,
        user_id: str,
        config: ExportConfig,
    ) -> List[Dict[str, Any]]:
        """Get application data based on filters and fields."""

        async with self.db_pool.acquire() as conn:
            # Build query
            query = """
            SELECT
                a.id,
                a.company,
                a.job_title,
                a.status,
                a.last_activity,
                a.created_at,
                a.updated_at,
                a.salary_min,
                a.salary_max,
                a.location,
                a.remote,
                a.priority,
                a.tags,
                a.source,
                a.referral,
                j.description as job_description,
                c.description as company_description
            FROM applications a
            LEFT JOIN jobs j ON a.job_id = j.id
            LEFT JOIN companies c ON j.company_id = c.id
            WHERE a.tenant_id = $1 AND a.user_id = $2
            """

            params = [tenant_id, user_id]
            param_idx = 3

            # Apply filters
            if config.filters:
                if "status" in config.filters:
                    query += f" AND a.status = ANY(${param_idx})"
                    params.append(config.filters["status"])
                    param_idx += 1

                if "company" in config.filters:
                    query += f" AND a.company ILIKE ${param_idx}"
                    params.append(f"%{escape_ilike(config.filters['company'])}%")
                    param_idx += 1

                if "date_from" in config.filters:
                    query += f" AND a.created_at >= ${param_idx}"
                    params.append(config.filters["date_from"])
                    param_idx += 1

                if "date_to" in config.filters:
                    query += f" AND a.created_at <= ${param_idx}"
                    params.append(config.filters["date_to"])
                    param_idx += 1

                if "priority" in config.filters:
                    query += f" AND a.priority = ${param_idx}"
                    params.append(config.filters["priority"])
                    param_idx += 1

            # Order by
            query += " ORDER BY a.created_at DESC"

            rows = await conn.fetch(query, *params)

            # Convert to dict format
            data = []
            for row in rows:
                row_dict = dict(row)

                # Format dates
                for date_field in ["created_at", "updated_at", "last_activity"]:
                    if row_dict.get(date_field):
                        row_dict[date_field] = row_dict[date_field].strftime(
                            config.date_format
                        )

                # Handle tags array
                if row_dict.get("tags"):
                    row_dict["tags"] = ", ".join(row_dict["tags"])
                else:
                    row_dict["tags"] = ""

                # Handle boolean
                row_dict["remote"] = "Yes" if row_dict.get("remote") else "No"

                data.append(row_dict)

            return data

    async def _export_csv(
        self,
        data: List[Dict[str, Any]],
        config: ExportConfig,
    ) -> StreamingResponse:
        """Export to CSV format."""

        output = io.StringIO()

        if data:
            # Filter to requested fields
            filtered_data = []
            for row in data:
                filtered_row = {field: row.get(field, "") for field in config.fields}
                filtered_data.append(filtered_row)

            writer = csv.DictWriter(output, fieldnames=config.fields)

            if config.include_headers:
                writer.writeheader()

            writer.writerows(filtered_data)

        output.seek(0)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{config.filename_prefix}_{timestamp}.csv"

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    async def _export_excel(
        self,
        data: List[Dict[str, Any]],
        config: ExportConfig,
    ) -> StreamingResponse:
        """Export to Excel format."""

        if not data:
            df = pd.DataFrame(columns=config.fields)
        else:
            # Filter to requested fields
            filtered_data = []
            for row in data:
                filtered_row = {field: row.get(field, "") for field in config.fields}
                filtered_data.append(filtered_row)

            df = pd.DataFrame(filtered_data)

        # Create Excel file in memory
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(
                writer, sheet_name="Applications", index=not config.include_headers
            )

            # Auto-adjust column widths
            worksheet = writer.sheets["Applications"]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except Exception:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        output.seek(0)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{config.filename_prefix}_{timestamp}.xlsx"

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    async def _export_json(
        self,
        data: List[Dict[str, Any]],
        config: ExportConfig,
    ) -> StreamingResponse:
        """Export to JSON format."""

        # Filter to requested fields
        filtered_data = []
        for row in data:
            filtered_row = {field: row.get(field, "") for field in config.fields}
            filtered_data.append(filtered_row)

        import json

        output = io.StringIO()
        json.dump(filtered_data, output, indent=2, ensure_ascii=False)
        output.seek(0)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{config.filename_prefix}_{timestamp}.json"

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    async def _export_pdf(
        self,
        data: List[Dict[str, Any]],
        config: ExportConfig,
    ) -> StreamingResponse:
        """Export to PDF format using reportlab."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)

        # Container for the 'Flowable' objects
        elements = []

        styles = getSampleStyleSheet()

        # Add title
        title = Paragraph("Applications Export", styles["Title"])
        elements.append(title)
        elements.append(Spacer(1, 12))

        if data:
            # Filter to requested fields
            table_data = []

            if config.include_headers:
                table_data.append(config.fields)

            for row in data:
                table_row = [str(row.get(field, "")) for field in config.fields]
                table_data.append(table_row)

            # Create table
            table = Table(table_data)

            # Add style
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 14),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )

            elements.append(table)
        else:
            no_data = Paragraph(
                "No applications found matching the criteria.", styles["Normal"]
            )
            elements.append(no_data)

        # Build PDF
        doc.build(elements)
        output.seek(0)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{config.filename_prefix}_{timestamp}.pdf"

        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    async def get_export_templates(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get available export templates."""

        templates = [
            {
                "id": "basic",
                "name": "Basic Export",
                "description": "Essential application information",
                "fields": ["company", "job_title", "status", "last_activity"],
                "format": "csv",
            },
            {
                "id": "detailed",
                "name": "Detailed Export",
                "description": "Complete application data with all fields",
                "fields": ALL_FIELDS,
                "format": "xlsx",
            },
            {
                "id": "analytics",
                "name": "Analytics Export",
                "description": "Data optimized for analysis",
                "fields": [
                    "company",
                    "job_title",
                    "status",
                    "salary_min",
                    "salary_max",
                    "location",
                    "remote",
                    "created_at",
                ],
                "format": "csv",
            },
            {
                "id": "report",
                "name": "Report Export",
                "description": "Formatted for reporting and presentations",
                "fields": [
                    "company",
                    "job_title",
                    "status",
                    "last_activity",
                    "priority",
                ],
                "format": "pdf",
            },
        ]

        return templates

    async def schedule_export(
        self,
        tenant_id: str,
        user_id: str,
        config: ExportConfig,
        schedule: Dict[str, Any],
    ) -> str:
        """Schedule recurring export.

        Stub: Returns a synthetic export_id. Full implementation would:
        - Persist schedule to DB (cron expression, timezone)
        - Register with a scheduler (e.g. APScheduler, Celery Beat)
        - Trigger export_run on schedule.
        """
        # Placeholder for scheduled export — not yet wired to a scheduler
        export_id = str(uuid.uuid4())

        logger.info(
            "Scheduled export %s for user %s with schedule %s",
            export_id,
            user_id,
            schedule,
        )

        return export_id


# Factory function
def create_export_manager(db_pool) -> ApplicationExportManager:
    """Create export manager instance."""
    return ApplicationExportManager(db_pool)
