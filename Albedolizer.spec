# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'onnxruntime',
        'lut_model',
        'clip_model',
        'tokenizers',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # ML-фреймворки (не нужны, у нас onnxruntime)
        'torch', 'torchvision', 'torchaudio',
        'tensorflow', 'keras',
        'sklearn', 'scipy', 'pandas', 'matplotlib',
        # Jupyter / IPython
        'IPython', 'jupyter', 'notebook',
        # GUI-тулкиты
        'tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx',
        # Тесты и доки
        'test', 'unittest', 'pydoc', 'doctest',
    ],
    noarchive=False,
    optimize=0,
)

# === Режем CUDA/TensorRT/ffmpeg ===
_exclude_bins = [
    "onnxruntime_providers_cuda",
    "onnxruntime_providers_tensorrt",
    "onnxruntime_providers_shared",
    "nvinfer",
    "nvonnxparser",
    "cublas",
    "cudnn",
    "cudart",
    "opencv_videoio_ffmpeg",
]
a.binaries = [x for x in a.binaries if not any(p in x[0].lower() for p in _exclude_bins)]
a.datas    = [x for x in a.datas    if not any(p in x[0].lower() for p in _exclude_bins)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Albedolizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)