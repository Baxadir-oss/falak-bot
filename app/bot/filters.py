"""
Reply-klaviatura tugmalari lokalizatsiya qilingani uchun (masalan,
"☀️ Bugun" / "☀️ Сегодня" / "☀️ Today" / "☀️ Бүгін"), matn qaysi
tilda kelishidan qat'iy nazar mos handler'ni topish uchun maxsus filter.
"""
from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.services.i18n import SUPPORTED_LANGUAGES, t


class MenuTextFilter(BaseFilter):
    def __init__(self, key: str) -> None:
        self.key = key
        self._variants = {t(key, lang) for lang in SUPPORTED_LANGUAGES}

    async def __call__(self, message: Message) -> bool:
        return message.text in self._variants
