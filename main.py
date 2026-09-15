import flet as ft
import numpy as np
from PIL import Image
import os
import sys
import base64
import io
import asyncio
import gc
import cv2
import subprocess
import tempfile
import shutil
from pbr_generator import (
    generate_all_pbr, remove_soap_adaptive,
    boost_saturation,
    to_preview_pil, save_pbr_map,
)


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
}

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
}

PROFILE_CATEGORIES = {
    "metal":   {"emoji": "🔥", "ru": "Металл",     "en": "Metal",
                "items": ["metal", "rust", "oxidized_metal", "patina", "brass", "aluminum"]},
    "nature":  {"emoji": "🌿", "ru": "Природа",    "en": "Nature",
                "items": ["wood", "leaves", "moss", "organic", "grass", "bark"]},
    "mineral": {"emoji": "🪨", "ru": "Минерал",    "en": "Mineral",
                "items": ["stone", "concrete", "brick", "ground", "asphalt", "marble", "sand"]},
    "synth":   {"emoji": "🧪", "ru": "Синтетика",  "en": "Synthetic",
                "items": ["plastic", "rubber", "glass", "ceramic", "painted_metal"]},
    "special": {"emoji": "💧", "ru": "Спецэффекты","en": "Special",
                "items": ["water", "mud", "snow", "ice"]},
    "fauna":   {"emoji": "🐾", "ru": "Фауна",      "en": "Fauna",
                "items": ["leather", "fur", "skin", "scales"]},
}


def _fallback_standalone(pil, profile_key):
    """Standalone-версия smart_correct_fallback (без log)."""
    prof = TEXTURE_PROFILES[profile_key]
    dark_t = prof["dark"]
    light_t = prof["light"]

    lab = np.array(pil.convert("LAB")).astype(np.uint8)
    L = lab[:, :, 0]

    p1 = float(np.percentile(L, 1))
    p99 = float(np.percentile(L, 99))
    std_L = float(np.std(L))

    if std_L < 15:
        clip_limit = 1.5
    elif std_L < 35:
        clip_limit = 2.0
    elif std_L < 55:
        clip_limit = 2.8
    else:
        clip_limit = 3.5

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    L_clahe = clahe.apply(L)

    need = 0.0
    if p1 < dark_t - 10:
        need += min(1.0, (dark_t - 10 - p1) / 50.0)
    if p99 > light_t + 10:
        need += min(1.0, (p99 - light_t - 10) / 50.0)
    need = min(1.0, need)

    blend = 0.4 + need * 0.3
    L_new = (L_clahe.astype(np.float32) * blend +
              L.astype(np.float32) * (1 - blend))

    hard_dark = max(0, dark_t - 20)
    hard_light = min(255, light_t + 20)

    dark_excess = np.maximum(0, hard_dark - L_new)
    L_new = L_new + dark_excess * 0.6

    light_excess = np.maximum(0, L_new - hard_light)
    L_new = L_new - light_excess * 0.6

    new_range = np.percentile(L_new, 99) - np.percentile(L_new, 1)
    target_range = hard_light - hard_dark

    if new_range < target_range * 0.55:
        np1 = np.percentile(L_new, 1)
        np99 = np.percentile(L_new, 99)
        if np99 - np1 > 1:
            L_norm = np.clip((L_new - np1) / (np99 - np1), 0, 1)
            L_curved = L_norm * L_norm * (3 - 2 * L_norm)
            L_mixed = 0.3 * L_curved + 0.7 * L_norm
            L_stretched = hard_dark + L_mixed * (hard_light - hard_dark)
            L_new = L_new * 0.7 + L_stretched * 0.3

    L_final = np.clip(L_new, 0, 255).astype(np.uint8)
    lab[:, :, 0] = L_final
    result = Image.fromarray(lab, mode="LAB").convert("RGB")

    arr = np.array(result).astype(np.uint8)
    hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.02, 0, 255)
    arr_back = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    return Image.fromarray(arr_back, mode="RGB")


