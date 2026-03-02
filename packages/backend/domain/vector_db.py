"""Vector Database Service for semantic job matching.

Implements external vector database integration (Pinecone/Weaviate) as recommended
in competitive analysis - enabling fast similarity search for job matching.

Supports:
- Pinecone (recommended for production)
- Weaviate (open-source alternative)
- In-memory fallback for development
"""

from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from typing import Any

import httpx
from shared.logging_config import get_logger

from shared.metrics import incr, observe

logger = get_logger("sorce.vector_db")

VECTOR_DIMENSION = 1536
DEFAULT_NAMESPACE = "default"
JOBS_NAMESPACE = "jobs"
PROFILES_NAMESPACE = "profiles"


def _track_metric(name: str, tags: dict[str, str], value: int = 1) -> None:
    """Helper to track metrics with proper signature."""
    incr(name, tags=tags, value=value)


class VectorDBError(Exception):
    """Raised when vector database operations fail."""

    pass


class VectorDBClient(ABC):
    """Abstract base class for vector database clients."""

    @abstractmethod
    async def upsert(
        self,
        id: str,
        vector: list[float],
        metadata: dict[str, Any],
        namespace: str = DEFAULT_NAMESPACE,
    ) -> bool:
        """Insert or update a vector."""
        pass

    @abstractmethod
    async def upsert_batch(
        self,
        items: list[dict[str, Any]],
        namespace: str = DEFAULT_NAMESPACE,
    ) -> int:
        """Insert or update multiple vectors. Returns count of successful upserts."""
        pass

    @abstractmethod
    async def query(
        self,
        vector: list[float],
        top_k: int = 10,
        namespace: str = DEFAULT_NAMESPACE,
        filter: dict[str, Any] | None = None,
        include_metadata: bool = True,
    ) -> list[dict[str, Any]]:
        """Query for similar vectors.

        Returns list of dicts with:
        - id: vector id
        - score: similarity score (0-1)
        - metadata: associated metadata
        """
        pass

    @abstractmethod
    async def delete(
        self,
        id: str,
        namespace: str = DEFAULT_NAMESPACE,
    ) -> bool:
        """Delete a vector by id."""
        pass

    @abstractmethod
    async def delete_batch(
        self,
        ids: list[str],
        namespace: str = DEFAULT_NAMESPACE,
    ) -> int:
        """Delete multiple vectors. Returns count deleted."""
        pass

    @abstractmethod
    async def fetch(
        self,
        id: str,
        namespace: str = DEFAULT_NAMESPACE,
    ) -> dict[str, Any] | None:
        """Fetch a single vector by id."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the database is healthy and accessible."""
        pass


