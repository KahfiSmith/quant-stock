"""add price provenance fields

Revision ID: 0007_price_provenance
Revises: 0006_fundamental_provenance
Create Date: 2026-08-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_price_provenance"
down_revision: str | None = "0006_fundamental_provenance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("prices", sa.Column("source_record_id", sa.String(length=128), nullable=True))
    op.add_column("prices", sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("prices", sa.Column("payload_checksum", sa.String(length=128), nullable=True))
    op.add_column(
        "prices",
        sa.Column("validation_state", sa.String(length=16), nullable=False, server_default="valid"),
    )


def downgrade() -> None:
    op.drop_column("prices", "validation_state")
    op.drop_column("prices", "payload_checksum")
    op.drop_column("prices", "retrieved_at")
    op.drop_column("prices", "source_record_id")
