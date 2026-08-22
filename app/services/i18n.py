"""
Bitta manba, ikki qatlam (plan 5.2-bo'lim): shu locales/*.json fayllaridan
ham Telegram bot, ham (kelajakda) Mini App API o'qiydi.

Son-son moslashuvi (5.3-bo'lim): rus tili uch shaklli (1/2-4/5-20),
ingliz ikki shaklli, o'zbek/qozoq bir shaklli — chunki bu tillar
agglyutinativ va son bilan kelganda ot shakli o'zgarmaydi.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
SUPPORTED_LANGUAGES = ("uz", "ru", "en", "kk", "qq")
DEFAULT_LANGUAGE = "uz"
# 5.8-bo'lim: agar Telegram tili 4 taga to'g'ri kelmasa — ruschaga o'tadi
# (mintaqada eng keng tushuniladigan ikkinchi til sifatida).
FALLBACK_LANGUAGE = "ru"


@lru_cache
def _load_locale(lang: str) -> dict[str, Any]:
    path = _LOCALES_DIR / f"{lang}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def normalize_language(tg_language_code: str | None) -> str:
    """Telegram bergan til kodini qo'llab-quvvatlanadigan tilga moslashtiradi."""
    if not tg_language_code:
        return DEFAULT_LANGUAGE
    code = tg_language_code.split("-")[0].lower()
    if code in SUPPORTED_LANGUAGES:
        return code
    return FALLBACK_LANGUAGE


def t(key: str, lang: str, **kwargs: Any) -> str:
    """Tarjima kalitini oladi, {placeholder}larni to'ldiradi."""
    lang = lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    data = _load_locale(lang)
    template = data.get(key)
    if template is None:
        # Zaxira til orqali urinib ko'ramiz, so'ng kalitning o'zini qaytaramiz —
        # bot hech qachon xato bilan yiqilmasligi kerak.
        template = _load_locale(DEFAULT_LANGUAGE).get(key, key)
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template


def raw(key: str, lang: str) -> Any:
    """t() faqat matn qaytaradi; bu funksiya ro'yxat/lug'at kabi xom
    qiymatlarni (masalan, weekdays_short) o'zgartirmasdan qaytaradi."""
    lang = lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    return _load_locale(lang).get(key)


def _ru_plural_form(n: int) -> str:
    n_abs = abs(n)
    if n_abs % 10 == 1 and n_abs % 100 != 11:
        return "one"
    if 2 <= n_abs % 10 <= 4 and not (12 <= n_abs % 100 <= 14):
        return "few"
    return "many"


def pluralize(count: int, lang: str, plural_key: str) -> str:
    """
    locales/<lang>.json ichidagi "plurals"."<plural_key>" ostidagi shakllardan
    to'g'risini tanlaydi va {n}ni qo'yadi.

    Masalan: pluralize(5, "ru", "days") -> "5 дней"
             pluralize(5, "uz", "days") -> "5 kunlik"
    """
    lang = lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    forms: dict[str, str] = _load_locale(lang).get("plurals", {}).get(plural_key, {})
    if lang == "ru":
        form = _ru_plural_form(count)
    elif lang == "en":
        form = "one" if count == 1 else "other"
    else:  # uz, kk — son bilan ot shakli o'zgarmaydi, bitta shakl yetarli
        form = "other"
    template = forms.get(form) or forms.get("other") or "{n}"
    return template.format(n=count)
