from uuid import UUID as UUID_TYPE
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import validates
from sqlalchemy.sql import expression

from infrastructure.database import Base

class Workspace(Base):
    """
    Represents a workspace entity in the system.
    
    A workspace is a container for organizing related content and configurations.
    It can have different plan types and customizable settings.
    
    Attributes:
        id (UUID): Unique identifier for the workspace
        title (str): Name/title of the workspace
        settings (Dict): JSON field containing workspace configurations
        plan_type (str): Type of subscription plan for the workspace
        description (str): Optional description of the workspace
        is_completed (bool): Flag indicating if workspace setup is completed
        created_at (datetime): Timestamp of workspace creation
        updated_at (datetime): Timestamp of last workspace update
    """
    __tablename__ = "workspaces"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    settings = Column(
        JSON, 
        info={"description": "Includes theme, features, limits"},
        nullable=True,
        server_default=expression.null()
    )
    plan_type = Column(
        String(50), 
        nullable=False,
        server_default='free'
    )
    description = Column(
        String(1000), 
        nullable=True,
        server_default=expression.null()
    )
    is_completed = Column(
        Boolean, 
        nullable=False,
        default=False,
        server_default=expression.false()
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Validation methods
    @validates('title')
    def validate_title(self, key: str, title: str) -> str:
        """Validate the workspace title."""
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")
        if len(title) > 255:
            raise ValueError("Title cannot exceed 255 characters")
        return title.strip()

    @validates('plan_type')
    def validate_plan_type(self, key: str, plan_type: str) -> str:
        """Validate the plan type."""
        valid_plans = {'free', 'basic', 'pro', 'enterprise'}
        if plan_type not in valid_plans:
            raise ValueError(f"Invalid plan type. Must be one of: {', '.join(valid_plans)}")
        return plan_type

    @validates('description')
    def validate_description(self, key: str, description: Optional[str]) -> Optional[str]:
        """Validate the workspace description."""
        if description and len(description) > 1000:
            raise ValueError("Description cannot exceed 1000 characters")
        return description.strip() if description else None

    def __repr__(self) -> str:
        """Return string representation of the workspace."""
        return f"<Workspace(id={self.id}, title='{self.title}', plan_type='{self.plan_type}')>"