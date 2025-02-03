
#schemas
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID

from domain.models.workspace import Workspace


class WorkspaceBase(BaseModel):
    """Base schema for workspace data."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    plan_type: str = Field(
        "free",
        pattern="^(free|basic|pro|enterprise)$"
    )
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "My Project Workspace",
                "description": "A workspace for my team's project",
                "plan_type": "pro",
                "settings": {
                    "theme": "dark",
                    "notification_enabled": True
                }
            }
        }
    )

class WorkspaceCreate(WorkspaceBase):
    """Schema for creating a new workspace."""
    pass

class WorkspaceUpdate(BaseModel):
    """Schema for updating an existing workspace."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    plan_type: Optional[str] = Field(
        None,
        pattern="^(free|basic|pro|enterprise)$"
    )
    settings: Optional[Dict[str, Any]] = None
    is_completed: Optional[bool] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Updated Project Workspace",
                "is_completed": True
            }
        }
    )

class WorkspaceResponse(WorkspaceBase):
    """Schema for workspace response data."""
    id: UUID
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, workspace: Workspace) -> "WorkspaceResponse":
        return cls(
            id=workspace.id,
            title=workspace.title,
            description=workspace.description,
            plan_type=workspace.plan_type,
            settings=workspace.settings,
            is_completed=workspace.is_completed,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at
        )


class PaginatedWorkspaceResponse(BaseModel):
    """Schema for paginated workspace results."""
    items: List[WorkspaceResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
