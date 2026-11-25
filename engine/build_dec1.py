"""Kat 2.0 batch Nov 30 - Dec 7 (14 skits). Usage: python3 build_dec1.py [slug ...]"""
import json, os, subprocess, sys, urllib.request

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs("kat2/audio", exist_ok=True)
KEY = open(os.path.expanduser("~/.kat/key")).read().strip()
VOICE = {"kat": "g4hzXZZhL5vwjYdqQDDM", "bf": "bIHbv24MWmeRgasZH58o"}
KAT = {"color": "#ffffff", "inner": "#ffb7c5"}
BF = {"male": True, "color": "#f3e2c4", "inner": "#d6bf98", "brow_col": "#8a6a40", "eye_style": "sleepy",
      "nose_col": "#8a6a40", "big_nose": True}
K = lambda **kw: dict(pose="sit", **kw)


def voice(tag, who, text):
    mp3 = f"kat2/audio/{tag}.mp3"; wav = mp3[:-4] + ".wav"
    if not os.path.exists(mp3):
        req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE[who]}?output_format=mp3_44100_128",
                                     data=json.dumps({"text": text, "model_id": "eleven_v4"}).encode(),
                                     headers={"xi-api-key": KEY, "Content-Type": "application/json"})
        open(mp3, "wb").write(urllib.request.urlopen(req, timeout=120).read())
    if not os.path.exists(wav):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-af",
                        "silenceremove=start_periods=1:start_threshold=-40dB,areverse,silenceremove=start_periods=1:start_threshold=-40dB,areverse",
                        "-ac", "1", "-ar", "44100", wav], check=True)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav],
                             capture_output=True, text=True).stdout)
    return wav, d


def build(slug, caption, shots, mood="sweet"):
    """shots: dict(dur_min, lines=[(who,text)], pre, post, + render keys; stickers/sfx with times relative to shot)."""
    out, voices, stickers, sfx, t = [], [], [], [], 0.0
    for i, sh in enumerate(shots):
        sh = dict(sh)
        lt, cursor = [], sh.pop("pre", 0.3)
        for j, (who, text) in enumerate(sh.pop("lines", [])):
            wav, d = voice(f"{slug}_{i}{j}", who, text)
            voices.append(dict(file=wav, t=round(t + cursor, 2), who=who))
            lt.append(cursor); cursor += d + 0.25
        dur = max(sh.pop("dur_min", 1.5), cursor + sh.pop("post", 0.4))
        for st in sh.pop("stickers", []):
            txt, a, b, x, y, col = st[:6]
            stickers.append(dict(text=txt, t0=round(t + a, 2), t1=round(t + min(b, dur), 2), x=x, y=y,
                                 size=st[6] if len(st) > 6 else 110, color=col, rot=st[7] if len(st) > 7 else -6))
        for a, kind, vol in sh.pop("sfx", []):
            sfx.append(dict(t=round(t + a, 2), kind=kind, vol=vol))
        sh["dur"] = round(dur, 2)
        out.append(sh); t += dur
    sk = {"caption": caption, "mood": mood, "music_level": 0.28, "shots": out, "voices": voices,
          "stickers": stickers, "sfx": sfx}
    for ov in shots[0].get("_overlays", []):
        pass
    json.dump(sk, open(f"kat2/{slug}.json", "w"), indent=1)
    print(slug, round(t, 1), "s")
    return sk


def cam(z0, z1, x, y, dur=20, shake=None):
    c = {"zoom": [[0, z0], [dur, z1]], "x": [[0, x]], "y": [[0, y]]}
    if shake:
        c["shake"] = shake
    return c


def kat(states, x=330, y=1450, size=1000, **kw):
    return dict(char=KAT, who="kat", x=[[0, x]] if isinstance(x, (int, float)) else x,
                y=[[0, y]] if isinstance(y, (int, float)) else y, size=size, states=states, **kw)


def bf(states, x=780, y=1440, size=1150, **kw):
    return dict(char=BF, who="bf", x=[[0, x]] if isinstance(x, (int, float)) else x,
                y=[[0, y]] if isinstance(y, (int, float)) else y, size=size, states=states, **kw)


ONLY = set(sys.argv[1:])
_build = build


def build(slug, caption, shots, mood="sweet"):
    if ONLY and slug not in ONLY:
        return None
    return _build(slug, caption, shots, mood)


def crash(x, y, z=2.4, shake=None, dur=20):
    c = {"zoom": [[0, 1.0], [0.25, z], [dur, z + 0.1]], "x": [[0, x]], "y": [[0, y]]}
    if shake:
        c["shake"] = shake
    return c


def dart(n=8, step=0.32, sweat="sweat_big", **kw):
    return [[i * step, K(eyes="open", mouth="wobble", look=(1 if i % 2 else -1), extras=[sweat], **kw)] for i in range(n)]


SH = [[0, 0.3], [0.4, 0.8], [3, 0.6]]
# floor / counter / sofa head points
KF, BFF = (330, 1240), (780, 1190)
KC, BC = (330, 1090), (780, 1030)
KS, BS = (380, 1225), (720, 1165)
WF, WC = (555, 1180), (555, 1100)
cookie_k = dict(kind="cookie", x=[[0, 330]], y=[[0, 1600]], s=[[0, 1]])

