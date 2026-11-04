import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError

from app.errors import DomainError
from app.schemas.system import StatusOut

logger = logging.getLogger(__name__)


def check_status(engine: Engine) -> StatusOut:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except DBAPIError as exc:
        logger.warning("database check failed: %s", type(exc).__name__)
        raise DomainError(503, "SYSTEM_NOT_READY") from exc
    return StatusOut(status="open")
