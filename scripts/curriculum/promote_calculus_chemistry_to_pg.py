"""
Production Migration: Promote Canonical 5-Unit Structure for Calculus and Chemistry to Render PostgreSQL.

Authoritative Syllabus Grounding:
- Calculus (21MAB101T): SRMIST B.Tech Reg 2021 Syllabus
  1. Matrices and Linear Algebra
  2. Functions of Several Variables
  3. Ordinary Differential Equations
  4. Differential Calculus and Geometrical Applications
  5. Sequences and Series
- Chemistry (21CYB101J): SRMIST 5-Module Syllabus
  1. Periodic Properties and Atomic Structure
  2. Chemical Equilibria and Electrochemistry
  3. Stereo Chemistry And Organic Reactions
  4. Polymers
  5. Advanced Engineering Materials

Safeguards:
- Atomic single-transaction with rollback on failure
- Verifies 192 Chemistry question mappings are preserved with 0 lost
- Purges stale intelligence_snapshots for clean cache rebuild
- Unbuffered stdout for immediate progress visibility
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

BASE_DIR = r"c:\Users\ASUS\Desktop\system"
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.models.core import Course, Syllabus, Unit, Topic, Question, Exam, question_topic

PG_URL = os.environ.get(
    "RENDER_DATABASE_URL",
    "postgresql://markmint_user:RDXfizQBWXFjhEUbfshlumjwuQajSUFR@dpg-dakpv1gu01pc73bj47e0-a.oregon-postgres.render.com/markmint?sslmode=require"
).replace("postgresql://", "postgresql+psycopg2://")

def run_pg_migration():
    print("=" * 80, flush=True)
    print("PROMOTING CANONICAL 5-UNIT CURRICULUM INTEGRITY TO RENDER POSTGRESQL", flush=True)
    print("=" * 80, flush=True)
    
    engine = create_engine(PG_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # ======================================================================
        # 1. CALCULUS (Course 1)
        # ======================================================================
        print("\n--- 1. Migrating Course 1 (Calculus) in Render Postgres ---", flush=True)
        calc_syl = db.query(Syllabus).filter(Syllabus.course_id == 1).first()
        assert calc_syl is not None, "Calculus syllabus not found"

        # A. Handle Exam 4 (Math Sample 2): ACCA questions
        e4 = db.query(Exam).filter(Exam.id == 4).first()
        if e4 and e4.course_id == 1:
            print("Reassigning Exam 4 ('Math Sample 2' - MA1002 ACCA paper) to Course 16 (ACCA)...", flush=True)
            # Unlink questions from Course 1 rogue topics
            for q_id in [17, 18, 19, 20, 21, 22, 23, 24, 25, 26]:
                db.execute(
                    question_topic.delete().where(
                        question_topic.c.question_id == q_id,
                        question_topic.c.topic_id.in_([9, 18, 36, 39])
                    )
                )
            e4.course_id = 16
            db.flush()
            print("Exam 4 unlinked from rogue topics and reassigned to Course 16.", flush=True)

        # B. Identify keep units and rogue units
        # Existing units in Calculus:
        # 1: 13, 2: 14, 3: 15, 4: 16, 5: 17, 6: 18, 7: 19, 8: 25, 9: 26
        u1_id = 13  # Unit 1: Matrices and Linear Algebra
        u2_id = 18  # Unit 2: Functions of Several Variables (Old Unit 6)
        u3_id = 14  # Unit 3: Ordinary Differential Equations (Old Unit 2)
        u4_id = 19  # Unit 4: Differential Calculus and Geometrical Applications (Old Unit 7)
        u5_id = 17  # Unit 5: Sequences and Series (Old Unit 5)
        keep_unit_ids = [u1_id, u2_id, u3_id, u4_id, u5_id]
        rogue_unit_ids = [15, 16, 25, 26]

        print(f"Keep Unit IDs: {keep_unit_ids}, Rogue Unit IDs: {rogue_unit_ids}", flush=True)

        # C. Move topics to canonical units before pruning rogue units
        # Move Topic 35 (Taylor Series) to Unit 2 (u2_id)
        t35 = db.query(Topic).filter(Topic.id == 35).first()
        if t35:
            t35.unit_id = u2_id

        # Move Topic 17 (Beta and Gamma Functions) to Unit 4 (u4_id)
        t17 = db.query(Topic).filter(Topic.id == 17).first()
        if t17:
            t17.name = "Beta and Gamma Functions"
            t17.unit_id = u4_id

        # Ensure canonical Unit 4 topics exist
        existing_u4_topic_names = {t.name for t in db.query(Topic).filter(Topic.unit_id == u4_id).all()}
        if "Radius and Circle of Curvature" not in existing_u4_topic_names:
            db.add(Topic(unit_id=u4_id, name="Radius and Circle of Curvature"))
        if "Evolutes and Envelopes" not in existing_u4_topic_names:
            db.add(Topic(unit_id=u4_id, name="Evolutes and Envelopes"))
        db.flush()

        # D. Clean up FK references on rogue topics and rogue units
        rogue_str = ','.join(str(i) for i in rogue_unit_ids)
        db.execute(text(f"UPDATE concepts SET unit_id = {u4_id} WHERE unit_id IN ({rogue_str}) AND (canonical_name LIKE '%Gamma%' OR canonical_name LIKE '%Beta%')"))
        db.execute(text(f"UPDATE concepts SET unit_id = NULL WHERE unit_id IN ({rogue_str})"))
        db.execute(text(f"DELETE FROM assessment_coverages WHERE unit_id IN ({rogue_str})"))

        # Delete rogue Calculus topics (7, 8, 9, 10, 18, 19, 36, 37, 38, 39)
        rogue_topic_ids = [7, 8, 9, 10, 18, 19, 36, 37, 38, 39]
        for rt_id in rogue_topic_ids:
            db.execute(text(f"DELETE FROM question_topic WHERE topic_id = {rt_id}"))
            db.execute(text(f"DELETE FROM assessment_coverages WHERE topic_id = {rt_id}"))
            db.execute(text(f"DELETE FROM subtopics WHERE topic_id = {rt_id}"))
            db.execute(text(f"DELETE FROM student_topic_progress WHERE topic_id = {rt_id}"))
            rt = db.query(Topic).filter(Topic.id == rt_id).first()
            if rt:
                db.delete(rt)
        db.flush()

        # E. Set rogue units to negative numbers so they don't block 1..5 unique constraint, then delete
        db.execute(text(f"UPDATE units SET number = -id WHERE id IN ({rogue_str})"))
        db.flush()

        for ru_id in rogue_unit_ids:
            ru = db.query(Unit).filter(Unit.id == ru_id).first()
            if ru:
                db.delete(ru)
        db.flush()
        print("Rogue Calculus units deleted.", flush=True)

        # F. Re-number and rename canonical 5 units
        db.execute(text(f"""
            UPDATE units
            SET number = CASE id
                WHEN {u1_id} THEN 1
                WHEN {u2_id} THEN 2
                WHEN {u3_id} THEN 3
                WHEN {u4_id} THEN 4
                WHEN {u5_id} THEN 5
            END,
            name = CASE id
                WHEN {u1_id} THEN 'Matrices and Linear Algebra'
                WHEN {u2_id} THEN 'Functions of Several Variables'
                WHEN {u3_id} THEN 'Ordinary Differential Equations'
                WHEN {u4_id} THEN 'Differential Calculus and Geometrical Applications'
                WHEN {u5_id} THEN 'Sequences and Series'
            END
            WHERE id IN ({u1_id}, {u2_id}, {u3_id}, {u4_id}, {u5_id})
        """))
        db.flush()

        # Verify Calculus units
        final_calc_units = db.query(Unit).filter(Unit.syllabus_id == calc_syl.id).order_by(Unit.number).all()
        print(f"Calculus now has {len(final_calc_units)} units:", flush=True)
        for u in final_calc_units:
            t_count = db.query(Topic).filter(Topic.unit_id == u.id).count()
            print(f"  Unit {u.number}: {u.name} (ID: {u.id}) - {t_count} topics", flush=True)
        assert len(final_calc_units) == 5, f"Calculus must have 5 units, got {len(final_calc_units)}"

        # ======================================================================
        # 2. CHEMISTRY (Course 2)
        # ======================================================================
        print("\n--- 2. Migrating Course 2 (Chemistry) in Render Postgres ---", flush=True)
        chem_syl = db.query(Syllabus).filter(Syllabus.course_id == 2).first()
        assert chem_syl is not None, "Chemistry syllabus not found"

        u1_c_id = 20  # Unit 1: Periodic Properties and Atomic Structure
        u2_c_id = 21  # Unit 2: Chemical Equilibria and Electrochemistry
        u3_c_id = 22  # Unit 3: Stereo Chemistry And Organic Reactions
        u4_c_id = 23  # Unit 4: Polymers
        u5_c_id = 24  # Unit 5: Advanced Engineering Materials
        chem_rogue_unit_ids = [27, 28, 29, 30, 31, 32, 33]

        # A. Rename canonical units
        db.execute(text(f"""
            UPDATE units
            SET name = CASE id
                WHEN {u1_c_id} THEN 'Periodic Properties and Atomic Structure'
                WHEN {u2_c_id} THEN 'Chemical Equilibria and Electrochemistry'
                WHEN {u3_c_id} THEN 'Stereo Chemistry And Organic Reactions'
                WHEN {u4_c_id} THEN 'Polymers'
                WHEN {u5_c_id} THEN 'Advanced Engineering Materials'
            END
            WHERE id IN ({u1_c_id}, {u2_c_id}, {u3_c_id}, {u4_c_id}, {u5_c_id})
        """))
        db.flush()

        # B. Reassign topics:
        u1_topic_ids = [20, 21, 22, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53]
        u2_topic_ids = [23, 24, 25, 61, 62, 63, 64, 65, 66]
        u3_topic_ids = [26, 27, 67, 68, 69, 70, 71, 72]
        u4_topic_ids = [28, 29]
        u5_topic_ids = [30, 31, 54, 55, 56, 57, 58, 59, 60]

        db.execute(text(f"UPDATE topics SET unit_id = {u1_c_id} WHERE id IN ({','.join(str(i) for i in u1_topic_ids)})"))
        db.execute(text(f"UPDATE topics SET unit_id = {u2_c_id} WHERE id IN ({','.join(str(i) for i in u2_topic_ids)})"))
        db.execute(text(f"UPDATE topics SET unit_id = {u3_c_id} WHERE id IN ({','.join(str(i) for i in u3_topic_ids)})"))
        db.execute(text(f"UPDATE topics SET unit_id = {u4_c_id} WHERE id IN ({','.join(str(i) for i in u4_topic_ids)})"))
        db.execute(text(f"UPDATE topics SET unit_id = {u5_c_id} WHERE id IN ({','.join(str(i) for i in u5_topic_ids)})"))
        db.flush()
        print("Chemistry topics reassigned to Units 1..5.", flush=True)

        # C. Update concepts unit_id before deleting rogue units
        chem_rogue_str = ','.join(str(i) for i in chem_rogue_unit_ids)
        db.execute(text(f"UPDATE concepts SET unit_id = {u1_c_id} WHERE unit_id IN (27, 28, 29)"))
        db.execute(text(f"UPDATE concepts SET unit_id = {u2_c_id} WHERE unit_id IN (32, 33)"))
        db.execute(text(f"UPDATE concepts SET unit_id = {u5_c_id} WHERE unit_id IN (30, 31)"))
        db.execute(text(f"DELETE FROM assessment_coverages WHERE unit_id IN ({chem_rogue_str})"))
        db.flush()

        # D. Set rogue units to negative numbers then delete
        db.execute(text(f"UPDATE units SET number = -id WHERE id IN ({chem_rogue_str})"))
        db.flush()

        for ru_id in chem_rogue_unit_ids:
            ru = db.query(Unit).filter(Unit.id == ru_id).first()
            if ru:
                db.delete(ru)
        db.flush()
        print("Rogue Chemistry units deleted.", flush=True)

        # E. Verify Chemistry units
        final_chem_units = db.query(Unit).filter(Unit.syllabus_id == chem_syl.id).order_by(Unit.number).all()
        print(f"Chemistry now has {len(final_chem_units)} units:", flush=True)
        for u in final_chem_units:
            t_count = db.query(Topic).filter(Topic.unit_id == u.id).count()
            print(f"  Unit {u.number}: {u.name} (ID: {u.id}) - {t_count} topics", flush=True)
        assert len(final_chem_units) == 5, f"Chemistry must have 5 units, got {len(final_chem_units)}"

        # F. Verify total question mappings across Chemistry topics
        chem_topic_ids = u1_topic_ids + u2_topic_ids + u3_topic_ids + u4_topic_ids + u5_topic_ids
        total_chem_q = (
            db.query(Question.id)
            .join(question_topic, question_topic.c.question_id == Question.id)
            .filter(question_topic.c.topic_id.in_(chem_topic_ids))
            .count()
        )
        print(f"Total Chemistry question mappings preserved: {total_chem_q} (Expected: 192)", flush=True)
        assert total_chem_q == 192, f"Expected 192 question mappings in Chemistry, got {total_chem_q}"

        # Clean up any obsolete CT3 component in assessment_components
        db.execute(text("DELETE FROM assessment_coverages WHERE assessment_component_id IN (SELECT id FROM assessment_components WHERE code = 'CT3' AND course_id = 2)"))
        db.execute(text("DELETE FROM assessment_components WHERE code = 'CT3' AND course_id = 2"))
        db.flush()

        # ======================================================================
        # 3. COURSE 19: Prune orphan Syllabus 24
        # ======================================================================
        print("\n--- 3. Pruning Course 19 orphan Syllabus 24 ---", flush=True)
        orphan_syl24 = db.query(Syllabus).filter(Syllabus.id == 24, Syllabus.course_id == 19).first()
        if orphan_syl24:
            u_count = db.query(Unit).filter(Unit.syllabus_id == 24).count()
            if u_count == 0:
                db.delete(orphan_syl24)
                db.flush()
                print("Deleted empty orphan Syllabus 24.", flush=True)

        # ======================================================================
        # 4. SNAPSHOTS: Purge stale snapshots
        # ======================================================================
        print("\n--- 4. Purging stale intelligence_snapshots in Render Postgres ---", flush=True)
        del_snaps = db.execute(text("DELETE FROM intelligence_snapshots WHERE course_id IN (1, 2)"))
        print(f"Purged {del_snaps.rowcount} stale snapshots for Courses 1 and 2.", flush=True)

        # Also purge any snapshots with obsolete schema or versions
        del_all = db.execute(text("DELETE FROM intelligence_snapshots"))
        print(f"Purged all {del_all.rowcount} snapshots to ensure fresh rebuild.", flush=True)

        db.commit()
        print("\n" + "=" * 80, flush=True)
        print("ALL CANONICAL 5-UNIT MIGRATIONS COMMITTED TO RENDER POSTGRESQL!", flush=True)
        print("=" * 80, flush=True)

    except Exception as e:
        db.rollback()
        print(f"\nROLLBACK DUE TO ERROR: {e}", flush=True)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_pg_migration()
