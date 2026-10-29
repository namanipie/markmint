with open('src/app/question-bank/page.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add import
old_import = 'import { TopicQuestionsViewer } from "@/components/ui/topic-questions-viewer";'
new_import = '''import { TopicQuestionsViewer } from "@/components/ui/topic-questions-viewer";
import { CycleTestArchiveViewer } from "@/components/analytics/cycle-test-archive-viewer";'''
text = text.replace(old_import, new_import, 1)

# 2. Add state
old_state = '  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);'
new_state = '''  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"SYLLABUS" | "CYCLE_TESTS">("SYLLABUS");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const tab = params.get("tab") || params.get("view");
      if (tab === "cycle-tests" || tab === "cycle_tests" || params.get("cycle")) {
        setActiveTab("CYCLE_TESTS");
      }
    }
  }, []);'''
text = text.replace(old_state, new_state, 1)

# 3. Add tabs right below header description
old_header = '''          <p className="text-sm text-muted-foreground max-w-2xl">
            Select your semester and subject to drill down into unit-wise topics. MintAI will instantly organize and generate 1-mark MCQs, 4-mark, 8-mark, and 13-mark questions for any topic.
          </p>
        </div>'''

new_header = '''          <p className="text-sm text-muted-foreground max-w-2xl">
            Select your semester and subject to drill down into unit-wise topics, or explore 1,343 authentic Cycle Test questions with faculty answer keys.
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex flex-wrap items-center gap-2 border-b border-border/60 pb-3">
          <button
            type="button"
            onClick={() => setActiveTab("SYLLABUS")}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
              activeTab === "SYLLABUS"
                ? "bg-primary text-primary-foreground shadow-xs font-bold"
                : "bg-muted/40 hover:bg-muted text-muted-foreground hover:text-foreground"
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span>Syllabus Taxonomy &amp; Units</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("CYCLE_TESTS")}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer border ${
              activeTab === "CYCLE_TESTS"
                ? "bg-accent text-accent-foreground border-accent shadow-xs font-bold"
                : "bg-accent/10 hover:bg-accent/20 border-accent/25 text-accent"
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>⚡ Cycle Test Archive</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-accent/20 border border-accent/30 text-accent">
              1,343 Questions &amp; Keys
            </span>
          </button>
        </div>'''
text = text.replace(old_header, new_header, 1)

# 4. Wrap Search Radar and Grid in activeTab === "CYCLE_TESTS" ? <CycleTestArchiveViewer /> : (...)
old_content_start = '''        {/* Search Radar: Universal Question & Formula Search */}'''
new_content_start = '''        {activeTab === "CYCLE_TESTS" ? (
          <CycleTestArchiveViewer
            initialSubject={activeSubject?.name || "ALL"}
          />
        ) : (
          <>
        {/* Search Radar: Universal Question & Formula Search */}'''
text = text.replace(old_content_start, new_content_start, 1)

# Close fragment at end of main
old_main_end = '''          </div>
        </div>
      </main>'''
new_main_end = '''          </div>
        </div>
          </>
        )}
      </main>'''
text = text.replace(old_main_end, new_main_end, 1)

# 5. Add CT link in active subject header
old_sub_header = '''                {/* Subject Header */}
                <div className="p-5 rounded-xl border border-border bg-card shadow-sm flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <BookOpen className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-foreground">
                      {activeSubject.canonicalCode ? `[${activeSubject.canonicalCode}] ` : ""}{activeSubject.name}
                    </h2>
                    <p className="text-xs text-muted-foreground mt-1">
                      {activeSubject.units?.length || 0} Units • {activeSubject.questionCount || 0} Total Questions
                    </p>
                  </div>
                </div>'''

new_sub_header = '''                {/* Subject Header */}
                <div className="p-5 rounded-xl border border-border bg-card shadow-sm flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <BookOpen className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-foreground">
                        {activeSubject.canonicalCode ? `[${activeSubject.canonicalCode}] ` : ""}{activeSubject.name}
                      </h2>
                      <p className="text-xs text-muted-foreground mt-1">
                        {activeSubject.units?.length || 0} Units • {activeSubject.questionCount || 0} Total Questions
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => setActiveTab("CYCLE_TESTS")}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent/10 hover:bg-accent/20 text-accent font-semibold text-xs border border-accent/25 transition-all cursor-pointer"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>View Authentic CT Papers &amp; Solutions &rarr;</span>
                  </button>
                </div>'''
text = text.replace(old_sub_header, new_sub_header, 1)

with open('src/app/question-bank/page.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated question-bank/page.tsx successfully")
