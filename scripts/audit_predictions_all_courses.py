import sys, os
sys.path.insert(0, os.path.abspath('.'))
from backend.core.database import SessionLocal
from backend.models.core import Course
from backend.api.endpoints.predictions import get_prediction

db = SessionLocal()
courses = db.query(Course).order_by(Course.id).all()
print(f"Total courses: {len(courses)}")

results = []
for c in courses:
    c_res = {'id': c.id, 'code': c.code, 'name': c.name}
    for cycle in ['CT1', 'CT2', 'ENDSEM']:
        try:
            # Handle foreign languages track if needed
            lang = 'german' if 'FORE' in c.code else None
            p = get_prediction(subject=c.code, assessment_cycle=cycle, language=lang, db=db)
            preds = p.get('predictions', [])
            c_res[cycle] = {
                'status': 'OK',
                'papers': p.get('evidence_breakdown', {}).get('total_papers_analyzed') or len(p.get('observed_years', [])),
                'preds_count': len(preds),
                'evidence_status': p.get('evidence_status')
            }
        except Exception as e:
            c_res[cycle] = {'status': 'ERROR', 'error': str(e)[:40]}
    results.append(c_res)

db.close()

print(f"\n--- Coverage Across All 43 Courses ---")
for r in results[:15]:
    ct1 = r['CT1']
    ct2 = r['CT2']
    es = r['ENDSEM']
    print(f"{r['code']:12s} | CT1: {ct1.get('preds_count', 0)} preds ({ct1.get('evidence_status', ct1.get('status'))}) | CT2: {ct2.get('preds_count', 0)} preds ({ct2.get('evidence_status', ct2.get('status'))}) | EndSem: {es.get('preds_count', 0)} preds ({es.get('evidence_status', es.get('status'))})")
