"""
lut_model.py — обёртка над LUTwithBGrid ONNX для Albedolizer.
"""
import os
import numpy as np
import onnxruntime as ort
from PIL import Image


class LUTwithBGridModel:
    """LUTwithBGrid ONNX inference для PBR-текстур."""

    _instance = None
    _session = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, onnx_path):
        """Загружает ONNX-модель (один раз)."""
        if self._session is not None:
            return True
        if not os.path.exists(onnx_path):
            return False
        try:
            providers = ['CPUExecutionProvider']
            self._session = ort.InferenceSession(onnx_path, providers=providers)
            return True
        except Exception as e:
            print(f"Warning: LUT ONNX load error: {e}")
            return False

    def is_loaded(self):
        return self._session is not None

    def correct(self, pil, max_pixels=16_000_000):
        """
        AI-коррекция через LUTwithBGrid.
        Если пикселей больше max_pixels — ресайзим до лимита,
        применяем модель, потом ресайзим L-канал обратно.
        Если пикселей <= max_pixels — подаём оригинал как есть.
        """
        if self._session is None:
            return None
        try:
            import cv2
            orig_w, orig_h = pil.size
            pil_rgb = pil.convert("RGB")
            total_px = orig_w * orig_h

            if total_px <= max_pixels:
                # Подаём 1:1
                arr = np.array(pil_rgb).astype(np.float32) / 255.0
                arr = np.transpose(arr, (2, 0, 1))[None, ...]

                result = self._session.run(None, {"input": arr})[0]
                result = np.transpose(result[0], (1, 2, 0))
                result = np.clip(result, 0.0, 1.0)
                result_u8 = (result * 255).astype(np.uint8)

                # L-канал из модели, A/B — из оригинала
                orig_lab = cv2.cvtColor(np.array(pil_rgb), cv2.COLOR_RGB2LAB)
                res_lab = cv2.cvtColor(result_u8, cv2.COLOR_RGB2LAB)
                orig_lab[:, :, 0] = res_lab[:, :, 0]
                result_final = cv2.cvtColor(orig_lab, cv2.COLOR_LAB2RGB)
                return Image.fromarray(result_final, mode="RGB")

            else:
                # Масштабируем до лимита
                scale = (max_pixels / total_px) ** 0.5
                new_w = max(64, int(orig_w * scale))
                new_h = max(64, int(orig_h * scale))

                small = pil_rgb.resize((new_w, new_h), Image.LANCZOS)
                arr = np.array(small).astype(np.float32) / 255.0
                arr = np.transpose(arr, (2, 0, 1))[None, ...]

                result = self._session.run(None, {"input": arr})[0]
                result = np.transpose(result[0], (1, 2, 0))
                result = np.clip(result, 0.0, 1.0)
                result_u8 = (result * 255).astype(np.uint8)
                small_out = Image.fromarray(result_u8, mode="RGB")

                # L-канал из модели
                small_out_lab = cv2.cvtColor(np.array(small_out), cv2.COLOR_RGB2LAB)
                small_L = small_out_lab[:, :, 0]

                # Ресайз L обратно
                big_L = cv2.resize(
                    small_L,
                    (orig_w, orig_h),
                    interpolation=cv2.INTER_CUBIC
                )

                # A/B — из оригинала
                orig_lab = cv2.cvtColor(np.array(pil_rgb), cv2.COLOR_RGB2LAB)
                orig_lab[:, :, 0] = big_L
                result_final = cv2.cvtColor(orig_lab, cv2.COLOR_LAB2RGB)
                return Image.fromarray(result_final, mode="RGB")

        except Exception as e:
            print(f"Warning: LUT correct error: {e}")
            return None