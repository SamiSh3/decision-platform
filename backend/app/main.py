"""FastAPI application factory and entry point for the Decision Intelligence Platform."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.exception_handlers import register_exception_handlers
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.database.session import get_db
from app.middleware.audit_middleware import AuditContextMiddleware
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.routers import (
    attachment_router,
    audit_router,
    auth_router,
    case_router,
    decision_router,
    domain_router,
    expert_router,
    expert_session_router,
    knowledge_source_router,
    permission_router,
    questionnaire_router,
    response_router,
    rule_router,
    user_router,
)

configure_logging()
logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("application_startup", app_name=settings.app_name, env=settings.app_env)
    yield
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Decision Intelligence Platform",
        description=(
            "Captures expert knowledge through structured questionnaires and converts it "
            "into a reusable knowledge repository and rule-based decision engine. "
            "The first implemented domain is Used Car Purchase Decision; the architecture "
            "is domain-driven and extensible to Real Estate, Medical Decisions, Insurance, "
            "Investment and Procurement."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AuditContextMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    register_exception_handlers(app)

    prefix = settings.api_v1_prefix
    app.include_router(auth_router.router, prefix=prefix)
    app.include_router(user_router.router, prefix=prefix)
    app.include_router(permission_router.router, prefix=prefix)
    app.include_router(expert_router.router, prefix=prefix)
    app.include_router(domain_router.router, prefix=prefix)
    app.include_router(questionnaire_router.router, prefix=prefix)
    app.include_router(case_router.router, prefix=prefix)
    app.include_router(response_router.router, prefix=prefix)
    app.include_router(knowledge_source_router.router, prefix=prefix)
    app.include_router(rule_router.router, prefix=prefix)
    app.include_router(decision_router.router, prefix=prefix)
    app.include_router(expert_session_router.router, prefix=prefix)
    app.include_router(attachment_router.router, prefix=prefix)
    app.include_router(audit_router.router, prefix=prefix)

    @app.get("/health", tags=["health"])
    def health_check(db: Session = Depends(get_db)) -> JSONResponse:
        db_status = "ok"
        try:
            db.execute(text("SELECT 1"))
        except Exception as exc:  # pragma: no cover - only hit if DB is truly down
            logger.error("health_check_database_unreachable", error=str(exc))
            db_status = "unreachable"

        payload = {
            "status": "ok" if db_status == "ok" else "degraded",
            "app": settings.app_name,
            "env": settings.app_env,
            "database": db_status,
        }
        status_code = (
            status.HTTP_200_OK if db_status == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return JSONResponse(status_code=status_code, content=payload)

    return app


app = create_app()
