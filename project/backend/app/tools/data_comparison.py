"""
Data Comparison Tool – compares metrics across two time periods or two products.
Produces structured delta analysis with percentage changes and significance flags.
"""

import sqlite3
import json
from langchain_core.tools import tool
from app.config import settings


def _get_db_path() -> str:
    return settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")


def _query(sql: str) -> list[dict]:
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def _pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round((current - previous) / previous * 100, 1)


def _significance_flag(pct: float) -> str:
    if abs(pct) >= 50:
        return "critical"
    elif abs(pct) >= 20:
        return "significant"
    elif abs(pct) >= 10:
        return "notable"
    return "minor"


@tool
def data_comparison_tool(
    compare_type: str,
    period_days: int = 30,
    product_a: str = None,
    product_b: str = None,
) -> str:
    """
    Compare business metrics between two time periods or two products.

    Available compare_type values:
    - "month_over_month_tickets"  : Compare support ticket volume this month vs last month
    - "month_over_month_revenue"  : Compare revenue this period vs previous period
    - "product_ticket_comparison" : Compare ticket volume between product_a and product_b
    - "product_revenue_comparison": Compare revenue between product_a and product_b
    - "severity_trend_comparison" : Compare ticket severity distribution across periods

    Args:
        compare_type: Type of comparison to run.
        period_days: Length of each comparison window (default 30 days).
        product_a: First product for product-level comparisons.
        product_b: Second product for product-level comparisons.

    Returns structured JSON with current values, previous values, delta,
    percentage change, and significance level for each metric.
    """
    try:
        if compare_type == "month_over_month_tickets":
            p_filter = f"AND product_name = '{product_a}'" if product_a else ""
            current = _query(f"""
                SELECT category, COUNT(*) as count
                FROM support_tickets
                WHERE created_at >= date('now', '-{period_days} days') {p_filter}
                GROUP BY category
            """)
            previous = _query(f"""
                SELECT category, COUNT(*) as count
                FROM support_tickets
                WHERE created_at >= date('now', '-{period_days * 2} days')
                  AND created_at < date('now', '-{period_days} days') {p_filter}
                GROUP BY category
            """)
            curr_map = {r["category"]: r["count"] for r in current}
            prev_map = {r["category"]: r["count"] for r in previous}
            curr_total = sum(curr_map.values())
            prev_total = sum(prev_map.values())

            category_breakdown = []
            for cat in set(list(curr_map.keys()) + list(prev_map.keys())):
                c = curr_map.get(cat, 0)
                p = prev_map.get(cat, 0)
                pct = _pct_change(c, p)
                category_breakdown.append({
                    "category": cat,
                    "current": c,
                    "previous": p,
                    "change_pct": pct,
                    "significance": _significance_flag(pct),
                })
            category_breakdown.sort(key=lambda x: x["change_pct"], reverse=True)

            return json.dumps({
                "compare_type": compare_type,
                "period_days": period_days,
                "product": product_a or "all",
                "summary": {
                    "current_total": curr_total,
                    "previous_total": prev_total,
                    "total_change_pct": _pct_change(curr_total, prev_total),
                    "significance": _significance_flag(_pct_change(curr_total, prev_total)),
                },
                "breakdown": category_breakdown,
            })

        elif compare_type == "month_over_month_revenue":
            p_filter = f"AND product_name = '{product_a}'" if product_a else ""
            curr = _query(f"""
                SELECT ROUND(SUM(amount), 2) as revenue, COUNT(*) as transactions
                FROM sales
                WHERE sale_date >= date('now', '-{period_days} days') {p_filter}
            """)
            prev = _query(f"""
                SELECT ROUND(SUM(amount), 2) as revenue, COUNT(*) as transactions
                FROM sales
                WHERE sale_date >= date('now', '-{period_days * 2} days')
                  AND sale_date < date('now', '-{period_days} days') {p_filter}
            """)
            c_rev = curr[0]["revenue"] or 0
            p_rev = prev[0]["revenue"] or 0
            c_trx = curr[0]["transactions"] or 0
            p_trx = prev[0]["transactions"] or 0

            return json.dumps({
                "compare_type": compare_type,
                "period_days": period_days,
                "product": product_a or "all",
                "current": {"revenue": c_rev, "transactions": c_trx},
                "previous": {"revenue": p_rev, "transactions": p_trx},
                "revenue_change_pct": _pct_change(c_rev, p_rev),
                "transaction_change_pct": _pct_change(c_trx, p_trx),
                "significance": _significance_flag(_pct_change(c_rev, p_rev)),
            })

        elif compare_type == "product_ticket_comparison":
            if not product_a or not product_b:
                return json.dumps({"error": "product_a and product_b required for product comparison."})
            rows = _query(f"""
                SELECT product_name,
                       COUNT(*) as total,
                       SUM(CASE WHEN severity='critical' THEN 1 ELSE 0 END) as critical,
                       SUM(CASE WHEN severity='high' THEN 1 ELSE 0 END) as high
                FROM support_tickets
                WHERE created_at >= date('now', '-{period_days} days')
                  AND product_name IN ('{product_a}', '{product_b}')
                GROUP BY product_name
            """)
            return json.dumps({
                "compare_type": compare_type,
                "period_days": period_days,
                "data": rows,
            })

        elif compare_type == "product_revenue_comparison":
            if not product_a or not product_b:
                return json.dumps({"error": "product_a and product_b required."})
            rows = _query(f"""
                SELECT product_name,
                       ROUND(SUM(amount), 2) as revenue,
                       COUNT(*) as transactions,
                       ROUND(AVG(amount), 2) as avg_deal
                FROM sales
                WHERE sale_date >= date('now', '-{period_days} days')
                  AND product_name IN ('{product_a}', '{product_b}')
                GROUP BY product_name
            """)
            return json.dumps({
                "compare_type": compare_type,
                "period_days": period_days,
                "data": rows,
            })

        elif compare_type == "severity_trend_comparison":
            p_filter = f"AND product_name = '{product_a}'" if product_a else ""
            current = _query(f"""
                SELECT severity, COUNT(*) as count
                FROM support_tickets
                WHERE created_at >= date('now', '-{period_days} days') {p_filter}
                GROUP BY severity
            """)
            previous = _query(f"""
                SELECT severity, COUNT(*) as count
                FROM support_tickets
                WHERE created_at >= date('now', '-{period_days * 2} days')
                  AND created_at < date('now', '-{period_days} days') {p_filter}
                GROUP BY severity
            """)
            curr_map = {r["severity"]: r["count"] for r in current}
            prev_map = {r["severity"]: r["count"] for r in previous}
            severities = ["low", "medium", "high", "critical"]
            breakdown = []
            for sev in severities:
                c = curr_map.get(sev, 0)
                p = prev_map.get(sev, 0)
                pct = _pct_change(c, p)
                breakdown.append({
                    "severity": sev,
                    "current": c,
                    "previous": p,
                    "change_pct": pct,
                    "significance": _significance_flag(pct),
                })
            return json.dumps({
                "compare_type": compare_type,
                "period_days": period_days,
                "product": product_a or "all",
                "breakdown": breakdown,
            })

        else:
            return json.dumps({"error": f"Unknown compare_type '{compare_type}'."})

    except Exception as e:
        return json.dumps({"error": f"Comparison error: {str(e)}"})
