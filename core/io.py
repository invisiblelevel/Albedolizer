"""
core/io.py — сохранение/загрузка изображений, конвертация, форматирование.

Не знает про Flet. Работает с PIL, numpy, cv2.
"""

import io
import base64
import os
import numpy as np
import cv2
from PIL import Image
from pbr_generator import to_preview_pil


# ═══════════════════════════════════════════════════════════
#  СОХРАНЕНИЕ PNG
# ═══════════════════════════════════════════════════════════

def save_16bit_or_8bit(pil_img, path, bit_depth: int = 16):
    """Сохраняет PIL в PNG с выбранной битностью. bit_depth: 8 или 16."""
    if bit_depth == 16:
        arr = np.array(pil_img.convert("RGB"))
        arr16 = (arr.astype(np.uint16) * 257)
        bgr = cv2.cvtColor(arr16, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(path), bgr)
    else:
        pil_img.save(str(path))


# ═══════════════════════════════════════════════════════════
#  ПРЕВЬЮ → BASE64
# ═══════════════════════════════════════════════════════════

def pil_to_b64(data, max_size: int = 900) -> str:
    """PIL или numpy → base64 PNG (для ft.Image src)."""
    if isinstance(data, np.ndarray):
        data = to_preview_pil(data)
    p = data.copy()
    if p.mode not in ("RGB", "L"):
        p = p.convert("RGB")
    p.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    p.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ═══════════════════════════════════════════════════════════
#  РАЗМЕР
# ═══════════════════════════════════════════════════════════

def fmt_size(b: int) -> str:
    """Байты → человекочитаемо: 1.2 KB / 3.4 MB / 1.5 GB."""
    if b < 1024:
        return f"{b} B"
    if b < 1024 * 1024:
        return f"{b / 1024:.1f} KB"
    if b < 1024 * 1024 * 1024:
        return f"{b / 1024 / 1024:.2f} MB"
    return f"{b / 1024 / 1024 / 1024:.2f} GB"


# ═══════════════════════════════════════════════════════════
#  ЯРКОСТЬ
# ═══════════════════════════════════════════════════════════

def get_luminance(pil) -> np.ndarray:
    """PIL → массив яркости (Rec. 709)."""
    arr = np.array(pil.convert("RGB")).astype(np.float32)
    return 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]


# ═══════════════════════════════════════════════════════════
#  БЕЗОПАСНОЕ ОТКРЫТИЕ
# ═══════════════════════════════════════════════════════════

def safe_open_rgb(path: str) -> Image.Image:
    """Открывает картинку и конвертит в RGB. Бросает OSError с понятным текстом."""
    try:
        img = Image.open(path)
        img.load()
        return img.convert("RGB")
    except OSError as ex:
        raise OSError(
            f"Не удалось открыть файл: {path}\n"
            f"Причина: {ex}\n"
            f"Проверь: длину пути (>260 символов?), права доступа, "
            f"свободное место на диске, целостность файла."
        ) from ex


def safe_open_gray(path: str) -> Image.Image:
    """Открывает картинку в grayscale."""
    try:
        img = Image.open(path)
        img.load()
        return img.convert("L")
    except OSError as ex:
        raise OSError(
            f"Не удалось открыть файл: {path}\n"
            f"Причина: {ex}\n"
            f"Проверь: длину пути (>260 символов?), права доступа, "
            f"свободное место на диске, целостность файла."
        ) from ex