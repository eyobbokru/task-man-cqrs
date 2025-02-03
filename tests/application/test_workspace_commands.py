import pytest
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from domain.exceptions import (
    WorkspaceNotFoundError,
    WorkspaceValidationError,
    WorkspacePermissionError
)
from application.commands.workspace_commands import (
    CreateWorkspaceCommand,
    UpdateWorkspaceCommand,
    DeleteWorkspaceCommand
)
from application.queries.workspace_queries import (
    GetWorkspacesQuery,
    GetWorkspaceByIdQuery
)

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

# Create Workspace Tests
@pytest.mark.asyncio
class TestCreateWorkspaceCommand:
    async def test_create_workspace_success(self, db_session):
        # Arrange
        command = CreateWorkspaceCommand()
        title = "Test Workspace"
        description = "Test Description"
        plan_type = "pro"
        settings = {"theme": "dark"}
        
        # Act
        workspace = await command.execute(
            db_session,
            title=title,
            description=description,
            plan_type=plan_type,
            settings=settings
        )
        
        # Assert
        assert workspace.id is not None
        assert workspace.title == title
        assert workspace.description == description
        assert workspace.plan_type == plan_type
        assert workspace.settings == settings
        assert workspace.is_completed is False
        assert isinstance(workspace.created_at, datetime)
        assert isinstance(workspace.updated_at, datetime)

    async def test_create_workspace_with_minimal_data(self, db_session):
        # Arrange
        command = CreateWorkspaceCommand()
        title = "Minimal Workspace"
        
        # Act
        workspace = await command.execute(db_session, title=title)
        
        # Assert
        assert workspace.id is not None
        assert workspace.title == title
        assert workspace.description is None
        assert workspace.plan_type == "free"
        assert workspace.settings == {}

    async def test_create_workspace_validation_error(self, db_session):
        # Arrange
        command = CreateWorkspaceCommand()
        
        # Act/Assert
        with pytest.raises(WorkspaceValidationError):
            await command.execute(db_session, title="", description="")

        with pytest.raises(WorkspaceValidationError):
            await command.execute(
                db_session,
                title="Test",
                plan_type="invalid_plan"
            )

# Update Workspace Tests
@pytest.mark.asyncio
class TestUpdateWorkspaceCommand:
    async def test_update_workspace_success(self, db_session, workspace_factory):
        # Arrange
        workspace = await workspace_factory()
        command = UpdateWorkspaceCommand()
        
        # Act
        updated_workspace = await command.execute(
            db_session,
            workspace.id,
            title="Updated Workspace",
            description="Updated Description",
            plan_type="pro",
            is_completed=True
        )
        
        # Assert
        assert updated_workspace.title == "Updated Workspace"
        assert updated_workspace.description == "Updated Description"
        assert updated_workspace.plan_type == "pro"
        assert updated_workspace.is_completed is True
        # assert updated_workspace.updated_at.timestamp() > workspace.updated_at.timestamp()

    async def test_update_workspace_partial(self, db_session, workspace_factory):
        # Arrange
        workspace = await workspace_factory()
        command = UpdateWorkspaceCommand()
        
        # Act
        updated_workspace = await command.execute(
            db_session,
            workspace.id,
            title="Updated Title"
        )
        
        # Assert
        assert updated_workspace.title == "Updated Title"
        assert updated_workspace.description == workspace.description
        assert updated_workspace.plan_type == workspace.plan_type

    async def test_update_nonexistent_workspace(self, db_session):
        # Arrange
        command = UpdateWorkspaceCommand()
        
        # Act/Assert
        with pytest.raises(WorkspaceNotFoundError):
            await command.execute(
                db_session,
                uuid4(),
                title="Updated Title"
            )

# Delete Workspace Tests
@pytest.mark.asyncio
class TestDeleteWorkspaceCommand:
    async def test_delete_workspace_success(self, db_session, workspace_factory):
        # Arrange
        workspace = await workspace_factory()
        command = DeleteWorkspaceCommand()
        query = GetWorkspaceByIdQuery()
        
        # Act
        await command.execute(db_session, workspace.id)
        
        # Assert
        with pytest.raises(WorkspaceNotFoundError) as exc_info:
            await query.execute(db_session, workspace.id)
        assert "not found" in str(exc_info.value) 

    async def test_delete_completed_workspace(self, db_session, workspace_factory):
        # Arrange
        workspace = await workspace_factory()
        update_command = UpdateWorkspaceCommand()
        delete_command = DeleteWorkspaceCommand()
        
        # Complete the workspace
        await update_command.execute(
            db_session,
            workspace.id,
            is_completed=True
        )
        
        # Act/Assert
        with pytest.raises(WorkspacePermissionError) as exc_info:
            await delete_command.execute(db_session, workspace.id)
        assert "Cannot delete a completed workspace" in str(exc_info.value)

      

    async def test_force_delete_completed_workspace(self, db_session, workspace_factory):
        # Arrange
        workspace = await workspace_factory()
        update_command = UpdateWorkspaceCommand()
        delete_command = DeleteWorkspaceCommand()
        
        # Complete the workspace
        await update_command.execute(
            db_session,
            workspace.id,
            is_completed=True
        )
        
        # Act
        await delete_command.execute(db_session, workspace.id, force=True)
        
        # Assert
        with pytest.raises(WorkspaceNotFoundError) as exc_info:
            await GetWorkspaceByIdQuery().execute(db_session, workspace.id)

        print(exc_info)
        assert "not found" in str(exc_info.value)