from aiogram.filters import BaseFilter
from aiogram.types import Message
from database.db import cur


class IsAdmin(BaseFilter):
    def __init__(self, admin_ids: int) -> None:
        self.admin_ids = admin_ids

    async def __call__(self, message: Message) -> bool:
        cur.execute(f"SELECT is_auth FROM accounts WHERE tg_id == {message.from_user.id}")
        obj = cur.fetchall()
        return str(obj[0][0]) == str(self.admin_ids)
