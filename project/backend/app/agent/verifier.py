"""
AIONO Verification Agent
========================
Checks that every critical system component is actually working —
not just imported, but genuinely functional.

Stages:
  1. Database connectivity + seed data presence
  2. All 5 agent tools produce valid output
  3. LLM connectivity (Groq API)
  4. Full agent run (end-to-end investigation)
  5. Auth flow (token creation + verification)
  6. Analytics endpoints (dashboard metrics query)

Run with:
    python -m app.agent.verifier
"""

import asyncio
import json
import time
import sys
import os

# ── colour helpers ────────────────────────────────────────────

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg: str):   print(f"  {GREEN}✓{RESET}  {msg}")
def fail(msg: str): print(f"  {RED}✗{RESET}  {msg}")
def warn(msg: str): print(f"  {YELLOW}⚠{RESET}  {msg}")
def header(msg: str): print(f"\n{BOLD}{CYAN}── {msg} {RESET}")


# ── Stage 1: Database ─────────────────────────────────────────

async def check_database() -> dict:
    header("Stage 1 / Database")
    results = {}

    try:
        from app.database import check_db_health, AsyncSessionLocal
        healthy = await check_db_health()
        if healthy:
            ok("DB connection healthy")
            results["db_connection"] = True
        else:
            fail("DB connection failed")
            results["db_connection"] = False
            return results
    except Exception as e:
        fail(f"DB import error: {e}")
        results["db_connection"] = False
        return results

    # Check seed data
    import sqlite3
    from app.config import settings
    db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        counts = {}
        for table in ["users", "sales", "support_tickets", "employees", "expenses", "documents"]:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cur.fetchone()[0]
        conn.close()

        all_seeded = all(v > 0 for v in counts.values())
        if all_seeded:
            ok(f"Seed data present: {counts}")
            results["seed_data"] = True
        else:
            empty = [k for k, v in counts.items() if v == 0]
            fail(f"Empty tables found: {empty}")
            results["seed_data"] = False
    except Exception as e:
        fail(f"Seed check error: {e}")
        results["seed_data"] = False

    return results


# ── Stage 2: Tools ────────────────────────────────────────────

def check_tools() -> dict:
    header("Stage 2 / Agent Tools")
    results = {}

    # sql_query_tool
    try:
        from app.tools.sql_query import sql_query_tool
        res = sql_query_tool.invoke({"query": "SELECT COUNT(*) as total FROM support_tickets"})
        data = json.loads(res)
        if "error" not in data and data.get("rows"):
            ok(f"sql_query_tool → {data['rows'][0]}")
            results["sql_query_tool"] = True
        else:
            fail(f"sql_query_tool returned error: {data.get('error')}")
            results["sql_query_tool"] = False
    except Exception as e:
        fail(f"sql_query_tool exception: {e}")
        results["sql_query_tool"] = False

    # analytics_tool
    try:
        from app.tools.analytics import analytics_tool
        res = analytics_tool.invoke({"metric": "complaint_spike_analysis", "period_days": 30})
        data = json.loads(res)
        if "error" not in data and "data" in data:
            ok(f"analytics_tool → {len(data['data'])} categories returned")
            results["analytics_tool"] = True
        else:
            fail(f"analytics_tool error: {data.get('error')}")
            results["analytics_tool"] = False
    except Exception as e:
        fail(f"analytics_tool exception: {e}")
        results["analytics_tool"] = False

    # document_search_tool
    try:
        from app.tools.document_search import document_search_tool
        res = document_search_tool.invoke({"query": "authentication Product X login", "top_k": 2})
        data = json.loads(res)
        if "error" not in data and isinstance(data.get("results"), list):
            ok(f"document_search_tool → {len(data['results'])} docs found ({data.get('search_type')})")
            results["document_search_tool"] = True
        else:
            fail(f"document_search_tool error: {data.get('error')}")
            results["document_search_tool"] = False
    except Exception as e:
        fail(f"document_search_tool exception: {e}")
        results["document_search_tool"] = False

    # data_comparison_tool
    try:
        from app.tools.data_comparison import data_comparison_tool
        res = data_comparison_tool.invoke({"compare_type": "month_over_month_tickets", "period_days": 30})
        data = json.loads(res)
        if "error" not in data and "summary" in data:
            ok(f"data_comparison_tool → change: {data['summary'].get('total_change_pct')}%")
            results["data_comparison_tool"] = True
        else:
            fail(f"data_comparison_tool error: {data.get('error')}")
            results["data_comparison_tool"] = False
    except Exception as e:
        fail(f"data_comparison_tool exception: {e}")
        results["data_comparison_tool"] = False

    # report_generator_tool
    try:
        from app.tools.report_generator import report_generator_tool
        res = report_generator_tool.invoke({
            "question": "Test question",
            "root_cause": "Test root cause",
            "evidence": [{"claim": "Test claim", "source": "test", "data": "x", "confidence": "high"}],
            "recommendations": ["Action 1"],
            "confidence": "high",
            "needs_human_review": False,
        })
        data = json.loads(res)
        if "error" not in data and data.get("root_cause"):
            ok(f"report_generator_tool → report with {data['evidence_count']} evidence item(s)")
            results["report_generator_tool"] = True
        else:
            fail(f"report_generator_tool error: {data.get('error')}")
            results["report_generator_tool"] = False
    except Exception as e:
        fail(f"report_generator_tool exception: {e}")
        results["report_generator_tool"] = False

    return results


