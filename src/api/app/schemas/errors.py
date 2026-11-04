from pydantic import BaseModel


class ErrorItem(BaseModel):
    field: str | None
    code: str
    params: dict[str, object]


class ErrorsOut(BaseModel):
    errors: list[ErrorItem]
