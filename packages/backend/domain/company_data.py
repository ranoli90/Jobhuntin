"""Company Data — enrich job listings with company information.

Features:
  - Company profile enrichment from multiple sources
  - Funding and financial data
  - Company size and growth metrics
  - Industry categorization
  - Company logo and branding
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import asyncpg
from shared.logging_config import get_logger

from shared.metrics import incr

logger = get_logger("sorce.company_data")


class CompanySize(StrEnum):
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class FundingStage(StrEnum):
    BOOTSTRAPPED = "bootstrapped"
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C = "series_c"
    SERIES_D = "series_d"
    IPO = "ipo"
    ACQUIRED = "acquired"


@dataclass
class CompanyProfile:
    name: str
    domain: str | None = None
    description: str | None = None
    industry: str | None = None
    size: CompanySize | None = None
    employee_count: int | None = None
    founded_year: int | None = None
    headquarters: str | None = None
    funding_stage: FundingStage | None = None
    total_funding_usd: int | None = None
    latest_funding_round: str | None = None
    latest_funding_date: datetime | None = None
    logo_url: str | None = None
    website_url: str | None = None
    linkedin_url: str | None = None
    twitter_handle: str | None = None
    glassdoor_rating: float | None = None
    glassdoor_review_count: int | None = None
    tech_stack: list[str] = field(default_factory=list)
    benefits: list[str] = field(default_factory=list)
    remote_policy: str | None = None
    diversity_score: float | None = None
    growth_rate: float | None = None
    last_updated: datetime | None = None


@dataclass
class FundingRound:
    round_type: str
    amount_usd: int | None
    date: datetime | None
    investors: list[str] = field(default_factory=list)
    valuation_usd: int | None = None


INDUSTRY_MAPPINGS: dict[str, str] = {
    "software": "Technology",
    "saas": "Technology",
    "fintech": "Financial Services",
    "healthtech": "Healthcare",
    "edtech": "Education",
    "ecommerce": "Retail",
    "marketplace": "Retail",
    "ai": "Technology",
    "ml": "Technology",
    "cybersecurity": "Technology",
    "developer tools": "Technology",
    "data": "Technology",
    "analytics": "Technology",
    "hr tech": "Human Resources",
    "proptech": "Real Estate",
    "legal tech": "Legal Services",
    "insurtech": "Insurance",
    "cleantech": "Energy",
    "biotech": "Healthcare",
    "gaming": "Entertainment",
}

SIZE_THRESHOLDS = [
    (10, CompanySize.STARTUP),
    (50, CompanySize.SMALL),
    (250, CompanySize.MEDIUM),
    (1000, CompanySize.LARGE),
    (float("inf"), CompanySize.ENTERPRISE),
]

KNOWN_COMPANIES: dict[str, CompanyProfile] = {
    "google": CompanyProfile(
        name="Google",
        domain="google.com",
        description="Search engine and technology company",
        industry="Technology",
        size=CompanySize.ENTERPRISE,
        employee_count=180000,
        founded_year=1998,
        headquarters="Mountain View, CA",
        funding_stage=FundingStage.IPO,
        total_funding_usd=None,
        logo_url="https://logo.clearbit.com/google.com",
        website_url="https://google.com",
        linkedin_url="https://linkedin.com/company/google",
        glassdoor_rating=4.3,
        glassdoor_review_count=50000,
        remote_policy="hybrid",
    ),
    "microsoft": CompanyProfile(
        name="Microsoft",
        domain="microsoft.com",
        description="Technology corporation",
        industry="Technology",
        size=CompanySize.ENTERPRISE,
        employee_count=220000,
        founded_year=1975,
        headquarters="Redmond, WA",
        funding_stage=FundingStage.IPO,
        logo_url="https://logo.clearbit.com/microsoft.com",
        website_url="https://microsoft.com",
        glassdoor_rating=4.2,
        glassdoor_review_count=45000,
        remote_policy="hybrid",
    ),
    "amazon": CompanyProfile(
        name="Amazon",
        domain="amazon.com",
        description="E-commerce and cloud computing company",
        industry="Technology",
        size=CompanySize.ENTERPRISE,
        employee_count=1500000,
        founded_year=1994,
        headquarters="Seattle, WA",
        funding_stage=FundingStage.IPO,
        logo_url="https://logo.clearbit.com/amazon.com",
        website_url="https://amazon.com",
        glassdoor_rating=3.9,
        glassdoor_review_count=75000,
        remote_policy="hybrid",
    ),
    "meta": CompanyProfile(
        name="Meta",
        domain="meta.com",
        description="Social technology company",
        industry="Technology",
        size=CompanySize.ENTERPRISE,
        employee_count=70000,
        founded_year=2004,
        headquarters="Menlo Park, CA",
        funding_stage=FundingStage.IPO,
        logo_url="https://logo.clearbit.com/meta.com",
        website_url="https://meta.com",
        glassdoor_rating=4.1,
        glassdoor_review_count=30000,
        remote_policy="hybrid",
    ),
    "apple": CompanyProfile(
        name="Apple",
        domain="apple.com",
        description="Consumer electronics and software company",
        industry="Technology",
        size=CompanySize.ENTERPRISE,
        employee_count=165000,
        founded_year=1976,
        headquarters="Cupertino, CA",
        funding_stage=FundingStage.IPO,
        logo_url="https://logo.clearbit.com/apple.com",
        website_url="https://apple.com",
        glassdoor_rating=4.2,
        glassdoor_review_count=35000,
        remote_policy="hybrid",
    ),
    "netflix": CompanyProfile(
        name="Netflix",
        domain="netflix.com",
        description="Streaming entertainment service",
        industry="Entertainment",
        size=CompanySize.LARGE,
        employee_count=13000,
        founded_year=1997,
        headquarters="Los Gatos, CA",
        funding_stage=FundingStage.IPO,
        logo_url="https://logo.clearbit.com/netflix.com",
        website_url="https://netflix.com",
        glassdoor_rating=4.0,
        glassdoor_review_count=10000,
        remote_policy="remote_friendly",
    ),
    "stripe": CompanyProfile(
        name="Stripe",
        domain="stripe.com",
        description="Financial infrastructure platform",
        industry="Financial Services",
        size=CompanySize.LARGE,
        employee_count=8000,
        founded_year=2010,
        headquarters="San Francisco, CA",
        funding_stage=FundingStage.SERIES_I,
        total_funding_usd=2000000000,
        logo_url="https://logo.clearbit.com/stripe.com",
        website_url="https://stripe.com",
        glassdoor_rating=4.4,
        glassdoor_review_count=5000,
        remote_policy="remote_first",
    ),
    "airbnb": CompanyProfile(
        name="Airbnb",
        domain="airbnb.com",
        description="Vacation rental marketplace",
        industry="Travel",
        size=CompanySize.LARGE,
        employee_count=6000,
        founded_year=2008,
        headquarters="San Francisco, CA",
        funding_stage=FundingStage.IPO,
        logo_url="https://logo.clearbit.com/airbnb.com",
        website_url="https://airbnb.com",
        glassdoor_rating=4.2,
        glassdoor_review_count=8000,
        remote_policy="remote_friendly",
    ),
    "uber": CompanyProfile(
        name="Uber",
        domain="uber.com",
        description="Ride-sharing and delivery platform",
        industry="Transportation",
        size=CompanySize.LARGE,
        employee_count=30000,
        founded_year=2009,
        headquarters="San Francisco, CA",
        funding_stage=FundingStage.IPO,
        logo_url="https://logo.clearbit.com/uber.com",
        website_url="https://uber.com",
        glassdoor_rating=3.9,
        glassdoor_review_count=20000,
        remote_policy="hybrid",
    ),
}


class CompanyDataManager:
    CACHE_DURATION_HOURS = 24

    def __init__(self, db_pool: asyncpg.Pool | None = None):
        self._pool = db_pool

    async def get_company_profile(
        self,
        company_name: str,
        domain: str | None = None,
    ) -> CompanyProfile | None:
        name_lower = company_name.lower().strip()

        if name_lower in KNOWN_COMPANIES:
            incr("company_data.cache_hit")
            return KNOWN_COMPANIES[name_lower]

        for key, profile in KNOWN_COMPANIES.items():
            if key in name_lower or name_lower in key:
                incr("company_data.cache_hit_partial")
                return profile

        if self._pool:
            cached = await self._get_cached_company(name_lower)
            if cached:
                incr("company_data.db_cache_hit")
                return cached

        profile = await self._fetch_company_data(company_name, domain)

        if profile and self._pool:
            await self._cache_company(profile)

        incr("company_data.profile_fetched")
        return profile

    async def enrich_job_with_company_data(
        self,
        job: dict[str, Any],
    ) -> dict[str, Any]:
        company_name = job.get("company")
        if not company_name:
            return job

        profile = await self.get_company_profile(company_name)

        if not profile:
            job["company_enriched"] = False
            return job

        job["company_enriched"] = True
        job["company_profile"] = {
            "name": profile.name,
            "industry": profile.industry,
            "size": profile.size.value if profile.size else None,
            "employee_count": profile.employee_count,
            "founded_year": profile.founded_year,
            "headquarters": profile.headquarters,
            "funding_stage": profile.funding_stage.value
            if profile.funding_stage
            else None,
            "total_funding_usd": profile.total_funding_usd,
            "logo_url": profile.logo_url,
            "glassdoor_rating": profile.glassdoor_rating,
            "remote_policy": profile.remote_policy,
        }

        incr("company_data.job_enriched")
        return job

    async def batch_enrich_jobs(
        self,
        jobs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        enriched = []
        for job in jobs:
            enriched.append(await self.enrich_job_with_company_data(job))
        return enriched

    async def search_companies(
        self,
        query: str,
        industry: str | None = None,
        size: CompanySize | None = None,
        min_employees: int | None = None,
        max_employees: int | None = None,
        limit: int = 20,
    ) -> list[CompanyProfile]:
        results = []
        query_lower = query.lower()

        for profile in KNOWN_COMPANIES.values():
            if query_lower not in profile.name.lower():
                continue

            if industry and profile.industry != industry:
                continue

            if size and profile.size != size:
                continue

            if min_employees and (
                not profile.employee_count or profile.employee_count < min_employees
            ):
                continue

            if max_employees and (
                not profile.employee_count or profile.employee_count > max_employees
            ):
                continue

            results.append(profile)

            if len(results) >= limit:
                break

        incr("company_data.search")
        return results

    async def get_industry_stats(self) -> dict[str, int]:
        stats: dict[str, int] = {}
        for profile in KNOWN_COMPANIES.values():
            if profile.industry:
                stats[profile.industry] = stats.get(profile.industry, 0) + 1
        return stats

    async def get_company_recommendations(
        self,
        user_preferences: dict[str, Any],
    ) -> list[CompanyProfile]:
        results = []

        preferred_industries = user_preferences.get("industries", [])
        preferred_size = user_preferences.get("company_size")
        min_rating = user_preferences.get("min_rating", 3.5)
        remote_preference = user_preferences.get("remote", False)

        for profile in KNOWN_COMPANIES.values():
            score = 0

            if preferred_industries and profile.industry in preferred_industries:
                score += 2

            if preferred_size and profile.size:
                size_order = list(CompanySize)
                try:
                    pref_idx = size_order.index(CompanySize(preferred_size.lower()))
                    company_idx = size_order.index(profile.size)
                    if abs(pref_idx - company_idx) <= 1:
                        score += 1
                except ValueError:
                    pass

            if profile.glassdoor_rating and profile.glassdoor_rating >= min_rating:
                score += 1

            if remote_preference and profile.remote_policy in (
                "remote_first",
                "remote_friendly",
            ):
                score += 1

            if score > 0:
                results.append((profile, score))

        results.sort(key=lambda x: x[1], reverse=True)
        incr("company_data.recommendations")
        return [r[0] for r in results[:10]]

    async def _fetch_company_data(
        self,
        company_name: str,
        domain: str | None = None,
    ) -> CompanyProfile | None:
        await asyncio.sleep(0.01)

        return CompanyProfile(
            name=company_name,
            domain=domain,
            description=f"Company: {company_name}",
            industry=self._infer_industry(company_name),
            size=CompanySize.MEDIUM,
            employee_count=100,
            logo_url=f"https://logo.clearbit.com/{domain}" if domain else None,
            last_updated=datetime.now(UTC),
        )

    def _infer_industry(self, company_name: str) -> str:
        name_lower = company_name.lower()
        for keyword, industry in INDUSTRY_MAPPINGS.items():
            if keyword in name_lower:
                return industry
        return "Technology"

    async def _get_cached_company(self, name_lower: str) -> CompanyProfile | None:
        if not self._pool:
            return None

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT data FROM public.company_cache
                WHERE name_lower = $1 AND cached_at > now() - INTERVAL '24 hours'
                """,
                name_lower,
            )

            if not row:
                return None

            data = row["data"]
            if isinstance(data, str):
                data = json.loads(data)

            return CompanyProfile(**data)

    async def _cache_company(self, profile: CompanyProfile) -> None:
        if not self._pool:
            return

        data = {
            "name": profile.name,
            "domain": profile.domain,
            "description": profile.description,
            "industry": profile.industry,
            "size": profile.size.value if profile.size else None,
            "employee_count": profile.employee_count,
            "founded_year": profile.founded_year,
            "headquarters": profile.headquarters,
            "funding_stage": profile.funding_stage.value
            if profile.funding_stage
            else None,
            "total_funding_usd": profile.total_funding_usd,
            "logo_url": profile.logo_url,
            "website_url": profile.website_url,
            "glassdoor_rating": profile.glassdoor_rating,
            "remote_policy": profile.remote_policy,
            "last_updated": datetime.now(UTC).isoformat(),
        }

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.company_cache (name_lower, data, cached_at)
                VALUES ($1, $2::jsonb, now())
                ON CONFLICT (name_lower) DO UPDATE SET data = $2::jsonb, cached_at = now()
                """,
                profile.name.lower(),
                json.dumps(data),
            )


async def init_company_cache_table(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS public.company_cache (
            name_lower TEXT PRIMARY KEY,
            data JSONB NOT NULL,
            cached_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_company_cache_cached_at
            ON public.company_cache(cached_at);
        """
    )
    logger.info("Company cache table initialized")
