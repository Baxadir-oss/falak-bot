"""
Falak Weather Bot — asosiy kirish nuqtasi.

Plan 2.1-band 1 (eng muhim arxitektura qarori): aiogram va FastAPI
ALOHIDA jarayon EMAS — bitta Python jarayonida, bitta event loop'da
ishlaydi. Telegram yangilanishlari webhook orqali keladi va
`/webhook` route'i ichidan to'g'ridan-to'g'ri `dp.feed_update()`ga
uzatiladi (ikkinchi jarayon yo'q).

Ishga tushirish (lokal test uchun):
    uvicorn app.main:app --host 127.0.0.1 --port 8080

Productionda systemd orqali ishga tushiriladi — qarang: deploy/falak-bot.service
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes
from app.bot.handlers import location, settings as settings_handlers, start, weather
from app.bot.middlewares import LoadUserMiddleware
from app.config import get_settings
from app.services.db import Database
from app.services.scheduler import setup_scheduler

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("falak.main")


def build_dispatcher(db: Database) -> Dispatcher:
    """Barcha router'larni va middleware'ni bitta Dispatcher'ga yig'adi."""
    dp = Dispatcher()
    dp["db"] = db  # aiogram avtomatik ravishda buni har bir handler'ga uzatadi

    dp.update.outer_middleware(LoadUserMiddleware(db))

    dp.include_router(start.router)
    dp.include_router(location.router)
    dp.include_router(weather.router)
    dp.include_router(settings_handlers.router)
    return dp


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Ishga tushirish ---
    db = Database(settings.db_path)
    await db.connect()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = build_dispatcher(db)

    app.state.bot = bot
    app.state.dp = dp
    app.state.db = db

    try:
        await bot.set_webhook(
            url=settings.webhook_url,
            secret_token=settings.webhook_secret,
            drop_pending_updates=False,
            allowed_updates=dp.resolve_used_update_types(),
        )
        logger.info("Webhook muvaffaqiyatli o'rnatildi: %s", settings.webhook_url)
    except Exception:
        logger.exception(
            "Webhook o'rnatishda xato — BOT_TOKEN va WEBHOOK_BASE_URL to'g'riligini tekshiring."
        )
        raise

    scheduler = setup_scheduler(bot, db)
    scheduler.start()
    logger.info("Kunlik bildirishnoma scheduler'i ishga tushdi.")

    yield

    # --- To'xtatish ---
    scheduler.shutdown(wait=False)
    await bot.session.close()
    await db.close()
    logger.info("Falak bot to'xtatildi.")


app = FastAPI(title="Falak Weather Bot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(routes.router)
app.add_api_route(settings.webhook_path, routes.telegram_webhook, methods=["POST"])
