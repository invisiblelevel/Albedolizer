"""
main.py — точка входа Albedolizer.

Тонкая сборка: state + тема + пути + FilePicker + CLIP → Header, Rail,
LogPanel, активная вкладка. Вся логика — в core/ и ui/.
"""

import os
import sys
import asyncio
import flet as ft
import cv2
import concurrent.futures

from config import (
    APP_VERSION, APP_BUILD, AUTOLEVELS_EXE_NAME, AUTOLEVELS_MODEL_NAME,
    LUTWITHBGRID_MODEL_NAME, DEFAULT_AI_MODEL,
)
from settings import load_settings, save_settings
from clip_model import CLIPMaterialClassifier
from translations import T

from core.state import create_state, persist_settings
from core.io import pil_to_b64  # noqa — используется через модули

from ui.theme import theme_for, THEME_DARK, THEME_LIGHT
from ui.helpers import log, refresh_log, clear_log
from ui.header import Header
from ui.rail import build_rail, is_tab_available, get_default_tab
from ui.log_panel import LogPanel
from ui.dialogs import create_info_dialog, show_welcome_dialog

from ui.tab_single import SingleTab
from ui.tab_pbr import PbrTab
from ui.tab_export import ExportTab
from ui.tab_realism import RealismTab
from ui.tab_batch import BatchTab
from ui.tab_compress import CompressTab

from translations import get_font_path

FONT = "Segoe UI"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 820


def _resolve_base_dir():
    """Определяет базовую папку (frozen или dev)."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        exe_dir = os.path.dirname(sys.executable)
        if meipass and os.path.exists(os.path.join(meipass, "manual.html")):
            return meipass
        return exe_dir
    return os.path.dirname(os.path.abspath(__file__))


def _resolve_icon_path(base_dir: str) -> str:
    """Путь до icon.ico с fallback на _MEIPASS."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        exe_dir = os.path.dirname(sys.executable)
        if meipass and os.path.exists(os.path.join(meipass, "icon.ico")):
            return os.path.join(meipass, "icon.ico")
        return os.path.join(exe_dir, "icon.ico")
    return os.path.join(base_dir, "icon.ico")


