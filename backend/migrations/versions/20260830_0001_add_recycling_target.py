"""add recycling_target column

Revision ID: 20260830_0001
Revises: 20260829_0002
Create Date: 2026-08-30

"""
from alembic import op
import sqlalchemy as sa


revision = "20260830_0001"
down_revision = "20260829_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("waste_scans", sa.Column("recycling_target", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("waste_scans", "recycling_target")
