"""
weather_codes.json'ni bitta marta yuklaydi va WMO kodini
(til, matn, emoji) ko'rinishiga o'giradi. Plan 3.7.2 / 5.5-bo'limlariga
mos — kod ichida hech qayerda ob-havo matni "qattiq yozilmaydi".
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "weather_codes.json"


class WeatherCodeEntry(TypedDict):
    uz: str
    ru: str
    en: str
    kk: str
    emoji: str


@lru_cache
def _load() -> dict[str, WeatherCodeEntry]:
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def describe(wmo_code: int, lang: str) -> str:
    """WMO kodi uchun berilgan tildagi sodda tavsifni qaytaradi."""
    table = _load()
    entry = table.get(str(wmo_code))
    if entry is None:
        # Noma'lum kod kelsa ham bot yiqilmasligi kerak (3-bo'lim: "hech qachon
        # bo'sh ekran ko'rmaydi" tamoyili shu yerda ham amal qiladi).
        fallback = {
            "uz": "Noma'lum ob-havo holati", "ru": "Неизвестное состояние погоды",
            "en": "Unknown weather condition", "kk": "Белгісіз ауа-райы жағдайы",
            "qq": "Belgisiz hawa rayı jaǵdayı",
        }
        return fallback.get(lang, "—")
    return entry.get(lang, entry["en"])


# Haftalik jadval uchun qisqa (bir so'zli) holat nomlari — monospace
# ustunlarga sig'ishi kerak, shuning uchun to'liq tavsifdan alohida.
_SHORT_LABELS: dict[str, dict[str, str]] = {
    "clear":  {"uz": "Quyosh",  "ru": "Солнце",  "en": "Sunny",  "kk": "Күн",      "qq": "Quyash"},
    "cloudy": {"uz": "Bulut",   "ru": "Облачно", "en": "Cloudy", "kk": "Бұлт",     "qq": "Bult"},
    "rainy":  {"uz": "Yomg'ir", "ru": "Дождь",   "en": "Rain",   "kk": "Жаңбыр",   "qq": "Jawın"},
    "snowy":  {"uz": "Qor",     "ru": "Снег",    "en": "Snow",   "kk": "Қар",      "qq": "Qar"},
    "stormy": {"uz": "Chaqmoq", "ru": "Гроза",   "en": "Storm",  "kk": "Найзағай", "qq": "Dawıl"},
}


def short_label(wmo_code: int, lang: str) -> str:
    """Haftalik jadval uchun bitta so'zli qisqa holat nomi."""
    if is_stormy(wmo_code):
        cat = "stormy"
    elif is_snowy(wmo_code):
        cat = "snowy"
    elif is_rainy(wmo_code):
        cat = "rainy"
    elif is_clear(wmo_code):
        cat = "clear"
    else:
        cat = "cloudy"
    return _SHORT_LABELS[cat].get(lang, _SHORT_LABELS[cat]["en"])


def emoji(wmo_code: int) -> str:
    table = _load()
    entry = table.get(str(wmo_code))
    return entry["emoji"] if entry else "❓"


def is_rainy(wmo_code: int) -> bool:
    return wmo_code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}


def is_snowy(wmo_code: int) -> bool:
    return wmo_code in {71, 73, 75, 77, 85, 86}


def is_stormy(wmo_code: int) -> bool:
    return wmo_code in {95, 96, 99}


def is_clear(wmo_code: int) -> bool:
    return wmo_code in {0, 1}
