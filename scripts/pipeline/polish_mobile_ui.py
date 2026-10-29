# Polish mobile UI across all 4 components

# 1. Polish cycle-test-questions-drawer.tsx
path_drawer = 'src/components/analytics/cycle-test-questions-drawer.tsx'
with open(path_drawer, 'r', encoding='utf-8') as f:
    c = f.read()

# Replace header badge
old_hdr = '''            <div className="flex items-center gap-2">
              <h4 className="text-xs sm:text-sm font-bold text-foreground">
                Authentic {cycle === "ALL" ? "Cycle Test" : cycle} Questions &amp; Testing System
              </h4>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-accent/20 border border-accent/30 text-accent">
                {descriptiveQuestions.length} Normal • {mcqQuestions.length} Interactive MCQs
              </span>
            </div>'''

new_hdr = '''            <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
              <h4 className="text-xs sm:text-sm font-bold text-foreground leading-tight">
                Authentic {cycle === "ALL" ? "Cycle Test" : cycle} Questions &amp; Testing System
              </h4>
              <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-accent/20 border border-accent/30 text-accent w-fit shrink-0">
                {descriptiveQuestions.length} Normal • {mcqQuestions.length} Interactive MCQs
              </span>
            </div>'''

c = c.replace(old_hdr, new_hdr, 1)

# Category switcher
old_tabs = '''          {/* Main Section Mode Tabs: Normal vs MCQ */}
          <div className="flex items-center gap-2 p-1 rounded-xl bg-muted/30 border border-border/60">
            <button
              type="button"
              onClick={() => {
                setActiveCategory("descriptive");
                setSelectedType("ALL");
              }}
              className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeCategory === "descriptive"
                  ? "bg-background text-foreground shadow-xs border border-border/70"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <FileText className="w-3.5 h-3.5 text-accent" />
              <span>Normal Questions ({descriptiveQuestions.length})</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveCategory("mcq");
                setSelectedType("ALL");
              }}
              className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeCategory === "mcq"
                  ? "bg-background text-foreground shadow-xs border border-border/70 text-purple-400"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <CheckSquare className="w-3.5 h-3.5 text-purple-400" />
              <span>Interactive MCQ Test ({mcqQuestions.length})</span>
            </button>
          </div>'''

new_tabs = '''          {/* Main Section Mode Tabs: Normal vs MCQ */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-1.5 sm:gap-2 p-1 rounded-xl bg-muted/30 border border-border/60">
            <button
              type="button"
              onClick={() => {
                setActiveCategory("descriptive");
                setSelectedType("ALL");
              }}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer touch-manipulation ${
                activeCategory === "descriptive"
                  ? "bg-background text-foreground shadow-xs border border-border/70 text-accent font-bold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <FileText className="w-3.5 h-3.5 text-accent shrink-0" />
              <span>Normal Questions ({descriptiveQuestions.length})</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveCategory("mcq");
                setSelectedType("ALL");
              }}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer touch-manipulation ${
                activeCategory === "mcq"
                  ? "bg-background text-foreground shadow-xs border border-border/70 text-purple-400 font-bold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <CheckSquare className="w-3.5 h-3.5 text-purple-400 shrink-0" />
              <span>Interactive MCQ Test ({mcqQuestions.length})</span>
            </button>
          </div>'''

c = c.replace(old_tabs, new_tabs, 1)

# Pills scrollable
old_pills = '''                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <span className="text-[11px] font-semibold text-muted-foreground mr-1">Section:</span>
                  {descriptiveTypes.map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setSelectedType(t)}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all cursor-pointer ${
                        selectedType === t
                          ? "bg-accent text-accent-foreground font-semibold shadow-2xs"
                          : "bg-muted/40 hover:bg-muted text-muted-foreground"
                      }`}
                    >
                      {t === "ALL" ? `All (${descriptiveQuestions.length})` : `${t} (${descriptiveQuestions.filter((q) => q.q_type === t).length})`}
                    </button>
                  ))}
                </div>'''

new_pills = '''                <div className="flex items-center gap-1.5 pt-1 overflow-x-auto no-scrollbar pb-1">
                  <span className="text-[11px] font-semibold text-muted-foreground mr-1 shrink-0">Section:</span>
                  {descriptiveTypes.map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setSelectedType(t)}
                      className={`px-3 py-1.5 rounded-lg text-[11px] font-medium transition-all cursor-pointer whitespace-nowrap shrink-0 touch-manipulation ${
                        selectedType === t
                          ? "bg-accent text-accent-foreground font-semibold shadow-2xs"
                          : "bg-muted/40 hover:bg-muted text-muted-foreground"
                      }`}
                    >
                      {t === "ALL" ? `All (${descriptiveQuestions.length})` : `${t} (${descriptiveQuestions.filter((q) => q.q_type === t).length})`}
                    </button>
                  ))}
                </div>'''