# ═══════════════════════════════════════════════════════════
#  ПЕРЕВОДЫ
# ═══════════════════════════════════════════════════════════
T = {
    "ru": {
        "subtitle": "PBR Albedo Checker & Optimizer",
        "tab_single": "🖼 Одиночная", "tab_pbr": "🎨 PBR",
        "tab_compress": "🗜 Сжатие", "tab_batch": "🗂 Пакетная",
        "load": "📂 Открыть", "check": "🔍 Проверить",
        "fix": "✨ Автокоррекция", "compress": "🗜 Сжать",
        "save": "💾 Сохранить", "reset": "↺ Сброс",
        "stats_title": "СТАТИСТИКА", "profile_title": "ТИП ТЕКСТУРЫ",
        "correction_mode_title": "РЕЖИМ КОРРЕКЦИИ",
        "correction_ai": "✨ AI",
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
        "welcome_1": "👋 Добро пожаловать в Albedolizer v1.3.3-beta",
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
        # Compress tab
        "compress_title": "СЖАТИЕ ALBEDO",
        "compress_single": "ОДИНОЧНОЕ СЖАТИЕ",
        "compress_batch": "ПАКЕТНОЕ СЖАТИЕ",
        "compress_run": "🗜 Сжать",
        "compress_batch_run": "▶ Сжать папку",
        "compress_log_done": "🗜 Сжатие выполнено:",
        "compress_batch_started": "⚡ Пакетное сжатие:",
        "compress_out": "Результат в:",
        # PBR
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
        "correction_mode_title": "CORRECTION MODE",
        "correction_ai": "✨ AI",
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
        "welcome_1": "👋 Welcome to Albedolizer v1.3.3-beta",
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
        # Compress tab
        "compress_title": "ALBEDO COMPRESSION",
        "compress_single": "SINGLE COMPRESSION",
        "compress_batch": "BATCH COMPRESSION",
        "compress_run": "🗜 Compress",
        "compress_batch_run": "▶ Compress folder",
        "compress_log_done": "🗜 Compression done:",
        "compress_batch_started": "⚡ Batch compression:",
        "compress_out": "Output:",
        # PBR
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


def _detect_system_lang():
    """Определяет язык системы через Windows API. ru → 'ru', остальное → 'en'."""
    try:
        import ctypes
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        primary = lang_id & 0x03FF
        if primary == 0x19:
            return "ru"
        return "en"
    except Exception:
        return "en"
        
def main(page: ft.Page):
    # ═══ Состояние ═══
    S = {
        "image_path": None,
        "original": None,
        "corrected": None,
        "profile": "metal",
        "profile_category": "metal",
        "correction_mode": "ai",
        "soap_fix_strength": 1.0,
        "saturation_boost": 1.15,
        "pbr_bit_depth": 8,
        "last_op": None,
        "lang": _detect_system_lang(),
        "theme": "dark",
        "ui_mode": "simple",
        "log_lines": [],
        "stats_lines": [],
        "pbr_source": None,
        "pbr_source_path": None,
        "pbr_result": None,
        "pbr_current_map": "albedo",
        "pbr_metallic": "black",
        "pbr_sliders": {},
        "pbr_preview": None,
        "pbr_preview_hint": None,
        "pbr_map_buttons": {},
        "pbr_batch_results": {},
        "pbr_batch_selected": None,
        "pbr_batch_index": 0,
        "pbr_batch_label": None,
        "pbr_batch_nav_panel": None,
        "batch_files": [],
        "compress_files": [],
        "active_tab": "single",
        "tiling_mode": False,
        "compress_original": None,
        "compress_corrected": None,
        "compress_path": None,
    }

    # ═══ Цвета темы ═══
    _theme = THEME_DARK if S["theme"] == "dark" else THEME_LIGHT
    BG = _theme["bg"]
    PANEL = _theme["panel"]
    CARD = _theme["card"]
    INPUT = _theme["input"]
    FG = _theme["fg"]
    FG2 = _theme["fg2"]
    FG3 = _theme["fg3"]
    ACCENT = _theme["accent"]
    SUCCESS = _theme["success"]
    DANGER = _theme["danger"]
    WARN = _theme["warn"]
    FONT = "Segoe UI"
    PBR_COLOR = SUCCESS
    BATCH_COLOR = WARN
    COMPRESS_COLOR = "#1565c0" if S["theme"] == "dark" else "#3d6fb8"
    SAVE_COLOR = "#6a4a9f"
    RESET_COLOR = "#555555" if S["theme"] == "dark" else "#9aa0a6"
    ON_ACCENT = "#ffffff"

    cv2.setNumThreads(os.cpu_count() or 4)
    page.title = "Albedolizer v1.3.3-beta"
    page.theme_mode = ft.ThemeMode.DARK if S["theme"] == "dark" else ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    page.window.width = 1280
    page.window.height = 820
    page.window.opacity = 0.97
    page.bgcolor = BG

    if getattr(sys, 'frozen', False):
        _base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        _icon_path = os.path.join(_base, "icon.ico")
    else:
        _icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    if os.path.exists(_icon_path):
        page.window.icon = _icon_path

    if getattr(sys, 'frozen', False):
        _base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        _base_dir = os.path.dirname(os.path.abspath(__file__))

    AUTOLEVELS_EXE = os.path.join(_base_dir, "autolevels.exe")
    AUTOLEVELS_MODEL = os.path.join(_base_dir, "free_xcittiny_wa14.onnx")

    def t(key):
        return T[S["lang"]].get(key, key)

    def profile_label(key):
        return TEXTURE_PROFILES[key][S["lang"]]

    def pil_to_b64(data, max_size=900):
        if isinstance(data, np.ndarray):
            data = to_preview_pil(data)
        p = data.copy()
        if p.mode not in ("RGB", "L"):
            p = p.convert("RGB")
        p.thumbnail((max_size, max_size), Image.LANCZOS)
        buf = io.BytesIO()
        p.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    def get_luminance(pil):
        arr = np.array(pil.convert("RGB")).astype(np.float32)
        return 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]

    def smart_correct_ai(pil):
        if not (os.path.exists(AUTOLEVELS_EXE) and os.path.exists(AUTOLEVELS_MODEL)):
            log("   ⚠ AI-модель/autolevels.exe не найдены", WARN)
            return None, False

        try:
            tmpdir = tempfile.mkdtemp(prefix="albedolizer_")
            try:
                src_path = os.path.join(tmpdir, "input.png")
                pil.save(src_path)
                creation_flags = 0x08000000 if os.name == 'nt' else 0
                result = subprocess.run(
                    [AUTOLEVELS_EXE, "--model", AUTOLEVELS_MODEL,
                     "--outdir", tmpdir, src_path],
                    capture_output=True, text=True, timeout=300,
                    creationflags=creation_flags
                )
                if result.returncode != 0:
                    log(f"   ⚠ autolevels: {result.stderr[:150]}", WARN)

                out_path = os.path.join(tmpdir, "input_al.png")
                if os.path.exists(out_path):
                    img = Image.open(out_path).convert("RGB")
                    img.load()
                    log("   ✅ AI-модель: применена", SUCCESS)
                    return img, True
                else:
                    log("   ⚠ AI-модель: результат не создан", WARN)
                    return None, False
            finally:
                shutil.rmtree(tmpdir, ignore_errors=True)
        except subprocess.TimeoutExpired:
            log("   ⚠ AI-модель: таймаут", WARN)
            return None, False
        except Exception as e:
            log(f"   ❌ AI-модель: {type(e).__name__}: {e}", DANGER)
            return None, False

    def smart_correct_fallback(pil, profile_key):
        prof = TEXTURE_PROFILES[profile_key]
        dark_t = prof["dark"]
        light_t = prof["light"]

        lab = np.array(pil.convert("LAB")).astype(np.uint8)
        L = lab[:, :, 0]

        p1 = float(np.percentile(L, 1))
        p99 = float(np.percentile(L, 99))
        std_L = float(np.std(L))

        if std_L < 15:
            clip_limit = 1.5
        elif std_L < 35:
            clip_limit = 2.0
        elif std_L < 55:
            clip_limit = 2.8
        else:
            clip_limit = 3.5

        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        L_clahe = clahe.apply(L)

        need = 0.0
        if p1 < dark_t - 10:
            need += min(1.0, (dark_t - 10 - p1) / 50.0)
        if p99 > light_t + 10:
            need += min(1.0, (p99 - light_t - 10) / 50.0)
        need = min(1.0, need)

        blend = 0.4 + need * 0.3
        L_new = (L_clahe.astype(np.float32) * blend +
                  L.astype(np.float32) * (1 - blend))

        hard_dark = max(0, dark_t - 20)
        hard_light = min(255, light_t + 20)

        dark_excess = np.maximum(0, hard_dark - L_new)
        L_new = L_new + dark_excess * 0.6

        light_excess = np.maximum(0, L_new - hard_light)
        L_new = L_new - light_excess * 0.6

        new_range = np.percentile(L_new, 99) - np.percentile(L_new, 1)
        target_range = hard_light - hard_dark

        if new_range < target_range * 0.55:
            np1 = np.percentile(L_new, 1)
            np99 = np.percentile(L_new, 99)
            if np99 - np1 > 1:
                L_norm = np.clip((L_new - np1) / (np99 - np1), 0, 1)
                L_curved = L_norm * L_norm * (3 - 2 * L_norm)
                L_mixed = 0.3 * L_curved + 0.7 * L_norm
                L_stretched = hard_dark + L_mixed * (hard_light - hard_dark)
                L_new = L_new * 0.7 + L_stretched * 0.3

        L_final = np.clip(L_new, 0, 255).astype(np.uint8)
        lab[:, :, 0] = L_final
        result = Image.fromarray(lab, mode="LAB").convert("RGB")

        arr = np.array(result).astype(np.uint8)
        hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.02, 0, 255)
        arr_back = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        return Image.fromarray(arr_back, mode="RGB")

    # ═══ UI ЭЛЕМЕНТЫ ═══
    S["log_column"] = ft.ListView(spacing=3, auto_scroll=True, expand=True, padding=4)
    S["log_column_batch"] = ft.ListView(spacing=3, auto_scroll=True, expand=True, padding=4)
    S["log_column_pbr"] = ft.ListView(spacing=3, auto_scroll=True, expand=True, padding=4)
    S["log_column_compress"] = ft.ListView(spacing=3, auto_scroll=True, expand=True, padding=4)

    S["stats_column"] = ft.Column([], spacing=4)
    S["preview_image"] = ft.Image(src="", visible=False, fit=ft.BoxFit.CONTAIN)
    S["progress_bar"] = ft.ProgressBar(value=None, visible=False, color=ACCENT,
                                        bgcolor=INPUT, height=4, bar_height=4)
    S["progress_text"] = ft.Text("", color=FG2, size=12, font_family=FONT, visible=False)
    S["pbr_progress_bar"] = ft.ProgressBar(value=None, visible=False, color=PBR_COLOR,
                                             bgcolor=INPUT, height=4, bar_height=4)
    S["pbr_progress_text"] = ft.Text("", color=FG2, size=12, font_family=FONT, visible=False)
    S["batch_progress_bar"] = ft.ProgressBar(value=0, visible=True, color=BATCH_COLOR,
                                               bgcolor=INPUT, height=4, bar_height=4)
    S["batch_progress_text"] = ft.Text("", color=FG2, size=12, font_family=FONT)
    S["compress_progress_bar"] = ft.ProgressBar(value=0, visible=True, color=COMPRESS_COLOR,
                                                  bgcolor=INPUT, height=4, bar_height=4)
    S["compress_progress_text"] = ft.Text("", color=FG2, size=12, font_family=FONT)
    S["buttons"] = {}

    def log(text, color=None):
        S["log_lines"].append((text, color or FG2))
        if len(S["log_lines"]) > 200:
            S["log_lines"].pop(0)
        refresh_log()

    def refresh_log():
        for lc in (S["log_column"], S["log_column_batch"],
                   S["log_column_pbr"], S["log_column_compress"]):
            lc.controls.clear()
            for txt, col in S["log_lines"]:
                lc.controls.append(
                    ft.Text(txt, color=col, size=13, font_family="Consolas",
                            selectable=True, expand=True)
                )

    def clear_stats():
        S["stats_lines"].clear()
        S["stats_column"].controls.clear()

    def add_stat(label, value, color=None):
        S["stats_lines"].append((label, value, color or FG2))
        S["stats_column"].controls.append(
            ft.Row([
                ft.Text(label, color=FG3, size=13, font_family=FONT, width=95),
                ft.Text(value, color=color or FG2, size=13, font_family="Consolas",
                        weight=ft.FontWeight.W_600),
            ], spacing=8)
        )

    async def show_progress(text="Обработка..."):
        S["progress_text"].value = text
        S["progress_text"].visible = True
        S["progress_bar"].visible = True
        page.update()
        await asyncio.sleep(0.05)
        page.update()

    async def hide_progress():
        S["progress_bar"].visible = False
        S["progress_text"].visible = False
        page.update()
        await asyncio.sleep(0.02)

    async def show_pbr_progress(text="Обработка..."):
        S["pbr_progress_text"].value = text
        S["pbr_progress_text"].visible = True
        S["pbr_progress_bar"].visible = True
        page.update()
        await asyncio.sleep(0.05)
        page.update()

    async def hide_pbr_progress():
        S["pbr_progress_bar"].visible = False
        S["pbr_progress_text"].visible = False
        page.update()
        await asyncio.sleep(0.02)

    def update_batch_progress(done, total, text=None):
        pct = int((done / total) * 100) if total > 0 else 0
        S["batch_progress_bar"].value = pct / 100
        if text is not None:
            S["batch_progress_text"].value = text
        else:
            S["batch_progress_text"].value = f"{done} / {total}  ({pct}%)"
        page.update()

    def update_compress_progress(done, total, text=None):
        pct = int((done / total) * 100) if total > 0 else 0
        S["compress_progress_bar"].value = pct / 100
        if text is not None:
            S["compress_progress_text"].value = text
        else:
            S["compress_progress_text"].value = f"{done} / {total}  ({pct}%)"
        page.update()

    def analyze_image(pil):
        lum = get_luminance(pil)
        prof = TEXTURE_PROFILES[S["profile"]]
        dt = prof["dark"]
        lt = prof["light"]
        total = lum.size
        dark_px = int(np.sum(lum < dt))
        light_px = int(np.sum(lum > lt))
        return {
            "min": float(np.min(lum)), "max": float(np.max(lum)),
            "avg": float(np.mean(lum)), "median": float(np.median(lum)),
            "p1": float(np.percentile(lum, 1)),
            "p99": float(np.percentile(lum, 99)),
            "dark_pct": dark_px / total * 100,
            "light_pct": light_px / total * 100,
            "dark_t": dt, "light_t": lt,
            "dark_px": dark_px, "light_px": light_px,
        }, lum

    def run_check(img, show_heatmap=True):
        s, lum = analyze_image(img)
        clear_stats()
        add_stat(t("stat_min"), f"{s['min']:.1f}")
        add_stat(t("stat_max"), f"{s['max']:.1f}")
        add_stat(t("stat_avg"), f"{s['avg']:.1f}")
        add_stat(t("stat_median"), f"{s['median']:.1f}")
        add_stat(t("stat_p1"), f"{s['p1']:.1f}")
        add_stat(t("stat_p99"), f"{s['p99']:.1f}")

        log("", FG2)
        log("━━━━━━━━━━━━━━━━━━━━━━", FG3)
        log(t("log_results"), FG)

        noise_t = 5.0
        dark_ok = s["dark_pct"] <= noise_t
        light_ok = s["light_pct"] <= noise_t

        log(f"  {t('log_dark')} (<{s['dark_t']}): {s['dark_pct']:.2f}%",
            SUCCESS if dark_ok else DANGER)
        log(f"  {t('log_light')} (>{s['light_t']}): {s['light_pct']:.2f}%",
            SUCCESS if light_ok else DANGER)

        fix_btn = S["buttons"].get("fix")
        if dark_ok and light_ok:
            log(t("log_pass"), SUCCESS)
            if fix_btn:
                fix_btn.disabled = True
        else:
            log(t("log_fail"), DANGER)
            if fix_btn:
                fix_btn.disabled = False

        if show_heatmap:
            arr = np.array(img).copy()
            arr[lum < s["dark_t"]] = [255, 0, 0]
            arr[lum > s["light_t"]] = [0, 100, 255]
            heatmap = Image.fromarray(arr.astype(np.uint8))
            S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(heatmap)}"

    async def do_check(e):
        if S["original"] is None:
            return
        await show_progress(t("progress_check"))
        await asyncio.sleep(0.1)
        img = S["corrected"] if S["corrected"] else S["original"]
        run_check(img, True)
        page.update()
        await asyncio.sleep(0.1)
        await hide_progress()

    async def do_auto_correct(e):
        if S["original"] is None:
            return
        try:
            await show_progress(t("progress_fix"))
            await asyncio.sleep(0.15)

            if S["correction_mode"] == "math":
                log("   → Режим: ∑ математическая коррекция", FG2)
                result = await asyncio.to_thread(
                    smart_correct_fallback, S["original"], S["profile"]
                )
                if S["soap_fix_strength"] > 0:
                    result = await asyncio.to_thread(
                        remove_soap_adaptive, result, S["soap_fix_strength"]
                    )
                S["corrected"] = result
                S["last_op"] = "corrected"
                S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(result)}"
                log("", FG2)
                log(t("log_fix_done"), SUCCESS)

                await asyncio.sleep(0.1)
                run_check(result, False)
                page.update()

                if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
                if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = False
                page.update()

                await asyncio.sleep(0.1)
                await hide_progress()
                return

            import time as _time
            _t0 = _time.time()
            ai_result, ai_ok = await asyncio.to_thread(
                smart_correct_ai, S["original"]
            )
            _dt = _time.time() - _t0
            log(f"   ⏱ AI-коррекция: {_dt:.2f} сек", FG2)

            if ai_ok and ai_result is not None:
                S["corrected"] = ai_result
                S["last_op"] = "corrected"
                S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(ai_result)}"
                log("", FG2)
                log(t("log_fix_done"), SUCCESS)

                await asyncio.sleep(0.1)
                run_check(ai_result, False)
                page.update()

                s, _ = analyze_image(ai_result)
                noise_t = 5.0
                ok = (s["dark_pct"] <= noise_t) and (s["light_pct"] <= noise_t)

                if not ok:
                    log("   ⚠ Результат AI не прошёл проверку", WARN)
                    show_fallback_dialog(ai_result, s)

                if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
                if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = False
                page.update()
            else:
                log("   → AI недоступен. Применяется fallback.", WARN)
                result = smart_correct_fallback(S["original"], S["profile"])
                if S["soap_fix_strength"] > 0:
                    result = await asyncio.to_thread(
                        remove_soap_adaptive, result, S["soap_fix_strength"]
                    )
                S["corrected"] = result
                S["last_op"] = "corrected"
                S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(result)}"
                log("", FG2)
                log(t("log_fix_done"), SUCCESS)

                await asyncio.sleep(0.1)
                run_check(result, False)
                page.update()

                if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
                if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = False
                page.update()

            await asyncio.sleep(0.1)
            await hide_progress()
        except Exception as ex:
            await hide_progress()
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def do_reset(e):
        if S["original"] is None:
            return
        S["corrected"] = None
        S["last_op"] = None
        S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(S['original'])}"
        log(t("log_reset"), FG2)
        if S["buttons"].get("save"): S["buttons"]["save"].disabled = True
        if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = True
        page.update()

    async def do_simple_process(e):
        """Simple mode: открыть → AI → saturation → результат."""
        try:
            files = await ft.FilePicker().pick_files(
                dialog_title=t("dialog_pick_title"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
            )
            if not files or not files[0].path:
                return
            fp = files[0].path

            await show_progress(t("progress_load"))
            await asyncio.sleep(0.1)

            img = Image.open(fp).convert("RGB")
            S["image_path"] = fp
            S["original"] = img
            S["corrected"] = None
            S["last_op"] = None
            S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(img)}"
            S["preview_image"].visible = True

            log("", FG2)
            log(f"{t('log_loaded')} {os.path.basename(fp)}", SUCCESS)
            log(f"{t('log_type')} {profile_label(S['profile'])}", FG2)
            page.update()

            await show_progress(t("progress_fix"))
            await asyncio.sleep(0.1)

            ai_result, ai_ok = await asyncio.to_thread(smart_correct_ai, img)

            if ai_ok and ai_result is not None:
                result = ai_result
            else:
                log("   → AI недоступен. Применяется fallback.", WARN)
                result = await asyncio.to_thread(
                    smart_correct_fallback, img, S["profile"]
                )

            # Saturation boost (1.15)
            result = await asyncio.to_thread(boost_saturation, result, 1.15)

            S["corrected"] = result
            S["last_op"] = "corrected"
            S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(result)}"
            log(t("log_fix_done"), SUCCESS)

            if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
            page.update()

            await asyncio.sleep(0.1)
            await hide_progress()
        except Exception as ex:
            await hide_progress()
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def open_file(e):
        try:
            files = await ft.FilePicker().pick_files(
                dialog_title=t("dialog_pick_title"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
            )
            if files and len(files) > 0:
                fp = files[0].path
                if fp:
                    await show_progress(t("progress_load"))
                    await asyncio.sleep(0.1)

                    img = Image.open(fp).convert("RGB")
                    S["image_path"] = fp
                    S["original"] = img
                    S["corrected"] = None
                    S["last_op"] = None
                    S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(img)}"
                    S["preview_image"].visible = True

                    log("", FG2)
                    log(f"{t('log_loaded')} {os.path.basename(fp)}", SUCCESS)
                    log(f"{t('log_type')} {profile_label(S['profile'])}", FG2)
                    log(t("log_click_check"), FG2)

                    if S["buttons"].get("check"): S["buttons"]["check"].disabled = False
                    if S["buttons"].get("fix"): S["buttons"]["fix"].disabled = True
                    if S["buttons"].get("save"): S["buttons"]["save"].disabled = True
                    if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = True
                    page.update()

                    await asyncio.sleep(0.15)
                    await hide_progress()
        except Exception as ex:
            await hide_progress()
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def open_save(e):
        try:
            if S.get("image_path"):
                base = os.path.splitext(os.path.basename(S["image_path"]))[0]
            else:
                base = "albedo"

            if S.get("last_op") == "compressed":
                default_name = f"{base}_compressed.png"
            else:
                default_name = f"{base}_corrected.png"

            path = await ft.FilePicker().save_file(
                dialog_title=t("dialog_save_title"),
                file_name=default_name,
                allowed_extensions=["png", "jpg", "tif"],
            )
            if path and S["corrected"] is not None:
                S["corrected"].save(str(path))
                log(f"{t('log_saved')} {os.path.basename(str(path))}", SUCCESS)
                page.update()
        except Exception as ex:
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    # ═══ СЖАТИЕ ═══
    async def compress_open_file(e):
        try:
            files = await ft.FilePicker().pick_files(
                dialog_title=t("dialog_pick_title"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
            )
            if files and len(files) > 0:
                fp = files[0].path
                if fp:
                    img = Image.open(fp).convert("RGB")
                    S["compress_original"] = img
                    S["compress_path"] = fp
                    S["compress_corrected"] = None
                    S["compress_preview"].src = f"data:image/png;base64,{pil_to_b64(img)}"
                    S["compress_preview"].visible = True
                    if S["compress_preview_hint"]:
                        S["compress_preview_hint"].visible = False
                    log(f"{t('log_loaded')} {os.path.basename(fp)}", SUCCESS)
                    if S["compress_buttons"].get("run"):
                        S["compress_buttons"]["run"].disabled = False
                    if S["compress_buttons"].get("save"):
                        S["compress_buttons"]["save"].disabled = True
                    page.update()
        except Exception as ex:
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def compress_do(e):
        if S["compress_original"] is None:
            return
        try:
            S["compress_progress_text"].value = t("progress_compress")
            S["compress_progress_text"].visible = True
            S["compress_progress_bar"].value = None
            S["compress_progress_bar"].visible = True
            page.update()
            await asyncio.sleep(0.1)

            result = await asyncio.to_thread(
                lambda: S["compress_original"].convert("LAB").convert("RGB")
            )
            S["compress_corrected"] = result
            S["compress_preview"].src = f"data:image/png;base64,{pil_to_b64(result)}"
            log(t("log_compress_done"), SUCCESS)

            if S["compress_buttons"].get("save"):
                S["compress_buttons"]["save"].disabled = False
            page.update()
            await asyncio.sleep(0.15)

            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            page.update()
        except Exception as ex:
            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def compress_save(e):
        if S["compress_corrected"] is None:
            return
        try:
            base = "albedo"
            if S.get("compress_path"):
                base = os.path.splitext(os.path.basename(S["compress_path"]))[0]

            path = await ft.FilePicker().save_file(
                dialog_title=t("dialog_save_title"),
                file_name=f"{base}_compressed.png",
                allowed_extensions=["png", "jpg", "tif"],
            )
            if not path:
                return

            S["compress_progress_text"].value = "💾 Сохранение..."
            S["compress_progress_text"].visible = True
            S["compress_progress_bar"].value = None
            S["compress_progress_bar"].visible = True
            page.update()
            await asyncio.sleep(0.05)

            await asyncio.to_thread(S["compress_corrected"].save, str(path))
            log(f"{t('log_saved')} {os.path.basename(str(path))}", SUCCESS)

            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            page.update()
        except Exception as ex:
            S["compress_progress_bar"].visible = False
            S["compress_progress_text"].visible = False
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def compress_select_folder(e):
        try:
            folder = await ft.FilePicker().get_directory_path(
                dialog_title=t("batch_select_folder"))
            if not folder:
                return
            exts = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')
            files = [os.path.join(folder, f) for f in os.listdir(folder)
                     if f.lower().endswith(exts)]
            S["compress_files"] = files
            log(f"📁 {t('batch_folder')} {folder}", FG2)
            log(f"   {t('batch_found')} {len(files)}", FG2)
            update_compress_progress(0, len(files),
                                     f"{t('batch_ready')}: {len(files)} {t('batch_files_count')}")
        except Exception as ex:
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def compress_select_files(e):
        try:
            files = await ft.FilePicker().pick_files(
                dialog_title=t("batch_select_files"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                allow_multiple=True,
            )
            if not files:
                return
            S["compress_files"] = [f.path for f in files if f.path]
            log(f"📄 {t('batch_selected')} {len(S['compress_files'])}", FG2)
            update_compress_progress(0, len(S["compress_files"]),
                                     f"{t('batch_ready')}: {len(S['compress_files'])} {t('batch_files_count')}")
        except Exception as ex:
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def compress_batch_run(e):
        files = S["compress_files"]
        if not files:
            log(t("batch_no_files"), WARN)
            page.update()
            return

        total = len(files)
        base_dir = os.path.dirname(files[0])
        out_dir = os.path.join(base_dir, "_compressed")
        os.makedirs(out_dir, exist_ok=True)

        log("", FG2)
        log("━━━━━━━━━━━━━━━━━━━━━━", FG3)
        log(f"{t('compress_batch_started')} {total}", FG)
        log(f"   {t('compress_out')} {out_dir}", FG2)
        page.update()

        count = 0
        for i, fp in enumerate(files, 1):
            try:
                img = Image.open(fp).convert("RGB")
                result = img.convert("LAB").convert("RGB")
                base = os.path.splitext(os.path.basename(fp))[0]
                result.save(str(os.path.join(out_dir, f"{base}.png")))
                img.close()
                count += 1
                log(f"  [{i}/{total}] ✓ {os.path.basename(fp)}", SUCCESS)
                update_compress_progress(i, total)
                if i % 5 == 0:
                    gc.collect()
                await asyncio.sleep(0.01)
            except Exception as ex:
                log(f"  ✗ {os.path.basename(fp)}: {ex}", DANGER)
                update_compress_progress(i, total)

        log(f"✅ {t('batch_processed')} {count} / {total}", SUCCESS)
        log(f"📁 {out_dir}", FG2)
        update_compress_progress(total, total, f"{t('batch_done')}: {count} / {total}")
        S["compress_files"] = []
        page.update()

    # ═══ ПАКЕТНАЯ AI-ОБРАБОТКА ═══
    async def batch_select_folder(e):
        try:
            folder = await ft.FilePicker().get_directory_path(
                dialog_title=t("batch_select_folder"))
            if not folder:
                return
            exts = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')
            files = [os.path.join(folder, f) for f in os.listdir(folder)
                     if f.lower().endswith(exts)]
            S["batch_files"] = files
            log(f"📁 {t('batch_folder')} {folder}", FG2)
            log(f"   {t('batch_found')} {len(files)}", FG2)
            S["batch_progress_bar"].value = 0
            S["batch_progress_text"].value = f"{t('batch_ready')}: {len(files)} {t('batch_files_count')}"
            page.update()
        except Exception as ex:
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def batch_select_files(e):
        try:
            files = await ft.FilePicker().pick_files(
                dialog_title=t("batch_select_files"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
                allow_multiple=True,
            )
            if not files:
                return
            S["batch_files"] = [f.path for f in files if f.path]
            log(f"📄 {t('batch_selected')} {len(S['batch_files'])}", FG2)
            S["batch_progress_bar"].value = 0
            S["batch_progress_text"].value = f"{t('batch_ready')}: {len(S['batch_files'])} {t('batch_files_count')}"
            page.update()
        except Exception as ex:
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def batch_run(e):
        files = S["batch_files"]
        if not files:
            log(t("batch_no_files"), WARN)
            page.update()
            return

        total = len(files)
        update_batch_progress(0, total, f"Запуск... 0 / {total}")

        base_dir = os.path.dirname(files[0])
        out_dir = os.path.join(base_dir, "_corrected")
        os.makedirs(out_dir, exist_ok=True)

        log("", FG2)
        log("━━━━━━━━━━━━━━━━━━━━━━", FG3)
        log(f"{t('batch_started')} {total}", FG)
        log(f"   {t('batch_out')} {out_dir}", FG2)
        page.update()

        count = 0
        done = 0
        sem = asyncio.Semaphore(3)

        async def process_one(fp):
            nonlocal count, done
            async with sem:
                base = os.path.splitext(os.path.basename(fp))[0]
                out_path = os.path.join(out_dir, f"{base}.png")
                err = None
                ok = False
                try:
                    img = Image.open(fp).convert("RGB")
                    if S["correction_mode"] == "math":
                        result = await asyncio.to_thread(
                            _fallback_standalone, img, S["profile"]
                        )
                    else:
                        import time as _time
                        _t0 = _time.time()
                        ai_res, ai_ok = await asyncio.to_thread(smart_correct_ai, img)
                        _dt = _time.time() - _t0
                        log(f"   ⏱ {os.path.basename(fp)}: {_dt:.2f} сек", FG2)
                        if ai_ok and ai_res is not None:
                            result = ai_res
                        else:
                            result = await asyncio.to_thread(
                                _fallback_standalone, img, S["profile"]
                            )
                    if S["soap_fix_strength"] > 0:
                        result = await asyncio.to_thread(
                            remove_soap_adaptive, result, S["soap_fix_strength"]
                        )
                    result.save(str(out_path))
                    img.close()
                    ok = True
                except Exception as ex:
                    err = f"{type(ex).__name__}: {ex}"
                done += 1
                if ok:
                    count += 1
                    log(f"  [{done}/{total}] ✓ {os.path.basename(fp)}", SUCCESS)
                else:
                    log(f"  ✗ {os.path.basename(fp)}: {err}", DANGER)
                update_batch_progress(done, total)
                page.update()

        await asyncio.gather(*[process_one(fp) for fp in files])

        log(f"✅ {t('batch_processed')} {count} / {total}", SUCCESS)
        log(f"📁 {out_dir}", FG2)
        update_batch_progress(total, total, f"{t('batch_done')}: {count} / {total}")
        S["batch_files"] = []
        page.update()

    # ═══ PBR-ОБРАБОТЧИКИ ═══
    async def pbr_do_load(e):
        try:
            files = await ft.FilePicker().pick_files(
                dialog_title=t("pbr_dialog_pick"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
            )
            if not files:
                return
            fp = files[0].path
            if not fp:
                return
            img = Image.open(fp).convert("RGB")
            S["pbr_source"] = img
            S["pbr_source_path"] = fp
            S["pbr_result"] = None
            log(f"{t('pbr_log_loaded')} {os.path.basename(fp)}", SUCCESS)
            log("→ " + t("pbr_gen"), FG2)

            if S["pbr_preview"] is not None:
                S["pbr_preview"].src = f"data:image/png;base64,{pil_to_b64(img)}"
                S["pbr_preview"].visible = True
            if S["pbr_preview_hint"] is not None:
                S["pbr_preview_hint"].visible = False

            if S["pbr_buttons"].get("gen"): S["pbr_buttons"]["gen"].disabled = False
            if S["pbr_buttons"].get("save"): S["pbr_buttons"]["save"].disabled = True
            page.update()
        except Exception as ex:
            log(f"❌ PBR load: {ex}", DANGER)
            page.update()

    async def pbr_do_generate(e):
        if S["pbr_source"] is None:
            return
        try:
            await show_pbr_progress(t("pbr_progress_gen"))
            await asyncio.sleep(0.15)

            sl = S["pbr_sliders"]
            result = generate_all_pbr(
                S["pbr_source"],
                height_blur=sl["height_blur"].value,
                normal_strength=sl["strength"].value,
                normal_smooth=sl["smooth"].value,
                normal_clamp=3.0,
                normal_high_pass=sl["high_pass"].value,
                normal_threshold=sl["threshold"].value,
                ao_radius=int(sl["ao_radius"].value),
                ao_intensity=sl["ao_intensity"].value,
                rough_base=sl["rough_base"].value,
                rough_variation=sl["rough_var"].value,
                metallic_mode=PBR_PRESETS.get(S["profile"], {}).get("metallic", S["pbr_metallic"]),
            )
            S["pbr_result"] = result
            log(t("pbr_log_gen_done"), SUCCESS)

            if S["pbr_buttons"].get("save"): S["pbr_buttons"]["save"].disabled = False
            page.update()

            await asyncio.sleep(0.15)
            await hide_pbr_progress()
        except Exception as ex:
            await hide_pbr_progress()
            log(f"❌ PBR generate: {ex}", DANGER)
            page.update()

    async def pbr_do_simple_generate(e):
        """Simple mode: открыть файл → сгенерировать с текущим пресетом."""
        try:
            files = await ft.FilePicker().pick_files(
                dialog_title=t("pbr_dialog_pick"),
                allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
            )
            if not files or not files[0].path:
                return
            fp = files[0].path
            img = Image.open(fp).convert("RGB")
            S["pbr_source"] = img
            S["pbr_source_path"] = fp
            S["pbr_result"] = None

            if S["pbr_preview"] is not None:
                S["pbr_preview"].src = f"data:image/png;base64,{pil_to_b64(img)}"
                S["pbr_preview"].visible = True
            if S["pbr_preview_hint"] is not None:
                S["pbr_preview_hint"].visible = False
            log(f"{t('pbr_log_loaded')} {os.path.basename(fp)}", SUCCESS)

            await show_pbr_progress(t("pbr_progress_gen"))
            await asyncio.sleep(0.1)

            # Если слайдеры уже есть — используем их, иначе пресет
            if S["pbr_sliders"]:
                sl = S["pbr_sliders"]
                result = generate_all_pbr(
                    img,
                    height_blur=sl["height_blur"].value,
                    normal_strength=sl["strength"].value,
                    normal_smooth=sl["smooth"].value,
                    normal_clamp=3.0,
                    normal_high_pass=sl["high_pass"].value,
                    normal_threshold=sl["threshold"].value,
                    ao_radius=int(sl["ao_radius"].value),
                    ao_intensity=sl["ao_intensity"].value,
                    rough_base=sl["rough_base"].value,
                    rough_variation=sl["rough_var"].value,
                    metallic_mode=PBR_PRESETS.get(S["profile"], {}).get("metallic", S["pbr_metallic"]),
                )
            else:
                preset = PBR_PRESETS.get(S["profile"], {})
                result = generate_all_pbr(
                    img,
                    height_blur=preset.get("height_blur", 2.0),
                    normal_strength=preset.get("strength", 1.5),
                    normal_smooth=preset.get("smooth", 1.5),
                    normal_clamp=3.0,
                    normal_high_pass=preset.get("high_pass", 40),
                    normal_threshold=preset.get("threshold", 0.05),
                    ao_radius=int(preset.get("ao_radius", 8)),
                    ao_intensity=preset.get("ao_intensity", 1.5),
                    rough_base=preset.get("rough_base", 0.7),
                    rough_variation=preset.get("rough_var", 0.3),
                    metallic_mode=preset.get("metallic", "black"),
                )

            S["pbr_result"] = result
            log(t("pbr_log_gen_done"), SUCCESS)

            if S["pbr_buttons"].get("save"): S["pbr_buttons"]["save"].disabled = False
            page.update()

            await asyncio.sleep(0.15)
            await hide_pbr_progress()
        except Exception as ex:
            await hide_pbr_progress()
            log(f"❌ PBR generate: {ex}", DANGER)
            page.update()

    async def pbr_do_save(e):
        if S["pbr_result"] is None:
            return
        try:
            await show_pbr_progress(t("pbr_progress_gen"))

            base_name = "pbr_output"
            if S["pbr_source_path"]:
                base_name = os.path.splitext(os.path.basename(S["pbr_source_path"]))[0]
            folder = os.path.dirname(S["pbr_source_path"]) if S["pbr_source_path"] else os.getcwd()
            out_dir = os.path.join(folder, f"{base_name}_pbr")
            os.makedirs(out_dir, exist_ok=True)

            total = len(S["pbr_result"])
            done = 0
            bit_depth = S.get("pbr_bit_depth", 8)
            for key, img in S["pbr_result"].items():
                save_pbr_map(img, str(os.path.join(out_dir, f"{base_name}_{key}.png")), bit_depth)
                done += 1
                S["pbr_progress_text"].value = f"{t('pbr_progress_gen')} {done}/{total}"
                page.update()
                await asyncio.sleep(0.02)

            gc.collect()
            log(f"{t('pbr_log_saved')} {out_dir}", SUCCESS)

            await hide_pbr_progress()
        except Exception as ex:
            await hide_pbr_progress()
            log(f"❌ PBR save: {ex}", DANGER)
            page.update()

    async def pbr_do_batch(e):
        try:
            folder = await ft.FilePicker().get_directory_path(
                dialog_title=t("pbr_dialog_folder"))
            if not folder:
                return
            exts = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')
            files = [os.path.join(folder, f) for f in os.listdir(folder)
                     if f.lower().endswith(exts)]
            if not files:
                log(t("pbr_log_no_files"), WARN)
                page.update()
                return

            await show_pbr_progress(t("pbr_progress_batch"))
            out_root = os.path.join(folder, "_pbr_output")
            os.makedirs(out_root, exist_ok=True)

            sl = S["pbr_sliders"]
            params = {
                "height_blur": sl["height_blur"].value,
                "normal_strength": sl["strength"].value,
                "normal_smooth": sl["smooth"].value,
                "normal_clamp": 3.0,
                "normal_high_pass": sl["high_pass"].value,
                "normal_threshold": sl["threshold"].value,
                "ao_radius": int(sl["ao_radius"].value),
                "ao_intensity": sl["ao_intensity"].value,
                "rough_base": sl["rough_base"].value,
                "rough_variation": sl["rough_var"].value,
                "metallic_mode": PBR_PRESETS.get(S["profile"], {}).get("metallic", S["pbr_metallic"]),
            }

            S["pbr_batch_results"] = {}
            count = 0
            total_files = len(files)
            for i, fp in enumerate(files, 1):
                try:
                    S["pbr_progress_text"].value = f"{t('pbr_progress_batch')} {i}/{total_files}"
                    page.update()

                    img = Image.open(fp).convert("RGB")
                    result = generate_all_pbr(img, **params)
                    base = os.path.splitext(os.path.basename(fp))[0]
                    sub = os.path.join(out_root, base)
                    os.makedirs(sub, exist_ok=True)
                    img.save(str(os.path.join(sub, f"{base}_albedo.png")))
                    bit_depth = S.get("pbr_bit_depth", 8)
                    for k, m in result.items():
                        save_pbr_map(m, str(os.path.join(sub, f"{base}_{k}.png")), bit_depth)
                    count += 1
                    S["pbr_batch_results"][base] = sub
                    log(f"  [{i}/{total_files}] ✓ {os.path.basename(fp)}", SUCCESS)
                    page.update()

                    try:
                        img.close()
                    except Exception:
                        pass
                    if i % 5 == 0:
                        gc.collect()

                    await asyncio.sleep(0.01)
                except Exception as ex:
                    log(f"  ✗ {os.path.basename(fp)}: {ex}", DANGER)
            log(f"{t('pbr_log_batch_done')} {count} {t('pbr_log_files')}", SUCCESS)
            log(f"📁 {out_root}", FG2)
            await hide_pbr_progress()

            if count > 0:
                keys = list(S["pbr_batch_results"].keys())
                S["pbr_batch_index"] = 0
                rebuild_ui()
                pbr_load_batch_texture(keys[0])
        except Exception as ex:
            await hide_pbr_progress()
            log(f"❌ PBR batch: {ex}", DANGER)
            page.update()

    def pbr_load_batch_texture(base_name):
        if not base_name or base_name == "_none_":
            return
        folder = S["pbr_batch_results"].get(base_name)
        if not folder or not os.path.exists(folder):
            return

        result = {}
        for key in ("albedo", "height", "normal", "ao", "roughness", "metallic", "orm", "edge"):
            path = os.path.join(folder, f"{base_name}_{key}.png")
            if os.path.exists(path):
                img = Image.open(path).convert("RGB")
                img.load()
                result[key] = img

        if not result:
            return

        S["pbr_result"] = result
        S["pbr_batch_selected"] = base_name
        keys = list(S["pbr_batch_results"].keys())
        if base_name in keys:
            S["pbr_batch_index"] = keys.index(base_name)

        show_key = "albedo" if "albedo" in result else next(iter(result.keys()), None)
        if show_key:
            S["pbr_preview"].src = f"data:image/png;base64,{pil_to_b64(result[show_key])}"
            S["pbr_preview"].visible = True
            S["pbr_current_map"] = show_key
            if S.get("pbr_preview_hint"):
                S["pbr_preview_hint"].visible = False

        pbr_batch_refresh_label()
        log(f"📂 Batch: загружена {base_name}", FG2)
        page.update()

    def pbr_batch_refresh_label():
        keys = list(S["pbr_batch_results"].keys())
        if not keys:
            if S.get("pbr_batch_label"):
                S["pbr_batch_label"].value = ""
            return
        idx = S["pbr_batch_index"]
        if idx >= len(keys):
            idx = 0
            S["pbr_batch_index"] = 0
        if S.get("pbr_batch_label"):
            S["pbr_batch_label"].value = f"{keys[idx]}  ({idx + 1}/{len(keys)})"

    def pbr_batch_next(e=None):
        keys = list(S["pbr_batch_results"].keys())
        if not keys:
            return
        S["pbr_batch_index"] = (S["pbr_batch_index"] + 1) % len(keys)
        pbr_load_batch_texture(keys[S["pbr_batch_index"]])
        for k, b in S["pbr_map_buttons"].items():
            b.bgcolor = ACCENT if k == S["pbr_current_map"] else CARD
            b.content.color = ON_ACCENT if k == S["pbr_current_map"] else FG2
        page.update()

    def pbr_batch_prev(e=None):
        keys = list(S["pbr_batch_results"].keys())
        if not keys:
            return
        S["pbr_batch_index"] = (S["pbr_batch_index"] - 1) % len(keys)
        pbr_load_batch_texture(keys[S["pbr_batch_index"]])
        for k, b in S["pbr_map_buttons"].items():
            b.bgcolor = ACCENT if k == S["pbr_current_map"] else CARD
            b.content.color = ON_ACCENT if k == S["pbr_current_map"] else FG2
        page.update()

    async def do_remove_soap(e):
        source = S["corrected"] if S["corrected"] is not None else S["original"]
        if source is None:
            log("   ⚠ Сначала загрузи текстуру", WARN)
            page.update()
            return
        try:
            await show_progress(t("soap_fix_progress"))
            await asyncio.sleep(0.1)

            result = await asyncio.to_thread(
                remove_soap_adaptive, source,
                S["soap_fix_strength"], 15, 25.0, None
            )
            S["corrected"] = result
            S["last_op"] = "soap_fix"
            S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(result)}"
            log(t("soap_fix_done"), SUCCESS)

            if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
            if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = False

            page.update()
            await asyncio.sleep(0.1)
            await hide_progress()
        except Exception as ex:
            await hide_progress()
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    async def do_boost_saturation(e):
        source = S["corrected"] if S["corrected"] is not None else S["original"]
        if source is None:
            log("   ⚠ Сначала загрузи текстуру", WARN)
            page.update()
            return
        try:
            await show_progress(t("sat_progress"))
            await asyncio.sleep(0.1)

            result = await asyncio.to_thread(
                boost_saturation, source, S["saturation_boost"]
            )
            S["corrected"] = result
            S["last_op"] = "saturation"
            S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(result)}"
            log(t("sat_done"), SUCCESS)

            if S["buttons"].get("save"): S["buttons"]["save"].disabled = False
            if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = False

            page.update()
            await asyncio.sleep(0.1)
            await hide_progress()
        except Exception as ex:
            await hide_progress()
            log(f"❌ {t('err')}: {ex}", DANGER)
            page.update()

    def toggle_tiling(e):
        S["tiling_mode"] = not S["tiling_mode"]
        img = None
        if S["corrected"] is not None:
            img = S["corrected"]
        elif S["original"] is not None:
            img = S["original"]
        if img is not None:
            if S["tiling_mode"]:
                w, h = img.size
                tiled = Image.new("RGB", (w * 3, h * 3))
                for x in range(3):
                    for y in range(3):
                        tiled.paste(img, (x * w, y * h))
                max_size = 1800
                tiled.thumbnail((max_size, max_size), Image.LANCZOS)
                S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(tiled)}"
            else:
                S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(img)}"
        rebuild_ui()

    def make_btn(label, on_click, color=None, disabled=False):
        color = color or ACCENT
        return ft.FilledButton(
            content=ft.Text(label, color=ON_ACCENT, size=14,
                            font_family=FONT, weight=ft.FontWeight.W_600,
                            text_align=ft.TextAlign.CENTER),
            style=ft.ButtonStyle(
                bgcolor=color, color=ON_ACCENT,
                padding=ft.Padding.symmetric(vertical=15, horizontal=14),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=on_click, disabled=disabled,
        )

    def set_profile(key):
        S["profile"] = key
        S["pbr_sliders"] = {}
        log(f"{t('log_type')} {profile_label(key)}", FG2)
        rebuild_ui()

    def make_correction_mode_switch():
        ai_active = S["correction_mode"] == "ai"
        math_active = S["correction_mode"] == "math"

        def set_mode(mode):
            S["correction_mode"] = mode
            rebuild_ui()

        ai_btn = ft.Container(
            content=ft.Text(
                t("correction_ai"),
                color=ON_ACCENT if ai_active else FG2,
                size=12, font_family=FONT,
                weight=ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=ACCENT if ai_active else CARD,
            border_radius=8,
            padding=ft.Padding.symmetric(vertical=8, horizontal=8),
            expand=True, ink=True,
            on_click=lambda e: set_mode("ai"),
        )
        math_btn = ft.Container(
            content=ft.Text(
                t("correction_math"),
                color=ON_ACCENT if math_active else FG2,
                size=12, font_family=FONT,
                weight=ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=ACCENT if math_active else CARD,
            border_radius=8,
            padding=ft.Padding.symmetric(vertical=8, horizontal=8),
            expand=True, ink=True,
            on_click=lambda e: set_mode("math"),
        )
        return ft.Row([ai_btn, math_btn], spacing=4)

    def set_category(key):
        S["profile_category"] = key
        items = PROFILE_CATEGORIES[key]["items"]
        if S["profile"] not in items:
            S["profile"] = items[0]
        S["pbr_sliders"] = {}
        rebuild_ui()

    def make_category_tabs(compact=False):
        rows = []
        row = []
        per_row = 3
        for key, cat in PROFILE_CATEGORIES.items():
            is_active = S["profile_category"] == key
            if compact:
                label = f"{cat['emoji']}"
                size = 16
            else:
                label = f"{cat['emoji']} {cat[S['lang']]}"
                size = 12
            btn = ft.Container(
                content=ft.Text(
                    label,
                    color=ON_ACCENT if is_active else FG2,
                    size=size, font_family=FONT,
                    weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_500,
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor=ACCENT if is_active else CARD,
                border_radius=8,
                padding=ft.Padding.symmetric(vertical=8, horizontal=4),
                expand=True, ink=True,
                tooltip=f"{cat['emoji']} {cat[S['lang']]}",
                on_click=lambda e, k=key: set_category(k),
            )
            row.append(btn)
            if len(row) == per_row:
                rows.append(ft.Row(row, spacing=4))
                row = []
        if row:
            while len(row) < per_row:
                row.append(ft.Container(expand=True))
            rows.append(ft.Row(row, spacing=4))
        return ft.Column(rows, spacing=4)

    def make_preset_grid(compact=False):
        cat_key = S["profile_category"]
        items = PROFILE_CATEGORIES[cat_key]["items"]
        rows = []
        row = []
        per_row = 3 if compact else 2
        for key in items:
            is_active = S["profile"] == key
            prof = TEXTURE_PROFILES[key]
            if compact:
                label = f"{prof['emoji']}"
                size = 14
            else:
                label = f"{prof['emoji']} {profile_label(key)}"
                size = 12
            btn = ft.Container(
                content=ft.Text(
                    label,
                    color=ON_ACCENT if is_active else FG2,
                    size=size, font_family=FONT,
                    weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_500,
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor=ACCENT if is_active else CARD,
                border_radius=10,
                padding=ft.Padding.symmetric(vertical=8, horizontal=4),
                expand=True, ink=True,
                tooltip=profile_label(key),
                on_click=lambda e, k=key: set_profile(k),
            )
            row.append(btn)
            if len(row) == per_row:
                rows.append(ft.Row(row, spacing=4))
                row = []
        if row:
            while len(row) < per_row:
                row.append(ft.Container(expand=True))
            rows.append(ft.Row(row, spacing=4))
        return ft.Column(rows, spacing=4)

    def create_info_dialog():
        help_content = ft.Container(
            content=ft.Column(
                [ft.Text(t("help_text"), color=FG, size=12,
                         font_family="Consolas", selectable=True,
                         expand=True)],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=ft.Padding.only(left=16, top=16, bottom=16, right=28),
            visible=True,
            expand=True,
        )
        about_content = ft.Container(
            content=ft.Column([
                ft.Text("◐ Albedolizer", size=24, weight=ft.FontWeight.BOLD,
                        color=ACCENT, font_family=FONT),
                ft.Container(height=16),
                ft.Row([ft.Text(f"{t('about_version')}:", color=FG3, size=12,
                                font_family=FONT, width=100),
                        ft.Text("1.3.3-beta", color=FG, size=12,
                                font_family="Consolas", weight=ft.FontWeight.W_600)]),
                ft.Row([ft.Text(f"{t('about_build')}:", color=FG3, size=12,
                                font_family=FONT, width=100),
                        ft.Text("2026-09-15", color=FG, size=12,
                                font_family="Consolas", weight=ft.FontWeight.W_600)]),
                ft.Row([ft.Text(f"{t('about_author')}:", color=FG3, size=12,
                                font_family=FONT, width=100),
                        ft.Text("INV.LVL", color=FG, size=12,
                                font_family="Consolas", weight=ft.FontWeight.W_600)]),
                ft.Row([ft.Text(f"{t('about_license')}:", color=FG3, size=12,
                                font_family=FONT, width=100),
                        ft.Text("Free / Open Source", color=FG, size=12,
                                font_family="Consolas", weight=ft.FontWeight.W_600)]),
                ft.Container(height=20),
                ft.Text(t("about_desc"), color=FG2, size=11, font_family=FONT),
            ], spacing=6),
            padding=20, visible=False,
        )

        copy_feedback = ft.Text("", color=SUCCESS, size=11, font_family=FONT)

        def copy_address(addr):
            def _do(e):
                try:
                    page.set_clipboard(addr)
                    copy_feedback.value = t("support_copied")
                except Exception:
                    copy_feedback.value = addr
                page.update()
            return _do

        wallet_cards = []
        for w in WALLETS:
            card = ft.Container(
                content=ft.Row([
                    ft.Text(w["label"], color=ACCENT, size=12,
                            font_family=FONT, width=130,
                            weight=ft.FontWeight.W_600),
                    ft.Text(w["address"], color=FG, size=11,
                            font_family="Consolas", selectable=True, expand=True),
                    ft.Container(
                        content=ft.Text("📋", size=14),
                        bgcolor=CARD, border_radius=6,
                        padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                        ink=True, on_click=copy_address(w["address"]),
                    ),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=CARD, border_radius=8, padding=10,
            )
            wallet_cards.append(card)

        support_content = ft.Container(
            content=ft.Column([
                ft.Text("💛", size=42, text_align=ft.TextAlign.CENTER),
                ft.Text(t("support_title"), size=18, weight=ft.FontWeight.BOLD,
                        color=FG, font_family=FONT, text_align=ft.TextAlign.CENTER),
                ft.Container(height=8),
                ft.Text(t("support_text"), color=FG2, size=11,
                        font_family=FONT, text_align=ft.TextAlign.CENTER),
                ft.Container(height=16),
                *wallet_cards, ft.Container(height=8), copy_feedback,
            ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20, visible=False,
        )

        tab_btns = {}

        def set_info_tab(name):
            help_content.visible = name == "help"
            about_content.visible = name == "about"
            support_content.visible = name == "support"
            for k, b in tab_btns.items():
                b.content.color = ON_ACCENT if k == name else FG2
                b.bgcolor = ACCENT if k == name else CARD
            page.update()

        def make_tab(key, label):
            b = ft.Container(
                content=ft.Text(label, color=FG2, size=12, font_family=FONT,
                                weight=ft.FontWeight.W_600),
                bgcolor=CARD, border_radius=8,
                padding=ft.Padding.symmetric(vertical=8, horizontal=14),
                ink=True, on_click=lambda e, k=key: set_info_tab(k),
            )
            tab_btns[key] = b
            return b

        def close_info(e=None):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                make_tab("help", t("info_tab_help")),
                make_tab("about", t("info_tab_about")),
                make_tab("support", t("info_tab_support")),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Text("✕", color=FG, size=14,
                                    font_family=FONT, weight=ft.FontWeight.BOLD),
                    bgcolor=CARD, border_radius=8,
                    padding=ft.Padding.symmetric(vertical=6, horizontal=12),
                    ink=True, on_click=close_info,
                ),
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            content=ft.Container(
                content=ft.Column([help_content, about_content, support_content],
                                  spacing=0),
                width=600, height=420,
            ),
            bgcolor=PANEL,
        )
        set_info_tab("help")
        return dlg

    def show_fallback_dialog(current_img, stats):
        dialog_ref = {"dlg": None}

        async def apply_fallback(e=None):
            try:
                dialog_ref["dlg"].open = False
                page.update()

                S["progress_text"].value = t("fb_dialog_progress")
                S["progress_text"].visible = True
                S["progress_bar"].visible = True
                for b in S["buttons"].values():
                    b.disabled = True
                page.update()
                await asyncio.sleep(0.05)

                result = await asyncio.to_thread(
                    smart_correct_fallback, current_img, S["profile"]
                )

                if S["soap_fix_strength"] > 0:
                    result = await asyncio.to_thread(
                        remove_soap_adaptive, result, S["soap_fix_strength"]
                    )
                S["corrected"] = result
                S["last_op"] = "corrected"
                S["preview_image"].src = f"data:image/png;base64,{pil_to_b64(result)}"
                log("", FG2)
                log(t("fb_dialog_applied"), SUCCESS)
                run_check(result, False)
                page.update()
            except Exception as ex:
                log(f"❌ {t('fb_dialog_err')} {ex}", DANGER)
            finally:
                S["progress_bar"].visible = False
                S["progress_text"].visible = False
                if S["buttons"].get("load"): S["buttons"]["load"].disabled = False
                if S["buttons"].get("check"): S["buttons"]["check"].disabled = False
                if S["buttons"].get("fix"): S["buttons"]["fix"].disabled = False
                if S["buttons"].get("save"): S["buttons"]["save"].disabled = (S["corrected"] is None)
                if S["buttons"].get("reset"): S["buttons"]["reset"].disabled = (S["corrected"] is None)
                page.update()

        async def keep_ai(e=None):
            try:
                dialog_ref["dlg"].open = False
                page.update()
                log(t("fb_dialog_kept"), FG2)
                page.update()
            except Exception:
                pass

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(t("fb_dialog_title"), color=FG, size=14),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(t("fb_dialog_text"),
                            color=FG2, size=12, font_family=FONT),
                    ft.Container(height=4),
                    ft.Text(f"  {t('fb_dialog_dark')} {stats['dark_pct']:.2f}%",
                            color=DANGER if stats['dark_pct'] > 5 else SUCCESS,
                            size=12, font_family="Consolas"),
                    ft.Text(f"  {t('fb_dialog_light')} {stats['light_pct']:.2f}%",
                            color=DANGER if stats['light_pct'] > 5 else SUCCESS,
                            size=12, font_family="Consolas"),
                    ft.Container(height=6),
                    ft.Text(t("fb_dialog_question"),
                            color=FG, size=12, font_family=FONT),
                ], spacing=2, tight=True),
                width=380,
                height=140,
            ),
            actions=[
                ft.TextButton(t("fb_dialog_keep_ai"), on_click=keep_ai),
                ft.TextButton(t("fb_dialog_apply"), on_click=apply_fallback),
            ],
            inset_padding=ft.Padding.symmetric(horizontal=80, vertical=120),
            bgcolor=PANEL,
        )
        dialog_ref["dlg"] = dlg
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def open_info(e):
        dlg = create_info_dialog()
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def toggle_lang(e):
        S["lang"] = "en" if S["lang"] == "ru" else "ru"
        rebuild_ui()

    def toggle_mode(e):
        S["ui_mode"] = "advanced" if S["ui_mode"] == "simple" else "simple"
        # Если уходим в Simple — переключаемся на Single если были на Batch/Compress
        if S["ui_mode"] == "simple" and S["active_tab"] in ("batch", "compress"):
            S["active_tab"] = "single"
        rebuild_ui()

    def toggle_theme(e):
        nonlocal BG, PANEL, CARD, INPUT, FG, FG2, FG3, ACCENT, SUCCESS, DANGER, WARN
        nonlocal PBR_COLOR, BATCH_COLOR, COMPRESS_COLOR, SAVE_COLOR, RESET_COLOR

        S["theme"] = "light" if S["theme"] == "dark" else "dark"
        th = THEME_DARK if S["theme"] == "dark" else THEME_LIGHT

        BG = th["bg"]
        PANEL = th["panel"]
        CARD = th["card"]
        INPUT = th["input"]
        FG = th["fg"]
        FG2 = th["fg2"]
        FG3 = th["fg3"]
        ACCENT = th["accent"]
        SUCCESS = th["success"]
        DANGER = th["danger"]
        WARN = th["warn"]
        PBR_COLOR = th["success"]
        BATCH_COLOR = th["warn"]
        COMPRESS_COLOR = "#1565c0" if S["theme"] == "dark" else "#3d6fb8"
        RESET_COLOR = "#555555" if S["theme"] == "dark" else "#9aa0a6"

        page.bgcolor = BG
        page.theme_mode = ft.ThemeMode.DARK if S["theme"] == "dark" else ft.ThemeMode.LIGHT
        rebuild_ui()

    def build_screen():
        is_simple = S["ui_mode"] == "simple"
        buttons = S["buttons"]

        # ═══ SINGLE VIEW ═══
        if is_simple:
            # Simple: одна кнопка + превью + пресеты
            buttons["load"] = make_btn("🚀 " + t("fix"), do_simple_process, SUCCESS)
            buttons["save"] = make_btn(t("save"), open_save, SAVE_COLOR,
                                        disabled=(S["corrected"] is None))

            simple_toolbar = ft.Row([
                buttons["load"],
                ft.Container(expand=True),
                buttons["save"],
            ], spacing=6)

            preview_hint = ft.Text(t("preview_hint"), color=FG3, size=14,
                                    font_family=FONT)

            preview_content = ft.Stack([
                ft.Container(content=preview_hint,
                             alignment=ft.Alignment.CENTER, expand=True),
                ft.Container(content=S["preview_image"],
                             alignment=ft.Alignment.CENTER, expand=True),
            ], expand=True)

            preview_box = ft.Container(
                content=ft.InteractiveViewer(
                    content=preview_content,
                    min_scale=0.5,
                    max_scale=8.0,
                    expand=True,
                ),
                bgcolor=CARD, border_radius=12, padding=10, expand=True,
            )

            right_panel = ft.Container(
                content=ft.Column([
                    ft.Text(t("profile_title"), size=10, weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=6),
                    make_category_tabs(compact=True),
                    ft.Container(height=4),
                    make_preset_grid(compact=False),
                    ft.Container(height=6),
                    ft.Container(
                        content=ft.Text(
                            f"{t('all_types')}: {profile_label(S['profile'])}",
                            color=FG2, size=12, font_family=FONT),
                        bgcolor=INPUT, border_radius=8, padding=10,
                    ),
                ], spacing=4, scroll=ft.ScrollMode.AUTO),
                bgcolor=PANEL, border_radius=12, padding=16, width=250,
            )

            log_panel = ft.Container(
                content=ft.Column([
                    ft.Text(t("log_title"), size=10, weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=4),
                    S["log_column"],
                ], spacing=4, expand=True),
                bgcolor=CARD, border_radius=12, padding=12,
                expand=1,
            )

            single_view = ft.Container(
                content=ft.Column([
                    simple_toolbar,
                    ft.Container(height=4),
                    S["progress_bar"],
                    S["progress_text"],
                    ft.Container(height=6),
                    ft.Container(
                        content=ft.Row([
                            ft.Container(content=preview_box, expand=True),
                            right_panel,
                        ], spacing=12, expand=True),
                        expand=3,
                    ),
                    ft.Container(height=8),
                    log_panel,
                ], spacing=0, expand=True),
                expand=True,
                visible=True,
            )
        else:
            # Advanced — всё как было
            buttons["load"] = make_btn(t("load"), open_file, ACCENT)
            buttons["check"] = make_btn(t("check"), do_check, ACCENT,
                                         disabled=(S["original"] is None))
            buttons["fix"] = make_btn(t("fix"), do_auto_correct, SUCCESS, disabled=True)
            buttons["save"] = make_btn(t("save"), open_save, SAVE_COLOR,
                                        disabled=(S["corrected"] is None))
            buttons["reset"] = make_btn(t("reset"), do_reset, RESET_COLOR,
                                         disabled=(S["corrected"] is None))

            toolbar = ft.Row([
                buttons["load"],
                buttons["check"],
                buttons["fix"],
                ft.Container(expand=True),
                buttons["reset"],
                buttons["save"],
            ], spacing=6)

            preview_hint = ft.Text(t("preview_hint"), color=FG3, size=14,
                                    font_family=FONT)

            preview_content = ft.Stack([
                ft.Container(content=preview_hint,
                             alignment=ft.Alignment.CENTER, expand=True),
                ft.Container(content=S["preview_image"],
                             alignment=ft.Alignment.CENTER, expand=True),
            ], expand=True)

            preview_box = ft.Container(
                content=ft.InteractiveViewer(
                    content=preview_content,
                    min_scale=0.5,
                    max_scale=8.0,
                    expand=True,
                ),
                bgcolor=CARD, border_radius=12, padding=10, expand=True,
            )

            right_panel = ft.Container(
                content=ft.Column([
                    ft.Text(t("profile_title"), size=10, weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=6),
                    make_category_tabs(compact=True),
                    ft.Container(height=4),
                    make_preset_grid(compact=False),
                    ft.Container(height=6),
                    ft.Container(
                        content=ft.Text(
                            f"{t('all_types')}: {profile_label(S['profile'])}",
                            color=FG2, size=12, font_family=FONT),
                        bgcolor=INPUT, border_radius=8, padding=10,
                    ),
                    ft.Container(height=14),
                    ft.Divider(color=FG3, height=1),
                    ft.Container(height=10),
                    ft.Text(t("correction_mode_title"), size=10,
                            weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=6),
                    make_correction_mode_switch(),
                    ft.Container(height=14),
                    ft.Divider(color=FG3, height=1),
                    ft.Container(height=10),
                    make_btn(
                        t("tiling_btn") if not S["tiling_mode"] else t("tiling_btn_off"),
                        toggle_tiling,
                        "#1565c0" if S["theme"] == "dark" else "#3d6fb8",
                    ),
                    ft.Container(height=14),
                    ft.Divider(color=FG3, height=1),
                    ft.Container(height=10),
                    ft.Text(t("soap_fix_title"), size=10,
                            weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=6),
                    ft.Text(t("soap_fix_label"), color=FG2, size=11, font_family=FONT),
                    ft.Slider(
                        min=0.0, max=3.0, divisions=15,
                        value=S["soap_fix_strength"],
                        label="{value}",
                        active_color=ACCENT, inactive_color=INPUT,
                        on_change=lambda e: S.update({"soap_fix_strength": e.control.value}),
                    ),
                    ft.Container(height=4),
                    make_btn(t("soap_fix_button"), do_remove_soap, SAVE_COLOR),
                    ft.Container(height=14),
                    ft.Divider(color=FG3, height=1),
                    ft.Container(height=10),
                    ft.Text(t("sat_title"), size=10,
                            weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=6),
                    ft.Text(t("sat_label"), color=FG2, size=11, font_family=FONT),
                    ft.Slider(
                        min=0.8, max=1.5, divisions=14,
                        value=S["saturation_boost"],
                        label="{value}",
                        active_color=ACCENT, inactive_color=INPUT,
                        on_change=lambda e: S.update({"saturation_boost": e.control.value}),
                    ),
                    ft.Container(height=4),
                    make_btn(t("sat_button"), do_boost_saturation, "#9c27b0" if S["theme"] == "dark" else "#6a1b9a"),
                    ft.Container(height=14),
                    ft.Divider(color=FG3, height=1),
                    ft.Container(height=10),
                    ft.Text(t("stats_title"), size=10, weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=8),
                    S["stats_column"],
                ], spacing=4, scroll=ft.ScrollMode.AUTO),
                bgcolor=PANEL, border_radius=12, padding=16, width=250,
            )

            log_panel = ft.Container(
                content=ft.Column([
                    ft.Text(t("log_title"), size=10, weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=4),
                    S["log_column"],
                ], spacing=4, expand=True),
                bgcolor=CARD, border_radius=12, padding=12,
                expand=1,
            )

            single_view = ft.Container(
                content=ft.Column([
                    toolbar,
                    ft.Container(height=4),
                    S["progress_bar"],
                    S["progress_text"],
                    ft.Container(height=6),
                    ft.Container(
                        content=ft.Row([
                            ft.Container(content=preview_box, expand=True),
                            right_panel,
                        ], spacing=12, expand=True),
                        expand=3,
                    ),
                    ft.Container(height=8),
                    log_panel,
                ], spacing=0, expand=True),
                expand=True,
                visible=True,
            )

        log_panel_pbr = ft.Container(
            content=ft.Column([
                ft.Text(t("log_title"), size=10, weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=4),
                S["log_column_pbr"],
            ], spacing=4, expand=True),
            bgcolor=CARD, border_radius=12, padding=12,
            height=140,
        )

        log_panel_batch = ft.Container(
            content=ft.Column([
                ft.Text(t("log_title"), size=10, weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=4),
                S["log_column_batch"],
            ], spacing=4, expand=True),
            bgcolor=CARD, border_radius=12, padding=12,
            expand=1,
        )

        log_panel_compress = ft.Container(
            content=ft.Column([
                ft.Text(t("log_title"), size=10, weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=4),
                S["log_column_compress"],
            ], spacing=4, expand=True),
            bgcolor=CARD, border_radius=12, padding=12,
            expand=1,
        )

        # ═══ ВКЛАДКА PBR ═══
        pbr_preview = ft.Image(src="", visible=False, fit=ft.BoxFit.CONTAIN)
        S["pbr_preview"] = pbr_preview

        pbr_preview_hint = ft.Text(t("pbr_preview_hint"),
                                     color=FG3, size=14, font_family=FONT)
        S["pbr_preview_hint"] = pbr_preview_hint

        batch_nav_label = ft.Text("", color=FG, size=12, font_family=FONT,
                                   weight=ft.FontWeight.W_600)
        S["pbr_batch_label"] = batch_nav_label

        batch_nav_inner = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text("◀", color=FG, size=14),
                    bgcolor=INPUT, border_radius=6,
                    padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                    ink=True, on_click=lambda e: pbr_batch_prev(),
                ),
                batch_nav_label,
                ft.Container(
                    content=ft.Text("▶", color=FG, size=14),
                    bgcolor=INPUT, border_radius=6,
                    padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                    ink=True, on_click=lambda e: pbr_batch_next(),
                ),
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER,
               tight=True),
            bgcolor=PANEL, border_radius=8, padding=6,
        )

        batch_nav_panel = ft.Container(
            content=ft.Row([batch_nav_inner],
                           alignment=ft.MainAxisAlignment.END),
            visible=len(S["pbr_batch_results"]) > 0,
        )
        S["pbr_batch_nav_panel"] = batch_nav_panel

        pbr_preview_box = ft.Container(
            content=ft.Stack([
                ft.Container(content=pbr_preview_hint,
                             alignment=ft.Alignment.CENTER, expand=True),
                ft.Container(content=pbr_preview,
                             alignment=ft.Alignment.CENTER, expand=True),
                ft.Container(content=batch_nav_panel,
                             alignment=ft.Alignment.BOTTOM_RIGHT,
                             padding=12),
            ], expand=True),
            bgcolor=CARD, border_radius=12, padding=10, expand=True,
        )

        if S["pbr_result"] and S.get("pbr_batch_selected"):
            key = S["pbr_current_map"] if S["pbr_current_map"] in S["pbr_result"] else "albedo"
            if key in S["pbr_result"]:
                pbr_preview.src = f"data:image/png;base64,{pil_to_b64(S['pbr_result'][key])}"
                pbr_preview.visible = True
                pbr_preview_hint.visible = False

        map_buttons = {}
        S["pbr_map_buttons"] = map_buttons
        map_keys = [
            ("albedo", "🎨 Albedo"), ("height", "⛰ Height"),
            ("normal", "📐 Normal"), ("ao", "🌑 AO"),
            ("roughness", "🔧 Rough"), ("metallic", "⚙ Metal"),
            ("edge", "🎯 Edge"), ("orm", "📦 ORM"),
        ]

        def show_pbr_map(key):
            S["pbr_current_map"] = key
            if S["pbr_batch_selected"] and S["pbr_result"] and key in S["pbr_result"]:
                pbr_preview.src = f"data:image/png;base64,{pil_to_b64(S['pbr_result'][key])}"
                pbr_preview.visible = True
            elif key == "albedo":
                if S["pbr_source"] is not None:
                    pbr_preview.src = f"data:image/png;base64,{pil_to_b64(S['pbr_source'])}"
                    pbr_preview.visible = True
                elif S["pbr_result"] and "albedo" in S["pbr_result"]:
                    pbr_preview.src = f"data:image/png;base64,{pil_to_b64(S['pbr_result']['albedo'])}"
                    pbr_preview.visible = True
            else:
                if S["pbr_result"] and key in S["pbr_result"]:
                    pbr_preview.src = f"data:image/png;base64,{pil_to_b64(S['pbr_result'][key])}"
                    pbr_preview.visible = True
            for k, b in map_buttons.items():
                b.bgcolor = ACCENT if k == key else CARD
                b.content.color = ON_ACCENT if k == key else FG2
            page.update()

        map_row = ft.Row([], spacing=4)
        for key, label in map_keys:
            is_active = key == S["pbr_current_map"]
            b = ft.Container(
                content=ft.Text(label, color=ON_ACCENT if is_active else FG2,
                                size=12, font_family=FONT,
                                weight=ft.FontWeight.W_600),
                bgcolor=ACCENT if is_active else CARD,
                border_radius=8,
                padding=ft.Padding.symmetric(vertical=8, horizontal=12),
                expand=True, ink=True,
                on_click=lambda e, k=key: show_pbr_map(k),
            )
            map_buttons[key] = b
            map_row.controls.append(b)

        sliders = {}
        S["pbr_sliders"] = sliders

        def make_pbr_slider(label, key_name, default, minv, maxv, res):
            preset_val = PBR_PRESETS.get(S["profile"], {}).get(key_name, default)
            divisions = max(1, int((maxv - minv) / res))
            var = ft.Slider(min=minv, max=maxv, divisions=divisions,
                            value=preset_val, label="{value}",
                            active_color=PBR_COLOR, inactive_color=INPUT)
            sliders[key_name] = var
            return ft.Column([
                ft.Text(label, color=FG2, size=12, font_family=FONT),
                var,
            ], spacing=2)

        pbr_metal_radio = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="black", label=t("pbr_metal_black"),
                         fill_color=PBR_COLOR),
                ft.Radio(value="white", label=t("pbr_metal_white"),
                         fill_color=PBR_COLOR),
            ]),
            value=PBR_PRESETS.get(S["profile"], {}).get("metallic", S["pbr_metallic"]),
            on_change=lambda e: S.update({"pbr_metallic": e.control.value}),
        )

        pbr_preset_buttons = ft.Column([
            make_category_tabs(compact=True),
            ft.Container(height=4),
            make_preset_grid(compact=True),
        ], spacing=0)

        pbr_bit_radio = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="8", label=t("pbr_bit_8"),
                         fill_color=PBR_COLOR),
                ft.Radio(value="16", label=t("pbr_bit_16"),
                         fill_color=PBR_COLOR),
            ]),
            value=str(S["pbr_bit_depth"]),
            on_change=lambda e: S.update({"pbr_bit_depth": int(e.control.value)}),
        )

        # ═══ PBR PANEL — Simple vs Advanced ═══
        if is_simple:
            pbr_params_panel = ft.Container(
                content=ft.Column([
                    ft.Text(t("pbr_params"), size=10, weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Container(height=6),
                    ft.Text(t("pbr_bit_depth"), color=FG2, size=12, font_family=FONT),
                    pbr_bit_radio,
                ], spacing=6),
                bgcolor=PANEL, border_radius=12, padding=14, width=200,
            )
        else:
            pbr_params_panel = ft.Container(
                content=ft.Column([
                    ft.Text(t("pbr_params"), size=10, weight=ft.FontWeight.BOLD,
                            color=FG3, font_family=FONT),
                    ft.Text(t("pbr_preset_label"), color=FG2, size=11, font_family=FONT),
                    pbr_preset_buttons,
                    ft.Divider(color=FG3, height=1),
                    ft.Text(t("pbr_metallic"), color=FG2, size=12, font_family=FONT),
                    pbr_metal_radio,
                    ft.Divider(color=FG3, height=1),
                    ft.Text(t("pbr_bit_depth"), color=FG2, size=12, font_family=FONT),
                    pbr_bit_radio,
                    ft.Divider(color=FG3, height=1),
                    make_pbr_slider(t("pbr_sl_strength"), "strength", 1.5, 0.1, 5.0, 0.1),
                    make_pbr_slider(t("pbr_sl_smooth"), "smooth", 1.5, 0.0, 5.0, 0.1),
                    make_pbr_slider(t("pbr_sl_threshold"), "threshold", 0.05, 0.0, 0.20, 0.01),
                    make_pbr_slider(t("pbr_sl_high_pass"), "high_pass", 40.0, 0.0, 100.0, 1.0),
                    make_pbr_slider(t("pbr_sl_height_blur"), "height_blur", 2.0, 0.0, 10.0, 0.5),
                    make_pbr_slider(t("pbr_sl_ao_radius"), "ao_radius", 8.0, 2.0, 30.0, 1.0),
                    make_pbr_slider(t("pbr_sl_ao_intensity"), "ao_intensity", 1.5, 0.1, 3.0, 0.1),
                    make_pbr_slider(t("pbr_sl_rough_base"), "rough_base", 0.7, 0.0, 1.0, 0.05),
                    make_pbr_slider(t("pbr_sl_rough_var"), "rough_var", 0.3, 0.0, 1.0, 0.05),
                ], spacing=6, scroll=ft.ScrollMode.AUTO),
                bgcolor=PANEL, border_radius=12, padding=14, width=250,
            )

        if is_simple:
            pbr_simple_btn = make_btn("🚀 " + t("pbr_gen"), pbr_do_simple_generate, SUCCESS)
            pbr_save_btn = make_btn(t("pbr_save"), pbr_do_save, SAVE_COLOR,
                                     disabled=(S["pbr_result"] is None))
            S["pbr_buttons"] = {"save": pbr_save_btn}
            pbr_toolbar = ft.Row([
                pbr_simple_btn,
                ft.Container(expand=True),
                pbr_save_btn,
            ], spacing=6)
        else:
            pbr_load_btn = make_btn(t("pbr_load"), pbr_do_load, ACCENT)
            pbr_gen_btn = make_btn(t("pbr_gen"), pbr_do_generate, SUCCESS,
                                    disabled=(S["pbr_source"] is None))
            pbr_batch_btn = make_btn(t("pbr_batch"), pbr_do_batch, COMPRESS_COLOR)
            pbr_save_btn = make_btn(t("pbr_save"), pbr_do_save, SAVE_COLOR,
                                     disabled=(S["pbr_result"] is None))
            S["pbr_buttons"] = {
                "load": pbr_load_btn, "gen": pbr_gen_btn,
                "batch": pbr_batch_btn, "save": pbr_save_btn,
            }
            pbr_toolbar = ft.Row([
                pbr_load_btn,
                pbr_gen_btn,
                pbr_batch_btn,
                ft.Container(expand=True),
                pbr_save_btn,
            ], spacing=6)

        pbr_view = ft.Container(
            content=ft.Column([
                pbr_toolbar,
                ft.Container(height=4),
                S["pbr_progress_bar"],
                S["pbr_progress_text"],
                ft.Container(height=6),
                map_row,
                ft.Container(height=6),
                ft.Row([
                    ft.Container(content=pbr_preview_box, expand=True),
                    pbr_params_panel,
                ], spacing=12, expand=True),
                ft.Container(height=8),
                log_panel_pbr,
            ], spacing=0, expand=True),
            expand=True, visible=False,
        )

        # ═══ ВКЛАДКА СЖАТИЕ (только Advanced) ═══
        S["compress_preview"] = ft.Image(src="", visible=False, fit=ft.BoxFit.CONTAIN)
        S["compress_preview_hint"] = ft.Text(t("preview_hint"),
                                              color=FG3, size=14, font_family=FONT)

        compress_preview_box = ft.Container(
            content=ft.Stack([
                ft.Container(content=S["compress_preview_hint"],
                             alignment=ft.Alignment.CENTER, expand=True),
                ft.Container(content=S["compress_preview"],
                             alignment=ft.Alignment.CENTER, expand=True),
            ], expand=True),
            bgcolor=CARD, border_radius=12, padding=10, expand=True,
        )

        compress_open_btn = make_btn(t("load"), compress_open_file, ACCENT)
        compress_run_btn = make_btn(t("compress_run"), compress_do, COMPRESS_COLOR,
                                     disabled=True)
        compress_save_btn = make_btn(t("save"), compress_save, SAVE_COLOR,
                                      disabled=True)
        S["compress_buttons"] = {
            "open": compress_open_btn,
            "run": compress_run_btn,
            "save": compress_save_btn,
        }

        compress_single_toolbar = ft.Row([
            compress_open_btn,
            compress_run_btn,
            ft.Container(expand=True),
            compress_save_btn,
        ], spacing=6)

        compress_single_card = ft.Container(
            content=ft.Column([
                ft.Text(t("compress_single"), size=10, weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=6),
                compress_single_toolbar,
                ft.Container(height=8),
                ft.Container(
                    content=ft.Row([
                        ft.Container(content=compress_preview_box, expand=True),
                    ], expand=True),
                    expand=True,
                ),
            ], spacing=0, expand=True),
            bgcolor=PANEL, border_radius=12, padding=16, expand=True,
        )

        compress_sel_row = ft.Row([
            make_btn(t("batch_select_folder"), compress_select_folder, ACCENT),
            make_btn(t("batch_select_files"), compress_select_files, ACCENT),
            ft.Container(expand=True),
            make_btn(t("compress_batch_run"), compress_batch_run, COMPRESS_COLOR),
        ], spacing=6)

        compress_batch_card = ft.Container(
            content=ft.Column([
                ft.Text(t("compress_batch"), size=10, weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=6),
                compress_sel_row,
            ], spacing=6),
            bgcolor=PANEL, border_radius=12, padding=16,
        )

        compress_view = ft.Container(
            content=ft.Column([
                S["compress_progress_bar"],
                S["compress_progress_text"],
                ft.Container(height=6),
                compress_single_card,
                ft.Container(height=8),
                compress_batch_card,
                ft.Container(height=8),
                log_panel_compress,
            ], spacing=0, expand=True),
            expand=True, visible=False,
        )

        # ═══ ВКЛАДКА ПАКЕТНАЯ (только Advanced) ═══
        batch_sel_row = ft.Row([
            make_btn(t("batch_select_folder"), batch_select_folder, ACCENT),
            make_btn(t("batch_select_files"), batch_select_files, ACCENT),
        ], spacing=6)

        batch_run_btn = make_btn(t("batch_run"), batch_run, SUCCESS)

        batch_info_card = ft.Container(
            content=ft.Column([
                ft.Text("✨ AI-коррекция папки", size=10,
                        weight=ft.FontWeight.BOLD,
                        color=FG3, font_family=FONT),
                ft.Container(height=6),
                ft.Text(t("batch_no_files"), color=FG3, size=11, visible=False),
            ], spacing=6),
            bgcolor=PANEL, border_radius=12, padding=16,
        )

        batch_view = ft.Container(
            content=ft.Column([
                batch_sel_row,
                ft.Container(height=8),
                batch_info_card,
                ft.Container(height=8),
                batch_run_btn,
                ft.Container(height=8),
                S["batch_progress_bar"],
                S["batch_progress_text"],
                ft.Container(height=8),
                log_panel_batch,
            ], spacing=0, expand=True),
            expand=True, visible=False,
        )

        tab_btns_local = {}

        def set_tab(name):
            S["active_tab"] = name
            for k, c in tab_btns_local.items():
                c.bgcolor = ACCENT if k == name else CARD
                c.content.color = ON_ACCENT if k == name else FG
            single_view.visible = name == "single"
            pbr_view.visible = name == "pbr"
            if not is_simple:
                compress_view.visible = name == "compress"
                batch_view.visible = name == "batch"
            page.update()

        def make_tab(key, label):
            c = ft.Container(
                content=ft.Text(label, color=ON_ACCENT, size=14, font_family=FONT,
                                weight=ft.FontWeight.W_600),
                bgcolor=ACCENT if key == "single" else CARD,
                border_radius=10,
                padding=ft.Padding.symmetric(vertical=12, horizontal=24),
                ink=True, on_click=lambda e, k=key: set_tab(k),
            )
            tab_btns_local[key] = c
            return c

        if is_simple:
            tabs_row = ft.Row([
                make_tab("single", t("tab_single")),
                make_tab("pbr", t("tab_pbr")),
            ], spacing=8)
        else:
            tabs_row = ft.Row([
                make_tab("single", t("tab_single")),
                make_tab("batch", t("tab_batch")),
                make_tab("pbr", t("tab_pbr")),
                make_tab("compress", t("tab_compress")),
            ], spacing=8)

        set_tab(S["active_tab"])

        theme_icon = "☀" if S["theme"] == "dark" else "🌙"
        mode_label = t("mode_btn_advanced") if is_simple else t("mode_btn_simple")

        header = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Row([
                        ft.Text("◐ Albedolizer", size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ACCENT, font_family=FONT),
                        ft.Container(
                            content=ft.Text("v1.3.3-beta", size=10, color=FG2,
                                            font_family=FONT,
                                            weight=ft.FontWeight.W_600),
                            bgcolor=CARD, border_radius=6,
                            padding=ft.Padding.symmetric(vertical=2, horizontal=8),
                        ),
                    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Text(t("subtitle"), size=11, color=FG2, font_family=FONT),
                ], spacing=2),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Text(mode_label, color=FG, size=13,
                                    font_family=FONT, weight=ft.FontWeight.W_600),
                    bgcolor=CARD, border_radius=8,
                    padding=ft.Padding.symmetric(vertical=10, horizontal=16),
                    ink=True, on_click=toggle_mode,
                ),
                ft.Container(width=8),
                ft.Container(
                    content=ft.Text(theme_icon, color=FG, size=14,
                                    font_family=FONT),
                    bgcolor=CARD, border_radius=8,
                    padding=ft.Padding.symmetric(vertical=10, horizontal=16),
                    ink=True, on_click=toggle_theme,
                    tooltip="Toggle theme",
                ),
                ft.Container(width=8),
                ft.Container(
                    content=ft.Text(t("lang_btn"), color=FG, size=13,
                                    font_family=FONT, weight=ft.FontWeight.W_600),
                    bgcolor=CARD, border_radius=8,
                    padding=ft.Padding.symmetric(vertical=10, horizontal=16),
                    ink=True, on_click=toggle_lang,
                ),
                ft.Container(width=8),
                ft.Container(
                    content=ft.Text(t("info_btn"), color=FG, size=13,
                                    font_family=FONT, weight=ft.FontWeight.W_600),
                    bgcolor=CARD, border_radius=8,
                    padding=ft.Padding.symmetric(vertical=10, horizontal=16),
                    ink=True, on_click=open_info,
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(vertical=14, horizontal=24),
            bgcolor=PANEL,
        )

        if is_simple:
            views_stack = ft.Stack([single_view, pbr_view], expand=True)
        else:
            views_stack = ft.Stack([single_view, pbr_view, compress_view, batch_view],
                                    expand=True)

        body = ft.Container(
            content=ft.Column([
                ft.Container(height=12),
                tabs_row,
                ft.Container(height=12),
                ft.Container(content=views_stack, expand=True),
            ], spacing=0, expand=True),
            padding=ft.Padding.symmetric(horizontal=24),
            expand=True,
        )

        page.add(
            ft.Column([header, body], spacing=0, expand=True)
        )

    def rebuild_ui():
        page.controls.clear()
        build_screen()
        page.update()

    build_screen()
    log(t("welcome_1"), FG2)
    log(t("welcome_2"), FG2)
    page.update()


if __name__ == "__main__":
    ft.run(main)