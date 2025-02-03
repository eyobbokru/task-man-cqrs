from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID

from domain.models.team import Team

class TeamBase(BaseModel):
    """Base schema for team data."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Engineering Team",
                "description": "Core engineering team",
                "settings": {
                    "default_role": "member",
                    "notifications_enabled": True
                }
            }
        }
    )

class TeamCreate(TeamBase):
    """Schema for creating a new team."""
    workspace_id: UUID

class TeamUpdate(BaseModel):
    """Schema for updating an existing team."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated Engineering Team",
                "is_active": True
            }
        }
    )

class TeamMemberBase(BaseModel):
    """Base schema for team member data."""
    role: str = Field(..., pattern="^(admin|member|guest)$")
    permissions: Optional[Dict[str, Any]] = Field(default_factory=dict)

class TeamResponse(TeamBase):
    """Schema for team response data."""
    id: UUID
    workspace_id: UUID
    owner_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, team: 'Team') -> "TeamResponse":
        return cls(
            id=team.id,
            workspace_id=team.workspace_id,
            owner_id=team.owner_id,
            name=team.name,
            description=team.description,
            settings=team.settings,
            is_active=team.is_active,
            created_at=team.created_at,
            updated_at=team.updated_at
        )

class PaginatedTeamResponse(BaseModel):
    """Schema for paginated team results."""
    items: List[TeamResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool