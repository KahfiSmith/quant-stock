"""normalize unique lookup indexes

Revision ID: 0009_unique_lookup_indexes
Revises: 0008_user_preferences
Create Date: 2026-08-27
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0009_unique_lookup_indexes"
down_revision: str | None = "0008_user_preferences"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_sessions_family_id", table_name="sessions")
    op.drop_index("ix_stocks_symbol", table_name="stocks")
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_sessions_family_id", "sessions", ["family_id"], unique=True)
    op.create_index("ix_stocks_symbol", "stocks", ["symbol"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_stocks_symbol", table_name="stocks")
    op.drop_index("ix_sessions_family_id", table_name="sessions")
    op.drop_index("ix_users_email", table_name="users")
    op.create_index("ix_stocks_symbol", "stocks", ["symbol"])
    op.create_index("ix_sessions_family_id", "sessions", ["family_id"])
    op.create_index("ix_users_email", "users", ["email"])
