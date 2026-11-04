from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.engine import Engine

from app.db import get_engine
from app.schemas.errors import ErrorsOut
from app.schemas.system import HealthOut, StatusOut
from app.services import system

router = APIRouter(tags=["system"])


@router.get("/healthz", response_model=HealthOut)
@router.get("/api/healthz", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(status="ok")


@router.get("/api/v1/status", response_model=StatusOut, responses={503: {"model": ErrorsOut}})
def status(engine: Annotated[Engine, Depends(get_engine)]) -> StatusOut:
    return system.check_status(engine)
