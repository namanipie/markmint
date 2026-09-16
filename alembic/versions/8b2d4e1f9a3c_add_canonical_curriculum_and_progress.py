"""Add canonical curriculum and course metadata columns.

Revision ID: 8b2d4e1f9a3c
Revises: 7a1c2d3e4f50
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "8b2d4e1f9a3c"
down_revision: Union[str, Sequence[str], None] = "7a1c2d3e4f50"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. Enrich courses table with canonical metadata
    course_columns = {column["name"] for column in inspector.get_columns("courses")}
    with op.batch_alter_table("courses", schema=None) as batch_op:
        if "canonical_code" not in course_columns:
            batch_op.add_column(sa.Column("canonical_code", sa.String(length=32), nullable=True))
            batch_op.create_index("ix_courses_canonical_code", ["canonical_code"], unique=False)
        if "regulation_year" not in course_columns:
            batch_op.add_column(sa.Column("regulation_year", sa.Integer(), nullable=True))
        if "department" not in course_columns:
            batch_op.add_column(sa.Column("department", sa.String(length=120), nullable=True))

    # 2. Create curriculum_mappings table idempotently
    if not inspector.has_table("curriculum_mappings"):
        op.create_table(
            "curriculum_mappings",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("branch_name", sa.String(length=120), nullable=False),
            sa.Column("semester", sa.Integer(), nullable=False),
            sa.Column("curriculum_id", sa.String(length=64), nullable=False),
            sa.Column("subject_name", sa.String(length=255), nullable=False),
            sa.Column("credits", sa.Integer(), server_default="3", nullable=False),
            sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="SET NULL"), nullable=True),
            sa.Column("status", sa.String(length=32), server_default="UNMATCHED", nullable=False),
            sa.Column("notes", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_curriculum_mappings_branch_name", "curriculum_mappings", ["branch_name"])
        op.create_index("ix_curriculum_mappings_semester", "curriculum_mappings", ["semester"])
        op.create_index("ix_curriculum_mappings_subject_name", "curriculum_mappings", ["subject_name"])
        op.create_index("ix_curriculum_mappings_course_id", "curriculum_mappings", ["course_id"])
        op.create_index("uq_branch_sem_curr_id", "curriculum_mappings", ["branch_name", "semester", "curriculum_id"], unique=True)
        op.create_index("idx_branch_sem_status", "curriculum_mappings", ["branch_name", "semester", "status"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("curriculum_mappings"):
        op.drop_table("curriculum_mappings")

    course_columns = {column["name"] for column in inspector.get_columns("courses")}
    with op.batch_alter_table("courses", schema=None) as batch_op:
        if "canonical_code" in course_columns:
            batch_op.drop_column("canonical_code")
        if "regulation_year" in course_columns:
            batch_op.drop_column("regulation_year")
        if "department" in course_columns:
            batch_op.drop_column("department")
