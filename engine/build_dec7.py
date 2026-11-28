"""Kat 2.0 batch 2: skits 15-21 (Dec 7 19:30 - Dec 10 19:30). Usage: python3 build_dec7.py [slug ...]"""
import json, os, subprocess, sys, urllib.request

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs("kat2/audio", exist_ok=True)
KEY = (os.environ.get("ELEVENLABS_API_KEY") or open(os.path.expanduser("~/.kat/key")).read()).strip()
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
FL = dict(y=1600)
kF = dict(y=1600, size=950)
bF = dict(y=1600, size=1100)

# ---------------------------------------------------------------- 15. we need to talk (him guilty)
S = dict(set="xmas", bg="#e4d5f6")
build("we_need_to_talk", "when she says \"we need to talk\" 😳", [
    dict(S, dur_min=2.4, cam=cam(2.0, 2.2, *KF), lines=[("kat", "[serious] babe. we need to talk.")],
         actors=[kat([[0, K(eyes="flat", mouth="w", hat="santa", look=1)]], **kF), bf([[0, K(eyes="open", mouth="smirk", hold="star", look=-1)]], **bF)],
         stickers=[("*gulp*", 1.6, 2.4, 780, 700, "#9fd8ff", 120)], sfx=[(1.6, "gulp", 0.4)]),
    dict(S, dur_min=2.6, cam=crash(*BFF, shake=SH), lines=[("bf", "[nervous] i broke your ornament! i'm sorry!")],
         actors=[kat([[0, K(eyes="flat", mouth="w", hat="santa", look=1)]], **kF), bf(dart(hold="star"), **bF)],
         stickers=[("*confession*", 0.3, 2.6, 780, 680, "#ff6b6b", 120)], sfx=[(0.05, "sting", 0.45)]),
    dict(S, dur_min=2.8, cam=cam(2.0, 2.15, *KF), lines=[("kat", "[softly] ...i was gonna ask what you want for christmas.")],
         actors=[kat([[0, K(eyes="open", mouth="o", hat="santa", look=1)]], **kF), bf([[0, K(eyes="open", mouth="wobble", hold="star", extras=["sweat"])]], **bF)]),
    dict(S, dur_min=2.4, cam=cam(2.1, 2.3, *BFF), lines=[("bf", "[nervous laugh] ...forget i said anything.")],
         actors=[kat([[0, K(eyes="flat", mouth="smirk", hat="santa", look=1)]], **kF), bf([[0, K(eyes="open", mouth="wobble", hold="star", look=1, extras=["sweat"])]], **bF)],
         stickers=[("*too late*", 0.3, 2.4, 780, 680, "#ffd23f", 120)]),
    dict(S, dur_min=3.6, cam=cam(1.05, 1.15, *WF), lights_on=0.3, lines=[("kat", "[giggles] you're getting glue.")], pre=0.9,
         actors=[bf([[0, K(eyes="happy", mouth="smirk", hold="star", look=-1, extras=["hearts"])]], **bF),
                 kat([[0, K(eyes="happy", mouth="w", hat="santa", blush="big", look=1, extras=["hearts"])]], x=[[0, 330], [0.8, 520]], **kF)],
         stickers=[("ta-da!", 1.0, 3.6, 555, 680, "#ffd23f", 140)], sfx=[(0.8, "tada", 0.4)]),
])

