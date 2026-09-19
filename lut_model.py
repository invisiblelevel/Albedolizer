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

    def correct(self, pil):
        """AI-коррекция через LUTwithBGrid. Гибрид: яркость из модели, цвет из оригинала."""
        if self._session is None:
            return None
        try:
            import cv2
            orig_size = pil.size
            pil_rgb = pil.convert("RGB")
            img_resized = pil_rgb.resize((512, 512), Image.LANCZOS)

            arr = np.array(img_resized).astype(np.float32) / 255.0
            arr = np.transpose(arr, (2, 0, 1))[None, ...]

            result = self._session.run(None, {"input": arr})[0]
            result = np.transpose(result[0], (1, 2, 0))
            result = np.clip(result, 0.0, 1.0)
            result_u8 = (result * 255).astype(np.uint8)
            out_pil = Image.fromarray(result_u8, mode="RGB")

            if orig_size != (512, 512):
                out_pil = out_pil.resize(orig_size, Image.LANCZOS)

            # ─── ГИБРИД: только яркость из модели, цвет из оригинала ───
            orig_arr = np.array(pil_rgb)
            out_arr = np.array(out_pil)

            orig_lab = cv2.cvtColor(orig_arr, cv2.COLOR_RGB2LAB).astype(np.float32)
            out_lab = cv2.cvtColor(out_arr, cv2.COLOR_RGB2LAB).astype(np.float32)

            orig_lab[:, :, 0] = out_lab[:, :, 0]
            orig_lab = np.clip(orig_lab, 0, 255).astype(np.uint8)
            result_final = cv2.cvtColor(orig_lab, cv2.COLOR_LAB2RGB)

            return Image.fromarray(result_final, mode="RGB")
        except Exception as e:
            print(f"Warning: LUT correct error: {e}")
            return None