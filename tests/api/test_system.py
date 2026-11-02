"""Health check and system status contracts (QA, US01a T0).

These are enabler tests, not criterion tests: F-SYS-01 System status and
F-SYS-02 Health check (docs/specs/function-list.md, BD-7), and decisions US01a-D7
and US01a-D8. The contract table is docs/plans/US01a.plan.md section 7.4. The
criteria that later prove them on dev01 (CNT-AC03, SCH group) belong to US01c,
US30 and US31 and are not claimed here.
"""

from __future__ import annotations

import time

from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy.engine import Engine

from app.main import create_app
from app.settings import Settings

HEALTH_PATHS = ("/healthz", "/api/healthz")
STATUS_PATH = "/api/v1/status"
SYSTEM_NOT_READY_BODY = {
    "errors": [{"field": None, "code": "SYSTEM_NOT_READY", "params": {}}],
}

# Obviously fake password for the tests that build their own Settings (plan 7.3).
MOCK_DB_PASSWORD = "mock-db-password-not-a-secret"

# RFC 5737 documentation address: never routed, so a connect attempt either fails
# at once or hangs until the client's connect timeout.
BLACKHOLE_DB_HOST = "192.0.2.1"


def _is_json(response_content_type: str | None) -> bool:
    return (response_content_type or "").split(";")[0].strip() == "application/json"


# ---------------------------------------------------------------------------
# F-SYS-02 Health check: GET /healthz and GET /api/healthz
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", HEALTH_PATHS)
def test_f_sys_02_healthz_ok_when_database_unreachable(
    path: str, unreachable_settings: Settings
) -> None:
    """200 {"status": "ok"} as JSON, no Set-Cookie, even with no database."""
    with TestClient(create_app(unreachable_settings)) as client:
        response = client.get(path)

    assert response.status_code == 200
    assert _is_json(response.headers.get("content-type"))
    assert response.json() == {"status": "ok"}
    assert "set-cookie" not in response.headers


@pytest.mark.parametrize("path", HEALTH_PATHS)
def test_f_sys_02_healthz_without_database_access(
    path: str,
    mock_settings: Settings,
    counted_sqlite_engine: tuple[Engine, Any],
) -> None:
    """The health check opens no database connection and runs no statement."""
    engine, counter = counted_sqlite_engine
    with TestClient(create_app(mock_settings, engine=engine)) as client:
        response = client.get(path)

    assert response.status_code == 200
    assert counter.connects == 0
    assert counter.statements == []


@pytest.mark.parametrize("path", HEALTH_PATHS)
def test_f_sys_02_healthz_body_has_no_configuration_values(
    path: str, unreachable_settings: Settings
) -> None:
    """The body holds no password, host or other configuration value."""
    with TestClient(create_app(unreachable_settings)) as client:
        response = client.get(path)

    assert unreachable_settings.db_password.get_secret_value() not in response.text
    assert unreachable_settings.db_host not in response.text


# ---------------------------------------------------------------------------
# F-SYS-01 System status: GET /api/v1/status
# ---------------------------------------------------------------------------


def test_f_sys_01_status_open_when_database_reachable(
    mock_settings: Settings,
    counted_sqlite_engine: tuple[Engine, Any],
) -> None:
    """200 with status "open" when the database answers; the database is queried."""
    engine, counter = counted_sqlite_engine
    with TestClient(create_app(mock_settings, engine=engine)) as client:
        response = client.get(STATUS_PATH)

    assert response.status_code == 200
    assert _is_json(response.headers.get("content-type"))
    # US08 adds setup_required, so only the status key is asserted (plan 7.4).
    assert response.json()["status"] == "open"
    assert "set-cookie" not in response.headers
    assert counter.statements, "the status check must run a query on the database"


def test_f_sys_01_status_503_when_database_unreachable(
    unreachable_settings: Settings,
) -> None:
    """503 SYSTEM_NOT_READY through the real psycopg path to a closed port."""
    with TestClient(create_app(unreachable_settings)) as client:
        response = client.get(STATUS_PATH)

    assert response.status_code == 503
    assert _is_json(response.headers.get("content-type"))
    assert response.json() == SYSTEM_NOT_READY_BODY
    assert "set-cookie" not in response.headers


