"""
ui/header.py — верхняя панель (хедер).

Лого + версия + subtitle слева. Simple/Advanced, тема, язык, инфо справа.
Все кнопки с Lucide-иконками.
"""

import flet as ft
from ui.icons import img_icon
from ui.theme import make_btn

FONT = "Segoe UI"


class Header:
    """
    Верхняя панель.

    Конструктор:
        page        — ft.Page
        S           — состояние
        t           — перевод
        theme       — цвета
        version     — '1.7.5-beta'
        on_toggle_mode  — callback() — переключить Simple/Advanced
        on_toggle_theme — callback() — переключить тему
        on_toggle_lang  — callback() — переключить язык
        on_open_info    — callback() — открыть Info-диалог
    """

    def __init__(self, page, S, t, theme, version,
                 on_toggle_mode, on_toggle_theme,
                 on_toggle_lang, on_open_info):
        self.page = page
        self.S = S
        self.t = t
        self.theme = theme
        self.version = version
        self.on_toggle_mode = on_toggle_mode
        self.on_toggle_theme = on_toggle_theme
        self.on_toggle_lang = on_toggle_lang
        self.on_open_info = on_open_info

    def build(self) -> ft.Container:
        th = self.theme
        S = self.S
        is_simple = S["ui_mode"] == "simple"

        # Левая часть — лого + версия + subtitle
        left = ft.Column([
            ft.Row([
                ft.Text("Albedolizer", size=20,
                        weight=ft.FontWeight.BOLD,
                        color=th["accent"], font_family=FONT),
                ft.Container(
                    content=ft.Text(f"v{self.version}", size=10,
                                    color=th["fg2"], font_family=FONT,
                                    weight=ft.FontWeight.W_600),
                    bgcolor=th["card"], border_radius=6,
                    padding=ft.Padding.symmetric(vertical=2, horizontal=8),
                ),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Text(self.t("subtitle"), size=11, color=th["fg2"],
                    font_family=FONT),
        ], spacing=2)

        # Кнопки справа
        mode_label = (self.t("mode_btn_advanced") if is_simple
                       else self.t("mode_btn_simple"))
        mode_btn = self._icon_text_btn(
            "settings", mode_label, self.on_toggle_mode)

        theme_icon = "sun" if S["theme"] == "dark" else "moon"
        theme_btn = self._icon_only_btn(
            theme_icon, self.on_toggle_theme, tooltip="Toggle theme")

        lang_btn = self._icon_text_btn(
            "globe", self.t("lang_btn"), self.on_toggle_lang)

        info_btn = self._icon_text_btn(
            "info", self.t("info_btn"), self.on_open_info)

        right = ft.Row([
            mode_btn,
            ft.Container(width=8),
            theme_btn,
            ft.Container(width=8),
            lang_btn,
            ft.Container(width=8),
            info_btn,
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        return ft.Container(
            content=ft.Row([
                left,
                ft.Container(expand=True),
                right,
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(vertical=14, horizontal=24),
            bgcolor=th["panel"],
        )

    def _icon_text_btn(self, icon_name, label, on_click):
        """Кнопка хедера: иконка + текст."""
        th = self.theme
        return ft.Container(
            content=ft.Row([
                img_icon(icon_name, th["fg"], 14),
                ft.Text(label, color=th["fg"], size=13,
                        font_family=FONT, weight=ft.FontWeight.W_600),
            ], spacing=8, tight=True,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=th["card"], border_radius=8,
            padding=ft.Padding.symmetric(vertical=10, horizontal=16),
            ink=True, on_click=on_click,
        )

    def _icon_only_btn(self, icon_name, on_click, tooltip=None):
        """Кнопка хедера: только иконка."""
        th = self.theme
        return ft.Container(
            content=img_icon(icon_name, th["fg"], 14),
            bgcolor=th["card"], border_radius=8,
            padding=ft.Padding.symmetric(vertical=10, horizontal=16),
            ink=True, on_click=on_click, tooltip=tooltip,
        )