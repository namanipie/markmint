import json

def summarize():
    with open('scratch_full_audit.json', encoding='utf-8') as f:
        rows = json.load(f)

    resolved = [r for r in rows if r['resolution_status'].startswith('RESOLVED')]
    print(f"Total resolved: {len(resolved)} / {len(rows)} ({len(resolved)/len(rows)*100:.1f}%)")
    
    for r in resolved:
        eid = r['exam_id']
        crs = r['course']
        cy = r['candidate_year']
        cat = str(r['candidate_atype'])
        ev_src = r['evidence_source']
        ev_snp = r['evidence_snippet']
        print(f"Exam {eid:3d} | {crs[:35]:35s} | Year: {cy} | Type: {cat:6s} | {ev_src}: '{ev_snp}'")

if __name__ == '__main__':
    summarize()
