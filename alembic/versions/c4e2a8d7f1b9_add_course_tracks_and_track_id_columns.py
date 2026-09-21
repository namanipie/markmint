"""Add course_tracks table and track_id columns across syllabuses, exams, assessment plans, and submissions.

Revision ID: c4e2a8d7f1b9
Revises: 8b2d4e1f9a3c
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c4e2a8d7f1b9"
down_revision: Union[str, Sequence[str], None] = "8b2d4e1f9a3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. Create course_tracks table idempotently
    if not inspector.has_table("course_tracks"):
        op.create_table(
            "course_tracks",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
            sa.Column("track_key", sa.String(length=64), nullable=False),
            sa.Column("track_name", sa.String(length=120), nullable=False),
            sa.Column("track_code", sa.String(length=64), nullable=True),
            sa.Column("track_type", sa.String(length=32), server_default="LANGUAGE", nullable=False),
            sa.Column("source_metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("course_id", "track_key", name="uq_course_track_key"),
        )
        op.create_index("ix_course_tracks_course_id", "course_tracks", ["course_id"])
        op.create_index("ix_course_tracks_track_key", "course_tracks", ["track_key"])
        op.create_index("ix_course_tracks_track_code", "course_tracks", ["track_code"])

    # 2. Seed canonical Course 8 (Foreign Languages) tracks if Course 8 exists
    course_tracks_table = sa.table(
        "course_tracks",
        sa.column("id", sa.Integer),
        sa.column("course_id", sa.Integer),
        sa.column("track_key", sa.String),
        sa.column("track_name", sa.String),
        sa.column("track_code", sa.String),
        sa.column("track_type", sa.String),
        sa.column("source_metadata", sa.JSON),
        sa.column("created_at", sa.DateTime),
    )

    # Query existing tracks for course 8
    existing_tracks = {}
    if inspector.has_table("course_tracks"):
        res = bind.execute(sa.text("SELECT id, track_key FROM course_tracks WHERE course_id = 8")).fetchall()
        existing_tracks = {r[1]: r[0] for r in res}

    language_tracks = [
        {"id": 1, "key": "german", "name": "German", "code": "21LEH104T"},
        {"id": 2, "key": "french", "name": "French", "code": "21LEH103T"},
        {"id": 3, "key": "spanish", "name": "Spanish", "code": "21LEH107T"},
        {"id": 4, "key": "japanese", "name": "Japanese", "code": "21LEH105T"},
        {"id": 5, "key": "korean", "name": "Korean", "code": "21LEH106T"},
        {"id": 6, "key": "chinese", "name": "Chinese", "code": "21LEH102T"},
    ]

    # Check if Course 8 exists before inserting
    course_8_exists = bind.execute(sa.text("SELECT count(*) FROM courses WHERE id = 8")).scalar() > 0

    if course_8_exists:
        for lt in language_tracks:
            if lt["key"] not in existing_tracks:
                # Insert track record
                bind.execute(
                    course_tracks_table.insert().values(
                        id=lt["id"],
                        course_id=8,
                        track_key=lt["key"],
                        track_name=lt["name"],
                        track_code=lt["code"],
                        track_type="LANGUAGE",
                        source_metadata={
                            "syllabus_file": f"corpus/Semester_1/{lt['name']}/SYLLABUS/{lt['name']} - Syllabus.pdf",
                            "regulation": 2021
                        }
                    )
                )
                existing_tracks[lt["key"]] = lt["id"]

        # Reset sequence in Postgres if needed
        if bind.dialect.name == "postgresql":
            bind.execute(sa.text("SELECT setval(pg_get_serial_sequence('course_tracks', 'id'), coalesce(max(id), 1)) FROM course_tracks"))

    # 3. Add track_id to syllabuses table
    syllabuses_cols = {c["name"] for c in inspector.get_columns("syllabuses")}
    with op.batch_alter_table("syllabuses", schema=None) as batch_op:
        if "track_id" not in syllabuses_cols:
            batch_op.add_column(sa.Column("track_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_syllabuses_track_id",
                "course_tracks",
                ["track_id"],
                ["id"],
                ondelete="CASCADE"
            )
            batch_op.create_index("ix_syllabuses_track_id", ["track_id"])

    # 4. Add track_id to exams table
    exams_cols = {c["name"] for c in inspector.get_columns("exams")}
    with op.batch_alter_table("exams", schema=None) as batch_op:
        if "track_id" not in exams_cols:
            batch_op.add_column(sa.Column("track_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_exams_track_id",
                "course_tracks",
                ["track_id"],
                ["id"],
                ondelete="SET NULL"
            )
            batch_op.create_index("ix_exams_track_id", ["track_id"])
            batch_op.create_index("ix_exams_track_year", ["track_id", "year"])

    # 5. Add track_id to course_assessment_plans table
    plans_cols = {c["name"] for c in inspector.get_columns("course_assessment_plans")}
    with op.batch_alter_table("course_assessment_plans", schema=None) as batch_op:
        if "track_id" not in plans_cols:
            batch_op.add_column(sa.Column("track_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_course_assessment_plans_track_id",
                "course_tracks",
                ["track_id"],
                ["id"],
                ondelete="CASCADE"
            )
            batch_op.create_index("ix_course_assessment_plans_track_id", ["track_id"])

    # 6. Add track_id to paper_submissions table
    submissions_cols = {c["name"] for c in inspector.get_columns("paper_submissions")}
    with op.batch_alter_table("paper_submissions", schema=None) as batch_op:
        if "track_id" not in submissions_cols:
            batch_op.add_column(sa.Column("track_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_paper_submissions_track_id",
                "course_tracks",
                ["track_id"],
                ["id"],
                ondelete="SET NULL"
            )
            batch_op.create_index("ix_paper_submissions_track_id", ["track_id"])

    # 7. Map Course 8 Foreign Language exams to their exact track_id
    # Verified Exam IDs per language track
    exam_track_assignments = {
        "german": [48, 49, 50, 51, 52, 127],
        "french": [46, 47, 124, 125, 126, 134],
        "spanish": [88, 89, 90],
        "japanese": [57, 58, 59, 128, 129],
        "korean": [60, 61, 62, 63, 130, 131, 132, 133],
        "chinese": [31, 32, 122, 123],
    }

    for track_key, exam_ids in exam_track_assignments.items():
        track_id = existing_tracks.get(track_key)
        if track_id and exam_ids:
            id_list = ", ".join(str(int(x)) for x in exam_ids)
            bind.execute(
                sa.text(f"UPDATE exams SET track_id = :tid WHERE id IN ({id_list}) AND course_id = 8"),
                {"tid": track_id}
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. Remove track_id from paper_submissions
    if inspector.has_table("paper_submissions"):
        submissions_cols = {c["name"] for c in inspector.get_columns("paper_submissions")}
        submissions_idxs = {i["name"] for i in inspector.get_indexes("paper_submissions")}
        with op.batch_alter_table("paper_submissions", schema=None) as batch_op:
            if "track_id" in submissions_cols:
                if "ix_paper_submissions_track_id" in submissions_idxs:
                    batch_op.drop_index("ix_paper_submissions_track_id")
                batch_op.drop_column("track_id")

    # 2. Remove track_id from course_assessment_plans
    if inspector.has_table("course_assessment_plans"):
        plans_cols = {c["name"] for c in inspector.get_columns("course_assessment_plans")}
        plans_idxs = {i["name"] for i in inspector.get_indexes("course_assessment_plans")}
        with op.batch_alter_table("course_assessment_plans", schema=None) as batch_op:
            if "track_id" in plans_cols:
                if "ix_course_assessment_plans_track_id" in plans_idxs:
                    batch_op.drop_index("ix_course_assessment_plans_track_id")
                batch_op.drop_column("track_id")

    # 3. Remove track_id from exams
    if inspector.has_table("exams"):
        exams_cols = {c["name"] for c in inspector.get_columns("exams")}
        exams_idxs = {i["name"] for i in inspector.get_indexes("exams")}
        with op.batch_alter_table("exams", schema=None) as batch_op:
            if "track_id" in exams_cols:
                if "ix_exams_track_year" in exams_idxs:
                    batch_op.drop_index("ix_exams_track_year")
                if "ix_exams_track_id" in exams_idxs:
                    batch_op.drop_index("ix_exams_track_id")
                batch_op.drop_column("track_id")

    # 4. Remove track_id from syllabuses
    if inspector.has_table("syllabuses"):
        syllabuses_cols = {c["name"] for c in inspector.get_columns("syllabuses")}
        syllabuses_idxs = {i["name"] for i in inspector.get_indexes("syllabuses")}
        with op.batch_alter_table("syllabuses", schema=None) as batch_op:
            if "track_id" in syllabuses_cols:
                if "ix_syllabuses_track_id" in syllabuses_idxs:
                    batch_op.drop_index("ix_syllabuses_track_id")
                batch_op.drop_column("track_id")

    # 5. Drop course_tracks table
    if inspector.has_table("course_tracks"):
        op.drop_table("course_tracks")
