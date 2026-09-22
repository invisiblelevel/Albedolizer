# Changelog

## [1.7.2-beta] — 2026-09-22

Viewer overhaul + 50 presets + QoL fixes.

### Added
- **3D viewer overhaul** — 4 shapes: Sphere / Cylinder / Cube / Plane, switchable on the fly via ImGui radio
- **Substance-style lighting** — key + fill + rim lights, proper volume on all shapes, no more flat look
- **ACES tone mapping** (Narkowicz approximation) instead of Reinhard — richer contrast, no washed-out result
- **Exposure slider** in the viewer panel (0.5–2.0), applied before tone mapping in linear space
- **Rim light** — separates the object silhouette from the background
- **Viewer control panel** — Shape / Lighting / Tiling sections in one window
- **3 new texture presets** (47 → 50):
  - **Stucco** (🏛) — Mineral
  - **Gemstone** (🔮) — Mineral
  - **Cardboard** (📦) — Synthetic

### Changed
- **PBR preview** now uses `InteractiveViewer` — zoomable with the mouse wheel (was static)
- **Log panel title** is now localized (RU: ЛОГ / EN: LOG) instead of hardcoded Russian
- **manual.html** — full Russian translation with in-page RU / EN switcher (remembers choice via localStorage)
- **Viewer default camera** — distance 1.5, FOV 40° (was 1.0 / 45°), fits all 4 shapes correctly
- Viewer tiling panel now wraps to two rows (4 + 4 buttons) so all values 1–16 fit in the panel width

### Fixed
- **Viewer volume on sphere** — was flat due to weak key light and dominant IBL; now has proper shading
- **Viewer exposure order** — was applied after gamma, now in linear space before ACES
- **GLSL indentation bug** in `viewer.py` (`def draw_panel()` glued to comment line)

### Internal
- `viewer.py` — added `create_cylinder()`, `create_cube()`, `create_plane()` geometry generators
- `viewer.py` — 4 VAOs held in memory, switched by `shape_idx` at render time
- `viewer.py` — `--shape` argparse argument added (sphere / cylinder / cube / plane)
- `config.py` — 3 new entries in `TEXTURE_PROFILES` and `PBR_PRESETS`, 2 updated categories in `PROFILE_CATEGORIES`
- `translations.py` — new key `log_title` (RU / EN)
- Version bumped to 1.7.2-beta across all files


---


## [1.7.1-beta] — 2026-09-21

Engine Export polish + viewer tiling + QoL fixes.

### Added
- **Engine Export tab** (`🎮 Engine` / `🎮 Движок`) — pack PBR maps for specific engines:
  - **Unity HDRP** — Mask Map: R=Metallic, G=AO, B=Detail Mask, A=Smoothness
  - **Unity URP** — MetallicSmoothness: R=Metallic, A=Smoothness, G/B=0
  - **Unreal** — ORM: R=AO, G=Roughness, B=Metallic
  - **Godot** — ORM: R=AO, G=Roughness, B=Metallic
- **Detail Mask** for Unity HDRP — white (1.0) / edge map / custom (load from disk)
- **Normal map format toggle** — OpenGL (Y+) or DirectX (Y-, green channel flipped)
- **Channel preview** in Engine tab — R / G / B / A / RGB / RGBA
- **3D viewer tiling panel** — in-window ImGui buttons for X/Y texture tiling
  - Tiling steps: 1×1, 2×2, 3×3, 4×4, 6×6, 8×8, 12×12, 16×16
  - `Reset 4x3` button
  - Panel follows app language (RU / EN)
- **Last opened folder memory** — all file pickers and save dialogs start from the last used folder, persists in `config.json`

### Changed
- **Wallet label** `TON` → `GRAM` (address unchanged)

### Fixed
- **Realism tab Save button** — was not working, now saves correctly
- **Realism progress bar** — added, so 8K textures don't look frozen during processing
- **LUTwithBGrid blur on high-res textures** — the model was running at 512px internally, causing blur on 2K+ textures. Now processes up to **6 megapixels** before downscaling. Blur gone.
- **Viewer language** — now follows the app language (`--lang` argument from `main.py`)

### Internal
- New module `engine_export.py` — packers for Unity HDRP / URP / Unreal / Godot
- New spec `viewer.spec` — separate PyInstaller spec for the viewer with `imgui_bundle` included
- Viewer now depends on `imgui-bundle` for the in-window tiling controls


---


## [1.7.0-beta] — 2026-09-20

Major UI refactor + new Realism tab.