# ---------------------------------------------------------------- 1. advent (Kat guilty)
S = dict(set="xmas", bg="#d5e9cf")
crumbs = dict(kind="crumbs", x=[[0, 330]], y=[[0, 1610]])
box = dict(kind="gift", x=[[0, 560]], y=[[0, 1610]], s=[[0, 0.9]])
build("advent", "tag the one who opens the advent calendar early 🍫", [
    dict(S, dur_min=2.8, cam=cam(1.0, 1.08, *WF), props=[box], lines=[("bf", "[sleepy] advent calendar starts tomorrow, babe.")],
         actors=[kat([[0, K(eyes="happy", mouth="w", hold="cookie", hat="santa", look=-1)]], y=1600, size=950),
                 bf([[0, K(eyes="open", mouth="smirk", hat="santa", look=-1)]], y=1600, size=1100)]),
    dict(S, dur_min=1.8, cam=crash(*KF), props=[box, dict(crumbs, t0=0.3)],
         actors=[kat([[0, K(eyes="open", mouth="wobble", hold="cookie", hat="santa", extras=["sweat"])]], y=1600, size=950),
                 bf([[0, K(eyes="open", mouth="smirk", hat="santa", look=-1)]], y=1600, size=1100)],
         stickers=[("*evidence*", 0.3, 1.8, 330, 700, "#ffd23f", 120)], sfx=[(0.05, "sting", 0.4)]),
    dict(S, dur_min=2.4, cam=cam(2.1, 2.3, *BFF), props=[box, crumbs], lines=[("bf", "[suspicious] ...why are all 24 doors open?")],
         actors=[kat([[0, K(eyes="open", mouth="wobble", hat="santa")]], y=1600, size=950),
                 bf([[0, K(eyes="flat", mouth="o", hat="santa", look=-1)]], y=1600, size=1100)],
         stickers=[("24/24 open", 0.4, 2.4, 780, 700, "#ffffff", 110)], sfx=[(0.3, "gulp", 0.4)]),
    dict(S, dur_min=2.4, cam=cam(2.2, 2.5, *KF, shake=SH), props=[box, crumbs], lines=[("kat", "[nervous laugh] they opened themselves!")],
         actors=[kat(dart(hat="santa", shake=0.5), y=1600, size=950),
                 bf([[0, K(eyes="flat", mouth="smirk", hat="santa", look=-1)]], y=1600, size=1100)],
         stickers=[("*sweating*", 0.1, 2.0, 330, 700, "#9fd8ff")]),
    dict(S, dur_min=3.8, cam=cam(1.05, 1.15, *WF), props=[box, crumbs], lights_on=0.2,
         lines=[("kat", "[softly] ...i saved you one."), ("bf", "[giggles] my little thief.")],
         actors=[kat([[0, K(eyes="teary", mouth="w", hold="cookie", hat="santa", look=1)], [1.8, K(eyes="happy", mouth="w", hold="cookie", hat="santa", blush="big", extras=["hearts"])]], y=1600, size=950),
                 bf([[0, K(eyes="open", mouth="o", hat="santa", look=-1)], [1.6, K(eyes="happy", mouth="smirk", hat="santa", look=-1, extras=["hearts"])]], y=1600, size=1100)],
         stickers=[("ta-da!", 1.8, 3.8, 555, 680, "#ffd23f", 140)], sfx=[(1.7, "tada", 0.4)]),
])

# ---------------------------------------------------------------- 2. on read (him guilty)
S = dict(set="night", bg="#cad8f3", fg="blanket")
build("on_read", "tag the one who leaves you on read 📱", [
    dict(S, dur_min=2.8, cam=cam(2.0, 2.15, *KC), lines=[("kat", "[sighs] he read it... three minutes ago.")],
         actors=[kat([[0, K(eyes="open", mouth="sad", hold="phone", ears=-1)]])],
         stickers=[("seen 8:02", 0.3, 2.8, 330, 700, "#ffffff", 110)]),
    dict(S, dur_min=2.0, cam=crash(*KC, shake=[[0, 0.9], [2, 0.6]]), lines=[("kat", "[crying] he doesn't love me anymore!")],
         actors=[kat([[0, K(eyes="cry", mouth="open", hold="phone", ears=-1, shake=1.0)]])],
         stickers=[("NOOOO", 0.2, 2.6, 330, 700, "#ff6b6b", 150)], sfx=[(0.05, "sting", 0.45)]),
    dict(S, dur_min=2.6, cam=cam(1.0, 1.08, *WC), lines=[("bf", "[nervous] babe... i was making cocoa.")], pre=1.0,
         actors=[kat([[0, K(eyes="teary", mouth="sad", hold="phone", look=1)]]),
                 bf([[0, K(eyes="flat", mouth="w", hold="mug", look=-1, extras=["sweat"])]], x=[[0, 1250], [0.9, 780]], walk=[[0, 1], [0.9, 0]])],
         sfx=[(1.0, "gulp", 0.4)]),
    dict(S, dur_min=2.4, cam=cam(1.3, 1.45, 555, 1060), lines=[("kat", "[sniffles] you could've typed 'ok'.")],
         actors=[kat([[0, K(eyes="teary", mouth="wobble", look=1)]]),
                 bf(dart(hold="mug"))]),
    dict(S, dur_min=4.0, cam=cam(1.05, 1.15, *WC), lines=[("bf", "[softly] i'd rather say it in person. ok.")],
         actors=[kat([[0, K(eyes="open", mouth="o", look=1)], [2.0, K(eyes="happy", mouth="w", hold="mug", blush="big", extras=["hearts"])]]),
                 bf([[0, K(eyes="open", mouth="smirk", hold="mug", look=-1)], [2.0, K(eyes="happy", mouth="smirk", look=-1, extras=["hearts"])]])],
         stickers=[("*forgiven*", 2.2, 4.0, 555, 680, "#ff9fb5", 130)], sfx=[(2.0, "ding", 0.4)]),
])

