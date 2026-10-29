import re

def run():
    path = "src/app/question-bank/page.tsx"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add isSidebarOpenMobile state
    if "isSidebarOpenMobile" not in content:
        content = content.replace(
            'const [activeTab, setActiveTab] = useState<"SYLLABUS" | "CYCLE_TESTS">("SYLLABUS");',
            'const [activeTab, setActiveTab] = useState<"SYLLABUS" | "CYCLE_TESTS">("SYLLABUS");\n  const [isSidebarOpenMobile, setIsSidebarOpenMobile] = useState<boolean>(false);'
        )

    # 2. Update handleSubjectClick to close mobile selector
    content = content.replace(
        """  const handleSubjectClick = (id: number | string) => {
    setSelectedSubjectId(id);
    setExpandedUnit(null);
    setExpandedTopic(null);
  };""",
        """  const handleSubjectClick = (id: number | string) => {
    setSelectedSubjectId(id);
    setExpandedUnit(null);
    setExpandedTopic(null);
    setIsSidebarOpenMobile(false);
  };"""
    )

    # 3. Update View Switcher Tabs to be responsive
    old_tabs = """        {/* View Switcher Tabs */}
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
              5,536 Questions &amp; Keys
            </span>
          </button>
        </div>"""

    new_tabs = """        {/* View Switcher Tabs */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 border-b border-border/60 pb-3">
          <button
            type="button"
            onClick={() => setActiveTab("SYLLABUS")}
            className={`flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer touch-manipulation ${
              activeTab === "SYLLABUS"
                ? "bg-primary text-primary-foreground shadow-xs font-bold"
                : "bg-muted/40 hover:bg-muted text-muted-foreground hover:text-foreground"
            }`}
          >
            <BookOpen className="w-4 h-4 shrink-0" />
            <span>Syllabus Taxonomy &amp; Units</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("CYCLE_TESTS")}
            className={`flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer border touch-manipulation ${
              activeTab === "CYCLE_TESTS"
                ? "bg-accent text-accent-foreground border-accent shadow-xs font-bold"
                : "bg-accent/10 hover:bg-accent/20 border-accent/25 text-accent"
            }`}
          >
            <Sparkles className="w-4 h-4 shrink-0" />
            <span>⚡ Cycle Test Archive</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-accent/20 border border-accent/30 text-accent">
              5,536 Questions &amp; Keys
            </span>
          </button>
        </div>"""

    content = content.replace(old_tabs, new_tabs)

    # 4. Add mobile accordion banner and wrap sidebar
    old_sidebar = """        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 items-start">
          
          {/* Left Sidebar: Selectors */}
          <div className="lg:col-span-1 space-y-6 sticky top-24">"""

    new_sidebar = """        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 lg:gap-8 items-start">
          
          {/* Mobile Accordion Toggle for Selectors */}
          <div className="lg:hidden col-span-1 p-3.5 rounded-xl border border-border/70 bg-card shadow-2xs space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] uppercase font-bold text-muted-foreground block">Curriculum Filter:</span>
                <span className="text-xs font-bold text-foreground">
                  {selectedBranch.split(" ")[0]} • Sem {selectedSemester} • {activeSubject?.name || "Choose Subject"}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setIsSidebarOpenMobile(!isSidebarOpenMobile)}
                className="px-3 py-1.5 rounded-lg bg-accent/15 border border-accent/25 text-accent text-xs font-bold hover:bg-accent/25 transition-all cursor-pointer touch-manipulation"
              >
                {isSidebarOpenMobile ? "Hide Selectors" : "Change Subject"}
              </button>
            </div>
          </div>

          {/* Left Sidebar: Selectors */}
          <div className={`lg:col-span-1 space-y-6 sticky top-24 ${isSidebarOpenMobile ? 'block' : 'hidden lg:block'}`}>"""

    content = content.replace(old_sidebar, new_sidebar)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Updated src/app/question-bank/page.tsx successfully!")

if __name__ == "__main__":
    run()
