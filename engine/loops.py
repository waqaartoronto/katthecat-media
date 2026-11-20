"""KatTheCatToons mood-loop engine. Usage: python3 loops.py episode.json out.mp4"""
import json, math, subprocess, sys, random
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

W, H, FPS, SR = 1080, 1920, 30, 44100
SS = 2                      # supersample factor for the character layer
INK = (43, 38, 41, 255)
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Gaegu-Bold.ttf")


def hexc(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def lerp(a, b, k):
    return a + (b - a) * k


# ------------------------------------------------------------------ music
def music(dur, seed, mood="sweet"):
    """Original soft music-box loop (procedural, royalty-free)."""
    rng = random.Random(seed)
    bpm = 84 if mood != "sad" else 70
    beat = 60 / bpm
    root = 60 + rng.choice([0, 2, 5, 7])
    if mood == "sad":
        prog = [[0, 3, 7], [-4, 0, 3], [-7, -3, 0], [-2, 2, 5]]       # i VI III VII-ish
    else:
        prog = [[0, 4, 7], [-5, -1, 2], [-3, 0, 4], [-7, -3, 0]]      # I V vi IV
    n = int(dur * SR) + SR
    out = np.zeros(n, dtype=np.float32)
    t = np.arange(int(SR * 2.5)) / SR

    def note(midi, start, vol, length=2.5, bell=True):
        f = 440 * 2 ** ((midi - 69) / 12)
        tt = t[: int(SR * length)]
        env = np.exp(-tt * (3.2 if bell else 1.2)) * (1 - np.exp(-tt * 300))
        w = np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * 2 * f * tt) + 0.08 * np.sin(2 * np.pi * 3.01 * f * tt)
        s = int(start * SR)
        e = min(n, s + len(w))
        if s < n:
            out[s:e] += (w * env * vol)[: e - s]

    pattern = [0, 1, 2, 1, 2, 1, 0, 2]
    step = beat / 2
    i = 0
    while i * step < dur + 1:
        chord = prog[(i // 8) % 4]
        k = pattern[i % 8]
        note(root + 12 + chord[k] + (12 if i % 16 in (6, 14) else 0), i * step, 0.16)
        if i % 8 == 0:
            for c in chord:
                note(root - 12 + c, i * step, 0.07, 2.5, bell=False)
        i += 1
    # simple echo for softness
    d = int(0.23 * SR)
    out[d:] += 0.35 * out[:-d]
    out = out[: int(dur * SR)]
    fade = int(0.25 * SR)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out / (np.max(np.abs(out)) + 1e-6) * 0.6


# ------------------------------------------------------------------ drawing helpers
class Pen:
    """Draws filled shapes with a chunky shared outline (outline pass, then fill pass)."""

    def __init__(self, d, stroke):
        self.d, self.s, self.ops = d, stroke, []

    def ellipse(self, cx, cy, rx, ry, fill, rot=0):
        self.ops.append(("e", cx, cy, rx, ry, fill, rot))

    def poly(self, pts, fill):
        self.ops.append(("p", pts, fill))

    def flush(self):
        s = self.s
        for op in self.ops:
            if op[0] == "e":
                _, cx, cy, rx, ry, _, rot = op
                self._ell(cx, cy, rx + s, ry + s, INK, rot)
            else:
                self.d.polygon(op[1], fill=INK)
                self.d.line(op[1] + [op[1][0]], fill=INK, width=int(s * 2), joint="curve")
                for p in op[1]:
                    self.d.ellipse([p[0] - s, p[1] - s, p[0] + s, p[1] + s], fill=INK)
        for op in self.ops:
            if op[0] == "e":
                _, cx, cy, rx, ry, fill, rot = op
                self._ell(cx, cy, rx, ry, fill, rot)
            else:
                self.d.polygon(op[1], fill=op[2])
        self.ops = []

    def _ell(self, cx, cy, rx, ry, fill, rot):
        if not rot:
            self.d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill)
        else:
            pts = [(cx + rx * math.cos(a) * math.cos(rot) - ry * math.sin(a) * math.sin(rot),
                    cy + rx * math.cos(a) * math.sin(rot) + ry * math.sin(a) * math.cos(rot))
                   for a in np.linspace(0, 2 * math.pi, 60)]
            self.d.polygon(pts, fill=fill)


def heart(d, cx, cy, size, fill, outline=True):
    pts = []
    for a in np.linspace(0, 2 * math.pi, 80):
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((cx + x * size / 16, cy - y * size / 16))
    if outline:
        d.line(pts + [pts[0]], fill=INK, width=int(size * 0.28), joint="curve")
    d.polygon(pts, fill=fill)


# ------------------------------------------------------------------ the cat
def draw_cat(c, st, t, f):
    """Returns RGBA image (supersampled size) of the cat in state st."""
    S = 900 * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = 1.6 * SS * c.get("scale", 1.0)       # unit
    stroke = 9 * SS
    pen = Pen(d, stroke)
    body = hexc(c["color"])
    pink = hexc(c.get("inner", "#ffb7c5"))
    cx, ground = S / 2, S * 0.80
    pose = st.get("pose", "sit")
    breathe = math.sin(t * 2 * math.pi / 2.6)
    bounce = st.get("bounce", 0)
    hop = abs(math.sin(t * math.pi * 2.2)) * 38 * u * bounce
    wig = math.sin(t * 2 * math.pi * 3) * st.get("wiggle", 0)
    sh = st.get("shake", 0) * math.sin(t * 60) * 4 * u

    # shadow
    d.ellipse([cx - 115 * u, ground - 12 * u, cx + 115 * u, ground + 12 * u], fill=(0, 0, 0, 30))
    if pose == "lie":
        bw, bh = 125 * u, 70 * u + breathe * 2 * u
        by = ground - bh
        hx, hy, hr = cx - 40 * u + sh, ground - 95 * u, 92 * u
    elif pose == "loaf":
        bw, bh = 120 * u, 82 * u + breathe * 2 * u
        by = ground - bh
        hx, hy, hr = cx + sh, ground - 135 * u, 96 * u
    else:  # sit
        bw, bh = 95 * u, 100 * u + breathe * 3 * u
        by = ground - bh - hop
        hx, hy, hr = cx + sh, ground - 205 * u - hop + breathe * 2 * u, 100 * u
    if c.get("male"):
        bw *= 1.14; hr *= 1.05
        by = ground - bh - (hop if pose == "sit" else 0)
    rot = wig * 0.12

    # tail
    tw = math.sin(t * 2 * math.pi / 1.8) * 0.35
    tail = []
    for i in range(22):
        k = i / 21
        a = -0.2 - k * 1.9 + tw * k
        tail.append((cx + bw * 0.75 + math.cos(a) * 70 * u * k * 1.4, ground - 20 * u - hop + math.sin(a) * 110 * u * k))
    d.line(tail, fill=INK, width=int(30 * u + 2 * stroke), joint="curve")
    d.line(tail, fill=body, width=int(30 * u), joint="curve")
    tx, ty = tail[-1]
    d.ellipse([tx - 15 * u - stroke, ty - 15 * u - stroke, tx + 15 * u + stroke, ty + 15 * u + stroke], fill=INK)
    d.ellipse([tx - 15 * u, ty - 15 * u, tx + 15 * u, ty + 15 * u], fill=body)

    # body + feet
    pat = c.get("pattern")
    dark = hexc(c.get("pat_color", "#2f3036"))
    WHITE = hexc("#ffffff")
    paw_col = dark if pat == "panda" else (WHITE if pat in ("tuxedo", "chest", "socks") else body)
    pen.ellipse(cx, by + bh * 0.05, bw, bh, body)
    if pose == "sit":
        for s in (-1, 1):
            pen.ellipse(cx + s * 52 * u, ground - 14 * u - hop, 34 * u, 20 * u, paw_col)
    # ears
    ear_tilt = st.get("ears", 0)  # negative = droopy
    for s in (-1, 1) if pat != "panda" else ():
        bx = hx + s * hr * 0.55
        if ear_tilt < 0:  # droopy: fold out and down
            pen.poly([(bx - s * 40 * u, hy - hr * 0.82), (hx + s * hr * 1.28, hy - hr * 0.32), (bx + s * 28 * u, hy - hr * 0.5)], body)
        else:
            tip = (hx + s * hr * 0.95, hy - hr * (1.12 + 0.12 * ear_tilt))
            pen.poly([(bx - s * 48 * u, hy - hr * 0.6), tip, (bx + s * 42 * u, hy - hr * 0.35)], body)
    if pat == "panda":
        for s in (-1, 1):
            pen.ellipse(hx + s * hr * 0.78, hy - hr * 0.72, 34 * u, 34 * u, dark)
    if c.get("ruff") and pose == "sit":
        pts = []
        for k in range(9):
            xx = hx - hr * 0.75 + k * hr * 1.5 / 8
            pts.append((xx, hy + hr * (1.12 if k % 2 else 0.9)))
        pen.poly([(hx - hr * 0.8, hy + hr * 0.4)] + pts + [(hx + hr * 0.8, hy + hr * 0.4)], body)
    if c.get("tufts"):
        for s in (-1, 1):
            pen.poly([(hx + s * hr * 0.9, hy - 14 * u), (hx + s * hr * 1.3, hy + 10 * u), (hx + s * hr * 1.02, hy + 26 * u),
                      (hx + s * hr * 1.24, hy + 50 * u), (hx + s * hr * 0.8, hy + 58 * u)], body)
    # head
    pen.ellipse(hx, hy, hr * 1.12, hr * 0.92, body, rot)
    # paws in front (sit/hug)
    held = st.get("hold")
    if pose == "sit":
        py = by + bh * 0.05
        if held:
            pass
        else:
            for s in (-1, 1):
                pen.ellipse(cx + s * 30 * u, py + 25 * u, 22 * u, 26 * u, paw_col)
    elif pose == "loaf":
        for s in (-1, 1):
            pen.ellipse(hx + s * 45 * u, ground - 14 * u, 30 * u, 18 * u, body)
    pen.flush()

    if c.get("ruff") and pose == "sit":
        pts = []
        for k in range(9):
            xx = hx - hr * 0.72 + k * hr * 1.44 / 8
            pts.append((xx, hy + hr * (1.16 if k % 2 else 0.98)))
        d.line(pts, fill=INK, width=int(7 * u), joint="curve")
    # fur patterns (flat patches, drawn inside the outlines)
    if pat == "tuxedo":
        d.ellipse([hx - 88 * u, hy - 12 * u, hx + 88 * u, hy + hr * 0.86], fill=WHITE)
        d.polygon([(hx - 30 * u, hy - 10 * u), (hx, hy - hr * 0.55), (hx + 30 * u, hy - 10 * u)], fill=WHITE)
        if pose == "sit":
            d.ellipse([cx - bw * 0.45, by + bh * 0.08, cx + bw * 0.45, by + bh * 0.85], fill=WHITE)
    elif pat == "tabby":
        sw = int(10 * u)
        for k in (-1, 0, 1):
            d.line([hx + k * 22 * u, hy - hr * 0.78, hx + k * 16 * u, hy - hr * 0.45], fill=dark, width=sw)
        for s_ in (-1, 1):
            for k in (0, 1):
                d.line([hx + s_ * (hr * 1.02), hy + (k * 22 - 6) * u, hx + s_ * (hr * 0.78), hy + (k * 22 - 2) * u], fill=dark, width=sw)
            for k in range(3):
                yy = by + bh * (0.2 + 0.22 * k)
                d.arc([cx + s_ * bw * 0.55 - 40 * u, yy - 18 * u, cx + s_ * bw * 0.55 + 40 * u, yy + 18 * u],
                      (100, 260)[s_ < 0] if False else (90 if s_ > 0 else 270) - 70, (90 if s_ > 0 else 270) + 70, fill=dark, width=sw)
    elif pat == "points":
        d.ellipse([hx - 52 * u, hy + 4 * u, hx + 52 * u, hy + 62 * u], fill=dark)
        for s_ in (-1, 1):
            bx = hx + s_ * hr * 0.55
            tip = (hx + s_ * hr * 0.95, hy - hr * (1.12 + 0.12 * ear_tilt))
            if ear_tilt >= 0:
                d.polygon([(bx - s_ * 44 * u, hy - hr * 0.62), tip, (bx + s_ * 38 * u, hy - hr * 0.37)], fill=dark)
    elif pat == "cow":
        d.ellipse([hx + 20 * u, hy - hr * 0.9, hx + hr * 1.0, hy - hr * 0.25], fill=dark)
        d.ellipse([cx - bw * 0.7, by + bh * 0.25, cx - bw * 0.15, by + bh * 0.7], fill=dark)
        d.ellipse([cx + bw * 0.3, by + bh * 0.55, cx + bw * 0.75, by + bh * 0.9], fill=dark)
    elif pat == "chest" and pose == "sit":
        d.ellipse([cx - bw * 0.42, by + bh * 0.12, cx + bw * 0.42, by + bh * 0.8], fill=WHITE)
        d.ellipse([hx - 40 * u, hy + 18 * u, hx + 40 * u, hy + 60 * u], fill=WHITE)
    elif pat == "bandit":
        d.rounded_rectangle([hx - hr * 0.92, hy - 24 * u, hx + hr * 0.92, hy + 30 * u], int(26 * u), fill=dark)
    elif pat == "panda":
        for s_ in (-1, 1):
            x_ = hx + s_ * 46 * u
            d.ellipse([x_ - 30 * u, hy + 4 * u - 26 * u, x_ + 30 * u, hy + 4 * u + 30 * u], fill=dark)
        if pose == "sit":
            d.rounded_rectangle([cx - bw * 0.95, by + bh * 0.02, cx + bw * 0.95, by + bh * 0.3], int(30 * u), fill=dark)

    # inner ears
    for s in (-1, 1) if pat != "panda" else ():
        bx = hx + s * hr * 0.55
        if ear_tilt < 0:
            d.polygon([(bx - s * 18 * u, hy - hr * 0.76), (hx + s * hr * 1.12, hy - hr * 0.42), (bx + s * 16 * u, hy - hr * 0.58)], fill=pink)
        else:
            tip = (hx + s * hr * 0.9, hy - hr * (1.0 + 0.12 * ear_tilt))
            d.polygon([(bx - s * 26 * u, hy - hr * 0.62), tip, (bx + s * 22 * u, hy - hr * 0.45)], fill=pink)

    # face
    look = st.get("look", 0) * 10 * u
    ey, ex = hy + 4 * u, 46 * u
    eyes = st.get("eyes", "open")
    blink = eyes == "open" and (f % 110) < 4
    for s in (-1, 1):
        x = hx + s * ex + look
        if (pat in ("panda", "bandit") or c.get("eye_white")) and eyes in ("open", "teary") and not blink:
            d.ellipse([x - 18 * u, ey - 21 * u, x + 18 * u, ey + 21 * u], fill=hexc(c.get("eye_white", "#ffffff")))
        if eyes == "open" and not blink:
            pr = 0.62 if c.get("eye_style") == "dot" else 1.0
            d.ellipse([x - 12 * u * pr, ey - 16 * u * pr, x + 12 * u * pr, ey + 16 * u * pr], fill=INK)
            if c.get("eye_style") != "dot":
                d.ellipse([x - 7 * u, ey - 11 * u, x + 1 * u, ey - 3 * u], fill=(255, 255, 255, 255))
            if c.get("eye_style") == "sleepy":
                lc = hexc(c.get("lid_col", c["color"]))
                d.rectangle([x - 20 * u, ey - 24 * u, x + 20 * u, ey - 2 * u], fill=lc)
                d.line([x - 16 * u, ey - 2 * u, x + 16 * u, ey - 2 * u], fill=hexc(c.get("arc_col", "#2b2b2b")), width=int(6 * u))
        elif eyes == "teary":
            d.ellipse([x - 15 * u, ey - 18 * u, x + 15 * u, ey + 18 * u], fill=INK)
            d.ellipse([x - 9 * u, ey - 13 * u, x + 1 * u, ey - 3 * u], fill=(255, 255, 255, 255))
            d.ellipse([x + 3 * u, ey + 4 * u, x + 9 * u, ey + 10 * u], fill=(255, 255, 255, 255))
            d.arc([x - 16 * u, ey + 10 * u, x + 16 * u, ey + 24 * u], 20, 160, fill=hexc("#8fd3ff"), width=int(5 * u))
        elif eyes in ("happy", "closed") or blink:
            ec = WHITE if pat in ("panda", "bandit") else hexc(c.get("arc_col", "#2b2b2b"))
            if eyes == "happy":
                d.arc([x - 16 * u, ey - 8 * u, x + 16 * u, ey + 20 * u], 200, 340, fill=ec, width=int(6 * u))
            else:
                d.arc([x - 16 * u, ey - 14 * u, x + 16 * u, ey + 10 * u], 20, 160, fill=ec, width=int(6 * u))
        elif eyes == "squeeze":
            d.line([x - 14 * u * s, ey - 10 * u, x + 10 * u * s, ey, x - 14 * u * s, ey + 10 * u], fill=INK, width=int(6 * u), joint="curve")
        elif eyes == "flat":
            d.line([x - 15 * u, ey, x + 15 * u, ey], fill=INK, width=int(6 * u))
        elif eyes == "cry":
            d.arc([x - 16 * u, ey - 14 * u, x + 16 * u, ey + 10 * u], 20, 160, fill=INK, width=int(6 * u))
    if eyes == "cry":  # tear rivers
        for s in (-1, 1):
            x = hx + s * ex
            k = (t * 2) % 1
            d.rounded_rectangle([x - 9 * u, ey + 6 * u, x + 9 * u, ey + 55 * u + 10 * u * math.sin(t * 9)], int(9 * u), fill=hexc("#8fd3ff"))
    # blush
    if st.get("blush", True) and not c.get("male"):
        for s in (-1, 1):
            x = hx + s * 72 * u + look
            a = 150 if st.get("blush") == "big" else 95
            d.ellipse([x - 20 * u, ey + 18 * u, x + 20 * u, ey + 32 * u], fill=hexc("#ff8fab", a))
    # nose + mouth
    ny = ey + 18 * u
    nk = 1.6 if c.get("big_nose") else 1.0
    d.polygon([(hx - 6 * u * nk + look, ny), (hx + 6 * u * nk + look, ny), (hx + look, ny + 6 * u * nk)], fill=hexc(c["nose_col"]) if c.get("nose_col") else pink)
    mouth = st.get("mouth", "w")
    mx, my = hx + look, ny + 8 * u
    if mouth == "w":
        d.arc([mx - 13 * u, my - 6 * u, mx, my + 7 * u], 0, 180, fill=INK, width=int(4.5 * u))
        d.arc([mx, my - 6 * u, mx + 13 * u, my + 7 * u], 0, 180, fill=INK, width=int(4.5 * u))
    elif mouth == "open":
        d.chord([mx - 14 * u, my - 6 * u, mx + 14 * u, my + 20 * u], 0, 180, fill=INK)
        d.ellipse([mx - 7 * u, my + 5 * u, mx + 7 * u, my + 13 * u], fill=hexc("#ff8fab"))
    elif mouth == "smirk":
        d.line([mx - 4 * u, my + 4 * u, mx + 8 * u, my + 4 * u], fill=INK, width=int(4.5 * u))
        d.arc([mx + 2 * u, my - 8 * u, mx + 16 * u, my + 6 * u], 20, 120, fill=INK, width=int(4.5 * u))
    elif mouth == "o":
        d.ellipse([mx - 6 * u, my, mx + 6 * u, my + 11 * u], fill=INK)
    elif mouth == "sad":
        d.arc([mx - 12 * u, my + 2 * u, mx + 12 * u, my + 18 * u], 200, 340, fill=INK, width=int(4.5 * u))
    elif mouth == "wobble":
        pts = [(mx - 16 * u + i * 4 * u, my + 8 * u + math.sin(i * 1.6 + t * 20) * 3 * u) for i in range(9)]
        d.line(pts, fill=INK, width=int(4.5 * u), joint="curve")
    # whiskers
    for s in (-1, 1):
        for k in (-1, 1):
            d.line([hx + s * 92 * u, ny + 2 * u + k * 6 * u, hx + s * 128 * u, ny - 4 * u + k * 16 * u], fill=INK, width=int(3 * u))

    if c.get("male"):
        bc = c.get("brow_col", "#2b2b2b")
        for s_ in (-1, 1):
            x = hx + s_ * ex + look
            d.line([x - s_ * 20 * u, ey - 27 * u, x + s_ * 18 * u, ey - 38 * u], fill=hexc(bc), width=int(10 * u))
    if c.get("scarf") and pose == "sit":
        sc_ = hexc(c["scarf"])
        sy = hy + hr * 0.78
        d.rounded_rectangle([hx - hr * 0.78 - stroke, sy - 22 * u - stroke, hx + hr * 0.78 + stroke, sy + 22 * u + stroke], int(22 * u), fill=INK)
        d.rounded_rectangle([hx - hr * 0.78, sy - 22 * u, hx + hr * 0.78, sy + 22 * u], int(20 * u), fill=sc_)
        d.rounded_rectangle([hx + hr * 0.25 - stroke, sy - stroke, hx + hr * 0.55 + stroke, sy + 80 * u + stroke], int(14 * u), fill=INK)
        d.rounded_rectangle([hx + hr * 0.25, sy, hx + hr * 0.55, sy + 80 * u], int(12 * u), fill=sc_)
    # held items in front of body
    if held and pose in ("sit", "loaf", "lie"):
        hx2, hy2 = cx, (by + bh * 0.15) if pose == "sit" else ground - 40 * u
        if held == "heart":
            pulse = 1 + 0.06 * math.sin(t * 2 * math.pi * 1.5)
            heart(d, hx2, hy2, 48 * u * pulse, hexc("#ff6f91"))
        elif held == "flower":
            d.line([hx2 + 10 * u, hy2 + 40 * u, hx2 + 62 * u, hy2 - 30 * u], fill=INK, width=int(14 * u))
            d.line([hx2 + 10 * u, hy2 + 40 * u, hx2 + 62 * u, hy2 - 30 * u], fill=hexc("#7bc96f"), width=int(7 * u))
            for a in range(5):
                ang = a * 2 * math.pi / 5 + t
                px, py = hx2 + 62 * u + math.cos(ang) * 20 * u, hy2 - 30 * u + math.sin(ang) * 20 * u
                d.ellipse([px - 16 * u, py - 16 * u, px + 16 * u, py + 16 * u], fill=INK)
            for a in range(5):
                ang = a * 2 * math.pi / 5 + t
                px, py = hx2 + 62 * u + math.cos(ang) * 20 * u, hy2 - 30 * u + math.sin(ang) * 20 * u
                d.ellipse([px - 11 * u, py - 11 * u, px + 11 * u, py + 11 * u], fill=hexc("#ffd166"))
            d.ellipse([hx2 + 52 * u, hy2 - 40 * u, hx2 + 72 * u, hy2 - 20 * u], fill=hexc("#ff8fab"))
        elif held == "cookie":
            r_ = 46 * u
            d.ellipse([hx2 - r_ - stroke, hy2 - r_ - stroke, hx2 + r_ + stroke, hy2 + r_ + stroke], fill=INK)
            d.ellipse([hx2 - r_, hy2 - r_, hx2 + r_, hy2 + r_], fill=hexc("#e0a96d"))
            d.pieslice([hx2 + r_ * 0.2, hy2 - r_ * 1.2, hx2 + r_ * 1.6, hy2 + r_ * 0.2], 120, 240, fill=(0, 0, 0, 0))
            for (cx_, cy_) in [(-0.4, -0.3), (0.2, 0.35), (-0.15, 0.25), (0.35, -0.45), (-0.5, 0.4)]:
                d.ellipse([hx2 + cx_ * r_ - 7 * u, hy2 + cy_ * r_ - 7 * u, hx2 + cx_ * r_ + 7 * u, hy2 + cy_ * r_ + 7 * u], fill=hexc("#5a3825"))
        elif held == "pillow":
            d.rounded_rectangle([hx2 - 85 * u - stroke, hy2 - 50 * u - stroke, hx2 + 85 * u + stroke, hy2 + 50 * u + stroke], int(40 * u), fill=INK)
            d.rounded_rectangle([hx2 - 85 * u, hy2 - 50 * u, hx2 + 85 * u, hy2 + 50 * u], int(36 * u), fill=hexc("#cdb4db"))
            heart(d, hx2, hy2 - 4 * u, 18 * u, hexc("#ffffff"), outline=False)
        elif held == "mug":
            d.rounded_rectangle([hx2 - 40 * u - stroke, hy2 - 50 * u - stroke, hx2 + 40 * u + stroke, hy2 + 45 * u + stroke], int(12 * u), fill=INK)
            d.rounded_rectangle([hx2 - 40 * u, hy2 - 50 * u, hx2 + 40 * u, hy2 + 45 * u], int(10 * u), fill=hexc("#ff8fab"))
            for k_ in (-1, 1):
                yy = hy2 - 70 * u - 18 * u * math.sin(t * 3 + k_)
                d.arc([hx2 + k_ * 16 * u - 10 * u, yy - 30 * u, hx2 + k_ * 16 * u + 10 * u, yy], 270, 90, fill=hexc("#ffffff"), width=int(5 * u))
        elif held == "star":
            r_ = 52 * u; pts = []
            for k_ in range(10):
                a_ = -math.pi / 2 + k_ * math.pi / 5; rr = r_ if k_ % 2 == 0 else r_ * 0.45
                pts.append((hx2 + math.cos(a_) * rr, hy2 - 30 * u + math.sin(a_) * rr))
            d.polygon(pts, fill=hexc("#ffd23f"), outline=INK, width=int(6 * u))
        elif held == "gift":
            d.rounded_rectangle([hx2 - 55 * u, hy2 - 45 * u, hx2 + 55 * u, hy2 + 50 * u], int(8 * u), fill=hexc("#4cc9a0"), outline=INK, width=int(6 * u))
            d.rectangle([hx2 - 9 * u, hy2 - 45 * u, hx2 + 9 * u, hy2 + 50 * u], fill=hexc("#e63946"))
            d.ellipse([hx2 - 30 * u, hy2 - 70 * u, hx2, hy2 - 42 * u], outline=hexc("#e63946"), width=int(8 * u))
            d.ellipse([hx2, hy2 - 70 * u, hx2 + 30 * u, hy2 - 42 * u], outline=hexc("#e63946"), width=int(8 * u))
        elif held == "phone":
            d.rounded_rectangle([hx2 - 34 * u - stroke, hy2 - 58 * u - stroke, hx2 + 34 * u + stroke, hy2 + 58 * u + stroke], int(14 * u), fill=INK)
            d.rounded_rectangle([hx2 - 34 * u, hy2 - 58 * u, hx2 + 34 * u, hy2 + 58 * u], int(12 * u), fill=hexc("#bde0fe"))
            heart(d, hx2, hy2 - 5 * u, 16 * u, hexc("#ff6f91"), outline=False)
        # paws over the item
        p2 = Pen(d, stroke)
        for s in (-1, 1):
            p2.ellipse(hx2 + s * 46 * u, hy2 + 10 * u, 22 * u, 24 * u, body)
        p2.flush()
    hat = st.get("hat") or c.get("hat")
    if hat == "santa":
        top = hy - hr * 0.62
        d.polygon([(hx - hr * 0.62, top), (hx + hr * 0.62, top), (hx + hr * 0.95, top - hr * 0.95)], fill=INK)
        d.polygon([(hx - hr * 0.55, top - 6 * u), (hx + hr * 0.55, top - 6 * u), (hx + hr * 0.9, top - hr * 0.88)], fill=hexc("#e63946"))
        d.rounded_rectangle([hx - hr * 0.72, top - 22 * u, hx + hr * 0.72, top + 26 * u], int(24 * u), fill=hexc("#ffffff"), outline=INK, width=int(6 * u))
        d.ellipse([hx + hr * 0.95 - 26 * u, top - hr * 0.95 - 26 * u, hx + hr * 0.95 + 26 * u, top - hr * 0.95 + 26 * u], fill=hexc("#ffffff"), outline=INK, width=int(6 * u))
    elif hat == "wizard":
        top = hy - hr * 0.6
        d.polygon([(hx - hr * 0.7, top), (hx + hr * 0.7, top), (hx + hr * 0.15, top - hr * 1.5)], fill=hexc("#6c4ab6"), outline=INK, width=int(7 * u))
        d.rounded_rectangle([hx - hr * 0.95, top - 14 * u, hx + hr * 0.95, top + 18 * u], int(16 * u), fill=hexc("#6c4ab6"), outline=INK, width=int(7 * u))
        for (sx, sy) in ((-0.2, -0.4), (0.25, -0.75), (0.0, -1.05)):
            x_, y_ = hx + sx * hr, top + sy * hr; r_ = 12 * u
            d.polygon([(x_, y_ - r_ * 2), (x_ + r_ * 0.5, y_ - r_ * 0.5), (x_ + r_ * 2, y_), (x_ + r_ * 0.5, y_ + r_ * 0.5),
                       (x_, y_ + r_ * 2), (x_ - r_ * 0.5, y_ + r_ * 0.5), (x_ - r_ * 2, y_), (x_ - r_ * 0.5, y_ - r_ * 0.5)], fill=hexc("#ffd23f"))
    if (st.get("bowtie") or c.get("bowtie")) and pose == "sit":
        by_ = hy + hr * 0.86
        col = hexc(st.get("bowtie") if isinstance(st.get("bowtie"), str) else "#e63946")
        for s_ in (-1, 1):
            d.polygon([(hx, by_), (hx + s_ * 46 * u, by_ - 26 * u), (hx + s_ * 46 * u, by_ + 26 * u)], fill=col, outline=INK, width=int(6 * u))
        d.ellipse([hx - 13 * u, by_ - 13 * u, hx + 13 * u, by_ + 13 * u], fill=col, outline=INK, width=int(6 * u))
    return img


# ------------------------------------------------------------------ scenes (static backgrounds, cat sits at floor y≈1314)
FLOOR = 1314
_SCENE_CACHE = {}


def _rr(d, box, r, fill, w=8):
    d.rounded_rectangle(box, r, fill=fill, outline=INK, width=w)


def draw_scene(name, bg):
    key = (name, bg)
    if key in _SCENE_CACHE:
        return _SCENE_CACHE[key]
    im = Image.new("RGBA", (W, H), bg)
    d = ImageDraw.Draw(im)
    floor = tuple(max(0, v - 28) for v in bg[:3]) + (255,)
    if name == "bed":
        d.rectangle([0, 1480, W, H], fill=floor)
        _rr(d, [150, 770, 930, 1340], 70, hexc("#d9a77a"))
        _rr(d, [230, 850, 850, 1000], 40, hexc("#e8bf98"), 6)
        _rr(d, [70, 1290, 1010, 1490], 40, hexc("#fffaf3"))
        _rr(d, [160, 1170, 450, 1310], 60, hexc("#ffffff"))
        _rr(d, [70, 1380, 1010, 1520], 40, hexc("#ffc7d4"))
        for x in range(150, 1000, 110):
            d.line([x, 1395, x + 40, 1505], fill=hexc("#ff9fb5"), width=10)
    elif name == "couch":
        d.rectangle([0, 1470, W, H], fill=floor)
        _rr(d, [80, 900, 1000, 1330], 90, hexc("#8fb8de"))
        _rr(d, [110, 1290, 970, 1450], 40, hexc("#a9c9e8"))
        _rr(d, [30, 1080, 190, 1460], 60, hexc("#7aa6d1"))
        _rr(d, [890, 1080, 1050, 1460], 60, hexc("#7aa6d1"))
        _rr(d, [700, 1130, 860, 1300], 50, hexc("#ffc7d4"), 6)
        for x in (120, 940):
            d.rectangle([x, 1450, x + 24, 1500], fill=INK)
    elif name == "kitchen":
        _rr(d, [-20, 380, 300, 620], 20, hexc("#f3e6d3"))
        _rr(d, [780, 380, 1100, 620], 20, hexc("#f3e6d3"))
        d.line([140, 380, 140, 620], fill=INK, width=6)
        d.line([940, 380, 940, 620], fill=INK, width=6)
        _rr(d, [-20, 1340, 1100, 1760], 10, hexc("#f3e6d3"))
        for x in (260, 540, 820):
            d.line([x, 1340, x, 1760], fill=INK, width=6)
        _rr(d, [-20, 1300, 1100, 1350], 10, hexc("#e0c49e"))
        _rr(d, [800, 1200, 980, 1305], 20, hexc("#9aa5b1"))
        d.line([980, 1230, 1060, 1215], fill=INK, width=14)
    elif name == "window":
        _rr(d, [230, 770, 850, 1270], 30, hexc("#ffffff"))
        d.rectangle([262, 802, 818, 1238], fill=hexc("#cad8f3"))
        d.rectangle([262, 1150, 818, 1238], fill=hexc("#ffffff"))
        d.line([540, 802, 540, 1238], fill=INK, width=10)
        d.line([262, 1020, 818, 1020], fill=INK, width=10)
        _rr(d, [190, 1270, 890, 1330], 16, hexc("#e8d5c0"))
    _SCENE_CACHE[key] = im
    return im


def kf(keys, t, default=0.0):
    """Interpolate keyframes [[t, v], ...] with easing."""
    if not keys:
        return default
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            return lerp(v0, v1, ease((t - t0) / max(1e-6, t1 - t0)))
    return keys[-1][1]


def sticker(frame, s, t):
    """Pop-up sound word: {text, t0, t1, x, y, size, color, rot}."""
    if not (s["t0"] <= t <= s["t1"]):
        return
    k_in = min(1, (t - s["t0"]) / 0.18)
    k_out = min(1, (s["t1"] - t) / 0.18)
    sc = (0.4 + 0.75 * ease(k_in) - 0.15 * (1 - k_out)) * (1 + 0.04 * math.sin(t * 14))
    f_ = ImageFont.truetype(FONT, int(s.get("size", 96) * sc) + 1)
    tmp = Image.new("RGBA", (900, 400), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    tw = td.textlength(s["text"], font=f_)
    td.text(((900 - tw) / 2, 120), s["text"], font=f_, fill=hexc(s.get("color", "#ffd23f"), int(255 * k_out)),
            stroke_width=8, stroke_fill=INK[:3] + (int(255 * k_out),))
    tmp = tmp.rotate(s.get("rot", 0) + 4 * math.sin(t * 6), resample=Image.BICUBIC)
    frame.alpha_composite(tmp, (int(s["x"] - 450), int(s["y"] - 200)))


def sfx_track(n, events):
    """Synth SFX: pop, boing, crunch, purr, ding, whoosh."""
    out = np.zeros(n, np.float32)
    rng = np.random.default_rng(7)
    for ev in events:
        o = int(ev["t"] * SR)
        kind, vol = ev["kind"], ev.get("vol", 0.5)
        if kind == "pop":
            L = int(0.12 * SR); tt = np.arange(L) / SR
            s = np.sin(2 * np.pi * (900 - 5000 * tt) * tt) * np.exp(-tt * 40)
        elif kind == "boing":
            L = int(0.5 * SR); tt = np.arange(L) / SR
            s = np.sin(2 * np.pi * (220 + 80 * np.sin(2 * np.pi * 14 * tt)) * tt) * np.exp(-tt * 6)
        elif kind == "crunch":
            L = int(0.35 * SR); tt = np.arange(L) / SR
            s = rng.uniform(-1, 1, L) * (np.sin(2 * np.pi * 18 * tt) > 0.2) * np.exp(-tt * 9)
        elif kind == "purr":
            L = int(ev.get("dur", 2.0) * SR); tt = np.arange(L) / SR
            s = np.convolve(rng.uniform(-1, 1, L), np.ones(40) / 40, "same") * (0.6 + 0.4 * np.sin(2 * np.pi * 24 * tt)) * 3
            s *= np.minimum(1, np.minimum(tt / 0.2, (tt[-1] - tt) / 0.2))
        elif kind == "sting":
            L = int(1.1 * SR); tt = np.arange(L) / SR
            f0 = np.where(tt < 0.35, 196, np.where(tt < 0.7, 185, 147))
            s = np.sign(np.sin(2 * np.pi * f0 * tt)) * 0.35 * np.exp(-((tt % 0.35)) * 3) + np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 3) * 0.8
        elif kind == "gulp":
            L = int(0.25 * SR); tt = np.arange(L) / SR
            s = np.sin(2 * np.pi * (300 - 900 * tt) * tt) * np.exp(-tt * 14)
        elif kind == "tada":
            L = int(1.2 * SR); tt = np.arange(L) / SR
            s = sum(np.sin(2 * np.pi * f * tt) * (tt > o_) * np.exp(-(tt - o_).clip(0) * 3) for f, o_ in ((523, 0), (659, 0.12), (784, 0.24), (1046, 0.36))) * 0.4
        elif kind == "ding":
            L = int(0.8 * SR); tt = np.arange(L) / SR
            s = (np.sin(2 * np.pi * 1320 * tt) + 0.5 * np.sin(2 * np.pi * 1980 * tt)) * np.exp(-tt * 5) * 0.6
        elif kind == "whoosh":
            L = int(0.45 * SR); tt = np.arange(L) / SR
            s = np.convolve(rng.uniform(-1, 1, L), np.ones(12) / 12, "same") * np.sin(np.pi * tt / tt[-1]) ** 2 * 2
        else:
            continue
        e = min(n, o + len(s))
        if o < n:
            out[o:e] += (s[: e - o] * vol).astype(np.float32)
    return out


def paw_print(d, cx, cy, s, col, w=10):
    d.ellipse([cx - 60 * s, cy - 40 * s, cx + 60 * s, cy + 55 * s], outline=col, width=w)
    for dx, dy in ((-70, -70), (-25, -105), (25, -105), (70, -70)):
        d.ellipse([cx + (dx - 22) * s, cy + (dy - 26) * s, cx + (dx + 22) * s, cy + (dy + 26) * s], outline=col, width=w)


# ------------------------------------------------------------------ extras / text
def extras(d, st, t, k_in, cx, cy):
    ex = st.get("extras", [])
    if "sweat" in ex or "sweat_big" in ex:
        n = 3 if "sweat_big" in ex else 1
        for i in range(n):
            ph = (t * (0.9 + 0.3 * i) + i * 0.37) % 1
            x = cx + [175, 205, -185][i]
            y = cy - [300, 200, 260][i] + ph * 120
            r = 22
            pts = [(x, y - r * 1.9), (x + r * 0.95, y - r * 0.2), (x, y + r), (x - r * 0.95, y - r * 0.2)]
            d.polygon(pts, fill=hexc("#9fd8ff", int(235 * k_in)), outline=INK[:3] + (int(255 * k_in),), width=5)
            d.ellipse([x - 7, y - 8, x + 1, y], fill=hexc("#ffffff", int(220 * k_in)))
    if "snow" in ex:
        for i in range(14):
            ph = (t * 0.35 + i / 14) % 1
            x = 280 + (i * 97) % 520 + 12 * math.sin(t * 2 + i)
            y = 815 + ph * 330
            d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=hexc("#ffffff", int(240 * k_in)))
    if "tap" in ex:
        p = (math.sin(t * 5) + 1) / 2
        paw_print(d, W / 2, 1700, 1.0 + 0.12 * p, hexc("#ff6f91", int(255 * k_in)), 12)
        d.ellipse([W / 2 - 170 - 30 * p, 1700 - 170 - 30 * p, W / 2 + 170 + 30 * p, 1700 + 170 + 30 * p],
                  outline=hexc("#ff6f91", int(120 * (1 - p) * k_in)), width=8)
    if "hearts" in ex:
        for i in range(6):
            ph = (t * 0.45 + i / 6) % 1
            x = cx + (1 if i % 2 else -1) * (250 + 40 * math.sin(i * 1.7 + ph * 5))
            y = cy - 40 - ph * 300
            a = int(255 * min(1, (1 - ph) * 1.6) * k_in)
            heart(d, x, y, 24 + 10 * math.sin(i), hexc("#ff6f91", a), outline=False)
    if "zzz" in ex:
        f2 = ImageFont.truetype(FONT, 70)
        for i in range(3):
            ph = (t * 0.5 + i / 3) % 1
            d.text((cx + 150 + ph * 90, cy - 230 - ph * 230), "z", font=f2, fill=INK[:3] + (int(255 * (1 - ph) * k_in),))
    if "sparkles" in ex:
        for i in range(5):
            a = (math.sin(t * 4 + i * 1.7) + 1) / 2
            x, y = cx + [-260, 250, -200, 220, 0][i], cy + [-260, -200, -40, 10, -300][i]
            r = 10 + 14 * a
            d.polygon([(x, y - r * 2), (x + r * 0.5, y - r * 0.5), (x + r * 2, y), (x + r * 0.5, y + r * 0.5),
                       (x, y + r * 2), (x - r * 0.5, y + r * 0.5), (x - r * 2, y), (x - r * 0.5, y - r * 0.5)],
                      fill=hexc("#ffffff", int(230 * k_in)))
    if "dots" in ex:
        f2 = ImageFont.truetype(FONT, 90)
        n = int((t * 3) % 4)
        d.text((cx - 50, cy - 400), "." * n, font=f2, fill=INK)
    if "rain" in ex:
        for i in range(10):
            ph = (t * 1.3 + i / 10) % 1
            x = cx - 270 + i * 60
            d.line([x, cy - 600 + ph * 520, x - 6, cy - 570 + ph * 520], fill=hexc("#8fb8de", 200), width=5)
        d.ellipse([cx - 200, cy - 680, cx + 200, cy - 560], fill=hexc("#9aa5b1"))
        d.ellipse([cx - 120, cy - 720, cx + 80, cy - 600], fill=hexc("#9aa5b1"))


