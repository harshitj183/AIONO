"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Search, Sparkles, ChevronRight, AlertCircle } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import { useAuth } from "@/hooks/useAuth";
import { submitInvestigation } from "@/lib/api";

const EXAMPLE_QUESTIONS = [
  "Why did customer complaints increase by 23% this month?",
  "What is causing the decline in AIONO Investigator revenue in Q3?",
  "Which department has the highest attrition risk right now?",
  "Are infrastructure costs above budget this quarter?",
  "What products are generating the most support tickets?",
];

export default function InvestigatePage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [question, setQuestion] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (isLoading) return null;
  if (!user) { router.push("/login"); return null; }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!question.trim() || question.trim().length < 10) {
      setError("Please enter a more detailed question (at least 10 characters).");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      const res = await submitInvestigation(question.trim());
      router.push(`/investigate/${res.investigation_id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to start investigation. Please try again.");
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar />
      <main className="flex-1 lg:ml-60 pt-16 lg:pt-0 p-4 sm:p-6 lg:p-8 animate-fade-in">
        <div className="max-w-2xl mx-auto">

          {/* Header */}
          <div className="text-center mb-8 lg:mb-10">
            <div className="inline-flex items-center justify-center w-12 h-12 lg:w-14 lg:h-14 bg-brand-600/15 rounded-2xl border border-brand-600/20 mb-4">
              <Sparkles className="w-6 h-6 lg:w-7 lg:h-7 text-brand-400" />
            </div>
            <h1 className="text-2xl lg:text-3xl font-bold text-text-primary mb-2">
              What do you want to investigate?
            </h1>
            <p className="text-text-secondary text-sm">
              Ask any business question. AIONO will query your data, search documents,
              and return an evidence-backed root cause analysis.
            </p>
          </div>

          {/* Viewer warning */}
          {user.role === "viewer" && (
            <div className="flex items-start gap-3 bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4 mb-6">
              <AlertCircle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-yellow-300">
                Your viewer account can browse investigations but cannot run new ones.
                Contact your admin to upgrade your access.
              </p>
            </div>
          )}

          {/* Question input */}
          <form onSubmit={handleSubmit} className="mb-8">
            <div className="relative">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="e.g. Why did customer complaints increase by 23% this month?"
                rows={3}
                maxLength={500}
                disabled={submitting || user.role === "viewer"}
                className="w-full bg-surface-card border border-surface-border rounded-2xl px-5 py-4 pr-16 text-text-primary placeholder-text-muted focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition resize-none text-sm leading-relaxed disabled:opacity-50"
              />
              <span className="absolute bottom-3 right-3 text-[10px] text-text-muted">
                {question.length}/500
              </span>
            </div>

            {error && (
              <p className="mt-2 text-xs text-red-400 flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5" />
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting || !question.trim() || user.role === "viewer"}
              className="mt-3 w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition flex items-center justify-center gap-2 text-sm"
            >
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Starting investigation…
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  Start Investigation
                </>
              )}
            </button>
          </form>

          {/* Example questions */}
          <div>
            <p className="text-xs text-text-muted mb-3 font-medium uppercase tracking-wide">
              Try one of these
            </p>
            <div className="space-y-2">
              {EXAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => setQuestion(q)}
                  disabled={user.role === "viewer"}
                  className="w-full flex items-center gap-3 p-3.5 bg-surface-card border border-surface-border hover:border-brand-500/40 hover:bg-surface-hover rounded-xl transition text-left group disabled:opacity-50"
                >
                  <ChevronRight className="w-4 h-4 text-brand-500 flex-shrink-0 group-hover:translate-x-0.5 transition-transform" />
                  <span className="text-sm text-text-secondary group-hover:text-text-primary transition">{q}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
