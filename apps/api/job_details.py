"""Job Details API endpoints for comprehensive job information."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.domain.repositories import JobRepo
from backend.domain.tenant import TenantContext
from shared.logging_config import get_logger

logger = get_logger("sorce.job_details")

router = APIRouter(tags=["job_details"])


class JobDetailsResponse(BaseModel):
    """Response model for job details."""

    id: str = Field(..., description="Job ID")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    remote: bool = Field(..., description="Whether job is remote")
    salary_min: Optional[float] = Field(default=None, description="Minimum salary")
    salary_max: Optional[float] = Field(default=None, description="Maximum salary")
    job_type: Optional[str] = Field(default=None, description="Job type")
    description: Optional[str] = Field(default=None, description="Job description")
    requirements: List[str] = Field(default=[], description="Job requirements")
    responsibilities: List[str] = Field(default=[], description="Job responsibilities")
    qualifications: List[str] = Field(default=[], description="Job qualifications")
    benefits: List[str] = Field(default=[], description="Job benefits")
    work_environment: List[str] = Field(default=[], description="Work environment")
    company_name: Optional[str] = Field(default=None, description="Company name")
    company_description: Optional[str] = Field(
        default=None, description="Company description"
    )
    company_logo_url: Optional[str] = Field(
        default=None, description="Company logo URL"
    )
    company_size: Optional[str] = Field(default=None, description="Company size")
    company_industry: Optional[str] = Field(
        default=None, description="Company industry"
    )
    company_culture: Optional[str] = Field(default=None, description="Company culture")
    company_values: List[str] = Field(default=[], description="Company values")
    company_technologies: List[str] = Field(
        default=[], description="Company technologies"
    )
    company_benefits: List[str] = Field(default=[], description="Company benefits")
    company_work_style: Optional[str] = Field(
        default=None, description="Company work style"
    )
    company_growth_stage: Optional[str] = Field(
        default=None, description="Company growth stage"
    )
    company_funding_stage: Optional[str] = Field(
        default=None, description="Company funding stage"
    )
    company_headquarters_location: Optional[str] = Field(
        default=None, description="Company headquarters location"
    )
    employee_count: Optional[int] = Field(default=None, description="Employee count")
    founded_year: Optional[int] = Field(default=None, description="Founded year")
    company_website: Optional[str] = Field(default=None, description="Company website")
    company_linkedin_url: Optional[str] = Field(
        default=None, description="Company LinkedIn URL"
    )
    created_at: str = Field(..., description="Job creation timestamp")
    updated_at: str = Field(..., description="Job update timestamp")
    is_active: bool = Field(..., description="Whether job is active")
    source: Optional[str] = Field(default=None, description="Job source")
    job_level: Optional[str] = Field(default=None, description="Job level")
    experience_years_min: Optional[int] = Field(
        default=None, description="Minimum years of experience"
    )
    experience_years_max: Optional[int] = Field(
        default=None, description="Maximum years of experience"
    )
    education_required: Optional[str] = Field(
        default=None, description="Required education"
    )
    skills_required: List[str] = Field(default=[], description="Required skills")
    industry_focus: Optional[str] = Field(default=None, description="Industry focus")
    remote_option: Optional[str] = Field(default=None, description="Remote work option")
    visa_sponsorship: Optional[bool] = Field(
        default=None, description="Visa sponsorship available"
    )
    deadline: Optional[str] = Field(default=None, description="Application deadline")
    application_url: Optional[str] = Field(default=None, description="Application URL")
    team_size: Optional[int] = Field(default=None, description="Team size")
    team_structure: Optional[str] = Field(default=None, description="Team structure")
    reporting_to: Optional[str] = Field(default=None, description="Reporting to")
    tags: List[str] = Field(default=[], description="Job tags")


class JobListResponse(BaseModel):
    """Response model for job listings."""

    jobs: List[JobDetailsResponse] = Field(..., description="List of jobs")
    total_count: int = Field(..., description="Total number of jobs")
    limit: int = Field(..., description="Number of jobs returned")
    offset: int = Field(..., description="Offset for pagination")


class JobFilters(BaseModel):
    """Model for job search filters."""

    location: Optional[str] = Field(default=None, description="Location filter")
    remote: Optional[bool] = Field(default=None, description="Remote work filter")
    job_type: Optional[str] = Field(default=None, description="Job type filter")
    company_size: Optional[str] = Field(default=None, description="Company size filter")
    industry: Optional[str] = Field(default=None, description="Industry filter")
    salary_min: Optional[float] = Field(
        default=None, description="Minimum salary filter"
    )
    salary_max: Optional[float] = Field(
        default=None, description="Maximum salary filter"
    )
    keywords: Optional[str] = Field(default=None, description="Keyword search")
    company_name: Optional[str] = Field(default=None, description="Company name filter")


def _get_pool():
    """Database pool dependency."""
    raise NotImplementedError("Pool dependency not injected")


def _get_tenant_ctx():
    """Tenant context dependency."""
    raise NotImplementedError("Tenant context dependency not injected")


@router.get("/{job_id}")
async def get_job_details(
    job_id: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> JobDetailsResponse:
    """Get comprehensive job details by ID.

    Args:
        job_id: Job identifier
        ctx: Tenant context for identification

    Returns:
        Comprehensive job details
    """
    from shared.validators import validate_uuid

    try:
        validate_uuid(job_id, "job_id")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    try:
        from backend.domain.repositories import get_pool

        async with get_pool().acquire() as conn:
            job_data = await JobRepo.get_by_id(conn, job_id)

            if not job_data:
                raise HTTPException(
                    status_code=404, detail=f"Job with ID {job_id} not found"
                )

            logger.info(
                f"Retrieved job details for {job_id} for tenant {ctx.tenant_id}"
            )
            return JobDetailsResponse(**job_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job details for {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve job details.")


@router.get("/")
async def list_jobs(
    ctx: TenantContext = Depends(_get_tenant_ctx),
    limit: int = Query(
        default=20, ge=1, le=100, description="Number of jobs to return"
    ),
    offset: int = Query(default=0, ge=0, le=1000, description="Offset for pagination"),
    location: Optional[str] = Query(default=None, description="Location filter"),
    remote: Optional[bool] = Query(default=None, description="Remote work filter"),
    job_type: Optional[str] = Query(default=None, description="Job type filter"),
    company_size: Optional[str] = Query(
        default=None, description="Company size filter"
    ),
    industry: Optional[str] = Query(default=None, description="Industry filter"),
    salary_min: Optional[float] = Query(
        default=None, description="Minimum salary filter"
    ),
    salary_max: Optional[float] = Query(
        default=None, description="Maximum salary filter"
    ),
    keywords: Optional[str] = Query(default=None, description="Keyword search"),
    company_name: Optional[str] = Query(
        default=None, description="Company name filter"
    ),
) -> JobListResponse:
    """List jobs with comprehensive details and filtering.

    Args:
        ctx: Tenant context for identification
        limit: Number of jobs to return
        offset: Offset for pagination
        location: Location filter
        remote: Remote work filter
        job_type: Job type filter
        company_size: Company size filter
        industry: Industry filter
        salary_min: Minimum salary filter
        salary_max: Maximum salary filter
        keywords: Keyword search
        company_name: Company name filter

    Returns:
        List of jobs with pagination info
    """
    try:
        from backend.domain.repositories import get_pool

        # Build filters
        filters = {}
        if location:
            filters["location"] = location
        if remote is not None:
            filters["remote"] = remote
        if job_type:
            filters["job_type"] = job_type
        if company_size:
            filters["company_size"] = company_size
        if industry:
            filters["industry"] = industry
        if salary_min is not None:
            filters["salary_min"] = salary_min
        if salary_max is not None:
            filters["salary_max"] = salary_max
        if keywords:
            filters["keywords"] = keywords
        if company_name:
            filters["company_name"] = company_name

        async with get_pool().acquire() as conn:
            jobs = await JobRepo.list_jobs(
                conn,
                limit=limit,
                offset=offset,
                filters=filters,
                tenant_id=ctx.tenant_id,
                user_id=ctx.user_id,
            )

            # Get total count for pagination
            # HIGH: Fix pagination total count - apply same filters to count query
            count_query = "SELECT COUNT(*) as total FROM public.jobs j LEFT JOIN public.companies c ON j.company_id = c.id WHERE j.is_active = true"
            count_params: list[Any] = []
            count_param_index = 1

            # Apply same filters to count query
            if filters:
                if "location" in filters and filters.get("location"):
                    count_query += f" AND j.location ILIKE ${count_param_index}"
                    count_params.append(f"%{filters['location']}%")
                    count_param_index += 1
                if "remote" in filters and filters.get("remote") is not None:
                    count_query += f" AND j.remote = ${count_param_index}"
                    count_params.append(filters["remote"])
                    count_param_index += 1
                if "job_type" in filters and filters.get("job_type"):
                    count_query += f" AND j.job_type = ${count_param_index}"
                    count_params.append(filters["job_type"])
                    count_param_index += 1
                if "company_size" in filters and filters.get("company_size"):
                    count_query += f" AND c.size = ${count_param_index}"
                    count_params.append(filters["company_size"])
                    count_param_index += 1
                if "industry" in filters and filters.get("industry"):
                    count_query += f" AND c.industry = ${count_param_index}"
                    count_params.append(filters["industry"])
                    count_param_index += 1
                if "salary_min" in filters and filters.get("salary_min") is not None:
                    count_query += f" AND j.salary_min >= ${count_param_index}"
                    count_params.append(filters["salary_min"])
                    count_param_index += 1
                if "salary_max" in filters and filters.get("salary_max") is not None:
                    count_query += f" AND j.salary_max <= ${count_param_index}"
                    count_params.append(filters["salary_max"])
                    count_param_index += 1

            total_result = await conn.fetchrow(count_query, *count_params)
            total_count = total_result["total"] if total_result else 0

            logger.info(f"Listed {len(jobs)} jobs for tenant {ctx.tenant_id}")

            return JobListResponse(
                jobs=[JobDetailsResponse(**job) for job in jobs],
                total_count=total_count,
                limit=limit,
                offset=offset,
            )

    except Exception as e:
        logger.error(f"Failed to list jobs for tenant {ctx.tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve job listings.")


@router.get("/search")
async def search_jobs(
    q: str = Query(..., description="Search query"),
    ctx: TenantContext = Depends(_get_tenant_ctx),
    limit: int = Query(
        default=20, ge=1, le=100, description="Number of jobs to return"
    ),
    offset: int = Query(default=0, ge=0, le=1000, description="Offset for pagination"),
) -> JobListResponse:
    """Search jobs by keywords.

    Args:
        q: Search query
        ctx: Tenant context for identification
        limit: Number of jobs to return
        offset: Offset for pagination

    Returns:
        List of matching jobs with pagination info
    """
    try:
        from backend.domain.repositories import get_pool

        filters = {"keywords": q}

        async with get_pool().acquire() as conn:
            jobs = await JobRepo.list_jobs(
                conn,
                limit=limit,
                offset=offset,
                filters=filters,
                tenant_id=ctx.tenant_id,
                user_id=ctx.user_id,
            )

            # Get total count for search results
            count_query = """
                SELECT COUNT(*) as total
                FROM public.jobs
                WHERE is_active = true
                    AND (title ILIKE $1 OR description ILIKE $1 OR company ILIKE $1)
            """
            total_result = await conn.fetchrow(count_query, f"%{q}%")
            total_count = total_result["total"]

            logger.info(
                f"Search for '{q}' returned {len(jobs)} jobs for tenant {ctx.tenant_id}"
            )

            return JobListResponse(
                jobs=[JobDetailsResponse(**job) for job in jobs],
                total_count=total_count,
                limit=limit,
                offset=offset,
            )

    except Exception as e:
        logger.error(f"Failed to search jobs for tenant {ctx.tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to search jobs.")


@router.get("/companies/{company_name}")
async def get_company_jobs(
    company_name: str,
    ctx: TenantContext = Depends(_get_tenant_ctx),
    limit: int = Query(
        default=20, ge=1, le=100, description="Number of jobs to return"
    ),
    offset: int = Query(default=0, ge=0, le=1000, description="Offset for pagination"),
) -> JobListResponse:
    """Get jobs for a specific company.

    Args:
        company_name: Company name
        ctx: Tenant context for identification
        limit: Number of jobs to return
        offset: Offset for pagination

    Returns:
        List of company jobs with pagination info
    """
    try:
        from backend.domain.repositories import get_pool

        filters = {"company_name": company_name}

        async with get_pool().acquire() as conn:
            jobs = await JobRepo.list_jobs(
                conn,
                limit=limit,
                offset=offset,
                filters=filters,
                tenant_id=ctx.tenant_id,
                user_id=ctx.user_id,
            )

            # Get total count for company jobs
            count_query = """
                SELECT COUNT(*) as total
                FROM public.jobs
                WHERE is_active = true AND company ILIKE $1
            """
            total_result = await conn.fetchrow(count_query, f"%{company_name}%")
            total_count = total_result["total"]

            logger.info(
                f"Retrieved {len(jobs)} jobs for company {company_name} for tenant {ctx.tenant_id}"
            )

            return JobListResponse(
                jobs=[JobDetailsResponse(**job) for job in jobs],
                total_count=total_count,
                limit=limit,
                offset=offset,
            )

    except Exception as e:
        logger.error(f"Failed to get company jobs for {company_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve company jobs.")


@router.get("/filters/options")
async def get_filter_options(
    ctx: TenantContext = Depends(_get_tenant_ctx),
) -> Dict[str, Any]:
    """Get available filter options for job search.

    Args:
        ctx: Tenant context for identification

    Returns:
        Available filter options
    """
    try:
        from backend.domain.repositories import get_pool

        async with get_pool().acquire() as conn:
            # Get unique values for filters
            locations = await conn.fetch("""
                SELECT DISTINCT location, COUNT(*) as count
                FROM public.jobs
                WHERE is_active = true AND location IS NOT NULL
                GROUP BY location
                ORDER BY count DESC
                LIMIT 20
            """)

            job_types = await conn.fetch("""
                SELECT DISTINCT job_type, COUNT(*) as count
                FROM public.jobs
                WHERE is_active = true AND job_type IS NOT NULL
                GROUP BY job_type
                ORDER BY count DESC
            """)

            company_sizes = await conn.fetch("""
                SELECT DISTINCT c.size, COUNT(*) as count
                FROM public.jobs j
                LEFT JOIN public.companies c ON j.company_id = c.id
                WHERE j.is_active = true AND c.size IS NOT NULL
                GROUP BY c.size
                ORDER BY count DESC
            """)

            industries = await conn.fetch("""
                SELECT DISTINCT c.industry, COUNT(*) as count
                FROM public.jobs j
                LEFT JOIN public.companies c ON j.company_id = c.id
                WHERE j.is_active = true AND c.industry IS NOT NULL
                GROUP BY c.industry
                ORDER BY count DESC
            """)

            return {
                "locations": [
                    {"name": row["location"], "count": row["count"]}
                    for row in locations
                ],
                "job_types": [
                    {"name": row["job_type"], "count": row["count"]}
                    for row in job_types
                ],
                "company_sizes": [
                    {"name": row["size"], "count": row["count"]}
                    for row in company_sizes
                ],
                "industries": [
                    {"name": row["industry"], "count": row["count"]}
                    for row in industries
                ],
            }

    except Exception as e:
        logger.error(f"Failed to get filter options for tenant {ctx.tenant_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve filter options."
        )
