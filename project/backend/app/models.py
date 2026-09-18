"""
Database models using SQLAlchemy ORM.
Covers: Users, Sales, Support Tickets, HR, Expenses, Documents, Investigation Logs.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean,
    ForeignKey, Index, Enum as SAEnum
)
from sqlalchemy.orm import relationship, DeclarativeBase
import enum


class Base(DeclarativeBase):
    pass


# ──────────────────────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="analyst")   # admin | analyst | viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    investigations = relationship("InvestigationLog", back_populates="user")


# ──────────────────────────────────────────────────────────────
# Sales Data
# ──────────────────────────────────────────────────────────────

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(100), nullable=False)
    product_category = Column(String(50))
    customer_id = Column(Integer)
    customer_region = Column(String(50))
    amount = Column(Float, nullable=False)
    units_sold = Column(Integer, default=1)
    sale_date = Column(DateTime, nullable=False, index=True)
    sales_rep = Column(String(100))
    status = Column(String(20), default="completed")  # completed | refunded | pending
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_sales_date_product", "sale_date", "product_name"),
        Index("ix_sales_category_date", "product_category", "sale_date"),
    )


# ──────────────────────────────────────────────────────────────
# Customer Support Tickets
# ──────────────────────────────────────────────────────────────

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(20), unique=True, nullable=False, index=True)
    customer_id = Column(Integer)
    product_name = Column(String(100))
    category = Column(String(50))   # login | billing | performance | feature | bug
    severity = Column(String(20), default="medium")   # low | medium | high | critical
    status = Column(String(20), default="open")       # open | in_progress | resolved | closed
    subject = Column(String(255))
    description = Column(Text)
    resolution = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime)
    agent_name = Column(String(100))

    __table_args__ = (
        Index("ix_tickets_product_date", "product_name", "created_at"),
        Index("ix_tickets_category_date", "category", "created_at"),
    )


# ──────────────────────────────────────────────────────────────
# HR Data
# ──────────────────────────────────────────────────────────────

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    department = Column(String(50))
    role = Column(String(100))
    team = Column(String(50))
    hire_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    performance_score = Column(Float)  # 1.0 – 5.0
    attrition_risk = Column(String(10), default="low")  # low | medium | high
    salary_band = Column(String(10))   # L1 – L6
    created_at = Column(DateTime, default=datetime.utcnow)


# ──────────────────────────────────────────────────────────────
# Expenses
# ──────────────────────────────────────────────────────────────

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    department = Column(String(50), nullable=False)
    category = Column(String(50))   # infra | marketing | hr | operations | product
    amount = Column(Float, nullable=False)
    description = Column(Text)
    approved_by = Column(String(100))
    expense_date = Column(DateTime, nullable=False, index=True)
    is_approved = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_expenses_dept_date", "department", "expense_date"),
    )


# ──────────────────────────────────────────────────────────────
# Internal Documents (for RAG)
# ──────────────────────────────────────────────────────────────

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    doc_type = Column(String(50))   # release_note | policy | incident_report | sop | memo
    department = Column(String(50))
    content = Column(Text, nullable=False)
    tags = Column(String(255))      # comma-separated tags
    author = Column(String(100))
    published_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ──────────────────────────────────────────────────────────────
# Investigation Logs (audit trail)
# ──────────────────────────────────────────────────────────────

class InvestigationLog(Base):
    __tablename__ = "investigation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question = Column(Text, nullable=False)
    status = Column(String(20), default="running")   # running | completed | failed | needs_review
    agent_trace = Column(Text)    # JSON: list of steps
    final_report = Column(Text)   # JSON: structured report
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)

    user = relationship("User", back_populates="investigations")

    __table_args__ = (
        Index("ix_investigations_user_date", "user_id", "created_at"),
    )
