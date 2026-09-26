"""
core/state.py — состояние приложения (словарь S), сохранение настроек.

Импортирует только settings.py (load_settings/save_settings) и config.py.
Не знает про Flet.
"""

import os
from config import (
    PROFILE_CATEGORIES, DEFAULT_AI_MODEL,
)


def _detect_system_lang() -> str:
    """Windows API → 'ru' если русский, иначе 'en'."""
    try:
        import ctypes
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        primary = lang_id & 0x03FF
        return "ru" if primary == 0x19 else "en"
    except Exception:
        return "en"


def create_state(user_settings: dict) -> dict:
    """
    Собирает словарь S из user_settings (то, что отдал load_settings()).
    Ничего не делает с UI. Просто данные.
    """
    S = {
        # ─── Single ───
        "image_path": None,
        "original": None,
        "file_info_label": None,
        "corrected": None,
        "profile": user_settings.get("profile", "metal"),
        "profile_category": user_settings.get("profile_category", "metal"),
        "correction_mode": user_settings.get("correction_mode", "ai"),
        "ai_model": user_settings.get("ai_model", DEFAULT_AI_MODEL),
        "soap_fix_strength": user_settings.get("soap_fix_strength", 1.0),
        "saturation_boost": user_settings.get("saturation_boost", 1.15),
        "last_op": None,
        "show_original": False,
        "need_fix": False,
        "lang": user_settings.get("lang") or _detect_system_lang(),
        "theme": user_settings.get("theme", "dark"),
        "ui_mode": user_settings.get("ui_mode", "simple"),
        "log_lines": [],
        "stats_lines": [],
        "tiling_mode": user_settings.get("tiling_mode", False),
        "seamless_hipass": user_settings.get("seamless_hipass", True),
        "batch_files": [],
        "batch_threads": user_settings.get("batch_threads", 3),
        "compress_files": [],
        "compress_original": None,
        "compress_corrected": None,
        "compress_path": None,
        "active_tab": "single",
        "last_folder": user_settings.get("last_folder", ""),

        # ─── PBR ───
        "pbr_bit_depth": user_settings.get("pbr_bit_depth", 16),
        "pbr_bit_depth_per_map": user_settings.get("pbr_bit_depth_per_map", {
            "albedo": 8, "height": 16, "normal": 16, "ao": 8,
            "roughness": 8, "metallic": 8, "edge": 8, "orm": 8,
        }),
        "pbr_source": None,
        "pbr_source_path": None,
        "pbr_result": None,
        "pbr_current_map": user_settings.get("pbr_current_map", "albedo"),
        "pbr_metallic": user_settings.get("pbr_metallic", "black"),
        "pbr_metallic_custom": None,
        "pbr_metallic_custom_path": None,
        "pbr_metal_target_rgb": None,
        "pbr_metal_tolerance": user_settings.get("pbr_metal_tolerance", 0.15),
        "pbr_metal_softness": user_settings.get("pbr_metal_softness", 0.05),
        "pbr_metal_negative_rgb": None,
        "pbr_metal_negative_tolerance":
            user_settings.get("pbr_metal_negative_tolerance", 0.10),
        "pbr_roughness": user_settings.get("pbr_roughness", "procedural"),
        "pbr_roughness_custom": None,
        "pbr_roughness_custom_path": None,
        "pbr_sliders": {},
        "pbr_values": {
            "height_blur": user_settings.get("pbr_height_blur", 2.0),
            "strength": user_settings.get("pbr_strength", 1.5),
            "smooth": user_settings.get("pbr_smooth", 1.5),
            "threshold": user_settings.get("pbr_threshold", 0.05),
            "high_pass": user_settings.get("pbr_high_pass", 40.0),
            "ao_radius": user_settings.get("pbr_ao_radius", 8.0),
            "ao_intensity": user_settings.get("pbr_ao_intensity", 1.5),
            "rough_base": user_settings.get("pbr_rough_base", 0.7),
            "rough_var": user_settings.get("pbr_rough_var", 0.3),
            "rough_detail": user_settings.get("rough_detail", 1.0),
        },
        "pbr_preview": None,
        "pbr_preview_hint": None,
        "pbr_map_buttons": {},
        "pbr_batch_results": {},
        "pbr_batch_selected": None,
        "pbr_batch_index": 0,
        "pbr_batch_label": None,
        "pbr_batch_nav_panel": None,

        # ─── Realism ───
        "realism_grain": user_settings.get("realism_grain", 0.15),
        "realism_highpass": user_settings.get("realism_highpass", 0.30),
        "realism_variation": user_settings.get("realism_variation", 0.20),
        "realism_source": None,
        "realism_result": None,

        # ─── Viewer ───
        "viewer_tile_x": 4,
        "viewer_tile_y": 3,

        # ─── Export ───
        "export_source": None,
        "export_source_label": None,
        "export_packed": None,
        "export_normal_out": None,
        "export_engine": user_settings.get("export_engine", "unity_hdrp"),
        "export_normal_format":
            user_settings.get("export_normal_format", "opengl"),
        "export_detail_mode": user_settings.get("export_detail_mode", "edge"),
        "export_custom_detail": None,
        "export_bit_depth": user_settings.get("export_bit_depth", 8),
        "export_preview_channel": "rgb",

        # ─── Misc ───
        "first_launch_done": user_settings.get("first_launch_done", False),
        "log_expanded": False,

        # ─── UI refs (заполняются в main.py при сборке) ───
        "log_column_bottom": None,
        "log_collapsed_preview": None,
        "stats_column": None,
        "preview_image": None,
        "preview_image_src": None,
        "preview_image_visible": False,
        "progress_bar": None,
        "progress_text": None,
        "pbr_progress_bar": None,
        "pbr_progress_text": None,
        "batch_progress_bar": None,
        "batch_progress_text": None,
        "compress_progress_bar": None,
        "compress_progress_text": None,
        "realism_progress_bar": None,
        "realism_progress_text": None,
        "compress_preview": None,
        "compress_preview_hint": None,
        "realism_save_btn": None,
        "buttons": {},
        "pbr_buttons": {},
        "compress_buttons": {},
        "pbr_params_ref": None,
        "update_pbr_preview": None,
    }

    # Валидация: profile ∈ profile_category
    cat_items = PROFILE_CATEGORIES.get(S["profile_category"], {}).get("items", [])
    if S["profile"] not in cat_items:
        for ck, cat in PROFILE_CATEGORIES.items():
            if S["profile"] in cat["items"]:
                S["profile_category"] = ck
                break
        else:
            S["profile"] = "metal"
            S["profile_category"] = "metal"

    return S


