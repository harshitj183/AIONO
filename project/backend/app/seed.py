"""
Seed script – populates the database with realistic mock business data.
Run once on first startup via: python -m app.seed
"""

import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal, init_db
from app.models import User, Sale, SupportTicket, Employee, Expense, Document
from app.auth.dependencies import hash_password

PRODUCTS = [
    ("Product X", "Software"),
    ("Product Y", "Analytics"),
    ("Product Z", "Infrastructure"),
    ("Service A", "Professional Services"),
    ("Service B", "Support Plans"),
]

REGIONS = ["North America", "Europe", "Asia Pacific", "India", "LATAM"]
DEPARTMENTS = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations"]
SUPPORT_CATEGORIES = ["login", "billing", "performance", "feature_request", "bug"]
SEVERITIES = ["low", "medium", "high", "critical"]


def days_ago(n: int) -> datetime:
    return datetime.utcnow() - timedelta(days=n)


def random_date(start_days_ago: int, end_days_ago: int) -> datetime:
    delta = random.randint(end_days_ago, start_days_ago)
    return days_ago(delta)


async def seed(session: AsyncSession) -> None:
    # ── Users ──────────────────────────────────────────────────────────────
    users = [
        User(
            username="admin",
            email="admin@aiono.ai",
            hashed_password=hash_password("Admin@123"),
            role="admin",
        ),
        User(
            username="analyst",
            email="analyst@aiono.ai",
            hashed_password=hash_password("Analyst@123"),
            role="analyst",
        ),
        User(
            username="viewer",
            email="viewer@aiono.ai",
            hashed_password=hash_password("Viewer@123"),
            role="viewer",
        ),
    ]
    session.add_all(users)

    # ── Sales ──────────────────────────────────────────────────────────────
    sales_reps = ["Alice Johnson", "Bob Martinez", "Carol White", "David Lee"]
    sales = []
    for i in range(350):
        product, category = random.choice(PRODUCTS)
        if product == "Product X" and i > 200:
            amount = random.uniform(500, 1200)
        else:
            amount = random.uniform(800, 8000)
        sales.append(Sale(
            product_name=product,
            product_category=category,
            customer_id=random.randint(1000, 9999),
            customer_region=random.choice(REGIONS),
            amount=round(amount, 2),
            units_sold=random.randint(1, 10),
            sale_date=random_date(90, 0),
            sales_rep=random.choice(sales_reps),
            status=random.choices(["completed", "refunded", "pending"], weights=[85, 10, 5])[0],
        ))
    session.add_all(sales)

    # ── Support Tickets ────────────────────────────────────────────────────
    tickets = []
    for i in range(400):
        is_recent = i > 250
        if is_recent:
            product = random.choices(
                [p[0] for p in PRODUCTS],
                weights=[60, 10, 10, 10, 10]
            )[0]
            category = random.choices(
                SUPPORT_CATEGORIES,
                weights=[55, 10, 15, 10, 10]
            )[0]
            severity = random.choices(SEVERITIES, weights=[10, 30, 40, 20])[0]
            created = random_date(30, 0)
        else:
            product = random.choice([p[0] for p in PRODUCTS])
            category = random.choice(SUPPORT_CATEGORIES)
            severity = random.choices(SEVERITIES, weights=[30, 40, 20, 10])[0]
            created = random_date(90, 31)

        ticket_num = f"TKT-{10000 + i}"
        subjects = {
            "login": "Unable to log in – authentication error",
            "billing": "Incorrect charge on invoice",
            "performance": "Dashboard loading very slowly",
            "feature_request": "Request for bulk export feature",
            "bug": "Data not saving after form submission",
        }
        tickets.append(SupportTicket(
            ticket_id=ticket_num,
            customer_id=random.randint(1000, 9999),
            product_name=product,
            category=category,
            severity=severity,
            status=random.choices(
                ["open", "in_progress", "resolved", "closed"],
                weights=[20, 25, 35, 20]
            )[0],
            subject=subjects.get(category, "General inquiry"),
            description=f"Customer reported issue with {category} on {product}. "
                        f"Severity: {severity}. Ticket #{ticket_num}.",
            created_at=created,
            resolved_at=created + timedelta(hours=random.randint(2, 72))
            if random.random() > 0.3 else None,
            agent_name=random.choice(["Support Team A", "Support Team B", "Support Team C"]),
        ))
    session.add_all(tickets)

    # ── Employees ──────────────────────────────────────────────────────────
    roles_map = {
        "Engineering": ["Software Engineer", "Senior Engineer", "Tech Lead", "QA Engineer"],
        "Sales": ["Sales Executive", "Account Manager", "Sales Manager"],
        "Marketing": ["Marketing Analyst", "Content Strategist", "Growth Manager"],
        "HR": ["HR Specialist", "Recruiter", "HR Manager"],
        "Finance": ["Financial Analyst", "Controller", "CFO"],
        "Operations": ["Operations Manager", "Business Analyst", "Project Manager"],
    }
    first_names = ["James", "Priya", "Chen", "Maria", "David", "Sara", "Raj", "Emma", "Omar", "Liu"]
    last_names = ["Kumar", "Smith", "Patel", "Johnson", "Wang", "Garcia", "Ali", "Brown", "Singh", "Lee"]
    employees = []
    for i in range(60):
        dept = random.choice(DEPARTMENTS)
        role = random.choice(roles_map[dept])
        employees.append(Employee(
            name=f"{random.choice(first_names)} {random.choice(last_names)}",
            department=dept,
            role=role,
            team=f"Team {random.choice(['Alpha', 'Beta', 'Gamma', 'Delta'])}",
            hire_date=random_date(1500, 30),
            is_active=random.random() > 0.08,
            performance_score=round(random.uniform(2.5, 5.0), 1),
            attrition_risk=random.choices(["low", "medium", "high"], weights=[60, 30, 10])[0],
            salary_band=random.choice(["L1", "L2", "L3", "L4", "L5"]),
        ))
    session.add_all(employees)

    # ── Expenses ──────────────────────────────────────────────────────────
    expense_categories = ["infrastructure", "marketing", "hr", "operations", "product_development"]
    approvers = ["CFO Office", "Department Head", "Finance Controller"]
    expenses = []
    for i in range(180):
        dept = random.choice(DEPARTMENTS)
        expenses.append(Expense(
            department=dept,
            category=random.choice(expense_categories),
            amount=round(random.uniform(500, 50000), 2),
            description=f"Q{random.randint(1,4)} {dept} operational expense",
            approved_by=random.choice(approvers),
            expense_date=random_date(90, 0),
            is_approved=random.random() > 0.05,
        ))
    session.add_all(expenses)

    # ── Documents (for RAG) ───────────────────────────────────────────────
    documents = [
        Document(
            title="Product X v2.3.0 Release Notes",
            doc_type="release_note",
            department="Engineering",
            content="""Product X version 2.3.0 was released on the 15th of last month.
Key changes:
- Migrated authentication service from OAuth 1.0 to OAuth 2.0 PKCE flow.
- Updated session token expiry from 24 hours to 2 hours for security compliance.
- New login UI redesign with multi-factor authentication prompts.
- Database connection pooling increased to handle higher concurrency.
- Known issue: Some users with saved browser sessions may face forced logout and re-authentication errors.
- Hotfix v2.3.1 is scheduled for next week to address session migration issues.
Engineering team has flagged this as a medium-priority regression.""",
            tags="product_x,release,authentication,login,regression",
            author="Engineering Team",
            published_at=days_ago(32),
        ),
        Document(
            title="Customer Support Escalation Policy",
            doc_type="policy",
            department="Operations",
            content="""Support Escalation Policy – Version 3.1.
All critical severity tickets must be escalated within 2 hours of creation.
High severity tickets require escalation within 8 hours.
If a product bug affects more than 50 customers, an incident report must be filed.
Support managers must notify the product team for any 20% spike in ticket volume for a single category within a 7-day window.
Post-incident reviews are mandatory for P1 and P2 incidents.""",
            tags="support,escalation,policy,sla",
            author="Operations Team",
            published_at=days_ago(120),
        ),
        Document(
            title="Q3 Sales Performance Review",
            doc_type="memo",
            department="Sales",
            content="""Q3 Sales Performance Summary:
Total revenue achieved: $2.4M against a target of $2.8M (85% attainment).
Product X contributed 42% of total revenue in Q2 but has seen a decline to 31% in Q3.
Major deals were lost in the Enterprise segment citing product stability concerns.
North America region showed strongest performance at 94% of quota.
Asia Pacific underperformed at 71% primarily due to delayed product localisation.
Sales leadership has raised concerns about Product X reliability impacting deal closures.""",
            tags="sales,q3,revenue,product_x,performance",
            author="Sales Director",
            published_at=days_ago(20),
        ),
        Document(
            title="Incident Report: Authentication Service Outage",
            doc_type="incident_report",
            department="Engineering",
            content="""Incident Report – INC-2024-089
Severity: P2 – High
Affected System: Authentication Service (Product X)
Duration: 4 hours 22 minutes
Root Cause: The OAuth 2.0 PKCE migration introduced an incompatibility with legacy browser sessions. When existing users attempted to log in after the v2.3.0 upgrade, old session tokens were rejected without a proper error message, causing silent authentication failures.
Impact: Approximately 1,200 users experienced login failures. 68% of new support tickets in this period were login-related.
Resolution: Temporary rollback of session validation to accept both old and new token formats.
Action Items:
1. Complete hotfix deployment within 5 business days.
2. Implement proper session migration for all active users.
3. Add monitoring alerts for authentication error rate spikes above 5%.""",
            tags="incident,authentication,product_x,outage,login",
            author="Engineering Lead",
            published_at=days_ago(28),
        ),
        Document(
            title="Q3 HR Attrition Analysis",
            doc_type="memo",
            department="HR",
            content="""HR Quarterly Attrition Report – Q3:
Total employee strength: 312. Voluntary exits: 18 (5.7% quarterly attrition).
Engineering department recorded the highest attrition at 8.2%, above the 5% threshold.
Primary reasons cited in exit interviews: workload pressure (44%), compensation (32%), career growth (24%).
Hiring pipeline has 23 open roles with an average time-to-fill of 67 days.
Recommendation: Conduct stay interviews with high-risk employees in Engineering.
Action: HR to partner with Engineering leadership on workload redistribution.""",
            tags="hr,attrition,engineering,hiring,retention",
            author="HR Manager",
            published_at=days_ago(15),
        ),
        Document(
            title="Infrastructure Cost Optimisation Initiative",
            doc_type="memo",
            department="Finance",
            content="""Infrastructure Cost Review – Finance Team:
Cloud infrastructure spend increased by 34% quarter-over-quarter, exceeding budget by $180,000.
Primary drivers: unoptimised database queries causing excessive read operations, over-provisioned staging environments running 24/7, and a 3x increase in data storage for Product X analytics.
Recommended actions:
1. Right-size staging environments to auto-scale during business hours only.
2. Archive analytics data older than 12 months to cold storage.
3. Implement query optimisation for the top 10 slow queries identified by the DBA team.
Target: 25% cost reduction within 60 days.""",
            tags="infrastructure,cost,finance,cloud,optimization",
            author="Finance Controller",
            published_at=days_ago(10),
        ),
        Document(
            title="Product Roadmap – Q4 Priorities",
            doc_type="policy",
            department="Engineering",
            content="""Product Roadmap Q4 Focus Areas:
1. Stability and reliability – address all P1/P2 open bugs before new feature work.
2. Authentication service hardening – complete OAuth 2.0 migration with full backward compatibility.
3. Performance improvements – target 40% reduction in dashboard load time.
4. Mobile app launch – iOS and Android beta by end of Q4.
5. API rate limiting and security hardening for enterprise customers.
Engineering velocity has been impacted by the authentication regression; two sprints have been dedicated to hotfix and stabilisation work.""",
            tags="roadmap,q4,product,authentication,performance,mobile",
            author="Product Manager",
            published_at=days_ago(5),
        ),
    ]
    session.add_all(documents)
    await session.commit()
    print("✅ Seed data inserted successfully.")
    print("   Default accounts:")
    print("   admin    / Admin@123")
    print("   analyst  / Analyst@123")
    print("   viewer   / Viewer@123")


async def main():
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed(session)


if __name__ == "__main__":
    asyncio.run(main())
