"""
PBR Generator — модуль для генерации PBR-карт из Albedo.
Использует NumPy + Pillow + OpenCV.
"""

import numpy as np
import cv2
from PIL import Image, ImageFilter


def _to_luminance(pil):
    arr = np.array(pil.convert("RGB")).astype(np.float32)
    lum = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    return lum


def _normalize(arr):
    mn, mx = arr.min(), arr.max()
    if mx - mn < 1e-6:
        return np.full_like(arr, 128, dtype=np.uint8)
    return ((arr - mn) / (mx - mn) * 255).astype(np.uint8)


def generate_height(albedo_pil, blur=2.0, contrast=1.0, invert=False):
    lum = _to_luminance(albedo_pil)

    if blur > 0:
        img = Image.fromarray(lum.astype(np.uint8), mode="L")
        img = img.filter(ImageFilter.GaussianBlur(radius=blur))
        lum = np.array(img).astype(np.float32)

    if contrast != 1.0:
        mean = lum.mean()
        lum = mean + (lum - mean) * contrast

    if invert:
        lum = 255 - lum

    result = np.clip(lum, 0, 255).astype(np.uint8)
    return Image.fromarray(result, mode="L")


def generate_normal(height_pil, strength=1.0, smooth=1.5, clamp=3.0,
                     high_pass_radius=40, threshold=0.05):
    if smooth > 0:
        h_img = height_pil.convert("L").filter(ImageFilter.GaussianBlur(radius=smooth))
    else:
        h_img = height_pil.convert("L")

    h = np.array(h_img).astype(np.float32) / 255.0

    if high_pass_radius > 0:
        blurred = h_img.filter(ImageFilter.GaussianBlur(radius=high_pass_radius))
        blurred_arr = np.array(blurred).astype(np.float32) / 255.0
        h = h - blurred_arr
        h = h - h.min()
        if h.max() > 1e-6:
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
        threshold_val = threshold * 8.0
        dx = np.sign(dx) * np.maximum(0, np.abs(dx) - threshold_val)
        dy = np.sign(dy) * np.maximum(0, np.abs(dy) - threshold_val)

    dx = np.clip(dx, -clamp, clamp)
    dy = np.clip(dy, -clamp, clamp)

    dz = np.ones_like(dx)
    length = np.sqrt(dx*dx + dy*dy + dz*dz)
    length = np.maximum(length, 1e-8)
    dx /= length
    dy /= length
    dz /= length

    r = ((dx * 0.5 + 0.5) * 255).astype(np.uint8)
    g = ((dy * 0.5 + 0.5) * 255).astype(np.uint8)
    b = ((dz * 0.5 + 0.5) * 255).astype(np.uint8)

    rgb = np.stack([r, g, b], axis=2)
    return Image.fromarray(rgb, mode="RGB")


def generate_ao(height_pil, radius=8, intensity=1.5):
    h = np.array(height_pil.convert("L")).astype(np.float32)

    blurred = Image.fromarray(h.astype(np.uint8), mode="L")
    blurred = blurred.filter(ImageFilter.GaussianBlur(radius=radius))
    blurred_arr = np.array(blurred).astype(np.float32)

    diff = blurred_arr - h
    diff = np.maximum(diff, 0) * intensity

    ao = 255 - np.clip(diff * 255 / 50, 0, 255)
    return Image.fromarray(ao.astype(np.uint8), mode="L")


def generate_roughness(albedo_pil, base=0.7, variation=0.3, blur=1.0):
    lum = _to_luminance(albedo_pil)
    lum_norm = lum / 255.0

    rough = base + (1 - lum_norm - 0.5) * variation
    rough = np.clip(rough, 0, 1)

    if blur > 0:
        img = Image.fromarray((rough * 255).astype(np.uint8), mode="L")
        img = img.filter(ImageFilter.GaussianBlur(radius=blur))
        rough = np.array(img).astype(np.float32) / 255.0

    return Image.fromarray((rough * 255).astype(np.uint8), mode="L")


