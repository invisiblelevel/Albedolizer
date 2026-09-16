"""
config.py — все константы, словари и настройки Albedolizer.
Только данные, никакой логики.
"""

# ═══════════════════════════════════════════════════════════
#  МЕТА
# ═══════════════════════════════════════════════════════════
APP_TITLE = "Albedolizer v1.5.0-beta"
APP_VERSION = "1.5.0-beta"
APP_BUILD = "2026-09-16"
APP_AUTHOR = "INV.LVL"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 820
WINDOW_OPACITY = 0.97

# ═══════════════════════════════════════════════════════════
#  ПУТИ К ФАЙЛАМ
# ═══════════════════════════════════════════════════════════
AUTOLEVELS_EXE_NAME = "autolevels.exe"
AUTOLEVELS_MODEL_NAME = "free_xcittiny_wa14.onnx"
ICON_NAME = "icon.ico"
LUTWITHBGRID_MODEL_NAME = "lutwithbgrid_fivek.onnx"
DEFAULT_AI_MODEL = "autolevels"


# ═══════════════════════════════════════════════════════════
#  AI МОДЕЛИ
# ═══════════════════════════════════════════════════════════
AI_MODELS = {
    "autolevels": {
        "ru": "Autolevels",
        "en": "Autolevels",
        "type": "exe",
    },
    "lutwithbgrid": {
        "ru": "LUTwithBGrid",
        "en": "LUTwithBGrid",
        "type": "onnx",
    },
}

# ═══════════════════════════════════════════════════════════
#  ДЕФОЛТНЫЕ ЗНАЧЕНИЯ
# ═══════════════════════════════════════════════════════════
DEFAULT_PROFILE = "metal"
DEFAULT_CATEGORY = "metal"
DEFAULT_CORRECTION_MODE = "ai"
DEFAULT_SOAP_STRENGTH = 1.0
DEFAULT_SATURATION = 1.15
DEFAULT_BIT_DEPTH = 8
DEFAULT_UI_MODE = "simple"
DEFAULT_THEME = "dark"
DEFAULT_ACTIVE_TAB = "single"

# ═══════════════════════════════════════════════════════════
#  ДОНАТЫ
# ═══════════════════════════════════════════════════════════
WALLETS = [
    {"label": "BTC", "address": "bc1q2ka70s4vtmrskandqj8l4d6n3kdxyxa7kf3wf7"},
    {"label": "USDT (TRC-20)", "address": "TUjY9p6oxKmeCQwNZwMfHqHdXuabaHpgT7"},
    {"label": "TON", "address": "UQDWumGNNlnITx48WBzyI7Clb5wrpFRlJ3Se7xhfVKY5E2ad"},
]

# ═══════════════════════════════════════════════════════════
#  ТЕМЫ
# ═══════════════════════════════════════════════════════════
THEME_DARK = {
    "bg":      "#1a1d23",
    "panel":   "#20242b",
    "card":    "#282c34",
    "input":   "#32373f",
    "fg":      "#e8eaed",
    "fg2":     "#9aa0a6",
    "fg3":     "#5f6368",
    "accent":  "#5b8dd9",
    "success": "#4caf50",
    "danger":  "#e53935",
    "warn":    "#ff9800",
}

THEME_LIGHT = {
    "bg":      "#f0f2f5",
    "panel":   "#ffffff",
    "card":    "#e8eaed",
    "input":   "#dde1e6",
    "fg":      "#1a1d23",
    "fg2":     "#5f6368",
    "fg3":     "#8a8f96",
    "accent":  "#3d6fb8",
    "success": "#2e7d32",
    "danger":  "#c62828",
    "warn":    "#ef6c00",
}

