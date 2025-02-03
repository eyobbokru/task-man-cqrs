from uuid import UUID
import pytest
from datetime import datetime

from domain.models.workspace import Workspace


def test_workspace_creation():
    """Test that a workspace is created with correct default values."""
    workspace = Workspace(
        title="Test Workspace",
        description="Test Description",
        plan_type="free"
    )
    
    assert workspace.title == "Test Workspace"
    assert workspace.description == "Test Description"
    # assert workspace.is_completed == False
    assert workspace.plan_type == "free"


def test_workspace_validation():
    """Test workspace validation rules."""
    # Test empty title
    with pytest.raises(ValueError, match="Title cannot be empty"):
        Workspace(title="", description="Test")
    
    # Test title too long
    with pytest.raises(ValueError, match="Title cannot exceed 255 characters"):
        Workspace(title="a" * 256, description="Test")
    
    # Test invalid plan type
    with pytest.raises(ValueError, match="Invalid plan type"):
        Workspace(
            title="Test",
            plan_type="invalid"
        )
    
    # Test description too long
    with pytest.raises(ValueError, match="Description cannot exceed 1000 characters"):
        Workspace(
            title="Test",
            description="a" * 1001
        )

def test_workspace_custom_values():
    """Test that a workspace can be created with custom values."""
    custom_settings = {"theme": "dark"}
    workspace = Workspace(
        title="Custom Workspace",
        description="Custom Description",
        plan_type="pro",
        settings=custom_settings,
        is_completed=True
    )
    
    assert workspace.title == "Custom Workspace"
    assert workspace.description == "Custom Description"
    assert workspace.plan_type == "pro"
    assert workspace.settings == custom_settings
    assert workspace.is_completed == True