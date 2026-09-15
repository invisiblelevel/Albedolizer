"""
viewer.py — PBR 3D viewer для Albedolizer.
Отдельное OpenGL-окно через moderngl + glfw.
"""

import os
import sys
import time
import argparse
import math
import numpy as np
import moderngl
import glfw
from PIL import Image


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
uniform sampler2D u_env;         // чёткая HDRI
uniform sampler2D u_env_blur;    // размытая HDRI

uniform vec3 u_cam_pos;
uniform float u_exposure;

out vec4 frag_color;

const float PI = 3.14159265359;

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

void main() {
    vec3 albedo = texture(u_albedo, v_uv).rgb;
    vec3 N = normalize(v_normal);
    float roughness = clamp(texture(u_roughness, v_uv).r, 0.05, 1.0);
    float metallic = clamp(texture(u_metallic, v_uv).r, 0.0, 1.0);

    vec3 V = normalize(u_cam_pos - v_world_pos);
    vec3 R = reflect(-V, N);

    // Diffuse — всегда размытая HDRI
    vec3 env_diff = sample_env_blur(N);

    // Specular
    vec3 env_refl;
    if (metallic > 0.5) {
        // Металл — чёткая HDRI с лёгким размытием по roughness
        vec3 blur_dir = normalize(mix(N, R, 1.0 - roughness * 0.5));
        env_refl = mix(sample_env(blur_dir), sample_env_blur(blur_dir), roughness);
    } else {
        // Диэлектрик — сильно размытая HDRI
        env_refl = sample_env_blur(R);
    }

    vec3 F0 = mix(vec3(0.04), albedo, metallic);

    // ═══ Diffuse (только для неметаллов) ═══
    vec3 diffuse = albedo * (1.0 - metallic) * env_diff * 2.0;

    // ═══ Ambient — мягкая подсветка теней ═══
    vec3 fill = sample_env_blur(N) * albedo * (1.0 - metallic) * 0.4;
    diffuse += fill;

    // ═══ Specular ═══
    float spec_strength = mix(0.4, 6.0, metallic);
    vec3 specular = env_refl * F0 * (1.0 - roughness * 0.3) * spec_strength;

    // ═══ Ambient для металлов ═══
    vec3 ambient = env_diff * F0 * 0.5 * metallic;

    vec3 color = diffuse + specular + ambient;

    // ACES tone mapping
    const float a = 2.51;
    const float b = 0.03;
    const float c = 2.43;
    const float d = 0.59;
    const float e = 0.14;
    color = clamp((color * (a * color + b)) / (color * (c * color + d) + e), 0.0, 1.0);
    color = pow(max(color, vec3(0.0)), vec3(1.0 / 2.2));
    color *= u_exposure;

    frag_color = vec4(color, 1.0);
}
"""


# ═══════════════════════════════════════════════════════════
#  ГЕОМЕТРИЯ
# ═══════════════════════════════════════════════════════════

def create_sphere(radius=1.0, segments=64, rings=64):
    verts = []
    for ring in range(rings + 1):
        phi = math.pi * ring / rings
        for seg in range(segments + 1):
            theta = 2.0 * math.pi * seg / segments
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.cos(phi)
            z = radius * math.sin(phi) * math.sin(theta)
            nx, ny, nz = x / radius, y / radius, z / radius
            u = (seg / segments) * 3.0        # 3 повтора по горизонтали
            v = (1.0 - ring / rings) * 3.0    # 3 повтора по вертикали
            verts.append((x, y, z, nx, ny, nz, u, v))

    idx = []
    for ring in range(rings):
        for seg in range(segments):
            a = ring * (segments + 1) + seg
            b = a + segments + 1
            idx.extend([a, b, a + 1])
            idx.extend([a + 1, b, b + 1])
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--albedo", default="")
    parser.add_argument("--roughness", default="")
    parser.add_argument("--metallic", default="")
    args = parser.parse_args()

    # ═══ Базовая папка (рядом с exe или скриптом) ═══
    if getattr(sys, 'frozen', False):
        # Ищем сначала внутри exe (_MEIPASS), потом рядом с exe
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
    ctx = moderngl.create_context()

    prog = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)

    tex_albedo = load_texture(ctx, args.albedo, default_color=(200, 180, 150))
    tex_rough = load_texture(ctx, args.roughness, default_color=(128, 128, 128))
    tex_metal = load_texture(ctx, args.metallic, default_color=(0, 0, 0))

    # ═══ Environment map — HDRI-панорама (env.png) ═══
    env_path = os.path.join(_base_dir, "env.png")
    tex_env = load_texture(ctx, env_path, default_color=(128, 128, 128))
    tex_env.repeat_x = True
    tex_env.repeat_y = False

    # ═══ Размытая версия HDRI (для диэлектриков) ═══
    env_blur_path = os.path.join(_base_dir, "env_blur.png")
    if os.path.exists(env_blur_path):
        tex_env_blur = load_texture(ctx, env_blur_path, default_color=(128, 128, 128))
        tex_env_blur.repeat_x = True
        tex_env_blur.repeat_y = False
    else:
        tex_env_blur = tex_env  # fallback — та же текстура

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

    verts, idx = create_sphere(radius=0.3)
    vbo = ctx.buffer(verts.tobytes())
    ibo = ctx.buffer(idx.tobytes())
    vao = ctx.vertex_array(prog, [(vbo, '3f 3f 2f', 'in_position', 'in_normal', 'in_uv')], ibo)

    yaw = 0.0
    pitch = 0.0
    dist = 1.0
    last_x = 0.0
    last_y = 0.0
    dragging = False

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

    glfw.set_mouse_button_callback(win, mouse_button)
    glfw.set_cursor_pos_callback(win, cursor_pos)
    glfw.set_scroll_callback(win, scroll_cb)

    ctx.enable(moderngl.DEPTH_TEST)

    # ═══ Ограничение 60 FPS ═══
    target_dt = 1.0 / 60.0

    while not glfw.window_should_close(win):
        frame_start = time.time()

        glfw.poll_events()

        w, h = glfw.get_framebuffer_size(win)
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

        vao.render(moderngl.TRIANGLES)
        glfw.swap_buffers(win)

        # Ограничение FPS — чтобы ноут не грелся
        elapsed = time.time() - frame_start
        if elapsed < target_dt:
            time.sleep(target_dt - elapsed)

    glfw.terminate()


if __name__ == "__main__":
    main()