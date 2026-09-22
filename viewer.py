"""
viewer.py — PBR 3D viewer для Albedolizer.
Отдельное OpenGL-окно через moderngl + glfw.
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
uniform sampler2D u_roughness;
uniform sampler2D u_metallic;
uniform sampler2D u_env;
uniform sampler2D u_env_blur;

uniform vec3 u_cam_pos;
uniform float u_exposure;
uniform float u_tile_x;
uniform float u_tile_y;

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

// ═══ BRDF функции (из LearnOpenGL) ═══
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

// ═══ Основной свет (для объёма) ═══
const vec3 LIGHT_DIR = normalize(vec3(-0.5, 0.8, 0.6));
const vec3 LIGHT_COLOR = vec3(1.0, 0.95, 0.9);

void main() {
    vec2 uv = vec2(v_uv.x * u_tile_x, v_uv.y * u_tile_y);
    vec3 albedo = texture(u_albedo, uv).rgb;
    vec3 N = normalize(v_normal);
    vec3 V = normalize(u_cam_pos - v_world_pos);
    vec3 R = reflect(-V, N);

    float roughness = clamp(texture(u_roughness, uv).r, 0.05, 1.0);
    float metallic = clamp(texture(u_metallic, uv).r, 0.0, 1.0);

    // F0: диэлектрики = 0.04, металлы = albedo
    vec3 F0 = vec3(0.04);
    F0 = mix(F0, albedo, metallic);

    // ═══ Прямой свет (для объёма) ═══
    vec3 L = LIGHT_DIR;
    vec3 H = normalize(V + L);
    float NdotL = max(dot(N, L), 0.0);
    float NdotV = max(dot(N, V), 0.0);

    // Cook-Torrance BRDF
    float D = DistributionGGX(N, H, roughness);
    float G = GeometrySmith(N, V, L, roughness);
    vec3 F = fresnelSchlick(max(dot(H, V), 0.0), F0);

    vec3 numerator = D * G * F;
    float denominator = 4.0 * max(NdotV, 0.001) * NdotL;
    vec3 specular_direct = numerator / max(denominator, 0.001);

    // kS = F, kD = (1 - kS) * (1 - metallic)
    vec3 kS = F;
    vec3 kD = (vec3(1.0) - kS) * (1.0 - metallic);

    vec3 Lo_direct = (kD * albedo / PI + specular_direct) * LIGHT_COLOR * NdotL;

    // ═══ IBL (ambient от env-карты) ═══
    vec3 F_ibl = fresnelSchlickRoughness(NdotV, F0, roughness);
    vec3 kS_ibl = F_ibl;
    vec3 kD_ibl = (vec3(1.0) - kS_ibl) * (1.0 - metallic);

    // Diffuse IBL — размытая HDRI
    vec3 irradiance = sample_env_blur(N);

    // Specular IBL — чёткая HDRI для металлов, размытая для диэлектриков
    vec3 reflection_env = mix(sample_env_blur(R), sample_env(R), metallic);

    // Упрощённая IBL-аппроксимация (без prefiltered cubemap)
    vec3 diffuse_ibl = irradiance * albedo * kD_ibl;
    // Спекуляр IBL — жёстко только для металлов
    vec3 specular_ibl = reflection_env * F_ibl * (metallic * 8.0 + (1.0 - metallic) * 0.05) * (1.0 - roughness * 0.5);

    vec3 color = Lo_direct + diffuse_ibl * 0.8 + specular_ibl;

    // ═══ Tone map (Reinhard) + gamma ═══
    color = color / (color + vec3(1.0));
    color = pow(max(color, vec3(0.0)), vec3(1.0 / 2.2));
    color *= u_exposure;

    frag_color = vec4(color, 1.0);
}
"""


# ═══════════════════════════════════════════════════════════
#  ГЕОМЕТРИЯ
# ═══════════════════════════════════════════════════════════

def create_sphere(radius=1.0, segments=64, rings=64):
    cols = segments + 1  # +1 дублирующий столбец для корректного UV-шва
    verts = []
    for ring in range(rings + 1):
        phi = math.pi * ring / rings
        for seg in range(cols):
            theta = 2.0 * math.pi * seg / segments
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.cos(phi)
            z = radius * math.sin(phi) * math.sin(theta)
            nx, ny, nz = x / radius, y / radius, z / radius
            u = seg / segments      # 0.0 ... 1.0 (дубль столбца = u=1.0)
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


# ═══════════════════════════════════════════════════════════
#  ЗАГРУЗКА ТЕКСТУР
# ═══════════════════════════════════════════════════════════

