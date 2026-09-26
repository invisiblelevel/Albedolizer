"""
ui/rail.py — левый NavigationRail.

Все вкладки приложения. В Simple-режиме показываются только:
single, pbr, export, compress. В Advanced — все шесть.
"""

import flet as ft
from ui.icons import img_icon
from ui.theme import make_toggle, FONT

# (key, lucide_icon, перевод-ключ, доступно-в-simple)
RAIL_TABS = [
    ("single",   "image",         "tab_single",   True),
    ("batch",    "layers",        "tab_batch",    False),
    ("pbr",      "palette",       "tab_pbr",      True),
    ("export",   "gamepad-2",     "tab_export",   True),
    ("compress", "archive",       "tab_compress", True),
    ("realism",  "clapperboard",  "tab_realism",  False),
]


def build_rail(page, S, t, theme, on_change) -> ft.Container:
    """
    Собирает NavigationRail из make_toggle — активный элемент
    получает синий фон + БЕЛЫЙ контент, неактивный — прозрачный.
    """
    th = theme
    is_simple = S["ui_mode"] == "simple"

    items = []
    for key, icon_name, label_key, available_in_simple in RAIL_TABS:
        if is_simple and not available_in_simple:
            continue
        is_active = (S["active_tab"] == key)
        # Цвет контента — ВСЕГДА белый на активном
        content_color = "#ffffff" if is_active else th["fg2"]

        # Вертикальный layout: иконка над текстом
        content = ft.Column([
            img_icon(icon_name, content_color, 18),
            ft.Container(height=2),
            ft.Text(t(label_key), size=10, color=content_color,
                    font_family=FONT, text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.W_600 if is_active
                    else ft.FontWeight.W_500),
        ], spacing=0,
           horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        # make_toggle для rail: используем кастомный content, но
        # прозрачный фон для неактивных (а не card) — rail на панели
        btn = ft.Container(
            content=content,
            bgcolor=th["accent"] if is_active else "transparent",
            border_radius=10,
            padding=ft.Padding.symmetric(vertical=12, horizontal=8),
            ink=not is_active,   # ← на активном не мигает
            on_click=lambda e, k=key: on_change(k),
            tooltip=t(label_key),
        )
        items.append(btn)

    return ft.Container(
        content=ft.Column(items, spacing=4),
        bgcolor=th["panel"],
        width=110,
        padding=ft.Padding.symmetric(vertical=12, horizontal=8),
    )


def is_tab_available(S, tab_key: str) -> bool:
    """Проверка, доступна ли вкладка в текущем режиме."""
    is_simple = S["ui_mode"] == "simple"
    for key, _, _, available_in_simple in RAIL_TABS:
        if key == tab_key:
            return (not is_simple) or available_in_simple
    return False


def get_default_tab(S) -> str:
    """Возвращает активную вкладку или 'single' если текущая недоступна."""
    if is_tab_available(S, S["active_tab"]):
        return S["active_tab"]
    return "single"