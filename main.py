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
from translations import T
from settings import load_settings, save_settings

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
        "corrected": None,
        "profile": USER_SETTINGS.get("profile", "metal"),
        "profile_category": USER_SETTINGS.get("profile_category", "metal"),
        "correction_mode": USER_SETTINGS.get("correction_mode", "ai"),
        "ai_model": USER_SETTINGS.get("ai_model", DEFAULT_AI_MODEL),
        "soap_fix_strength": 1.0,
        "saturation_boost": 1.15,
        "pbr_bit_depth": 8,
        "last_op": None,
        "lang": _detect_system_lang(),
        "theme": "dark",
        "ui_mode": "simple",
        "log_lines": [],
        "stats_lines": [],
        "pbr_source": None,
        "pbr_source_path": None,
        "pbr_result": None,
        "pbr_current_map": "albedo",
        "pbr_metallic": "black",
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
        "compress_files": [],
        "active_tab": "single",
        "tiling_mode": False,
        "compress_original": None,
        "compress_corrected": None,
        "compress_path": None,
    }

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
    page.title = "Albedolizer v1.6.1-beta"

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
        # Ищем сначала внутри exe, потом рядом с exe
        _meipass = getattr(sys, '_MEIPASS', None)
        _exe_dir = os.path.dirname(sys.executable)
        _icon_dir = _meipass if (_meipass and os.path.exists(os.path.join(_meipass, "icon.ico"))) else _exe_dir
        _icon_path = os.path.join(_icon_dir, "icon.ico")
    else:
        _icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    if os.path.exists(_icon_path):
        page.window.icon = _icon_path

    if getattr(sys, 'frozen', False):
        # Ищем сначала внутри exe (_MEIPASS), потом рядом с exe
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

    def get_luminance(pil):
        arr = np.array(pil.convert("RGB")).astype(np.float32)
        return 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]

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
    S["log_column"] = ft.ListView(spacing=3, auto_scroll=True, expand=True, padding=4)
    S["log_column_batch"] = ft.ListView(spacing=3, auto_scroll=True, expand=True, padding=4)
    S["log_column_pbr"] = ft.ListView(spacing=3, auto_scroll=True, expand=True, padding=4)
    S["log_column_compress"] = ft.ListView(spacing=3, auto_scroll=True, expand=True, padding=4)

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
    # CLIP классификатор (ленивая загрузка — при первом использовании)
    S["clip"] = CLIPMaterialClassifier()
    S["buttons"] = {}

    def log(text, color=None):
        S["log_lines"].append((text, color or FG2))
        if len(S["log_lines"]) > 200:
            S["log_lines"].pop(0)
        refresh_log()

    def refresh_log():
        for lc in (S["log_column"], S["log_column_batch"],
                   S["log_column_pbr"], S["log_column_compress"]):
            lc.controls.clear()
            for txt, col in S["log_lines"]:
                lc.controls.append(
                    ft.Text(txt, color=col, size=13, font_family="Consolas",
                            selectable=True, expand=True)
                )

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
            S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(heatmap)}"

    async def do_check(e):
        if S["original"] is None:
            return
        await show_progress(t("progress_check"))
        await asyncio.sleep(0.1)
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
                S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(result)}"
                log("", FG2)
                log(t("log_fix_done"), SUCCESS)

                await asyncio.sleep(0.1)
                run_check(result, False)
                page.update()

                if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
                if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = False
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
                S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(ai_result)}"
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
                S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(result)}"
                log("", FG2)
                log(t("log_fix_done"), SUCCESS)

                await asyncio.sleep(0.1)
                run_check(result, False)
                page.update()

                if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
                if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = False
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
        S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(S['original'])}"
        log(t("log_reset"), FG2)
        if S["buttons"].get("save"): S["buttons"]["save"].disabled = True
        if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = True
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
            
            # Ленивая загрузка CLIP
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
            
            # Классификация
            profile, conf, top5 = await asyncio.to_thread(
                S["clip"].classify, S["original"]
            )
            
            if profile is None:
                log(t("auto_detect_fail"), WARN)
                await hide_progress()
                return
            
            # Устанавливаем профиль
            old_profile = S["profile"]
            S["profile"] = profile
            
            # Определяем категорию
            from config import PROFILE_CATEGORIES
            for cat_key, cat in PROFILE_CATEGORIES.items():
                if profile in cat["items"]:
                    S["profile_category"] = cat_key
                    break
            
            # Лог
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
            
            # Пересохраняем настройки
            persist_settings()
            
            await hide_progress()
            rebuild_ui()
        except Exception as ex:
            await hide_progress()
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def do_simple_process(e):
        """Simple mode: открыть → AI → saturation → результат."""
        try:
            files = await picker.pick_files(
                dialog_title=t("dialog_pick_title"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
            )
            if not files or not files[0].path:
                return
            fp = files[0].path

            await show_progress(t("progress_load"))
            await asyncio.sleep(0.1)

            img = Image.open(fp).convert("RGB")
            S["image_path"] = fp
            S["original"] = img
            S["corrected"] = None
            S["last_op"] = None
            S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(img)}"
            S["preview_image"].visible = True

            log("", FG2)
            log(f"{t('log_loaded')} {os.path.basename(fp)}", SUCCESS)
            log(f"{t('log_type')} {profile_label(S['profile'])}", FG2)
            page.update()

            await show_progress(t("progress_fix"))
            await asyncio.sleep(0.1)

            ai_result, ai_ok = await asyncio.to_thread(smart_correct_ai, img)

            if ai_ok and ai_result is not None:
                result = ai_result
            else:
                log("   → AI недоступен. Применяется fallback.", WARN)
                result = await asyncio.to_thread(
                    smart_correct_fallback, img, S["profile"]
                )

            # Saturation boost (1.15)
            result = await asyncio.to_thread(boost_saturation, result, 1.15)

            S["corrected"] = result
            S["last_op"] = "corrected"
            S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(result)}"
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
            )
            if files and len(files) > 0:
                fp = files[0].path
                if fp:
                    await show_progress(t("progress_load"))
                    await asyncio.sleep(0.1)

                    img = Image.open(fp).convert("RGB")
                    S["image_path"] = fp
                    S["original"] = img
                    S["corrected"] = None
                    S["last_op"] = None
                    S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(img)}"
                    S["preview_image"].visible = True

                    log("", FG2)
                    log(f"{t('log_loaded')} {os.path.basename(fp)}", SUCCESS)
                    log(f"{t('log_type')} {profile_label(S['profile'])}", FG2)
                    log(t("log_click_check"), FG2)

                    if S["buttons"].get("check"): S["buttons"]["check"].disabled = False
                    if S["buttons"].get("fix"): S["buttons"]["fix"].disabled = True
                    if S["buttons"].get("save"): S["buttons"]["save"].disabled = True
                    if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = True
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
            )
            if path and S["corrected"] is not None:
                S["corrected"].save(str(path))
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
            )
            if files and len(files) > 0:
                fp = files[0].path
                if fp:
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
            )
            if not path:
                return

            S["compress_progress_text"].value = "💾 Сохранение..."
            S["compress_progress_text"].visible = True
            S["compress_progress_bar"].value = None
            S["compress_progress_bar"].visible = True
            page.update()
            await asyncio.sleep(0.05)

            await asyncio.to_thread(S["compress_corrected"].save, str(path))
            log(f"{t('log_saved')} {os.path.basename(str(path))}", SUCCESS)

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
            )
            if not files:
                return
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
        for i, fp in enumerate(files, 1):
            try:
                img = Image.open(fp).convert("RGB")
                result = img.convert("LAB").convert("RGB")
                base = os.path.splitext(os.path.basename(fp))[0]
                result.save(str(os.path.join(out_dir, f"{base}.png")))
                img.close()
                count += 1
                log(f"  [{i}/{total}] ✓ {os.path.basename(fp)}", SUCCESS)
                update_compress_progress(i, total)
                if i % 5 == 0:
                    gc.collect()
                await asyncio.sleep(0.01)
            except Exception as ex:
                log(f"  ✗ {os.path.basename(fp)}: {ex}", DANGER)
                update_compress_progress(i, total)

        log(f"✅ {t('batch_processed')} {count} / {total}", SUCCESS)
        log(f"📁 {out_dir}", FG2)
        update_compress_progress(total, total, f"{t('batch_done')}: {count} / {total}")
        S["compress_files"] = []
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
            )
            if not files:
                return
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
        sem = asyncio.Semaphore(3)

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
                    result.save(str(out_path))
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

    # ═══ PBR-ОБРАБОТЧИКИ ═══
    async def pbr_do_load(e):
        try:
            files = await picker.pick_files(
                dialog_title=t("pbr_dialog_pick"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
            )
            if not files:
                return
            fp = files[0].path
            if not fp:
                return
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
                metallic_mode=PBR_PRESETS.get(S["profile"], {}).get("metallic", S["pbr_metallic"]),
            )
            S["pbr_result"] = result
            log(t("pbr_log_gen_done"), SUCCESS)

            if S["pbr_buttons"].get("save"): S["pbr_buttons"]["save"].disabled = False
            if S["pbr_buttons"].get("viewer"): S["pbr_buttons"]["viewer"].disabled = False
            page.update()

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
            )
            if not files or not files[0].path:
                return
            fp = files[0].path
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

            # Если слайдеры уже есть — используем их, иначе пресет
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
                    metallic_mode=PBR_PRESETS.get(S["profile"], {}).get("metallic", S["pbr_metallic"]),
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
                    metallic_mode=preset.get("metallic", "black"),
                )

            S["pbr_result"] = result
            log(t("pbr_log_gen_done"), SUCCESS)

            if S["pbr_buttons"].get("save"): S["pbr_buttons"]["save"].disabled = False
            if S["pbr_buttons"].get("viewer"): S["pbr_buttons"]["viewer"].disabled = False
            page.update()

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
            bit_depth = S.get("pbr_bit_depth", 8)
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

            # Сохраняем карты во временную папку
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

            # Если albedo нет в result — берём из pbr_source
            if "albedo" not in paths and S["pbr_source"] is not None:
                p = os.path.join(tmpdir, "albedo.png")
                await asyncio.to_thread(S["pbr_source"].save, p)
                paths["albedo"] = p

            # Определяем путь к viewer
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

            sl = S["pbr_sliders"]
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
                "metallic_mode": PBR_PRESETS.get(S["profile"], {}).get("metallic", S["pbr_metallic"]),
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
                    bit_depth = S.get("pbr_bit_depth", 8)
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

    def pbr_batch_prev(e=None):
        keys = list(S["pbr_batch_results"].keys())
        if not keys:
            return
        S["pbr_batch_index"] = (S["pbr_batch_index"] - 1) % len(keys)
        pbr_load_batch_texture(keys[S["pbr_batch_index"]])
        for k, b in S["pbr_map_buttons"].items():
            b.bgcolor = ACCENT if k == S["pbr_current_map"] else CARD
            b.content.color = ON_ACCENT if k == S["pbr_current_map"] else FG2
        page.update()

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
            S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(result)}"
            log(t("soap_fix_done"), SUCCESS)

            if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
            if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = False

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
            S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(result)}"
            log(t("sat_done"), SUCCESS)

            if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
            if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = False

            page.update()
            await asyncio.sleep(0.1)
            await hide_progress()
        except Exception as ex:
            await hide_progress()
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    def toggle_tiling(e):
        S["tiling_mode"] = not S["tiling_mode"]
        img = None
        if S["corrected"] is not None:
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
                0.6, 1.0, 0.3, "smootherstep"
            )
            S["corrected"] = result
            S["last_op"] = "seamless"
            S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(result)}"
            log(t("seamless_done"), SUCCESS)

            if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
            if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = False

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
                        ft.Text("1.6.1-beta", color=FG, size=12,
                                font_family="Consolas", weight=ft.FontWeight.W_600)]),
                ft.Row([ft.Text(f"{t('about_build')}:", color=FG3, size=12,
                                font_family=FONT, width=100),
                        ft.Text("2026-09-19", color=FG, size=12,
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
                S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(result)}"
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
        # Если уходим в Simple — переключаемся на Single если были на Batch/Compress
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
            "window": {
                "width": page.window.width or 1280,
                "height": page.window.height or 820,
            }
        })

    def build_screen():
        is_simple = S["ui_mode"] == "simple"
        buttons = S["buttons"]

        # ═══ SINGLE VIEW ═══
        if is_simple:
            # Simple: одна кнопка + превью + пресеты
            buttons["load"] = make_btn("🚀 " + t("fix"), do_simple_process, SUCCESS)
            buttons["save"] = make_btn(t("save"), open_save, SAVE_COLOR,
                                        disabled=(S["corrected"] is None))

            simple_toolbar = ft.Row([
                buttons["load"],
                ft.Container(expand=True),
                buttons["save"],
            ], spacing=6)

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

            log_panel = ft.Container(
                content=ft.Column([
                    ft.Text(t("log_title"), size=10, weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=4),
                    S["log_column"],
                ], spacing=4, expand=True),
                bgcolor=CARD, border_radius=12, padding=12,
                expand=1,
            )

            single_view = ft.Container(
                content=ft.Column([
                    simple_toolbar,
                    ft.Container(height=4),
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
            # Advanced — всё как было
            buttons["load"] = make_btn(t("load"), open_file, ACCENT)
            buttons["check"] = make_btn(t("check"), do_check, ACCENT,
                                         disabled=(S["original"] is None))
            buttons["fix"] = make_btn(t("fix"), do_auto_correct, SUCCESS, disabled=True)
            buttons["save"] = make_btn(t("save"), open_save, SAVE_COLOR,
                                        disabled=(S["corrected"] is None))
            buttons["reset"] = make_btn(t("reset"), do_reset, RESET_COLOR,
                                         disabled=(S["corrected"] is None))

            toolbar = ft.Row([
                buttons["load"],
                buttons["check"],
                buttons["fix"],
                ft.Container(expand=True),
                buttons["reset"],
                buttons["save"],
            ], spacing=6)

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

            log_panel = ft.Container(
                content=ft.Column([
                    ft.Text(t("log_title"), size=10, weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=4),
                    S["log_column"],
                ], spacing=4, expand=True),
                bgcolor=CARD, border_radius=12, padding=12,
                expand=1,
            )

            single_view = ft.Container(
                content=ft.Column([
                    toolbar,
                    ft.Container(height=4),
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

        log_panel_pbr = ft.Container(
            content=ft.Column([
                ft.Text(t("log_title"), size=10, weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=4),
                S["log_column_pbr"],
            ], spacing=4, expand=True),
            bgcolor=CARD, border_radius=12, padding=12,
            height=140,
        )

        log_panel_batch = ft.Container(
            content=ft.Column([
                ft.Text(t("log_title"), size=10, weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=4),
                S["log_column_batch"],
            ], spacing=4, expand=True),
            bgcolor=CARD, border_radius=12, padding=12,
            expand=1,
        )

        log_panel_compress = ft.Container(
            content=ft.Column([
                ft.Text(t("log_title"), size=10, weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=4),
                S["log_column_compress"],
            ], spacing=4, expand=True),
            bgcolor=CARD, border_radius=12, padding=12,
            expand=1,
        )

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
            content=ft.Stack([
                ft.Container(content=pbr_preview_hint,
                             alignment=ft.Alignment.CENTER, expand=True),
                ft.Container(content=pbr_preview,
                             alignment=ft.Alignment.CENTER, expand=True),
                ft.Container(content=batch_nav_panel,
                             alignment=ft.Alignment.BOTTOM_RIGHT,
                             padding=12),
            ], expand=True),
            bgcolor=CARD, border_radius=12, padding=10, expand=True,
        )

        if S["pbr_result"] and S.get("pbr_batch_selected"):
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

        def show_pbr_map(key):
            S["pbr_current_map"] = key
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
            for k, b in map_buttons.items():
                b.bgcolor = ACCENT if k == key else CARD
                b.content.color = ON_ACCENT if k == key else FG2
            page.update()

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

        pbr_metal_radio = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="black", label=t("pbr_metal_black"),
                         fill_color=PBR_COLOR),
                ft.Radio(value="white", label=t("pbr_metal_white"),
                         fill_color=PBR_COLOR),
            ]),
            value=PBR_PRESETS.get(S["profile"], {}).get("metallic", S["pbr_metallic"]),
            on_change=lambda e: S.update({"pbr_metallic": e.control.value}),
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

        # ═══ PBR PANEL — Simple vs Advanced ═══
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
                    make_pbr_slider(t("pbr_sl_rough_base"), "rough_base", 0.7, 0.0, 1.0, 0.05),
                    make_pbr_slider(t("pbr_sl_rough_var"), "rough_var", 0.3, 0.0, 1.0, 0.05),
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
            expand=True, visible=False,
        )

        # ═══ ВКЛАДКА СЖАТИЕ (только Advanced) ═══
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
            expand=True, visible=False,
        )

        # ═══ ВКЛАДКА ПАКЕТНАЯ (только Advanced) ═══
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
            expand=True, visible=False,
        )

        tab_btns_local = {}

        def set_tab(name):
            S["active_tab"] = name
            for k, c in tab_btns_local.items():
                c.bgcolor = ACCENT if k == name else CARD
                c.content.color = ON_ACCENT if k == name else FG
            single_view.visible = name == "single"
            pbr_view.visible = name == "pbr"
            if not is_simple:
                compress_view.visible = name == "compress"
                batch_view.visible = name == "batch"
            page.update()

        def make_tab(key, label):
            c = ft.Container(
                content=ft.Text(label, color=ON_ACCENT, size=14, font_family=FONT,
                                weight=ft.FontWeight.W_600),
                bgcolor=ACCENT if key == "single" else CARD,
                border_radius=10,
                padding=ft.Padding.symmetric(vertical=12, horizontal=24),
                ink=True, on_click=lambda e, k=key: set_tab(k),
            )
            tab_btns_local[key] = c
            return c

        if is_simple:
            tabs_row = ft.Row([
                make_tab("single", t("tab_single")),
                make_tab("pbr", t("tab_pbr")),
            ], spacing=8)
        else:
            tabs_row = ft.Row([
                make_tab("single", t("tab_single")),
                make_tab("batch", t("tab_batch")),
                make_tab("pbr", t("tab_pbr")),
                make_tab("compress", t("tab_compress")),
            ], spacing=8)

        set_tab(S["active_tab"])

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
                            content=ft.Text("v1.6.1-beta", size=10, color=FG2,
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

        if is_simple:
            views_stack = ft.Stack([single_view, pbr_view], expand=True)
        else:
            views_stack = ft.Stack([single_view, pbr_view, compress_view, batch_view],
                                    expand=True)

        body = ft.Container(
            content=ft.Column([
                ft.Container(height=12),
                tabs_row,
                ft.Container(height=12),
                ft.Container(content=views_stack, expand=True),
            ], spacing=0, expand=True),
            padding=ft.Padding.symmetric(horizontal=24),
            expand=True,
        )

        page.add(
            ft.Column([header, body], spacing=0, expand=True)
        )

    def rebuild_ui():
        page.controls.clear()
        build_screen()
        page.update()

    build_screen()
    log(t("welcome_1"), FG2)
    log(t("welcome_2"), FG2)
    page.update()


if __name__ == "__main__":
    ft.run(main)