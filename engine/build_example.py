"""Kat 2.0 launch batch: 7 couple skits. Generates voices (ElevenLabs), lays out shots by line length, writes JSONs."""
import json, os, subprocess, urllib.request

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


# ---------------------------------------------------------------- 1. Black Friday (Kat guilty)
L1 = dict(set="living", bg="#f9d9e6")
FLOOR = dict(y=1600)
bags = [dict(kind="bag", x=[[0, 610]], y=[[0, 1600]], s=[[0, 1.0]], color="#ff8fab", t0=0.2),
        dict(kind="bag", x=[[0, 1000]], y=[[0, 1610]], s=[[0, 1.1]], color="#7fd6ff", t0=0.6),
        dict(kind="bag", x=[[0, 560]], y=[[0, 1450]], s=[[0, 0.9]], color="#ffd23f", t0=1.0),
        dict(kind="bag", x=[[0, 1030]], y=[[0, 1440]], s=[[0, 0.9]], color="#b388ff", t0=1.4)]
bags_all = [dict(b, t0=0) for b in bags]
dart = [[0, K(eyes="open", mouth="wobble", look=-1, extras=["sweat"])]] + \
       [[i * 0.35, K(eyes="open", mouth="wobble", look=(1 if i % 2 else -1), extras=["sweat_big"])] for i in range(1, 8)]
build("bf_friday", "tag the one who's \"just looking\" on black friday", [
    dict(L1, dur_min=3.0, cam=cam(1.0, 1.08, 540, 1180), lines=[("kat", "[sweetly] i'm just looking, babe.")],
         actors=[bf([[0, K(eyes="open", mouth="smirk", look=1)]], x=330, y=1600, size=1100),
                 kat([[0, K(eyes="happy", mouth="w", hold="phone")]], x=790, y=1600, size=950)]),
    dict(L1, dur_min=2.6, cam=cam(1.05, 1.15, 600, 1180), props=bags,
         actors=[bf([[0, K(eyes="open", mouth="smirk", look=1)]], x=330, y=1600, size=1100),
                 kat([[0, K(eyes="happy", mouth="w")]], x=790, y=1600, size=950)],
         stickers=[("*just looking*", 0.3, 2.5, 760, 640, "#ffffff")],
         sfx=[(0.2, "pop", 0.4), (0.6, "pop", 0.4), (1.0, "pop", 0.4), (1.4, "pop", 0.4)]),
    dict(L1, dur_min=2.0, cam=cam(2.2, 2.4, 330, 1150, shake=[[0, 0], [0.4, 0.8], [1.5, 0.3]]),
         lines=[("bf", "[shocked] babe... the bank just called.")], props=bags_all,
         actors=[bf([[0, K(eyes="open", mouth="o", hold="phone", shake=0.5)]], x=330, y=1600, size=1100),
                 kat([[0, K(eyes="happy", mouth="w")]], x=790, y=1600, size=950)],
         stickers=[("$$$", 0.2, 2.5, 330, 650, "#7ad67a", 150)], sfx=[(0.1, "sting", 0.4)]),
    dict(L1, dur_min=2.6, cam=cam(2.1, 2.5, 790, 1200, shake=[[0, 0.2], [2.5, 0.7]]),
         lines=[("kat", "[nervous laugh] okay... maybe i bought a little.")], props=bags_all,
         actors=[bf([[0, K(eyes="open", mouth="o")]], x=330, y=1600, size=1100), kat(dart, x=790, y=1600, size=950)],
         stickers=[("*sweating*", 0.1, 1.4, 540, 640, "#9fd8ff")], sfx=[(0.1, "gulp", 0.4)]),
    dict(L1, dur_min=4.0, cam=cam(1.1, 1.25, 560, 1180),
         lines=[("kat", "[excited] but this one's for you!"), ("bf", "[sighs] [softly] okay... i'll carry the bags.")],
         props=bags_all,
         actors=[bf([[0, K(eyes="open", mouth="o")], [1.8, K(eyes="happy", mouth="smirk", extras=["hearts"])]], x=330, y=1600, size=1100),
                 kat([[0, K(eyes="happy", mouth="open", hold="gift", bounce=1.0, extras=["sparkles"])], [1.8, K(eyes="happy", mouth="w", blush="big", extras=["hearts"])]], x=790, y=1600, size=950)],
         stickers=[("forgiven", 2.4, 6.0, 540, 640, "#ff9fb5")], sfx=[(0.2, "tada", 0.35)]),
])

