"""
image_processor.py — вся обработка изображений.
Принимает PIL, возвращает PIL. Никаких зависимостей от UI.
"""

import os
import subprocess
import tempfile
import shutil
import numpy as np
import cv2
from PIL import Image

from config import TEXTURE_PROFILES


def fallback_correct(pil, profile_key):
    """
    Математическая коррекция: CLAHE + soft-clip в LAB.
    Принимает PIL, возвращает PIL.
    """
    prof = TEXTURE_PROFILES[profile_key]
    dark_t = prof["dark"]
    light_t = prof["light"]

    lab = np.array(pil.convert("LAB")).astype(np.uint8)
    L = lab[:, :, 0]

    p1 = float(np.percentile(L, 1))
    p99 = float(np.percentile(L, 99))
    std_L = float(np.std(L))

    if std_L < 15:
        clip_limit = 1.5
    elif std_L < 35:
        clip_limit = 2.0
    elif std_L < 55:
        clip_limit = 2.8
    else:
        clip_limit = 3.5

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    L_clahe = clahe.apply(L)

    need = 0.0
    if p1 < dark_t - 10:
        need += min(1.0, (dark_t - 10 - p1) / 50.0)
    if p99 > light_t + 10:
        need += min(1.0, (p99 - light_t - 10) / 50.0)
    need = min(1.0, need)

    blend = 0.4 + need * 0.3
    L_new = (L_clahe.astype(np.float32) * blend +
              L.astype(np.float32) * (1 - blend))

    hard_dark = max(0, dark_t - 20)
    hard_light = min(255, light_t + 20)

    dark_excess = np.maximum(0, hard_dark - L_new)
    L_new = L_new + dark_excess * 0.6

    light_excess = np.maximum(0, L_new - hard_light)
    L_new = L_new - light_excess * 0.6

    new_range = np.percentile(L_new, 99) - np.percentile(L_new, 1)
    target_range = hard_light - hard_dark

    if new_range < target_range * 0.55:
        np1 = np.percentile(L_new, 1)
        np99 = np.percentile(L_new, 99)
        if np99 - np1 > 1:
            L_norm = np.clip((L_new - np1) / (np99 - np1), 0, 1)
            L_curved = L_norm * L_norm * (3 - 2 * L_norm)
            L_mixed = 0.3 * L_curved + 0.7 * L_norm
            L_stretched = hard_dark + L_mixed * (hard_light - hard_dark)
            L_new = L_new * 0.7 + L_stretched * 0.3

    L_final = np.clip(L_new, 0, 255).astype(np.uint8)
    lab[:, :, 0] = L_final
    result = Image.fromarray(lab, mode="LAB").convert("RGB")

    arr = np.array(result).astype(np.uint8)
    hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.02, 0, 255)
    arr_back = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    return Image.fromarray(arr_back, mode="RGB")


def ai_correct(pil, exe_path, model_path, timeout=300):
    """
    AI-коррекция через autolevels.exe.
    Возвращает (PIL | None, ok, error_message | None).
    Не пишет в log — просто возвращает статус.
    """
    if not (os.path.exists(exe_path) and os.path.exists(model_path)):
        return None, False, "AI-модель/autolevels.exe не найдены"

    try:
        tmpdir = tempfile.mkdtemp(prefix="albedolizer_")
        try:
            src_path = os.path.join(tmpdir, "input.png")
            pil.save(src_path)
            creation_flags = 0x08000000 if os.name == 'nt' else 0
            result = subprocess.run(
                [exe_path, "--model", model_path,
                 "--outdir", tmpdir, src_path],
                capture_output=True, text=True, timeout=timeout,
                creationflags=creation_flags
            )
            if result.returncode != 0:
                return None, False, f"autolevels: {result.stderr[:150]}"

            out_path = os.path.join(tmpdir, "input_al.png")
            if os.path.exists(out_path):
                img = Image.open(out_path).convert("RGB")
                img.load()
                return img, True, None
            else:
                return None, False, "результат не создан"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    except subprocess.TimeoutExpired:
        return None, False, "таймаут"
    except Exception as e:
        return None, False, f"{type(e).__name__}: {e}"