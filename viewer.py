"""
viewer.py — PBR 3D viewer для Albedolizer.
Отдельное OpenGL-окно через moderngl + glfw.
v1.7.6: Normal + AO + Height (parallax offset), RU/EN/ZH.
"""

import os
import sys
import time
import argparse
import math
import ctypes
import numpy as np
import moderngl
import glfw
from PIL import Image

from imgui_bundle import imgui


# ═══════════════════════════════════════════════════════════
#  ШЕЙДЕРЫ
# ═══════════════════════════════════════════════════════════

VERTEX_SHADER = """
#version 330

in vec3 in_position;
in vec3 in_normal;
in vec2 in_uv;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;

out vec3 v_world_pos;
out vec3 v_normal;
out vec2 v_uv;

void main() {
    vec4 world = m_model * vec4(in_position, 1.0);
    v_world_pos = world.xyz;
    v_normal = mat3(m_model) * in_normal;
    v_uv = in_uv;
    gl_Position = m_proj * m_view * world;
}
"""

FRAGMENT_SHADER = """
#version 330

in vec3 v_world_pos;
in vec3 v_normal;
in vec2 v_uv;

uniform sampler2D u_albedo;
uniform sampler2D u_normal;
uniform sampler2D u_roughness;
uniform sampler2D u_metallic;
uniform sampler2D u_ao;
uniform sampler2D u_height;
uniform sampler2D u_env;
uniform sampler2D u_env_blur;

uniform vec3 u_cam_pos;
uniform float u_exposure;
uniform float u_tile_x;
uniform float u_tile_y;
uniform int u_has_normal;
uniform int u_has_ao;
uniform int u_has_height;
uniform float u_parallax_strength;

out vec4 frag_color;

const float PI = 3.14159265359;

// ═══ Mapping direction to equirect UV ═══
vec2 dir_to_uv(vec3 dir) {
    float u = atan(dir.z, dir.x) / (2.0 * PI) + 0.5;
    float v = acos(clamp(dir.y, -1.0, 1.0)) / PI;
    return vec2(u, v);
}

vec3 sample_env(vec3 dir) {
    return texture(u_env, dir_to_uv(dir)).rgb;
}

vec3 sample_env_blur(vec3 dir) {
    return texture(u_env_blur, dir_to_uv(dir)).rgb;
}

// ═══ Simple parallax offset ═══
// Смещает UV в зависимости от height и направления взгляда (в tangent space).
vec2 parallax_offset(vec2 uv, vec3 V_ts, float strength) {
    if (u_has_height == 0 || strength <= 0.0) {
        return uv;
    }
    // V_ts: направление взгляда в tangent space (упрощённо)
    // Многократный sample для сглаживания
    float h = texture(u_height, uv).r;
    // Смещение по V_ts.xy * (h - 0.5) * strength
    vec2 offset = V_ts.xy * (h - 0.5) * strength * 0.05;
    return uv - offset;
}

// ═══ Применение normal map ═══
vec3 apply_normal_map(vec3 N, vec2 uv, vec3 world_pos, sampler2D tex) {
    vec3 n = texture(tex, uv).rgb * 2.0 - 1.0;
    vec3 dp1 = dFdx(world_pos);
    vec3 dp2 = dFdy(world_pos);
    vec2 duv1 = dFdx(uv);
    vec2 duv2 = dFdy(uv);

    vec3 T = normalize(dp1 * duv2.y - dp2 * duv1.y);
    vec3 B = normalize(cross(N, T));
    if (length(T) < 0.001 || length(B) < 0.001) {
        return N;
    }
    mat3 TBN = mat3(T, B, N);
    return normalize(TBN * n);
}

// ═══ BRDF ═══
float DistributionGGX(vec3 N, vec3 H, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float NdotH = max(dot(N, H), 0.0);
    float NdotH2 = NdotH * NdotH;

    float nom = a2;
    float denom = (NdotH2 * (a2 - 1.0) + 1.0);
    denom = PI * denom * denom;

    return nom / max(denom, 0.0001);
}

float GeometrySchlickGGX(float NdotV, float roughness) {
    float r = (roughness + 1.0);
    float k = (r * r) / 8.0;

    float nom = NdotV;
    float denom = NdotV * (1.0 - k) + k;

    return nom / max(denom, 0.0001);
}

float GeometrySmith(vec3 N, vec3 V, vec3 L, float roughness) {
    float NdotV = max(dot(N, V), 0.0);
    float NdotL = max(dot(N, L), 0.0);
    float ggx2 = GeometrySchlickGGX(NdotV, roughness);
    float ggx1 = GeometrySchlickGGX(NdotL, roughness);

    return ggx1 * ggx2;
}

vec3 fresnelSchlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

vec3 fresnelSchlickRoughness(float cosTheta, vec3 F0, float roughness) {
    return F0 + (max(vec3(1.0 - roughness), F0) - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

// ═══ Три источника света ═══
const vec3 KEY_DIR   = normalize(vec3(-0.6, 0.8, 0.5));
const vec3 KEY_COLOR = vec3(1.6, 1.55, 1.45);

const vec3 FILL_DIR   = normalize(vec3(0.7, -0.3, 0.4));
const vec3 FILL_COLOR = vec3(0.20, 0.24, 0.32);

const vec3 RIM_DIR   = normalize(vec3(0.3, 0.6, -0.9));
const vec3 RIM_COLOR = vec3(0.55, 0.60, 0.65);


vec3 direct_light(vec3 N, vec3 V, vec3 L, vec3 light_color,
                  vec3 albedo, vec3 F0, float roughness, float metallic) {
    vec3 H = normalize(V + L);
    float NdotL = max(dot(N, L), 0.0);
    if (NdotL <= 0.0) return vec3(0.0);
    float NdotV = max(dot(N, V), 0.0);

    float D = DistributionGGX(N, H, roughness);
    float G = GeometrySmith(N, V, L, roughness);
    vec3 F = fresnelSchlick(max(dot(H, V), 0.0), F0);

    vec3 numerator = D * G * F;
    float denominator = 4.0 * max(NdotV, 0.001) * NdotL;
    vec3 specular = numerator / max(denominator, 0.001);

    vec3 kS = F;
    vec3 kD = (vec3(1.0) - kS) * (1.0 - metallic);

    return (kD * albedo / PI + specular) * light_color * NdotL;
}

vec3 aces_tonemap(vec3 x) {
    const float a = 2.51;
    const float b = 0.03;
    const float c = 2.43;
    const float d = 0.59;
    const float e = 0.14;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}


void main() {
    // Базовые UV с тайлингом
    vec2 uv = vec2(v_uv.x * u_tile_x, v_uv.y * u_tile_y);

    // Двусторонние нормали
    vec3 Ng = normalize(v_normal);
    if (!gl_FrontFacing) {
        Ng = -Ng;
    }

    // Простой tangent space для параллакса (производные)
    vec3 V = normalize(u_cam_pos - v_world_pos);

    // Простой parallax: смещение UV по направлению взгляда в плоскости поверхности
    if (u_has_height == 1 && u_parallax_strength > 0.0) {
        // Упрощённый tangent: используем производные UV
        vec3 dp1 = dFdx(v_world_pos);
        vec3 dp2 = dFdy(v_world_pos);
        vec2 duv1 = dFdx(uv);
        vec2 duv2 = dFdy(uv);

        vec3 T = normalize(dp1 * duv2.y - dp2 * duv1.y);
        vec3 B = normalize(cross(Ng, T));

        // V в tangent space
        vec3 V_ts = vec3(dot(V, T), dot(V, B), dot(V, Ng));

        // Один шаг parallax offset
        float h = texture(u_height, uv).r;
        vec2 offset = V_ts.xy / max(abs(V_ts.z), 0.001) * (h - 0.5) * u_parallax_strength * 0.05;
        uv -= offset;
    }

    vec3 albedo = texture(u_albedo, uv).rgb;

    vec3 N = Ng;
    if (u_has_normal == 1) {
        N = apply_normal_map(N, uv, v_world_pos, u_normal);
    }

    vec3 R = reflect(-V, N);

    float roughness = clamp(texture(u_roughness, uv).r, 0.05, 1.0);
    float metallic = clamp(texture(u_metallic, uv).r, 0.0, 1.0);
    float ao = (u_has_ao == 1) ? texture(u_ao, uv).r : 1.0;

    vec3 F0 = vec3(0.04);
    F0 = mix(F0, albedo, metallic);

    // ═══ Прямой свет ═══
    vec3 Lo = vec3(0.0);
    Lo += direct_light(N, V, KEY_DIR,  KEY_COLOR,  albedo, F0, roughness, metallic);
    Lo += direct_light(N, V, FILL_DIR, FILL_COLOR, albedo, F0, roughness, metallic);
    Lo += direct_light(N, V, RIM_DIR,  RIM_COLOR,  albedo, F0, roughness, metallic);

    // ═══ Rim light ═══
    float rim = pow(1.0 - max(dot(N, V), 0.0), 4.0);
    vec3 rim_color = vec3(0.15, 0.17, 0.20) * rim * 0.3;

    // ═══ IBL ═══
    float NdotV = max(dot(N, V), 0.0);
    vec3 F_ibl = fresnelSchlickRoughness(NdotV, F0, roughness);
    vec3 kS_ibl = F_ibl;
    vec3 kD_ibl = (vec3(1.0) - kS_ibl) * (1.0 - metallic);

    vec3 irradiance = sample_env_blur(N);

    vec3 reflection_env = mix(sample_env_blur(R), sample_env(R), metallic);

    vec3 diffuse_ibl = irradiance * albedo * kD_ibl;
    vec3 specular_ibl = reflection_env * F_ibl * (metallic * 8.0 + (1.0 - metallic) * 0.05) * (1.0 - roughness * 0.5);

    vec3 ambient = (diffuse_ibl * 0.22 + specular_ibl * 0.45) * ao;

    vec3 color = Lo + ambient + rim_color;

    color *= u_exposure;
    color = aces_tonemap(color);
    color = pow(max(color, vec3(0.0)), vec3(1.0 / 2.2));

    frag_color = vec4(color, 1.0);
}
"""


