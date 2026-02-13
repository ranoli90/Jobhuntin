"""Add pgvector support for vector similarity search

Revision ID: ab12cd34ef56
Revises: 16a542a11f84
Create Date: 2026-02-13

This addresses recommendation #15: Use pgvector for efficient
vector similarity search instead of JSON storage.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'ab12cd34ef56'
down_revision = '16a542a11f84'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add pgvector extension and vector tables."""
    # Try to create pgvector extension (may fail if not installed)
    try:
        op.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        print("✓ pgvector extension installed")
    except Exception as e:
        print(f"⚠ pgvector extension not available: {e}")
        print("  Falling back to JSON-based vector storage")
    
    # Create vector embeddings table (works with or without pgvector)
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS vec_embeddings (
            id TEXT PRIMARY KEY,
            namespace TEXT NOT NULL DEFAULT 'default',
            embedding JSONB NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """))
    print("✓ Created vec_embeddings table")
    
    # Create namespace index
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS vec_embeddings_namespace_idx 
        ON vec_embeddings (namespace)
    """))
    print("✓ Created namespace index")
    
    # Try to add vector column if pgvector is available
    try:
        op.execute(text("""
            ALTER TABLE vec_embeddings 
            ADD COLUMN IF NOT EXISTS embedding_vec vector(1536)
        """))
        print("✓ Added vector column for pgvector")
        
        # Create vector similarity index
        op.execute(text("""
            CREATE INDEX IF NOT EXISTS vec_embeddings_embedding_vec_idx 
            ON vec_embeddings 
            USING ivfflat (embedding_vec vector_cosine_ops)
            WITH (lists = 100)
        """))
        print("✓ Created vector similarity index")
    except Exception as e:
        print(f"⚠ Could not add vector column: {e}")
    
    # Create job embeddings table (migration from old JSON-based storage)
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS job_embeddings_v2 (
            job_id TEXT PRIMARY KEY,
            embedding JSONB NOT NULL,
            embedding_vec vector(1536),
            text_hash TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """))
    print("✓ Created job_embeddings_v2 table")
    
    # Create profile embeddings table
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS profile_embeddings_v2 (
            user_id TEXT PRIMARY KEY,
            embedding JSONB NOT NULL,
            embedding_vec vector(1536),
            text_hash TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """))
    print("✓ Created profile_embeddings_v2 table")
    
    # Create indexes for job/profile embeddings
    try:
        op.execute(text("""
            CREATE INDEX IF NOT EXISTS job_embeddings_v2_vec_idx 
            ON job_embeddings_v2 
            USING ivfflat (embedding_vec vector_cosine_ops)
            WITH (lists = 100)
        """))
        op.execute(text("""
            CREATE INDEX IF NOT EXISTS profile_embeddings_v2_vec_idx 
            ON profile_embeddings_v2 
            USING ivfflat (embedding_vec vector_cosine_ops)
            WITH (lists = 100)
        """))
        print("✓ Created vector indexes for job/profile embeddings")
    except Exception as e:
        print(f"⚠ Could not create vector indexes: {e}")
    
    # Add function to compute cosine similarity (fallback for non-pgvector)
    op.execute(text("""
        CREATE OR REPLACE FUNCTION cosine_similarity_json(a jsonb, b jsonb)
        RETURNS float AS $$
        DECLARE
            dot_product float := 0;
            norm_a float := 0;
            norm_b float := 0;
            val_a float;
            val_b float;
            i int;
        BEGIN
            FOR i IN 0..jsonb_array_length(a)-1 LOOP
                val_a := (a->i)::float;
                val_b := (b->i)::float;
                dot_product := dot_product + val_a * val_b;
                norm_a := norm_a + val_a * val_a;
                norm_b := norm_b + val_b * val_b;
            END LOOP;
            
            IF norm_a = 0 OR norm_b = 0 THEN
                RETURN 0;
            END IF;
            
            RETURN dot_product / (sqrt(norm_a) * sqrt(norm_b));
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
    """))
    print("✓ Created cosine_similarity_json function")


def downgrade() -> None:
    """Remove pgvector tables and extension."""
    op.execute(text("DROP TABLE IF EXISTS profile_embeddings_v2"))
    op.execute(text("DROP TABLE IF EXISTS job_embeddings_v2"))
    op.execute(text("DROP TABLE IF EXISTS vec_embeddings"))
    op.execute(text("DROP FUNCTION IF EXISTS cosine_similarity_json(jsonb, jsonb)"))
    
    # Don't drop the extension as it might be used by other applications
    # op.execute(text("DROP EXTENSION IF EXISTS vector"))
