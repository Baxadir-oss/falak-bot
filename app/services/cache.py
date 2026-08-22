"""
In-process LRU+TTL kesh (plan 2.1 va 2.5-bo'limlari).
Alohida Redis jarayoni ishlatilmaydi — 0.5 GB byudjetda buning
hojati yo'q. Koordinata ~10 km katakka yaxlitlanadi, shu katak
uchun kesh bitta bo'ladi — bir hududdagi ko'p foydalanuvchi bitta
keshdan foydalanadi.
"""
from __future__ import annotations

from cachetools import TTLCache

from app.config import get_settings

_settings = get_settings()

# lat/lon'ni ~0.1 gradusgacha yaxlitlash taxminan 10 km'ga to'g'ri keladi
# ekvatorga yaqin kengliklarda; O'rta Osiyo kengliklarida ham yetarlicha yaqin.
_GRID_PRECISION = 1  # o'nlik xonalar soni (0.1 gradus)

weather_cache: TTLCache = TTLCache(
    maxsize=_settings.cache_max_size, ttl=_settings.cache_ttl_seconds
)
geocoding_cache: TTLCache = TTLCache(maxsize=500, ttl=6 * 3600)
# Havo sifati sekinroq o'zgaradi va tashqi xizmat qo'shimcha — TTL
# bir oz uzunroq, keshning o'zi sekinlikni yashiradi.
aqi_cache: TTLCache = TTLCache(maxsize=_settings.cache_max_size, ttl=3600)


def grid_key(lat: float, lon: float) -> str:
    """Koordinatani katakka yaxlitlab, kesh kaliti sifatida qaytaradi."""
    return f"{round(lat, _GRID_PRECISION)}:{round(lon, _GRID_PRECISION)}"
