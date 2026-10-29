path = 'src/app/question-bank/page.tsx'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

target = '<span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-accent/20 border border-accent/30 text-accent">\n              5,536 Questions &amp; Keys\n            </span>'
replacement = '<span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold border ${activeTab === "CYCLE_TESTS" ? "bg-black/25 text-white border-white/20" : "bg-accent/20 border-accent/30 text-accent"}`}>\n              5,536 Questions &amp; Keys\n            </span>'

if target in c:
    c = c.replace(target, replacement)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print("Successfully updated badge styling!")
else:
    print("Target not found, checking with alternate whitespace...")
    import re
    c = re.sub(
        r'<span className="px-2 py-0\.5 rounded-full text-\[10px\] font-mono font-bold bg-accent/20 border border-accent/30 text-accent">\s*5,536 Questions &amp; Keys\s*</span>',
        r'<span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold border ${activeTab === "CYCLE_TESTS" ? "bg-black/25 text-white border-white/20" : "bg-accent/20 border-accent/30 text-accent"}`}>\n              5,536 Questions &amp; Keys\n            </span>',
        c
    )
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print("Replaced with regex!")
