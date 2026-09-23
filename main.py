import flet as ft
import numpy as np
from PIL import Image
import os
import sys
import base64
import io
import asyncio
import gc
import cv2
import subprocess
import tempfile
import shutil
from pbr_generator import (
    generate_all_pbr, remove_soap_adaptive,
    boost_saturation, make_seamless,
    to_preview_pil, save_pbr_map,
)
from config import (
    WALLETS, THEME_DARK, THEME_LIGHT,
    TEXTURE_PROFILES, PBR_PRESETS, PROFILE_CATEGORIES,
    AI_MODELS, DEFAULT_AI_MODEL, LUTWITHBGRID_MODEL_NAME,
)
from image_processor import fallback_correct, ai_correct, lut_correct
from clip_model import CLIPMaterialClassifier
from realism import add_realism
from translations import T
from settings import load_settings, save_settings
from engine_export import (
    pack_for_engine, save_engine_map,
    load_pbr_folder, engine_folder_suffix,
)


def _detect_system_lang():
    """Определяет язык системы через Windows API. ru → 'ru', остальное → 'en'."""
    try:
        import ctypes
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        primary = lang_id & 0x03FF
        if primary == 0x19:
            return "ru"
        return "en"
    except Exception:
        return "en"


def main(page: ft.Page):
    # ═══ Загрузка пользовательских настроек ═══
    USER_SETTINGS = load_settings()

    # ═══ Состояние ═══
    S = {
        "image_path": None,
        "original": None,
        "file_info_label": None,
        "corrected": None,
        "profile": USER_SETTINGS.get("profile", "metal"),
        "profile_category": USER_SETTINGS.get("profile_category", "metal"),
        "correction_mode": USER_SETTINGS.get("correction_mode", "ai"),
        "ai_model": USER_SETTINGS.get("ai_model", DEFAULT_AI_MODEL),
        "soap_fix_strength": USER_SETTINGS.get("soap_fix_strength", 1.0),
        "saturation_boost": USER_SETTINGS.get("saturation_boost", 1.15),
        "pbr_bit_depth": USER_SETTINGS.get("pbr_bit_depth", 16),
        "last_op": None,
        "show_original": False,
        "lang": USER_SETTINGS.get("lang") or _detect_system_lang(),
        "theme": USER_SETTINGS.get("theme", "dark"),
        "ui_mode": USER_SETTINGS.get("ui_mode", "simple"),
        "log_lines": [],
        "stats_lines": [],
        "pbr_source": None,
        "pbr_source_path": None,
        "pbr_result": None,
        "pbr_current_map": USER_SETTINGS.get("pbr_current_map", "albedo"),
        "pbr_metallic": USER_SETTINGS.get("pbr_metallic", "black"),
        "pbr_metallic_custom": None,
        "pbr_metallic_custom_path": None,
        "pbr_roughness": USER_SETTINGS.get("pbr_roughness", "procedural"),
        "pbr_roughness_custom": None,
        "pbr_roughness_custom_path": None,
        "pbr_sliders": {},
        "pbr_preview": None,
        "pbr_preview_hint": None,
        "pbr_map_buttons": {},
        "pbr_batch_results": {},
        "pbr_batch_selected": None,
        "pbr_batch_index": 0,
        "pbr_batch_label": None,
        "pbr_batch_nav_panel": None,
        "batch_files": [],
        "batch_threads": USER_SETTINGS.get("batch_threads", 3),
        "compress_files": [],
        "active_tab": "single",
        "tiling_mode": USER_SETTINGS.get("tiling_mode", False),
        "seamless_hipass": USER_SETTINGS.get("seamless_hipass", True),
        "realism_grain": USER_SETTINGS.get("realism_grain", 0.15),
        "realism_highpass": USER_SETTINGS.get("realism_highpass", 0.30),
        "realism_variation": USER_SETTINGS.get("realism_variation", 0.20),
        "realism_source": None,
        "viewer_tile_x": 4,
        "viewer_tile_y": 3,
        "realism_result": None,
        "compress_original": None,
        "compress_corrected": None,
        "compress_path": None,
        "last_folder": USER_SETTINGS.get("last_folder", ""),
        "export_source": None,
        "export_source_label": None,
        "export_packed": None,
        "export_normal_out": None,
       "export_engine": USER_SETTINGS.get("export_engine", "unity_hdrp"),
        "export_normal_format": USER_SETTINGS.get("export_normal_format", "opengl"),
        "export_detail_mode": USER_SETTINGS.get("export_detail_mode", "edge"),
        "export_custom_detail": None,
        "export_bit_depth": USER_SETTINGS.get("export_bit_depth", 8),
        "export_preview_channel": "rgb",
        "first_launch_done": USER_SETTINGS.get("first_launch_done", False),
    }

