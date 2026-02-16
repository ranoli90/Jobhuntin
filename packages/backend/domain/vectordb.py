"""
Vector database abstraction layer for semantic search.

Supports multiple backends:
1. pgvector - PostgreSQL extension for vector similarity search
2. Pinecone - Managed vector database
3. Weaviate - Open-source vector database
4. In-memory fallback for development

This addresses recommendation #15: Use external vector DB for embeddings
instead of storing as JSON for slow similarity search.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any

import asyncpg
from shared.config import Settings
from shared.logging_config import get_logger

from shared.metrics import incr

logger = get_logger("sorce.vectordb")

# Default embedding dimension (OpenAI text-embedding-3-small)
DEFAULT_DIMENSION = 1536


class VectorDBError(Exception):
    """Raised when vector database operations fail."""
    pass


class VectorDBBackend(ABC):
    """Abstract base class for vector database backends."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the backend (create tables, indexes, etc.)."""
        pass

    @abstractmethod
    async def upsert(
        self,
        id: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
        namespace: str = "default",
    ) -> None:
        """Insert or update a vector."""
        pass

    @abstractmethod
    async def upsert_batch(
        self,
        items: list[dict[str, Any]],
        namespace: str = "default",
    ) -> None:
        """Insert or update multiple vectors."""
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
        namespace: str = "default",
    ) -> list[dict[str, Any]]:
        """
        Search for similar vectors.
        
        Returns list of dicts with:
        - id: str
        - score: float (similarity score)
        - metadata: dict
        """
        pass

    @abstractmethod
    async def delete(
        self,
        id: str,
        namespace: str = "default",
    ) -> None:
        """Delete a vector by ID."""
        pass

    @abstractmethod
    async def delete_by_filter(
        self,
        filters: dict[str, Any],
        namespace: str = "default",
    ) -> int:
        """Delete vectors matching filters. Returns count deleted."""
        pass

    @abstractmethod
    async def get(
        self,
        id: str,
        namespace: str = "default",
    ) -> dict[str, Any] | None:
        """Get a vector by ID."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the backend is healthy."""
        pass


