"""Kat 2.0 skit engine: shots + cuts, real camera (zoom/pan over the whole set), foreground sets,
props, multiple characters, movement and flips. Reuses the Kat drawing code from loops.py.
Usage: python3 skit.py skit.json out.mp4"""
import json, math, subprocess, sys
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageOps
import loops as L

W, H, FPS, SR = L.W, L.H, L.FPS, L.SR
INK = L.INK
CAT_S = None  # supersampled cat canvas size, filled on first draw


def pick(states, t):
    cur = states[0][1]
    for t0, st in states:
        if t >= t0:
            cur = st
    return cur


# ---------------------------------------------------------------- sets (background + foreground)
def set_bg(name, bg):
    im = Image.new("RGBA", (W, H), L.hexc(bg))
    d = ImageDraw.Draw(im)
    if name == "kitchen":
        for y in range(380, 1380, 120):
            d.line([0, y, W, y], fill=L.hexc("#ffffff", 70), width=4)
        for x in range(0, W, 120):
            d.line([x, 380, x, 1380], fill=L.hexc("#ffffff", 70), width=4)
        L._rr(d, [-20, 120, 330, 420], 20, L.hexc("#f3e6d3"))
        L._rr(d, [750, 120, 1100, 420], 20, L.hexc("#f3e6d3"))
        d.line([155, 120, 155, 420], fill=INK, width=6)
        d.line([925, 120, 925, 420], fill=INK, width=6)
    elif name == "bedroom":
        L._rr(d, [700, 300, 1000, 700], 20, L.hexc("#cad8f3"))
        d.line([850, 300, 850, 700], fill=INK, width=8)
        d.line([700, 500, 1000, 500], fill=INK, width=8)
        d.rectangle([0, 1500, W, H], fill=L.hexc("#d9b99a"))
    elif name in ("xmas", "snowy", "night"):
        win = L.hexc("#2b3a67") if name != "xmas" else L.hexc("#9db4e0")
        d.rectangle([0, 1500, W, H], fill=L.hexc("#c99a6e" if name == "xmas" else "#d9b99a"))
        L._rr(d, [120, 420, 560, 900], 20, L.hexc("#ffffff"))
        d.rectangle([146, 446, 534, 874], fill=win)
        d.line([340, 446, 340, 874], fill=INK, width=8); d.line([146, 660, 534, 660], fill=INK, width=8)
        d.rectangle([146, 820, 534, 874], fill=L.hexc("#ffffff"))
        if name == "night":
            d.ellipse([420, 480, 500, 560], fill=L.hexc("#fff3b0"))
        if name == "xmas":
            tx, ty = 860, 1500
            for k, (w_, y_) in enumerate(((330, 0), (260, -260), (190, -500))):
                d.polygon([(tx - w_, ty + y_ - 20), (tx + w_, ty + y_ - 20), (tx, ty + y_ - 380)], fill=L.hexc("#2e8b57"), outline=INK, width=8)
            d.rectangle([tx - 40, ty - 20, tx + 40, ty + 40], fill=L.hexc("#8b5a2b"), outline=INK, width=6)
            for gx, gc in ((640, "#e63946"), (1000, "#4cc9a0")):
                L._rr(d, [gx - 70, 1430, gx + 70, 1540], 10, L.hexc(gc))
                d.rectangle([gx - 10, 1430, gx + 10, 1540], fill=L.hexc("#ffd23f"))
    elif name == "living":
        d.rectangle([0, 1480, W, H], fill=L.hexc("#d9b99a"))
        L._rr(d, [90, 420, 330, 640], 16, L.hexc("#fff3e0"))
        d.ellipse([170, 470, 250, 550], fill=L.hexc("#ffb7c5"), outline=INK, width=6)
    return im


def set_fg(d, name):
    if name == "counter":
        L._rr(d, [-30, 1390, W + 30, 1460], 14, L.hexc("#e0c49e"))
        L._rr(d, [-30, 1455, W + 30, H + 40], 0, L.hexc("#f3e6d3"))
        for x in (270, 540, 810):
            d.line([x, 1460, x, H], fill=INK, width=7)
        for x in (225, 495, 765):
            d.ellipse([x, 1560, x + 26, 1586], fill=INK)
    elif name == "blanket":
        L._rr(d, [-30, 1380, W + 30, H + 40], 60, L.hexc("#ffc7d4"))
        for x in range(40, W, 140):
            d.line([x, 1400, x + 60, 1560], fill=L.hexc("#ff9fb5"), width=12)
    elif name == "sofa":
        L._rr(d, [-30, 1400, W + 30, H + 40], 50, L.hexc("#8fb8de"))


