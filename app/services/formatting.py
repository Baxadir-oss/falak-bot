"""
Open-Meteo'dan kelgan xom JSON'ni foydalanuvchiga ko'rinadigan,
chiroyli formatlangan matnga aylantiradi (plan 3.2, 3.3, 3.6-bo'limlar).

5.4-bo'lim qoidasi: joy nomiga hech qachon grammatik qo'shimcha
qo'shilmaydi — "📍 Nukus — hozir +25°" uslubida, ajratkich orqali.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from app.services import i18n, weather_codes
from app.services.advice import build_advice_lines
from app.services.wisdom import daily_wisdom


_MD_SPECIAL = "_*`["


def md_escape(text: str) -> str:
    """Telegram legacy Markdown'da maxsus belgilarni ekranlaydi — geokodlash
    API'sidan kelgan joy nomi (foydalanuvchi kiritmagan, lekin tashqi manba
    bo'lgani uchun ishonchsiz) xabar formatini buzib qo'ymasligi uchun."""
    if not text:
        return text
    return "".join(f"\\{c}" if c in _MD_SPECIAL else c for c in text)


def _signed(value: float | int | None) -> str:
    if value is None:
        return "—"
    rounded = round(value)
    return f"+{rounded}" if rounded >= 0 else str(rounded)


def _format_date(iso_str: str, lang: str) -> str:
    """Sana tartibi KK.OO.YYYY — plan 5.7-bo'lim."""
    d = date.fromisoformat(iso_str)
    return d.strftime("%d.%m.%Y")


def _weekday_label(iso_date_str: str, lang: str, is_first: bool) -> str:
    if is_first:
        return i18n.t("today_label", lang)
    names = i18n.raw("weekdays_short", lang) or []
    d = date.fromisoformat(iso_date_str)
    idx = d.weekday()  # Dushanba=0
    return names[idx] if idx < len(names) else iso_date_str


def format_today(data: dict[str, Any], place: str, lang: str) -> str:
    current = data.get("current", {})
    daily = data.get("daily", {})

    wmo = int(current.get("weather_code", 0))
    condition = weather_codes.describe(wmo, lang)
    emj = weather_codes.emoji(wmo)

    today_iso = (daily.get("time") or [None])[0]
    date_str = _format_date(today_iso, lang) if today_iso else ""

    lines = [
        i18n.t("today_header", lang, emoji=emj, place=md_escape(place), date=date_str),
        "",
        i18n.t("today_temp_line", lang,
               temp=_signed(current.get("temperature_2m")),
               feels=_signed(current.get("apparent_temperature"))),
        i18n.t("today_condition_line", lang, emoji=emj, condition=condition),
    ]

    precip_prob = (daily.get("precipitation_probability_max") or [None])[0]
    if precip_prob is not None:
        lines.append(i18n.t("today_precip_line", lang, prob=round(precip_prob)))

    wind = current.get("wind_speed_10m")
    if wind is not None:
        lines.append(i18n.t("today_wind_line", lang, speed=round(wind)))

    humidity = current.get("relative_humidity_2m")
    if humidity is not None:
        lines.append(i18n.t("today_humidity_line", lang, humidity=round(humidity)))

    uv = (daily.get("uv_index_max") or [None])[0]
    if uv is not None:
        lines.append(i18n.t("today_uv_line", lang, uv=round(uv, 1)))

    sunrise = (daily.get("sunrise") or [None])[0]
    sunset = (daily.get("sunset") or [None])[0]
    if sunrise and sunset:
        lines.append(i18n.t("today_sun_line", lang,
                             sunrise=sunrise[-5:], sunset=sunset[-5:]))

    advice = build_advice_lines(
        wmo_code=wmo,
        wind_speed_kmh=wind or 0,
        uv_index=uv or 0,
        temperature_c=current.get("temperature_2m", 20),
        lang=lang,
    )
    if advice:
        lines.append("")
        lines.extend(advice)

    wisdom = daily_wisdom(wmo, lang)
    if wisdom:
        lines.append("")
        lines.append(i18n.t("wisdom_line", lang, text=wisdom))

    return "\n".join(lines)


def format_week(data: dict[str, Any], place: str, lang: str) -> str:
    daily = data.get("daily", {})
    times: list[str] = daily.get("time", [])
    codes: list[int] = daily.get("weather_code", [])
    tmax: list[float] = daily.get("temperature_2m_max", [])
    tmin: list[float] = daily.get("temperature_2m_min", [])
    probs: list[float] = daily.get("precipitation_probability_max", [])

    n_days = len(times)
    days_label = i18n.pluralize(n_days, lang, "days")

    lines = [i18n.t("week_header", lang, place=md_escape(place), days=days_label), ""]
    for i in range(n_days):
        wmo = int(codes[i]) if i < len(codes) else 0
        lines.append(i18n.t(
            "week_day_line", lang,
            day_label=_weekday_label(times[i], lang, is_first=(i == 0)),
            emoji=weather_codes.emoji(wmo),
            max=_signed(tmax[i] if i < len(tmax) else None),
            min=_signed(tmin[i] if i < len(tmin) else None),
            prob=round(probs[i]) if i < len(probs) and probs[i] is not None else 0,
        ))

    return "\n".join(lines)


def format_daily_notification(data: dict[str, Any], place: str, lang: str) -> str:
    """Plan 3.6-bo'limdagi qisqa xabar namunasiga mos, 3-4 soniyada
    o'qib bo'ladigan qisqa format."""
    current = data.get("current", {})
    daily = data.get("daily", {})

    wmo = int(current.get("weather_code", 0))
    emj = weather_codes.emoji(wmo)
    today_iso = (daily.get("time") or [None])[0]
    date_str = _format_date(today_iso, lang) if today_iso else ""

    tmax = (daily.get("temperature_2m_max") or [None])[0]
    tmin = (daily.get("temperature_2m_min") or [None])[0]
    precip_prob = (daily.get("precipitation_probability_max") or [0])[0] or 0
    wind = current.get("wind_speed_10m", 0)
    uv = (daily.get("uv_index_max") or [0])[0] or 0

    lines = [
        f"{emj} {md_escape(place)} — {date_str}",
        f"{_signed(tmax)}° / {_signed(tmin)}°",
    ]

    advice = build_advice_lines(
        wmo_code=wmo, wind_speed_kmh=wind, uv_index=uv,
        temperature_c=tmax if tmax is not None else 20, lang=lang,
    )
    lines.extend(advice)

    wisdom = daily_wisdom(wmo, lang)
    if wisdom:
        lines.append(i18n.t("wisdom_line", lang, text=wisdom))

    return "\n".join(lines)