class PineconeClient(VectorDBClient):
    """Pinecone vector database client.

    Pinecone is a managed vector database optimized for production use.
    Provides fast similarity search with metadata filtering.
    """

    def __init__(
        self,
        api_key: str,
        environment: str,
        index_name: str,
    ) -> None:
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self.base_url = f"https://{index_name}-{environment}.svc.pinecone.io"
        self.timeout = 30

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to Pinecone API."""
        url = f"{self.base_url}{path}"
        headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if method == "GET":
                resp = await client.get(url, headers=headers)
            elif method == "POST":
                resp = await client.post(url, json=payload, headers=headers)
            elif method == "DELETE":
                resp = await client.request(
                    "DELETE", url, json=payload, headers=headers
                )
            else:
                raise ValueError(f"Unsupported method: {method}")

            resp.raise_for_status()
            return resp.json()

    async def upsert(
        self,
        id: str,
        vector: list[float],
        metadata: dict[str, Any],
        namespace: str = DEFAULT_NAMESPACE,
    ) -> bool:
        """Upsert a single vector to Pinecone."""
        t0 = time.monotonic()
        try:
            payload = {
                "vectors": [
                    {
                        "id": id,
                        "values": vector,
                        "metadata": metadata,
                    }
                ],
                "namespace": namespace,
            }
            await self._request("POST", "/vectors/upsert", payload)
            duration = time.monotonic() - t0
            observe(
                "vector_db.upsert_latency_seconds", duration, {"provider": "pinecone"}
            )
            _track_metric("vector_db.upserts", {"provider": "pinecone"})
            return True
        except Exception as e:
            _track_metric(
                "vector_db.errors", {"provider": "pinecone", "operation": "upsert"}
            )
            logger.error("Pinecone upsert failed: %s", e)
            raise VectorDBError(f"Pinecone upsert failed: {e}") from e

    async def upsert_batch(
        self,
        items: list[dict[str, Any]],
        namespace: str = DEFAULT_NAMESPACE,
    ) -> int:
        """Upsert multiple vectors to Pinecone (max 100 per batch)."""
        if not items:
            return 0

        batch_size = 100
        total_upserted = 0

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            t0 = time.monotonic()
            try:
                vectors = []
                for item in batch:
                    vectors.append(
                        {
                            "id": item["id"],
                            "values": item["vector"],
                            "metadata": item.get("metadata", {}),
                        }
                    )

                payload = {
                    "vectors": vectors,
                    "namespace": namespace,
                }
                await self._request("POST", "/vectors/upsert", payload)
                total_upserted += len(vectors)
                duration = time.monotonic() - t0
                observe(
                    "vector_db.batch_upsert_latency_seconds",
                    duration,
                    {"provider": "pinecone"},
                )
            except Exception as e:
                _track_metric(
                    "vector_db.errors",
                    {"provider": "pinecone", "operation": "batch_upsert"},
                )
                logger.error("Pinecone batch upsert failed: %s", e)

        _track_metric(
            "vector_db.batch_upserts",
            {"provider": "pinecone"},
            total_upserted,
        )
        return total_upserted

    async def query(
        self,
        vector: list[float],
        top_k: int = 10,
        namespace: str = DEFAULT_NAMESPACE,
        filter: dict[str, Any] | None = None,
        include_metadata: bool = True,
    ) -> list[dict[str, Any]]:
        """Query Pinecone for similar vectors."""
        t0 = time.monotonic()
        try:
            payload = {
                "vector": vector,
                "top_k": top_k,
                "namespace": namespace,
                "include_metadata": include_metadata,
            }
            if filter:
                payload["filter"] = filter

            result = await self._request("POST", "/query", payload)
            duration = time.monotonic() - t0
            observe(
                "vector_db.query_latency_seconds", duration, {"provider": "pinecone"}
            )
            _track_metric("vector_db.queries", {"provider": "pinecone"})

            matches = []
            for match in result.get("matches", []):
                matches.append(
                    {
                        "id": match["id"],
                        "score": match["score"],
                        "metadata": match.get("metadata", {}),
                    }
                )
            return matches
        except Exception as e:
            _track_metric(
                "vector_db.errors", {"provider": "pinecone", "operation": "query"}
            )
            logger.error("Pinecone query failed: %s", e)
            raise VectorDBError(f"Pinecone query failed: {e}") from e

    async def delete(
        self,
        id: str,
        namespace: str = DEFAULT_NAMESPACE,
    ) -> bool:
        """Delete a vector from Pinecone."""
        t0 = time.monotonic()
        try:
            payload = {
                "ids": [id],
                "namespace": namespace,
            }
            await self._request("DELETE", "/vectors/delete", payload)
            duration = time.monotonic() - t0
            observe(
                "vector_db.delete_latency_seconds", duration, {"provider": "pinecone"}
            )
            _track_metric("vector_db.deletes", {"provider": "pinecone"})
            return True
        except Exception as e:
            _track_metric(
                "vector_db.errors", {"provider": "pinecone", "operation": "delete"}
            )
            logger.error("Pinecone delete failed: %s", e)
            return False

    async def delete_batch(
        self,
        ids: list[str],
        namespace: str = DEFAULT_NAMESPACE,
    ) -> int:
        """Delete multiple vectors from Pinecone."""
        if not ids:
            return 0

        t0 = time.monotonic()
        try:
            payload = {
                "ids": ids,
                "namespace": namespace,
            }
            await self._request("DELETE", "/vectors/delete", payload)
            duration = time.monotonic() - t0
            observe(
                "vector_db.batch_delete_latency_seconds",
                duration,
                {"provider": "pinecone"},
            )
            _track_metric("vector_db.batch_deletes", {"provider": "pinecone"}, len(ids))
            return len(ids)
        except Exception as e:
            _track_metric(
                "vector_db.errors",
                {"provider": "pinecone", "operation": "batch_delete"},
            )
            logger.error("Pinecone batch delete failed: %s", e)
            return 0

    async def fetch(
        self,
        id: str,
        namespace: str = DEFAULT_NAMESPACE,
    ) -> dict[str, Any] | None:
        """Fetch a vector from Pinecone."""
        try:
            result = await self._request(
                "GET", f"/vectors/fetch?ids={id}&namespace={namespace}"
            )
            vectors = result.get("vectors", {})
            if id in vectors:
                v = vectors[id]
                return {
                    "id": id,
                    "vector": v.get("values", []),
                    "metadata": v.get("metadata", {}),
                }
            return None
        except Exception as e:
            logger.error("Pinecone fetch failed: %s", e)
            return None

    async def health_check(self) -> bool:
        """Check Pinecone health."""
        try:
            result = await self._request("GET", "/describe-index-stats")
            return "dimension" in result
        except Exception as e:
            logger.warning("Pinecone health check failed: %s", e)
            return False


class WeaviateClient(VectorDBClient):
    """Weaviate vector database client.

    Weaviate is an open-source vector database with semantic search capabilities.
    Can be self-hosted or used via Weaviate Cloud.
    """

    def __init__(
        self,
        url: str,
        api_key: str | None = None,
    ) -> None:
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.timeout = 30

    def _get_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to Weaviate API."""
        url = f"{self.url}{path}"
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if method == "GET":
                resp = await client.get(url, headers=headers)
            elif method == "POST":
                resp = await client.post(url, json=payload, headers=headers)
            elif method == "DELETE":
                resp = await client.request(
                    "DELETE", url, json=payload, headers=headers
                )
            elif method == "PUT":
                resp = await client.put(url, json=payload, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            resp.raise_for_status()
            if resp.content:
                return resp.json()
            return {}

    async def upsert(
        self,
        id: str,
        vector: list[float],
        metadata: dict[str, Any],
        namespace: str = DEFAULT_NAMESPACE,
    ) -> bool:
        """Upsert a single vector to Weaviate."""
        t0 = time.monotonic()
        try:
            payload = {
                "class": namespace,
                "id": id,
                "vector": vector,
                "properties": metadata,
            }
            await self._request("POST", "/v1/objects", payload)
            duration = time.monotonic() - t0
            observe(
                "vector_db.upsert_latency_seconds", duration, {"provider": "weaviate"}
            )
            _track_metric("vector_db.upserts", {"provider": "weaviate"})
            return True
        except Exception as e:
            _track_metric(
                "vector_db.errors", {"provider": "weaviate", "operation": "upsert"}
            )
            logger.error("Weaviate upsert failed: %s", e)
            raise VectorDBError(f"Weaviate upsert failed: {e}") from e

    async def upsert_batch(
        self,
        items: list[dict[str, Any]],
        namespace: str = DEFAULT_NAMESPACE,
    ) -> int:
        """Upsert multiple vectors to Weaviate."""
        if not items:
            return 0

        total_upserted = 0
        for item in items:
            try:
                await self.upsert(
                    id=item["id"],
                    vector=item["vector"],
                    metadata=item.get("metadata", {}),
                    namespace=namespace,
                )
                total_upserted += 1
            except Exception as e:
                logger.warning("Batch upsert item failed: %s", e)

        _track_metric(
            "vector_db.batch_upserts", {"provider": "weaviate"}, total_upserted
        )
        return total_upserted

    async def query(
        self,
        vector: list[float],
        top_k: int = 10,
        namespace: str = DEFAULT_NAMESPACE,
        filter: dict[str, Any] | None = None,
        include_metadata: bool = True,
    ) -> list[dict[str, Any]]:
        """Query Weaviate for similar vectors."""
        import json as json_module

        t0 = time.monotonic()
        try:
            near_vector = {
                "vector": vector,
                "certainty": 0.7,
            }

            gql_query = {
                "query": f"""{{
                    Get {{
                        {namespace}(
                            nearVector: {json_module.dumps(near_vector)}
                            limit: {top_k}
                        ) {{
                            _additional {{
                                id
                                certainty
                            }}
                        }}
                    }}
                }}"""
            }

            result = await self._request("POST", "/v1/graphql", gql_query)
            duration = time.monotonic() - t0
            observe(
                "vector_db.query_latency_seconds", duration, {"provider": "weaviate"}
            )
            _track_metric("vector_db.queries", {"provider": "weaviate"})

            matches = []
            data = result.get("data", {}).get("Get", {}).get(namespace, [])
            for item in data:
                additional = item.get("_additional", {})
                matches.append(
                    {
                        "id": additional.get("id"),
                        "score": additional.get("certainty", 0),
                        "metadata": {
                            k: v for k, v in item.items() if k != "_additional"
                        },
                    }
                )
            return matches
        except Exception as e:
            _track_metric(
                "vector_db.errors", {"provider": "weaviate", "operation": "query"}
            )
            logger.error("Weaviate query failed: %s", e)
            raise VectorDBError(f"Weaviate query failed: {e}") from e

    async def delete(
        self,
        id: str,
        namespace: str = DEFAULT_NAMESPACE,
    ) -> bool:
        """Delete a vector from Weaviate."""
        t0 = time.monotonic()
        try:
            await self._request("DELETE", f"/v1/objects/{namespace}/{id}")
            duration = time.monotonic() - t0
            observe(
                "vector_db.delete_latency_seconds", duration, {"provider": "weaviate"}
            )
            _track_metric("vector_db.deletes", {"provider": "weaviate"})
            return True
        except Exception as e:
            _track_metric(
                "vector_db.errors", {"provider": "weaviate", "operation": "delete"}
            )
            logger.error("Weaviate delete failed: %s", e)
            return False

    async def delete_batch(
        self,
        ids: list[str],
        namespace: str = DEFAULT_NAMESPACE,
    ) -> int:
        """Delete multiple vectors from Weaviate."""
        total_deleted = 0
        for id in ids:
            if await self.delete(id, namespace):
                total_deleted += 1
        _track_metric(
            "vector_db.batch_deletes", {"provider": "weaviate"}, total_deleted
        )
        return total_deleted

    async def fetch(
        self,
        id: str,
        namespace: str = DEFAULT_NAMESPACE,
    ) -> dict[str, Any] | None:
        """Fetch a vector from Weaviate."""
        try:
            result = await self._request("GET", f"/v1/objects/{namespace}/{id}")
            return {
                "id": result.get("id"),
                "vector": result.get("vector", []),
                "metadata": result.get("properties", {}),
            }
        except Exception as e:
            logger.error("Weaviate fetch failed: %s", e)
            return None

    async def health_check(self) -> bool:
        """Check Weaviate health."""
        try:
            await self._request("GET", "/v1/.well-known/ready")
            return True
        except Exception as e:
            logger.warning("Weaviate health check failed: %s", e)
            return False


class InMemoryVectorDB(VectorDBClient):
    """In-memory vector database for development and testing.

    Not suitable for production - vectors are lost on restart.
    Uses in-memory dictionary with brute-force similarity search.
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, dict[str, Any]]] = {}

    def _get_namespace(self, namespace: str) -> dict[str, dict[str, Any]]:
        if namespace not in self._store:
            self._store[namespace] = {}
        return self._store[namespace]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot_product = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    async def upsert(
        self,
        id: str,
        vector: list[float],
        metadata: dict[str, Any],
        namespace: str = DEFAULT_NAMESPACE,
    ) -> bool:
        ns = self._get_namespace(namespace)
        ns[id] = {
            "id": id,
            "vector": vector,
            "metadata": metadata,
        }
        _track_metric("vector_db.upserts", {"provider": "memory"})
        return True

    async def upsert_batch(
        self,
        items: list[dict[str, Any]],
        namespace: str = DEFAULT_NAMESPACE,
    ) -> int:
        ns = self._get_namespace(namespace)
        count = 0
        for item in items:
            ns[item["id"]] = {
                "id": item["id"],
                "vector": item["vector"],
                "metadata": item.get("metadata", {}),
            }
            count += 1
        _track_metric("vector_db.batch_upserts", {"provider": "memory"}, count)
        return count

    async def query(
        self,
        vector: list[float],
        top_k: int = 10,
        namespace: str = DEFAULT_NAMESPACE,
        filter: dict[str, Any] | None = None,
        include_metadata: bool = True,
    ) -> list[dict[str, Any]]:
        ns = self._get_namespace(namespace)
        _track_metric("vector_db.queries", {"provider": "memory"})

        results = []
        for id, item in ns.items():
            score = self._cosine_similarity(vector, item["vector"])
            results.append(
                {
                    "id": id,
                    "score": score,
                    "metadata": item["metadata"] if include_metadata else {},
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    async def delete(
        self,
        id: str,
        namespace: str = DEFAULT_NAMESPACE,
    ) -> bool:
        ns = self._get_namespace(namespace)
        if id in ns:
            del ns[id]
            _track_metric("vector_db.deletes", {"provider": "memory"})
            return True
        return False

    async def delete_batch(
        self,
        ids: list[str],
        namespace: str = DEFAULT_NAMESPACE,
    ) -> int:
        ns = self._get_namespace(namespace)
        count = 0
        for id in ids:
            if id in ns:
                del ns[id]
                count += 1
        _track_metric("vector_db.batch_deletes", {"provider": "memory"}, count)
        return count

    async def fetch(
        self,
        id: str,
        namespace: str = DEFAULT_NAMESPACE,
    ) -> dict[str, Any] | None:
        ns = self._get_namespace(namespace)
        return ns.get(id)

    async def health_check(self) -> bool:
        return True


_vector_db_client: VectorDBClient | None = None


def get_vector_db_client() -> VectorDBClient:
    """Get or create the singleton vector database client."""
    global _vector_db_client

    if _vector_db_client is not None:
        return _vector_db_client

    provider = os.environ.get("VECTOR_DB_PROVIDER", "memory").lower()

    if provider == "pinecone":
        api_key = os.environ.get("PINECONE_API_KEY", "")
        environment = os.environ.get("PINECONE_ENVIRONMENT", "us-east-1-aws")
        index_name = os.environ.get("PINECONE_INDEX_NAME", "jobhuntin")

        if not api_key:
            logger.warning(
                "PINECONE_API_KEY not set, falling back to in-memory vector DB"
            )
            _vector_db_client = InMemoryVectorDB()
        else:
            logger.info("Initializing Pinecone vector DB client")
            _vector_db_client = PineconeClient(
                api_key=api_key,
                environment=environment,
                index_name=index_name,
            )

    elif provider == "weaviate":
        url = os.environ.get("WEAVIATE_URL", "")
        api_key = os.environ.get("WEAVIATE_API_KEY")

        if not url:
            logger.warning("WEAVIATE_URL not set, falling back to in-memory vector DB")
            _vector_db_client = InMemoryVectorDB()
        else:
            logger.info("Initializing Weaviate vector DB client")
            _vector_db_client = WeaviateClient(url=url, api_key=api_key)

    else:
        logger.info("Using in-memory vector DB (not suitable for production)")
        _vector_db_client = InMemoryVectorDB()

    return _vector_db_client


def reset_vector_db_client() -> None:
    """Reset the singleton vector DB client (for testing)."""
    global _vector_db_client
    _vector_db_client = None
