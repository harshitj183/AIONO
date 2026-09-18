"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Database, Table2, ChevronDown, ChevronRight, RefreshCw,
  Search, AlertCircle, Info, TrendingUp, Users, DollarSign,
  FileText, Ticket, BarChart2
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import { useAuth } from "@/hooks/useAuth";
import api from "@/lib/api";
import { clsx } from "clsx";

// ── Types ─────────────────────────────────────────────────────

interface TableInfo {
  name: string;
  row_count: number;
  columns: { name: string; type: string }[];
  sample_rows: Record<string, any>[];
}

interface DataExplorerResponse {
  tables: TableInfo[];
  db_size_kb: number;
  generated_at: string;
}

const TABLE_ICONS: Record<string, any> = {
  sales: DollarSign,
  support_tickets: Ticket,
  employees: Users,
  expenses: BarChart2,
  documents: FileText,
  investigation_logs: Search,
  users: Users,
};

const TABLE_DESCRIPTIONS: Record<string, string> = {
  sales: "Revenue transactions, product sales, and deal data",
  support_tickets: "Customer support issues, categories, and resolutions",
  employees: "HR data including performance scores and attrition risk",
  expenses: "Departmental expense records and budget tracking",
  documents: "Internal docs indexed for agent RAG search",
  investigation_logs: "Full audit trail of all agent investigations",
  users: "User accounts and role-based access control",
};

// ── Schema row badge ──────────────────────────────────────────

function TypeBadge({ type }: { type: string }) {
  const t = type.toUpperCase();
  const styles =
    t.includes("INT") || t.includes("FLOAT") || t.includes("REAL") || t.includes("NUMERIC")
      ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
      : t.includes("TEXT") || t.includes("CHAR") || t.includes("BLOB")
      ? "bg-purple-500/10 text-purple-400 border-purple-500/20"
      : t.includes("DATE") || t.includes("TIME")
      ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
      : t.includes("BOOL")
      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
      : "bg-surface text-text-muted border-surface-border";
  return (
    <span className={clsx("text-[10px] font-mono px-1.5 py-0.5 rounded border", styles)}>
      {type || "TEXT"}
    </span>
  );
}

// ── Table card ────────────────────────────────────────────────

