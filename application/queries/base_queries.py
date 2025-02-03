from dataclasses import dataclass
from typing import Any, List

from domain.exceptions import DatabaseError


@dataclass
class PaginationParams:
    """Parameters for pagination."""
    page: int = 1
    per_page: int = 20
    order_by: str = "created_at"
    order_direction: str = "desc"

@dataclass
class PaginationParams:
    """Parameters for pagination."""
    page: int = 1
    per_page: int = 20
    order_by: str = "created_at"
    order_direction: str = "desc"

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


from typing import TypeVar, Generic, Optional, Any
from dataclasses import dataclass
from sqlalchemy import select, and_, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from sqlalchemy.exc import SQLAlchemyError

from core.logging import get_logger

from application.queries.base_queries import PaginatedResult, PaginationParams

logger = get_logger(__name__)

T = TypeVar('T')  # Type var for the model
F = TypeVar('F')  # Type var for the filters

class BaseQueryHandler(Generic[T, F]):
    """
    Base class for query handlers with common filtering and pagination functionality.
    
    Generic Parameters:
        T: The model type (e.g., Team, Workspace)
        F: The filter type (e.g., TeamFilters, WorkspaceFilters)
    """
    
    def __init__(self, model: type[T]):
        self.model = model

    def _build_filters(self, query: Select, filters: F) -> Select:
        """
        Apply filters to the query. Override this method to implement
        model-specific filtering logic.
        """
        conditions = []
        
        for field, value in filters.__dict__.items():
            if value is not None and hasattr(self.model, field):
                if isinstance(value, str) and field.endswith('_like'):
                    # Handle case-insensitive string search
                    field_name = field.replace('_like', '')
                    conditions.append(getattr(self.model, field_name).ilike(f"%{value}%"))
                else:
                    conditions.append(getattr(self.model, field) == value)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        return query

    def _apply_pagination(
        self,
        query: Select,
        pagination: PaginationParams
    ) -> Select:
        """Apply pagination parameters to the query."""
        if not hasattr(self.model, pagination.order_by):
            logger.warning(
                "invalid_order_by_field",
                field=pagination.order_by,
                fallback="created_at"
            )
            pagination.order_by = "created_at"

        order_func = desc if pagination.order_direction == "desc" else asc
        query = query.order_by(order_func(getattr(self.model, pagination.order_by)))

        offset = (pagination.page - 1) * pagination.per_page
        query = query.offset(offset).limit(pagination.per_page)

        return query

    async def execute_paginated_query(
        self,
        session: AsyncSession,
        filters: Optional[F] = None,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResult:
        """
        Execute a paginated query with optional filtering.
        """
        try:
            query = select(self.model)
            
            if filters:
                query = self._build_filters(query, filters)
            
            # Get total count for pagination
            count_query = select(self.model)
            if filters:
                count_query = self._build_filters(count_query, filters)
            total = await session.scalar(
                select(func.count()).select_from(count_query.subquery())
            )
            
            # Apply pagination
            pagination = pagination or PaginationParams()
            query = self._apply_pagination(query, pagination)
            
            logger.info(
                f"fetching_{self.model.__name__.lower()}s",
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
                f"{self.model.__name__.lower()}_query_error",
                error=str(e)
            )
            raise DatabaseError(f"Error fetching {self.model.__name__.lower()}s: {str(e)}")