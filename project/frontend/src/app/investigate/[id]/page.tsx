"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  CheckCircle2, Circle, Loader2, XCircle, AlertTriangle,
  ChevronDown, ChevronUp, Database, FileText, BarChart2,
  GitCompare, FileCheck, ArrowLeft, Shield, ClipboardList,
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import { useAuth } from "@/hooks/useAuth";
import { getInvestigation } from "@/lib/api";
import { clsx } from "clsx";

interface TraceStep { stage: string; action: string; detail: any; timestamp: string; }
interface EvidenceItem { claim: string; source: string; data: any; confidence: "high" | "medium" | "low"; }
interface Report {
  question: string; root_cause: string; confidence: string;
  needs_human_review: boolean; evidence_count: number;
  evidence: EvidenceItem[]; recommendations: string[];
  evidence_quality: string; report_status: string;
}
interface Investigation {
  id: number; question: string; status: string; report: Report;
  tool_trace: TraceStep[]; tokens_used: number; latency_ms: number;
  error_message?: string; created_at: string; completed_at?: string;
}

const STAGE_ICONS: Record<string, any> = {
  Planner: ClipboardList, Research: Database, Analysis: BarChart2,
  "Evidence Check": Shield, "Root Cause": GitCompare, Report: FileCheck,
};
const STAGE_ORDER = ["Planner", "Research", "Analysis", "Evidence Check", "Root Cause", "Report"];

function ConfidenceBadge({ confidence }: { confidence: string }) {
  const styles: Record<string, string> = {
    high: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    medium: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    low: "bg-red-500/10 text-red-400 border-red-500/20",
  };
  return (
    <span className={clsx("text-xs font-medium px-2.5 py-1 rounded-full border capitalize", styles[confidence] ?? styles.low)}>
      {confidence} confidence
    </span>
  );
}

