# Kat 2.0 skit guide (for the autopilot)

Kat 2.0 = short **couple skits** (10–20 s) starring **Kat** (white girl cat) and **her boyfriend** (cream tomcat, no name yet).
Kat 1.0 (one cat sitting + 3 quotes) is retired. Never make 1.0 videos again.

## Characters (exact dicts — never change)
- Kat: `{"color":"#ffffff","inner":"#ffb7c5"}` — voice ElevenLabs `g4hzXZZhL5vwjYdqQDDM`, model `eleven_v4`. Emotional, dramatic, sweet.
- Boyfriend: `{"male":true,"color":"#f3e2c4","inner":"#d6bf98","brow_col":"#8a6a40","eye_style":"sleepy","nose_col":"#8a6a40","big_nose":true}`
  — voice ElevenLabs **Will** `bIHbv24MWmeRgasZH58o`. Chill, sleepy, smirky, secretly sweet. Default mouth `smirk`. Size ~15% bigger than Kat.
- Speak about him as "him"/"babe" until Waqar picks a name.

## Story recipe (every skit)
1. **Setup** (who wants what) → 2. **Problem / accusation** → 3. **Guilty reaction** (look away, wobble mouth, gulp) →
4. **Escalation** (sweat drops multiply, eyes dart, camera pushes in + shakes, evidence appears) → 5. **Save / payoff** (ta-da, hearts).
- **Alternate who's guilty**: roughly half the skits Kat is the guilty one, half him.
- Kat's reactions are **dramatic**: crash zoom, `eyes:"cry"` tear rivers, `shake`, "NOOOO"-style sticker, `sting` sfx.
- Hooks (caption box) point at a person: "tag the one who…", "when he/she…", "POV:…", "send this to your person". Max 1 POV per batch. Caption ≤ ~50 chars.
- Lines are short (≤ ~8 words), lowercase, with ElevenLabs tags: [gasps] [giggles] [sniffles] [crying] [sighs] [whispers] [excited] [nervous laugh] [sleepy] [confident] [softly] [shouting] [yawns].
- Mix it up across a batch: different sets, backgrounds, props, hats, seasons, and **current trends** (search the web each run for 1–2 trending formats/sounds/memes of the week; copy the format/idea, never copyrighted songs, characters or other creators' jokes).
- Seasonal calendar: Dec = Christmas (santa hats, xmas set, gifts, first snow, cocoa), New Year's Eve countdown; Jan = resolutions, gym, cold; Feb = Valentine's (big one for a couple page); Oct = Halloween costumes.

## Engine
- `engine/loops.py` (character drawing, sfx, stickers) + `engine/skit.py` (shots, camera, sets, props, voices, lip-sync).
- Render: `cd engine && python3 skit.py <skit.json> <out.mp4>` (~35 s per skit). Needs pillow numpy soundfile + ffmpeg, font `fonts/Gaegu-Bold.ttf` next to loops.py (download from google/fonts ofl/gaegu).
- `engine/build_example.py` is the Nov 20 launch batch builder: copy its helpers (`voice`, `build`, `cam`, `kat`, `bf`) — it generates voices, lays out shots by line length, writes the JSON. Key from `~/.kat/key` (never print/commit).

### Skit JSON
`{"caption", "mood":"sweet", "music_level":0.28, "shots":[...], "voices":[{"file","t","who"}], "stickers":[...], "sfx":[...], "overlays":[...]}`
Each shot: `dur`, `set`, `bg`, optional `fg`, `cam`, `actors`, `props`, `props_back`, `snow`, `lights_on`, `star_at`.
- **sets**: `kitchen`, `living`, `bedroom`, `night` (dark window + moon), `snowy` (use with `"snow":true`), `xmas` (tree + gifts; `lights_on`/`star_at` = seconds into shot).
- **fg** (foreground hiding lower bodies): `counter` (top y≈1390; cats at y≈1440–1450), `sofa`, `blanket`. No fg → cats sit on floor at y≈1600.
- **bg colours**: #f7cddc #f9d9e6 #d5e9cf #cad8f3 #ffe3bf #e4d5f6 #cdb4db.
- **actor**: `{char, who:"kat"|"bf", x:[[t,v]], y:[[t,v]], size, states:[[t,{pose,eyes,mouth,...}]]}` (x/y keyframes allow walking, leaning, piggyback).
  - Two-shot defaults: Kat x≈330, him x≈780. Floor: Kat size 950, him 1100. Counter: Kat 1000 y 1450, him 1150 y 1440.
  - Head centre ≈ y − 0.8·size + 0.436·size (use for close-ups: zoom 2.1–2.5 on that point).
- **state keys**: pose sit|loaf|lie · eyes open|happy|closed|teary|cry|flat|squeeze · mouth w|open|o|sad|wobble|smirk ·
  look −1..1 · ears −1 (droop) · shake/bounce/wiggle 0–1.5 · blush "big" (Kat only) · extras [hearts, sparkles, zzz, dots, rain, sweat, sweat_big] ·
  hold heart|flower|cookie|phone|mug|star|gift · hat santa|wizard · bowtie true.
- **props**: cookie, half_cookie, crumbs, plate, jar (`empty`), cookie_tray, bag (`color`), laptop (`screen`), clock (`text`,`text2`,`switch`), gift, phone, zzz_cloud — all with x/y/s keyframes and optional t0/t1.
- **cam**: `{"zoom":[[t,z]],"x":[[t,v]],"y":[[t,v]],"shake":[[t,0..1.2]]}` — crash zoom = jump zoom 1.0→2.4 in 0.25 s.
- **stickers** (screen space, global time): `{text,t0,t1,x,y,size,color,rot}` — sound words like *sweating*, *guilty*, *evidence*, ta-da!, NOOOO, hehe, swoon.
- **sfx**: pop, boing, crunch, purr, ding, whoosh, sting (dramatic), gulp, tada.
- **overlays**: `{"kind":"loading","label","t0","t1","keys":[[t,pct]]}` (loading-bar trend).

## Checks before scheduling
Grab 4 frames per video (ffmpeg) and look: faces not covered, caption readable, nothing drawn over faces, props make sense
(e.g. an "empty" jar is empty). Fix and re-render rather than post a broken video.