class PgVectorBackend(VectorDBBackend):
    """
    PostgreSQL pgvector backend.
    
    Uses the pgvector extension for efficient vector similarity search.
    Falls back to JSON storage with Python similarity if pgvector not available.
    """

    def __init__(
        self,
        conn: asyncpg.Connection,
        dimension: int = DEFAULT_DIMENSION,
        table_prefix: str = "vec",
    ) -> None:
        self._conn = conn
        self._dimension = dimension
        self._table_prefix = table_prefix
        self._pgvector_available = False

    async def initialize(self) -> None:
        """Create tables and indexes."""
        # Check if pgvector extension is available
        try:
            result = await self._conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            )
            self._pgvector_available = result
        except Exception:
            self._pgvector_available = False
            logger.warning(
                "pgvector extension not available, falling back to JSON storage"
            )

        # Create main vectors table
        table_name = f"{self._table_prefix}_embeddings"

        if self._pgvector_available:
            # Use native vector column
            await self._conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id TEXT PRIMARY KEY,
                    namespace TEXT NOT NULL DEFAULT 'default',
                    embedding vector({self._dimension}),
                    metadata JSONB DEFAULT '{{}}',
                    created_at TIMESTAMPTZ DEFAULT now(),
                    updated_at TIMESTAMPTZ DEFAULT now()
                )
            """)
            # Create vector index for similarity search
            await self._conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {table_name}_embedding_idx
                ON {table_name}
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
            # Create namespace index
            await self._conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {table_name}_namespace_idx
                ON {table_name} (namespace)
            """)
        else:
            # Fallback to JSON storage
            await self._conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id TEXT PRIMARY KEY,
                    namespace TEXT NOT NULL DEFAULT 'default',
                    embedding JSONB NOT NULL,
                    metadata JSONB DEFAULT '{{}}',
                    created_at TIMESTAMPTZ DEFAULT now(),
                    updated_at TIMESTAMPTZ DEFAULT now()
                )
            """)
            await self._conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {table_name}_namespace_idx
                ON {table_name} (namespace)
            """)

        logger.info(
            f"Initialized pgvector backend (pgvector={self._pgvector_available})"
        )

    async def upsert(
        self,
        id: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
        namespace: str = "default",
    ) -> None:
        """Insert or update a vector."""
        table_name = f"{self._table_prefix}_embeddings"
        metadata = metadata or {}

        if self._pgvector_available:
            # Format embedding as pgvector string
            vec_str = "[" + ",".join(str(x) for x in embedding) + "]"
            await self._conn.execute(
                f"""
                INSERT INTO {table_name} (id, namespace, embedding, metadata, updated_at)
                VALUES ($1, $2, $3::vector, $4, now())
                ON CONFLICT (id) DO UPDATE SET
                    embedding = $3::vector,
                    metadata = $4,
                    updated_at = now()
                """,
                id,
                namespace,
                vec_str,
                json.dumps(metadata),
            )
        else:
            await self._conn.execute(
                f"""
                INSERT INTO {table_name} (id, namespace, embedding, metadata, updated_at)
                VALUES ($1, $2, $3::jsonb, $4, now())
                ON CONFLICT (id) DO UPDATE SET
                    embedding = $3::jsonb,
                    metadata = $4,
                    updated_at = now()
                """,
                id,
                namespace,
                json.dumps(embedding),
                json.dumps(metadata),
            )

    async def upsert_batch(
        self,
        items: list[dict[str, Any]],
        namespace: str = "default",
    ) -> None:
        """Insert or update multiple vectors."""
        for item in items:
            await self.upsert(
                id=item["id"],
                embedding=item["embedding"],
                metadata=item.get("metadata"),
                namespace=namespace,
            )

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
        namespace: str = "default",
    ) -> list[dict[str, Any]]:
        """Search for similar vectors."""
        table_name = f"{self._table_prefix}_embeddings"

        if self._pgvector_available:
            # Use native pgvector cosine similarity search
            vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

            # Build filter conditions
            where_clauses = ["namespace = $1"]
            params: list[Any] = [namespace]
            param_idx = 2

            if filters:
                for key, value in filters.items():
                    where_clauses.append(f"metadata->>${key} = ${param_idx}")
                    params.append(str(value))
                    param_idx += 1

            query = f"""
                SELECT
                    id,
                    1 - (embedding <=> $1::vector) as score,
                    metadata
                FROM {table_name}
                WHERE {' AND '.join(where_clauses)}
                ORDER BY embedding <=> $1::vector
                LIMIT ${param_idx}
            """
            params.insert(0, vec_str)
            params.append(top_k)

            rows = await self._conn.fetch(query, *params)
            return [
                {
                    "id": row["id"],
                    "score": float(row["score"]),
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                }
                for row in rows
            ]
        else:
            # Fallback: fetch all and compute similarity in Python
            where_clauses = ["namespace = $1"]
            params: list[Any] = [namespace]

            if filters:
                for key, value in filters.items():
                    where_clauses.append(f"metadata->>${key} = ${len(params) + 1}")
                    params.append(str(value))

            query = f"""
                SELECT id, embedding, metadata
                FROM {table_name}
                WHERE {' AND '.join(where_clauses)}
            """

            rows = await self._conn.fetch(query, *params)

            # Compute cosine similarity for each
            results: list[dict[str, Any]] = []
            for row in rows:
                stored_embedding = json.loads(row["embedding"])
                score = self._cosine_similarity(query_embedding, stored_embedding)
                results.append({
                    "id": row["id"],
                    "score": score,
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                })

            # Sort by score descending and return top_k
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]

    async def delete(
        self,
        id: str,
        namespace: str = "default",
    ) -> None:
        """Delete a vector by ID."""
        table_name = f"{self._table_prefix}_embeddings"
        await self._conn.execute(
            f"DELETE FROM {table_name} WHERE id = $1 AND namespace = $2",
            id,
            namespace,
        )

    async def delete_by_filter(
        self,
        filters: dict[str, Any],
        namespace: str = "default",
    ) -> int:
        """Delete vectors matching filters."""
        table_name = f"{self._table_prefix}_embeddings"

        where_clauses = ["namespace = $1"]
        params: list[Any] = [namespace]

        for key, value in filters.items():
            where_clauses.append(f"metadata->>${key} = ${len(params) + 1}")
            params.append(str(value))

        result = await self._conn.execute(
            f"DELETE FROM {table_name} WHERE {' AND '.join(where_clauses)}",
            *params
        )
        # Parse "DELETE N" result
        return int(result.split()[-1]) if result else 0

    async def get(
        self,
        id: str,
        namespace: str = "default",
    ) -> dict[str, Any] | None:
        """Get a vector by ID."""
        table_name = f"{self._table_prefix}_embeddings"
        row = await self._conn.fetchrow(
            f"SELECT id, embedding, metadata FROM {table_name} WHERE id = $1 AND namespace = $2",
            id,
            namespace,
        )
        if not row:
            return None
        return {
            "id": row["id"],
            "embedding": json.loads(row["embedding"]) if isinstance(row["embedding"], str) else row["embedding"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
        }

    async def health_check(self) -> bool:
        """Check if the backend is healthy."""
        try:
            await self._conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not a or not b or len(a) != len(b):
            return 0.0
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)