# ---------------------------------------------------------------- props
def prop(d, p, t):
    k = p["kind"]
    x, y = L.kf(p.get("x"), t, 540), L.kf(p.get("y"), t, 1380)
    s = L.kf(p.get("s"), t, 1.0)
    rot = L.kf(p.get("rot"), t, 0.0)
    if k == "cookie":
        r = 62 * s
        d.ellipse([x - r, y - r, x + r, y + r], fill=L.hexc("#d9a15b"), outline=INK, width=8)
        for i, (dx, dy) in enumerate(((-25, -20), (20, -28), (8, 18), (-30, 22), (32, 12))):
            a = rot + i
            d.ellipse([x + dx * s - 9 * s, y + dy * s - 9 * s, x + dx * s + 9 * s, y + dy * s + 9 * s], fill=L.hexc("#5a3a22"))
    elif k == "half_cookie":
        r = 62 * s
        d.chord([x - r, y - r, x + r, y + r], 200, 520, fill=L.hexc("#d9a15b"), outline=INK, width=8)
    elif k == "crumbs":
        rng = np.random.default_rng(3)
        for i in range(10):
            dx, dy = rng.uniform(-90, 90), rng.uniform(-20, 20)
            d.ellipse([x + dx - 9, y + dy - 9, x + dx + 9, y + dy + 9], fill=L.hexc("#d9a15b"), outline=INK, width=3)
    elif k == "plate":
        d.ellipse([x - 150 * s, y - 34 * s, x + 150 * s, y + 34 * s], fill=L.hexc("#ffffff"), outline=INK, width=8)
    elif k == "jar":
        L._rr(d, [x - 90 * s, y - 230 * s, x + 90 * s, y], 30, L.hexc("#e8f3ff"))
        L._rr(d, [x - 70 * s, y - 270 * s, x + 70 * s, y - 220 * s], 14, L.hexc("#c99a6e"))
        for i in range(0 if p.get("empty") else 3):
            d.ellipse([x - 50 * s + i * 30 * s, y - 120 * s + (i % 2) * 40 * s, x + 10 * s + i * 30 * s, y - 60 * s + (i % 2) * 40 * s],
                      fill=L.hexc("#d9a15b"), outline=INK, width=5)
    elif k == "cookie_tray":
        L._rr(d, [x - 220 * s, y - 20 * s, x + 220 * s, y + 30 * s], 14, L.hexc("#c9ced6"))
        for i, (dx, dy) in enumerate(((-140, -50), (-50, -60), (40, -55), (130, -48), (-95, -110), (0, -118), (90, -108), (-45, -165), (45, -165))):
            r = 52 * s
            cx_, cy_ = x + dx * s, y + dy * s
            d.ellipse([cx_ - r, cy_ - r, cx_ + r, cy_ + r], fill=L.hexc("#d9a15b"), outline=INK, width=7)
            for (ex_, ey_) in ((-18, -14), (14, -20), (4, 14)):
                d.ellipse([cx_ + ex_ * s - 7 * s, cy_ + ey_ * s - 7 * s, cx_ + ex_ * s + 7 * s, cy_ + ey_ * s + 7 * s], fill=L.hexc("#5a3a22"))
    elif k == "bag":
        col = L.hexc(p.get("color", "#ff8fab"))
        L._rr(d, [x - 80 * s, y - 170 * s, x + 80 * s, y], 10, col)
        d.arc([x - 45 * s, y - 230 * s, x + 45 * s, y - 120 * s], 180, 360, fill=INK, width=10)
        d.text((x - 30 * s, y - 120 * s), "%", font=ImageFont.truetype(L.FONT, int(80 * s)), fill=INK)
    elif k == "laptop":
        L._rr(d, [x - 190 * s, y - 230 * s, x + 190 * s, y - 20 * s], 16, L.hexc("#3a3d46"))
        d.rectangle([x - 165 * s, y - 205 * s, x + 165 * s, y - 45 * s], fill=L.hexc(p.get("screen", "#1b1d22")))
        L._rr(d, [x - 230 * s, y - 24 * s, x + 230 * s, y + 6 * s], 8, L.hexc("#9aa0ab"))
    elif k == "clock":
        L._rr(d, [x - 220 * s, y - 120 * s, x + 220 * s, y + 120 * s], 30, L.hexc("#2b2d33"))
        txt = p.get("text", "11:59") if t < p.get("switch", 99) else p.get("text2", "12:00")
        f_ = ImageFont.truetype(L.FONT, int(150 * s))
        d.text((x - d.textlength(txt, font=f_) / 2, y - 95 * s), txt, font=f_, fill=L.hexc("#ff4d4d" if t < p.get("switch", 99) else "#7ad67a"))
    elif k == "gift":
        L._rr(d, [x - 80 * s, y - 130 * s, x + 80 * s, y], 8, L.hexc("#4cc9a0"))
        d.rectangle([x - 12 * s, y - 130 * s, x + 12 * s, y], fill=L.hexc("#e63946"))
    elif k == "phone":
        L._rr(d, [x - 60 * s, y - 110 * s, x + 60 * s, y + 110 * s], 20, L.hexc("#9ec5ff"))
    elif k == "zzz_cloud":
        d.ellipse([x - 160, y - 70, x + 160, y + 70], fill=L.hexc("#ffffff", 220), outline=INK, width=6)


