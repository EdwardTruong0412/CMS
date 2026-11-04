"""Settings and database engine (QA, US01a T0).

Enabler tests for decision US01a-D6 (separate CMS_DB_* settings, sslmode
default `require`, URL built with URL.create), docs/plans/US01a.plan.md T2
items 2 and 3, and section 7.3. No connection is opened here.
"""

from __future__ import annotations

import pytest
from pydantic import SecretStr, ValidationError
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.db import create_db_engine
from app.main import create_app
from app.settings import Settings

MOCK_DB_PASSWORD = "mock-db-password-not-a-secret"


def test_us01a_d6_settings_defaults(clean_cms_env: pytest.MonkeyPatch) -> None:
    settings = Settings(db_password=SecretStr(MOCK_DB_PASSWORD))

    assert settings.db_host == "localhost"
    assert settings.db_port == 5432
    assert settings.db_name == "cms"
    assert settings.db_user == "cms"
    assert settings.db_sslmode == "require"
    assert settings.log_level == "INFO"


def test_us01a_d6_settings_read_from_cms_environment(clean_cms_env: pytest.MonkeyPatch) -> None:
    clean_cms_env.setenv("CMS_DB_HOST", "db.mock.example.test")
    clean_cms_env.setenv("CMS_DB_PORT", "6543")
    clean_cms_env.setenv("CMS_DB_NAME", "mock_db")
    clean_cms_env.setenv("CMS_DB_USER", "mock_user")
    clean_cms_env.setenv("CMS_DB_PASSWORD", MOCK_DB_PASSWORD)
    clean_cms_env.setenv("CMS_DB_SSLMODE", "disable")
    clean_cms_env.setenv("CMS_LOG_LEVEL", "DEBUG")

    settings = Settings()  # type: ignore[call-arg]  # values come from CMS_ variables

    assert settings.db_host == "db.mock.example.test"
    assert settings.db_port == 6543
    assert settings.db_name == "mock_db"
    assert settings.db_user == "mock_user"
    assert settings.db_password.get_secret_value() == MOCK_DB_PASSWORD
    assert settings.db_sslmode == "disable"
    assert settings.log_level == "DEBUG"


def test_us01a_d6_keyword_arguments_take_precedence(clean_cms_env: pytest.MonkeyPatch) -> None:
    clean_cms_env.setenv("CMS_DB_HOST", "from-environment.example.test")

    settings = Settings(db_password=SecretStr(MOCK_DB_PASSWORD), db_host="from-argument")

    assert settings.db_host == "from-argument"


def test_us01a_d6_db_password_required(clean_cms_env: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]  # no CMS_DB_PASSWORD on purpose


def test_us01a_d6_db_password_is_secret(clean_cms_env: pytest.MonkeyPatch) -> None:
    settings = Settings(db_password=SecretStr(MOCK_DB_PASSWORD))

    assert isinstance(settings.db_password, SecretStr)
    assert MOCK_DB_PASSWORD not in repr(settings)
    assert MOCK_DB_PASSWORD not in str(settings)


@pytest.mark.parametrize(
    "sslmode", ["disable", "prefer", "require", "verify-ca", "verify-full"]
)
def test_us01a_d6_sslmode_accepts_libpq_modes(
    sslmode: str, clean_cms_env: pytest.MonkeyPatch
) -> None:
    settings = Settings(db_password=SecretStr(MOCK_DB_PASSWORD), db_sslmode=sslmode)

    assert settings.db_sslmode == sslmode


@pytest.mark.parametrize(
    ("field", "value"),
    [("db_sslmode", "allow"), ("db_sslmode", "off"), ("log_level", "TRACE")],
)
def test_us01a_d6_rejects_unknown_sslmode_or_log_level(
    field: str, value: str, clean_cms_env: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ValidationError):
        Settings(db_password=SecretStr(MOCK_DB_PASSWORD), **{field: value})


def test_us01a_d6_create_app_reads_cms_environment_without_settings(
    clean_cms_env: pytest.MonkeyPatch,
) -> None:
    """create_app() with no settings reads the CMS_ variables (plan T2 item 9)."""
    clean_cms_env.setenv("CMS_DB_PASSWORD", MOCK_DB_PASSWORD)
    clean_cms_env.setenv("CMS_DB_HOST", "env-host.example.test")
    engine = create_engine("sqlite+pysqlite:///:memory:")
    try:
        app = create_app(engine=engine)
        assert app.state.settings.db_host == "env-host.example.test"
        assert app.state.engine is engine
    finally:
        engine.dispose()


def test_us01a_d6_engine_url_built_from_settings(clean_cms_env: pytest.MonkeyPatch) -> None:
    """The engine URL carries every setting, unformatted, on the psycopg driver.

    The password holds URL-reserved characters: URL.create keeps it intact, while
    string formatting would break it (plan T2 item 3).
    """
    password = "mock@pass:word/with#chars"
    settings = Settings(
        db_password=SecretStr(password),
        db_host="db.mock.example.test",
        db_port=6543,
        db_name="mock_db",
        db_user="mock_user",
    )

    engine: Engine = create_db_engine(settings)
    try:
        url = engine.url
        assert url.drivername == "postgresql+psycopg"
        assert url.host == "db.mock.example.test"
        assert url.port == 6543
        assert url.database == "mock_db"
        assert url.username == "mock_user"
        assert url.password == password
        # The rendered URL hides the password.
        assert password not in str(url)
    finally:
        engine.dispose()