# ═══════════════════════════════════════════════════════════
#  ПРОФИЛИ ТЕКСТУР
# ═══════════════════════════════════════════════════════════
TEXTURE_PROFILES = {
    # 🔥 METAL
    "metal":          {"dark": 140, "light": 255, "ru": "Металл",        "en": "Metal",          "emoji": "⚙"},
    "rust":           {"dark": 20,  "light": 235, "ru": "Ржавчина",       "en": "Rust",           "emoji": "🔴"},
    "oxidized_metal": {"dark": 30,  "light": 240, "ru": "Окисл. металл",  "en": "Oxidized Metal", "emoji": "🟢"},
    "patina":         {"dark": 25,  "light": 235, "ru": "Патина",         "en": "Patina",         "emoji": "🟩"},
    "brass":          {"dark": 120, "light": 250, "ru": "Латунь",         "en": "Brass",          "emoji": "🟡"},
    "aluminum":       {"dark": 130, "light": 250, "ru": "Алюминий",       "en": "Aluminum",       "emoji": "⚪"},
    # 🌿 NATURE
    "wood":           {"dark": 25,  "light": 240, "ru": "Дерево",         "en": "Wood",           "emoji": "🌳"},
    "leaves":         {"dark": 20,  "light": 245, "ru": "Листва",         "en": "Leaves",         "emoji": "🌿"},
    "moss":           {"dark": 10,  "light": 230, "ru": "Мох",            "en": "Moss",           "emoji": "🌱"},
    "organic":        {"dark": 15,  "light": 235, "ru": "Органика",       "en": "Organic",        "emoji": "🍂"},
    "grass":          {"dark": 20,  "light": 240, "ru": "Трава",          "en": "Grass",          "emoji": "🌾"},
    "bark":           {"dark": 20,  "light": 230, "ru": "Кора",           "en": "Bark",           "emoji": "🪵"},
    # 🪨 MINERAL
    "tile":           {"dark": 30,  "light": 245, "ru": "Плитка",       "en": "Tile",        "emoji": "🔲"},
    "gravel":         {"dark": 20,  "light": 220, "ru": "Гравий",       "en": "Gravel",      "emoji": "🪨"},
    "coal":           {"dark": 10,  "light": 150, "ru": "Уголь",        "en": "Coal",        "emoji": "⚫"},
    "roof_tiles":     {"dark": 25,  "light": 230, "ru": "Черепица",     "en": "Roof Tiles",  "emoji": "🏠"},
    "stone":          {"dark": 25,  "light": 235, "ru": "Камень",         "en": "Stone",          "emoji": "🪨"},
    "concrete":       {"dark": 30,  "light": 240, "ru": "Бетон",          "en": "Concrete",       "emoji": "🧊"},
    "brick":          {"dark": 25,  "light": 235, "ru": "Кирпич",         "en": "Brick",          "emoji": "🧱"},
    "ground":         {"dark": 20,  "light": 235, "ru": "Земля",          "en": "Ground",         "emoji": "🌍"},
    "asphalt":        {"dark": 15,  "light": 200, "ru": "Асфальт",        "en": "Asphalt",        "emoji": "⬛"},
    "marble":         {"dark": 35,  "light": 250, "ru": "Мрамор",         "en": "Marble",         "emoji": "⬜"},
    "sand":           {"dark": 40,  "light": 245, "ru": "Песок",          "en": "Sand",           "emoji": "🟨"},
    # 🧪 SYNTHETIC
    "plastic":        {"dark": 30,  "light": 245, "ru": "Пластик",        "en": "Plastic",        "emoji": "🎨"},
    "rubber":         {"dark": 20,  "light": 200, "ru": "Резина",         "en": "Rubber",         "emoji": "⚫"},
    "glass":          {"dark": 50,  "light": 250, "ru": "Стекло",         "en": "Glass",          "emoji": "💎"},
    "ceramic":        {"dark": 35,  "light": 245, "ru": "Керамика",       "en": "Ceramic",        "emoji": "🏺"},
    "painted_metal":  {"dark": 25,  "light": 240, "ru": "Краш. металл",   "en": "Painted Metal",  "emoji": "🎭"},
    # 💧 SPECIAL
    "water":          {"dark": 40,  "light": 250, "ru": "Вода",           "en": "Water",          "emoji": "💧"},
    "mud":            {"dark": 20,  "light": 220, "ru": "Грязь",          "en": "Mud",            "emoji": "🟤"},
    "snow":           {"dark": 80,  "light": 255, "ru": "Снег",           "en": "Snow",           "emoji": "❄"},
    "ice":            {"dark": 60,  "light": 250, "ru": "Лёд",            "en": "Ice",            "emoji": "🧊"},
    # 🐾 FAUNA
    "leather":        {"dark": 25,  "light": 235, "ru": "Кожа",           "en": "Leather",        "emoji": "🐂"},
    "fur":            {"dark": 20,  "light": 245, "ru": "Мех",            "en": "Fur",            "emoji": "🦊"},
    "skin":           {"dark": 30,  "light": 240, "ru": "Кожа (тело)",    "en": "Skin",           "emoji": "✋"},
    "scales":         {"dark": 25,  "light": 245, "ru": "Чешуя",          "en": "Scales",         "emoji": "🐍"},
    "bone":           {"dark": 60,  "light": 245, "ru": "Кость",        "en": "Bone",        "emoji": "🦴"},
}

