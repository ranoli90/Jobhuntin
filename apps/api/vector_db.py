"""Vector Database API endpoints for semantic job matching.

Provides endpoints for:
- Upserting job/profile vectors
- Querying for similar jobs/profiles
- Health checks and stats
"""

from __future__ import annotations

from typing import Any

from backend.domain.vector_db import (
    JOBS_NAMESPACE,
    PROFILES_NAMESPACE,
    VectorDBClient,
    get_vector_db_client,
)
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from shared.logging_config import get_logger

logger = get_logger("sorce.api.vector_db")

router = APIRouter(prefix="/v1/vector", tags=["vector-db"])


class VectorUpsertRequest(BaseModel):
    id: str
    vector: list[float]
    metadata: dict[str, Any] = {}
    namespace: str = "default"


class VectorBatchUpsertRequest(BaseModel):
    items: list[dict[str, Any]]
    namespace: str = "default"


class VectorQueryRequest(BaseModel):
    vector: list[float]
    top_k: int = 10
    namespace: str = "default"
    filter: dict[str, Any] | None = None
    include_metadata: bool = True


class VectorDeleteRequest(BaseModel):
    ids: list[str]
    namespace: str = "default"


class VectorQueryResponse(BaseModel):
    matches: list[dict[str, Any]]


class VectorUpsertResponse(BaseModel):
    success: bool
    id: str


class VectorBatchUpsertResponse(BaseModel):
    upserted_count: int


class VectorDeleteResponse(BaseModel):
    deleted_count: int


def _get_vector_db() -> VectorDBClient:
    return get_vector_db_client()


@router.post("/upsert", response_model=VectorUpsertResponse)
async def upsert_vector(
    body: VectorUpsertRequest,
    client: VectorDBClient = Depends(_get_vector_db),
) -> VectorUpsertResponse:
    """Upsert a single vector to the database."""
    if len(body.vector) != 1536:
        raise HTTPException(
            status_code=400,
            detail=f"Vector dimension must be 1536, got {len(body.vector)}",
        )

    try:
        success = await client.upsert(
            id=body.id,
            vector=body.vector,
            metadata=body.metadata,
            namespace=body.namespace,
        )
        return VectorUpsertResponse(success=success, id=body.id)
    except Exception as e:
        logger.error("Vector upsert failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upsert-batch", response_model=VectorBatchUpsertResponse)
async def upsert_batch(
    body: VectorBatchUpsertRequest,
    client: VectorDBClient = Depends(_get_vector_db),
) -> VectorBatchUpsertResponse:
    """Upsert multiple vectors in batch."""
    for item in body.items:
        if "id" not in item or "vector" not in item:
            raise HTTPException(
                status_code=400, detail="Each item must have 'id' and 'vector' fields"
            )
        if len(item["vector"]) != 1536:
            raise HTTPException(
                status_code=400,
                detail=f"Vector dimension must be 1536, got {len(item['vector'])}",
            )

    try:
        count = await client.upsert_batch(items=body.items, namespace=body.namespace)
        return VectorBatchUpsertResponse(upserted_count=count)
    except Exception as e:
        logger.error("Vector batch upsert failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=VectorQueryResponse)
async def query_vectors(
    body: VectorQueryRequest,
    client: VectorDBClient = Depends(_get_vector_db),
) -> VectorQueryResponse:
    """Query for similar vectors."""
    if len(body.vector) != 1536:
        raise HTTPException(
            status_code=400,
            detail=f"Vector dimension must be 1536, got {len(body.vector)}",
        )

    try:
        matches = await client.query(
            vector=body.vector,
            top_k=body.top_k,
            namespace=body.namespace,
            filter=body.filter,
            include_metadata=body.include_metadata,
        )
        return VectorQueryResponse(matches=matches)
    except Exception as e:
        logger.error("Vector query failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete", response_model=VectorDeleteResponse)
async def delete_vectors(
    body: VectorDeleteRequest,
    client: VectorDBClient = Depends(_get_vector_db),
) -> VectorDeleteResponse:
    """Delete vectors by IDs."""
    try:
        count = await client.delete_batch(ids=body.ids, namespace=body.namespace)
        return VectorDeleteResponse(deleted_count=count)
    except Exception as e:
        logger.error("Vector delete failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fetch/{vector_id}")
async def fetch_vector(
    vector_id: str,
    namespace: str = "default",
    client: VectorDBClient = Depends(_get_vector_db),
) -> dict[str, Any]:
    """Fetch a single vector by ID."""
    result = await client.fetch(id=vector_id, namespace=namespace)
    if result is None:
        raise HTTPException(status_code=404, detail="Vector not found")
    return result


@router.get("/health")
async def vector_db_health(
    client: VectorDBClient = Depends(_get_vector_db),
) -> dict[str, Any]:
    """Check vector database health."""
    healthy = await client.health_check()
    return {
        "status": "healthy" if healthy else "unhealthy",
        "provider": type(client).__name__,
    }


@router.post("/jobs/upsert")
async def upsert_job_vector(
    job_id: str,
    vector: list[float],
    metadata: dict[str, Any] = None,
    client: VectorDBClient = Depends(_get_vector_db),
) -> dict[str, Any]:
    """Upsert a job vector (convenience endpoint)."""
    if metadata is None:
        metadata = {}
    success = await client.upsert(
        id=job_id,
        vector=vector,
        metadata=metadata,
        namespace=JOBS_NAMESPACE,
    )
    return {"success": success, "job_id": job_id}


@router.post("/jobs/query", response_model=VectorQueryResponse)
async def query_jobs(
    vector: list[float],
    top_k: int = 10,
    filter: dict[str, Any] | None = None,
    client: VectorDBClient = Depends(_get_vector_db),
) -> VectorQueryResponse:
    """Query for similar jobs (convenience endpoint)."""
    matches = await client.query(
        vector=vector,
        top_k=top_k,
        namespace=JOBS_NAMESPACE,
        filter=filter,
    )
    return VectorQueryResponse(matches=matches)


@router.post("/profiles/upsert")
async def upsert_profile_vector(
    user_id: str,
    vector: list[float],
    metadata: dict[str, Any] = None,
    client: VectorDBClient = Depends(_get_vector_db),
) -> dict[str, Any]:
    """Upsert a profile vector (convenience endpoint)."""
    if metadata is None:
        metadata = {}
    success = await client.upsert(
        id=user_id,
        vector=vector,
        metadata=metadata,
        namespace=PROFILES_NAMESPACE,
    )
    return {"success": success, "user_id": user_id}


@router.post("/profiles/query", response_model=VectorQueryResponse)
async def query_profiles(
    vector: list[float],
    top_k: int = 10,
    filter: dict[str, Any] | None = None,
    client: VectorDBClient = Depends(_get_vector_db),
) -> VectorQueryResponse:
    """Query for similar profiles (convenience endpoint)."""
    matches = await client.query(
        vector=vector,
        top_k=top_k,
        namespace=PROFILES_NAMESPACE,
        filter=filter,
    )
    return VectorQueryResponse(matches=matches)
