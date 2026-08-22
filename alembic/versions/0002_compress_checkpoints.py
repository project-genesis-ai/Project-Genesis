"""Store large checkpoint payloads in compressed binary form.

Revision ID: 0002_compress_checkpoints
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_compress_checkpoints"
down_revision = "0001_genesis_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "checkpoints",
        sa.Column("canonical_state_blob", sa.LargeBinary(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("checkpoints", "canonical_state_blob")
