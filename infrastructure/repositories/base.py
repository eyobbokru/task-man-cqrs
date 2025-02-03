from typing import Generic, TypeVar, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from core.logging import get_logger

logger = get_logger(__name__)

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType]):
        self.model = model

    async def create(self, db: AsyncSession, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        db.add(instance)
        await db.commit()
        await db.refresh(instance)
        logger.info(f"Created {self.model.__name__}", id=instance.id)
        return instance

    async def get(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession) -> List[ModelType]:
        query = select(self.model)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update(
        self, 
        db: AsyncSession,
        id: int,
        **kwargs
    ) -> Optional[ModelType]:
        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await db.execute(query)
        await db.commit()
        return result.scalar_one_or_none()

    async def delete(self, db: AsyncSession, id: int) -> bool:
        query = delete(self.model).where(self.model.id == id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0