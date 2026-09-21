# ◐ Albedolizer

**PBR Albedo Checker & Optimizer** — a tool for checking, correcting, and generating PBR maps from Albedo textures.

![Version](https://img.shields.io/badge/version-1.7.1--beta-orange)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10%2B-yellow)

[🇷🇺 Русская версия ниже](#-русская-версия)

---

## 📖 What is it

Albedolizer is a tool for 3D artists, game designers, and anyone working with PBR textures. It checks Albedo maps against standards, automatically corrects color via an AI model, generates a full set of PBR maps, packs them for a target engine, and lets you preview the result in a built-in 3D viewer.

---

## Screenshots
![Main UI](screenshots/main_int.jpg)

## 🆕 What's new in v1.7.1-beta

### New Engine Export tab
- **Unity HDRP** — Mask Map (R=Metallic, G=AO, B=Detail, A=Smoothness)
- **Unity URP** — MetallicSmoothness (R=Metallic, A=Smoothness)
- **Unreal / Godot** — ORM (R=AO, G=Roughness, B=Metallic)
- **DirectX / OpenGL** normal map flip
- **Detail Mask** — white / edge map / custom file

### 3D viewer: tiling controls
- In-window panel with X/Y tiling buttons
- Scale from 1×1 up to 16×16
- Language follows the app language

### Quality of life
- **Last opened folder is remembered** across sessions
- **Realism tab Save** fixed, progress bar added for 8K textures
- **LUTwithBGrid** no longer blurs high-res textures (processes up to 6MP)

---

## ✨ Features

### 🔍 Albedo Analysis
- Dark and light pixel check against standards for each texture type
- Problem zone visualization (heatmap)
- Detailed statistics: min / max / avg / median / percentiles
- **Soap removal** — adaptive unsharp mask that fixes blurry patches after AI correction or upscaling

### ✨ AI Auto-Correction
- **Three methods:** Autolevels (XCiT model), LUTwithBGrid (ECCV 2024, ONNX), or Math (CLAHE + soft-clip)
- **Switch models** in the sidebar — pick what works best for your texture
- **🤖 Material auto-detection** — CLIP-based classifier (ViT-B/32) automatically picks the right preset from 47 options
- Fallback dialog if AI result doesn't pass validation
- **Saturation boost** — fix washed-out colors after AI correction

### 🎨 PBR Map Generation
- **Height** — height map
- **Normal** — normals (Sobel-based)
- **AO** — ambient occlusion
- **Roughness** — surface roughness
- **Metallic** — metalness (black / white / auto)
- **ORM** — packed map (AO in R, Roughness in G, Metallic in B)
- **Edge** — edge map (Sobel via OpenCV)
- **16-bit PNG output** — Height and Normal maps in full precision

### 🎮 Engine Export
- **Unity HDRP** Mask Map — R=Metallic, G=AO, B=Detail Mask, A=Smoothness
- **Unity URP** MetallicSmoothness — R=Metallic, A=Smoothness
- **Unreal ORM** — R=AO, G=Roughness, B=Metallic
- **Godot ORM** — R=AO, G=Roughness, B=Metallic
- **Normal map format** — OpenGL (Y+) / DirectX (Y-) with green channel flip
- **Detail Mask** for HDRP — white (1.0) / edge map / custom loaded from disk
- **Channel preview** — R / G / B / A / RGB / RGBA
- **Source:** current PBR result or a folder with `*_albedo.png`, `*_normal.png`, `*_ao.png`, etc.

### 🎞 Realism Filter
- **Procedural photorealism** — adds camera-like imperfection to albedo textures
- **Grain** — fine and coarse noise layers
- **Detail** — adaptive high-pass overlay for micro-detail
- **Variation** — large-scale color/brightness patches + subtle vignette
- **Tileable noise** — noise pattern can be tiled without visible seams

### 👁 Built-in 3D Viewer
- Real-time PBR preview via OpenGL (`viewer.exe`)
- **Tiling panel** — click X/Y buttons in the window to change texture scale (1×1 to 16×16)
- Rotate with LMB, zoom with mouse wheel
- Powered by Moderngl + GLFW + ImGui
- HDRI environment lighting with blurred reflections
- Correct UV mapping — no seams or stretching
- Viewer UI language follows the app language

### 📖 Built-in Manual
- Full HTML manual with screenshots and annotations
- Russian / English — switch inside the manual
- Opens in your browser from the **Info → 📖 Manual** button

### 🎯 47 Texture Presets in 7 Categories
**🔥 Metal** · **🌿 Nature** · **🪨 Mineral** · **🧪 Synthetic** · **🧵 Fabric** · **💧 Special** · **🐾 Fauna**

### 🗂 Batch Processing
- Process folders or file lists
- Two modes: AI correction or compression
- **Threads slider** — control parallelism (1–8)
- Progress bar with ETA

### 🌓 Themes & Modes
- Dark and light theme with one-click toggle
- **Simple / Advanced modes** — one-click workflow or full control
- Tiling checker (3×3 preview) to spot seams

### 🌐 Interface
- Russian / English with auto-detection
- Interactive preview with zoom (0.5x–8x)
- **Last opened folder is remembered** across sessions

---

## 🚀 Installation

### Installer (recommended)

1. Download `Albedolizer_Setup_v1.7.1-beta.exe` from the [latest release](../../releases/latest)
2. Run the installer — it places everything in `Program Files\Albedolizer`
3. Launch from Start Menu or Desktop shortcut

**Requirements:** Windows 10/11, 64-bit

### From source

    git clone https://github.com/invisiblelevel/Albedolizer.git
    cd Albedolizer
    pip install -r requirements.txt
    python main.py

---

## 🎮 Usage

### Single file processing
1. Pick a **texture type** on the right (e.g. 🌳 Wood)
2. Click **📂 Open** and select an Albedo texture
3. Click **🔍 Check** — you'll see stats and heatmap
4. If FAIL → **✨ Auto-Correct** (AI + fallback)
5. **💾 Save** the result

### PBR generation + 3D preview
1. **🎨 PBR** tab
2. **📂 Load Albedo**
3. Pick a **preset** (sliders auto-tune)
4. Adjust sliders if needed
5. **🎨 Generate** → 7 maps
6. Switch between maps with buttons on top
7. **👁 3D Preview** — opens the OpenGL viewer with tiling controls
8. **💾 Save all** — creates a `<name>_pbr/` folder

### Engine Export
1. **🎮 Engine** tab
2. **⚙️ From current PBR** (uses your last generated maps) or **📂 Load from folder**
3. Pick **engine:** Unity HDRP / URP / Unreal / Godot
4. Pick **normal map format:** OpenGL (Y+) or DirectX (Y-)
5. For HDRP — pick **Detail Mask:** white / edge / custom
6. **⚙️ Pack** — see the packed map in the preview
7. Switch channels: **R / G / B / A / RGB / RGBA**
8. **💾 Save all** — creates `<name>_<engine>_<gl|dx>/`

### Realism filter
1. **🎞 Realism** tab
2. **📂 Open** — load a texture
3. Adjust three sliders: **grain**, **detail**, **variation**
4. **🎞 Apply** — see the result in the preview
5. **💾 Save** the result

### Batch processing
1. **Batch** tab
2. **📁 Select folder** or **📄 Select files**
3. Choose correction method (Autolevels / LUTwithBGrid / Math) on the right
4. Set **threads** count (1–8)
5. **▶ Run processing**
6. Output goes to `_corrected` folder next to sources

### Compression
1. **🗜 Compress** tab
2. **📂 Open** for single file, or **📁 Select folder** for batch
3. Choose **8-bit** or **16-bit** PNG on the right
4. **🗜 Compress** or **▶ Compress folder**
5. Output to `_compressed` folder next to sources

### Manual
Click **ℹ Info** in the header → **📖 Manual** tab.

---

## 🛠 Tech Stack

- **[Flet](https://flet.dev/)** — cross-platform UI in Python
- **[NumPy](https://numpy.org/)** — math and array operations
- **[Pillow](https://python-pillow.org/)** — image processing
- **[OpenCV](https://opencv.org/)** — Sobel filters, HSV manipulation
- **[Moderngl](https://moderngl.readthedocs.io/)** + **[GLFW](https://www.glfw.org/)** + **[imgui-bundle](https://pypi.org/project/imgui-bundle/)** — 3D viewer with in-window controls
- **[ONNX Runtime](https://onnxruntime.ai/)** — inference for CLIP and LUTwithBGrid
- **[Transformers](https://huggingface.co/docs/transformers/)** + **[Tokenizers](https://huggingface.co/docs/tokenizers/)** — CLIP tokenizer
- **Autolevels** (XCiT-tiny) — AI color correction model

---

## 🙏 Credits

- **LUTwithBGrid** (ECCV 2024) — Wontae Kim, Nam Ik Cho — [Apache 2.0](https://github.com/WontaeaeKim/LUTwithBGrid)

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

## 📄 License

MIT — free to use, including in commercial projects.

---

**Author:** INV.LVL  
**Version:** 1.7.1-beta  
**Date:** 2026

---

<br>
<br>

# ◐ Albedolizer

**PBR Albedo Checker & Optimizer** — утилита для проверки, коррекции и генерации PBR-карт из Albedo-текстур.

---

## 📖 Что это

Albedolizer — инструмент для 3D-художников, геймдизайнеров и всех, кто работает с PBR-текстурами. Он проверяет Albedo-карты на соответствие стандартам, автоматически корректирует цвет через AI-модель, генерирует полный набор PBR-карт, упаковывает их под конкретный движок и позволяет посмотреть результат во встроенном 3D-вьюере.

---

## 🆕 Что нового в v1.7.1-beta

### Новая вкладка «Движок» (Engine Export)
- **Unity HDRP** — Mask Map (R=Metallic, G=AO, B=Detail, A=Smoothness)
- **Unity URP** — MetallicSmoothness (R=Metallic, A=Smoothness)
- **Unreal / Godot** — ORM (R=AO, G=Roughness, B=Metallic)
- **DirectX / OpenGL** — переворот Normal map
- **Detail Mask** — белая / edge-карта / своя с диска

### 3D-вьюер: управление тайлингом
- Панель с кнопками X/Y прямо в окне вьюера
- Масштаб от 1×1 до 16×16
- Язык панели следует за языком приложения

### Качество жизни
- **Запоминается последняя папка** между сессиями
- **Realism:** кнопка Save починена, добавлен прогресс-бар для 8K
- **LUTwithBGrid** больше не мылит текстуры высокого разрешения (обработка до 6 МП)

---

## ✨ Возможности

### 🔍 Анализ Albedo
- Проверка тёмных и светлых пикселей по стандартам для каждого типа текстуры
- Визуализация проблемных зон (heatmap)
- Детальная статистика: min / max / avg / median / перцентили
- **Устранение «мыла»** — адаптивный unsharp mask, чинит размытые участки после AI-коррекции

### ✨ AI-автокоррекция
- **Три метода:** Autolevels (модель XCiT), LUTwithBGrid (ECCV 2024, ONNX) или Math (CLAHE + soft-clip)
- **Переключай модели** в сайдбаре — выбирай что лучше для твоей текстуры
- **🤖 Автоопределение материала** — CLIP-классификатор (ViT-B/32) сам подбирает пресет из 47 доступных
- Диалог выбора если AI не прошёл валидацию
- **Насыщенность** — фикс блеклых цветов после AI-коррекции

### 🎨 Генерация PBR-карт
- **Height** — карта высот
- **Normal** — нормали (на основе Sobel)
- **AO** — ambient occlusion
- **Roughness** — шероховатость
- **Metallic** — металличность (чёрная / белая / авто)
- **ORM** — упакованная карта (AO в R, Roughness в G, Metallic в B)
- **Edge** — карта граней (Sobel через OpenCV)
- **16-битный PNG** — Height и Normal в полной точности

### 🎮 Экспорт для движков
- **Unity HDRP** Mask Map — R=Metallic, G=AO, B=Detail Mask, A=Smoothness
- **Unity URP** MetallicSmoothness — R=Metallic, A=Smoothness
- **Unreal ORM** — R=AO, G=Roughness, B=Metallic
- **Godot ORM** — R=AO, G=Roughness, B=Metallic
- **Формат Normal** — OpenGL (Y+) / DirectX (Y-) с инверсией зелёного канала
- **Detail Mask** для HDRP — белая (1.0) / edge-карта / своя с диска
- **Просмотр каналов** — R / G / B / A / RGB / RGBA
- **Источник:** текущий PBR-результат или папка с `*_albedo.png`, `*_normal.png`, `*_ao.png` и т.д.

### 🎞 Фильтр реализма
- **Процедурный фотореализм** — добавляет текстуре «неидеальность» как на фото
- **Grain** — мелкое и крупное зерно
- **Detail** — адаптивный high-pass для микро-деталей
- **Variation** — крупные пятна цвета/яркости + лёгкая виньетка
- **Тайлящийся шум** — паттерн не создаёт видимых швов при тайлинге

### 👁 Встроенный 3D-вьюер
- Просмотр PBR в реальном времени через OpenGL (`viewer.exe`)
- **Панель тайлинга** — кнопки X/Y прямо в окне, масштаб от 1×1 до 16×16
- Вращение ЛКМ, зум колесом
- На базе Moderngl + GLFW + ImGui
- HDRI-освещение с размытыми отражениями
- Корректный UV-маппинг — без швов и растяжения
- Язык панели следует за языком приложения

### 📖 Встроенный мануал
- Полный HTML-мануал со скринами и разметкой
- Русский / English — переключение внутри мануала
- Открывается из **Info → 📖 Мануал**

### 🎯 47 пресетов текстур в 7 категориях
**🔥 Металл** · **🌿 Природа** · **🪨 Минерал** · **🧪 Синтетика** · **🧵 Ткани** · **💧 Спецэффекты** · **🐾 Фауна**

### 🗂 Пакетная обработка
- Обработка папок или списка файлов
- Два режима: AI-коррекция или сжатие
- **Слайдер потоков** — управление параллелизмом (1–8)
- Прогресс-бар с ETA

### 🌓 Темы и режимы
- Тёмная и светлая тема одной кнопкой
- **Simple / Advanced режимы** — workflow в одну кнопку или полный контроль
- Тайлинг-чекер (3×3) для поиска швов

### 🌐 Интерфейс
- Русский / English с автоопределением системы
- Интерактивное превью с зумом (0.5x–8x)
- **Запоминается последняя открытая папка** между сессиями

---

## 🚀 Установка

### Инсталлер (рекомендуется)

1. Скачай `Albedolizer_Setup_v1.7.1-beta.exe` из [последнего релиза](../../releases/latest)
2. Запусти установщик — всё встанет в `Program Files\Albedolizer`
3. Запускай из меню Пуск или ярлыка на рабочем столе

**Требования:** Windows 10/11, 64-bit

### Из исходников

    git clone https://github.com/invisiblelevel/Albedolizer.git
    cd Albedolizer
    pip install -r requirements.txt
    python main.py

---

## 🎮 Как пользоваться

### Одиночная обработка
1. Выбери **тип текстуры** справа (например, 🌳 Дерево)
2. Нажми **📂 Открыть** и выбери Albedo-текстуру
3. Нажми **🔍 Проверить** — увидишь статистику и heatmap
4. Если FAIL → **✨ Автокоррекция** (AI + fallback)
5. **💾 Сохранить** результат

### PBR-генерация + 3D-превью
1. Вкладка **🎨 PBR**
2. **📂 Загрузить Albedo**
3. Выбери **пресет** (слайдеры настроятся автоматически)
4. При необходимости подкрути параметры
5. **🎨 Сгенерировать** → 7 карт
6. Переключайся между картами кнопками сверху
7. **👁 3D Preview** — открывает OpenGL-вьюер с панелью тайлинга
8. **💾 Сохранить все** — создастся папка `<имя>_pbr/`

### Экспорт для движков
1. Вкладка **🎮 Движок**
2. **⚙️ Из текущего PBR** (берёт последние сгенерированные карты) или **📂 Загрузить из папки**
3. Выбери **движок:** Unity HDRP / URP / Unreal / Godot
4. Выбери **формат Normal:** OpenGL (Y+) или DirectX (Y-)
5. Для HDRP — выбери **Detail Mask:** белая / edge / своя
6. **⚙️ Упаковать** — увидишь упакованную карту в превью
7. Переключай каналы: **R / G / B / A / RGB / RGBA**
8. **💾 Сохранить все** — создастся папка `<имя>_<движок>_<gl|dx>/`

### Фильтр реализма
1. Вкладка **🎞 Realism**
2. **📂 Открыть** — загрузи текстуру
3. Крути три слайдера: **зерно**, **детализация**, **вариация**
4. **🎞 Применить** — результат в превью
5. **💾 Сохранить** результат

### Пакетная обработка
1. Вкладка **Пакетная**
2. **📁 Выбрать папку** или **📄 Выбрать файлы**
3. Выбери метод коррекции справа (Autolevels / LUTwithBGrid / Math)
4. Задай **потоки** (1–8)
5. **▶ Запустить обработку**
6. Результат в папке `_corrected` рядом с исходниками

### Сжатие
1. Вкладка **🗜 Сжатие**
2. **📂 Открыть** для одного файла или **📁 Выбрать папку** для пакета
3. Выбери **8-bit** или **16-bit** PNG справа
4. **🗜 Сжать** или **▶ Сжать папку**
5. Результат в папке `_compressed` рядом с исходниками

### Мануал
Нажми **ℹ Инфо** в хедере → вкладка **📖 Мануал**.

---

## 🛠 Технологии

- **[Flet](https://flet.dev/)** — кроссплатформенный UI на Python
- **[NumPy](https://numpy.org/)** — математика и работа с массивами
- **[Pillow](https://python-pillow.org/)** — работа с изображениями
- **[OpenCV](https://opencv.org/)** — Sobel-фильтры, HSV-манипуляции
- **[Moderngl](https://moderngl.readthedocs.io/)** + **[GLFW](https://www.glfw.org/)** + **[imgui-bundle](https://pypi.org/project/imgui-bundle/)** — 3D-вьюер с внутриоконными контролами
- **[ONNX Runtime](https://onnxruntime.ai/)** — инференс CLIP и LUTwithBGrid
- **[Transformers](https://huggingface.co/docs/transformers/)** + **[Tokenizers](https://huggingface.co/docs/tokenizers/)** — CLIP-токенайзер
- **Autolevels** (XCiT-tiny) — AI-модель цветокоррекции

---

## 🤝 Вклад

Pull requests приветствуются. Для крупных изменений сначала откройте issue для обсуждения.

---

## 📄 Лицензия

MIT — используйте свободно, в том числе в коммерческих проектах.

---

**Автор:** INV.LVL  
**Версия:** 1.7.1-beta  
**Дата:** 2026