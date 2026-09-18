"""
Analytics Tool – computes statistical summaries and trend metrics.
Uses Python/numpy on top of raw DB data, keeping LLM calls focused on reasoning.
"""

import sqlite3
import json
from typing import Optional
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


@tool
def analytics_tool(metric: str, period_days: int = 30, product: Optional[str] = None) -> str:
    """
    Compute business analytics and trend metrics.

    Available metrics:
    - "ticket_volume_trend"     : Daily support ticket counts over the period
    - "ticket_category_breakdown": Ticket counts grouped by category
    - "revenue_trend"           : Daily revenue over the period
    - "product_revenue_summary" : Revenue totals and average per product
    - "complaint_spike_analysis": Compare recent vs previous period ticket volume
    - "top_complaint_categories": Top N complaint categories with % share
    - "employee_attrition_summary": Attrition risk distribution by department

    Args:
        metric: One of the metric names listed above.
        period_days: Number of days to look back (default 30).
        product: Optional product name filter (e.g. "Product X").

    Returns JSON with computed analytics data and interpretation hints.
    """
    try:
        product_filter = f"AND product_name = '{product}'" if product else ""

        if metric == "ticket_volume_trend":
            rows = _query(f"""
                SELECT date(created_at) as day, COUNT(*) as count
                FROM support_tickets
                WHERE created_at >= date('now', '-{period_days} days')
                {product_filter}
                GROUP BY date(created_at)
                ORDER BY day
            """)
            return json.dumps({"metric": metric, "period_days": period_days,
                               "product": product, "data": rows,
                               "insight": f"Ticket volume trend over last {period_days} days."})

        elif metric == "ticket_category_breakdown":
            rows = _query(f"""
                SELECT category,
                       COUNT(*) as count,
                       ROUND(COUNT(*) * 100.0 / (
                           SELECT COUNT(*) FROM support_tickets
                           WHERE created_at >= date('now', '-{period_days} days')
                           {product_filter}
                       ), 1) as pct
                FROM support_tickets
                WHERE created_at >= date('now', '-{period_days} days')
                {product_filter}
                GROUP BY category
                ORDER BY count DESC
            """)
            return json.dumps({"metric": metric, "period_days": period_days,
                               "product": product, "data": rows,
                               "insight": "Breakdown of complaint categories."})

        elif metric == "revenue_trend":
            rows = _query(f"""
                SELECT date(sale_date) as day,
                       ROUND(SUM(amount), 2) as revenue,
                       COUNT(*) as transactions
                FROM sales
                WHERE sale_date >= date('now', '-{period_days} days')
                {product_filter.replace('product_name', 'product_name')}
                GROUP BY date(sale_date)
                ORDER BY day
            """)
            return json.dumps({"metric": metric, "period_days": period_days,
                               "data": rows,
                               "insight": f"Daily revenue trend over last {period_days} days."})

        elif metric == "product_revenue_summary":
            rows = _query(f"""
                SELECT product_name,
                       ROUND(SUM(amount), 2) as total_revenue,
                       ROUND(AVG(amount), 2) as avg_deal_size,
                       COUNT(*) as transactions
                FROM sales
                WHERE sale_date >= date('now', '-{period_days} days')
                GROUP BY product_name
                ORDER BY total_revenue DESC
            """)
            return json.dumps({"metric": metric, "period_days": period_days,
                               "data": rows,
                               "insight": "Revenue summary per product."})

        elif metric == "complaint_spike_analysis":
            # Compare tickets in last N days vs previous N days
            recent = _query(f"""
                SELECT category, COUNT(*) as recent_count
                FROM support_tickets
                WHERE created_at >= date('now', '-{period_days} days')
                {product_filter}
                GROUP BY category
            """)
            prev = _query(f"""
                SELECT category, COUNT(*) as prev_count
                FROM support_tickets
                WHERE created_at >= date('now', '-{period_days * 2} days')
                  AND created_at < date('now', '-{period_days} days')
                {product_filter}
                GROUP BY category
            """)
            recent_map = {r["category"]: r["recent_count"] for r in recent}
            prev_map = {r["category"]: r["prev_count"] for r in prev}
            all_cats = set(list(recent_map.keys()) + list(prev_map.keys()))
            comparison = []
            for cat in all_cats:
                r = recent_map.get(cat, 0)
                p = prev_map.get(cat, 0)
                change = round(((r - p) / p * 100) if p > 0 else 100.0, 1)
                comparison.append({
                    "category": cat,
                    "recent_count": r,
                    "prev_count": p,
                    "change_pct": change,
                })
            comparison.sort(key=lambda x: x["change_pct"], reverse=True)
            return json.dumps({"metric": metric, "period_days": period_days,
                               "product": product, "data": comparison,
                               "insight": "Spike analysis: recent vs previous period."})

        elif metric == "top_complaint_categories":
            rows = _query(f"""
                SELECT category, COUNT(*) as count
                FROM support_tickets
                WHERE created_at >= date('now', '-{period_days} days')
                {product_filter}
                GROUP BY category
                ORDER BY count DESC
                LIMIT 5
            """)
            total = sum(r["count"] for r in rows)
            for r in rows:
                r["pct"] = round(r["count"] / total * 100, 1) if total else 0
            return json.dumps({"metric": metric, "data": rows,
                               "total_tickets": total,
                               "insight": "Top complaint categories by volume."})

        elif metric == "employee_attrition_summary":
            rows = _query("""
                SELECT department,
                       SUM(CASE WHEN attrition_risk='high' THEN 1 ELSE 0 END) as high_risk,
                       SUM(CASE WHEN attrition_risk='medium' THEN 1 ELSE 0 END) as medium_risk,
                       COUNT(*) as total
                FROM employees
                WHERE is_active = 1
                GROUP BY department
                ORDER BY high_risk DESC
            """)
            return json.dumps({"metric": metric, "data": rows,
                               "insight": "Employee attrition risk by department."})

        else:
            return json.dumps({"error": f"Unknown metric '{metric}'. "
                                        f"Choose from: ticket_volume_trend, ticket_category_breakdown, "
                                        f"revenue_trend, product_revenue_summary, complaint_spike_analysis, "
                                        f"top_complaint_categories, employee_attrition_summary."})

    except Exception as e:
        return json.dumps({"error": f"Analytics error: {str(e)}", "metric": metric})
