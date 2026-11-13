#!/usr/bin/env python3
"""Renders the 12-second HERO energy drink spot (9:16, 1080x1920, 30fps).

Each shot is a still in shots/ that gets animated here (speed-ramped camera
moves, flashes, shake, particles), plus a fully synthesized soundtrack.

    pip install imageio-ffmpeg numpy pillow
    python3 render.py            # -> hero_commercial.mp4
"""
import os, subprocess, wave
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageChops
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, SHOT = 1080, 1920, 30, 1.0
N_SHOTS = 12
SS = 1.5  # working-resolution supersample of the stills
rng = np.random.default_rng(7)


def load(n):
    im = Image.open(os.path.join(HERE, "shots", f"{n:02d}.png")).convert("RGB")
    return cover(im)


def cover(im):
    tw, th = int(W * SS), int(H * SS)
    s = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l, t = (im.width - tw) // 2, (im.height - th) // 2
    return im.crop((l, t, l + tw, t + th))


# ---------- composited shots 11 & 12 (built from the shot-1 can) ----------
CAN_BOX = (280, 415, 490, 952)  # can bounds inside shots/01.png


def can_cutout(scale):
    src = Image.open(os.path.join(HERE, "shots", "01.png")).convert("RGB")
    can = src.crop(CAN_BOX)
    cw, ch = round(can.width * scale), round(can.height * scale)
    can = can.resize((cw, ch), Image.LANCZOS).filter(
        ImageFilter.UnsharpMask(radius=2.5, percent=90, threshold=2))
    m = Image.new("L", (cw, ch), 0)
    d = ImageDraw.Draw(m)
    r = int(cw * 0.07)
    d.rounded_rectangle((3, 3, cw - 4, ch - 1), radius=r, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(2.5))
    # fade the very bottom (splash area) out
    a = np.asarray(m, dtype=np.float32)
    fade = np.clip((ch - np.arange(ch)) / (ch * 0.05), 0, 1)[:, None]
    m = Image.fromarray((a * fade).astype(np.uint8))
    return can, m


def radial_glow(w, h, cx, cy, rx, ry, color, power=2.0):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2)
    g = np.clip(1 - d, 0, 1) ** power
    return (g[..., None] * np.array(color, dtype=np.float32))


def build_final(with_wolf):
    tw, th = int(W * SS), int(H * SS)
    canw = tw * (0.40 if with_wolf else 0.46)
    can, mask = can_cutout(canw / (CAN_BOX[2] - CAN_BOX[0]))
    cx = tw // 2
    floor_y = int(th * (0.80 if with_wolf else 0.76))
    top = floor_y - can.height
    bg = np.zeros((th, tw, 3), np.float32)
    if with_wolf:
        wolf = Image.open(os.path.join(HERE, "shots", "04.png")).convert("RGB")
        # wolf head region, blown up to loom behind the can
        wolf = wolf.crop((150, 330, 620, 1166))
        wolf = wolf.resize((tw, th), Image.LANCZOS)
        wa = np.asarray(wolf, np.float32)
        # radial zoom blur
        acc = np.zeros_like(wa)
        steps = 14
        for i in range(steps):
            z = 1 + 0.035 * i
            cw_, ch_ = tw / z, th / z
            box = (cx - cw_ / 2, th * 0.42 - ch_ * 0.42, cx + cw_ / 2, th * 0.42 + ch_ * 0.58)
            acc += np.asarray(wolf.resize((tw, th), Image.BILINEAR, box=box), np.float32) * (1 - i / steps * 0.6)
        acc /= steps * 0.7
        bg = np.maximum(wa * 0.95, acc * 0.5)
        bg += radial_glow(tw, th, cx, th * 0.45, tw * 0.9, th * 0.6, (45, 26, 4), 1.5)
    else:
        bg += radial_glow(tw, th, cx, top + can.height * 0.45, tw * 0.75, th * 0.42, (70, 42, 8), 1.8)
        bg += radial_glow(tw, th, cx, floor_y, tw * 0.8, th * 0.05, (150, 95, 25), 1.2)
        bg[:, :, 2] += 6  # faint teal in the blacks
        bg[:, :, 1] += 4
    bgim = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8))
    # floor: darken + reflection
    refl = can.transpose(Image.FLIP_TOP_BOTTOM)
    rm = np.asarray(mask.transpose(Image.FLIP_TOP_BOTTOM), np.float32)
    fall = np.clip(1 - np.arange(can.height) / (can.height * 0.55), 0, 1)[:, None] ** 1.6
    rm = Image.fromarray((rm * fall * 0.45).astype(np.uint8))
    refl = refl.filter(ImageFilter.GaussianBlur(3))
    if with_wolf:
        fl = Image.new("RGB", (tw, th - floor_y), (0, 0, 0))
        fm = Image.new("L", (tw, th - floor_y), 150)
        bgim.paste(fl, (0, floor_y), fm)
    x0 = cx - can.width // 2
    bgim.paste(refl, (x0, floor_y - 4), rm)
    # rim light on can edges
    ca = np.asarray(can, np.float32)
    xs = np.linspace(-1, 1, can.width)[None, :, None]
    ca += (np.abs(xs) ** 6) * np.array([70, 48, 12], np.float32)
    can = Image.fromarray(np.clip(ca, 0, 255).astype(np.uint8))
    bgim.paste(can, (x0, top), mask)
    return bgim


