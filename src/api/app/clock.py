from datetime import UTC, datetime
from typing import Protocol, cast

from fastapi import Request


class Clock(Protocol):
    def now(self) -> datetime:
        """Return the current timezone-aware UTC time."""
        ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def get_clock(request: Request) -> Clock:
    return cast(Clock, request.app.state.clock)