# Валидация: profile должен быть в profile_category
    _cat_items = PROFILE_CATEGORIES.get(S["profile_category"], {}).get("items", [])
    if S["profile"] not in _cat_items:
        for _ck, _cat in PROFILE_CATEGORIES.items():
            if S["profile"] in _cat["items"]:
                S["profile_category"] = _ck
                break
        else:
            S["profile"] = "metal"
            S["profile_category"] = "metal"

    # ═══ Цвета темы ═══
    _theme = THEME_DARK if S["theme"] == "dark" else THEME_LIGHT
    BG = _theme["bg"]
    PANEL = _theme["panel"]
    CARD = _theme["card"]
    INPUT = _theme["input"]
    FG = _theme["fg"]
    FG2 = _theme["fg2"]
    FG3 = _theme["fg3"]
    ACCENT = _theme["accent"]
    SUCCESS = _theme["success"]
    DANGER = _theme["danger"]
    WARN = _theme["warn"]
    FONT = "Segoe UI"
    PBR_COLOR = SUCCESS
    BATCH_COLOR = WARN
    COMPRESS_COLOR = "#1565c0" if S["theme"] == "dark" else "#3d6fb8"
    SAVE_COLOR = "#6a4a9f"
    RESET_COLOR = "#555555" if S["theme"] == "dark" else "#9aa0a6"
    ON_ACCENT = "#ffffff"

    cv2.setNumThreads(os.cpu_count() or 4)
    page.title = "Albedolizer v1.7.3-beta"

    # ═══ FilePicker — один на всё приложение ═══
    picker = ft.FilePicker()
    page.theme_mode = ft.ThemeMode.DARK if S["theme"] == "dark" else ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    page.window.width = 1280
    page.window.height = 820
    page.window.opacity = 1.0
    page.bgcolor = BG

    if getattr(sys, 'frozen', False):
        _meipass = getattr(sys, '_MEIPASS', None)
        _exe_dir = os.path.dirname(sys.executable)
        _icon_dir = _meipass if (_meipass and os.path.exists(os.path.join(_meipass, "icon.ico"))) else _exe_dir
        _icon_path = os.path.join(_icon_dir, "icon.ico")
    else:
        _icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    if os.path.exists(_icon_path):
        page.window.icon = _icon_path

    if getattr(sys, 'frozen', False):
        _meipass = getattr(sys, '_MEIPASS', None)
        _exe_dir = os.path.dirname(sys.executable)
        _base_dir = _meipass if (_meipass and os.path.exists(os.path.join(_meipass, "manual.html"))) else _exe_dir
    else:
        _base_dir = os.path.dirname(os.path.abspath(__file__))

    AUTOLEVELS_EXE = os.path.join(_base_dir, "autolevels.exe")
    AUTOLEVELS_MODEL = os.path.join(_base_dir, "free_xcittiny_wa14.onnx")
    CLIP_VISION_PATH = os.path.join(_base_dir, "clip_vision_int8.onnx")
    CLIP_TEXT_PATH = os.path.join(_base_dir, "clip_text_encoder.onnx")

    def t(key):
        return T[S["lang"]].get(key, key)

    def profile_label(key):
        return TEXTURE_PROFILES[key][S["lang"]]

    def pil_to_b64(data, max_size=900):
        if isinstance(data, np.ndarray):
            data = to_preview_pil(data)
        p = data.copy()
        if p.mode not in ("RGB", "L"):
            p = p.convert("RGB")
        p.thumbnail((max_size, max_size), Image.LANCZOS)
        buf = io.BytesIO()
        p.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    def _init_dir():
        """Возвращает последнюю открытую папку или None."""
        lf = S.get("last_folder") or ""
        if lf and os.path.isdir(lf):
            return lf
        return None

    def _remember_folder(file_path):
        """Запоминает папку файла и сохраняет в настройки."""
        if not file_path:
            return
        try:
            folder = os.path.dirname(os.path.abspath(file_path))
            if folder and folder != S.get("last_folder"):
                S["last_folder"] = folder
                persist_settings()
        except Exception:
            pass

    def save_16bit_or_8bit(pil_img, path, bit_depth=16):
        """Сохраняет PIL в PNG с выбранной битностью. bit_depth: 8 или 16."""
        if bit_depth == 16:
            arr = np.array(pil_img.convert("RGB"))
            arr16 = (arr.astype(np.uint16) * 257)
            bgr = cv2.cvtColor(arr16, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(path), bgr)
        else:
            pil_img.save(str(path))

    def get_luminance(pil):
        arr = np.array(pil.convert("RGB")).astype(np.float32)
        return 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
        
    def update_preview_display():
        """Ставит preview_image.src в зависимости от S["show_original"]."""
        if S["show_original"] and S["original"] is not None:
            img = S["original"]
        elif S["corrected"] is not None:
            img = S["corrected"]
        elif S["original"] is not None:
            img = S["original"]
        else:
            return
        S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(img)}"
        S["preview_image"].visible = True
        
    def update_file_info():
        """Обновляет инфо-плашку файла в Single."""
        lbl = S.get("file_info_label")
        if lbl is None:
            return
        if not S.get("image_path") or S.get("original") is None:
            lbl.visible = False
            return
        try:
            import os as _os
            name = _os.path.basename(S["image_path"])
            w, h = S["original"].size
            mode = S["original"].mode
            try:
                size_bytes = _os.path.getsize(S["image_path"])
                size_str = _fmt_size(size_bytes)
            except Exception:
                size_str = "—"
            lbl.content.value = f"📂 {name}  ·  {w}×{h}  ·  {mode}  ·  {size_str}"
            lbl.visible = True
        except Exception:
            lbl.visible = False
        
    def _fmt_size(b):
        """Байты → человекочитаемо: 1.2 KB / 3.4 MB / 1.5 GB."""
        if b < 1024:
            return f"{b} B"
        if b < 1024 * 1024:
            return f"{b / 1024:.1f} KB"
        if b < 1024 * 1024 * 1024:
            return f"{b / 1024 / 1024:.2f} MB"
        return f"{b / 1024 / 1024 / 1024:.2f} GB"    

    def smart_correct_ai(pil):
        """Обёртка вокруг ai_correct / lut_correct — выбор модели."""
        model_key = S.get("ai_model", "autolevels")
        
        if model_key == "lutwithbgrid":
            onnx_path = os.path.join(_base_dir, LUTWITHBGRID_MODEL_NAME)
            result, ok, err = lut_correct(pil, onnx_path)
            if ok:
                log("   ✅ AI-модель: LUTwithBGrid", SUCCESS)
            else:
                log(f"   ⚠ AI LUTwithBGrid: {err}", WARN)
            return result, ok
        else:
            result, ok, err = ai_correct(pil, AUTOLEVELS_EXE, AUTOLEVELS_MODEL)
            if ok:
                log("   ✅ AI-модель: Autolevels", SUCCESS)
            else:
                log(f"   ⚠ AI Autolevels: {err}", WARN)
            return result, ok

    def smart_correct_fallback(pil, profile_key):
        """Обёртка вокруг image_processor.fallback_correct."""
        return fallback_correct(pil, profile_key)

    # ═══ UI ЭЛЕМЕНТЫ ═══
    S["log_column_bottom"] = ft.ListView(spacing=3, auto_scroll=True, expand=True, padding=4)

    S["stats_column"] = ft.Column([], spacing=4)
    S["preview_image"] = ft.Image(src="", visible=False, fit=ft.BoxFit.CONTAIN)
    S["progress_bar"] = ft.ProgressBar(value=None, visible=False, color=ACCENT,
                                        bgcolor=INPUT, height=4, bar_height=4)
    S["progress_text"] = ft.Text("", color=FG2, size=12, font_family=FONT, visible=False)
    S["pbr_progress_bar"] = ft.ProgressBar(value=None, visible=False, color=PBR_COLOR,
                                             bgcolor=INPUT, height=4, bar_height=4)
    S["pbr_progress_text"] = ft.Text("", color=FG2, size=12, font_family=FONT, visible=False)
    S["batch_progress_bar"] = ft.ProgressBar(value=0, visible=True, color=BATCH_COLOR,
                                               bgcolor=INPUT, height=4, bar_height=4)
    S["batch_progress_text"] = ft.Text("", color=FG2, size=12, font_family=FONT)
    S["compress_progress_bar"] = ft.ProgressBar(value=0, visible=True, color=COMPRESS_COLOR,
                                                  bgcolor=INPUT, height=4, bar_height=4)
    S["compress_progress_text"] = ft.Text("", color=FG2, size=12, font_family=FONT)
    S["realism_progress_bar"] = ft.ProgressBar(value=None, visible=False, color=ACCENT,
                                                bgcolor=INPUT, height=4, bar_height=4)
    S["realism_progress_text"] = ft.Text("", color=FG2, size=12, font_family=FONT, visible=False)
    S["clip"] = CLIPMaterialClassifier()
    S["buttons"] = {}

    def log(text, color=None):
        S["log_lines"].append((text, color or FG2))
        if len(S["log_lines"]) > 200:
            S["log_lines"].pop(0)
        refresh_log()

    def refresh_log():
        lc = S["log_column_bottom"]
        lc.controls.clear()
        for txt, col in S["log_lines"]:
            lc.controls.append(
                ft.Text(txt, color=col, size=13, font_family="Consolas",
                        selectable=True, expand=True)
            )
        prev = S.get("log_collapsed_preview")
        if prev is not None:
            if S["log_lines"]:
                last_txt, last_col = S["log_lines"][-1]
                prev.value = last_txt
                prev.color = last_col
            else:
                prev.value = ""

    def clear_log(e=None):
        S["log_lines"].clear()
        refresh_log()
        page.update()

    def clear_stats():
        S["stats_lines"].clear()
        S["stats_column"].controls.clear()

    def add_stat(label, value, color=None):
        S["stats_lines"].append((label, value, color or FG2))
        S["stats_column"].controls.append(
            ft.Row([
                ft.Text(label, color=FG3, size=13, font_family=FONT, width=95),
                ft.Text(value, color=color or FG2, size=13, font_family="Consolas",
                        weight=ft.FontWeight.W_600),
            ], spacing=8)
        )

    async def show_progress(text="Обработка..."):
        S["progress_text"].value = text
        S["progress_text"].visible = True
        S["progress_bar"].visible = True
        page.update()
        await asyncio.sleep(0.05)
        page.update()

    async def hide_progress():
        S["progress_bar"].visible = False
        S["progress_text"].visible = False
        page.update()
        await asyncio.sleep(0.02)

    async def show_pbr_progress(text="Обработка..."):
        S["pbr_progress_text"].value = text
        S["pbr_progress_text"].visible = True
        S["pbr_progress_bar"].visible = True
        page.update()
        await asyncio.sleep(0.05)
        page.update()

    async def hide_pbr_progress():
        S["pbr_progress_bar"].visible = False
        S["pbr_progress_text"].visible = False
        page.update()
        await asyncio.sleep(0.02)

    async def show_realism_progress(text="Обработка..."):
        S["realism_progress_text"].value = text
        S["realism_progress_text"].visible = True
        S["realism_progress_bar"].visible = True
        page.update()
        await asyncio.sleep(0.05)
        page.update()

    async def hide_realism_progress():
        S["realism_progress_bar"].visible = False
        S["realism_progress_text"].visible = False
        page.update()
        await asyncio.sleep(0.02)

    def update_batch_progress(done, total, text=None):
        pct = int((done / total) * 100) if total > 0 else 0
        S["batch_progress_bar"].value = pct / 100
        if text is not None:
            S["batch_progress_text"].value = text
        else:
            S["batch_progress_text"].value = f"{done} / {total}  ({pct}%)"
        page.update()

    def update_compress_progress(done, total, text=None):
        pct = int((done / total) * 100) if total > 0 else 0
        S["compress_progress_bar"].value = pct / 100
        if text is not None:
            S["compress_progress_text"].value = text
        else:
            S["compress_progress_text"].value = f"{done} / {total}  ({pct}%)"
        page.update()

    def analyze_image(pil):
        lum = get_luminance(pil)
        prof = TEXTURE_PROFILES[S["profile"]]
        dt = prof["dark"]
        lt = prof["light"]
        total = lum.size
        dark_px = int(np.sum(lum < dt))
        light_px = int(np.sum(lum > lt))
        return {
            "min": float(np.min(lum)), "max": float(np.max(lum)),
            "avg": float(np.mean(lum)), "median": float(np.median(lum)),
            "p1": float(np.percentile(lum, 1)),
            "p99": float(np.percentile(lum, 99)),
            "dark_pct": dark_px / total * 100,
            "light_pct": light_px / total * 100,
            "dark_t": dt, "light_t": lt,
            "dark_px": dark_px, "light_px": light_px,
        }, lum

    def run_check(img, show_heatmap=True):
        s, lum = analyze_image(img)
        clear_stats()
        add_stat(t("stat_min"), f"{s['min']:.1f}")
        add_stat(t("stat_max"), f"{s['max']:.1f}")
        add_stat(t("stat_avg"), f"{s['avg']:.1f}")
        add_stat(t("stat_median"), f"{s['median']:.1f}")
        add_stat(t("stat_p1"), f"{s['p1']:.1f}")
        add_stat(t("stat_p99"), f"{s['p99']:.1f}")

        log("", FG2)
        log("━━━━━━━━━━━━━━━━━━━━━━", FG3)
        log(t("log_results"), FG)

        noise_t = 5.0
        dark_ok = s["dark_pct"] <= noise_t
        light_ok = s["light_pct"] <= noise_t

        log(f"  {t('log_dark')} (<{s['dark_t']}): {s['dark_pct']:.2f}%",
            SUCCESS if dark_ok else DANGER)
        log(f"  {t('log_light')} (>{s['light_t']}): {s['light_pct']:.2f}%",
            SUCCESS if light_ok else DANGER)

        fix_btn = S["buttons"].get("fix")
        if dark_ok and light_ok:
            log(t("log_pass"), SUCCESS)
            if fix_btn:
                fix_btn.disabled = True
        else:
            log(t("log_fail"), DANGER)
            if fix_btn:
                fix_btn.disabled = False

        if show_heatmap:
            arr = np.array(img).copy()
            arr[lum < s["dark_t"]] = [255, 0, 0]
            arr[lum > s["light_t"]] = [0, 100, 255]
            heatmap = Image.fromarray(arr.astype(np.uint8))
            S["show_original"] = False
            S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(heatmap)}"
            S["preview_image"].visible = True
            if S["buttons"].get("preview_toggle"):
                S["buttons"]["preview_toggle"].content.value = t("preview_toggle_orig")

    async def do_check(e):
        if S["original"] is None:
            return
        await show_progress(t("progress_check"))
        await asyncio.sleep(0.1)
        S["show_original"] = False
        img = S["corrected"] if S["corrected"] else S["original"]
        run_check(img, True)
        page.update()
        await asyncio.sleep(0.1)
        await hide_progress()

    async def do_auto_correct(e):
        if S["original"] is None:
            return
        try:
            await show_progress(t("progress_fix"))
            await asyncio.sleep(0.15)

            if S["correction_mode"] == "math":
                log("   → Режим: ∑ математическая коррекция", FG2)
                result = await asyncio.to_thread(
                    smart_correct_fallback, S["original"], S["profile"]
                )
                if S["soap_fix_strength"] > 0:
                    result = await asyncio.to_thread(
                        remove_soap_adaptive, result, S["soap_fix_strength"]
                    )
                S["corrected"] = result
                S["last_op"] = "corrected"
                S["show_original"] = False
                update_preview_display()
                log("", FG2)
                log(t("log_fix_done"), SUCCESS)

                await asyncio.sleep(0.1)
                run_check(result, False)
                page.update()

                if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
                if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = False
                if S["buttons"].get("preview_toggle"): S["buttons"]["preview_toggle"].disabled = False
                page.update()

                await asyncio.sleep(0.1)
                await hide_progress()
                return

            import time as _time
            _t0 = _time.time()
            ai_result, ai_ok = await asyncio.to_thread(
                smart_correct_ai, S["original"]
            )
            _dt = _time.time() - _t0
            log(f"   ⏱ AI-коррекция: {_dt:.2f} сек", FG2)

            if ai_ok and ai_result is not None:
                S["corrected"] = ai_result
                S["last_op"] = "corrected"
                S["show_original"] = False
                update_preview_display()
                log("", FG2)
                log(t("log_fix_done"), SUCCESS)

                await asyncio.sleep(0.1)
                run_check(ai_result, False)
                page.update()

                s, _ = analyze_image(ai_result)
                noise_t = 5.0
                ok = (s["dark_pct"] <= noise_t) and (s["light_pct"] <= noise_t)

                if not ok:
                    log("   ⚠ Результат AI не прошёл проверку", WARN)
                    show_fallback_dialog(ai_result, s)

                if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
                if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = False
                if S["buttons"].get("preview_toggle"): S["buttons"]["preview_toggle"].disabled = False
                page.update()
            else:
                log("   → AI недоступен. Применяется fallback.", WARN)
                result = smart_correct_fallback(S["original"], S["profile"])
                if S["soap_fix_strength"] > 0:
                    result = await asyncio.to_thread(
                        remove_soap_adaptive, result, S["soap_fix_strength"]
                    )
                S["corrected"] = result
                S["last_op"] = "corrected"
                S["show_original"] = False
                update_preview_display()
                log("", FG2)
                log(t("log_fix_done"), SUCCESS)

                await asyncio.sleep(0.1)
                run_check(result, False)
                page.update()

                if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
                if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = False
                if S["buttons"].get("preview_toggle"): S["buttons"]["preview_toggle"].disabled = False
                page.update()

            await asyncio.sleep(0.1)
            await hide_progress()
        except Exception as ex:
            await hide_progress()
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()
            
            
    async def do_reset(e):
        if S["original"] is None:
            return
        S["corrected"] = None
        S["last_op"] = None
        S["show_original"] = False
        update_preview_display()
        log(t("log_reset"), FG2)
        if S["buttons"].get("save"): S["buttons"]["save"].disabled = True
        if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = True
        if S["buttons"].get("preview_toggle"): S["buttons"]["preview_toggle"].disabled = True
        page.update()

    async def do_auto_detect_material(e):
        """CLIP-определение материала текстуры."""
        if S["original"] is None:
            log("   ⚠ Сначала загрузи текстуру", WARN)
            page.update()
            return

        try:
            await show_progress(t("auto_detect_progress"))
            await asyncio.sleep(0.05)

            if not S["clip"].is_loaded():
                log(t("auto_detect_loading"), FG2)
                page.update()
                ok = await asyncio.to_thread(
                    S["clip"].load, CLIP_VISION_PATH, CLIP_TEXT_PATH
                )
                if not ok:
                    log(t("auto_detect_no_clip"), WARN)
                    await hide_progress()
                    return

            profile, conf, top5 = await asyncio.to_thread(
                S["clip"].classify, S["original"]
            )

            if profile is None:
                log(t("auto_detect_fail"), WARN)
                await hide_progress()
                return

            old_profile = S["profile"]
            S["profile"] = profile

            for cat_key, cat in PROFILE_CATEGORIES.items():
                if profile in cat["items"]:
                    S["profile_category"] = cat_key
                    break

            log("", FG2)
            log("━━━━━━━━━━━━━━━━━━━━━━", FG3)
            log(t("auto_detect_result"), FG)
            log(f"{t('auto_detect_winner')} {profile_label(profile)} ({conf*100:.1f}%)", SUCCESS)
            log(t("auto_detect_top5"), FG2)
            for i, (key, c) in enumerate(top5[:5], 1):
                log(f"      {i}. {profile_label(key)}: {c*100:.2f}%", FG2)

            if old_profile != profile:
                log(f"{t('auto_detect_changed')} {profile_label(old_profile)} → {profile_label(profile)}", FG2)
            else:
                log(t("auto_detect_same"), FG2)

            persist_settings()

            await hide_progress()
            rebuild_ui()
        except Exception as ex:
            await hide_progress()
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def do_simple_process(e):
        """Simple mode: открыть → auto-detect → AI → saturation → результат."""
        try:
            files = await picker.pick_files(
                dialog_title=t("dialog_pick_title"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                initial_directory=_init_dir(),
            )
            if not files or not files[0].path:
                return
            fp = files[0].path
            _remember_folder(fp)

            await show_progress(t("progress_load"))
            await asyncio.sleep(0.1)

            img = Image.open(fp).convert("RGB")
            S["image_path"] = fp
            S["original"] = img
            S["corrected"] = None
            S["last_op"] = None
            S["show_original"] = False
            S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(img)}"
            S["preview_image"].visible = True
            update_file_info()

            log("", FG2)
            log(f"{t('log_loaded')} {os.path.basename(fp)}", SUCCESS)
            page.update()

            # ═══ AUTO-DETECT материала ═══
            S["progress_text"].value = t("auto_detect_progress")
            page.update()
            await asyncio.sleep(0.05)

            detected = False
            try:
                if not S["clip"].is_loaded():
                    log(t("auto_detect_loading"), FG2)
                    page.update()
                    ok = await asyncio.to_thread(
                        S["clip"].load, CLIP_VISION_PATH, CLIP_TEXT_PATH
                    )
                    if not ok:
                        log(t("auto_detect_no_clip"), WARN)

                if S["clip"].is_loaded():
                    profile, conf, top5 = await asyncio.to_thread(
                        S["clip"].classify, img
                    )
                    if profile:
                        old_profile = S["profile"]
                        S["profile"] = profile
                        for cat_key, cat in PROFILE_CATEGORIES.items():
                            if profile in cat["items"]:
                                S["profile_category"] = cat_key
                                break
                        log(f"🤖 {t('auto_detect_winner')} {profile_label(profile)} ({conf*100:.1f}%)", SUCCESS)
                        detected = True
                    else:
                        log(t("auto_detect_fail"), WARN)
            except Exception as ex:
                log(f"   ⚠ Auto-detect: {ex}", WARN)

            if not detected:
                log(f"{t('log_type')} {profile_label(S['profile'])}", FG2)
            else:
                persist_settings()

            page.update()
            await asyncio.sleep(0.1)

            # ═══ AI-коррекция ═══
            S["progress_text"].value = t("progress_fix")
            page.update()
            await asyncio.sleep(0.1)

            ai_result, ai_ok = await asyncio.to_thread(smart_correct_ai, img)

            if ai_ok and ai_result is not None:
                result = ai_result
            else:
                log("   → AI недоступен. Применяется fallback.", WARN)
                result = await asyncio.to_thread(
                    smart_correct_fallback, img, S["profile"]
                )

            result = await asyncio.to_thread(boost_saturation, result, 1.15)

            S["corrected"] = result
            S["last_op"] = "corrected"
            S["show_original"] = False
            update_preview_display()
            log(t("log_fix_done"), SUCCESS)

            if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
            page.update()

            rebuild_ui()

            await asyncio.sleep(0.1)
            await hide_progress()
        except Exception as ex:
            await hide_progress()
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def open_file(e):
        try:
            files = await picker.pick_files(
                dialog_title=t("dialog_pick_title"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                initial_directory=_init_dir(),
            )
            if files and len(files) > 0:
                fp = files[0].path
                if fp:
                    _remember_folder(fp)
                    await show_progress(t("progress_load"))
                    await asyncio.sleep(0.1)

                    img = Image.open(fp).convert("RGB")
                    S["image_path"] = fp
                    S["original"] = img
                    S["corrected"] = None
                    S["last_op"] = None
                    S["show_original"] = False
                    update_preview_display()
                    update_file_info()

                    log("", FG2)
                    log(f"{t('log_loaded')} {os.path.basename(fp)}", SUCCESS)
                    log(f"{t('log_type')} {profile_label(S['profile'])}", FG2)
                    log(t("log_click_check"), FG2)

                    if S["buttons"].get("check"): S["buttons"]["check"].disabled = False
                    if S["buttons"].get("fix"): S["buttons"]["fix"].disabled = True
                    if S["buttons"].get("save"): S["buttons"]["save"].disabled = True
                    if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = True
                    if S["buttons"].get("preview_toggle"): S["buttons"]["preview_toggle"].disabled = True
                    page.update()

                    rebuild_ui()

                    await asyncio.sleep(0.15)
                    await hide_progress()
        except Exception as ex:
            await hide_progress()
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def open_save(e):
        try:
            if S.get("image_path"):
                base = os.path.splitext(os.path.basename(S["image_path"]))[0]
            else:
                base = "albedo"

            if S.get("last_op") == "compressed":
                default_name = f"{base}_compressed.png"
            else:
                default_name = f"{base}_corrected.png"

            path = await picker.save_file(
                dialog_title=t("dialog_save_title"),
                file_name=default_name,
                allowed_extensions=["png", "jpg", "tif"],
                initial_directory=_init_dir(),
            )
            if path and S["corrected"] is not None:
                await asyncio.to_thread(
                    save_16bit_or_8bit, S["corrected"], str(path), 16
                )
                _remember_folder(str(path))
                log(f"{t('log_saved')} {os.path.basename(str(path))}", SUCCESS)
                page.update()
        except Exception as ex:
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    # ═══ СЖАТИЕ ═══
    async def compress_open_file(e):
        try:
            files = await picker.pick_files(
                dialog_title=t("dialog_pick_title"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                initial_directory=_init_dir(),
            )
            if files and len(files) > 0:
                fp = files[0].path
                if fp:
                    _remember_folder(fp)
                    img = Image.open(fp).convert("RGB")
                    S["compress_original"] = img
                    S["compress_path"] = fp
                    S["compress_corrected"] = None
                    S["compress_preview"].src = f"data:image/png;base64,{pil_to_b64(img)}"
                    S["compress_preview"].visible = True
                    if S["compress_preview_hint"]:
                        S["compress_preview_hint"].visible = False
                    log(f"{t('log_loaded')} {os.path.basename(fp)}", SUCCESS)
                    if S["compress_buttons"].get("run"):
                        S["compress_buttons"]["run"].disabled = False
                    if S["compress_buttons"].get("save"):
                        S["compress_buttons"]["save"].disabled = True
                    page.update()
        except Exception as ex:
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def compress_do(e):
        if S["compress_original"] is None:
            return
        try:
            S["compress_progress_text"].value = t("progress_compress")
            S["compress_progress_text"].visible = True
            S["compress_progress_bar"].value = None
            S["compress_progress_bar"].visible = True
            page.update()
            await asyncio.sleep(0.1)

            result = await asyncio.to_thread(
                lambda: S["compress_original"].convert("LAB").convert("RGB")
            )
            S["compress_corrected"] = result
            S["compress_preview"].src = f"data:image/png;base64,{pil_to_b64(result)}"
            log(t("log_compress_done"), SUCCESS)

            if S["compress_buttons"].get("save"):
                S["compress_buttons"]["save"].disabled = False
            page.update()
            await asyncio.sleep(0.15)

            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            page.update()
        except Exception as ex:
            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def compress_save(e):
        if S["compress_corrected"] is None:
            return
        try:
            base = "albedo"
            if S.get("compress_path"):
                base = os.path.splitext(os.path.basename(S["compress_path"]))[0]

            path = await picker.save_file(
                dialog_title=t("dialog_save_title"),
                file_name=f"{base}_compressed.png",
                allowed_extensions=["png", "jpg", "tif"],
                initial_directory=_init_dir(),
            )
            if not path:
                return

            S["compress_progress_text"].value = "💾 Сохранение..."
            S["compress_progress_text"].visible = True
            S["compress_progress_bar"].value = None
            S["compress_progress_bar"].visible = True
            page.update()
            await asyncio.sleep(0.05)

            await asyncio.to_thread(
                save_16bit_or_8bit, S["compress_corrected"], str(path),
                S.get("pbr_bit_depth", 16)
            )
            _remember_folder(str(path))
            log(f"{t('log_saved')} {os.path.basename(str(path))}", SUCCESS)

            try:
                orig_size = os.path.getsize(S["compress_path"]) if S.get("compress_path") and os.path.exists(S["compress_path"]) else 0
                new_size = os.path.getsize(str(path)) if os.path.exists(str(path)) else 0
                if orig_size > 0 and new_size > 0:
                    saved = orig_size - new_size
                    pct = (saved / orig_size) * 100
                    if saved > 0:
                        log(f"   📉 Сжатие: {_fmt_size(orig_size)} → {_fmt_size(new_size)}  (−{_fmt_size(saved)}, −{pct:.1f}%)", SUCCESS)
                    elif saved < 0:
                        log(f"   📈 Файл вырос: {_fmt_size(orig_size)} → {_fmt_size(new_size)}  (+{_fmt_size(-saved)}, +{abs(pct):.1f}%)", WARN)
                    else:
                        log(f"   📊 Размер не изменился: {_fmt_size(orig_size)}", FG2)
            except Exception:
                pass

            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            page.update()
        except Exception as ex:
            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def compress_select_folder(e):
        try:
            folder = await picker.get_directory_path(
                dialog_title=t("batch_select_folder"))
            if not folder:
                return
            exts = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')
            files = [os.path.join(folder, f) for f in os.listdir(folder)
                     if f.lower().endswith(exts)]
            S["compress_files"] = files
            log(f"📁 {t('batch_folder')} {folder}", FG2)
            log(f"   {t('batch_found')} {len(files)}", FG2)
            update_compress_progress(0, len(files),
                                     f"{t('batch_ready')}: {len(files)} {t('batch_files_count')}")
        except Exception as ex:
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def compress_select_files(e):
        try:
            files = await picker.pick_files(
                dialog_title=t("batch_select_files"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                allow_multiple=True,
                initial_directory=_init_dir(),
            )
            if not files:
                return
            if files and files[0].path:
                _remember_folder(files[0].path)
            S["compress_files"] = [f.path for f in files if f.path]
            log(f"📄 {t('batch_selected')} {len(S['compress_files'])}", FG2)
            update_compress_progress(0, len(S["compress_files"]),
                                     f"{t('batch_ready')}: {len(S['compress_files'])} {t('batch_files_count')}")
        except Exception as ex:
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def compress_batch_run(e):
        files = S["compress_files"]
        if not files:
            log(t("batch_no_files"), WARN)
            page.update()
            return

        total = len(files)
        base_dir = os.path.dirname(files[0])
        out_dir = os.path.join(base_dir, "_compressed")
        os.makedirs(out_dir, exist_ok=True)

        log("", FG2)
        log("━━━━━━━━━━━━━━━━━━━━━━", FG3)
        log(f"{t('compress_batch_started')} {total}", FG)
        log(f"   {t('compress_out')} {out_dir}", FG2)
        page.update()

        count = 0
        total_orig = 0
        total_new = 0
        for i, fp in enumerate(files, 1):
            try:
                img = Image.open(fp).convert("RGB")
                result = img.convert("LAB").convert("RGB")
                base = os.path.splitext(os.path.basename(fp))[0]
                out_path = os.path.join(out_dir, f"{base}.png")
                bd = S.get("pbr_bit_depth", 16)
                await asyncio.to_thread(save_16bit_or_8bit, result, out_path, bd)
                img.close()
                count += 1

                try:
                    osz = os.path.getsize(fp)
                    nsz = os.path.getsize(out_path)
                    total_orig += osz
                    total_new += nsz
                    saved = osz - nsz
                    pct = (saved / osz) * 100 if osz > 0 else 0
                    if saved > 0:
                        log(f"  [{i}/{total}] ✓ {os.path.basename(fp)}  −{pct:.1f}%", SUCCESS)
                    elif saved < 0:
                        log(f"  [{i}/{total}] ⚠ {os.path.basename(fp)}  +{abs(pct):.1f}%", WARN)
                    else:
                        log(f"  [{i}/{total}] ✓ {os.path.basename(fp)}", SUCCESS)
                except Exception:
                    log(f"  [{i}/{total}] ✓ {os.path.basename(fp)}", SUCCESS)

                update_compress_progress(i, total)
                if i % 5 == 0:
                    gc.collect()
                await asyncio.sleep(0.01)
            except Exception as ex:
                log(f"  ✗ {os.path.basename(fp)}: {ex}", DANGER)
                update_compress_progress(i, total)

        log(f"✅ {t('batch_processed')} {count} / {total}", SUCCESS)
        if total_orig > 0 and total_new > 0:
            saved = total_orig - total_new
            pct = (saved / total_orig) * 100
            if saved > 0:
                log(f"   📉 Итого: {_fmt_size(total_orig)} → {_fmt_size(total_new)}  (−{_fmt_size(saved)}, −{pct:.1f}%)", SUCCESS)
            elif saved < 0:
                log(f"   📈 Итого файлы выросли: {_fmt_size(total_orig)} → {_fmt_size(total_new)}  (+{_fmt_size(-saved)}, +{abs(pct):.1f}%)", WARN)
            else:
                log(f"   📊 Итого без изменений: {_fmt_size(total_orig)}", FG2)
        log(f"📁 {out_dir}", FG2)
        update_compress_progress(total, total, f"{t('batch_done')}: {count} / {total}")
        S["compress_files"] = []
        page.update()
        
        
        # ═══ SIMPLE MODE COMPRESS ═══
    async def compress_simple_process(e):
        """Simple: открыть файл → LAB → сохранить в _compressed рядом."""
        try:
            files = await picker.pick_files(
                dialog_title=t("dialog_pick_title"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                initial_directory=_init_dir(),
            )
            if not files or not files[0].path:
                return
            fp = files[0].path
            _remember_folder(fp)

            S["compress_progress_text"].value = t("progress_compress")
            S["compress_progress_text"].visible = True
            S["compress_progress_bar"].value = None
            S["compress_progress_bar"].visible = True
            page.update()
            await asyncio.sleep(0.05)

            img = Image.open(fp).convert("RGB")
            result = await asyncio.to_thread(
                lambda: img.convert("LAB").convert("RGB")
            )

            base = os.path.splitext(os.path.basename(fp))[0]
            folder = os.path.dirname(fp)
            out_dir = os.path.join(folder, "_compressed")
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{base}.png")

            bd = S.get("pbr_bit_depth", 16)
            await asyncio.to_thread(save_16bit_or_8bit, result, out_path, bd)
            img.close()

            log(f"🗜 {os.path.basename(fp)}", SUCCESS)

            osz = os.path.getsize(fp)
            nsz = os.path.getsize(out_path)
            saved = osz - nsz
            pct = (saved / osz) * 100 if osz > 0 else 0
            if saved > 0:
                log(f"   📉 {_fmt_size(osz)} → {_fmt_size(nsz)}  (−{_fmt_size(saved)}, −{pct:.1f}%)", SUCCESS)
            elif saved < 0:
                log(f"   📈 {_fmt_size(osz)} → {_fmt_size(nsz)}  (+{_fmt_size(-saved)}, +{abs(pct):.1f}%)", WARN)
            else:
                log(f"   📊 Без изменений: {_fmt_size(osz)}", FG2)
            log(f"📁 {out_dir}", FG2)

            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            page.update()

            show_compress_done_dialog(out_path, osz, nsz, is_batch=False)

        except Exception as ex:
            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def compress_simple_batch(e):
        """Simple: выбрать папку → LAB все → сохранить в _compressed."""
        try:
            folder = await picker.get_directory_path(
                dialog_title=t("batch_select_folder"))
            if not folder:
                return
            if folder and folder != S.get("last_folder"):
                S["last_folder"] = folder
                persist_settings()

            exts = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')
            files = [os.path.join(folder, f) for f in os.listdir(folder)
                     if f.lower().endswith(exts)]
            if not files:
                log(t("batch_no_files"), WARN)
                page.update()
                return

            total = len(files)
            out_dir = os.path.join(folder, "_compressed")
            os.makedirs(out_dir, exist_ok=True)

            log("", FG2)
            log("━━━━━━━━━━━━━━━━━━━━━━", FG3)
            log(f"{t('compress_batch_started')} {total}", FG)
            log(f"   {t('compress_out')} {out_dir}", FG2)

            S["compress_progress_bar"].value = 0
            S["compress_progress_bar"].visible = True
            S["compress_progress_text"].visible = True
            page.update()

            count = 0
            total_orig = 0
            total_new = 0
            for i, fp in enumerate(files, 1):
                try:
                    img = Image.open(fp).convert("RGB")
                    result = img.convert("LAB").convert("RGB")
                    base = os.path.splitext(os.path.basename(fp))[0]
                    out_path = os.path.join(out_dir, f"{base}.png")
                    bd = S.get("pbr_bit_depth", 16)
                    await asyncio.to_thread(save_16bit_or_8bit, result, out_path, bd)
                    img.close()
                    count += 1

                    try:
                        osz = os.path.getsize(fp)
                        nsz = os.path.getsize(out_path)
                        total_orig += osz
                        total_new += nsz
                        saved = osz - nsz
                        pct = (saved / osz) * 100 if osz > 0 else 0
                        if saved > 0:
                            log(f"  [{i}/{total}] ✓ {os.path.basename(fp)}  −{pct:.1f}%", SUCCESS)
                        elif saved < 0:
                            log(f"  [{i}/{total}] ⚠ {os.path.basename(fp)}  +{abs(pct):.1f}%", WARN)
                        else:
                            log(f"  [{i}/{total}] ✓ {os.path.basename(fp)}", SUCCESS)
                    except Exception:
                        log(f"  [{i}/{total}] ✓ {os.path.basename(fp)}", SUCCESS)

                    S["compress_progress_bar"].value = i / total
                    S["compress_progress_text"].value = f"{i} / {total}  ({int(i / total * 100)}%)"
                    page.update()

                    if i % 5 == 0:
                        gc.collect()
                    await asyncio.sleep(0.01)
                except Exception as ex:
                    log(f"  ✗ {os.path.basename(fp)}: {ex}", DANGER)

            log(f"✅ {t('batch_processed')} {count} / {total}", SUCCESS)
            if total_orig > 0 and total_new > 0:
                saved = total_orig - total_new
                pct = (saved / total_orig) * 100
                if saved > 0:
                    log(f"   📉 Итого: {_fmt_size(total_orig)} → {_fmt_size(total_new)}  (−{_fmt_size(saved)}, −{pct:.1f}%)", SUCCESS)
                elif saved < 0:
                    log(f"   📈 Итого файлы выросли: {_fmt_size(total_orig)} → {_fmt_size(total_new)}  (+{_fmt_size(-saved)}, +{abs(pct):.1f}%)", WARN)
            log(f"📁 {out_dir}", FG2)

            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            page.update()

            if count > 0 and total_orig > 0 and total_new > 0:
                show_compress_done_dialog(out_dir, total_orig, total_new,
                                          is_batch=True, count=count, total=total)

        except Exception as ex:
            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()
            
    def show_compress_done_dialog(out_path, orig_size, new_size,
                                   is_batch=False, count=0, total=0):
        """Диалог 'Готово' с размерами и кнопкой открыть папку."""
        saved = orig_size - new_size
        pct = (saved / orig_size) * 100 if orig_size > 0 else 0

        if saved > 0:
            size_line = f"{_fmt_size(orig_size)} → {_fmt_size(new_size)}  (−{_fmt_size(saved)}, −{pct:.1f}%)"
            size_color = SUCCESS
        elif saved < 0:
            size_line = f"{_fmt_size(orig_size)} → {_fmt_size(new_size)}  (+{_fmt_size(-saved)}, +{abs(pct):.1f}%)"
            size_color = WARN
        else:
            size_line = f"{_fmt_size(orig_size)}  ({t('compress_done_same')})"
            size_color = FG2

        folder = os.path.dirname(out_path) if os.path.isfile(out_path) else out_path

        def _open_folder(e=None):
            try:
                os.startfile(folder)
            except Exception as ex:
                log(f"⚠ Не удалось открыть папку: {ex}", WARN)
            dlg.open = False
            page.update()

        def _close(e=None):
            dlg.open = False
            page.update()

        rows = []
        if is_batch:
            rows.append(ft.Row([
                ft.Text(t("compress_done_batch"), color=FG3, size=12,
                        font_family=FONT, width=170),
                ft.Text(f"{count} / {total}", color=FG, size=12,
                        font_family="Consolas", weight=ft.FontWeight.W_600),
            ], spacing=8))
        else:
            rows.append(ft.Row([
                ft.Text(t("compress_done_single"), color=FG3, size=12,
                        font_family=FONT, width=170),
                ft.Text(os.path.basename(out_path), color=FG, size=12,
                        font_family="Consolas", weight=ft.FontWeight.W_600,
                        selectable=True),
            ], spacing=8))
        rows.append(ft.Row([
            ft.Text(t("compress_done_size"), color=FG3, size=12,
                    font_family=FONT, width=170),
            ft.Text(size_line, color=size_color, size=12,
                    font_family="Consolas", weight=ft.FontWeight.W_600),
        ], spacing=8))
        rows.append(ft.Container(height=6))
        rows.append(ft.Text(folder, color=FG3, size=11,
                            font_family="Consolas", selectable=True))

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Text("✅", size=18),
                ft.Text(t("compress_done_title"), color=FG, size=14,
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
            bgcolor=PANEL,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()
        
    # ═══ ПАКЕТНАЯ AI-ОБРАБОТКА ═══
    async def batch_select_folder(e):
        try:
            folder = await picker.get_directory_path(
                dialog_title=t("batch_select_folder"))
            if not folder:
                return
            exts = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')
            files = [os.path.join(folder, f) for f in os.listdir(folder)
                     if f.lower().endswith(exts)]
            S["batch_files"] = files
            log(f"📁 {t('batch_folder')} {folder}", FG2)
            log(f"   {t('batch_found')} {len(files)}", FG2)
            S["batch_progress_bar"].value = 0
            S["batch_progress_text"].value = f"{t('batch_ready')}: {len(files)} {t('batch_files_count')}"
            page.update()
        except Exception as ex:
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def batch_select_files(e):
        try:
            files = await picker.pick_files(
                dialog_title=t("batch_select_files"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                allow_multiple=True,
                initial_directory=_init_dir(),
            )
            if not files:
                return
            if files and files[0].path:
                _remember_folder(files[0].path)
            S["batch_files"] = [f.path for f in files if f.path]
            log(f"📄 {t('batch_selected')} {len(S['batch_files'])}", FG2)
            S["batch_progress_bar"].value = 0
            S["batch_progress_text"].value = f"{t('batch_ready')}: {len(S['batch_files'])} {t('batch_files_count')}"
            page.update()
        except Exception as ex:
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def batch_run(e):
        files = S["batch_files"]
        if not files:
            log(t("batch_no_files"), WARN)
            page.update()
            return

        total = len(files)
        update_batch_progress(0, total, f"Запуск... 0 / {total}")

        base_dir = os.path.dirname(files[0])
        out_dir = os.path.join(base_dir, "_corrected")
        os.makedirs(out_dir, exist_ok=True)

        log("", FG2)
        log("━━━━━━━━━━━━━━━━━━━━━━", FG3)
        log(f"{t('batch_started')} {total}", FG)
        log(f"   {t('batch_out')} {out_dir}", FG2)
        page.update()

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
                    img = Image.open(fp).convert("RGB")
                    if S["correction_mode"] == "math":
                        result = await asyncio.to_thread(
                            fallback_correct, img, S["profile"]
                        )
                    else:
                        import time as _time
                        _t0 = _time.time()
                        ai_res, ai_ok = await asyncio.to_thread(smart_correct_ai, img)
                        _dt = _time.time() - _t0
                        log(f"   ⏱ {os.path.basename(fp)}: {_dt:.2f} сек", FG2)
                        if ai_ok and ai_res is not None:
                            result = ai_res
                        else:
                            result = await asyncio.to_thread(
                                fallback_correct, img, S["profile"]
                            )
                    if S["soap_fix_strength"] > 0:
                        result = await asyncio.to_thread(
                            remove_soap_adaptive, result, S["soap_fix_strength"]
                        )
                    await asyncio.to_thread(
                        save_16bit_or_8bit, result, out_path, 16
                    )
                    img.close()
                    ok = True
                except Exception as ex:
                    err = f"{type(ex).__name__}: {ex}"
                done += 1
                if ok:
                    count += 1
                    log(f"  [{done}/{total}] ✓ {os.path.basename(fp)}", SUCCESS)
                else:
                    log(f"  ✗ {os.path.basename(fp)}: {err}", DANGER)
                update_batch_progress(done, total)
                page.update()

        await asyncio.gather(*[process_one(fp) for fp in files])

        log(f"✅ {t('batch_processed')} {count} / {total}", SUCCESS)
        log(f"📁 {out_dir}", FG2)
        update_batch_progress(total, total, f"{t('batch_done')}: {count} / {total}")
        S["batch_files"] = []
        page.update()
        
    async def pbr_load_metallic_map(e=None):
        """Загрузка своей Metallic-карты (grayscale)."""
        try:
            files = await picker.pick_files(
                dialog_title="Выбери Metallic map (grayscale)",
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                initial_directory=_init_dir(),
            )
            if not files or not files[0].path:
                return
            fp = files[0].path
            _remember_folder(fp)
            img = Image.open(fp).convert("L")
            arr = np.array(img).astype(np.float32) / 255.0

            if S.get("pbr_source") is not None:
                arr, ok = await _ask_resize_dialog(arr, S["pbr_source"], "Metallic")
                if not ok:
                    log("   ⚠ Metallic загрузка отменена", WARN)
                    page.update()
                    return

            S["pbr_metallic_custom"] = arr
            S["pbr_metallic_custom_path"] = fp
            S["pbr_metallic"] = "custom"
            log(f"⚙ Metallic map загружена: {os.path.basename(fp)}", SUCCESS)
            page.update()

            if S.get("pbr_source") is not None and S.get("pbr_result") is not None:
                log("   → Автогенерация PBR с новой картой...", FG2)
                await pbr_do_generate(None)
            else:
                if S.get("update_pbr_preview"):
                    S["update_pbr_preview"]()
        except Exception as ex:
            log(f"❌ Metallic load: {ex}", DANGER)
            page.update()
            
    async def _ask_resize_dialog(custom_arr, albedo_pil, map_name):
        """Диалог ресайза при несовпадении размеров. → (arr, ok)."""
        ah, aw = albedo_pil.size[1], albedo_pil.size[0]
        ch, cw = custom_arr.shape[:2]
        if (cw, ch) == (aw, ah):
            return custom_arr, True

        loop = asyncio.get_event_loop()
        fut = loop.create_future()

        def _resolve(ok):
            if not fut.done():
                fut.set_result(ok)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(t("pbr_resize_title"), color=FG, size=14),
            content=ft.Container(
                content=ft.Text(
                    t("pbr_resize_text").format(w1=cw, h1=ch, w2=aw, h2=ah),
                    color=FG2, size=12, font_family=FONT,
                ),
                width=380, height=100,
            ),
            actions=[
                ft.TextButton(t("pbr_resize_no"), on_click=lambda e: _resolve(False)),
                ft.TextButton(t("pbr_resize_yes"), on_click=lambda e: _resolve(True)),
            ],
            inset_padding=ft.Padding.symmetric(horizontal=80, vertical=120),
            bgcolor=PANEL,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

        ok = await fut
        dlg.open = False
        page.update()

        if not ok:
            return custom_arr, False

        resized = cv2.resize(
            custom_arr, (aw, ah), interpolation=cv2.INTER_LANCZOS4
        ).astype(np.float32)
        log(f"   ✅ {map_name} resized: {cw}×{ch} → {aw}×{ah}", FG2)
        return resized, True

    async def pbr_load_roughness_map(e=None):
        """Загрузка своей Roughness-карты (grayscale)."""
        try:
            files = await picker.pick_files(
                dialog_title="Выбери Roughness map (grayscale)",
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                initial_directory=_init_dir(),
            )
            if not files or not files[0].path:
                return
            fp = files[0].path
            _remember_folder(fp)
            img = Image.open(fp).convert("L")
            arr = np.array(img).astype(np.float32) / 255.0

            if S.get("pbr_source") is not None:
                arr, ok = await _ask_resize_dialog(arr, S["pbr_source"], "Roughness")
                if not ok:
                    log("   ⚠ Roughness загрузка отменена", WARN)
                    page.update()
                    return

            S["pbr_roughness_custom"] = arr
            S["pbr_roughness_custom_path"] = fp
            S["pbr_roughness"] = "custom"
            log(f"🔧 Roughness map загружена: {os.path.basename(fp)}", SUCCESS)
            page.update()

            if S.get("pbr_source") is not None and S.get("pbr_result") is not None:
                log("   → Автогенерация PBR с новой картой...", FG2)
                await pbr_do_generate(None)
            else:
                if S.get("update_pbr_preview"):
                    S["update_pbr_preview"]()
        except Exception as ex:
            log(f"❌ Roughness load: {ex}", DANGER)
            page.update()

    # ═══ PBR-ОБРАБОТЧИКИ ═══
    async def pbr_do_load(e):
        try:
            files = await picker.pick_files(
                dialog_title=t("pbr_dialog_pick"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                initial_directory=_init_dir(),
            )
            if not files:
                return
            fp = files[0].path
            if not fp:
                return
            _remember_folder(fp)
            img = Image.open(fp).convert("RGB")
            S["pbr_source"] = img
            S["pbr_source_path"] = fp
            S["pbr_result"] = None
            log(f"{t('pbr_log_loaded')} {os.path.basename(fp)}", SUCCESS)
            log("→ " + t("pbr_gen"), FG2)

            if S["pbr_preview"] is not None:
                S["pbr_preview"].src = f"data:image/png;base64,{pil_to_b64(img)}"
                S["pbr_preview"].visible = True
            if S["pbr_preview_hint"] is not None:
                S["pbr_preview_hint"].visible = False

            if S["pbr_buttons"].get("gen"): S["pbr_buttons"]["gen"].disabled = False
            if S["pbr_buttons"].get("save"): S["pbr_buttons"]["save"].disabled = True
            page.update()
        except Exception as ex:
            log(f"❌ PBR load: {ex}", DANGER)
            page.update()

    async def pbr_do_generate(e):
        if S["pbr_source"] is None:
            return
        try:
            await show_pbr_progress(t("pbr_progress_gen"))
            await asyncio.sleep(0.15)

            sl = S["pbr_sliders"]
            _metallic_mode = S.get("pbr_metallic", "black")
            _metallic_custom = S.get("pbr_metallic_custom") if _metallic_mode == "custom" else None
            _rough_mode = S.get("pbr_roughness", "procedural")
            _rough_custom = S.get("pbr_roughness_custom") if _rough_mode == "custom" else None
            result = generate_all_pbr(
                S["pbr_source"],
                height_blur=sl["height_blur"].value,
                normal_strength=sl["strength"].value,
                normal_smooth=sl["smooth"].value,
                normal_clamp=3.0,
                normal_high_pass=sl["high_pass"].value,
                normal_threshold=sl["threshold"].value,
                ao_radius=int(sl["ao_radius"].value),
                ao_intensity=sl["ao_intensity"].value,
                rough_base=sl["rough_base"].value,
                rough_variation=sl["rough_var"].value,
                metallic_mode=_metallic_mode,
                metallic_custom=_metallic_custom,
                roughness_mode=_rough_mode,
                roughness_custom=_rough_custom,
            )
            S["pbr_result"] = result
            log(t("pbr_log_gen_done"), SUCCESS)

            if S["pbr_buttons"].get("save"): S["pbr_buttons"]["save"].disabled = False
            if S["pbr_buttons"].get("viewer"): S["pbr_buttons"]["viewer"].disabled = False
            page.update()

            if S.get("update_pbr_preview"):
                S["update_pbr_preview"]()

            await asyncio.sleep(0.15)
            await hide_pbr_progress()
        except Exception as ex:
            await hide_pbr_progress()
            log(f"❌ PBR generate: {ex}", DANGER)
            page.update()

    async def pbr_do_simple_generate(e):
        """Simple mode: открыть файл → сгенерировать с текущим пресетом."""
        try:
            files = await picker.pick_files(
                dialog_title=t("pbr_dialog_pick"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                initial_directory=_init_dir(),
            )
            if not files or not files[0].path:
                return
            fp = files[0].path
            _remember_folder(fp)
            img = Image.open(fp).convert("RGB")
            S["pbr_source"] = img
            S["pbr_source_path"] = fp
            S["pbr_result"] = None

            if S["pbr_preview"] is not None:
                S["pbr_preview"].src = f"data:image/png;base64,{pil_to_b64(img)}"
                S["pbr_preview"].visible = True
            if S["pbr_preview_hint"] is not None:
                S["pbr_preview_hint"].visible = False
            log(f"{t('pbr_log_loaded')} {os.path.basename(fp)}", SUCCESS)

            await show_pbr_progress(t("pbr_progress_gen"))
            await asyncio.sleep(0.1)

            _metallic_mode = S.get("pbr_metallic", "black")
            _metallic_custom = S.get("pbr_metallic_custom") if _metallic_mode == "custom" else None
            _rough_mode = S.get("pbr_roughness", "procedural")
            _rough_custom = S.get("pbr_roughness_custom") if _rough_mode == "custom" else None

            if S["pbr_sliders"]:
                sl = S["pbr_sliders"]
                result = generate_all_pbr(
                    img,
                    height_blur=sl["height_blur"].value,
                    normal_strength=sl["strength"].value,
                    normal_smooth=sl["smooth"].value,
                    normal_clamp=3.0,
                    normal_high_pass=sl["high_pass"].value,
                    normal_threshold=sl["threshold"].value,
                    ao_radius=int(sl["ao_radius"].value),
                    ao_intensity=sl["ao_intensity"].value,
                    rough_base=sl["rough_base"].value,
                    rough_variation=sl["rough_var"].value,
                    metallic_mode=_metallic_mode,
                    metallic_custom=_metallic_custom,
                    roughness_mode=_rough_mode,
                    roughness_custom=_rough_custom,
                )
            else:
                preset = PBR_PRESETS.get(S["profile"], {})
                result = generate_all_pbr(
                    img,
                    height_blur=preset.get("height_blur", 2.0),
                    normal_strength=preset.get("strength", 1.5),
                    normal_smooth=preset.get("smooth", 1.5),
                    normal_clamp=3.0,
                    normal_high_pass=preset.get("high_pass", 40),
                    normal_threshold=preset.get("threshold", 0.05),
                    ao_radius=int(preset.get("ao_radius", 8)),
                    ao_intensity=preset.get("ao_intensity", 1.5),
                    rough_base=preset.get("rough_base", 0.7),
                    rough_variation=preset.get("rough_var", 0.3),
                    metallic_mode=_metallic_mode,
                    metallic_custom=_metallic_custom,
                    roughness_mode=_rough_mode,
                    roughness_custom=_rough_custom,
                )

            S["pbr_result"] = result
            log(t("pbr_log_gen_done"), SUCCESS)

            if S["pbr_buttons"].get("save"): S["pbr_buttons"]["save"].disabled = False
            if S["pbr_buttons"].get("viewer"): S["pbr_buttons"]["viewer"].disabled = False
            page.update()

            if S.get("update_pbr_preview"):
                S["update_pbr_preview"]()

            await asyncio.sleep(0.15)
            await hide_pbr_progress()
        except Exception as ex:
            await hide_pbr_progress()
            log(f"❌ PBR generate: {ex}", DANGER)
            page.update()

    async def pbr_do_save(e):
        if S["pbr_result"] is None:
            return
        try:
            await show_pbr_progress(t("pbr_progress_gen"))

            base_name = "pbr_output"
            if S["pbr_source_path"]:
                base_name = os.path.splitext(os.path.basename(S["pbr_source_path"]))[0]
            folder = os.path.dirname(S["pbr_source_path"]) if S["pbr_source_path"] else os.getcwd()
            out_dir = os.path.join(folder, f"{base_name}_pbr")
            os.makedirs(out_dir, exist_ok=True)

            total = len(S["pbr_result"])
            done = 0
            bit_depth = S.get("pbr_bit_depth", 16)
            for key, img in S["pbr_result"].items():
                save_pbr_map(img, str(os.path.join(out_dir, f"{base_name}_{key}.png")), bit_depth)
                done += 1
                S["pbr_progress_text"].value = f"{t('pbr_progress_gen')} {done}/{total}"
                page.update()
                await asyncio.sleep(0.02)

            gc.collect()
            log(f"{t('pbr_log_saved')} {out_dir}", SUCCESS)

            await hide_pbr_progress()
        except Exception as ex:
            await hide_pbr_progress()
            log(f"❌ PBR save: {ex}", DANGER)
            page.update()

    async def pbr_open_viewer(e):
        """Открывает viewer.py (или viewer.exe) отдельным процессом."""
        if S["pbr_result"] is None:
            log(t("pbr_viewer_no_result"), WARN)
            page.update()
            return
        try:
            await show_pbr_progress(t("pbr_viewer_progress"))
            await asyncio.sleep(0.05)

            tmpdir = tempfile.mkdtemp(prefix="albedo_viewer_")
            paths = {}
            keys = ("albedo", "height", "normal", "ao", "roughness", "metallic", "orm")
            total = len(keys)
            done = 0
            for key in keys:
                if key in S["pbr_result"]:
                    p = os.path.join(tmpdir, f"{key}.png")
                    img = S["pbr_result"][key]
                    if isinstance(img, np.ndarray):
                        await asyncio.to_thread(to_preview_pil(img).save, p)
                    else:
                        await asyncio.to_thread(img.save, p)
                    paths[key] = p
                done += 1
                S["pbr_progress_text"].value = f"{t('pbr_viewer_progress')} {done}/{total}"
                page.update()

            if "albedo" not in paths and S["pbr_source"] is not None:
                p = os.path.join(tmpdir, "albedo.png")
                await asyncio.to_thread(S["pbr_source"].save, p)
                paths["albedo"] = p

            if getattr(sys, 'frozen', False):
                viewer_path = os.path.join(os.path.dirname(sys.executable), "viewer.exe")
                if not os.path.exists(viewer_path):
                    viewer_path = os.path.join(_base_dir, "viewer.exe")
                cmd = [viewer_path]
            else:
                viewer_path = os.path.join(_base_dir, "viewer.py")
                cmd = [sys.executable, viewer_path]

            cmd += [
                "--albedo", paths.get("albedo", ""),
                "--roughness", paths.get("roughness", ""),
                "--metallic", paths.get("metallic", ""),
                "--tile-x", str(S.get("viewer_tile_x", 4)),
                "--tile-y", str(S.get("viewer_tile_y", 3)),
                "--lang", S.get("lang", "ru"),
            ]

            S["pbr_progress_text"].value = t("pbr_viewer_progress") + " " + "🚀"
            page.update()

            subprocess.Popen(cmd)
            log("👁 Viewer запущен", SUCCESS)

            await asyncio.sleep(0.3)
            await hide_pbr_progress()

        except Exception as ex:
            await hide_pbr_progress()
            log(f"❌ Viewer: {ex}", DANGER)
            page.update()

    async def pbr_do_batch(e):
        try:
            folder = await picker.get_directory_path(
                dialog_title=t("pbr_dialog_folder"))
            if not folder:
                return
            exts = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')
            files = [os.path.join(folder, f) for f in os.listdir(folder)
                     if f.lower().endswith(exts)]
            if not files:
                log(t("pbr_log_no_files"), WARN)
                page.update()
                return

            await show_pbr_progress(t("pbr_progress_batch"))
            out_root = os.path.join(folder, "_pbr_output")
            os.makedirs(out_root, exist_ok=True)

            _m_mode = S.get("pbr_metallic", "black")
            _r_mode = S.get("pbr_roughness", "procedural")
            if _m_mode == "custom":
                log(f"   ⚠ Custom Metallic map будет применена ко ВСЕМ {len(files)} текстурам", WARN)
                log(f"      Убедись что все они одного материала!", WARN)
            if _r_mode == "custom":
                log(f"   ⚠ Custom Roughness map будет применена ко ВСЕМ {len(files)} текстурам", WARN)
                log(f"      Убедись что все они одного материала!", WARN)

            sl = S["pbr_sliders"]
            _metallic_mode = S.get("pbr_metallic", "black")
            _metallic_custom = S.get("pbr_metallic_custom") if _metallic_mode == "custom" else None
            _rough_mode = S.get("pbr_roughness", "procedural")
            _rough_custom = S.get("pbr_roughness_custom") if _rough_mode == "custom" else None
            params = {
                "height_blur": sl["height_blur"].value,
                "normal_strength": sl["strength"].value,
                "normal_smooth": sl["smooth"].value,
                "normal_clamp": 3.0,
                "normal_high_pass": sl["high_pass"].value,
                "normal_threshold": sl["threshold"].value,
                "ao_radius": int(sl["ao_radius"].value),
                "ao_intensity": sl["ao_intensity"].value,
                "rough_base": sl["rough_base"].value,
                "rough_variation": sl["rough_var"].value,
                "metallic_mode": _metallic_mode,
                "metallic_custom": _metallic_custom,
                "roughness_mode": _rough_mode,
                "roughness_custom": _rough_custom,
            }

            S["pbr_batch_results"] = {}
            count = 0
            total_files = len(files)
            for i, fp in enumerate(files, 1):
                try:
                    S["pbr_progress_text"].value = f"{t('pbr_progress_batch')} {i}/{total_files}"
                    page.update()

                    img = Image.open(fp).convert("RGB")
                    result = generate_all_pbr(img, **params)
                    base = os.path.splitext(os.path.basename(fp))[0]
                    sub = os.path.join(out_root, base)
                    os.makedirs(sub, exist_ok=True)
                    img.save(str(os.path.join(sub, f"{base}_albedo.png")))
                    bit_depth = S.get("pbr_bit_depth", 16)
                    for k, m in result.items():
                        save_pbr_map(m, str(os.path.join(sub, f"{base}_{k}.png")), bit_depth)
                    count += 1
                    S["pbr_batch_results"][base] = sub
                    log(f"  [{i}/{total_files}] ✓ {os.path.basename(fp)}", SUCCESS)
                    page.update()

                    try:
                        img.close()
                    except Exception:
                        pass
                    if i % 5 == 0:
                        gc.collect()

                    await asyncio.sleep(0.01)
                except Exception as ex:
                    log(f"  ✗ {os.path.basename(fp)}: {ex}", DANGER)
            log(f"{t('pbr_log_batch_done')} {count} {t('pbr_log_files')}", SUCCESS)
            log(f"📁 {out_root}", FG2)
            await hide_pbr_progress()

            if count > 0:
                keys = list(S["pbr_batch_results"].keys())
                S["pbr_batch_index"] = 0
                rebuild_ui()
                pbr_load_batch_texture(keys[0])
        except Exception as ex:
            await hide_pbr_progress()
            log(f"❌ PBR batch: {ex}", DANGER)
            page.update()

    def pbr_load_batch_texture(base_name):
        if not base_name or base_name == "_none_":
            return
        folder = S["pbr_batch_results"].get(base_name)
        if not folder or not os.path.exists(folder):
            return

        result = {}
        for key in ("albedo", "height", "normal", "ao", "roughness", "metallic", "orm", "edge"):
            path = os.path.join(folder, f"{base_name}_{key}.png")
            if os.path.exists(path):
                img = Image.open(path).convert("RGB")
                img.load()
                result[key] = img

        if not result:
            return

        S["pbr_result"] = result
        S["pbr_batch_selected"] = base_name
        keys = list(S["pbr_batch_results"].keys())
        if base_name in keys:
            S["pbr_batch_index"] = keys.index(base_name)

        show_key = "albedo" if "albedo" in result else next(iter(result.keys()), None)
        if show_key:
            S["pbr_preview"].src = f"data:image/png;base64,{pil_to_b64(result[show_key])}"
            S["pbr_preview"].visible = True
            S["pbr_current_map"] = show_key
            if S.get("pbr_preview_hint"):
                S["pbr_preview_hint"].visible = False

        pbr_batch_refresh_label()
        log(f"📂 Batch: загружена {base_name}", FG2)
        page.update()

    def pbr_batch_refresh_label():
        keys = list(S["pbr_batch_results"].keys())
        if not keys:
            if S.get("pbr_batch_label"):
                S["pbr_batch_label"].value = ""
            return
        idx = S["pbr_batch_index"]
        if idx >= len(keys):
            idx = 0
            S["pbr_batch_index"] = 0
        if S.get("pbr_batch_label"):
            S["pbr_batch_label"].value = f"{keys[idx]}  ({idx + 1}/{len(keys)})"

    def pbr_batch_next(e=None):
        keys = list(S["pbr_batch_results"].keys())
        if not keys:
            return
        S["pbr_batch_index"] = (S["pbr_batch_index"] + 1) % len(keys)
        pbr_load_batch_texture(keys[S["pbr_batch_index"]])
        for k, b in S["pbr_map_buttons"].items():
            b.bgcolor = ACCENT if k == S["pbr_current_map"] else CARD
            b.content.color = ON_ACCENT if k == S["pbr_current_map"] else FG2
        page.update()

    # ═══════════════════════════════════════════════════════════
    #  EXPORT — упаковка под движки
    # ═══════════════════════════════════════════════════════════

    def _export_engine_label(eng):
        return {
            "unity_hdrp": "Unity HDRP",
            "unity_urp": "Unity URP",
            "unreal": "Unreal",
            "godot": "Godot",
        }.get(eng, eng)

    def _export_normal_label(nf):
        return "DirectX (Y-)" if nf == "directx" else "OpenGL (Y+)"

    async def export_load_from_pbr(e=None):
        if S.get("pbr_result") is None:
            log("   ⚠ PBR-карты не сгенерированы", WARN)
            page.update()
            return
        src = {}
        for k, v in S["pbr_result"].items():
            if v is not None:
                src[k] = v
        if "albedo" not in src and S.get("pbr_source") is not None:
            arr = np.array(S["pbr_source"].convert("RGB")).astype(np.float32) / 255.0
            src["albedo"] = arr
        S["export_source"] = src
        base = "PBR"
        if S.get("pbr_source_path"):
            base = os.path.splitext(os.path.basename(S["pbr_source_path"]))[0]
        S["export_source_label"] = f"PBR / {base}"
        log(f"📦 Export: источник — текущий PBR ({len(src)} карт)", SUCCESS)
        page.update()
        rebuild_ui()

    async def export_load_from_folder(e=None):
        folder = await picker.get_directory_path(
            dialog_title="Выбери папку с PBR-картами",
            initial_directory=_init_dir(),
        )
        if not folder:
            return
        if folder and folder != S.get("last_folder"):
            S["last_folder"] = folder
            persist_settings()
        src = load_pbr_folder(folder)
        if not src or "normal" not in src:
            log(f"   ⚠ В папке нет *_normal.png: {folder}", WARN)
            page.update()
            return
        S["export_source"] = src
        S["export_source_label"] = folder
        log(f"📦 Export: загружено {len(src)} карт из {os.path.basename(folder)}", SUCCESS)
        page.update()
        rebuild_ui()

    async def export_load_custom_detail(e=None):
        files = await picker.pick_files(
            dialog_title="Выбери Detail Mask (grayscale)",
            allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
            initial_directory=_init_dir(),
        )
        if not files or not files[0].path:
            return
        fp = files[0].path
        _remember_folder(fp)
        try:
            img = Image.open(fp).convert("L")
            arr = np.array(img).astype(np.float32) / 255.0
            S["export_custom_detail"] = arr
            S["export_detail_mode"] = "custom"
            log(f"📦 Detail Mask загружена: {os.path.basename(fp)}", SUCCESS)
        except Exception as ex:
            log(f"❌ Detail Mask: {ex}", DANGER)
        page.update()
        rebuild_ui()

    async def export_pack(e=None):
        if S.get("export_source") is None:
            log("   ⚠ Сначала выбери источник (PBR или папка)", WARN)
            page.update()
            return
        try:
            await show_pbr_progress("📦 Упаковка...")
            await asyncio.sleep(0.05)
            engine = S.get("export_engine", "unity_hdrp")
            nf = S.get("export_normal_format", "opengl")
            detail_mode = S.get("export_detail_mode", "edge")
            detail_mask = None
            if engine == "unity_hdrp":
                if detail_mode == "white":
                    detail_mask = None
                elif detail_mode == "custom":
                    detail_mask = S.get("export_custom_detail")
            result = await asyncio.to_thread(
                pack_for_engine,
                S["export_source"], engine, nf, detail_mask
            )
            if not result or "packed" not in result:
                log("   ⚠ Упаковка не удалась", WARN)
                await hide_pbr_progress()
                return
            S["export_packed"] = result["packed"]
            S["export_normal_out"] = result.get("normal")
            log(f"📦 Упаковано: {_export_engine_label(engine)} / {_export_normal_label(nf)}", SUCCESS)
            page.update()
            await asyncio.sleep(0.05)
            await hide_pbr_progress()
            rebuild_ui()
        except Exception as ex:
            await hide_pbr_progress()
            log(f"❌ Export pack: {ex}", DANGER)
            page.update()

    async def export_save(e=None):
        if S.get("export_packed") is None:
            log("   ⚠ Нечего сохранять — сначала упакуй", WARN)
            page.update()
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
            await show_pbr_progress("💾 Сохранение...")
            await asyncio.sleep(0.05)
            await asyncio.to_thread(
                save_engine_map, S["export_packed"],
                os.path.join(out_dir, packed_name), bd
            )
            if S.get("export_normal_out") is not None:
                await asyncio.to_thread(
                    save_engine_map, S["export_normal_out"],
                    os.path.join(out_dir, normal_name), bd
                )
            log(f"💾 Export сохранён: {out_dir}", SUCCESS)
            page.update()
            await asyncio.sleep(0.1)
            await hide_pbr_progress()
        except Exception as ex:
            await hide_pbr_progress()
            log(f"❌ Export save: {ex}", DANGER)
            page.update()

    def export_set_engine(eng):
        S["export_engine"] = eng
        S["export_packed"] = None
        persist_settings()
        page.update()
        rebuild_ui()

    def export_set_normal_format(nf):
        S["export_normal_format"] = nf
        S["export_packed"] = None
        persist_settings()
        page.update()
        rebuild_ui()

    def export_set_detail_mode(mode):
        S["export_detail_mode"] = mode
        S["export_packed"] = None
        persist_settings()
        page.update()
        rebuild_ui()

    def export_set_channel(ch):
        S["export_preview_channel"] = ch
        page.update()
        rebuild_ui()

    def export_build_preview_pil():
        arr = S.get("export_packed")
        if arr is None:
            return None
        ch = S.get("export_preview_channel", "rgb")
        if arr.ndim == 2:
            a = np.clip(arr, 0, 1)
            return Image.fromarray((a * 255).astype(np.uint8), mode="L")
        if ch == "r":
            a = np.clip(arr[..., 0], 0, 1)
            return Image.fromarray((a * 255).astype(np.uint8), mode="L")
        if ch == "g":
            a = np.clip(arr[..., 1], 0, 1)
            return Image.fromarray((a * 255).astype(np.uint8), mode="L")
        if ch == "b":
            a = np.clip(arr[..., 2], 0, 1)
            return Image.fromarray((a * 255).astype(np.uint8), mode="L")
        if ch == "a":
            if arr.shape[2] >= 4:
                a = np.clip(arr[..., 3], 0, 1)
                return Image.fromarray((a * 255).astype(np.uint8), mode="L")
            return None
        a = np.clip(arr[..., :3], 0, 1)
        return Image.fromarray((a * 255).astype(np.uint8), mode="RGB")

    def build_right_panel_export():
        engine = S.get("export_engine", "unity_hdrp")

        def make_radio_engine():
            return ft.RadioGroup(
                content=ft.Column([
                    ft.Radio(value="unity_hdrp", label="Unity HDRP — Mask Map"),
                    ft.Radio(value="unity_urp", label="Unity URP — MetallicSmoothness"),
                    ft.Radio(value="unreal", label="Unreal — ORM"),
                    ft.Radio(value="godot", label="Godot — ORM"),
                ], spacing=2),
                value=engine,
                on_change=lambda e: export_set_engine(e.control.value),
            )

        def make_radio_normal():
            return ft.RadioGroup(
                content=ft.Column([
                    ft.Radio(value="opengl", label="OpenGL (Y+)"),
                    ft.Radio(value="directx", label="DirectX (Y-)"),
                ], spacing=2),
                value=S.get("export_normal_format", "opengl"),
                on_change=lambda e: export_set_normal_format(e.control.value),
            )

        def make_radio_detail():
            return ft.RadioGroup(
                content=ft.Column([
                    ft.Radio(value="white", label="White (1.0)"),
                    ft.Radio(value="edge", label="Edge map"),
                    ft.Radio(value="custom", label="Своя (загрузить)"),
                ], spacing=2),
                value=S.get("export_detail_mode", "edge"),
                on_change=lambda e: export_set_detail_mode(e.control.value),
            )

        def make_radio_bit():
            def _on_change(e):
                S["export_bit_depth"] = int(e.control.value)
                persist_settings()
            return ft.RadioGroup(
                content=ft.Row([
                    ft.Radio(value="8", label="8-bit", fill_color=SAVE_COLOR),
                    ft.Radio(value="16", label="16-bit", fill_color=SAVE_COLOR),
                ]),
                value=str(S.get("export_bit_depth", 8)),
                on_change=_on_change,
            )

        detail_block = ft.Container(
            content=ft.Column([
                ft.Text("Detail Mask (только HDRP)", size=10,
                        weight=ft.FontWeight.BOLD, color=FG3, font_family=FONT),
                ft.Container(height=4),
                make_radio_detail(),
                ft.Container(height=4),
                make_btn("📁 Загрузить свою", export_load_custom_detail, ACCENT),
            ], spacing=2),
            visible=(engine == "unity_hdrp"),
        )

        layout_text = {
            "unity_hdrp": "R = Metallic\nG = AO\nB = Detail Mask\nA = Smoothness (1-Rough)",
            "unity_urp":  "R = Metallic\nG = 0\nB = 0\nA = Smoothness (1-Rough)",
            "unreal":     "R = AO\nG = Roughness\nB = Metallic\nA = 1.0",
            "godot":      "R = AO\nG = Roughness\nB = Metallic\nA = 1.0",
        }.get(engine, "")

        return ft.Container(
            content=ft.Column([
                ft.Text("🎮 ДВИЖОК", size=10, weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=6),
                make_radio_engine(),
                ft.Container(height=14),
                ft.Divider(color=FG3, height=1),
                ft.Container(height=10),
                ft.Text("📐 NORMAL MAP", size=10, weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=6),
                make_radio_normal(),
                ft.Container(height=14),
                ft.Divider(color=FG3, height=1),
                ft.Container(height=10),
                detail_block,
                ft.Container(height=14),
                ft.Divider(color=FG3, height=1),
                ft.Container(height=10),
                ft.Text("💾 БИТНОСТЬ PNG", size=10, weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=6),
                make_radio_bit(),
                ft.Container(height=14),
                ft.Divider(color=FG3, height=1),
                ft.Container(height=10),
                ft.Text("📋 РАСКЛАДКА КАНАЛОВ", size=10,
                        weight=ft.FontWeight.BOLD, color=FG3, font_family=FONT),
                ft.Container(height=6),
                ft.Container(
                    content=ft.Text(layout_text, color=FG2, size=11,
                                    font_family="Consolas", selectable=True),
                    bgcolor=INPUT, border_radius=8, padding=10,
                ),
            ], spacing=4, scroll=ft.ScrollMode.AUTO),
            bgcolor=PANEL, border_radius=12, padding=16, width=320,
        )

    async def do_remove_soap(e):
        source = S["corrected"] if S["corrected"] is not None else S["original"]
        if source is None:
            log(t("auto_detect_no_tex"), WARN)
            page.update()
            return
        try:
            await show_progress(t("soap_fix_progress"))
            await asyncio.sleep(0.1)

            result = await asyncio.to_thread(
                remove_soap_adaptive, source,
                S["soap_fix_strength"], 15, 25.0, None
            )
            S["corrected"] = result
            S["last_op"] = "soap_fix"
            S["show_original"] = False
            update_preview_display()
            log(t("soap_fix_done"), SUCCESS)

            if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
            if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = False
            if S["buttons"].get("preview_toggle"): S["buttons"]["preview_toggle"].disabled = False

            page.update()
            await asyncio.sleep(0.1)
            await hide_progress()
        except Exception as ex:
            await hide_progress()
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def do_boost_saturation(e):
        source = S["corrected"] if S["corrected"] is not None else S["original"]
        if source is None:
            log("   ⚠ Сначала загрузи текстуру", WARN)
            page.update()
            return
        try:
            await show_progress(t("sat_progress"))
            await asyncio.sleep(0.1)

            result = await asyncio.to_thread(
                boost_saturation, source, S["saturation_boost"]
            )
            S["corrected"] = result
            S["last_op"] = "saturation"
            S["show_original"] = False
            update_preview_display()
            log(t("sat_done"), SUCCESS)

            if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
            if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = False
            if S["buttons"].get("preview_toggle"): S["buttons"]["preview_toggle"].disabled = False

            page.update()
            await asyncio.sleep(0.1)
            await hide_progress()
        except Exception as ex:
            await hide_progress()
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()
            
    async def do_apply_realism(e):
        source = S["corrected"] if S["corrected"] is not None else S["original"]
        if source is None:
            log("   ⚠ Сначала загрузи текстуру", WARN)
            page.update()
            return
        try:
            await show_progress(t("realism_progress"))
            await asyncio.sleep(0.1)

            result = await asyncio.to_thread(
                add_realism, source,
                S["realism_grain"],
                S["realism_highpass"],
                S["realism_variation"],
            )
            S["corrected"] = result
            S["last_op"] = "realism"
            S["show_original"] = False
            update_preview_display()
            log(t("realism_done"), SUCCESS)

            if S["buttons"].get("save"):
                S["buttons"]["save"].disabled = False
            if S["buttons"].get("reset"):
                S["buttons"]["reset"].disabled = False
            if S["buttons"].get("preview_toggle"):
                S["buttons"]["preview_toggle"].disabled = False

            page.update()
            await asyncio.sleep(0.1)
            await hide_progress()
        except Exception as ex:
            await hide_progress()
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    def toggle_tiling(e):
        S["tiling_mode"] = not S["tiling_mode"]
        persist_settings()
        img = None
        if S["show_original"] and S["original"] is not None:
            img = S["original"]
        elif S["corrected"] is not None:
            img = S["corrected"]
        elif S["original"] is not None:
            img = S["original"]
        if img is not None:
            if S["tiling_mode"]:
                w, h = img.size
                tiled = Image.new("RGB", (w * 3, h * 3))
                for x in range(3):
                    for y in range(3):
                        tiled.paste(img, (x * w, y * h))
                max_size = 1800
                tiled.thumbnail((max_size, max_size), Image.LANCZOS)
                S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(tiled)}"
            else:
                S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(img)}"
        rebuild_ui()
        
    def toggle_preview(e):
        """Переключает превью между оригиналом и результатом."""
        if S["original"] is None:
            return
        S["show_original"] = not S["show_original"]
        update_preview_display()
        if S["buttons"].get("preview_toggle"):
            if S["show_original"]:
                S["buttons"]["preview_toggle"].content.value = t("preview_toggle_result")
            else:
                S["buttons"]["preview_toggle"].content.value = t("preview_toggle_orig")
        page.update()
        
    def on_keyboard(e: ft.KeyboardEvent):
        """Глобальные горячие клавиши."""
        # Игнорируем если открыт диалог
        if page.overlay:
            for dlg in page.overlay:
                if isinstance(dlg, ft.AlertDialog) and dlg.open:
                    return

        key = (e.key or "").lower()
        tab = S.get("active_tab", "single")
        is_simple = S.get("ui_mode", "simple") == "simple"

        # ═══ Ctrl+O — Open ═══
        if e.ctrl and key == "o":
            if tab == "single":
                if is_simple:
                    page.run_task(do_simple_process, None)
                else:
                    page.run_task(open_file, None)
            elif tab == "pbr":
                if is_simple:
                    page.run_task(pbr_do_simple_generate, None)
                else:
                    page.run_task(pbr_do_load, None)
            elif tab == "compress":
                if is_simple:
                    page.run_task(compress_simple_process, None)
                else:
                    page.run_task(compress_open_file, None)
            return

        # ═══ Ctrl+S — Save ═══
        if e.ctrl and key == "s":
            if tab == "single" and S.get("corrected") is not None:
                page.run_task(open_save, None)
            elif tab == "pbr" and S.get("pbr_result") is not None:
                page.run_task(pbr_do_save, None)
            elif tab == "compress" and S.get("compress_corrected") is not None:
                if not is_simple:
                    page.run_task(compress_save, None)
            elif tab == "export" and S.get("export_packed") is not None:
                page.run_task(export_save, None)
            return

        # ═══ Ctrl+R — Reset ═══
        if e.ctrl and key == "r":
            if tab == "single" and S.get("original") is not None:
                page.run_task(do_reset, None)
            return

        # ═══ Ctrl+Z — Undo (пока = Reset) ═══
        if e.ctrl and key == "z":
            if tab == "single" and S.get("corrected") is not None:
                page.run_task(do_reset, None)
            return

        # ═══ Space — toggle preview original/result ═══
        if key == " " or key == "space":
            if tab == "single" and not is_simple and S.get("corrected") is not None:
                toggle_preview(None)
            return

        # ═══ Enter — быстрые действия по вкладкам ═══
        if key == "enter":
            if tab == "single":
                if is_simple:
                    if S.get("original") is None:
                        page.run_task(do_simple_process, None)
                else:
                    if S.get("corrected") is not None:
                        page.run_task(open_save, None)
                    elif S.get("original") is not None:
                        page.run_task(do_auto_correct, None)
            elif tab == "pbr" and S.get("pbr_result") is not None:
                page.run_task(pbr_open_viewer, None)
            return

    async def do_make_seamless(e):
        source = S["corrected"] if S["corrected"] is not None else S["original"]
        if source is None:
            log("   ⚠ Сначала загрузи текстуру", WARN)
            page.update()
            return
        try:
            await show_progress(t("seamless_progress"))
            await asyncio.sleep(0.1)

            result = await asyncio.to_thread(
                make_seamless, source,
                S.get("seamless_hipass", True),
            )
            S["corrected"] = result
            S["last_op"] = "seamless"
            S["show_original"] = False
            update_preview_display()
            log(t("seamless_done"), SUCCESS)

            if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
            if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = False
            if S["buttons"].get("preview_toggle"): S["buttons"]["preview_toggle"].disabled = False

            page.update()
            await asyncio.sleep(0.1)
            await hide_progress()
        except Exception as ex:
            await hide_progress()
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    def make_btn(label, on_click, color=None, disabled=False):
        color = color or ACCENT
        return ft.FilledButton(
            content=ft.Text(label, color=ON_ACCENT, size=14,
                            font_family=FONT, weight=ft.FontWeight.W_600,
                            text_align=ft.TextAlign.CENTER),
            style=ft.ButtonStyle(
                bgcolor=color, color=ON_ACCENT,
                padding=ft.Padding.symmetric(vertical=15, horizontal=14),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=on_click, disabled=disabled,
        )

    def set_profile(key):
        S["profile"] = key
        S["pbr_sliders"] = {}
        log(f"{t('log_type')} {profile_label(key)}", FG2)
        persist_settings()
        rebuild_ui()

    def make_correction_switch():
        """Пирамида: 2 AI модели сверху, Math снизу."""
        method = S.get("correction_mode", "ai")
        model = S.get("ai_model", "autolevels")

        def set_ai_model(model_key):
            S["correction_mode"] = "ai"
            S["ai_model"] = model_key
            persist_settings()
            rebuild_ui()

        def set_math():
            S["correction_mode"] = "math"
            persist_settings()
            rebuild_ui()

        autolevels_active = (method == "ai") and (model == "autolevels")
        lut_active = (method == "ai") and (model == "lutwithbgrid")

        autolevels_btn = ft.Container(
            content=ft.Text(
                t("correction_ai_autolevels"),
                color=ON_ACCENT if autolevels_active else FG2,
                size=11, font_family=FONT,
                weight=ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=ACCENT if autolevels_active else CARD,
            border_radius=8,
            padding=ft.Padding.symmetric(vertical=8, horizontal=6),
            expand=True, ink=True,
            on_click=lambda e: set_ai_model("autolevels"),
        )

        lut_btn = ft.Container(
            content=ft.Text(
                t("correction_ai_lutwithbgrid"),
                color=ON_ACCENT if lut_active else FG2,
                size=11, font_family=FONT,
                weight=ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=ACCENT if lut_active else CARD,
            border_radius=8,
            padding=ft.Padding.symmetric(vertical=8, horizontal=6),
            expand=True, ink=True,
            on_click=lambda e: set_ai_model("lutwithbgrid"),
        )

        math_active = (method == "math")
        math_btn = ft.Container(
            content=ft.Text(
                t("correction_math"),
                color=ON_ACCENT if math_active else FG2,
                size=11, font_family=FONT,
                weight=ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=ACCENT if math_active else CARD,
            border_radius=8,
            padding=ft.Padding.symmetric(vertical=8, horizontal=6),
            ink=True,
            on_click=lambda e: set_math(),
            width=142,
        )

        return ft.Column([
            ft.Row([autolevels_btn, lut_btn], spacing=4),
            ft.Row([math_btn], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=4)

    def set_category(key):
        S["profile_category"] = key
        items = PROFILE_CATEGORIES[key]["items"]
        if S["profile"] not in items:
            S["profile"] = items[0]
        S["pbr_sliders"] = {}
        persist_settings()
        rebuild_ui()

    def make_category_tabs(compact=False):
        rows = []
        row = []
        per_row = 3
        for key, cat in PROFILE_CATEGORIES.items():
            is_active = S["profile_category"] == key
            if compact:
                label = f"{cat['emoji']}"
                size = 16
            else:
                label = f"{cat['emoji']} {cat[S['lang']]}"
                size = 12
            btn = ft.Container(
                content=ft.Text(
                    label,
                    color=ON_ACCENT if is_active else FG2,
                    size=size, font_family=FONT,
                    weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_500,
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor=ACCENT if is_active else CARD,
                border_radius=8,
                padding=ft.Padding.symmetric(vertical=8, horizontal=4),
                expand=True, ink=True,
                tooltip=f"{cat['emoji']} {cat[S['lang']]}",
                on_click=lambda e, k=key: set_category(k),
            )
            row.append(btn)
            if len(row) == per_row:
                rows.append(ft.Row(row, spacing=4))
                row = []
        if row:
            while len(row) < per_row:
                row.append(ft.Container(expand=True))
            rows.append(ft.Row(row, spacing=4))
        return ft.Column(rows, spacing=4)

    def make_preset_grid(compact=False):
        cat_key = S["profile_category"]
        items = PROFILE_CATEGORIES[cat_key]["items"]
        rows = []
        row = []
        per_row = 3 if compact else 2
        for key in items:
            is_active = S["profile"] == key
            prof = TEXTURE_PROFILES[key]
            if compact:
                label = f"{prof['emoji']}"
                size = 14
            else:
                label = f"{prof['emoji']} {profile_label(key)}"
                size = 12
            btn = ft.Container(
                content=ft.Text(
                    label,
                    color=ON_ACCENT if is_active else FG2,
                    size=size, font_family=FONT,
                    weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_500,
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor=ACCENT if is_active else CARD,
                border_radius=10,
                padding=ft.Padding.symmetric(vertical=8, horizontal=4),
                expand=True, ink=True,
                tooltip=profile_label(key),
                on_click=lambda e, k=key: set_profile(k),
            )
            row.append(btn)
            if len(row) == per_row:
                rows.append(ft.Row(row, spacing=4))
                row = []
        if row:
            while len(row) < per_row:
                row.append(ft.Container(expand=True))
            rows.append(ft.Row(row, spacing=4))
        return ft.Column(rows, spacing=4)

    def create_info_dialog():
        help_content = ft.Container(
            content=ft.Column(
                [ft.Text(t("help_text"), color=FG, size=12,
                         font_family="Consolas", selectable=True,
                         expand=True)],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=ft.Padding.only(left=16, top=16, bottom=16, right=28),
            visible=True,
            expand=True,
        )
        about_content = ft.Container(
            content=ft.Column([
                ft.Text("◐ Albedolizer", size=24, weight=ft.FontWeight.BOLD,
                        color=ACCENT, font_family=FONT),
                ft.Container(height=16),
                ft.Row([ft.Text(f"{t('about_version')}:", color=FG3, size=12,
                                font_family=FONT, width=100),
                        ft.Text("1.7.3-beta", color=FG, size=12,
                                font_family="Consolas", weight=ft.FontWeight.W_600)]),
                ft.Row([ft.Text(f"{t('about_build')}:", color=FG3, size=12,
                                font_family=FONT, width=100),
                        ft.Text("2026-09-23", color=FG, size=12,
                                font_family="Consolas", weight=ft.FontWeight.W_600)]),
                ft.Row([ft.Text(f"{t('about_author')}:", color=FG3, size=12,
                                font_family=FONT, width=100),
                        ft.Text("INV.LVL", color=FG, size=12,
                                font_family="Consolas", weight=ft.FontWeight.W_600)]),
                ft.Row([ft.Text(f"{t('about_license')}:", color=FG3, size=12,
                                font_family=FONT, width=100),
                        ft.Text("Free / Open Source", color=FG, size=12,
                                font_family="Consolas", weight=ft.FontWeight.W_600)]),
                ft.Container(height=20),
                ft.Text(t("about_desc"), color=FG2, size=11, font_family=FONT),
            ], spacing=6),
            padding=20, visible=False,
        )

        copy_feedback = ft.Text("", color=SUCCESS, size=11, font_family=FONT)

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
                    ft.Text(w["label"], color=ACCENT, size=12,
                            font_family=FONT, width=130,
                            weight=ft.FontWeight.W_600),
                    ft.Text(w["address"], color=FG, size=11,
                            font_family="Consolas", selectable=True, expand=True),
                    ft.Container(
                        content=ft.Text("📋", size=14),
                        bgcolor=CARD, border_radius=6,
                        padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                        ink=True, on_click=copy_address(w["address"]),
                    ),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=CARD, border_radius=8, padding=10,
            )
            wallet_cards.append(card)

        support_content = ft.Container(
            content=ft.Column([
                ft.Text("💛", size=42, text_align=ft.TextAlign.CENTER),
                ft.Text(t("support_title"), size=18, weight=ft.FontWeight.BOLD,
                        color=FG, font_family=FONT, text_align=ft.TextAlign.CENTER),
                ft.Container(height=8),
                ft.Text(t("support_text"), color=FG2, size=11,
                        font_family=FONT, text_align=ft.TextAlign.CENTER),
                ft.Container(height=16),
                *wallet_cards, ft.Container(height=8), copy_feedback,
            ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20, visible=False,
        )

        tab_btns = {}

        def set_info_tab(name):
            help_content.visible = name == "help"
            about_content.visible = name == "about"
            support_content.visible = name == "support"
            for k, b in tab_btns.items():
                b.content.color = ON_ACCENT if k == name else FG2
                b.bgcolor = ACCENT if k == name else CARD
            page.update()

        def make_tab(key, label):
            b = ft.Container(
                content=ft.Text(label, color=FG2, size=12, font_family=FONT,
                                weight=ft.FontWeight.W_600),
                bgcolor=CARD, border_radius=8,
                padding=ft.Padding.symmetric(vertical=8, horizontal=14),
                ink=True, on_click=lambda e, k=key: set_info_tab(k),
            )
            tab_btns[key] = b
            return b

        def open_manual(e=None):
            """Открывает manual.html в браузере."""
            import webbrowser
            manual_path = os.path.join(_base_dir, "manual.html")
            if os.path.exists(manual_path):
                webbrowser.open(f"file:///{manual_path.replace(os.sep, '/')}")
                log("📖 Мануал открыт в браузере", FG2)
            else:
                log(f"⚠ manual.html не найден: {manual_path}", WARN)
            page.update()

        def close_info(e=None):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                make_tab("help", t("info_tab_help")),
                make_tab("about", t("info_tab_about")),
                make_tab("support", t("info_tab_support")),
                ft.Container(
                    content=ft.Text("📖 " + t("info_tab_manual"),
                                    color=ON_ACCENT, size=12,
                                    font_family=FONT,
                                    weight=ft.FontWeight.W_600),
                    bgcolor=ACCENT, border_radius=8,
                    padding=ft.Padding.symmetric(vertical=8, horizontal=14),
                    ink=True, on_click=open_manual,
                ),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Text("✕", color=FG, size=14,
                                    font_family=FONT, weight=ft.FontWeight.BOLD),
                    bgcolor=CARD, border_radius=8,
                    padding=ft.Padding.symmetric(vertical=6, horizontal=12),
                    ink=True, on_click=close_info,
                ),
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            content=ft.Container(
                content=ft.Column([help_content, about_content, support_content],
                                  spacing=0),
                width=600, height=420,
            ),
            bgcolor=PANEL,
        )
        set_info_tab("help")
        return dlg

    def show_welcome_dialog():
        """Welcome-диалог при первом запуске."""
        def _close(e=None):
            dlg.open = False
            S["first_launch_done"] = True
            persist_settings()
            page.update()

        def _open_manual(e=None):
            dlg.open = False
            S["first_launch_done"] = True
            persist_settings()
            import webbrowser
            manual_path = os.path.join(_base_dir, "manual.html")
            if os.path.exists(manual_path):
                webbrowser.open(f"file:///{manual_path.replace(os.sep, '/')}")
            page.update()

        def _switch_advanced(e=None):
            dlg.open = False
            S["first_launch_done"] = True
            S["ui_mode"] = "advanced"
            persist_settings()
            rebuild_ui()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Text("◐", size=24, color=ACCENT),
                ft.Text(t("welcome_title"), color=FG, size=16,
                        weight=ft.FontWeight.W_600),
            ], spacing=10),
            content=ft.Container(
                content=ft.Text(
                    t("welcome_text"),
                    color=FG2, size=12, font_family=FONT,
                    selectable=True,
                ),
                width=480,
                padding=ft.Padding.symmetric(vertical=8),
            ),
            actions=[
                ft.TextButton(
                    t("welcome_manual"),
                    on_click=_open_manual,
                ),
                ft.TextButton(
                    t("welcome_switch_simple"),
                    on_click=_switch_advanced,
                ),
                ft.FilledButton(
                    content=ft.Text(t("welcome_ok"), color=ON_ACCENT,
                                    size=13, weight=ft.FontWeight.W_600),
                    style=ft.ButtonStyle(bgcolor=SUCCESS),
                    on_click=_close,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            bgcolor=PANEL,
            inset_padding=ft.Padding.symmetric(horizontal=60, vertical=80),
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def show_fallback_dialog(current_img, stats):
        dialog_ref = {"dlg": None}

        async def apply_fallback(e=None):
            try:
                dialog_ref["dlg"].open = False
                page.update()

                S["progress_text"].value = t("fb_dialog_progress")
                S["progress_text"].visible = True
                S["progress_bar"].visible = True
                for b in S["buttons"].values():
                    b.disabled = True
                page.update()
                await asyncio.sleep(0.05)

                result = await asyncio.to_thread(
                    smart_correct_fallback, current_img, S["profile"]
                )

                if S["soap_fix_strength"] > 0:
                    result = await asyncio.to_thread(
                        remove_soap_adaptive, result, S["soap_fix_strength"]
                    )
                S["corrected"] = result
                S["last_op"] = "corrected"
                S["show_original"] = False
                update_preview_display()
                log("", FG2)
                log(t("fb_dialog_applied"), SUCCESS)
                run_check(result, False)
                page.update()
            except Exception as ex:
                log(f"❌ {t('fb_dialog_err')} {ex}", DANGER)
            finally:
                S["progress_bar"].visible = False
                S["progress_text"].visible = False
                if S["buttons"].get("load"): S["buttons"]["load"].disabled = False
                if S["buttons"].get("check"): S["buttons"]["check"].disabled = False
                if S["buttons"].get("fix"): S["buttons"]["fix"].disabled = False
                if S["buttons"].get("save"): S["buttons"]["save"].disabled = (S["corrected"] is None)
                if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = (S["corrected"] is None)
                page.update()

        async def keep_ai(e=None):
            try:
                dialog_ref["dlg"].open = False
                page.update()
                log(t("fb_dialog_kept"), FG2)
                page.update()
            except Exception:
                pass

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(t("fb_dialog_title"), color=FG, size=14),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(t("fb_dialog_text"),
                            color=FG2, size=12, font_family=FONT),
                    ft.Container(height=4),
                    ft.Text(f"  {t('fb_dialog_dark')} {stats['dark_pct']:.2f}%",
                            color=DANGER if stats['dark_pct'] > 5 else SUCCESS,
                            size=12, font_family="Consolas"),
                    ft.Text(f"  {t('fb_dialog_light')} {stats['light_pct']:.2f}%",
                            color=DANGER if stats['light_pct'] > 5 else SUCCESS,
                            size=12, font_family="Consolas"),
                    ft.Container(height=6),
                    ft.Text(t("fb_dialog_question"),
                            color=FG, size=12, font_family=FONT),
                ], spacing=2, tight=True),
                width=380,
                height=140,
            ),
            actions=[
                ft.TextButton(t("fb_dialog_keep_ai"), on_click=keep_ai),
                ft.TextButton(t("fb_dialog_apply"), on_click=apply_fallback),
            ],
            inset_padding=ft.Padding.symmetric(horizontal=80, vertical=120),
            bgcolor=PANEL,
        )
        dialog_ref["dlg"] = dlg
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def open_info(e):
        dlg = create_info_dialog()
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def toggle_lang(e):
        S["lang"] = "en" if S["lang"] == "ru" else "ru"
        persist_settings()
        rebuild_ui()

    def toggle_mode(e):
        S["ui_mode"] = "advanced" if S["ui_mode"] == "simple" else "simple"
        if S["ui_mode"] == "simple" and S["active_tab"] in ("batch", "compress"):
            S["active_tab"] = "single"
        persist_settings()
        rebuild_ui()

    def toggle_theme(e):
        nonlocal BG, PANEL, CARD, INPUT, FG, FG2, FG3, ACCENT, SUCCESS, DANGER, WARN
        nonlocal PBR_COLOR, BATCH_COLOR, COMPRESS_COLOR, SAVE_COLOR, RESET_COLOR

        S["theme"] = "light" if S["theme"] == "dark" else "dark"
        th = THEME_DARK if S["theme"] == "dark" else THEME_LIGHT

        BG = th["bg"]
        PANEL = th["panel"]
        CARD = th["card"]
        INPUT = th["input"]
        FG = th["fg"]
        FG2 = th["fg2"]
        FG3 = th["fg3"]
        ACCENT = th["accent"]
        SUCCESS = th["success"]
        DANGER = th["danger"]
        WARN = th["warn"]
        PBR_COLOR = th["success"]
        BATCH_COLOR = th["warn"]
        COMPRESS_COLOR = "#1565c0" if S["theme"] == "dark" else "#3d6fb8"
        RESET_COLOR = "#555555" if S["theme"] == "dark" else "#9aa0a6"

        page.bgcolor = BG
        page.theme_mode = ft.ThemeMode.DARK if S["theme"] == "dark" else ft.ThemeMode.LIGHT
        persist_settings()
        rebuild_ui()

    def persist_settings():
        """Сохраняет текущие настройки в config.json."""
        save_settings({
            "lang": S["lang"],
            "theme": S["theme"],
            "ui_mode": S["ui_mode"],
            "profile": S["profile"],
            "profile_category": S["profile_category"],
            "correction_mode": S["correction_mode"],
            "ai_model": S["ai_model"],
            "soap_fix_strength": S["soap_fix_strength"],
            "saturation_boost": S["saturation_boost"],
            "pbr_bit_depth": S["pbr_bit_depth"],
            "last_folder": S.get("last_folder", ""),
            "seamless_hipass": S.get("seamless_hipass", True),
            "realism_grain": S.get("realism_grain", 0.15),
            "realism_highpass": S.get("realism_highpass", 0.30),
            "realism_variation": S.get("realism_variation", 0.20),
            "batch_threads": S.get("batch_threads", 3),
            "export_engine": S.get("export_engine", "unity_hdrp"),
            "export_normal_format": S.get("export_normal_format", "opengl"),
            "export_detail_mode": S.get("export_detail_mode", "edge"),
            "export_bit_depth": S.get("export_bit_depth", 8),
            "pbr_metallic": S.get("pbr_metallic", "black"),
            "pbr_roughness": S.get("pbr_roughness", "procedural"),
            "tiling_mode": S.get("tiling_mode", False),
            "pbr_current_map": S.get("pbr_current_map", "albedo"),
            "first_launch_done": S.get("first_launch_done", False),
            "window": {
                "width": page.window.width or 1280,
                "height": page.window.height or 820,
            }
        })

    def build_right_panel_batch():
        """Правая панель для вкладки Batch."""
        return ft.Container(
            content=ft.Column([
                ft.Text(t("batch_right_title"), size=10, weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=8),
                ft.Text(t("correction_mode_title"), size=10,
                        weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=6),
                make_correction_switch(),
                ft.Container(height=14),
                ft.Divider(color=FG3, height=1),
                ft.Container(height=10),
                ft.Text(t("soap_fix_title"), size=10,
                        weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=6),
                ft.Text(t("soap_fix_label"), color=FG2, size=11, font_family=FONT),
                ft.Slider(
                    min=0.0, max=3.0, divisions=15,
                    value=S["soap_fix_strength"],
                    label="{value}",
                    active_color=ACCENT, inactive_color=INPUT,
                    on_change=lambda e: S.update({"soap_fix_strength": e.control.value}),
                ),
                ft.Container(height=14),
                ft.Divider(color=FG3, height=1),
                ft.Container(height=10),
                ft.Text(t("batch_threads_title"), size=10,
                        weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=6),
                ft.Text(t("batch_threads_label"), color=FG2, size=11, font_family=FONT),
                ft.Slider(
                    min=1, max=8, divisions=7,
                    value=S.get("batch_threads", 3),
                    label="{value}",
                    active_color=ACCENT, inactive_color=INPUT,
                    on_change=lambda e: S.update(
                        {"batch_threads": int(e.control.value)}
                    ),
                ),
                ft.Container(height=14),
                ft.Divider(color=FG3, height=1),
                ft.Container(height=10),
                ft.Text(t("batch_right_info"), size=10,
                        weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=8),
                ft.Text(t("batch_right_hint"), color=FG2, size=11,
                        font_family=FONT, selectable=True),
            ], spacing=4, scroll=ft.ScrollMode.AUTO),
            bgcolor=PANEL, border_radius=12, padding=16, width=320,
        )

    def build_right_panel_compress():
        """Правая панель для вкладки Compress."""
        return ft.Container(
            content=ft.Column([
                ft.Text(t("compress_right_title"), size=10,
                        weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=8),

                ft.Text(t("pbr_bit_depth"), color=FG2, size=12, font_family=FONT),
                ft.Container(height=4),
                ft.RadioGroup(
                    content=ft.Row([
                        ft.Radio(value="8", label="8-bit",
                                 fill_color=COMPRESS_COLOR),
                        ft.Radio(value="16", label="16-bit",
                                 fill_color=COMPRESS_COLOR),
                    ]),
                    value=str(S["pbr_bit_depth"]),
                    on_change=lambda e: S.update(
                        {"pbr_bit_depth": int(e.control.value)}
                    ),
                ),

                ft.Container(height=14),
                ft.Divider(color=FG3, height=1),
                ft.Container(height=10),

                ft.Text(t("compress_right_info"), size=10,
                        weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=8),
                ft.Text(t("compress_right_hint"), color=FG2, size=11,
                        font_family=FONT, selectable=True),
            ], spacing=4, scroll=ft.ScrollMode.AUTO),
            bgcolor=PANEL, border_radius=12, padding=16, width=320,
        )

    def build_screen():
        is_simple = S["ui_mode"] == "simple"
        buttons = S["buttons"]

        # ═══ SINGLE VIEW ═══
        if is_simple:
            buttons["load"] = make_btn("🚀 " + t("fix"), do_simple_process, SUCCESS)
            buttons["save"] = make_btn(t("save"), open_save, SAVE_COLOR,
                                        disabled=(S["corrected"] is None))

            simple_toolbar = ft.Row([
                buttons["load"],
                ft.Container(expand=True),
                buttons["save"],
            ], spacing=6)
            
            file_info_lbl = ft.Container(
                content=ft.Text(
                    "", color=FG, size=12, font_family="Consolas",
                    selectable=True,
                ),
                bgcolor=INPUT, border_radius=6,
                padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                visible=False,
            )
            S["file_info_label"] = file_info_lbl
            update_file_info()

            preview_hint = ft.Text(t("preview_hint"), color=FG3, size=14,
                                    font_family=FONT)

            preview_content = ft.Stack([
                ft.Container(content=preview_hint,
                             alignment=ft.Alignment.CENTER, expand=True),
                ft.Container(content=S["preview_image"],
                             alignment=ft.Alignment.CENTER, expand=True),
            ], expand=True)

            preview_box = ft.Container(
                content=ft.InteractiveViewer(
                    content=preview_content,
                    min_scale=0.5,
                    max_scale=8.0,
                    expand=True,
                ),
                bgcolor=CARD, border_radius=12, padding=10, expand=True,
            )

            right_panel = ft.Container(
                content=ft.Column([
                    make_btn(
                        t("auto_detect_btn"),
                        do_auto_detect_material,
                        SUCCESS,
                        disabled=(S["original"] is None),
                    ),
                    ft.Container(height=10),
                    ft.Divider(color=FG3, height=1),
                    ft.Container(height=10),
                    ft.Text(t("profile_title"), size=10, weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=6),
                    make_category_tabs(compact=True),
                    ft.Container(height=4),
                    make_preset_grid(compact=False),
                    ft.Container(height=6),
                    ft.Container(
                        content=ft.Text(
                            f"{t('all_types')}: {profile_label(S['profile'])}",
                            color=FG2, size=12, font_family=FONT),
                        bgcolor=INPUT, border_radius=8, padding=10,
                    ),
                ], spacing=4, scroll=ft.ScrollMode.AUTO),
                bgcolor=PANEL, border_radius=12, padding=16, width=320,
            )

            log_panel = ft.Container(height=0)

            single_view = ft.Container(
                content=ft.Column([
                    simple_toolbar,
                    ft.Container(height=4),
                    file_info_lbl,
                    S["progress_bar"],
                    S["progress_text"],
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
        else:
            buttons["load"] = make_btn(t("load"), open_file, ACCENT)
            buttons["check"] = make_btn(t("check"), do_check, ACCENT,
                                         disabled=(S["original"] is None))
            buttons["fix"] = make_btn(t("fix"), do_auto_correct, SUCCESS, disabled=True)
            buttons["save"] = make_btn(t("save"), open_save, SAVE_COLOR,
                                        disabled=(S["corrected"] is None))
            buttons["reset"] = make_btn(t("reset"), do_reset, RESET_COLOR,
                                         disabled=(S["corrected"] is None))
            buttons["preview_toggle"] = make_btn(
                t("preview_toggle_result") if S["show_original"] else t("preview_toggle_orig"),
                toggle_preview, "#00897b",
                disabled=(S["corrected"] is None),
            )

            toolbar = ft.Row([
                buttons["load"],
                buttons["check"],
                buttons["fix"],
                buttons["preview_toggle"],
                ft.Container(expand=True),
                buttons["reset"],
                buttons["save"],
            ], spacing=6)

            file_info_lbl = ft.Container(
                content=ft.Text(
                    "", color=FG, size=12, font_family="Consolas",
                    selectable=True,
                ),
                bgcolor=INPUT, border_radius=6,
                padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                visible=False,
            )
            S["file_info_label"] = file_info_lbl
            update_file_info()

            preview_hint = ft.Text(t("preview_hint"), color=FG3, size=14,
                                    font_family=FONT)

            preview_content = ft.Stack([
                ft.Container(content=preview_hint,
                             alignment=ft.Alignment.CENTER, expand=True),
                ft.Container(content=S["preview_image"],
                             alignment=ft.Alignment.CENTER, expand=True),
            ], expand=True)

            preview_box = ft.Container(
                content=ft.InteractiveViewer(
                    content=preview_content,
                    min_scale=0.5,
                    max_scale=8.0,
                    expand=True,
                ),
                bgcolor=CARD, border_radius=12, padding=10, expand=True,
            )

            right_panel = ft.Container(
                content=ft.Column([
                    make_btn(
                        t("auto_detect_btn"),
                        do_auto_detect_material,
                        SUCCESS,
                        disabled=(S["original"] is None),
                    ),
                    ft.Container(height=10),
                    ft.Divider(color=FG3, height=1),
                    ft.Container(height=10),
                    ft.Text(t("profile_title"), size=10, weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=6),
                    make_category_tabs(compact=True),
                    ft.Container(height=4),
                    make_preset_grid(compact=False),
                    ft.Container(height=6),
                    ft.Container(
                        content=ft.Text(
                            f"{t('all_types')}: {profile_label(S['profile'])}",
                            color=FG2, size=12, font_family=FONT),
                        bgcolor=INPUT, border_radius=8, padding=10,
                    ),
                    ft.Container(height=14),
                    ft.Divider(color=FG3, height=1),
                    ft.Container(height=10),
                    ft.Text(t("correction_mode_title"), size=10,
                            weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=6),
                    make_correction_switch(),
                    ft.Container(height=14),
                    ft.Divider(color=FG3, height=1),
                    ft.Container(height=10),
                    ft.Row([
                        ft.Container(
                            content=make_btn(
                                t("tiling_btn") if not S["tiling_mode"] else t("tiling_btn_off"),
                                toggle_tiling,
                                "#1565c0" if S["theme"] == "dark" else "#3d6fb8",
                            ),
                            expand=True,
                        ),
                        ft.Container(
                            content=make_btn(
                                t("seamless_btn"),
                                do_make_seamless,
                                "#00897b",
                            ),
                            expand=True,
                        ),
                    ], spacing=6),
                    ft.Container(height=4),
                    ft.Checkbox(
                        label=t("seamless_hipass"),
                        value=S.get("seamless_hipass", True),
                        fill_color="#00897b",
                        label_style=ft.TextStyle(color=FG2, size=11, font_family=FONT),
                        on_change=lambda e: (S.update({"seamless_hipass": e.control.value}), persist_settings()),
                    ),
                    ft.Container(height=14),
                    ft.Divider(color=FG3, height=1),
                    ft.Container(height=10),
                    ft.Text(t("soap_fix_title"), size=10,
                            weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=6),
                    ft.Text(t("soap_fix_label"), color=FG2, size=11, font_family=FONT),
                    ft.Slider(
                        min=0.0, max=3.0, divisions=15,
                        value=S["soap_fix_strength"],
                        label="{value}",
                        active_color=ACCENT, inactive_color=INPUT,
                        on_change=lambda e: S.update({"soap_fix_strength": e.control.value}),
                    ),
                    ft.Container(height=4),
                    make_btn(t("soap_fix_button"), do_remove_soap, SAVE_COLOR),
                    ft.Container(height=14),
                    ft.Divider(color=FG3, height=1),
                    ft.Container(height=10),
                    ft.Text(t("sat_title"), size=10,
                            weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=6),
                    ft.Text(t("sat_label"), color=FG2, size=11, font_family=FONT),
                    ft.Slider(
                        min=0.8, max=1.5, divisions=14,
                        value=S["saturation_boost"],
                        label="{value}",
                        active_color=ACCENT, inactive_color=INPUT,
                        on_change=lambda e: S.update({"saturation_boost": e.control.value}),
                    ),
                    ft.Container(height=4),
                    make_btn(t("sat_button"), do_boost_saturation, "#9c27b0" if S["theme"] == "dark" else "#6a1b9a"),
                    ft.Container(height=14),
                    ft.Divider(color=FG3, height=1),
                    ft.Container(height=10),
                    ft.Text(t("stats_title"), size=10, weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=8),
                    S["stats_column"],
                ], spacing=4, scroll=ft.ScrollMode.AUTO),
                bgcolor=PANEL, border_radius=12, padding=16, width=320,
            )

            log_panel = ft.Container(height=0)

            single_view = ft.Container(
                content=ft.Column([
                    toolbar,
                    ft.Container(height=4),
                    file_info_lbl,
                    S["progress_bar"],
                    S["progress_text"],
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

        # ═══ ЛОГ-ПАНЕЛИ ДЛЯ ОСТАЛЬНЫХ ВКЛАДОК ═══
        log_panel_pbr = ft.Container(height=0)

        log_panel_batch = ft.Container(height=0)
        
        log_panel_compress = ft.Container(height=0)

        # ═══ ВКЛАДКА PBR ═══
        pbr_preview = ft.Image(src="", visible=False, fit=ft.BoxFit.CONTAIN)
        S["pbr_preview"] = pbr_preview

        pbr_preview_hint = ft.Text(t("pbr_preview_hint"),
                                     color=FG3, size=14, font_family=FONT)
        S["pbr_preview_hint"] = pbr_preview_hint

        batch_nav_label = ft.Text("", color=FG, size=12, font_family=FONT,
                                   weight=ft.FontWeight.W_600)
        S["pbr_batch_label"] = batch_nav_label

        batch_nav_inner = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text("◀", color=FG, size=14),
                    bgcolor=INPUT, border_radius=6,
                    padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                    ink=True, on_click=lambda e: pbr_batch_prev(),
                ),
                batch_nav_label,
                ft.Container(
                    content=ft.Text("▶", color=FG, size=14),
                    bgcolor=INPUT, border_radius=6,
                    padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                    ink=True, on_click=lambda e: pbr_batch_next(),
                ),
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER,
               tight=True),
            bgcolor=PANEL, border_radius=8, padding=6,
        )

        batch_nav_panel = ft.Container(
            content=ft.Row([batch_nav_inner],
                           alignment=ft.MainAxisAlignment.END),
            visible=len(S["pbr_batch_results"]) > 0,
        )
        S["pbr_batch_nav_panel"] = batch_nav_panel

        pbr_preview_box = ft.Container(
            content=ft.InteractiveViewer(
                content=ft.Stack([
                    ft.Container(content=pbr_preview_hint,
                                 alignment=ft.Alignment.CENTER, expand=True),
                    ft.Container(content=pbr_preview,
                                 alignment=ft.Alignment.CENTER, expand=True),
                    ft.Container(content=batch_nav_panel,
                                 alignment=ft.Alignment.BOTTOM_RIGHT,
                                 padding=12),
                ], expand=True),
                min_scale=0.5,
                max_scale=8.0,
                expand=True,
            ),
            bgcolor=CARD, border_radius=12, padding=10, expand=True,
        )

        if S["pbr_result"] and not S.get("pbr_batch_selected"):
            key = S["pbr_current_map"] if S["pbr_current_map"] in S["pbr_result"] else "albedo"
            if key in S["pbr_result"]:
                pbr_preview.src = f"data:image/png;base64,{pil_to_b64(S['pbr_result'][key])}"
                pbr_preview.visible = True
                pbr_preview_hint.visible = False
        elif S["pbr_result"] and S.get("pbr_batch_selected"):
            key = S["pbr_current_map"] if S["pbr_current_map"] in S["pbr_result"] else "albedo"
            if key in S["pbr_result"]:
                pbr_preview.src = f"data:image/png;base64,{pil_to_b64(S['pbr_result'][key])}"
                pbr_preview.visible = True
                pbr_preview_hint.visible = False

        map_buttons = {}
        S["pbr_map_buttons"] = map_buttons
        map_keys = [
            ("albedo", "🎨 Albedo"), ("height", "⛰ Height"),
            ("normal", "📐 Normal"), ("ao", "🌑 AO"),
            ("roughness", "🔧 Rough"), ("metallic", "⚙ Metal"),
            ("edge", "🎯 Edge"), ("orm", "📦 ORM"),
        ]

        def update_pbr_preview():
            """Обновляет превью и подсветку кнопок по S["pbr_result"] и S["pbr_current_map"]."""
            key = S.get("pbr_current_map", "albedo")
            if S["pbr_batch_selected"] and S["pbr_result"] and key in S["pbr_result"]:
                pbr_preview.src = f"data:image/png;base64,{pil_to_b64(S['pbr_result'][key])}"
                pbr_preview.visible = True
            elif key == "albedo":
                if S["pbr_source"] is not None:
                    pbr_preview.src = f"data:image/png;base64,{pil_to_b64(S['pbr_source'])}"
                    pbr_preview.visible = True
                elif S["pbr_result"] and "albedo" in S["pbr_result"]:
                    pbr_preview.src = f"data:image/png;base64,{pil_to_b64(S['pbr_result']['albedo'])}"
                    pbr_preview.visible = True
            else:
                if S["pbr_result"] and key in S["pbr_result"]:
                    pbr_preview.src = f"data:image/png;base64,{pil_to_b64(S['pbr_result'][key])}"
                    pbr_preview.visible = True
            if S.get("pbr_preview_hint"):
                S["pbr_preview_hint"].visible = False
            for k, b in map_buttons.items():
                b.bgcolor = ACCENT if k == key else CARD
                b.content.color = ON_ACCENT if k == key else FG2
            page.update()

        S["update_pbr_preview"] = update_pbr_preview

        def show_pbr_map(key):
            S["pbr_current_map"] = key
            update_pbr_preview()

        map_row = ft.Row([], spacing=4)
        for key, label in map_keys:
            is_active = key == S["pbr_current_map"]
            b = ft.Container(
                content=ft.Text(label, color=ON_ACCENT if is_active else FG2,
                                size=12, font_family=FONT,
                                weight=ft.FontWeight.W_600),
                bgcolor=ACCENT if is_active else CARD,
                border_radius=8,
                padding=ft.Padding.symmetric(vertical=8, horizontal=12),
                expand=True, ink=True,
                on_click=lambda e, k=key: show_pbr_map(k),
            )
            map_buttons[key] = b
            map_row.controls.append(b)

        sliders = {}
        S["pbr_sliders"] = sliders

        def make_pbr_slider(label, key_name, default, minv, maxv, res):
            preset_val = PBR_PRESETS.get(S["profile"], {}).get(key_name, default)
            divisions = max(1, int((maxv - minv) / res))
            var = ft.Slider(min=minv, max=maxv, divisions=divisions,
                            value=preset_val, label="{value}",
                            active_color=PBR_COLOR, inactive_color=INPUT)
            sliders[key_name] = var
            return ft.Column([
                ft.Text(label, color=FG2, size=12, font_family=FONT),
                var,
            ], spacing=2)

        def _on_metallic_mode_change(e):
            S["pbr_metallic"] = e.control.value
            persist_settings()
            page.update()
            rebuild_ui()

        pbr_metal_radio = ft.RadioGroup(
            content=ft.Column([
                ft.Row([
                    ft.Radio(value="black", label=t("pbr_metal_black"),
                             fill_color=PBR_COLOR),
                    ft.Radio(value="white", label=t("pbr_metal_white"),
                             fill_color=PBR_COLOR),
                ], spacing=8),
                ft.Row([
                    ft.Radio(value="custom", label=t("pbr_metal_custom"),
                             fill_color=PBR_COLOR),
                ]),
            ], spacing=2),
            value=S.get("pbr_metallic", PBR_PRESETS.get(S["profile"], {}).get("metallic", "black")),
            on_change=_on_metallic_mode_change,
        )

        pbr_metal_custom_block = ft.Container(
            content=ft.Column([
                ft.Container(height=4),
                make_btn(t("pbr_metal_load"), pbr_load_metallic_map, ACCENT),
                ft.Container(height=4),
                ft.Text(
                    os.path.basename(S["pbr_metallic_custom_path"])
                    if S.get("pbr_metallic_custom_path") else "—",
                    color=FG3, size=10, font_family="Consolas",
                    selectable=True,
                ),
            ], spacing=2),
            visible=(S.get("pbr_metallic") == "custom"),
        )

        def _on_roughness_mode_change(e):
            S["pbr_roughness"] = e.control.value
            persist_settings()
            page.update()
            rebuild_ui()

        pbr_rough_radio = ft.RadioGroup(
            content=ft.Column([
                ft.Row([
                    ft.Radio(value="procedural", label=t("pbr_rough_procedural"),
                             fill_color=PBR_COLOR),
                ], spacing=8),
                ft.Row([
                    ft.Radio(value="custom", label=t("pbr_rough_custom"),
                             fill_color=PBR_COLOR),
                ]),
            ], spacing=2),
            value=S.get("pbr_roughness", "procedural"),
            on_change=_on_roughness_mode_change,
        )

        pbr_rough_custom_block = ft.Container(
            content=ft.Column([
                ft.Container(height=4),
                make_btn(t("pbr_rough_load"), pbr_load_roughness_map, ACCENT),
                ft.Container(height=4),
                ft.Text(
                    os.path.basename(S["pbr_roughness_custom_path"])
                    if S.get("pbr_roughness_custom_path") else "—",
                    color=FG3, size=10, font_family="Consolas",
                    selectable=True,
                ),
            ], spacing=2),
            visible=(S.get("pbr_roughness") == "custom"),
        )

        pbr_preset_buttons = ft.Column([
            make_category_tabs(compact=True),
            ft.Container(height=4),
            make_preset_grid(compact=True),
        ], spacing=0)

        pbr_bit_radio = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="8", label=t("pbr_bit_8"),
                         fill_color=PBR_COLOR),
                ft.Radio(value="16", label=t("pbr_bit_16"),
                         fill_color=PBR_COLOR),
            ]),
            value=str(S["pbr_bit_depth"]),
            on_change=lambda e: S.update({"pbr_bit_depth": int(e.control.value)}),
        )

        if is_simple:
            pbr_params_panel = ft.Container(
                content=ft.Column([
                    ft.Text(t("pbr_params"), size=10, weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=6),
                    ft.Text(t("pbr_bit_depth"), color=FG2, size=12, font_family=FONT),
                    pbr_bit_radio,
                ], spacing=6),
                bgcolor=PANEL, border_radius=12, padding=14, width=200,
            )
        else:
            pbr_params_panel = ft.Container(
                content=ft.Column([
                    ft.Text(t("pbr_params"), size=10, weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Text(t("pbr_preset_label"), color=FG2, size=11, font_family=FONT),
                    pbr_preset_buttons,
                    ft.Divider(color=FG3, height=1),
                    ft.Text(t("pbr_metallic"), color=FG2, size=12, font_family=FONT),
                    pbr_metal_radio,
                    pbr_metal_custom_block,
                    ft.Divider(color=FG3, height=1),
                    ft.Text(t("pbr_roughness"), color=FG2, size=12, font_family=FONT),
                    pbr_rough_radio,
                    pbr_rough_custom_block,
                    ft.Container(
                        content=ft.Column([
                            make_pbr_slider(t("pbr_sl_rough_base"), "rough_base", 0.7, 0.0, 1.0, 0.05),
                            make_pbr_slider(t("pbr_sl_rough_var"), "rough_var", 0.3, 0.0, 1.0, 0.05),
                        ], spacing=6),
                        visible=(S.get("pbr_roughness") != "custom"),
                    ),
                    ft.Divider(color=FG3, height=1),
                    ft.Text(t("pbr_bit_depth"), color=FG2, size=12, font_family=FONT),
                    pbr_bit_radio,
                    ft.Divider(color=FG3, height=1),
                    make_pbr_slider(t("pbr_sl_strength"), "strength", 1.5, 0.1, 5.0, 0.1),
                    make_pbr_slider(t("pbr_sl_smooth"), "smooth", 1.5, 0.0, 5.0, 0.1),
                    make_pbr_slider(t("pbr_sl_threshold"), "threshold", 0.05, 0.0, 0.20, 0.01),
                    make_pbr_slider(t("pbr_sl_high_pass"), "high_pass", 40.0, 0.0, 100.0, 1.0),
                    make_pbr_slider(t("pbr_sl_height_blur"), "height_blur", 2.0, 0.0, 10.0, 0.5),
                    make_pbr_slider(t("pbr_sl_ao_radius"), "ao_radius", 8.0, 2.0, 30.0, 1.0),
                    make_pbr_slider(t("pbr_sl_ao_intensity"), "ao_intensity", 1.5, 0.1, 3.0, 0.1),
                ], spacing=6, scroll=ft.ScrollMode.AUTO),
                bgcolor=PANEL, border_radius=12, padding=14, width=250,
            )

        if is_simple:
            pbr_simple_btn = make_btn("🚀 " + t("pbr_gen"), pbr_do_simple_generate, SUCCESS)
            pbr_viewer_btn = make_btn(t("pbr_viewer"), pbr_open_viewer, "#00897b",
                                       disabled=(S["pbr_result"] is None))
            pbr_save_btn = make_btn(t("pbr_save"), pbr_do_save, SAVE_COLOR,
                                     disabled=(S["pbr_result"] is None))
            S["pbr_buttons"] = {"viewer": pbr_viewer_btn, "save": pbr_save_btn}
            pbr_toolbar = ft.Row([
                pbr_simple_btn,
                ft.Container(expand=True),
                pbr_viewer_btn,
                pbr_save_btn,
            ], spacing=6)
        else:
            pbr_load_btn = make_btn(t("pbr_load"), pbr_do_load, ACCENT)
            pbr_gen_btn = make_btn(t("pbr_gen"), pbr_do_generate, SUCCESS,
                                    disabled=(S["pbr_source"] is None))
            pbr_batch_btn = make_btn(t("pbr_batch"), pbr_do_batch, COMPRESS_COLOR)
            pbr_viewer_btn = make_btn(t("pbr_viewer"), pbr_open_viewer, "#00897b",
                                       disabled=(S["pbr_result"] is None))
            pbr_save_btn = make_btn(t("pbr_save"), pbr_do_save, SAVE_COLOR,
                                     disabled=(S["pbr_result"] is None))
            S["pbr_buttons"] = {
                "load": pbr_load_btn, "gen": pbr_gen_btn,
                "batch": pbr_batch_btn, "viewer": pbr_viewer_btn,
                "save": pbr_save_btn,
            }
            pbr_toolbar = ft.Row([
                pbr_load_btn,
                pbr_gen_btn,
                pbr_batch_btn,
                ft.Container(expand=True),
                pbr_viewer_btn,
                pbr_save_btn,
            ], spacing=6)

        pbr_view = ft.Container(
            content=ft.Column([
                pbr_toolbar,
                ft.Container(height=4),
                S["pbr_progress_bar"],
                S["pbr_progress_text"],
                ft.Container(height=6),
                map_row,
                ft.Container(height=6),
                ft.Row([
                    ft.Container(content=pbr_preview_box, expand=True),
                    pbr_params_panel,
                ], spacing=12, expand=True),
                ft.Container(height=8),
                log_panel_pbr,
            ], spacing=0, expand=True),
            expand=True, visible=True,
        )

        # ═══ ВКЛАДКА СЖАТИЕ ═══
        S["compress_preview"] = ft.Image(src="", visible=False, fit=ft.BoxFit.CONTAIN)
        S["compress_preview_hint"] = ft.Text(t("preview_hint"),
                                              color=FG3, size=14, font_family=FONT)

        compress_preview_box = ft.Container(
            content=ft.Stack([
                ft.Container(content=S["compress_preview_hint"],
                             alignment=ft.Alignment.CENTER, expand=True),
                ft.Container(content=S["compress_preview"],
                             alignment=ft.Alignment.CENTER, expand=True),
            ], expand=True),
            bgcolor=CARD, border_radius=12, padding=10, expand=True,
        )

        compress_open_btn = make_btn(t("load"), compress_open_file, ACCENT)
        compress_run_btn = make_btn(t("compress_run"), compress_do, COMPRESS_COLOR,
                                     disabled=True)
        compress_save_btn = make_btn(t("save"), compress_save, SAVE_COLOR,
                                      disabled=True)
        S["compress_buttons"] = {
            "open": compress_open_btn,
            "run": compress_run_btn,
            "save": compress_save_btn,
        }

        compress_single_toolbar = ft.Row([
            compress_open_btn,
            compress_run_btn,
            ft.Container(expand=True),
            compress_save_btn,
        ], spacing=6)

        compress_single_card = ft.Container(
            content=ft.Column([
                ft.Text(t("compress_single"), size=10, weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=6),
                compress_single_toolbar,
                ft.Container(height=8),
                ft.Container(
                    content=ft.Row([
                        ft.Container(content=compress_preview_box, expand=True),
                    ], expand=True),
                    expand=True,
                ),
            ], spacing=0, expand=True),
            bgcolor=PANEL, border_radius=12, padding=16, expand=True,
        )

        compress_sel_row = ft.Row([
            make_btn(t("batch_select_folder"), compress_select_folder, ACCENT),
            make_btn(t("batch_select_files"), compress_select_files, ACCENT),
            ft.Container(expand=True),
            make_btn(t("compress_batch_run"), compress_batch_run, COMPRESS_COLOR),
        ], spacing=6)

        compress_batch_card = ft.Container(
            content=ft.Column([
                ft.Text(t("compress_batch"), size=10, weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=6),
                compress_sel_row,
            ], spacing=6),
            bgcolor=PANEL, border_radius=12, padding=16,
        )

        compress_view = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        S["compress_progress_bar"],
                        S["compress_progress_text"],
                        ft.Container(height=6),
                        compress_single_card,
                        ft.Container(height=8),
                        compress_batch_card,
                        ft.Container(height=8),
                        log_panel_compress,
                    ], spacing=0, expand=True),
                    expand=True,
                ),
                build_right_panel_compress(),
            ], spacing=12, expand=True),
            expand=True, visible=True,
        )
        
        # ═══ SIMPLE MODE COMPRESS VIEW ═══
        compress_simple_card = ft.Container(
            content=ft.Column([
                ft.Text(t("compress_single"), size=10, weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=8),
                make_btn("🚀 " + t("compress_single_btn"), compress_simple_process, COMPRESS_COLOR),
                ft.Container(height=8),
                ft.Text(t("compress_simple_hint"), color=FG2, size=11,
                        font_family=FONT),
            ], spacing=0,
               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=PANEL, border_radius=12, padding=16,
            width=520,
        )

        compress_batch_simple_card = ft.Container(
            content=ft.Column([
                ft.Text(t("compress_batch"), size=10, weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=8),
                make_btn("📁 " + t("compress_batch_btn"), compress_simple_batch, COMPRESS_COLOR),
                ft.Container(height=8),
                ft.Text(t("compress_batch_hint"), color=FG2, size=11,
                        font_family=FONT),
            ], spacing=0,
               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=PANEL, border_radius=12, padding=16,
            width=520,
        )

        # ═══ ВКЛАДКА ПАКЕТНАЯ ═══
        batch_sel_row = ft.Row([
            make_btn(t("batch_select_folder"), batch_select_folder, ACCENT),
            make_btn(t("batch_select_files"), batch_select_files, ACCENT),
        ], spacing=6)

        batch_run_btn = make_btn(t("batch_run"), batch_run, SUCCESS)

        batch_info_card = ft.Container(
            content=ft.Column([
                ft.Text("✨ AI-коррекция папки", size=10,
                        weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=6),
                ft.Text(t("batch_no_files"), color=FG3, size=11, visible=False),
            ], spacing=6),
            bgcolor=PANEL, border_radius=12, padding=16,
        )

        batch_view = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        batch_sel_row,
                        ft.Container(height=8),
                        batch_info_card,
                        ft.Container(height=8),
                        batch_run_btn,
                        ft.Container(height=8),
                        S["batch_progress_bar"],
                        S["batch_progress_text"],
                        ft.Container(height=8),
                        log_panel_batch,
                    ], spacing=0, expand=True),
                    expand=True,
                ),
                build_right_panel_batch(),
            ], spacing=12, expand=True),
            expand=True, visible=True,
        )
        
        # ═══ ВКЛАДКА REALISM ═══
        realism_preview = ft.Image(src="", visible=False, fit=ft.BoxFit.CONTAIN)
        realism_hint = ft.Text(t("realism_preview_hint"),
                               color=FG3, size=14, font_family=FONT)

        realism_preview_content = ft.Stack([
            ft.Container(content=realism_hint,
                         alignment=ft.Alignment.CENTER, expand=True),
            ft.Container(content=realism_preview,
                         alignment=ft.Alignment.CENTER, expand=True),
        ], expand=True)

        realism_preview_box = ft.Container(
            content=ft.InteractiveViewer(
                content=realism_preview_content,
                min_scale=0.5,
                max_scale=8.0,
                expand=True,
            ),
            bgcolor=CARD, border_radius=12, padding=10, expand=True,
        )

        def realism_load(e):
            async def _do():
                try:
                    files = await picker.pick_files(
                        dialog_title=t("dialog_pick_title"),
                        allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                        initial_directory=_init_dir(),
                    )
                    if not files or not files[0].path:
                        return
                    fp = files[0].path
                    _remember_folder(fp)
                    img = Image.open(fp).convert("RGB")
                    S["realism_source"] = img
                    S["realism_result"] = None
                    realism_preview.src = f"data:image/png;base64,{pil_to_b64(img)}"
                    realism_preview.visible = True
                    realism_hint.visible = False
                    log(f"{t('log_loaded')} {os.path.basename(fp)}", SUCCESS)
                    page.update()
                except Exception as ex:
                    log(f"❌ {t('err')}: {ex}", DANGER)
                    page.update()
            page.run_task(_do)

        async def realism_apply(e):
            if S["realism_source"] is None:
                log("   ⚠ Сначала загрузи текстуру", WARN)
                page.update()
                return
            try:
                await show_realism_progress(t("realism_progress"))
                await asyncio.sleep(0.05)

                result = await asyncio.to_thread(
                    add_realism, S["realism_source"],
                    S["realism_grain"],
                    S["realism_highpass"],
                    S["realism_variation"],
                )
                S["realism_result"] = result
                if S.get("realism_save_btn") is not None:
                    S["realism_save_btn"].disabled = False
                realism_preview.src = f"data:image/png;base64,{pil_to_b64(result)}"
                realism_preview.visible = True
                realism_hint.visible = False
                log(t("realism_done"), SUCCESS)
                page.update()
                await asyncio.sleep(0.05)
                await hide_realism_progress()
            except Exception as ex:
                await hide_realism_progress()
                log(f"❌ {t('err')}: {ex}", DANGER)
                page.update()

        async def realism_save(e):
            if S["realism_result"] is None:
                log("   ⚠ Нечего сохранять — сначала примени фильтр", WARN)
                page.update()
                return
            try:
                path = await picker.save_file(
                    dialog_title=t("dialog_save_title"),
                    file_name="realism.png",
                    allowed_extensions=["png", "jpg", "tif"],
                    initial_directory=_init_dir(),
                )
                if not path:
                    return
                await asyncio.to_thread(
                    save_16bit_or_8bit, S["realism_result"], str(path), 16
                )
                _remember_folder(str(path))
                log(f"{t('log_saved')} {os.path.basename(str(path))}", SUCCESS)
                page.update()
            except Exception as ex:
                log(f"❌ {t('err')}: {ex}", DANGER)
                page.update()

        realism_save_btn = make_btn(t("save"), realism_save, SAVE_COLOR)
        S["realism_save_btn"] = realism_save_btn
        realism_toolbar = ft.Row([
            make_btn(t("load"), realism_load, ACCENT),
            ft.Container(expand=True),
            realism_save_btn,
        ], spacing=6)

        REALISM_PRESETS = {
            "soft":   {"grain": 0.08, "highpass": 0.20, "variation": 0.10},
            "medium": {"grain": 0.15, "highpass": 0.30, "variation": 0.20},
            "hard":   {"grain": 0.45, "highpass": 0.75, "variation": 0.55},
        }

        def apply_realism_preset(name):
            p = REALISM_PRESETS.get(name)
            if not p:
                return
            S["realism_grain"] = p["grain"]
            S["realism_highpass"] = p["highpass"]
            S["realism_variation"] = p["variation"]
            _label_key = {
                "soft": "realism_preset_soft",
                "medium": "realism_preset_medium",
                "hard": "realism_preset_hard",
            }.get(name, name)
            log(f"🎞 {t('realism_preset_log')}: {t(_label_key)}", FG2)
            rebuild_ui()

        def _realism_active_preset():
            """Определяет какой пресет сейчас активен по значениям."""
            for name, p in REALISM_PRESETS.items():
                if (abs(S["realism_grain"] - p["grain"]) < 0.001 and
                    abs(S["realism_highpass"] - p["highpass"]) < 0.001 and
                    abs(S["realism_variation"] - p["variation"]) < 0.001):
                    return name
            return None

        active_preset = _realism_active_preset()

        def make_preset_btn(name, label_key):
            active = (active_preset == name)
            return ft.Container(
                content=ft.Text(
                    t(label_key),
                    color=ON_ACCENT if active else FG2,
                    size=12, font_family=FONT,
                    weight=ft.FontWeight.W_600,
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor=ACCENT if active else CARD,
                border_radius=8,
                padding=ft.Padding.symmetric(vertical=10, horizontal=6),
                expand=True, ink=True,
                on_click=lambda e, n=name: apply_realism_preset(n),
            )

        realism_right_panel = ft.Container(
            content=ft.Column([
                ft.Text(t("realism_presets"), size=10,
                        weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=6),
                ft.Row([
                    make_preset_btn("soft", "realism_preset_soft"),
                    make_preset_btn("medium", "realism_preset_medium"),
                    make_preset_btn("hard", "realism_preset_hard"),
                ], spacing=4),

                ft.Container(height=14),
                ft.Divider(color=FG3, height=1),
                ft.Container(height=10),

                ft.Text(t("realism_params"), size=10,
                        weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=8),

                ft.Text(t("realism_grain"), color=FG2, size=11, font_family=FONT),
                ft.Slider(min=0.0, max=1.0, divisions=20,
                          value=S["realism_grain"], label="{value}",
                          active_color=ACCENT, inactive_color=INPUT,
                          on_change=lambda e: S.update({"realism_grain": e.control.value})),

                ft.Text(t("realism_highpass"), color=FG2, size=11, font_family=FONT),
                ft.Slider(min=0.0, max=1.0, divisions=20,
                          value=S["realism_highpass"], label="{value}",
                          active_color=ACCENT, inactive_color=INPUT,
                          on_change=lambda e: S.update({"realism_highpass": e.control.value})),

                ft.Text(t("realism_variation"), color=FG2, size=11, font_family=FONT),
                ft.Slider(min=0.0, max=1.0, divisions=20,
                          value=S["realism_variation"], label="{value}",
                          active_color=ACCENT, inactive_color=INPUT,
                          on_change=lambda e: S.update({"realism_variation": e.control.value})),

                ft.Container(height=14),
                make_btn(t("realism_apply"), realism_apply, SUCCESS),
            ], spacing=6, scroll=ft.ScrollMode.AUTO),
            bgcolor=PANEL, border_radius=12, padding=16, width=320,
        )

        realism_log_panel = ft.Container(height=0)

        realism_view = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        realism_toolbar,
                        ft.Container(height=6),
                        S["realism_progress_bar"],
                        S["realism_progress_text"],
                        ft.Container(height=6),
                        ft.Container(content=realism_preview_box, expand=True),
                        ft.Container(height=8),
                        realism_log_panel,
                    ], spacing=0, expand=True),
                    expand=True,
                ),
                realism_right_panel,
            ], spacing=12, expand=True),
            expand=True, visible=True,
        )

