"""
translations.py — все переводы интерфейса Albedolizer (RU + EN + ZH).
Только данные, никакой логики.

UI-строки (кнопки, табы, заголовки) — БЕЗ эмодзи.
Лог-строки — эмодзи оставлены как цветовые маркеры статуса.
"""

import os

T = {
    "ru": {
        "subtitle": "PBR Albedo Checker & Optimizer",
        # ─── Табы (rail) ───
        "tab_single": "Одиночная", "tab_pbr": "PBR",
        "tab_compress": "Сжатие", "tab_batch": "Пакетная",
        "tab_realism": "Реализм", "tab_export": "Движок",
        # ─── Кнопки тулбара ───
        "load": "Открыть", "check": "Проверить",
        "fix": "Автокоррекция", "compress": "Сжать",
        "save": "Сохранить", "reset": "Сброс",
        "preview_toggle_orig": "Оригинал",
        "preview_toggle_result": "Результат",
        # ─── Заголовки панелей ───
        "stats_title": "СТАТИСТИКА", "profile_title": "ТИП ТЕКСТУРЫ",
        "correction_mode_title": "МЕТОД КОРРЕКЦИИ",
        "soap_fix_title": "УБРАТЬ МЫЛО",
        "sat_title": "НАСЫЩЕННОСТЬ",
        "seamless_title": "SEAMLESS",
        "pbr_params": "ПАРАМЕТРЫ PBR",
        "export_title": "ЭКСПОРТ ДЛЯ ДВИЖКОВ",
        "realism_params": "ПАРАМЕТРЫ",
        "realism_presets": "ПРЕСЕТЫ",
        # ─── Auto-detect ───
        "auto_detect_btn": "Автоопределить материал",
        "auto_detect_progress": "🤖 Определение материала...",
        "auto_detect_loading": "   🔄 Загрузка CLIP...",
        "auto_detect_result": "🤖 АВТООПРЕДЕЛЕНИЕ МАТЕРИАЛА",
        "auto_detect_winner": "   🏆 Результат:",
        "auto_detect_top5": "   📊 Топ-5:",
        "auto_detect_changed": "   → Пресет изменён:",
        "auto_detect_same": "   → Пресет не изменился",
        "auto_detect_fail": "   ⚠ Не удалось определить материал",
        "auto_detect_no_tex": "   ⚠ Сначала загрузи текстуру",
        "auto_detect_no_clip": "   ⚠ Не удалось загрузить CLIP-модель",
        # ─── Correction method ───
        "correction_ai_autolevels": "Autolevels",
        "correction_ai_lutwithbgrid": "LUTwithBGrid",
        "correction_math": "Math",
        # ─── Soap / tiling / seamless ───
        "soap_fix_label": "Сила детализации",
        "soap_fix_button": "Убрать мыло",
        "tiling_btn": "Тайлинг 3×3",
        "tiling_btn_off": "Обычный вид",
        "seamless_btn": "Seamless",
        "seamless_done": "🔲 Текстура сделана бесшовной",
        "seamless_hipass": "Hi-pass (выровнять яркость)",
        "seamless_progress": "Делаем бесшовной...",
        "seamless_overlap": "Зона бленда (%)",
        "seamless_softness": "Мягкость",
        "seamless_scatter": "Волнистость",
        "seamless_apply": "Сделать бесшовной",
        "seamless_auto_tiling": "→ Авто-превью 3×3 включено",
        "soap_fix_done": "🔧 Детализация применена",
        "soap_fix_progress": "Убираем мыло...",
        # ─── Saturation ───
        "sat_label": "Множитель",
        "sat_button": "Поднять насыщенность",
        "sat_done": "🎨 Насыщенность повышена",
        "sat_progress": "Поднимаем насыщенность...",
        # ─── Прочее UI ───
        "all_types": "Все типы", "log_title": "ЛОГ",
        "info_btn": "Инфо", "lang_btn": "EN",
        "mode_btn_simple": "Simple",
        "mode_btn_advanced": "Advanced",
        "preview_hint": "Загрузи Albedo-текстуру, чтобы начать",
        # ─── Welcome dialog ───
        "welcome_title": "Добро пожаловать в Albedolizer",
        "welcome_text": (
            "Проверка, коррекция и генерация PBR-карт из Albedo-текстур.\n\n"
            "ДВА РЕЖИМА:\n"
            "• SIMPLE — одна кнопка «Обработать текстуру»: открыть → AI-коррекция → сохранить. Для быстрой работы.\n"
            "• ADVANCED — полный контроль: выбор пресета, метод коррекции, статистика, тайлинг, seamless, ручная настройка PBR.\n"
            "Переключение — кнопкой в хедере в любой момент.\n\n"
            "БЫСТРЫЙ СТАРТ (Simple):\n"
            "1. Нажми «Обработать текстуру» и выбери файл\n"
            "2. Результат появится через несколько секунд\n"
            "3. «Сохранить»\n\n"
            "PBR-вкладка — генерация 7 PBR-карт из Albedo.\n"
            "Engine — упаковка PBR-карт под Unity / Unreal / Godot."
        ),
        "welcome_ok": "Понятно, погнали",
        "welcome_manual": "Открыть мануал",
        "welcome_switch_simple": "Включить Advanced mode",
        # ─── Логи (эмодзи оставлены) ───
        "welcome_1": "👋 Добро пожаловать в Albedolizer v1.7.6-beta",
        "welcome_2": "→ Нажми «Открыть» для начала",
        "log_loaded": "📂 Загружено:", "log_type": "→ Тип:",
        "log_click_check": "→ Нажми «Проверить» для анализа",
        "log_results": "📊 РЕЗУЛЬТАТЫ",
        "log_dark": "тёмные", "log_light": "светлые",
        "log_pass": "✅ PASS — в допустимом диапазоне",
        "log_fail": "❌ FAIL — жми «Автокоррекция»",
        "log_fix_done": "✨ АВТОКОРРЕКЦИЯ ВЫПОЛНЕНА",
        "log_compress_done": "🗜 СЖАТИЕ ВЫПОЛНЕНО",
        "log_reset": "↺ Сброс выполнен", "log_saved": "💾 Сохранено:",
        "progress_check": "Проверка...", "progress_fix": "Умная коррекция...",
        "progress_compress": "LAB-прогон...", "progress_load": "Загрузка...",
        # ─── Stats ───
        "stat_min": "Мин:", "stat_max": "Макс:", "stat_avg": "Сред:",
        "stat_median": "Медиана:", "stat_p1": "1%:", "stat_p99": "99%:",
        # ─── Batch ───
        "batch_title": "ПАКЕТНАЯ ОБРАБОТКА",
        "batch_select_folder": "Выбрать папку",
        "batch_select_files": "Выбрать файлы",
        "batch_run": "Запустить обработку",
        "batch_ready": "Готово к запуску",
        "batch_files_count": "файлов",
        "batch_done": "Готово",
        "batch_folder": "Папка:",
        "batch_found": "Найдено файлов:",
        "batch_selected": "Выбрано файлов:",
        "batch_no_files": "⚠ Файлы не выбраны",
        "batch_started": "⚡ Пакетная обработка:",
        "batch_out": "Результат в:",
        "batch_processed": "Обработано:",
        "batch_right_title": "УПРАВЛЕНИЕ",
        "batch_right_info": "ИНФОРМАЦИЯ",
        "batch_threads_title": "ПОТОКИ",
        "batch_threads_label": "Параллельных задач (1–8)",
        "batch_right_hint": "Выбери папку или файлы → задай метод коррекции слева → жми «Запустить обработку».\n\nРезультат сохранится в папку _corrected рядом с исходниками.",
        # ─── Compress ───
        "compress_title": "СЖАТИЕ ALBEDO",
        "compress_single": "ОДИНОЧНОЕ СЖАТИЕ",
        "compress_batch": "ПАКЕТНОЕ СЖАТИЕ",
        "compress_run": "Сжать",
        "compress_batch_run": "Сжать папку",
        "compress_log_done": "🗜 Сжатие выполнено:",
        "compress_batch_started": "⚡ Пакетное сжатие:",
        "compress_out": "Результат в:",
        "compress_right_title": "НАСТРОЙКИ",
        "compress_right_info": "ИНФОРМАЦИЯ",
        "compress_right_hint": "Одиночное сжатие — файл → результат.\n\nПакетное — выбирай папку или файлы, жми «Сжать папку».\n\nРезультат в папке _compressed рядом с исходниками.",
        "compress_single_btn": "Сжать текстуру",
        "compress_batch_btn": "Сжать папку",
        "compress_simple_hint": "Открыть файл → LAB-прогон → автосохранение в _compressed рядом с исходником.",
        "compress_batch_hint": "Выбрать папку → LAB все файлы → _compressed рядом с исходниками.",
        "compress_done_title": "Сжатие завершено",
        "compress_done_single": "Файл сохранён:",
        "compress_done_batch": "Обработано файлов:",
        "compress_done_size": "Размер:",
        "compress_done_grew": "Файл стал больше",
        "compress_done_same": "Размер не изменился",
        "compress_open_folder": "Открыть папку",
        "compress_ok": "OK",
        # ─── PBR ───
        "pbr_load": "Загрузить Albedo", "pbr_gen": "Сгенерировать",
        "pbr_batch": "Из папки", "pbr_save": "Сохранить все",
        "pbr_preset_label": "Пресет:",
        "pbr_bit_depth": "Битность PNG:",
        "pbr_bit_8": "8-bit",
        "pbr_bit_16": "16-bit",
        "pbr_metallic": "Metallic карта:",
        "pbr_metal_black": "Чёрная", "pbr_metal_white": "Белая",
        "pbr_metal_custom": "Своя",
        "pbr_metal_auto": "По цвету",
        "pbr_metal_auto_hint": "Ткни пипеткой в Albedo по металлу, потом Generate Metallic",
        "pbr_metal_pick": "Ткнуть в Albedo",
        "pbr_metal_pick_dialog": "Кликни по металлической части текстуры",
        "pbr_metal_pick_saved": "✅ Цвет выбран: RGB({r}, {g}, {b})",
        "pbr_metal_generate": "Сгенерировать маску",
        "pbr_metal_negative_pick": "Ткнуть в фон",
        "pbr_metal_negative_hint": "Кликни по НЕ-металлу (тени, фон) — исключим из маски",
        "pbr_metal_negative_saved": "🚫 Negative цвет: RGB({r}, {g}, {b})",
        "pbr_metal_negative_clear": "Убрать negative",
        "pbr_metal_negative_tolerance": "Negative tolerance",
        "pbr_metal_target_label": "Positive:",
        "pbr_metal_negative_label": "Negative:",
        "pbr_metal_generated": "🎨 Metallic маска сгенерирована",
        "pbr_metal_tolerance": "Tolerance (ширина маски)",
        "pbr_metal_softness": "Softness (мягкость границ)",
        "pbr_metal_no_pick": "⚠ Сначала ткни пипеткой в Albedo",
        "pbr_metal_pick_dialog_close": "OK",
        "pbr_metal_load": "Загрузить metallic map",
        "pbr_roughness": "Roughness карта:",
        "pbr_rough_procedural": "Процедурная",
        "pbr_rough_custom": "Своя",
        "pbr_rough_load": "Загрузить roughness map",
        "pbr_resize_title": "Размер не совпадает",
        "pbr_resize_text": "Карта {w1}×{h1} не совпадает с albedo {w2}×{h2}.\nРесайзить автоматически?",
        "pbr_resize_yes": "Ресайзить",
        "pbr_resize_no": "Отмена",
        "pbr_sl_strength": "Сила нормалей", "pbr_sl_smooth": "Сглаживание",
        "pbr_sl_threshold": "Порог (фон)", "pbr_sl_high_pass": "High-pass",
        "pbr_sl_height_blur": "Blur Height", "pbr_sl_ao_radius": "AO радиус",
        "pbr_sl_ao_intensity": "AO сила", "pbr_sl_rough_base": "Rough база",
        "pbr_sl_rough_var": "Rough вариация",
        "pbr_sl_rough_detail": "Rough detail",
        "pbr_preview_hint": "Загрузи Albedo и нажми «Сгенерировать»",
        "pbr_progress_gen": "Генерация PBR-карт...",
        "pbr_progress_batch": "PBR: обработка папки...",
        "pbr_log_loaded": "📂 PBR: загружено",
        "pbr_log_gen_done": "✅ PBR: сгенерировано 7 карт",
        "pbr_log_saved": "💾 PBR сохранено в",
        "pbr_log_no_files": "⚠ PBR: файлов в папке нет",
        "pbr_log_batch_done": "✅ PBR batch готово:",
        "pbr_log_files": "файлов",
        "pbr_dialog_pick": "Выбери Albedo для PBR",
        "pbr_dialog_folder": "Выбери папку с текстурами",
        "pbr_viewer": "3D Preview",
        "pbr_viewer_progress": "Запуск вьюера...",
        "pbr_viewer_no_result": "⚠ Сначала сгенерируй PBR-карты",
        "pbr_metal_auto_footer": "→ Жми «Сгенерировать» вверху для обновления PBR",
        "pbr_metal_presets_title": "ПРЕСЕТЫ ТОЧНОСТИ",
        "pbr_metal_preset_tight": "Точный",
        "pbr_metal_preset_medium": "Средний",
        "pbr_metal_preset_loose": "Широкий",
        "pbr_metal_manual_title": "РУЧНАЯ НАСТРОЙКА",
        "pbr_edge_info": "Edge генерируется автоматически из Height.\n\nНастроек нет — параметры фиксированные.",
        "pbr_orm_info": "ORM — упакованная карта.\n\nR = AO, G = Roughness, B = Metallic.\n\nНастраивай компоненты во вкладках AO, Rough и Metal.",
        # ─── Export ───
        "export_source": "ИСТОЧНИК",
        "export_target": "ДВИЖОК",
        "export_normal": "ФОРМАТ NORMAL MAP",
        "export_detail": "DETAIL MASK (HDRP)",
        "export_bit": "БИТНОСТЬ PNG",
        "export_layout": "РАСКЛАДКА КАНАЛОВ",
        "export_load_pbr": "Из текущего PBR",
        "export_load_folder": "Загрузить из папки",
        "export_pack": "Упаковать",
        "export_save": "Сохранить все",
        "export_load_detail": "Загрузить свою",
        "export_hint": "Выбери источник: PBR или папка",
        "export_source_none": "Источник: —",
        "export_engine_hdrp": "Unity HDRP — Mask Map",
        "export_engine_urp": "Unity URP — MetallicSmoothness",
        "export_engine_unreal": "Unreal — ORM",
        "export_engine_godot": "Godot — ORM",
        "export_normal_gl": "OpenGL (Y+)",
        "export_normal_dx": "DirectX (Y-)",
        "export_detail_white": "White (1.0)",
        "export_detail_edge": "Edge map",
        "export_detail_custom": "Своя (загрузить)",
        "export_progress_pack": "📦 Упаковка...",
        "export_progress_save": "💾 Сохранение...",
        "export_log_source_pbr": "📦 Export: источник — текущий PBR",
        "export_log_source_folder": "📦 Export: загружено из папки",
        "export_log_packed": "📦 Упаковано",
        "export_log_saved": "💾 Export сохранён:",
        "export_log_no_pbr": "⚠ PBR-карты не сгенерированы",
        "export_log_no_normal": "⚠ В папке нет *_normal.png",
        "export_log_no_source": "⚠ Сначала выбери источник",
        "export_log_no_packed": "⚠ Нечего сохранять — сначала упакуй",
        "export_log_detail_loaded": "📦 Detail Mask загружена:",
        # ─── Realism ───
        "realism_grain": "Зерно",
        "realism_highpass": "Детализация",
        "realism_variation": "Вариация",
        "realism_preset_soft": "Мягкий",
        "realism_preset_medium": "Средний",
        "realism_preset_hard": "Жёсткий",
        "realism_apply": "Применить",
        "realism_preset_log": "Пресет",
        "realism_preview_hint": "Загрузи текстуру и настрой фильтр",
        "realism_progress": "Наложение фотореализма...",
        "realism_done": "🎞 Фильтр применён",
        # ─── Диалоги ───
        "dialog_save_title": "Сохранить результат",
        "dialog_pick_title": "Выбери текстуру",
        "err": "Ошибка",
        "fb_dialog_title": "Результат AI не прошёл проверку",
        "fb_dialog_text": "AI убрал цветовой сдвиг, но яркость вне порога:",
        "fb_dialog_dark": "Тёмные:",
        "fb_dialog_light": "Светлые:",
        "fb_dialog_question": "Применить CLAHE fallback?",
        "fb_dialog_keep_ai": "Оставить AI",
        "fb_dialog_apply": "Применить fallback",
        "fb_dialog_kept": "   → Оставлен результат AI как есть",
        "fb_dialog_applied": "   ✨ Fallback применён к результату AI",
        "fb_dialog_progress": "Fallback коррекция...",
        "fb_dialog_err": "Fallback ошибка:",
        # ─── Info dialog ───
        "info_tab_help": "Справка",
        "info_tab_manual": "Мануал",
        "info_tab_about": "О программе",
        "info_tab_support": "Поддержать",
        "support_title": "Поддержать разработку",
        "support_text": ("Albedolizer — бесплатный инструмент.\n"
                          "Если он экономит тебе время — можешь закинуть на папиросы.\n"
                          "Спасибо!"),
        "support_copied": "✅ Скопировано!",
        "about_version": "Версия", "about_build": "Сборка",
        "about_author": "Автор", "about_license": "Лицензия",
        "about_desc": ("Albedolizer — утилита для проверки и оптимизации\n"
                        "Albedo-карт PBR-текстур. LAB + Autolevels AI."),
        "help_text": (
            "Albedolizer — руководство\n\n"
            "РЕЖИМЫ\n\n"
            "SIMPLE — для быстрой работы\n"
            "Одна кнопка «Обработать текстуру»:\n"
            "1. Открывает файл\n"
            "2. AI-коррекция цвета\n"
            "3. Поднимает насыщенность на 15%\n"
            "Результат за 30 секунд.\n\n"
            "ADVANCED — для полного контроля\n"
            "Открывает все инструменты:\n"
            "- Режим коррекции (AI / Math)\n"
            "- Убирание мыла\n"
            "- Насыщенность\n"
            "- Tiling-checker\n"
            "- Пакетная обработка\n"
            "- Сжатие\n\n"
            "Переключайся между режимами кнопкой в хедере.\n\n"
            "ОДИНОЧНАЯ (Advanced)\n"
            "1. Выбери тип текстуры\n"
            "2. «Открыть» → «Проверить»\n"
            "3. Если FAIL — «Автокоррекция»\n"
            "4. «Сохранить»\n\n"
            "PBR\n"
            "1. «Загрузить Albedo»\n"
            "2. Выбери пресет\n"
            "3. «Сгенерировать» → «Сохранить все»\n\n"
            "СЖАТИЕ\n"
            "Одиночное или пакетное сжатие Albedo.\n\n"
            "ПАКЕТНАЯ\n"
            "AI-коррекция целой папки."
        ),
    },
    "en": {
        "subtitle": "PBR Albedo Checker & Optimizer",
        # ─── Tabs ───
        "tab_single": "Single", "tab_pbr": "PBR",
        "tab_compress": "Compress", "tab_batch": "Batch",
        "tab_realism": "Realism", "tab_export": "Engine",
        # ─── Toolbar ───
        "load": "Open", "check": "Check",
        "fix": "Auto-Correct", "compress": "Compress",
        "save": "Save", "reset": "Reset",
        "preview_toggle_orig": "Original",
        "preview_toggle_result": "Result",
        # ─── Panel titles ───
        "stats_title": "STATISTICS", "profile_title": "TEXTURE TYPE",
        "correction_mode_title": "CORRECTION METHOD",
        "soap_fix_title": "REMOVE SOAP",
        "sat_title": "SATURATION",
        "seamless_title": "SEAMLESS",
        "pbr_params": "PBR PARAMETERS",
        "export_title": "ENGINE EXPORT",
        "realism_params": "PARAMETERS",
        "realism_presets": "PRESETS",
        # ─── Auto-detect ───
        "auto_detect_btn": "Auto-detect material",
        "auto_detect_progress": "🤖 Detecting material...",
        "auto_detect_loading": "   🔄 Loading CLIP...",
        "auto_detect_result": "🤖 MATERIAL AUTO-DETECTION",
        "auto_detect_winner": "   🏆 Result:",
        "auto_detect_top5": "   📊 Top-5:",
        "auto_detect_changed": "   → Preset changed:",
        "auto_detect_same": "   → Preset unchanged",
        "auto_detect_fail": "   ⚠ Could not detect material",
        "auto_detect_no_tex": "   ⚠ Load a texture first",
        "auto_detect_no_clip": "   ⚠ Could not load CLIP model",
        # ─── Correction ───
        "correction_ai_autolevels": "Autolevels",
        "correction_ai_lutwithbgrid": "LUTwithBGrid",
        "correction_math": "Math",
        # ─── Soap / tiling / seamless ───
        "soap_fix_label": "Detail strength",
        "soap_fix_button": "Remove soap",
        "tiling_btn": "Tiling 3×3",
        "tiling_btn_off": "Normal view",
        "seamless_btn": "Seamless",
        "seamless_done": "🔲 Texture made seamless",
        "seamless_hipass": "Hi-pass (even brightness)",
        "seamless_progress": "Making seamless...",
        "seamless_overlap": "Blend zone (%)",
        "seamless_softness": "Softness",
        "seamless_scatter": "Scatter",
        "seamless_apply": "Make seamless",
        "seamless_auto_tiling": "→ Auto 3×3 preview enabled",
        "soap_fix_done": "🔧 Detail enhanced",
        "soap_fix_progress": "Removing soap...",
        # ─── Saturation ───
        "sat_label": "Multiplier",
        "sat_button": "Boost saturation",
        "sat_done": "🎨 Saturation boosted",
        "sat_progress": "Boosting saturation...",
        # ─── Misc ───
        "all_types": "All types", "log_title": "LOG",
        "info_btn": "Info", "lang_btn": "RU",
        "mode_btn_simple": "Simple",
        "mode_btn_advanced": "Advanced",
        "preview_hint": "Load an Albedo texture to start",
        # ─── Welcome ───
        "welcome_title": "Welcome to Albedolizer",
        "welcome_text": (
            "Check, correct and generate PBR maps from Albedo textures.\n\n"
            "TWO MODES:\n"
            "• SIMPLE — one button «Process texture»: open → AI correct → save. For quick work.\n"
            "• ADVANCED — full control: preset picker, correction method, statistics, tiling, seamless, manual PBR tuning.\n"
            "Switch anytime via the header button.\n\n"
            "QUICK START (Simple):\n"
            "1. Click «Process texture» and pick a file\n"
            "2. Result appears in a few seconds\n"
            "3. «Save»\n\n"
            "PBR tab — generate 7 PBR maps from Albedo.\n"
            "Engine — pack PBR maps for Unity / Unreal / Godot."
        ),
        "welcome_ok": "Got it, let's go",
        "welcome_manual": "Open manual",
        "welcome_switch_simple": "Enable Advanced mode",
        # ─── Logs (emoji kept) ───
        "welcome_1": "👋 Welcome to Albedolizer v1.7.6-beta",
        "welcome_2": "→ Click «Open» to start",
        "log_loaded": "📂 Loaded:", "log_type": "→ Type:",
        "log_click_check": "→ Click «Check» to analyze",
        "log_results": "📊 RESULTS",
        "log_dark": "dark", "log_light": "light",
        "log_pass": "✅ PASS — in valid range",
        "log_fail": "❌ FAIL — click «Auto-Correct»",
        "log_fix_done": "✨ AUTO-CORRECTION DONE",
        "log_compress_done": "🗜 COMPRESSION DONE",
        "log_reset": "↺ Reset done", "log_saved": "💾 Saved:",
        "progress_check": "Checking...", "progress_fix": "Smart correction...",
        "progress_compress": "LAB roundtrip...", "progress_load": "Loading...",
        # ─── Stats ───
        "stat_min": "Min:", "stat_max": "Max:", "stat_avg": "Avg:",
        "stat_median": "Median:", "stat_p1": "1%:", "stat_p99": "99%:",
        # ─── Batch ───
        "batch_title": "BATCH PROCESSING",
        "batch_select_folder": "Select folder",
        "batch_select_files": "Select files",
        "batch_run": "Run processing",
        "batch_ready": "Ready to start",
        "batch_files_count": "files",
        "batch_done": "Done",
        "batch_folder": "Folder:",
        "batch_found": "Files found:",
        "batch_selected": "Files selected:",
        "batch_no_files": "⚠ No files selected",
        "batch_started": "⚡ Batch processing:",
        "batch_out": "Output:",
        "batch_processed": "Processed:",
        "batch_right_title": "CONTROLS",
        "batch_right_info": "INFO",
        "batch_threads_title": "THREADS",
        "batch_threads_label": "Parallel tasks (1–8)",
        "batch_right_hint": "Pick a folder or files → choose correction method on the left → hit «Run processing».\n\nResults are saved to _corrected folder next to sources.",
        # ─── Compress ───
        "compress_title": "ALBEDO COMPRESSION",
        "compress_single": "SINGLE COMPRESSION",
        "compress_batch": "BATCH COMPRESSION",
        "compress_run": "Compress",
        "compress_batch_run": "Compress folder",
        "compress_log_done": "🗜 Compression done:",
        "compress_batch_started": "⚡ Batch compression:",
        "compress_out": "Output:",
        "compress_right_title": "SETTINGS",
        "compress_right_info": "INFO",
        "compress_right_hint": "Single compression — file → result.\n\nBatch — pick folder or files, hit «Compress folder».\n\nResults go to _compressed folder next to sources.",
        "compress_single_btn": "Compress texture",
        "compress_batch_btn": "Compress folder",
        "compress_simple_hint": "Open file → LAB roundtrip → auto-save to _compressed next to source.",
        "compress_batch_hint": "Pick folder → LAB all files → _compressed next to sources.",
        "compress_done_title": "Compression done",
        "compress_done_single": "File saved:",
        "compress_done_batch": "Files processed:",
        "compress_done_size": "Size:",
        "compress_done_grew": "File got bigger",
        "compress_done_same": "Size unchanged",
        "compress_open_folder": "Open folder",
        "compress_ok": "OK",
        # ─── PBR ───
        "pbr_load": "Load Albedo", "pbr_gen": "Generate",
        "pbr_batch": "From folder", "pbr_save": "Save all",
        "pbr_preset_label": "Preset:",
        "pbr_bit_depth": "PNG bit depth:",
        "pbr_bit_8": "8-bit",
        "pbr_bit_16": "16-bit",
        "pbr_metallic": "Metallic map:",
        "pbr_metal_black": "Black", "pbr_metal_white": "White",
        "pbr_metal_custom": "Custom",
        "pbr_metal_auto": "By color",
        "pbr_metal_auto_hint": "Pick a pixel on Albedo, then Generate Metallic",
        "pbr_metal_pick": "Pick on Albedo",
        "pbr_metal_pick_dialog": "Click on the metal part of the texture",
        "pbr_metal_pick_saved": "✅ Color picked: RGB({r}, {g}, {b})",
        "pbr_metal_generate": "Generate mask",
        "pbr_metal_negative_pick": "Pick background",
        "pbr_metal_negative_hint": "Click on NON-metal (shadows, background) to exclude",
        "pbr_metal_negative_saved": "🚫 Negative color: RGB({r}, {g}, {b})",
        "pbr_metal_negative_clear": "Clear negative",
        "pbr_metal_negative_tolerance": "Negative tolerance",
        "pbr_metal_target_label": "Positive:",
        "pbr_metal_negative_label": "Negative:",
        "pbr_metal_generated": "🎨 Metallic mask generated",
        "pbr_metal_tolerance": "Tolerance (mask width)",
        "pbr_metal_softness": "Softness (edge blur)",
        "pbr_metal_no_pick": "⚠ Pick a color on Albedo first",
        "pbr_metal_pick_dialog_close": "OK",
        "pbr_metal_load": "Load metallic map",
        "pbr_roughness": "Roughness map:",
        "pbr_rough_procedural": "Procedural",
        "pbr_rough_custom": "Custom",
        "pbr_rough_load": "Load roughness map",
        "pbr_resize_title": "Size mismatch",
        "pbr_resize_text": "Map {w1}×{h1} does not match albedo {w2}×{h2}.\nResize automatically?",
        "pbr_resize_yes": "Resize",
        "pbr_resize_no": "Cancel",
        "pbr_sl_strength": "Normal strength", "pbr_sl_smooth": "Smoothing",
        "pbr_sl_threshold": "Threshold", "pbr_sl_high_pass": "High-pass",
        "pbr_sl_height_blur": "Height blur", "pbr_sl_ao_radius": "AO radius",
        "pbr_sl_ao_intensity": "AO intensity", "pbr_sl_rough_base": "Rough base",
        "pbr_sl_rough_var": "Rough variation",
        "pbr_sl_rough_detail": "Rough detail",
        "pbr_preview_hint": "Load Albedo and click «Generate»",
        "pbr_progress_gen": "Generating PBR maps...",
        "pbr_progress_batch": "PBR: processing folder...",
        "pbr_log_loaded": "📂 PBR: loaded",
        "pbr_log_gen_done": "✅ PBR: generated 7 maps",
        "pbr_log_saved": "💾 PBR saved to",
        "pbr_log_no_files": "⚠ PBR: no files in folder",
        "pbr_log_batch_done": "✅ PBR batch done:",
        "pbr_log_files": "files",
        "pbr_dialog_pick": "Select Albedo for PBR",
        "pbr_dialog_folder": "Select folder with textures",
        "pbr_viewer": "3D Preview",
        "pbr_viewer_progress": "Starting viewer...",
        "pbr_viewer_no_result": "⚠ Generate PBR maps first",
        "pbr_metal_auto_footer": "→ Click «Generate» at the top to refresh PBR",
        "pbr_metal_presets_title": "PRECISION PRESETS",
        "pbr_metal_preset_tight": "Tight",
        "pbr_metal_preset_medium": "Medium",
        "pbr_metal_preset_loose": "Loose",
        "pbr_metal_manual_title": "MANUAL TUNING",
        "pbr_edge_info": "Edge is auto-generated from Height.\n\nNo settings — parameters are fixed.",
        "pbr_orm_info": "ORM is a packed map.\n\nR = AO, G = Roughness, B = Metallic.\n\nTune components in AO, Rough and Metal tabs.",
        # ─── Export ───
        "export_source": "SOURCE",
        "export_target": "ENGINE",
        "export_normal": "NORMAL MAP FORMAT",
        "export_detail": "DETAIL MASK (HDRP)",
        "export_bit": "PNG BIT DEPTH",
        "export_layout": "CHANNEL LAYOUT",
        "export_load_pbr": "From current PBR",
        "export_load_folder": "Load from folder",
        "export_pack": "Pack",
        "export_save": "Save all",
        "export_load_detail": "Load custom",
        "export_hint": "Pick a source: PBR or folder",
        "export_source_none": "Source: —",
        "export_engine_hdrp": "Unity HDRP — Mask Map",
        "export_engine_urp": "Unity URP — MetallicSmoothness",
        "export_engine_unreal": "Unreal — ORM",
        "export_engine_godot": "Godot — ORM",
        "export_normal_gl": "OpenGL (Y+)",
        "export_normal_dx": "DirectX (Y-)",
        "export_detail_white": "White (1.0)",
        "export_detail_edge": "Edge map",
        "export_detail_custom": "Custom (load)",
        "export_progress_pack": "📦 Packing...",
        "export_progress_save": "💾 Saving...",
        "export_log_source_pbr": "📦 Export: source — current PBR",
        "export_log_source_folder": "📦 Export: loaded from folder",
        "export_log_packed": "📦 Packed",
        "export_log_saved": "💾 Export saved:",
        "export_log_no_pbr": "⚠ PBR maps not generated",
        "export_log_no_normal": "⚠ No *_normal.png in folder",
        "export_log_no_source": "⚠ Pick a source first",
        "export_log_no_packed": "⚠ Nothing to save — pack first",
        "export_log_detail_loaded": "📦 Detail Mask loaded:",
        # ─── Realism ───
        "realism_grain": "Grain",
        "realism_highpass": "Detail",
        "realism_variation": "Variation",
        "realism_preset_soft": "Soft",
        "realism_preset_medium": "Medium",
        "realism_preset_hard": "Hard",
        "realism_apply": "Apply",
        "realism_preset_log": "Preset",
        "realism_preview_hint": "Load a texture and tweak the filter",
        "realism_progress": "Applying realism filter...",
        "realism_done": "🎞 Filter applied",
        # ─── Dialogs ───
        "dialog_save_title": "Save result",
        "dialog_pick_title": "Select texture",
        "err": "Error",
        "fb_dialog_title": "AI result failed validation",
        "fb_dialog_text": "AI fixed the color cast, but brightness is out of range:",
        "fb_dialog_dark": "Dark:",
        "fb_dialog_light": "Light:",
        "fb_dialog_question": "Apply CLAHE fallback?",
        "fb_dialog_keep_ai": "Keep AI",
        "fb_dialog_apply": "Apply fallback",
        "fb_dialog_kept": "   → Kept AI result as is",
        "fb_dialog_applied": "   ✨ Fallback applied on top of AI result",
        "fb_dialog_progress": "Fallback correction...",
        "fb_dialog_err": "Fallback error:",
        # ─── Info ───
        "info_tab_help": "Help",
        "info_tab_manual": "Manual",
        "info_tab_about": "About",
        "info_tab_support": "Support",
        "support_title": "Support development",
        "support_text": ("Albedolizer is a free tool.\n"
                          "If it saves your time — drop some smokes for uncle.\n"
                          "Thank you!"),
        "support_copied": "✅ Copied!",
        "about_version": "Version", "about_build": "Build",
        "about_author": "Author", "about_license": "License",
        "about_desc": ("Albedolizer — a utility to check and optimize\n"
                        "Albedo maps of PBR textures. LAB + Autolevels AI."),
        "help_text": (
            "Albedolizer — user guide\n\n"
            "MODES\n\n"
            "SIMPLE — for quick work\n"
            "One button «Process texture»:\n"
            "1. Opens file\n"
            "2. AI color correction\n"
            "3. Boosts saturation by 15%\n"
            "Result in 30 seconds.\n\n"
            "ADVANCED — full control\n"
            "Unlocks all tools:\n"
            "- Correction mode (AI / Math)\n"
            "- Soap removal\n"
            "- Saturation\n"
            "- Tiling checker\n"
            "- Batch processing\n"
            "- Compression\n\n"
            "Switch modes via header button.\n\n"
            "SINGLE (Advanced)\n"
            "1. Pick texture type\n"
            "2. «Open» → «Check»\n"
            "3. If FAIL — «Auto-Correct»\n"
            "4. «Save»\n\n"
            "PBR\n"
            "1. «Load Albedo»\n"
            "2. Pick preset\n"
            "3. «Generate» → «Save all»\n\n"
            "COMPRESS\n"
            "Single or batch Albedo compression.\n\n"
            "BATCH\n"
            "AI-correction of a whole folder."
        ),
    },
    "zh": {
        "subtitle": "PBR Albedo 检查与优化",
        # ─── Табы (rail) ───
        "tab_single": "单张图片", "tab_pbr": "PBR",
        "tab_compress": "压缩", "tab_batch": "批量处理",
        "tab_realism": "真实感", "tab_export": "导出引擎",
        # ─── Кнопки тулбара ───
        "load": "加载", "check": "检查",
        "fix": "自动校正", "compress": "压缩",
        "save": "保存", "reset": "重置",
        "preview_toggle_orig": "原图",
        "preview_toggle_result": "结果",
        # ─── Заголовки панелей ───
        "stats_title": "统计", "profile_title": "纹理类型",
        "correction_mode_title": "校正模式",
        "soap_fix_title": "去除模糊",
        "sat_title": "饱和度",
        "seamless_title": "无缝",
        "pbr_params": "PBR 参数",
        "export_title": "引擎导出",
        "realism_params": "参数",
        "realism_presets": "预设",
        # ─── Auto-detect ───
        "auto_detect_btn": "自动检测材质",
        "auto_detect_progress": "🤖 正在检测材质...",
        "auto_detect_loading": "   🔄 加载 CLIP...",
        "auto_detect_result": "🤖 材质自动检测",
        "auto_detect_winner": "   🏆 结果:",
        "auto_detect_top5": "   📊 前 5:",
        "auto_detect_changed": "   → 预设已更改:",
        "auto_detect_same": "   → 预设未更改",
        "auto_detect_fail": "   ⚠ 无法检测材质",
        "auto_detect_no_tex": "   ⚠ 请先加载纹理",
        "auto_detect_no_clip": "   ⚠ 无法加载 CLIP 模型",
        # ─── Correction method ───
        "correction_ai_autolevels": "Autolevels",
        "correction_ai_lutwithbgrid": "LUTwithBGrid",
        "correction_math": "数学",
        # ─── Soap / tiling / seamless ───
        "soap_fix_label": "细节强度",
        "soap_fix_button": "去除模糊",
        "tiling_btn": "平铺 3×3",
        "tiling_btn_off": "普通视图",
        "seamless_btn": "无缝",
        "seamless_done": "🔲 纹理已无缝",
        "seamless_hipass": "高通滤波 (均匀亮度)",
        "seamless_progress": "正在制作无缝...",
        "seamless_overlap": "混合区域 (%)",
        "seamless_softness": "柔和度",
        "seamless_scatter": "波动",
        "seamless_apply": "制作无缝",
        "seamless_auto_tiling": "→ 自动 3×3 预览已启用",
        "soap_fix_done": "🔧 细节已增强",
        "soap_fix_progress": "正在去除模糊...",
        # ─── Saturation ───
        "sat_label": "倍数",
        "sat_button": "提升饱和度",
        "sat_done": "🎨 饱和度已提升",
        "sat_progress": "正在提升饱和度...",
        # ─── Прочее UI ───
        "all_types": "所有类型", "log_title": "日志",
        "info_btn": "信息", "lang_btn": "RU",
        "mode_btn_simple": "简单",
        "mode_btn_advanced": "高级",
        "preview_hint": "加载 Albedo 纹理以开始",
        # ─── Welcome dialog ───
        "welcome_title": "欢迎使用 Albedolizer",
        "welcome_text": (
            "从 Albedo 纹理检查、校正并生成 PBR 贴图。\n\n"
            "两种模式:\n"
            "• 简单 — 一键「处理纹理」: 打开 → AI 校正 → 保存。适合快速工作。\n"
            "• 高级 — 完全控制: 预设选择、校正方法、统计、平铺、无缝、手动 PBR 调整。\n"
            "随时通过标题栏按钮切换。\n\n"
            "快速开始 (简单):\n"
            "1. 点击「处理纹理」并选择文件\n"
            "2. 几秒后显示结果\n"
            "3. 「保存」\n\n"
            "PBR 选项卡 — 从 Albedo 生成 7 张 PBR 贴图。\n"
            "引擎 — 为 Unity / Unreal / Godot 打包 PBR 贴图。"
        ),
        "welcome_ok": "明白了，开始吧",
        "welcome_manual": "打开手册",
        "welcome_switch_simple": "启用高级模式",
        # ─── Логи (эмодзи оставлены) ───
        "welcome_1": "👋 欢迎使用 Albedolizer v1.7.6-beta",
        "welcome_2": "→ 点击「加载」开始",
        "log_loaded": "📂 已加载:", "log_type": "→ 类型:",
        "log_click_check": "→ 点击「检查」进行分析",
        "log_results": "📊 结果",
        "log_dark": "暗", "log_light": "亮",
        "log_pass": "✅ 通过 — 在有效范围内",
        "log_fail": "❌ 失败 — 点击「自动校正」",
        "log_fix_done": "✨ 自动校正完成",
        "log_compress_done": "🗜 压缩完成",
        "log_reset": "↺ 重置完成", "log_saved": "💾 已保存:",
        "progress_check": "检查中...", "progress_fix": "智能校正...",
        "progress_compress": "LAB 往返...", "progress_load": "加载中...",
        # ─── Stats ───
        "stat_min": "最小:", "stat_max": "最大:", "stat_avg": "平均:",
        "stat_median": "中位数:", "stat_p1": "1%:", "stat_p99": "99%:",
        # ─── Batch ───
        "batch_title": "批量处理",
        "batch_select_folder": "选择文件夹",
        "batch_select_files": "选择文件",
        "batch_run": "开始处理",
        "batch_ready": "准备就绪",
        "batch_files_count": "个文件",
        "batch_done": "完成",
        "batch_folder": "文件夹:",
        "batch_found": "找到文件:",
        "batch_selected": "已选择文件:",
        "batch_no_files": "⚠ 未选择文件",
        "batch_started": "⚡ 批量处理:",
        "batch_out": "输出:",
        "batch_processed": "已处理:",
        "batch_right_title": "控制",
        "batch_right_info": "信息",
        "batch_threads_title": "线程",
        "batch_threads_label": "并行任务 (1–8)",
        "batch_right_hint": "选择文件夹或文件 → 在左侧选择校正方法 → 点击「开始处理」。\n\n结果保存在源文件旁的 _corrected 文件夹中。",
        # ─── Compress ───
        "compress_title": "Albedo 压缩",
        "compress_single": "单张压缩",
        "compress_batch": "批量压缩",
        "compress_run": "压缩",
        "compress_batch_run": "压缩文件夹",
        "compress_log_done": "🗜 压缩完成:",
        "compress_batch_started": "⚡ 批量压缩:",
        "compress_out": "输出:",
        "compress_right_title": "设置",
        "compress_right_info": "信息",
        "compress_right_hint": "单张压缩 — 文件 → 结果。\n\n批量 — 选择文件夹或文件，点击「压缩文件夹」。\n\n结果保存在源文件旁的 _compressed 文件夹中。",
        "compress_single_btn": "压缩纹理",
        "compress_batch_btn": "压缩文件夹",
        "compress_simple_hint": "打开文件 → LAB 往返 → 自动保存到源文件旁的 _compressed。",
        "compress_batch_hint": "选择文件夹 → LAB 所有文件 → 源文件旁的 _compressed。",
        "compress_done_title": "压缩完成",
        "compress_done_single": "文件已保存:",
        "compress_done_batch": "已处理文件:",
        "compress_done_size": "大小:",
        "compress_done_grew": "文件变大",
        "compress_done_same": "大小未变",
        "compress_open_folder": "打开文件夹",
        "compress_ok": "OK",
        # ─── PBR ───
        "pbr_load": "加载 Albedo", "pbr_gen": "生成",
        "pbr_batch": "从文件夹", "pbr_save": "保存全部",
        "pbr_preset_label": "预设:",
        "pbr_bit_depth": "PNG 位深度:",
        "pbr_bit_8": "8-bit",
        "pbr_bit_16": "16-bit",
        "pbr_metallic": "金属度贴图:",
        "pbr_metal_black": "黑色", "pbr_metal_white": "白色",
        "pbr_metal_custom": "自定义",
        "pbr_metal_auto": "按颜色",
        "pbr_metal_auto_hint": "在 Albedo 上拾取金属像素，然后生成金属度",
        "pbr_metal_pick": "在 Albedo 上拾取",
        "pbr_metal_pick_dialog": "点击纹理的金属部分",
        "pbr_metal_pick_saved": "✅ 已选颜色: RGB({r}, {g}, {b})",
        "pbr_metal_generate": "生成遮罩",
        "pbr_metal_negative_pick": "拾取背景",
        "pbr_metal_negative_hint": "点击非金属部分 (阴影、背景) 以排除",
        "pbr_metal_negative_saved": "🚫 排除颜色: RGB({r}, {g}, {b})",
        "pbr_metal_negative_clear": "清除排除",
        "pbr_metal_negative_tolerance": "排除容差",
        "pbr_metal_target_label": "目标:",
        "pbr_metal_negative_label": "排除:",
        "pbr_metal_generated": "🎨 金属度遮罩已生成",
        "pbr_metal_tolerance": "容差 (遮罩宽度)",
        "pbr_metal_softness": "柔化 (边缘模糊)",
        "pbr_metal_no_pick": "⚠ 请先在 Albedo 上拾取颜色",
        "pbr_metal_pick_dialog_close": "OK",
        "pbr_metal_load": "加载金属度贴图",
        "pbr_roughness": "粗糙度贴图:",
        "pbr_rough_procedural": "程序化",
        "pbr_rough_custom": "自定义",
        "pbr_rough_load": "加载粗糙度贴图",
        "pbr_resize_title": "大小不匹配",
        "pbr_resize_text": "贴图 {w1}×{h1} 与 albedo {w2}×{h2} 不匹配。\n是否自动调整大小？",
        "pbr_resize_yes": "调整大小",
        "pbr_resize_no": "取消",
        "pbr_sl_strength": "法线强度", "pbr_sl_smooth": "平滑",
        "pbr_sl_threshold": "阈值 (背景)", "pbr_sl_high_pass": "高通滤波",
        "pbr_sl_height_blur": "高度模糊", "pbr_sl_ao_radius": "AO 半径",
        "pbr_sl_ao_intensity": "AO 强度", "pbr_sl_rough_base": "粗糙度基础",
        "pbr_sl_rough_var": "粗糙度变化",
        "pbr_sl_rough_detail": "粗糙度细节",
        "pbr_preview_hint": "加载 Albedo 并点击「生成」",
        "pbr_progress_gen": "正在生成 PBR 贴图...",
        "pbr_progress_batch": "PBR: 正在处理文件夹...",
        "pbr_log_loaded": "📂 PBR: 已加载",
        "pbr_log_gen_done": "✅ PBR: 已生成 7 张贴图",
        "pbr_log_saved": "💾 PBR 已保存到",
        "pbr_log_no_files": "⚠ PBR: 文件夹中没有文件",
        "pbr_log_batch_done": "✅ PBR 批量处理完成:",
        "pbr_log_files": "个文件",
        "pbr_dialog_pick": "选择用于 PBR 的 Albedo",
        "pbr_dialog_folder": "选择包含纹理的文件夹",
        "pbr_viewer": "3D 预览",
        "pbr_viewer_progress": "正在启动查看器...",
        "pbr_viewer_no_result": "⚠ 请先生成 PBR 贴图",
        "pbr_metal_auto_footer": "→ 点击顶部的「生成」以刷新 PBR",
        "pbr_metal_presets_title": "精度预设",
        "pbr_metal_preset_tight": "紧",
        "pbr_metal_preset_medium": "中",
        "pbr_metal_preset_loose": "松",
        "pbr_metal_manual_title": "手动调整",
        "pbr_edge_info": "边缘贴图从高度贴图自动生成。\n\n无设置 — 参数固定。",
        "pbr_orm_info": "ORM 是打包贴图。\n\nR = AO, G = 粗糙度, B = 金属度。\n\n在 AO、粗糙度和金属度选项卡中调整组件。",
        # ─── Export ───
        "export_source": "来源",
        "export_target": "引擎",
        "export_normal": "法线贴图格式",
        "export_detail": "细节遮罩 (HDRP)",
        "export_bit": "PNG 位深度",
        "export_layout": "通道布局",
        "export_load_pbr": "从当前 PBR",
        "export_load_folder": "从文件夹加载",
        "export_pack": "打包",
        "export_save": "保存全部",
        "export_load_detail": "加载自定义",
        "export_hint": "选择来源: PBR 或文件夹",
        "export_source_none": "来源: —",
        "export_engine_hdrp": "Unity HDRP — Mask Map",
        "export_engine_urp": "Unity URP — MetallicSmoothness",
        "export_engine_unreal": "Unreal — ORM",
        "export_engine_godot": "Godot — ORM",
        "export_normal_gl": "OpenGL (Y+)",
        "export_normal_dx": "DirectX (Y-)",
        "export_detail_white": "白色 (1.0)",
        "export_detail_edge": "边缘贴图",
        "export_detail_custom": "自定义 (加载)",
        "export_progress_pack": "📦 打包中...",
        "export_progress_save": "💾 保存中...",
        "export_log_source_pbr": "📦 导出: 来源 — 当前 PBR",
        "export_log_source_folder": "📦 导出: 从文件夹加载",
        "export_log_packed": "📦 已打包",
        "export_log_saved": "💾 导出已保存:",
        "export_log_no_pbr": "⚠ PBR 贴图未生成",
        "export_log_no_normal": "⚠ 文件夹中没有 *_normal.png",
        "export_log_no_source": "⚠ 请先选择来源",
        "export_log_no_packed": "⚠ 没有可保存的内容 — 请先打包",
        "export_log_detail_loaded": "📦 细节遮罩已加载:",
        # ─── Realism ───
        "realism_grain": "颗粒",
        "realism_highpass": "细节",
        "realism_variation": "变化",
        "realism_preset_soft": "柔和",
        "realism_preset_medium": "中等",
        "realism_preset_hard": "强烈",
        "realism_apply": "应用",
        "realism_preset_log": "预设",
        "realism_preview_hint": "加载纹理并调整滤镜",
        "realism_progress": "正在应用真实感滤镜...",
        "realism_done": "🎞 滤镜已应用",
        # ─── Dialogs ───
        "dialog_save_title": "保存结果",
        "dialog_pick_title": "选择纹理",
        "err": "错误",
        "fb_dialog_title": "AI 结果未通过验证",
        "fb_dialog_text": "AI 修复了色偏，但亮度超出范围:",
        "fb_dialog_dark": "暗:",
        "fb_dialog_light": "亮:",
        "fb_dialog_question": "应用 CLAHE 回退？",
        "fb_dialog_keep_ai": "保留 AI",
        "fb_dialog_apply": "应用回退",
        "fb_dialog_kept": "   → 保留 AI 结果",
        "fb_dialog_applied": "   ✨ 回退已应用于 AI 结果",
        "fb_dialog_progress": "回退校正...",
        "fb_dialog_err": "回退错误:",
        # ─── Info ───
        "info_tab_help": "帮助",
        "info_tab_manual": "手册",
        "info_tab_about": "关于",
        "info_tab_support": "支持",
        "support_title": "支持开发",
        "support_text": ("Albedolizer 是一个免费工具。\n"
                          "如果它节省了你的时间 — 可以请作者抽根烟。\n"
                          "谢谢！"),
        "support_copied": "✅ 已复制！",
        "about_version": "版本", "about_build": "构建",
        "about_author": "作者", "about_license": "许可证",
        "about_desc": ("Albedolizer — 用于检查和优化 PBR 纹理\n"
                        "Albedo 贴图的工具。LAB + Autolevels AI。"),
        "help_text": (
            "Albedolizer — 用户指南\n\n"
            "模式\n\n"
            "简单 — 快速工作\n"
            "一键「处理纹理」:\n"
            "1. 打开文件\n"
            "2. AI 颜色校正\n"
            "3. 提升饱和度 15%\n"
            "30 秒内出结果。\n\n"
            "高级 — 完全控制\n"
            "解锁所有工具:\n"
            "- 校正模式 (AI / 数学)\n"
            "- 去除模糊\n"
            "- 饱和度\n"
            "- 平铺检查\n"
            "- 批量处理\n"
            "- 压缩\n\n"
            "通过标题栏按钮切换模式。\n\n"
            "单张 (高级)\n"
            "1. 选择纹理类型\n"
            "2. 「加载」→「检查」\n"
            "3. 如果失败 — 「自动校正」\n"
            "4. 「保存」\n\n"
            "PBR\n"
            "1. 「加载 Albedo」\n"
            "2. 选择预设\n"
            "3. 「生成」→「保存全部」\n\n"
            "压缩\n"
            "单张或批量 Albedo 压缩。\n\n"
            "批量\n"
            "对整个文件夹进行 AI 校正。"
        ),
    },
}


def get_font_path():
    """Возвращает путь к кастомному шрифту, если он есть, иначе None."""
    import sys
    font_name = "NotoSansSC-VariableFont_wght.ttf"
    paths_to_check = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            paths_to_check.append(os.path.join(meipass, font_name))
        paths_to_check.append(
            os.path.join(os.path.dirname(sys.executable), font_name))
    paths_to_check.extend([
        os.path.join(os.getcwd(), font_name),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), font_name),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", font_name),
    ])
    for p in paths_to_check:
        if os.path.exists(p):
            return p
    return None