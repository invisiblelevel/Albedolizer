# ◐ Albedolizer

**PBR Albedo Checker & Optimizer** — a tool for checking, correcting, and generating PBR maps from Albedo textures.

![Version](https://img.shields.io/badge/version-1.7.0--beta-orange)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10%2B-yellow)

[🇷🇺 Русская версия ниже](#-русская-версия)

---

## 📖 What is it

Albedolizer is a tool for 3D artists, game designers, and anyone working with PBR textures. It checks Albedo maps against standards, automatically corrects color via an AI model, generates a full set of PBR maps, and lets you preview the result in a built-in 3D viewer.

---

## 🆕 What's new in v1.7.0-beta

### Major UI refactor
- **NavigationRail** on the left instead of tab buttons — 5 tabs: Single, Batch, PBR, Compress, Realism
- **Own right panel** for each tab (previously a universal pile)
- **BottomSheet log** at the bottom — single, collapsible, shows the last line

### New Realism tab
- **Procedural photorealism filter** — grain + high-pass + HSV variation + vignette
- Three sliders: grain, detail, variation
- Zoom in preview (mouse wheel)

### Improvements
- **Batch:** threads slider (1–8 parallel tasks)
- **Compress:** PNG bit depth selector (8/16-bit)

### Optimization
- **Slim exe:** ~140 MB → ~119 MB (CUDA/TensorRT/ffmpeg stripped)

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

### 🎞 Realism Filter
- **Procedural photorealism** — adds camera-like imperfection to albedo textures
- **Grain** — fine and coarse noise layers
- **Detail** — adaptive high-pass overlay for micro-detail
- **Variation** — large-scale color/brightness patches + subtle vignette
- **Tileable noise** — noise pattern can be tiled without visible seams

### 👁 Built-in 3D Viewer
- Real-time PBR preview via OpenGL (`viewer.exe`)
- Rotate with LMB, zoom with mouse wheel
- Powered by Moderngl + GLFW
- HDRI environment lighting with blurred reflections
- Correct UV mapping — no seams or stretching

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

---

## 🚀 Installation

### Installer (recommended)

1. Download `Albedolizer_Setup_v1.7.0-beta.exe` from the [latest release](../../releases/latest)
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
7. **👁 3D Preview** — opens the OpenGL viewer
8. **💾 Save all** — creates a `<name>_pbr/` folder

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
- **[Moderngl](https://moderngl.readthedocs.io/)** + **[GLFW](https://www.glfw.org/)** — 3D viewer
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
**Version:** 1.7.0-beta  
**Date:** 2026

---

<br>
<br>

# ◐ Albedolizer

**PBR Albedo Checker & Optimizer** — утилита для проверки, коррекции и генерации PBR-карт из Albedo-текстур.

---

## 📖 Что это

Albedolizer — инструмент для 3D-художников, геймдизайнеров и всех, кто работает с PBR-текстурами. Он проверяет Albedo-карты на соответствие стандартам, автоматически корректирует цвет через AI-модель, генерирует полный набор PBR-карт и позволяет посмотреть результат во встроенном 3D-вьюере.

---

## 🆕 Что нового в v1.7.0-beta

### Крупный рефакторинг UI
- **NavigationRail** слева вместо кнопок-табов — 5 вкладок: Single, Batch, PBR, Compress, Realism
- **Своя правая панель** у каждой вкладки (раньше была одна универсальная свалка)
- **BottomSheet-лог** снизу — один общий, сворачивается кликом, показывает последнюю строку

### Новая вкладка Realism
- **Процедурный фильтр фотореализма** — grain + high-pass + HSV-вариация + виньетка
- Три слайдера: зерно, детализация, вариация
- Zoom в превью (колесо мыши)

### Улучшения
- **Batch:** слайдер потоков (1–8 параллельных задач)
- **Compress:** выбор битности PNG (8/16-bit)

### Оптимизация
- **exe slim:** ~140 МБ → ~119 МБ (вырезаны CUDA/TensorRT/ffmpeg)

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

### 🎞 Фильтр реализма
- **Процедурный фотореализм** — добавляет текстуре «неидеальность» как на фото
- **Grain** — мелкое и крупное зерно
- **Detail** — адаптивный high-pass для микро-деталей
- **Variation** — крупные пятна цвета/яркости + лёгкая виньетка
- **Тайлящийся шум** — паттерн не создаёт видимых швов при тайлинге

### 👁 Встроенный 3D-вьюер
- Просмотр PBR в реальном времени через OpenGL (`viewer.exe`)
- Вращение ЛКМ, зум колесом
- На базе Moderngl + GLFW
- HDRI-освещение с размытыми отражениями
- Корректный UV-маппинг — без швов и растяжения

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

---

## 🚀 Установка

### Инсталлер (рекомендуется)

1. Скачай `Albedolizer_Setup_v1.7.0-beta.exe` из [последнего релиза](../../releases/latest)
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
7. **👁 3D Preview** — открывает OpenGL-вьюер
8. **💾 Сохранить все** — создастся папка `<имя>_pbr/`

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
- **[Moderngl](https://moderngl.readthedocs.io/)** + **[GLFW](https://www.glfw.org/)** — 3D-вьюер
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
**Версия:** 1.7.0-beta  
**Дата:** 2026
