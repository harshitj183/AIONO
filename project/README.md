# AIONO — AI Business Operations Investigator

[![Live Demo](https://img.shields.io/badge/Live%20Demo-aiono--frontend.vercel.app-6366f1?style=for-the-badge&logo=vercel&logoColor=white)](https://aiono-frontend.vercel.app)
[![Backend API](https://img.shields.io/badge/Backend%20API-onrender.com-10b981?style=for-the-badge&logo=render&logoColor=white)](https://aiono-backend.onrender.com/docs)
[![GitHub](https://img.shields.io/badge/GitHub-harshitj183%2FAIONO-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/harshitj183/AIONO)

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20AI-6366f1?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-LLM-F55036?style=flat-square)](https://groq.com)

> Ask any business question. AIONO investigates your data, searches internal documents, and returns an evidence-backed root cause report — automatically.

| 🌐 Frontend | 🔌 Backend API | 📖 API Docs |
|:---:|:---:|:---:|
| [aiono-frontend.vercel.app](https://aiono-frontend.vercel.app) | [aiono-backend.onrender.com](https://aiono-backend.onrender.com) | [/docs](https://aiono-backend.onrender.com/docs) |

---

## What It Does

Most business dashboards just show numbers. AIONO goes further — it **investigates**.

When a manager asks *"Why did customer complaints increase by 23% this month?"*, AIONO:

1. Queries the support ticket database
2. Compares current vs. previous period metrics
3. Searches internal release notes, incident reports, and policy documents
4. Cross-correlates findings across all data sources
5. Identifies root cause with supporting evidence
6. Generates recommended actions — all traceable back to real data

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS |
| **Backend** | FastAPI (Python), Uvicorn ASGI |
| **AI / Agent** | LangGraph, LangChain, Groq LLM (qwen/qwen3.8-27b) |
| **RAG** | TF-IDF semantic search (lightweight, production-ready) |
| **Database** | SQLite with SQLAlchemy async ORM (aiosqlite) |
| **Auth** | JWT (python-jose), bcrypt password hashing |
| **Logging** | structlog (structured JSON logs) |
| **Charts** | Recharts |
| **Icons** | Lucide React |

---

## Project Structure

```
AIONO/
├── docs/                        # Architecture, PRD, flowcharts
│   ├── architecture.md
│   ├── prd.md
│   └── must will be.txt
├── project/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── agent/
│   │   │   │   └── workflow.py      # LangGraph 6-stage agent
│   │   │   ├── auth/
│   │   │   │   └── dependencies.py  # JWT + bcrypt
│   │   │   ├── routers/
│   │   │   │   ├── auth.py          # Login, register, /me
│   │   │   │   ├── investigations.py # Submit + poll investigations
│   │   │   │   └── analytics.py     # Dashboard + schema endpoints
│   │   │   ├── tools/
│   │   │   │   ├── sql_query.py         # Safe read-only SQL execution
│   │   │   │   ├── analytics.py         # Statistical trend computation
│   │   │   │   ├── document_search.py   # FAISS semantic + keyword search
│   │   │   │   ├── data_comparison.py   # Period-over-period delta analysis
│   │   │   │   └── report_generator.py  # Structured evidence report builder
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── models.py            # ORM: User, Sale, SupportTicket, Employee, Expense, Document, InvestigationLog
│   │   │   ├── main.py              # FastAPI app + middleware
│   │   │   └── seed.py              # Realistic mock data generator
│   │   ├── requirements.txt
│   │   └── .env.example
│   └── frontend/
│       └── src/
│           ├── app/
│           │   ├── page.tsx             # Dashboard with KPIs and charts
│           │   ├── investigate/page.tsx  # Submit investigation
│           │   ├── investigate/[id]/page.tsx # Investigation results + trace
│           │   ├── history/page.tsx      # Investigation history + search
│           │   └── data/page.tsx         # Data explorer (schema browser)
│           ├── components/
│           │   └── Sidebar.tsx
│           ├── hooks/
│           │   └── useAuth.tsx
│           └── lib/
│               └── api.ts               # Axios client with JWT interceptors
```

---

## Agent Workflow

The LangGraph agent runs 6 sequential stages:

```
Question
   ↓
[1] Planner     — creates a 3-bullet investigation plan
   ↓
[2] Researcher  — LLM-directed tool calls (SQL, analytics, documents, comparison)
   ↓
[3] Analyst     — identifies patterns, spikes, correlated events
   ↓
[4] Evidence Checker — builds structured evidence list with source traceability
   ↓
[5] Root Cause  — synthesises evidence into one-sentence root cause + recommendations
   ↓
[6] Report      — assembles final JSON report for the frontend
```

**Tools available to the agent:**

| Tool | Purpose |
|---|---|
| `sql_query_tool` | Safe SELECT-only queries on sales, tickets, HR, expenses tables |
| `analytics_tool` | Pre-computed trend metrics (spike analysis, category breakdown, attrition) |
| `document_search_tool` | FAISS semantic search over internal documents |
| `data_comparison_tool` | Period-over-period delta analysis with significance flags |
| `report_generator_tool` | Structured evidence report builder |

---

## Getting Started

### Backend

```bash
cd project/backend

# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your GROQ_API_KEY to .env

# Seed database with realistic mock data
python -m app.seed

# Start the server
uvicorn app.main:app --reload --port 8000
```

Backend runs at: **http://localhost:8000**
API docs at: **http://localhost:8000/docs**

### Frontend

```bash
cd project/frontend

npm install
npm run dev
```

Frontend runs at: **http://localhost:3000**

---

## Live Deployment

| Service | URL |
|---|---|
| **Frontend** | https://aiono-frontend.vercel.app |
| **Backend API** | https://aiono-backend.onrender.com |
| **API Docs** | https://aiono-backend.onrender.com/docs |

---

## Demo Accounts

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@123` |
| Analyst | `analyst` | `Analyst@123` |
| Viewer | `viewer` | `Viewer@123` |

Role permissions:
- **Admin** — can see and delete all investigations
- **Analyst** — can run investigations, see own history
- **Viewer** — read-only; cannot run investigations

---

## Sample Questions to Try

- *"Why did customer complaints increase by 23% this month?"*
- *"What is causing the decline in Product X revenue in Q3?"*
- *"Which department has the highest attrition risk right now?"*
- *"Are infrastructure costs above budget this quarter?"*
- *"What products are generating the most support tickets?"*

---

## Key Features

- **Agentic workflow** with 6 reasoning stages visible in real time
- **Evidence traceability** — every conclusion links to its source (table, document, query)
- **RAG over internal documents** — release notes, incident reports, HR memos
- **Role-based access control** — admin / analyst / viewer
- **Human-in-the-loop flag** when evidence is insufficient
- **Confidence scoring** — high / medium / low with explanation
- **Async background processing** — submit and poll pattern, no blocking
- **Full audit trail** — token usage, latency, tool call history per investigation
- **Data Explorer** — live schema browser with sample rows
- **Dashboard** — KPI cards, ticket trend charts, category breakdown

---

## Environment Variables

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
SECRET_KEY=your_jwt_secret_key
DATABASE_URL=sqlite+aiosqlite:///./aiono.db
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=http://localhost:3000
```

---

## Verification Agent

Run this to confirm every system component is genuinely working — not just imported, but functionally tested end-to-end:

```bash
cd project/backend
source .venv/bin/activate
python -m app.agent.verifier
```

Checks all 13 critical components across 6 stages:
- Database connectivity + seed data
- All 5 agent tools (SQL, analytics, RAG, comparison, report)
- Groq LLM API call
- Full agent run (2–3s end-to-end)
- JWT + bcrypt auth
- Analytics dashboard queries

---

## License

MIT License — built for engineering internship demonstration purposes.
