"""create todos table

Revision ID: c3611d830b95
Revises: b33cdafd061a
Create Date: 2025-06-14 14:09:32.201408

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3611d830b95'
down_revision: Union[str, None] = 'b33cdafd061a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
