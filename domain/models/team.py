from uuid import UUID as UUID_TYPE
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import validates, relationship
from sqlalchemy.sql import expression

from infrastructure.database import Base

class Team(Base):
    """
    Represents a team entity within a workspace.
    
    A team is a group within a workspace that can contain multiple members
    and have its own settings and configurations.
    
    Attributes:
        id (UUID): Unique identifier for the team
        workspace_id (UUID): Reference to the parent workspace
        name (str): Name of the team
        description (str): Optional description of the team
        owner_id (UUID): Reference to the team owner
        settings (Dict): JSON field containing team configurations
        is_active (bool): Flag indicating if the team is active
        created_at (datetime): Timestamp of team creation
        updated_at (datetime): Timestamp of last team update
    """
    __tablename__ = "teams"
    
    # Primary and Foreign Keys
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    workspace_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('workspaces.id'),
        nullable=False,
        index=True
    )
    owner_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    # Basic fields
    name = Column(String(255), nullable=False, index=True)
    description = Column(
        String(1000),
        nullable=True,
        server_default=expression.null()
    )
    settings = Column(
        JSON,
        info={"description": "Team-specific settings and configurations"},
        nullable=True,
        server_default=expression.null()
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=expression.true()
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

    # Relationships
    workspace = relationship("Workspace", back_populates="teams")
    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("TeamMember", back_populates="team")

    # Validation methods
    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        """Validate the team name."""
        if not name or not name.strip():
            raise ValueError("Team name cannot be empty")
        if len(name) > 255:
            raise ValueError("Team name cannot exceed 255 characters")
        return name.strip()

    @validates('description')
    def validate_description(self, key: str, description: Optional[str]) -> Optional[str]:
        """Validate the team description."""
        if description and len(description) > 1000:
            raise ValueError("Description cannot exceed 1000 characters")
        return description.strip() if description else None

    @validates('settings')
    def validate_settings(self, key: str, settings: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate the team settings."""
        if settings is not None and not isinstance(settings, dict):
            raise ValueError("Settings must be a dictionary")
        return settings

    def __repr__(self) -> str:
        """Return string representation of the team."""
        return f"<Team(id={self.id}, name='{self.name}', workspace_id='{self.workspace_id}')>"
    

class TeamMember(Base):
    """
    Represents a team membership entity in the system.
    
    Links users to teams with specific roles and permissions. Each team member
    can have different access levels and customized permissions within their team.
    
    Attributes:
        id (UUID): Unique identifier for the team membership
        team_id (UUID): Reference to the team
        user_id (UUID): Reference to the user
        role (str): Role of the member (admin, member, or guest)
        permissions (Dict): JSON field containing custom permissions
        created_at (datetime): Timestamp of membership creation
        updated_at (datetime): Timestamp of last membership update
    """
    __tablename__ = "team_members"
    
    # Primary and Foreign Keys
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    team_id = Column(
        UUID(as_uuid=True),
        ForeignKey('teams.id'),
        nullable=False,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    
    # Role and Permissions
    role = Column(
        String(50),
        nullable=False,
        default='member',
        server_default='member'
    )
    permissions = Column(
        JSON,
        info={"description": "Custom permissions for the team member"},
        nullable=True,
        server_default=expression.null()
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

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")

    # Class variables
    VALID_ROLES = {'admin', 'member', 'guest'}

    # Validation methods
    @validates('role')
    def validate_role(self, key: str, role: str) -> str:
        """Validate the team member role."""
        if not role or not role.strip():
            raise ValueError("Role cannot be empty")
        role = role.lower().strip()
        if role not in self.VALID_ROLES:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(self.VALID_ROLES)}")
        return role

    @validates('permissions')
    def validate_permissions(self, key: str, permissions: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate the team member permissions."""
        if permissions is not None:
            if not isinstance(permissions, dict):
                raise ValueError("Permissions must be a dictionary")
            
            # Validate permissions structure if needed
            # Add custom validation logic here based on your permissions schema
            
        return permissions

    def __repr__(self) -> str:
        """Return string representation of the team membership."""
        return f"<TeamMember(id={self.id}, team_id='{self.team_id}', user_id='{self.user_id}', role='{self.role}')>"