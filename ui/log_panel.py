"""
ui/log_panel.py — нижняя панель лога (collapsible).

Свёрнутая: одна строка + иконка раскрытия + кнопка очистки.
Развёрнутая: ListView со всей историей.
"""

import flet as ft
from ui.icons import img_icon
from ui.theme import make_chip

FONT = "Segoe UI"
FONT_MONO = "Consolas"


class LogPanel:
    """
    Нижний лог-бар.

    Конструктор:
        page    — ft.Page
        S       — состояние (для S['log_lines'])
        t       — функция перевода
        theme   — цвета
        on_clear — callback() — очистить лог (обновляет S['log_lines'])
    """

    def __init__(self, page, S, t, theme, on_clear):
        self.page = page
        self.S = S
        self.t = t
        self.theme = theme
        self.on_clear = on_clear

        self.collapsed_preview = None
        self.log_body = None
        self.toggle_icon = None
        self.root = None

    def build(self) -> ft.Container:
        th = self.theme

        # Ссылка на ListView из S — там log() и refresh_log() пишут
        lc = self.S.get("log_column_bottom")

        self.collapsed_preview = ft.Text(
            "", color=th["fg2"], size=11, font_family=FONT_MONO,
            selectable=False, expand=True, max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.S["log_collapsed_preview"] = self.collapsed_preview

        self.toggle_icon = img_icon("chevron-up", th["fg2"], 12)

        self.log_body = ft.Container(
            content=lc,
            height=130,
            visible=False,
            bgcolor=th["card"],
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        )

        def _toggle_log(e=None):
            expanded = not self.S.get("log_expanded", False)
            self.S["log_expanded"] = expanded
            if expanded:
                self.log_body.visible = True
                self.toggle_icon.src = img_icon("chevron-down",
                                                 th["fg2"], 12).src
                self.collapsed_preview.visible = False
            else:
                self.log_body.visible = False
                self.toggle_icon.src = img_icon("chevron-up",
                                                 th["fg2"], 12).src
                self.collapsed_preview.visible = True
            self.page.update()

        def _clear(e=None):
            self.on_clear()
            self.page.update()

        clear_btn = ft.Container(
            content=img_icon("trash-2", th["fg2"], 13),
            border_radius=6,
            padding=ft.Padding.symmetric(vertical=4, horizontal=8),
            ink=True, on_click=_clear,
            tooltip="Clear log",
        )

        log_header = ft.Container(
            content=ft.Row([
                img_icon("clipboard-list", th["fg3"], 14),
                ft.Text(self.t("log_title"), size=11, color=th["fg3"],
                        font_family=FONT, weight=ft.FontWeight.W_600),
                ft.Container(width=8),
                self.collapsed_preview,
                self.toggle_icon,
                ft.Container(width=6),
                clear_btn,
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            bgcolor=th["panel"],
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            on_click=_toggle_log,
            ink=True,
        )

        self.root = ft.Container(
            content=ft.Column([log_header, self.log_body],
                              spacing=0, tight=True),
            bgcolor=th["panel"],
        )
        return self.root