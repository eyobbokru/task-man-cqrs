# Query Tests

import pytest
from application.commands.workspace_commands import CreateWorkspaceCommand
from application.queries.workspace_queries import GetWorkspaceByIdQuery, GetWorkspacesQuery, PaginationParams, WorkspaceFilters
from domain.models.workspace import Workspace

@pytest.fixture
async def workspace_factory(db_session):
    """Fixture to create test workspaces."""
    async def create_workspace(
        title="Test Workspace",
        description="Test Description",
        plan_type="free",
        settings=None
    ):
        command = CreateWorkspaceCommand()
        return await command.execute(
            db_session,
            title=title,
            description=description,
            plan_type=plan_type,
            settings=settings or {}
        )
    return create_workspace


@pytest.mark.asyncio
class TestWorkspaceQueries:
    async def test_get_workspace_by_id(self, db_session, workspace_factory):
        # Arrange
        workspace = await workspace_factory()
        query = GetWorkspaceByIdQuery()
        
        # Act
        result = await query.execute(db_session, workspace.id)
        
        # Assert
        assert result.id == workspace.id
        assert result.title == workspace.title

    async def test_get_workspaces_with_filters(self, db_session, workspace_factory):
        # Arrange
        await workspace_factory(title="First Workspace", plan_type="free")
        await workspace_factory(title="Second Workspace", plan_type="pro")
        query = GetWorkspacesQuery(Workspace)
        
        # Act
        result = await query.execute(
            db_session,
            filters=WorkspaceFilters(plan_type="pro"),
            pagination=PaginationParams(page=1, per_page=10)
        )
        
        # Assert
        assert result.total == 1
        assert result.items[0].plan_type == "pro"

    async def test_get_workspaces_pagination(self, db_session, workspace_factory):
        # Arrange
        workspaces = [
            await workspace_factory(title=f"Workspace {i}")
            for i in range(5)
        ]
        query = GetWorkspacesQuery(Workspace)
        
        # Act
        result = await query.execute(
            db_session,
            pagination=PaginationParams(page=1, per_page=2)
        )
        
        # Assert
        assert result.total == 5
        assert result.total_pages == 3
        assert len(result.items) == 2
        assert result.has_next is True
        assert result.has_prev is False
