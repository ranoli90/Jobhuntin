"""Add available_at filter to claim_next_prioritized.

Revision ID: ef78gh90ij12
Revises: ab12cd34ef56
Create Date: 2026-03-10

Fixes retry backoff: failed applications with available_at in the future
should not be claimed until the backoff period expires.
"""

from alembic import op

revision = "ef78gh90ij12"
down_revision = "ab12cd34ef56"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.claim_next_prioritized(
            p_max_attempts int DEFAULT 3
        )
        RETURNS SETOF public.applications AS $$
        BEGIN
            RETURN QUERY
            UPDATE public.applications
            SET status = 'PROCESSING', locked_at = now(), updated_at = now()
            WHERE id = (
                SELECT id FROM public.applications
                WHERE (
                    status = 'QUEUED' OR (
                        status = 'PROCESSING' AND
                        locked_at < now() - interval '10 minutes'
                    )
                )
                  AND (snoozed_until IS NULL OR snoozed_until < now())
                  AND (available_at IS NULL OR available_at <= now())
                  AND attempt_count < p_max_attempts
                ORDER BY priority_score DESC, created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            RETURNING *;
        END;
        $$ LANGUAGE plpgsql;
    """
    )


def downgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.claim_next_prioritized(
            p_max_attempts int DEFAULT 3
        )
        RETURNS SETOF public.applications AS $$
        BEGIN
            RETURN QUERY
            UPDATE public.applications
            SET status = 'PROCESSING', locked_at = now(), updated_at = now()
            WHERE id = (
                SELECT id FROM public.applications
                WHERE (
                    status = 'QUEUED' OR (
                        status = 'PROCESSING' AND
                        locked_at < now() - interval '10 minutes'
                    )
                )
                  AND (snoozed_until IS NULL OR snoozed_until < now())
                  AND attempt_count < p_max_attempts
                ORDER BY priority_score DESC, created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            RETURNING *;
        END;
        $$ LANGUAGE plpgsql;
    """
    )