class PineconeBackend(VectorDBBackend):
    """
    Pinecone vector database backend.
    
    Requires pinecone-client package and PINECONE_API_KEY env var.
    """

    def __init__(
        self,
        api_key: str,
        environment: str,
        index_name: str,
        dimension: int = DEFAULT_DIMENSION,
    ) -> None:
        self._api_key = api_key
        self._environment = environment
        self._index_name = index_name
        self._dimension = dimension
        self._index = None

    async def initialize(self) -> None:
        """Initialize Pinecone connection."""
        try:
            import pinecone

            pinecone.init(
                api_key=self._api_key,
                environment=self._environment,
            )

            # Create index if it doesn't exist
            if self._index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=self._index_name,
                    dimension=self._dimension,
                    metric="cosine",
                )

            self._index = pinecone.Index(self._index_name)
            logger.info(f"Initialized Pinecone backend (index={self._index_name})")
        except ImportError:
            raise VectorDBError("pinecone-client not installed. Run: pip install pinecone-client")

    async def upsert(
        self,
        id: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
        namespace: str = "default",
    ) -> None:
        """Insert or update a vector."""
        self._index.upsert(
            vectors=[(id, embedding, metadata or {})],
            namespace=namespace,
        )

    async def upsert_batch(
        self,
        items: list[dict[str, Any]],
        namespace: str = "default",
    ) -> None:
        """Insert or update multiple vectors."""
        vectors = [
            (item["id"], item["embedding"], item.get("metadata", {}))
            for item in items
        ]
        # Pinecone recommends batches of 100
        for i in range(0, len(vectors), 100):
            batch = vectors[i:i + 100]
            self._index.upsert(vectors=batch, namespace=namespace)

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
        namespace: str = "default",
    ) -> list[dict[str, Any]]:
        """Search for similar vectors."""
        results = self._index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            namespace=namespace,
            filter=filters,
        )
        return [
            {
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata or {},
            }
            for match in results.matches
        ]

    async def delete(
        self,
        id: str,
        namespace: str = "default",
    ) -> None:
        """Delete a vector by ID."""
        self._index.delete(ids=[id], namespace=namespace)

    async def delete_by_filter(
        self,
        filters: dict[str, Any],
        namespace: str = "default",
    ) -> int:
        """Delete vectors matching filters."""
        # Pinecone requires a metadata filter for delete
        self._index.delete(filter=filters, namespace=namespace)
        return -1  # Pinecone doesn't return count

    async def get(
        self,
        id: str,
        namespace: str = "default",
    ) -> dict[str, Any] | None:
        """Get a vector by ID."""
        results = self._index.fetch(ids=[id], namespace=namespace)
        if id in results.vectors:
            v = results.vectors[id]
            return {
                "id": id,
                "embedding": v.values,
                "metadata": v.metadata or {},
            }
        return None

    async def health_check(self) -> bool:
        """Check if the backend is healthy."""
        try:
            self._index.describe_index_stats()
            return True
        except Exception:
            return False