# ---------------------------------------------------------------- 16. double text (Kat guilty)
S = dict(set="bedroom", bg="#f9d9e6")
build("double_text", "tag the one who double texts 📱", [
    dict(S, dur_min=2.8, cam=cam(2.0, 2.2, *KF), lines=[("kat", "[excited] hi. hi. hiii. are you there?")],
         actors=[kat([[0, K(eyes="happy", mouth="w", hold="phone", bounce=0.8)]], **kF)],
         stickers=[("sent x27", 0.4, 2.8, 330, 700, "#ffffff", 110)], sfx=[(0.4, "ding", 0.3), (1.0, "ding", 0.3), (1.6, "ding", 0.3)]),
    dict(S, dur_min=3.0, cam=cam(1.0, 1.08, *WF), lines=[("bf", "[sighs] babe... i was in the shower for five minutes.")], pre=1.0,
         actors=[kat([[0, K(eyes="happy", mouth="w", hold="phone", look=1)]], **kF),
                 bf([[0, K(eyes="flat", mouth="w", look=-1)]], x=[[0, 1250], [0.9, 780]], walk=[[0, 1], [0.9, 0]], **bF)]),
    dict(S, dur_min=1.6, cam=crash(*KF),
         actors=[kat([[0, K(eyes="open", mouth="wobble", hold="phone", extras=["sweat"])]], **kF), bf([[0, K(eyes="flat", mouth="w", look=-1)]], **bF)],
         stickers=[("*busted*", 0.2, 1.6, 330, 700, "#ff6b6b", 130)], sfx=[(0.05, "sting", 0.45)]),
    dict(S, dur_min=2.2, cam=cam(2.2, 2.45, *KF, shake=SH), lines=[("kat", "[nervous laugh] ...i missed you?")],
         actors=[kat(dart(hold="phone"), **kF), bf([[0, K(eyes="flat", mouth="smirk", look=-1)]], **bF)]),
    dict(S, dur_min=3.6, cam=cam(1.05, 1.15, *WF), lines=[("bf", "[softly] i replied to all of them.")],
         actors=[kat([[0, K(eyes="open", mouth="o", hold="phone", look=1)], [1.8, K(eyes="happy", mouth="w", hold="phone", blush="big", extras=["hearts"])]], **kF),
                 bf([[0, K(eyes="open", mouth="smirk", hold="phone", look=-1)], [1.8, K(eyes="happy", mouth="smirk", hold="phone", look=-1, extras=["hearts"])]], **bF)],
         stickers=[("i love you x27", 1.8, 3.6, 555, 680, "#ff9fb5", 120)], sfx=[(1.8, "ding", 0.4)]),
])

# ---------------------------------------------------------------- 17. first snow (him guilty)
S = dict(set="snowy", bg="#cad8f3", snow=True)
kk = dict(x=330, y=1600, size=900)
bb = dict(x=780, y=1600, size=1050)
KN, BN = (330, 1270), (780, 1220)
build("first_snow", "tag the one who throws the first snowball ❄️", [
    dict(S, dur_min=2.8, cam=cam(1.0, 1.08, 555, 1180), lines=[("kat", "[softly] the first snow... so peaceful.")],
         actors=[kat([[0, K(eyes="happy", mouth="w", hat="santa", look=1)]], **kk), bf([[0, K(eyes="open", mouth="smirk", hat="santa", look=-1)]], **bb)],
         stickers=[("*peaceful*", 0.4, 2.8, 555, 680, "#ffffff", 110)]),
    dict(S, dur_min=1.4, cam=cam(2.0, 2.1, *KN),
         actors=[kat([[0, K(eyes="happy", mouth="w", hat="santa")], [0.3, K(eyes="squeeze", mouth="o", hat="santa", shake=0.9)]], **kk)],
         stickers=[("*poof*", 0.3, 1.4, 330, 850, "#ffffff", 150)], sfx=[(0.3, "boing", 0.5)]),
    dict(S, dur_min=2.0, cam=crash(*KN, shake=[[0, 0.9], [2, 0.6]]), lines=[("kat", "[gasps] who did that?!")],
         actors=[kat([[0, K(eyes="cry", mouth="open", hat="santa", shake=1.0)]], **kk)],
         stickers=[("NOOOO", 0.2, 2.0, 330, 680, "#ff6b6b", 150)], sfx=[(0.05, "sting", 0.45)]),
    dict(S, dur_min=2.2, cam=cam(2.0, 2.2, *BN), lines=[("bf", "[nervous laugh] ...the wind?")],
         actors=[kat([[0, K(eyes="flat", mouth="w", hat="santa", look=1)]], **kk), bf([[0, K(eyes="open", mouth="smirk", hat="santa", look=1, extras=["sweat_big"])]], **bb)],
         stickers=[("*guilty*", 0.3, 2.2, 780, 680, "#ff6b6b", 120)]),
    dict(S, dur_min=3.8, cam=cam(1.1, 1.2, 600, 1180), lines=[("bf", "[giggles] okay, okay, it was me.")], pre=0.9,
         actors=[bf([[0, K(eyes="happy", mouth="smirk", hat="santa", look=-1, extras=["hearts"])]], **bb),
                 kat([[0, K(eyes="happy", mouth="open", hat="santa", blush="big", look=1, extras=["hearts"])]], x=[[0, 330], [0.6, 560]], y=1600, size=900)],
         stickers=[("*snow war*", 1.0, 3.8, 600, 680, "#ffd23f", 130)], sfx=[(0.6, "purr", 0.45)]),
])