# ═══════════════════════════════════════════════════════════
#  ГЕОМЕТРИЯ
# ═══════════════════════════════════════════════════════════

def create_sphere(radius=0.5, segments=64, rings=64):
    cols = segments + 1
    verts = []
    for ring in range(rings + 1):
        phi = math.pi * ring / rings
        for seg in range(cols):
            theta = 2.0 * math.pi * seg / segments
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.cos(phi)
            z = radius * math.sin(phi) * math.sin(theta)
            nx, ny, nz = x / radius, y / radius, z / radius
            u = seg / segments
            v = 1.0 - ring / rings
            verts.append((x, y, z, nx, ny, nz, u, v))

    idx = []
    for ring in range(rings):
        for seg in range(segments):
            a = ring * cols + seg
            b = a + cols
            a_next = a + 1
            b_next = b + 1
            idx.extend([a, b, a_next])
            idx.extend([a_next, b, b_next])
    return np.array(verts, dtype='f4'), np.array(idx, dtype='i4')


def create_cylinder(radius=0.5, height=1.0, segments=64):
    verts = []
    idx = []
    half_h = height * 0.5

    side_start = 0
    for seg in range(segments + 1):
        theta = 2.0 * math.pi * seg / segments
        x = radius * math.cos(theta)
        z = radius * math.sin(theta)
        nx, nz = math.cos(theta), math.sin(theta)
        u = seg / segments
        verts.append((x, -half_h, z, nx, 0.0, nz, u, 0.0))
        verts.append((x,  half_h, z, nx, 0.0, nz, u, 1.0))

    for seg in range(segments):
        a = side_start + seg * 2
        b = a + 1
        c = a + 2
        d = a + 3
        idx.extend([a, c, b])
        idx.extend([b, c, d])

    top_center = len(verts)
    verts.append((0.0, half_h, 0.0, 0.0, 1.0, 0.0, 0.5, 0.5))
    top_ring_start = len(verts)
    for seg in range(segments + 1):
        theta = 2.0 * math.pi * seg / segments
        x = radius * math.cos(theta)
        z = radius * math.sin(theta)
        u = 0.5 + 0.5 * math.cos(theta)
        v = 0.5 + 0.5 * math.sin(theta)
        verts.append((x, half_h, z, 0.0, 1.0, 0.0, u, v))
    for seg in range(segments):
        a = top_ring_start + seg
        b = a + 1
        idx.extend([top_center, b, a])

    bot_center = len(verts)
    verts.append((0.0, -half_h, 0.0, 0.0, -1.0, 0.0, 0.5, 0.5))
    bot_ring_start = len(verts)
    for seg in range(segments + 1):
        theta = 2.0 * math.pi * seg / segments
        x = radius * math.cos(theta)
        z = radius * math.sin(theta)
        u = 0.5 + 0.5 * math.cos(theta)
        v = 0.5 + 0.5 * math.sin(theta)
        verts.append((x, -half_h, z, 0.0, -1.0, 0.0, u, v))
    for seg in range(segments):
        a = bot_ring_start + seg
        b = a + 1
        idx.extend([bot_center, a, b])

    return np.array(verts, dtype='f4'), np.array(idx, dtype='i4')


