"""
ui/tab_batch.py — вкладка Batch (пакетная AI-коррекция папки).
"""

import os
import asyncio
import gc
from PIL import Image
import flet as ft

from core.image_ops import apply_ai, apply_fallback, apply_soap
from core.io import save_16bit_or_8bit, safe_open_rgb
from core.state import remember_folder, init_dir
from ui.theme import make_btn, section_title, divider
from ui.helpers import (
    log, update_batch_progress, refresh_log,
)

FONT = "Segoe UI"


class BatchTab:
    def __init__(self, page, S, t, picker, paths, theme,
                 on_rebuild, on_persist):
        self.page = page
        self.S = S
        self.t = t
        self.picker = picker
        self.paths = paths
        self.theme = theme
        self.on_rebuild = on_rebuild
        self.on_persist = on_persist

    def build(self) -> ft.Container:
        th = self.theme
        S = self.S

        sel_row = ft.Row([
            make_btn(self.t("batch_select_folder"), self.batch_select_folder,
                     th["accent"], icon="folder-open",
                     size=13, vertical=11, horizontal=16),
            make_btn(self.t("batch_select_files"), self.batch_select_files,
                     th["accent"], icon="layers",
                     size=13, vertical=11, horizontal=16),
        ], spacing=6)

        info_card = ft.Container(
            content=ft.Column([
                ft.Text("AI-коррекция папки", size=10,
                        weight=ft.FontWeight.BOLD,
                        color=th["fg3"], font_family=FONT),
                ft.Container(height=6),
                ft.Text(self.t("batch_no_files"), color=th["fg3"],
                        size=11, visible=False),
            ], spacing=6),
            bgcolor=th["panel"], border_radius=12, padding=16,
        )

        run_btn = make_btn(self.t("batch_run"), self.batch_run,
                            th["success"], icon="play",
                            size=14, vertical=13, horizontal=16)

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        sel_row,
                        ft.Container(height=8),
                        info_card,
                        ft.Container(height=8),
                        run_btn,
                        ft.Container(height=8),
                        S["batch_progress_bar"],
                        S["batch_progress_text"],
                    ], spacing=0, expand=True),
                    expand=True,
                ),
                self._build_right_panel(),
            ], spacing=12, expand=True),
            expand=True, visible=True,
        )

    def _build_right_panel(self) -> ft.Container:
        th = self.theme
        S = self.S
        method = S.get("correction_mode", "ai")

        def _method_btn(label, active, on_click):
            return ft.Container(
                content=ft.Text(label,
                                 color="#ffffff" if active else th["fg2"],
                                 size=11, font_family=FONT,
                                 weight=ft.FontWeight.W_600,
                                 text_align=ft.TextAlign.CENTER),
                bgcolor=th["accent"] if active else th["card"],
                border_radius=8,
                padding=ft.Padding.symmetric(vertical=8, horizontal=6),
                expand=True, ink=not active, on_click=on_click,
            )

        def set_math():
            S["correction_mode"] = "math"
            self.on_persist()
            self.on_rebuild()

        def set_ai():
            S["correction_mode"] = "ai"
            self.on_persist()
            self.on_rebuild()

        return ft.Container(
            content=ft.Column([
                section_title(self.t("batch_right_title"), th["fg3"]),
                ft.Container(height=8),
                section_title(self.t("correction_mode_title"), th["fg3"]),
                ft.Container(height=6),
                ft.Row([
                    _method_btn(self.t("correction_ai_autolevels"),
                                 method == "ai", lambda e: set_ai()),
                    _method_btn(self.t("correction_math"),
                                 method == "math", lambda e: set_math()),
                ], spacing=4),
                ft.Container(height=14),
                divider(th["fg3"]),
                ft.Container(height=10),
                section_title(self.t("soap_fix_title"), th["fg3"]),
                ft.Container(height=6),
                ft.Text(self.t("soap_fix_label"), color=th["fg2"],
                        size=11, font_family=FONT),
                ft.Slider(min=0.0, max=3.0, divisions=15,
                          value=S["soap_fix_strength"], label="{value}",
                          active_color=th["accent"],
                          inactive_color=th["input"],
                          on_change=lambda e: S.update(
                              {"soap_fix_strength": e.control.value})),
                ft.Container(height=14),
                divider(th["fg3"]),
                ft.Container(height=10),
                section_title(self.t("batch_threads_title"), th["fg3"]),
                ft.Container(height=6),
                ft.Text(self.t("batch_threads_label"), color=th["fg2"],
                        size=11, font_family=FONT),
                ft.Slider(min=1, max=8, divisions=7,
                          value=S.get("batch_threads", 3), label="{value}",
                          active_color=th["accent"],
                          inactive_color=th["input"],
                          on_change=lambda e: S.update(
                              {"batch_threads": int(e.control.value)})),
                ft.Container(height=14),
                divider(th["fg3"]),
                ft.Container(height=10),
                section_title(self.t("batch_right_info"), th["fg3"]),
                ft.Container(height=8),
                ft.Text(self.t("batch_right_hint"), color=th["fg2"],
                        size=11, font_family=FONT, selectable=True),
            ], spacing=4, scroll=ft.ScrollMode.AUTO),
            bgcolor=th["panel"], border_radius=12,
            padding=16, width=320,
        )

    # ─── Действия ───

    async def batch_select_folder(self, e=None):
        th = self.theme
        try:
            folder = await self.picker.get_directory_path(
                dialog_title=self.t("batch_select_folder"))
            if not folder:
                return
            exts = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')
            files = [os.path.join(folder, f) for f in os.listdir(folder)
                     if f.lower().endswith(exts)]
            self.S["batch_files"] = files
            log(self.S, f"📁 {self.t('batch_folder')} {folder}",
                color=th["fg2"], fg2=th["fg2"])
            log(self.S, f"   {self.t('batch_found')} {len(files)}",
                color=th["fg2"], fg2=th["fg2"])
            self.S["batch_progress_bar"].value = 0
            self.S["batch_progress_text"].value = (
                f"{self.t('batch_ready')}: {len(files)} "
                f"{self.t('batch_files_count')}"
            )
            self.page.update()
        except Exception as ex:
            log(self.S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def batch_select_files(self, e=None):
        th = self.theme
        try:
            files = await self.picker.pick_files(
                dialog_title=self.t("batch_select_files"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                allow_multiple=True,
                initial_directory=init_dir(self.S),
            )
            if not files:
                return
            if files[0].path:
                remember_folder(self.S, files[0].path)
            self.S["batch_files"] = [f.path for f in files if f.path]
            log(self.S, f"📄 {self.t('batch_selected')} "
                        f"{len(self.S['batch_files'])}",
                color=th["fg2"], fg2=th["fg2"])
            self.S["batch_progress_bar"].value = 0
            self.S["batch_progress_text"].value = (
                f"{self.t('batch_ready')}: {len(self.S['batch_files'])} "
                f"{self.t('batch_files_count')}"
            )
            self.page.update()
        except Exception as ex:
            log(self.S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def batch_run(self, e=None):
        S = self.S
        th = self.theme
        files = S["batch_files"]
        if not files:
            log(S, self.t("batch_no_files"), color=th["warn"],
                fg2=th["fg2"])
            self.page.update()
            return

        total = len(files)
        update_batch_progress(S, self.page, 0, total,
                               f"Запуск... 0 / {total}",
                               fg2=th["fg2"])

        base_dir = os.path.dirname(files[0])
        out_dir = os.path.join(base_dir, "_corrected")
        os.makedirs(out_dir, exist_ok=True)

        log(S, "", fg2=th["fg2"])
        log(S, "━━━━━━━━━━━━━━━━━━━━━━", color=th["fg3"], fg2=th["fg2"])
        log(S, f"{self.t('batch_started')} {total}",
            color=th["fg"], fg2=th["fg2"])
        log(S, f"   {self.t('batch_out')} {out_dir}",
            color=th["fg2"], fg2=th["fg2"])
        self.page.update()

        count = 0
        done = 0
        sem = asyncio.Semaphore(max(1, min(8, S.get("batch_threads", 3))))

        async def process_one(fp):
            nonlocal count, done
            async with sem:
                base = os.path.splitext(os.path.basename(fp))[0]
                out_path = os.path.join(out_dir, f"{base}.png")
                err = None
                ok = False
                try:
                    img = await asyncio.to_thread(safe_open_rgb, fp)
                    if S["correction_mode"] == "math":
                        result = await asyncio.to_thread(
                            apply_fallback, img, S["profile"])
                    else:
                        import time as _time
                        _t0 = _time.time()
                        ai_res, ai_ok, ai_err = await asyncio.to_thread(
                            apply_ai, img, S["ai_model"],
                            self.paths["autolevels_exe"],
                            self.paths["autolevels_model"],
                            self.paths["lutwithbgrid_model"],
                        )
                        _dt = _time.time() - _t0
                        log(S, f"   ⏱ {os.path.basename(fp)}: {_dt:.2f} сек",
                            color=th["fg2"], fg2=th["fg2"])
                        if ai_ok and ai_res is not None:
                            result = ai_res
                        else:
                            result = await asyncio.to_thread(
                                apply_fallback, img, S["profile"])
                    if S["soap_fix_strength"] > 0:
                        result = await asyncio.to_thread(
                            apply_soap, result, S["soap_fix_strength"])
                    await asyncio.to_thread(
                        save_16bit_or_8bit, result, out_path, 16)
                    img.close()
                    ok = True
                except Exception as ex:
                    err = f"{type(ex).__name__}: {ex}"
                done += 1
                if ok:
                    count += 1
                    log(S, f"  [{done}/{total}] ✓ {os.path.basename(fp)}",
                        color=th["success"], fg2=th["fg2"])
                else:
                    log(S, f"  ✗ {os.path.basename(fp)}: {err}",
                        color=th["danger"], fg2=th["fg2"])
                update_batch_progress(S, self.page, done, total,
                                       fg2=th["fg2"])
                self.page.update()

        await asyncio.gather(*[process_one(fp) for fp in files])

        log(S, f"✅ {self.t('batch_processed')} {count} / {total}",
            color=th["success"], fg2=th["fg2"])
        log(S, f"📁 {out_dir}", color=th["fg2"], fg2=th["fg2"])
        update_batch_progress(S, self.page, total, total,
                               f"{self.t('batch_done')}: {count} / {total}",
                               fg2=th["fg2"])
        S["batch_files"] = []
        self.page.update()