"""
Open-Meteo'dan kelgan xom JSON'ni foydalanuvchiga ko'rinadigan,
chiroyli formatlangan matnga aylantiradi (plan 3.2, 3.3, 3.6-bo'limlari,
keyinchalik boy ma'lumot va yaxshiroq dizayn bilan kengaytirildi).

Dizayn qarorlari:
- "Bugun" kartasi mavzular bo'yicha guruhlangan (Asosiy / Atmosfera / Osmon)
  — ko'p ma'lumot bo'lsa ham ko'zga chiroyli va tez o'qiladigan bo'lishi uchun.
- "Hafta" jadvali monospace (```-bloki) qilib chiziladi, ustun kengliklari
  HAR SAFAR haqiqiy ma'lumotga qarab hisoblanadi — shu tufayli 5 tilning
  qaysi birida ham (so'zlar turli uzunlikda bo'lsa ham) ustunlar to'g'ri
  tekislanadi.
- AQI va Oy fazasi — API xato bersa ham yoki qiymat bo'lmasa ham,
  o'sha qatorlar shunchaki tashlab ketiladi (4.3-bo'lim: bo'sh ekran yo'q).

5.4-bo'lim qoidasi: joy nomiga hech qachon grammatik qo'shimcha
qo'shilmaydi — "📍 Nukus — hozir +25°" uslubida, ajratkich orqali.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Optional

from app.services import i18n, weather_codes
from app.services.advice import build_advice_lines
from app.services.astronomy import moon_emoji, moon_phase_key
from app.services.atmosphere import aqi_category_key, degrees_to_compass_key
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


def _compass_word(degrees: float | None, lang: str) -> Optional[str]:
    key = degrees_to_compass_key(degrees)
    if key is None:
        return None
    table = i18n.raw("compass", lang) or {}
    return table.get(key)


def _section_header(key: str, lang: str) -> str:
    return f"*{i18n.t(key, lang)}*"


def _aqi_line(aqi: Optional[int], lang: str) -> Optional[str]:
    if aqi is None:
        return None
    cat = aqi_category_key(aqi)
    labels = i18n.raw("aqi_labels", lang) or {}
    label = labels.get(cat, str(cat))
    return i18n.t("today_aqi_line", lang, label=label, value=aqi)


def _moon_line(for_date: Optional[date], lang: str) -> str:
    key = moon_phase_key(for_date)
    phases = i18n.raw("moon_phases", lang) or {}
    label = phases.get(key, key)
    return i18n.t("today_moon_line", lang, emoji=moon_emoji(for_date), label=label)


def format_today(
    data: dict[str, Any], place: str, lang: str, aqi: Optional[int] = None
) -> str:
    current = data.get("current", {})
    daily = data.get("daily", {})

    wmo = int(current.get("weather_code", 0))
    condition = weather_codes.describe(wmo, lang)
    emj = weather_codes.emoji(wmo)

    today_iso = (daily.get("time") or [None])[0]
    today_date = date.fromisoformat(today_iso) if today_iso else None
    date_str = _format_date(today_iso, lang) if today_iso else ""

    # ---- Sarlavha + asosiy holat ----
    lines = [
        i18n.t("today_header", lang, emoji=emj, place=md_escape(place), date=date_str),
        "",
        i18n.t("today_temp_line", lang,
               temp=_signed(current.get("temperature_2m")),
               feels=_signed(current.get("apparent_temperature"))),
        i18n.t("today_condition_line", lang, emoji=emj, condition=condition),
    ]

    # ---- Atmosfera bo'limi ----
    atmosphere_lines: list[str] = []

    precip_prob = (daily.get("precipitation_probability_max") or [None])[0]
    precip_amount = (daily.get("precipitation_sum") or [None])[0]
    if precip_prob is not None:
        atmosphere_lines.append(i18n.t(
            "today_precip_line", lang,
            prob=round(precip_prob),
            amount=round(precip_amount, 1) if precip_amount is not None else 0,
        ))

    wind_speed = current.get("wind_speed_10m")
    wind_dir_deg = (daily.get("wind_direction_10m_dominant") or [None])[0]
    if wind_speed is not None:
        direction = _compass_word(wind_dir_deg, lang) or ""
        atmosphere_lines.append(
            i18n.t("today_wind_line", lang, speed=round(wind_speed), direction=direction)
        )

    gust = (daily.get("wind_gusts_10m_max") or [None])[0]
    if gust is not None and wind_speed is not None and gust > wind_speed * 1.3:
        # Zarbalar oddiy shamoldan sezilarli farq qilsagina ko'rsatiladi —
        # aks holda ikkita deyarli bir xil qatorni takrorlash foydasiz.
        atmosphere_lines.append(i18n.t("today_gust_line", lang, gust=round(gust)))

    pressure = current.get("surface_pressure")
    if pressure is not None:
        atmosphere_lines.append(i18n.t("today_pressure_line", lang, pressure=round(pressure)))

    humidity = current.get("relative_humidity_2m")
    if humidity is not None:
        atmosphere_lines.append(i18n.t("today_humidity_line", lang, humidity=round(humidity)))

    cloud = current.get("cloud_cover")
    if cloud is not None:
        atmosphere_lines.append(i18n.t("today_cloud_line", lang, cloud=round(cloud)))

    uv = (daily.get("uv_index_max") or [None])[0]
    if uv is not None:
        atmosphere_lines.append(i18n.t("today_uv_line", lang, uv=round(uv, 1)))

    aqi_line = _aqi_line(aqi, lang)
    if aqi_line:
        atmosphere_lines.append(aqi_line)

    if atmosphere_lines:
        lines.append("")
        lines.append(_section_header("today_section_atmosphere", lang))
        lines.extend(atmosphere_lines)

    # ---- Osmon bo'limi (quyosh + oy) ----
    sky_lines: list[str] = []
    sunrise = (daily.get("sunrise") or [None])[0]
    sunset = (daily.get("sunset") or [None])[0]
    if sunrise and sunset:
        sky_lines.append(i18n.t("today_sun_line", lang, sunrise=sunrise[-5:], sunset=sunset[-5:]))
    sky_lines.append(_moon_line(today_date, lang))

    if sky_lines:
        lines.append("")
        lines.append(_section_header("today_section_sky", lang))
        lines.extend(sky_lines)

    # ---- Amaliy tavsiyalar ----
    advice = build_advice_lines(
        wmo_code=wmo,
        wind_speed_kmh=wind_speed or 0,
        uv_index=uv or 0,
        temperature_c=current.get("temperature_2m", 20),
        aqi=aqi,
        lang=lang,
    )
    if advice:
        lines.append("")
        lines.extend(advice)

    # ---- Falak Hikmati ----
    wisdom = daily_wisdom(wmo, lang)
    if wisdom:
        lines.append("")
        lines.append(i18n.t("wisdom_line", lang, text=wisdom))

    return "\n".join(lines)


def _week_table(data: dict[str, Any], lang: str) -> str:
    """7 kunlik prognozni monospace (tekislangan) jadval qilib quradi.
    Ustun kengliklari HAQIQIY qiymatlardan hisoblanadi — shuning uchun
    har qanday til uzunlikda muammosiz to'g'ri chiqadi."""
    daily = data.get("daily", {})
    times: list[str] = daily.get("time", [])
    codes: list[int] = daily.get("weather_code", [])
    tmax: list[float] = daily.get("temperature_2m_max", [])
    tmin: list[float] = daily.get("temperature_2m_min", [])
    probs: list[float] = daily.get("precipitation_probability_max", [])
    winds: list[float] = daily.get("wind_speed_10m_max", [])

    headers = (
        i18n.raw("week_col_day", lang) or "Day",
        i18n.raw("week_col_condition", lang) or "Cond",
        i18n.raw("week_col_temp", lang) or "Max/Min",
        i18n.raw("week_col_rain", lang) or "Rain",
        i18n.raw("week_col_wind", lang) or "Wind",
    )
    align = ("<", "<", ">", ">", ">")

    rows: list[tuple[str, str, str, str, str]] = []
    for i in range(len(times)):
        wmo = int(codes[i]) if i < len(codes) else 0
        day_label = _weekday_label(times[i], lang, is_first=(i == 0))
        cond = weather_codes.short_label(wmo, lang)
        temp_range = f"{_signed(tmax[i] if i < len(tmax) else None)}/{_signed(tmin[i] if i < len(tmin) else None)}"
        rain = f"{round(probs[i])}%" if i < len(probs) and probs[i] is not None else "0%"
        wind = f"{round(winds[i])}" if i < len(winds) and winds[i] is not None else "—"
        rows.append((day_label, cond, temp_range, rain, wind))

    all_rows = [headers, *rows]
    widths = [max(len(r[c]) for r in all_rows) for c in range(5)]

    def fmt_row(r: tuple[str, ...]) -> str:
        cells = []
        for i, val in enumerate(r):
            cells.append(val.rjust(widths[i]) if align[i] == ">" else val.ljust(widths[i]))
        return "  ".join(cells)

    lines = [fmt_row(headers), "-" * (sum(widths) + 2 * 4)]
    lines.extend(fmt_row(r) for r in rows)
    return "```\n" + "\n".join(lines) + "\n```"


def format_week(data: dict[str, Any], place: str, lang: str) -> str:
    daily = data.get("daily", {})
    n_days = len(daily.get("time", []))
    days_label = i18n.pluralize(n_days, lang, "days")

    header = i18n.t("week_header", lang, place=md_escape(place), days=days_label)
    table = _week_table(data, lang)
    return f"{header}\n\n{table}"


def format_daily_notification(
    data: dict[str, Any], place: str, lang: str, aqi: Optional[int] = None
) -> str:
    """Plan 3.6-bo'limdagi qisqa xabar namunasiga mos, 3-4 soniyada
    o'qib bo'ladigan qisqa format — bu yerda ataylab qisqa saqlanadi,
    to'liq ma'lumot uchun "Bugun" tugmasi bor."""
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
        temperature_c=tmax if tmax is not None else 20, aqi=aqi, lang=lang,
    )
    lines.extend(advice)

    wisdom = daily_wisdom(wmo, lang)
    if wisdom:
        lines.append(i18n.t("wisdom_line", lang, text=wisdom))

    return "\n".join(lines)
