"""
ui/tab_pbr.py — вкладка PBR целиком.
"""

import os
import asyncio
import gc
import subprocess
import tempfile
import numpy as np
from PIL import Image
import flet as ft

from config import PBR_PRESETS, TEXTURE_PROFILES, PROFILE_CATEGORIES
from core.image_ops import (
    generate_pbr_all, make_metallic_mask, pick_color_from_pixel,
    mask_white_pct, resize_to_match,
)
from core.io import save_16bit_or_8bit, pil_to_b64, fmt_size, safe_open_rgb, safe_open_gray
from core.state import remember_folder, init_dir
from pbr_generator import save_pbr_map, to_preview_pil
from ui.icons import img_icon
from ui.theme import make_btn, make_chip, section_title, divider
from ui.helpers import (
    log, show_pbr_progress, hide_pbr_progress,
)

FONT = "Segoe UI"
FONT_MONO = "Consolas"

MAP_ICONS = {
    "albedo":    "palette",
    "height":    "mountain-snow",
    "normal":    "grid-3x3",
    "ao":        "circle-dot",
    "roughness": "waves",
    "metallic":  "aperture",
    "edge":      "target",
    "orm":       "waypoints",
}

MAP_KEYS = [
    ("albedo",    "Albedo"),
    ("height",    "Height"),
    ("normal",    "Normal"),
    ("ao",        "AO"),
    ("roughness", "Rough"),
    ("metallic",  "Metal"),
    ("edge",      "Edge"),
    ("orm",       "ORM"),
]


