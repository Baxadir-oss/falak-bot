"""
Ikkita kichik, lekin foydali hisob-kitob:
1. Shamol gradusini (0-360) kompas nuqtasi kalitiga o'girish.
2. Yevropa AQI raqamini (0-100+) tushunarli toifaga o'girish.
Ikkalasi ham hech qanday tashqi so'rov talab qilmaydi.
"""
from __future__ import annotations

_COMPASS_KEYS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def degrees_to_compass_key(degrees: float | None) -> str | None:
    if degrees is None:
        return None
    idx = round((degrees % 360) / 45) % 8
    return _COMPASS_KEYS[idx]


def aqi_category_key(aqi: int) -> str:
    """Yevropa AQI shkalasi (Open-Meteo standarti): 0-20 yaxshi,
    20-40 qoniqarli, 40-60 o'rtacha, 60-80 yomon, 80+ juda yomon."""
    if aqi < 20:
        return "good"
    if aqi < 40:
        return "fair"
    if aqi < 60:
        return "moderate"
    if aqi < 80:
        return "poor"
    return "very_poor"