def text_block(d, text, t_in, y, reveal=0.6):
    if not text:
        return
    size = 76
    font = ImageFont.truetype(FONT, size)
    k = ease(t_in / 0.35)
    shown = text[: max(1, int(len(text) * min(1, t_in / reveal)))] if text != "..." else text
    lines, cur = [], ""
    for w in shown.split(" "):
        test = (cur + " " + w).strip()
        if d.textlength(test, font=font) > W - 220:
            lines.append(cur); cur = w
        else:
            cur = test
    lines.append(cur)
    y = y - (len(lines) - 1) * (size + 6)
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=font)
        d.text(((W - tw) / 2, y + i * (size + 6) + (1 - k) * 14), ln, font=font, fill=INK[:3] + (int(255 * k),))


# ------------------------------------------------------------------ render
def render(ep, out):
    c = ep["character"]
    beats = ep["beats"]
    LEAD = 0.25
    v = None
    ext = None
    if ep.get("audio_file"):  # pre-recorded performance (e.g. ElevenLabs); beats carry "start" in voice time
        ext, esr = sf.read(ep["audio_file"], dtype="float32")
        if ext.ndim > 1:
            ext = ext.mean(axis=1)
        if esr != SR:
            ext = np.interp(np.arange(0, len(ext), esr / SR), np.arange(len(ext)), ext).astype(np.float32)
        LEAD = ep.get("lead", 0.12)
        vlen = len(ext) / SR
        st_ = [b["start"] for b in beats] + [vlen]
        for i, b in enumerate(beats):
            b["dur"] = (st_[i + 1] - st_[i]) + (LEAD if i == 0 else 0) + (ep.get("tail", 0.3) if i == len(beats) - 1 else 0)
            b["_reveal"] = max(0.3, (st_[i + 1] - st_[i]) * 0.75)
    total = sum(b["dur"] for b in beats)
    bg = hexc(ep["bg"])
    starts, acc = [], 0
    for b in beats:
        starts.append(acc); acc += b["dur"]
    a = music(total, hash(out) % 1000, ep.get("mood", "sweet")) * (0.3 if v else 1.0)
    talk = np.zeros(int(total * FPS) + 2)
    for b, s0 in zip(beats, starts):
        sp = b.get("_sp")
        if sp is None:
            continue
        o = int((s0 + LEAD) * SR)
        e = min(len(a), o + len(sp))
        a[o:e] += sp[: e - o] * 0.95
        b["_reveal"] = len(sp) / SR
        for fr in range(int(len(sp) / SR * FPS)):
            seg = sp[int(fr / FPS * SR): int((fr + 1) / FPS * SR)]
            talk[int((s0 + LEAD) * FPS) + fr] = float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0
    if ext is not None:
        a = a * ep.get("music_level", 0.22)
        o = int(LEAD * SR); e = min(len(a), o + len(ext))
        a[o:e] += ext[: e - o]
        for fr in range(int(len(ext) / SR * FPS)):
            seg = ext[int(fr / FPS * SR): int((fr + 1) / FPS * SR)]
            if int(LEAD * FPS) + fr < len(talk):
                talk[int(LEAD * FPS) + fr] = float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0
    if ep.get("sfx"):
        a = a + sfx_track(len(a), ep["sfx"])
    a = a / max(1.0, float(np.max(np.abs(a))) / 0.95)
    sf.write(out + ".wav", a, SR)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", out + ".wav",
                             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                             "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
                            stdin=subprocess.PIPE)
    wm_font = ImageFont.truetype(FONT, 46)
    nf = int(total * FPS)
    for f in range(nf):
        t = f / FPS
        i = max(j for j in range(len(beats)) if starts[j] <= t)
        st, t_in = beats[i], t - starts[i]
        lo, hi = ep.get("lip", [0.02, 0.06])
        if talk[f] > lo and not st.get("no_lipsync"):
            st = dict(st, mouth="open" if (talk[f] > hi and f % 4 < 3) else st.get("mouth", "w"))
        frame = draw_scene(ep["scene"], bg).copy() if ep.get("scene") else Image.new("RGBA", (W, H), bg)
        d = ImageDraw.Draw(frame)
        # pop-in squash when a new beat starts
        pop = 1 + 0.08 * math.exp(-t_in * 9) * math.cos(t_in * 25)
        cat = draw_cat(c, st, t, f)
        cam = ep.get("camera")
        z = kf(cam.get("zoom"), t, 1.0) if cam else 1.0
        shake = kf(cam.get("shake"), t, 0.0) if cam else 0.0
        size = int(900 * pop * z)
        cat = cat.resize((size, size), Image.LANCZOS)
        cx, cy = W // 2, int(H * 0.60)
        if cam:
            cx = int(W / 2 + kf(cam.get("dx"), t, 0) + shake * 14 * math.sin(t * 47))
            cy = int(kf(cam.get("face_y"), t, 986) + 0.184 * size + shake * 10 * math.cos(t * 39))
        frame.alpha_composite(cat, (cx - size // 2, cy - int(size * 0.62)))
        extras(d, st, t, ease(t_in / 0.3), cx, cy)
        for stk in ep.get("stickers", []):
            sticker(frame, stk, t)
        d = ImageDraw.Draw(frame)
        text_block(d, st.get("text", ""), max(0, t_in - (LEAD if (v or ext is not None) and i == 0 else (LEAD if v else 0))), int(H * (0.31 if ep.get("scene") else 0.36)), st.get("_reveal", 0.6))
        if ep.get("hook") and ep.get("hook_style") == "meme":
            hf = ImageFont.truetype(FONT, 74)
            words, lines_, cur = ep["hook"].split(" "), [], ""
            for w_ in words:
                test = (cur + " " + w_).strip()
                if d.textlength(test, font=hf) > W - 200:
                    lines_.append(cur); cur = w_
                else:
                    cur = test
            lines_.append(cur)
            bw_ = max(d.textlength(l_, font=hf) for l_ in lines_)
            y0 = 190
            d.rounded_rectangle([(W - bw_) / 2 - 40, y0 - 24, (W + bw_) / 2 + 40, y0 + len(lines_) * 86 + 14], 36,
                                fill=(255, 255, 255, 240), outline=INK, width=6)
            for k_, l_ in enumerate(lines_):
                d.text(((W - d.textlength(l_, font=hf)) / 2, y0 + k_ * 86), l_, font=hf, fill=INK)
        elif ep.get("hook") and t < ep.get("hook_secs", 2.4):
            hf = ImageFont.truetype(FONT, 58)
            a_ = int(255 * min(1, (ep.get("hook_secs", 2.4) - t) / 0.4))
            hl = ep["hook"]; tw_ = d.textlength(hl, font=hf)
            d.rounded_rectangle([(W - tw_) / 2 - 34, H * 0.16 - 14, (W + tw_) / 2 + 34, H * 0.16 + 74], 40, fill=(255, 255, 255, int(a_ * 0.75)))
            d.text(((W - tw_) / 2, H * 0.16), hl, font=hf, fill=INK[:3] + (a_,))
        handle = ep.get("handle", "")
        tw = d.textlength(handle, font=wm_font)
        d.text(((W - tw) / 2, H * 0.78), handle, font=wm_font, fill=INK[:3] + (55,))
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close(); proc.wait()
    return total


if __name__ == "__main__":
    ep = json.load(open(sys.argv[1]))
    print(f"{render(ep, sys.argv[2]):.1f}s -> {sys.argv[2]}")
