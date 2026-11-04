"""Shared fixtures for the API tests (QA, US01a T0).

Plan reference: docs/plans/US01a.plan.md, section 7 "For QA".

- The app is built with `app.main.create_app(settings, engine=..., clock=...)` and
  always used inside `with TestClient(...)`, so the lifespan runs (7.1).
- Settings are built from keyword arguments with an obviously fake password; the
  value is mock data, not a secret (7.3).
- 200 cases use an in-memory SQLite engine; 503 cases use the real psycopg path
  to 127.0.0.1:9, where nothing listens (7.5).
- `controlled_clock` implements the `app.clock.Clock` protocol (7.6).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from pydantic import SecretStr
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from app.settings import Settings

# Obviously fake values. Tests assert that none of them leaks into a body or a log.
MOCK_DB_PASSWORD = "mock-db-password-not-a-secret"
UNREACHABLE_DB_HOST = "127.0.0.1"
UNREACHABLE_DB_PORT = 9

# A fixed, timezone-aware UTC start time for the controlled clock.
CLOCK_START = datetime(2026, 11, 2, 1, 30, 0, tzinfo=UTC)

# Every CMS_ variable the Settings class reads (plan T2 item 2). Tests that check
# defaults or environment reading clear them first, so the machine's environment
# cannot change the result.
CMS_ENV_VARS = (
    "CMS_DB_HOST",
    "CMS_DB_PORT",
    "CMS_DB_NAME",
    "CMS_DB_USER",
    "CMS_DB_PASSWORD",
    "CMS_DB_SSLMODE",
    "CMS_LOG_LEVEL",
)


class ControlledClock:
    """Test clock implementing the app.clock.Clock protocol (D-PM3, US01a-D10).

    `now()` returns a timezone-aware UTC datetime that moves only when the test
    calls `advance(delta)`.
    """

    def __init__(self, start: datetime = CLOCK_START) -> None:
        if start.tzinfo is None or start.utcoffset() != timedelta(0):
            raise ValueError("ControlledClock needs a timezone-aware UTC start time")
        self._now = start

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now = self._now + delta


@pytest.fixture
def controlled_clock() -> ControlledClock:
    """A fresh controlled clock starting at CLOCK_START."""
    return ControlledClock()


@pytest.fixture
def clean_cms_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Remove every CMS_ variable from the environment for the test."""
    for name in CMS_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


@pytest.fixture
def mock_settings() -> Settings:
    """Settings with a fake password; the database values are not used by SQLite."""
    return Settings(db_password=SecretStr(MOCK_DB_PASSWORD))


@pytest.fixture
def unreachable_settings() -> Settings:
    """Settings that point the real psycopg engine at a port where nothing listens."""
    return Settings(
        db_password=SecretStr(MOCK_DB_PASSWORD),
        db_host=UNREACHABLE_DB_HOST,
        db_port=UNREACHABLE_DB_PORT,
    )


class ConnectionCounter:
    """Counts DBAPI connections opened and statements executed on an engine."""

    def __init__(self, engine: Engine) -> None:
        self.connects = 0
        self.statements: list[str] = []
        event.listen(engine, "connect", self._on_connect)
        event.listen(engine, "before_cursor_execute", self._on_execute)

    def _on_connect(self, dbapi_connection: Any, connection_record: Any) -> None:
        self.connects += 1

    def _on_execute(
        self,
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        self.statements.append(statement)


@pytest.fixture
def sqlite_engine() -> Iterator[Engine]:
    """A reachable engine: in-memory SQLite from the standard library (plan 7.5)."""
    engine = create_engine("sqlite+pysqlite:///:memory:")
    yield engine
    engine.dispose()


@pytest.fixture
def counted_sqlite_engine(sqlite_engine: Engine) -> tuple[Engine, ConnectionCounter]:
    """The SQLite engine plus a counter of its connections and statements."""
    return sqlite_engine, ConnectionCounter(sqlite_engine)


@pytest.fixture
def failing_query_engine() -> Iterator[Engine]:
    """A reachable engine on which every SELECT fails with a DBAPI error.

    The connection opens, but SQLite's authorizer denies SELECT statements, so
    `SELECT 1` raises sqlite3.DatabaseError, which SQLAlchemy wraps in a DBAPIError
    ("the query fails" row of plan 7.4).
    """
    engine = create_engine("sqlite+pysqlite:///:memory:")

    def deny_select(action: int, *args: object) -> int:
        if action == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    @event.listens_for(engine, "connect")
    def _install_authorizer(dbapi_connection: Any, connection_record: Any) -> None:
        dbapi_connection.set_authorizer(deny_select)

    yield engine
    engine.dispose()
