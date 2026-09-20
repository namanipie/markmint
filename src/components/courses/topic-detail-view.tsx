import Link from "next/link";
import { TopicCatalogItem } from "@/lib/topics";
import { 
  ChevronRight, 
  Sparkles, 
  BookOpen, 
  FileText, 
  HelpCircle, 
  Layers, 
  TrendingUp, 
  CalendarCheck, 
  ArrowRight,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  ListOrdered
} from "lucide-react";

interface TopicDetailViewProps {
  topic: TopicCatalogItem;
  siblingTopics?: TopicCatalogItem[];
}

export function TopicDetailView({ topic, siblingTopics = [] }: TopicDetailViewProps) {
  const marksKeys = Object.keys(topic.marksDistribution).sort((a, b) => Number(a) - Number(b));

  return (
    <div className="w-full space-y-12">
      {/* Breadcrumbs */}
      <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <Link href="/" className="hover:text-foreground transition-colors">
          Home
        </Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link href="/courses" className="hover:text-foreground transition-colors">
          Courses
        </Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link 
          href={topic.isLanguageTrack ? `/courses/foreign-languages?track=${topic.languageKey}` : `/courses/${topic.courseSlug}`}
          className="hover:text-foreground transition-colors max-w-[180px] sm:max-w-none truncate"
        >
          {topic.courseName}
        </Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-muted-foreground">
          Unit {topic.unitNumber}
        </span>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-foreground font-medium truncate max-w-[220px] sm:max-w-none">
          {topic.name}
        </span>
      </nav>

      {/* Hero Header */}
      <section className="space-y-5 pb-8 border-b border-border/40">
        <div className="flex flex-wrap items-center gap-2.5 text-xs text-muted-foreground font-mono">
          <span className="px-2.5 py-1 rounded-md bg-accent/10 text-accent font-semibold tracking-wide">
            Unit {topic.unitNumber}: {topic.unitName}
          </span>
          <span className="px-2.5 py-1 rounded-md bg-secondary text-secondary-foreground font-semibold">
            {topic.canonicalCode || topic.courseCode}
          </span>
          {topic.isLanguageTrack && (
            <span className="px-2.5 py-1 rounded-md bg-accent/5 border border-accent/20 text-accent">
              {topic.languageName} Track Isolated
            </span>
          )}
        </div>

        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-8">
          <div className="max-w-3xl space-y-3">
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-foreground leading-[1.15]">
              {topic.name}
            </h1>
            <p className="text-base text-muted-foreground leading-relaxed">
              {topic.description}
            </p>
          </div>

          {/* Action CTAs */}
          <div className="flex flex-col sm:flex-row lg:flex-col gap-3 shrink-0">
            <Link
              href={topic.practiceUrl}
              className="flex items-center justify-center gap-2 px-6 py-3.5 bg-foreground text-background text-sm font-medium rounded-xl hover:bg-foreground/90 transition-all active:scale-[0.98] shadow-sm"
            >
              <HelpCircle className="w-4 h-4 text-accent" />
              Practice Topic Questions
            </Link>
            <Link
              href={topic.mintAiUrl}
              className="flex items-center justify-center gap-2 px-6 py-3.5 bg-secondary hover:bg-secondary/80 text-foreground text-sm font-medium rounded-xl border border-border/60 transition-all"
            >
              <Sparkles className="w-4 h-4 text-accent" />
              Open Course Intelligence
            </Link>
          </div>
        </div>
      </section>

      {/* Corpus Historical Evidence Bar */}
      <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-card border border-border/60 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            <HelpCircle className="w-4 h-4 text-accent" />
            <span>Appearances</span>
          </div>
          <div className="text-3xl font-bold text-foreground">{topic.appearanceCount}</div>
          <div className="text-xs text-muted-foreground mt-1">Cataloged Exam Questions</div>
        </div>

        <div className="p-5 rounded-2xl bg-card border border-border/60 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            <FileText className="w-4 h-4 text-accent" />
            <span>Exam Papers</span>
          </div>
          <div className="text-3xl font-bold text-foreground">{topic.paperCount}</div>
          <div className="text-xs text-muted-foreground mt-1">Distinct University Exams</div>
        </div>

        <div className="p-5 rounded-2xl bg-card border border-border/60 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            <TrendingUp className="w-4 h-4 text-accent" />
            <span>Question Families</span>
          </div>
          <div className="text-3xl font-bold text-foreground">{topic.questionFamilies.length}</div>
          <div className="text-xs text-muted-foreground mt-1">Recurring Conceptual Archetypes</div>
        </div>

        <div className="p-5 rounded-2xl bg-card border border-border/60 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            <ShieldCheck className="w-4 h-4 text-accent" />
            <span>SRMIST Status</span>
          </div>
          <div className="text-3xl font-bold text-accent">Active</div>
          <div className="text-xs text-muted-foreground mt-1">Regulation 2021 Syllabus</div>
        </div>
      </section>

      {/* Assessment Appearances & Marks Breakdown */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Assessment Cycles Breakdown */}
        <div className="p-6 rounded-2xl bg-card border border-border/60 space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <CalendarCheck className="w-4 h-4 text-accent" />
            <span>Assessment Cycle Weightage</span>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Historical appearance distribution across SRMIST Formative Tests (CT1, CT2) and University End Semester examinations.
          </p>

          <div className="grid grid-cols-3 gap-3 pt-2">
            <div className="p-3.5 rounded-xl bg-secondary/30 border border-border/40 text-center">
              <div className="text-xs text-muted-foreground font-mono">CT1</div>
              <div className="text-xl font-bold text-foreground mt-1">
                {topic.assessmentAppearances.CT1}
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">Cycle Test 1</div>
            </div>

            <div className="p-3.5 rounded-xl bg-secondary/30 border border-border/40 text-center">
              <div className="text-xs text-muted-foreground font-mono">CT2</div>
              <div className="text-xl font-bold text-foreground mt-1">
                {topic.assessmentAppearances.CT2}
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">Cycle Test 2</div>
            </div>

            <div className="p-3.5 rounded-xl bg-secondary/30 border border-border/40 text-center">
              <div className="text-xs text-muted-foreground font-mono">EndSem</div>
              <div className="text-xl font-bold text-accent mt-1">
                {topic.assessmentAppearances.EndSem}
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">Semester Exam</div>
            </div>
          </div>
        </div>

        {/* Reliable Marks Distribution */}
        <div className="p-6 rounded-2xl bg-card border border-border/60 space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <ListOrdered className="w-4 h-4 text-accent" />
            <span>Marks Weightage Distribution</span>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Factual marks weightage of questions asked on this topic in historical examinations.
          </p>

          {marksKeys.length > 0 ? (
            <div className="flex flex-wrap gap-2 pt-2">
              {marksKeys.map((mk) => (
                <div
                  key={mk}
                  className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-secondary/40 border border-border/50 text-xs"
                >
                  <span className="font-bold text-foreground">{mk} Marks:</span>
                  <span className="px-1.5 py-0.5 rounded bg-accent/10 text-accent font-mono font-semibold">
                    {topic.marksDistribution[mk]} questions
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-muted-foreground py-4">
              Marks details are recorded on individual past question papers.
            </div>
          )}
        </div>
      </section>

      {/* Recurring Question Families (if present) */}
      {topic.questionFamilies && topic.questionFamilies.length > 0 && (
        <section className="space-y-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-lg font-bold text-foreground">
              <TrendingUp className="w-5 h-5 text-accent" />
              <span>Recurring Question Families ({topic.questionFamilies.length})</span>
            </div>
            <p className="text-xs text-muted-foreground">
              Question templates that recur across multiple examination cycles with similar conceptual stems.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {topic.questionFamilies.map((fam) => (
              <div
                key={fam.id}
                className="p-5 rounded-2xl bg-card border border-border/60 space-y-3"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="px-2 py-0.5 rounded bg-secondary text-[11px] font-mono text-muted-foreground capitalize">
                    {fam.repetitionType.replace("_", " ")}
                  </span>
                  <span className="text-xs font-semibold text-accent font-mono">
                    {fam.count} paper {fam.count === 1 ? "appearance" : "appearances"}
                  </span>
                </div>
                <p className="text-xs text-foreground font-medium leading-relaxed line-clamp-3">
                  &ldquo;{fam.name}&rdquo;
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Sample Historical Questions */}
      {topic.sampleQuestions && topic.sampleQuestions.length > 0 && (
        <section className="space-y-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-lg font-bold text-foreground">
              <BookOpen className="w-5 h-5 text-accent" />
              <span>Sample Past Exam Questions</span>
            </div>
            <p className="text-xs text-muted-foreground">
              Representative historical questions extracted directly from SRMIST examination papers.
            </p>
          </div>

          <div className="space-y-3">
            {topic.sampleQuestions.map((sq, idx) => (
              <div
                key={idx}
                className="p-5 rounded-2xl bg-card border border-border/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="space-y-2 max-w-3xl">
                  <p className="text-xs text-foreground font-mono leading-relaxed">
                    {sq.text}
                  </p>
                  <div className="flex items-center gap-2 text-[11px] text-muted-foreground font-mono">
                    <span>Year: {sq.year}</span>
                    <span>&bull;</span>
                    <span>Assessment: {sq.assessmentType}</span>
                  </div>
                </div>

                {sq.marks > 0 && (
                  <div className="shrink-0 self-start sm:self-center">
                    <span className="px-3 py-1.5 rounded-lg bg-secondary text-foreground text-xs font-bold font-mono">
                      {sq.marks} Marks
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Historical Exam Papers List */}
      {topic.papers && topic.papers.length > 0 && (
        <section className="space-y-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-lg font-bold text-foreground">
              <FileText className="w-5 h-5 text-accent" />
              <span>Historical Papers Indexed ({topic.papers.length})</span>
            </div>
            <p className="text-xs text-muted-foreground">
              Examinations where questions for {topic.name} have appeared.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {topic.papers.map((p) => (
              <div
                key={p.id}
                className="p-4 rounded-xl bg-card border border-border/60 flex flex-col justify-between gap-2"
              >
                <div className="font-semibold text-foreground text-xs line-clamp-2">
                  {p.title}
                </div>
                <div className="flex items-center justify-between text-[11px] text-muted-foreground font-mono pt-2 border-t border-border/30">
                  <span>{p.year}</span>
                  <span className="px-1.5 py-0.5 rounded bg-secondary text-[10px]">
                    {p.assessmentType}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Sibling Topics in Same Unit */}
      {siblingTopics && siblingTopics.length > 1 && (
        <section className="p-6 sm:p-8 rounded-2xl bg-secondary/20 border border-border/60 space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <Layers className="w-4 h-4 text-accent" />
            <span>Other Exam Topics in Unit {topic.unitNumber}: {topic.unitName}</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {siblingTopics
              .filter((st) => st.slug !== topic.slug)
              .map((st) => (
                <Link
                  key={st.slug}
                  href={st.isLanguageTrack ? `/courses/foreign-languages/${st.languageKey}/topics/${st.slug}` : `/courses/${st.courseSlug}/topics/${st.slug}`}
                  className="p-3.5 rounded-xl bg-card hover:bg-secondary/40 border border-border/50 hover:border-accent/40 transition-all text-xs flex items-center justify-between group"
                >
                  <span className="font-medium text-foreground group-hover:text-accent transition-colors line-clamp-1">
                    {st.name}
                  </span>
                  <span className="text-[10px] text-muted-foreground shrink-0 ml-2">
                    {st.appearanceCount} Qs
                  </span>
                </Link>
              ))}
          </div>
        </section>
      )}

      {/* Bottom CTA Card */}
      <section className="p-8 sm:p-10 rounded-2xl bg-foreground text-background flex flex-col md:flex-row items-center justify-between gap-6 shadow-md">
        <div className="space-y-2 max-w-xl text-center md:text-left">
          <h3 className="text-2xl font-bold tracking-tight">
            Master {topic.name} in MintAI
          </h3>
          <p className="text-sm text-background/80 leading-relaxed">
            Practice past exam questions, test recurring archetypes, and view predictive probability for this topic before your upcoming exam.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 shrink-0">
          <Link
            href={topic.practiceUrl}
            className="px-6 py-3.5 bg-background text-foreground font-medium rounded-xl hover:bg-background/90 transition-all flex items-center justify-center gap-2 text-sm"
          >
            Practice Topic
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href={topic.mintAiUrl}
            className="px-6 py-3.5 bg-foreground border border-background/30 text-background font-medium rounded-xl hover:bg-background/10 transition-all flex items-center justify-center gap-2 text-sm"
          >
            Course Forecast
          </Link>
        </div>
      </section>
    </div>
  );
}