# ---------------------------------------------------------------- 18. same order (Kat guilty)
S = dict(set="kitchen", bg="#ffe3bf", fg="counter")
m1 = dict(kind="cookie", x=[[0, 560]], y=[[0, 1400]], s=[[0, 0.8]])
build("same_order", "tag the one who orders the same thing every time ☕", [
    dict(S, dur_min=2.6, cam=cam(1.0, 1.08, *WC), props=[m1], lines=[("kat", "[confident] today i'm trying something new.")],
         actors=[kat([[0, K(eyes="happy", mouth="w", bounce=0.8, look=1)]]), bf([[0, K(eyes="open", mouth="smirk", look=-1)]])],
         stickers=[("*new me*", 0.4, 2.6, 330, 680, "#ffd23f", 120)]),
    dict(S, dur_min=2.4, cam=cam(2.1, 2.3, *BC), props=[m1], lines=[("bf", "[suspicious] okay... what are you having?")],
         actors=[kat([[0, K(eyes="happy", mouth="w", look=1)]]), bf([[0, K(eyes="flat", mouth="smirk", look=-1)]])]),
    dict(S, dur_min=2.2, cam=cam(2.1, 2.3, *KC), props=[m1], lines=[("kat", "[whispers] ...peppermint cocoa.")],
         actors=[kat(dart(n=6, sweat="sweat")), bf([[0, K(eyes="flat", mouth="smirk", look=-1)]])],
         stickers=[("*again*", 0.6, 2.2, 330, 680, "#ff6b6b", 130)], sfx=[(0.3, "gulp", 0.4)]),
    dict(S, dur_min=1.8, cam=crash(*BC), props=[m1],
         actors=[kat([[0, K(eyes="open", mouth="wobble")]]), bf([[0, K(eyes="squeeze", mouth="open", bounce=1.0)]])],
         stickers=[("*47th time*", 0.2, 1.8, 780, 650, "#ffffff", 120)], sfx=[(0.05, "sting", 0.4)]),
    dict(S, dur_min=3.6, cam=cam(1.05, 1.15, *WC), props=[m1], lines=[("bf", "[softly] already made it.")],
         actors=[kat([[0, K(eyes="open", mouth="o", look=1)], [1.4, K(eyes="happy", mouth="w", hold="mug", blush="big", look=1, extras=["hearts"])]]),
                 bf([[0, K(eyes="open", mouth="smirk", hold="mug", look=-1)], [1.4, K(eyes="happy", mouth="smirk", look=-1, extras=["hearts"])]])],
         stickers=[("swoon", 1.6, 3.6, 330, 680, "#ff9fb5", 130)], sfx=[(1.4, "ding", 0.4)]),
])

