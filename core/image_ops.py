"""
core/image_ops.py — чистая работа с изображениями.

Ноль Flet. Ноль page. Ноль UI.
Только PIL / numpy / cv2 + модули обработки (image_processor, pbr_generator, realism).

Всё, что касается "взять картинку → вернуть картинку/данные" — живёт здесь.
UI-обвязка (progress bar, лог, кнопки) — в ui/tab_*.py.
"""

import os
import numpy as np
from PIL import Image

from image_processor import fallback_correct, ai_correct, lut_correct
from pbr_generator import (
    remove_soap_adaptive,
    boost_saturation,
    make_seamless,
    extract_metallic_by_color,
)
from realism import add_realism
from config import TEXTURE_PROFILES


# ═══════════════════════════════════════════════════════════
#  ЯРКОСТЬ / АНАЛИЗ
# ═══════════════════════════════════════════════════════════

def get_luminance(pil: Image.Image) -> np.ndarray:
    """PIL → массив яркости (Rec. 709)."""
    arr = np.array(pil.convert("RGB")).astype(np.float32)
    return 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]


def analyze_image(pil: Image.Image, profile_key: str) -> dict:
    """
    Считает статистику яркости по профилю.
    Возвращает dict с min/max/avg/median/p1/p99/dark_pct/light_pct и порогами.
    """
    lum = get_luminance(pil)
    prof = TEXTURE_PROFILES[profile_key]
    dt = prof["dark"]
    lt = prof["light"]
    total = lum.size
    dark_px = int(np.sum(lum < dt))
    light_px = int(np.sum(lum > lt))
    return {
        "min": float(np.min(lum)),
        "max": float(np.max(lum)),
        "avg": float(np.mean(lum)),
        "median": float(np.median(lum)),
        "p1": float(np.percentile(lum, 1)),
        "p99": float(np.percentile(lum, 99)),
        "dark_pct": dark_px / total * 100,
        "light_pct": light_px / total * 100,
        "dark_t": dt,
        "light_t": lt,
        "dark_px": dark_px,
        "light_px": light_px,
        "lum": lum,
    }


def is_valid(stats: dict, noise_threshold: float = 5.0) -> bool:
    """Проверка: PASS или FAIL по порогам."""
    return (stats["dark_pct"] <= noise_threshold
            and stats["light_pct"] <= noise_threshold)


def make_heatmap(pil: Image.Image, stats: dict) -> Image.Image:
    """Красит проблемные пиксели: тёмные → красный, светлые → синий."""
    arr = np.array(pil.convert("RGB")).copy()
    lum = stats["lum"]
    arr[lum < stats["dark_t"]] = [255, 0, 0]
    arr[lum > stats["light_t"]] = [0, 100, 255]
    return Image.fromarray(arr.astype(np.uint8))


# ═══════════════════════════════════════════════════════════
#  AI-КОРРЕКЦИЯ
# ═══════════════════════════════════════════════════════════

def apply_ai(pil: Image.Image, model_key: str,
             autolevels_exe: str, autolevels_model: str,
             lutwithbgrid_model: str):
    """
    AI-коррекция. model_key: 'autolevels' | 'lutwithbgrid'.

    Возвращает (result_pil, ok: bool, err: str|None).
    """
    if model_key == "lutwithbgrid":
        return lut_correct(pil, lutwithbgrid_model)
    else:
        return ai_correct(pil, autolevels_exe, autolevels_model)


def apply_fallback(pil: Image.Image, profile_key: str) -> Image.Image:
    """Математический fallback (CLAHE + LAB)."""
    return fallback_correct(pil, profile_key)


# ═══════════════════════════════════════════════════════════
#  ПОСТ-ОБРАБОТКА
# ═══════════════════════════════════════════════════════════

def apply_soap(pil: Image.Image, strength: float) -> Image.Image:
    """Убирает 'мыло' — адаптивное усиление детализации."""
    if strength <= 0:
        return pil
    return remove_soap_adaptive(pil, strength)


def apply_saturation(pil: Image.Image, multiplier: float) -> Image.Image:
    """Поднимает насыщенность (LAB)."""
    return boost_saturation(pil, multiplier)


def apply_seamless(pil: Image.Image, hipass: bool = True) -> Image.Image:
    """GIMP-style seamless + опциональный Hi-pass."""
    return make_seamless(pil, hipass)


def apply_realism(pil: Image.Image, grain: float,
                  highpass: float, variation: float) -> Image.Image:
    """Процедурный фотореализм."""
    return add_realism(pil, grain, highpass, variation)


# ═══════════════════════════════════════════════════════════
#  TILING
# ═══════════════════════════════════════════════════════════

