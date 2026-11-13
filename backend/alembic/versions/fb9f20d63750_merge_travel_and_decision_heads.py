"""merge_travel_and_decision_heads

Revision ID: fb9f20d63750
Revises: 0ffe6300e06b, f92a86007329
Create Date: 2026-11-13 19:49:28.647383

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb9f20d63750'
down_revision: Union[str, Sequence[str], None] = ('0ffe6300e06b', 'f92a86007329')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