class InMemoryBackend(VectorDBBackend):
    """
    In-memory vector database for development/testing.
    
    NOT suitable for production - data is lost on restart.
    """

    def __init__(self, dimension: int = DEFAULT_DIMENSION) -> None:
        self._dimension = dimension
        self._data: dict[str, dict[str, dict[str, Any]]] = {}  # namespace -> id -> item

    async def initialize(self) -> None:
        """No initialization needed."""
        logger.warning("Using in-memory vector backend - NOT suitable for production")

    async def upsert(
        self,
        id: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
        namespace: str = "default",
    ) -> None:
        """Insert or update a vector."""
        if namespace not in self._data:
            self._data[namespace] = {}
        self._data[namespace][id] = {
            "id": id,
            "embedding": embedding,
            "metadata": metadata or {},
        }

    async def upsert_batch(
        self,
        items: list[dict[str, Any]],
        namespace: str = "default",
    ) -> None:
        """Insert or update multiple vectors."""
        for item in items:
            await self.upsert(
                id=item["id"],
                embedding=item["embedding"],
                metadata=item.get("metadata"),
                namespace=namespace,
            )

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
        namespace: str = "default",
    ) -> list[dict[str, Any]]:
        """Search for similar vectors."""
        if namespace not in self._data:
            return []

        results: list[dict[str, Any]] = []
        for item in self._data[namespace].values():
            # Apply filters
            if filters:
                match = all(
                    item["metadata"].get(k) == v
                    for k, v in filters.items()
                )
                if not match:
                    continue

            score = self._cosine_similarity(query_embedding, item["embedding"])
            results.append({
                "id": item["id"],
                "score": score,
                "metadata": item["metadata"],
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    async def delete(
        self,
        id: str,
        namespace: str = "default",
    ) -> None:
        """Delete a vector by ID."""
        if namespace in self._data:
            self._data[namespace].pop(id, None)

    async def delete_by_filter(
        self,
        filters: dict[str, Any],
        namespace: str = "default",
    ) -> int:
        """Delete vectors matching filters."""
        if namespace not in self._data:
            return 0

        to_delete = []
        for id, item in self._data[namespace].items():
            if all(item["metadata"].get(k) == v for k, v in filters.items()):
                to_delete.append(id)

        for id in to_delete:
            del self._data[namespace][id]

        return len(to_delete)

    async def get(
        self,
        id: str,
        namespace: str = "default",
    ) -> dict[str, Any] | None:
        """Get a vector by ID."""
        if namespace in self._data and id in self._data[namespace]:
            return self._data[namespace][id]
        return None

    async def health_check(self) -> bool:
        """Always healthy."""
        return True

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not a or not b or len(a) != len(b):
            return 0.0
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)


class VectorDB:
    """
    Main vector database interface.
    
    Provides a unified interface to different backends.
    """

    def __init__(self, backend: VectorDBBackend) -> None:
        self._backend = backend

    @classmethod
    async def create(
        cls,
        settings: Settings,
        conn: asyncpg.Connection | None = None,
    ) -> "VectorDB":
        """
        Create a VectorDB instance based on settings.
        
        Priority:
        1. Pinecone if PINECONE_API_KEY is set
        2. pgvector if connection provided
        3. In-memory fallback
        """
        backend: VectorDBBackend

        # Check for Pinecone configuration
        pinecone_key = os.environ.get("PINECONE_API_KEY")
        pinecone_env = os.environ.get("PINECONE_ENVIRONMENT", "us-west1-gcp")
        pinecone_index = os.environ.get("PINECONE_INDEX", "sorce-embeddings")

        if pinecone_key:
            backend = PineconeBackend(
                api_key=pinecone_key,
                environment=pinecone_env,
                index_name=pinecone_index,
            )
            await backend.initialize()
            return cls(backend)

        # Fall back to pgvector if connection provided
        if conn:
            backend = PgVectorBackend(conn=conn)
            await backend.initialize()
            return cls(backend)

        # In-memory fallback
        backend = InMemoryBackend()
        await backend.initialize()
        return cls(backend)

    async def upsert(
        self,
        id: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
        namespace: str = "default",
    ) -> None:
        """Insert or update a vector."""
        incr("vectordb.upsert", {"namespace": namespace})
        await self._backend.upsert(id, embedding, metadata, namespace)

    async def upsert_batch(
        self,
        items: list[dict[str, Any]],
        namespace: str = "default",
    ) -> None:
        """Insert or update multiple vectors."""
        incr("vectordb.upsert_batch", {"namespace": namespace, "count": str(len(items))})
        await self._backend.upsert_batch(items, namespace)

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
        namespace: str = "default",
    ) -> list[dict[str, Any]]:
        """Search for similar vectors."""
        incr("vectordb.search", {"namespace": namespace})
        return await self._backend.search(query_embedding, top_k, filters, namespace)

    async def delete(
        self,
        id: str,
        namespace: str = "default",
    ) -> None:
        """Delete a vector by ID."""
        incr("vectordb.delete", {"namespace": namespace})
        await self._backend.delete(id, namespace)

    async def delete_by_filter(
        self,
        filters: dict[str, Any],
        namespace: str = "default",
    ) -> int:
        """Delete vectors matching filters."""
        count = await self._backend.delete_by_filter(filters, namespace)
        incr("vectordb.delete_by_filter", {"namespace": namespace, "count": str(count)})
        return count

    async def get(
        self,
        id: str,
        namespace: str = "default",
    ) -> dict[str, Any] | None:
        """Get a vector by ID."""
        return await self._backend.get(id, namespace)

    async def health_check(self) -> bool:
        """Check if the backend is healthy."""
        return await self._backend.health_check()


# Singleton instance
_vectordb: VectorDB | None = None


async def get_vectordb(
    settings: Settings | None = None,
    conn: asyncpg.Connection | None = None,
) -> VectorDB:
    """Get or create the singleton VectorDB instance."""
    global _vectordb
    if _vectordb is None:
        from shared.config import get_settings
        settings = settings or get_settings()
        _vectordb = await VectorDB.create(settings, conn)
    return _vectordb
