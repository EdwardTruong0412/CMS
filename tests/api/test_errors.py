"""One error format for every error path (QA, US01a T0).

Enabler tests for decision US01a-D9 (D-DL1: the API never returns sentences),
docs/plans/US01a.plan.md T2 item 5 and section 7.4. US01a has no route that
raises, so these tests add their own test-only routes to the app that
`create_app` returns, before the TestClient starts (plan 7.4). Nothing here is
added to src/.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Annotated

import pytest
from fastapi import FastAPI, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from sqlalchemy.engine import Engine

from app.errors import DomainError
from app.main import create_app
from app.settings import Settings

MOCK_DB_PASSWORD = "mock-db-password-not-a-secret"


# ---------------------------------------------------------------------------
# Test-only request models and routes
# ---------------------------------------------------------------------------


class MockAddressIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city: str = Field(min_length=2)


class MockThingIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3)
    address: MockAddressIn | None = None


class MockValidatedIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str

    @field_validator("label")
    @classmethod
    def label_not_reserved(cls, value: str) -> str:
        if value == "reserved":
            raise ValueError("mock reason")
        return value


def raise_domain_error_full() -> None:
    raise DomainError(409, "MOCK_CONFLICT", field="name", params={"max": 3, "label": "x"})


def raise_domain_error_bare() -> None:
    raise DomainError(400, "MOCK_BAD_REQUEST")


def accept_thing(payload: MockThingIn) -> dict[str, str]:
    return {"name": payload.name}


def accept_validated(payload: MockValidatedIn) -> dict[str, str]:
    return {"label": payload.label}


def accept_query(limit: Annotated[int, Query()]) -> dict[str, int]:
    return {"limit": limit}


def raise_runtime_error() -> None:
    # The message holds no request data, so the log check below only finds request
    # data if the handler logged it.
    raise RuntimeError("mock unhandled failure")


def add_test_routes(app: FastAPI) -> FastAPI:
    app.add_api_route("/test/domain-full", raise_domain_error_full, methods=["GET"])
    app.add_api_route("/test/domain-bare", raise_domain_error_bare, methods=["GET"])
    app.add_api_route("/test/thing", accept_thing, methods=["POST"])
    app.add_api_route("/test/validated", accept_validated, methods=["POST"])
    app.add_api_route("/test/query", accept_query, methods=["GET"])
    app.add_api_route("/test/boom", raise_runtime_error, methods=["GET", "POST"])
    return app


@pytest.fixture
def client(mock_settings: Settings, sqlite_engine: Engine) -> Iterator[TestClient]:
    app = add_test_routes(create_app(mock_settings, engine=sqlite_engine))
    # raise_server_exceptions=False: Starlette re-raises an unhandled exception
    # after the 500 response is sent; the test checks the response instead.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def _single_error(body: dict[str, object]) -> dict[str, object]:
    assert set(body) == {"errors"}
    errors = body["errors"]
    assert isinstance(errors, list)
    assert len(errors) == 1
    item = errors[0]
    assert isinstance(item, dict)
    assert set(item) == {"field", "code", "params"}
    return item


# ---------------------------------------------------------------------------
# Starlette HTTP errors
# ---------------------------------------------------------------------------


def test_us01a_d9_unknown_path_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/nothing")

    assert response.status_code == 404
    assert response.json() == {
        "errors": [{"field": None, "code": "NOT_FOUND", "params": {}}],
    }


def test_us01a_d9_method_not_allowed_keeps_allow_header(client: TestClient) -> None:
    response = client.post("/healthz")

    assert response.status_code == 405
    assert response.json() == {
        "errors": [{"field": None, "code": "METHOD_NOT_ALLOWED", "params": {}}],
    }
    assert "GET" in response.headers.get("allow", "")


# ---------------------------------------------------------------------------
# DomainError
# ---------------------------------------------------------------------------


def test_us01a_d9_domain_error_with_field_and_params(client: TestClient) -> None:
    response = client.get("/test/domain-full")

    assert response.status_code == 409
    assert response.json() == {
        "errors": [{"field": "name", "code": "MOCK_CONFLICT", "params": {"max": 3, "label": "x"}}],
    }


def test_us01a_d9_domain_error_defaults_field_null_params_empty(client: TestClient) -> None:
    response = client.get("/test/domain-bare")

    assert response.status_code == 400
    assert response.json() == {
        "errors": [{"field": None, "code": "MOCK_BAD_REQUEST", "params": {}}],
    }


def test_us01a_d9_domain_error_attributes() -> None:
    """DomainError keeps status_code and one error item (plan T2 item 5, section 6)."""
    error = DomainError(503, "SYSTEM_NOT_READY")

    assert error.status_code == 503
    assert len(error.errors) == 1
    item = error.errors[0]
    assert item.code == "SYSTEM_NOT_READY"
    assert item.field is None
    assert item.params == {}


# ---------------------------------------------------------------------------
# RequestValidationError
# ---------------------------------------------------------------------------


def test_us01a_d9_validation_missing_field(client: TestClient) -> None:
    response = client.post("/test/thing", json={})

    assert response.status_code == 422
    item = _single_error(response.json())
    assert item["code"] == "MISSING"
    assert item["field"] == "name"


def test_us01a_d9_validation_one_item_per_error(client: TestClient) -> None:
    """Two errors give two items; the body source is not part of the field."""
    response = client.post("/test/thing", json={"name": "ab", "unexpected": 1})

    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"errors"}
    by_code = {item["code"]: item for item in body["errors"]}
    assert len(body["errors"]) == 2
    assert set(by_code) == {"STRING_TOO_SHORT", "EXTRA_FORBIDDEN"}
    assert by_code["STRING_TOO_SHORT"]["field"] == "name"
    assert by_code["STRING_TOO_SHORT"]["params"] == {"min_length": 3}
    assert by_code["EXTRA_FORBIDDEN"]["field"] == "unexpected"
    for item in body["errors"]:
        assert set(item) == {"field", "code", "params"}


def test_us01a_d9_validation_nested_field_joined_with_dot(client: TestClient) -> None:
    response = client.post("/test/thing", json={"name": "abc", "address": {"city": "x"}})

    assert response.status_code == 422
    item = _single_error(response.json())
    assert item["code"] == "STRING_TOO_SHORT"
    assert item["field"] == "address.city"


def test_us01a_d9_validation_query_parameter_without_source(client: TestClient) -> None:
    response = client.get("/test/query", params={"limit": "not-a-number"})

    assert response.status_code == 422
    item = _single_error(response.json())
    assert item["code"] == "INT_PARSING"
    assert item["field"] == "limit"


def test_us01a_d9_validation_params_made_json_safe(client: TestClient) -> None:
    """A ctx value that is not JSON-native (a ValueError) is sent as its str()."""
    response = client.post("/test/validated", json={"label": "reserved"})

    assert response.status_code == 422
    item = _single_error(response.json())
    assert item["code"] == "VALUE_ERROR"
    assert item["field"] == "label"
    assert item["params"] == {"error": "mock reason"}


# ---------------------------------------------------------------------------
# Unhandled exceptions
# ---------------------------------------------------------------------------


def test_us01a_d9_unhandled_error_is_internal_error(client: TestClient) -> None:
    response = client.get("/test/boom")

    assert response.status_code == 500
    assert response.json() == {
        "errors": [{"field": None, "code": "INTERNAL_ERROR", "params": {}}],
    }
    assert "mock unhandled failure" not in response.text
    assert "Traceback" not in response.text


def test_us01a_d9_unhandled_error_logs_method_and_path_only(
    capsys: pytest.CaptureFixture[str],
    sqlite_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The log names method and path, never the body, query, headers or cookies.

    capsys, not caplog (plan 7.4). The app is built inside the test so its stdout
    handler writes to the captured stream. The test client's own httpx logger logs
    the full URL at INFO; it is raised to WARNING so only the app's log is checked.
    """
    httpx_logger = logging.getLogger("httpx")
    monkeypatch.setattr(httpx_logger, "level", httpx_logger.level)  # restored after the test
    httpx_logger.setLevel(logging.WARNING)  # setLevel also clears the level cache
    settings = Settings(db_password=SecretStr(MOCK_DB_PASSWORD), log_level="INFO")
    app = add_test_routes(create_app(settings, engine=sqlite_engine))
    capsys.readouterr()

    with TestClient(app, raise_server_exceptions=False) as test_client:
        test_client.cookies.set("mock_cookie", "mock-cookie-value")
        response = test_client.post(
            "/test/boom",
            params={"mock_query": "mock-query-value"},
            headers={"X-Mock-Header": "mock-header-value"},
            json={"mock_body": "mock-body-value"},
        )
    out = capsys.readouterr().out

    assert response.status_code == 500
    assert "unhandled error on POST /test/boom" in out
    for leaked in (
        "mock-query-value",
        "mock_query",
        "mock-header-value",
        "mock-cookie-value",
        "mock-body-value",
        MOCK_DB_PASSWORD,
    ):
        assert leaked not in out, f"the log leaks {leaked!r}"
