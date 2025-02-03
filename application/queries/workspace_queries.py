from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from sqlalchemy.exc import SQLAlchemyError

from application.queries.base_queries import BaseQueryHandler, PaginatedResult, PaginationParams
from core.logging import get_logger
from domain.models.workspace import Workspace
from domain.exceptions import WorkspaceNotFoundError, DatabaseError


logger = get_logger(__name__)



@dataclass
class WorkspaceFilters:
    """Filters for workspace queries."""
    title: Optional[str] = None
    plan_type: Optional[str] = None
    is_completed: Optional[bool] = None
    created_after: Optional[str] = None
    created_before: Optional[str] = None


class GetWorkspacesQuery(BaseQueryHandler[Workspace, WorkspaceFilters]):
    """Query handler for fetching multiple workspaces with filtering and pagination."""

    def _build_filters(self, query: Select, filters: WorkspaceFilters) -> Select:
        """Apply filters to the query."""
        
        query = super()._build_filters(query, filters)
        
        if filters.created_after:
            query = query.where(Workspace.created_at >= filters.created_after)

        if filters.created_before:
            query = query.where(Workspace.created_at <= filters.created_before)
        return query

    async def execute(
        self,
        session: AsyncSession,
        filters: Optional[WorkspaceFilters] = None,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResult:
        """
        Execute the workspace query with optional filtering and pagination.
        
        Args:
            session: Database session
            filters: Optional filtering parameters
            pagination: Optional pagination parameters
            
        Returns:
            PaginatedResult containing workspaces and pagination info
            
        Raises:
            DatabaseError: If there's an error executing the query
        """
        return await self.execute_paginated_query(session, filters, pagination)

class GetWorkspaceByIdQuery:
    """Query handler for fetching a single workspace by ID."""
    
    async def execute(
        self,
        session: AsyncSession,
        workspace_id: UUID
    ) -> Workspace:
        """
        Execute the workspace query by ID.
        
        Args:
            session: Database session
            workspace_id: UUID of the workspace to fetch
            
        Returns:
            Workspace instance
            
        Raises:
            WorkspaceNotFoundError: If workspace doesn't exist
            DatabaseError: If there's an error executing the query
        """
        try:
            logger.info("fetching_workspace", workspace_id=str(workspace_id))
            
            workspace = await session.get(Workspace, workspace_id)
            
            if not workspace:
                logger.warning(
                    "workspace_not_found",
                    workspace_id=str(workspace_id)
                )
                raise WorkspaceNotFoundError(
                f"Workspace {workspace_id} not found",
                )
            
            return workspace
            
        except SQLAlchemyError as e:
            logger.error(
                "workspace_query_error",
                error=str(e),
                workspace_id=str(workspace_id)
            )
            raise DatabaseError(f"Error fetching workspace: {str(e)}")