# ═══ ВКЛАДКА EXPORT ═══
        export_preview = ft.Image(src="", visible=False, fit=ft.BoxFit.CONTAIN)
        export_hint = ft.Text("📦  Выбери источник: PBR или папка",
                              color=FG3, size=14, font_family=FONT)

        export_preview_content = ft.Stack([
            ft.Container(content=export_hint,
                         alignment=ft.Alignment.CENTER, expand=True),
            ft.Container(content=export_preview,
                         alignment=ft.Alignment.CENTER, expand=True),
        ], expand=True)

        export_preview_box = ft.Container(
            content=ft.InteractiveViewer(
                content=export_preview_content,
                min_scale=0.5, max_scale=8.0, expand=True,
            ),
            bgcolor=CARD, border_radius=12, padding=10, expand=True,
        )

        def _refresh_export_preview():
            pil = export_build_preview_pil()
            if pil is None:
                export_hint.visible = True
                export_preview.visible = False
            else:
                export_preview.src = f"data:image/png;base64,{pil_to_b64(pil)}"
                export_preview.visible = True
                export_hint.visible = False

        _refresh_export_preview()

        def _chan_btn(key, label):
            active = (S.get("export_preview_channel", "rgb") == key)
            return ft.Container(
                content=ft.Text(label,
                                color=ON_ACCENT if active else FG2,
                                size=12, font_family=FONT,
                                weight=ft.FontWeight.W_600),
                bgcolor=ACCENT if active else CARD,
                border_radius=8,
                padding=ft.Padding.symmetric(vertical=6, horizontal=12),
                ink=True,
                on_click=lambda e, k=key: export_set_channel(k),
            )

        export_channel_row = ft.Row([
            _chan_btn("r", "R"),
            _chan_btn("g", "G"),
            _chan_btn("b", "B"),
            _chan_btn("a", "A"),
            _chan_btn("rgb", "RGB"),
            _chan_btn("rgba", "RGBA"),
        ], spacing=4)

        export_toolbar = ft.Row([
            make_btn("⚙️ Из текущего PBR", export_load_from_pbr, ACCENT),
            make_btn("📂 Загрузить из папки", export_load_from_folder, ACCENT),
            ft.Container(expand=True),
            make_btn("⚙️ Упаковать", export_pack, SUCCESS),
            make_btn("💾 Сохранить все", export_save, SAVE_COLOR,
                     disabled=(S.get("export_packed") is None)),
        ], spacing=6)

        export_source_label = ft.Text(
            f"Источник: {S.get('export_source_label') or '—'}",
            color=FG3, size=11, font_family="Consolas",
        )

        export_view = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        export_toolbar,
                        ft.Container(height=4),
                        export_source_label,
                        ft.Container(height=4),
                        S["pbr_progress_bar"],
                        S["pbr_progress_text"],
                        ft.Container(height=6),
                        export_channel_row,
                        ft.Container(height=6),
                        ft.Container(content=export_preview_box, expand=True),
                    ], spacing=0, expand=True),
                    expand=True,
                ),
                build_right_panel_export(),
            ], spacing=12, expand=True),
            expand=True, visible=True,
        )

        compress_view_simple = ft.Container(
            content=ft.Column([
                S["compress_progress_bar"],
                S["compress_progress_text"],
                ft.Container(height=8),
                compress_simple_card,
                ft.Container(height=8),
                compress_batch_simple_card,
                ft.Container(height=8),
                log_panel_compress,
            ], spacing=0, expand=True,
               horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, visible=True,
        )

        # ═══ NavigationRail ═══
        def _rail_label(key):
            """Убирает emoji из начала строки, оставляет только текст."""
            s = t(key)
            parts = s.split(" ", 1)
            return parts[1] if len(parts) > 1 else s

        RAIL_TABS = [
            ("single", "🖼", _rail_label("tab_single")),
            ("batch", "🗂", _rail_label("tab_batch")),
            ("pbr", "🎨", _rail_label("tab_pbr")),
            ("export", "🎮", _rail_label("tab_export")),
            ("compress", "🗜", _rail_label("tab_compress")),
            ("realism", "🎞", _rail_label("tab_realism")),
        ]

        active_keys = [k for k, _, _ in RAIL_TABS
                       if not (is_simple and k not in ("single", "pbr", "export", "compress"))]

        rail_destinations = []
        for key, icon, label in RAIL_TABS:
            if key not in active_keys:
                continue
            rail_destinations.append(
                ft.NavigationRailDestination(
                    icon=ft.Text(icon, size=22),
                    selected_icon=ft.Text(icon, size=22),
                    label=label,
                )
            )

        content_holder = ft.Container(expand=True)

        views_map = {
            "single": single_view,
            "batch": batch_view,
            "pbr": pbr_view,
            "export": export_view,
            "compress": compress_view_simple if is_simple else compress_view,
            "realism": realism_view,
        }

        if S["active_tab"] not in active_keys:
            S["active_tab"] = "single"

        def set_tab(name):
            if name not in active_keys:
                name = "single"
            S["active_tab"] = name
            content_holder.content = views_map[name]
            idx = active_keys.index(name)
            if nav_rail.selected_index != idx:
                nav_rail.selected_index = idx
            page.update()

        def on_rail_change(e):
            idx = e.control.selected_index
            if 0 <= idx < len(active_keys):
                name = active_keys[idx]
                S["active_tab"] = name
                content_holder.content = views_map[name]
                page.update()

        nav_rail = ft.NavigationRail(
            selected_index=active_keys.index(S["active_tab"]),
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=110,
            min_extended_width=140,
            group_alignment=-0.9,
            destinations=rail_destinations,
            on_change=on_rail_change,
            bgcolor=PANEL,
            indicator_color=ACCENT,
        )

        content_holder.content = views_map[S["active_tab"]]

        # ═══ ХЕДЕР ═══
        theme_icon = "☀" if S["theme"] == "dark" else "🌙"
        mode_label = t("mode_btn_advanced") if is_simple else t("mode_btn_simple")

        header = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Row([
                        ft.Text("◐ Albedolizer", size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ACCENT, font_family=FONT),
                        ft.Container(
                            content=ft.Text("v1.7.3-beta", size=10, color=FG2,
                                            font_family=FONT,
                                            weight=ft.FontWeight.W_600),
                            bgcolor=CARD, border_radius=6,
                            padding=ft.Padding.symmetric(vertical=2, horizontal=8),
                        ),
                    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Text(t("subtitle"), size=11, color=FG2, font_family=FONT),
                ], spacing=2),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Text(mode_label, color=FG, size=13,
                                    font_family=FONT, weight=ft.FontWeight.W_600),
                    bgcolor=CARD, border_radius=8,
                    padding=ft.Padding.symmetric(vertical=10, horizontal=16),
                    ink=True, on_click=toggle_mode,
                ),
                ft.Container(width=8),
                ft.Container(
                    content=ft.Text(theme_icon, color=FG, size=14,
                                    font_family=FONT),
                    bgcolor=CARD, border_radius=8,
                    padding=ft.Padding.symmetric(vertical=10, horizontal=16),
                    ink=True, on_click=toggle_theme,
                    tooltip="Toggle theme",
                ),
                ft.Container(width=8),
                ft.Container(
                    content=ft.Text(t("lang_btn"), color=FG, size=13,
                                    font_family=FONT, weight=ft.FontWeight.W_600),
                    bgcolor=CARD, border_radius=8,
                    padding=ft.Padding.symmetric(vertical=10, horizontal=16),
                    ink=True, on_click=toggle_lang,
                ),
                ft.Container(width=8),
                ft.Container(
                    content=ft.Text(t("info_btn"), color=FG, size=13,
                                    font_family=FONT, weight=ft.FontWeight.W_600),
                    bgcolor=CARD, border_radius=8,
                    padding=ft.Padding.symmetric(vertical=10, horizontal=16),
                    ink=True, on_click=open_info,
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(vertical=14, horizontal=24),
            bgcolor=PANEL,
        )

        body = ft.Row([
            nav_rail,
            ft.Container(
                content=content_holder,
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                expand=True,
            ),
        ], spacing=0, expand=True)

        # ═══ BottomSheet-лог ═══
        collapsed_preview = ft.Text(
            "", color=FG2, size=11, font_family="Consolas",
            selectable=False, expand=True, max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        S["log_collapsed_preview"] = collapsed_preview

        log_toggle_icon = ft.Text("▲", color=FG2, size=12, font_family=FONT)

        log_body = ft.Container(
            content=S["log_column_bottom"],
            height=130,
            visible=False,
            bgcolor=CARD,
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        )

        def toggle_log(e=None):
            S["log_expanded"] = not S.get("log_expanded", False)
            if S["log_expanded"]:
                log_body.visible = True
                log_toggle_icon.value = "▼"
                collapsed_preview.visible = False
            else:
                log_body.visible = False
                log_toggle_icon.value = "▲"
                collapsed_preview.visible = True
            page.update()

        def clear_log_bottom(e=None):
            S["log_lines"].clear()
            refresh_log()
            page.update()

        log_header = ft.Container(
            content=ft.Row([
                ft.Text("📋", size=14, font_family=FONT),
                ft.Text(t("log_title"), size=11, color=FG3,
                        font_family=FONT, weight=ft.FontWeight.W_600),
                ft.Container(width=8),
                collapsed_preview,
                log_toggle_icon,
                ft.Container(width=6),
                ft.Container(
                    content=ft.Text("🗑", size=13, font_family=FONT),
                    border_radius=6,
                    padding=ft.Padding.symmetric(vertical=4, horizontal=8),
                    ink=True,
                    on_click=clear_log_bottom,
                    tooltip="Clear log",
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            bgcolor=PANEL,
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            on_click=toggle_log,
            ink=True,
        )

        log_bottom_sheet = ft.Container(
            content=ft.Column([
                log_header,
                log_body,
            ], spacing=0, tight=True),
            bgcolor=PANEL,
        )

        page.add(
            ft.Column([
                header,
                ft.Container(content=body, expand=True),
                log_bottom_sheet,
            ], spacing=0, expand=True)
        )

    def rebuild_ui():
        page.controls.clear()
        build_screen()
        page.update()

    build_screen()
    log(t("welcome_1"), FG2)
    log(t("welcome_2"), FG2)
    page.update()

    # ═══ Глобальные хоткеи ═══
    page.on_keyboard_event = on_keyboard

    # ═══ Welcome при первом запуске ═══
    if not S.get("first_launch_done", False):
        import asyncio as _aio
        async def _show_welcome_later():
            await _aio.sleep(0.4)
            show_welcome_dialog()
        page.run_task(_show_welcome_later)


if __name__ == "__main__":
    ft.run(main)