class ModeratorService:
    moderators: dict[int, None]

    def __init__(self, database):
        self.database = database
        self.refresh_moderators()

    async def refresh_moderators(self):
        self.moderators = await self.database.select_moderators()

    def have_access(self, isu: int) -> bool:
        return isu in self.moderators
