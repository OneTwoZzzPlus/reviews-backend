from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy import select
from core.database import AsyncSession, get_database
from models.content import Moderator


class ModeratorService:
    _moderators_cache: set[int] = set()

    def __init__(self, session: AsyncSession):
        self.session = session

    async def refresh_moderators(self) -> None:
        stmt = select(Moderator.isu).where(Moderator.access)
        res = await self.session.scalars(stmt)
        ModeratorService._moderators_cache = set(res.all())

    async def have_access(self, isu: int) -> bool:
        if not ModeratorService._moderators_cache:
            await self.refresh_moderators()
        return isu in ModeratorService._moderators_cache


async def get_moderator_service(
    session: AsyncSession = Depends(get_database),
) -> AsyncGenerator[ModeratorService, None]:
    yield ModeratorService(session=session)
