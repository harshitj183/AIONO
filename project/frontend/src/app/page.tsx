"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell,
} from "recharts";
import { TrendingUp, TrendingDown, AlertCircle, Ticket, DollarSign, Search } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import { useAuth } from "@/hooks/useAuth";
import { getDashboardMetrics, listInvestigations } from "@/lib/api";
import { clsx } from "clsx";

const PIE_COLORS = ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe"];

function StatCard({
  label, value, change, icon: Icon,
}: {
  label: string; value: string | number; change?: number; icon: any;
}) {
  const up = change !== undefined && change > 0;
  const down = change !== undefined && change < 0;
  return (
    <div className="bg-surface-card border border-surface-border rounded-2xl p-5">
      <div className="flex items-start justify-between mb-4">
        <div className="w-10 h-10 bg-brand-600/15 rounded-xl flex items-center justify-center border border-brand-600/20">
          <Icon className="w-5 h-5 text-brand-400" />
        </div>
        {change !== undefined && (
          <span className={clsx(
            "flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-lg",
            up ? "text-emerald-400 bg-emerald-500/10"
              : down ? "text-red-400 bg-red-500/10"
              : "text-text-muted bg-surface",
          )}>
            {up ? <TrendingUp className="w-3 h-3" /> : down ? <TrendingDown className="w-3 h-3" /> : null}
            {Math.abs(change)}%
          </span>
        )}
      </div>
      <p className="text-2xl font-bold text-text-primary">
        {typeof value === "number" ? value.toLocaleString() : value}
      </p>
      <p className="text-xs text-text-muted mt-1">{label}</p>
    </div>
  );
}