function EvidenceCard({ item, index }: { item: EvidenceItem; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const borderColor = { high: "border-l-emerald-500", medium: "border-l-yellow-500", low: "border-l-red-500" }[item.confidence] ?? "border-l-surface-border";
  return (
    <div className={clsx("bg-surface border border-surface-border rounded-xl overflow-hidden border-l-2", borderColor)}>
      <button onClick={() => setExpanded(!expanded)} className="w-full flex items-start gap-3 p-4 text-left hover:bg-surface-hover transition">
        <span className="w-5 h-5 flex-shrink-0 rounded-full bg-brand-600/20 text-brand-400 text-[10px] font-bold flex items-center justify-center mt-0.5">
          {index + 1}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-text-primary leading-snug">{item.claim}</p>
          <p className="text-xs text-text-muted mt-0.5 flex items-center gap-1.5">
            <FileText className="w-3 h-3 flex-shrink-0" />
            <span className="truncate">{item.source}</span>
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0 ml-2">
          <ConfidenceBadge confidence={item.confidence} />
          {expanded ? <ChevronUp className="w-4 h-4 text-text-muted hidden sm:block" /> : <ChevronDown className="w-4 h-4 text-text-muted hidden sm:block" />}
        </div>
      </button>
      {expanded && item.data && (
        <div className="px-4 pb-4 border-t border-surface-border">
          <p className="text-xs text-text-muted mb-1.5 font-medium pt-3">Supporting data</p>
          <pre className="text-xs text-text-secondary bg-surface rounded-lg p-3 overflow-x-auto leading-relaxed whitespace-pre-wrap">
            {typeof item.data === "object" ? JSON.stringify(item.data, null, 2) : String(item.data)}
          </pre>
        </div>
      )}
    </div>
  );
}

function TraceTimeline({ trace, status }: { trace: TraceStep[]; status: string }) {
  const completedStages = new Set(trace.map((t) => t.stage));
  return (
    <div className="space-y-2">
      {STAGE_ORDER.map((stage, idx) => {
        const steps = trace.filter((t) => t.stage === stage);
        const done = completedStages.has(stage);
        const isRunning = status === "running" && !done &&
          STAGE_ORDER.indexOf(stage) === STAGE_ORDER.findIndex(s => !completedStages.has(s));
        const Icon = STAGE_ICONS[stage] || Circle;
        return (
          <div key={stage} className="flex items-start gap-3">
            <div className="flex flex-col items-center">
              <div className={clsx(
                "w-8 h-8 rounded-xl flex items-center justify-center border flex-shrink-0",
                done ? "bg-brand-600/20 border-brand-600/40 text-brand-400" :
                isRunning ? "bg-yellow-500/10 border-yellow-500/30 text-yellow-400" :
                "bg-surface border-surface-border text-text-muted",
              )}>
                {isRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : done ? <Icon className="w-4 h-4" /> : <Icon className="w-4 h-4 opacity-40" />}
              </div>
              {idx < STAGE_ORDER.length - 1 && (
                <div className={clsx("w-px h-5 mt-1", done ? "bg-brand-600/30" : "bg-surface-border")} />
              )}
            </div>
            <div className="pt-1.5 min-w-0 flex-1">
              <p className={clsx("text-sm font-medium", done ? "text-text-primary" : isRunning ? "text-yellow-300" : "text-text-muted")}>
                {stage}{isRunning && <span className="ml-2 text-xs text-yellow-400">running…</span>}
              </p>
              {done && steps.slice(-1).map((s, i) => (
                <p key={i} className="text-xs text-text-muted mt-0.5 truncate">{s.action}</p>
              ))}
            </div>
            {done && <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-1.5" />}
          </div>
        );
      })}
    </div>
  );
}

export default function InvestigationResultPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const id = Number(params.id);
  const [inv, setInv] = useState<Investigation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [traceOpen, setTraceOpen] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const data = await getInvestigation(id);
      setInv(data);
      return data.status;
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load investigation.");
      return "failed";
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { if (!isLoading && !user) router.push("/login"); }, [isLoading, user, router]);
  useEffect(() => {
    if (!user) return;
    fetchData().then((status) => {
      if (status === "running") {
        const poll = setInterval(async () => {
          const s = await fetchData();
          if (s !== "running") clearInterval(poll);
        }, 3000);
        return () => clearInterval(poll);
      }
    });
  }, [user, fetchData]);

  if (isLoading || (!inv && loading)) {
    return (
      <div className="flex min-h-screen bg-surface">
        <Sidebar />
        <main className="flex-1 lg:ml-60 pt-16 lg:pt-0 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 text-brand-400 animate-spin" />
            <p className="text-text-secondary text-sm">Loading investigation…</p>
          </div>
        </main>
      </div>
    );
  }

  if (error || !inv) {
    return (
      <div className="flex min-h-screen bg-surface">
        <Sidebar />
        <main className="flex-1 lg:ml-60 pt-16 lg:pt-0 flex items-center justify-center px-4">
          <div className="text-center">
            <XCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
            <p className="text-text-secondary">{error || "Investigation not found."}</p>
            <button onClick={() => router.push("/investigate")} className="mt-4 text-sm text-brand-400 hover:text-brand-300">
              ← Start a new investigation
            </button>
          </div>
        </main>
      </div>
    );
  }

  const report: Report = inv.report || {} as Report;
  const isRunning = inv.status === "running";
  const isFailed = inv.status === "failed";

  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar />
      <main className="flex-1 lg:ml-60 pt-16 lg:pt-0 p-4 sm:p-6 lg:p-8 animate-fade-in">
        <div className="max-w-4xl mx-auto">

          {/* Back */}
          <button onClick={() => router.push("/investigate")} className="flex items-center gap-2 text-sm text-text-muted hover:text-text-primary transition mb-5">
            <ArrowLeft className="w-4 h-4" />
            New investigation
          </button>

          {/* Question header */}
          <div className="bg-surface-card border border-surface-border rounded-2xl p-5 lg:p-6 mb-5 lg:mb-6">
            <div className="flex items-start gap-3 lg:gap-4">
              <div className="w-9 h-9 lg:w-10 lg:h-10 bg-brand-600/20 rounded-xl border border-brand-600/30 flex items-center justify-center flex-shrink-0">
                <Database className="w-4 h-4 lg:w-5 lg:h-5 text-brand-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-text-muted mb-1 font-medium uppercase tracking-wide">Investigation</p>
                <h1 className="text-base lg:text-lg font-semibold text-text-primary leading-snug">{inv.question}</h1>
                <div className="flex items-center gap-2 lg:gap-3 mt-3 flex-wrap">
                  <span className={clsx(
                    "flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border",
                    isRunning ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/20" :
                    isFailed ? "bg-red-500/10 text-red-400 border-red-500/20" :
                    "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
                  )}>
                    {isRunning ? <Loader2 className="w-3 h-3 animate-spin" /> : isFailed ? <XCircle className="w-3 h-3" /> : <CheckCircle2 className="w-3 h-3" />}
                    {inv.status}
                  </span>
                  {!isRunning && report.confidence && <ConfidenceBadge confidence={report.confidence} />}
                  {inv.tokens_used > 0 && <span className="text-xs text-text-muted">{inv.tokens_used.toLocaleString()} tokens</span>}
                  {inv.latency_ms > 0 && <span className="text-xs text-text-muted">{(inv.latency_ms / 1000).toFixed(1)}s</span>}
                </div>
              </div>
            </div>
          </div>

          {/* Mobile: collapsible agent trace */}
          <div className="lg:hidden mb-4">
            <button
              onClick={() => setTraceOpen(!traceOpen)}
              className="w-full flex items-center justify-between bg-surface-card border border-surface-border rounded-2xl p-4 text-sm font-medium text-text-primary"
            >
              <span>Agent Workflow</span>
              {traceOpen ? <ChevronUp className="w-4 h-4 text-text-muted" /> : <ChevronDown className="w-4 h-4 text-text-muted" />}
            </button>
            {traceOpen && (
              <div className="bg-surface-card border border-surface-border border-t-0 rounded-b-2xl p-4">
                <TraceTimeline trace={inv.tool_trace || []} status={inv.status} />
              </div>
            )}
          </div>

          {/* Desktop: 2-col layout */}
          <div className="lg:grid lg:grid-cols-3 lg:gap-6 space-y-5 lg:space-y-0">
            {/* Left: report */}
            <div className="lg:col-span-2 space-y-5">
              {isRunning && (
                <div className="bg-yellow-500/5 border border-yellow-500/20 rounded-2xl p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <Loader2 className="w-5 h-5 text-yellow-400 animate-spin" />
                    <p className="text-sm font-semibold text-yellow-300">Investigation in progress</p>
                  </div>
                  <p className="text-xs text-text-secondary">
                    The agent is querying databases, searching documents, and analysing patterns.
                    This page refreshes automatically every 3 seconds.
                  </p>
                </div>
              )}

              {isFailed && (
                <div className="bg-red-500/5 border border-red-500/20 rounded-2xl p-5">
                  <div className="flex items-center gap-3 mb-2">
                    <XCircle className="w-5 h-5 text-red-400" />
                    <p className="text-sm font-semibold text-red-300">Investigation failed</p>
                  </div>
                  <p className="text-xs text-text-secondary">{inv.error_message || "An unexpected error occurred."}</p>
                </div>
              )}

              {report.needs_human_review && !isRunning && (
                <div className="bg-yellow-500/5 border border-yellow-500/20 rounded-2xl p-4 flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold text-yellow-300">Human review recommended</p>
                    <p className="text-xs text-text-secondary mt-1">
                      The agent found insufficient or conflicting evidence. These findings should be reviewed by a domain expert before taking action.
                    </p>
                  </div>
                </div>
              )}

              {report.root_cause && (
                <div className="bg-surface-card border border-surface-border rounded-2xl p-5 lg:p-6">
                  <h2 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-3">Root Cause</h2>
                  <p className="text-text-primary leading-relaxed">{report.root_cause}</p>
                </div>
              )}

              {report.evidence && report.evidence.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="text-xs font-medium text-text-muted uppercase tracking-wide">
                      Evidence ({report.evidence.length})
                    </h2>
                    <span className={clsx(
                      "text-xs px-2.5 py-1 rounded-full border font-medium",
                      report.evidence_quality === "strong" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                      report.evidence_quality === "moderate" ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/20" :
                      "bg-red-500/10 text-red-400 border-red-500/20",
                    )}>
                      {report.evidence_quality} evidence
                    </span>
                  </div>
                  <div className="space-y-2">
                    {report.evidence.map((item, i) => <EvidenceCard key={i} item={item} index={i} />)}
                  </div>
                </div>
              )}

              {report.recommendations && report.recommendations.length > 0 && (
                <div className="bg-surface-card border border-surface-border rounded-2xl p-5 lg:p-6">
                  <h2 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-4">
                    Recommended Actions
                  </h2>
                  <div className="space-y-2.5">
                    {report.recommendations.map((rec, i) => (
                      <div key={i} className="flex items-start gap-3">
                        <span className="w-5 h-5 rounded-lg bg-brand-600/20 text-brand-400 text-[10px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                          {i + 1}
                        </span>
                        <p className="text-sm text-text-secondary leading-relaxed">{rec}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right: agent trace — desktop only */}
            <div className="hidden lg:block lg:col-span-1">
              <div className="bg-surface-card border border-surface-border rounded-2xl p-5 sticky top-8">
                <h2 className="text-xs font-medium text-text-muted uppercase tracking-wide mb-4">
                  Agent Workflow
                </h2>
                <TraceTimeline trace={inv.tool_trace || []} status={inv.status} />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