def make_tiled(pil: Image.Image, tiles: int = 3,
               max_size: int = 1800) -> Image.Image:
    """Плитка tiles×tiles, обрезанная до max_size."""
    w, h = pil.size
    tiled = Image.new("RGB", (w * tiles, h * tiles))
    for x in range(tiles):
        for y in range(tiles):
            tiled.paste(pil, (x * w, y * h))
    tiled.thumbnail((max_size, max_size), Image.LANCZOS)
    return tiled
    
# ═══════════════════════════════════════════════════════════
#  РЕСАЙЗ ПОД ALBEDO
# ═══════════════════════════════════════════════════════════

def resize_to_match(arr: np.ndarray, target_pil: Image.Image,
                    map_name: str = "map") -> np.ndarray:
    """
    Ресайзит float32-массив под размеры target_pil (Lanczos4).
    Возвращает (resized_arr, was_resized: bool, old_size, new_size).
    """
    import cv2
    ah, aw = target_pil.size[1], target_pil.size[0]
    ch, cw = arr.shape[:2]
    if (cw, ch) == (aw, ah):
        return arr, False, (cw, ch), (aw, ah)
    resized = cv2.resize(arr, (aw, ah),
                          interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    return resized, True, (cw, ch), (aw, ah)


# ═══════════════════════════════════════════════════════════
#  PBR-ГЕНЕРАЦИЯ (обёртка)
# ═══════════════════════════════════════════════════════════

def generate_pbr_all(pil: Image.Image, vals: dict,
                     metallic_mode: str = "black",
                     metallic_custom=None,
                     roughness_mode: str = "procedural",
                     roughness_custom=None) -> dict:
    """
    Обёртка над generate_all_pbr. Принимает vals-словарь (как в S['pbr_values'])
    и режимы metallic/roughness.
    """
    from pbr_generator import generate_all_pbr
    return generate_all_pbr(
        pil,
        height_blur=vals.get("height_blur", 2.0),
        normal_strength=vals.get("strength", 1.5),
        normal_smooth=vals.get("smooth", 1.5),
        normal_clamp=3.0,
        normal_high_pass=vals.get("high_pass", 40.0),
        normal_threshold=vals.get("threshold", 0.05),
        ao_radius=int(vals.get("ao_radius", 8.0)),
        ao_intensity=vals.get("ao_intensity", 1.5),
        rough_base=vals.get("rough_base", 0.7),
        rough_variation=vals.get("rough_var", 0.3),
        rough_detail=vals.get("rough_detail", 1.0),
        metallic_mode=metallic_mode,
        metallic_custom=metallic_custom,
        roughness_mode=roughness_mode,
        roughness_custom=roughness_custom,
    )


# ═══════════════════════════════════════════════════════════
#  METALLIC MASK (по цвету)
# ═══════════════════════════════════════════════════════════

def make_metallic_mask(pil: Image.Image, rgb: tuple,
                       tolerance: float, softness: float,
                       negative_rgb: tuple = None,
                       negative_tolerance: float = 0.10) -> np.ndarray:
    """
    Маска металла по цвету. Обёртка над extract_metallic_by_color.
    Возвращает float32 массив [0..1].
    """
    return extract_metallic_by_color(
        pil, rgb,
        tolerance=tolerance,
        softness=softness,
        negative_rgb=negative_rgb,
        negative_tolerance=negative_tolerance,
    )


def pick_color_from_pixel(pil: Image.Image, x: int, y: int,
                          half_window: int = 2) -> tuple:
    """
    Усреднённый RGB 5×5 вокруг точки (x, y) с защитой краёв.
    half_window=2 → окно 5×5.
    Возвращает (r, g, b).
    """
    w, h = pil.size
    x0 = max(0, x - half_window)
    x1 = min(w, x + half_window + 1)
    y0 = max(0, y - half_window)
    y1 = min(h, y + half_window + 1)
    patch = pil.crop((x0, y0, x1, y1))
    arr = np.array(patch).astype(np.float32)
    mean_rgb = arr.mean(axis=(0, 1))
    return (int(round(mean_rgb[0])),
            int(round(mean_rgb[1])),
            int(round(mean_rgb[2])))


def mask_white_pct(mask: np.ndarray, threshold: float = 0.5) -> float:
    """Сколько процентов маски белое."""
    return float((mask > threshold).mean() * 100)


# ═══════════════════════════════════════════════════════════
#  LAB-СЖАТИЕ
# ═══════════════════════════════════════════════════════════

def lab_roundtrip(pil: Image.Image) -> Image.Image:
    """Сжатие через LAB-прогон (RGB → LAB → RGB)."""
    return pil.convert("LAB").convert("RGB")