"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart2, Search, History, Database, LogOut,
  Activity, ChevronRight, Menu, X,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { clsx } from "clsx";

const NAV = [
  { href: "/", icon: BarChart2, label: "Dashboard" },
  { href: "/investigate", icon: Search, label: "Investigate" },
  { href: "/history", icon: History, label: "History" },
  { href: "/data", icon: Database, label: "Data Explorer" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  const content = (
    <div className="flex flex-col h-full">
      {/* Brand */}
      <div className="px-5 py-5 border-b border-surface-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-brand-600/20 rounded-lg border border-brand-600/30 flex items-center justify-center flex-shrink-0">
            <Activity className="w-4 h-4 text-brand-400" />
          </div>
          <div>
            <span className="text-sm font-bold text-text-primary tracking-tight">AIONO</span>
            <p className="text-[10px] text-text-muted leading-tight">Operations Investigator</p>
          </div>
        </div>
        {/* Close button — mobile only */}
        <button
          onClick={() => setOpen(false)}
          className="lg:hidden p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-hover transition"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Nav links */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(({ href, icon: Icon, label }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition group",
                active
                  ? "bg-brand-600/15 text-brand-400 border border-brand-600/20"
                  : "text-text-secondary hover:bg-surface-hover hover:text-text-primary"
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
              {active && <ChevronRight className="w-3 h-3 ml-auto opacity-60" />}
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      <div className="px-3 py-4 border-t border-surface-border">
        <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-surface mb-2">
          <div className="w-7 h-7 rounded-full bg-brand-600/30 flex items-center justify-center flex-shrink-0">
            <span className="text-xs font-semibold text-brand-400 uppercase">
              {user?.username?.[0] ?? "U"}
            </span>
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-text-primary truncate">{user?.username}</p>
            <p className="text-[10px] text-text-muted capitalize">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-text-muted hover:text-red-400 hover:bg-red-500/5 transition w-full"
        >
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* ── Desktop sidebar ── */}
      <aside className="hidden lg:flex fixed left-0 top-0 h-full w-60 bg-surface-card border-r border-surface-border flex-col z-40">
        {content}
      </aside>

      {/* ── Mobile top bar ── */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-40 bg-surface-card border-b border-surface-border px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-brand-600/20 rounded-lg border border-brand-600/30 flex items-center justify-center">
            <Activity className="w-3.5 h-3.5 text-brand-400" />
          </div>
          <span className="text-sm font-bold text-text-primary">AIONO</span>
        </div>
        <button
          onClick={() => setOpen(true)}
          className="p-2 rounded-xl text-text-muted hover:text-text-primary hover:bg-surface-hover transition"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>
      </header>

      {/* ── Mobile drawer overlay ── */}
      {open && (
        <div
          className="lg:hidden fixed inset-0 z-50 flex"
          onClick={() => setOpen(false)}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

          {/* Drawer */}
          <aside
            className="relative w-72 max-w-[85vw] bg-surface-card border-r border-surface-border flex flex-col z-50 animate-slide-in-left"
            onClick={(e) => e.stopPropagation()}
          >
            {content}
          </aside>
        </div>
      )}
    </>
  );
}
