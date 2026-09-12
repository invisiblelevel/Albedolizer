# ◐ Albedolizer

**PBR Albedo Checker & Optimizer** — a tool for checking, correcting, and generating PBR maps from Albedo textures.

![Version](https://img.shields.io/badge/version-1.1.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10%2B-yellow)

[🇷🇺 Русская версия ниже](#-русская-версия)

---

## 📖 What is it

Albedolizer is a tool for 3D artists, game designers, and anyone working with PBR textures. It checks Albedo maps against standards, automatically corrects color via an AI model, and generates a full set of PBR maps.

**Why not Materialize?** Materialize is slow — it takes forever to load an Albedo and even longer to save files. Albedolizer does the same job **many times faster**, plus it supports **batch processing**, which Materialize lacks.

---

## ✨ Features

### 🔍 Albedo Analysis
- Dark and light pixel check against standards for each texture type
- Problem zone visualization (heatmap)
- Detailed statistics: min / max / avg / median / percentiles

### ✨ AI Auto-Correction
- Correction via the Autolevels neural network (XCiT model)
- Fallback mathematical algorithm (CLAHE + soft-clip)
- User dialog when AI result doesn't pass validation

### 🎨 PBR Map Generation
- **Height** — height map
- **Normal** — normals (Sobel-based)
- **AO** — ambient occlusion
- **Roughness** — surface roughness
- **Metallic** — metalness (black / white / auto)
- **ORM** — packed map (AO in R, Roughness in G, Metallic in B)
- **Edge** — edge map (Sobel via OpenCV)

### 🎯 Texture Presets
10 texture types with ready-to-use PBR parameters:
🌳 Wood · 🪨 Stone · ⚙ Metal · 🌍 Ground · 🔴 Rust · 🧱 Brick · 🌿 Leaves · 🍂 Organic · Concrete · Moss

### 🗂 Batch Processing
- Process folders or file lists
- Two modes: AI correction or compression
- Progress bar with ETA

### 🌐 Interface
- Russian / English
- Dark theme
- Interactive preview with zoom (0.5x–8x)

---

## 🚀 Installation

### Pre-built binary (recommended)

1. Download `Albedolizer.exe` from the [latest release](../../releases/latest)
2. Run it — no installation required
3. Windows 10/11, 64-bit

### From source

```bash
git clone https://github.com/invisiblelevel/Albedolizer.git
cd Albedolizer
pip install -r requirements.txt
python main.py
```

### Building the exe

```bash
python -m PyInstaller --onefile --windowed --name Albedolizer ^
  --icon=icon.ico ^
  --add-data "autolevels.exe;." ^
  --add-data "free_xcittiny_wa14.onnx;." ^
  --add-data "icon.ico;." ^
  --clean main.py
```

Output: `dist/Albedolizer.exe`

---

## 🎮 Usage

### Single file processing
1. Pick a **texture type** on the right (e.g. 🌳 Wood)
2. Click **📂 Open** and select an Albedo texture
3. Click **🔍 Check** — you'll see stats and heatmap
4. If FAIL → **✨ Auto-Correct** (AI + fallback)
5. **💾 Save** the result

### PBR generation
1. **🎨 PBR** tab
2. **📂 Load Albedo**
3. Pick a **preset** (sliders auto-tune)
4. Adjust sliders if needed
5. **🎨 Generate** → 7 maps
6. Switch between maps with buttons on top
7. **💾 Save all** — creates a `<name>_pbr/` folder

### Batch processing
1. **Batch** tab
2. **📁 Select folder** or **📄 Select files**
3. Pick a mode: AI correction or compression
4. **▶ Run processing**
5. Output goes to `_corrected` or `_compressed` folder next to sources

---

## 🛠 Tech Stack

- **[Flet](https://flet.dev/)** — cross-platform UI in Python
- **[NumPy](https://numpy.org/)** — math and array operations
- **[Pillow](https://python-pillow.org/)** — image processing
- **[OpenCV](https://opencv.org/)** — Sobel filters for Edge Map
- **Autolevels** (XCiT-tiny) — AI color correction model

---

## 📁 Project Structure

```
Albedolizer/
├── main.py                  # Main file: UI and logic
├── pbr_generator.py         # PBR map generator
├── autolevels.exe           # AI correction (external process)
├── free_xcittiny_wa14.onnx  # AI model
├── icon.ico                 # App icon
├── main.spec                # PyInstaller config
├── requirements.txt
├── README.md
└── LICENSE
```

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

## 📄 License

MIT — free to use, including in commercial projects.

---

**Author:** INV.LVL  
**Version:** 1.1.0  
**Date:** 2026

---

<br>
<br>

# ◐ Albedolizer

**PBR Albedo Checker & Optimizer** — утилита для проверки, коррекции и генерации PBR-карт из Albedo-текстур.

---

## 📖 Что это

Albedolizer — инструмент для 3D-художников, геймдизайнеров и всех, кто работает с PBR-текстурами. Он проверяет Albedo-карты на соответствие стандартам, автоматически корректирует цвет через AI-модель и генерирует полный набор PBR-карт.

**Почему не Materialize?** Materialize тормозит — долго загружает Albedo и ещё дольше сохраняет файлы. Albedolizer делает ту же работу **в разы быстрее**, плюс поддерживает **пакетную обработку**, которой у Materialize нет.

---

## ✨ Возможности

### 🔍 Анализ Albedo
- Проверка тёмных и светлых пикселей по стандартам для каждого типа текстуры
- Визуализация проблемных зон (heatmap)
- Детальная статистика: min / max / avg / median / перцентили

### ✨ AI-автокоррекция
- Коррекция через нейросеть Autolevels (модель XCiT)
- Резервный математический алгоритм (CLAHE + soft-clip)
- Диалог выбора при неудовлетворительном результате AI

### 🎨 Генерация PBR-карт
- **Height** — карта высот
- **Normal** — нормали (на основе Sobel)
- **AO** — ambient occlusion
- **Roughness** — шероховатость
- **Metallic** — металличность (чёрная / белая / авто)
- **ORM** — упакованная карта (AO в R, Roughness в G, Metallic в B)
- **Edge** — карта граней (Sobel через OpenCV)

### 🎯 Пресеты текстур
10 типов текстур с готовыми параметрами PBR:
🌳 Дерево · 🪨 Камень · ⚙ Металл · 🌍 Земля · 🔴 Ржавчина · 🧱 Кирпич · 🌿 Листва · 🍂 Органика · Бетон · Мох

### 🗂 Пакетная обработка
- Обработка папок или списка файлов
- Два режима: AI-коррекция или сжатие
- Прогресс-бар с ETA

### 🌐 Интерфейс
- Русский / English
- Тёмная тема
- Интерактивное превью с зумом (0.5x–8x)

---

## 🚀 Установка

### Готовый билд (рекомендуется)

1. Скачай `Albedolizer.exe` из [последнего релиза](../../releases/latest)
2. Запусти — установка не требуется
3. Windows 10/11, 64-bit

### Из исходников

```bash
git clone https://github.com/invisiblelevel/Albedolizer.git
cd Albedolizer
pip install -r requirements.txt
python main.py
```

### Сборка exe

```bash
python -m PyInstaller --onefile --windowed --name Albedolizer ^
  --icon=icon.ico ^
  --add-data "autolevels.exe;." ^
  --add-data "free_xcittiny_wa14.onnx;." ^
  --add-data "icon.ico;." ^
  --clean main.py
```

Готовый файл: `dist/Albedolizer.exe`

---

## 🎮 Как пользоваться

### Одиночная обработка
1. Выбери **тип текстуры** справа (например, 🌳 Дерево)
2. Нажми **📂 Открыть** и выбери Albedo-текстуру
3. Нажми **🔍 Проверить** — увидишь статистику и heatmap
4. Если FAIL → **✨ Автокоррекция** (AI + fallback)
5. **💾 Сохранить** результат

### PBR-генерация
1. Вкладка **🎨 PBR**
2. **📂 Загрузить Albedo**
3. Выбери **пресет** (слайдеры настроятся автоматически)
4. При необходимости подкрути параметры
5. **🎨 Сгенерировать** → 7 карт
6. Переключайся между картами кнопками сверху
7. **💾 Сохранить все** — создастся папка `<имя>_pbr/`

### Пакетная обработка
1. Вкладка **Пакетная**
2. **📁 Выбрать папку** или **📄 Выбрать файлы**
3. Выбери режим: AI-коррекция или сжатие
4. **▶ Запустить обработку**
5. Результат в папке `_corrected` или `_compressed` рядом с исходниками

---

## 🛠 Технологии

- **[Flet](https://flet.dev/)** — кроссплатформенный UI на Python
- **[NumPy](https://numpy.org/)** — математика и работа с массивами
- **[Pillow](https://python-pillow.org/)** — работа с изображениями
- **[OpenCV](https://opencv.org/)** — Sobel-фильтры для Edge Map
- **Autolevels** (XCiT-tiny) — AI-модель цветокоррекции

---

## 📁 Структура проекта

```
Albedolizer/
├── main.py                  # Главный файл: UI и логика
├── pbr_generator.py         # Генератор PBR-карт
├── autolevels.exe           # AI-коррекция (внешний процесс)
├── free_xcittiny_wa14.onnx  # AI-модель
├── icon.ico                 # Иконка приложения
├── main.spec                # Конфиг PyInstaller
├── requirements.txt
├── README.md
└── LICENSE
```

---

## 🤝 Вклад

Pull requests приветствуются. Для крупных изменений сначала откройте issue для обсуждения.

---

## 📄 Лицензия

MIT — используйте свободно, в том числе в коммерческих проектах.

---

**Автор:** INV.LVL  
**Версия:** 1.1.0  
**Дата:** 2026
