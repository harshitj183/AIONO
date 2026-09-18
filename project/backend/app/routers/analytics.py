"""
Analytics router – provides pre-built dashboard metrics for the frontend.
These are deterministic DB queries, no LLM involved.
"""

import sqlite3
import os
from datetime import datetime
from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.models import User
from app.config import settings

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def _db():
    conn = sqlite3.connect(settings.DATABASE_URL.replace("sqlite+aiosqlite:///", ""))
    conn.row_factory = sqlite3.Row
    return conn


def _q(sql: str) -> list[dict]:
    conn = _db()
    cur = conn.cursor()
    cur.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


@router.get("/dashboard")
async def dashboard_metrics(current_user: User = Depends(get_current_user)):
    """
    Returns key business metrics for the dashboard overview:
    total tickets, revenue, complaint categories, and recent trends.
    """
    ticket_total = _q("SELECT COUNT(*) as total FROM support_tickets WHERE created_at >= date('now', '-30 days')")
    prev_ticket_total = _q("SELECT COUNT(*) as total FROM support_tickets WHERE created_at >= date('now', '-60 days') AND created_at < date('now', '-30 days')")
    revenue_30 = _q("SELECT ROUND(SUM(amount),2) as total FROM sales WHERE sale_date >= date('now', '-30 days')")
    prev_revenue_30 = _q("SELECT ROUND(SUM(amount),2) as total FROM sales WHERE sale_date >= date('now', '-60 days') AND sale_date < date('now', '-30 days')")
    top_categories = _q("""
        SELECT category, COUNT(*) as count
        FROM support_tickets
        WHERE created_at >= date('now', '-30 days')
        GROUP BY category ORDER BY count DESC LIMIT 5
    """)
    daily_tickets = _q("""
        SELECT date(created_at) as day, COUNT(*) as count
        FROM support_tickets
        WHERE created_at >= date('now', '-30 days')
        GROUP BY date(created_at) ORDER BY day
    """)
    product_tickets = _q("""
        SELECT product_name, COUNT(*) as count
        FROM support_tickets
        WHERE created_at >= date('now', '-30 days')
        GROUP BY product_name ORDER BY count DESC LIMIT 5
    """)
    open_tickets = _q("SELECT COUNT(*) as total FROM support_tickets WHERE status IN ('open', 'in_progress')")

    def _pct(curr, prev):
        if not prev or prev == 0:
            return 0.0
        return round((curr - prev) / prev * 100, 1)

    t_curr = ticket_total[0]["total"] if ticket_total else 0
    t_prev = prev_ticket_total[0]["total"] if prev_ticket_total else 0
    r_curr = revenue_30[0]["total"] or 0 if revenue_30 else 0
    r_prev = prev_revenue_30[0]["total"] or 0 if prev_revenue_30 else 0

    return {
        "summary": {
            "tickets_30d": t_curr,
            "tickets_change_pct": _pct(t_curr, t_prev),
            "revenue_30d": r_curr,
            "revenue_change_pct": _pct(r_curr, r_prev),
            "open_tickets": open_tickets[0]["total"] if open_tickets else 0,
        },
        "top_categories": top_categories,
        "daily_ticket_trend": daily_tickets,
        "product_ticket_breakdown": product_tickets,
    }


@router.get("/schema")
async def data_schema(current_user: User = Depends(get_current_user)):
    """
    Returns live database schema: table names, column definitions, row counts, and sample rows.
    Used by the Data Explorer page in the frontend.
    """
    db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    conn = _db()
    cur = conn.cursor()

    # Get all tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    table_names = [row["name"] for row in cur.fetchall()]

    tables = []
    for tname in table_names:
        # Column info
        cur.execute(f"PRAGMA table_info({tname})")
        columns = [{"name": row["name"], "type": row["type"] or "TEXT"} for row in cur.fetchall()]

        # Row count
        cur.execute(f"SELECT COUNT(*) as cnt FROM {tname}")
        row_count = cur.fetchone()["cnt"]

        # Sample rows (5 rows, skip sensitive fields for users table)
        if tname == "users":
            safe_cols = [c["name"] for c in columns if c["name"] not in ("hashed_password",)]
            col_str = ", ".join(safe_cols)
            cur.execute(f"SELECT {col_str} FROM {tname} LIMIT 5")
        else:
            cur.execute(f"SELECT * FROM {tname} LIMIT 5")

        sample_rows = [dict(r) for r in cur.fetchall()]

        tables.append({
            "name": tname,
            "row_count": row_count,
            "columns": columns,
            "sample_rows": sample_rows,
        })

    conn.close()

    # DB file size
    db_size_kb = 0
    try:
        db_size_kb = round(os.path.getsize(db_path) / 1024, 1)
    except Exception:
        pass

    return {
        "tables": tables,
        "db_size_kb": db_size_kb,
        "generated_at": datetime.utcnow().isoformat(),
    }
