from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.filters import MenuTextFilter
from app.bot.keyboards import language_keyboard, location_request_keyboard, settings_keyboard
from app.bot.states import SettingsFlow
from app.services import i18n
from app.services.db import Database

router = Router(name="settings")


def _settings_text(user: dict, lang: str) -> str:
    lines = [i18n.t("settings_title", lang), ""]
    if user.get("notify_enabled"):
        lines.append(
            i18n.t("settings_notify_status_on", lang, time=str(user.get("notify_hour", 7)).zfill(2))
        )
    else:
        lines.append(i18n.t("settings_notify_status_off", lang))
    return "\n".join(lines)


@router.message(Command("sozlamalar"))
@router.message(MenuTextFilter("menu_settings"))
async def cmd_settings(message: Message, user: dict, lang: str) -> None:
    await message.answer(
        _settings_text(user, lang),
        parse_mode="Markdown",
        reply_markup=settings_keyboard(lang, bool(user.get("notify_enabled"))),
    )


@router.callback_query(F.data == "notify:on")
async def on_notify_on(callback: CallbackQuery, db: Database, user: dict, lang: str) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    hour = user.get("notify_hour", 7)
    minute = user.get("notify_minute", 0)
    await db.set_notify(callback.from_user.id, True, hour, minute)
    if callback.message is not None:
        await callback.message.edit_text(i18n.t("notify_enabled", lang, time=str(hour).zfill(2)))
    await callback.answer()


@router.callback_query(F.data == "notify:off")
async def on_notify_off(callback: CallbackQuery, db: Database, lang: str) -> None:
    if callback.from_user is None:
        await callback.answer()
        return
    await db.set_notify(callback.from_user.id, False)
    if callback.message is not None:
        await callback.message.edit_text(i18n.t("notify_disabled", lang))
    await callback.answer()


@router.callback_query(F.data == "notify:time")
async def on_notify_time_request(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    if callback.message is not None:
        await callback.message.answer(i18n.t("ask_notify_time", lang))
    await state.set_state(SettingsFlow.waiting_notify_hour)
    await callback.answer()


@router.message(SettingsFlow.waiting_notify_hour)
async def on_notify_hour_entered(
    message: Message, state: FSMContext, db: Database, lang: str
) -> None:
    if message.from_user is None:
        return
    text = (message.text or "").strip()
    if not text.isdigit() or not (0 <= int(text) <= 23):
        await message.answer(i18n.t("notify_time_invalid", lang))
        return
    hour = int(text)
    await db.set_notify(message.from_user.id, True, hour, 0)
    await state.clear()
    await message.answer(i18n.t("notify_enabled", lang, time=str(hour).zfill(2)))


@router.callback_query(F.data == "settings:language")
async def on_change_language(callback: CallbackQuery, lang: str) -> None:
    if callback.message is not None:
        await callback.message.answer(i18n.t("choose_language_prompt", lang), reply_markup=language_keyboard())
    await callback.answer()


@router.callback_query(F.data == "settings:location")
async def on_change_location(callback: CallbackQuery, lang: str) -> None:
    if callback.message is not None:
        await callback.message.answer(
            i18n.t("ask_location", lang), reply_markup=location_request_keyboard(lang)
        )
    await callback.answer()
