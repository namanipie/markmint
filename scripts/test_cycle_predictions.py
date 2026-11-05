import sys, os
sys.path.insert(0, os.path.abspath('.'))
from backend.core.database import SessionLocal
from backend.api.endpoints.predictions import get_prediction

db = SessionLocal()

print("=== TESTING PREDICTIONS FOR 21MAB101T ACROSS CYCLES ===")

for cycle in ['CT1', 'CT2', 'ENDSEM']:
    try:
        res = get_prediction(subject='21MAB101T', assessment_cycle=cycle, db=db)
        print(f"\n--- Assessment Cycle: {cycle} ---")
        meta = res.get('metadata', {})
        print(f"  Target Year: {meta.get('target_year')}")
        print(f"  Assessment Cycle: {meta.get('assessment_cycle')}")
        print(f"  Papers Analyzed: {meta.get('papers_analyzed')}")
        print(f"  Total Historical Questions: {meta.get('total_historical_questions')}")
        
        # Check topic predictions
        topic_preds = res.get('topic_predictions', [])
        print(f"  Total Topic Predictions: {len(topic_preds)}")
        for tp in topic_preds[:4]:
            print(f"    - [{tp.get('confidence')}] {tp.get('name')} (Score: {tp.get('prediction_score')}) | Evidence: {tp.get('evidence_count')} | Reason: {tp.get('reason_codes')}")
            
        # Check unit priorities
        unit_priorities = res.get('unit_priorities', [])
        print(f"  Unit Priorities: {len(unit_priorities)}")
        for up in unit_priorities:
            print(f"    - {up.get('unit_name')}: {up.get('predicted_marks')} marks | Priority: {up.get('priority')}")
            
    except Exception as e:
        print(f"Error for cycle {cycle}: {e}")

db.close()
