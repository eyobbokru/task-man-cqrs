from .base import BaseRepository
from domain.models.workspace import Workspace
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from core.logging import get_logger

logger = get_logger(__name__)

class WorkspaceRepository(BaseRepository[Workspace]):
    def __init__(self):
        super().__init__(Workspace)