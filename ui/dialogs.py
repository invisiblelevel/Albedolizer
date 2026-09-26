"""
ui/dialogs.py — общие диалоги Albedolizer.

Info (Help / About / Support / Manual), Welcome (первый запуск),
Compress-done (результат сжатия).
"""

import os
import webbrowser
import flet as ft

from config import WALLETS
from ui.icons import img_icon
from ui.theme import make_btn, divider
from ui.helpers import log

FONT = "Segoe UI"
FONT_MONO = "Consolas"
ON_ACCENT = "#ffffff"


# ═══════════════════════════════════════════════════════════
#  INFO-ДИАЛОГ (Help / About / Support / Manual)
# ═══════════════════════════════════════════════════════════

def create_info_dialog(page, S, t, theme, base_dir) -> ft.AlertDialog:
    """
    Возвращает готовый AlertDialog с 4 табами.
    Зовётся из header.
    """
    th = theme

    # ─── Help content ───
    help_content = ft.Container(
        content=ft.Column(
            [ft.Text(t("help_text"), color=th["fg"], size=12,
                     font_family=FONT_MONO, selectable=True, expand=True)],
            scroll=ft.ScrollMode.AUTO, expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
        padding=ft.Padding.only(left=16, top=16, bottom=16, right=28),
        visible=True, expand=True,
    )

    # ─── About content ───
    about_rows = [
        ("about_version", "1.7.5-beta"),
        ("about_build", "2026-09-26"),
        ("about_author", "INV.LVL"),
        ("about_license", "Free / Open Source"),
    ]
    about_col = [
        ft.Text("Albedolizer", size=24, weight=ft.FontWeight.BOLD,
                color=th["accent"], font_family=FONT),
        ft.Container(height=16),
    ]
    for key, val in about_rows:
        about_col.append(ft.Row([
            ft.Text(f"{t(key)}:", color=th["fg3"], size=12,
                    font_family=FONT, width=100),
            ft.Text(val, color=th["fg"], size=12,
                    font_family=FONT_MONO, weight=ft.FontWeight.W_600),
        ]))
    about_col.extend([
        ft.Container(height=20),
        ft.Text(t("about_desc"), color=th["fg2"], size=11, font_family=FONT),
    ])
    about_content = ft.Container(
        content=ft.Column(about_col, spacing=6),
        padding=20, visible=False,
    )

    # ─── Support content ───
    copy_feedback = ft.Text("", color=th["success"], size=11,
                             font_family=FONT)

    def copy_address(addr):
        def _do(e):
            try:
                page.set_clipboard(addr)
                copy_feedback.value = t("support_copied")
            except Exception:
                copy_feedback.value = addr
            page.update()
        return _do

    wallet_cards = []
    for w in WALLETS:
        card = ft.Container(
            content=ft.Row([
                ft.Text(w["label"], color=th["accent"], size=12,
                        font_family=FONT, width=130,
                        weight=ft.FontWeight.W_600),
                ft.Text(w["address"], color=th["fg"], size=11,
                        font_family=FONT_MONO, selectable=True, expand=True),
                ft.Container(
                    content=img_icon("copy", th["fg"], 14),
                    bgcolor=th["card"], border_radius=6,
                    padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                    ink=True, on_click=copy_address(w["address"]),
                ),
            ], spacing=8,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=th["card"], border_radius=8, padding=10,
        )
        wallet_cards.append(card)

    support_content = ft.Container(
        content=ft.Column([
            img_icon("heart", th["save"], 42),
            ft.Text(t("support_title"), size=18,
                    weight=ft.FontWeight.BOLD, color=th["fg"],
                    font_family=FONT, text_align=ft.TextAlign.CENTER),
            ft.Container(height=8),
            ft.Text(t("support_text"), color=th["fg2"], size=11,
                    font_family=FONT, text_align=ft.TextAlign.CENTER),
            ft.Container(height=16),
            *wallet_cards,
            ft.Container(height=8),
            copy_feedback,
        ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=20, visible=False,
    )

    # ─── Tab switcher ───
    tab_btns = {}

    def set_info_tab(name):
        help_content.visible = (name == "help")
        about_content.visible = (name == "about")
        support_content.visible = (name == "support")
        for k, b in tab_btns.items():
            b.content.color = ON_ACCENT if k == name else th["fg2"]
            b.bgcolor = th["accent"] if k == name else th["card"]
        page.update()

    def make_tab(key, label):
        b = ft.Container(
            content=ft.Text(label, color=th["fg2"], size=12,
                            font_family=FONT, weight=ft.FontWeight.W_600),
            bgcolor=th["card"], border_radius=8,
            padding=ft.Padding.symmetric(vertical=8, horizontal=14),
            ink=True, on_click=lambda e, k=key: set_info_tab(k),
        )
        tab_btns[key] = b
        return b

    # ─── Manual button ───
    def open_manual(e=None):
        manual_path = os.path.join(base_dir, "manual.html")
        if os.path.exists(manual_path):
            webbrowser.open(f"file:///{manual_path.replace(os.sep, '/')}")
            log(S, "📖 Мануал открыт в браузере",
                color=th["fg2"], fg2=th["fg2"])
        else:
            log(S, f"⚠ manual.html не найден: {manual_path}",
                color=th["warn"], fg2=th["fg2"])
        page.update()

    def close_info(e=None):
        dlg.open = False
        page.update()

    # ─── Кнопка закрытия ───
    close_btn = ft.Container(
        content=img_icon("x", th["fg"], 14),
        bgcolor=th["card"], border_radius=8,
        padding=ft.Padding.symmetric(vertical=6, horizontal=12),
        ink=True, on_click=close_info,
    )

    manual_btn = ft.Container(
        content=ft.Row([
            img_icon("book-open", ON_ACCENT, 14),
            ft.Text(t("info_tab_manual"), color=ON_ACCENT, size=12,
                    font_family=FONT, weight=ft.FontWeight.W_600),
        ], spacing=6, tight=True,
           vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=th["accent"], border_radius=8,
        padding=ft.Padding.symmetric(vertical=8, horizontal=14),
        ink=True, on_click=open_manual,
    )

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            make_tab("help", t("info_tab_help")),
            make_tab("about", t("info_tab_about")),
            make_tab("support", t("info_tab_support")),
            manual_btn,
            ft.Container(expand=True),
            close_btn,
        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        content=ft.Container(
            content=ft.Column([help_content, about_content, support_content],
                              spacing=0),
            width=600, height=420,
        ),
        bgcolor=th["panel"],
    )
    set_info_tab("help")
    return dlg


# ═══════════════════════════════════════════════════════════
#  WELCOME-ДИАЛОГ (первый запуск)
# ═══════════════════════════════════════════════════════════

def show_welcome_dialog(page, S, t, theme, base_dir, on_switch_advanced,
                        persist_fn):
    """
    Welcome при первом запуске. Возвращает AlertDialog (уже открытый).
    """
    th = theme

    def _close(e=None):
        dlg.open = False
        S["first_launch_done"] = True
        persist_fn()
        page.update()

    def _open_manual(e=None):
        dlg.open = False
        S["first_launch_done"] = True
        persist_fn()
        manual_path = os.path.join(base_dir, "manual.html")
        if os.path.exists(manual_path):
            webbrowser.open(f"file:///{manual_path.replace(os.sep, '/')}")
        page.update()

    def _switch_advanced(e=None):
        dlg.open = False
        S["first_launch_done"] = True
        S["ui_mode"] = "advanced"
        persist_fn()
        on_switch_advanced()

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Text("Albedolizer", size=16, color=th["accent"],
                    weight=ft.FontWeight.BOLD, font_family=FONT),
        ], spacing=10),
        content=ft.Container(
            content=ft.Text(t("welcome_text"), color=th["fg2"], size=12,
                            font_family=FONT, selectable=True),
            width=480,
            padding=ft.Padding.symmetric(vertical=8),
        ),
        actions=[
            ft.TextButton(t("welcome_manual"), on_click=_open_manual),
            ft.TextButton(t("welcome_switch_simple"),
                          on_click=_switch_advanced),
            ft.FilledButton(
                content=ft.Text(t("welcome_ok"), color=ON_ACCENT,
                                size=13, weight=ft.FontWeight.W_600),
                style=ft.ButtonStyle(bgcolor=th["success"]),
                on_click=_close,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        bgcolor=th["panel"],
        inset_padding=ft.Padding.symmetric(horizontal=60, vertical=80),
    )
    return dlg


# ═══════════════════════════════════════════════════════════
#  COMPRESS DONE
# ═══════════════════════════════════════════════════════════

def show_compress_done_dialog(page, S, t, theme, out_path,
                               orig_size, new_size,
                               is_batch=False, count=0, total=0):
    """Диалог 'Готово' с размерами и кнопкой открыть папку."""
    from core.io import fmt_size

    th = theme
    saved = orig_size - new_size
    pct = (saved / orig_size) * 100 if orig_size > 0 else 0

    if saved > 0:
        size_line = (f"{fmt_size(orig_size)} → {fmt_size(new_size)}  "
                     f"(−{fmt_size(saved)}, −{pct:.1f}%)")
        size_color = th["success"]
    elif saved < 0:
        size_line = (f"{fmt_size(orig_size)} → {fmt_size(new_size)}  "
                     f"(+{fmt_size(-saved)}, +{abs(pct):.1f}%)")
        size_color = th["warn"]
    else:
        size_line = f"{fmt_size(orig_size)}  ({t('compress_done_same')})"
        size_color = th["fg2"]

    folder = os.path.dirname(out_path) if os.path.isfile(out_path) else out_path

    def _open_folder(e=None):
        try:
            os.startfile(folder)
        except Exception as ex:
            log(S, f"⚠ Не удалось открыть папку: {ex}",
                color=th["warn"], fg2=th["fg2"])
        dlg.open = False
        page.update()

    def _close(e=None):
        dlg.open = False
        page.update()

    rows = []
    if is_batch:
        rows.append(ft.Row([
            ft.Text(t("compress_done_batch"), color=th["fg3"], size=12,
                    font_family=FONT, width=170),
            ft.Text(f"{count} / {total}", color=th["fg"], size=12,
                    font_family=FONT_MONO, weight=ft.FontWeight.W_600),
        ], spacing=8))
    else:
        rows.append(ft.Row([
            ft.Text(t("compress_done_single"), color=th["fg3"], size=12,
                    font_family=FONT, width=170),
            ft.Text(os.path.basename(out_path), color=th["fg"], size=12,
                    font_family=FONT_MONO, weight=ft.FontWeight.W_600,
                    selectable=True),
        ], spacing=8))
    rows.extend([
        ft.Row([
            ft.Text(t("compress_done_size"), color=th["fg3"], size=12,
                    font_family=FONT, width=170),
            ft.Text(size_line, color=size_color, size=12,
                    font_family=FONT_MONO, weight=ft.FontWeight.W_600),
        ], spacing=8),
        ft.Container(height=6),
        ft.Text(folder, color=th["fg3"], size=11,
                font_family=FONT_MONO, selectable=True),
    ])

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            img_icon("check", th["success"], 18),
            ft.Text(t("compress_done_title"), color=th["fg"], size=14,
                    weight=ft.FontWeight.W_600),
        ], spacing=8),
        content=ft.Container(
            content=ft.Column(rows, spacing=6, tight=True),
            width=460,
        ),
        actions=[
            ft.TextButton(t("compress_open_folder"), on_click=_open_folder),
            ft.TextButton(t("compress_ok"), on_click=_close),
        ],
        inset_padding=ft.Padding.symmetric(horizontal=80, vertical=120),
        bgcolor=th["panel"],
    )
    page.overlay.append(dlg)
    dlg.open = True
    page.update()