# ---------------------------------------------------------------- 2. while they're out partying
L2 = dict(set="night", bg="#cdb4db", fg="sofa")
build("bf_party", "while they're out partying btw", [
    dict(L2, dur_min=3.2, cam=cam(1.0, 1.08, 560, 1180), lines=[("kat", "[whispers] [giggles] this is the best party ever.")],
         actors=[bf([[0, K(eyes="open", mouth="smirk", look=-1)]], x=720, y=1560, size=1100),
                 kat([[0, K(eyes="happy", mouth="w", hold="mug")]], x=380, y=1570, size=950)],
         stickers=[("*party mode*", 0.4, 3.0, 540, 640, "#ffd23f")]),
    dict(L2, dur_min=3.0, cam=cam(2.1, 2.3, 720, 1150), lines=[("bf", "[sleepy] yeah... best... party...")],
         actors=[bf([[0, K(eyes="open", mouth="w")], [1.4, K(eyes="closed", mouth="w", extras=["zzz"])]], x=720, y=1560, size=1100),
                 kat([[0, K(eyes="happy", mouth="w", hold="mug")]], x=380, y=1570, size=950)]),
    dict(L2, dur_min=2.2, cam=cam(2.2, 2.4, 380, 1200), lines=[("kat", "[whispers] [giggles] he's asleep.")],
         actors=[bf([[0, K(eyes="closed", mouth="w", extras=["zzz"])]], x=720, y=1560, size=1100),
                 kat([[0, K(eyes="open", mouth="o", look=1)], [0.8, K(eyes="happy", mouth="w", look=1)]], x=380, y=1570, size=950)]),
    dict(L2, dur_min=3.4, cam=cam(1.15, 1.3, 560, 1180), lines=[("kat", "[whispers] goodnight, party animal.")],
         actors=[bf([[0, K(eyes="closed", mouth="w", extras=["zzz"])]], x=720, y=1560, size=1100),
                 kat([[0, K(eyes="happy", mouth="w", blush="big", extras=["hearts"])]], x=[[0, 380], [1.0, 480]], y=1570, size=950)],
         stickers=[("10/10 party", 1.0, 3.4, 540, 640, "#ff9fb5")], sfx=[(1.0, "pop", 0.3)]),
])