# ═══════════════════════════════════════════════════════════
#  PBR ПРЕСЕТЫ
# ═══════════════════════════════════════════════════════════
PBR_PRESETS = {
    # 🔥 METAL
    "metal":          {"strength": 0.8, "smooth": 1.0, "threshold": 0.05, "high_pass": 30, "height_blur": 1.5, "ao_radius": 6,  "ao_intensity": 1.0, "rough_base": 0.30, "rough_var": 0.40, "metallic": "white"},
    "rust":           {"strength": 1.5, "smooth": 1.5, "threshold": 0.05, "high_pass": 40, "height_blur": 2.0, "ao_radius": 10, "ao_intensity": 1.5, "rough_base": 0.80, "rough_var": 0.30, "metallic": "black"},
    "oxidized_metal": {"strength": 1.3, "smooth": 1.5, "threshold": 0.05, "high_pass": 35, "height_blur": 2.0, "ao_radius": 8,  "ao_intensity": 1.3, "rough_base": 0.55, "rough_var": 0.45, "metallic": "auto"},
    "patina":         {"strength": 1.3, "smooth": 1.8, "threshold": 0.05, "high_pass": 35, "height_blur": 2.0, "ao_radius": 8,  "ao_intensity": 1.2, "rough_base": 0.80, "rough_var": 0.25, "metallic": "black"},
    "brass":          {"strength": 0.8, "smooth": 1.0, "threshold": 0.05, "high_pass": 30, "height_blur": 1.5, "ao_radius": 6,  "ao_intensity": 1.0, "rough_base": 0.35, "rough_var": 0.35, "metallic": "white"},
    "aluminum":       {"strength": 1.0, "smooth": 1.2, "threshold": 0.05, "high_pass": 25, "height_blur": 1.2, "ao_radius": 5,  "ao_intensity": 0.9, "rough_base": 0.40, "rough_var": 0.30, "metallic": "white"},
    # 🌿 NATURE
    "wood":           {"strength": 1.2, "smooth": 1.5, "threshold": 0.05, "high_pass": 40, "height_blur": 2.0, "ao_radius": 8,  "ao_intensity": 1.2, "rough_base": 0.60, "rough_var": 0.30, "metallic": "black"},
    "leaves":         {"strength": 1.0, "smooth": 1.5, "threshold": 0.05, "high_pass": 30, "height_blur": 1.5, "ao_radius": 6,  "ao_intensity": 1.0, "rough_base": 0.50, "rough_var": 0.30, "metallic": "black"},
    "moss":           {"strength": 1.2, "smooth": 2.0, "threshold": 0.05, "high_pass": 35, "height_blur": 2.0, "ao_radius": 8,  "ao_intensity": 1.3, "rough_base": 0.90, "rough_var": 0.15, "metallic": "black"},
    "organic":        {"strength": 1.2, "smooth": 2.0, "threshold": 0.05, "high_pass": 35, "height_blur": 2.0, "ao_radius": 8,  "ao_intensity": 1.3, "rough_base": 0.80, "rough_var": 0.25, "metallic": "black"},
    "grass":          {"strength": 1.1, "smooth": 1.8, "threshold": 0.05, "high_pass": 32, "height_blur": 1.8, "ao_radius": 7,  "ao_intensity": 1.1, "rough_base": 0.65, "rough_var": 0.30, "metallic": "black"},
    "bark":           {"strength": 1.5, "smooth": 1.5, "threshold": 0.05, "high_pass": 45, "height_blur": 2.0, "ao_radius": 10, "ao_intensity": 1.6, "rough_base": 0.85, "rough_var": 0.25, "metallic": "black"},
    # 🪨 MINERAL
    "tile":           {"strength": 1.2, "smooth": 1.8, "threshold": 0.05, "high_pass": 35, "height_blur": 2.0, "ao_radius": 8,  "ao_intensity": 1.2, "rough_base": 0.45, "rough_var": 0.25, "metallic": "black"},
    "gravel":         {"strength": 1.8, "smooth": 1.5, "threshold": 0.05, "high_pass": 45, "height_blur": 1.8, "ao_radius": 9,  "ao_intensity": 1.8, "rough_base": 0.85, "rough_var": 0.25, "metallic": "black"},
    "coal":           {"strength": 1.5, "smooth": 1.8, "threshold": 0.05, "high_pass": 40, "height_blur": 2.0, "ao_radius": 8,  "ao_intensity": 1.5, "rough_base": 0.70, "rough_var": 0.30, "metallic": "black"},
    "roof_tiles":     {"strength": 1.6, "smooth": 1.5, "threshold": 0.05, "high_pass": 40, "height_blur": 2.0, "ao_radius": 10, "ao_intensity": 1.7, "rough_base": 0.75, "rough_var": 0.25, "metallic": "black"},
    "stone":          {"strength": 2.0, "smooth": 2.0, "threshold": 0.05, "high_pass": 50, "height_blur": 2.5, "ao_radius": 12, "ao_intensity": 2.0, "rough_base": 0.80, "rough_var": 0.20, "metallic": "black"},
    "concrete":       {"strength": 1.5, "smooth": 2.0, "threshold": 0.05, "high_pass": 40, "height_blur": 2.5, "ao_radius": 10, "ao_intensity": 1.5, "rough_base": 0.90, "rough_var": 0.15, "metallic": "black"},
    "brick":          {"strength": 1.8, "smooth": 1.5, "threshold": 0.05, "high_pass": 40, "height_blur": 2.0, "ao_radius": 10, "ao_intensity": 1.8, "rough_base": 0.85, "rough_var": 0.20, "metallic": "black"},
    "ground":         {"strength": 1.8, "smooth": 2.0, "threshold": 0.05, "high_pass": 45, "height_blur": 2.0, "ao_radius": 10, "ao_intensity": 1.8, "rough_base": 0.85, "rough_var": 0.20, "metallic": "black"},
    "asphalt":        {"strength": 1.6, "smooth": 2.0, "threshold": 0.05, "high_pass": 40, "height_blur": 2.0, "ao_radius": 9,  "ao_intensity": 1.6, "rough_base": 0.90, "rough_var": 0.15, "metallic": "black"},
    "marble":         {"strength": 0.7, "smooth": 1.5, "threshold": 0.05, "high_pass": 30, "height_blur": 1.5, "ao_radius": 6,  "ao_intensity": 0.8, "rough_base": 0.25, "rough_var": 0.20, "metallic": "black"},
    "sand":           {"strength": 1.2, "smooth": 2.0, "threshold": 0.05, "high_pass": 35, "height_blur": 2.0, "ao_radius": 8,  "ao_intensity": 1.3, "rough_base": 0.90, "rough_var": 0.20, "metallic": "black"},
    # 🧪 SYNTHETIC
    "plastic":        {"strength": 0.8, "smooth": 1.5, "threshold": 0.05, "high_pass": 30, "height_blur": 1.5, "ao_radius": 6,  "ao_intensity": 0.8, "rough_base": 0.35, "rough_var": 0.30, "metallic": "black"},
    "rubber":         {"strength": 1.2, "smooth": 2.0, "threshold": 0.05, "high_pass": 35, "height_blur": 2.0, "ao_radius": 7,  "ao_intensity": 1.2, "rough_base": 0.90, "rough_var": 0.10, "metallic": "black"},
    "glass":          {"strength": 0.5, "smooth": 1.5, "threshold": 0.05, "high_pass": 25, "height_blur": 1.0, "ao_radius": 5,  "ao_intensity": 0.6, "rough_base": 0.10, "rough_var": 0.15, "metallic": "black"},
    "ceramic":        {"strength": 0.9, "smooth": 1.5, "threshold": 0.05, "high_pass": 32, "height_blur": 1.8, "ao_radius": 6,  "ao_intensity": 0.9, "rough_base": 0.30, "rough_var": 0.25, "metallic": "black"},
    "painted_metal":  {"strength": 1.0, "smooth": 1.5, "threshold": 0.05, "high_pass": 32, "height_blur": 1.8, "ao_radius": 6,  "ao_intensity": 1.0, "rough_base": 0.45, "rough_var": 0.30, "metallic": "black"},
    # 💧 SPECIAL
    "water":          {"strength": 0.6, "smooth": 1.5, "threshold": 0.05, "high_pass": 25, "height_blur": 1.2, "ao_radius": 5,  "ao_intensity": 0.7, "rough_base": 0.05, "rough_var": 0.10, "metallic": "black"},
    "mud":            {"strength": 1.5, "smooth": 2.0, "threshold": 0.05, "high_pass": 40, "height_blur": 2.0, "ao_radius": 9,  "ao_intensity": 1.5, "rough_base": 0.85, "rough_var": 0.20, "metallic": "black"},
    "snow":           {"strength": 1.0, "smooth": 2.0, "threshold": 0.05, "high_pass": 30, "height_blur": 1.8, "ao_radius": 7,  "ao_intensity": 1.0, "rough_base": 0.40, "rough_var": 0.35, "metallic": "black"},
    "ice":            {"strength": 0.9, "smooth": 1.8, "threshold": 0.05, "high_pass": 28, "height_blur": 1.5, "ao_radius": 6,  "ao_intensity": 0.9, "rough_base": 0.20, "rough_var": 0.30, "metallic": "black"},
    # 🐾 FAUNA
    "leather":        {"strength": 1.1, "smooth": 1.8, "threshold": 0.05, "high_pass": 38, "height_blur": 1.8, "ao_radius": 7,  "ao_intensity": 1.1, "rough_base": 0.65, "rough_var": 0.30, "metallic": "black"},
    "fur":            {"strength": 1.2, "smooth": 2.0, "threshold": 0.05, "high_pass": 35, "height_blur": 2.0, "ao_radius": 8,  "ao_intensity": 1.2, "rough_base": 0.75, "rough_var": 0.30, "metallic": "black"},
    "skin":           {"strength": 0.9, "smooth": 2.0, "threshold": 0.05, "high_pass": 35, "height_blur": 2.0, "ao_radius": 7,  "ao_intensity": 1.0, "rough_base": 0.50, "rough_var": 0.30, "metallic": "black"},
    "scales":         {"strength": 1.3, "smooth": 1.5, "threshold": 0.05, "high_pass": 38, "height_blur": 1.8, "ao_radius": 7,  "ao_intensity": 1.3, "rough_base": 0.45, "rough_var": 0.35, "metallic": "black"},
    "bone":           {"strength": 1.0, "smooth": 1.5, "threshold": 0.05, "high_pass": 35, "height_blur": 1.8, "ao_radius": 7,  "ao_intensity": 1.0, "rough_base": 0.55, "rough_var": 0.25, "metallic": "black"},
}

