# AIONO — Product Requirements Document (PRD)

**Version:** 1.0.0
**Status:** Production-ready MVP

---

## Problem Statement

Business operations teams have data spread across multiple systems — sales, support tickets, HR, expenses, and internal documents. When something goes wrong (complaint spike, revenue decline, attrition surge), managers spend days manually correlating data across dashboards and asking engineers to write ad-hoc SQL queries.

**Core problem:** There is no single tool that can take a natural-language business question, autonomously gather evidence from multiple data sources, and return a traceable, evidence-backed root cause explanation.

---

## Solution

AIONO is an AI-powered Business Operations Investigator. It accepts natural-language questions from business analysts and managers, runs a multi-step agentic investigation across structured data and unstructured documents, and returns a complete root cause report with supporting evidence.

---

## Target Users

| User | Role | Needs |
|---|---|---|
| Business Manager | Asks questions | Fast answers with evidence, no SQL knowledge required |
| Business Analyst | Runs investigations | Deep data access, full trace, recommendations |
| Admin | Manages platform | See all investigations, manage users |
| Viewer | Read-only stakeholder | Browse investigation reports |

---

## Core User Stories

### Investigation

1. As an analyst, I want to type a business question and have the system automatically investigate it across all data sources, so I get an answer in minutes instead of days.

2. As a manager, I want to see exactly which data sources and documents were used to reach a conclusion, so I can trust the result before taking action.

3. As a user, I want the agent to flag when it doesn't have enough evidence to be confident, so I know when to involve a domain expert.

4. As an analyst, I want to see step-by-step agent progress in real time, so I understand what the AI is doing.

### Dashboard

5. As a manager, I want to see key business metrics on the dashboard — ticket volume, revenue trends, top complaint categories — so I can spot anomalies before they escalate.

### History

6. As an analyst, I want a searchable history of all past investigations with their status, tokens used, and latency, so I can reference past findings and track AI usage.

### Data Explorer

7. As an analyst, I want to browse the database schema and see sample rows, so I understand what data is available for investigations.

### Auth

8. As an admin, I want role-based access control so viewers can read reports but cannot run new investigations.

---

## Functional Requirements

### Agent Requirements

- [ ] Agent must produce a plan before executing any tool calls
- [ ] Agent must call at least 2 different tools per investigation
- [ ] Every evidence item must reference its source (table name or document title)
- [ ] Agent must output confidence level: high / medium / low
- [ ] Agent must flag `needs_human_review: true` when evidence is insufficient
- [ ] Agent must provide at least 3 recommended actions
- [ ] All LLM calls must have deterministic fallbacks
- [ ] Total tokens per investigation should stay under 2000 to preserve free Groq quota

### API Requirements

- [ ] `POST /api/investigations` returns immediately with an ID (async processing)
- [ ] `GET /api/investigations/{id}` returns current status and full report when done
- [ ] Authentication required on all investigation endpoints
- [ ] Viewers blocked from running investigations (403)
- [ ] Analysts can only access their own investigations
- [ ] Admins can access all investigations

### Frontend Requirements

- [ ] Investigation results page must poll every 3 seconds when status is "running"
- [ ] Each agent stage must be visible in the trace timeline
- [ ] Evidence items must be expandable to show raw supporting data
- [ ] Human review flag must be displayed prominently
- [ ] Dashboard must show 4 KPI cards, a trend line chart, and a category pie chart
- [ ] History page must support search by question text and filter by status

---

## Non-Functional Requirements

| Requirement | Target |
|---|---|
| Investigation latency (Groq) | < 30 seconds end-to-end |
| API response time (non-agent) | < 200ms |
| Token usage per investigation | < 2000 tokens |
| Authentication | JWT, 60-min expiry |
| Data security | bcrypt passwords, env-based secrets |
| Error handling | Fallbacks at every agent stage, no raw errors exposed to UI |

---

## Example Investigation Flow

**Question:** "Why did customer complaints increase by 23% this month?"

**Agent execution:**

1. Planner creates: "Query support_tickets for spike analysis. Search release notes for recent deployments. Compare month-over-month."
2. Researcher calls `analytics_tool` (complaint_spike_analysis) → finds login category spiked 78%
3. Researcher calls `document_search_tool` ("authentication Product X login") → finds v2.3.0 release notes and INC-2024-089 incident report
4. Analyst notes: "Login complaints spiked 78% after v2.3.0 OAuth 2.0 PKCE migration"
5. Evidence Checker builds: 2 evidence items with high confidence
6. Root Cause: "The complaint surge is driven by login failures in Product X caused by OAuth 2.0 PKCE migration in v2.3.0 rejecting legacy browser sessions."
7. Recommendations: deploy hotfix, add monitoring, update triage playbooks

**Output confidence:** High (2+ high-confidence evidence items)

---

## Out of Scope (MVP)

- Real-time data ingestion / connectors to external systems
- Email or Slack notifications when investigations complete
- Multi-user collaboration on investigations
- LLM provider switching (locked to Groq)
- Mobile application
- Investigation sharing via public link

---

## Business Value

This project demonstrates measurable value in an engineering interview context:

1. **Problem clarity** — solves a real pain point for operations teams
2. **Agentic architecture** — shows LangGraph multi-step reasoning, tool calling, state management
3. **RAG** — semantic document search with FAISS + Sentence Transformers
4. **Production patterns** — async processing, role-based auth, audit trail, structured logging
5. **Evidence traceability** — AI conclusions are never opaque; every claim has a source
6. **Full-stack delivery** — database design through to polished frontend