def create_cube(size=1.0):
    h = size * 0.5

    faces = [
        (( h, -h, -h), (1, 0, 0)), (( h,  h, -h), (1, 0, 0)),
        (( h,  h,  h), (1, 0, 0)), (( h, -h,  h), (1, 0, 0)),
        ((-h, -h,  h), (-1, 0, 0)), ((-h,  h,  h), (-1, 0, 0)),
        ((-h,  h, -h), (-1, 0, 0)), ((-h, -h, -h), (-1, 0, 0)),
        ((-h,  h, -h), (0, 1, 0)), ((-h,  h,  h), (0, 1, 0)),
        (( h,  h,  h), (0, 1, 0)), (( h,  h, -h), (0, 1, 0)),
        ((-h, -h,  h), (0, -1, 0)), ((-h, -h, -h), (0, -1, 0)),
        (( h, -h, -h), (0, -1, 0)), (( h, -h,  h), (0, -1, 0)),
        ((-h, -h,  h), (0, 0, 1)), (( h, -h,  h), (0, 0, 1)),
        (( h,  h,  h), (0, 0, 1)), ((-h,  h,  h), (0, 0, 1)),
        (( h, -h, -h), (0, 0, -1)), ((-h, -h, -h), (0, 0, -1)),
        ((-h,  h, -h), (0, 0, -1)), (( h,  h, -h), (0, 0, -1)),
    ]

    uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]

    verts = []
    idx = []
    for fi, base in enumerate(range(0, len(faces), 4)):
        for vi in range(4):
            pos, nrm = faces[base + vi]
            u, v = uvs[vi]
            verts.append((pos[0], pos[1], pos[2], nrm[0], nrm[1], nrm[2], u, v))
        o = fi * 4
        idx.extend([o, o + 1, o + 2])
        idx.extend([o, o + 2, o + 3])

    return np.array(verts, dtype='f4'), np.array(idx, dtype='i4')