def persist_settings(S: dict, save_fn, page=None):
    """
    Сохраняет текущие настройки через save_fn (settings.save_settings).

    page — опционально, если нужно сохранить размер окна.
    """
    data = {
        "lang": S.get("lang"),
        "theme": S.get("theme"),
        "ui_mode": S.get("ui_mode"),
        "profile": S.get("profile"),
        "profile_category": S.get("profile_category"),
        "correction_mode": S.get("correction_mode"),
        "ai_model": S.get("ai_model"),
        "soap_fix_strength": S.get("soap_fix_strength"),
        "saturation_boost": S.get("saturation_boost"),
        "pbr_bit_depth": S.get("pbr_bit_depth"),
        "pbr_bit_depth_per_map": S.get("pbr_bit_depth_per_map", {}),
        "pbr_values": S.get("pbr_values", {}),
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
        "pbr_metal_tolerance": S.get("pbr_metal_tolerance", 0.15),
        "pbr_metal_softness": S.get("pbr_metal_softness", 0.05),
        "pbr_metal_negative_tolerance":
            S.get("pbr_metal_negative_tolerance", 0.10),
        "pbr_roughness": S.get("pbr_roughness", "procedural"),
        "tiling_mode": S.get("tiling_mode", False),
        "pbr_current_map": S.get("pbr_current_map", "albedo"),
        "first_launch_done": S.get("first_launch_done", False),
    }
    if page is not None:
        try:
            data["window"] = {
                "width": page.window.width or 1280,
                "height": page.window.height or 820,
            }
        except Exception:
            pass
    save_fn(data)


# ═══════════════════════════════════════════════════════════
#  ПАПКИ
# ═══════════════════════════════════════════════════════════

def init_dir(S: dict):
    """Возвращает последнюю открытую папку или None."""
    lf = S.get("last_folder") or ""
    if lf and os.path.isdir(lf):
        return lf
    return None


def remember_folder(S: dict, file_path: str, save_fn=None):
    """Запоминает папку файла и сохраняет в настройки."""
    if not file_path:
        return
    try:
        folder = os.path.dirname(os.path.abspath(file_path))
        if folder and folder != S.get("last_folder"):
            S["last_folder"] = folder
            if save_fn is not None:
                persist_settings(S, save_fn)
    except Exception:
        pass