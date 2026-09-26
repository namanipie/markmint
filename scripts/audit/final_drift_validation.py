import sqlite3
import time
from collections import defaultdict
from backend.core.database import SessionLocal
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.api.endpoints.analysis import _get_exams_as_dicts
from backend.models.core import Unit, Syllabus, Course

def run_audit():
    print("=" * 60)
    print("MINTAI HISTORICAL FOCUS EVOLUTION: FINAL END-TO-END AUDIT")
    print("=" * 60)

    # 1. Database Integrity
    conn = sqlite3.connect('production_corpus.db')
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM questions")
    total_q = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM exams")
    total_e = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM exams WHERE year IS NOT NULL")
    total_e_year = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM question_families")
    total_qf = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM topics")
    total_t = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM units")
    total_u = c.fetchone()[0]

    c.execute("SELECT question_type, COUNT(*) FROM questions GROUP BY question_type ORDER BY COUNT(*) DESC")
    qtypes = c.fetchall()

    print("\n--- 1. DATABASE INVARIANTS ---")
    print(f"Total Questions: {total_q} (Expected: 9013, Match: {total_q == 9013})")
    print(f"Total Exams: {total_e} (With year: {total_e_year})")
    print(f"Total Question Families: {total_qf} (Expected: 7450, Match: {total_qf == 7450})")
    print(f"Taxonomy: {total_u} Units, {total_t} Topics")
    print("Question Type Distribution:")
    for qt, cnt in qtypes:
        print(f"  {qt}: {cnt}")

    # Check question topic relationship table name
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in c.fetchall()]
    print(f"\nTables in DB: {tables}")

    conn.close()

    # 2. Canonical Course Validations
    db = SessionLocal()
    try:
        canonical_courses = [
            (1, "Calculus And Linear Algebra"),
            (2, "Chemistry"),
            (5, "Programming For Problem Solving"),
            (28, "Database Management Systems")
        ]

        print("\n--- 2. CANONICAL COURSE VALIDATIONS ---")
        for cid, cname in canonical_courses:
            exams = _get_exams_as_dicts(cid, db=db)
            syllabus_units = [
                {'id': u.id, 'name': u.name, 'number': u.number}
                for u in db.query(Unit).join(Syllabus).filter(Syllabus.course_id == cid).order_by(Unit.number).all()
            ]

            t0 = time.perf_counter()
            res = DNAAnalyzerService.analyze(exams, syllabus_units=syllabus_units)
            t_cold = (time.perf_counter() - t0) * 1000

            # Test duplicate exam inputs idempotence
            duplicate_exams = exams + exams
            res_dup = DNAAnalyzerService.analyze(duplicate_exams, syllabus_units=syllabus_units)

            # Test cutoffs
            exams_cutoff_2020 = _get_exams_as_dicts(cid, db=db, cutoff_year=2020)
            exams_cutoff_2023 = _get_exams_as_dicts(cid, db=db, cutoff_year=2023)
            exams_cutoff_2024 = _get_exams_as_dicts(cid, db=db, cutoff_year=2024)

            res_cutoff_2020 = DNAAnalyzerService.analyze(exams_cutoff_2020, syllabus_units=syllabus_units)
            res_cutoff_2023 = DNAAnalyzerService.analyze(exams_cutoff_2023, syllabus_units=syllabus_units)
            res_cutoff_2024 = DNAAnalyzerService.analyze(exams_cutoff_2024, syllabus_units=syllabus_units)

            # Test assessment cycle filtering if course 5
            res_endsem = None
            if cid == 5:
                exams_endsem = _get_exams_as_dicts(cid, db=db, assessment_cycle="ENDSEM")
                res_endsem = DNAAnalyzerService.analyze(exams_endsem, syllabus_units=syllabus_units)

            # Check year reconciliation
            years = sorted(list(set(r.year for r in res.temporal_unit_focus)))
            sparse_years = sorted(list(set(r.year for r in res.temporal_unit_focus if r.is_sparse)))

            q_reconciled = True
            m_reconciled = True
            for y in years:
                u_rows = [r for r in res.temporal_unit_focus if r.year == y]
                q_sum = round(sum(r.question_percentage for r in u_rows), 2)
                m_sum = round(sum(r.marks_weight_percentage for r in u_rows), 2)
                if abs(q_sum - 100.0) > 0.1 and q_sum > 0:
                    q_reconciled = False
                if abs(m_sum - 100.0) > 0.1 and m_sum > 0:
                    m_reconciled = False

            print(f"\nCourse: {cname} (ID: {cid})")
            print(f"  Exams: {len(exams)}, Temporal Years: {years}, Sparse Years: {sparse_years}")
            print(f"  Unit Focus Rows: {len(res.temporal_unit_focus)}, Topic Focus Rows: {len(res.temporal_topic_focus)}")
            print(f"  Topic Footprints: {len(res.topic_historical_footprints)}")
            print(f"  Questions % Reconciled: {q_reconciled} | Marks % Reconciled: {m_reconciled}")
            print(f"  Computation Latency: {t_cold:.2f} ms")

            # Cutoff validation check: no future leak
            for co, r_co in [(2020, res_cutoff_2020), (2023, res_cutoff_2023), (2024, res_cutoff_2024)]:
                co_years = set(r.year for r in r_co.temporal_unit_focus)
                leak = [y for y in co_years if y >= co]
                assert len(leak) == 0, f"Future leak in cutoff {co}: {leak}"
            print(f"  Cutoff Integrity (2020, 2023, 2024): Strict, 0% future leakage.")

            # Duplicate exam invariance check
            # Question and marks percentages should remain invariant
            dup_invariant = True
            if len(res.temporal_unit_focus) != len(res_dup.temporal_unit_focus):
                dup_invariant = False
            else:
                for r1, r2 in zip(res.temporal_unit_focus, res_dup.temporal_unit_focus):
                    if r1.question_percentage != r2.question_percentage or r1.marks_weight_percentage != r2.marks_weight_percentage:
                        dup_invariant = False
                        break
            print(f"  Duplicate Input Invariance: {dup_invariant}")

            if cid == 5 and res_endsem:
                endsem_years = sorted(list(set(r.year for r in res_endsem.temporal_unit_focus)))
                print(f"  PPS ENDSEM Filtered Years: {endsem_years} (Exams: {res_endsem.sample_size.papers})")

        # 3. Topic Mapping Quality Audit
        print("\n--- 3. TOPIC MAPPING QUALITY AUDIT ---")
        # Check unmapped questions across entire database
        c2 = sqlite3.connect('production_corpus.db').cursor()
        c2.execute('''
            SELECT c.name, COUNT(DISTINCT q.id) as unmapped_q
            FROM questions q
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            JOIN courses c ON e.course_id = c.id
            LEFT JOIN question_topic qt ON q.id = qt.question_id
            WHERE qt.topic_id IS NULL
            GROUP BY c.id ORDER BY unmapped_q DESC LIMIT 10
        ''')
        unmapped_by_course = c2.fetchall()
        print("Top 10 Courses by Unmapped Questions:")
        for cn, uq in unmapped_by_course:
            print(f"  {cn}: {uq} unmapped questions")

        # Check topics with single-year spikes
        c2.execute('''
            SELECT t.name, c.name, COUNT(DISTINCT e.year) as yrs, COUNT(q.id) as q_cnt
            FROM questions q
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            JOIN courses c ON e.course_id = c.id
            JOIN question_topic qt ON q.id = qt.question_id
            JOIN topics t ON qt.topic_id = t.id
            WHERE e.year IS NOT NULL
            GROUP BY t.id, c.id
            HAVING yrs = 1 AND q_cnt >= 10
            ORDER BY q_cnt DESC LIMIT 5
        ''')
        spikes = c2.fetchall()
        print("\nSuspicious Single-Year Spike Topics (>= 10 questions in 1 year only):")
        for tn, cn, yrs, q_cnt in spikes:
            print(f"  Topic '{tn}' ({cn}): {q_cnt} questions in {yrs} year only")

        c2.connection.close()

    finally:
        db.close()

if __name__ == '__main__':
    run_audit()
