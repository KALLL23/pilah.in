"""add recycling_products column

Revision ID: 0614c6ec7b90
Revises: 20260830_0001
Create Date: 2026-08-31 16:00:41.761546+07:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0614c6ec7b90"
down_revision: Union[str, None] = "20260830_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "waste_scans",
        sa.Column("recycling_products", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("waste_scans", "recycling_products")