"""
SQL Query Tool – executes safe, read-only queries against the SQLite database.
The agent calls this to retrieve raw data from sales, support, HR, and expenses tables.
"""

import sqlite3
import json
import re
from typing import Any
from langchain_core.tools import tool
from app.config import settings

# Tables and columns the agent is allowed to touch (allowlist for safety)
ALLOWED_TABLES = {
    "sales", "support_tickets", "employees", "expenses", "documents"
}

# Patterns that indicate write operations – always blocked
WRITE_PATTERNS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|MERGE)\b",
    re.IGNORECASE,
)


def _get_db_path() -> str:
    url = settings.DATABASE_URL
    # sqlite+aiosqlite:///./aiono.db  →  ./aiono.db
    return url.replace("sqlite+aiosqlite:///", "")


def _validate_query(query: str) -> None:
    """Raise ValueError if the query looks dangerous."""
    if WRITE_PATTERNS.search(query):
        raise ValueError("Only SELECT queries are permitted.")
    # Basic table allowlist check
    tables_used = re.findall(r"FROM\s+(\w+)|JOIN\s+(\w+)", query, re.IGNORECASE)
    for pair in tables_used:
        for tbl in pair:
            if tbl and tbl.lower() not in ALLOWED_TABLES:
                raise ValueError(f"Table '{tbl}' is not accessible.")


@tool
def sql_query_tool(query: str) -> str:
    """
    Execute a read-only SQL SELECT query against the business database.

    Available tables:
    - sales(id, product_name, product_category, customer_id, customer_region,
            amount, units_sold, sale_date, sales_rep, status)
    - support_tickets(id, ticket_id, customer_id, product_name, category,
                      severity, status, subject, description, created_at, resolved_at)
    - employees(id, name, department, role, team, hire_date, is_active,
                performance_score, attrition_risk, salary_band)
    - expenses(id, department, category, amount, description, expense_date, is_approved)
    - documents(id, title, doc_type, department, content, tags, author, published_at)

    Returns JSON with columns, rows, row_count, and the query executed.
    Returns an error message string on failure.

    Example:
        SELECT product_name, COUNT(*) as ticket_count
        FROM support_tickets
        WHERE created_at >= date('now', '-30 days')
        GROUP BY product_name
        ORDER BY ticket_count DESC
    """
    try:
        _validate_query(query)
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchmany(25)   # cap at 25 rows to optimize token usage
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        conn.close()

        result = {
            "query": query,
            "columns": columns,
            "rows": [dict(row) for row in rows],
            "row_count": len(rows),
        }
        return json.dumps(result, default=str)

    except ValueError as ve:
        return json.dumps({"error": str(ve), "query": query})
    except sqlite3.Error as e:
        return json.dumps({"error": f"Database error: {str(e)}", "query": query})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}", "query": query})
