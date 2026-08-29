"""Refactor waste knowledge into atomic facts and add facility access state."""

from typing import Sequence, Union

from alembic import op

revision: str = "20260829_0002"
down_revision: Union[str, None] = "20260827_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE waste_knowledge ADD COLUMN content text")
    op.execute("UPDATE waste_knowledge SET content = management_guidance")
    op.execute(
        """
        INSERT INTO waste_knowledge (
            id, category_id, condition_scope, content, source, source_url,
            last_reviewed_at, is_active, created_at, updated_at
        )
        SELECT gen_random_uuid(), wk.category_id, wk.condition_scope, item.value,
               wk.source, wk.source_url, wk.last_reviewed_at, wk.is_active,
               wk.created_at, wk.updated_at
        FROM waste_knowledge AS wk
        CROSS JOIN LATERAL jsonb_array_elements_text(
            COALESCE(wk.preparation_guidance, '[]'::jsonb) || COALESCE(wk.warnings, '[]'::jsonb)
        ) AS item(value)
        WHERE item.value <> ''
        """
    )
    op.execute("ALTER TABLE waste_knowledge ALTER COLUMN content SET NOT NULL")
    op.execute("ALTER TABLE waste_knowledge DROP COLUMN management_guidance")
    op.execute("ALTER TABLE waste_knowledge DROP COLUMN preparation_guidance")
    op.execute("ALTER TABLE waste_knowledge DROP COLUMN warnings")

    op.execute("CREATE TYPE facility_access_scope AS ENUM ('PUBLIC', 'COMMUNITY', 'INTERNAL', 'UNKNOWN')")
    op.execute(
        "ALTER TABLE facilities ADD COLUMN access_scope facility_access_scope NOT NULL DEFAULT 'UNKNOWN'"
    )
    op.execute("ALTER TABLE facilities ADD COLUMN is_active boolean NOT NULL DEFAULT true")
    op.execute("CREATE INDEX ix_facilities_public_active ON facilities(verified, is_active, access_scope)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_facilities_public_active")
    op.execute("ALTER TABLE facilities DROP COLUMN is_active")
    op.execute("ALTER TABLE facilities DROP COLUMN access_scope")
    op.execute("DROP TYPE facility_access_scope")

    op.execute("ALTER TABLE waste_knowledge ADD COLUMN management_guidance text")
    op.execute("ALTER TABLE waste_knowledge ADD COLUMN preparation_guidance jsonb NOT NULL DEFAULT '[]'::jsonb")
    op.execute("ALTER TABLE waste_knowledge ADD COLUMN warnings jsonb NOT NULL DEFAULT '[]'::jsonb")
    op.execute("UPDATE waste_knowledge SET management_guidance = content")
    op.execute("ALTER TABLE waste_knowledge ALTER COLUMN management_guidance SET NOT NULL")
    op.execute("ALTER TABLE waste_knowledge DROP COLUMN content")