def create_plane(size=1.0):
    h = size * 0.5
    verts = np.array([
        (-h, -h, 0, 0, 0, 1, 0, 0),
        ( h, -h, 0, 0, 0, 1, 1, 0),
        ( h,  h, 0, 0, 0, 1, 1, 1),
        (-h,  h, 0, 0, 0, 1, 0, 1),
    ], dtype='f4')
    idx = np.array([0, 1, 2, 0, 2, 3], dtype='i4')
    return verts, idx


# ═══════════════════════════════════════════════════════════
#  ЗАГРУЗКА ТЕКСТУР
# ═══════════════════════════════════════════════════════════

def load_texture(ctx, path, default_color=(128, 128, 128),
                 srgb=False, max_dim=4096):
    if path and path != "" and path.lower() != "none":
        try:
            img = Image.open(path).convert("RGB")
            if max(img.size) > max_dim:
                img.thumbnail((max_dim, max_dim), Image.LANCZOS)
            data = img.tobytes()
            w, h = img.size
            tex = ctx.texture((w, h), 3, data)
            tex.build_mipmaps()
            tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
            tex.repeat_x = True
            tex.repeat_y = True
            tex.anisotropy = 8.0
            return tex
        except Exception as e:
            print(f"⚠ Не удалось загрузить {path}: {e}")

    default = np.array([[default_color]], dtype='u1')
    tex = ctx.texture((1, 1), 3, default.tobytes())
    tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
    return tex


