from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from domain.models.workspace import Workspace
from infrastructure.database import get_session

from application.commands.workspace_commands import CreateWorkspaceCommand, DeleteWorkspaceCommand, UpdateWorkspaceCommand
from application.queries.workspace_queries import GetWorkspacesQuery, GetWorkspaceByIdQuery, PaginationParams, WorkspaceFilters


from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
from core.logging import get_logger


logger = get_logger(__name__)



#schemas
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


router = APIRouter(
    prefix="/workspaces",
    tags=["workspaces"]
)

@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=201,
    summary="Create a new workspace"
)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    session: AsyncSession = Depends(get_session),
    # current_user: Any = Depends(get_current_user)
) -> WorkspaceResponse:
    """
    Create a new workspace with the provided data.
    
    Requires authentication. Returns the created workspace.
    """
    try:
        command = CreateWorkspaceCommand()
        workspace = await command.execute(
            session=session,
            **workspace_data.model_dump()
        )
        return WorkspaceResponse.from_orm(workspace)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    

@router.get(
    "",
    response_model=PaginatedWorkspaceResponse,
    summary="Get all workspaces"
)
async def get_workspaces(
    title: Optional[str] = Query(None, description="Filter by title"),
    plan_type: Optional[str] = Query(None, description="Filter by plan type"),
    is_completed: Optional[bool] = Query(None, description="Filter by completion status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    order_by: str = Query("created_at", description="Field to order by"),
    order_direction: str = Query("desc", pattern="^(asc|desc)$"),
    session: AsyncSession = Depends(get_session),
    # current_user: Any = Depends(get_current_user)
) -> PaginatedWorkspaceResponse:
    """
    Get all workspaces with optional filtering and pagination.
    
    Requires authentication. Returns paginated list of workspaces.
    """
    query = GetWorkspacesQuery()
    filters = WorkspaceFilters(
        title=title,
        plan_type=plan_type,
        is_completed=is_completed
    )
    pagination = PaginationParams(
        page=page,
        per_page=per_page,
        order_by=order_by,
        order_direction=order_direction
    )
    
    result = await query.execute(session, filters, pagination)

    return PaginatedWorkspaceResponse(
        items=[WorkspaceResponse.from_orm(w) for w in result.items],
        total=result.total,
        page=result.page,
        per_page=result.per_page,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev
    )


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Get a specific workspace"
)
async def get_workspace(
    workspace_id: UUID = Path(..., description="The ID of the workspace"),
    session: AsyncSession = Depends(get_session),
    # current_user: Any = Depends(get_current_user)
) -> WorkspaceResponse:
    """
    Get a specific workspace by ID.
    
    Requires authentication. Returns the workspace if found.
    """
    query = GetWorkspaceByIdQuery()
    workspace = await query.execute(session, workspace_id)
    return WorkspaceResponse.from_orm(workspace)


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="Update a workspace"
)
async def update_workspace(
    workspace_data: WorkspaceUpdate,
    workspace_id: UUID = Path(..., description="The ID of the workspace"),
    session: AsyncSession = Depends(get_session),
    # current_user: Any = Depends(get_current_user)
) -> WorkspaceResponse:
    """
    Update a workspace with the provided data.
    
    Requires authentication. Returns the updated workspace.
    """
    try:
        command = UpdateWorkspaceCommand()
        workspace = await command.execute(
            session=session,
            workspace_id=workspace_id,
            **workspace_data.model_dump(exclude_unset=True)
        )
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        return WorkspaceResponse.from_orm(workspace)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    

@router.delete(
    "/{workspace_id}",
    status_code=204,
    summary="Delete a workspace"
)
async def delete_workspace(
    workspace_id: UUID = Path(..., description="The ID of the workspace"),
    session: AsyncSession = Depends(get_session),
    # current_user: Any = Depends(get_current_user)
):
    """
    Delete a specific workspace.
    
    Requires authentication. Returns no content on success.
    """
    command = DeleteWorkspaceCommand()
    await command.execute(session, workspace_id)