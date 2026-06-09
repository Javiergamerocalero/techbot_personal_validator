"""Entrypoint FastAPI."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.core.config import get_settings
from app.core.database import dispose_engine
from app.core.logging import configure_logging
from app.routers import employees, health, tenants

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    log.info("service.start", extra={"version": __version__})
    yield
    log.info("service.stop")
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Qapp Employee Validation Service",
        version=__version__,
        description=(
            "Servicio multi-tenant para validar empleados autorizados "
            "a comprar en quioscos Qapp. Cada tenant carga su Excel y "
            "los quioscos consultan via X-Tenant-Key."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = "/api/v1"
    app.include_router(health.router, prefix=prefix, tags=["health"])
    app.include_router(employees.router, prefix=prefix, tags=["employees"])
    app.include_router(tenants.router, prefix=prefix, tags=["tenants"])
    return app


app = create_app()
