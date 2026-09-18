"""
Investigations router – handles investigation submission, status polling,
history retrieval, and individual report viewing.
"""

import json
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, field_validator

from app.database import get_db
from app.models import InvestigationLog, User
from app.auth.dependencies import get_current_user
from app.agent.workflow import run_investigation
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/investigations", tags=["Investigations"])


# ── Schemas ───────────────────────────────────────────────────

class InvestigationRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Question must be at least 10 characters.")
        if len(v) > 500:
            raise ValueError("Question must be under 500 characters.")
        return v


class InvestigationSummary(BaseModel):
    id: int
    question: str
    status: str
    confidence: Optional[str]
    tokens_used: int
    latency_ms: int
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── Background worker ─────────────────────────────────────────

async def _run_and_persist(
    log_id: int,
    question: str,
    user_id: int,
    db_session_factory,
):
    """Run investigation in background and persist the result."""
    async with db_session_factory() as db:
        try:
            result = await run_investigation(question, user_id)

            log = await db.get(InvestigationLog, log_id)
            if log:
                log.status = result["status"]
                log.final_report = json.dumps(result.get("report", {}))
                log.agent_trace = json.dumps(result.get("tool_trace", []))
                log.tokens_used = result.get("tokens_used", 0)
                log.latency_ms = result.get("latency_ms", 0)
                log.error_message = result.get("error")
                log.completed_at = datetime.utcnow()
                await db.commit()

        except Exception as exc:
            logger.error("investigation.background.failed", error=str(exc), log_id=log_id)
            try:
                async with db_session_factory() as err_db:
                    log = await err_db.get(InvestigationLog, log_id)
                    if log:
                        log.status = "failed"
                        log.error_message = str(exc)
                        log.completed_at = datetime.utcnow()
                        await err_db.commit()
            except Exception:
                pass


# ── Routes ────────────────────────────────────────────────────

@router.post("", status_code=202)
async def submit_investigation(
    payload: InvestigationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a business question for investigation.
    Returns immediately with an investigation ID. Poll /status for results.
    Viewers are not permitted to run investigations.
    """
    if current_user.role == "viewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Viewer accounts cannot run investigations. Contact your admin.",
        )

    # Create log entry immediately
    log = InvestigationLog(
        user_id=current_user.id,
        question=payload.question,
        status="running",
    )
    db.add(log)
    await db.flush()
    log_id = log.id
    await db.commit()

    logger.info("investigation.submitted", log_id=log_id, user=current_user.username)

    # Import here to avoid circular at module level
    from app.database import AsyncSessionLocal

    background_tasks.add_task(
        _run_and_persist,
        log_id=log_id,
        question=payload.question,
        user_id=current_user.id,
        db_session_factory=AsyncSessionLocal,
    )

    return {
        "investigation_id": log_id,
        "status": "running",
        "message": "Investigation started. Poll /api/investigations/{id} for results.",
    }


@router.get("/{investigation_id}")
async def get_investigation(
    investigation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a single investigation by ID. Users can only access their own investigations."""
    log = await db.get(InvestigationLog, investigation_id)
    if not log:
        raise HTTPException(status_code=404, detail="Investigation not found.")

    # Admins can see all; others only their own
    if current_user.role != "admin" and log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    report = {}
    trace = []
    try:
        if log.final_report:
            report = json.loads(log.final_report)
        if log.agent_trace:
            trace = json.loads(log.agent_trace)
    except (json.JSONDecodeError, TypeError):
        pass

    return {
        "id": log.id,
        "question": log.question,
        "status": log.status,
        "report": report,
        "tool_trace": trace,
        "tokens_used": log.tokens_used,
        "latency_ms": log.latency_ms,
        "error_message": log.error_message,
        "created_at": log.created_at,
        "completed_at": log.completed_at,
    }


@router.get("")
async def list_investigations(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List investigations. Admins see all; others see only their own."""
    query = select(InvestigationLog).order_by(desc(InvestigationLog.created_at))

    if current_user.role != "admin":
        query = query.where(InvestigationLog.user_id == current_user.id)

    query = query.limit(min(limit, 50)).offset(offset)
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "investigations": [
            {
                "id": log.id,
                "question": log.question,
                "status": log.status,
                "tokens_used": log.tokens_used,
                "latency_ms": log.latency_ms,
                "created_at": log.created_at,
                "completed_at": log.completed_at,
            }
            for log in logs
        ],
        "total": len(logs),
        "limit": limit,
        "offset": offset,
    }


@router.delete("/{investigation_id}", status_code=204)
async def delete_investigation(
    investigation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an investigation log. Admins can delete any; users only their own."""
    log = await db.get(InvestigationLog, investigation_id)
    if not log:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    if current_user.role != "admin" and log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    await db.delete(log)
    await db.commit()
    return
