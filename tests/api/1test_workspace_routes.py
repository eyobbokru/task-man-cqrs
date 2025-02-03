import uuid
from typing import AsyncGenerator, Dict
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import get_session
from core.config import get_settings as settings
# from core.auth import get_current_user
from tests.conftest import db_session, override_get_session
# from tests.utils.auth import get_test_user


@pytest.fixture
async def test_workspace(client: AsyncClient) -> Dict:
    """Create a test workspace and return its data."""
    workspace_data = {
        "title": "Test Workspace",
        "description": "Test Description",
        "plan_type": "free",
        "settings": {"theme": "light"}
    }
    response = await client.post("/api/v1/workspaces/", json=workspace_data)
    return response.json()

# Test cases
@pytest.mark.asyncio
class TestWorkspaceRoutes:
    async def test_create_workspace_success(self, client: AsyncClient):
        # Arrange
        workspace_data = {
            "title": "Test Workspace",
            "description": "Test Description",
            "plan_type": "pro",
            "settings": {"theme": "dark"}
        }
        
        # Act
        response = await client.post("/api/v1/workspaces/", json=workspace_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == workspace_data["title"]
        assert data["description"] == workspace_data["description"]
        assert data["plan_type"] == workspace_data["plan_type"]
        assert data["settings"] == workspace_data["settings"]
        assert data["is_completed"] is False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    async def test_get_workspaces_pagination(self, client: AsyncClient):
        # Arrange
        workspaces = [
            {"title": f"Workspace {i}", "plan_type": "free"}
            for i in range(5)
        ]
        for workspace in workspaces:
            await client.post("/api/v1/workspaces/", json=workspace)
        
        # Act
        response = await client.get("/api/v1/workspaces/?page=1&per_page=2")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["total_pages"] == 3
        assert data["has_next"] is True
        assert data["has_prev"] is False

    async def test_create_workspace_validation_error(self, client: AsyncClient):
        # Test missing required field
        response = await client.post("/api/v1/workspaces/", json={})
        assert response.status_code == 422

        # Test invalid plan type
        response = await client.post("/api/v1/workspaces/", json={
            "title": "Test",
            "plan_type": "invalid"
        })
        assert response.status_code == 422

    

    async def test_get_workspaces_filtering(self, client: AsyncClient):
        # Arrange
        workspaces = [
            {"title": "Pro Workspace", "plan_type": "pro"},
            {"title": "Free Workspace", "plan_type": "free"}
        ]
        for workspace in workspaces:
            await client.post("/api/v1/workspaces/", json=workspace)
        
        # Act
        response = await client.get(
            "/api/v1/workspaces/?plan_type=pro&title=Pro"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["plan_type"] == "pro"

    async def test_get_workspace_by_id(self, client: AsyncClient, test_workspace: Dict):
        # Act
        response = await client.get(
            f"/api/v1/workspaces/{test_workspace['id']}"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_workspace["id"]
        assert data["title"] == test_workspace["title"]

    async def test_get_nonexistent_workspace(self, client: AsyncClient):
        # Act
        response = await client.get(
            f"/api/v1/workspaces/{uuid.uuid4()}"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_update_workspace_success(
        self,
        client: AsyncClient,
        test_workspace: Dict
    ):
        # Arrange
        update_data = {
            "title": "Updated Workspace",
            "description": "Updated Description",
            "is_completed": True
        }
        
        # Act
        response = await client.patch(
            f"/api/v1/workspaces/{test_workspace['id']}",
            json=update_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_workspace["id"]
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
        assert data["is_completed"] == update_data["is_completed"]
        assert data["updated_at"] > test_workspace["updated_at"]

    async def test_update_workspace_partial(
        self,
        client: AsyncClient,
        test_workspace: Dict
    ):
        # Arrange
        update_data = {"title": "Updated Title"}
        
        # Act
        response = await client.patch(
            f"/api/v1/workspaces/{test_workspace['id']}",
            json=update_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == test_workspace["description"]

    async def test_delete_workspace_success(
        self,
        client: AsyncClient,
        test_workspace: Dict
    ):
        # Act
        response = await client.delete(
            f"/api/v1/workspaces/{test_workspace['id']}"
        )
        
        # Assert
        assert response.status_code == 204
        
        # Verify deletion
        get_response = await client.get(
            f"/api/v1/workspaces/{test_workspace['id']}"
        )
        assert get_response.status_code == 404

    async def test_delete_completed_workspace(
        self,
        client: AsyncClient,
        test_workspace: Dict
    ):
        # Arrange - Complete the workspace
        await client.patch(
            f"/api/v1/workspaces/{test_workspace['id']}",
            json={"is_completed": True}
        )
        
        # Act
        response = await client.delete(
            f"/api/v1/workspaces/{test_workspace['id']}"
        )
        
        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data

