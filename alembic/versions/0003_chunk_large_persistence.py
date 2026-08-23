"""Chunk large checkpoint and world snapshot payloads.

Revision ID: 0003_chunk_large_persistence
Revises: 0002_compress_checkpoints
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_chunk_large_persistence"
down_revision = "0002_compress_checkpoints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "checkpoint_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("checkpoint_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("checkpoints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("checkpoint_id", "chunk_index", name="uq_checkpoint_chunk_index"),
    )
    op.create_index("ix_checkpoint_chunks_checkpoint", "checkpoint_chunks", ["checkpoint_id", "chunk_index"])

    op.create_table(
        "world_snapshot_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("world_snapshots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("snapshot_id", "chunk_index", name="uq_world_snapshot_chunk_index"),
    )
    op.create_index("ix_world_snapshot_chunks_snapshot", "world_snapshot_chunks", ["snapshot_id", "chunk_index"])


def downgrade() -> None:
    op.drop_index("ix_world_snapshot_chunks_snapshot", table_name="world_snapshot_chunks")
    op.drop_table("world_snapshot_chunks")
    op.drop_index("ix_checkpoint_chunks_checkpoint", table_name="checkpoint_chunks")
    op.drop_table("checkpoint_chunks")
