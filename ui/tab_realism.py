"""
ui/tab_realism.py — вкладка Realism (процедурный фотореализм).

Класс RealismTab: пресеты (soft/medium/hard), слайдеры grain/highpass/variation,
кнопка Apply, кнопка Load, кнопка Save.
"""

import os
import asyncio
import flet as ft

from core.image_ops import apply_realism
from core.io import save_16bit_or_8bit, pil_to_b64, safe_open_rgb
from core.state import remember_folder, init_dir
from ui.theme import make_btn, section_title, divider
from ui.helpers import log, show_realism_progress, hide_realism_progress

FONT = "Segoe UI"

REALISM_PRESETS = {
    "soft":   {"grain": 0.08, "highpass": 0.20, "variation": 0.10},
    "medium": {"grain": 0.15, "highpass": 0.30, "variation": 0.20},
    "hard":   {"grain": 0.45, "highpass": 0.75, "variation": 0.55},
}


class RealismTab:
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
        self.save_btn = None

    def build(self) -> ft.Container:
        th = self.theme
        S = self.S

        self.preview_image = ft.Image(src="", visible=False,
                                        fit=ft.BoxFit.CONTAIN)
        self.preview_hint = ft.Text(self.t("realism_preview_hint"),
                                     color=th["fg3"], size=14,
                                     font_family=FONT)

        preview_content = ft.Stack([
            ft.Container(content=self.preview_hint,
                          alignment=ft.Alignment.CENTER, expand=True),
            ft.Container(content=self.preview_image,
                          alignment=ft.Alignment.CENTER, expand=True),
        ], expand=True)

        preview_box = ft.Container(
            content=ft.InteractiveViewer(content=preview_content,
                                           min_scale=0.5, max_scale=8.0,
                                           expand=True),
            bgcolor=th["card"], border_radius=12, padding=10, expand=True,
        )

        # Восстановление превью если результат уже есть
        if S.get("realism_result") is not None:
            self.preview_image.src = (
                f"data:image/png;base64,{pil_to_b64(S['realism_result'])}"
            )
            self.preview_image.visible = True
            self.preview_hint.visible = False
        elif S.get("realism_source") is not None:
            self.preview_image.src = (
                f"data:image/png;base64,{pil_to_b64(S['realism_source'])}"
            )
            self.preview_image.visible = True
            self.preview_hint.visible = False

        # Кнопка Save — disabled если результата нет
        self.save_btn = make_btn(
            self.t("save"), self.realism_save, th["save"],
            icon="save",
            disabled=(S.get("realism_result") is None),
            size=13, vertical=11, horizontal=16,
        )
        S["realism_save_btn"] = self.save_btn

        toolbar = ft.Row([
            make_btn(self.t("load"), self.realism_load, th["accent"],
                     icon="folder-open",
                     size=13, vertical=11, horizontal=16),
            ft.Container(expand=True),
            self.save_btn,
        ], spacing=6)

        # Правая панель
        right_panel = self._build_right_panel()

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        toolbar,
                        ft.Container(height=6),
                        S["realism_progress_bar"],
                        S["realism_progress_text"],
                        ft.Container(height=6),
                        ft.Container(content=preview_box, expand=True),
                    ], spacing=0, expand=True),
                    expand=True,
                ),
                right_panel,
            ], spacing=12, expand=True),
            expand=True, visible=True,
        )

    def _build_right_panel(self) -> ft.Container:
        th = self.theme
        active = self._active_preset()

        def _preset_btn(name, label_key):
            is_active = (active == name)
            return ft.Container(
                content=ft.Text(self.t(label_key),
                                 color="#ffffff" if is_active else th["fg2"],
                                 size=12, font_family=FONT,
                                 weight=ft.FontWeight.W_600,
                                 text_align=ft.TextAlign.CENTER),
                bgcolor=th["accent"] if is_active else th["card"],
                border_radius=8,
                padding=ft.Padding.symmetric(vertical=10, horizontal=6),
                expand=True, ink=not is_active,
                on_click=lambda e, n=name: self._apply_preset(n),
            )

        return ft.Container(
            content=ft.Column([
                section_title(self.t("realism_presets"), th["fg3"]),
                ft.Container(height=6),
                ft.Row([
                    _preset_btn("soft",   "realism_preset_soft"),
                    _preset_btn("medium", "realism_preset_medium"),
                    _preset_btn("hard",   "realism_preset_hard"),
                ], spacing=4),
                ft.Container(height=14),
                divider(th["fg3"]),
                ft.Container(height=10),
                section_title(self.t("realism_params"), th["fg3"]),
                ft.Container(height=8),
                self._slider(self.t("realism_grain"), "realism_grain"),
                self._slider(self.t("realism_highpass"), "realism_highpass"),
                self._slider(self.t("realism_variation"), "realism_variation"),
                ft.Container(height=14),
                make_btn(self.t("realism_apply"), self.realism_apply,
                         th["success"], icon="clapperboard",
                         size=13, vertical=12, horizontal=16),
            ], spacing=6, scroll=ft.ScrollMode.AUTO),
            bgcolor=th["panel"], border_radius=12,
            padding=16, width=320,
        )

    def _slider(self, label, key):
        th = self.theme
        return ft.Column([
            ft.Text(label, color=th["fg2"], size=11, font_family=FONT),
            ft.Slider(min=0.0, max=1.0, divisions=20,
                      value=self.S.get(key, 0.2), label="{value}",
                      active_color=th["accent"],
                      inactive_color=th["input"],
                      on_change=lambda e, k=key: self.S.update({k: e.control.value})),
        ], spacing=2)

    def _active_preset(self):
        for name, p in REALISM_PRESETS.items():
            if (abs(self.S["realism_grain"] - p["grain"]) < 0.001
                    and abs(self.S["realism_highpass"] - p["highpass"]) < 0.001
                    and abs(self.S["realism_variation"] - p["variation"]) < 0.001):
                return name
        return None

    def _apply_preset(self, name):
        p = REALISM_PRESETS.get(name)
        if not p:
            return
        self.S["realism_grain"] = p["grain"]
        self.S["realism_highpass"] = p["highpass"]
        self.S["realism_variation"] = p["variation"]
        label_key = {
            "soft":   "realism_preset_soft",
            "medium": "realism_preset_medium",
            "hard":   "realism_preset_hard",
        }.get(name, name)
        log(self.S, f"🎞 {self.t('realism_preset_log')}: {self.t(label_key)}",
            color=self.theme["fg2"], fg2=self.theme["fg2"])
        self.on_rebuild()

    # ─── Действия ───

    async def realism_load(self, e=None):
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
            self.S["realism_source"] = img
            self.S["realism_result"] = None
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

    async def realism_apply(self, e=None):
        th = self.theme
        if self.S.get("realism_source") is None:
            log(self.S, "   ⚠ Сначала загрузи текстуру",
                color=th["warn"], fg2=th["fg2"])
            self.page.update()
            return
        try:
            await show_realism_progress(self.S, self.page,
                                         self.t("realism_progress"))
            await asyncio.sleep(0.05)
            result = await asyncio.to_thread(
                apply_realism, self.S["realism_source"],
                self.S["realism_grain"],
                self.S["realism_highpass"],
                self.S["realism_variation"],
            )
            self.S["realism_result"] = result
            log(self.S, self.t("realism_done"),
                color=th["success"], fg2=th["fg2"])
            await hide_realism_progress(self.S, self.page)
            self.on_rebuild()
        except Exception as ex:
            await hide_realism_progress(self.S, self.page)
            log(self.S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()

    async def realism_save(self, e=None):
        th = self.theme
        if self.S.get("realism_result") is None:
            return
        try:
            path = await self.picker.save_file(
                dialog_title=self.t("dialog_save_title"),
                file_name="realism.png",
                allowed_extensions=["png", "jpg", "tif"],
                initial_directory=init_dir(self.S),
            )
            if not path:
                return
            await asyncio.to_thread(
                save_16bit_or_8bit, self.S["realism_result"], str(path), 16)
            remember_folder(self.S, str(path))
            log(self.S, f"{self.t('log_saved')} {os.path.basename(str(path))}",
                color=th["success"], fg2=th["fg2"])
            self.page.update()
        except Exception as ex:
            log(self.S, f"❌ {self.t('err')}: {ex}",
                color=th["danger"], fg2=th["fg2"])
            self.page.update()