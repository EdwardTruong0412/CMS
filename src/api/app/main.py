import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.engine import Engine

from app.clock import Clock, SystemClock
from app.db import create_db_engine
from app.errors import register_exception_handlers
from app.routers import system
from app.settings import Settings


def create_app(
    settings: Settings | None = None,
    *,
    engine: Engine | None = None,
    clock: Clock | None = None,
) -> FastAPI:
    if settings is None:
        settings = Settings()  # Values come from CMS_ environment variables.
    logging.basicConfig(
        level=settings.log_level,
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )
    db_engine = engine if engine is not None else create_db_engine(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            db_engine.dispose()

    app = FastAPI(
        title="CMS API", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan
    )
    app.state.settings = settings
    app.state.engine = db_engine
    app.state.clock = clock if clock is not None else SystemClock()
    register_exception_handlers(app)
    app.include_router(system.router)
    return app
