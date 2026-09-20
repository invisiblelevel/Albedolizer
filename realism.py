"""
realism.py — процедурный фильтр фотореализма (без ML).
Компоненты: grain (зерно), high-pass detail, HSV-вариация, виньетка.
"""

import numpy as np
import cv2
from PIL import Image


def _grain_noise(h, w, sigma=1.0):
    """Настоящее зерно: нормальный шум + гауссово размытие. -1..1 float32."""
    n = np.random.randn(h, w).astype(np.float32)
    if sigma > 0:
        n = cv2.GaussianBlur(n, (0, 0), sigmaX=sigma)
    std = float(np.std(n))
    if std > 1e-6:
        n = n / std
    return np.clip(n / 3.0, -1.0, 1.0).astype(np.float32)


def _vignette(h, w, strength=0.15):
    """Радиальная виньетка: 1.0 в центре, ниже к краям."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cy, cx = h / 2.0, w / 2.0
    r = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    r = r / max(np.sqrt(cy ** 2 + cx ** 2), 1e-6)
    return (1.0 - r * strength).astype(np.float32)


def add_realism(pil, grain=0.15, highpass=0.30, variation=0.20,
                seed=None):
    """
    Процедурный фильтр фотореализма.

    grain:     0..1 — сила зерна (микро-шум)
    highpass:  0..1 — сила high-pass overlay (детализация)
    variation: 0..1 — неравномерность цвета/яркости + виньетка
    """
    if seed is not None:
        np.random.seed(seed)

    arr = np.array(pil.convert("RGB")).astype(np.float32) / 255.0
    h, w, _ = arr.shape
    short = min(h, w)

    # ─── 1. Grain (зерно) ───
    if grain > 0:
        # Два слоя: мелкое зерно + чуть крупнее
        fine = _grain_noise(h, w, sigma=0.8)
        coarse = _grain_noise(h, w, sigma=max(1.5, short / 800.0))
        noise = fine * 0.7 + coarse * 0.3
        arr = arr + noise[..., None] * grain * 0.10

    # ─── 2. High-pass overlay (детализация) ───
    if highpass > 0:
        u8 = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
        sigma = max(1.5, short / 512.0)
        blur = cv2.GaussianBlur(u8, (0, 0), sigmaX=sigma)
        hp = u8.astype(np.float32) - blur.astype(np.float32)
        arr = arr + hp / 255.0 * highpass * 0.6

    # ─── 3. HSV-вариация: крупные пятна + мелкая микро-вариация ───
    if variation > 0:
        big = _grain_noise(h, w, sigma=max(8.0, short / 32.0))
        small = _grain_noise(h, w, sigma=2.0)
        v_map = big * 0.75 + small * 0.25

        u8 = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
        hsv = cv2.cvtColor(u8, cv2.COLOR_RGB2HSV).astype(np.float32)

        # H: 0..179, S: 0..255, V: 0..255
        hsv[..., 0] += v_map * variation * 5.0
        hsv[..., 0] = np.mod(hsv[..., 0], 180.0)
        hsv[..., 1] *= (1.0 + v_map * variation * 0.18)  # насыщенность
        hsv[..., 2] *= (1.0 + v_map * variation * 0.12)  # яркость

        # Клип по каналам правильными границами, потом uint8
        hsv[..., 0] = np.clip(hsv[..., 0], 0, 179)
        hsv[..., 1] = np.clip(hsv[..., 1], 0, 255)
        hsv[..., 2] = np.clip(hsv[..., 2], 0, 255)
        hsv_u8 = hsv.astype(np.uint8)

        arr = cv2.cvtColor(hsv_u8, cv2.COLOR_HSV2RGB).astype(np.float32) / 255.0

    # ─── 4. Виньетка (лёгкая неравномерность освещения) ───
    if variation > 0:
        vig = _vignette(h, w, strength=variation * 0.20)
        arr = arr * vig[..., None]

    arr = np.clip(arr, 0, 1)
    return Image.fromarray((arr * 255).astype(np.uint8), mode="RGB")