function TableCard({ table }: { table: TableInfo }) {
  const [expanded, setExpanded] = useState(false);
  const [tab, setTab] = useState<"schema" | "sample">("schema");
  const Icon = TABLE_ICONS[table.name] || Table2;

  return (
    <div className="bg-surface-card border border-surface-border rounded-2xl overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-4 p-5 hover:bg-surface-hover transition text-left"
      >
        <div className="w-9 h-9 bg-brand-600/15 rounded-xl border border-brand-600/20 flex items-center justify-center flex-shrink-0">
          <Icon className="w-4 h-4 text-brand-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-text-primary font-mono">{table.name}</span>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-surface border border-surface-border text-text-muted">
              {table.row_count.toLocaleString()} rows
            </span>
          </div>
          <p className="text-xs text-text-muted mt-0.5 truncate">
            {TABLE_DESCRIPTIONS[table.name] || `${table.columns.length} columns`}
          </p>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <span className="text-xs text-text-muted">{table.columns.length} cols</span>
          {expanded ? (
            <ChevronDown className="w-4 h-4 text-text-muted" />
          ) : (
            <ChevronRight className="w-4 h-4 text-text-muted" />
          )}
        </div>
      </button>

      {/* Expanded body */}
      {expanded && (
        <div className="border-t border-surface-border">
          {/* Tabs */}
          <div className="flex gap-1 p-3 pb-0 border-b border-surface-border">
            {(["schema", "sample"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={clsx(
                  "text-xs font-medium px-3 py-1.5 rounded-lg transition capitalize",
                  tab === t
                    ? "bg-brand-600/20 text-brand-400"
                    : "text-text-muted hover:text-text-secondary hover:bg-surface-hover"
                )}
              >
                {t === "schema" ? "Column Schema" : "Sample Data"}
              </button>
            ))}
          </div>

          {tab === "schema" && (
            <div className="p-4">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-text-muted">
                    <th className="text-left pb-2 font-medium w-8">#</th>
                    <th className="text-left pb-2 font-medium">Column</th>
                    <th className="text-left pb-2 font-medium">Type</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border">
                  {table.columns.map((col, i) => (
                    <tr key={col.name} className="hover:bg-surface-hover/50">
                      <td className="py-2 text-text-muted">{i + 1}</td>
                      <td className="py-2 font-mono text-text-secondary">{col.name}</td>
                      <td className="py-2">
                        <TypeBadge type={col.type} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {tab === "sample" && (
            <div className="p-4 overflow-x-auto">
              {table.sample_rows.length === 0 ? (
                <p className="text-xs text-text-muted text-center py-6">No data in this table yet.</p>
              ) : (
                <table className="w-full text-xs min-w-max">
                  <thead>
                    <tr className="text-text-muted">
                      {Object.keys(table.sample_rows[0]).slice(0, 8).map((col) => (
                        <th key={col} className="text-left pb-2 pr-4 font-medium font-mono">{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-border">
                    {table.sample_rows.map((row, i) => (
                      <tr key={i} className="hover:bg-surface-hover/50">
                        {Object.values(row).slice(0, 8).map((val: any, j) => (
                          <td key={j} className="py-2 pr-4 text-text-secondary max-w-[200px] truncate">
                            {val === null || val === undefined ? (
                              <span className="text-text-muted italic">null</span>
                            ) : typeof val === "boolean" ? (
                              <span className={val ? "text-emerald-400" : "text-red-400"}>
                                {val.toString()}
                              </span>
                            ) : (
                              String(val).slice(0, 60) + (String(val).length > 60 ? "…" : "")
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              <p className="text-[10px] text-text-muted mt-3">
                Showing up to 5 sample rows for reference.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────

export default function DataExplorerPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<DataExplorerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  const fetchData = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get("/api/analytics/schema");
      setData(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load schema data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) fetchData();
  }, [user]);

  const filteredTables = data?.tables.filter((t) =>
    t.name.toLowerCase().includes(search.toLowerCase())
  ) ?? [];

  if (isLoading || !user) return null;

  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar />
      <main className="flex-1 lg:ml-60 pt-16 lg:pt-0 p-4 sm:p-6 lg:p-8 animate-fade-in">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="flex items-start justify-between mb-8">
            <div>
              <h1 className="text-2xl font-bold text-text-primary tracking-tight">Data Explorer</h1>
              <p className="text-text-secondary text-sm mt-1">
                Browse the live database schema and sample data that powers AIONO's investigations.
              </p>
            </div>
            <button
              onClick={fetchData}
              disabled={loading}
              className="flex items-center gap-2 bg-surface-card border border-surface-border hover:bg-surface-hover text-text-secondary hover:text-text-primary text-xs font-medium px-3.5 py-2.5 rounded-xl transition"
            >
              <RefreshCw className={clsx("w-3.5 h-3.5", loading && "animate-spin")} />
              Refresh
            </button>
          </div>

          {/* Stats bar */}
          {data && (
            <div className="grid grid-cols-3 gap-4 mb-8">
              <div className="bg-surface-card border border-surface-border rounded-2xl p-4 flex items-center gap-3">
                <div className="w-9 h-9 bg-brand-600/15 rounded-xl border border-brand-600/20 flex items-center justify-center flex-shrink-0">
                  <Database className="w-4 h-4 text-brand-400" />
                </div>
                <div>
                  <p className="text-xl font-bold text-text-primary">{data.tables.length}</p>
                  <p className="text-xs text-text-muted">Tables</p>
                </div>
              </div>
              <div className="bg-surface-card border border-surface-border rounded-2xl p-4 flex items-center gap-3">
                <div className="w-9 h-9 bg-emerald-500/15 rounded-xl border border-emerald-500/20 flex items-center justify-center flex-shrink-0">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                </div>
                <div>
                  <p className="text-xl font-bold text-text-primary">
                    {data.tables.reduce((acc, t) => acc + t.row_count, 0).toLocaleString()}
                  </p>
                  <p className="text-xs text-text-muted">Total records</p>
                </div>
              </div>
              <div className="bg-surface-card border border-surface-border rounded-2xl p-4 flex items-center gap-3">
                <div className="w-9 h-9 bg-purple-500/15 rounded-xl border border-purple-500/20 flex items-center justify-center flex-shrink-0">
                  <BarChart2 className="w-4 h-4 text-purple-400" />
                </div>
                <div>
                  <p className="text-xl font-bold text-text-primary">{data.db_size_kb} KB</p>
                  <p className="text-xs text-text-muted">Database size</p>
                </div>
              </div>
            </div>
          )}

          {/* Note banner */}
          <div className="flex items-start gap-3 bg-brand-600/5 border border-brand-600/15 rounded-xl p-4 mb-6">
            <Info className="w-4 h-4 text-brand-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-text-secondary">
              This is a read-only view of the database schema. The investigation agent uses these
              tables to answer business questions. Sample data is limited to 5 rows per table.
            </p>
          </div>

          {/* Search */}
          <div className="relative mb-5">
            <Search className="w-4 h-4 text-text-muted absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter tables..."
              className="w-full sm:w-64 bg-surface-card border border-surface-border rounded-xl pl-9 pr-4 py-2 text-xs text-text-primary placeholder-text-muted focus:border-brand-500 outline-none transition"
            />
          </div>

          {/* Tables */}
          {loading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="bg-surface-card border border-surface-border rounded-2xl h-20 animate-pulse" />
              ))}
            </div>
          ) : error ? (
            <div className="bg-red-500/5 border border-red-500/20 rounded-2xl p-8 text-center">
              <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-3" />
              <p className="text-sm text-red-300">{error}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredTables.map((table) => (
                <TableCard key={table.name} table={table} />
              ))}
              {filteredTables.length === 0 && (
                <div className="text-center py-12 text-text-muted text-sm">No tables match your search.</div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