# ---------------------------------------------------------------- 19. i'm fine (him guilty)
S = dict(set="xmas", bg="#d5e9cf")
g2 = [dict(kind="gift", x=[[0, 560]], y=[[0, 1610]], s=[[0, 0.8]]), dict(kind="gift", x=[[0, 1010]], y=[[0, 1610]], s=[[0, 0.7]])]
build("im_fine", "when she says \"i'm fine\" 🙂", [
    dict(S, dur_min=3.4, cam=cam(1.0, 1.06, *WF), props=g2, lights_on=0, lines=[("kat", "[sweetly] wow. you decorated without me. i'm fine.")],
         actors=[kat([[0, K(eyes="flat", mouth="w", look=1)]], **kF), bf([[0, K(eyes="happy", mouth="smirk", look=-1)]], **bF)],
         stickers=[("*she's not fine*", 1.4, 3.4, 555, 680, "#ff6b6b", 110)]),
    dict(S, dur_min=1.6, cam=crash(*BFF, shake=SH), props=g2, lights_on=0,
         actors=[kat([[0, K(eyes="flat", mouth="w", look=1)]], **kF), bf(dart(n=5), **bF)],
         stickers=[("*danger*", 0.2, 1.6, 780, 680, "#ff6b6b", 130)], sfx=[(0.05, "sting", 0.45)]),
    dict(S, dur_min=2.4, cam=cam(2.1, 2.3, *BFF), props=g2, lights_on=0, lines=[("bf", "[nervous] i... wanted to surprise you?")],
         actors=[kat([[0, K(eyes="flat", mouth="w", look=1)]], **kF), bf(dart(n=7, sweat="sweat"), **bF)], sfx=[(0.2, "gulp", 0.4)]),
    dict(S, dur_min=2.4, cam=cam(2.0, 2.2, *KF), props=g2, lights_on=0, lines=[("kat", "[sniffles] it was our thing.")],
         actors=[kat([[0, K(eyes="teary", mouth="sad", ears=-1, look=1)]], **kF), bf([[0, K(eyes="open", mouth="wobble", look=-1)]], **bF)]),
    dict(S, dur_min=4.0, cam=cam(1.05, 1.15, *WF), props=g2, lights_on=1.6, lines=[("bf", "[softly] i saved the best one for you.")],
         actors=[kat([[0, K(eyes="teary", mouth="o", look=1)], [1.6, K(eyes="happy", mouth="w", hold="star", blush="big", extras=["hearts", "sparkles"])]], **kF),
                 bf([[0, K(eyes="open", mouth="smirk", hold="star", look=-1)], [1.6, K(eyes="happy", mouth="smirk", look=-1, extras=["hearts"])]], **bF)],
         stickers=[("*our thing*", 1.8, 4.0, 555, 680, "#ffd23f", 130)], sfx=[(1.6, "tada", 0.4)]),
])

# ---------------------------------------------------------------- 20. every story (Kat guilty)
S = dict(set="night", bg="#cad8f3", fg="sofa")
k20 = dict(x=380, y=1570, size=950)
b20 = dict(x=720, y=1560, size=1100)
build("every_story", "tag the one who posts you on every story 📸", [
    dict(S, dur_min=2.8, cam=cam(1.15, 1.25, 550, 1150), lines=[("kat", "[whispers] so cute... posting it.")],
         actors=[kat([[0, K(eyes="happy", mouth="w", hold="phone", look=1)]], **k20), bf([[0, K(eyes="closed", mouth="w", extras=["zzz"])]], **b20)],
         stickers=[("*posted*", 1.8, 2.8, 380, 700, "#ffffff", 120)], sfx=[(1.8, "pop", 0.4)]),
    dict(S, dur_min=2.6, cam=cam(2.0, 2.2, *BS), lines=[("bf", "[sleepy] why do i have 400 messages?")],
         actors=[kat([[0, K(eyes="happy", mouth="w", hold="phone")]], **k20), bf([[0, K(eyes="flat", mouth="w", hold="phone", look=-1)]], **b20)]),
    dict(S, dur_min=1.6, cam=crash(*KS),
         actors=[kat([[0, K(eyes="open", mouth="wobble", hold="phone", extras=["sweat"])]], **k20), bf([[0, K(eyes="flat", mouth="w", look=-1)]], **b20)],
         stickers=[("*evidence*", 0.2, 1.6, 380, 700, "#ffd23f", 120)], sfx=[(0.05, "sting", 0.45)]),
    dict(S, dur_min=2.6, cam=cam(2.2, 2.45, *KS, shake=SH), lines=[("kat", "[nervous laugh] ...you're just very popular?")],
         actors=[kat(dart(hold="phone"), **k20), bf([[0, K(eyes="flat", mouth="smirk", look=-1)]], **b20)]),
    dict(S, dur_min=3.8, cam=cam(1.15, 1.25, 550, 1150), lines=[("bf", "[giggles] reposted. 'that's my girl.'")],
         actors=[kat([[0, K(eyes="open", mouth="o", look=1)], [2.0, K(eyes="happy", mouth="w", blush="big", extras=["hearts"])]], **k20),
                 bf([[0, K(eyes="open", mouth="smirk", hold="phone", look=-1)], [2.0, K(eyes="happy", mouth="smirk", hold="phone", look=-1, extras=["hearts"])]], **b20)],
         stickers=[("*couple goals*", 2.0, 3.8, 550, 680, "#ff9fb5", 120)], sfx=[(2.0, "ding", 0.4)]),
])