c = c.replace(old_pills, new_pills, 1)

with open(path_drawer, 'w', encoding='utf-8') as f:
    f.write(c)
print('Updated cycle-test-questions-drawer.tsx')


# 2. Polish mcq-testing-suite.tsx
path_suite = 'src/components/practice/mcq-testing-suite.tsx'
with open(path_suite, 'r', encoding='utf-8') as f:
    s = f.read()

# Replace Quiz Question Navigation Strip to be horizontally scrollable
old_strip = '''              {/* Question Navigation Strip */}
              <div className="flex flex-wrap items-center gap-1.5 p-3 rounded-xl bg-muted/30 border border-border/50">
                {mcqList.map((_, i) => {
                  const isAnswered = !!quizAnswers[i];
                  const isActive = currentQuizIndex === i;

                  return (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setCurrentQuizIndex(i)}
                      className={`w-7 h-7 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer flex items-center justify-center ${
                        isActive
                          ? "bg-purple-600 text-white ring-2 ring-purple-400/50 shadow-xs"
                          : isAnswered
                          ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                          : "bg-muted text-muted-foreground hover:bg-muted/80"
                      }`}
                    >
                      {i + 1}
                    </button>
                  );
                })}
              </div>'''

new_strip = '''              {/* Question Navigation Strip (Touch-friendly & horizontally scrollable on mobile) */}
              <div className="p-2.5 rounded-xl bg-muted/30 border border-border/50">
                <div className="flex items-center justify-between text-[11px] text-muted-foreground pb-1.5 px-0.5">
                  <span className="font-semibold">Question Navigator:</span>
                  <span>Swipe to jump to question</span>
                </div>
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-thin">
                  {mcqList.map((_, i) => {
                    const isAnswered = !!quizAnswers[i];
                    const isActive = currentQuizIndex === i;

                    return (
                      <button
                        key={i}
                        type="button"
                        onClick={() => setCurrentQuizIndex(i)}
                        className={`w-8 h-8 rounded-lg text-xs font-mono font-bold shrink-0 transition-all cursor-pointer touch-manipulation flex items-center justify-center ${
                          isActive
                            ? "bg-purple-600 text-white ring-2 ring-purple-400/50 shadow-xs"
                            : isAnswered
                            ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                            : "bg-muted/70 text-muted-foreground hover:bg-muted"
                        }`}
                      >
                        {i + 1}
                      </button>
                    );
                  })}
                </div>
              </div>'''

s = s.replace(old_strip, new_strip, 1)

# Mode Selector Tabs on Suite Header
old_header_tabs = '''        {/* Mode Selector Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-background/80 border border-border/70 shadow-2xs">
          <button
            type="button"
            onClick={() => setTestMode("PRACTICE")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              testMode === "PRACTICE"
                ? "bg-purple-600 text-white shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Practice Mode</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setTestMode("QUIZ");
              if (!quizStarted) startQuiz();
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              testMode === "QUIZ"
                ? "bg-purple-600 text-white shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Award className="w-3.5 h-3.5" />
            <span>Timed Quiz Mode</span>
          </button>
        </div>'''

new_header_tabs = '''        {/* Mode Selector Tabs */}
        <div className="w-full sm:w-auto flex items-center gap-1.5 p-1 rounded-xl bg-background/80 border border-border/70 shadow-2xs">
          <button
            type="button"
            onClick={() => setTestMode("PRACTICE")}
            className={`flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer touch-manipulation ${
              testMode === "PRACTICE"
                ? "bg-purple-600 text-white shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <BookOpen className="w-3.5 h-3.5 shrink-0" />
            <span>Practice Mode</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setTestMode("QUIZ");
              if (!quizStarted) startQuiz();
            }}
            className={`flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer touch-manipulation ${
              testMode === "QUIZ"
                ? "bg-purple-600 text-white shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Award className="w-3.5 h-3.5 shrink-0" />
            <span>Timed Quiz Mode</span>
          </button>
        </div>'''

s = s.replace(old_header_tabs, new_header_tabs, 1)

# Options touch-manipulation & min-height
s = s.replace(
    'className={`w-full flex items-start gap-2.5 p-3 rounded-xl border text-left transition-all cursor-pointer ${btnStyle}`}',
    'className={`w-full min-h-[44px] flex items-start gap-2.5 p-3 sm:p-3.5 rounded-xl border text-left transition-all cursor-pointer touch-manipulation ${btnStyle}`}'
)

with open(path_suite, 'w', encoding='utf-8') as f:
    f.write(s)
print('Updated mcq-testing-suite.tsx')


# 3. Polish cycle-test-archive-viewer.tsx
path_archive = 'src/components/analytics/cycle-test-archive-viewer.tsx'
with open(path_archive, 'r', encoding='utf-8') as f:
    a = f.read()

