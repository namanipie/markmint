"""add_track_id_to_question_families

Revision ID: 98a712a69b11
Revises: f6a4b1c2d3e4
Create Date: 2026-09-25 22:14:04.000434

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98a712a69b11'
down_revision: Union[str, Sequence[str], None] = 'f6a4b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nullable track_id column and index to question_families."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("question_families")}
    with op.batch_alter_table("question_families", schema=None) as batch_op:
        if "track_id" not in cols:
            batch_op.add_column(sa.Column("track_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_question_families_track_id",
                "course_tracks",
                ["track_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch_op.create_index("ix_question_families_track_id", ["track_id"], unique=False)


def downgrade() -> None:
    """Remove track_id column and index from question_families."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("question_families")}
    with op.batch_alter_table("question_families", schema=None) as batch_op:
        if "track_id" in cols:
            batch_op.drop_index("ix_question_families_track_id")
            batch_op.drop_constraint("fk_question_families_track_id", type_="foreignkey")
            batch_op.drop_column("track_id")