# ═══════════════════════════════════════════════════════════
#  МАТРИЦЫ
# ═══════════════════════════════════════════════════════════

def perspective(fov, aspect, near, far):
    f = 1.0 / math.tan(fov / 2.0)
    m = np.zeros((4, 4), dtype='f4')
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


def look_at(eye, target, up):
    eye = np.array(eye, dtype='f4')
    target = np.array(target, dtype='f4')
    up = np.array(up, dtype='f4')

    f = target - eye
    f = f / np.linalg.norm(f)
    s = np.cross(f, up)
    s = s / np.linalg.norm(s)
    u = np.cross(s, f)

    m = np.eye(4, dtype='f4')
    m[0, :3] = s
    m[1, :3] = u
    m[2, :3] = -f
    m[0, 3] = -np.dot(s, eye)
    m[1, 3] = -np.dot(u, eye)
    m[2, 3] = np.dot(f, eye)
    return m


# ═══════════════════════════════════════════════════════════
#  IMGUI BACKEND
# ═══════════════════════════════════════════════════════════

def _win_addr(w):
    return ctypes.cast(w, ctypes.c_void_p).value


def imgui_glfw_backend(win):
    imgui.backends.glfw_init_for_opengl(_win_addr(win), False)

    def _cb_key(window, key, scancode, action, mods):
        imgui.backends.glfw_key_callback(_win_addr(window), key, scancode, action, mods)

    glfw.set_key_callback(win, _cb_key)

    imgui.backends.opengl3_init("#version 330")

    class _Backend:
        def new_frame(self):
            imgui.backends.opengl3_new_frame()
            imgui.backends.glfw_new_frame()
            imgui.new_frame()

        def render(self):
            imgui.render()
            imgui.backends.opengl3_render_draw_data(imgui.get_draw_data())

    return _Backend()


