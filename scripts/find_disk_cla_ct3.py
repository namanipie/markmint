import os, re

matches = []

for root_dir in ['corpus', 'data']:
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            name_upper = f.upper()
            path_upper = root.upper()
            
            # Check for CT3, CT4, CLA, FT, Formative, Internal, Compilation
            patterns = ['CT3', 'CT-3', 'CT 3', 'CT4', 'CT-4', 'CT 4', 'CLA', 'FT1', 'FT2', 'FT3', 'FT4', 'FT-I', 'FT-II', 'FT-IV', 'FT IV', 'INTERNAL', 'FORMATIVE']
            for pat in patterns:
                if re.search(r'\b' + re.escape(pat) + r'\b', name_upper) or pat in name_upper:
                    matches.append((pat, os.path.join(root, f)))
                    break

print(f"Total matching files found on disk: {len(matches)}")
print("\nSample matching files on disk:")
for pat, path in matches[:35]:
    print(f"[{pat:8s}] {path}")