# ---------------------------------------------------------------- actors
def actor_img(a, t, f, talk=0.0):
    st = dict(pick(a["states"], t))
    if talk > 0.04 and not st.get("no_lipsync"):
        st["mouth"] = "open" if (talk > 0.09 and f % 4 < 3) else ("o" if f % 4 < 2 else st.get("mouth", "w"))
    img = L.draw_cat(a["char"], st, t, f)
    size = int(a.get("size", 900) * L.kf(a.get("grow"), t, 1.0))
    img = img.resize((size, size), Image.LANCZOS)
    flip = pick(a["flip"], t) if a.get("flip") else False
    if flip:
        img = ImageOps.mirror(img)
    return img, size, st


def render(sk, out):
    shots = sk["shots"]
    total = sum(s["dur"] for s in shots)
    a = L.music(total, hash(out) % 1000, sk.get("mood", "sweet")) * sk.get("music_level", 0.55)
    if sk.get("sfx"):
        a = a + L.sfx_track(len(a), sk["sfx"])
    env = {}
    for vc in sk.get("voices", []):
        v, vsr = sf.read(vc["file"], dtype="float32")
        v = v.mean(axis=1) if v.ndim > 1 else v
        if vsr != SR:
            v = np.interp(np.arange(0, len(v), vsr / SR), np.arange(len(v)), v).astype(np.float32)
        o = int(vc["t"] * SR); e = min(len(a), o + len(v))
        a[o:e] += v[: e - o] * vc.get("gain", 1.0)
        arr = env.setdefault(vc["who"], np.zeros(int(total * FPS) + 2))
        for k in range(int(len(v) / SR * FPS)):
            seg = v[int(k / FPS * SR): int((k + 1) / FPS * SR)]
            idx = int(vc["t"] * FPS) + k
            if idx < len(arr) and len(seg):
                arr[idx] = float(np.sqrt(np.mean(seg ** 2)))
    if sk.get("voice"):
        v, vsr = sf.read(sk["voice"]["file"], dtype="float32")
        v = v.mean(axis=1) if v.ndim > 1 else v
        o = int(sk["voice"].get("t", 0) * SR)
        e = min(len(a), o + len(v))
        a[o:e] += v[: e - o]
    a = a / max(1.0, float(np.max(np.abs(a))) / 0.95)
    sf.write(out + ".wav", a, SR)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", out + ".wav",
                             "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
                             "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
                            stdin=subprocess.PIPE)
    starts, acc = [], 0
    for s in shots:
        starts.append(acc); acc += s["dur"]
    bgs = {}
    wm = ImageFont.truetype(L.FONT, 46)
    for fr in range(int(total * FPS)):
        t = fr / FPS
        i = max(j for j in range(len(shots)) if starts[j] <= t)
        sh, ts = shots[i], t - starts[i]
        key = (sh.get("set", "plain"), sh.get("bg", "#ffe3bf"))
        if key not in bgs:
            bgs[key] = set_bg(*key)
        world = bgs[key].copy()
        d = ImageDraw.Draw(world)
        for p in sh.get("props_back", []):
            if p.get("t0", 0) <= ts <= p.get("t1", 99):
                prop(d, p, ts)
        if sh.get("lights_on") is not None and ts >= sh["lights_on"]:
            for k in range(14):
                lx = 860 + math.sin(k * 2.1) * (60 + k * 16); ly = 1000 + k * 33
                col = ("#ffd23f", "#ff6b6b", "#7fd6ff", "#b388ff")[k % 4]
                on = (int(t * 4) + k) % 3 != 0
                d.ellipse([lx - 16, ly - 16, lx + 16, ly + 16], fill=L.hexc(col if on else "#555555"), outline=INK, width=4)
        if sh.get("star_at") is not None and ts >= sh["star_at"]:
            r_ = 70; pts = []
            for k in range(10):
                a_ = -math.pi / 2 + k * math.pi / 5; rr = r_ if k % 2 == 0 else r_ * 0.45
                pts.append((860 + math.cos(a_) * rr, 760 + math.sin(a_) * rr))
            d.polygon(pts, fill=L.hexc("#ffd23f"), outline=INK, width=7)
        for ac in sh.get("actors", []):
            who = ac.get("who")
            img, size, st = actor_img(ac, ts, fr, env[who][fr] if who in env and fr < len(env[who]) else 0.0)
            x, gy = L.kf(ac.get("x"), ts, 540), L.kf(ac.get("y"), ts, 1400)
            hop = abs(math.sin(ts * math.pi * 4)) * 40 * L.kf(ac.get("walk"), ts, 0)
            world.alpha_composite(img, (int(x - size / 2), int(gy - 0.80 * size - hop)))
            d = ImageDraw.Draw(world)
            L.extras(d, st, ts, 1.0, x, gy - 0.29 * size)
        if sh.get("snow"):
            for k in range(16):
                ph = (t * 0.3 + k / 16) % 1
                x_ = 160 + (k * 97) % 360 + 10 * math.sin(t * 2 + k); y_ = 460 + ph * 360
                d.ellipse([x_ - 8, y_ - 8, x_ + 8, y_ + 8], fill=L.hexc("#ffffff"))
        set_fg(d, sh.get("fg"))
        for p in sh.get("props", []):
            if p.get("t0", 0) <= ts <= p.get("t1", 99):
                prop(d, p, ts)
        # camera over the whole set
        cam = sh.get("cam", {})
        z = L.kf(cam.get("zoom"), ts, 1.0)
        cx, cy = L.kf(cam.get("x"), ts, W / 2), L.kf(cam.get("y"), ts, H / 2)
        shk = L.kf(cam.get("shake"), ts, 0)
        cx += shk * 18 * math.sin(t * 47); cy += shk * 14 * math.cos(t * 41)
        cw, ch = W / z, H / z
        x0 = min(max(0, cx - cw / 2), W - cw); y0 = min(max(0, cy - ch / 2), H - ch)
        frame = world.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)
        # screen-space overlays
        for stk in sk.get("stickers", []):
            L.sticker(frame, stk, t)
        d = ImageDraw.Draw(frame)
        if sk.get("caption"):
            hf = ImageFont.truetype(L.FONT, 90)
            words, lines, cur = sk["caption"].split(" "), [], ""
            for w_ in words:
                test = (cur + " " + w_).strip()
                if d.textlength(test, font=hf) > W - 160:
                    lines.append(cur); cur = w_
                else:
                    cur = test
            lines.append(cur)
            bw = max(d.textlength(l_, font=hf) for l_ in lines)
            d.rounded_rectangle([(W - bw) / 2 - 40, 352, (W + bw) / 2 + 40, 376 + len(lines) * 104 + 14], 36,
                                fill=(255, 255, 255, 240), outline=INK, width=6)
            for k_, l_ in enumerate(lines):
                d.text(((W - d.textlength(l_, font=hf)) / 2, 376 + k_ * 104), l_, font=hf, fill=INK)
        for ov in sk.get("overlays", []):
            if ov["kind"] == "loading" and ov["t0"] <= t <= ov["t1"]:
                pct = L.kf(ov["keys"], t, 0)
                bx0, by0, bw_ = 190, 1580, 700
                d.rounded_rectangle([bx0, by0, bx0 + bw_, by0 + 70], 35, fill=(255, 255, 255, 235), outline=INK, width=7)
                d.rounded_rectangle([bx0 + 10, by0 + 10, bx0 + 10 + (bw_ - 20) * pct / 100, by0 + 60], 25, fill=L.hexc("#7ad67a"))
                lf = ImageFont.truetype(L.FONT, 70); lab = f"{ov.get('label', 'loading')} {int(pct)}%"
                d.text(((W - d.textlength(lab, font=lf)) / 2, by0 - 95), lab, font=lf, fill=INK, stroke_width=6, stroke_fill=(255, 255, 255))
        hd = sk.get("handle", "@katthecattoons")
        d.text(((W - d.textlength(hd, font=wm)) / 2, H * 0.93), hd, font=wm, fill=INK[:3] + (70,))
        # quick flash on cuts
        if i > 0 and ts < 0.06:
            frame = Image.blend(frame, Image.new("RGBA", (W, H), (255, 255, 255, 255)), 0.35)
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close(); proc.wait()
    return total


if __name__ == "__main__":
    sk = json.load(open(sys.argv[1]))
    print(f"{render(sk, sys.argv[2]):.1f}s -> {sys.argv[2]}")
