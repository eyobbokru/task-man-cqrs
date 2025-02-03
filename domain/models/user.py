from uuid import UUID as UUID_TYPE
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import validates, relationship
from sqlalchemy.sql import expression

from domain.models.team import Team
from infrastructure.database import Base

class User(Base):
    """
    Represents a user entity in the system.
    
    A user can be a member of multiple workspaces and teams, with their own
    profile settings and security preferences.
    
    Attributes:
        id (UUID): Unique identifier for the user
        email (str): Unique email address for the user
        name (str): Full name of the user
        password_hash (str): Hashed password for security
        is_active (bool): Flag indicating if the user account is active
        profile (Dict): JSON field containing user profile data (avatar, phone, timezone)
        preferences (Dict): JSON field containing user preferences
        two_factor_enabled (bool): Flag indicating if 2FA is enabled
        last_login_at (datetime): Timestamp of user's last login
        created_at (datetime): Timestamp of user account creation
        updated_at (datetime): Timestamp of last user account update
    """
    __tablename__ = "users"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=expression.true()
    )
    
    # JSON fields
    profile = Column(
        JSON,
        info={"description": "User profile data including avatar, phone, timezone"},
        nullable=True,
        server_default=expression.null()
    )
    preferences = Column(
        JSON,
        info={"description": "User preferences and settings"},
        nullable=True,
        server_default=expression.null()
    )
    
    # Security fields
    two_factor_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=expression.false()
    )
    
    # Timestamp fields
    last_login_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
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
    workspace_memberships = relationship("WorkspaceMember", back_populates="user")
    team_memberships = relationship("TeamMember", back_populates="user")
    owned_teams = relationship("Team", foreign_keys=[Team.owner_id])
   
    # Validation methods
    @validates('email')
    def validate_email(self, key: str, email: str) -> str:
        """Validate the user email."""
        if not email or not email.strip():
            raise ValueError("Email cannot be empty")
        if len(email) > 255:
            raise ValueError("Email cannot exceed 255 characters")
        if '@' not in email:
            raise ValueError("Invalid email format")
        return email.lower().strip()

    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        """Validate the user name."""
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")
        if len(name) > 255:
            raise ValueError("Name cannot exceed 255 characters")
        return name.strip()

    @validates('profile')
    def validate_profile(self, key: str, profile: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate the user profile data."""
        if profile is not None:
            if not isinstance(profile, dict):
                raise ValueError("Profile must be a dictionary")
            
            # Validate required profile fields if present
            if 'timezone' in profile and not isinstance(profile['timezone'], str):
                raise ValueError("Timezone must be a string")
            if 'phone' in profile and not isinstance(profile['phone'], str):
                raise ValueError("Phone must be a string")
            if 'avatar' in profile and not isinstance(profile['avatar'], str):
                raise ValueError("Avatar must be a string URL")
                
        return profile

    @validates('preferences')
    def validate_preferences(self, key: str, preferences: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate the user preferences."""
        if preferences is not None and not isinstance(preferences, dict):
            raise ValueError("Preferences must be a dictionary")
        return preferences

    def __repr__(self) -> str:
        """Return string representation of the user."""
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"