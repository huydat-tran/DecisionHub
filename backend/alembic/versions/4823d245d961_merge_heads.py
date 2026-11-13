"""merge_heads

Revision ID: 4823d245d961
Revises: 0ffe6300e06b, f92a86007329
Create Date: 2026-11-13 20:23:28.789508

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4823d245d961'
down_revision: Union[str, Sequence[str], None] = ('0ffe6300e06b', 'f92a86007329')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
