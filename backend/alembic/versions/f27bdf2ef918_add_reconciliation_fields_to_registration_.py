"""add reconciliation fields to registration folder

Revision ID: f27bdf2ef918
Revises: 31d805886dd9
Create Date: 2026-06-28 04:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f27bdf2ef918'
down_revision: Union[str, None] = '31d805886dd9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('registrationfolder', sa.Column('is_reconciled', sa.Boolean(), nullable=True))
    op.add_column('registrationfolder', sa.Column('pennylane_invoice_id', sa.String(), nullable=True))
    op.add_column('registrationfolder', sa.Column('pennylane_invoice_number', sa.String(), nullable=True))
    op.add_column('registrationfolder', sa.Column('pennylane_paid_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('registrationfolder', sa.Column('wedof_paid_date', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('registrationfolder', 'wedof_paid_date')
    op.drop_column('registrationfolder', 'pennylane_paid_date')
    op.drop_column('registrationfolder', 'pennylane_invoice_number')
    op.drop_column('registrationfolder', 'pennylane_invoice_id')
    op.drop_column('registrationfolder', 'is_reconciled')
