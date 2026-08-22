from __future__ import annotations

from aiogram import Bot, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.filters import MenuTextFilter
from app.services import i18n
from app.services.db import Database
from app.services.formatting import format_today, format_week
from app.services.weather_api import fetch_forecast, fetch_weather_bundle

router = Router(name="weather")


async def _has_location(message: Message, user: dict, lang: str) -> bool:
    if user.get("lat") is None:
        await message.answer(i18n.t("no_location_yet", lang))
        return False
    return True


@router.message(Command("bugun"))
@router.message(MenuTextFilter("menu_today"))
async def cmd_today(message: Message, user: dict, lang: str, bot: Bot) -> None:
    if not await _has_location(message, user, lang):
        return
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    # Prognoz + havo sifati PARALLEL so'raladi (weather_api.py) — ketma-ket
    # so'ralganda sezilarli sekinlashuv bo'lar edi.
    data, aqi = await fetch_weather_bundle(user["lat"], user["lon"])
    if data is None:
        await message.answer(i18n.t("error_api_down_no_cache", lang))
        return
    await message.answer(format_today(data, user["place_name"], lang, aqi=aqi))


@router.message(Command("hafta"))
@router.message(MenuTextFilter("menu_week"))
async def cmd_week(message: Message, user: dict, lang: str, bot: Bot) -> None:
    if not await _has_location(message, user, lang):
        return
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    # Haftalik jadvalda AQI ko'rsatilmaydi — shuning uchun bu yerda
    # qo'shimcha havo-sifati so'rovi yuborilmaydi (tezroq javob).
    data = await fetch_forecast(user["lat"], user["lon"])
    if data is None:
        await message.answer(i18n.t("error_api_down_no_cache", lang))
        return
    await message.answer(format_week(data, user["place_name"], lang))