def test_f_sys_01_status_503_when_query_fails(
    mock_settings: Settings, failing_query_engine: Engine
) -> None:
    """503 SYSTEM_NOT_READY when the connection opens but SELECT 1 fails."""
    with TestClient(create_app(mock_settings, engine=failing_query_engine)) as client:
        response = client.get(STATUS_PATH)

    assert response.status_code == 503
    assert response.json() == SYSTEM_NOT_READY_BODY


def test_f_sys_01_status_503_body_has_no_secret_host_or_exception_text(
    unreachable_settings: Settings,
) -> None:
    """The 503 body holds no password, host, port or exception text."""
    with TestClient(create_app(unreachable_settings)) as client:
        response = client.get(STATUS_PATH)

    text = response.text
    assert unreachable_settings.db_password.get_secret_value() not in text
    assert unreachable_settings.db_host not in text
    for fragment in ("OperationalError", "psycopg", "refused", "Traceback"):
        assert fragment not in text, f"503 body leaks {fragment!r}"


def test_f_sys_01_status_503_logs_exception_class_only(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The 503 path logs `database check failed: OperationalError` to stdout.

    The log holds no password and no host. capsys, not caplog, because create_app
    replaces the root handlers with logging.basicConfig(force=True) (plan 7.4).
    The app is created inside the test so its handler writes to the captured stdout.
    """
    settings = Settings(
        db_password=SecretStr(MOCK_DB_PASSWORD),
        db_host="127.0.0.1",
        db_port=9,
        log_level="INFO",
    )
    capsys.readouterr()
    with TestClient(create_app(settings)) as client:
        response = client.get(STATUS_PATH)
    out = capsys.readouterr().out

    assert response.status_code == 503
    assert "database check failed: OperationalError" in out
    assert MOCK_DB_PASSWORD not in out
    assert "127.0.0.1" not in out


def test_f_sys_01_engine_disposed_on_shutdown(
    mock_settings: Settings, sqlite_engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The lifespan disposes the engine when the app shuts down (plan T2 item 9)."""
    calls: list[int] = []
    original_dispose = sqlite_engine.dispose

    def recording_dispose(*args: Any, **kwargs: Any) -> None:
        calls.append(1)
        original_dispose(*args, **kwargs)

    monkeypatch.setattr(sqlite_engine, "dispose", recording_dispose)

    with TestClient(create_app(mock_settings, engine=sqlite_engine)) as client:
        client.get(STATUS_PATH)
        assert calls == [], "the engine must not be disposed while the app runs"

    assert calls, "the engine must be disposed on shutdown"


# ---------------------------------------------------------------------------
# US01a-D7: the status check answers within the 3-second connect timeout
# ---------------------------------------------------------------------------


def test_us01a_d7_connect_timeout_is_3_seconds() -> None:
    """DB_CONNECT_TIMEOUT_SECONDS is fixed at 3 (plan T2 item 3)."""
    from app.db import DB_CONNECT_TIMEOUT_SECONDS

    assert DB_CONNECT_TIMEOUT_SECONDS == 3


def test_us01a_d7_status_answers_within_connect_timeout() -> None:
    """With a host that never answers, 503 comes back in about 3 seconds.

    192.0.2.1 is not routed: the connect either fails at once or waits for the
    connect timeout. Without the timeout it would hang far longer. The margin
    above 3 seconds covers libpq and test client overhead.
    """
    settings = Settings(
        db_password=SecretStr(MOCK_DB_PASSWORD),
        db_host=BLACKHOLE_DB_HOST,
        db_port=5432,
    )
    with TestClient(create_app(settings)) as client:
        started = time.monotonic()
        response = client.get(STATUS_PATH)
        elapsed = time.monotonic() - started

    assert response.status_code == 503
    assert response.json() == SYSTEM_NOT_READY_BODY
    assert elapsed < 6.0, f"status took {elapsed:.1f} s; the connect timeout is 3 s"


# ---------------------------------------------------------------------------
# US01a-D8: API documentation is off
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_us01a_d8_docs_off(path: str, mock_settings: Settings, sqlite_engine: Engine) -> None:
    """/docs, /redoc and /openapi.json answer 404 NOT_FOUND in the error format."""
    with TestClient(create_app(mock_settings, engine=sqlite_engine)) as client:
        response = client.get(path)

    assert response.status_code == 404
    assert response.json() == {
        "errors": [{"field": None, "code": "NOT_FOUND", "params": {}}],
    }
