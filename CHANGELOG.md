# Changelog

All notable changes to Albedolizer are documented in this file.


## [1.4.0-beta] — 2026-09-15

### ✨ Added
- **Built-in 3D viewer** (`viewer.exe`) — real-time PBR preview via OpenGL (Moderngl + GLFW). Rotate with LMB, zoom with wheel, HDRI lighting with blurred reflections
- **Built-in HTML manual** — full user guide with screenshots and annotations, RU/EN switch, opens via **Info → 📖 Manual** button
- **Inno Setup installer** — single `Albedolizer_Setup_v1.4.0-beta.exe` for clean installation to Program Files
- **9 annotated screenshots** in the manual (Simple, Type, PBR, Viewer, Advanced, Batch, Info, Compress, Adv toggle)
- Smart file lookup: exe first checks inside itself (`_MEIPASS`), then falls back to its own folder

  ### 🛠 Improved
- `open_manual()` now uses the shared `_base_dir` with proper fallback
- Version bumped to 1.4.0-beta across UI, About dialog, and installer

## [1.3.3-beta] — 2026-09-15

### ✨ Added
- **Simple / Advanced modes** — Simple mode hides all advanced tools and gives you one-click workflow (Open → AI correct → Saturation boost). Switch via header button.
- **Saturation boost** — slider (0.8–1.5) + button to fix washed-out colors after AI correction. Works in HSV, preserves hue and brightness.

### 🛠 Improved
- Info dialog text now scrollable — long help text no longer overflows
- Internal PBR pipeline runs in float32 for higher precision
- Extracted `ao_range` from hardcoded value into a parameter
- Removed dead `mode` field from theme dicts

---

## [1.3.2-beta] — 2026-09-15

### ✨ Added
- **16-bit PNG output** — Height and Normal maps can now be saved in 16-bit for pro pipelines
- **16 / 8-bit toggle** in the PBR parameters panel
- **Tiling checker** — 3×3 preview button to spot seams on tileable textures

### 🛠 Improved
- Internal PBR pipeline now runs in float32 for higher precision
- `ao_range` parameter extracted from hardcoded magic number (was 50)
- Removed dead `mode` field from theme dicts

---

## [1.3.1-beta] — 2026-09-14

### ✨ Added
- **Light theme** — switch between dark and light theme with the ☀ / 🌙 button in the header
- **Theme toggle** in the header, next to the language switcher

### 🐛 Fixed
- Progress bar now shows during single compression and save in the Compress tab

### 🛠 Improved
- Fixed typo in the "Scales" preset (`strongth` → `strength`)
- Minor code cleanup

---

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
