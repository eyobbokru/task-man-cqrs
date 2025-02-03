from datetime import datetime, timezone
from uuid import UUID
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi import FastAPI
from infrastructure.database import Base, get_session
from main import app
from api.routes.workspace_routes import  router as api_router

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}  # Required for SQLite
)

# Test session factory using async_sessionmaker
test_async_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    """Backend for anyio."""
    return "asyncio"

@pytest.fixture(scope="session")
async def initialize_test_db():
    """Initialize test database once per session."""

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)




@pytest.fixture
async def db_session(initialize_test_db) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for a test."""
    print("**here")
    # await initialize_test_db
    async with test_async_session_maker() as session:
        try:
            yield session
            await session.rollback()  # Rollback any changes
        finally:
            await session.close()

@pytest.fixture
async def clean_db(db_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """Ensure clean database state for each test."""
    try:
        yield 
    finally:
        # Clear all tables after each test
        async with db_session.begin():
            for table in reversed(Base.metadata.sorted_tables):
                await db_session.execute(table.delete())
        await db_session.commit()

async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    """Override get_session dependency for testing."""
    async with test_async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

@pytest.fixture
def test_app() -> FastAPI:
    """Create a test FastAPI application with dependencies overridden."""
    app.include_router(api_router, prefix="/api/v1")

    app.dependency_overrides[get_session] = override_get_session
    return app

@pytest.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        follow_redirects=True
    ) as test_client:
        yield test_client

# Optional: Add these if you're using authentication in your tests
# from core.auth import get_current_user  # Adjust import path as needed

# class TestUser:
#     def __init__(self):
#         self.id = "test-user-id"
#         self.email = "test@example.com"
#         self.is_active = True

# async def override_get_current_user():
#     # """Override get_current_user dependency for testing."""
#     return TestUser()

# @pytest.fixture
# def authenticated_app() -> FastAPI:
#     """Create a test FastAPI application with authentication."""
#     app.dependency_overrides[get_session] = override_get_session
#     app.dependency_overrides[get_current_user] = override_get_current_user
#     return app

# @pytest.fixture
# async def authenticated_client(authenticated_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
#     """Create an async test client with authentication."""
#     async with AsyncClient(
#         transport=ASGITransport(app=authenticated_app),
#         base_url="http://test",
#         follow_redirects=True
#     ) as test_client:
#         yield test_client

@pytest.fixture
def sample_uuid():
    return UUID('12345678-1234-5678-1234-567812345678')

@pytest.fixture
def sample_workspace_data():
    return {
        "title": "Test Workspace",
        "description": "Test Description",
        "plan_type": "free",
        "settings": {"theme": "light"},
        "is_completed": False
    }

# If you want to customize settings, create a separate fixture factory:
@pytest.fixture
def make_workspace_data():
    def _make_workspace_data(custom_settings=None):
        return {
            "title": "Test Workspace",
            "description": "Test Description",
            "plan_type": "free",
            "settings": custom_settings or {"theme": "light"},
            "is_completed": False
        }
    return _make_workspace_data

@pytest.fixture
def sample_team_data():
    return {
        "name": "Test Team",
        "description": "Test Description",
        "workspace_id": UUID('12345678-1234-5678-1234-567812345678'),
        "owner_id": UUID('87654321-4321-8765-4321-876543210987'),
        "settings": {"default_role": "member"},
        "is_active": True
    }

@pytest.fixture
def sample_user_data():
    return {
        "email": "test@example.com",
        "name": "Test User",
        "password_hash": "hashed_password",
        "profile": {"avatar": "default.jpg", "timezone": "UTC"},
        "preferences": {"theme": "dark"}, 
     
    }

@pytest.fixture
def sample_team_member_data():
    return {
        "team_id": UUID('12345678-1234-5678-1234-567812345678'),
        "user_id": UUID('87654321-4321-8765-4321-876543210987'),
        "role": "member",
        "permissions": {"can_invite": True}
    }

@pytest.fixture
def current_time():
    return datetime.now(timezone.utc)