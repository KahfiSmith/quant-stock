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
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.create_check_constraint(
            "ck_transactions_type",
            "transaction_type IN ('BUY', 'SELL')",
        )
        batch_op.create_check_constraint(
            "ck_transactions_quantity_positive",
            "quantity > 0",
        )
        batch_op.create_check_constraint(
            "ck_transactions_price_positive",
            "price > 0",
        )
        batch_op.create_check_constraint(
            "ck_transactions_fee_nonnegative",
            "fee >= 0",
        )


def downgrade() -> None:
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.drop_constraint("ck_transactions_fee_nonnegative", type_="check")
        batch_op.drop_constraint("ck_transactions_price_positive", type_="check")
        batch_op.drop_constraint("ck_transactions_quantity_positive", type_="check")
        batch_op.drop_constraint("ck_transactions_type", type_="check")
