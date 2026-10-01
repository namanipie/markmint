"use client";

import { useState, useEffect } from "react";
import { 
  ShieldCheck, Lock, ArrowRight, Leaf, Users, Search, 
  FileText, CheckCircle2, XCircle, BarChart3, Radio, 
  Settings, Wand2, AlertTriangle, ChevronRight
} from "lucide-react";
import { toast } from "sonner";
import { listPaperSubmissions, approvePaperSubmission, rejectPaperSubmission } from "@/lib/api";
import { PaperSubmissionRecord } from "@/lib/types";

export default function ModsPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState("");
  const [isAnimating, setIsAnimating] = useState(false);
  const [activeTab, setActiveTab] = useState("queue");

  // Moderation Queue State
  const [queue, setQueue] = useState<PaperSubmissionRecord[]>([]);
  const [isLoadingQueue, setIsLoadingQueue] = useState(false);

  useEffect(() => {
    if (isAuthenticated && activeTab === "queue") {
      fetchQueue();
    }
  }, [isAuthenticated, activeTab]);

  const fetchQueue = async () => {
    setIsLoadingQueue(true);
    try {
      const data = await listPaperSubmissions("PENDING");
      setQueue(data || []);
    } catch (err) {
      toast.error("Failed to fetch moderation queue from server.");
    } finally {
      setIsLoadingQueue(false);
    }
  };

  const handleApprove = async (id: number) => {
    toast.loading("Approving and injecting into MintAI...", { id: `approve-${id}` });
    try {
      await approvePaperSubmission(id);
      toast.success("Successfully injected paper into MintAI Engine!", { id: `approve-${id}` });
      setQueue(queue.filter(p => p.id !== id));
    } catch (err) {
      toast.error("Failed to approve paper.", { id: `approve-${id}` });
    }
  };

  const handleReject = async (id: number) => {
    try {
      await rejectPaperSubmission(id, "Rejected by moderator.");
      toast.success("Paper rejected and deleted.");
      setQueue(queue.filter(p => p.id !== id));
    } catch (err) {
      toast.error("Failed to reject paper.");
    }
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (password === "markmint_godmode") {
      setIsAnimating(true);
      setTimeout(() => {
        setIsAuthenticated(true);
        toast.success("Welcome back, Mod.");
      }, 600);
    } else {
      toast.error("Access Denied. Incorrect passphrase.");
      setPassword("");
    }
  };

  if (isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex flex-col md:flex-row">
        {/* Sidebar */}
        <aside className="w-full md:w-64 border-r border-border/40 bg-card/30 flex flex-col">
          <div className="p-6 border-b border-border/40 flex items-center gap-3">
            <div className="p-2 bg-accent/10 rounded-lg">
              <ShieldCheck className="w-6 h-6 text-accent" />
            </div>
            <div>
              <h2 className="font-bold text-foreground leading-tight">Mod Console</h2>
              <p className="text-[10px] text-muted-foreground font-mono">ACCESS_LEVEL_0</p>
            </div>
          </div>
          
          <nav className="p-4 space-y-1.5 flex-1">
            <button 
              onClick={() => setActiveTab("queue")}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-all ${activeTab === "queue" ? "bg-accent text-accent-foreground font-semibold" : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"}`}
            >
              <FileText className="w-4 h-4" /> Moderation Queue
            </button>
            <button 
              onClick={() => setActiveTab("radar")}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-all ${activeTab === "radar" ? "bg-accent text-accent-foreground font-semibold" : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"}`}
            >
              <Search className="w-4 h-4" /> Search Radar
            </button>
            <button 
              onClick={() => setActiveTab("godmode")}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-all ${activeTab === "godmode" ? "bg-accent text-accent-foreground font-semibold" : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"}`}
            >
              <Wand2 className="w-4 h-4" /> MintAI God Mode
            </button>
            <button 
              onClick={() => setActiveTab("broadcast")}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-all ${activeTab === "broadcast" ? "bg-accent text-accent-foreground font-semibold" : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"}`}
            >
              <Radio className="w-4 h-4" /> Global Broadcast
            </button>
          </nav>

          <div className="p-4 border-t border-border/40">
            <button 
              onClick={() => setIsAuthenticated(false)}
              className="w-full flex items-center justify-center gap-2 py-2 text-xs text-muted-foreground hover:text-red-400 transition-colors"
            >
              <Lock className="w-3 h-3" /> Lock Console
            </button>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 p-6 md:p-10 overflow-y-auto">
          
          {activeTab === "queue" && (
            <div className="space-y-6 max-w-4xl">
              <div>
                <h1 className="text-2xl font-bold text-foreground">Moderation Queue</h1>
                <p className="text-muted-foreground text-sm mt-1">Review and approve crowdsourced papers from students to feed MintAI.</p>
              </div>
              
              <div className="grid gap-4">
                {isLoadingQueue ? (
                  <div className="p-12 border border-dashed border-border/40 rounded-xl flex items-center justify-center">
                    <div className="flex flex-col items-center gap-2">
                      <div className="w-6 h-6 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
                      <p className="text-sm text-muted-foreground">Fetching live submissions...</p>
                    </div>
                  </div>
                ) : queue.length === 0 ? (
                  <div className="p-12 border border-dashed border-border/40 rounded-xl flex flex-col items-center justify-center text-center bg-card/10">
                    <CheckCircle2 className="w-10 h-10 text-emerald-500/50 mb-3" />
                    <p className="text-foreground font-semibold">Inbox Zero!</p>
                    <p className="text-sm text-muted-foreground">There are no pending paper submissions.</p>
                  </div>
                ) : (
                  queue.map((paper) => (
                    <div key={paper.id} className="p-4 rounded-xl border border-border/40 bg-card flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all hover:border-accent/30">
                      <div className="flex items-start gap-4">
                        <div className="p-3 bg-blue-500/10 rounded-lg text-blue-400">
                          <FileText className="w-6 h-6" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-foreground">
                            {paper.subject_name} {paper.declared_assessment ? `- ${paper.declared_assessment}` : ""}
                          </h3>
                          <p className="text-xs text-muted-foreground mt-0.5">
                            File: {paper.original_filename} • {paper.page_count} Pages
                          </p>
                          <div className="flex gap-2 mt-2">
                            <span className="px-2 py-0.5 rounded text-[10px] bg-secondary text-secondary-foreground font-mono">ID: {paper.id}</span>
                            <span className={`px-2 py-0.5 rounded text-[10px] ${paper.consistency_score > 0.8 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-500'}`}>
                              Match Confidence: {Math.round(paper.consistency_score * 100)}%
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button 
                          onClick={() => handleReject(paper.id)}
                          className="px-3 py-1.5 rounded-md bg-secondary hover:bg-red-500/20 hover:text-red-400 text-xs transition-colors flex items-center gap-1"
                        >
                          <XCircle className="w-3.5 h-3.5" /> Reject
                        </button>
                        <button 
                          onClick={() => handleApprove(paper.id)}
                          className="px-3 py-1.5 rounded-md bg-accent text-accent-foreground text-xs font-semibold transition-colors flex items-center gap-1 hover:brightness-110"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" /> Approve & Inject
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === "radar" && (
            <div className="space-y-6 max-w-4xl">
              <div>
                <h1 className="text-2xl font-bold text-foreground">Search Radar & Analytics</h1>
                <p className="text-muted-foreground text-sm mt-1">Live overview of student searches and MintAI blind spots.</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                <div className="p-5 rounded-xl border border-border/40 bg-card">
                  <p className="text-xs text-muted-foreground mb-1 uppercase tracking-wider">Active Users (24h)</p>
                  <p className="text-3xl font-bold text-foreground">1,402</p>
                  <p className="text-[10px] text-emerald-400 mt-2">+12% from yesterday</p>
                </div>
                <div className="p-5 rounded-xl border border-border/40 bg-card">
                  <p className="text-xs text-muted-foreground mb-1 uppercase tracking-wider">MintAI Queries</p>
                  <p className="text-3xl font-bold text-foreground">8,933</p>
                  <p className="text-[10px] text-emerald-400 mt-2">Engine is healthy</p>
                </div>
                <div className="p-5 rounded-xl border border-red-500/20 bg-red-500/5">
                  <p className="text-xs text-red-400 mb-1 uppercase tracking-wider">Failed Queries</p>
                  <p className="text-3xl font-bold text-red-400">124</p>
                  <p className="text-[10px] text-muted-foreground mt-2">Due to insufficient data</p>
                </div>
              </div>

              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-amber-500" /> Missing Data Priorities</h2>
              <div className="bg-card border border-border/40 rounded-xl overflow-hidden">
                <table className="w-full text-sm text-left">
                  <thead className="bg-secondary/50 text-xs uppercase text-muted-foreground">
                    <tr>
                      <th className="px-6 py-3 font-medium">Subject Searched</th>
                      <th className="px-6 py-3 font-medium">Assessment</th>
                      <th className="px-6 py-3 font-medium text-right">Failed Searches</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40">
                    <tr className="hover:bg-secondary/20">
                      <td className="px-6 py-4 text-foreground font-medium">Machine Learning (18CSC305J)</td>
                      <td className="px-6 py-4 text-muted-foreground">CT2</td>
                      <td className="px-6 py-4 text-right font-bold text-amber-500">89</td>
                    </tr>
                    <tr className="hover:bg-secondary/20">
                      <td className="px-6 py-4 text-foreground font-medium">Compiler Design</td>
                      <td className="px-6 py-4 text-muted-foreground">EndSem</td>
                      <td className="px-6 py-4 text-right font-bold text-amber-500">34</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === "godmode" && (
            <div className="space-y-6 max-w-4xl">
              <div>
                <h1 className="text-2xl font-bold text-foreground text-amber-500 flex items-center gap-2">
                  <Wand2 className="w-6 h-6" /> MintAI God Mode
                </h1>
                <p className="text-muted-foreground text-sm mt-1">Force-override the algorithm. Add "Professor Hints" to guarantee specific topics appear in student study plans.</p>
              </div>
              <div className="p-12 border border-dashed border-border/60 rounded-xl bg-card/20 flex flex-col items-center justify-center text-center">
                <Settings className="w-8 h-8 text-muted-foreground mb-4 opacity-50" />
                <p className="text-muted-foreground">We will connect the backend API to this panel so you can select a course and explicitly boost the weightage of any syllabus topic instantly.</p>
              </div>
            </div>
          )}

          {activeTab === "broadcast" && (
            <div className="space-y-6 max-w-4xl">
              <div>
                <h1 className="text-2xl font-bold text-foreground">Global Broadcast</h1>
                <p className="text-muted-foreground text-sm mt-1">Send a push notification banner to every student currently on MarkMint.</p>
              </div>
              <div className="p-6 border border-border/40 rounded-xl bg-card space-y-4">
                <div>
                  <label className="text-xs font-semibold uppercase text-muted-foreground">Announcement Message</label>
                  <textarea 
                    className="w-full mt-2 bg-background border border-border/50 rounded-lg p-3 text-sm focus:outline-none focus:border-accent"
                    rows={3}
                    placeholder="e.g., Servers are down for maintenance tonight at 12 AM."
                  />
                </div>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2 text-sm text-foreground">
                    <input type="radio" name="type" className="text-accent" defaultChecked /> Info Banner
                  </label>
                  <label className="flex items-center gap-2 text-sm text-foreground">
                    <input type="radio" name="type" className="text-amber-500" /> Warning Banner
                  </label>
                </div>
                <button className="px-6 py-2 bg-foreground text-background font-semibold rounded-lg hover:bg-foreground/90 transition-colors flex items-center gap-2">
                  <Radio className="w-4 h-4" /> Go Live
                </button>
              </div>
            </div>
          )}

        </main>
      </div>
    );
  }

  // --- LOGIN SCREEN BELOW ---
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-accent/5 rounded-full blur-[100px] pointer-events-none" />
      
      <div className={`w-full max-w-md bg-card/50 backdrop-blur-xl border border-border/50 rounded-2xl p-8 shadow-2xl relative z-10 transition-all duration-500 ${isAnimating ? "scale-95 opacity-0" : "scale-100 opacity-100"}`}>
        <div className="flex flex-col items-center text-center mb-8">
          <div className="w-12 h-12 bg-accent/10 rounded-full flex items-center justify-center mb-4 border border-accent/20">
            <ShieldCheck className="w-6 h-6 text-accent" />
          </div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Restricted Area</h1>
          <p className="text-sm text-muted-foreground mt-2">
            MarkMint Moderator Access Only.
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className="h-4 w-4 text-muted-foreground" />
            </div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="block w-full pl-10 pr-3 py-3 border border-border/50 rounded-xl bg-background/50 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent transition-all sm:text-sm"
              placeholder="Enter mod passphrase..."
              required
            />
          </div>
          
          <button
            type="submit"
            className="w-full flex items-center justify-center gap-2 bg-foreground text-background font-semibold py-3 px-4 rounded-xl hover:bg-foreground/90 hover:scale-[0.98] transition-all active:scale-95"
          >
            Authenticate <ArrowRight className="w-4 h-4" />
          </button>
        </form>
      </div>

      <div className="mt-8 flex items-center gap-2 text-muted-foreground opacity-50 text-xs font-mono">
        <Leaf className="w-3 h-3" />
        <span>MARK_MINT_SECURE_AUTH</span>
      </div>
    </div>
  );
}
