"""Create Genesis persistent storage schema.

Revision ID: 0001_genesis_persistence
"""
from alembic import op

from genesis.persistence.models import Base

revision = "0001_genesis_persistence"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(op.get_bind())