# ---------------------------------------------------------------- 3. shake gift (Kat guilty)
S = dict(set="xmas", bg="#f9d9e6", lights_on=0)
build("shake_gift", "tag the one who shakes every gift 🎁", [
    dict(S, dur_min=2.8, cam=cam(2.0, 2.2, *KF), lines=[("kat", "[whispers] just one tiny shake...")],
         actors=[kat([[0, K(eyes="happy", mouth="w", hold="gift", hat="santa")], [1.0, K(eyes="squeeze", mouth="w", hold="gift", hat="santa", shake=1.2)]], y=1600, size=950)],
         stickers=[("*rattle*", 1.0, 2.0, 200, 800, "#ffd23f", 100, -10), ("*rattle*", 1.6, 2.8, 470, 900, "#ffd23f", 100, 8)],
         sfx=[(1.0, "boing", 0.3), (1.5, "boing", 0.3), (2.0, "boing", 0.3)]),
    dict(S, dur_min=2.0, cam=cam(1.0, 1.08, *WF), lines=[("bf", "[confident] babe. put it down.")],
         actors=[kat([[0, K(eyes="squeeze", mouth="w", hold="gift", hat="santa", shake=1.0)]], y=1600, size=950),
                 bf([[0, K(eyes="flat", mouth="smirk", look=-1)]], y=1600, size=1100)]),
    dict(S, dur_min=1.6, cam=crash(*KF),
         actors=[kat([[0, K(eyes="open", mouth="wobble", hold="gift", hat="santa", extras=["sweat"])]], y=1600, size=950),
                 bf([[0, K(eyes="flat", mouth="smirk", look=-1)]], y=1600, size=1100)],
         stickers=[("*caught*", 0.2, 1.6, 330, 700, "#ff6b6b", 130)], sfx=[(0.05, "sting", 0.45)]),
    dict(S, dur_min=2.4, cam=cam(2.2, 2.45, *KF, shake=SH), lines=[("kat", "[nervous laugh] i was checking it's... safe?")],
         actors=[kat(dart(hold="gift", hat="santa"), y=1600, size=950),
                 bf([[0, K(eyes="flat", mouth="smirk", look=-1)]], y=1600, size=1100)]),
    dict(S, dur_min=4.4, cam=cam(1.05, 1.15, *WF),
         lines=[("bf", "[sighs] [softly] fine. open it."), ("kat", "[gasps] it's a locket of us!")],
         actors=[kat([[0, K(eyes="open", mouth="o", hold="gift", hat="santa", look=1)], [2.0, K(eyes="happy", mouth="open", hold="heart", hat="santa", blush="big", extras=["sparkles", "hearts"])]], y=1600, size=950),
                 bf([[0, K(eyes="open", mouth="smirk", look=-1)], [2.4, K(eyes="happy", mouth="smirk", look=-1, extras=["hearts"])]], y=1600, size=1100)],
         stickers=[("ta-da!", 2.0, 4.4, 555, 680, "#ffd23f", 140)], sfx=[(2.0, "tada", 0.4)]),
])

# ---------------------------------------------------------------- 4. forgot (him guilty)
S = dict(set="kitchen", bg="#ffe3bf", fg="counter")
build("forgot", "when he pretends he forgot 💐", [
    dict(S, dur_min=2.6, cam=cam(1.0, 1.08, *WC), lines=[("kat", "[excited] babe! do you know what today is?")],
         actors=[kat([[0, K(eyes="happy", mouth="open", bounce=1.0, look=1)]]), bf([[0, K(eyes="open", mouth="smirk", look=-1)]])]),
    dict(S, dur_min=2.0, cam=cam(2.1, 2.3, *BC), lines=[("bf", "[nervous] ...tuesday?")],
         actors=[kat([[0, K(eyes="open", mouth="o", look=1)]]), bf([[0, K(eyes="open", mouth="wobble", look=1, extras=["sweat"])]])],
         stickers=[("*gulp*", 0.3, 2.0, 780, 650, "#9fd8ff", 120)], sfx=[(0.2, "gulp", 0.4)]),
    dict(S, dur_min=2.2, cam=crash(*KC, shake=[[0, 0.9], [2, 0.6]]), lines=[("kat", "[crying] you forgot!")],
         actors=[kat([[0, K(eyes="cry", mouth="open", ears=-1, shake=1.0)]]), bf([[0, K(eyes="open", mouth="wobble")]])],
         stickers=[("NOOOO", 0.2, 2.2, 330, 680, "#ff6b6b", 150)], sfx=[(0.05, "sting", 0.45)]),
    dict(S, dur_min=1.8, cam=cam(2.2, 2.4, *BC, shake=SH),
         actors=[kat([[0, K(eyes="cry", mouth="sad", ears=-1)]]), bf(dart(n=6))],
         stickers=[("*sweating*", 0.1, 1.8, 780, 650, "#9fd8ff")]),
    dict(S, dur_min=4.0, cam=cam(1.05, 1.15, *WC), lines=[("bf", "[giggles] two years. i never forget.")],
         actors=[kat([[0, K(eyes="teary", mouth="o", look=1)], [1.6, K(eyes="happy", mouth="w", blush="big", look=1, extras=["hearts"])]]),
                 bf([[0, K(eyes="open", mouth="smirk", hold="flower", look=-1)], [1.6, K(eyes="happy", mouth="smirk", hold="flower", look=-1, extras=["hearts"])]])],
         stickers=[("swoon", 1.8, 4.0, 330, 680, "#ff9fb5", 130)], sfx=[(0.2, "ding", 0.4)]),
])

