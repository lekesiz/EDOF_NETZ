"""add settings table

Revision ID: a5214eba7575
Revises: f27bdf2ef918
Create Date: 2026-06-28 05:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5214eba7575'
down_revision: Union[str, None] = 'f27bdf2ef918'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    settings = op.create_table(
        'settings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )
    op.bulk_insert(
        settings,
        [
            {
                "id": "target-2026",
                "key": "target_2026",
                "value": "0",
                "description": "Objectif CA 2026 (EUR)",
                "updated_at": "2026-06-28 00:00:00+00:00",
            },
            {
                "id": "target-2027",
                "key": "target_2027",
                "value": "0",
                "description": "Objectif CA 2027 (EUR)",
                "updated_at": "2026-06-28 00:00:00+00:00",
            },
            {
                "id": "vade-gun",
                "key": "vade_gun",
                "value": "37",
                "description": "Nombre de jours apres la fin de formation pour l'echeance",
                "updated_at": "2026-06-28 00:00:00+00:00",
            },
        ],
    )


def downgrade() -> None:
    op.drop_table('settings')
