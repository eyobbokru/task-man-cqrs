from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from sqlalchemy.exc import SQLAlchemyError

from core.logging import get_logger
from domain.models.workspaces import Workspace
from domain.exceptions import WorkspaceNotFoundError, DatabaseError

logger = get_logger(__name__)

@dataclass
class PaginationParams:
    """Parameters for pagination."""
    page: int = 1
    per_page: int = 20
    order_by: str = "created_at"
    order_direction: str = "desc"

@dataclass
class WorkspaceFilters:
    """Filters for workspace queries."""
    title: Optional[str] = None
    plan_type: Optional[str] = None
    is_completed: Optional[bool] = None
    created_after: Optional[str] = None
    created_before: Optional[str] = None

@dataclass
class PaginatedResult:
    """Container for paginated results."""
    items: List[Any]
    total: int
    page: int
    per_page: int
    total_pages: int

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1

class GetWorkspacesQuery:
    """Query handler for fetching multiple workspaces with filtering and pagination."""

    def _build_filters(self, query: Select, filters: WorkspaceFilters) -> Select:
        """Apply filters to the query."""
        conditions = []
        
        if filters.title:
            conditions.append(Workspace.title.ilike(f"%{filters.title}%"))
        
        if filters.plan_type:
            conditions.append(Workspace.plan_type == filters.plan_type)
        
        if filters.is_completed is not None:
            conditions.append(Workspace.is_completed == filters.is_completed)
        
        if filters.created_after:
            conditions.append(Workspace.created_at >= filters.created_after)
        
        if filters.created_before:
            conditions.append(Workspace.created_at <= filters.created_before)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        return query

    def _apply_pagination(
        self,
        query: Select,
        pagination: PaginationParams
    ) -> Select:
        """Apply pagination parameters to the query."""
        # Validate order_by field
        if not hasattr(Workspace, pagination.order_by):
            logger.warning(
                "invalid_order_by_field",
                field=pagination.order_by,
                fallback="created_at"
            )
            pagination.order_by = "created_at"

        # Apply ordering
        order_func = desc if pagination.order_direction == "desc" else asc
        query = query.order_by(order_func(getattr(Workspace, pagination.order_by)))

        # Apply pagination
        offset = (pagination.page - 1) * pagination.per_page
        query = query.offset(offset).limit(pagination.per_page)

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
        try:
            # Initialize query
            query = select(Workspace)
            
            # Apply filters if provided
            if filters:
                query = self._build_filters(query, filters)
            
            # Get total count for pagination
            count_query = select(Workspace)
            if filters:
                count_query = self._build_filters(count_query, filters)
            total = await session.scalar(
                select(func.count()).select_from(count_query.subquery())
            )
            
            # Apply pagination
            pagination = pagination or PaginationParams()
            query = self._apply_pagination(query, pagination)
            
            # Execute query
            logger.info(
                "fetching_workspaces",
                filters=filters.__dict__ if filters else None,
                pagination=pagination.__dict__
            )
            
            result = await session.execute(query)
            items = result.scalars().all()
            
            total_pages = (total + pagination.per_page - 1) // pagination.per_page
            
            return PaginatedResult(
                items=items,
                total=total,
                page=pagination.page,
                per_page=pagination.per_page,
                total_pages=total_pages
            )
            
        except SQLAlchemyError as e:
            logger.error(
                "workspace_query_error",
                error=str(e),
                filters=filters.__dict__ if filters else None
            )
            raise DatabaseError(f"Error fetching workspaces: {str(e)}")

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