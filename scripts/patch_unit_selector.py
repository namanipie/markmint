with open('src/components/analytics/exam-unit-selector.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add counters
t1 = 'const courseResources = useMemo(() => course ? getCourseResources(course.slug) : null, [course]);'
r1 = """const courseResources = useMemo(() => course ? getCourseResources(course.slug) : null, [course]);
  const ct1PapersCount = useMemo(() => 
    courseResources?.pyqs.filter(p => p.examType === 'CT1').length || 0,
    [courseResources]
  );
  const ct2PapersCount = useMemo(() => 
    courseResources?.pyqs.filter(p => p.examType === 'CT2').length || 0,
    [courseResources]
  );
  const totalCtPapersCount = useMemo(() => 
    courseResources?.pyqs.filter(p => ['CT1', 'CT2', 'CT3', 'CT', 'MODEL'].includes(p.examType)).length || 0,
    [courseResources]
  );"""

assert t1 in content, "t1 not found"
content = content.replace(t1, r1, 1)

# 2. Add CT badge to CT1
t_ct1 = "CT1 (Units 1 &amp; 2)"
r_ct1 = """CT1 (Units 1 &amp; 2)
          {ct1PapersCount > 0 && (
            <span className="ml-1.5 px-1.5 py-0.2 rounded-md text-[10px] bg-accent/20 border border-accent/30 font-mono font-bold">
              {ct1PapersCount}
            </span>
          )}"""
assert t_ct1 in content, "t_ct1 not found"
content = content.replace(t_ct1, r_ct1, 1)

# 3. Add CT badge to CT2
t_ct2 = "CT2 (Units 3 &amp; 4)"
r_ct2 = """CT2 (Units 3 &amp; 4)
          {ct2PapersCount > 0 && (
            <span className="ml-1.5 px-1.5 py-0.2 rounded-md text-[10px] bg-accent/20 border border-accent/30 font-mono font-bold">
              {ct2PapersCount}
            </span>
          )}"""
assert t_ct2 in content, "t_ct2 not found"
content = content.replace(t_ct2, r_ct2, 1)

# 4. Dynamic CT link
t_pill = "<span>{courseResources.pyqsCount} Verified PYQs &amp; Slides Available &rarr;</span>"
r_pill = """<span>
              {isCT1Preset && ct1PapersCount > 0
                ? `${ct1PapersCount} Verified CT1 Papers & Keys Available →`
                : isCT2Preset && ct2PapersCount > 0
                ? `${ct2PapersCount} Verified CT2 Papers & Keys Available →`
                : totalCtPapersCount > 0
                ? `${totalCtPapersCount} Cycle Test Papers & Keys Available →`
                : `${courseResources.pyqsCount} Verified PYQs & Slides Available →`}
            </span>"""
assert t_pill in content, "t_pill not found"
content = content.replace(t_pill, r_pill, 1)

with open('src/components/analytics/exam-unit-selector.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("exam-unit-selector.tsx successfully patched!")
