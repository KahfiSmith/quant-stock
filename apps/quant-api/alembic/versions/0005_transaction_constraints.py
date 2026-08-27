"""add transaction integrity constraints

Revision ID: 0005_transaction_constraints
Revises: 0004_portfolios
Create Date: 2026-08-27
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_transaction_constraints"
down_revision: str | None = "0004_portfolios"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_transactions_type",
        "transactions",
        "transaction_type IN ('BUY', 'SELL')",
    )
    op.create_check_constraint(
        "ck_transactions_quantity_positive",
        "transactions",
        "quantity > 0",
    )
    op.create_check_constraint(
        "ck_transactions_price_positive",
        "transactions",
        "price > 0",
    )
    op.create_check_constraint(
        "ck_transactions_fee_nonnegative",
        "transactions",
        "fee >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_transactions_fee_nonnegative", "transactions", type_="check")
    op.drop_constraint("ck_transactions_price_positive", "transactions", type_="check")
    op.drop_constraint("ck_transactions_quantity_positive", "transactions", type_="check")
    op.drop_constraint("ck_transactions_type", "transactions", type_="check")
