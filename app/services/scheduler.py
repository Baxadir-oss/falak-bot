"""
Kunlik xabar (plan 3.6-bo'lim). APScheduler har daqiqada SQLite'dan
"hozir kimningdir yuborish vaqtimi" deb tekshiradi va mos foydalanuvchilarga
yuboradi. Qo'shimcha RAM sarfi ~5-10MB — 0.5GB byudjetga mos.

Eslatma (soddalashtirish): hozirgi versiyada barcha foydalanuvchilar uchun
bitta server vaqt zonasi (Asia/Tashkent) ishlatiladi. Har bir foydalanuvchi
uchun individual vaqt zonasini qo'llab-quvvatlash (masalan, Mini App'dan
brauzer vaqt zonasini olib `users.tz_name`ga yozish) — keyingi bosqichda
qo'shsa bo'ladigan kengaytma.
"""
from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.db import Database
from app.services.formatting import format_daily_notification
from app.services.weather_api import fetch_forecast

logger = logging.getLogger("falak.scheduler")

# MUHIM: bu yerda ataylab qatiy ZoneInfo obyekti ishlatiladi, oddiy
# datetime.now() emas. Ko'pchilik VPS provayderlari serverni standart
# UTC vaqtida sozlaydi — agar shu yerda datetime.now() (naive, server
# vaqti) ishlatilganda, foydalanuvchi "7:00" da xabar kutayotganda,
# xabar aslida UTC bo'yicha soat 7:00 da (ya'ni Toshkent vaqti bilan
# taxminan 12:00-13:00 da) ketib qolar edi. Shu sababli har doim aniq
# vaqt zonasi bilan datetime.now(TZ) chaqiriladi — server sozlamasidan
# butunlay mustaqil ishlaydi.
TZ = ZoneInfo("Asia/Tashkent")


async def _send_due_notifications(bot: Bot, db: Database) -> None:
    now = datetime.now(TZ)
    today_str = now.date().isoformat()
    try:
        users = await db.get_users_due_for_notification(now.hour, now.minute, today_str)
    except Exception:
        logger.exception("Bildirishnoma uchun foydalanuvchilarni olishda xato.")
        return

    for user in users:
        try:
            data = await fetch_forecast(user["lat"], user["lon"])
            if data is None:
                # API vaqtincha javob bermasa — bugun jim o'tkazamiz, ertaga
                # qayta uriniladi. Eski/noto'g'ri ma'lumot yuborishdan yaxshi.
                continue
            text = format_daily_notification(data, user["place_name"], user["language"])
            await bot.send_message(user["tg_id"], text)
            await db.mark_notified(user["tg_id"], today_str)
        except Exception:
            logger.exception("Kunlik xabar yuborishda xato: tg_id=%s", user["tg_id"])


def setup_scheduler(bot: Bot, db: Database) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TZ)
    scheduler.add_job(
        _send_due_notifications,
        trigger=CronTrigger(second=0, timezone=TZ),  # har daqiqaning boshida ishga tushadi
        args=[bot, db],
        id="daily_weather_notifications",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=30,
    )
    return scheduler
