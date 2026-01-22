class ModeratorService:
    moderators: dict[int, None]

    def __init__(self, database):
        self.database = database

    async def refresh_moderators(self):
        self.moderators = await self.database.select_moderators()

    async def have_access(self, isu: int) -> bool:
        await self.refresh_moderators()
        return isu in self.moderators