# ═══════════════════════════════════════════════════════════
#  FALLBACK-ДИАЛОГ (используется из tab_single)
# ═══════════════════════════════════════════════════════════

def show_fallback_dialog(page, S, t, theme, current_img, stats,
                          on_apply_fallback, on_keep_ai):
    """
    Диалог 'AI не прошёл проверку'.

    on_apply_fallback — async callback() — вызвать fallback коррекцию.
    on_keep_ai        — sync callback() — оставить как есть.
    """
    th = theme
    dialog_ref = {"dlg": None}

    async def _apply(e=None):
        dialog_ref["dlg"].open = False
        page.update()
        await on_apply_fallback()

    def _keep(e=None):
        dialog_ref["dlg"].open = False
        page.update()
        on_keep_ai()

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(t("fb_dialog_title"), color=th["fg"], size=14),
        content=ft.Container(
            content=ft.Column([
                ft.Text(t("fb_dialog_text"), color=th["fg2"], size=12,
                        font_family=FONT),
                ft.Container(height=4),
                ft.Text(f"  {t('fb_dialog_dark')} "
                        f"{stats['dark_pct']:.2f}%",
                        color=th["danger"] if stats['dark_pct'] > 5
                        else th["success"],
                        size=12, font_family=FONT_MONO),
                ft.Text(f"  {t('fb_dialog_light')} "
                        f"{stats['light_pct']:.2f}%",
                        color=th["danger"] if stats['light_pct'] > 5
                        else th["success"],
                        size=12, font_family=FONT_MONO),
                ft.Container(height=6),
                ft.Text(t("fb_dialog_question"), color=th["fg"],
                        size=12, font_family=FONT),
            ], spacing=2, tight=True),
            width=380, height=140,
        ),
        actions=[
            ft.TextButton(t("fb_dialog_keep_ai"), on_click=_keep),
            ft.TextButton(t("fb_dialog_apply"), on_click=_apply),
        ],
        inset_padding=ft.Padding.symmetric(horizontal=80, vertical=120),
        bgcolor=th["panel"],
    )
    dialog_ref["dlg"] = dlg
    page.overlay.append(dlg)
    dlg.open = True
    page.update()