### Added
- **Realism tab** — procedural photorealism filter (grain + high-pass + HSV variation + vignette)
  - Three sliders: grain, detail, variation
  - Tileable noise — no visible seams on tiled textures
  - Zoom in preview (mouse wheel)
- **Batch threads slider** — control parallelism (1–8 tasks), previously hardcoded to 3
- **Compress bit depth selector** — 8-bit or 16-bit PNG output
- **NavigationRail** on the left (5 tabs: Single, Batch, PBR, Compress, Realism)
- **Per-tab right panels** — Single / Batch / PBR / Compress / Realism each have their own
- **BottomSheet log** — single shared log at the bottom, collapsible (35px collapsed / 130px expanded), shows last line when collapsed

### Changed
- Header simplified: mode / theme / language / info buttons are now 4 compact icons
- Log is now shared across all tabs (was 4 separate logs)
- Preview area in Single / Realism / PBR now uses `InteractiveViewer` with zoom support
- `refresh_log()` now writes to a single log column instead of 4

### Removed
- `tabs_row` + `views_stack` (replaced by NavigationRail + content holder)
- Per-tab log panels (`log_panel`, `log_panel_batch`, `log_panel_pbr`, `log_panel_compress`)
- Window transparency (already gone in 1.6.1)

### Optimized
- **exe slim:** ~140 MB → ~119 MB
  - Stripped CUDA / TensorRT / ffmpeg binaries
  - Excluded `torch`, `tensorflow`, `scipy`, `matplotlib`, `tkinter`, test packages
  - Disabled UPX (safer for onnxruntime DLLs)

### Fixed
- Realism filter precision loss — HSV conversion now clips channels to proper bounds (H: 0–179, S/V: 0–255) before `uint8` cast


---


## [1.6.1-beta] — 2026-09-19

### Added
- **Tiling** — new `🔲 Seamless` button (radial mask + scatter)
- **CLIP tokenizer** bundled locally — works offline on first launch

### Changed
- **Viewer** — lighting reworked (Cook-Torrance BRDF + IBL)
- **UI** — right panel widened to 320px, log panel moved under the preview
- **Math** button stretched to full width
- **Window** transparency removed (opacity fixed at 1.0)

### Fixed
- **Viewer** — UV seam on sphere (texture stretching + pole tearing)
- **lut_model** — LAB→RGB conversion (clip before astype)
- **FilePicker** — single instance across the entire app (fixes memory leaks)

### Performance
- **exe** slimmed — CUDA/TensorRT/ffmpeg binaries stripped (~268 MB → ~140 MB)
- **CLIP vision** quantized to INT8 — faster CPU inference

---


## [1.6.0-beta] — 2026-09-17

### ✨ Added
- **🤖 Material auto-detection** — CLIP-based classifier (OpenAI ViT-B/32, ONNX, 269 MB) with zero-shot classification. Automatically picks the best preset for your texture from 47 options.
- **New Fabric category** — 6 new presets: cotton, wool, silk, denim, carpet, velvet.
- **New presets in existing categories:** copper (Metal), clay + granite (Mineral), carbon (Synthetic).
- **Total presets: 47** (was 37) across 7 categories.
- **Viewer window now floats on top** — opens focused and stays above the main app.

### 🛠 Improved
- **Rewritten CLIP prompts** — unified PBR prefix (`"a close-up PBR albedo texture of X"`), 5-8 prompts per class for better accuracy.
- **All UI strings for auto-detection** moved to translations (RU + EN).
- Version bumped to 1.6.0-beta.

---


## [1.5.0-beta] — 2026-09-16

### ✨ Added
- **LUTwithBGrid AI model** — second AI correction method (ONNX, 1.9 MB). Based on LUTwithBGrid (ECCV 2024) — image-adaptive 3D LUT with bilateral grid. Runs on CPU via onnxruntime.
- **Three correction methods** — now choose between Autolevels, LUTwithBGrid, or Math via the new pyramid switch in the sidebar (works in both Simple and Advanced modes).
- **Hybrid LUTwithBGrid mode** — takes brightness from the model, keeps original color. Prevents color cast on PBR textures.

### 🛠 Improved
- `smart_correct_ai()` now selects the model based on user choice (saved in config.json)
- Version bumped to 1.5.0-beta

---


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


---


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

---


## [1.2.1] — 2026-09-13

### ✨ Added
- Correction mode switch (AI / Math)
- Auto system language detection
- Concrete preset

### 🐛 Fixed
- Fallback dialog translation
- Duplicate dialog
- Preset label translation

---


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

---


## [1.1.0] — 2026-09-12

### ✨ Added
- PBR map generation (7 maps)
- Batch processing
- Compression
- RU / EN interface
- Preset system

### 🎉 Initial release