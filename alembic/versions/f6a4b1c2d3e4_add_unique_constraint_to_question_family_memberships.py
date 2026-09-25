"""Add unique constraint on question_id in question_family_memberships.

Revision ID: f6a4b1c2d3e4
Revises: e5f3b9c8d2a1
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "f6a4b1c2d3e4"
down_revision: Union[str, Sequence[str], None] = "e5f3b9c8d2a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("question_family_memberships"):
        with op.batch_alter_table("question_family_memberships", schema=None) as batch_op:
            batch_op.create_unique_constraint(
                "uq_question_family_memberships_question_id",
                ["question_id"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("question_family_memberships"):
        with op.batch_alter_table("question_family_memberships", schema=None) as batch_op:
            batch_op.drop_constraint("uq_question_family_memberships_question_id", type_="unique")
