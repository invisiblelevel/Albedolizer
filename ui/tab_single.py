"""
ui/tab_single.py — вкладка Single целиком.

Класс SingleTab:
  • тулбар (Simple / Advanced)
  • правая панель: авто-детект, категории, пресеты, correction switch,
    tiling, seamless, soap, saturation, stats
  • превью с InteractiveViewer
  • все действия Single
  • хоткеи Ctrl+O/S/R/Z, Space, Enter
  • fallback-диалог
  • info-диалог

Зависимости передаются через конструктор — не через глобалы.
"""

import os
import asyncio
import numpy as np
from PIL import Image
import flet as ft

from config import (
    TEXTURE_PROFILES, PROFILE_CATEGORIES, AI_MODELS,
)
from core.image_ops import (
    analyze_image, is_valid, make_heatmap, get_luminance,
    apply_ai, apply_fallback, apply_soap, apply_saturation,
    apply_seamless, apply_realism, make_tiled,
)
from core.io import (
    save_16bit_or_8bit, pil_to_b64, fmt_size, safe_open_rgb,
)
from core.state import remember_folder, init_dir
from ui.icons import img_icon
from ui.theme import make_btn, make_chip, section_title, divider
from ui.helpers import (
    log, refresh_log, add_stat, clear_stats,
    show_progress, hide_progress,
)

FONT = "Segoe UI"
FONT_MONO = "Consolas"


