import json
from backend.core.database import SessionLocal
from backend.models.core import Syllabus, Unit, Topic

db = SessionLocal()
syl = db.query(Syllabus).filter(Syllabus.course_id == 2).first()
units = db.query(Unit).filter(Unit.syllabus_id == syl.id).order_by(Unit.number).all()

with open('backend/services/taxonomy_registry/definitions/course_02_chemistry.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Index all original topics
orig_topics = {}
for old_u in data.get('units', []):
    for old_t in old_u.get('topics', []):
        orig_topics[old_t.get('id')] = old_t
        orig_topics[old_t.get('name')] = old_t

new_units = []
for u in units:
    u_obj = {
        'id': u.id,
        'number': u.number,
        'name': u.name,
        'topics': []
    }
    topics = db.query(Topic).filter(Topic.unit_id == u.id).all()
    for t in topics:
        if t.id in orig_topics:
            t_data = orig_topics[t.id]
            t_data['name'] = t.name
            t_data['canonical_name'] = t.name
            u_obj['topics'].append(t_data)
        elif t.name in orig_topics:
            t_data = orig_topics[t.name]
            t_data['id'] = t.id
            u_obj['topics'].append(t_data)
        else:
            u_obj['topics'].append({
                'id': t.id,
                'name': t.name,
                'canonical_name': t.name,
                'aliases': [],
                'strong_phrases': [t.name.lower()],
                'specific_keywords': [w.lower() for w in t.name.split() if len(w) > 3],
                'negative_guards': [],
                'context_hints': ['chemistry']
            })
    new_units.append(u_obj)

data['units'] = new_units
data['taxonomy_version'] = '2.0.0'
with open('backend/services/taxonomy_registry/definitions/course_02_chemistry.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print('Updated course_02_chemistry.json with', len(new_units), 'units')
for u in new_units:
    num = u['number']
    nm = u['name']
    tc = len(u['topics'])
    print(f'  Unit {num}: {nm} ({tc} topics)')
db.close()
