markdown
# ◐ Albedolizer

**PBR Albedo Checker & Optimizer** — a tool for checking, correcting, and generating PBR maps from Albedo textures.

![Version](https://img.shields.io/badge/version-1.4.0--beta-orange)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10%2B-yellow)

[🇷🇺 Русская версия ниже](#-русская-версия)

---

## 📖 What is it

Albedolizer is a tool for 3D artists, game designers, and anyone working with PBR textures. It checks Albedo maps against standards, automatically corrects color via an AI model, generates a full set of PBR maps, and lets you preview the result in a built-in 3D viewer.

---

## ✨ Features

### 🔍 Albedo Analysis
- Dark and light pixel check against standards for each texture type
- Problem zone visualization (heatmap)
- Detailed statistics: min / max / avg / median / percentiles
- **Soap removal** — adaptive unsharp mask that fixes blurry patches after AI correction or upscaling

### ✨ AI Auto-Correction
- **Two modes:** AI (via Autolevels XCiT model) or Math (CLAHE + soft-clip)
- One-click switch in the sidebar — pick what works best for your texture
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

### 👁 Built-in 3D Viewer
- Real-time PBR preview via OpenGL (`viewer.exe`)
- Rotate with LMB, zoom with mouse wheel
- Powered by Moderngl + GLFW
- HDRI environment lighting with blurred reflections

### 📖 Built-in Manual
- Full HTML manual with screenshots and annotations
- Russian / English — switch inside the manual
- Opens in your browser from the **Info → 📖 Manual** button

### 🎯 37 Texture Presets in 6 Categories
**🔥 Metal** · **🌿 Nature** · **🪨 Mineral** · **🧪 Synthetic** · **💧 Special** · **🐾 Fauna**

### 🗂 Batch Processing
- Process folders or file lists
- Two modes: AI correction or compression
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

1. Download `Albedolizer_Setup_v1.4.0-beta.exe` from the [latest release](../../releases/latest)
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

### Batch processing
1. **Batch** tab
2. **📁 Select folder** or **📄 Select files**
3. Pick a mode: AI correction or compression
4. **▶ Run processing**
5. Output goes to `_corrected` or `_compressed` folder next to sources

### Compression
1. **🗜 Compress** tab
2. **📂 Open** for single file, or **📁 Select folder** for batch
3. **🗜 Compress** or **▶ Compress folder**
4. Output to `_compressed` folder next to sources

### Manual
Click **ℹ Info** in the header → **📖 Manual** tab.

---

## 🛠 Tech Stack

- **[Flet](https://flet.dev/)** — cross-platform UI in Python
- **[NumPy](https://numpy.org/)** — math and array operations
- **[Pillow](https://python-pillow.org/)** — image processing
- **[OpenCV](https://opencv.org/)** — Sobel filters for Edge Map
- **[Moderngl](https://moderngl.readthedocs.io/)** + **[GLFW](https://www.glfw.org/)** — 3D viewer
- **Autolevels** (XCiT-tiny) — AI color correction model

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

## 📄 License

MIT — free to use, including in commercial projects.

---

**Author:** INV.LVL  
**Version:** 1.4.0-beta  
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

## ✨ Возможности

### 🔍 Анализ Albedo
- Проверка тёмных и светлых пикселей по стандартам для каждого типа текстуры
- Визуализация проблемных зон (heatmap)
- Детальная статистика: min / max / avg / median / перцентили
- **Устранение «мыла»** — адаптивный unsharp mask, чинит размытые участки после AI-коррекции

### ✨ AI-автокоррекция
- **Два режима:** AI (через модель Autolevels XCiT) или Math (CLAHE + soft-clip)
- Переключатель в сайдбаре — выбирай что лучше для твоей текстуры
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

### 👁 Встроенный 3D-вьюер
- Просмотр PBR в реальном времени через OpenGL (`viewer.exe`)
- Вращение ЛКМ, зум колесом
- На базе Moderngl + GLFW
- HDRI-освещение с размытыми отражениями

### 📖 Встроенный мануал
- Полный HTML-мануал со скринами и разметкой
- Русский / English — переключение внутри мануала
- Открывается из **Info → 📖 Мануал**

### 🎯 37 пресетов текстур в 6 категориях
**🔥 Металл** · **🌿 Природа** · **🪨 Минерал** · **🧪 Синтетика** · **💧 Спецэффекты** · **🐾 Фауна**

### 🗂 Пакетная обработка
- Обработка папок или списка файлов
- Два режима: AI-коррекция или сжатие
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

1. Скачай `Albedolizer_Setup_v1.4.0-beta.exe` из [последнего релиза](../../releases/latest)
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

### Пакетная обработка
1. Вкладка **Пакетная**
2. **📁 Выбрать папку** или **📄 Выбрать файлы**
3. Выбери режим: AI-коррекция или сжатие
4. **▶ Запустить обработку**
5. Результат в папке `_corrected` или `_compressed` рядом с исходниками

### Сжатие
1. Вкладка **🗜 Сжатие**
2. **📂 Открыть** для одного файла или **📁 Выбрать папку** для пакета
3. **🗜 Сжать** или **▶ Сжать папку**
4. Результат в папке `_compressed` рядом с исходниками

### Мануал
Нажми **ℹ Инфо** в хедере → вкладка **📖 Мануал**.

---

## 🛠 Технологии

- **[Flet](https://flet.dev/)** — кроссплатформенный UI на Python
- **[NumPy](https://numpy.org/)** — математика и работа с массивами
- **[Pillow](https://python-pillow.org/)** — работа с изображениями
- **[OpenCV](https://opencv.org/)** — Sobel-фильтры для Edge Map
- **[Moderngl](https://moderngl.readthedocs.io/)** + **[GLFW](https://www.glfw.org/)** — 3D-вьюер
- **Autolevels** (XCiT-tiny) — AI-модель цветокоррекции

---

## 🤝 Вклад

Pull requests приветствуются. Для крупных изменений сначала откройте issue для обсуждения.

---

## 📄 Лицензия

MIT — используйте свободно, в том числе в коммерческих проектах.

---

**Автор:** INV.LVL  
**Версия:** 1.4.0-beta  
**Дата:** 2026
