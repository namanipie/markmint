with open('src/components/courses/course-resources-section.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update selectedUnit state
text = text.replace(
    'const [selectedUnit, setSelectedUnit] = useState<number | "ALL">("ALL");',
    'const [selectedUnit, setSelectedUnit] = useState<number | "ALL" | "CT1" | "CT2">("ALL");'
)

# 2. Update filteredNotes calculation and add counts
old_filtered = '''  // Filtered Notes
  const filteredNotes = useMemo(() => {
    if (!resources.notes) return [];
    if (selectedUnit === "ALL") return resources.notes;
    return resources.notes.filter((n) => n.unit === selectedUnit);
  }, [resources.notes, selectedUnit]);'''

new_filtered = '''  // Filtered Notes
  const filteredNotes = useMemo(() => {
    if (!resources.notes) return [];
    if (selectedUnit === "ALL") return resources.notes;
    if (selectedUnit === "CT1") return resources.notes.filter((n) => n.unit === 1 || n.unit === 2);
    if (selectedUnit === "CT2") return resources.notes.filter((n) => n.unit === 3 || n.unit === 4);
    return resources.notes.filter((n) => n.unit === selectedUnit);
  }, [resources.notes, selectedUnit]);

  // Counts by portion
  const ct1NotesCount = resources.notes ? resources.notes.filter((n) => n.unit === 1 || n.unit === 2).length : 0;
  const ct2NotesCount = resources.notes ? resources.notes.filter((n) => n.unit === 3 || n.unit === 4).length : 0;'''

text = text.replace(old_filtered, new_filtered, 1)

# 3. Update Unit Filters UI in TAB 2
old_filters_ui = '''            <button
              type="button"
              onClick={() => setSelectedUnit("ALL")}
              className={`px-3 py-1 rounded-lg border transition-all cursor-pointer ${
                selectedUnit === "ALL"
                  ? "bg-secondary text-secondary-foreground border-border font-bold shadow-2xs"
                  : "bg-muted/10 border-border/40 text-muted-foreground hover:text-foreground"
              }`}
            >
              All Units ({resources.notesCount})
            </button>'''

new_filters_ui = '''            <button
              type="button"
              onClick={() => setSelectedUnit("ALL")}
              className={`px-3 py-1 rounded-lg border transition-all cursor-pointer ${
                selectedUnit === "ALL"
                  ? "bg-secondary text-secondary-foreground border-border font-bold shadow-2xs"
                  : "bg-muted/10 border-border/40 text-muted-foreground hover:text-foreground"
              }`}
            >
              All Units ({resources.notesCount})
            </button>

            {/* Quick Portion Presets */}
            {ct1NotesCount > 0 && (
              <button
                type="button"
                onClick={() => setSelectedUnit("CT1")}
                className={`px-3 py-1 rounded-lg border transition-all cursor-pointer flex items-center gap-1.5 ${
                  selectedUnit === "CT1"
                    ? "bg-accent text-accent-foreground border-accent font-bold shadow-2xs"
                    : "bg-accent/10 border-accent/25 text-accent hover:bg-accent/20"
                }`}
              >
                <Sparkles className="w-3 h-3" />
                <span>CT1 (Units 1 &amp; 2)</span>
                <span className="text-[10px] opacity-80">({ct1NotesCount})</span>
              </button>
            )}

            {ct2NotesCount > 0 && (
              <button
                type="button"
                onClick={() => setSelectedUnit("CT2")}
                className={`px-3 py-1 rounded-lg border transition-all cursor-pointer flex items-center gap-1.5 ${
                  selectedUnit === "CT2"
                    ? "bg-accent text-accent-foreground border-accent font-bold shadow-2xs"
                    : "bg-accent/10 border-accent/25 text-accent hover:bg-accent/20"
                }`}
              >
                <Sparkles className="w-3 h-3" />
                <span>CT2 (Units 3 &amp; 4)</span>
                <span className="text-[10px] opacity-80">({ct2NotesCount})</span>
              </button>
            )}'''

text = text.replace(old_filters_ui, new_filters_ui, 1)

with open('src/components/courses/course-resources-section.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated course-resources-section.tsx successfully!")
