"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  Search, Clock, Trash2, ArrowRight, CheckCircle2,
  XCircle, Loader2, RefreshCw, Filter, Zap,
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import { useAuth } from "@/hooks/useAuth";
import { listInvestigations, deleteInvestigation } from "@/lib/api";
import { clsx } from "clsx";

interface InvestigationItem {
  id: number; question: string; status: string;
  tokens_used: number; latency_ms: number;
  created_at: string; completed_at?: string;
}

export default function HistoryPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [investigations, setInvestigations] = useState<InvestigationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => { if (!isLoading && !user) router.push("/login"); }, [isLoading, user, router]);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await listInvestigations(50, 0);
      setInvestigations(res.investigations || []);
    } catch (err) {
      console.error("Failed to load history:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (user) loadData(); }, [user]);

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Delete this investigation log?")) return;
    setDeletingId(id);
    try {
      await deleteInvestigation(id);
      setInvestigations((prev) => prev.filter((item) => item.id !== id));
    } catch {
      alert("Failed to delete investigation.");
    } finally {
      setDeletingId(null);
    }
  };

  const filtered = useMemo(() => investigations.filter((inv) => {
    const matchesSearch = inv.question.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "all" || inv.status === statusFilter;
    return matchesSearch && matchesStatus;
  }), [investigations, searchTerm, statusFilter]);

  const stats = useMemo(() => {
    const total = investigations.length;
    const completed = investigations.filter((i) => i.status === "completed").length;
    const totalTokens = investigations.reduce((acc, cur) => acc + (cur.tokens_used || 0), 0);
    const avgLatency = completed > 0
      ? Math.round(investigations.filter((i) => i.status === "completed" && i.latency_ms > 0)
          .reduce((acc, cur) => acc + cur.latency_ms, 0) / completed / 1000)
      : 0;
    return { total, completed, totalTokens, avgLatency };
  }, [investigations]);

  if (isLoading || !user) return null;

  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar />
      <main className="flex-1 lg:ml-60 pt-16 lg:pt-0 p-4 sm:p-6 lg:p-8 animate-fade-in">
        <div className="max-w-5xl mx-auto">

          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 lg:mb-8">
            <div>
              <h1 className="text-xl lg:text-2xl font-bold text-text-primary tracking-tight">
                Investigation History
              </h1>
              <p className="text-text-secondary text-sm mt-1">
                Complete audit trail of all investigations, root-cause analyses, and agent traces.
              </p>
            </div>
            <div className="flex items-center gap-2 self-start sm:self-auto">
              <button
                onClick={loadData}
                disabled={loading}
                className="flex items-center gap-2 bg-surface-card border border-surface-border hover:bg-surface-hover text-text-secondary hover:text-text-primary text-xs font-medium px-3 py-2.5 rounded-xl transition"
              >
                <RefreshCw className={clsx("w-3.5 h-3.5", loading && "animate-spin")} />
                <span className="hidden sm:inline">Refresh</span>
              </button>
              <button
                onClick={() => router.push("/investigate")}
                className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold px-3 sm:px-4 py-2.5 rounded-xl transition"
              >
                <Search className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">New Investigation</span>
                <span className="sm:hidden">Investigate</span>
              </button>
            </div>
          </div>

          {/* Stats — 2 cols mobile, 4 cols desktop */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4 mb-6 lg:mb-8">
            {[
              { label: "Total", value: stats.total, color: "text-text-primary" },
              { label: "Completed", value: stats.completed, color: "text-emerald-400" },
              { label: "Avg Latency", value: `${stats.avgLatency}s`, color: "text-text-primary" },
              { label: "Tokens Used", value: stats.totalTokens.toLocaleString(), color: "text-brand-400" },
            ].map(({ label, value, color }) => (
              <div key={label} className="bg-surface-card border border-surface-border rounded-2xl p-4">
                <p className="text-xs text-text-muted font-medium">{label}</p>
                <p className={clsx("text-xl lg:text-2xl font-bold mt-1", color)}>{value}</p>
              </div>
            ))}
          </div>

          {/* Search + filter */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mb-5">
            <div className="relative w-full sm:w-72">
              <Search className="w-4 h-4 text-text-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search questions…"
                className="w-full bg-surface-card border border-surface-border rounded-xl pl-9 pr-4 py-2 text-xs text-text-primary placeholder-text-muted focus:border-brand-500 outline-none transition"
              />
            </div>
            <div className="flex items-center gap-1.5 flex-wrap">
              <Filter className="w-3.5 h-3.5 text-text-muted mr-1" />
              {["all", "completed", "running", "failed"].map((s) => (
                <button
                  key={s}
                  onClick={() => setStatusFilter(s)}
                  className={clsx(
                    "text-xs px-3 py-1.5 rounded-lg capitalize font-medium transition",
                    statusFilter === s
                      ? "bg-brand-600 text-white"
                      : "bg-surface-card border border-surface-border text-text-secondary hover:text-text-primary hover:bg-surface-hover",
                  )}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* List */}
          {loading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="bg-surface-card border border-surface-border rounded-2xl p-5 h-20 animate-pulse" />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="bg-surface-card border border-surface-border rounded-2xl p-10 sm:p-12 text-center">
              <Search className="w-10 h-10 text-text-muted mx-auto mb-3 opacity-50" />
              <h3 className="text-sm font-semibold text-text-primary">No investigations found</h3>
              <p className="text-xs text-text-secondary mt-1 max-w-sm mx-auto">
                {searchTerm || statusFilter !== "all"
                  ? "Try changing your search or filter."
                  : "Start your first AI investigation to see reports here."}
              </p>
              <button
                onClick={() => router.push("/investigate")}
                className="mt-4 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold px-4 py-2 rounded-xl transition"
              >
                Start Investigation
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {filtered.map((inv) => {
                const isCompleted = inv.status === "completed";
                const isRunning = inv.status === "running";
                const isFailed = inv.status === "failed";
                const dateStr = new Date(inv.created_at).toLocaleDateString(undefined, {
                  month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                });
                return (
                  <div
                    key={inv.id}
                    onClick={() => router.push(`/investigate/${inv.id}`)}
                    className="bg-surface-card border border-surface-border hover:border-brand-500/40 rounded-2xl p-4 sm:p-5 transition cursor-pointer group flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                        <span className={clsx(
                          "inline-flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-0.5 rounded-full border",
                          isCompleted && "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
                          isRunning && "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
                          isFailed && "bg-red-500/10 text-red-400 border-red-500/20",
                        )}>
                          {isRunning && <Loader2 className="w-3 h-3 animate-spin" />}
                          {isCompleted && <CheckCircle2 className="w-3 h-3" />}
                          {isFailed && <XCircle className="w-3 h-3" />}
                          {inv.status}
                        </span>
                        <span className="text-[11px] text-text-muted flex items-center gap-1">
                          <Clock className="w-3 h-3" />{dateStr}
                        </span>
                        {inv.tokens_used > 0 && (
                          <span className="text-[11px] text-brand-400/80 flex items-center gap-1">
                            <Zap className="w-3 h-3" />{inv.tokens_used.toLocaleString()}
                          </span>
                        )}
                      </div>
                      <h3 className="text-sm font-medium text-text-primary group-hover:text-brand-300 transition line-clamp-2 sm:line-clamp-1">
                        {inv.question}
                      </h3>
                    </div>
                    <div className="flex items-center gap-2 self-end sm:self-auto flex-shrink-0">
                      <button
                        onClick={(e) => handleDelete(inv.id, e)}
                        disabled={deletingId === inv.id}
                        className="p-2 text-text-muted hover:text-red-400 hover:bg-red-500/10 rounded-xl transition"
                      >
                        {deletingId === inv.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                      </button>
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-brand-400 group-hover:translate-x-0.5 transition-transform">
                        View <ArrowRight className="w-3.5 h-3.5" />
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