# ---------------------------------------------------------------- 3. wizard laptop fix
L3 = dict(set="living", bg="#e4d5f6", fg="counter")
lap = dict(kind="laptop", x=[[0, 560]], y=[[0, 1395]], s=[[0, 1.0]])
lap_on = dict(lap, screen="#7fd6ff")
build("bf_wizard", "when he fixes your laptop like a wizard", [
    dict(L3, dur_min=2.8, cam=cam(1.0, 1.08, 540, 1100), lines=[("kat", "[sniffles] my laptop won't turn on...")], props=[lap],
         actors=[kat([[0, K(eyes="teary", mouth="wobble")]]), bf([[0, K(eyes="open", mouth="smirk", look=-1)]])]),
    dict(L3, dur_min=2.6, cam=cam(2.2, 2.35, 780, 1060), lines=[("bf", "[confident] stand back. i'm a professional.")], props=[lap],
         actors=[kat([[0, K(eyes="teary", mouth="sad")]]), bf([[0, K(eyes="open", mouth="smirk", hat="wizard", extras=["sparkles"])]])],
         stickers=[("*cracks knuckles*", 0.3, 2.5, 540, 600, "#ffffff", 95)], sfx=[(0.2, "whoosh", 0.35)]),
    dict(L3, dur_min=3.0, cam=cam(1.5, 1.7, 680, 1150, shake=[[0, 0.6], [3, 0.9]]), props=[lap],
         actors=[kat([[0, K(eyes="open", mouth="o", look=1)]]), bf([[0, K(eyes="squeeze", mouth="w", hat="wizard", shake=0.6, extras=["sparkles"])]])],
         stickers=[("tak tak tak", 0.1, 1.2, 760, 1250, "#ffd23f", 100, 8), ("tak tak", 1.0, 2.2, 360, 1300, "#ffd23f", 100, -8),
                   ("TAK!", 2.0, 3.0, 700, 1240, "#ff6b6b", 130, 6)],
         sfx=[(0.1, "pop", 0.25), (0.4, "pop", 0.25), (0.7, "pop", 0.25), (1.0, "pop", 0.25), (1.4, "pop", 0.25), (1.8, "pop", 0.25), (2.3, "ding", 0.4)]),
    dict(L3, dur_min=2.0, cam=cam(2.2, 2.4, 330, 1100), lines=[("kat", "[gasps] [excited] it works! how?!")], props=[lap_on],
         actors=[kat([[0, K(eyes="open", mouth="open", bounce=1.2, extras=["sparkles"])]]), bf([[0, K(eyes="open", mouth="smirk", hat="wizard")]])]),
    dict(L3, dur_min=3.6, cam=cam(1.2, 1.3, 560, 1100),
         lines=[("bf", "[whispers] ...it wasn't plugged in."), ("kat", "[giggles] my genius.")], props=[lap_on],
         actors=[kat([[0, K(eyes="open", mouth="w", look=1)], [1.8, K(eyes="happy", mouth="w", blush="big", extras=["hearts"])]]),
                 bf([[0, K(eyes="open", mouth="smirk", hat="wizard", look=-1)]])],
         stickers=[("*it was unplugged*", 0.2, 1.9, 540, 620, "#ffffff", 95)]),
])

# ---------------------------------------------------------------- 4. montage: send this to your person
build("bf_montage", "send this to your person", [
    dict(set="kitchen", bg="#ffe3bf", fg="counter", dur_min=3.4, cam=cam(1.05, 1.2, 560, 1100),
         lines=[("kat", "[softly] you made me cocoa?")],
         actors=[kat([[0, K(eyes="open", mouth="w", hold="mug", look=1)], [1.6, K(eyes="happy", mouth="w", hold="mug", blush="big", extras=["hearts"])]]),
                 bf([[0, K(eyes="open", mouth="smirk", hold="mug", look=-1)]])], sfx=[(0.1, "ding", 0.2)]),
    dict(set="snowy", bg="#cad8f3", snow=True, dur_min=3.2, cam=cam(1.0, 1.12, 400, 1000),
         actors=[kat([[0, K(eyes="open", mouth="o", look=-1, extras=["sparkles"])]], x=260, y=1560, size=900),
                 bf([[0, K(eyes="open", mouth="smirk", look=-1)]], x=600, y=1560, size=1050)],
         stickers=[("first snow", 0.4, 3.0, 760, 640, "#ffffff")]),
    dict(set="living", bg="#f9d9e6", fg="sofa", dur_min=3.8, cam=cam(1.2, 1.5, 560, 1150),
         lines=[("kat", "[giggles] boop."), ("bf", "[softly] love you too.")],
         actors=[bf([[0, K(eyes="open", mouth="smirk", look=-1)], [1.0, K(eyes="happy", mouth="smirk", extras=["hearts"])]], x=700, y=1560, size=1100),
                 kat([[0, K(eyes="happy", mouth="w", look=1)], [0.6, K(eyes="happy", mouth="w", blush="big", extras=["hearts"])]], x=[[0, 300], [0.6, 470]], y=1570, size=950)],
         stickers=[("boop", 0.6, 1.6, 560, 820, "#ff9fb5", 130)], sfx=[(0.6, "pop", 0.45)]),
])