# ---------------------------------------------------------------- 5. cookie dough (Kat guilty)
S = dict(set="kitchen", bg="#f7cddc", fg="counter")
jar = dict(kind="jar", x=[[0, 565]], y=[[0, 1400]], s=[[0, 0.75]], empty=True)
cr = dict(kind="crumbs", x=[[0, 330]], y=[[0, 1400]])
build("cookie_dough", "tag the one who eats all the cookie dough 🍪", [
    dict(S, dur_min=2.6, cam=cam(1.0, 1.08, *WC), props=[jar], lines=[("bf", "[confident] okay. time to bake the cookies.")],
         actors=[kat([[0, K(eyes="open", mouth="w", hat="santa", look=-1)]]), bf([[0, K(eyes="open", mouth="smirk", hat="santa", look=-1)]])]),
    dict(S, dur_min=1.6, cam=crash(565, 1250, z=2.2), props=[jar],
         actors=[kat([[0, K(eyes="open", mouth="w", hat="santa", look=-1)]]), bf([[0, K(eyes="open", mouth="o", hat="santa", look=-1)]])],
         stickers=[("*empty*", 0.3, 1.6, 540, 800, "#ffffff", 130)], sfx=[(0.05, "sting", 0.4)]),
    dict(S, dur_min=2.2, cam=cam(2.1, 2.3, *BC), props=[jar], lines=[("bf", "[suspicious] where'd the dough go?")],
         actors=[kat([[0, K(eyes="open", mouth="wobble", hat="santa")]]), bf([[0, K(eyes="flat", mouth="o", hat="santa", look=-1)]])]),
    dict(S, dur_min=2.2, cam=crash(330, 1180, z=2.0, shake=SH), props=[jar, cr], lines=[("kat", "[nervous laugh] ...what dough?")],
         actors=[kat(dart(hat="santa")), bf([[0, K(eyes="flat", mouth="o", hat="santa", look=-1)]])],
         stickers=[("*evidence*", 0.4, 2.2, 330, 700, "#ffd23f", 120)]),
    dict(S, dur_min=4.2, cam=cam(1.05, 1.15, *WC), props=[jar, cr],
         lines=[("kat", "[sniffles] i'm sorry, it was too yummy."), ("bf", "[softly] good thing i bought two.")],
         actors=[kat([[0, K(eyes="teary", mouth="sad", hat="santa", look=1)], [2.6, K(eyes="happy", mouth="w", hat="santa", blush="big", extras=["hearts"])]]),
                 bf([[0, K(eyes="open", mouth="smirk", hat="santa", look=-1)], [2.0, K(eyes="happy", mouth="smirk", hat="santa", hold="cookie", look=-1, extras=["hearts"])]])],
         stickers=[("ta-da!", 2.2, 4.2, 555, 680, "#ffd23f", 140)], sfx=[(2.0, "tada", 0.4)]),
])

# ---------------------------------------------------------------- 6. not cold (him guilty)
S = dict(set="snowy", bg="#cad8f3", snow=True)
kk = dict(x=300, y=1600, size=900)
bb = dict(x=760, y=1600, size=1050)
KN, BN = (300, 1270), (760, 1220)
build("not_cold", "tag the one who's \"not cold\" ❄️", [
    dict(S, dur_min=2.8, cam=cam(1.0, 1.08, 530, 1180), lines=[("kat", "[softly] babe, take my blanket. it's freezing.")],
         actors=[kat([[0, K(eyes="open", mouth="w", hold="pillow", look=1)]], **kk), bf([[0, K(eyes="open", mouth="smirk", look=-1)]], **bb)]),
    dict(S, dur_min=2.2, cam=cam(2.0, 2.2, *BN), lines=[("bf", "[confident] cold? i don't get cold.")],
         actors=[kat([[0, K(eyes="open", mouth="w", hold="pillow", look=1)]], **kk), bf([[0, K(eyes="happy", mouth="smirk", look=-1)]], **bb)]),
    dict(S, dur_min=2.0, cam=cam(2.0, 2.2, *BN),
         actors=[kat([[0, K(eyes="open", mouth="w", look=1)]], **kk), bf([[0, K(eyes="squeeze", mouth="wobble", shake=1.0, extras=["sweat"])]], **bb)],
         stickers=[("*shiver*", 0.2, 1.2, 600, 800, "#ffffff", 110, -8), ("*shiver*", 0.9, 2.0, 920, 900, "#ffffff", 110, 8)],
         sfx=[(0.2, "boing", 0.3), (0.9, "boing", 0.3)]),
    dict(S, dur_min=2.4, cam=crash(*KN, z=2.2), lines=[("kat", "[giggles] your teeth are chattering.")],
         actors=[kat([[0, K(eyes="flat", mouth="smirk", look=1)]], **kk), bf(dart(shake=0.8), **bb)]),
    dict(S, dur_min=1.8, cam=cam(2.0, 2.2, *BN, shake=SH),
         actors=[kat([[0, K(eyes="flat", mouth="w", look=1)]], **kk), bf(dart(n=6, shake=0.8), **bb)]),
    dict(S, dur_min=3.8, cam=cam(1.1, 1.2, 600, 1180), lines=[("bf", "[whispers] ...okay maybe a little cold.")], pre=1.0,
         actors=[bf([[0, K(eyes="happy", mouth="smirk", look=-1, extras=["hearts"])]], **bb),
                 kat([[0, K(eyes="happy", mouth="w", blush="big", look=1, extras=["hearts"])]], x=[[0, 300], [0.8, 470]], y=1600, size=900)],
         stickers=[("*warm now*", 1.2, 3.8, 600, 680, "#ff9fb5", 130)], sfx=[(0.8, "purr", 0.4)]),
])

