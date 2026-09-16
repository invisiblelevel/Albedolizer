"""
translations.py — все переводы интерфейса Albedolizer (RU + EN).
Только данные, никакой логики.
"""

T = {
    "ru": {
        "subtitle": "PBR Albedo Checker & Optimizer",
        "tab_single": "🖼 Одиночная", "tab_pbr": "🎨 PBR",
        "tab_compress": "🗜 Сжатие", "tab_batch": "🗂 Пакетная",
        "load": "📂 Открыть", "check": "🔍 Проверить",
        "fix": "✨ Автокоррекция", "compress": "🗜 Сжать",
        "save": "💾 Сохранить", "reset": "↺ Сброс",
        "stats_title": "СТАТИСТИКА", "profile_title": "ТИП ТЕКСТУРЫ",
        "correction_mode_title": "МЕТОД КОРРЕКЦИИ",
        "auto_detect_btn": "🤖 Автоопределить материал",
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
        "correction_ai_autolevels": "✨ Autolevels",
        "correction_ai_lutwithbgrid": "🎨 LUTwithBGrid",
        "correction_math": "∑ Math",
        "soap_fix_title": "🔧 УБРАТЬ МЫЛО",
        "soap_fix_label": "Сила детализации",
        "soap_fix_button": "🔧 Убрать мыло",
        "tiling_btn": "🔁 Тайлинг 3×3",
        "tiling_btn_off": "🔁 Обычный вид",
        "soap_fix_done": "🔧 Детализация применена",
        "soap_fix_progress": "Убираем мыло...",
        "sat_title": "🎨 НАСЫЩЕННОСТЬ",
        "sat_label": "Множитель",
        "sat_button": "🎨 Поднять насыщенность",
        "sat_done": "🎨 Насыщенность повышена",
        "sat_progress": "Поднимаем насыщенность...",
        "all_types": "Все типы", "log_title": "ЛОГ",
        "info_btn": "ℹ Инфо", "lang_btn": "🌐 EN",
        "mode_btn_simple": "⚙ Simple",
        "mode_btn_advanced": "⚙ Advanced",
        "preview_hint": "🖼  Загрузи Albedo-текстуру, чтобы начать",
        "welcome_1": "👋 Добро пожаловать в Albedolizer v1.6.0-beta",
        "welcome_2": "→ Нажми «📂 Открыть» для начала",
        "log_loaded": "📂 Загружено:", "log_type": "→ Тип:",
        "log_click_check": "→ Нажми «Проверить» для анализа",
        "log_results": "📊 РЕЗУЛЬТАТЫ",
        "log_dark": "тёмные", "log_light": "светлые",
        "log_pass": "✅ PASS — в допустимом диапазоне",
        "log_fail": "❌ FAIL — жми «✨ Автокоррекция»",
        "log_fix_done": "✨ АВТОКОРРЕКЦИЯ ВЫПОЛНЕНА",
        "log_compress_done": "🗜 СЖАТИЕ ВЫПОЛНЕНО",
        "log_reset": "↺ Сброс выполнен", "log_saved": "💾 Сохранено:",
        "progress_check": "Проверка...", "progress_fix": "Умная коррекция...",
        "progress_compress": "LAB-прогон...", "progress_load": "Загрузка...",
        "stat_min": "Мин:", "stat_max": "Макс:", "stat_avg": "Сред:",
        "stat_median": "Медиана:", "stat_p1": "1%:", "stat_p99": "99%:",
        "batch_title": "ПАКЕТНАЯ ОБРАБОТКА",
        "batch_select_folder": "📁 Выбрать папку",
        "batch_select_files": "📄 Выбрать файлы",
        "batch_run": "▶ Запустить обработку",
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
        "compress_title": "СЖАТИЕ ALBEDO",
        "compress_single": "ОДИНОЧНОЕ СЖАТИЕ",
        "compress_batch": "ПАКЕТНОЕ СЖАТИЕ",
        "compress_run": "🗜 Сжать",
        "compress_batch_run": "▶ Сжать папку",
        "compress_log_done": "🗜 Сжатие выполнено:",
        "compress_batch_started": "⚡ Пакетное сжатие:",
        "compress_out": "Результат в:",
        "pbr_load": "📂 Загрузить Albedo", "pbr_gen": "🎨 Сгенерировать",
        "pbr_batch": "🗂 Из папки", "pbr_save": "💾 Сохранить все",
        "pbr_params": "ПАРАМЕТРЫ PBR",
        "pbr_preset_label": "🎯 Пресет:",
        "pbr_bit_depth": "Битность PNG:",
        "pbr_bit_8": "8-bit",
        "pbr_bit_16": "16-bit",
        "pbr_metallic": "Metallic карта:",
        "pbr_metal_black": "Чёрная", "pbr_metal_white": "Белая",
        "pbr_sl_strength": "Сила нормалей", "pbr_sl_smooth": "Сглаживание",
        "pbr_sl_threshold": "Порог (фон)", "pbr_sl_high_pass": "High-pass",
        "pbr_sl_height_blur": "Blur Height", "pbr_sl_ao_radius": "AO радиус",
        "pbr_sl_ao_intensity": "AO сила", "pbr_sl_rough_base": "Rough база",
        "pbr_sl_rough_var": "Rough вариация",
        "pbr_preview_hint": "🖼  Загрузи Albedo и нажми «🎨 Сгенерировать»",
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
        "pbr_viewer": "👁 3D Preview",
        "pbr_viewer_progress": "Запуск вьюера...",
        "pbr_viewer_no_result": "⚠ Сначала сгенерируй PBR-карты",
        "dialog_save_title": "Сохранить результат",
        "dialog_pick_title": "Выбери текстуру",
        "err": "Ошибка",
        "fb_dialog_title": "Результат AI не прошёл проверку",
        "fb_dialog_text": "AI убрал цветовой сдвиг, но яркость вне порога:",
        "fb_dialog_dark": "Тёмные:",
        "fb_dialog_light": "Светлые:",
        "fb_dialog_question": "Применить CLAHE fallback?",
        "fb_dialog_keep_ai": "✅ Оставить AI",
        "fb_dialog_apply": "⚡ Применить fallback",
        "fb_dialog_kept": "   → Оставлен результат AI как есть",
        "fb_dialog_applied": "   ✨ Fallback применён к результату AI",
        "fb_dialog_progress": "Fallback коррекция...",
        "fb_dialog_err": "Fallback ошибка:",
        "info_tab_help": "📖 Справка",
        "info_tab_manual": "Мануал",
        "info_tab_about": "ℹ О программе",
        "info_tab_support": "💛 Поддержать",
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
            "🎛 РЕЖИМЫ\n\n"
            "⚙ SIMPLE — для быстрой работы\n"
            "Одна кнопка «🚀 Обработать текстуру»:\n"
            "1. Открывает файл\n"
            "2. AI-коррекция цвета\n"
            "3. Поднимает насыщенность на 15%\n"
            "Результат за 30 секунд.\n\n"
            "🔧 ADVANCED — для полного контроля\n"
            "Открывает все инструменты:\n"
            "- Режим коррекции (AI / Math)\n"
            "- Убирание мыла\n"
            "- Насыщенность\n"
            "- Tiling-checker\n"
            "- Пакетная обработка\n"
            "- Сжатие\n\n"
            "Переключайся между режимами кнопкой в хедере.\n\n"
            "🖼 ОДИНОЧНАЯ (Advanced)\n"
            "1. Выбери тип текстуры\n"
            "2. «📂 Открыть» → «🔍 Проверить»\n"
            "3. Если FAIL — «✨ Автокоррекция»\n"
            "4. «💾 Сохранить»\n\n"
            "🎨 PBR\n"
            "1. «📂 Загрузить Albedo»\n"
            "2. Выбери пресет\n"
            "3. «🎨 Сгенерировать» → «💾 Сохранить все»\n\n"
            "🗜 СЖАТИЕ\n"
            "Одиночное или пакетное сжатие Albedo.\n\n"
            "🗂 ПАКЕТНАЯ\n"
            "AI-коррекция целой папки."
        ),
    },
    "en": {
        "subtitle": "PBR Albedo Checker & Optimizer",
        "tab_single": "🖼 Single", "tab_pbr": "🎨 PBR",
        "tab_compress": "🗜 Compress", "tab_batch": "🗂 Batch",
        "load": "📂 Open", "check": "🔍 Check",
        "fix": "✨ Auto-Correct", "compress": "🗜 Compress",
        "save": "💾 Save", "reset": "↺ Reset",
        "stats_title": "STATISTICS", "profile_title": "TEXTURE TYPE",
        "correction_mode_title": "CORRECTION METHOD",
        "auto_detect_btn": "🤖 Auto-detect material",
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
        "correction_ai_autolevels": "✨ Autolevels",
        "correction_ai_lutwithbgrid": "🎨 LUTwithBGrid",
        "correction_math": "∑ Math",
        "soap_fix_title": "🔧 REMOVE SOAP",
        "soap_fix_label": "Detail strength",
        "soap_fix_button": "🔧 Remove soap",
        "tiling_btn": "🔁 Tiling 3×3",
        "tiling_btn_off": "🔁 Normal view",
        "soap_fix_done": "🔧 Detail enhanced",
        "soap_fix_progress": "Removing soap...",
        "sat_title": "🎨 SATURATION",
        "sat_label": "Multiplier",
        "sat_button": "🎨 Boost saturation",
        "sat_done": "🎨 Saturation boosted",
        "sat_progress": "Boosting saturation...",
        "all_types": "All types", "log_title": "LOG",
        "info_btn": "ℹ Info", "lang_btn": "🌐 RU",
        "mode_btn_simple": "⚙ Simple",
        "mode_btn_advanced": "⚙ Advanced",
        "preview_hint": "🖼  Load an Albedo texture to start",
        "welcome_1": "👋 Welcome to Albedolizer v1.6.0-beta",
        "welcome_2": "→ Click «📂 Open» to start",
        "log_loaded": "📂 Loaded:", "log_type": "→ Type:",
        "log_click_check": "→ Click «Check» to analyze",
        "log_results": "📊 RESULTS",
        "log_dark": "dark", "log_light": "light",
        "log_pass": "✅ PASS — in valid range",
        "log_fail": "❌ FAIL — click «✨ Auto-Correct»",
        "log_fix_done": "✨ AUTO-CORRECTION DONE",
        "log_compress_done": "🗜 COMPRESSION DONE",
        "log_reset": "↺ Reset done", "log_saved": "💾 Saved:",
        "progress_check": "Checking...", "progress_fix": "Smart correction...",
        "progress_compress": "LAB roundtrip...", "progress_load": "Loading...",
        "stat_min": "Min:", "stat_max": "Max:", "stat_avg": "Avg:",
        "stat_median": "Median:", "stat_p1": "1%:", "stat_p99": "99%:",
        "batch_title": "BATCH PROCESSING",
        "batch_select_folder": "📁 Select folder",
        "batch_select_files": "📄 Select files",
        "batch_run": "▶ Run processing",
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
        "compress_title": "ALBEDO COMPRESSION",
        "compress_single": "SINGLE COMPRESSION",
        "compress_batch": "BATCH COMPRESSION",
        "compress_run": "🗜 Compress",
        "compress_batch_run": "▶ Compress folder",
        "compress_log_done": "🗜 Compression done:",
        "compress_batch_started": "⚡ Batch compression:",
        "compress_out": "Output:",
        "pbr_load": "📂 Load Albedo", "pbr_gen": "🎨 Generate",
        "pbr_batch": "🗂 From folder", "pbr_save": "💾 Save all",
        "pbr_params": "PBR PARAMETERS",
        "pbr_preset_label": "🎯 Preset:",
        "pbr_bit_depth": "PNG bit depth:",
        "pbr_bit_8": "8-bit",
        "pbr_bit_16": "16-bit",
        "pbr_metallic": "Metallic map:",
        "pbr_metal_black": "Black", "pbr_metal_white": "White",
        "pbr_sl_strength": "Normal strength", "pbr_sl_smooth": "Smoothing",
        "pbr_sl_threshold": "Threshold", "pbr_sl_high_pass": "High-pass",
        "pbr_sl_height_blur": "Height blur", "pbr_sl_ao_radius": "AO radius",
        "pbr_sl_ao_intensity": "AO intensity", "pbr_sl_rough_base": "Rough base",
        "pbr_sl_rough_var": "Rough variation",
        "pbr_preview_hint": "🖼  Load Albedo and click «🎨 Generate»",
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
        "pbr_viewer": "👁 3D Preview",
        "pbr_viewer_progress": "Starting viewer...",
        "pbr_viewer_no_result": "⚠ Generate PBR maps first",
        "dialog_save_title": "Save result",
        "dialog_pick_title": "Select texture",
        "err": "Error",
        "fb_dialog_title": "AI result failed validation",
        "fb_dialog_text": "AI fixed the color cast, but brightness is out of range:",
        "fb_dialog_dark": "Dark:",
        "fb_dialog_light": "Light:",
        "fb_dialog_question": "Apply CLAHE fallback?",
        "fb_dialog_keep_ai": "✅ Keep AI",
        "fb_dialog_apply": "⚡ Apply fallback",
        "fb_dialog_kept": "   → Kept AI result as is",
        "fb_dialog_applied": "   ✨ Fallback applied on top of AI result",
        "fb_dialog_progress": "Fallback correction...",
        "fb_dialog_err": "Fallback error:",
        "info_tab_help": "📖 Help",
        "info_tab_manual": "Manual",
        "info_tab_about": "ℹ About",
        "info_tab_support": "💛 Support",
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
            "🎛 MODES\n\n"
            "⚙ SIMPLE — for quick work\n"
            "One button «🚀 Process texture»:\n"
            "1. Opens file\n"
            "2. AI color correction\n"
            "3. Boosts saturation by 15%\n"
            "Result in 30 seconds.\n\n"
            "🔧 ADVANCED — full control\n"
            "Unlocks all tools:\n"
            "- Correction mode (AI / Math)\n"
            "- Soap removal\n"
            "- Saturation\n"
            "- Tiling checker\n"
            "- Batch processing\n"
            "- Compression\n\n"
            "Switch modes via header button.\n\n"
            "🖼 SINGLE (Advanced)\n"
            "1. Pick texture type\n"
            "2. «📂 Open» → «🔍 Check»\n"
            "3. If FAIL — «✨ Auto-Correct»\n"
            "4. «💾 Save»\n\n"
            "🎨 PBR\n"
            "1. «📂 Load Albedo»\n"
            "2. Pick preset\n"
            "3. «🎨 Generate» → «💾 Save all»\n\n"
            "🗜 COMPRESS\n"
            "Single or batch Albedo compression.\n\n"
            "🗂 BATCH\n"
            "AI-correction of a whole folder."
        ),
    },
}