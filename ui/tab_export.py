"""
ui/tab_export.py — вкладка Engine Export (упаковка PBR под движки).
"""

import os
import asyncio
import numpy as np
from PIL import Image
import flet as ft

from engine_export import (
    pack_for_engine, save_engine_map, load_pbr_folder, engine_folder_suffix,
)
from core.io import pil_to_b64
from core.state import remember_folder, init_dir
from ui.theme import make_btn, section_title, divider
from ui.helpers import log, show_pbr_progress, hide_pbr_progress

FONT = "Segoe UI"
FONT_MONO = "Consolas"


class ExportTab:
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

    def build(self) -> ft.Container:
        th = self.theme
        S = self.S

        self.preview_image = ft.Image(src="", visible=False,
                                        fit=ft.BoxFit.CONTAIN)
        self.preview_hint = ft.Text(self.t("export_hint"),
                                     color=th["fg3"], size=14,
                                     font_family=FONT)

        preview_box = ft.Container(
            content=ft.InteractiveViewer(
                content=ft.Stack([
                    ft.Container(content=self.preview_hint,
                                  alignment=ft.Alignment.CENTER, expand=True),
                    ft.Container(content=self.preview_image,
                                  alignment=ft.Alignment.CENTER, expand=True),
                ], expand=True),
                min_scale=0.5, max_scale=8.0, expand=True,
            ),
            bgcolor=th["card"], border_radius=12, padding=10, expand=True,
        )
        self._refresh_preview()

        toolbar = ft.Row([
            make_btn(self.t("export_load_pbr"), self.export_load_from_pbr,
                     th["accent"], icon="palette",
                     size=13, vertical=11, horizontal=16),
            make_btn(self.t("export_load_folder"), self.export_load_from_folder,
                     th["accent"], icon="folder-open",
                     size=13, vertical=11, horizontal=16),
            ft.Container(expand=True),
            make_btn(self.t("export_pack"), self.export_pack, th["success"],
                     icon="box",
                     size=13, vertical=11, horizontal=16),
            make_btn(self.t("export_save"), self.export_save, th["save"],
                     icon="save",
                     disabled=(S.get("export_packed") is None),
                     size=13, vertical=11, horizontal=16),
        ], spacing=6)

        source_label = ft.Text(
            f"Источник: {S.get('export_source_label') or '—'}",
            color=th["fg3"], size=11, font_family=FONT_MONO)

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        toolbar,
                        ft.Container(height=4),
                        source_label,
                        ft.Container(height=4),
                        S["pbr_progress_bar"],
                        S["pbr_progress_text"],
                        ft.Container(height=6),
                        self._build_channel_row(),
                        ft.Container(height=6),
                        ft.Container(content=preview_box, expand=True),
                    ], spacing=0, expand=True),
                    expand=True,
                ),
                self._build_right_panel(),
            ], spacing=12, expand=True),
            expand=True, visible=True,
        )

    def _build_channel_row(self) -> ft.Row:
        th = self.theme
        active = self.S.get("export_preview_channel", "rgb")

        def _btn(key, label):
            is_active = (active == key)
            return ft.Container(
                content=ft.Text(label,
                                 color="#ffffff" if is_active else th["fg2"],
                                 size=12, font_family=FONT,
                                 weight=ft.FontWeight.W_600),
                bgcolor=th["accent"] if is_active else th["card"],
                border_radius=8,
                padding=ft.Padding.symmetric(vertical=6, horizontal=12),
                ink=not is_active,
                on_click=lambda e, k=key: self._set_channel(k),
            )

        return ft.Row([
            _btn("r", "R"), _btn("g", "G"), _btn("b", "B"), _btn("a", "A"),
            _btn("rgb", "RGB"), _btn("rgba", "RGBA"),
        ], spacing=4)

    def _set_channel(self, ch):
        self.S["export_preview_channel"] = ch
        self._refresh_preview()
        self.on_rebuild()

    def _build_right_panel(self) -> ft.Container:
        th = self.theme
        S = self.S
        engine = S.get("export_engine", "unity_hdrp")

        def _on_engine_change(e):
            S["export_engine"] = e.control.value
            S["export_packed"] = None
            self.on_persist()
            self.on_rebuild()

        def _on_normal_change(e):
            S["export_normal_format"] = e.control.value
            S["export_packed"] = None
            self.on_persist()
            self.on_rebuild()

        def _on_detail_change(e):
            S["export_detail_mode"] = e.control.value
            S["export_packed"] = None
            self.on_persist()
            self.on_rebuild()

        layout = {
            "unity_hdrp": "R = Metallic\nG = AO\nB = Detail Mask\nA = Smoothness (1-Rough)",
            "unity_urp":  "R = Metallic\nG = AO\nB = 0\nA = Smoothness (1-Rough)",
            "unreal":     "R = AO\nG = Roughness\nB = Metallic\nA = 1.0",
            "godot":      "R = AO\nG = Roughness\nB = Metallic\nA = 1.0",
        }.get(engine, "")

        detail_block = ft.Container(
            content=ft.Column([
                section_title("Detail Mask (HDRP)", th["fg3"]),
                ft.Container(height=4),
                ft.RadioGroup(
                    content=ft.Column([
                        ft.Radio(value="white",
                                 label=self.t("export_detail_white")),
                        ft.Radio(value="edge",
                                 label=self.t("export_detail_edge")),
                        ft.Radio(value="custom",
                                 label=self.t("export_detail_custom")),
                    ], spacing=2),
                    value=S.get("export_detail_mode", "edge"),
                    on_change=_on_detail_change,
                ),
                ft.Container(height=4),
                make_btn(self.t("export_load_detail"),
                         self.export_load_custom_detail, th["accent"],
                         icon="folder-open",
                         size=11, vertical=9, horizontal=12),
            ], spacing=2),
            visible=(engine == "unity_hdrp"),
        )

        return ft.Container(
            content=ft.Column([
                section_title(self.t("export_target"), th["fg3"]),
                ft.Container(height=6),
                ft.RadioGroup(
                    content=ft.Column([
                        ft.Radio(value="unity_hdrp",
                                 label=self.t("export_engine_hdrp")),
                        ft.Radio(value="unity_urp",
                                 label=self.t("export_engine_urp")),
                        ft.Radio(value="unreal",
                                 label=self.t("export_engine_unreal")),
                        ft.Radio(value="godot",
                                 label=self.t("export_engine_godot")),
                    ], spacing=2),
                    value=engine, on_change=_on_engine_change,
                ),
                ft.Container(height=14),
                divider(th["fg3"]),
                ft.Container(height=10),
                section_title(self.t("export_normal"), th["fg3"]),
                ft.Container(height=6),
                ft.RadioGroup(
                    content=ft.Column([
                        ft.Radio(value="opengl",
                                 label=self.t("export_normal_gl")),
                        ft.Radio(value="directx",
                                 label=self.t("export_normal_dx")),
                    ], spacing=2),
                    value=S.get("export_normal_format", "opengl"),
                    on_change=_on_normal_change,
                ),
                ft.Container(height=14),
                divider(th["fg3"]),
                ft.Container(height=10),
                detail_block,
                ft.Container(height=14),
                divider(th["fg3"]),
                ft.Container(height=10),
                section_title(self.t("export_layout"), th["fg3"]),
                ft.Container(height=6),
                ft.Container(
                    content=ft.Text(layout, color=th["fg2"], size=11,
                                     font_family=FONT_MONO, selectable=True),
                    bgcolor=th["input"], border_radius=8, padding=10,
                ),
            ], spacing=4, scroll=ft.ScrollMode.AUTO),
            bgcolor=th["panel"], border_radius=12,
            padding=16, width=320,
        )

    # ─── Превью ───

    def _refresh_preview(self):
        arr = self.S.get("export_packed")
        if arr is None:
            if self.preview_image is not None:
                self.preview_image.visible = False
            if self.preview_hint is not None:
                self.preview_hint.visible = True
            return
        pil = self._build_preview_pil(arr)
        if pil is None:
            return
        self.preview_image.src = f"data:image/png;base64,{pil_to_b64(pil)}"
        self.preview_image.visible = True
        self.preview_hint.visible = False

    def _build_preview_pil(self, arr):
        ch = self.S.get("export_preview_channel", "rgb")
        if arr.ndim == 2:
            a = np.clip(arr, 0, 1)
            return Image.fromarray((a * 255).astype(np.uint8), mode="L")
        if ch in ("r", "g", "b", "a"):
            idx = {"r": 0, "g": 1, "b": 2, "a": 3}[ch]
            if idx >= arr.shape[2]:
                return None
            a = np.clip(arr[..., idx], 0, 1)
            return Image.fromarray((a * 255).astype(np.uint8), mode="L")
        a = np.clip(arr[..., :3], 0, 1)
        return Image.fromarray((a * 255).astype(np.uint8), mode="RGB")

    # ─── Действия ───

    async def export_load_from_pbr(self, e=None):
        th = self.theme
        S = self.S
        if S.get("pbr_result") is None:
            log(S, self.t("export_log_no_pbr"), color=th["warn"], fg2=th["fg2"])
            self.page.update()
            return
        src = {k: v for k, v in S["pbr_result"].items() if v is not None}
        if "albedo" not in src and S.get("pbr_source") is not None:
            arr = np.array(S["pbr_source"].convert("RGB")).astype(np.float32) / 255.0
            src["albedo"] = arr
        S["export_source"] = src
        base = "PBR"
        if S.get("pbr_source_path"):
            base = os.path.splitext(os.path.basename(S["pbr_source_path"]))[0]
        S["export_source_label"] = f"PBR / {base}"
        log(S, f"{self.t('export_log_source_pbr')} ({len(src)} карт)",
            color=th["success"], fg2=th["fg2"])
        self.page.update()
        self.on_rebuild()

    async def export_load_from_folder(self, e=None):
        th = self.theme
        S = self.S
        folder = await self.picker.get_directory_path(
            dialog_title="Выбери папку с PBR-картами",
            initial_directory=init_dir(S))
        if not folder:
            return
        remember_folder(S, folder)
        src = load_pbr_folder(folder)
        if not src or "normal" not in src:
            log(S, f"{self.t('export_log_no_normal')}: {folder}",
                color=th["warn"], fg2=th["fg2"])
            self.page.update()
            return
        S["export_source"] = src
        S["export_source_label"] = folder
        log(S, f"{self.t('export_log_source_folder')} "
               f"({len(src)} карт из {os.path.basename(folder)})",
            color=th["success"], fg2=th["fg2"])
        self.page.update()
        self.on_rebuild()

    async def export_load_custom_detail(self, e=None):
        th = self.theme
        S = self.S
        files = await self.picker.pick_files(
            dialog_title="Выбери Detail Mask (grayscale)",
            allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
            initial_directory=init_dir(S))
        if not files or not files[0].path:
            return
        fp = files[0].path
        remember_folder(S, fp)
        try:
            img = Image.open(fp).convert("L")
            arr = np.array(img).astype(np.float32) / 255.0
            S["export_custom_detail"] = arr
            S["export_detail_mode"] = "custom"
            log(S, f"{self.t('export_log_detail_loaded')} "
                   f"{os.path.basename(fp)}",
                color=th["success"], fg2=th["fg2"])
        except Exception as ex:
            log(S, f"❌ Detail Mask: {ex}",
                color=th["danger"], fg2=th["fg2"])
        self.page.update()
        self.on_rebuild()

    async def export_pack(self, e=None):
        S = self.S
        th = self.theme
        if S.get("export_source") is None:
            log(S, self.t("export_log_no_source"), color=th["warn"], fg2=th["fg2"])
            self.page.update()
            return
        try:
            await show_pbr_progress(S, self.page,
                                     self.t("export_progress_pack"))
            await asyncio.sleep(0.05)
            engine = S.get("export_engine", "unity_hdrp")
            nf = S.get("export_normal_format", "opengl")
            detail_mask = None
            if engine == "unity_hdrp":
                if S.get("export_detail_mode") == "custom":
                    detail_mask = S.get("export_custom_detail")
            result = await asyncio.to_thread(
                pack_for_engine, S["export_source"], engine, nf, detail_mask)
            if not result or "packed" not in result:
                log(S, "   ⚠ Упаковка не удалась",
                    color=th["warn"], fg2=th["fg2"])
                await hide_pbr_progress(S, self.page)
                return
            S["export_packed"] = result["packed"]
            S["export_normal_out"] = result.get("normal")
            log(S, f"{self.t('export_log_packed')}: {engine} / {nf}",
                color=th["success"], fg2=th["fg2"])
            self.page.update()
            await asyncio.sleep(0.05)
            await hide_pbr_progress(S, self.page)
            self.on_rebuild()
        except Exception as ex:
            await hide_pbr_progress(S, self.page)
            log(S, f"❌ Export pack: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def export_save(self, e=None):
        S = self.S
        th = self.theme
        if S.get("export_packed") is None:
            log(S, self.t("export_log_no_packed"),
                color=th["warn"], fg2=th["fg2"])
            self.page.update()
            return
        try:
            src_label = S.get("export_source_label") or ""
            if src_label.startswith("PBR / "):
                base_name = src_label.replace("PBR / ", "")
                folder = os.path.dirname(S.get("pbr_source_path") or os.getcwd())
            elif os.path.isdir(src_label):
                folder = os.path.dirname(src_label)
                base_name = os.path.basename(src_label.rstrip("\\/")) or "pbr"
            else:
                folder = os.getcwd()
                base_name = "pbr"
            engine = S.get("export_engine", "unity_hdrp")
            nf = S.get("export_normal_format", "opengl")
            suffix = engine_folder_suffix(engine, nf)
            out_dir = os.path.join(folder, f"{base_name}{suffix}")
            os.makedirs(out_dir, exist_ok=True)
            bd = S.get("export_bit_depth", 8)
            packed_name = {
                "unity_hdrp": f"{base_name}_MaskMap.png",
                "unity_urp":  f"{base_name}_MetallicSmoothness.png",
                "unreal":     f"{base_name}_ORM.png",
                "godot":      f"{base_name}_ORM.png",
            }.get(engine, f"{base_name}_packed.png")
            normal_name = f"{base_name}_normal.png"

            await show_pbr_progress(S, self.page,
                                     self.t("export_progress_save"))
            await asyncio.sleep(0.05)
            await asyncio.to_thread(
                save_engine_map, S["export_packed"],
                os.path.join(out_dir, packed_name), bd)
            if S.get("export_normal_out") is not None:
                await asyncio.to_thread(
                    save_engine_map, S["export_normal_out"],
                    os.path.join(out_dir, normal_name), bd)
            log(S, f"{self.t('export_log_saved')} {out_dir}",
                color=th["success"], fg2=th["fg2"])
            self.page.update()
            await asyncio.sleep(0.1)
            await hide_pbr_progress(S, self.page)
        except Exception as ex:
            await hide_pbr_progress(S, self.page)
            log(S, f"❌ Export save: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()