# ---------- per-frame helpers ----------
def ease_out(t, p=3.0):
    return 1 - (1 - t) ** p


def view(im, zoom, cx, cy):
    """Crop im (working res) at zoom around normalised centre -> WxH frame."""
    tw, th = im.size
    cw, ch = tw / zoom, th / zoom
    x = min(max(cx * tw - cw / 2, 0), tw - cw)
    y = min(max(cy * th - ch / 2, 0), th - ch)
    return im.resize((W, H), Image.BICUBIC, box=(x, y, x + cw, y + ch))


yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = 1 - 0.38 * np.clip(np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2), 0, 1.3) ** 2.2
VIG = VIG[..., None]
GOLD = np.array([255, 200, 90], np.float32)

# gold dust particles (used on the product shots)
NP_ = 90
P = dict(x=rng.uniform(0, W, NP_), y=rng.uniform(0, H, NP_), vx=rng.normal(0, 14, NP_),
         vy=rng.uniform(-45, -10, NP_), r=rng.uniform(1.2, 4.5, NP_), ph=rng.uniform(0, 6.28, NP_))


def dust(frame, t, amount):
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(NP_):
        x = (P["x"][i] + P["vx"][i] * t + 18 * np.sin(t * 1.3 + P["ph"][i])) % W
        y = (P["y"][i] + P["vy"][i] * t) % H
        r = P["r"][i]
        b = amount * (0.55 + 0.45 * np.sin(t * 5 + P["ph"][i]))
        c = tuple(int(v * b) for v in (255, 190, 80))
        d.ellipse((x - r, y - r, x + r, y + r), fill=c)
    layer = ImageChops.lighter(layer.filter(ImageFilter.GaussianBlur(3)), layer)
    return ImageChops.screen(frame, layer)


# name, (zoom0, zoom1), (cx0, cy0), (cx1, cy1), options
SHOTS = [
    dict(z=(1.55, 1.08), a=(0.5, 0.56), b=(0.5, 0.50), shake=10, flash=1.0),            # 1 shards
    dict(z=(1.25, 1.12), a=(0.5, 0.78), b=(0.5, 0.30), shake=0, flash=0.5),             # 2 macro tilt up
    dict(z=(1.10, 1.35), a=(0.5, 0.45), b=(0.52, 0.34), shake=5, flash=0.6),            # 3 tab pull
    dict(z=(1.05, 1.45), a=(0.5, 0.42), b=(0.5, 0.50), shake=6, flash=0.9, flick=1),    # 4 wolf strides
    dict(z=(1.45, 1.40), a=(0.72, 0.5), b=(0.30, 0.5), shake=4, flash=0.6, flick=1),    # 5 wolf prowls
    dict(z=(1.50, 1.15), a=(0.45, 0.75), b=(0.45, 0.62), shake=12, flash=0.8),          # 6 start block
    dict(z=(1.30, 1.30), a=(0.38, 0.55), b=(0.62, 0.55), shake=7, flash=0.5),           # 7 runner
    dict(z=(1.00, 1.50), a=(0.5, 0.50), b=(0.5, 0.42), shake=9, flash=0.9, flick=1),    # 8 wolf leap
    dict(z=(1.40, 1.15), a=(0.62, 0.62), b=(0.45, 0.58), shake=6, flash=0.6),           # 9 skates
    dict(z=(1.15, 1.40), a=(0.35, 0.50), b=(0.55, 0.52), shake=8, flash=0.6),           # 10 rowing
    dict(z=(1.00, 1.30), a=(0.5, 0.50), b=(0.5, 0.56), shake=10, flash=1.0, flick=1, dust=0.8),  # 11 can + wolf
    dict(z=(1.00, 1.12), a=(0.5, 0.50), b=(0.5, 0.48), shake=0, flash=1.0, dust=1.0, linear=1),  # 12 final
]


