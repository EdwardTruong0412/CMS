from typing import Literal

from pydantic import BaseModel


class HealthOut(BaseModel):
    status: Literal["ok"]


class StatusOut(BaseModel):
    status: Literal["open"]
