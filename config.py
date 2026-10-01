"""
config.py — все константы, словари и настройки Albedolizer.
Только данные, никакой логики.
"""

# ═══════════════════════════════════════════════════════════
#  МЕТА
# ═══════════════════════════════════════════════════════════
PP_TITLE = "Albedolizer v1.7.7-beta"
APP_VERSION = "1.7.7-beta"
APP_BUILD = "2026-10-01"
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
        "zh": "Autolevels",
        "type": "exe",
    },
    "lutwithbgrid": {
        "ru": "LUTwithBGrid",
        "en": "LUTwithBGrid",
        "zh": "LUTwithBGrid",
        "type": "onnx",
    },
}

# ═══════════════════════════════════════════════════════════
#  ДЕФОЛТНЫЕ ЗНАЧЕНИЯ
# ═══════════════════════════════════════════════════════════
DEFAULT_LANG = "en"
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
    {"label": "GRAM", "address": "UQDWumGNNlnITx48WBzyI7Clb5wrpFRlJ3Se7xhfVKY5E2ad"},
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
    # METAL
    "metal":          {"dark": 140, "light": 255, "ru": "Металл",        "en": "Metal",          "zh": "金属"},
    "rust":           {"dark": 20,  "light": 235, "ru": "Ржавчина",       "en": "Rust",           "zh": "锈"},
    "oxidized_metal": {"dark": 30,  "light": 240, "ru": "Окисл. металл",  "en": "Oxidized Metal", "zh": "氧化金属"},
    "patina":         {"dark": 25,  "light": 235, "ru": "Патина",         "en": "Patina",         "zh": "铜绿"},
    "brass":          {"dark": 120, "light": 250, "ru": "Латунь",         "en": "Brass",          "zh": "黄铜"},
    "aluminum":       {"dark": 130, "light": 250, "ru": "Алюминий",       "en": "Aluminum",       "zh": "铝"},
    "copper":         {"dark": 120, "light": 250, "ru": "Медь",           "en": "Copper",         "zh": "铜"},
    # NATURE
    "wood":           {"dark": 25,  "light": 240, "ru": "Дерево",         "en": "Wood",           "zh": "木材"},
    "leaves":         {"dark": 20,  "light": 245, "ru": "Листва",         "en": "Leaves",         "zh": "树叶"},
    "moss":           {"dark": 10,  "light": 230, "ru": "Мох",            "en": "Moss",           "zh": "苔藓"},
    "organic":        {"dark": 15,  "light": 235, "ru": "Органика",       "en": "Organic",        "zh": "有机"},
    "grass":          {"dark": 20,  "light": 240, "ru": "Трава",          "en": "Grass",          "zh": "草"},
    "bark":           {"dark": 20,  "light": 230, "ru": "Кора",           "en": "Bark",           "zh": "树皮"},
    # MINERAL
    "tile":           {"dark": 30,  "light": 245, "ru": "Плитка",         "en": "Tile",           "zh": "瓷砖"},
    "gravel":         {"dark": 20,  "light": 220, "ru": "Гравий",         "en": "Gravel",         "zh": "砾石"},
    "coal":           {"dark": 10,  "light": 150, "ru": "Уголь",          "en": "Coal",           "zh": "煤"},
    "roof_tiles":     {"dark": 25,  "light": 230, "ru": "Черепица",       "en": "Roof Tiles",     "zh": "屋顶瓦"},
    "stone":          {"dark": 25,  "light": 235, "ru": "Камень",         "en": "Stone",          "zh": "石头"},
    "concrete":       {"dark": 30,  "light": 240, "ru": "Бетон",          "en": "Concrete",       "zh": "混凝土"},
    "brick":          {"dark": 25,  "light": 235, "ru": "Кирпич",         "en": "Brick",          "zh": "砖"},
    "ground":         {"dark": 20,  "light": 235, "ru": "Земля",          "en": "Ground",         "zh": "地面"},
    "asphalt":        {"dark": 15,  "light": 200, "ru": "Асфальт",        "en": "Asphalt",        "zh": "沥青"},
    "marble":         {"dark": 35,  "light": 250, "ru": "Мрамор",         "en": "Marble",         "zh": "大理石"},
    "sand":           {"dark": 40,  "light": 245, "ru": "Песок",          "en": "Sand",           "zh": "沙子"},
    "clay":           {"dark": 30,  "light": 230, "ru": "Глина",          "en": "Clay",           "zh": "粘土"},
    "granite":        {"dark": 25,  "light": 230, "ru": "Гранит",         "en": "Granite",        "zh": "花岗岩"},
    "stucco":         {"dark": 40,  "light": 250, "ru": "Штукатурка",     "en": "Stucco",         "zh": "灰泥"},
    "gemstone":       {"dark": 30,  "light": 250, "ru": "Самоцвет",       "en": "Gemstone",       "zh": "宝石"},
    # SYNTHETIC
    "plastic":        {"dark": 30,  "light": 245, "ru": "Пластик",        "en": "Plastic",        "zh": "塑料"},
    "rubber":         {"dark": 20,  "light": 200, "ru": "Резина",         "en": "Rubber",         "zh": "橡胶"},
    "glass":          {"dark": 50,  "light": 250, "ru": "Стекло",         "en": "Glass",          "zh": "玻璃"},
    "ceramic":        {"dark": 35,  "light": 245, "ru": "Керамика",       "en": "Ceramic",        "zh": "陶瓷"},
    "painted_metal":  {"dark": 25,  "light": 240, "ru": "Краш. металл",   "en": "Painted Metal",  "zh": "涂漆金属"},
    "carbon":         {"dark": 15,  "light": 200, "ru": "Карбон",         "en": "Carbon",         "zh": "碳纤维"},
    "cardboard":      {"dark": 45,  "light": 245, "ru": "Картон",         "en": "Cardboard",      "zh": "纸板"},
    # SPECIAL
    "water":          {"dark": 40,  "light": 250, "ru": "Вода",           "en": "Water",          "zh": "水"},
    "mud":            {"dark": 20,  "light": 220, "ru": "Грязь",          "en": "Mud",            "zh": "泥"},
    "snow":           {"dark": 80,  "light": 255, "ru": "Снег",           "en": "Snow",           "zh": "雪"},
    "ice":            {"dark": 60,  "light": 250, "ru": "Лёд",            "en": "Ice",            "zh": "冰"},
    # FABRIC
    "cotton":         {"dark": 30,  "light": 245, "ru": "Хлопок",         "en": "Cotton",         "zh": "棉"},
    "wool":           {"dark": 25,  "light": 240, "ru": "Шерсть",         "en": "Wool",           "zh": "羊毛"},
    "silk":           {"dark": 40,  "light": 250, "ru": "Шёлк",           "en": "Silk",           "zh": "丝绸"},
    "denim":          {"dark": 25,  "light": 200, "ru": "Джинса",         "en": "Denim",          "zh": "牛仔布"},
    "carpet":         {"dark": 30,  "light": 235, "ru": "Ковёр",          "en": "Carpet",         "zh": "地毯"},
    "velvet":         {"dark": 20,  "light": 210, "ru": "Бархат",         "en": "Velvet",         "zh": "天鹅绒"},
    # FAUNA
    "leather":        {"dark": 25,  "light": 235, "ru": "Кожа",           "en": "Leather",        "zh": "皮革"},
    "fur":            {"dark": 20,  "light": 245, "ru": "Мех",            "en": "Fur",            "zh": "毛皮"},
    "skin":           {"dark": 30,  "light": 240, "ru": "Кожа (тело)",    "en": "Skin",           "zh": "皮肤"},
    "scales":         {"dark": 25,  "light": 245, "ru": "Чешуя",          "en": "Scales",         "zh": "鳞片"},
    "bone":           {"dark": 60,  "light": 245, "ru": "Кость",          "en": "Bone",           "zh": "骨头"},
}

