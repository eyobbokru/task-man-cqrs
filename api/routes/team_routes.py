from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from domain.models.team import Team
from infrastructure.database import get_session
from core.logging import get_logger
from application.commands.team_commands import TeamCommands
from application.queries.team_queries import (
    TeamQueries, TeamFilters, PaginationParams
)
from infrastructure.schema.team_schemas  import (
    TeamCreate, TeamUpdate, TeamResponse, PaginatedTeamResponse
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/teams",
    tags=["teams"]
)

@router.post(
    "",
    response_model=TeamResponse,
    status_code=201,
    summary="Create a new team"
)
async def create_team(
    team_data: TeamCreate,
    session: AsyncSession = Depends(get_session),
) -> TeamResponse:
    """Create a new team in the specified workspace."""
    try:
        command = TeamCommands()
        team = await command.create_team(
            session=session,
            **team_data.model_dump()
        )
        return TeamResponse.from_orm(team)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get(
    "",
    response_model=PaginatedTeamResponse,
    summary="Get all teams"
)
async def get_teams(
    workspace_id: Optional[UUID] = Query(None, description="Filter by workspace ID"),
    name: Optional[str] = Query(None, description="Filter by name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    order_by: str = Query("created_at", description="Field to order by"),
    order_direction: str = Query("desc", pattern="^(asc|desc)$"),
    session: AsyncSession = Depends(get_session),
) -> PaginatedTeamResponse:
    """Get all teams with optional filtering and pagination."""
    queries = TeamQueries()
    filters = TeamFilters(
        name_like=name,
        workspace_id=workspace_id,
        is_active=is_active
    )
    pagination = PaginationParams(
        page=page,
        per_page=per_page,
        order_by=order_by,
        order_direction=order_direction
    )
    
    result = await queries.get_teams(session, filters, pagination)
    
    return PaginatedTeamResponse(
        items=[TeamResponse.from_orm(t) for t in result.items],
        total=result.total,
        page=result.page,
        per_page=result.per_page,
        total_pages=result.total_pages,
        has_next=result.page < result.total_pages,
        has_prev=result.page > 1
    )

@router.get(
    "/workspace/{workspace_id}",
    response_model=List[TeamResponse],
    summary="Get teams by workspace"
)
async def get_workspace_teams(
    workspace_id: UUID = Path(..., description="The workspace ID"),
    session: AsyncSession = Depends(get_session),
) -> List[TeamResponse]:
    """Get all teams in a specific workspace."""
    queries = TeamQueries()
    teams = await queries.get_workspace_teams(session, workspace_id)
    return [TeamResponse.from_orm(t) for t in teams]

@router.get(
    "/{team_id}",
    response_model=TeamResponse,
    summary="Get a specific team"
)
async def get_team(
    team_id: UUID = Path(..., description="The team ID"),
    session: AsyncSession = Depends(get_session),
) -> TeamResponse:
    """Get a specific team by ID."""
    queries = TeamQueries()
    team = await queries.get_team_by_id(session, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamResponse.from_orm(team)

@router.patch(
    "/{team_id}",
    response_model=TeamResponse,
    summary="Update a team"
)
async def update_team(
    team_data: TeamUpdate,
    team_id: UUID = Path(..., description="The team ID"),
    session: AsyncSession = Depends(get_session),
) -> TeamResponse:
    """Update a team with the provided data."""
    try:
        command = TeamCommands()
        team = await command.update_team(
            session=session,
            team_id=team_id,
            **team_data.model_dump(exclude_unset=True)
        )
        return TeamResponse.from_orm(team)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.delete(
    "/{team_id}",
    status_code=204,
    summary="Delete a team"
)
async def delete_team(
    team_id: UUID = Path(..., description="The team ID"),
    session: AsyncSession = Depends(get_session),
):
    """Delete a specific team."""
    command = TeamCommands()
    await command.delete_team(session, team_id)

# Team Members endpoints
@router.post(
    "/{team_id}/members/{user_id}",
    response_model=TeamResponse,
    summary="Add team member"
)
async def add_team_member(
    team_id: UUID = Path(..., description="The team ID"),
    user_id: UUID = Path(..., description="The user ID"),
    role: str = Query("member", pattern="^(admin|member|guest)$"),
    session: AsyncSession = Depends(get_session),
) -> TeamResponse:
    """Add a new member to the team."""
    command = TeamCommands()
    team = await command.add_team_member(session, team_id, user_id, role)
    return TeamResponse.from_orm(team)

@router.delete(
    "/{team_id}/members/{user_id}",
    status_code=204,
    summary="Remove team member"
)
async def remove_team_member(
    team_id: UUID = Path(..., description="The team ID"),
    user_id: UUID = Path(..., description="The user ID"),
    session: AsyncSession = Depends(get_session),
):
    """Remove a member from the team."""
    command = TeamCommands()
    await command.remove_team_member(session, team_id, user_id)