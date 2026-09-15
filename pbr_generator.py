"""
PBR Generator — генерация PBR-карт из Albedo.
Внутренняя обработка во float32 (0.0–1.0) для сохранения точности.
Возвращает numpy arrays float32. Сохранение — через save_pbr_map.
"""

import numpy as np
import cv2
from PIL import Image, ImageFilter


def _to_luminance(pil):
    """PIL RGB → float32 2D (0.0-1.0)."""
    arr = np.array(pil.convert("RGB")).astype(np.float32) / 255.0
    lum = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    return lum.astype(np.float32)


def _pil_to_float(pil):
    """PIL → float32 без потери точности."""
    return np.array(pil.convert("RGB")).astype(np.float32) / 255.0


def _blur_float(arr, radius):
    """Гауссовое размытие float32 массива через PIL."""
    u8 = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
    blurred = Image.fromarray(u8, mode="L").filter(ImageFilter.GaussianBlur(radius=radius))
    return np.array(blurred).astype(np.float32) / 255.0


def generate_height(albedo_pil, blur=2.0, contrast=1.0, invert=False):
    """float32 2D 0-1."""
    lum = _to_luminance(albedo_pil)

    if blur > 0:
        lum = _blur_float(lum, blur)

    if contrast != 1.0:
        mean = float(lum.mean())
        lum = mean + (lum - mean) * contrast

    if invert:
        lum = 1.0 - lum

    return np.clip(lum, 0, 1).astype(np.float32)


def generate_normal(height_arr, strength=1.0, smooth=1.5, clamp=3.0,
                     high_pass_radius=40, threshold=0.05):
    """height_arr: float32 2D 0-1. Возвращает float32 3D (H,W,3) 0-1."""
    if smooth > 0:
        h = _blur_float(height_arr, smooth)
    else:
        h = height_arr.copy()

    if high_pass_radius > 0:
        blurred = _blur_float(h, high_pass_radius)
        h = h - blurred
        h = h - h.min()
        if h.max() > 1e-8:
            h = h / h.max()

    hp = np.pad(h, 1, mode='edge')

    a = hp[0:-2, 0:-2]
    b = hp[0:-2, 1:-1]
    c = hp[0:-2, 2:  ]
    d = hp[1:-1, 0:-2]
    f = hp[1:-1, 2:  ]
    g = hp[2:  , 0:-2]
    hh = hp[2:  , 1:-1]
    i = hp[2:  , 2:  ]

    dx = (c + 2*f + i) - (a + 2*d + g)
    dy = (g + 2*hh + i) - (a + 2*b + c)

    dx *= strength * 8.0
    dy *= -strength * 8.0

    if threshold > 0:
        tv = threshold * 8.0
        dx = np.sign(dx) * np.maximum(0, np.abs(dx) - tv)
        dy = np.sign(dy) * np.maximum(0, np.abs(dy) - tv)

    dx = np.clip(dx, -clamp, clamp)
    dy = np.clip(dy, -clamp, clamp)

    dz = np.ones_like(dx)
    length = np.sqrt(dx*dx + dy*dy + dz*dz)
    length = np.maximum(length, 1e-8)
    dx /= length
    dy /= length
    dz /= length

    r = (dx * 0.5 + 0.5).astype(np.float32)
    g = (dy * 0.5 + 0.5).astype(np.float32)
    b = (dz * 0.5 + 0.5).astype(np.float32)

    return np.stack([r, g, b], axis=2).astype(np.float32)


def generate_ao(height_arr, radius=8, intensity=1.5, ao_range=50.0):
    """float32 2D 0-1. ao_range — порог максимального AO (было магическое 50)."""
    u8 = (np.clip(height_arr, 0, 1) * 255).astype(np.uint8)
    blurred = Image.fromarray(u8, mode="L").filter(ImageFilter.GaussianBlur(radius=radius))
    blurred_f = np.array(blurred).astype(np.float32)

    h_f = height_arr * 255.0
    diff = np.maximum(blurred_f - h_f, 0) * intensity
    ao = 255.0 - np.clip(diff * 255.0 / ao_range, 0, 255)
    return np.clip(ao / 255.0, 0, 1).astype(np.float32)


def generate_roughness(albedo_pil, base=0.7, variation=0.3, blur=1.0):
    """float32 2D 0-1."""
    lum = _to_luminance(albedo_pil)
    rough = base + (1.0 - lum - 0.5) * variation
    rough = np.clip(rough, 0, 1)

    if blur > 0:
        rough = _blur_float(rough, blur)

    return rough.astype(np.float32)


def generate_metallic(albedo_pil, mode="black"):
    """float32 2D 0-1."""
    w, h = albedo_pil.size
    if mode == "white":
        return np.ones((h, w), dtype=np.float32)
    elif mode == "auto":
        arr = np.array(albedo_pil.convert("RGB")).astype(np.float32)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        avg = (r + g + b) / 3
        diff = np.abs(r - g) + np.abs(g - b) + np.abs(r - b)
        mask = ((avg > 140) & (diff < 30)).astype(np.float32)
        return mask
    else:
        return np.zeros((h, w), dtype=np.float32)


