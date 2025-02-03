import pytest
from uuid import UUID
from datetime import datetime, timezone

from domain.models.workspace import Workspace
from domain.exceptions import ValidationError

class TestWorkspaceCreation:
    """Test suite for Workspace model creation."""
    
    def test_basic_creation(self, sample_workspace_data):
        """Test basic workspace creation with minimal fields."""
        workspace = Workspace(**sample_workspace_data)
        assert workspace.title == sample_workspace_data["title"]
        assert workspace.description == sample_workspace_data["description"]
        assert workspace.plan_type == sample_workspace_data["plan_type"]
        assert workspace.is_completed == False
        assert isinstance(workspace.settings, dict)

    def test_full_creation(self, make_workspace_data, current_time):
        """Test workspace creation with all possible fields."""
        _sample_workspace_data = make_workspace_data(custom_settings = {"custom": "setting"})
        workspace = Workspace(
            **_sample_workspace_data,
            created_at=current_time,
            updated_at=current_time
        )
        assert workspace.title == _sample_workspace_data["title"]
        assert workspace.settings == {"custom": "setting"}
        assert workspace.created_at == current_time
        assert workspace.updated_at == current_time

class TestWorkspaceValidation:
    """Test suite for Workspace model validation rules."""

    def test_title_validation(self, sample_workspace_data):
        """Test title validation rules."""
        # Empty title
        with pytest.raises(ValueError, match="Title cannot be empty"):

            sample_workspace_data["title"] = ""
            Workspace(**sample_workspace_data)

        # Title too long
        with pytest.raises(ValueError, match="Title cannot exceed 255 characters"):
            sample_workspace_data["title"] = "a" * 256
            Workspace(**sample_workspace_data)

    def test_plan_type_validation(self, sample_workspace_data):
        """Test plan type validation rules."""
        # Invalid plan type
        with pytest.raises(ValueError, match="Invalid plan type"):
            sample_workspace_data["plan_type"] = "invalid"
            Workspace(**sample_workspace_data)

        # Valid plan types
        for plan in ['free', 'basic', 'pro', 'enterprise']:
            sample_workspace_data["plan_type"] = plan
            workspace = Workspace(**sample_workspace_data)
            assert workspace.plan_type == plan

    def test_description_validation(self, sample_workspace_data):
        """Test description validation rules."""
        # Description too long
        with pytest.raises(ValueError, match="Description cannot exceed 1000 characters"):
            sample_workspace_data["description"] = "a" * 1001
            Workspace(**sample_workspace_data)

class TestWorkspaceRelationships:
    """Test suite for Workspace model relationships."""

    def test_teams_relationship(self, sample_workspace_data):
        """Test teams relationship."""
        workspace = Workspace(**sample_workspace_data)
        assert hasattr(workspace, 'teams')
        assert len(workspace.teams) == 0

    def test_members_relationship(self, sample_workspace_data):
        """Test members relationship."""
        workspace = Workspace(**sample_workspace_data)
        assert hasattr(workspace, 'members')
        assert len(workspace.members) == 0

class TestWorkspaceBusinessLogic:
    """Test suite for Workspace business logic."""

    def test_is_pro_or_enterprise(self, sample_workspace_data):
        pass
        """Test pro/enterprise plan checking."""
        # workspace = Workspace(**sample_workspace_data)
        # assert not workspace.is_pro_or_enterprise()

        # workspace.plan_type = 'pro'
        # assert workspace.is_pro_or_enterprise()

        # workspace.plan_type = 'enterprise'
        # assert workspace.is_pro_or_enterprise()

@pytest.mark.asyncio
class TestWorkspaceAsync:
    """Test suite for Workspace model async operations."""

    async def test_get_active_teams_async(self, sample_workspace_data):
        pass
        """Test getting active teams asynchronously."""
        # workspace = Workspace(**sample_workspace_data)
        # teams = await workspace.get_active_teams()
        # assert isinstance(teams, list)