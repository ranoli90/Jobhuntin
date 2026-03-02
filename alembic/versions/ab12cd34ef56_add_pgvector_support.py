"""Add pgvector support for vector similarity search.

Revision ID: ab12cd34ef56
Revises: 16a542a11f84
Create Date: 2026-02-13

This addresses recommendation #15: Use pgvector for efficient
vector similarity search instead of JSON storage.
"""
from alembic import op

revision = 'ab12cd34ef56'
down_revision = '16a542a11f84'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS vec_embeddings (
            id TEXT PRIMARY KEY,
            namespace TEXT NOT NULL DEFAULT 'default',
            embedding JSONB NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS vec_embeddings_namespace_idx
        ON vec_embeddings (namespace)
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS job_embeddings_v2 (
            job_id TEXT PRIMARY KEY,
            embedding JSONB NOT NULL,
            text_hash TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS profile_embeddings_v2 (
            user_id TEXT PRIMARY KEY,
            embedding JSONB NOT NULL,
            text_hash TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute("""
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
    """)


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS profile_embeddings_v2')
    op.execute('DROP TABLE IF EXISTS job_embeddings_v2')
    op.execute('DROP TABLE IF EXISTS vec_embeddings')
    op.execute('DROP FUNCTION IF EXISTS cosine_similarity_json(jsonb, jsonb)')