def load_texture(ctx, path, default_color=(128, 128, 128)):
    if path and path != "" and path.lower() != "none":
        try:
            img = Image.open(path).convert("RGB")
            data = img.tobytes()
            w, h = img.size
            tex = ctx.texture((w, h), 3, data)
            tex.build_mipmaps()
            tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
            tex.repeat_x = True
            tex.repeat_y = True
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

    # Row-major (для .T при передаче)
    m = np.eye(4, dtype='f4')
    m[0, :3] = s
    m[1, :3] = u
    m[2, :3] = -f
    m[0, 3] = -np.dot(s, eye)
    m[1, 3] = -np.dot(u, eye)
    m[2, 3] = np.dot(f, eye)
    return m


# ═══════════════════════════════════════════════════════════
#  ГЛАВНОЕ
# ═══════════════════════════════════════════════════════════

def _win_addr(w):
    """GLFW-окно → int-адрес (нужен для бэкендов imgui-bundle)."""
    return ctypes.cast(w, ctypes.c_void_p).value


def imgui_glfw_backend(win):
    """
    Минимальный биндинг ImGui → GLFW + OpenGL3 через imgui-bundle.
    Мышиные callback'и НЕ трогает — их комбинирует вызывающий код.
    Возвращает объект с методами new_frame() и render().
    """
    # ═══ СНАЧАЛА GLFW platform backend ═══
    imgui.backends.glfw_init_for_opengl(_win_addr(win), False)

    # Только клавиатура, char, framebuffer — мышью управляет main()
    def _cb_key(window, key, scancode, action, mods):
        imgui.backends.glfw_key_callback(_win_addr(window), key, scancode, action, mods)
    def _cb_char(window, codepoint):
        imgui.backends.glfw_char_callback(_win_addr(window), codepoint)
    def _cb_fb(window, w, h):
        imgui.backends.glfw_framebuffer_size_callback(_win_addr(window), w, h)

    glfw.set_key_callback(win, _cb_key)
    # glfw.set_char_callback(win, _cb_char)
    # glfw.set_framebuffer_size_callback(win, _cb_fb)

    # ═══ ПОТОМ OpenGL3 renderer backend ═══
    imgui.backends.opengl3_init("#version 330")

    class _Backend:
        def new_frame(self):
            imgui.backends.opengl3_new_frame()
            imgui.backends.glfw_new_frame()
            imgui.new_frame()

        def render(self):
            imgui.render()
            imgui.backends.opengl3_render_draw_data(
                imgui.get_draw_data()
            )

    return _Backend()



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--albedo", default="")
    parser.add_argument("--roughness", default="")
    parser.add_argument("--metallic", default="")
    parser.add_argument("--tile-x", type=int, default=4)
    parser.add_argument("--tile-y", type=int, default=3)
    parser.add_argument("--lang", default="ru")
    args = parser.parse_args()

    # ═══ Локализация UI вьюера ═══
    VIEWER_STRINGS = {
        "ru": {
            "window_title": "Tiling",
            "current": "Текущий",
            "horizontal": "По горизонтали (X):",
            "vertical": "По вертикали (Y):",
            "reset": "Сброс 4x3",
        },
        "en": {
            "window_title": "Tiling",
            "current": "Current",
            "horizontal": "Horizontal (X):",
            "vertical": "Vertical (Y):",
            "reset": "Reset 4x3",
        },
    }
    L = VIEWER_STRINGS.get(args.lang, VIEWER_STRINGS["ru"])

    # ═══ Базовая папка (рядом с exe или скриптом) ═══
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

    win = glfw.create_window(800, 800, "Albedolizer — 3D Viewer", None, None)
    if not win:
        glfw.terminate()
        print("Не удалось создать окно")
        return

    glfw.make_context_current(win)
    glfw.set_window_attrib(win, glfw.FLOATING, True)
    glfw.focus_window(win)
    ctx = moderngl.create_context()

    # ═══ ImGui init ═══
    imgui.create_context()
    io = imgui.get_io()

    # ─── Шрифт с кириллицей ───
    font_path = r"C:\Windows\Fonts\segoeui.ttf"
    if not os.path.exists(font_path):
        font_path = r"C:\Windows\Fonts\arial.ttf"

    if os.path.exists(font_path):
        io.fonts.add_font_from_file_ttf(font_path, 18.0)
    else:
        io.fonts.add_font_default()

    io.display_size = glfw.get_window_size(win)
    io.delta_time = 1.0 / 60.0
    impl = imgui_glfw_backend(win)

    prog = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)

    # ═══ Текстуры ═══
    tex_albedo = load_texture(ctx, args.albedo, default_color=(200, 180, 150))
    tex_rough = load_texture(ctx, args.roughness, default_color=(128, 128, 128))
    tex_metal = load_texture(ctx, args.metallic, default_color=(0, 0, 0))

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
    tex_rough.use(1)
    tex_metal.use(2)
    tex_env.use(3)
    tex_env_blur.use(4)

    prog["u_albedo"] = 0
    prog["u_roughness"] = 1
    prog["u_metallic"] = 2
    prog["u_env"] = 3
    prog["u_env_blur"] = 4
    prog["u_exposure"] = 1.0

    # ═══ Геометрия — VAO ═══
    verts, idx = create_sphere(radius=0.3)
    vbo = ctx.buffer(verts.tobytes())
    ibo = ctx.buffer(idx.tobytes())
    vao = ctx.vertex_array(prog, [(vbo, '3f 3f 2f', 'in_position', 'in_normal', 'in_uv')], ibo)

    # ═══ Состояние камеры ═══
    yaw = 0.0
    pitch = 0.0
    dist = 1.0
    last_x = 0.0
    last_y = 0.0
    dragging = False

    # ═══ Tiling state ═══
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

    # ═══ Совмещённые callback'и ═══
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

    # ═══ ImGui стиль ═══
    imgui.style_colors_dark()
    style = imgui.get_style()
    style.window_rounding = 8.0
    style.frame_rounding = 6.0
    style.window_padding = imgui.ImVec2(12, 12)
    style.frame_padding = imgui.ImVec2(8, 6)

    # ═══ Панель tiling ═══
    def draw_tiling_panel():
        nonlocal tile_idx_x, tile_idx_y

        imgui.set_next_window_pos(imgui.ImVec2(12, 12), imgui.Cond_.always)
        imgui.set_next_window_size(imgui.ImVec2(260, 0), imgui.Cond_.always)
        imgui.begin(L["window_title"], None,
                    imgui.WindowFlags_.no_resize |
                    imgui.WindowFlags_.no_move |
                    imgui.WindowFlags_.always_auto_resize)

        imgui.text(f"{L['current']}: {TILE_STEPS[tile_idx_x]} x {TILE_STEPS[tile_idx_y]}")
        imgui.separator()

        imgui.text(L["horizontal"])
        for i, val in enumerate(TILE_STEPS):
            active = (i == tile_idx_x)
            if active:
                imgui.push_style_color(imgui.Col_.button, imgui.ImVec4(0.36, 0.55, 0.85, 1.0))
            if imgui.button(f"{val}##x{i}", imgui.ImVec2(34, 28)):
                tile_idx_x = i
            if active:
                imgui.pop_style_color()
            if i < len(TILE_STEPS) - 1:
                imgui.same_line()

        imgui.spacing()
        imgui.text(L["vertical"])
        for i, val in enumerate(TILE_STEPS):
            active = (i == tile_idx_y)
            if active:
                imgui.push_style_color(imgui.Col_.button, imgui.ImVec4(0.36, 0.55, 0.85, 1.0))
            if imgui.button(f"{val}##y{i}", imgui.ImVec2(34, 28)):
                tile_idx_y = i
            if active:
                imgui.pop_style_color()
            if i < len(TILE_STEPS) - 1:
                imgui.same_line()

        imgui.spacing()
        if imgui.button(L["reset"], imgui.ImVec2(-1, 28)):
            tile_idx_x = 3
            tile_idx_y = 2

        imgui.end()

    # ═══ Главный цикл ═══
    target_dt = 1.0 / 60.0

    while not glfw.window_should_close(win):
        frame_start = time.time()
        glfw.poll_events()

        w, h = glfw.get_framebuffer_size(win)

        # Защита от нулевого размера окна (свёрнуто, не отрисовалось, etc.)
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
        proj = perspective(math.radians(45.0), w / h, 0.1, 100.0)
        view = look_at(eye, (0, 0, 0), (0, 1, 0))
        model = np.eye(4, dtype='f4')

        prog["m_proj"].write(proj.T.tobytes())
        prog["m_view"].write(view.T.tobytes())
        prog["m_model"].write(model.T.tobytes())
        prog["u_cam_pos"].value = eye
        prog["u_tile_x"].value = float(TILE_STEPS[tile_idx_x])
        prog["u_tile_y"].value = float(TILE_STEPS[tile_idx_y])

        vao.render(moderngl.TRIANGLES)

        impl.new_frame()
        draw_tiling_panel()
        impl.render()

        glfw.swap_buffers(win)

        elapsed = time.time() - frame_start
        if elapsed < target_dt:
            time.sleep(target_dt - elapsed)

    glfw.terminate()


if __name__ == "__main__":
    main()