# ═══════════════════════════════════════════════════════════
#  ГЛАВНОЕ
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--albedo", default="")
    parser.add_argument("--normal", default="")
    parser.add_argument("--roughness", default="")
    parser.add_argument("--metallic", default="")
    parser.add_argument("--ao", default="")
    parser.add_argument("--height", default="")
    parser.add_argument("--tile-x", type=int, default=4)
    parser.add_argument("--tile-y", type=int, default=3)
    parser.add_argument("--shape", default="sphere", choices=["sphere", "cylinder", "cube", "plane"])
    parser.add_argument("--lang", default="ru")
    args = parser.parse_args()

    VIEWER_STRINGS = {
        "ru": {
            "window_title": "Viewer", "shape": "Форма",
            "sphere": "Сфера", "cylinder": "Цилиндр",
            "cube": "Куб", "plane": "Плоскость",
            "lighting": "Освещение", "exposure": "Экспозиция",
            "parallax": "Параллакс",
            "tiling": "Тайлинг", "current": "Текущий",
            "horizontal": "По горизонтали (X):", "vertical": "По вертикали (Y):",
            "reset": "Сброс 4x3",
        },
        "en": {
            "window_title": "Viewer", "shape": "Shape",
            "sphere": "Sphere", "cylinder": "Cylinder",
            "cube": "Cube", "plane": "Plane",
            "lighting": "Lighting", "exposure": "Exposure",
            "parallax": "Parallax",
            "tiling": "Tiling", "current": "Current",
            "horizontal": "Horizontal (X):", "vertical": "Vertical (Y):",
            "reset": "Reset 4x3",
        },
        "zh": {
            "window_title": "查看器", "shape": "形状",
            "sphere": "球体", "cylinder": "圆柱",
            "cube": "立方体", "plane": "平面",
            "lighting": "光照", "exposure": "曝光",
            "parallax": "视差",
            "tiling": "平铺", "current": "当前",
            "horizontal": "水平 (X):", "vertical": "垂直 (Y):",
            "reset": "重置 4x3",
        },
    }
    L = VIEWER_STRINGS.get(args.lang, VIEWER_STRINGS["ru"])

    if getattr(sys, 'frozen', False):
        _meipass = getattr(sys, '_MEIPASS', None)
        _exe_dir = os.path.dirname(sys.executable)
        _base_dir = _meipass if (_meipass and os.path.exists(os.path.join(_meipass, "env.png"))) else _exe_dir
    else:
        _base_dir = os.path.dirname(os.path.abspath(__file__))

    if not glfw.init():
        print("glfw init failed")
        return

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    win = glfw.create_window(900, 900, "Albedolizer — 3D Viewer", None, None)
    if not win:
        glfw.terminate()
        print("Не удалось создать окно")
        return

    glfw.make_context_current(win)
    glfw.set_window_attrib(win, glfw.FLOATING, True)
    glfw.focus_window(win)
    ctx = moderngl.create_context()

    imgui.create_context()
    io = imgui.get_io()

    font_candidates = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyh.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    font_loaded = False
    for fp in font_candidates:
        if os.path.exists(fp):
            try:
                io.fonts.add_font_from_file_ttf(fp, 18.0)
                font_loaded = True
                break
            except Exception:
                continue
    if not font_loaded:
        io.fonts.add_font_default()

    io.display_size = glfw.get_window_size(win)
    io.delta_time = 1.0 / 60.0
    impl = imgui_glfw_backend(win)

    prog = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)

    tex_albedo = load_texture(ctx, args.albedo, default_color=(200, 180, 150))
    tex_normal = load_texture(ctx, args.normal, default_color=(128, 128, 255))
    tex_rough = load_texture(ctx, args.roughness, default_color=(128, 128, 128))
    tex_metal = load_texture(ctx, args.metallic, default_color=(0, 0, 0))
    tex_ao = load_texture(ctx, args.ao, default_color=(255, 255, 255))
    tex_height = load_texture(ctx, args.height, default_color=(128, 128, 128))

    has_normal = 1 if (args.normal and args.normal != "" and args.normal.lower() != "none") else 0
    has_ao = 1 if (args.ao and args.ao != "" and args.ao.lower() != "none") else 0
    has_height = 1 if (args.height and args.height != "" and args.height.lower() != "none") else 0

    env_path = os.path.join(_base_dir, "env.png")
    tex_env = load_texture(ctx, env_path, default_color=(128, 128, 128))
    tex_env.repeat_x = True
    tex_env.repeat_y = False

    env_blur_path = os.path.join(_base_dir, "env_blur.png")
    if os.path.exists(env_blur_path):
        tex_env_blur = load_texture(ctx, env_blur_path, default_color=(128, 128, 128))
        tex_env_blur.repeat_x = True
        tex_env_blur.repeat_y = False
    else:
        tex_env_blur = tex_env

    tex_albedo.use(0)
    tex_normal.use(1)
    tex_rough.use(2)
    tex_metal.use(3)
    tex_ao.use(4)
    tex_height.use(5)
    tex_env.use(6)
    tex_env_blur.use(7)

    def _set_u(name, value):
        try:
            prog[name] = value
        except KeyError:
            print(f"⚠ Uniform {name} not found")

    _set_u("u_albedo", 0)
    _set_u("u_normal", 1)
    _set_u("u_roughness", 2)
    _set_u("u_metallic", 3)
    _set_u("u_ao", 4)
    _set_u("u_height", 5)
    _set_u("u_env", 6)
    _set_u("u_env_blur", 7)
    _set_u("u_has_normal", has_normal)
    _set_u("u_has_ao", has_ao)
    _set_u("u_has_height", has_height)

    def make_vao(verts, idx):
        vbo = ctx.buffer(verts.tobytes())
        ibo = ctx.buffer(idx.tobytes())
        return ctx.vertex_array(prog, [(vbo, '3f 3f 2f', 'in_position', 'in_normal', 'in_uv')], ibo)

    v_sphere, i_sphere = create_sphere(radius=0.5)
    v_cyl, i_cyl = create_cylinder(radius=0.5, height=1.0)
    v_cube, i_cube = create_cube(size=1.0)
    v_plane, i_plane = create_plane(size=1.0)

    vao_sphere = make_vao(v_sphere, i_sphere)
    vao_cylinder = make_vao(v_cyl, i_cyl)
    vao_cube = make_vao(v_cube, i_cube)
    vao_plane = make_vao(v_plane, i_plane)

    SHAPES = ["sphere", "cylinder", "cube", "plane"]
    SHAPE_LABELS = {
        "sphere": L["sphere"],
        "cylinder": L["cylinder"],
        "cube": L["cube"],
        "plane": L["plane"],
    }

    shape_idx = SHAPES.index(args.shape) if args.shape in SHAPES else 0

    yaw = 0.0
    pitch = 0.0
    dist = 1.5
    last_x = 0.0
    last_y = 0.0
    dragging = False

    TILE_STEPS = [1, 2, 3, 4, 6, 8, 12, 16]

    def _idx_for(val):
        if val in TILE_STEPS:
            return TILE_STEPS.index(val)
        i = 0
        for j, v in enumerate(TILE_STEPS):
            if v <= val:
                i = j
        return i

    tile_idx_x = _idx_for(args.tile_x)
    tile_idx_y = _idx_for(args.tile_y)

    exposure = 0.75
    parallax_strength = 1.0 if has_height else 0.0

    def mouse_button(window, button, action, mods):
        nonlocal dragging, last_x, last_y
        if button == glfw.MOUSE_BUTTON_LEFT:
            if action == glfw.PRESS:
                dragging = True
                last_x, last_y = glfw.get_cursor_pos(window)
            elif action == glfw.RELEASE:
                dragging = False

    def cursor_pos(window, x, y):
        nonlocal yaw, pitch, last_x, last_y
        if dragging:
            dx = x - last_x
            dy = y - last_y
            last_x = x
            last_y = y
            yaw += dx * 0.01
            pitch += dy * 0.01
            pitch = max(-math.pi / 2 + 0.01, min(math.pi / 2 - 0.01, pitch))

    def scroll_cb(window, xoff, yoff):
        nonlocal dist
        dist *= (1.0 - yoff * 0.08)
        dist = max(0.8, min(15.0, dist))

    def mouse_button_combined(window, button, action, mods):
        try:
            imgui.backends.glfw_mouse_button_callback(_win_addr(window), button, action, mods)
        except Exception:
            pass
        if imgui.get_io().want_capture_mouse:
            return
        mouse_button(window, button, action, mods)

    def cursor_pos_combined(window, x, y):
        try:
            imgui.backends.glfw_cursor_pos_callback(_win_addr(window), x, y)
        except Exception:
            pass
        if imgui.get_io().want_capture_mouse:
            return
        cursor_pos(window, x, y)

    def scroll_combined(window, xoff, yoff):
        try:
            imgui.backends.glfw_scroll_callback(_win_addr(window), xoff, yoff)
        except Exception:
            pass
        if imgui.get_io().want_capture_mouse:
            return
        scroll_cb(window, xoff, yoff)

    glfw.set_mouse_button_callback(win, mouse_button_combined)
    glfw.set_cursor_pos_callback(win, cursor_pos_combined)
    glfw.set_scroll_callback(win, scroll_combined)

    ctx.enable(moderngl.DEPTH_TEST)
    ctx.disable(moderngl.CULL_FACE)

    imgui.style_colors_dark()
    style = imgui.get_style()
    style.window_rounding = 8.0
    style.frame_rounding = 6.0
    style.window_padding = imgui.ImVec2(12, 12)
    style.frame_padding = imgui.ImVec2(8, 6)

    def draw_panel():
        nonlocal shape_idx, tile_idx_x, tile_idx_y, exposure, parallax_strength

        imgui.set_next_window_pos(imgui.ImVec2(12, 12), imgui.Cond_.always)
        imgui.set_next_window_size(imgui.ImVec2(280, 0), imgui.Cond_.always)
        imgui.begin(L["window_title"], None,
                    imgui.WindowFlags_.no_resize |
                    imgui.WindowFlags_.no_move |
                    imgui.WindowFlags_.always_auto_resize)

        imgui.text(L["shape"])
        imgui.separator()
        for i, key in enumerate(SHAPES):
            if imgui.radio_button(SHAPE_LABELS[key], shape_idx == i):
                shape_idx = i
        imgui.spacing()

        imgui.text(L["lighting"])
        imgui.separator()
        imgui.text(L["exposure"])
        changed, exposure = imgui.slider_float("##exposure", exposure, 0.5, 2.0, "%.2f")

        if has_height == 1:
            imgui.text(L["parallax"])
            changed_p, parallax_strength = imgui.slider_float(
                "##parallax", parallax_strength, 0.0, 3.0, "%.2f")
        imgui.spacing()

        imgui.text(L["tiling"])
        imgui.separator()
        imgui.text(f"{L['current']}: {TILE_STEPS[tile_idx_x]} x {TILE_STEPS[tile_idx_y]}")

        imgui.text(L["horizontal"])
        for i, val in enumerate(TILE_STEPS):
            active = (i == tile_idx_x)
            if active:
                imgui.push_style_color(imgui.Col_.button, imgui.ImVec4(0.36, 0.55, 0.85, 1.0))
            if imgui.button(f"{val}##x{i}", imgui.ImVec2(58, 30)):
                tile_idx_x = i
            if active:
                imgui.pop_style_color()
            if (i + 1) % 4 == 0:
                pass
            elif i < len(TILE_STEPS) - 1:
                imgui.same_line()

        imgui.spacing()
        imgui.text(L["vertical"])
        for i, val in enumerate(TILE_STEPS):
            active = (i == tile_idx_y)
            if active:
                imgui.push_style_color(imgui.Col_.button, imgui.ImVec4(0.36, 0.55, 0.85, 1.0))
            if imgui.button(f"{val}##y{i}", imgui.ImVec2(58, 30)):
                tile_idx_y = i
            if active:
                imgui.pop_style_color()
            if (i + 1) % 4 == 0:
                pass
            elif i < len(TILE_STEPS) - 1:
                imgui.same_line()

        imgui.spacing()
        if imgui.button(L["reset"], imgui.ImVec2(-1, 28)):
            tile_idx_x = 3
            tile_idx_y = 2

        imgui.end()

    target_dt = 1.0 / 60.0

    while not glfw.window_should_close(win):
        frame_start = time.time()
        glfw.poll_events()

        w, h = glfw.get_framebuffer_size(win)

        if w <= 0 or h <= 0:
            glfw.swap_buffers(win)
            elapsed = time.time() - frame_start
            if elapsed < target_dt:
                time.sleep(target_dt - elapsed)
            continue

        ctx.viewport = (0, 0, w, h)
        ctx.clear(0.12, 0.12, 0.15, 1.0)

        eye = (
            dist * math.cos(pitch) * math.sin(yaw),
            dist * math.sin(pitch),
            dist * math.cos(pitch) * math.cos(yaw),
        )
        proj = perspective(math.radians(40.0), w / h, 0.1, 100.0)
        view = look_at(eye, (0, 0, 0), (0, 1, 0))
        model = np.eye(4, dtype='f4')

        prog["m_proj"].write(proj.T.tobytes())
        prog["m_view"].write(view.T.tobytes())
        prog["m_model"].write(model.T.tobytes())
        prog["u_cam_pos"].value = eye
        prog["u_tile_x"].value = float(TILE_STEPS[tile_idx_x])
        prog["u_tile_y"].value = float(TILE_STEPS[tile_idx_y])
        prog["u_exposure"].value = float(exposure)
        prog["u_parallax_strength"].value = float(parallax_strength)

        vao = [vao_sphere, vao_cylinder, vao_cube, vao_plane][shape_idx]
        vao.render(moderngl.TRIANGLES)

        impl.new_frame()
        draw_panel()
        impl.render()

        glfw.swap_buffers(win)

        elapsed = time.time() - frame_start
        if elapsed < target_dt:
            time.sleep(target_dt - elapsed)

    glfw.terminate()


if __name__ == "__main__":
    main()