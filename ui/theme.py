"""
ui/theme.py — тема Albedolizer: цвета, шрифты, фабрики кнопок и чипов.
"""

import flet as ft
from ui.icons import img_icon


THEME_DARK = {
    "bg":      "#1a1d23",
    "panel":   "#20242b",
    "card":    "#282c34",
    "input":   "#32373f",
    "fg":      "#e8eaed",
    "fg2":     "#9aa0a6",
    "fg3":     "#5f6368",
    "accent":  "#5b8dd9",
    "success": "#4caf50",
    "danger":  "#e53935",
    "warn":    "#ff9800",
    "pbr":     "#4caf50",
    "batch":   "#ff9800",
    "compress": "#1565c0",
    "save":    "#6a4a9f",
    "reset":   "#555555",
    "seamless": "#00897b",
    "sat":     "#9c27b0",
    "tiling":  "#1565c0",
}

THEME_LIGHT = {
    "bg":      "#f0f2f5",
    "panel":   "#ffffff",
    "card":    "#e8eaed",
    "input":   "#dde1e6",
    "fg":      "#1a1d23",
    "fg2":     "#5f6368",
    "fg3":     "#8a8f96",
    "accent":  "#3d6fb8",
    "success": "#2e7d32",
    "danger":  "#c62828",
    "warn":    "#ef6c00",
    "pbr":     "#2e7d32",
    "batch":   "#ef6c00",
    "compress": "#3d6fb8",
    "save":    "#6a4a9f",
    "reset":   "#9aa0a6",
    "seamless": "#00695c",
    "sat":     "#6a1b9a",
    "tiling":  "#3d6fb8",
}

FONT = "Segoe UI"
FONT_MONO = "Consolas"
ON_ACCENT = "#ffffff"


class Btn(ft.Container):
    """ft.Container с методом set_disabled() и set_label()."""

    def __init__(self, color: str, disabled_color: str, on_click,
                 initially_disabled: bool = False,
                 label_control=None, **kwargs):
        # Поля ДО super() — Flet дёргает сеттер disabled внутри
        self._color = color
        self._disabled_color = disabled_color
        self._on_click = on_click
        self._disabled = bool(initially_disabled)
        self.label_control = label_control
        kwargs.pop("disabled", None)
        super().__init__(**kwargs)
        self.on_click = None if self._disabled else on_click

    @property
    def disabled(self) -> bool:
        return self._disabled

    @disabled.setter
    def disabled(self, value: bool):
        self.set_disabled(value)

    def set_disabled(self, value: bool):
        value = bool(value)
        if not hasattr(self, "_disabled"):
            self._disabled = value
            return
        if value == self._disabled:
            return
        self._disabled = value
        self.bgcolor = self._disabled_color if value else self._color
        self.on_click = None if value else self._on_click
        self.ink = not value
        try:
            if self.page is not None:
                self.page.update()
        except Exception:
            pass

    def set_label(self, text: str):
        if self.label_control is not None:
            self.label_control.value = text
            try:
                if self.page is not None:
                    self.page.update()
            except Exception:
                pass


