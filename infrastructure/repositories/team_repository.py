from .base import BaseRepository
from domain.models.team import Team, TeamMember
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from core.logging import get_logger

logger = get_logger(__name__)

class TeamRepository(BaseRepository[Team]):
    """
    Base repository for Team entity operations.
    Extends the BaseRepository with Team-specific functionality.
    """
    
    def __init__(self):
        super().__init__(Team)