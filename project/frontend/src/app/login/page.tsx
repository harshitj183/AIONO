"use client";

import { useState, FormEvent } from "react";
import { useAuth } from "@/hooks/useAuth";
import { Eye, EyeOff, Search, Zap } from "lucide-react";

export default function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username, password);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Login failed. Please check your credentials."
      );
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4">
      {/* Background glow */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-brand-600/10 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-brand-600/20 rounded-2xl border border-brand-600/30 mb-4">
            <Search className="w-7 h-7 text-brand-400" />
          </div>
          <h1 className="text-3xl font-bold text-text-primary tracking-tight">AIONO</h1>
          <p className="text-text-secondary text-sm mt-1">AI Business Operations Investigator</p>
        </div>

        {/* Card */}
        <div className="bg-surface-card border border-surface-border rounded-2xl p-8 shadow-2xl">
          <h2 className="text-xl font-semibold text-text-primary mb-6">Sign in to your workspace</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="analyst"
                required
                autoComplete="username"
                className="w-full bg-surface border border-surface-border rounded-xl px-4 py-2.5 text-text-primary placeholder-text-muted focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPwd ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  autoComplete="current-password"
                  className="w-full bg-surface border border-surface-border rounded-xl px-4 py-2.5 pr-10 text-text-primary placeholder-text-muted focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(!showPwd)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition"
                >
                  {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-red-400 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-xl transition flex items-center justify-center gap-2 text-sm mt-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Signing in…
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  Sign In
                </>
              )}
            </button>
          </form>

          {/* Demo accounts */}
          <div className="mt-6 pt-5 border-t border-surface-border">
            <p className="text-xs text-text-muted text-center mb-3">Demo accounts</p>
            <div className="grid grid-cols-3 gap-2">
              {[
                { label: "Admin", u: "admin", p: "Admin@123" },
                { label: "Analyst", u: "analyst", p: "Analyst@123" },
                { label: "Viewer", u: "viewer", p: "Viewer@123" },
              ].map(({ label, u, p }) => (
                <button
                  key={u}
                  onClick={() => fillDemo(u, p)}
                  className="text-xs bg-surface border border-surface-border hover:border-brand-500/50 text-text-secondary hover:text-text-primary rounded-lg py-2 px-3 transition"
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
