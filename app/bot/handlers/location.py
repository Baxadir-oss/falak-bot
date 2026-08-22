from __future__ import annotations

import asyncio

from aiogram import Bot, F, Router
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.filters import MenuTextFilter
from app.bot.keyboards import main_menu_keyboard
from app.bot.states import LocationFlow
from app.services import i18n
from app.services.db import Database
from app.services.formatting import md_escape
from app.services.weather_api import fetch_weather_bundle, geocode_city, reverse_geocode

router = Router(name="location")


@router.message(F.location)
async def on_location_shared(message: Message, db: Database, lang: str, bot: Bot) -> None:
    if message.from_user is None or message.location is None:
        return
    lat, lon = message.location.latitude, message.location.longitude

    # Tezlik: haqiqiy kutish vaqtini emas, SEZILGAN tezlikni oshiradi —
    # foydalanuvchi darhol botning ishlayotganini ko'radi. Server geografik
    # jihatdan uzoqda joylashgan bo'lsa (masalan Railway'ning AQSh mintaqasi)
    # bu ayniqsa muhim, chunki so'rov-javob orasidagi vaqt sezilarli bo'ladi.
    await bot.send_chat_action(message.chat.id, ChatAction.FIND_LOCATION)

    place = await reverse_geocode(lat, lon, lang=lang)
    if not place:
        # 4.3-bo'lim: tarmoq xatosida ham foydalanuvchi bo'sh javob ko'rmaydi —
        # koordinataning o'zi zaxira sifatida ko'rsatiladi.
        place = f"{lat:.2f}, {lon:.2f}"

    await db.set_location(message.from_user.id, lat, lon, place)
    await message.answer(
        i18n.t("location_saved", lang, place=md_escape(place)),
        reply_markup=main_menu_keyboard(lang),
    )

    # Keshni oldindan "isitib qo'yish": foydalanuvchi "☀️ Bugun" tugmasini
    # bosguncha ob-havo ma'lumoti allaqachon keshda tayyor turadi — keyingi
    # so'rov deyarli bir zumda javob beradi. Xato chiqsa ham jim o'tkaziladi
    # (bu shunchaki oldindan tayyorlash, muvaffaqiyatsizligi kritik emas).
    asyncio.create_task(fetch_weather_bundle(lat, lon))


@router.message(MenuTextFilter("btn_search_city"))
async def on_search_city_button(message: Message, state: FSMContext, lang: str) -> None:
    await message.answer(i18n.t("ask_city_name", lang))
    await state.set_state(LocationFlow.waiting_city_name)


@router.message(LocationFlow.waiting_city_name)
async def on_city_name_entered(
    message: Message, state: FSMContext, db: Database, lang: str, bot: Bot
) -> None:
    if message.from_user is None:
        return
    query = (message.text or "").strip()
    if not query:
        return

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    results = await geocode_city(query)
    if not results:
        await message.answer(i18n.t("city_not_found", lang, query=md_escape(query)))
        return

    top = results[0]
    place = top.get("name") or query
    country = top.get("country")
    if country:
        place = f"{place}, {country}"

    await db.set_location(message.from_user.id, top["latitude"], top["longitude"], place)
    await state.clear()
    await message.answer(
        i18n.t("location_saved", lang, place=md_escape(place)),
        reply_markup=main_menu_keyboard(lang),
    )
    asyncio.create_task(fetch_weather_bundle(top["latitude"], top["longitude"]))
