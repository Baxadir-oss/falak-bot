"""
Amaliy tavsiyalar — oddiy qoidalar asosida (plan 3.5-bo'lim).
AI kerak emas, hisoblash arzon, RAM tejaydi.
"""
from __future__ import annotations

from app.services.weather_codes import is_rainy, is_snowy
from app.services.i18n import t

WIND_STRONG_KMH = 40
UV_HIGH = 6
TEMP_COLD_C = 5


def build_advice_lines(
    *, wmo_code: int, wind_speed_kmh: float, uv_index: float, temperature_c: float, lang: str
) -> list[str]:
    lines: list[str] = []
    if is_rainy(wmo_code) or is_snowy(wmo_code):
        lines.append(t("advice_umbrella", lang))
    if uv_index is not None and uv_index >= UV_HIGH:
        lines.append(t("advice_uv", lang))
    if wind_speed_kmh is not None and wind_speed_kmh >= WIND_STRONG_KMH:
        lines.append(t("advice_wind", lang))
    if temperature_c is not None and temperature_c <= TEMP_COLD_C:
        lines.append(t("advice_cold", lang))
    return lines
