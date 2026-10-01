"use client";

import { useState } from "react";
import { ShieldCheck, Lock, ArrowRight, Leaf } from "lucide-react";
import { toast } from "sonner";

export default function ModsPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState("");
  const [isAnimating, setIsAnimating] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Simple hardcoded password for now. You can change this later!
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
      <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6">
        <ShieldCheck className="w-16 h-16 text-emerald-500 mb-6" />
        <h1 className="text-3xl font-bold text-foreground mb-2">Moderator Dashboard</h1>
        <p className="text-muted-foreground mb-8 text-center max-w-md">
          Welcome to the control center. We will build the Moderation Queue and Analytics graphs here next!
        </p>
        <button 
          onClick={() => setIsAuthenticated(false)}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          Lock Console
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Background glow effects */}
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
