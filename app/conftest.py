import asyncio
import os
from collections.abc import AsyncGenerator

import alembic.command
import alembic.config
import pytest
import pytest_asyncio
import sqlalchemy
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.core import database_session
from app.core.config import PROJECT_DIR, get_settings
from app.core.database_session import new_async_session
from app.main import app as fastapi_app


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def fixture_setup_new_test_database() -> AsyncGenerator[None]:
    worker_name = os.getenv("PYTEST_XDIST_WORKER", "gw0")
    test_db_name = f"test_db_{worker_name}"

    # create new test db using connection to current database
    conn = await database_session._ASYNC_ENGINE.connect()
    await conn.execution_options(isolation_level="AUTOCOMMIT")
    await conn.execute(sqlalchemy.text(f"DROP DATABASE IF EXISTS {test_db_name}"))
    await conn.execute(sqlalchemy.text(f"CREATE DATABASE {test_db_name}"))
    await conn.close()

    # dispose the original engine before switching to test database
    await database_session._ASYNC_ENGINE.dispose()

    session_mpatch = pytest.MonkeyPatch()
    session_mpatch.setenv("DATABASE__DB", test_db_name)
    # force settings to use now monkeypatched environments
    get_settings.cache_clear()

    # monkeypatch test database engine
    engine = database_session.new_async_engine(get_settings().sqlalchemy_database_uri)

    session_mpatch.setattr(
        database_session,
        "_ASYNC_ENGINE",
        engine,
    )
    session_mpatch.setattr(
        database_session,
        "_ASYNC_SESSIONMAKER",
        async_sessionmaker(engine, expire_on_commit=False),
    )

    def alembic_upgrade() -> None:
        # synchronous function to run alembic upgrade
        alembic_config = alembic.config.Config(PROJECT_DIR / "alembic.ini")
        alembic.command.upgrade(alembic_config, "head")

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, alembic_upgrade)

    yield

    # cleanup: dispose the test engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function", loop_scope="session", autouse=True)
async def fixture_clean_get_settings_between_tests() -> AsyncGenerator[None]:
    yield

    get_settings.cache_clear()


@pytest_asyncio.fixture(name="session", loop_scope="session", scope="function")
async def fixture_session_with_rollback(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[AsyncSession]:
    # we want to monkeypatch new_async_session with one bound to session
    # that we will always rollback on function scope

    connection = await database_session._ASYNC_ENGINE.connect()
    transaction = await connection.begin()

    session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    monkeypatch.setattr(
        database_session,
        "new_script_async_session",
        lambda: session,
    )

    fastapi_app.dependency_overrides[new_async_session] = lambda: session

    yield session

    fastapi_app.dependency_overrides.pop(new_async_session, None)

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture(name="client", loop_scope="session", scope="function")
async def fixture_client(session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as aclient:
        aclient.headers.update({"Host": "localhost"})
        yield aclient