# ---------------------------------------------------------------- 5. piggyback star (Christmas)
X5 = dict(set="xmas", bg="#d5e9cf")
build("bf_star", "tag the one who always needs a boost", [
    dict(X5, dur_min=2.8, cam=cam(1.0, 1.05, 560, 1150), lines=[("kat", "[struggling] i can't reach the top!")],
         actors=[bf([[0, K(eyes="open", mouth="smirk", hat="santa", look=1)]], x=300, y=1600, size=1050),
                 kat([[0, K(eyes="squeeze", mouth="wobble", hold="star", hat="santa", bounce=1.3)]], x=620, y=1600, size=850)]),
    dict(X5, dur_min=1.8, cam=cam(2.2, 2.3, 300, 1150), lines=[("bf", "[confident] hop on.")],
         actors=[bf([[0, K(eyes="open", mouth="smirk", hat="santa", look=1)]], x=300, y=1600, size=1050),
                 kat([[0, K(eyes="open", mouth="o", hold="star", hat="santa")]], x=620, y=1600, size=850)]),
    dict(X5, dur_min=3.6, star_at=2.6, cam=cam(1.0, 1.1, 620, 1050, shake=[[0, 0], [1.0, 0.6], [2.6, 0]]),
         actors=[bf([[0, K(eyes="squeeze", mouth="wobble", hat="santa", shake=0.4)]], x=[[0, 300], [1.0, 640]], y=1600, size=1050),
                 kat([[0, K(eyes="open", mouth="o", hold="star", hat="santa")], [2.6, K(eyes="happy", mouth="open", hat="santa")]],
                     x=[[0, 620], [1.0, 650]], y=[[0, 1600], [1.0, 980]], size=700)],
         stickers=[("*wobble*", 1.0, 2.5, 300, 700, "#ffffff")], sfx=[(1.0, "boing", 0.35), (2.6, "ding", 0.4)]),
    dict(X5, dur_min=3.4, star_at=0, lights_on=0.3, cam=cam(1.0, 1.08, 600, 1080),
         lines=[("kat", "[gasps] [excited] it's perfect!")],
         actors=[bf([[0, K(eyes="happy", mouth="smirk", hat="santa", extras=["hearts"])]], x=640, y=1600, size=1050),
                 kat([[0, K(eyes="happy", mouth="open", hat="santa", blush="big", extras=["hearts"])]], x=650, y=980, size=700)],
         stickers=[("ta-da!", 0.3, 2.0, 300, 640, "#ffd23f", 140)], sfx=[(0.3, "tada", 0.45)]),
])

# ---------------------------------------------------------------- 6. loading: getting ready for date night
L6 = dict(set="living", bg="#cad8f3")
sk6 = build("bf_loading", "him getting ready for date night", [
    dict(L6, dur_min=2.8, cam=cam(1.6, 1.7, 540, 1150), lines=[("bf", "[yawns] ...date night? now?")],
         actors=[bf([[0, K(eyes="closed", mouth="w", ears=-1, extras=["zzz"])]], x=540, y=1600, size=1150)]),
    dict(L6, dur_min=2.6, cam=cam(1.6, 1.8, 540, 1150, shake=[[0, 0.9], [2.6, 0.9]]),
         actors=[bf([[i * 0.3, K(eyes="open", mouth="wobble", look=(1 if i % 2 else -1), extras=["sweat_big"], shake=0.8)] for i in range(9)], x=540, y=1600, size=1150)],
         stickers=[("*panic*", 0.2, 2.5, 540, 600, "#ff6b6b", 130)], sfx=[(0.1, "whoosh", 0.3), (0.9, "pop", 0.3), (1.6, "boing", 0.3)]),
    dict(L6, dur_min=3.0, cam=cam(1.5, 1.6, 540, 1150), lines=[("bf", "[smooth] ready when you are.")],
         actors=[bf([[0, K(eyes="open", mouth="smirk", bowtie=True, extras=["sparkles"])]], x=540, y=1600, size=1150)],
         sfx=[(0.05, "tada", 0.4)]),
    dict(set="living", bg="#f9d9e6", dur_min=2.6, cam=cam(2.0, 2.2, 540, 1180), lines=[("kat", "[gasps] [giggles] oh my...")],
         actors=[kat([[0, K(eyes="open", mouth="o")], [0.7, K(eyes="happy", mouth="open", blush="big", bounce=1.2, extras=["hearts"])]], x=540, y=1600, size=1000)],
         stickers=[("swoon", 0.8, 2.6, 540, 640, "#ff9fb5", 130)]),
])
t0, t1, t2 = sk6["shots"][0]["dur"], sk6["shots"][1]["dur"], sk6["shots"][2]["dur"]
sk6["overlays"] = [dict(kind="loading", label="date night", t0=0, t1=t0 + t1 + t2,
                        keys=[[0, 0], [t0, 12], [t0 + t1, 63], [t0 + t1 + 0.6, 100]])]
