"""Add intelligence_snapshots table for deterministic snapshot caching.

Revision ID: e5f3b9c8d2a1
Revises: c4e2a8d7f1b9
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "e5f3b9c8d2a1"
down_revision: Union[str, Sequence[str], None] = "c4e2a8d7f1b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("intelligence_snapshots"):
        op.create_table(
            "intelligence_snapshots",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
            sa.Column("track_id", sa.Integer(), sa.ForeignKey("course_tracks.id", ondelete="SET NULL"), nullable=True),
            sa.Column("cache_key", sa.String(length=255), nullable=False),
            sa.Column("assessment_cycle", sa.String(length=50), nullable=False),
            sa.Column("model_version", sa.String(length=50), nullable=False),
            sa.Column("taxonomy_version", sa.String(length=50), nullable=False),
            sa.Column("corpus_version", sa.String(length=50), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("cache_key", name="uq_intel_snapshots_cache_key"),
        )
        op.create_index("ix_intel_snapshots_course_id", "intelligence_snapshots", ["course_id"])
        op.create_index("ix_intel_snapshots_track_id", "intelligence_snapshots", ["track_id"])
        op.create_index("ix_intel_snapshots_cache_key", "intelligence_snapshots", ["cache_key"])
        op.create_index("ix_intel_snapshots_course_cycle", "intelligence_snapshots", ["course_id", "assessment_cycle"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("intelligence_snapshots"):
        op.drop_table("intelligence_snapshots")
