"""
Migration script: Canonical 5-Unit Structure for Calculus and Chemistry.

Authoritative Syllabus Grounding:
- Calculus (21MAB101T): data/1 Year/MATHS/detailed sylabbus.docx (Template 6 Tables 1-5)
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

Also prunes empty orphan Syllabus 24 on Course 19.
Preserves all authentic question mappings and SHA-256 idempotency.
"""
import os
import sys
import shutil
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.core.database import SessionLocal
from backend.models.core import Course, Syllabus, Unit, Topic, Question, Exam, question_topic

def migrate():
    # 1. Backup DB
    db_file = "production_corpus.db"
    backup_file = "production_corpus.db.pre_taxonomy_migration_backup"
    if os.path.exists(db_file) and not os.path.exists(backup_file):
        shutil.copy2(db_file, backup_file)
        print(f"Backed up {db_file} to {backup_file}")

    db = SessionLocal()
    try:
        # ======================================================================
        # 1. CALCULUS (Course 1)
        # ======================================================================
        print("\n--- Migrating Course 1 (Calculus) ---")
        calc_syl = db.query(Syllabus).filter(Syllabus.course_id == 1).first()
        assert calc_syl is not None, "Calculus syllabus not found"

        # Handle Exam 4 (Math Sample 2): ACCA questions
        e4 = db.query(Exam).filter(Exam.id == 4).first()
        if e4 and e4.course_id == 1:
            print("Reassigning Exam 4 ('Math Sample 2' - MA1002 ACCA paper) to Course 16 (ACCA)...")
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

            # Map Exam 4 questions to canonical ACCA topics
            acca_mappings = [
                (17, 316), (18, 317), (19, 319), (21, 324), (25, 337), (26, 335)
            ]
            for q_id, t_id in acca_mappings:
                db.execute(question_topic.insert().values(question_id=q_id, topic_id=t_id))
            db.flush()

        # Existing units in Calculus
        existing_calc_units = {u.number: u for u in db.query(Unit).filter(Unit.syllabus_id == calc_syl.id).all()}
        
        # Unit 1: Matrices and Linear Algebra (ID 13)
        u1 = existing_calc_units.get(1)
        u1.name = "Matrices and Linear Algebra"

        # Unit 2: Functions of Several Variables (Old Unit 6, ID 18)
        u2 = existing_calc_units.get(6)
        assert u2 is not None, "Old Unit 6 not found"
        u2.name = "Functions of Several Variables"

        # Move Topic 35 (Taylor Series) to Unit 2
        t35 = db.query(Topic).filter(Topic.id == 35).first()
        if t35:
            t35.unit_id = u2.id

        # Unit 3: Ordinary Differential Equations (Old Unit 2, ID 14)
        u3 = existing_calc_units.get(2)
        assert u3 is not None, "Old Unit 2 not found"
        u3.name = "Ordinary Differential Equations"

        # Unit 4: Differential Calculus and Geometrical Applications
        u4 = existing_calc_units.get(4) or existing_calc_units.get(7)
        assert u4 is not None, "Unit 4 slot not found"
        u4.name = "Differential Calculus and Geometrical Applications"

        # Move Topic 17 (Beta and Gamma Functions) to Unit 4
        t17 = db.query(Topic).filter(Topic.id == 17).first()
        if t17:
            t17.name = "Beta and Gamma Functions"
            t17.unit_id = u4.id

        # Check / add canonical Unit 4 topics if not present
        existing_u4_topic_names = {t.name for t in db.query(Topic).filter(Topic.unit_id == u4.id).all()}
        if "Radius and Circle of Curvature" not in existing_u4_topic_names:
            db.add(Topic(unit_id=u4.id, name="Radius and Circle of Curvature"))
        if "Evolutes and Envelopes" not in existing_u4_topic_names:
            db.add(Topic(unit_id=u4.id, name="Evolutes and Envelopes"))

        # Unit 5: Sequences and Series (Old Unit 5, ID 17)
        u5 = existing_calc_units.get(5)
        assert u5 is not None, "Old Unit 5 not found"
        u5.name = "Sequences and Series"

        # Re-number canonical units to 1..5 safely
        u1.number = 101
        u2.number = 102
        u3.number = 103
        u4.number = 104
        u5.number = 105
        db.flush()

        u1.number = 1
        u2.number = 2
        u3.number = 3
        u4.number = 4
        u5.number = 5
        db.flush()

        # Identify rogue calculus units
        keep_unit_ids = {u1.id, u2.id, u3.id, u4.id, u5.id}
        all_calc_units = db.query(Unit).filter(Unit.syllabus_id == calc_syl.id).all()
        rogue_unit_ids = [u.id for u in all_calc_units if u.id not in keep_unit_ids]

        # Concepts FK update for Calculus
        db.execute(text(f"UPDATE concepts SET unit_id = {u4.id} WHERE unit_id IN ({','.join(str(i) for i in rogue_unit_ids)}) AND (canonical_name LIKE '%Gamma%' OR canonical_name LIKE '%Beta%')"))
        db.execute(text(f"UPDATE concepts SET unit_id = NULL WHERE unit_id IN ({','.join(str(i) for i in rogue_unit_ids)})"))

        # Assessment coverages FK cleanup
        db.execute(text(f"DELETE FROM assessment_coverages WHERE unit_id IN ({','.join(str(i) for i in rogue_unit_ids)})"))

        # Identify rogue topics to delete (only Calculus rogue topics)
        # Note: Topics 20 and 21 belong to Chemistry Unit 1, so do NOT delete them!
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

        # Now delete rogue units
        for u in all_calc_units:
            if u.id in rogue_unit_ids:
                # delete any remaining attached topics
                for at in db.query(Topic).filter(Topic.unit_id == u.id).all():
                    db.execute(text(f"DELETE FROM question_topic WHERE topic_id = {at.id}"))
                    db.execute(text(f"DELETE FROM assessment_coverages WHERE topic_id = {at.id}"))
                    db.execute(text(f"DELETE FROM subtopics WHERE topic_id = {at.id}"))
                    db.execute(text(f"DELETE FROM student_topic_progress WHERE topic_id = {at.id}"))
                    db.delete(at)
                db.delete(u)
        db.flush()

        # Verify Calculus units
        final_calc_units = db.query(Unit).filter(Unit.syllabus_id == calc_syl.id).order_by(Unit.number).all()
        print(f"Calculus now has {len(final_calc_units)} units:")
        for u in final_calc_units:
            t_count = db.query(Topic).filter(Topic.unit_id == u.id).count()
            print(f"  Unit {u.number}: {u.name} (ID: {u.id}) - {t_count} topics")
        assert len(final_calc_units) == 5, f"Calculus must have 5 units, got {len(final_calc_units)}"

        # ======================================================================
        # 2. CHEMISTRY (Course 2)
        # ======================================================================
        print("\n--- Migrating Course 2 (Chemistry) ---")
        chem_syl = db.query(Syllabus).filter(Syllabus.course_id == 2).first()
        assert chem_syl is not None, "Chemistry syllabus not found"

        chem_units = {u.number: u for u in db.query(Unit).filter(Unit.syllabus_id == chem_syl.id).all()}

        # 5 Canonical Units
        u1_c = chem_units[1]
        u1_c.name = "Periodic Properties and Atomic Structure"
        u1_c.number = 1

        u2_c = chem_units[2]
        u2_c.name = "Chemical Equilibria and Electrochemistry"
        u2_c.number = 2

        u3_c = chem_units[3]
        u3_c.name = "Stereo Chemistry And Organic Reactions"
        u3_c.number = 3

        u4_c = chem_units[4]
        u4_c.name = "Polymers"
        u4_c.number = 4

        u5_c = chem_units[5]
        u5_c.name = "Advanced Engineering Materials"
        u5_c.number = 5

        # Reassign topics:
        u1_topic_ids = [20, 21, 22, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53]
        for tid in u1_topic_ids:
            t = db.query(Topic).filter(Topic.id == tid).first()
            if t: t.unit_id = u1_c.id

        u2_topic_ids = [23, 24, 25, 61, 62, 63, 64, 65, 66]
        for tid in u2_topic_ids:
            t = db.query(Topic).filter(Topic.id == tid).first()
            if t: t.unit_id = u2_c.id

        u3_topic_ids = [26, 27, 67, 68, 69, 70, 71, 72]
        for tid in u3_topic_ids:
            t = db.query(Topic).filter(Topic.id == tid).first()
            if t: t.unit_id = u3_c.id

        u4_topic_ids = [28, 29]
        for tid in u4_topic_ids:
            t = db.query(Topic).filter(Topic.id == tid).first()
            if t: t.unit_id = u4_c.id

        u5_topic_ids = [30, 31, 54, 55, 56, 57, 58, 59, 60]
        for tid in u5_topic_ids:
            t = db.query(Topic).filter(Topic.id == tid).first()
            if t: t.unit_id = u5_c.id

        db.flush()

        # Update concepts unit_id for Chemistry before deleting units 6..12
        chem_rogue_unit_ids = [chem_units[num].id for num in range(6, 13) if num in chem_units]
        if chem_rogue_unit_ids:
            # Units 6, 7, 8 (27, 28, 29) -> u1_c.id
            db.execute(text(f"UPDATE concepts SET unit_id = {u1_c.id} WHERE unit_id IN (27, 28, 29)"))
            # Units 11, 12 (32, 33) -> u2_c.id
            db.execute(text(f"UPDATE concepts SET unit_id = {u2_c.id} WHERE unit_id IN (32, 33)"))
            # Units 9, 10 (30, 31) -> u5_c.id
            db.execute(text(f"UPDATE concepts SET unit_id = {u5_c.id} WHERE unit_id IN (30, 31)"))
            
            # Clean up assessment_coverages pointing to rogue units
            db.execute(text(f"DELETE FROM assessment_coverages WHERE unit_id IN ({','.join(str(i) for i in chem_rogue_unit_ids)})"))
            db.flush()

        # Delete rogue units 6..12
        for num in range(6, 13):
            if num in chem_units:
                u = chem_units[num]
                remaining = db.query(Topic).filter(Topic.unit_id == u.id).count()
                assert remaining == 0, f"Unit {u.id} still has {remaining} topics!"
                db.delete(u)
        db.flush()

        # Verify Chemistry units
        final_chem_units = db.query(Unit).filter(Unit.syllabus_id == chem_syl.id).order_by(Unit.number).all()
        print(f"Chemistry now has {len(final_chem_units)} units:")
        for u in final_chem_units:
            t_count = db.query(Topic).filter(Topic.unit_id == u.id).count()
            print(f"  Unit {u.number}: {u.name} (ID: {u.id}) - {t_count} topics")
        assert len(final_chem_units) == 5, f"Chemistry must have 5 units, got {len(final_chem_units)}"

        # Verify total question mappings across Chemistry topics
        chem_topic_ids = u1_topic_ids + u2_topic_ids + u3_topic_ids + u4_topic_ids + u5_topic_ids
        total_chem_q = (
            db.query(Question.id)
            .join(question_topic, question_topic.c.question_id == Question.id)
            .filter(question_topic.c.topic_id.in_(chem_topic_ids))
            .count()
        )
        print(f"Total Chemistry question mappings preserved: {total_chem_q} (Expected: 192)")
        assert total_chem_q == 192, f"Expected 192 question mappings in Chemistry, got {total_chem_q}"

        # Clean up any obsolete assessment_coverages and components for Chemistry component (CT3)
        db.execute(text("DELETE FROM assessment_coverages WHERE assessment_component_id IN (SELECT id FROM assessment_components WHERE code = 'CT3' AND course_id = 2)"))
        db.execute(text("DELETE FROM assessment_components WHERE code = 'CT3' AND course_id = 2"))
        db.flush()

        # ======================================================================
        # 3. COURSE 19: Prune orphan Syllabus 24
        # ======================================================================
        print("\n--- Pruning Course 19 orphan Syllabus 24 ---")
        orphan_syl24 = db.query(Syllabus).filter(Syllabus.id == 24, Syllabus.course_id == 19).first()
        if orphan_syl24:
            u_count = db.query(Unit).filter(Unit.syllabus_id == 24).count()
            if u_count == 0:
                db.delete(orphan_syl24)
                db.flush()
                print("Deleted empty orphan Syllabus 24.")

        db.commit()
        print("\nMigration committed successfully!")

    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
