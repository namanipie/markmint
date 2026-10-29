import os
import re

for root, dirs, files in os.walk('src'):
    for f in files:
        if f.endswith(('.ts', '.tsx')):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as file:
                content = file.read()
                matches = re.findall(r'from\s+[\'"]([^\'"]+\.json)[\'"]', content)
                if matches:
                    print(f'{p}: {matches}')