def main(page: ft.Page):
    cv2.setNumThreads(1)
    asyncio.get_event_loop().set_default_executor(
        concurrent.futures.ThreadPoolExecutor(max_workers=4)
    )
    # ═══ Настройки и state ═══
    user_settings = load_settings()
    S = create_state(user_settings)

    # ═══ Пути ═══
    base_dir = _resolve_base_dir()
    paths = {
        "base_dir": base_dir,
        "autolevels_exe": os.path.join(base_dir, AUTOLEVELS_EXE_NAME),
        "autolevels_model": os.path.join(base_dir, AUTOLEVELS_MODEL_NAME),
        "lutwithbgrid_model": os.path.join(base_dir, LUTWITHBGRID_MODEL_NAME),
        "clip_vision": os.path.join(base_dir, "clip_vision_int8.onnx"),
        "clip_text": os.path.join(base_dir, "clip_text_encoder.onnx"),
    }

    # ═══ Окно ═══
    page.title = f"Albedolizer v{APP_VERSION}"
    page.padding = 0
    page.spacing = 0
    page.window.width = WINDOW_WIDTH
    page.window.height = WINDOW_HEIGHT
    page.window.opacity = 1.0

    # ═══ Авто-масштаб интерфейса под HiDPI / 4K ═══
    # SetProcessDpiAwareness уже вызван на уровне модуля (до ft.run).
    # Здесь только читаем DPI и ставим scale.
    try:
        import ctypes
        user32 = ctypes.windll.user32
        try:
            dpi = user32.GetDpiForSystem()
        except Exception:
            hdc = user32.GetDC(0)
            dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
            user32.ReleaseDC(0, hdc)
        if dpi and dpi > 0:
            # 96 DPI = 100%. На 4K обычно 144 или 192.
            # 0.85 — компенсация, чтобы UI не был слишком крупным.
            page.window.scale = max(1.0, round((dpi / 96.0) * 0.85, 2))
    except Exception:
        pass

    # ═══ Шрифт для китайского ═══
    font_path = get_font_path()
    if font_path:
        page.fonts = {"NotoSansSC": font_path}
        page.theme = ft.Theme(font_family="NotoSansSC")

    icon_path = _resolve_icon_path(base_dir)
    if os.path.exists(icon_path):
        page.window.icon = icon_path

    # ═══ CLIP + FilePicker ═══
    S["clip"] = CLIPMaterialClassifier()
    picker = ft.FilePicker()

    # ═══ Функции-обёртки для переводов/темы ═══
    def t(key):
        lang = S.get("lang", "en")
        if lang not in T:
            lang = "en"
        return T[lang].get(key, key)

    def current_theme():
        return theme_for(S["theme"])

    def apply_theme():
        th = current_theme()
        page.bgcolor = th["bg"]
        page.theme_mode = (ft.ThemeMode.DARK if S["theme"] == "dark"
                            else ft.ThemeMode.LIGHT)
        return th

    # ═══ Коллбеки ═══
    def on_persist():
        persist_settings(S, save_settings, page)

    def on_rebuild():
        rebuild_ui()

    def on_toggle_mode():
        S["ui_mode"] = ("advanced" if S["ui_mode"] == "simple"
                         else "simple")
        # Если активная вкладка недоступна в новом режиме — на single
        S["active_tab"] = get_default_tab(S)
        on_persist()
        rebuild_ui()

    def on_toggle_theme():
        S["theme"] = "light" if S["theme"] == "dark" else "dark"
        apply_theme()
        on_persist()
        rebuild_ui()

    LANG_CYCLE = ["ru", "en", "zh"]

    def on_set_lang(code: str):
        if code not in LANG_CYCLE:
            return
        if S["lang"] == code:
            return
        S["lang"] = code
        on_persist()
        rebuild_ui()

    def on_toggle_lang():
        # циклическое переключение (для горячей клавиши, если есть)
        idx = LANG_CYCLE.index(S["lang"]) if S["lang"] in LANG_CYCLE else 0
        on_set_lang(LANG_CYCLE[(idx + 1) % len(LANG_CYCLE)])

    def on_open_info():
        th = current_theme()
        dlg = create_info_dialog(page, S, t, th, base_dir)
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def on_rail_change(key):
        if not is_tab_available(S, key):
            return
        S["active_tab"] = key
        rebuild_ui()

    def on_clear_log():
        clear_log(S)

    # ═══ UI-элементы, разделяемые между вкладками ═══
    def build_shared_elements():
        th = current_theme()
        S["progress_bar"] = ft.ProgressBar(
            value=None, visible=False, color=th["accent"],
            bgcolor=th["input"], height=4, bar_height=4)
        S["progress_text"] = ft.Text("", color=th["fg2"], size=12,
                                       font_family=FONT, visible=False)
        S["pbr_progress_bar"] = ft.ProgressBar(
            value=None, visible=False, color=th["pbr"],
            bgcolor=th["input"], height=4, bar_height=4)
        S["pbr_progress_text"] = ft.Text("", color=th["fg2"], size=12,
                                           font_family=FONT, visible=False)
        S["batch_progress_bar"] = ft.ProgressBar(
            value=0, visible=True, color=th["batch"],
            bgcolor=th["input"], height=4, bar_height=4)
        S["batch_progress_text"] = ft.Text("", color=th["fg2"], size=12,
                                             font_family=FONT)
        S["compress_progress_bar"] = ft.ProgressBar(
            value=0, visible=True, color=th["compress"],
            bgcolor=th["input"], height=4, bar_height=4)
        S["compress_progress_text"] = ft.Text("", color=th["fg2"], size=12,
                                                font_family=FONT)
        S["realism_progress_bar"] = ft.ProgressBar(
            value=None, visible=False, color=th["accent"],
            bgcolor=th["input"], height=4, bar_height=4)
        S["realism_progress_text"] = ft.Text("", color=th["fg2"], size=12,
                                               font_family=FONT, visible=False)
        S["stats_column"] = ft.Column([], spacing=4)
        S["log_column_bottom"] = ft.ListView(spacing=3, auto_scroll=True,
                                               expand=True, padding=4)
        S["buttons"] = {}
        S["pbr_buttons"] = {}
        S["compress_buttons"] = {}
        S["pbr_map_buttons"] = {}
        # Восстановить строки лога после rebuild
        refresh_log(S)

    # ═══ Хоткеи ═══
    def on_keyboard(e: ft.KeyboardEvent):
        # Если открыт диалог — не трогаем
        for dlg in page.overlay:
            if isinstance(dlg, ft.AlertDialog) and dlg.open:
                return

        tab = S.get("active_tab", "single")

        # Делегируем в SingleTab, если он активен
        if tab == "single" and "single_tab" in S:
            if S["single_tab"].run_hotkey(e):
                return

        # Ctrl+O / Ctrl+S / Ctrl+R / Ctrl+Z / Space / Enter для других вкладок
        key = (e.key or "").lower()

        if e.ctrl and key == "o":
            if tab == "pbr" and "pbr_tab" in S:
                page.run_task(S["pbr_tab"].pbr_do_load, None)
            elif tab == "compress" and "compress_tab" in S:
                if S["ui_mode"] == "simple":
                    page.run_task(
                        S["compress_tab"].compress_simple_process, None)
                else:
                    page.run_task(
                        S["compress_tab"].compress_open_file, None)
            return

        if e.ctrl and key == "s":
            if tab == "pbr" and "pbr_tab" in S:
                if S.get("pbr_result") is not None:
                    page.run_task(S["pbr_tab"].pbr_do_save, None)
            elif tab == "compress" and "compress_tab" in S:
                if S.get("compress_corrected") is not None:
                    page.run_task(S["compress_tab"].compress_save, None)
            elif tab == "export" and "export_tab" in S:
                if S.get("export_packed") is not None:
                    page.run_task(S["export_tab"].export_save, None)
            return

        if key == "enter":
            if tab == "pbr" and "pbr_tab" in S:
                if S.get("pbr_result") is not None:
                    page.run_task(S["pbr_tab"].pbr_open_viewer, None)
            return

    page.on_keyboard_event = on_keyboard

    # ═══ Сборка UI ═══
    def rebuild_ui():
        th = apply_theme()
        build_shared_elements()

        # Активная вкладка (после смены режима она может стать недоступной)
        S["active_tab"] = get_default_tab(S)

        # ─── Header ───
        header = Header(
            page, S, t, th, APP_VERSION,
            on_toggle_mode, on_toggle_theme,
            on_toggle_lang, on_open_info,
            on_set_lang=on_set_lang,
        ).build()

        # ─── Активная вкладка ───
        active = S["active_tab"]

        if active == "single":
            single = SingleTab(page, S, t, picker, paths, th, S["clip"],
                                on_rebuild, on_persist, on_toggle_lang)
            S["single_tab"] = single
            tab_view = single.build()
        elif active == "pbr":
            pbr = PbrTab(page, S, t, picker, paths, th,
                          on_rebuild, on_persist)
            S["pbr_tab"] = pbr
            tab_view = pbr.build()
        elif active == "export":
            exp = ExportTab(page, S, t, picker, paths, th,
                             on_rebuild, on_persist)
            S["export_tab"] = exp
            tab_view = exp.build()
        elif active == "realism":
            rl = RealismTab(page, S, t, picker, paths, th,
                             on_rebuild, on_persist)
            S["realism_tab"] = rl
            tab_view = rl.build()
        elif active == "batch":
            bt = BatchTab(page, S, t, picker, paths, th,
                           on_rebuild, on_persist)
            S["batch_tab"] = bt
            tab_view = bt.build()
        elif active == "compress":
            cp = CompressTab(page, S, t, picker, paths, th,
                              on_rebuild, on_persist)
            S["compress_tab"] = cp
            tab_view = cp.build()
        else:
            tab_view = ft.Container()

        # ─── Rail ───
        rail = build_rail(page, S, t, th, on_rail_change)

        # ─── LogPanel ───
        log_panel = LogPanel(page, S, t, th, on_clear_log).build()

        # ─── Компоновка ───
        content_holder = ft.Container(
            content=tab_view,
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            expand=True,
        )

        body = ft.Row([
            rail,
            content_holder,
        ], spacing=0, expand=True)

        page.controls.clear()
        page.add(
            ft.Column([
                header,
                ft.Container(content=body, expand=True),
                log_panel,
            ], spacing=0, expand=True)
        )
        page.update()

    # ═══ Первый рендер ═══
    rebuild_ui()
    log(S, t("welcome_1"), color=current_theme()["fg2"],
        fg2=current_theme()["fg2"])
    log(S, t("welcome_2"), color=current_theme()["fg2"],
        fg2=current_theme()["fg2"])
    page.update()

    # ═══ Welcome при первом запуске ═══
    if not S.get("first_launch_done", False):
        async def _show_welcome_later():
            await asyncio.sleep(0.4)
            th = current_theme()
            dlg = show_welcome_dialog(
                page, S, t, th, base_dir,
                on_switch_advanced=rebuild_ui,
                persist_fn=on_persist,
            )
            page.overlay.append(dlg)
            dlg.open = True
            page.update()
        page.run_task(_show_welcome_later)


# ═══ DPI awareness — ДО создания окна Flet ═══
# SetProcessDpiAwareness надо вызвать до ft.run(), иначе Windows
# не отдаёт реальный DPI, и scale не применяется.
if sys.platform == "win32":
    try:
        import ctypes
        # 2 = PROCESS_PER_MONITOR_DPI_AWARE (Win 8.1+)
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


if __name__ == "__main__":
    ft.run(main)