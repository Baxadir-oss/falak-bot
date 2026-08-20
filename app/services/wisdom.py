"""
Falak Hikmati (plan 7-bo'lim) — joriy ob-havo holatiga mos, har kuni
boshqacha hikmat tanlaydi. Hisoblash narxi deyarli nol — oddiy
lookup-jadval, AI kerak emas.
"""
from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path

from app.services.weather_codes import is_clear, is_rainy, is_snowy, is_stormy

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "wisdom.json"


@lru_cache
def _load() -> dict:
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _category_for_code(wmo_code: int) -> str:
    if is_stormy(wmo_code):
        return "stormy"
    if is_snowy(wmo_code):
        return "snowy"
    if is_rainy(wmo_code):
        return "rainy"
    if is_clear(wmo_code):
        return "clear"
    return "cloudy"


def daily_wisdom(wmo_code: int, lang: str, for_date: date | None = None) -> str:
    """Berilgan ob-havo holati va tilga mos, shu kun uchun barqaror
    (lekin kundan-kunga o'zgaruvchi) hikmatni qaytaradi."""
    data = _load()
    category = _category_for_code(wmo_code)
    options: list[str] = data.get(category, {}).get(lang) or data.get(category, {}).get("uz", [])
    if not options:
        return ""
    day = for_date or date.today()
    index = day.toordinal() % len(options)
    return options[index]
