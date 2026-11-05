import os
import glob
from collections import Counter, defaultdict

corpus_files = []
for root, dirs, files in os.walk('corpus'):
    for f in files:
        if f.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
            corpus_files.append(os.path.join(root, f))

data_files = []
for root, dirs, files in os.walk('data'):
    for f in files:
        if f.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png', '.json')):
            if 'extractions' in root or 'priority_pyqs' in root or 'cycle_tests' in root or 'more_cycle_tests' in root:
                data_files.append(os.path.join(root, f))

print(f"Total Corpus media/PDF files: {len(corpus_files)}")
print(f"Total Data paper/extraction files: {len(data_files)}")

# Break down corpus files by category (PYQ, STUDY_MATERIAL, SYLLABUS, etc.)
corpus_cat = Counter()
for p in corpus_files:
    parts = p.split(os.sep)
    if len(parts) >= 4:
        corpus_cat[parts[3]] += 1
    else:
        corpus_cat['other'] += 1

print("\nCorpus files by category folder:")
for k, v in corpus_cat.most_common():
    print(f"  {k}: {v}")
