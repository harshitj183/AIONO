"""
AIONO – AI Business Operations Investigator
FastAPI application entry point.
"""

import time
import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db, check_db_health
from app.routers import auth, investigations, analytics

# ── Structured logging setup ──────────────────────────────────

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger("aiono.api")


# ── Lifespan (startup / shutdown) ─────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("aiono.startup", version=settings.APP_VERSION)
    await init_db()
    # Ensure demo DB uses AIONO product branding (seed empty / upgrade from Product X)
    try:
        from sqlalchemy import text, select, func
        from app.database import AsyncSessionLocal
        from app.models import User
        from app.seed import seed, clear_all

        async with AsyncSessionLocal() as session:
            user_count = (await session.execute(select(func.count()).select_from(User))).scalar() or 0
            legacy = 0
            try:
                legacy = (
                    await session.execute(
                        text(
                            "SELECT COUNT(*) FROM sales "
                            "WHERE product_name LIKE 'Product %' OR product_name LIKE 'Service %'"
                        )
                    )
                ).scalar() or 0
            except Exception:
                legacy = 0
            if user_count == 0:
                await seed(session)
                logger.info("aiono.seed.created")
            elif legacy > 0:
                await clear_all(session)
                await seed(session)
                logger.info("aiono.seed.migrated_products")
    except Exception as exc:
        logger.warning("aiono.seed.skipped", error=str(exc))
    yield
    logger.info("aiono.shutdown")


# ── App initialisation ────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AIONO investigates business problems by querying your data, "
        "searching documents, and producing evidence-backed root cause reports."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS – allow the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    latency = round((time.time() - start) * 1000)
    logger.info(
        "http.request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        latency_ms=latency,
    )
    return response


# ── Global error handler ──────────────────────────────────────

@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    logger.error("http.unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."},
    )


# ── Routers ───────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(investigations.router)
app.include_router(analytics.router)


# ── Health check ─────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    """Returns application health status and database connectivity."""
    db_ok = await check_db_health()
    return {
        "status": "healthy" if db_ok else "degraded",
        "version": settings.APP_VERSION,
        "database": "connected" if db_ok else "unreachable",
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
