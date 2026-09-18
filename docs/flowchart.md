# AIONO — System Flowcharts

## 1. Full Agent Investigation Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER submits question                            │
│        "Why did customer complaints increase by 23% this month?"        │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │  POST /api/investigations
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FastAPI Background Task                              │
│                  investigation_id returned immediately                  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
        ╔═══════════════════════════════════════════════╗
        ║           LANGGRAPH AGENT PIPELINE            ║
        ╠═══════════════════════════════════════════════╣
        ║                                               ║
        ║  ┌─────────────────────────────────────────┐  ║
        ║  │  STAGE 1: PLANNER                       │  ║
        ║  │  LLM creates 3-bullet investigation     │  ║
        ║  │  plan. Identifies tables & docs to      │  ║
        ║  │  check. Max 256 tokens.                 │  ║
        ║  └──────────────────┬──────────────────────┘  ║
        ║                     │                         ║
        ║                     ▼                         ║
        ║  ┌─────────────────────────────────────────┐  ║
        ║  │  STAGE 2: RESEARCHER                    │  ║
        ║  │  LLM picks 1-2 tools → executes them   │  ║
        ║  │  + deterministic safety-net queries     │  ║
        ║  │                                         │  ║
        ║  │  ┌──────────────┐  ┌─────────────────┐  │  ║
        ║  │  │ sql_query    │  │ analytics_tool  │  │  ║
        ║  │  │ _tool        │  │                 │  │  ║
        ║  │  └──────────────┘  └─────────────────┘  │  ║
        ║  │  ┌──────────────┐  ┌─────────────────┐  │  ║
        ║  │  │ document_    │  │ data_comparison │  │  ║
        ║  │  │ search_tool  │  │ _tool           │  │  ║
        ║  │  └──────────────┘  └─────────────────┘  │  ║
        ║  └──────────────────┬──────────────────────┘  ║
        ║                     │                         ║
        ║                     ▼                         ║
        ║  ┌─────────────────────────────────────────┐  ║
        ║  │  STAGE 3: ANALYST                       │  ║
        ║  │  LLM identifies patterns, % spikes,     │  ║
        ║  │  correlated events. Max 512 tokens.     │  ║
        ║  └──────────────────┬──────────────────────┘  ║
        ║                     │                         ║
        ║                     ▼                         ║
        ║  ┌─────────────────────────────────────────┐  ║
        ║  │  STAGE 4: EVIDENCE CHECKER              │  ║
        ║  │  Deterministic — no LLM.                │  ║
        ║  │  Builds evidence list with sources.     │  ║
        ║  │                                         │  ║
        ║  │  Evidence ≥ 2?                          │  ║
        ║  │    YES → confidence=high                │  ║
        ║  │    NO  → needs_human_review=true        │  ║
        ║  └──────────────────┬──────────────────────┘  ║
        ║                     │                         ║
        ║                     ▼                         ║
        ║  ┌─────────────────────────────────────────┐  ║
        ║  │  STAGE 5: ROOT CAUSE                    │  ║
        ║  │  LLM returns JSON:                      │  ║
        ║  │  { root_cause, recommendations }        │  ║
        ║  │  Deterministic fallback if LLM fails.   │  ║
        ║  └──────────────────┬──────────────────────┘  ║
        ║                     │                         ║
        ║                     ▼                         ║
        ║  ┌─────────────────────────────────────────┐  ║
        ║  │  STAGE 6: REPORT GENERATOR              │  ║
        ║  │  Deterministic — no LLM.                │  ║
        ║  │  Assembles final structured JSON report │  ║
        ║  └──────────────────┬──────────────────────┘  ║
        ║                     │                         ║
        ╚═════════════════════╪═════════════════════════╝
                              │
                              ▼
        ┌─────────────────────────────────────────────┐
        │         Saved to investigation_logs         │
        │   { report, tool_trace, tokens, latency }   │
        └──────────────────┬──────────────────────────┘
                           │
                           ▼
        ┌─────────────────────────────────────────────┐
        │     Frontend polls GET /investigations/{id} │
        │     every 3 seconds until status=completed  │
        └─────────────────────────────────────────────┘
```

---

## 2. Evidence Traceability Chain

```
  User sees: "Login complaints increased 78%"
       │
       ▼
  Evidence Item
  ┌─────────────────────────────────────────────────────┐
  │  claim:  "Login complaints up 78% vs prior period" │
  │  source: analytics_tool / support_tickets          │
  │  data:   { recent: 87, previous: 49 }              │
  │  confidence: HIGH                                  │
  └─────────────────────────────────────────────────────┘
       │
       ▼
  Backing query (sql_query_tool):
  SELECT category, COUNT(*) FROM support_tickets
  WHERE created_at >= date('now', '-30 days')
  GROUP BY category
       │
       ▼
  Document corroboration (document_search_tool):
  "Product X v2.3.0 Release Notes" → OAuth 2.0 migration
  "Incident Report INC-2024-089"   → Login failure root cause
```

---

## 3. Authentication Flow

```
  Browser                    FastAPI                   DB
     │                          │                       │
     │  POST /api/auth/login    │                       │
     │  { username, password }  │                       │
     │ ────────────────────────►│                       │
     │                          │  SELECT user WHERE    │
     │                          │  username=?           │
     │                          │ ─────────────────────►│
     │                          │       user row        │
     │                          │ ◄─────────────────────│
     │                          │                       │
     │                          │  bcrypt.verify()      │
     │                          │  JWT.encode()         │
     │                          │                       │
     │  { access_token, user }  │                       │
     │ ◄────────────────────────│                       │
     │                          │                       │
     │  Stores token in         │                       │
     │  localStorage            │                       │
     │                          │                       │
     │  GET /api/investigations │                       │
     │  Authorization: Bearer…  │                       │
     │ ────────────────────────►│                       │
     │                          │  JWT.decode()         │
     │                          │  role check           │
     │  { investigations }      │                       │
     │ ◄────────────────────────│                       │
```

---

## 4. Token Budget per Investigation

```
  Stage           LLM Call?   Max Tokens   Cumulative
  ─────────────────────────────────────────────────────
  Planner         YES         256          ~256
  Researcher      YES         512          ~768
  Analyst         YES         512          ~1280
  Evidence Check  NO  ──────  0            ~1280
  Root Cause      YES         384          ~1664
  Report          NO  ──────  0            ~1664
  ─────────────────────────────────────────────────────
  Total LLM calls: 4          Budget: < 2000 tokens ✓

  Cost optimization techniques:
  • Research data compacted to ≤1500 chars before LLM
  • Evidence snippets limited to ≤800 chars
  • 2 of 6 stages are fully deterministic (no LLM)
  • Deterministic fallbacks prevent retry token waste
```

---

## 5. Role-Based Access Control

```
  Request hits API
        │
        ▼
  JWT decoded → role extracted
        │
        ├── role = "viewer"
        │     ├── GET  investigations → ✓ own records only
        │     ├── POST investigations → ✗ 403 Forbidden
        │     └── DELETE             → ✗ 403 Forbidden
        │
        ├── role = "analyst"
        │     ├── GET  investigations → ✓ own records only
        │     ├── POST investigations → ✓ allowed
        │     └── DELETE             → ✓ own records only
        │
        └── role = "admin"
              ├── GET  investigations → ✓ ALL records
              ├── POST investigations → ✓ allowed
              └── DELETE             → ✓ ANY record
```
