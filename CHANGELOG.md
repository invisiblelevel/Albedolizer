# Changelog

All notable changes to Albedolizer are documented in this file.

## [1.3.0-beta] — 2026-09-13

### ✨ Added
- **Preset categories** — 32 texture presets organized into 6 categories (Metal, Nature, Mineral, Synthetic, Special, Fauna)
- **New presets:** oxidized metal, patina, brass, aluminum, grass, bark, asphalt, marble, sand, plastic, rubber, glass, ceramic, painted metal, water, mud, snow, ice, leather, fur, skin, scales
- **Soap removal tool** — adaptive unsharp mask that fixes blurry patches after AI correction or upscaling
- **PBR batch browser** — flip through batch-processed textures with ◀ ▶ arrows in the preview
- **Auto system language detection** — starts in Russian on Russian Windows, English for everyone else
- **AI / Math correction mode switch** — choose between neural network and CLAHE-based correction

### 🐛 Fixed
- Fallback dialog now properly translated (was showing Russian on English UI)
- Removed duplicate fallback dialog
- Fixed «🎯 Preset:» label translation in PBR tab
- Fixed log panels disappearing on some tabs
- Fixed double log output in batch processing

### ⚠️ Known issues (beta)
- GPU acceleration not yet available (CPU only, ~30s per 8K texture)
- Some presets may require manual slider tuning for best results
- Batch processing on very large folders (>100 files) can be slow

## [1.2.1] — 2026-09-13

### ✨ Added
- Correction mode switch (AI / Math)
- Auto system language detection
- Concrete preset

### 🐛 Fixed
- Fallback dialog translation
- Duplicate dialog
- Preset label translation

## [1.2.0] — 2026-09-13

### ✨ Added
- New tab structure (Single, Batch, PBR, Compress)
- Edge map generation
- Independent log panel per tab
- Info dialog close button
- Progress bars for PBR save and batch

### 🐛 Fixed
- Console window popup during AI correction
- Duplicate log panels

## [1.1.0] — 2026-09-12

### ✨ Added
- PBR map generation (7 maps)
- Batch processing
- Compression
- RU / EN interface
- Preset system

### 🎉 Initial release