export default function DashboardPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [metrics, setMetrics] = useState<any>(null);
  const [recentInvs, setRecentInvs] = useState<any[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
  }, [isLoading, user, router]);

  useEffect(() => {
    if (!user) return;
    Promise.all([getDashboardMetrics(), listInvestigations(5)])
      .then(([m, invs]) => {
        setMetrics(m);
        setRecentInvs(invs.investigations || []);
      })
      .catch(console.error)
      .finally(() => setLoadingData(false));
  }, [user]);

  if (isLoading || !user) return null;

  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar />

      {/* lg: offset for fixed sidebar; mobile: top-bar offset */}
      <main className="flex-1 lg:ml-60 pt-16 lg:pt-0 p-4 sm:p-6 lg:p-8 animate-fade-in">

        {/* Header */}
        <div className="mb-6 lg:mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-text-primary">
              Good morning, {user.username} 👋
            </h1>
            <p className="text-text-secondary text-sm mt-1">
              Here's what's happening across your business operations.
            </p>
          </div>
          <button
            onClick={() => router.push("/investigate")}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-4 py-2.5 rounded-xl transition self-start sm:self-auto"
          >
            <Search className="w-4 h-4" />
            New Investigation
          </button>
        </div>

        {loadingData ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4 mb-6 lg:mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-surface-card border border-surface-border rounded-2xl p-5 h-28 animate-pulse" />
            ))}
          </div>
        ) : metrics ? (
          <>
            {/* KPI Cards — 2 cols mobile, 4 cols desktop */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4 mb-6 lg:mb-8">
              <StatCard
                label="Support tickets (30d)"
                value={metrics.summary.tickets_30d}
                change={metrics.summary.tickets_change_pct}
                icon={Ticket}
              />
              <StatCard
                label="Revenue (30d)"
                value={`$${(metrics.summary.revenue_30d / 1000).toFixed(1)}k`}
                change={metrics.summary.revenue_change_pct}
                icon={DollarSign}
              />
              <StatCard
                label="Open tickets"
                value={metrics.summary.open_tickets}
                icon={AlertCircle}
              />
              <StatCard
                label="Investigations run"
                value={recentInvs.length}
                icon={Search}
              />
            </div>

            {/* Charts row — stacked mobile, 3-col desktop */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6 lg:mb-8">
              {/* Ticket trend — full width mobile, 2/3 desktop */}
              <div className="lg:col-span-2 bg-surface-card border border-surface-border rounded-2xl p-5">
                <h3 className="text-sm font-semibold text-text-primary mb-4">
                  Daily Ticket Volume – Last 30 Days
                </h3>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={metrics.daily_ticket_trend}>
                    <XAxis dataKey="day" tick={{ fontSize: 10, fill: "#475569" }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: "#475569" }} tickLine={false} axisLine={false} width={24} />
                    <Tooltip
                      contentStyle={{ background: "#161b27", border: "1px solid #1e2433", borderRadius: 10, fontSize: 12 }}
                      labelStyle={{ color: "#94a3b8" }}
                    />
                    <Line type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Category pie */}
              <div className="bg-surface-card border border-surface-border rounded-2xl p-5">
                <h3 className="text-sm font-semibold text-text-primary mb-4">Ticket Categories</h3>
                <ResponsiveContainer width="100%" height={160}>
                  <PieChart>
                    <Pie
                      data={metrics.top_categories}
                      dataKey="count"
                      nameKey="category"
                      cx="50%" cy="50%"
                      innerRadius={45}
                      outerRadius={70}
                      strokeWidth={0}
                    >
                      {metrics.top_categories.map((_: any, i: number) => (
                        <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ background: "#161b27", border: "1px solid #1e2433", borderRadius: 10, fontSize: 12 }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-1 mt-2">
                  {metrics.top_categories.slice(0, 4).map((c: any, i: number) => (
                    <div key={c.category} className="flex items-center gap-2 text-xs">
                      <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: PIE_COLORS[i] }} />
                      <span className="text-text-secondary capitalize">{c.category}</span>
                      <span className="ml-auto text-text-muted">{c.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Bottom row — stacked mobile, 2-col desktop */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="bg-surface-card border border-surface-border rounded-2xl p-5">
                <h3 className="text-sm font-semibold text-text-primary mb-4">
                  Tickets by Product (30d)
                </h3>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={metrics.product_ticket_breakdown} layout="vertical">
                    <XAxis type="number" tick={{ fontSize: 10, fill: "#475569" }} tickLine={false} axisLine={false} />
                    <YAxis type="category" dataKey="product_name" tick={{ fontSize: 10, fill: "#94a3b8" }} tickLine={false} axisLine={false} width={130} />
                    <Tooltip
                      contentStyle={{ background: "#161b27", border: "1px solid #1e2433", borderRadius: 10, fontSize: 12 }}
                    />
                    <Bar dataKey="count" fill="#6366f1" radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-surface-card border border-surface-border rounded-2xl p-5">
                <h3 className="text-sm font-semibold text-text-primary mb-4">Recent Investigations</h3>
                {recentInvs.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-32 text-text-muted">
                    <Search className="w-8 h-8 mb-2 opacity-40" />
                    <p className="text-xs">No investigations yet</p>
                    <button
                      onClick={() => router.push("/investigate")}
                      className="mt-3 text-xs text-brand-400 hover:text-brand-300 transition"
                    >
                      Start your first investigation →
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {recentInvs.map((inv: any) => (
                      <button
                        key={inv.id}
                        onClick={() => router.push(`/investigate/${inv.id}`)}
                        className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-surface-hover transition text-left"
                      >
                        <div className={clsx(
                          "w-2 h-2 rounded-full flex-shrink-0",
                          inv.status === "completed" ? "bg-emerald-400" :
                          inv.status === "running" ? "bg-yellow-400 animate-pulse" : "bg-red-400",
                        )} />
                        <p className="text-xs text-text-secondary line-clamp-1 flex-1">{inv.question}</p>
                        <span className={clsx(
                          "text-[10px] px-2 py-0.5 rounded-full flex-shrink-0 font-medium",
                          inv.status === "completed" ? "bg-emerald-500/10 text-emerald-400" :
                          inv.status === "running" ? "bg-yellow-500/10 text-yellow-400" :
                          "bg-red-500/10 text-red-400",
                        )}>
                          {inv.status}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </>
        ) : null}
      </main>
    </div>
  );
}