def make_btn(label: str, on_click=None, color: str = "#5b8dd9",
             disabled: bool = False, icon: str = None,
             icon_color: str = None, fg: str = "#e8eaed",
             fg3: str = "#5f6368", input_bg: str = "#32373f",
             size: int = 14, icon_size: int = 16,
             vertical: int = 15, horizontal: int = 14) -> "Btn":
    """Кнопка-действие. Возвращает Btn с .set_disabled() и .set_label()."""
    text_color = ON_ACCENT if not disabled else fg3
    ic_color = icon_color or (ON_ACCENT if not disabled else fg3)

    label_ctrl = None
    if icon:
        label_ctrl = ft.Text(label, color=text_color, size=size,
                             font_family=FONT, weight=ft.FontWeight.W_600)
        inner = ft.Row([
            img_icon(icon, ic_color, icon_size),
            label_ctrl,
        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER,
           vertical_alignment=ft.CrossAxisAlignment.CENTER)
    else:
        label_ctrl = ft.Text(label, color=text_color, size=size,
                             font_family=FONT, weight=ft.FontWeight.W_600,
                             text_align=ft.TextAlign.CENTER)
        inner = label_ctrl

    return Btn(
        color=color,
        disabled_color=input_bg,
        on_click=on_click,
        initially_disabled=disabled,
        label_control=label_ctrl,
        content=inner,
        bgcolor=color if not disabled else input_bg,
        border_radius=10,
        padding=ft.Padding.symmetric(vertical=vertical, horizontal=horizontal),
        ink=not disabled,
    )


def make_btn_compact(label: str, on_click=None, color: str = "#5b8dd9",
                     disabled: bool = False, icon: str = None,
                     icon_color: str = None, fg3: str = "#5f6368",
                     input_bg: str = "#32373f",
                     size: int = 13, icon_size: int = 15) -> "Btn":
    return make_btn(label, on_click, color, disabled, icon, icon_color,
                    fg3=fg3, input_bg=input_bg, size=size, icon_size=icon_size,
                    vertical=11, horizontal=16)


def make_toggle(
    label: str = None,
    active: bool = False,
    on_click=None,
    accent: str = "#5b8dd9",
    card: str = "#282c34",
    fg2: str = "#9aa0a6",
    icon: str = None,
    icon_size: int = 14,
    size: int = 11,
    expand: bool = False,
    width: int = None,
    vertical: int = 8,
    horizontal: int = 10,
    border_radius: int = 8,
    tooltip: str = None,
    content=None,
) -> ft.Container:
    """Toggle: активный = accent-фон + белый контент + ink=False."""
    text_color = "#ffffff" if active else fg2
    icon_color = "#ffffff" if active else fg2
    bg = accent if active else card

    if content is not None:
        inner = content
    elif icon and label:
        inner = ft.Row([
            img_icon(icon, icon_color, icon_size),
            ft.Text(label, color=text_color, size=size, font_family=FONT,
                    weight=ft.FontWeight.W_600 if active
                    else ft.FontWeight.W_500,
                    text_align=ft.TextAlign.CENTER),
        ], spacing=6, alignment=ft.MainAxisAlignment.CENTER,
           vertical_alignment=ft.CrossAxisAlignment.CENTER)
    elif icon:
        inner = img_icon(icon, icon_color, icon_size)
    else:
        inner = ft.Text(label or "", color=text_color, size=size,
                        font_family=FONT,
                        weight=ft.FontWeight.W_600 if active
                        else ft.FontWeight.W_500,
                        text_align=ft.TextAlign.CENTER)

    return ft.Container(
        content=inner,
        bgcolor=bg,
        border_radius=border_radius,
        padding=ft.Padding.symmetric(vertical=vertical, horizontal=horizontal),
        ink=not active,
        on_click=on_click,
        expand=expand,
        width=width,
        tooltip=tooltip,
    )


def section_title(text: str, fg3: str = "#5f6368") -> ft.Text:
    return ft.Text(text, size=10, weight=ft.FontWeight.BOLD,
                   color=fg3, font_family=FONT)


def divider(fg3: str = "#5f6368") -> ft.Divider:
    return ft.Divider(color=fg3, height=1)


def theme_for(mode: str) -> dict:
    return THEME_DARK if mode == "dark" else THEME_LIGHT


def make_chip(label: str, active: bool = False, on_click=None,
              accent: str = "#5b8dd9", card: str = "#282c34",
              on_accent: str = "#ffffff", fg2: str = "#9aa0a6",
              size: int = 11, expand: bool = False,
              icon: str = None) -> ft.Container:
    return make_toggle(
        label=label, active=active, on_click=on_click,
        accent=accent, card=card, fg2=fg2, icon=icon,
        size=size, expand=expand,
    )