# ═══════════════════════════════════════════════════════════
#  PBR ПРЕСЕТЫ
# ═══════════════════════════════════════════════════════════
PBR_PRESETS = {
    # METAL
    "metal":          {"strength": 0.8, "smooth": 1.0, "threshold": 0.05, "high_pass": 30, "height_blur": 1.5, "ao_radius": 6,  "ao_intensity": 1.0, "rough_base": 0.30, "rough_var": 0.40, "metallic": "white"},
    "rust":           {"strength": 1.5, "smooth": 1.5, "threshold": 0.05, "high_pass": 40, "height_blur": 2.0, "ao_radius": 10, "ao_intensity": 1.5, "rough_base": 0.80, "rough_var": 0.30, "metallic": "black"},
    "oxidized_metal": {"strength": 1.3, "smooth": 1.5, "threshold": 0.05, "high_pass": 35, "height_blur": 2.0, "ao_radius": 8,  "ao_intensity": 1.3, "rough_base": 0.55, "rough_var": 0.45, "metallic": "auto"},
    "patina":         {"strength": 1.3, "smooth": 1.8, "threshold": 0.05, "high_pass": 35, "height_blur": 2.0, "ao_radius": 8,  "ao_intensity": 1.2, "rough_base": 0.80, "rough_var": 0.25, "metallic": "black"},
    "brass":          {"strength": 0.8, "smooth": 1.0, "threshold": 0.05, "high_pass": 30, "height_blur": 1.5, "ao_radius": 6,  "ao_intensity": 1.0, "rough_base": 0.35, "rough_var": 0.35, "metallic": "white"},
    "aluminum":       {"strength": 1.0, "smooth": 1.2, "threshold": 0.05, "high_pass": 25, "height_blur": 1.2, "ao_radius": 5,  "ao_intensity": 0.9, "rough_base": 0.40, "rough_var": 0.30, "metallic": "white"},
    "copper":         {"strength": 0.8, "smooth": 1.2, "threshold": 0.05, "high_pass": 28, "height_blur": 1.5, "ao_radius": 6,  "ao_intensity": 1.0, "rough_base": 0.35, "rough_var": 0.35, "metallic": "white"},
    # NATURE
    "wood":           {"strength": 1.2, "smooth": 1.5, "threshold": 0.05, "high_pass": 40, "height_blur": 2.0, "ao_radius": 8,  "ao_intensity": 1.2, "rough_base": 0.60, "rough_var": 0.30, "metallic": "black"},
    "leaves":         {"strength": 1.0, "smooth": 1.5, "threshold": 0.05, "high_pass": 30, "height_blur": 1.5, "ao_radius": 6,  "ao_intensity": 1.0, "rough_base": 0.50, "rough_var": 0.30, "metallic": "black"},
    "moss":           {"strength": 1.2, "smooth": 2.0, "threshold": 0.05, "high_pass": 35, "height_blur": 2.0, "ao_radius": 8,  "ao_intensity": 1.3, "rough_base": 0.90, "rough_var": 0.15, "metallic": "black"},
    "organic":        {"strength": 1.2, "smooth": 2.0, "threshold": 0.05, "high_pass": 35, "height_blur": 2.0, "ao_radius": 8,  "ao_intensity": 1.3, "rough_base": 0.80, "rough_var": 0.25, "metallic": "black"},
    "grass":          {"strength": 1.1, "smooth": 1.8, "threshold": 0.05, "high_pass": 32, "height_blur": 1.8, "ao_radius": 7,  "ao_intensity": 1.1, "rough_base": 0.65, "rough_var": 0.30, "metallic": "black"},
    "bark":           {"strength": 1.5, "smooth": 1.5, "threshold": 0.05, "high_pass": 45, "height_blur": 2.0, "ao_radius": 10, "ao_intensity": 1.6, "rough_base": 0.85, "rough_var": 0.25, "metallic": "black"},
    # MINERAL
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
    "clay":           {"strength": 1.4, "smooth": 2.0, "threshold": 0.05, "high_pass": 38, "height_blur": 2.2, "ao_radius": 9,  "ao_intensity": 1.4, "rough_base": 0.85, "rough_var": 0.20, "metallic": "black"},
    "granite":        {"strength": 1.6, "smooth": 1.8, "threshold": 0.05, "high_pass": 45, "height_blur": 2.2, "ao_radius": 10, "ao_intensity": 1.7, "rough_base": 0.75, "rough_var": 0.25, "metallic": "black"},
    "stucco":         {"strength": 1.3, "smooth": 2.2, "threshold": 0.05, "high_pass": 35, "height_blur": 2.8, "ao_radius": 9,  "ao_intensity": 1.3, "rough_base": 0.75, "rough_var": 0.20, "metallic": "black"},
    "gemstone":       {"strength": 0.8, "smooth": 1.2, "threshold": 0.05, "high_pass": 28, "height_blur": 1.2, "ao_radius": 5,  "ao_intensity": 0.8, "rough_base": 0.15, "rough_var": 0.30, "metallic": "black"},
    # SYNTHETIC
    "plastic":        {"strength": 0.8, "smooth": 1.5, "threshold": 0.05, "high_pass": 30, "height_blur": 1.5, "ao_radius": 6,  "ao_intensity": 0.8, "rough_base": 0.35, "rough_var": 0.30, "metallic": "black"},
    "rubber":         {"strength": 1.2, "smooth": 2.0, "threshold": 0.05, "high_pass": 35, "height_blur": 2.0, "ao_radius": 7,  "ao_intensity": 1.2, "rough_base": 0.90, "rough_var": 0.10, "metallic": "black"},
    "glass":          {"strength": 0.5, "smooth": 1.5, "threshold": 0.05, "high_pass": 25, "height_blur": 1.0, "ao_radius": 5,  "ao_intensity": 0.6, "rough_base": 0.10, "rough_var": 0.15, "metallic": "black"},
    "ceramic":        {"strength": 0.9, "smooth": 1.5, "threshold": 0.05, "high_pass": 32, "height_blur": 1.8, "ao_radius": 6,  "ao_intensity": 0.9, "rough_base": 0.30, "rough_var": 0.25, "metallic": "black"},
    "painted_metal":  {"strength": 1.0, "smooth": 1.5, "threshold": 0.05, "high_pass": 32, "height_blur": 1.8, "ao_radius": 6,  "ao_intensity": 1.0, "rough_base": 0.45, "rough_var": 0.30, "metallic": "black"},
    "carbon":         {"strength": 1.0, "smooth": 1.2, "threshold": 0.05, "high_pass": 35, "height_blur": 1.5, "ao_radius": 6,  "ao_intensity": 1.0, "rough_base": 0.30, "rough_var": 0.25, "metallic": "black"},
    "cardboard":      {"strength": 0.7, "smooth": 2.0, "threshold": 0.05, "high_pass": 30, "height_blur": 2.0, "ao_radius": 7,  "ao_intensity": 0.9, "rough_base": 0.90, "rough_var": 0.15, "metallic": "black"},
    # SPECIAL
    "water":          {"strength": 0.6, "smooth": 1.5, "threshold": 0.05, "high_pass": 25, "height_blur": 1.2, "ao_radius": 5,  "ao_intensity": 0.7, "rough_base": 0.05, "rough_var": 0.10, "metallic": "black"},
    "mud":            {"strength": 1.5, "smooth": 2.0, "threshold": 0.05, "high_pass": 40, "height_blur": 2.0, "ao_radius": 9,  "ao_intensity": 1.5, "rough_base": 0.85, "rough_var": 0.20, "metallic": "black"},
    "snow":           {"strength": 1.0, "smooth": 2.0, "threshold": 0.05, "high_pass": 30, "height_blur": 1.8, "ao_radius": 7,  "ao_intensity": 1.0, "rough_base": 0.40, "rough_var": 0.35, "metallic": "black"},
    "ice":            {"strength": 0.9, "smooth": 1.8, "threshold": 0.05, "high_pass": 28, "height_blur": 1.5, "ao_radius": 6,  "ao_intensity": 0.9, "rough_base": 0.20, "rough_var": 0.30, "metallic": "black"},
    # FABRIC
    "cotton":         {"strength": 1.0, "smooth": 1.8, "threshold": 0.05, "high_pass": 35, "height_blur": 1.8, "ao_radius": 7,  "ao_intensity": 1.1, "rough_base": 0.80, "rough_var": 0.15, "metallic": "black"},
    "wool":           {"strength": 1.2, "smooth": 2.0, "threshold": 0.05, "high_pass": 38, "height_blur": 2.0, "ao_radius": 8,  "ao_intensity": 1.3, "rough_base": 0.90, "rough_var": 0.15, "metallic": "black"},
    "silk":           {"strength": 0.8, "smooth": 1.5, "threshold": 0.05, "high_pass": 28, "height_blur": 1.5, "ao_radius": 6,  "ao_intensity": 0.8, "rough_base": 0.25, "rough_var": 0.25, "metallic": "black"},
    "denim":          {"strength": 1.3, "smooth": 1.8, "threshold": 0.05, "high_pass": 40, "height_blur": 2.0, "ao_radius": 8,  "ao_intensity": 1.4, "rough_base": 0.85, "rough_var": 0.20, "metallic": "black"},
    "carpet":         {"strength": 1.5, "smooth": 2.0, "threshold": 0.05, "high_pass": 42, "height_blur": 2.2, "ao_radius": 9,  "ao_intensity": 1.6, "rough_base": 0.90, "rough_var": 0.15, "metallic": "black"},
    "velvet":         {"strength": 0.9, "smooth": 1.5, "threshold": 0.05, "high_pass": 30, "height_blur": 1.5, "ao_radius": 6,  "ao_intensity": 1.0, "rough_base": 0.60, "rough_var": 0.25, "metallic": "black"},
    # FAUNA
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
    "metal":   {"ru": "Металл",     "en": "Metal",     "zh": "金属",
                "items": ["metal", "rust", "oxidized_metal", "patina", "brass", "aluminum", "copper"]},
    "nature":  {"ru": "Природа",    "en": "Nature",    "zh": "自然",
                "items": ["wood", "leaves", "moss", "organic", "grass", "bark"]},
    "mineral": {"ru": "Минерал",    "en": "Mineral",   "zh": "矿物",
                "items": ["stone", "concrete", "brick", "ground", "asphalt", "marble", "sand",
                          "tile", "gravel", "coal", "roof_tiles", "clay", "granite",
                          "stucco", "gemstone"]},
    "synth":   {"ru": "Синтетика",  "en": "Synthetic", "zh": "合成",
                "items": ["plastic", "rubber", "glass", "ceramic", "painted_metal", "carbon",
                          "cardboard"]},
    "fabric":  {"ru": "Ткани",      "en": "Fabric",    "zh": "织物",
                "items": ["cotton", "wool", "silk", "denim", "carpet", "velvet"]},
    "special": {"ru": "Спецэффекты","en": "Special",   "zh": "特殊",
                "items": ["water", "mud", "snow", "ice"]},
    "fauna":   {"ru": "Фауна",      "en": "Fauna",     "zh": "动物",
                "items": ["leather", "fur", "skin", "scales", "bone"]},
}