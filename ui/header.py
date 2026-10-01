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
        version     — '1.7.7-beta'
        on_toggle_mode  — callback() — переключить Simple/Advanced
        on_toggle_theme — callback() — переключить тему
        on_toggle_lang  — callback() — циклическое переключение языка (fallback)
        on_open_info    — callback() — открыть Info-диалог
        on_set_lang     — callback(code) — установить конкретный язык ('ru'/'en'/'zh')
    """

    def __init__(self, page, S, t, theme, version,
                 on_toggle_mode, on_toggle_theme,
                 on_toggle_lang, on_open_info,
                 on_set_lang=None):
        self.page = page
        self.S = S
        self.t = t
        self.theme = theme
        self.version = version
        self.on_toggle_mode = on_toggle_mode
        self.on_toggle_theme = on_toggle_theme
        self.on_toggle_lang = on_toggle_lang
        self.on_open_info = on_open_info
        self.on_set_lang = on_set_lang or (lambda code: None)

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

        lang_switch = self._build_lang_switch()

        info_btn = self._icon_text_btn(
            "info", self.t("info_btn"), self.on_open_info)

        right = ft.Row([
            mode_btn,
            ft.Container(width=8),
            theme_btn,
            ft.Container(width=8),
            lang_switch,
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

    def _build_lang_switch(self) -> ft.Container:
        """Сегментированный переключатель языка: RU | EN | 中文."""
        th = self.theme
        S = self.S
        langs = [("ru", "RU"), ("en", "EN"), ("zh", "中文")]

        chips = []
        for code, label in langs:
            is_active = S.get("lang", "ru") == code
            chip = ft.Container(
                content=ft.Text(
                    label,
                    color="#ffffff" if is_active else th["fg2"],
                    size=11, font_family=FONT,
                    weight=(ft.FontWeight.W_600 if is_active
                            else ft.FontWeight.W_500),
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor=th["accent"] if is_active else th["card"],
                border_radius=6,
                padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                ink=not is_active,
                on_click=lambda e, c=code: self.on_set_lang(c),
            )
            chips.append(chip)

        return ft.Container(
            content=ft.Row(chips, spacing=3, tight=True),
            bgcolor=th["panel"],
            border_radius=8,
            padding=3,
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