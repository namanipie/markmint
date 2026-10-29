with open('src/components/analytics/exam-unit-selector.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'const isCustomPreset = !isAllSelected && !isCT1Preset && !isCT2Preset;'
replacement = '''const isCustomPreset = !isAllSelected && !isCT1Preset && !isCT2Preset;

  const inScopeNotes = useMemo(() => {
    if (!courseResources?.notes) return [];
    if (isAllSelected) return courseResources.notes;
    return courseResources.notes.filter(
      (n) => n.unit == null || selectedUnits.includes(n.unit)
    );
  }, [courseResources?.notes, isAllSelected, selectedUnits]);'''

if target in text:
    text = text.replace(target, replacement, 1)
    with open('src/components/analytics/exam-unit-selector.tsx', 'w', encoding='utf-8') as f:
        f.write(text)
    print("SUCCESS: inScopeNotes added to exam-unit-selector.tsx")
else:
    print("FAILED: target not found")
