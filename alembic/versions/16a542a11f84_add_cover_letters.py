"""add_cover_letters

Revision ID: 16a542a11f84
Revises: edde89a3dcba
Create Date: 2026-02-09 23:23:11.842488

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '16a542a11f84'
down_revision: Union[str, Sequence[str], None] = 'edde89a3dcba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
    CREATE TABLE IF NOT EXISTS cover_letters (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID NOT NULL REFERENCES users(id),
        job_id UUID REFERENCES jobs(id),
        content TEXT NOT NULL,
        template_id VARCHAR(100),
        tone VARCHAR(50),
        quality_score FLOAT,
        suggestions JSONB,
        is_bookmarked BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_cover_letters_user_id ON cover_letters(user_id);
    CREATE INDEX IF NOT EXISTS idx_cover_letters_job_id ON cover_letters(job_id);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
    DROP INDEX IF EXISTS idx_cover_letters_job_id;
    DROP INDEX IF EXISTS idx_cover_letters_user_id;
    DROP TABLE IF EXISTS cover_letters;
    """)