# ---------------------------------------------------------------- 7. xmas movie (Kat guilty)
S = dict(set="night", bg="#e4d5f6", fg="sofa")
ks = dict(x=380, y=1570, size=950)
bs = dict(x=720, y=1560, size=1100)
build("xmas_movie", "tag the one who cries at every christmas movie 🎬", [
    dict(S, dur_min=2.6, cam=cam(1.0, 1.08, 550, 1150), lines=[("bf", "[sleepy] it's just a christmas movie, babe.")],
         actors=[kat([[0, K(eyes="teary", mouth="wobble", hold="mug")]], **ks), bf([[0, K(eyes="open", mouth="smirk", look=-1)]], **bs)]),
    dict(S, dur_min=2.2, cam=crash(*KS, shake=[[0, 0.9], [2, 0.6]]), lines=[("kat", "[crying] he found his puppy!")],
         actors=[kat([[0, K(eyes="cry", mouth="open", hold="mug", shake=1.2, ears=-1)]], **ks), bf([[0, K(eyes="open", mouth="smirk", look=-1)]], **bs)],
         stickers=[("NOOOO", 0.2, 2.2, 380, 700, "#ff6b6b", 150)], sfx=[(0.05, "sting", 0.45)]),
    dict(S, dur_min=2.2, cam=cam(2.0, 2.2, *BS), lines=[("bf", "[giggles] you're crying at the ad?")],
         actors=[kat([[0, K(eyes="cry", mouth="sad", hold="mug")]], **ks), bf([[0, K(eyes="flat", mouth="smirk", look=-1)]], **bs)],
         stickers=[("*it's an ad*", 0.4, 2.2, 720, 680, "#ffffff", 110)]),
    dict(S, dur_min=2.6, cam=cam(2.0, 2.25, *KS, shake=SH), lines=[("kat", "[nervous laugh] i'm not crying. you're crying.")],
         actors=[kat(dart(sweat="sweat", hold="mug"), **ks), bf([[0, K(eyes="flat", mouth="smirk", look=-1)]], **bs)]),
    dict(S, dur_min=3.6, cam=cam(1.5, 1.2, 600, 1150), lines=[("bf", "[sniffles] ...the puppy was cute.")],
         actors=[bf([[0, K(eyes="teary", mouth="wobble", look=-1)], [2.0, K(eyes="happy", mouth="smirk", look=-1, extras=["hearts"])]], **bs),
                 kat([[0, K(eyes="open", mouth="o", hold="mug", look=1)], [2.0, K(eyes="happy", mouth="w", hold="mug", blush="big", extras=["hearts"])]], x=[[0, 380], [2.0, 450]], y=1570, size=950)],
         sfx=[(2.0, "pop", 0.4)]),
])

# ---------------------------------------------------------------- 8. one more game (him guilty)
S = dict(set="living", bg="#d5e9cf", fg="counter")
lap = dict(kind="laptop", x=[[0, 620]], y=[[0, 1400]], s=[[0, 0.7]], screen="#7fd6ff")
lap_off = dict(lap, screen="#1b1d22")
clk = dict(kind="clock", x=[[0, 760]], y=[[0, 600]], s=[[0, 0.7]], text="8:00", text2="2:00", switch=99)
build("one_more_game", "when he says \"one more game\" 🎮", [
    dict(S, dur_min=3.0, cam=cam(1.0, 1.06, 555, 1050), props=[lap], props_back=[clk],
         lines=[("kat", "[softly] babe... dinner's ready."), ("bf", "[excited] one more game!")],
         actors=[kat([[0, K(eyes="happy", mouth="w", look=1)]]), bf([[0, K(eyes="open", mouth="smirk", look=-1)], [1.6, K(eyes="squeeze", mouth="open", bounce=1.0)]])]),
    dict(S, dur_min=1.8, cam=cam(2.4, 2.5, 760, 640), props=[lap], props_back=[dict(clk, switch=0.6)],
         actors=[kat([[0, K(eyes="open", mouth="w")]]), bf([[0, K(eyes="squeeze", mouth="w")]])],
         stickers=[("*6 hours later*", 0.4, 1.8, 540, 1050, "#ffffff", 110)], sfx=[(0.5, "whoosh", 0.4)]),
    dict(S, dur_min=2.2, cam=crash(*KC), props=[lap], props_back=[dict(clk, switch=0)], lines=[("kat", "[sighs] dinner's cold now.")],
         actors=[kat([[0, K(eyes="flat", mouth="sad", ears=-1, hold="cookie", look=1)]]), bf([[0, K(eyes="squeeze", mouth="w")]])],
         sfx=[(0.05, "sting", 0.4)]),
    dict(S, dur_min=2.2, cam=cam(2.1, 2.35, *BC, shake=SH), props=[lap], props_back=[dict(clk, switch=0)], lines=[("bf", "[nervous laugh] ...good game though?")],
         actors=[kat([[0, K(eyes="flat", mouth="sad", ears=-1)]]), bf(dart())],
         stickers=[("*guilty*", 0.2, 2.2, 780, 650, "#ff6b6b", 120)]),
    dict(S, dur_min=4.0, cam=cam(1.05, 1.12, 555, 1050), props=[lap_off], props_back=[dict(clk, switch=0)], lines=[("bf", "[softly] last game is you. movie night?")],
         actors=[kat([[0, K(eyes="open", mouth="o", look=1)], [2.0, K(eyes="happy", mouth="w", blush="big", extras=["hearts"])]]),
                 bf([[0, K(eyes="open", mouth="smirk", look=-1)], [2.0, K(eyes="happy", mouth="smirk", look=-1, extras=["hearts"])]])],
         stickers=[("*player 2*", 2.2, 4.0, 330, 760, "#ff9fb5", 120)], sfx=[(0.1, "pop", 0.3), (2.0, "ding", 0.4)]),
])