# ---------------------------------------------------------------- 21. too many lights (him guilty)
S = dict(set="xmas", bg="#f7cddc")
N = dict(set="night", bg="#cdb4db")
build("too_many_lights", "when he puts up 1000 christmas lights 💡", [
    dict(S, dur_min=2.8, cam=cam(2.0, 2.2, *BFF), lights_on=0.3, lines=[("bf", "[excited] one thousand lights, babe! watch this!")],
         actors=[kat([[0, K(eyes="open", mouth="w", look=1)]], **kF), bf([[0, K(eyes="happy", mouth="smirk", hat="santa", bounce=0.9)]], **bF)],
         stickers=[("1000", 0.4, 2.8, 780, 680, "#ffd23f", 140)], sfx=[(0.3, "whoosh", 0.4)]),
    dict(S, dur_min=1.0, cam=cam(1.0, 1.1, *WF), lights_on=0,
         actors=[kat([[0, K(eyes="happy", mouth="o", look=1)]], **kF), bf([[0, K(eyes="happy", mouth="smirk", hat="santa", look=-1)]], **bF)],
         stickers=[("*pop*", 0.7, 1.0, 555, 700, "#ffffff", 150)], sfx=[(0.7, "sting", 0.45)]),
    dict(N, dur_min=2.2, cam=cam(2.0, 2.2, *KF), lines=[("kat", "[sighs] ...you blew the power.")],
         actors=[kat([[0, K(eyes="flat", mouth="w", look=1)]], **kF), bf([[0, K(eyes="open", mouth="wobble", hat="santa")]], **bF)]),
    dict(N, dur_min=2.4, cam=crash(*BFF, shake=SH), lines=[("bf", "[nervous laugh] ...romantic, right?")],
         actors=[kat([[0, K(eyes="flat", mouth="w", look=1)]], **kF), bf(dart(hat="santa"), **bF)],
         stickers=[("*guilty*", 0.2, 2.4, 780, 680, "#ff6b6b", 120)]),
    dict(N, dur_min=3.8, cam=cam(1.1, 1.2, 600, 1180), lines=[("kat", "[softly] okay. it kind of is.")], pre=0.9,
         actors=[bf([[0, K(eyes="happy", mouth="smirk", hat="santa", look=-1, extras=["hearts"])]], **bF),
                 kat([[0, K(eyes="happy", mouth="w", blush="big", look=1, extras=["hearts"])]], x=[[0, 330], [0.8, 520]], **kF)],
         stickers=[("*moonlight date*", 1.0, 3.8, 600, 680, "#ff9fb5", 120)], sfx=[(0.8, "purr", 0.45)]),
])
