"""add fundamental provenance fields

Revision ID: 0006_fundamental_provenance
Revises: 0005_transaction_constraints
Create Date: 2026-08-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_fundamental_provenance"
down_revision: str | None = "0005_transaction_constraints"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("fundamentals", sa.Column("currency", sa.String(length=8), nullable=True))
    op.add_column("fundamentals", sa.Column("source_record_id", sa.String(length=128), nullable=True))
    op.add_column("fundamentals", sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("fundamentals", sa.Column("payload_checksum", sa.String(length=128), nullable=True))
    op.add_column(
        "fundamentals",
        sa.Column("validation_state", sa.String(length=16), nullable=False, server_default="flagged"),
    )


def downgrade() -> None:
    op.drop_column("fundamentals", "validation_state")
    op.drop_column("fundamentals", "payload_checksum")
    op.drop_column("fundamentals", "retrieved_at")
    op.drop_column("fundamentals", "source_record_id")
    op.drop_column("fundamentals", "currency")
