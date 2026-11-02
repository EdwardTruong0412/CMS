import logging
from collections.abc import Mapping

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.schemas.errors import ErrorItem, ErrorsOut

logger = logging.getLogger(__name__)


class DomainError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        *,
        field: str | None = None,
        params: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(code)
        self.status_code = status_code
        self.errors = [ErrorItem(field=field, code=code, params=dict(params or {}))]


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorsOut(errors=exc.errors).model_dump(mode="json"),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for error in exc.errors():
            location = error["loc"]
            if location and location[0] in {"body", "query", "path", "header", "cookie"}:
                location = location[1:]
            params = {
                key: value if isinstance(value, (str, int, float, bool, type(None))) else str(value)
                for key, value in error.get("ctx", {}).items()
            }
            errors.append(
                ErrorItem(
                    field=".".join(str(part) for part in location) or None,
                    code=error["type"].upper(),
                    params=params,
                )
            )
        return JSONResponse(
            status_code=422, content=ErrorsOut(errors=errors).model_dump(mode="json")
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(
            exc.status_code, f"HTTP_{exc.status_code}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            headers=exc.headers,
            content=ErrorsOut(errors=[ErrorItem(field=None, code=code, params={})]).model_dump(
                mode="json"
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=ErrorsOut(
                errors=[ErrorItem(field=None, code="INTERNAL_ERROR", params={})]
            ).model_dump(mode="json"),
        )