# Hero Header Badge
old_arc_badge = '''              <div className="flex items-center gap-2">
                <h2 className="text-lg sm:text-xl font-bold tracking-tight text-foreground">
                  Authentic Cycle Test Question Archive
                </h2>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-accent/20 border border-accent/30 text-accent">
                  5,536 Verified Questions Across All 43 Subjects
                </span>
              </div>'''

new_arc_badge = '''              <div className="flex flex-col sm:flex-row sm:items-center gap-1.5 sm:gap-2">
                <h2 className="text-lg sm:text-xl font-bold tracking-tight text-foreground leading-tight">
                  Authentic Cycle Test Question Archive
                </h2>
                <span className="px-2.5 py-0.5 rounded-md text-[11px] sm:text-xs font-mono font-bold bg-accent/20 border border-accent/30 text-accent w-fit shrink-0">
                  5,536 Verified Questions Across All 43 Subjects
                </span>
              </div>'''

a = a.replace(old_arc_badge, new_arc_badge, 1)

# Category Switcher
old_arc_cat = '''        {/* Section Category Switcher: Normal vs MCQs */}
        <div className="pt-2">
          <div className="flex flex-wrap items-center gap-2 p-1 rounded-xl bg-muted/40 border border-border/60 max-w-xl">
            <button
              type="button"
              onClick={() => {
                setActiveCategory("all");
                setSelectedType("ALL");
              }}
              className={`flex items-center gap-2 py-2 px-3.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeCategory === "all"
                  ? "bg-background text-foreground shadow-xs border border-border/70"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-accent" />
              <span>All Questions ({questions.length})</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveCategory("descriptive");
                setSelectedType("ALL");
              }}
              className={`flex items-center gap-2 py-2 px-3.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeCategory === "descriptive"
                  ? "bg-background text-foreground shadow-xs border border-border/70 text-accent font-bold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <FileText className="w-3.5 h-3.5 text-accent" />
              <span>Normal Questions ({descriptiveCount})</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveCategory("mcq");
                setSelectedType("ALL");
              }}
              className={`flex items-center gap-2 py-2 px-3.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeCategory === "mcq"
                  ? "bg-background text-foreground shadow-xs border border-border/70 text-purple-400 font-bold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <CheckSquare className="w-3.5 h-3.5 text-purple-400" />
              <span>MCQ Testing System ({mcqCount})</span>
            </button>
          </div>
        </div>'''

new_arc_cat = '''        {/* Section Category Switcher: Normal vs MCQs */}
        <div className="pt-2">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-1.5 sm:gap-2 p-1 rounded-xl bg-muted/40 border border-border/60 max-w-xl">
            <button
              type="button"
              onClick={() => {
                setActiveCategory("all");
                setSelectedType("ALL");
              }}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer touch-manipulation ${
                activeCategory === "all"
                  ? "bg-background text-foreground shadow-xs border border-border/70 font-bold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-accent shrink-0" />
              <span>All ({questions.length})</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveCategory("descriptive");
                setSelectedType("ALL");
              }}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer touch-manipulation ${
                activeCategory === "descriptive"
                  ? "bg-background text-foreground shadow-xs border border-border/70 text-accent font-bold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <FileText className="w-3.5 h-3.5 text-accent shrink-0" />
              <span>Normal Questions ({descriptiveCount})</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setActiveCategory("mcq");
                setSelectedType("ALL");
              }}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs font-semibold transition-all cursor-pointer touch-manipulation ${
                activeCategory === "mcq"
                  ? "bg-background text-foreground shadow-xs border border-border/70 text-purple-400 font-bold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <CheckSquare className="w-3.5 h-3.5 text-purple-400 shrink-0" />
              <span>MCQ Test ({mcqCount})</span>
            </button>
          </div>
        </div>'''

a = a.replace(old_arc_cat, new_arc_cat, 1)

# Cycle filter buttons: horizontally scrollable
old_cyc_tabs = '''            <div className="flex flex-wrap items-center gap-1.5">
              {[
                { id: "ALL", label: "All Cycles" },
                { id: "CT1", label: "CT1 (Units 1 & 2)" },
                { id: "CT2", label: "CT2 (Units 3 & 4)" },
                { id: "CT3", label: "CT3 / Model" },
              ].map((cyc) => ('''

new_cyc_tabs = '''            <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-1">
              {[
                { id: "ALL", label: "All Cycles" },
                { id: "CT1", label: "CT1 (Units 1 & 2)" },
                { id: "CT2", label: "CT2 (Units 3 & 4)" },
                { id: "CT3", label: "CT3 / Model" },
              ].map((cyc) => ('''

a = a.replace(old_cyc_tabs, new_cyc_tabs, 1)

with open(path_archive, 'w', encoding='utf-8') as f:
    f.write(a)
print('Updated cycle-test-archive-viewer.tsx')
