"""
clip_model.py — классификатор материалов через CLIP (ONNX).
Использует OpenAI CLIP ViT-B/32 + zero-shot classification.
"""
import sys
import os
import numpy as np
import onnxruntime as ort
from PIL import Image


# ═══════════════════════════════════════════════════════════
#  ПРОМПТЫ ДЛЯ КЛАССОВ
# ═══════════════════════════════════════════════════════════
# Формат: profile_key → [список промптов]
# CLIP усредняет эмбеддинги всех промптов класса.
# Все промпты — с единым PBR-префиксом для стабильности.
CLASS_PROMPTS = {
    # 🔥 METAL
    "metal": [
        "a close-up PBR albedo texture of bare metal",
        "a seamless metal surface texture",
        "a tileable brushed steel texture",
        "a flat metal albedo without shadows",
        "an industrial metal plate texture",
        "a polished metal surface texture",
        "a close-up of a generic metal material",
        "a grayscale metal albedo map",
    ],
    "rust": [
        "a close-up PBR albedo texture of rusty metal",
        "a seamless rusted iron surface",
        "a tileable corroded metal texture",
        "an orange rust albedo map",
        "a close-up of heavy rust on steel",
        "a weathered rusty iron plate",
    ],
    "oxidized_metal": [
        "a close-up PBR albedo texture of oxidized metal",
        "a seamless oxidized copper surface",
        "a tileable weathered metal texture",
        "a green-tinted oxidized metal albedo",
        "a close-up of oxidized aluminum",
    ],
    "patina": [
        "a close-up PBR albedo texture of patina",
        "a seamless verdigris patina surface",
        "a tileable aged copper patina texture",
        "a green patina on bronze albedo",
        "a close-up of turquoise patina",
    ],
    "brass": [
        "a close-up PBR albedo texture of brass",
        "a seamless polished brass surface",
        "a tileable golden brass texture",
        "a yellow-gold brass metal albedo",
        "a close-up of aged brass",
    ],
    "aluminum": [
        "a close-up PBR albedo texture of aluminum",
        "a seamless brushed aluminum surface",
        "a tileable silver aluminum texture",
        "a light gray metal albedo map",
        "a close-up of polished aluminum",
    ],
    "copper": [
        "a close-up PBR albedo texture of copper",
        "a seamless polished copper surface",
        "a tileable reddish copper texture",
        "an orange-brown copper metal albedo",
        "a close-up of raw copper plate",
    ],
    # 🌿 NATURE
    "wood": [
        "a close-up PBR albedo texture of wood",
        "a seamless wooden plank surface",
        "a tileable oak wood texture",
        "a natural wood grain albedo map",
        "a brown wooden surface texture",
        "a close-up of polished wood",
        "a flat wood albedo without shadows",
    ],
    "leaves": [
        "a close-up PBR albedo texture of leaves",
        "a seamless green leaf surface",
        "a tileable foliage texture",
        "a close-up of plant leaves",
        "a green leafy albedo map",
    ],
    "moss": [
        "a close-up PBR albedo texture of moss",
        "a seamless green moss surface",
        "a tileable mossy texture",
        "a soft green moss albedo",
        "a close-up of dense moss",
    ],
    "organic": [
        "a close-up PBR albedo texture of organic material",
        "a seamless natural organic surface",
        "a tileable decomposing matter texture",
        "a brown organic albedo map",
        "a close-up of soil and organic debris",
    ],
    "grass": [
        "a close-up PBR albedo texture of grass",
        "a seamless green grass surface",
        "a tileable lawn grass texture",
        "a close-up of dense grass blades",
        "a green grass albedo map",
    ],
    "bark": [
        "a close-up PBR albedo texture of tree bark",
        "a seamless bark surface",
        "a tileable rough tree bark texture",
        "a brown bark albedo map",
        "a close-up of deep bark grooves",
    ],
    # 🪨 MINERAL
    "tile": [
        "a close-up PBR albedo texture of a ceramic tile",
        "a seamless glazed floor tile surface",
        "a tileable ceramic tile texture",
        "a polished tile albedo map",
        "a close-up of a tiled floor",
    ],
    "gravel": [
        "a close-up PBR albedo texture of gravel",
        "a seamless small stones surface",
        "a tileable gravel texture",
        "a close-up of loose gravel",
        "a gray gravel albedo map",
    ],
    "coal": [
        "a close-up PBR albedo texture of coal",
        "a seamless black coal surface",
        "a tileable coal texture",
        "a close-up of raw coal chunks",
        "a black coal albedo map",
    ],
    "roof_tiles": [
        "a close-up PBR albedo texture of roof tiles",
        "a seamless red roof tiles surface",
        "a tileable clay roof tile texture",
        "a close-up of terracotta roof tiles",
        "a red roof tile albedo map",
    ],
    "stone": [
        "a close-up PBR albedo texture of stone",
        "a seamless natural stone surface",
        "a tileable rock texture",
        "a gray stone wall albedo",
        "a close-up of rough stone",
        "a flat stone albedo without shadows",
    ],
    "concrete": [
        "a close-up PBR albedo texture of concrete",
        "a seamless concrete wall surface",
        "a tileable raw concrete texture",
        "a gray concrete albedo map",
        "a close-up of smooth concrete",
    ],
    "brick": [
        "a close-up PBR albedo texture of a brick wall",
        "a seamless red brick surface",
        "a tileable brick texture",
        "a close-up of weathered bricks",
        "a red brick albedo map",
    ],
    "ground": [
        "a close-up PBR albedo texture of ground soil",
        "a seamless dirt surface",
        "a tileable earth ground texture",
        "a brown soil albedo map",
        "a close-up of dry dirt",
    ],
    "asphalt": [
        "a close-up PBR albedo texture of asphalt",
        "a seamless asphalt road surface",
        "a tileable black asphalt texture",
        "a close-up of rough asphalt",
        "a dark gray asphalt albedo map",
    ],
    "marble": [
        "a close-up PBR albedo texture of marble",
        "a seamless white marble surface",
        "a tileable veined marble texture",
        "a polished marble albedo map",
        "a close-up of marble veins",
    ],
    "sand": [
        "a close-up PBR albedo texture of sand",
        "a seamless beach sand surface",
        "a tileable fine sand texture",
        "a beige sand albedo map",
        "a close-up of rippled sand",
    ],
    "clay": [
        "a close-up PBR albedo texture of clay",
        "a seamless natural clay surface",
        "a tileable brown clay texture",
        "a close-up of raw clay",
        "a reddish clay albedo map",
    ],
    "granite": [
        "a close-up PBR albedo texture of granite",
        "a seamless speckled granite surface",
        "a tileable granite stone texture",
        "a close-up of polished granite",
        "a gray granite albedo map",
    ],
    # 🧪 SYNTHETIC
    "plastic": [
        "a close-up PBR albedo texture of plastic",
        "a seamless smooth plastic surface",
        "a tileable colored plastic texture",
        "a glossy plastic albedo map",
        "a close-up of matte plastic",
    ],
    "rubber": [
        "a close-up PBR albedo texture of rubber",
        "a seamless black rubber surface",
        "a tileable rubber mat texture",
        "a matte rubber albedo map",
        "a close-up of textured rubber",
    ],
    "glass": [
        "a close-up PBR albedo texture of glass",
        "a seamless transparent glass surface",
        "a tileable glass panel texture",
        "a frosted glass albedo map",
        "a close-up of reflective glass",
    ],
    "ceramic": [
        "a close-up PBR albedo texture of ceramic",
        "a seamless glazed ceramic surface",
        "a tileable ceramic texture",
        "a glossy ceramic albedo map",
        "a close-up of porcelain ceramic",
    ],
    "painted_metal": [
        "a close-up PBR albedo texture of painted metal",
        "a seamless colored painted metal surface",
        "a tileable car paint texture",
        "a glossy painted metal albedo",
        "a close-up of chipped paint on metal",
    ],
    "carbon": [
        "a close-up PBR albedo texture of carbon fiber",
        "a seamless black carbon fiber surface",
        "a tileable carbon fiber weave texture",
        "a glossy carbon fiber albedo map",
        "a close-up of carbon fiber pattern",
    ],
    # 🧵 FABRIC
    "cotton": [
        "a close-up PBR albedo texture of cotton fabric",
        "a seamless white cotton cloth surface",
        "a tileable cotton textile texture",
        "a soft cotton albedo map",
        "a close-up of woven cotton",
    ],
    "wool": [
        "a close-up PBR albedo texture of wool fabric",
        "a seamless woolen cloth surface",
        "a tileable fuzzy wool texture",
        "a soft wool albedo map",
        "a close-up of knitted wool",
    ],
    "silk": [
        "a close-up PBR albedo texture of silk fabric",
        "a seamless shiny silk cloth surface",
        "a tileable smooth silk texture",
        "a glossy silk albedo map",
        "a close-up of flowing silk",
    ],
    "denim": [
        "a close-up PBR albedo texture of denim fabric",
        "a seamless blue jeans surface",
        "a tileable denim cloth texture",
        "a blue denim albedo map",
        "a close-up of woven denim",
    ],
    "carpet": [
        "a close-up PBR albedo texture of carpet",
        "a seamless fuzzy carpet surface",
        "a tileable woven carpet texture",
        "a soft carpet albedo map",
        "a close-up of thick carpet pile",
    ],
    "velvet": [
        "a close-up PBR albedo texture of velvet",
        "a seamless soft velvet surface",
        "a tileable velvet cloth texture",
        "a plush velvet albedo map",
        "a close-up of crushed velvet",
    ],
    # 💧 SPECIAL
    "water": [
        "a close-up PBR albedo texture of water",
        "a seamless clear water surface",
        "a tileable water ripples texture",
        "a blue water albedo map",
        "a close-up of calm water",
    ],
    "mud": [
        "a close-up PBR albedo texture of mud",
        "a seamless wet mud surface",
        "a tileable brown mud texture",
        "a dark mud albedo map",
        "a close-up of cracked mud",
    ],
    "snow": [
        "a close-up PBR albedo texture of snow",
        "a seamless white snow surface",
        "a tileable fresh snow texture",
        "a bright snow albedo map",
        "a close-up of powdery snow",
    ],
    "ice": [
        "a close-up PBR albedo texture of ice",
        "a seamless frozen ice surface",
        "a tileable icy texture",
        "a blue-white ice albedo map",
        "a close-up of cracked ice",
    ],
    # 🐾 FAUNA
    "leather": [
        "a close-up PBR albedo texture of leather",
        "a seamless brown leather surface",
        "a tileable animal leather texture",
        "a natural leather albedo map",
        "a close-up of aged leather",
    ],
    "fur": [
        "a close-up PBR albedo texture of fur",
        "a seamless animal fur surface",
        "a tileable furry texture",
        "a soft fur albedo map",
        "a close-up of dense fur",
    ],
    "skin": [
        "a close-up PBR albedo texture of human skin",
        "a seamless skin surface",
        "a tileable skin texture",
        "a natural skin albedo map",
        "a close-up of skin pores",
    ],
    "scales": [
        "a close-up PBR albedo texture of scales",
        "a seamless reptile scales surface",
        "a tileable fish scales texture",
        "a shiny scales albedo map",
        "a close-up of overlapping scales",
    ],
    "bone": [
        "a close-up PBR albedo texture of bone",
        "a seamless animal bone surface",
        "a tileable white bone texture",
        "a natural bone albedo map",
        "a close-up of dried bone",
    ],
}


