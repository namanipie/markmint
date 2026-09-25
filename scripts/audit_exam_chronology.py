import sqlite3
from collections import defaultdict, Counter

def run_audit():
    conn = sqlite3.connect('production_corpus.db')
    c = conn.cursor()

    # 1. Total exams
    c.execute('SELECT COUNT(*) FROM exams')
    total_exams = c.fetchone()[0]

    # 2. Exams with year vs without year
    c.execute('SELECT COUNT(*) FROM exams WHERE year IS NOT NULL')
    exams_with_year = c.fetchone()[0]
    exams_without_year = total_exams - exams_with_year

    # 3. Exams with assessment_type vs without
    c.execute('SELECT COUNT(*) FROM exams WHERE assessment_type IS NOT NULL AND length(trim(assessment_type)) > 0')
    exams_with_assessment_type = c.fetchone()[0]
    exams_without_assessment_type = total_exams - exams_with_assessment_type

    # 4. Exams with term vs without
    c.execute('SELECT COUNT(*) FROM exams WHERE term IS NOT NULL AND length(trim(term)) > 0')
    exams_with_term = c.fetchone()[0]
    exams_without_term = total_exams - exams_with_term

    # 5. Course semester metadata
    c.execute('''
        SELECT e.id, e.course_id, c.name, e.year, e.assessment_type, e.document_id
        FROM exams e
        JOIN courses c ON e.course_id = c.id
    ''')
    all_exam_rows = c.fetchall()

    print(f"Total exams: {total_exams}")
    print(f"Exams with year: {exams_with_year} ({round(exams_with_year/total_exams*100, 1)}%)")
    print(f"Exams without year: {exams_without_year} ({round(exams_without_year/total_exams*100, 1)}%)")
    print(f"Exams with assessment_type: {exams_with_assessment_type} ({round(exams_with_assessment_type/total_exams*100, 1)}%)")
    print(f"Exams without assessment_type: {exams_without_assessment_type} ({round(exams_without_assessment_type/total_exams*100, 1)}%)")
    print(f"Exams with term: {exams_with_term} ({round(exams_with_term/total_exams*100, 1)}%)")

    # Assessment type distribution for missing-year exams
    c.execute('''
        SELECT coalesce(assessment_type, 'NULL/UNSPECIFIED'), count(*)
        FROM exams
        WHERE year IS NULL
        GROUP BY 1
        ORDER BY 2 DESC
    ''')
    atype_dist = c.fetchall()
    print("\n--- Assessment types among missing-year exams ---")
    for atype, cnt in atype_dist:
        print(f"  {atype:<25}: {cnt}")

    # Course missing counts
    course_missing_counts = defaultdict(lambda: {'total': 0, 'missing': 0, 'with_year': 0})
    for eid, cid, cname, yr, atype, did in all_exam_rows:
        course_missing_counts[cname]['total'] += 1
        if yr is None:
            course_missing_counts[cname]['missing'] += 1
        else:
            course_missing_counts[cname]['with_year'] += 1

    print("\n--- Distribution of missing-year exams by course ---")
    missing_courses = [k for k, v in course_missing_counts.items() if v['missing'] > 0]
    print(f"Total courses with missing years: {len(missing_courses)}")
    for cname, stats in sorted(course_missing_counts.items(), key=lambda x: x[1]['missing'], reverse=True):
        if stats['missing'] > 0:
            pct = round(stats['missing'] / stats['total'] * 100, 1)
            print(f"  {cname:<45}: {stats['missing']:>2}/{stats['total']:>2} missing ({pct:>5}%) [Has year: {stats['with_year']:>2}]")

    # Documents linked to missing-year exams
    c.execute('''
        SELECT e.id, e.course_id, c.name, e.assessment_type, e.document_id,
               d.title, d.original_url, d.source, d.semester, d.year, d.exam_type
        FROM exams e
        JOIN courses c ON e.course_id = c.id
        LEFT JOIN documents d ON e.document_id = d.id
        WHERE e.year IS NULL
        ORDER BY e.course_id, e.id
    ''')
    missing_exam_docs = c.fetchall()
    print(f"\nTotal missing-year exams inspected: {len(missing_exam_docs)}")
    print(f"Exams with document_id: {sum(1 for r in missing_exam_docs if r[4] is not None)}")

    conn.close()

if __name__ == '__main__':
    run_audit()