# ── Stage 3: LLM ─────────────────────────────────────────────

def check_llm() -> dict:
    header("Stage 3 / LLM (Groq API)")
    results = {}

    try:
        from app.config import settings
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            max_tokens=30,
            temperature=0,
        )
        resp = llm.invoke([
            SystemMessage(content="Reply with exactly: OK"),
            HumanMessage(content="Are you working?"),
        ])
        if resp.content:
            tokens = resp.usage_metadata.get("total_tokens", 0) if resp.usage_metadata else "?"
            ok(f"LLM responded: '{resp.content.strip()}' | tokens: {tokens}")
            results["llm_call"] = True
            results["model"] = settings.GROQ_MODEL
        else:
            fail("LLM returned empty response")
            results["llm_call"] = False
    except Exception as e:
        fail(f"LLM call failed: {e}")
        results["llm_call"] = False

    return results


# ── Stage 4: Full Agent Run ───────────────────────────────────

async def check_agent() -> dict:
    header("Stage 4 / Full Agent End-to-End")
    results = {}

    try:
        from app.agent.workflow import run_investigation

        start = time.time()
        result = await run_investigation(
            question="Why did customer complaints increase this month?",
            user_id=1
        )
        elapsed = round(time.time() - start, 2)

        if result["status"] == "completed":
            report = result.get("report", {})
            ok(f"Agent completed in {elapsed}s")
            ok(f"Confidence: {result.get('confidence')}")
            ok(f"Tokens used: {result.get('tokens_used')}")
            ok(f"Evidence items: {report.get('evidence_count', 0)}")
            ok(f"Recommendations: {len(report.get('recommendations', []))}")
            ok(f"Root cause preview: {report.get('root_cause', '')[:80]}...")

            # Validate report structure
            required_keys = ["question", "root_cause", "evidence", "recommendations", "confidence"]
            missing = [k for k in required_keys if k not in report]
            if missing:
                warn(f"Report missing keys: {missing}")
                results["agent_report_complete"] = False
            else:
                ok("Report structure complete (all required keys present)")
                results["agent_report_complete"] = True

            results["agent_run"] = True
            results["agent_latency_s"] = elapsed
            results["agent_tokens"] = result.get("tokens_used", 0)
        else:
            fail(f"Agent status: {result['status']} | error: {result.get('error')}")
            results["agent_run"] = False

    except Exception as e:
        fail(f"Agent run exception: {e}")
        results["agent_run"] = False

    return results


# ── Stage 5: Auth ─────────────────────────────────────────────