class SingleTab:
    """
    Вкладка Single.

    Конструктор:
        page            — ft.Page
        S               — словарь состояния (core.state)
        t               — функция перевода t(key) → str
        picker          — ft.FilePicker
        paths           — dict: {
                            'base_dir', 'autolevels_exe', 'autolevels_model',
                            'lutwithbgrid_model', 'clip_vision', 'clip_text'
                          }
        theme           — dict цветов (THEME_DARK или THEME_LIGHT)
        clip            — CLIPMaterialClassifier (уже загруженный объект)
        on_rebuild      — callback() — перерисовать весь экран
        on_persist      — callback() — сохранить настройки
        on_lang_toggle  — callback() — переключить язык
    """

    def __init__(self, page, S, t, picker, paths, theme, clip,
                 on_rebuild, on_persist, on_lang_toggle):
        self.page = page
        self.S = S
        self.t = t
        self.picker = picker
        self.paths = paths
        self.theme = theme
        self.clip = clip
        self.on_rebuild = on_rebuild
        self.on_persist = on_persist
        self.on_lang_toggle = on_lang_toggle

        # Ссылки, заполняются в _build_*
        self.buttons = {}
        self.preview_image = None
        self.file_info_label = None
        self._dialog = None

    # ═══════════════════════════════════════════════════════════
    #  ПУБЛИЧНЫЙ API
    # ═══════════════════════════════════════════════════════════

    def build(self) -> ft.Container:
        """Собирает вкладку и возвращает готовый Container."""
        is_simple = self.S["ui_mode"] == "simple"

        # ─── Общие ссылки (в S, чтобы helpers работали) ───
        self.preview_image = ft.Image(src="", visible=False,
                                       fit=ft.BoxFit.CONTAIN)
        _saved_src = self.S.get("preview_image_src")
        if _saved_src:
            self.preview_image.src = _saved_src
            self.preview_image.visible = self.S.get(
                "preview_image_visible", True)
        self.S["preview_image"] = self.preview_image

        file_info_lbl = ft.Container(
            content=ft.Text("", color=self.theme["fg"], size=12,
                            font_family=FONT_MONO, selectable=True),
            bgcolor=self.theme["input"], border_radius=6,
            padding=ft.Padding.symmetric(vertical=6, horizontal=10),
            visible=False,
        )
        self.file_info_label = file_info_lbl
        self.S["file_info_label"] = file_info_lbl
        self._update_file_info()

        preview_hint = ft.Text(self.t("preview_hint"),
                                color=self.theme["fg3"], size=14,
                                font_family=FONT,
                                visible=not bool(self.S.get("preview_image_src")))

        preview_content = ft.Stack([
            ft.Container(content=preview_hint,
                         alignment=ft.Alignment.CENTER, expand=True),
            ft.Container(content=self.preview_image,
                         alignment=ft.Alignment.CENTER, expand=True),
        ], expand=True)

        preview_box = ft.Container(
            content=ft.InteractiveViewer(
                content=preview_content,
                min_scale=0.5, max_scale=8.0, expand=True,
            ),
            bgcolor=self.theme["card"], border_radius=12,
            padding=10, expand=True,
        )

        # ─── Тулбар ───
        if is_simple:
            toolbar = self._build_toolbar_simple()
        else:
            toolbar = self._build_toolbar_advanced()

        # ─── Правая панель ───
        right_panel = self._build_right_panel(is_simple)

        # ─── Лог-панель (bottom sheet) — заглушка, общий лог в main ───
        log_panel = ft.Container(height=0)

        return ft.Container(
            content=ft.Column([
                toolbar,
                ft.Container(height=4),
                file_info_lbl,
                self.S["progress_bar"],
                self.S["progress_text"],
                ft.Container(height=6),
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Container(content=preview_box, expand=3),
                                ft.Container(height=8),
                                log_panel,
                            ], spacing=0, expand=True),
                            expand=True,
                        ),
                        right_panel,
                    ], spacing=12, expand=True),
                    expand=True,
                ),
            ], spacing=0, expand=True),
            expand=True,
            visible=True,
        )

    def run_hotkey(self, e) -> bool:
        """
        Обрабатывает хоткей если активна Single-вкладка.
        Возвращает True если обработал.
        """
        key = (e.key or "").lower()
        is_simple = self.S["ui_mode"] == "simple"

        if e.ctrl and key == "o":
            if is_simple:
                self.page.run_task(self.do_simple_process, None)
            else:
                self.page.run_task(self.open_file, None)
            return True

        if e.ctrl and key == "s":
            if self.S.get("corrected") is not None:
                self.page.run_task(self.open_save, None)
            return True

        if e.ctrl and key == "r":
            if self.S.get("original") is not None:
                self.page.run_task(self.do_reset, None)
            return True

        if e.ctrl and key == "z":
            if self.S.get("corrected") is not None:
                self.page.run_task(self.do_reset, None)
            return True

        if key in (" ", "space"):
            if not is_simple and self.S.get("corrected") is not None:
                self.toggle_preview(None)
            return True

        if key == "enter":
            if is_simple:
                if self.S.get("original") is None:
                    self.page.run_task(self.do_simple_process, None)
            else:
                if self.S.get("corrected") is not None:
                    self.page.run_task(self.open_save, None)
                elif self.S.get("original") is not None:
                    self.page.run_task(self.do_auto_correct, None)
            return True

        return False

    # ═══════════════════════════════════════════════════════════
    #  ТУЛБАРЫ
    # ═══════════════════════════════════════════════════════════

    def _build_toolbar_simple(self) -> ft.Row:
        th = self.theme
        btns = self.buttons

        btns["load"] = make_btn(
            self.t("fix"), self.do_simple_process, th["success"],
            icon="wand-sparkles", size=14, vertical=13, horizontal=16,
        )
        btns["save"] = make_btn(
            self.t("save"), self.open_save, th["save"],
            icon="save", disabled=(self.S["corrected"] is None),
            size=14, vertical=13, horizontal=16,
        )

        return ft.Row([
            btns["load"],
            ft.Container(expand=True),
            btns["save"],
        ], spacing=6)

    def _build_toolbar_advanced(self) -> ft.Row:
        th = self.theme
        btns = self.buttons

        btns["load"] = make_btn(
            self.t("load"), self.open_file, th["accent"],
            icon="folder-open", size=13, vertical=11, horizontal=16,
        )
        btns["check"] = make_btn(
            self.t("check"), self.do_check, th["accent"],
            icon="search-check",
            disabled=(self.S["original"] is None),
            size=13, vertical=11, horizontal=16,
        )
        btns["fix"] = make_btn(
            self.t("fix"), self.do_auto_correct, th["success"],
            icon="wand-sparkles",
            disabled=not self.S.get("need_fix", False),
            size=13, vertical=11, horizontal=16,
        )
        btns["preview_toggle"] = make_btn(
            self.t("preview_toggle_result") if self.S["show_original"]
            else self.t("preview_toggle_orig"),
            self.toggle_preview, th["seamless"],
            icon="eye", disabled=(self.S["corrected"] is None),
            size=13, vertical=11, horizontal=16,
        )
        btns["reset"] = make_btn(
            self.t("reset"), self.do_reset, th["reset"],
            icon="rotate-ccw", disabled=(self.S["corrected"] is None),
            size=13, vertical=11, horizontal=16,
        )
        btns["save"] = make_btn(
            self.t("save"), self.open_save, th["save"],
            icon="save", disabled=(self.S["corrected"] is None),
            size=13, vertical=11, horizontal=16,
        )

        return ft.Row([
            btns["load"],
            btns["check"],
            btns["fix"],
            btns["preview_toggle"],
            ft.Container(expand=True),
            btns["reset"],
            btns["save"],
        ], spacing=6)

    # ═══════════════════════════════════════════════════════════
    #  ПРАВАЯ ПАНЕЛЬ
    # ═══════════════════════════════════════════════════════════

    def _build_right_panel(self, is_simple: bool) -> ft.Container:
        th = self.theme
        S = self.S

        auto_detect_btn = make_btn(
            self.t("auto_detect_btn"), self.do_auto_detect_material,
            th["success"], icon="bot",
            disabled=(S["original"] is None),
            size=12, vertical=11, horizontal=14,
        )
        self.buttons["auto_detect"] = auto_detect_btn

        controls = [
            auto_detect_btn,
            ft.Container(height=10),
            divider(th["fg3"]),
            ft.Container(height=10),
            section_title(self.t("profile_title"), th["fg3"]),
            ft.Container(height=6),
            self._build_category_tabs(),
            ft.Container(height=4),
            self._build_preset_grid(),
            ft.Container(height=6),
            ft.Container(
                content=ft.Text(
                    f"{self.t('all_types')}: "
                    f"{TEXTURE_PROFILES[S['profile']][S['lang']]}",
                    color=th["fg2"], size=12, font_family=FONT),
                bgcolor=th["input"], border_radius=8, padding=10,
            ),
        ]

        if not is_simple:
            controls.extend([
                ft.Container(height=14),
                divider(th["fg3"]),
                ft.Container(height=10),
                section_title(self.t("correction_mode_title"), th["fg3"]),
                ft.Container(height=6),
                self._build_correction_switch(),
                ft.Container(height=14),
                divider(th["fg3"]),
                ft.Container(height=10),
                self._build_tiling_seamless_row(),
                ft.Container(height=4),
                ft.Checkbox(
                    label=self.t("seamless_hipass"),
                    value=S.get("seamless_hipass", True),
                    fill_color=th["seamless"],
                    label_style=ft.TextStyle(color=th["fg2"], size=11,
                                              font_family=FONT),
                    on_change=self._on_hipass_toggle,
                ),
                ft.Container(height=14),
                divider(th["fg3"]),
                ft.Container(height=10),
                section_title(self.t("soap_fix_title"), th["fg3"]),
                ft.Container(height=6),
                ft.Text(self.t("soap_fix_label"), color=th["fg2"],
                        size=11, font_family=FONT),
                self._make_slider("soap_fix_strength", 0.0, 3.0, 15),
                ft.Container(height=4),
                make_btn(
                    self.t("soap_fix_button"), self.do_remove_soap,
                    th["save"], icon="sparkles",
                    size=12, vertical=11, horizontal=14,
                ),
                ft.Container(height=14),
                divider(th["fg3"]),
                ft.Container(height=10),
                section_title(self.t("sat_title"), th["fg3"]),
                ft.Container(height=6),
                ft.Text(self.t("sat_label"), color=th["fg2"],
                        size=11, font_family=FONT),
                self._make_slider("saturation_boost", 0.8, 1.5, 14),
                ft.Container(height=4),
                make_btn(
                    self.t("sat_button"), self.do_boost_saturation,
                    th["sat"], icon="palette",
                    size=12, vertical=11, horizontal=14,
                ),
                ft.Container(height=14),
                divider(th["fg3"]),
                ft.Container(height=10),
                section_title(self.t("stats_title"), th["fg3"]),
                ft.Container(height=8),
                self.S["stats_column"],
            ])

        return ft.Container(
            content=ft.Column(controls, spacing=4,
                              scroll=ft.ScrollMode.AUTO),
            bgcolor=th["panel"], border_radius=12,
            padding=16, width=320,
        )

    def _make_slider(self, key: str, minv: float, maxv: float,
                     divisions: int) -> ft.Slider:
        th = self.theme

        def _on_change(e):
            self.S[key] = e.control.value
        return ft.Slider(
            min=minv, max=maxv, divisions=divisions,
            value=self.S.get(key, (minv + maxv) / 2),
            label="{value}",
            active_color=th["accent"], inactive_color=th["input"],
            on_change=_on_change,
        )

    def _on_hipass_toggle(self, e):
        self.S["seamless_hipass"] = e.control.value
        self.on_persist()

    def _build_category_tabs(self) -> ft.Column:
        """Сетка категорий: 4 сверху, 3 снизу. С Lucide-иконками."""
        th = self.theme
        icon_map = {
            "metal": "flame",
            "nature": "leaf",
            "mineral": "mountain",
            "synth": "flask-conical",
            "fabric": "shirt",
            "special": "droplet",
            "fauna": "paw-print",
        }
        rows = []
        row = []
        per_row = 4
        for key, cat in PROFILE_CATEGORIES.items():
            is_active = self.S["profile_category"] == key
            icon_name = icon_map.get(key, "layers")
            # Цвет контента — БЕЛЫЙ на активном
            content_color = "#ffffff" if is_active else th["fg2"]

            content = ft.Column([
                img_icon(icon_name, content_color, 16),
                ft.Container(height=2),
                ft.Text(cat[self.S["lang"]],
                        color=content_color,
                        size=9, font_family=FONT,
                        text_align=ft.TextAlign.CENTER),
            ], spacing=0,
               horizontal_alignment=ft.CrossAxisAlignment.CENTER)

            chip = ft.Container(
                content=content,
                bgcolor=th["accent"] if is_active else th["card"],
                border_radius=8,
                padding=ft.Padding.symmetric(vertical=6, horizontal=4),
                expand=True, ink=not is_active,
                on_click=lambda e, k=key: self._set_category(k),
            )
            row.append(chip)
            if len(row) == per_row:
                rows.append(ft.Row(row, spacing=4))
                row = []
        if row:
            while len(row) < per_row:
                row.append(ft.Container(expand=True))
            rows.append(ft.Row(row, spacing=4))
        return ft.Column(rows, spacing=4)

    def _build_preset_grid(self) -> ft.Column:
        """Пресеты внутри категории. БЕЗ иконок — только название."""
        th = self.theme
        cat_key = self.S["profile_category"]
        items = PROFILE_CATEGORIES[cat_key]["items"]
        rows = []
        row = []
        per_row = 2
        for key in items:
            is_active = self.S["profile"] == key
            label = TEXTURE_PROFILES[key][self.S["lang"]]
            chip = ft.Container(
                content=ft.Text(
                    label,
                    color="#ffffff" if is_active else th["fg2"],
                    size=11, font_family=FONT,
                    weight=ft.FontWeight.W_600 if is_active
                    else ft.FontWeight.W_500,
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor=th["accent"] if is_active else th["card"],
                border_radius=8,
                padding=ft.Padding.symmetric(vertical=8, horizontal=4),
                expand=True, ink=not is_active,
                on_click=lambda e, k=key: self._set_profile(k),
            )
            row.append(chip)
            if len(row) == per_row:
                rows.append(ft.Row(row, spacing=4))
                row = []
        if row:
            while len(row) < per_row:
                row.append(ft.Container(expand=True))
            rows.append(ft.Row(row, spacing=4))
        return ft.Column(rows, spacing=4)

    def _build_correction_switch(self) -> ft.Column:
        """Autolevels / LUTwithBGrid / Math. БЕЗ иконок."""
        th = self.theme
        method = self.S.get("correction_mode", "ai")
        model = self.S.get("ai_model", "autolevels")

        def _btn(label, active, on_click, width=None):
            return ft.Container(
                content=ft.Text(label,
                                color="#ffffff" if active else th["fg2"],
                                size=11, font_family=FONT,
                                weight=ft.FontWeight.W_600,
                                text_align=ft.TextAlign.CENTER),
                bgcolor=th["accent"] if active else th["card"],
                border_radius=8,
                padding=ft.Padding.symmetric(vertical=8, horizontal=6),
                expand=(width is None), width=width,
                ink=not active,
                on_click=on_click,
            )

        def set_ai_model(model_key):
            self.S["correction_mode"] = "ai"
            self.S["ai_model"] = model_key
            self.on_persist()
            self.on_rebuild()

        def set_math():
            self.S["correction_mode"] = "math"
            self.on_persist()
            self.on_rebuild()

        autolevels_active = (method == "ai") and (model == "autolevels")
        lut_active = (method == "ai") and (model == "lutwithbgrid")
        math_active = (method == "math")

        return ft.Column([
            ft.Row([
                _btn(self.t("correction_ai_autolevels"), autolevels_active,
                     lambda e: set_ai_model("autolevels")),
                _btn(self.t("correction_ai_lutwithbgrid"), lut_active,
                     lambda e: set_ai_model("lutwithbgrid")),
            ], spacing=4),
            ft.Row([
                _btn(self.t("correction_math"), math_active,
                     lambda e: set_math(), width=142),
            ], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=4)

    def _build_tiling_seamless_row(self) -> ft.Row:
        th = self.theme
        tiling_btn = make_btn(
            self.t("tiling_btn") if not self.S["tiling_mode"]
            else self.t("tiling_btn_off"),
            self.toggle_tiling, th["tiling"],
            icon="grid-3x3", size=11, vertical=10, horizontal=10,
        )
        self.buttons["tiling"] = tiling_btn
        seamless_btn = make_btn(
            self.t("seamless_btn"), self.do_make_seamless,
            th["seamless"], icon="square",
            size=11, vertical=10, horizontal=10,
        )
        return ft.Row([
            ft.Container(content=tiling_btn, expand=True),
            ft.Container(content=seamless_btn, expand=True),
        ], spacing=6)

    # ═══════════════════════════════════════════════════════════
    #  СМЕНА ПРОФИЛЯ / КАТЕГОРИИ
    # ═══════════════════════════════════════════════════════════

    def _set_profile(self, key: str):
        self.S["profile"] = key
        self.S["pbr_sliders"] = {}
        log(self.S, f"{self.t('log_type')} "
                    f"{TEXTURE_PROFILES[key][self.S['lang']]}",
            color=self.theme["fg2"], fg2=self.theme["fg2"])
        self.on_persist()
        self.on_rebuild()

    def _set_category(self, key: str):
        self.S["profile_category"] = key
        items = PROFILE_CATEGORIES[key]["items"]
        if self.S["profile"] not in items:
            self.S["profile"] = items[0]
        self.S["pbr_sliders"] = {}
        self.on_persist()
        self.on_rebuild()

    # ═══════════════════════════════════════════════════════════
    #  ПРЕВЬЮ / СТАТИСТИКА
    # ═══════════════════════════════════════════════════════════

    def _set_preview(self, pil_img):
        """Ставит превью и сохраняет src в S (чтобы не терять при rebuild)."""
        src_data = f"data:image/png;base64,{pil_to_b64(pil_img)}"
        self.preview_image.src = src_data
        self.preview_image.visible = True
        self.S["preview_image_src"] = src_data
        self.S["preview_image_visible"] = True

    def _update_preview_display(self):
        """Ставит preview_image.src в зависимости от show_original."""
        S = self.S
        if S["show_original"] and S["original"] is not None:
            img = S["original"]
        elif S["corrected"] is not None:
            img = S["corrected"]
        elif S["original"] is not None:
            img = S["original"]
        else:
            return
        self._set_preview(img)

    def _update_file_info(self):
        """Инфо-плашка файла."""
        lbl = self.file_info_label
        if lbl is None:
            return
        S = self.S
        if not S.get("image_path") or S.get("original") is None:
            lbl.visible = False
            return
        try:
            name = os.path.basename(S["image_path"])
            w, h = S["original"].size
            mode = S["original"].mode
            try:
                size_str = fmt_size(os.path.getsize(S["image_path"]))
            except Exception:
                size_str = "—"
            lbl.content.value = (
                f"{name}  ·  {w}×{h}  ·  {mode}  ·  {size_str}"
            )
            lbl.visible = True
        except Exception:
            lbl.visible = False

    def run_check(self, img: Image.Image, show_heatmap: bool = True):
        """Статистика + PASS/FAIL + heatmap."""
        th = self.theme
        s = analyze_image(img, self.S["profile"])
        clear_stats(self.S)
        add_stat(self.S, self.t("stat_min"), f"{s['min']:.1f}",
                 fg2=th["fg2"], fg3=th["fg3"])
        add_stat(self.S, self.t("stat_max"), f"{s['max']:.1f}",
                 fg2=th["fg2"], fg3=th["fg3"])
        add_stat(self.S, self.t("stat_avg"), f"{s['avg']:.1f}",
                 fg2=th["fg2"], fg3=th["fg3"])
        add_stat(self.S, self.t("stat_median"), f"{s['median']:.1f}",
                 fg2=th["fg2"], fg3=th["fg3"])
        add_stat(self.S, self.t("stat_p1"), f"{s['p1']:.1f}",
                 fg2=th["fg2"], fg3=th["fg3"])
        add_stat(self.S, self.t("stat_p99"), f"{s['p99']:.1f}",
                 fg2=th["fg2"], fg3=th["fg3"])

        log(self.S, "", fg2=th["fg2"])
        log(self.S, "━━━━━━━━━━━━━━━━━━━━━━", color=th["fg3"],
            fg2=th["fg2"])
        log(self.S, self.t("log_results"), color=th["fg"],
            fg2=th["fg2"])

        dark_ok = s["dark_pct"] <= 5.0
        light_ok = s["light_pct"] <= 5.0

        log(self.S, f"  {self.t('log_dark')} (<{s['dark_t']}): "
                    f"{s['dark_pct']:.2f}%",
            color=th["success"] if dark_ok else th["danger"],
            fg2=th["fg2"])
        log(self.S, f"  {self.t('log_light')} (>{s['light_t']}): "
                    f"{s['light_pct']:.2f}%",
            color=th["success"] if light_ok else th["danger"],
            fg2=th["fg2"])

        if dark_ok and light_ok:
            log(self.S, self.t("log_pass"), color=th["success"],
                fg2=th["fg2"])
            self.S["need_fix"] = False
        else:
            log(self.S, self.t("log_fail"), color=th["danger"],
                fg2=th["fg2"])
            self.S["need_fix"] = True

        if show_heatmap:
            heatmap = make_heatmap(img, s)
            self.S["show_original"] = False
            self._set_preview(heatmap)
            if self.buttons.get("preview_toggle"):
                self.buttons["preview_toggle"].set_label(
                    self.t("preview_toggle_orig")
                )

    # ═══════════════════════════════════════════════════════════
    #  ДЕЙСТВИЯ: ПРОВЕРКА / КОРРЕКЦИЯ / СБРОС
    # ═══════════════════════════════════════════════════════════

    async def do_check(self, e):
        if self.S["original"] is None:
            return
        th = self.theme
        await show_progress(self.S, self.page, self.t("progress_check"),
                            fg2=th["fg2"])
        await asyncio.sleep(0.1)
        self.S["show_original"] = False
        img = self.S["corrected"] if self.S["corrected"] else self.S["original"]
        self.run_check(img, True)
        await hide_progress(self.S, self.page)
        self.on_rebuild()

    async def do_auto_correct(self, e):
        if self.S["original"] is None:
            return
        th = self.theme
        try:
            await show_progress(self.S, self.page, self.t("progress_fix"),
                                fg2=th["fg2"])
            await asyncio.sleep(0.15)

            if self.S["correction_mode"] == "math":
                await self._correct_math_path()
                return

            import time as _time
            _t0 = _time.time()
            ai_result, ai_ok, err = await asyncio.to_thread(self._apply_ai)
            _dt = _time.time() - _t0
            log(self.S, f"   ⏱ AI-коррекция: {_dt:.2f} сек",
                color=th["fg2"], fg2=th["fg2"])

            if ai_ok and ai_result is not None:
                self.S["corrected"] = ai_result
                self.S["last_op"] = "corrected"
                self.S["show_original"] = False
                log(self.S, "", fg2=th["fg2"])
                log(self.S, self.t("log_fix_done"), color=th["success"],
                    fg2=th["fg2"])
                self.run_check(ai_result, False)
                await hide_progress(self.S, self.page)
                self.on_rebuild()
                return
            else:
                if err:
                    log(self.S, f"   ⚠ AI: {err}", color=th["warn"],
                        fg2=th["fg2"])
                log(self.S, "   → AI недоступен. Применяется fallback.",
                    color=th["warn"], fg2=th["fg2"])
                result = await asyncio.to_thread(
                    apply_fallback, self.S["original"], self.S["profile"]
                )
                result = await asyncio.to_thread(
                    apply_soap, result, self.S["soap_fix_strength"]
                )
                self.S["corrected"] = result
                self.S["last_op"] = "corrected"
                self.S["show_original"] = False
                log(self.S, self.t("log_fix_done"), color=th["success"],
                    fg2=th["fg2"])
                self.run_check(result, False)
                await hide_progress(self.S, self.page)
                self.on_rebuild()
                return
        except Exception as ex:
            await hide_progress(self.S, self.page)
            log(self.S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    def _apply_ai(self):
        """Синхронная AI-коррекция (для to_thread)."""
        return apply_ai(
            self.S["original"],
            self.S["ai_model"],
            self.paths["autolevels_exe"],
            self.paths["autolevels_model"],
            self.paths["lutwithbgrid_model"],
        )

    async def _correct_math_path(self):
        """Math-путь для do_auto_correct."""
        th = self.theme
        log(self.S, "   → Режим: Math коррекция",
            color=th["fg2"], fg2=th["fg2"])
        result = await asyncio.to_thread(
            apply_fallback, self.S["original"], self.S["profile"]
        )
        result = await asyncio.to_thread(
            apply_soap, result, self.S["soap_fix_strength"]
        )
        self.S["corrected"] = result
        self.S["last_op"] = "corrected"
        self.S["show_original"] = False
        self._update_preview_display()
        log(self.S, "", fg2=th["fg2"])
        log(self.S, self.t("log_fix_done"), color=th["success"],
            fg2=th["fg2"])
        await asyncio.sleep(0.1)
        self.run_check(result, False)
        await hide_progress(self.S, self.page)
        self.on_rebuild()

    def _enable_post_actions(self):
        """Включает кнопки Save/Reset/Preview после коррекции."""
        for k in ("save", "reset", "preview_toggle"):
            if self.buttons.get(k):
                self.buttons[k].disabled = False
        self.page.update()

    async def do_reset(self, e):
        if self.S["original"] is None:
            return
        th = self.theme
        self.S["corrected"] = None
        self.S["last_op"] = None
        self.S["show_original"] = False
        self.S["need_fix"] = False
        self._update_preview_display()
        log(self.S, self.t("log_reset"), color=th["fg2"], fg2=th["fg2"])
        self.on_rebuild()

    # ═══════════════════════════════════════════════════════════
    #  SIMPLE PROCESS
    # ═══════════════════════════════════════════════════════════

    async def do_simple_process(self, e):
        """Simple: открыть → auto-detect → AI → saturation → результат."""
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
            remember_folder(self.S, fp, save_fn=None)

            await show_progress(self.S, self.page, self.t("progress_load"),
                                fg2=th["fg2"])
            await asyncio.sleep(0.1)

            img = await asyncio.to_thread(safe_open_rgb, fp)
            self.S["image_path"] = fp
            self.S["original"] = img
            self.S["corrected"] = None
            self.S["last_op"] = None
            self.S["show_original"] = False
            self.S["need_fix"] = False
            self._set_preview(img)
            self._update_file_info()

            log(self.S, "", fg2=th["fg2"])
            log(self.S, f"{self.t('log_loaded')} {os.path.basename(fp)}",
                color=th["success"], fg2=th["fg2"])
            self.page.update()

            # Auto-detect
            self.S["progress_text"].value = self.t("auto_detect_progress")
            self.page.update()
            await asyncio.sleep(0.05)

            detected = await self._try_auto_detect(img)

            if not detected:
                log(self.S, f"{self.t('log_type')} "
                            f"{TEXTURE_PROFILES[self.S['profile']][self.S['lang']]}",
                    color=th["fg2"], fg2=th["fg2"])
            else:
                self.on_persist()

            self.page.update()
            await asyncio.sleep(0.1)

            # AI
            self.S["progress_text"].value = self.t("progress_fix")
            self.page.update()
            await asyncio.sleep(0.1)

            ai_result, ai_ok, err = await asyncio.to_thread(self._apply_ai)

            if ai_ok and ai_result is not None:
                result = ai_result
            else:
                log(self.S, "   → AI недоступен. Применяется fallback.",
                    color=th["warn"], fg2=th["fg2"])
                result = await asyncio.to_thread(
                    apply_fallback, img, self.S["profile"]
                )

            result = await asyncio.to_thread(
                apply_saturation, result, 1.15
            )

            self.S["corrected"] = result
            self.S["last_op"] = "corrected"
            self.S["show_original"] = False
            self._update_preview_display()
            log(self.S, self.t("log_fix_done"), color=th["success"],
                fg2=th["fg2"])

            await hide_progress(self.S, self.page)
            self.on_rebuild()
        except Exception as ex:
            await hide_progress(self.S, self.page)
            log(self.S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    # ═══════════════════════════════════════════════════════════
    #  OPEN / SAVE
    # ═══════════════════════════════════════════════════════════

    async def open_file(self, e):
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
            remember_folder(self.S, fp, save_fn=None)

            await show_progress(self.S, self.page, self.t("progress_load"),
                                fg2=th["fg2"])
            await asyncio.sleep(0.1)

            img = await asyncio.to_thread(safe_open_rgb, fp)
            self.S["image_path"] = fp
            self.S["original"] = img
            self.S["corrected"] = None
            self.S["last_op"] = None
            self.S["show_original"] = False
            self._update_preview_display()
            self._update_file_info()

            log(self.S, "", fg2=th["fg2"])
            log(self.S, f"{self.t('log_loaded')} {os.path.basename(fp)}",
                color=th["success"], fg2=th["fg2"])
            log(self.S, f"{self.t('log_type')} "
                        f"{TEXTURE_PROFILES[self.S['profile']][self.S['lang']]}",
                color=th["fg2"], fg2=th["fg2"])
            log(self.S, self.t("log_click_check"), color=th["fg2"],
                fg2=th["fg2"])

            await hide_progress(self.S, self.page)
            self.on_rebuild()
        except Exception as ex:
            await hide_progress(self.S, self.page)
            log(self.S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def open_save(self, e):
        th = self.theme
        try:
            if self.S.get("image_path"):
                base = os.path.splitext(
                    os.path.basename(self.S["image_path"])
                )[0]
            else:
                base = "albedo"

            if self.S.get("last_op") == "compressed":
                default_name = f"{base}_compressed.png"
            else:
                default_name = f"{base}_corrected.png"

            path = await self.picker.save_file(
                dialog_title=self.t("dialog_save_title"),
                file_name=default_name,
                allowed_extensions=["png", "jpg", "tif"],
                initial_directory=init_dir(self.S),
            )
            if path and self.S["corrected"] is not None:
                await asyncio.to_thread(
                    save_16bit_or_8bit, self.S["corrected"], str(path), 16
                )
                remember_folder(self.S, str(path), save_fn=None)
                log(self.S, f"{self.t('log_saved')} "
                            f"{os.path.basename(str(path))}",
                    color=th["success"], fg2=th["fg2"])
                self.page.update()
        except Exception as ex:
            log(self.S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    # ═══════════════════════════════════════════════════════════
    #  AUTO-DETECT (CLIP)
    # ═══════════════════════════════════════════════════════════

    async def _try_auto_detect(self, img: Image.Image) -> bool:
        """Возвращает True если определил материал."""
        th = self.theme
        try:
            if not self.clip.is_loaded():
                log(self.S, self.t("auto_detect_loading"),
                    color=th["fg2"], fg2=th["fg2"])
                self.page.update()
                ok = await asyncio.to_thread(
                    self.clip.load,
                    self.paths["clip_vision"],
                    self.paths["clip_text"],
                )
                if not ok:
                    log(self.S, self.t("auto_detect_no_clip"),
                        color=th["warn"], fg2=th["fg2"])
                    return False

            profile, conf, top5 = await asyncio.to_thread(
                self.clip.classify, img
            )
            if not profile:
                log(self.S, self.t("auto_detect_fail"),
                    color=th["warn"], fg2=th["fg2"])
                return False

            old_profile = self.S["profile"]
            self.S["profile"] = profile
            for cat_key, cat in PROFILE_CATEGORIES.items():
                if profile in cat["items"]:
                    self.S["profile_category"] = cat_key
                    break

            label = TEXTURE_PROFILES[profile][self.S["lang"]]
            log(self.S, f"🤖 {self.t('auto_detect_winner')} "
                        f"{label} ({conf * 100:.1f}%)",
                color=th["success"], fg2=th["fg2"])
            return True
        except Exception as ex:
            log(self.S, f"   ⚠ Auto-detect: {ex}",
                color=th["warn"], fg2=th["fg2"])
            return False

    async def do_auto_detect_material(self, e):
        """CLIP-определение материала текстуры (кнопкой)."""
        th = self.theme
        if self.S["original"] is None:
            log(self.S, self.t("auto_detect_no_tex"),
                color=th["warn"], fg2=th["fg2"])
            self.page.update()
            return

        try:
            await show_progress(self.S, self.page,
                                self.t("auto_detect_progress"),
                                fg2=th["fg2"])
            await asyncio.sleep(0.05)

            if not self.clip.is_loaded():
                log(self.S, self.t("auto_detect_loading"),
                    color=th["fg2"], fg2=th["fg2"])
                self.page.update()
                ok = await asyncio.to_thread(
                    self.clip.load,
                    self.paths["clip_vision"],
                    self.paths["clip_text"],
                )
                if not ok:
                    log(self.S, self.t("auto_detect_no_clip"),
                        color=th["warn"], fg2=th["fg2"])
                    await hide_progress(self.S, self.page)
                    return

            profile, conf, top5 = await asyncio.to_thread(
                self.clip.classify, self.S["original"]
            )
            if not profile:
                log(self.S, self.t("auto_detect_fail"),
                    color=th["warn"], fg2=th["fg2"])
                await hide_progress(self.S, self.page)
                return

            old_profile = self.S["profile"]
            self.S["profile"] = profile
            for cat_key, cat in PROFILE_CATEGORIES.items():
                if profile in cat["items"]:
                    self.S["profile_category"] = cat_key
                    break

            log(self.S, "", fg2=th["fg2"])
            log(self.S, "━━━━━━━━━━━━━━━━━━━━━━", color=th["fg3"],
                fg2=th["fg2"])
            log(self.S, self.t("auto_detect_result"), color=th["fg"],
                fg2=th["fg2"])
            log(self.S, f"{self.t('auto_detect_winner')} "
                        f"{TEXTURE_PROFILES[profile][self.S['lang']]} "
                        f"({conf * 100:.1f}%)",
                color=th["success"], fg2=th["fg2"])
            log(self.S, self.t("auto_detect_top5"), color=th["fg2"],
                fg2=th["fg2"])
            for i, (key, c) in enumerate(top5[:5], 1):
                log(self.S, f"      {i}. "
                            f"{TEXTURE_PROFILES[key][self.S['lang']]}: "
                            f"{c * 100:.2f}%",
                    color=th["fg2"], fg2=th["fg2"])

            if old_profile != profile:
                log(self.S, f"{self.t('auto_detect_changed')} "
                            f"{TEXTURE_PROFILES[old_profile][self.S['lang']]} → "
                            f"{TEXTURE_PROFILES[profile][self.S['lang']]}",
                    color=th["fg2"], fg2=th["fg2"])
            else:
                log(self.S, self.t("auto_detect_same"),
                    color=th["fg2"], fg2=th["fg2"])

            self.on_persist()
            await hide_progress(self.S, self.page)
            self.on_rebuild()
        except Exception as ex:
            await hide_progress(self.S, self.page)
            log(self.S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    # ═══════════════════════════════════════════════════════════
    #  SOAP / SATURATION / SEAMLESS / TILING / PREVIEW
    # ═══════════════════════════════════════════════════════════

    async def do_remove_soap(self, e):
        th = self.theme
        source = self.S["corrected"] if self.S["corrected"] is not None \
            else self.S["original"]
        if source is None:
            log(self.S, self.t("auto_detect_no_tex"),
                color=th["warn"], fg2=th["fg2"])
            self.page.update()
            return
        try:
            await show_progress(self.S, self.page,
                                self.t("soap_fix_progress"),
                                fg2=th["fg2"])
            await asyncio.sleep(0.1)

            result = await asyncio.to_thread(
                apply_soap, source, self.S["soap_fix_strength"]
            )
            self.S["corrected"] = result
            self.S["last_op"] = "soap_fix"
            self.S["show_original"] = False
            self._update_preview_display()
            log(self.S, self.t("soap_fix_done"), color=th["success"],
                fg2=th["fg2"])
            self._enable_post_actions()
            await hide_progress(self.S, self.page)
            self.on_rebuild()
        except Exception as ex:
            await hide_progress(self.S, self.page)
            log(self.S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def do_boost_saturation(self, e):
        th = self.theme
        source = self.S["corrected"] if self.S["corrected"] is not None \
            else self.S["original"]
        if source is None:
            log(self.S, self.t("auto_detect_no_tex"),
                color=th["warn"], fg2=th["fg2"])
            self.page.update()
            return
        try:
            await show_progress(self.S, self.page, self.t("sat_progress"),
                                fg2=th["fg2"])
            await asyncio.sleep(0.1)

            result = await asyncio.to_thread(
                apply_saturation, source, self.S["saturation_boost"]
            )
            self.S["corrected"] = result
            self.S["last_op"] = "saturation"
            self.S["show_original"] = False
            self._update_preview_display()
            log(self.S, self.t("sat_done"), color=th["success"],
                fg2=th["fg2"])
            await hide_progress(self.S, self.page)
            self.on_rebuild()
        except Exception as ex:
            await hide_progress(self.S, self.page)
            log(self.S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def do_make_seamless(self, e):
        th = self.theme
        source = self.S["corrected"] if self.S["corrected"] is not None \
            else self.S["original"]
        if source is None:
            log(self.S, self.t("auto_detect_no_tex"),
                color=th["warn"], fg2=th["fg2"])
            self.page.update()
            return
        try:
            await show_progress(self.S, self.page,
                                self.t("seamless_progress"),
                                fg2=th["fg2"])
            await asyncio.sleep(0.1)

            result = await asyncio.to_thread(
                apply_seamless, source, self.S.get("seamless_hipass", True)
            )
            self.S["corrected"] = result
            self.S["last_op"] = "seamless"
            self.S["show_original"] = False
            self._update_preview_display()
            log(self.S, self.t("seamless_done"), color=th["success"],
                fg2=th["fg2"])
            await hide_progress(self.S, self.page)
            self.on_rebuild()
        except Exception as ex:
            await hide_progress(self.S, self.page)
            log(self.S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    def toggle_tiling(self, e):
        self.S["tiling_mode"] = not self.S["tiling_mode"]
        self.on_persist()
        img = None
        if self.S["show_original"] and self.S["original"] is not None:
            img = self.S["original"]
        elif self.S["corrected"] is not None:
            img = self.S["corrected"]
        elif self.S["original"] is not None:
            img = self.S["original"]
        if img is not None:
            if self.S["tiling_mode"]:
                tiled = make_tiled(img, tiles=3, max_size=1800)
                self._set_preview(tiled)
            else:
                self._set_preview(img)
        # Обновить текст кнопки без rebuild
        self._refresh_tiling_btn()
        self.page.update()

    def _refresh_tiling_btn(self):
        """Меняет текст кнопки Tiling без rebuild."""
        btn = self.buttons.get("tiling")
        if btn is None:
            return
        btn.set_label(
            self.t("tiling_btn") if not self.S["tiling_mode"]
            else self.t("tiling_btn_off")
        )

    def toggle_preview(self, e):
        if self.S["original"] is None:
            return
        self.S["show_original"] = not self.S["show_original"]
        self._update_preview_display()
        if self.buttons.get("preview_toggle"):
            self.buttons["preview_toggle"].set_label(
                self.t("preview_toggle_result")
                if self.S["show_original"]
                else self.t("preview_toggle_orig")
            )
        self.page.update()

    # ═══════════════════════════════════════════════════════════
    #  FALLBACK-ДИАЛОГ
    # ═══════════════════════════════════════════════════════════

    def _show_fallback_dialog(self, current_img, stats):
        th = self.theme
        dialog_ref = {"dlg": None}

        async def apply_fb(e=None):
            try:
                dialog_ref["dlg"].open = False
                self.page.update()

                self.S["progress_text"].value = self.t("fb_dialog_progress")
                self.S["progress_text"].visible = True
                self.S["progress_bar"].visible = True
                for b in self.buttons.values():
                    b.disabled = True
                self.page.update()
                await asyncio.sleep(0.05)

                result = await asyncio.to_thread(
                    apply_fallback, current_img, self.S["profile"]
                )
                result = await asyncio.to_thread(
                    apply_soap, result, self.S["soap_fix_strength"]
                )
                self.S["corrected"] = result
                self.S["last_op"] = "corrected"
                self.S["show_original"] = False
                self._update_preview_display()
                log(self.S, "", fg2=th["fg2"])
                log(self.S, self.t("fb_dialog_applied"),
                    color=th["success"], fg2=th["fg2"])
                self.run_check(result, False)
                self.page.update()
            except Exception as ex:
                log(self.S, f"❌ {self.t('fb_dialog_err')} {ex}",
                    color=th["danger"], fg2=th["fg2"])
            finally:
                self.S["progress_bar"].visible = False
                self.S["progress_text"].visible = False
                self.on_rebuild()

        async def keep_ai(e=None):
            dialog_ref["dlg"].open = False
            self.page.update()
            log(self.S, self.t("fb_dialog_kept"),
                color=th["fg2"], fg2=th["fg2"])
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(self.t("fb_dialog_title"),
                          color=th["fg"], size=14),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(self.t("fb_dialog_text"),
                            color=th["fg2"], size=12, font_family=FONT),
                    ft.Container(height=4),
                    ft.Text(f"  {self.t('fb_dialog_dark')} "
                            f"{stats['dark_pct']:.2f}%",
                            color=th["danger"] if stats["dark_pct"] > 5
                            else th["success"],
                            size=12, font_family=FONT_MONO),
                    ft.Text(f"  {self.t('fb_dialog_light')} "
                            f"{stats['light_pct']:.2f}%",
                            color=th["danger"] if stats["light_pct"] > 5
                            else th["success"],
                            size=12, font_family=FONT_MONO),
                    ft.Container(height=6),
                    ft.Text(self.t("fb_dialog_question"),
                            color=th["fg"], size=12, font_family=FONT),
                ], spacing=2, tight=True),
                width=380, height=140,
            ),
            actions=[
                ft.TextButton(self.t("fb_dialog_keep_ai"),
                              on_click=keep_ai),
                ft.TextButton(self.t("fb_dialog_apply"),
                              on_click=apply_fb),
            ],
            inset_padding=ft.Padding.symmetric(horizontal=80, vertical=120),
            bgcolor=th["panel"],
        )
        dialog_ref["dlg"] = dlg
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()