def render_video(path):
    stills = [load(i) for i in range(1, 13)]
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
           "-pix_fmt", "yuv420p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    per = int(FPS * SHOT)
    for s, (cfg, im) in enumerate(zip(SHOTS, stills)):
        for f in range(per):
            t = f / (per - 1)
            e = t if cfg.get("linear") else ease_out(t, 3.2)  # speed ramp: whip in, settle
            z = cfg["z"][0] + (cfg["z"][1] - cfg["z"][0]) * e
            cx = cfg["a"][0] + (cfg["b"][0] - cfg["a"][0]) * e
            cy = cfg["a"][1] + (cfg["b"][1] - cfg["a"][1]) * e
            sh = cfg["shake"] * (1 - t) ** 3
            cx += rng.normal(0, sh) / W
            cy += rng.normal(0, sh) / H
            fr = view(im, z * 1.04, cx, cy)
            # motion blur on the whip-in
            if not cfg.get("linear") and f < 4:
                fr = fr.filter(ImageFilter.GaussianBlur((4 - f) * 2.2))
            if cfg.get("dust"):
                fr = dust(fr, s + f / FPS, cfg["dust"] * min(1, t * 3 + 0.3))
            a = np.asarray(fr, np.float32)
            if cfg.get("flick"):
                a *= 1 + 0.10 * rng.normal() + 0.06 * np.sin(f * 2.1)
            a *= VIG
            # grade: lift contrast slightly, cool the shadows
            a = np.clip((a / 255) ** 1.06 * 255 * 1.05, 0, 255)
            # cut flash (gold-white)
            fl = cfg["flash"] * max(0, 1 - f / 4.0) ** 2
            if s == 0:
                a *= min(1, f / 3.0 + 0.25)  # tiny fade-up
            a = a + (GOLD - a * 0.3) * fl * 0.55
            if s == N_SHOTS - 1 and f >= per - 5:  # soft landing
                a *= 1 - 0.5 * (f - (per - 5)) / 5
            p.stdin.write(np.clip(a, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close()
    p.wait()


# ---------- soundtrack ----------
SR = 44100


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(t / max(a, 1e-4), 1) * np.exp(-np.maximum(t - a, 0) / d)


def lowpass(x, fc):
    k = 1 - np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += k * (x[i] - acc)
        y[i] = acc
    return y


def add(buf, sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    n = min(len(sig), buf.shape[0] - i)
    if n <= 0:
        return
    buf[i:i + n, 0] += sig[:n] * gain * (1 - max(pan, 0))
    buf[i:i + n, 1] += sig[:n] * gain * (1 + min(pan, 0))


def impact(dur=0.7, f0=95, f1=38):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.06)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (dur * 0.3))
    click = rng.normal(0, 1, n) * np.exp(-t / 0.012) * 0.5
    return np.tanh((s + click) * 1.8)


def whoosh(dur=0.35, up=True):
    n = int(dur * SR)
    x = rng.normal(0, 1, n)
    lo = lowpass(x, 900)
    hi = x - lowpass(x, 2500)
    t = np.linspace(0, 1, n)
    mix = t if up else 1 - t
    e = np.sin(np.pi * t ** (1.8 if up else 0.6)) ** 2
    return (lo * (1 - mix) * 2 + hi * mix * 0.6) * e


def hiss(dur=0.8):
    n = int(dur * SR)
    x = rng.normal(0, 1, n)
    x = x - lowpass(x, 5000)
    t = np.arange(n) / SR
    crack = rng.normal(0, 1, n) * np.exp(-t / 0.008) * 3
    return x * env(n, 0.01, 0.28) + crack


def crackle(dur=0.9):
    n = int(dur * SR)
    x = np.zeros(n)
    idx = rng.integers(0, n, int(dur * 140))
    x[idx] = rng.normal(0, 1, len(idx))
    x = np.convolve(x, np.exp(-np.arange(200) / 25.0) * np.sin(np.arange(200) * 0.9), "same")
    return x * np.sin(np.pi * np.linspace(0, 1, n)) ** 0.5


def render_audio(path):
    total = N_SHOTS * SHOT
    buf = np.zeros((int(total * SR), 2))
    t = np.arange(buf.shape[0]) / SR
    # dark sub drone that rises
    drone = (np.sin(2 * np.pi * 49 * t) + 0.5 * np.sin(2 * np.pi * 98.3 * t) + 0.25 * np.sin(2 * np.pi * 147.6 * t))
    drone *= 0.10 * (0.5 + 0.5 * t / total) * (0.75 + 0.25 * np.sin(2 * np.pi * 2 * t))
    buf += drone[:, None]
    # hats / pulse at 120 bpm 8ths for drive
    for k in range(int(total * 4)):
        n = int(0.05 * SR)
        h = rng.normal(0, 1, n)
        h = (h - lowpass(h, 6000)) * np.exp(-np.arange(n) / SR / 0.012)
        add(buf, h, k * 0.25, 0.10 if k % 2 else 0.05, pan=0.3 * (-1) ** k)
    # half-beat kicks
    for k in range(int(total * 2)):
        if k % 2:
            add(buf, impact(0.3, 80, 42), k * 0.5, 0.35)
    # every cut: whoosh into it + impact on it
    for s in range(N_SHOTS):
        big = s in (0, 3, 7, 10, 11)
        add(buf, impact(1.0 if big else 0.6, 110 if big else 90), s * SHOT, 0.95 if big else 0.7)
        if s > 0:
            add(buf, whoosh(0.32, True), s * SHOT - 0.30, 0.5, pan=0.5 * (-1) ** s)
        add(buf, whoosh(0.4, False), s * SHOT, 0.22, pan=-0.5 * (-1) ** s)
    # shot 1 glass shatter
    n = int(0.9 * SR)
    g = rng.normal(0, 1, n)
    g = (g - lowpass(g, 4000)) * env(n, 0.002, 0.2)
    for fq in (3100, 4300, 5200, 6900):
        g += np.sin(2 * np.pi * fq * np.arange(n) / SR) * env(n, 0.001, 0.12) * 0.25
    add(buf, g, 0.03, 0.35)
    # shot 3 can opening
    add(buf, hiss(0.85), 2.12, 0.55)
    # wolf shots: electric crackle + growl
    for s in (3, 4, 7, 10):
        add(buf, crackle(0.95), s * SHOT, 0.5, pan=0.2 * (-1) ** s)
        n = int(0.9 * SR)
        tt = np.arange(n) / SR
        gr = np.sign(np.sin(2 * np.pi * (62 + 10 * np.sin(tt * 9)) * tt)) * (0.6 + 0.4 * np.sin(2 * np.pi * 27 * tt))
        gr = lowpass(gr, 420) * np.sin(np.pi * tt / 0.9) ** 0.7
        add(buf, gr, s * SHOT + 0.03, 0.30)
    # riser into the final shot, then a bright shimmer tail
    n = int(1.0 * SR)
    tt = np.linspace(0, 1, n)
    r = np.sin(2 * np.pi * np.cumsum(200 + 1400 * tt ** 2) / SR) * tt ** 2
    add(buf, r, 10.0, 0.16)
    n = int(1.0 * SR)
    tt = np.arange(n) / SR
    sh = sum(np.sin(2 * np.pi * fq * tt) for fq in (392, 587.3, 784, 1174.7)) * env(n, 0.005, 0.45)
    add(buf, sh, 11.0, 0.10)
    # master
    buf = np.tanh(buf * 1.25)
    fade = int(0.12 * SR)
    buf[-fade:] *= np.linspace(1, 0, fade)[:, None]
    buf = buf / np.abs(buf).max() * 0.92
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((buf * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    v, a = "/tmp/hero_v.mp4", "/tmp/hero_a.wav"
    out = os.path.join(HERE, "hero_commercial.mp4")
    render_audio(a)
    render_video(v)
    subprocess.check_call([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", v, "-i", a,
                           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                           "-shortest", out])
    print("wrote", out)