def check_auth() -> dict:
    header("Stage 5 / Auth (JWT + bcrypt)")
    results = {}

    try:
        from app.auth.dependencies import hash_password, verify_password, create_access_token
        from jose import jwt
        from app.config import settings

        # bcrypt round-trip
        plain = "TestPass@999"
        hashed = hash_password(plain)
        valid = verify_password(plain, hashed)
        wrong = verify_password("WrongPass", hashed)

        if valid and not wrong:
            ok("bcrypt hash + verify working correctly")
            results["bcrypt"] = True
        else:
            fail(f"bcrypt issue: valid={valid}, wrong={wrong}")
            results["bcrypt"] = False

        # JWT round-trip
        token = create_access_token({"sub": "testuser", "role": "analyst"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("sub") == "testuser":
            ok(f"JWT create + decode working | algo: {settings.ALGORITHM}")
            results["jwt"] = True
        else:
            fail("JWT decode mismatch")
            results["jwt"] = False

    except Exception as e:
        fail(f"Auth check exception: {e}")
        results["bcrypt"] = False
        results["jwt"] = False

    return results


# ── Stage 6: Analytics ────────────────────────────────────────

def check_analytics() -> dict:
    header("Stage 6 / Analytics & Dashboard Queries")
    results = {}

    try:
        import sqlite3
        from app.config import settings

        db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Dashboard queries
        cur.execute("SELECT COUNT(*) as total FROM support_tickets WHERE created_at >= date('now', '-30 days')")
        tickets_30d = cur.fetchone()["total"]

        cur.execute("SELECT ROUND(SUM(amount),2) as total FROM sales WHERE sale_date >= date('now', '-30 days')")
        revenue_30d = cur.fetchone()["total"] or 0

        cur.execute("SELECT category, COUNT(*) as count FROM support_tickets GROUP BY category ORDER BY count DESC LIMIT 5")
        top_categories = cur.fetchall()

        cur.execute("SELECT COUNT(*) as total FROM employees WHERE is_active=1")
        active_employees = cur.fetchone()["total"]

        conn.close()

        ok(f"Tickets (30d): {tickets_30d}")
        ok(f"Revenue (30d): ${revenue_30d:,.2f}")
        ok(f"Top category: {dict(top_categories[0])['category'] if top_categories else 'none'}")
        ok(f"Active employees: {active_employees}")

        results["analytics_queries"] = True
    except Exception as e:
        fail(f"Analytics query exception: {e}")
        results["analytics_queries"] = False

    return results


# ── Summary ───────────────────────────────────────────────────

def print_summary(all_results: dict):
    print(f"\n{BOLD}{'─'*55}{RESET}")
    print(f"{BOLD}  AIONO Verification Summary{RESET}")
    print(f"{BOLD}{'─'*55}{RESET}")

    total = 0
    passed = 0

    for stage, checks in all_results.items():
        for key, val in checks.items():
            if isinstance(val, bool):
                total += 1
                status = f"{GREEN}PASS{RESET}" if val else f"{RED}FAIL{RESET}"
                label = f"{stage}.{key}"
                print(f"  {status}  {label}")
                if val:
                    passed += 1

    print(f"\n{BOLD}  Result: {passed}/{total} checks passed{RESET}")

    if passed == total:
        print(f"  {GREEN}{BOLD}All systems operational. AIONO is production-ready.{RESET}\n")
        return True
    else:
        failed = total - passed
        print(f"  {RED}{BOLD}{failed} check(s) failed. Review output above.{RESET}\n")
        return False


# ── Main ──────────────────────────────────────────────────────

async def run_all():
    print(f"\n{BOLD}{CYAN}{'═'*55}{RESET}")
    print(f"{BOLD}{CYAN}  AIONO — Verification Agent{RESET}")
    print(f"{BOLD}{CYAN}  Checking all system components...{RESET}")
    print(f"{BOLD}{CYAN}{'═'*55}{RESET}")

    all_results = {}

    all_results["database"]  = await check_database()
    all_results["tools"]     = check_tools()
    all_results["llm"]       = check_llm()
    all_results["agent"]     = await check_agent()
    all_results["auth"]      = check_auth()
    all_results["analytics"] = check_analytics()

    success = print_summary(all_results)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    # Add backend root to path so imports work
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)
    ))))
    asyncio.run(run_all())