# ═══════════════════════════════════════════════════════════
#  КАТЕГОРИИ ПРОФИЛЕЙ
# ═══════════════════════════════════════════════════════════
PROFILE_CATEGORIES = {
    "metal":   {"emoji": "🔥", "ru": "Металл",     "en": "Metal",
                "items": ["metal", "rust", "oxidized_metal", "patina", "brass", "aluminum"]},
    "nature":  {"emoji": "🌿", "ru": "Природа",    "en": "Nature",
                "items": ["wood", "leaves", "moss", "organic", "grass", "bark"]},
    "mineral": {"emoji": "🪨", "ru": "Минерал",    "en": "Mineral",
                "items": ["stone", "concrete", "brick", "ground", "asphalt", "marble", "sand",
                          "tile", "gravel", "coal", "roof_tiles"]},
    "synth":   {"emoji": "🧪", "ru": "Синтетика",  "en": "Synthetic",
                "items": ["plastic", "rubber", "glass", "ceramic", "painted_metal"]},
    "special": {"emoji": "💧", "ru": "Спецэффекты","en": "Special",
                "items": ["water", "mud", "snow", "ice"]},
    "fauna":   {"emoji": "🐾", "ru": "Фауна",      "en": "Fauna",
                "items": ["leather", "fur", "skin", "scales", "bone"]},
}