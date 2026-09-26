"""
ui/helpers.py — лог, статистика, прогресс-бары.

Работает с любым dict-like S (словарём состояния из core/state.py).
Не импортирует core — не создаёт циклических зависимостей.
"""

import asyncio
import flet as ft

FONT = "Segoe UI"
FONT_MONO = "Consolas"


# ═══════════════════════════════════════════════════════════
#  ЛОГ
# ═══════════════════════════════════════════════════════════

def log(S: dict, text: str, color: str = None, fg2: str = "#9aa0a6"):
    """Добавляет строку в лог и обновляет ListView."""
    S["log_lines"].append((text, color or fg2))
    if len(S["log_lines"]) > 200:
        S["log_lines"].pop(0)
    refresh_log(S)


def refresh_log(S: dict):
    """Перерисовывает весь лог из S['log_lines']."""
    lc = S.get("log_column_bottom")
    if lc is None:
        return
    lc.controls.clear()
    for txt, col in S["log_lines"]:
        lc.controls.append(
            ft.Text(txt, color=col, size=13, font_family=FONT_MONO,
                    selectable=True, expand=True)
        )
    # Обновляем свёрнутый preview, если есть
    prev = S.get("log_collapsed_preview")
    if prev is not None:
        if S["log_lines"]:
            last_txt, last_col = S["log_lines"][-1]
            prev.value = last_txt
            prev.color = last_col
        else:
            prev.value = ""


def clear_log(S: dict):
    """Очищает лог."""
    S["log_lines"].clear()
    refresh_log(S)


# ═══════════════════════════════════════════════════════════
#  СТАТИСТИКА
# ═══════════════════════════════════════════════════════════

def add_stat(S: dict, label: str, value: str,
             color: str = None, fg2: str = "#9aa0a6",
             fg3: str = "#5f6368"):
    """Добавляет строку в панель статистики."""
    col = color or fg2
    S["stats_lines"].append((label, value, col))
    col_ctrl = S.get("stats_column")
    if col_ctrl is None:
        return
    col_ctrl.controls.append(
        ft.Row([
            ft.Text(label, color=fg3, size=13, font_family=FONT, width=95),
            ft.Text(value, color=col, size=13, font_family=FONT_MONO,
                    weight=ft.FontWeight.W_600),
        ], spacing=8)
    )


def clear_stats(S: dict):
    """Очищает панель статистики."""
    S["stats_lines"].clear()
    col_ctrl = S.get("stats_column")
    if col_ctrl is not None:
        col_ctrl.controls.clear()


# ═══════════════════════════════════════════════════════════
#  ПРОГРЕСС-БАРЫ (async)
# ═══════════════════════════════════════════════════════════

async def show_progress(S: dict, page: ft.Page, text: str = "Обработка...",
                        fg2: str = "#9aa0a6"):
    bar = S.get("progress_bar")
    lbl = S.get("progress_text")
    if bar:
        bar.visible = True
    if lbl:
        lbl.value = text
        lbl.visible = True
    page.update()
    await asyncio.sleep(0.05)
    page.update()


async def hide_progress(S: dict, page: ft.Page):
    bar = S.get("progress_bar")
    lbl = S.get("progress_text")
    if bar:
        bar.visible = False
    if lbl:
        lbl.visible = False
    page.update()
    await asyncio.sleep(0.02)


async def show_pbr_progress(S: dict, page: ft.Page, text: str = "Обработка..."):
    bar = S.get("pbr_progress_bar")
    lbl = S.get("pbr_progress_text")
    if bar:
        bar.visible = True
    if lbl:
        lbl.value = text
        lbl.visible = True
    page.update()
    await asyncio.sleep(0.05)
    page.update()


async def hide_pbr_progress(S: dict, page: ft.Page):
    bar = S.get("pbr_progress_bar")
    lbl = S.get("pbr_progress_text")
    if bar:
        bar.visible = False
    if lbl:
        lbl.visible = False
    page.update()
    await asyncio.sleep(0.02)


async def show_realism_progress(S: dict, page: ft.Page,
                                 text: str = "Обработка..."):
    bar = S.get("realism_progress_bar")
    lbl = S.get("realism_progress_text")
    if bar:
        bar.visible = True
    if lbl:
        lbl.value = text
        lbl.visible = True
    page.update()
    await asyncio.sleep(0.05)
    page.update()


async def hide_realism_progress(S: dict, page: ft.Page):
    bar = S.get("realism_progress_bar")
    lbl = S.get("realism_progress_text")
    if bar:
        bar.visible = False
    if lbl:
        lbl.visible = False
    page.update()
    await asyncio.sleep(0.02)


# ═══════════════════════════════════════════════════════════
#  ПРОГРЕСС-БАРЫ БЕЗ ASYNC (batch / compress)
# ═══════════════════════════════════════════════════════════

def update_batch_progress(S: dict, page: ft.Page, done: int, total: int,
                          text: str = None, fg2: str = "#9aa0a6"):
    pct = int((done / total) * 100) if total > 0 else 0
    bar = S.get("batch_progress_bar")
    lbl = S.get("batch_progress_text")
    if bar:
        bar.value = pct / 100
    if lbl:
        lbl.value = text if text is not None else f"{done} / {total}  ({pct}%)"
    page.update()


def update_compress_progress(S: dict, page: ft.Page, done: int, total: int,
                              text: str = None, fg2: str = "#9aa0a6"):
    pct = int((done / total) * 100) if total > 0 else 0
    bar = S.get("compress_progress_bar")
    lbl = S.get("compress_progress_text")
    if bar:
        bar.value = pct / 100
    if lbl:
        lbl.value = text if text is not None else f"{done} / {total}  ({pct}%)"
    page.update()