# AIONO — System Architecture

## Overview

AIONO is a full-stack agentic AI application. The frontend (Next.js) talks to a FastAPI backend over REST. The backend runs a LangGraph multi-stage agent that orchestrates tool calls across a SQLite database and a FAISS document index to answer business questions with evidence-backed root cause reports.

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           USER (Browser)                                 │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ HTTPS / REST
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND — Next.js 14                             │
│                                                                          │
│   /                Dashboard (KPIs, charts, recent investigations)       │
│   /investigate      Question input form                                  │
│   /investigate/[id] Live investigation result + agent trace              │
│   /history          Full investigation history + search/filter           │
│   /data             Data Explorer (schema browser + sample rows)         │
│                                                                          │
│   Auth: JWT stored in localStorage, attached via Axios interceptor       │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ REST API (port 8000)
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       BACKEND — FastAPI + Uvicorn                        │
│                                                                          │
│   /api/auth/login              JWT login                                 │
│   /api/auth/register           New account creation                      │
│   /api/auth/me                 Current user profile                      │
│   POST /api/investigations     Submit investigation (async)              │
│   GET  /api/investigations/{id} Poll result + trace                      │
│   GET  /api/investigations     List history                              │
│   DELETE /api/investigations/{id} Delete log                             │
│   GET /api/analytics/dashboard Dashboard KPI metrics                     │
│   GET /api/analytics/schema   DB schema + sample rows                    │
│   GET /health                 Health check                               │
│                                                                          │
│   Middleware: CORS, request logging (structlog), global error handler    │
│   Auth: OAuth2PasswordBearer, JWT decode, role-based access              │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                    ┌────────────┴─────────────┐
                    │                          │
                    ▼                          ▼
     ┌─────────────────────────┐   ┌───────────────────────────┐
     │  LangGraph Agent        │   │  SQLite Database          │
     │  (6-stage workflow)     │   │  (aiosqlite + SQLAlchemy) │
     │                         │   │                           │
     │  1. Planner             │   │  users                    │
     │  2. Researcher          │   │  sales                    │
     │  3. Analyst             │   │  support_tickets          │
     │  4. Evidence Checker    │   │  employees                │
     │  5. Root Cause          │   │  expenses                 │
     │  6. Report Generator    │   │  documents                │
     │                         │   │  investigation_logs       │
     └───────────┬─────────────┘   └───────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
 ┌──────────────┐   ┌──────────────────┐
 │ Groq LLM    │   │ Tool Layer       │
 │ (qwen/qwen3 │   │                  │
 │  .8-27b)    │   │ sql_query_tool   │
 └──────────────┘   │ analytics_tool  │
                    │ doc_search_tool │  ←── FAISS + Sentence Transformers
                    │ comparison_tool │
                    │ report_tool     │
                    └─────────────────┘
```

---

## Agent Workflow — Detailed

```
User Question
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1: PLANNER                                               │
│  Input:  raw question                                           │
│  Action: LLM creates 3-bullet investigation plan               │
│  Output: plan string (tables to query, documents to search)    │
│  Tokens: ~256 max                                               │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 2: RESEARCHER                                            │
│  Input:  question + plan                                        │
│  Action: LLM selects 1-2 tools, executes them                  │
│          + deterministic safety-net for key metrics             │
│  Tools:  analytics_tool, sql_query_tool,                        │
│          document_search_tool, data_comparison_tool             │
│  Output: research_data list with raw tool results               │
│  Tokens: ~512 max                                               │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 3: ANALYST                                               │
│  Input:  question + research_data (compacted to ~1500 chars)   │
│  Action: LLM identifies patterns, % spikes, correlated events  │
│  Output: analysis_notes (max 120 words)                         │
│  Tokens: ~512 max                                               │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 4: EVIDENCE CHECKER                                      │
│  Input:  research_data (deterministic parsing, no LLM)         │
│  Action: Builds structured evidence list from tool outputs      │
│          Each item: claim + source + data + confidence          │
│  Output: evidence list, confidence score, needs_human_review   │
│  Tokens: 0 (no LLM call)                                        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 5: ROOT CAUSE                                            │
│  Input:  evidence + analysis_notes                              │
│  Action: LLM returns JSON {root_cause, recommendations}        │
│          Falls back to deterministic output if LLM fails        │
│  Output: root_cause string, recommendations list               │
│  Tokens: ~384 max                                               │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 6: REPORT GENERATOR (deterministic, no LLM)             │
│  Input:  all state fields                                       │
│  Action: Structures data into final JSON report                 │
│  Output: {question, root_cause, evidence, recommendations,     │
│           confidence, needs_human_review, evidence_quality}    │
│  Tokens: 0                                                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                    Persisted to investigation_logs
                    Frontend polls /api/investigations/{id}
```

---

## Database Schema

```
users
  id, username, email, hashed_password, role, is_active, created_at, updated_at

sales
  id, product_name, product_category, customer_id, customer_region,
  amount, units_sold, sale_date, sales_rep, status, created_at
  Index: (sale_date, product_name), (product_category, sale_date)

support_tickets
  id, ticket_id, customer_id, product_name, category, severity, status,
  subject, description, resolution, created_at, resolved_at, agent_name
  Index: (product_name, created_at), (category, created_at)

employees
  id, name, department, role, team, hire_date, is_active,
  performance_score, attrition_risk, salary_band, created_at

expenses
  id, department, category, amount, description, approved_by,
  expense_date, is_approved, created_at
  Index: (department, expense_date)

documents
  id, title, doc_type, department, content, tags, author, published_at, created_at

investigation_logs
  id, user_id (FK → users), question, status, agent_trace (JSON),
  final_report (JSON), tokens_used, latency_ms, error_message,
  created_at, completed_at
  Index: (user_id, created_at)
```

---

## Authentication & Authorization

- Passwords hashed with bcrypt
- JWT tokens (HS256), 60-minute expiry
- Role-based access: `admin` | `analyst` | `viewer`
- OAuth2PasswordBearer scheme
- Token attached via Axios request interceptor
- Auto-redirect to `/login` on 401

---

## Token Optimization Strategy

Total LLM calls per investigation: **3** (Planner, Analyst, Root Cause)

| Stage | Max tokens | LLM call |
|---|---|---|
| Planner | 256 | Yes |
| Researcher | 512 | Yes (tool routing only) |
| Analyst | 512 | Yes |
| Evidence Checker | 0 | No — deterministic |
| Root Cause | 384 | Yes |
| Report Generator | 0 | No — deterministic |

Research data compacted to ≤1500 chars before LLM. Evidence limited to ≤800 chars. Deterministic fallbacks at every stage.

---

## Security Measures

1. SQL injection prevention — allowlist of tables + regex blocking write patterns
2. JWT secret via environment variable
3. Password hashing with bcrypt + random salt
4. Role-based route guards (viewer cannot run investigations)
5. User isolation — analysts can only see their own investigations
6. Input validation — question length: 10–500 chars
7. CORS configured for specific origin only
8. Global error handler — never exposes internal error details
