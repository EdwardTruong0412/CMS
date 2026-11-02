from typing import cast

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine

from app.settings import Settings

DB_CONNECT_TIMEOUT_SECONDS = 3


def create_db_engine(settings: Settings) -> Engine:
    url = URL.create(
        "postgresql+psycopg",
        username=settings.db_user,
        password=settings.db_password.get_secret_value(),
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
    )
    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={
            "connect_timeout": DB_CONNECT_TIMEOUT_SECONDS,
            "sslmode": settings.db_sslmode,
        },
    )


def get_engine(request: Request) -> Engine:
    return cast(Engine, request.app.state.engine)
