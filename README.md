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

## 🌐 Live Deployment

| Service | URL |
|:---|:---|
| **Frontend** | [https://aiono-frontend.vercel.app](https://aiono-frontend.vercel.app) |
| **Backend API** | [https://aiono-backend.onrender.com](https://aiono-backend.onrender.com) |
| **API Docs** | [https://aiono-backend.onrender.com/docs](https://aiono-backend.onrender.com/docs) |

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
| **AI / Agent** | LangGraph, LangChain, Groq LLM |
| **RAG** | TF-IDF semantic search (lightweight, production-ready) |
| **Database** | SQLite with SQLAlchemy async ORM (aiosqlite) |
| **Auth** | JWT (python-jose), bcrypt password hashing |
| **Logging** | structlog (structured JSON logs) |
| **Charts** | Recharts |

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

---

## Getting Started

### Backend

```bash
cd project/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add GROQ_API_KEY
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd project/frontend
npm install
npm run dev
```

---

## Demo Accounts

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@123` |
| Analyst | `analyst` | `Analyst@123` |
| Viewer | `viewer` | `Viewer@123` |

---

## Sample Questions

- *"Why did customer complaints increase by 23% this month?"*
- *"What is causing the decline in Product X revenue in Q3?"*
- *"Which department has the highest attrition risk right now?"*
- *"Are infrastructure costs above budget this quarter?"*
- *"What products are generating the most support tickets?"*

---

## Key Features

- **Agentic workflow** with 6 reasoning stages visible in real time
- **Evidence traceability** — every conclusion links to its source
- **RAG over internal documents** — release notes, incident reports, HR memos
- **Role-based access control** — admin / analyst / viewer
- **Confidence scoring** — high / medium / low with explanation
- **Async background processing** — submit and poll pattern
- **Full audit trail** — token usage, latency, tool call history

---

## License

MIT License — built for engineering internship demonstration purposes.

Full project docs: [`project/README.md`](./project/README.md)
