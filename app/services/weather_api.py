"""
Open-Meteo API klienti (plan 2.1, 2.5, 2.6-bo'limlari).
- Kalitsiz, bepul, 16 kungacha aniq prognoz.
- Har bir so'rov oldin kesh tekshiriladi (10km katak + TTL).
- Tarmoq xatosi bo'lsa None qaytaradi — chaqiruvchi tomon
  keshlangan ma'lumot yoki xushmuomala xato xabari bilan ishlaydi
  (4.3-bo'lim: "foydalanuvchi hech qachon bo'sh ekran ko'rmaydi").
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from app.config import get_settings
from app.services.cache import geocoding_cache, grid_key, weather_cache

logger = logging.getLogger("falak.weather_api")
_settings = get_settings()

_HOURLY_FIELDS = ",".join([
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation_probability",
    "weather_code",
    "wind_speed_10m",
    "uv_index",
])
_DAILY_FIELDS = ",".join([
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_probability_max",
    "wind_speed_10m_max",
    "uv_index_max",
    "sunrise",
    "sunset",
])


async def fetch_forecast(lat: float, lon: float) -> Optional[dict[str, Any]]:
    """Bugungi + 7 kunlik prognozni qaytaradi (keshlangan bo'lishi mumkin)."""
    key = grid_key(lat, lon)
    cached = weather_cache.get(key)
    if cached is not None:
        return cached

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": _HOURLY_FIELDS,
        "daily": _DAILY_FIELDS,
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,relative_humidity_2m",
        "timezone": "auto",
        "forecast_days": 7,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(_settings.open_meteo_forecast_url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Open-Meteo forecast xatosi: %s", exc)
        return None

    weather_cache[key] = data
    return data


async def geocode_city(query: str, count: int = 5) -> Optional[list[dict[str, Any]]]:
    """Shahar/qishloq nomidan koordinatalar ro'yxatini qaytaradi."""
    cache_key = f"geo:{query.strip().lower()}"
    cached = geocoding_cache.get(cache_key)
    if cached is not None:
        return cached

    params = {"name": query, "count": count, "language": "ru", "format": "json"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(_settings.open_meteo_geocoding_url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Open-Meteo geocoding xatosi: %s", exc)
        return None

    results = data.get("results") or []
    geocoding_cache[cache_key] = results
    return results


async def reverse_geocode(lat: float, lon: float, lang: str = "ru") -> Optional[str]:
    """Koordinatadan shahar/tuman nomini topadi.

    Eslatma: Open-Meteo'da teskari geokodlash yo'q (u faqat nom -> koordinata
    ishlaydi, plan 2.1-bo'lim). Bot chatida "📍 Joylashuvni yuborish" tugmasi
    orqali kelgan koordinatani odam o'qiy oladigan nomga aylantirish uchun
    BigDataCloud'ning bepul, kalitsiz reverse-geocoding xizmati qo'shildi.
    Bu servis ishlamay qolsa, chaqiruvchi tomon koordinatani o'zini
    ko'rsatishga qaytadi (4.3-bo'lim: xato holatlari ham dizayn qismi)."""
    cache_key = f"rev:{grid_key(lat, lon)}"
    cached = geocoding_cache.get(cache_key)
    if cached is not None:
        return cached

    params = {"latitude": lat, "longitude": lon, "localityLanguage": lang}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://api.bigdatacloud.net/data/reverse-geocode-client", params=params
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Reverse geocoding xatosi: %s", exc)
        return None

    name = data.get("city") or data.get("locality") or data.get("principalSubdivision")
    if name:
        geocoding_cache[cache_key] = name
    return name
