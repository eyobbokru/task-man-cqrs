from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

from sqlalchemy import func, select, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from sqlalchemy.exc import SQLAlchemyError

from domain.exceptions import DatabaseError
from domain.models.team import Team, TeamMember
from application.queries.base_queries import BaseQueryHandler, PaginatedResult, PaginationParams
from infrastructure.repositories.team_repository import TeamRepository

from core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class TeamFilters:
    """Filters for team queries."""
    name: Optional[str] = None
    workspace_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

class TeamQueries(BaseQueryHandler[Team, TeamFilters]):
    """
    Handles all read operations for Teams and TeamMembers with pagination and filtering support.
    """
    def __init__(self, repository: TeamRepository):
        self._repository = repository

    def _build_filters(self, query: Select, filters: TeamFilters) -> Select:
        """Apply filters to the query."""
        query = super()._build_filters(query, filters)
       
        if filters.created_after:
            query = query.where(Team.created_at >= filters.created_after)

        if filters.created_before:
            query = query.where(Team.created_at <= filters.created_before)
        
        return query

    async def get_teams(
        self,
        session: AsyncSession,
        filters: Optional[TeamFilters] = None,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResult:
        """
        Get teams with optional filtering and pagination.
        
        Args:
            session: Database session
            filters: Optional filtering parameters
            pagination: Optional pagination parameters
            
        Returns:
            PaginatedResult containing teams and pagination info
        """
        return await self.execute_paginated_query(session, filters, pagination)


    async def get_workspace_teams(
        self,
        session: AsyncSession,
        workspace_id: UUID,
        include_inactive: bool = False
    ) -> List[Team]:
        """Get all teams in a workspace."""
        try:
            filters = TeamFilters(workspace_id=workspace_id)
            if not include_inactive:
                filters.is_active = True
                
            result = await self.get_teams(
                session,
                filters=filters,
                pagination=PaginationParams(per_page=100)  # Adjust as needed
            )
            return result.items
            
        except SQLAlchemyError as e:
            logger.error("workspace_teams_query_error", error=str(e))
            raise DatabaseError(f"Error fetching workspace teams: {str(e)}")

    async def get_team_member(
        self,
        session: AsyncSession,
        team_id: UUID,
        user_id: UUID
    ) -> Optional[TeamMember]:
        """Get a specific team member."""
        try:
            query = select(TeamMember).where(
                and_(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == user_id
                )
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
            
        except SQLAlchemyError as e:
            logger.error("team_member_query_error", error=str(e))
            raise DatabaseError(f"Error fetching team member: {str(e)}")

    async def get_team_members(
        self,
        session: AsyncSession,
        team_id: UUID,
        role: Optional[str] = None
    ) -> List[TeamMember]:
        """Get all members of a team, optionally filtered by role."""
        try:
            query = select(TeamMember).where(TeamMember.team_id == team_id)
            if role:
                query = query.where(TeamMember.role == role)
            
            result = await session.execute(query)
            return list(result.scalars().all())
            
        except SQLAlchemyError as e:
            logger.error("team_members_query_error", error=str(e))
            raise DatabaseError(f"Error fetching team members: {str(e)}")

    async def get_user_teams(
        self,
        session: AsyncSession,
        user_id: UUID,
        workspace_id: Optional[UUID] = None
    ) -> List[Team]:
        """Get all teams a user is a member of, optionally filtered by workspace."""
        try:
            query = (
                select(Team)
                .join(TeamMember)
                .where(TeamMember.user_id == user_id)
                .where(Team.is_active == True)
            )
            
            if workspace_id:
                query = query.where(Team.workspace_id == workspace_id)
            
            result = await session.execute(query)
            return list(result.scalars().all())
            
        except SQLAlchemyError as e:
            logger.error("user_teams_query_error", error=str(e))
            raise DatabaseError(f"Error fetching user teams: {str(e)}")

    async def get_team_member_count(
        self,
        session: AsyncSession,
        team_id: UUID
    ) -> int:
        """Get the total number of members in a team."""
        try:
            query = (
                select(func.count())
                .select_from(TeamMember)
                .where(TeamMember.team_id == team_id)
            )
            result = await session.execute(query)
            return result.scalar_one()
            
        except SQLAlchemyError as e:
            logger.error("team_member_count_error", error=str(e))
            raise DatabaseError(f"Error counting team members: {str(e)}")