def generate_edge(height_arr, blur=1.0, strength=1.0):
    """float32 2D 0-1."""
    if blur > 0:
        arr = _blur_float(height_arr, blur)
    else:
        arr = height_arr.copy()

    gx = cv2.Sobel(arr, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(arr, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = np.sqrt(gx**2 + gy**2) * strength

    mx = float(magnitude.max())
    if mx > 1e-8:
        magnitude = magnitude / mx
    return np.clip(magnitude, 0, 1).astype(np.float32)


def pack_orm(ao_arr, rough_arr, metal_arr):
    """Все float32 2D. Возвращает float32 3D."""
    return np.stack([ao_arr, rough_arr, metal_arr], axis=2).astype(np.float32)


# ═══════════════════════════════════════════════════════════
#  ПРЕВЬЮ И СОХРАНЕНИЕ
# ═══════════════════════════════════════════════════════════

def to_preview_pil(arr):
    """float32 2D/3D 0-1 → PIL Image uint8 для превью в UI."""
    if arr.ndim == 2:
        return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), mode="L")
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), mode="RGB")


def save_pbr_map(arr, path, bit_depth=8):
    """Сохраняет float32 массив 0-1 в PNG. bit_depth: 8 или 16."""
    arr = np.clip(arr, 0, 1)

    if bit_depth == 16:
        data16 = (arr * 65535).astype(np.uint16)
        if arr.ndim == 2:
            # Grayscale 16-bit — Pillow умеет
            Image.fromarray(data16, mode="I;16").save(path)
        else:
            # RGB 16-bit — через cv2 (BGR)
            bgr = cv2.cvtColor(data16, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(path), bgr)
    else:
        if arr.ndim == 2:
            Image.fromarray((arr * 255).astype(np.uint8), mode="L").save(path)
        else:
            Image.fromarray((arr * 255).astype(np.uint8), mode="RGB").save(path)


def generate_all_pbr(albedo_pil,
                     height_blur=2.0,
                     height_contrast=1.0,
                     normal_strength=1.5,
                     normal_smooth=1.5,
                     normal_clamp=3.0,
                     normal_high_pass=40,
                     normal_threshold=0.05,
                     ao_radius=8,
                     ao_intensity=1.5,
                     ao_range=50.0,
                     rough_base=0.7,
                     rough_variation=0.3,
                     metallic_mode="black",
                     edge_blur=1.0,
                     edge_strength=1.0):
    height = generate_height(albedo_pil, blur=height_blur, contrast=height_contrast)
    normal = generate_normal(
        height,
        strength=normal_strength,
        smooth=normal_smooth,
        clamp=normal_clamp,
        high_pass_radius=normal_high_pass,
        threshold=normal_threshold,
    )
    ao = generate_ao(height, radius=ao_radius, intensity=ao_intensity, ao_range=ao_range)
    roughness = generate_roughness(albedo_pil, base=rough_base, variation=rough_variation)
    metallic = generate_metallic(albedo_pil, mode=metallic_mode)
    edge = generate_edge(height, blur=edge_blur, strength=edge_strength)
    orm = pack_orm(ao, roughness, metallic)

    return {
        "height": height,
        "normal": normal,
        "ao": ao,
        "roughness": roughness,
        "metallic": metallic,
        "orm": orm,
        "edge": edge,
    }


def remove_soap_adaptive(pil, strength=1.0, window=15, threshold=25.0, original=None):
    """
    Финальный pipeline: unsharp по средним частотам, bilateral, tanh soft-clip.
    Работает только в мыльных зонах, не трогает цвет.
    """
    if strength <= 0:
        return pil

    rgb = np.array(pil.convert("RGB"))
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    L = lab[:, :, 0]

    k = window if window % 2 == 1 else window + 1
    mean = cv2.blur(L, (k, k))
    sq_mean = cv2.blur(L * L, (k, k))
    std = np.sqrt(np.maximum(sq_mean - mean * mean, 0))
    med = float(np.median(std)) + 1e-6
    ratio = std / med
    deficit = np.clip((1.2 - ratio) / 0.6, 0, 1)
    deficit = cv2.GaussianBlur(deficit, (0, 0), sigmaX=window / 3.0)
    deficit = np.where(deficit < 0.20, 0.0, deficit)

    if deficit.max() < 0.05:
        return pil

    hp2 = L - cv2.GaussianBlur(L, (0, 0), sigmaX=2.5)
    hp3 = L - cv2.GaussianBlur(L, (0, 0), sigmaX=6.0)
    boost = strength * 3.0
    detail_sum = hp2 * 0.7 + hp3 * 0.4
    L_sharp = L + detail_sum * boost * deficit

    L_u8 = np.clip(L_sharp, 0, 255).astype(np.uint8)
    L_clean = cv2.bilateralFilter(L_u8, d=5, sigmaColor=18, sigmaSpace=7).astype(np.float32)

    local_mean = cv2.GaussianBlur(L_clean, (0, 0), sigmaX=3.0)
    excess = L_clean - local_mean
    CLIP = 14.0
    soft_excess = CLIP * np.tanh(excess / CLIP)
    L_clipped = local_mean + soft_excess

    L_final = L * (1 - deficit) + L_clipped * deficit
    L_final = np.clip(L_final, 0, 255)

    lab[:, :, 0] = L_final
    lab = np.clip(lab, 0, 255).astype(np.uint8)
    result = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    return Image.fromarray(result, mode="RGB")
    
def boost_saturation(pil, strength=1.15):
    """
    Поднимает насыщенность после AI-коррекции.
    strength: 1.0 = без изменений, 1.15 = +15%, 1.5 = +50%, 0.8 = -20%
    Работает в HSV — не трогает цветовой тон и яркость.
    """
    if abs(strength - 1.0) < 1e-3:
        return pil
    rgb = np.array(pil.convert("RGB"))
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * strength, 0, 255)
    hsv = hsv.astype(np.uint8)
    result = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    return Image.fromarray(result, mode="RGB")