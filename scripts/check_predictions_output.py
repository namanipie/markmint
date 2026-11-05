import sys, os
sys.path.insert(0, os.path.abspath('.'))
from backend.core.database import SessionLocal
from backend.api.endpoints.predictions import get_prediction

db = SessionLocal()
for cycle in ['CT1', 'CT2', 'ENDSEM']:
    res = get_prediction(subject='21MAB101T', assessment_cycle=cycle, db=db)
    print(f"\n=======================================================")
    print(f"=== CYCLE: {cycle} ===")
    print(f"=======================================================")
    print('assessment_cycle in res:', res.get('assessment_cycle'))
    print('evidence_status:', res.get('evidence_status'))
    print('observed_years:', res.get('observed_years'))
    preds = res.get('predictions', [])
    print(f'Total predictions: {len(preds)}')
    for p in preds[:5]:
        print(f"  [{p.get('confidence')}] {p.get('name')} | Score: {p.get('score')} | Rank: {p.get('rank')} | Target: {p.get('target')}")
db.close()
