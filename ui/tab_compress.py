"""
ui/tab_compress.py — вкладка Compress (сжатие Albedo).

Simple: две большие кнопки (файл / папка) — автосохранение в _compressed.
Advanced: одиночное сжатие + пакетное + выбор битности.
"""

import os
import asyncio
import gc
from PIL import Image
import flet as ft

from core.image_ops import lab_roundtrip
from core.io import save_16bit_or_8bit, pil_to_b64, fmt_size, safe_open_rgb
from core.state import remember_folder, init_dir
from ui.theme import make_btn, section_title, divider
from ui.helpers import (
    log, update_compress_progress,
)

FONT = "Segoe UI"


class CompressTab:
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

        self.preview_image = None
        self.preview_hint = None
        self.compress_buttons = {}

    def build(self) -> ft.Container:
        is_simple = self.S["ui_mode"] == "simple"
        if is_simple:
            return self._build_simple()
        return self._build_advanced()

    # ─── SIMPLE ───

    def _build_simple(self) -> ft.Container:
        th = self.theme
        S = self.S

        card_single = ft.Container(
            content=ft.Column([
                section_title(self.t("compress_single"), th["fg3"]),
                ft.Container(height=8),
                make_btn(self.t("compress_single_btn"),
                         self.compress_simple_process, th["compress"],
                         icon="archive",
                         size=14, vertical=13, horizontal=16),
                ft.Container(height=8),
                ft.Text(self.t("compress_simple_hint"), color=th["fg2"],
                        size=11, font_family=FONT),
            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=th["panel"], border_radius=12, padding=16, width=520,
        )

        card_batch = ft.Container(
            content=ft.Column([
                section_title(self.t("compress_batch"), th["fg3"]),
                ft.Container(height=8),
                make_btn(self.t("compress_batch_btn"),
                         self.compress_simple_batch, th["compress"],
                         icon="layers",
                         size=14, vertical=13, horizontal=16),
                ft.Container(height=8),
                ft.Text(self.t("compress_batch_hint"), color=th["fg2"],
                        size=11, font_family=FONT),
            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=th["panel"], border_radius=12, padding=16, width=520,
        )

        return ft.Container(
            content=ft.Column([
                S["compress_progress_bar"],
                S["compress_progress_text"],
                ft.Container(height=8),
                card_single,
                ft.Container(height=8),
                card_batch,
            ], spacing=0, expand=True,
               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, visible=True,
        )

    # ─── ADVANCED ───

    def _build_advanced(self) -> ft.Container:
        th = self.theme
        S = self.S

        self.preview_image = ft.Image(src="", visible=False,
                                        fit=ft.BoxFit.CONTAIN)
        # Восстановить превью после rebuild
        _prev_src = None
        if S.get("compress_corrected") is not None:
            _prev_src = f"data:image/png;base64,{pil_to_b64(S['compress_corrected'])}"
        elif S.get("compress_original") is not None:
            _prev_src = f"data:image/png;base64,{pil_to_b64(S['compress_original'])}"
        if _prev_src:
            self.preview_image.src = _prev_src
            self.preview_image.visible = True

        self.preview_hint = ft.Text(self.t("preview_hint"),
                                     color=th["fg3"], size=14,
                                     font_family=FONT,
                                     visible=(_prev_src is None))
        S["compress_preview"] = self.preview_image
        S["compress_preview_hint"] = self.preview_hint

        preview_box = ft.Container(
            content=ft.Stack([
                ft.Container(content=self.preview_hint,
                              alignment=ft.Alignment.CENTER, expand=True),
                ft.Container(content=self.preview_image,
                              alignment=ft.Alignment.CENTER, expand=True),
            ], expand=True),
            bgcolor=th["card"], border_radius=12, padding=10, expand=True,
        )

        # Кнопки single
        open_btn = make_btn(self.t("load"), self.compress_open_file,
                             th["accent"], icon="folder-open",
                             size=13, vertical=11, horizontal=16)
        run_btn = make_btn(self.t("compress_run"), self.compress_do,
                            th["compress"], icon="archive",
                            disabled=(S.get("compress_original") is None),
                            size=13, vertical=11, horizontal=16)
        save_btn = make_btn(self.t("save"), self.compress_save, th["save"],
                             icon="save",
                             disabled=(S.get("compress_corrected") is None),
                             size=13, vertical=11, horizontal=16)
        self.compress_buttons = {"open": open_btn, "run": run_btn,
                                   "save": save_btn}
        S["compress_buttons"] = self.compress_buttons

        toolbar = ft.Row([open_btn, run_btn, ft.Container(expand=True),
                           save_btn], spacing=6)

        card_single = ft.Container(
            content=ft.Column([
                section_title(self.t("compress_single"), th["fg3"]),
                ft.Container(height=6),
                toolbar,
                ft.Container(height=8),
                ft.Container(content=preview_box, expand=True),
            ], spacing=0, expand=True),
            bgcolor=th["panel"], border_radius=12, padding=16, expand=True,
        )

        # Batch
        batch_sel = ft.Row([
            make_btn(self.t("batch_select_folder"),
                     self.compress_select_folder, th["accent"],
                     icon="folder-open",
                     size=12, vertical=10, horizontal=14),
            make_btn(self.t("batch_select_files"),
                     self.compress_select_files, th["accent"],
                     icon="layers",
                     size=12, vertical=10, horizontal=14),
            ft.Container(expand=True),
            make_btn(self.t("compress_batch_run"), self.compress_batch_run,
                     th["compress"], icon="play",
                     size=12, vertical=10, horizontal=14),
        ], spacing=6)

        card_batch = ft.Container(
            content=ft.Column([
                section_title(self.t("compress_batch"), th["fg3"]),
                ft.Container(height=6),
                batch_sel,
            ], spacing=6),
            bgcolor=th["panel"], border_radius=12, padding=16,
        )

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        S["compress_progress_bar"],
                        S["compress_progress_text"],
                        ft.Container(height=6),
                        card_single,
                        ft.Container(height=8),
                        card_batch,
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

        def _on_bit_change(e):
            S["pbr_bit_depth"] = int(e.control.value)
            self.on_persist()

        return ft.Container(
            content=ft.Column([
                section_title(self.t("compress_right_title"), th["fg3"]),
                ft.Container(height=8),
                ft.Text(self.t("pbr_bit_depth"), color=th["fg2"],
                        size=12, font_family=FONT),
                ft.Container(height=4),
                ft.RadioGroup(
                    content=ft.Row([
                        ft.Radio(value="8", label="8-bit",
                                 fill_color=th["compress"]),
                        ft.Radio(value="16", label="16-bit",
                                 fill_color=th["compress"]),
                    ]),
                    value=str(S["pbr_bit_depth"]),
                    on_change=_on_bit_change,
                ),
                ft.Container(height=14),
                divider(th["fg3"]),
                ft.Container(height=10),
                section_title(self.t("compress_right_info"), th["fg3"]),
                ft.Container(height=8),
                ft.Text(self.t("compress_right_hint"), color=th["fg2"],
                        size=11, font_family=FONT, selectable=True),
            ], spacing=4, scroll=ft.ScrollMode.AUTO),
            bgcolor=th["panel"], border_radius=12,
            padding=16, width=320,
        )

    # ─── Действия ───

    async def compress_open_file(self, e=None):
        th = self.theme
        try:
            files = await self.picker.pick_files(
                dialog_title=self.t("dialog_pick_title"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                initial_directory=init_dir(self.S),
            )
            if not files or not files[0].path:
                return
            fp = files[0].path
            remember_folder(self.S, fp)
            img = await asyncio.to_thread(safe_open_rgb, fp)
            self.S["compress_original"] = img
            self.S["compress_path"] = fp
            self.S["compress_corrected"] = None
            self.preview_image.src = f"data:image/png;base64,{pil_to_b64(img)}"
            self.preview_image.visible = True
            self.preview_hint.visible = False
            log(self.S, f"{self.t('log_loaded')} {os.path.basename(fp)}",
                color=th["success"], fg2=th["fg2"])
            self.on_rebuild()
        except Exception as ex:
            log(self.S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def compress_do(self, e=None):
        th = self.theme
        S = self.S
        if S.get("compress_original") is None:
            return
        try:
            S["compress_progress_text"].value = self.t("progress_compress")
            S["compress_progress_text"].visible = True
            S["compress_progress_bar"].value = None
            S["compress_progress_bar"].visible = True
            self.page.update()
            await asyncio.sleep(0.1)
            result = await asyncio.to_thread(
                lab_roundtrip, S["compress_original"])
            S["compress_corrected"] = result
            self.preview_image.src = f"data:image/png;base64,{pil_to_b64(result)}"
            log(S, self.t("log_compress_done"),
                color=th["success"], fg2=th["fg2"])
            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            self.on_rebuild()
        except Exception as ex:
            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            log(S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def compress_save(self, e=None):
        th = self.theme
        S = self.S
        if S.get("compress_corrected") is None:
            return
        try:
            base = "albedo"
            if S.get("compress_path"):
                base = os.path.splitext(
                    os.path.basename(S["compress_path"]))[0]
            path = await self.picker.save_file(
                dialog_title=self.t("dialog_save_title"),
                file_name=f"{base}_compressed.png",
                allowed_extensions=["png", "jpg", "tif"],
                initial_directory=init_dir(S),
            )
            if not path:
                return
            S["compress_progress_text"].value = "💾 Сохранение..."
            S["compress_progress_text"].visible = True
            S["compress_progress_bar"].value = None
            S["compress_progress_bar"].visible = True
            self.page.update()
            await asyncio.sleep(0.05)
            await asyncio.to_thread(
                save_16bit_or_8bit, S["compress_corrected"], str(path),
                S.get("pbr_bit_depth", 16))
            remember_folder(S, str(path))
            log(S, f"{self.t('log_saved')} {os.path.basename(str(path))}",
                color=th["success"], fg2=th["fg2"])
            # Показать дельту
            try:
                osz = os.path.getsize(S["compress_path"]) if S.get("compress_path") else 0
                nsz = os.path.getsize(str(path))
                if osz > 0 and nsz > 0:
                    saved = osz - nsz
                    pct = (saved / osz) * 100
                    if saved > 0:
                        log(S, f"   📉 Сжатие: {fmt_size(osz)} → "
                               f"{fmt_size(nsz)}  (−{fmt_size(saved)}, "
                               f"−{pct:.1f}%)",
                            color=th["success"], fg2=th["fg2"])
                    elif saved < 0:
                        log(S, f"   📈 Файл вырос: {fmt_size(osz)} → "
                               f"{fmt_size(nsz)}  (+{fmt_size(-saved)}, "
                               f"+{abs(pct):.1f}%)",
                            color=th["warn"], fg2=th["fg2"])
            except Exception:
                pass
            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            self.page.update()
        except Exception as ex:
            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            log(S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def compress_select_folder(self, e=None):
        try:
            folder = await self.picker.get_directory_path(
                dialog_title=self.t("batch_select_folder"))
            if not folder:
                return
            exts = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')
            files = [os.path.join(folder, f) for f in os.listdir(folder)
                     if f.lower().endswith(exts)]
            self.S["compress_files"] = files
            log(self.S, f"📁 {self.t('batch_folder')} {folder}",
                color=self.theme["fg2"], fg2=self.theme["fg2"])
            log(self.S, f"   {self.t('batch_found')} {len(files)}",
                color=self.theme["fg2"], fg2=self.theme["fg2"])
            update_compress_progress(
                self.S, self.page, 0, len(files),
                f"{self.t('batch_ready')}: {len(files)} "
                f"{self.t('batch_files_count')}",
                fg2=self.theme["fg2"])
        except Exception as ex:
            log(self.S, f"❌ {self.t('err')}: {ex}",
                color=self.theme["danger"], fg2=self.theme["fg2"])
            self.page.update()

    async def compress_select_files(self, e=None):
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
            self.S["compress_files"] = [f.path for f in files if f.path]
            log(self.S, f"📄 {self.t('batch_selected')} "
                        f"{len(self.S['compress_files'])}",
                color=self.theme["fg2"], fg2=self.theme["fg2"])
            update_compress_progress(
                self.S, self.page, 0, len(self.S["compress_files"]),
                f"{self.t('batch_ready')}: "
                f"{len(self.S['compress_files'])} "
                f"{self.t('batch_files_count')}",
                fg2=self.theme["fg2"])
        except Exception as ex:
            log(self.S, f"❌ {self.t('err')}: {ex}",
                color=self.theme["danger"], fg2=self.theme["fg2"])
            self.page.update()

    async def compress_batch_run(self, e=None):
        S = self.S
        th = self.theme
        files = S["compress_files"]
        if not files:
            log(S, self.t("batch_no_files"), color=th["warn"], fg2=th["fg2"])
            self.page.update()
            return
        total = len(files)
        base_dir = os.path.dirname(files[0])
        out_dir = os.path.join(base_dir, "_compressed")
        os.makedirs(out_dir, exist_ok=True)
        log(S, "", fg2=th["fg2"])
        log(S, "━━━━━━━━━━━━━━━━━━━━━━", color=th["fg3"], fg2=th["fg2"])
        log(S, f"{self.t('compress_batch_started')} {total}",
            color=th["fg"], fg2=th["fg2"])
        log(S, f"   {self.t('compress_out')} {out_dir}",
            color=th["fg2"], fg2=th["fg2"])
        self.page.update()

        count = 0
        for i, fp in enumerate(files, 1):
            try:
                img = await asyncio.to_thread(safe_open_rgb, fp)
                result = await asyncio.to_thread(lab_roundtrip, img)
                base = os.path.splitext(os.path.basename(fp))[0]
                out_path = os.path.join(out_dir, f"{base}.png")
                bd = S.get("pbr_bit_depth", 16)
                await asyncio.to_thread(
                    save_16bit_or_8bit, result, out_path, bd)
                img.close()
                count += 1
                log(S, f"  [{i}/{total}] ✓ {os.path.basename(fp)}",
                    color=th["success"], fg2=th["fg2"])
                update_compress_progress(S, self.page, i, total,
                                          fg2=th["fg2"])
                if i % 5 == 0:
                    gc.collect()
                await asyncio.sleep(0.01)
            except Exception as ex:
                log(S, f"  ✗ {os.path.basename(fp)}: {ex}",
                    color=th["danger"], fg2=th["fg2"])
                update_compress_progress(S, self.page, i, total,
                                          fg2=th["fg2"])
        log(S, f"✅ {self.t('batch_processed')} {count} / {total}",
            color=th["success"], fg2=th["fg2"])
        log(S, f"📁 {out_dir}", color=th["fg2"], fg2=th["fg2"])
        update_compress_progress(S, self.page, total, total,
                                  f"{self.t('batch_done')}: {count} / {total}",
                                  fg2=th["fg2"])
        S["compress_files"] = []
        self.page.update()

    # ─── SIMPLE MODE действия ───

    async def compress_simple_process(self, e=None):
        th = self.theme
        S = self.S
        try:
            files = await self.picker.pick_files(
                dialog_title=self.t("dialog_pick_title"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                initial_directory=init_dir(S),
            )
            if not files or not files[0].path:
                return
            fp = files[0].path
            remember_folder(S, fp)
            S["compress_progress_text"].value = self.t("progress_compress")
            S["compress_progress_text"].visible = True
            S["compress_progress_bar"].value = None
            S["compress_progress_bar"].visible = True
            self.page.update()
            await asyncio.sleep(0.05)
            img = await asyncio.to_thread(safe_open_rgb, fp)
            result = await asyncio.to_thread(lab_roundtrip, img)
            base = os.path.splitext(os.path.basename(fp))[0]
            folder = os.path.dirname(fp)
            out_dir = os.path.join(folder, "_compressed")
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{base}.png")
            bd = S.get("pbr_bit_depth", 16)
            await asyncio.to_thread(
                save_16bit_or_8bit, result, out_path, bd)
            img.close()
            log(S, f"🗜 {os.path.basename(fp)}",
                color=th["success"], fg2=th["fg2"])
            osz = os.path.getsize(fp)
            nsz = os.path.getsize(out_path)
            saved = osz - nsz
            pct = (saved / osz) * 100 if osz > 0 else 0
            if saved > 0:
                log(S, f"   📉 {fmt_size(osz)} → {fmt_size(nsz)}  "
                       f"(−{fmt_size(saved)}, −{pct:.1f}%)",
                    color=th["success"], fg2=th["fg2"])
            elif saved < 0:
                log(S, f"   📈 {fmt_size(osz)} → {fmt_size(nsz)}  "
                       f"(+{fmt_size(-saved)}, +{abs(pct):.1f}%)",
                    color=th["warn"], fg2=th["fg2"])
            log(S, f"📁 {out_dir}", color=th["fg2"], fg2=th["fg2"])
            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            self.page.update()
        except Exception as ex:
            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            log(S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def compress_simple_batch(self, e=None):
        th = self.theme
        S = self.S
        try:
            folder = await self.picker.get_directory_path(
                dialog_title=self.t("batch_select_folder"))
            if not folder:
                return
            remember_folder(S, folder)
            exts = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')
            files = [os.path.join(folder, f) for f in os.listdir(folder)
                     if f.lower().endswith(exts)]
            if not files:
                log(S, self.t("batch_no_files"), color=th["warn"],
                    fg2=th["fg2"])
                self.page.update()
                return
            total = len(files)
            out_dir = os.path.join(folder, "_compressed")
            os.makedirs(out_dir, exist_ok=True)
            log(S, "", fg2=th["fg2"])
            log(S, "━━━━━━━━━━━━━━━━━━━━━━", color=th["fg3"], fg2=th["fg2"])
            log(S, f"{self.t('compress_batch_started')} {total}",
                color=th["fg"], fg2=th["fg2"])
            log(S, f"   {self.t('compress_out')} {out_dir}",
                color=th["fg2"], fg2=th["fg2"])
            S["compress_progress_bar"].value = 0
            S["compress_progress_bar"].visible = True
            S["compress_progress_text"].visible = True
            self.page.update()
            count = 0
            for i, fp in enumerate(files, 1):
                try:
                    img = await asyncio.to_thread(safe_open_rgb, fp)
                    result = await asyncio.to_thread(lab_roundtrip, img)
                    base = os.path.splitext(os.path.basename(fp))[0]
                    out_path = os.path.join(out_dir, f"{base}.png")
                    bd = S.get("pbr_bit_depth", 16)
                    await asyncio.to_thread(
                        save_16bit_or_8bit, result, out_path, bd)
                    img.close()
                    count += 1
                    log(S, f"  [{i}/{total}] ✓ {os.path.basename(fp)}",
                        color=th["success"], fg2=th["fg2"])
                    S["compress_progress_bar"].value = i / total
                    S["compress_progress_text"].value = (
                        f"{i} / {total}  ({int(i / total * 100)}%)"
                    )
                    self.page.update()
                    if i % 5 == 0:
                        gc.collect()
                    await asyncio.sleep(0.01)
                except Exception as ex:
                    log(S, f"  ✗ {os.path.basename(fp)}: {ex}",
                        color=th["danger"], fg2=th["fg2"])
            log(S, f"✅ {self.t('batch_processed')} {count} / {total}",
                color=th["success"], fg2=th["fg2"])
            log(S, f"📁 {out_dir}", color=th["fg2"], fg2=th["fg2"])
            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            self.page.update()
        except Exception as ex:
            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            log(S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()