# ---------------------------------------------------------------- 9. group chat (Kat guilty)
S = dict(set="bedroom", bg="#f9d9e6")
fk, fb = dict(y=1600, size=950), dict(y=1600, size=1100)
build("group_chat", "tag the one who screenshots your texts 📸", [
    dict(S, dur_min=2.8, cam=cam(2.0, 2.2, *KF), lines=[("kat", "[giggles] he said 'goodnight my moon'...")],
         actors=[kat([[0, K(eyes="happy", mouth="w", hold="phone", blush="big")]], **fk)],
         stickers=[("*screenshot*", 1.6, 2.8, 330, 760, "#ffffff", 110)], sfx=[(1.6, "pop", 0.45)]),
    dict(S, dur_min=2.8, cam=cam(1.0, 1.06, *WF), lines=[("bf", "[suspicious] why is the group chat sending hearts?")], pre=0.9,
         actors=[kat([[0, K(eyes="happy", mouth="w", hold="phone")]], **fk),
                 bf([[0, K(eyes="flat", mouth="o", hold="phone", look=-1)]], x=[[0, 1250], [0.8, 780]], walk=[[0, 1], [0.8, 0]], **fb)]),
    dict(S, dur_min=1.6, cam=crash(*KF),
         actors=[kat([[0, K(eyes="open", mouth="wobble", hold="phone", extras=["sweat"])]], **fk), bf([[0, K(eyes="flat", mouth="o", look=-1)]], **fb)],
         stickers=[("*busted*", 0.2, 1.6, 330, 700, "#ff6b6b", 130)], sfx=[(0.05, "sting", 0.45)]),
    dict(S, dur_min=2.0, cam=cam(2.2, 2.45, *KF, shake=SH), lines=[("kat", "[nervous laugh] ...wrong chat?")],
         actors=[kat(dart(hold="phone"), **fk), bf([[0, K(eyes="flat", mouth="o", look=-1)]], **fb)]),
    dict(S, dur_min=3.6, cam=cam(1.05, 1.12, *WF), lines=[("bf", "[whispers] ...send them the cute one.")],
         actors=[kat([[0, K(eyes="open", mouth="o", hold="phone", look=1)], [1.8, K(eyes="happy", mouth="open", hold="phone", bounce=1.0, blush="big", extras=["hearts"])]], **fk),
                 bf([[0, K(eyes="open", mouth="smirk", look=1)], [1.8, K(eyes="happy", mouth="smirk", look=-1, extras=["hearts"])]], **fb)],
         stickers=[("*posted*", 2.0, 3.6, 555, 680, "#ff9fb5", 130)], sfx=[(1.8, "ding", 0.4)]),
])

# ---------------------------------------------------------------- 10. wrapping nap (him guilty)
S = dict(set="xmas", bg="#ffe3bf")
gifts = [dict(kind="gift", x=[[0, 610]], y=[[0, 1615]], s=[[0, 0.8]]), dict(kind="gift", x=[[0, 960]], y=[[0, 1620]], s=[[0, 0.9]]),
         dict(kind="gift", x=[[0, 1010]], y=[[0, 1500]], s=[[0, 0.6]])]
build("wrapping_nap", "tag the one who falls asleep wrapping gifts 😴", [
    dict(S, dur_min=2.6, cam=cam(1.0, 1.06, *WF), props=gifts, lines=[("bf", "[sleepy] i'll wrap the gifts, babe.")],
         actors=[kat([[0, K(eyes="happy", mouth="w", hat="santa", look=1)]], **fk), bf([[0, K(eyes="open", mouth="smirk", hat="santa", look=-1)]], **fb)]),
    dict(S, dur_min=2.2, cam=cam(2.0, 2.1, *BFF), props=gifts,
         actors=[bf([[0, K(eyes="closed", mouth="w", hat="santa", ears=-1, extras=["zzz"])]], **fb)],
         stickers=[("*5 min later*", 0.2, 2.2, 600, 760, "#ffffff", 110)], sfx=[(0.3, "purr", 0.4)]),
    dict(S, dur_min=2.6, cam=crash(555, 1200, z=1.5), props=gifts, lines=[("kat", "[gasps] you wrapped... yourself?!")], pre=0.5,
         actors=[bf([[0, K(eyes="closed", mouth="w", hat="santa", bowtie=True, extras=["zzz"])]], **fb),
                 kat([[0, K(eyes="open", mouth="o", hat="santa", look=1)]], x=[[0, -150], [0.5, 330]], walk=[[0, 1], [0.5, 0]], **fk)],
         stickers=[("*tape*", 0.6, 2.6, 700, 900, "#ffffff", 100, -12), ("*tape*", 0.9, 2.6, 900, 1080, "#ffffff", 100, 10),
                   ("*bow*", 1.2, 2.6, 780, 1500, "#e63946", 100, 0)], sfx=[(0.5, "sting", 0.4)]),
    dict(S, dur_min=2.4, cam=cam(2.0, 2.2, *BFF, shake=SH), props=gifts, lines=[("bf", "[nervous laugh] ...surprise. i'm your gift?")],
         actors=[kat([[0, K(eyes="open", mouth="o", hat="santa", look=1)]], **fk), bf(dart(hat="santa", bowtie=True, sweat="sweat"), **fb)]),
    dict(S, dur_min=3.6, cam=cam(1.05, 1.12, *WF), props=gifts, lights_on=0, lines=[("kat", "[giggles] best gift ever.")],
         actors=[bf([[0, K(eyes="happy", mouth="smirk", hat="santa", bowtie=True, look=-1, extras=["hearts"])]], **fb),
                 kat([[0, K(eyes="happy", mouth="w", hat="santa", blush="big", look=1, extras=["hearts"])]], x=[[0, 330], [1.0, 450]], **fk)],
         stickers=[("ta-da!", 1.2, 3.6, 555, 680, "#ffd23f", 140)], sfx=[(1.0, "tada", 0.4)]),
])

