from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.services.db import Database
from app.services.i18n import normalize_language


class LoadUserMiddleware(BaseMiddleware):
    """Har bir update kelganda foydalanuvchini DB'da topadi (yo'q bo'lsa
    yaratadi) va handler'larga `user` (dict) hamda `lang` (str) sifatida
    uzatadi — har bir handler'da qayta-qayta so'rov yozilmasligi uchun.

    Eslatma: bu klass ataylab "UserContextMiddleware" deb nomlanmagan —
    aiogram'ning ichki (built-in) middleware'i xuddi shu nomda va u
    `event_from_user`ni to'ldiradi (bizga aynan shu kerak, quyida
    ishlatiladi). Ikkalasini adashtirmaslik uchun nom boshqacha tanlandi."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        if tg_user is not None:
            user = await self.db.create_user_if_missing(
                tg_user.id, language=normalize_language(tg_user.language_code)
            )
            data["user"] = user
            data["lang"] = user["language"]
        return await handler(event, data)
