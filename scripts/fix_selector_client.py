with open('src/components/analytics/exam-unit-selector.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Filter out any existing 'use client' lines
filtered = [l for l in lines if '"use client"' not in l and "'use client'" not in l]

# Prepend "use client"; at line 1
new_content = '"use client";\n' + "".join(filtered)

with open('src/components/analytics/exam-unit-selector.tsx', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Placed 'use client'; at line 1 successfully.")
