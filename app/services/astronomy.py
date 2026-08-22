"""
Oy fazasi — "Falak" brendiga mos kichik, lekin chiroyli qo'shimcha.
Hech qanday tashqi API kerak emas: sinodik oy davri (29.53058867 kun)
va ma'lum bir yangi oy sanasidan hisoblanadi — bepul, tezkor, har doim ishlaydi.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

_SYNODIC_MONTH = 29.53058867
# 2000-yil 6-yanvardagi yangi oy — hisob-kitob uchun boshlang'ich nuqta.
_KNOWN_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)

# (yuqori chegara ulush, phase_key) — 8 bosqich
_PHASES = [
    (0.03, "new_moon"),
    (0.22, "waxing_crescent"),
    (0.28, "first_quarter"),
    (0.47, "waxing_gibbous"),
    (0.53, "full_moon"),
    (0.72, "waning_gibbous"),
    (0.78, "last_quarter"),
    (0.97, "waning_crescent"),
    (1.01, "new_moon"),
]

_EMOJI = {
    "new_moon": "🌑",
    "waxing_crescent": "🌒",
    "first_quarter": "🌓",
    "waxing_gibbous": "🌔",
    "full_moon": "🌕",
    "waning_gibbous": "🌖",
    "last_quarter": "🌗",
    "waning_crescent": "🌘",
}


def moon_phase_key(for_date: date | None = None) -> str:
    d = for_date or datetime.now(timezone.utc).date()
    dt = datetime(d.year, d.month, d.day, 12, tzinfo=timezone.utc)
    days_since = (dt - _KNOWN_NEW_MOON).total_seconds() / 86400.0
    fraction = (days_since % _SYNODIC_MONTH) / _SYNODIC_MONTH
    for upper, key in _PHASES:
        if fraction < upper:
            return key
    return "new_moon"


def moon_emoji(for_date: date | None = None) -> str:
    return _EMOJI[moon_phase_key(for_date)]
