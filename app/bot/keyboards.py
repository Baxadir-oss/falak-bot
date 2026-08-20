from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.services import i18n


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="O'zbekcha", callback_data="lang:uz")
    builder.button(text="Русский", callback_data="lang:ru")
    builder.button(text="English", callback_data="lang:en")
    builder.button(text="Қазақша", callback_data="lang:kk")
    builder.adjust(2)
    return builder.as_markup()


def location_request_keyboard(lang: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=i18n.t("btn_share_location", lang), request_location=True)
    builder.button(text=i18n.t("btn_search_city", lang))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=i18n.t("menu_today", lang))
    builder.button(text=i18n.t("menu_week", lang))
    builder.button(text=i18n.t("menu_settings", lang))
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)


def settings_keyboard(lang: str, notify_enabled: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if notify_enabled:
        builder.button(text=i18n.t("btn_notify_toggle_off", lang), callback_data="notify:off")
    else:
        builder.button(text=i18n.t("btn_notify_toggle_on", lang), callback_data="notify:on")
    builder.button(text=i18n.t("btn_notify_time", lang), callback_data="notify:time")
    builder.button(text=i18n.t("menu_change_location", lang), callback_data="settings:location")
    builder.button(text=i18n.t("menu_change_language", lang), callback_data="settings:language")
    builder.adjust(1)
    return builder.as_markup()
