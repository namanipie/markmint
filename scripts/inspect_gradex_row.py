import csv

with open('data/gradex_subdeck_resources.csv', 'r', encoding='utf-8', errors='ignore') as f:
    raw_lines = [l.strip()[1:-1] if l.strip().startswith('"') and l.strip().endswith('"') else l.strip() for l in f.readlines()]

reader = csv.reader(raw_lines)
header = next(reader)
for row in reader:
    if len(row) > 3 and ('Calculus' in row[1] or 'Chemistry' in row[1]):
        print(f"=== {row[0]} | {row[1]} ===")
        print("PPTs count chars:", len(row[2]))
        print("PYQs count chars:", len(row[3]))
        print("PYQs preview:", row[3][:400])
        print()
