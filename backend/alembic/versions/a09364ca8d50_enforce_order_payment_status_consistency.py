"""enforce order payment status consistency

Revision ID: a09364ca8d50
Revises: 646f565b7940
Create Date: 2026-11-04 19:43:44.404827

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a09364ca8d50'
down_revision: Union[str, Sequence[str], None] = '646f565b7940'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "chk_order_payment_status_consistency",
        "orders",
        """
        (
            (status = 'DELIVERED' AND payment_status = 'PAID')
            OR
            (
                status IN ('PENDING', 'CONFIRMED', 'CANCELLED')
                AND payment_status = 'UNPAID'
            )
        )
        """,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "chk_order_payment_status_consistency",
        "orders",
        type_="check",
    )