# ---------------------------------------------------------------- 11. matching sweaters (Kat guilty)
S = dict(set="living", bg="#f7cddc")
bag = dict(kind="bag", x=[[0, 560]], y=[[0, 1620]], s=[[0, 0.9]], color="#ff8fab")
build("matching_sweaters", "when she bought matching sweaters 🎄", [
    dict(S, dur_min=2.6, cam=cam(1.0, 1.06, *WF), props=[bag], lines=[("kat", "[sweetly] babe... promise you won't be mad?")],
         actors=[kat([[0, K(eyes="happy", mouth="w", hold="gift", look=1)]], **fk), bf([[0, K(eyes="open", mouth="smirk", look=-1)]], **fb)]),
    dict(S, dur_min=2.0, cam=cam(2.1, 2.3, *BFF), props=[bag], lines=[("bf", "[suspicious] ...what did you buy?")],
         actors=[kat([[0, K(eyes="happy", mouth="w", hold="gift")]], **fk), bf([[0, K(eyes="flat", mouth="o", look=-1)]], **fb)]),
    dict(S, dur_min=2.6, cam=crash(*KF, shake=SH), props=[bag], lines=[("kat", "[nervous laugh] maybe... matching sweaters?")],
         actors=[kat(dart(hold="gift"), **fk), bf([[0, K(eyes="flat", mouth="o", look=-1)]], **fb)],
         stickers=[("*sweating*", 0.2, 2.6, 330, 700, "#9fd8ff")], sfx=[(0.05, "gulp", 0.4)]),
    dict(S, dur_min=1.6, cam=cam(2.2, 2.4, *BFF), props=[bag],
         actors=[kat([[0, K(eyes="open", mouth="wobble", hold="gift")]], **fk), bf([[0, K(eyes="open", mouth="o", look=-1)]], **fb)],
         stickers=[("...", 0.3, 1.6, 780, 700, "#ffffff", 150)], sfx=[(0.3, "pop", 0.3)]),
    dict(S, dur_min=3.6, cam=cam(1.05, 1.12, *WF), props=[bag], lines=[("bf", "[confident] we look amazing.")], pre=0.6,
         actors=[kat([[0, K(eyes="happy", mouth="open", bowtie=True, blush="big", bounce=0.8, extras=["hearts", "sparkles"])]], **fk),
                 bf([[0, K(eyes="happy", mouth="smirk", bowtie=True, look=-1, extras=["hearts", "sparkles"])]], **fb)],
         stickers=[("*couple goals*", 0.6, 3.6, 555, 680, "#ff9fb5", 130)], sfx=[(0.05, "tada", 0.4)]),
])

# ---------------------------------------------------------------- 12. lost gift (him guilty)
S = dict(set="living", bg="#e4d5f6", fg="counter")
head_gift = dict(kind="gift", x=[[0, 780]], y=[[0, 760]], s=[[0, 0.8]], t0=0)
build("lost_gift", "when he hides your gift too well 🎁", [
    dict(S, dur_min=2.6, cam=cam(1.0, 1.06, *WC), lines=[("bf", "[confident] i hid your gift. you'll never find it.")],
         actors=[kat([[0, K(eyes="open", mouth="w", look=1)]]), bf([[0, K(eyes="happy", mouth="smirk", look=-1)]])]),
    dict(S, dur_min=2.2, cam=cam(1.3, 1.4, 555, 1060), lines=[("kat", "[excited] can i have it now?")],
         actors=[kat([[0, K(eyes="happy", mouth="open", bounce=1.0, look=1)]]),
                 bf([[0, K(eyes="happy", mouth="smirk", look=-1)], [1.4, K(eyes="open", mouth="o", extras=["sweat"])]])]),
    dict(S, dur_min=2.4, cam=crash(*BC, shake=SH), lines=[("bf", "[whispers] ...where did i put it?")],
         actors=[kat([[0, K(eyes="happy", mouth="w")]]), bf(dart())],
         stickers=[("*panic*", 0.2, 2.4, 780, 650, "#ff6b6b", 130)], sfx=[(0.05, "sting", 0.45)]),
    dict(S, dur_min=2.0, cam=cam(2.1, 2.3, *KC, shake=[[0, 0.8]]), lines=[("kat", "[crying] you lost it?!")],
         actors=[kat([[0, K(eyes="cry", mouth="open", shake=1.0, ears=-1)]]), bf(dart())],
         stickers=[("NOOOO", 0.2, 2.0, 330, 680, "#ff6b6b", 150)]),
    dict(S, dur_min=3.8, cam=cam(1.0, 1.06, 555, 1000), props=[head_gift], lines=[("kat", "[giggles] babe... it's on your head.")],
         actors=[kat([[0, K(eyes="teary", mouth="o", look=1)], [0.8, K(eyes="happy", mouth="w", look=1)], [2.4, K(eyes="happy", mouth="w", blush="big", extras=["hearts"])]]),
                 bf([[0, K(eyes="open", mouth="wobble", look=-1)], [2.4, K(eyes="happy", mouth="smirk", look=-1, extras=["hearts"])]])],
         stickers=[("found it!", 2.4, 3.8, 330, 680, "#ffd23f", 130)], sfx=[(2.4, "ding", 0.4)]),
])

