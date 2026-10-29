with open('src/components/analytics/exam-unit-selector.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add import
imp = 'import { CycleTestQuestionsDrawer } from "./cycle-test-questions-drawer";\n'
content = imp + content

# 2. Add CycleTestQuestionsDrawer right above Modal Dialog
target = '      {/* Modal Dialog */}'
replacement = '''      {/* Authentic Cycle Test Questions Drawer */}
      {course?.name && (
        <CycleTestQuestionsDrawer
          courseName={course.name}
          cycle={isCT1Preset ? "CT1" : isCT2Preset ? "CT2" : "ALL"}
          isOpenDefault={isCT1Preset || isCT2Preset}
        />
      )}

      {/* Modal Dialog */}'''

assert target in content, "target not found"
content = content.replace(target, replacement, 1)

with open('src/components/analytics/exam-unit-selector.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("exam-unit-selector.tsx successfully updated with CycleTestQuestionsDrawer!")
