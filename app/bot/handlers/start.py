from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import language_keyboard, location_request_keyboard
from app.services import i18n
from app.services.db import Database

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, lang: str) -> None:
    await message.answer(i18n.t("welcome", lang), reply_markup=language_keyboard())


@router.callback_query(F.data.startswith("lang:"))
async def on_language_chosen(callback: CallbackQuery, db: Database) -> None:
    new_lang = (callback.data or "").split(":", 1)[1]
    if new_lang not in i18n.SUPPORTED_LANGUAGES or callback.from_user is None:
        await callback.answer()
        return

    await db.set_language(callback.from_user.id, new_lang)

    if callback.message is not None:
        await callback.message.edit_text(i18n.t("lang_saved", new_lang))
        await callback.message.answer(
            i18n.t("ask_location", new_lang),
            reply_markup=location_request_keyboard(new_lang),
        )
    await callback.answer()