# ---------------------------------------------------------------- 13. text from couch (Kat guilty)
S = dict(set="living", bg="#cad8f3", fg="sofa")
k13 = dict(x=300, y=1570, size=950)
b13 = dict(y=1560, size=1100)
B13 = (760, 1165)
build("text_from_couch", "tag the one who texts you from the next room 💬", [
    dict(S, dur_min=2.0, cam=cam(2.0, 2.1, *B13),
         actors=[kat([[0, K(eyes="happy", mouth="w", hold="phone")]], **k13), bf([[0, K(eyes="open", mouth="o", hold="phone")]], x=760, **b13)],
         stickers=[("new message: come here", 0.3, 2.0, 540, 760, "#ffffff", 90, -4)], sfx=[(0.3, "ding", 0.5)]),
    dict(S, dur_min=2.4, cam=cam(1.0, 1.06, 540, 1150), lines=[("bf", "[sighs] babe... you're right there.")],
         actors=[kat([[0, K(eyes="happy", mouth="w", hold="phone")]], **k13), bf([[0, K(eyes="flat", mouth="w", hold="phone", look=-1)]], x=760, **b13)]),
    dict(S, dur_min=2.4, cam=crash(300, 1225, shake=SH), lines=[("kat", "[nervous laugh] ...my legs are asleep?")],
         actors=[kat(dart(sweat="sweat", hold="phone"), **k13), bf([[0, K(eyes="flat", mouth="w", look=-1)]], x=760, **b13)],
         stickers=[("*guilty*", 0.2, 2.4, 300, 700, "#ff6b6b", 120)], sfx=[(0.05, "sting", 0.4)]),
    dict(S, dur_min=3.6, cam=cam(1.2, 1.3, 540, 1150), lines=[("bf", "[sleepy] what do you need?"), ("kat", "[softly] a hug. obviously.")],
         actors=[kat([[0, K(eyes="teary", mouth="w", look=1)]], **k13), bf([[0, K(eyes="open", mouth="smirk", look=-1)]], x=760, **b13)]),
    dict(S, dur_min=3.0, cam=cam(1.1, 1.2, 470, 1150),
         actors=[bf([[0, K(eyes="happy", mouth="smirk", look=-1, extras=["hearts"])]], x=[[0, 760], [0.8, 600]], **b13),
                 kat([[0, K(eyes="happy", mouth="w", blush="big", extras=["hearts"])]], **k13)],
         stickers=[("*delivered*", 0.8, 3.0, 470, 680, "#ff9fb5", 130)], sfx=[(0.6, "purr", 0.45)]),
])

# ---------------------------------------------------------------- 14. my moon montage
tray = dict(kind="cookie_tray", x=[[0, 560]], y=[[0, 1400]], s=[[0, 0.55]])
build("my_moon", "send this to your moon 🌙", [
    dict(set="xmas", bg="#d5e9cf", lights_on=0.4, dur_min=3.0, cam=cam(1.0, 1.1, *WF), lines=[("kat", "[softly] you're my moon.")],
         actors=[kat([[0, K(eyes="happy", mouth="w", hat="santa", look=1, blush="big", extras=["hearts"])]], **fk),
                 bf([[0, K(eyes="happy", mouth="smirk", hat="santa", look=-1)]], **fb)], sfx=[(0.4, "ding", 0.3)]),
    dict(set="snowy", bg="#cad8f3", snow=True, dur_min=2.8, cam=cam(1.0, 1.1, 530, 1180), lines=[("bf", "[giggles] okay, you win.")], pre=0.9,
         actors=[kat([[0, K(eyes="happy", mouth="open", look=1, bounce=0.8)]], **kk),
                 bf([[0, K(eyes="open", mouth="smirk", look=-1)], [0.5, K(eyes="squeeze", mouth="o", shake=0.6)], [1.0, K(eyes="happy", mouth="smirk", look=-1)]], **bb)],
         stickers=[("*poof*", 0.5, 1.6, 760, 900, "#ffffff", 140)], sfx=[(0.5, "boing", 0.45)]),
    dict(set="kitchen", bg="#ffe3bf", fg="counter", dur_min=2.6, cam=cam(1.05, 1.15, *WC), props=[tray],
         actors=[kat([[0, K(eyes="happy", mouth="w", hold="mug", look=1)]]), bf([[0, K(eyes="happy", mouth="smirk", hold="mug", look=-1)]])],
         stickers=[("*cocoa date*", 0.3, 2.6, 555, 700, "#ffffff", 120)], sfx=[(0.2, "pop", 0.3)]),
    dict(set="night", bg="#cdb4db", fg="sofa", dur_min=3.8, cam=cam(1.15, 1.3, 590, 1150), lines=[("bf", "[whispers] and you're my everything.")],
         actors=[bf([[0, K(eyes="open", mouth="smirk", look=-1)], [2.4, K(eyes="closed", mouth="w", extras=["zzz"])]], x=720, y=1560, size=1100),
                 kat([[0, K(eyes="closed", mouth="w", blush="big", extras=["hearts"])], [2.4, K(eyes="closed", mouth="w", extras=["zzz"])]], x=470, y=1570, size=950)],
         stickers=[("*my moon*", 0.4, 3.8, 590, 680, "#ffd23f", 130)], sfx=[(0.3, "purr", 0.4)]),
])