class PbrTab:
    """Вкладка PBR."""

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
        self.batch_label = None
        self.batch_nav_panel = None
        self.map_buttons = {}
        self.pbr_buttons = {}
        self.pbr_params_ref = None

    def build(self) -> ft.Container:
        S = self.S
        th = self.theme
        is_simple = S["ui_mode"] == "simple"

        self.preview_image = ft.Image(src="", visible=False,
                                       fit=ft.BoxFit.CONTAIN)
        # Восстановление превью после rebuild
        if S.get("pbr_result") and S.get("pbr_current_map") in S["pbr_result"]:
            key = S["pbr_current_map"]
            self.preview_image.src = (
                f"data:image/png;base64,{pil_to_b64(S['pbr_result'][key])}"
            )
            self.preview_image.visible = True
        elif S.get("pbr_source") is not None:
            self.preview_image.src = (
                f"data:image/png;base64,{pil_to_b64(S['pbr_source'])}"
            )
            self.preview_image.visible = True
        S["pbr_preview"] = self.preview_image

        self.preview_hint = ft.Text(self.t("pbr_preview_hint"),
                                     color=th["fg3"], size=14,
                                     font_family=FONT,
                                     visible=(S.get("pbr_source") is None
                                              and S.get("pbr_result") is None))
        S["pbr_preview_hint"] = self.preview_hint

        self.batch_label = ft.Text("", color=th["fg"], size=12,
                                    font_family=FONT,
                                    weight=ft.FontWeight.W_600)
        S["pbr_batch_label"] = self.batch_label

        batch_nav_inner = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=img_icon("chevron-left", th["fg"], 14),
                    bgcolor=th["input"], border_radius=6,
                    padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                    ink=True, on_click=lambda e: self.pbr_batch_prev(),
                ),
                self.batch_label,
                ft.Container(
                    content=img_icon("chevron-right", th["fg"], 14),
                    bgcolor=th["input"], border_radius=6,
                    padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                    ink=True, on_click=lambda e: self.pbr_batch_next(),
                ),
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER,
               tight=True),
            bgcolor=th["panel"], border_radius=8, padding=6,
        )

        self.batch_nav_panel = ft.Container(
            content=ft.Row([batch_nav_inner],
                            alignment=ft.MainAxisAlignment.END),
            visible=len(S["pbr_batch_results"]) > 0,
        )
        S["pbr_batch_nav_panel"] = self.batch_nav_panel

        preview_box = ft.Container(
            content=ft.InteractiveViewer(
                content=ft.Stack([
                    ft.Container(content=self.preview_hint,
                                  alignment=ft.Alignment.CENTER, expand=True),
                    ft.Container(content=self.preview_image,
                                  alignment=ft.Alignment.CENTER, expand=True),
                    ft.Container(content=self.batch_nav_panel,
                                  alignment=ft.Alignment.BOTTOM_RIGHT,
                                  padding=12),
                ], expand=True),
                min_scale=0.5, max_scale=8.0, expand=True,
            ),
            bgcolor=th["card"], border_radius=12, padding=10, expand=True,
        )

        # Кнопки карт
        map_row = ft.Row([], spacing=4)
        for key, label in MAP_KEYS:
            is_active = key == S["pbr_current_map"]
            content_color = "#ffffff" if is_active else th["fg2"]
            b = ft.Container(
                content=ft.Row([
                    img_icon(MAP_ICONS[key], content_color, 14),
                    ft.Text(label, color=content_color,
                            size=12, font_family=FONT,
                            weight=ft.FontWeight.W_600),
                ], spacing=6, alignment=ft.MainAxisAlignment.CENTER,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=th["accent"] if is_active else th["card"],
                border_radius=8,
                padding=ft.Padding.symmetric(vertical=8, horizontal=12),
                expand=True, ink=not is_active,
                on_click=lambda e, k=key: self._show_map(k),
            )
            self.map_buttons[key] = b
            map_row.controls.append(b)

        toolbar = (self._build_toolbar_simple() if is_simple
                    else self._build_toolbar_advanced())

        if is_simple:
            params_panel = self._build_simple_params_panel()
        else:
            params_panel = self._build_params_panel()
            self.pbr_params_ref = params_panel
            self.S["pbr_params_ref"] = params_panel

        return ft.Container(
            content=ft.Column([
                toolbar,
                ft.Container(height=4),
                self.S["pbr_progress_bar"],
                self.S["pbr_progress_text"],
                ft.Container(height=6),
                map_row,
                ft.Container(height=6),
                ft.Row([
                    ft.Container(content=preview_box, expand=True),
                    params_panel,
                ], spacing=12, expand=True),
                ft.Container(height=8),
                ft.Container(height=0),
            ], spacing=0, expand=True),
            expand=True, visible=True,
        )

    # ═══════════════════════════════════════════════════════════
    #  ТУЛБАРЫ
    # ═══════════════════════════════════════════════════════════

    def _build_toolbar_simple(self) -> ft.Row:
        th = self.theme
        gen_btn = make_btn(self.t("pbr_gen"), self.pbr_do_simple_generate,
                            th["success"], icon="wand-sparkles",
                            size=14, vertical=13, horizontal=16)
        viewer_btn = make_btn(self.t("pbr_viewer"), self.pbr_open_viewer,
                               th["seamless"], icon="rotate-3d",
                               disabled=(self.S["pbr_result"] is None),
                               size=13, vertical=11, horizontal=16)
        save_btn = make_btn(self.t("pbr_save"), self.pbr_do_save,
                             th["save"], icon="save",
                             disabled=(self.S["pbr_result"] is None),
                             size=13, vertical=11, horizontal=16)
        self.pbr_buttons = {"viewer": viewer_btn, "save": save_btn,
                             "gen": gen_btn}
        self.S["pbr_buttons"] = self.pbr_buttons
        return ft.Row([
            gen_btn,
            ft.Container(expand=True),
            viewer_btn,
            save_btn,
        ], spacing=6)

    def _build_toolbar_advanced(self) -> ft.Row:
        th = self.theme
        load_btn = make_btn(self.t("pbr_load"), self.pbr_do_load,
                             th["accent"], icon="folder-open",
                             size=13, vertical=11, horizontal=16)
        gen_btn = make_btn(self.t("pbr_gen"), self.pbr_do_generate,
                            th["success"], icon="wand-sparkles",
                            disabled=(self.S["pbr_source"] is None),
                            size=13, vertical=11, horizontal=16)
        batch_btn = make_btn(self.t("pbr_batch"), self.pbr_do_batch,
                              th["compress"], icon="layers",
                              size=13, vertical=11, horizontal=16)
        viewer_btn = make_btn(self.t("pbr_viewer"), self.pbr_open_viewer,
                               th["seamless"], icon="rotate-3d",
                               disabled=(self.S["pbr_result"] is None),
                               size=13, vertical=11, horizontal=16)
        save_btn = make_btn(self.t("pbr_save"), self.pbr_do_save,
                             th["save"], icon="save",
                             disabled=(self.S["pbr_result"] is None),
                             size=13, vertical=11, horizontal=16)
        self.pbr_buttons = {
            "load": load_btn, "gen": gen_btn, "batch": batch_btn,
            "viewer": viewer_btn, "save": save_btn,
        }
        self.S["pbr_buttons"] = self.pbr_buttons
        return ft.Row([
            load_btn, gen_btn, batch_btn,
            ft.Container(expand=True),
            viewer_btn, save_btn,
        ], spacing=6)

    # ═══════════════════════════════════════════════════════════
    #  ПРАВАЯ ПАНЕЛЬ
    # ═══════════════════════════════════════════════════════════

    def _build_simple_params_panel(self) -> ft.Container:
        th = self.theme
        bit_radio = self._build_bit_radio()
        return ft.Container(
            content=ft.Column([
                section_title(self.t("pbr_params"), th["fg3"]),
                ft.Container(height=6),
                ft.Text(self.t("pbr_bit_depth"), color=th["fg2"],
                        size=12, font_family=FONT),
                bit_radio,
            ], spacing=6),
            bgcolor=th["panel"], border_radius=12,
            padding=14, width=200,
        )

    def _build_params_panel(self) -> ft.Container:
        th = self.theme
        key = self.S.get("pbr_current_map", "albedo")
        header = section_title(self.t("pbr_params"), th["fg3"])
        bit_block = self._build_bit_block(key)

        if key == "albedo":
            content = [header, self._build_preset_selector(), bit_block]
        elif key == "height":
            content = [header,
                       self._slider(self.t("pbr_sl_height_blur"),
                                     "height_blur", 2.0, 0.0, 10.0, 0.5),
                       bit_block]
        elif key == "normal":
            content = [header,
                       self._slider(self.t("pbr_sl_strength"),
                                     "strength", 1.5, 0.1, 5.0, 0.1),
                       self._slider(self.t("pbr_sl_smooth"),
                                     "smooth", 1.5, 0.0, 5.0, 0.1),
                       self._slider(self.t("pbr_sl_threshold"),
                                     "threshold", 0.05, 0.0, 0.20, 0.01),
                       self._slider(self.t("pbr_sl_high_pass"),
                                     "high_pass", 40.0, 0.0, 100.0, 1.0),
                       bit_block]
        elif key == "ao":
            content = [header,
                       self._slider(self.t("pbr_sl_ao_radius"),
                                     "ao_radius", 8.0, 2.0, 30.0, 1.0),
                       self._slider(self.t("pbr_sl_ao_intensity"),
                                     "ao_intensity", 1.5, 0.1, 3.0, 0.1),
                       bit_block]
        elif key == "roughness":
            content = [header,
                       ft.Text(self.t("pbr_roughness"), color=th["fg2"],
                               size=12, font_family=FONT),
                       self._build_rough_radio(),
                       self._build_rough_custom_block(),
                       ft.Container(
                           content=ft.Column([
                               self._slider(self.t("pbr_sl_rough_base"),
                                             "rough_base", 0.7, 0.0, 1.0, 0.05),
                               self._slider(self.t("pbr_sl_rough_var"),
                                             "rough_var", 0.3, 0.0, 1.0, 0.05),
                               self._slider(self.t("pbr_sl_rough_detail"),
                                             "rough_detail", 1.0, 0.0, 1.0, 0.05),
                           ], spacing=6),
                           visible=(self.S.get("pbr_roughness") != "custom"),
                       ),
                       bit_block]
        elif key == "metallic":
            content = [header,
                       ft.Text(self.t("pbr_metallic"), color=th["fg2"],
                               size=12, font_family=FONT),
                       self._build_metal_radio(),
                       self._build_metal_custom_block(),
                       self._build_metal_auto_block(),
                       bit_block]
        elif key == "edge":
            content = [header,
                       ft.Text(self.t("pbr_edge_info"), color=th["fg2"],
                               size=11, font_family=FONT, selectable=True),
                       bit_block]
        elif key == "orm":
            content = [header,
                       ft.Text(self.t("pbr_orm_info"), color=th["fg2"],
                               size=11, font_family=FONT, selectable=True),
                       bit_block]
        else:
            content = [header, bit_block]

        return ft.Container(
            content=ft.Column(content, spacing=6,
                              scroll=ft.ScrollMode.AUTO),
            bgcolor=th["panel"], border_radius=12,
            padding=14, width=250,
        )

    def _build_preset_selector(self) -> ft.Column:
        th = self.theme
        icon_map = {
            "metal": "flame", "nature": "leaf", "mineral": "mountain",
            "synth": "flask-conical", "fabric": "shirt",
            "special": "droplet", "fauna": "paw-print",
        }
        cat_rows = []
        cat_row = []
        for key, cat in PROFILE_CATEGORIES.items():
            is_active = self.S["profile_category"] == key
            content_color = "#ffffff" if is_active else th["fg2"]
            chip = ft.Container(
                content=img_icon(icon_map.get(key, "layers"),
                                  content_color, 14),
                bgcolor=th["accent"] if is_active else th["card"],
                border_radius=6,
                padding=ft.Padding.symmetric(vertical=6, horizontal=6),
                expand=True, ink=not is_active,
                tooltip=cat[self.S["lang"]],
                on_click=lambda e, k=key: self._set_pbr_category(k),
            )
            cat_row.append(chip)
            if len(cat_row) == 4:
                cat_rows.append(ft.Row(cat_row, spacing=3))
                cat_row = []
        if cat_row:
            while len(cat_row) < 4:
                cat_row.append(ft.Container(expand=True))
            cat_rows.append(ft.Row(cat_row, spacing=3))

        items = PROFILE_CATEGORIES[self.S["profile_category"]]["items"]
        preset_rows = []
        preset_row = []
        for key in items:
            is_active = self.S["profile"] == key
            label = TEXTURE_PROFILES[key][self.S["lang"]]
            chip = ft.Container(
                content=ft.Text(label,
                                 color="#ffffff" if is_active else th["fg2"],
                                 size=10, font_family=FONT,
                                 weight=ft.FontWeight.W_600 if is_active
                                 else ft.FontWeight.W_500,
                                 text_align=ft.TextAlign.CENTER),
                bgcolor=th["accent"] if is_active else th["card"],
                border_radius=6,
                padding=ft.Padding.symmetric(vertical=6, horizontal=2),
                expand=True, ink=not is_active,
                on_click=lambda e, k=key: self._set_pbr_profile(k),
            )
            preset_row.append(chip)
            if len(preset_row) == 2:
                preset_rows.append(ft.Row(preset_row, spacing=3))
                preset_row = []
        if preset_row:
            while len(preset_row) < 2:
                preset_row.append(ft.Container(expand=True))
            preset_rows.append(ft.Row(preset_row, spacing=3))

        return ft.Column([
            ft.Text(self.t("pbr_preset_label"), color=th["fg2"],
                    size=11, font_family=FONT),
            ft.Column(cat_rows, spacing=3),
            ft.Container(height=4),
            ft.Column(preset_rows, spacing=3),
        ], spacing=4)

    def _build_bit_block(self, map_key: str) -> ft.Column:
        th = self.theme
        cur_bd = str(self.S.get("pbr_bit_depth_per_map", {}).get(map_key, 8))

        def _on_change(e):
            self.S.setdefault("pbr_bit_depth_per_map", {})[map_key] = int(
                e.control.value)
            self.on_persist()

        return ft.Column([
            divider(th["fg3"]),
            ft.Text(f"{self.t('pbr_bit_depth')} ({map_key})",
                    color=th["fg2"], size=12, font_family=FONT),
            ft.RadioGroup(
                content=ft.Row([
                    ft.Radio(value="8", label=self.t("pbr_bit_8"),
                             fill_color=th["pbr"]),
                    ft.Radio(value="16", label=self.t("pbr_bit_16"),
                             fill_color=th["pbr"]),
                ]),
                value=cur_bd, on_change=_on_change,
            ),
        ], spacing=6)

    def _build_bit_radio(self) -> ft.RadioGroup:
        th = self.theme
        return ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="8", label=self.t("pbr_bit_8"),
                         fill_color=th["pbr"]),
                ft.Radio(value="16", label=self.t("pbr_bit_16"),
                         fill_color=th["pbr"]),
            ]),
            value=str(self.S["pbr_bit_depth"]),
            on_change=lambda e: self.S.update(
                {"pbr_bit_depth": int(e.control.value)}),
        )

    def _slider(self, label: str, key: str, default: float,
                minv: float, maxv: float, res: float) -> ft.Column:
        th = self.theme
        preset_val = self.S.get("pbr_values", {}).get(key)
        if preset_val is None:
            preset_val = PBR_PRESETS.get(self.S["profile"], {}).get(key, default)
        divisions = max(1, int((maxv - minv) / res))

        def _on_change(e):
            self.S.setdefault("pbr_values", {})[key] = e.control.value
            self.on_persist()

        slider = ft.Slider(
            min=minv, max=maxv, divisions=divisions,
            value=preset_val, label="{value}",
            active_color=th["pbr"], inactive_color=th["input"],
            on_change=_on_change,
        )
        self.S.setdefault("pbr_sliders", {})[key] = slider
        return ft.Column([
            ft.Text(label, color=th["fg2"], size=12, font_family=FONT),
            slider,
        ], spacing=2)

    def _build_metal_radio(self) -> ft.RadioGroup:
        th = self.theme

        def _on_change(e):
            self.S["pbr_metallic"] = e.control.value
            self.on_persist()
            self.on_rebuild()

        return ft.RadioGroup(
            content=ft.Column([
                ft.Row([
                    ft.Radio(value="black", label=self.t("pbr_metal_black"),
                             fill_color=th["pbr"]),
                    ft.Radio(value="white", label=self.t("pbr_metal_white"),
                             fill_color=th["pbr"]),
                ], spacing=8),
                ft.Row([
                    ft.Radio(value="custom", label=self.t("pbr_metal_custom"),
                             fill_color=th["pbr"]),
                    ft.Radio(value="auto", label=self.t("pbr_metal_auto"),
                             fill_color=th["pbr"]),
                ], spacing=8),
            ], spacing=2),
            value=self.S.get("pbr_metallic", "black"),
            on_change=_on_change,
        )

    def _build_rough_radio(self) -> ft.RadioGroup:
        th = self.theme

        def _on_change(e):
            self.S["pbr_roughness"] = e.control.value
            self.on_persist()
            self.on_rebuild()

        return ft.RadioGroup(
            content=ft.Column([
                ft.Row([
                    ft.Radio(value="procedural",
                             label=self.t("pbr_rough_procedural"),
                             fill_color=th["pbr"]),
                ], spacing=8),
                ft.Row([
                    ft.Radio(value="custom",
                             label=self.t("pbr_rough_custom"),
                             fill_color=th["pbr"]),
                ]),
            ], spacing=2),
            value=self.S.get("pbr_roughness", "procedural"),
            on_change=_on_change,
        )

    def _build_metal_custom_block(self) -> ft.Container:
        th = self.theme
        path_label = (os.path.basename(self.S["pbr_metallic_custom_path"])
                      if self.S.get("pbr_metallic_custom_path") else "—")
        return ft.Container(
            content=ft.Column([
                ft.Container(height=4),
                make_btn(self.t("pbr_metal_load"),
                         self.pbr_load_metallic_map, th["accent"],
                         icon="folder-open",
                         size=11, vertical=9, horizontal=12),
                ft.Container(height=4),
                ft.Text(path_label, color=th["fg3"], size=10,
                        font_family=FONT_MONO, selectable=True),
            ], spacing=2),
            visible=(self.S.get("pbr_metallic") == "custom"),
        )

    def _build_rough_custom_block(self) -> ft.Container:
        th = self.theme
        path_label = (os.path.basename(self.S["pbr_roughness_custom_path"])
                      if self.S.get("pbr_roughness_custom_path") else "—")
        return ft.Container(
            content=ft.Column([
                ft.Container(height=4),
                make_btn(self.t("pbr_rough_load"),
                         self.pbr_load_roughness_map, th["accent"],
                         icon="folder-open",
                         size=11, vertical=9, horizontal=12),
                ft.Container(height=4),
                ft.Text(path_label, color=th["fg3"], size=10,
                        font_family=FONT_MONO, selectable=True),
            ], spacing=2),
            visible=(self.S.get("pbr_roughness") == "custom"),
        )

    def _build_metal_auto_block(self) -> ft.Container:
        th = self.theme
        rgb = self.S.get("pbr_metal_target_rgb")
        rgb_text = f"RGB({rgb[0]}, {rgb[1]}, {rgb[2]})" if rgb else "—"
        neg_rgb = self.S.get("pbr_metal_negative_rgb")
        neg_text = (f"RGB({neg_rgb[0]}, {neg_rgb[1]}, {neg_rgb[2]})"
                    if neg_rgb else "—")

        def _clear_negative(e=None):
            self.S["pbr_metal_negative_rgb"] = None
            self.on_persist()
            self.on_rebuild()

        return ft.Container(
            content=ft.Column([
                ft.Container(height=4),
                ft.Text(self.t("pbr_metal_auto_hint"), color=th["fg3"],
                        size=10, font_family=FONT),
                ft.Container(height=6),
                make_btn(self.t("pbr_metal_pick"),
                         lambda e: self.page.run_task(
                             self.pbr_pick_color, None, "positive"),
                         th["accent"], icon="pipette",
                         size=11, vertical=9, horizontal=12),
                ft.Container(height=4),
                ft.Row([
                    ft.Text(self.t("pbr_metal_target_label"), color=th["fg3"],
                            size=10, font_family=FONT),
                    ft.Text(rgb_text, color=th["fg2"], size=11,
                            font_family=FONT_MONO, selectable=True),
                ], spacing=6),
                ft.Container(height=8),
                make_btn(self.t("pbr_metal_negative_pick"),
                         lambda e: self.page.run_task(
                             self.pbr_pick_color, None, "negative"),
                         th["save"], icon="eraser",
                         size=11, vertical=9, horizontal=12),
                ft.Container(height=4),
                ft.Row([
                    ft.Text(self.t("pbr_metal_negative_label"), color=th["fg3"],
                            size=10, font_family=FONT),
                    ft.Text(neg_text, color=th["fg2"], size=11,
                            font_family=FONT_MONO, selectable=True),
                ], spacing=6),
                ft.Container(
                    content=make_btn(self.t("pbr_metal_negative_clear"),
                                     _clear_negative, th["reset"],
                                     icon="x",
                                     size=11, vertical=9, horizontal=12),
                    visible=(neg_rgb is not None),
                ),
                ft.Container(height=8),
                section_title(self.t("pbr_metal_presets_title"), th["fg3"]),
                ft.Container(height=4),
                ft.Row([
                    self._metal_preset_btn("tight",
                                            self.t("pbr_metal_preset_tight"),
                                            0.10, 0.02, 0.05),
                    self._metal_preset_btn("medium",
                                            self.t("pbr_metal_preset_medium"),
                                            0.20, 0.05, 0.10),
                    self._metal_preset_btn("loose",
                                            self.t("pbr_metal_preset_loose"),
                                            0.40, 0.10, 0.15),
                ], spacing=4),
                ft.Container(height=10),
                section_title(self.t("pbr_metal_manual_title"), th["fg3"]),
                ft.Container(height=4),
                ft.Text(self.t("pbr_metal_tolerance"), color=th["fg2"],
                        size=11, font_family=FONT),
                ft.Slider(min=0.05, max=0.60, divisions=22,
                          value=self.S.get("pbr_metal_tolerance", 0.20),
                          label="{value:.2f}",
                          active_color=th["pbr"], inactive_color=th["input"],
                          on_change=lambda e: self.S.update(
                              {"pbr_metal_tolerance": e.control.value})),
                ft.Text(self.t("pbr_metal_softness"), color=th["fg2"],
                        size=11, font_family=FONT),
                ft.Slider(min=0.0, max=0.5, divisions=20,
                          value=self.S.get("pbr_metal_softness", 0.05),
                          label="{value:.2f}",
                          active_color=th["pbr"], inactive_color=th["input"],
                          on_change=lambda e: self.S.update(
                              {"pbr_metal_softness": e.control.value})),
                ft.Text(self.t("pbr_metal_negative_tolerance"),
                        color=th["fg2"], size=11, font_family=FONT),
                ft.Slider(min=0.02, max=0.40, divisions=19,
                          value=self.S.get("pbr_metal_negative_tolerance", 0.10),
                          label="{value:.2f}",
                          active_color=th["save"], inactive_color=th["input"],
                          on_change=lambda e: self.S.update(
                              {"pbr_metal_negative_tolerance":
                               e.control.value})),
                ft.Container(height=8),
                ft.Text(self.t("pbr_metal_auto_footer"), color=th["fg3"],
                        size=10, font_family=FONT),
            ], spacing=2),
            visible=(self.S.get("pbr_metallic") == "auto"),
        )

    def _metal_preset_btn(self, key: str, label: str,
                           tol: float, soft: float, neg_tol: float
                           ) -> ft.Container:
        th = self.theme
        is_active = (abs(self.S.get("pbr_metal_tolerance", 0.20) - tol) < 0.001
                     and abs(self.S.get("pbr_metal_softness", 0.05) - soft) < 0.001)

        def _apply(e):
            self.S["pbr_metal_tolerance"] = tol
            self.S["pbr_metal_softness"] = soft
            self.S["pbr_metal_negative_tolerance"] = neg_tol
            self.on_persist()
            self.on_rebuild()

        return ft.Container(
            content=ft.Text(label,
                             color="#ffffff" if is_active else th["fg2"],
                             size=10, font_family=FONT,
                             weight=ft.FontWeight.W_600,
                             text_align=ft.TextAlign.CENTER),
            bgcolor=th["accent"] if is_active else th["card"],
            border_radius=8,
            padding=ft.Padding.symmetric(vertical=8, horizontal=4),
            expand=True, ink=not is_active, on_click=_apply,
        )

    # ═══════════════════════════════════════════════════════════
    #  ПЕРЕКЛЮЧЕНИЕ КАРТ
    # ═══════════════════════════════════════════════════════════

    def _show_map(self, key: str):
        self.S["pbr_current_map"] = key
        self._update_preview()
        if self.pbr_params_ref is not None:
            new_panel = self._build_params_panel()
            self.pbr_params_ref.content = new_panel.content
            self.pbr_params_ref.width = new_panel.width
            self.page.update()

    def _update_preview(self):
        S = self.S
        th = self.theme
        key = S.get("pbr_current_map", "albedo")
        if S["pbr_batch_selected"] and S["pbr_result"] and key in S["pbr_result"]:
            self.preview_image.src = (
                f"data:image/png;base64,{pil_to_b64(S['pbr_result'][key])}"
            )
            self.preview_image.visible = True
        elif key == "albedo":
            if S["pbr_source"] is not None:
                self.preview_image.src = (
                    f"data:image/png;base64,{pil_to_b64(S['pbr_source'])}"
                )
                self.preview_image.visible = True
            elif S["pbr_result"] and "albedo" in S["pbr_result"]:
                self.preview_image.src = (
                    f"data:image/png;base64,"
                    f"{pil_to_b64(S['pbr_result']['albedo'])}"
                )
                self.preview_image.visible = True
        else:
            if S["pbr_result"] and key in S["pbr_result"]:
                self.preview_image.src = (
                    f"data:image/png;base64,{pil_to_b64(S['pbr_result'][key])}"
                )
                self.preview_image.visible = True
        if self.preview_hint is not None:
            self.preview_hint.visible = False
        for k, b in self.map_buttons.items():
            is_active = (k == key)
            b.bgcolor = th["accent"] if is_active else th["card"]
            b.ink = not is_active
            content_color = "#ffffff" if is_active else th["fg2"]
            b.content.controls[0] = img_icon(
                MAP_ICONS[k], content_color, 14)
            b.content.controls[1].color = content_color
        self.page.update()

    def _set_pbr_category(self, key: str):
        self.S["profile_category"] = key
        items = PROFILE_CATEGORIES[key]["items"]
        if self.S["profile"] not in items:
            self.S["profile"] = items[0]
        self.on_persist()
        self.on_rebuild()

    def _set_pbr_profile(self, key: str):
        self.S["profile"] = key
        self.S["pbr_sliders"] = {}
        self.on_persist()
        self.on_rebuild()

    # ═══════════════════════════════════════════════════════════
    #  BATCH NAV
    # ═══════════════════════════════════════════════════════════

    def pbr_batch_next(self, e=None):
        keys = list(self.S["pbr_batch_results"].keys())
        if not keys:
            return
        self.S["pbr_batch_index"] = (self.S["pbr_batch_index"] + 1) % len(keys)
        self.pbr_load_batch_texture(keys[self.S["pbr_batch_index"]])
        self._update_preview()

    def pbr_batch_prev(self, e=None):
        keys = list(self.S["pbr_batch_results"].keys())
        if not keys:
            return
        self.S["pbr_batch_index"] = (self.S["pbr_batch_index"] - 1) % len(keys)
        self.pbr_load_batch_texture(keys[self.S["pbr_batch_index"]])
        self._update_preview()

    def pbr_load_batch_texture(self, base_name: str):
        if not base_name or base_name == "_none_":
            return
        folder = self.S["pbr_batch_results"].get(base_name)
        if not folder or not os.path.exists(folder):
            return

        result = {}
        for key in ("albedo", "height", "normal", "ao", "roughness",
                    "metallic", "orm", "edge"):
            path = os.path.join(folder, f"{base_name}_{key}.png")
            if os.path.exists(path):
                img = Image.open(path).convert("RGB")
                img.load()
                result[key] = img

        if not result:
            return
        self.S["pbr_result"] = result
        self.S["pbr_batch_selected"] = base_name
        keys = list(self.S["pbr_batch_results"].keys())
        if base_name in keys:
            self.S["pbr_batch_index"] = keys.index(base_name)

        show_key = "albedo" if "albedo" in result else next(iter(result.keys()), None)
        if show_key:
            self.S["pbr_current_map"] = show_key
        self._refresh_batch_label()
        log(self.S, f"📂 Batch: загружена {base_name}",
            color=self.theme["fg2"], fg2=self.theme["fg2"])
        self.page.update()

    def _refresh_batch_label(self):
        keys = list(self.S["pbr_batch_results"].keys())
        if not keys or self.batch_label is None:
            return
        idx = self.S["pbr_batch_index"]
        if idx >= len(keys):
            idx = 0
            self.S["pbr_batch_index"] = 0
        self.batch_label.value = f"{keys[idx]}  ({idx + 1}/{len(keys)})"

    # ═══════════════════════════════════════════════════════════
    #  ДЕЙСТВИЯ
    # ═══════════════════════════════════════════════════════════

    async def pbr_do_load(self, e):
        th = self.theme
        try:
            files = await self.picker.pick_files(
                dialog_title=self.t("pbr_dialog_pick"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                initial_directory=init_dir(self.S),
            )
            if not files or not files[0].path:
                return
            fp = files[0].path
            remember_folder(self.S, fp)
            img = await asyncio.to_thread(safe_open_rgb, fp)
            self.S["pbr_source"] = img
            self.S["pbr_source_path"] = fp
            self.S["pbr_result"] = None
            self.S["pbr_batch_selected"] = None
            log(self.S, f"{self.t('pbr_log_loaded')} {os.path.basename(fp)}",
                color=th["success"], fg2=th["fg2"])
            log(self.S, "→ " + self.t("pbr_gen"),
                color=th["fg2"], fg2=th["fg2"])
            self.on_rebuild()
        except Exception as ex:
            log(self.S, f"❌ PBR load: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def pbr_do_generate(self, e):
        S = self.S
        th = self.theme
        if S["pbr_source"] is None:
            return
        try:
            await show_pbr_progress(S, self.page, self.t("pbr_progress_gen"))
            await asyncio.sleep(0.15)
            await self._maybe_rebuild_auto_metal_mask()
            result = await asyncio.to_thread(self._generate_sync)
            S["pbr_result"] = result
            log(S, self.t("pbr_log_gen_done"),
                color=th["success"], fg2=th["fg2"])
            await hide_pbr_progress(S, self.page)
            self.on_rebuild()
        except Exception as ex:
            await hide_pbr_progress(S, self.page)
            log(S, f"❌ PBR generate: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def pbr_do_simple_generate(self, e):
        S = self.S
        th = self.theme
        try:
            files = await self.picker.pick_files(
                dialog_title=self.t("pbr_dialog_pick"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                initial_directory=init_dir(S),
            )
            if not files or not files[0].path:
                return
            fp = files[0].path
            remember_folder(S, fp)
            img = await asyncio.to_thread(safe_open_rgb, fp)
            S["pbr_source"] = img
            S["pbr_source_path"] = fp
            S["pbr_result"] = None
            S["pbr_batch_selected"] = None
            log(S, f"{self.t('pbr_log_loaded')} {os.path.basename(fp)}",
                color=th["success"], fg2=th["fg2"])

            await show_pbr_progress(S, self.page, self.t("pbr_progress_gen"))
            await asyncio.sleep(0.1)
            await self._maybe_rebuild_auto_metal_mask()
            result = await asyncio.to_thread(self._generate_sync)
            S["pbr_result"] = result
            log(S, self.t("pbr_log_gen_done"),
                color=th["success"], fg2=th["fg2"])
            await hide_pbr_progress(S, self.page)
            self.on_rebuild()
        except Exception as ex:
            await hide_pbr_progress(S, self.page)
            log(S, f"❌ PBR generate: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    def _generate_sync(self) -> dict:
        S = self.S
        m_mode = S.get("pbr_metallic", "black")
        m_custom = S.get("pbr_metallic_custom") if m_mode in ("custom", "auto") else None
        r_mode = S.get("pbr_roughness", "procedural")
        r_custom = S.get("pbr_roughness_custom") if r_mode == "custom" else None
        return generate_pbr_all(
            S["pbr_source"],
            S.get("pbr_values", {}),
            metallic_mode=m_mode,
            metallic_custom=m_custom,
            roughness_mode=r_mode,
            roughness_custom=r_custom,
        )

    async def _maybe_rebuild_auto_metal_mask(self):
        S = self.S
        if (S.get("pbr_metallic") == "auto"
                and S.get("pbr_metal_target_rgb") is not None):
            try:
                rgb = S["pbr_metal_target_rgb"]
                mask = await asyncio.to_thread(
                    make_metallic_mask,
                    S["pbr_source"], rgb,
                    S.get("pbr_metal_tolerance", 0.15),
                    S.get("pbr_metal_softness", 0.05),
                    S.get("pbr_metal_negative_rgb"),
                    S.get("pbr_metal_negative_tolerance", 0.10),
                )
                S["pbr_metallic_custom"] = mask
                pct = mask_white_pct(mask)
                log(S, f"🎨 Metallic auto: {pct:.1f}% белых",
                    color=self.theme["fg2"], fg2=self.theme["fg2"])
            except Exception as ex:
                log(S, f"   ⚠ Auto metallic: {ex}",
                    color=self.theme["warn"], fg2=self.theme["fg2"])

    async def pbr_do_save(self, e):
        S = self.S
        th = self.theme
        if S["pbr_result"] is None:
            return
        try:
            await show_pbr_progress(S, self.page, self.t("pbr_progress_gen"))

            base_name = "pbr_output"
            if S["pbr_source_path"]:
                base_name = os.path.splitext(
                    os.path.basename(S["pbr_source_path"]))[0]
            folder = (os.path.dirname(S["pbr_source_path"])
                      if S["pbr_source_path"] else os.getcwd())
            out_dir = os.path.join(folder, f"{base_name}_pbr")
            os.makedirs(out_dir, exist_ok=True)

            bit_per_map = S.get("pbr_bit_depth_per_map", {})
            total = len(S["pbr_result"])
            done = 0
            for key, img in S["pbr_result"].items():
                bd = bit_per_map.get(key, S.get("pbr_bit_depth", 8))
                await asyncio.to_thread(
                    save_pbr_map, img,
                    str(os.path.join(out_dir, f"{base_name}_{key}.png")), bd,
                )
                done += 1
                S["pbr_progress_text"].value = (
                    f"{self.t('pbr_progress_gen')} {done}/{total}"
                )
                self.page.update()
                await asyncio.sleep(0.02)

            gc.collect()
            log(S, f"{self.t('pbr_log_saved')} {out_dir}",
                color=th["success"], fg2=th["fg2"])
            await hide_pbr_progress(S, self.page)
        except Exception as ex:
            await hide_pbr_progress(S, self.page)
            log(S, f"❌ PBR save: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def pbr_open_viewer(self, e):
        S = self.S
        th = self.theme
        if S["pbr_result"] is None:
            log(S, self.t("pbr_viewer_no_result"),
                color=th["warn"], fg2=th["fg2"])
            self.page.update()
            return
        try:
            await show_pbr_progress(S, self.page,
                                     self.t("pbr_viewer_progress"))
            await asyncio.sleep(0.05)

            tmpdir = tempfile.mkdtemp(prefix="albedo_viewer_")
            paths = {}
            keys = ("albedo", "height", "normal", "ao", "roughness",
                    "metallic", "orm")
            for key in keys:
                if key in S["pbr_result"]:
                    p = os.path.join(tmpdir, f"{key}.png")
                    img = S["pbr_result"][key]
                    if isinstance(img, np.ndarray):
                        await asyncio.to_thread(
                            to_preview_pil(img).save, p)
                    else:
                        await asyncio.to_thread(img.save, p)
                    paths[key] = p

            if "albedo" not in paths and S["pbr_source"] is not None:
                p = os.path.join(tmpdir, "albedo.png")
                await asyncio.to_thread(S["pbr_source"].save, p)
                paths["albedo"] = p

            import sys
            if getattr(sys, "frozen", False):
                viewer_path = os.path.join(
                    os.path.dirname(sys.executable), "viewer.exe")
                if not os.path.exists(viewer_path):
                    viewer_path = os.path.join(self.paths["base_dir"],
                                                "viewer.exe")
                cmd = [viewer_path]
            else:
                viewer_path = os.path.join(self.paths["base_dir"], "viewer.py")
                cmd = [sys.executable, viewer_path]

            cmd += [
                "--albedo", paths.get("albedo", ""),
                "--roughness", paths.get("roughness", ""),
                "--metallic", paths.get("metallic", ""),
                "--tile-x", str(S.get("viewer_tile_x", 4)),
                "--tile-y", str(S.get("viewer_tile_y", 3)),
                "--lang", S.get("lang", "ru"),
            ]
            subprocess.Popen(cmd)
            log(S, "👁 Viewer запущен", color=th["success"], fg2=th["fg2"])
            await asyncio.sleep(0.3)
            await hide_pbr_progress(S, self.page)
        except Exception as ex:
            await hide_pbr_progress(S, self.page)
            log(S, f"❌ Viewer: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def pbr_do_batch(self, e):
        S = self.S
        th = self.theme
        try:
            folder = await self.picker.get_directory_path(
                dialog_title=self.t("pbr_dialog_folder"))
            if not folder:
                return
            exts = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')
            files = [os.path.join(folder, f) for f in os.listdir(folder)
                     if f.lower().endswith(exts)]
            if not files:
                log(S, self.t("pbr_log_no_files"),
                    color=th["warn"], fg2=th["fg2"])
                self.page.update()
                return

            await show_pbr_progress(S, self.page, self.t("pbr_progress_batch"))
            out_root = os.path.join(folder, "_pbr_output")
            os.makedirs(out_root, exist_ok=True)

            m_mode = S.get("pbr_metallic", "black")
            r_mode = S.get("pbr_roughness", "procedural")
            if m_mode == "custom":
                log(S, f"   ⚠ Custom Metallic map будет применена ко ВСЕМ "
                       f"{len(files)} текстурам", color=th["warn"], fg2=th["fg2"])
            if r_mode == "custom":
                log(S, f"   ⚠ Custom Roughness map будет применена ко ВСЕМ "
                       f"{len(files)} текстурам", color=th["warn"], fg2=th["fg2"])

            m_custom = S.get("pbr_metallic_custom") if m_mode in ("custom", "auto") else None
            r_custom = S.get("pbr_roughness_custom") if r_mode == "custom" else None
            vals = S.get("pbr_values", {})

            S["pbr_batch_results"] = {}
            count = 0
            total_files = len(files)
            for i, fp in enumerate(files, 1):
                try:
                    S["pbr_progress_text"].value = (
                        f"{self.t('pbr_progress_batch')} {i}/{total_files}"
                    )
                    self.page.update()

                    img = await asyncio.to_thread(safe_open_rgb, fp)
                    result = await asyncio.to_thread(
                        generate_pbr_all, img, vals,
                        metallic_mode=m_mode,
                        metallic_custom=m_custom,
                        roughness_mode=r_mode,
                        roughness_custom=r_custom,
                    )
                    base = os.path.splitext(os.path.basename(fp))[0]
                    sub = os.path.join(out_root, base)
                    os.makedirs(sub, exist_ok=True)
                    await asyncio.to_thread(
                        img.save, str(os.path.join(sub, f"{base}_albedo.png")))
                    bit_per_map = S.get("pbr_bit_depth_per_map", {})
                    for k, m in result.items():
                        bd = bit_per_map.get(k, 8)
                        await asyncio.to_thread(
                            save_pbr_map, m,
                            str(os.path.join(sub, f"{base}_{k}.png")), bd,
                        )
                    count += 1
                    S["pbr_batch_results"][base] = sub
                    log(S, f"  [{i}/{total_files}] ✓ {os.path.basename(fp)}",
                        color=th["success"], fg2=th["fg2"])
                    self.page.update()
                    try:
                        img.close()
                    except Exception:
                        pass
                    if i % 5 == 0:
                        gc.collect()
                    await asyncio.sleep(0.01)
                except Exception as ex:
                    log(S, f"  ✗ {os.path.basename(fp)}: {ex}",
                        color=th["danger"], fg2=th["fg2"])
            log(S, f"{self.t('pbr_log_batch_done')} {count} "
                   f"{self.t('pbr_log_files')}",
                color=th["success"], fg2=th["fg2"])
            log(S, f"📁 {out_root}", color=th["fg2"], fg2=th["fg2"])
            await hide_pbr_progress(S, self.page)

            if count > 0:
                keys = list(S["pbr_batch_results"].keys())
                S["pbr_batch_index"] = 0
                self.pbr_load_batch_texture(keys[0])
                self.on_rebuild()
        except Exception as ex:
            await hide_pbr_progress(S, self.page)
            log(S, f"❌ PBR batch: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    # ═══════════════════════════════════════════════════════════
    #  ЗАГРУЗКА СВОИХ MAP
    # ═══════════════════════════════════════════════════════════

    async def pbr_load_metallic_map(self, e=None):
        S = self.S
        th = self.theme
        try:
            files = await self.picker.pick_files(
                dialog_title="Выбери Metallic map (grayscale)",
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                initial_directory=init_dir(S),
            )
            if not files or not files[0].path:
                return
            fp = files[0].path
            remember_folder(S, fp)
            img = await asyncio.to_thread(safe_open_gray, fp)
            arr = np.array(img).astype(np.float32) / 255.0

            if S.get("pbr_source") is not None:
                arr, ok = await self._ask_resize_dialog(
                    arr, S["pbr_source"], "Metallic")
                if not ok:
                    log(S, "   ⚠ Metallic загрузка отменена",
                        color=th["warn"], fg2=th["fg2"])
                    self.page.update()
                    return

            S["pbr_metallic_custom"] = arr
            S["pbr_metallic_custom_path"] = fp
            S["pbr_metallic"] = "custom"
            log(S, f"⚙ Metallic map загружена: {os.path.basename(fp)}",
                color=th["success"], fg2=th["fg2"])

            if S.get("pbr_source") is not None and S.get("pbr_result") is not None:
                log(S, "   → Автогенерация PBR с новой картой...",
                    color=th["fg2"], fg2=th["fg2"])
                await self.pbr_do_generate(None)
            else:
                self.on_rebuild()
        except Exception as ex:
            log(S, f"❌ Metallic load: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def pbr_load_roughness_map(self, e=None):
        S = self.S
        th = self.theme
        try:
            files = await self.picker.pick_files(
                dialog_title="Выбери Roughness map (grayscale)",
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                initial_directory=init_dir(S),
            )
            if not files or not files[0].path:
                return
            fp = files[0].path
            remember_folder(S, fp)
            img = await asyncio.to_thread(safe_open_gray, fp)
            arr = np.array(img).astype(np.float32) / 255.0

            if S.get("pbr_source") is not None:
                arr, ok = await self._ask_resize_dialog(
                    arr, S["pbr_source"], "Roughness")
                if not ok:
                    log(S, "   ⚠ Roughness загрузка отменена",
                        color=th["warn"], fg2=th["fg2"])
                    self.page.update()
                    return

            S["pbr_roughness_custom"] = arr
            S["pbr_roughness_custom_path"] = fp
            S["pbr_roughness"] = "custom"
            log(S, f"🔧 Roughness map загружена: {os.path.basename(fp)}",
                color=th["success"], fg2=th["fg2"])

            if S.get("pbr_source") is not None and S.get("pbr_result") is not None:
                log(S, "   → Автогенерация PBR с новой картой...",
                    color=th["fg2"], fg2=th["fg2"])
                await self.pbr_do_generate(None)
            else:
                self.on_rebuild()
        except Exception as ex:
            log(S, f"❌ Roughness load: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def _ask_resize_dialog(self, custom_arr, albedo_pil, map_name):
        resized, was_resized, old_size, new_size = resize_to_match(
            custom_arr, albedo_pil, map_name)
        if not was_resized:
            return custom_arr, True

        loop = asyncio.get_event_loop()
        fut = loop.create_future()

        def _resolve(ok):
            if not fut.done():
                fut.set_result(ok)

        th = self.theme
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(self.t("pbr_resize_title"), color=th["fg"], size=14),
            content=ft.Container(
                content=ft.Text(
                    self.t("pbr_resize_text").format(
                        w1=old_size[0], h1=old_size[1],
                        w2=new_size[0], h2=new_size[1]),
                    color=th["fg2"], size=12, font_family=FONT),
                width=380, height=100,
            ),
            actions=[
                ft.TextButton(self.t("pbr_resize_no"),
                              on_click=lambda e: _resolve(False)),
                ft.TextButton(self.t("pbr_resize_yes"),
                              on_click=lambda e: _resolve(True)),
            ],
            inset_padding=ft.Padding.symmetric(horizontal=80, vertical=120),
            bgcolor=th["panel"],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

        ok = await fut
        dlg.open = False
        self.page.update()

        if not ok:
            return custom_arr, False
        log(self.S, f"   ✅ {map_name} resized: {old_size[0]}×{old_size[1]} "
                    f"→ {new_size[0]}×{new_size[1]}",
            color=th["fg2"], fg2=th["fg2"])
        return resized, True

    # ═══════════════════════════════════════════════════════════
    #  PIPETTE
    # ═══════════════════════════════════════════════════════════

    async def pbr_pick_color(self, e=None, mode: str = "positive"):
        S = self.S
        th = self.theme
        if S.get("pbr_source") is None:
            log(S, "   ⚠ Сначала загрузи Albedo в PBR",
                color=th["warn"], fg2=th["fg2"])
            self.page.update()
            return

        src = S["pbr_source"]
        max_disp = 600
        disp = src.copy()
        disp.thumbnail((max_disp, max_disp), Image.LANCZOS)
        disp_w, disp_h = disp.size
        orig_w, orig_h = src.size
        scale = orig_w / disp_w

        state = {"rgb": None,
                 "img_src": f"data:image/png;base64,"
                            f"{pil_to_b64(disp, max_size=max_disp)}"}

        color_swatch = ft.Container(width=32, height=32, bgcolor="#000000",
                                      border_radius=4)
        picked_label = ft.Text("—", color=th["fg"], size=13,
                                font_family=FONT_MONO,
                                weight=ft.FontWeight.W_600)
        img_control = ft.Image(src=state["img_src"],
                                fit=ft.BoxFit.CONTAIN,
                                width=disp_w, height=disp_h)
        stack = ft.Stack([img_control], width=disp_w, height=disp_h)

        def _on_image_click(e):
            try:
                lx = getattr(e, "local_x", None)
                ly = getattr(e, "local_y", None)
                if lx is None or ly is None:
                    pos = getattr(e, "local_position", None)
                    if pos is not None:
                        lx = getattr(pos, "x", None)
                        ly = getattr(pos, "y", None)
                if lx is None or ly is None:
                    return
                ox = int(lx * scale)
                oy = int(ly * scale)
                ox = max(0, min(orig_w - 1, ox))
                oy = max(0, min(orig_h - 1, oy))

                rgb = pick_color_from_pixel(src, ox, oy, half_window=2)
                state["rgb"] = rgb
                color_swatch.bgcolor = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
                picked_label.value = f"RGB({rgb[0]}, {rgb[1]}, {rgb[2]})"
                if mode == "negative":
                    log(S, self.t("pbr_metal_negative_saved").format(
                        r=rgb[0], g=rgb[1], b=rgb[2]),
                        color=th["success"], fg2=th["fg2"])
                else:
                    log(S, self.t("pbr_metal_pick_saved").format(
                        r=rgb[0], g=rgb[1], b=rgb[2]),
                        color=th["success"], fg2=th["fg2"])
                self.page.update()
            except Exception:
                pass

        clickable = ft.GestureDetector(
            content=stack, on_tap_down=_on_image_click,
            mouse_cursor=ft.MouseCursor.PRECISE,
        )

        title_text = (self.t("pbr_metal_negative_hint") if mode == "negative"
                       else self.t("pbr_metal_pick_dialog"))

        def _close(e=None):
            dlg.open = False
            if state["rgb"] is not None:
                if mode == "negative":
                    S["pbr_metal_negative_rgb"] = state["rgb"]
                else:
                    S["pbr_metal_target_rgb"] = state["rgb"]
                    S["pbr_metallic"] = "auto"
                self.on_persist()
                self.on_rebuild()
            else:
                self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(title_text, color=th["fg"], size=14),
            content=ft.Container(
                content=ft.Column([
                    clickable,
                    ft.Container(height=8),
                    ft.Row([color_swatch, ft.Container(width=8), picked_label],
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ], spacing=0,
                   horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=min(disp_w, 600) + 20,
            ),
            actions=[
                ft.TextButton(self.t("pbr_metal_pick_dialog_close"),
                              on_click=_close),
            ],
            inset_padding=ft.Padding.symmetric(horizontal=40, vertical=40),
            bgcolor=th["panel"],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()