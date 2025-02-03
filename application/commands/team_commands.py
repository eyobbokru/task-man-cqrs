from sqlite3 import IntegrityError
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.team import Team, TeamMember
from sqlalchemy.exc import SQLAlchemyError
from domain.exceptions import DatabaseError, NotFoundException, ValidationError
from core.logging import get_logger

from infrastructure.repositories.team_repository import TeamRepository

logger = get_logger(__name__)

class TeamCommands:
    """
    Handles all write operations for Teams and TeamMembers.
    """
    def __init__(self, repository: TeamRepository):
        self._repository = repository

    async def create_team(
        self,
        session: AsyncSession,
        workspace_id: UUID,
        owner_id: UUID,
        name: str,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Team:
        """Create a new team in the specified workspace."""
        team = Team(
            workspace_id=workspace_id,
            owner_id=owner_id,
            name=name,
            description=description,
            settings=settings or {},
            is_active=True
        )
        
        session.add(team)
        await session.flush()
        logger.info(f"Created new team: {team.id}")
        return team

    async def update_team(
        self,
        session: AsyncSession,
        team_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Team:
        """Update an existing team's information."""
        team = await self._repository.get_by_id(session, team_id)
        if not team:
            raise NotFoundException(f"Team {team_id} not found")

        if name is not None:
            team.name = name
        if description is not None:
            team.description = description
        if settings is not None:
            team.settings = settings
        if is_active is not None:
            team.is_active = is_active

        team.updated_at = datetime.now(timezone.utc)
        await session.flush()
        logger.info(f"Updated team: {team_id}")
        return team

    async def delete_team(
        self,
        session: AsyncSession,
        team_id: UUID,
        force: bool = False):
         
         """Delete a team."""
         try:
            team = await self._repository.get_by_id(session, team_id)

            if not team:
                raise NotFoundException(f"Team {team_id} not found")
            
            # Check if deletion is allowed for the teams.

            logger.info(
                "deleting_team",
                team_id=str(team_id),
            
                force=force
            )
            
            await self._repository.delete(session, team_id)
            logger.info(
                    "team_deleted_successfully",
                    team_id=str(team_id)
                )
            pass
         except IntegrityError as e:
            await session.rollback()
            logger.error(
                "team_deletion_integrity_error",
                team_id=str(team_id),
                error=str(e)
            )
            raise DatabaseError(
                f"Database integrity error while deleting team: {str(e)}"
            )
            
         except Exception as e:
            await session.rollback()
            logger.error(
                "team_deletion_error",
                team_id=str(team_id),
                error=str(e)
            )
            raise

    async def add_team_member(
        self,
        session: AsyncSession,
        team_id: UUID,
        user_id: UUID,
        role: str = 'member',
        permissions: Optional[Dict[str, Any]] = None
    ) -> TeamMember:
        """Add a new member to the team."""
        # Verify team exists
        team = await self._repository.get_by_id(session, team_id)
        if not team:
            raise NotFoundException(f"Team {team_id} not found")

        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role,
            permissions=permissions or {}
        )
        
        session.add(member)
        await session.flush()
        logger.info(f"Added member {user_id} to team {team_id}")
        return member

    async def update_team_member(
        self,
        session: AsyncSession,
        team_id: UUID,
        user_id: UUID,
        role: Optional[str] = None,
        permissions: Optional[Dict[str, Any]] = None
    ) -> TeamMember:
        """Update a team member's role or permissions."""
        query = await self._repository.queries.get_team_member(session, team_id, user_id)
        if not query:
            raise NotFoundException(f"Member {user_id} not found in team {team_id}")

        if role is not None:
            query.role = role
        if permissions is not None:
            query.permissions = permissions

        query.updated_at = datetime.now(timezone.utc)
        await session.flush()
        logger.info(f"Updated member {user_id} in team {team_id}")
        return query
    
    async def remove_team_member(
    self,
    session: AsyncSession,
    team_id: UUID,
    user_id: UUID
) -> None:
        """
        Remove a member from the team.
        
        Args:
            session: Database session
            team_id: ID of the team
            user_id: ID of the user to remove
            
        Raises:
            NotFoundException: If member is not found in team
            DatabaseError: If there's an error during removal
        """
        # Check if member exists
        member = await self._repository.queries.get_team_member(session, team_id, user_id)
        if not member:
            raise NotFoundException(f"Member {user_id} not found in team {team_id}")

        try:
            # Remove the member
            await session.delete(member)
            await session.flush()
            
            logger.info(
                "removed_team_member",
                team_id=str(team_id),
                user_id=str(user_id)
            )
        except SQLAlchemyError as e:
            logger.error(
                "team_member_removal_error",
                error=str(e),
                team_id=str(team_id),
                user_id=str(user_id)
            )
            raise DatabaseError(f"Error removing team member: {str(e)}")