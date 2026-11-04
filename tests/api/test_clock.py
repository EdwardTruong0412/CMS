"""Injectable clock (QA, US01a T0).

Enabler tests for decision US01a-D10 (D-PM3): the `app.clock.Clock` protocol,
`SystemClock`, injection through `create_app(clock=...)` and the `get_clock`
dependency (docs/plans/US01a.plan.md T2 item 4, section 7.6). No US01a criterion
needs the clock; it is fixed now for US08 to US24.
"""

from __future__ import annotations

import re
from datetime import UTC, timedelta
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine

from app.clock import Clock, SystemClock, get_clock
from app.main import create_app
from app.settings import Settings

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = REPO_ROOT / "src" / "api" / "app"


def read_now(clock: Annotated[Clock, Depends(get_clock)]) -> dict[str, str]:
    """Test-only route: returns what the injected clock says."""
    return {"now": clock.now().isoformat()}


def test_us01a_d10_create_app_injects_clock(
    mock_settings: Settings, sqlite_engine: Engine, controlled_clock: Any
) -> None:
    app = create_app(mock_settings, engine=sqlite_engine, clock=controlled_clock)

    assert app.state.clock is controlled_clock


def test_us01a_d10_routes_read_injected_clock_through_get_clock(
    mock_settings: Settings, sqlite_engine: Engine, controlled_clock: Any
) -> None:
    """A route using get_clock sees the controlled time, and it moves on advance()."""
    app = create_app(mock_settings, engine=sqlite_engine, clock=controlled_clock)
    app.add_api_route("/test/now", read_now, methods=["GET"])
    start = controlled_clock.now()

    with TestClient(app) as client:
        first = client.get("/test/now").json()["now"]
        controlled_clock.advance(timedelta(hours=8))
        second = client.get("/test/now").json()["now"]

    assert first == start.isoformat()
    assert second == (start + timedelta(hours=8)).isoformat()


def test_us01a_d10_system_clock_is_default(
    mock_settings: Settings, sqlite_engine: Engine
) -> None:
    app = create_app(mock_settings, engine=sqlite_engine)

    assert isinstance(app.state.clock, SystemClock)


def test_us01a_d10_system_clock_is_timezone_aware_utc() -> None:
    now = SystemClock().now()

    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)
    assert now.tzinfo == UTC


def test_us01a_d10_controlled_clock_fixture_follows_protocol(controlled_clock: Any) -> None:
    """QA's fixture keeps the protocol's promise: aware UTC, moved only by advance()."""
    start = controlled_clock.now()
    assert start.utcoffset() == timedelta(0)
    assert controlled_clock.now() == start

    controlled_clock.advance(timedelta(minutes=61))

    assert controlled_clock.now() - start == timedelta(minutes=61)


def test_us01a_d10_datetime_now_only_in_system_clock() -> None:
    """No module of the app reads the time except app/clock.py (D-PM3, plan T2)."""
    assert APP_DIR.is_dir(), f"{APP_DIR} is missing"
    pattern = re.compile(r"\b(?:datetime\.now|datetime\.utcnow)\s*\(")
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in sorted(APP_DIR.rglob("*.py"))
        if path.name != "clock.py" or path.parent != APP_DIR
        if pattern.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == [], f"the current time is read outside app/clock.py: {offenders}"