json.dump(sk6, open("kat2/bf_loading.json", "w"), indent=1)

# ---------------------------------------------------------------- 7. 11:59 on Nov 30
N7 = dict(set="night", bg="#cdb4db")
clock = dict(kind="clock", x=[[0, 540]], y=[[0, 760]], s=[[0, 1.0]], text="11:59", text2="12:00", switch=99)
clock12 = dict(clock, switch=0)
build("bf_1159", "me at 11:59pm on november 30th", [
    dict(N7, dur_min=2.8, cam=cam(1.0, 1.08, 540, 1150), props_back=[clock],
         actors=[bf([[0, K(eyes="closed", mouth="w", extras=["zzz"])]], x=760, y=1600, size=1100),
                 kat([[0, K(eyes="open", mouth="w", look=0)]], x=330, y=1600, size=950)],
         stickers=[("*waiting*", 0.4, 2.7, 330, 1000, "#ffffff")]),
    dict(N7, dur_min=1.6, cam=cam(2.4, 2.6, 540, 760), props_back=[dict(clock, switch=0.8)],
         actors=[bf([[0, K(eyes="closed", mouth="w")]], x=760, y=1600, size=1100), kat([[0, K(eyes="open", mouth="w")]], x=330, y=1600, size=950)],
         sfx=[(0.8, "ding", 0.5)]),
    dict(set="xmas", bg="#d5e9cf", lights_on=0, star_at=0, dur_min=3.0, cam=cam(1.0, 1.15, 450, 1150, shake=[[0, 1.0], [1.5, 0.2]]),
         lines=[("kat", "[excited] [shouting] it's christmas season!")],
         actors=[bf([[0, K(eyes="closed", mouth="w", extras=["zzz"])]], x=760, y=1600, size=1100),
                 kat([[0, K(eyes="happy", mouth="open", hat="santa", bounce=1.5, extras=["sparkles", "hearts"])]], x=330, y=1600, size=950)],
         stickers=[("IT'S TIME", 0.0, 2.2, 540, 620, "#ff6b6b", 150)], sfx=[(0.0, "tada", 0.5)]),
    dict(set="xmas", bg="#d5e9cf", lights_on=0, star_at=0, dur_min=2.2, cam=cam(2.2, 2.35, 760, 1100),
         lines=[("bf", "[sleepy] babe... it's midnight.")],
         actors=[bf([[0, K(eyes="open", mouth="w", ears=-1)]], x=760, y=1600, size=1100),
                 kat([[0, K(eyes="happy", mouth="open", hat="santa")]], x=330, y=1600, size=950)]),
    dict(set="xmas", bg="#d5e9cf", lights_on=0, star_at=0, dur_min=2.8, cam=cam(1.1, 1.2, 540, 1150),
         lines=[("kat", "[giggles] no sleeping, elf.")],
         actors=[bf([[0, K(eyes="open", mouth="smirk", hat="santa")]], x=760, y=1600, size=1100),
                 kat([[0, K(eyes="happy", mouth="w", hat="santa", blush="big", extras=["hearts"])]], x=330, y=1600, size=950)],
         sfx=[(0.1, "pop", 0.4)]),
])