def generate_metallic(albedo_pil, mode="black"):
    w, h = albedo_pil.size

    if mode == "white":
        return Image.new("L", (w, h), 255)
    elif mode == "auto":
        arr = np.array(albedo_pil.convert("RGB")).astype(np.float32)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        avg = (r + g + b) / 3
        diff = np.abs(r - g) + np.abs(g - b) + np.abs(r - b)
        mask = ((avg > 140) & (diff < 30)).astype(np.uint8) * 255
        return Image.fromarray(mask, mode="L")
    else:
        return Image.new("L", (w, h), 0)


def generate_edge(height_pil, blur=1.0, strength=1.0):
    """Генерирует Edge Map из Height Map через Sobel (cv2)."""
    if blur > 0:
        h_img = height_pil.convert("L").filter(ImageFilter.GaussianBlur(radius=blur))
    else:
        h_img = height_pil.convert("L")

    arr = np.array(h_img).astype(np.float32)

    gx = cv2.Sobel(arr, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(arr, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = np.sqrt(gx**2 + gy**2) * strength

    mx = magnitude.max()
    if mx > 1e-6:
        magnitude = magnitude / mx * 255

    result = np.clip(magnitude, 0, 255).astype(np.uint8)
    return Image.fromarray(result, mode="L")


def pack_orm(ao_pil, rough_pil, metal_pil):
    ao = np.array(ao_pil.convert("L"))
    rough = np.array(rough_pil.convert("L"))
    metal = np.array(metal_pil.convert("L"))

    rgb = np.stack([ao, rough, metal], axis=2)
    return Image.fromarray(rgb, mode="RGB")


def remove_soap_adaptive(pil, strength=1.0, window=15, threshold=25.0, original=None):
    """
    Финальный pipeline:
    - unsharp по средним частотам
    - bilateral шлифовка
    - SOFT-CLIP через tanh — плавное сжатие без плато/камуфляжа
    """
    if strength <= 0:
        return pil

    rgb = np.array(pil.convert("RGB"))
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    L = lab[:, :, 0]

    # ═══ Детектор мыла ═══
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

    # ═══ ШАГ 1: Unsharp по средним частотам ═══
    hp2 = L - cv2.GaussianBlur(L, (0, 0), sigmaX=2.5)
    hp3 = L - cv2.GaussianBlur(L, (0, 0), sigmaX=6.0)
    boost = strength * 3.0
    detail_sum = hp2 * 0.7 + hp3 * 0.4
    L_sharp = L + detail_sum * boost * deficit

    # ═══ ШАГ 2: Bilateral ═══
    L_u8 = np.clip(L_sharp, 0, 255).astype(np.uint8)
    L_clean = cv2.bilateralFilter(L_u8, d=5, sigmaColor=18, sigmaSpace=7).astype(np.float32)

    # ═══ ШАГ 3: SOFT-CLIP через tanh ═══
    # Локальное среднее (не медиана — не даёт червей)
    local_mean = cv2.GaussianBlur(L_clean, (0, 0), sigmaX=3.0)

    # Отклонение от локального среднего
    excess = L_clean - local_mean

    # CLIP — «мягкая граница», tanh плавно её сжимает
    CLIP = 14.0
    scaled = excess / CLIP
    # tanh(x) даёт плавное сжатие: x → ±1 асимптотически
    soft_excess = CLIP * np.tanh(scaled)

    L_clipped = local_mean + soft_excess

    # ═══ Финальный микс — только мыльные зоны ═══
    L_final = L * (1 - deficit) + L_clipped * deficit
    L_final = np.clip(L_final, 0, 255)

    lab[:, :, 0] = L_final
    lab = np.clip(lab, 0, 255).astype(np.uint8)
    result = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    return Image.fromarray(result, mode="RGB")


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
    ao = generate_ao(height, radius=ao_radius, intensity=ao_intensity)
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
