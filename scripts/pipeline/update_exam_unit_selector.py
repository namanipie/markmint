with open('src/components/analytics/exam-unit-selector.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add import
old_imp = 'import { CycleTestQuestionsDrawer } from "./cycle-test-questions-drawer";'
new_imp = '''import { CycleTestQuestionsDrawer } from "./cycle-test-questions-drawer";
import { PortionNotesDrawer } from "./portion-notes-drawer";'''
text = text.replace(old_imp, new_imp, 1)

# 2. Add inScopeNotes computation
old_anchor = '  const totalCtPapersCount = ct1PapersCount + ct2Count;'
new_anchor = '''  const totalCtPapersCount = ct1PapersCount + ct2Count;

  // In-scope professor slides & notes
  const inScopeNotes = useMemo(() => {
    if (!courseResources?.notes) return [];
    if (isAllSelected) return courseResources.notes;
    return courseResources.notes.filter(
      (n) => n.unit == null || selectedUnits.includes(n.unit)
    );
  }, [courseResources?.notes, isAllSelected, selectedUnits]);'''
text = text.replace(old_anchor, new_anchor, 1)

# 3. Add PortionNotesDrawer right under CycleTestQuestionsDrawer
old_drawer = '''      {/* Authentic Cycle Test Questions Drawer */}
      {course?.name && (
        <CycleTestQuestionsDrawer
          courseName={course.name}
          cycle={isCT1Preset ? "CT1" : isCT2Preset ? "CT2" : "ALL"}
          isOpenDefault={isCT1Preset || isCT2Preset}
        />
      )}'''

new_drawer = '''      {/* Authentic Cycle Test Questions Drawer */}
      {course?.name && (
        <CycleTestQuestionsDrawer
          courseName={course.name}
          cycle={isCT1Preset ? "CT1" : isCT2Preset ? "CT2" : "ALL"}
          isOpenDefault={isCT1Preset || isCT2Preset}
        />
      )}

      {/* In-Scope Professor Slides & Notes Drawer */}
      {course?.name && inScopeNotes.length > 0 && (
        <PortionNotesDrawer
          notes={inScopeNotes}
          courseName={course.name}
          selectedUnits={selectedUnits}
          isCT1={isCT1Preset}
          isCT2={isCT2Preset}
          courseSlug={course.slug}
          isOpenDefault={false}
        />
      )}'''
text = text.replace(old_drawer, new_drawer, 1)

with open('src/components/analytics/exam-unit-selector.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated exam-unit-selector.tsx successfully!")
