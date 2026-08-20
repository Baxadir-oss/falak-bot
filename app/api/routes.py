"""
FastAPI route'lari. Bitta jarayon ichida ikkita vazifa (plan 2.1-band 1):
- /webhook — Telegram'dan kelgan yangilanishlarni aiogram Dispatcher'iga uzatadi
- /api/weather — Mini App uchun yengil JSON API
- /health — UptimeRobot kabi tashqi monitoring uchun (6-bo'lim)
"""
from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Query, Request

from app.config import get_settings
from app.services.weather_api import fetch_forecast

logger = logging.getLogger("falak.api")
router = APIRouter()
_settings = get_settings()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/api/weather")
async def api_weather(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
) -> dict:
    """Mini App shu endpoint orqali ob-havo ma'lumotini oladi
    (statik fayllar Cloudflare Pages'da, faqat bu API VPS'da — plan 2.2)."""
    data = await fetch_forecast(lat, lon)
    if data is None:
        raise HTTPException(status_code=503, detail="Weather service temporarily unavailable")
    return data


async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    """Plan 2.1-band 3: webhook xavfsizligi — Telegram yuboradigan
    maxfiy tokenni har bir so'rovda tekshiramiz. Mos kelmasa, so'rov
    Telegramdan emas deb hisoblanadi va rad etiladi."""
    if x_telegram_bot_api_secret_token != _settings.webhook_secret:
        logger.warning("Webhook: noto'g'ri secret token bilan so'rov keldi.")
        raise HTTPException(status_code=401, detail="Invalid secret token")

    bot: Bot = request.app.state.bot
    dp: Dispatcher = request.app.state.dp

    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}