# ═══════════════════════════════════════════════════════════
#  КЛАССИФИКАТОР
# ═══════════════════════════════════════════════════════════
class CLIPMaterialClassifier:
    """CLIP zero-shot классификатор материалов. Singleton."""
    
    _instance = None
    _vision_session = None
    _text_session = None
    _tokenizer = None
    _text_embeds = None
    _class_keys = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load(self, vision_path, text_path):
        """Загружает ONNX-модели и токенайзер, кэширует text embeddings."""
        if self._vision_session is not None:
            return True
        
        if not (os.path.exists(vision_path) and os.path.exists(text_path)):
            return False
        
        try:
            # ONNX сессии
            self._vision_session = ort.InferenceSession(
                vision_path, providers=['CPUExecutionProvider']
            )
            self._text_session = ort.InferenceSession(
                text_path, providers=['CPUExecutionProvider']
            )
            
            # Токенайзер CLIP — локальный (рядом с exe)
            from transformers import CLIPTokenizer
            import os as _os
            if getattr(sys, 'frozen', False):
                # В exe-режиме ищем СНАЧАЛА рядом с exe, потом в _MEIPASS
                _exe_dir = _os.path.dirname(sys.executable)
                _meipass = getattr(sys, '_MEIPASS', None)
                if _os.path.exists(_os.path.join(_exe_dir, "clip_tokenizer")):
                    _base = _exe_dir
                elif _meipass and _os.path.exists(_os.path.join(_meipass, "clip_tokenizer")):
                    _base = _meipass
                else:
                    _base = _exe_dir  # fallback
            else:
                _base = _os.path.dirname(_os.path.abspath(__file__))
            _tok_dir = _os.path.join(_base, "clip_tokenizer")
            self._tokenizer = CLIPTokenizer.from_pretrained(_tok_dir)
            
            # Собираем все промпты плоским списком
            self._class_keys = list(CLASS_PROMPTS.keys())
            all_prompts = []
            prompts_per_class = []
            for key in self._class_keys:
                prompts = CLASS_PROMPTS[key]
                prompts_per_class.append(len(prompts))
                all_prompts.extend(prompts)
            
            # Токенизация
            text_inputs = self._tokenizer(
                all_prompts,
                padding="max_length",
                max_length=77,
                truncation=True,
                return_tensors="np"
            )
            
            # Text embeddings
            text_embeds = self._text_session.run(None, {
                "input_ids": text_inputs["input_ids"].astype(np.int64),
                "attention_mask": text_inputs["attention_mask"].astype(np.int64),
            })[0]
            
            # Нормализация
            text_embeds = text_embeds / np.linalg.norm(text_embeds, axis=-1, keepdims=True)
            
            # Усредняем эмбеддинги внутри каждого класса
            class_embeds = []
            idx = 0
            for n in prompts_per_class:
                class_embeds.append(text_embeds[idx:idx+n].mean(axis=0))
                idx += n
            
            class_embeds = np.stack(class_embeds)
            class_embeds = class_embeds / np.linalg.norm(class_embeds, axis=-1, keepdims=True)
            self._text_embeds = class_embeds
            
            return True
        except Exception as e:
            print(f"⚠ CLIP load error: {e}")
            self._vision_session = None
            return False
    
    def is_loaded(self):
        return self._vision_session is not None
    
    def classify(self, pil):
        """
        Классифицирует изображение.
        Возвращает: (profile_key, confidence, top5_list)
        где top5_list = [(profile_key, confidence), ...]
        """
        if self._vision_session is None:
            return None, 0.0, []
        
        try:
            # Препроцессинг
            img = pil.convert("RGB").resize((224, 224), Image.BICUBIC)
            arr = np.array(img).astype(np.float32) / 255.0
            mean = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
            std = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)
            arr = (arr - mean) / std
            arr = arr.transpose(2, 0, 1)[None, ...]
            
            # Image embedding
            image_embeds = self._vision_session.run(None, {"pixel_values": arr})[0]
            image_embeds = image_embeds / np.linalg.norm(image_embeds, axis=-1, keepdims=True)
            
            # Similarity
            similarities = (image_embeds @ self._text_embeds.T)[0]
            logits = similarities * 100.0
            exp_logits = np.exp(logits - np.max(logits))
            probs = exp_logits / exp_logits.sum()
            
            # Top-5
            top5_idx = np.argsort(probs)[::-1][:5]
            top5 = [(self._class_keys[i], float(probs[i])) for i in top5_idx]
            
            return self._class_keys[top5_idx[0]], float(probs[top5_idx[0]]), top5
        except Exception as e:
            print(f"⚠ CLIP classify error: {e}")
            return None, 0.0, []