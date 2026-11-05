"""Pure SVG renderer: data dict in, self-contained SVG string out.

Transparent canvas, IDE-style windows, streaming Matrix rain, simulated chat.
No scripts, no external references, no external fonts. All external text is
sanitised and XML-escaped before insertion.
"""
from __future__ import annotations

import math
import random
import re
import textwrap
from xml.sax.saxutils import escape

import config

C = config.COLORS
W, H = config.WIDTH, config.HEIGHT
FONT = "ui-monospace,'SFMono-Regular',Menlo,Consolas,'DejaVu Sans Mono',monospace"
WIN, WIN_BORDER, TITLEBAR, GUTTER = "#0A1410", "#1C3B2C", "#0F1F18", "#35614B"
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]")
GLYPHS = "01234567890ABCDEFGHJKLMNPRSTUVWXYZ<>/{}$#%=+*&|;:"
CHAT_SLOT = 9  # seconds per dialogue


def clean(text: object, limit: int | None = None) -> str:
    """Sanitise untrusted text: strip control/bidi chars, collapse space, truncate, escape."""
    s = _CTRL.sub("", str(text if text is not None else ""))
    s = " ".join(s.split())
    if limit and len(s) > limit:
        s = s[: limit - 1].rstrip() + "\u2026"
    return escape(s, {'"': "&quot;"})


def fmt(n: int | None) -> str:
    if n is None:
        return "--"
    return f"{n/1000:.1f}k" if n >= 10000 else f"{n:,}"


def T(x, y, s, size=13, fill=None, weight="normal", anchor="start", cls="", extra=""):
    fill = fill or C["text"]
    c = f' class="{cls}"' if cls else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}"{c}{extra}>{s}</text>')


# ---------------------------------------------------------------- styles / defs
def _defs(animate: bool, n_chat: int) -> str:
    css = (".rn{fill:#00C878}.rh{fill:#D6FFE9}"
           "@media (prefers-color-scheme:light){.rn{fill:#00864A}.rh{fill:#005C32}}")
    if animate:
        slot = 100.0 / max(n_chat, 1)
        f = 0.5
        kf = []
        for i in range(n_chat):
            a, b = i * slot, (i + 1) * slot
            end = min(b, 100 - f)
            for name, t_on in (("q", a + slot * 0.04), ("d", a + slot * 0.14), ("a", a + slot * 0.30)):
                t_off = end if name != "d" else a + slot * 0.30
                kf.append(f"@keyframes {name}{i}{{0%{{opacity:0}}{t_on:.2f}%{{opacity:0}}"
                          f"{t_on+f:.2f}%{{opacity:1}}{t_off:.2f}%{{opacity:1}}"
                          f"{min(t_off+f, 100):.2f}%{{opacity:0}}100%{{opacity:0}}}}")
        css += (
            f"@keyframes fall{{from{{transform:translateY(0)}}to{{transform:translateY({H+520}px)}}}}"
            "@keyframes flick{0%,100%{opacity:.05}50%{opacity:1}}"
            "@keyframes spin{to{transform:rotate(360deg)}}"
            "@keyframes spinr{to{transform:rotate(-360deg)}}"
            "@keyframes arc{from{stroke-dasharray:0 377}}"
            "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
            "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}"
            "@keyframes caret{0%,49%{opacity:1}50%,100%{opacity:0}}"
            "@keyframes blink{0%,92%,100%{transform:scaleY(1)}96%{transform:scaleY(.1)}}"
            ".rain{animation-name:fall;animation-timing-function:linear;animation-iteration-count:infinite}"
            ".fl{animation-name:flick;animation-timing-function:steps(2,end);animation-iteration-count:infinite}"
            ".spin{animation:spin 40s linear infinite}.spin2{animation:spinr 24s linear infinite}"
            ".arc{animation:arc 1.8s ease-out both}"
            ".pulse{animation:pulse 2.2s ease-in-out infinite}"
            ".caret{animation:caret 1s steps(1) infinite}"
            ".blink{transform-box:fill-box;transform-origin:center;animation:blink 5s infinite}"
            + "".join(kf)
            + "@media (prefers-reduced-motion:reduce){*{animation:none!important}"
              ".cq0,.ca0{opacity:1!important}}")
    return (
        f"<defs><style>{css}</style>"
        f'<clipPath id="clip"><rect width="{W}" height="{H}"/></clipPath>'
        f'<filter id="glow" x="-30%" y="-30%" width="160%" height="160%">'
        f'<feGaussianBlur stdDeviation="2.2" result="b"/>'
        f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        f"</defs>")


# ---------------------------------------------------------------- matrix rain
def _rain(animate: bool) -> str:
    rnd = random.Random(1337)
    out = [f'<g clip-path="url(#clip)" font-size="14">']
    cols = 78
    for i in range(cols):
        x = round(i * (W / cols) + rnd.uniform(-6, 6), 1)
        fs = rnd.choice((11, 12, 13, 14, 16))
        lh = fs + 3
        n = rnd.randint(14, 32)
        a = [rnd.choice(GLYPHS) for _ in range(n)]
        b = [rnd.choice(GLYPHS) for _ in range(n)]
        speed = rnd.uniform(70, 190)
        dur = round((H + 520) / speed, 1)
        delay = round(-rnd.uniform(0, dur), 1)

        def spans(chars):
            s = []
            for j, ch in enumerate(chars):
                op = 0.05 + 0.5 * j / n
                head = j == n - 1
                s.append(f'<tspan x="{x}" dy="{0 if j == 0 else lh}"'
                         f'{" class=\"rh\"" if head else ""} fill-opacity="{1 if head else round(op,2)}">'
                         f"{escape(ch)}</tspan>")
            return "".join(s)

        y0 = -n * lh - 20
        if animate:
            fdur = round(rnd.uniform(0.5, 1.6), 2)
            out.append(
                f'<g class="rain" style="animation-duration:{dur}s;animation-delay:{delay}s" '
                f'font-size="{fs}"><text class="rn" y="{y0}">{spans(a)}</text>'
                + (f'<text class="rn fl" y="{y0}" style="animation-duration:{fdur}s;'
                   f'animation-delay:{-round(rnd.uniform(0, fdur), 2)}s">{spans(b)}</text>' if i % 2 else '')
                + '</g>')
        else:
            ys = rnd.randint(0, H - 300)
            out.append(f'<text class="rn" font-size="{fs}" y="{ys}">{spans(a)}</text>')
    out.append("</g>")
    return "".join(out)


# ---------------------------------------------------------------- window chrome
def _window(x, y, w, h, name):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{WIN}" fill-opacity="0.96" '
           f'stroke="{WIN_BORDER}"/>',
           f'<path d="M{x} {y+30} V{y+8} Q{x} {y} {x+8} {y} H{x+w-8} Q{x+w} {y} {x+w} {y+8} V{y+30} Z" '
           f'fill="{TITLEBAR}"/>']
    for i, col in enumerate(("#1F6F47", "#2FA66A", C["green"])):
        out.append(f'<circle cx="{x+16+i*16}" cy="{y+15}" r="4.5" fill="{col}"/>')
    out.append(f'<rect x="{x+68}" y="{y+6}" width="{len(name)*7+24}" height="24" fill="{WIN}"/>')
    out.append(f'<rect x="{x+68}" y="{y+28}" width="{len(name)*7+24}" height="2" fill="{C["green"]}"/>')
    out.append(T(x + 80, y + 22, clean(name), 11, C["highlight"]))
    for r in range((h - 44) // 22):
        out.append(T(x + 30, y + 52 + r * 22, r + 1, 10, GUTTER, anchor="end"))
    out.append(f'<path d="M{x+38} {y+36} V{y+h-6}" stroke="{WIN_BORDER}"/>')
    return "".join(out)


# ---------------------------------------------------------------- banner scene
def _scene(animate) -> str:
    rnd = random.Random(7)
    g, h = C["green"], C["highlight"]
    o = []

    def monitor(x, y, w, hh, lines):
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{hh}" rx="4" fill="#020B07" '
                 f'stroke="{C["green2"]}" stroke-opacity="0.7"/>')
        yy = y + 14
        while yy < y + hh - 8 and lines:
            ind = rnd.choice((0, 0, 14, 28))
            ww = rnd.randint(30, int(w * 0.6))
            o.append(f'<rect x="{x+10+ind}" y="{yy}" width="{min(ww, w-24-ind)}" height="3" '
                     f'fill="{g}" fill-opacity="{rnd.choice((0.25, 0.4, 0.6))}"/>')
            yy += 9

    monitor(80, 96, 250, 140, True)
    monitor(870, 96, 250, 140, True)
    monitor(350, 44, 500, 196, False)
    # centre monitor title
    o.append(T(600, 110, clean(config.PRODUCT), 44, g, "bold", "middle", extra=' letter-spacing="8" filter="url(#glow)"'))
    o.append(T(600, 140, clean(config.SUBTITLE), 12, h, anchor="middle", extra=' letter-spacing="7"'))
    o.append(T(600, 166, clean(config.TAGLINE), 13, C["text"], anchor="middle"))
    pulse = ' class="pulse"' if animate else ""
    o.append(f'<circle{pulse} cx="440" cy="196" r="4" fill="{g}"/>')
    o.append(T(452, 200, "INTERFACE ONLINE", 10, g))
    o.append(T(640, 200, "AI BACKEND: NONE (VISUAL)", 10, C["muted"]))
    # AI core on right monitor
    cx, cy = 995, 166
    sp1 = ' class="spin"' if animate else ""
    sp2 = ' class="spin2"' if animate else ""
    o.append(f'<circle{sp1} cx="{cx}" cy="{cy}" r="52" fill="none" stroke="{C["green2"]}" stroke-dasharray="2 7" '
             f'style="transform-origin:{cx}px {cy}px"/>')
    o.append(f'<circle{sp2} cx="{cx}" cy="{cy}" r="40" fill="none" stroke="{g}" stroke-width="1.5" '
             f'stroke-dasharray="70 20 8 20" style="transform-origin:{cx}px {cy}px"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="22" fill="{g}" fill-opacity="0.12" stroke="{h}" stroke-opacity="0.6"/>')
    # desk + silhouette
    o.append(f'<path d="M40 300 H1160" stroke="{C["green2"]}" stroke-opacity="0.45"/>')
    o.append(f'<path d="M455 330 C470 286 540 280 568 282 L632 282 C660 280 730 286 745 330 Z" '
             f'fill="#010503" stroke="{g}" stroke-opacity="0.45"/>')
    o.append(f'<circle cx="600" cy="256" r="36" fill="#010503" stroke="{g}" stroke-opacity="0.45"/>')
    o.append(f'<path d="M565 244 Q600 206 635 244 Q620 232 600 232 Q580 232 565 244 Z" fill="#010503"/>')
    return "".join(o)


# ---------------------------------------------------------------- cat
def _cat(cx, cy, s, animate) -> str:
    g, h, g2 = C["green"], C["highlight"], C["green2"]
    blink = ' class="blink"' if animate else ""
    return (
        f'<g transform="translate({cx} {cy}) scale({s})" fill="none" stroke="{g}" stroke-width="2" '
        f'stroke-linejoin="round" stroke-linecap="round" filter="url(#glow)">'
        # body
        f'<path d="M-38 38 Q-62 70 -44 104 H44 Q62 70 38 38" fill="{WIN}"/>'
        f'<path d="M-20 60 V96 M0 56 V100 M20 60 V96" stroke="{g2}" stroke-width="1" stroke-opacity="0.7"/>'
        # head
        f'<path d="M-46 -8 L-42 -56 L-16 -32 Q0 -36 16 -32 L42 -56 L46 -8 Q52 32 0 46 Q-52 32 -46 -8 Z" fill="{WIN}"/>'
        f'<path d="M-37 -40 L-31 -22 M37 -40 L31 -22" stroke="{h}" stroke-width="1.3"/>'
        # circuit forehead
        f'<path d="M0 -33 V-20 M-10 -30 V-22 H-4 M10 -30 V-22 H4" stroke="{g2}" stroke-width="1"/>'
        f'<circle cx="0" cy="-17" r="2" fill="{h}" stroke="none"/>'
        # eyes
        f'<g{blink} stroke="none"><path d="M-32 -2 L-11 -9 L-13 7 Z" fill="{g}"/>'
        f'<path d="M32 -2 L11 -9 L13 7 Z" fill="{g}"/>'
        f'<ellipse cx="-20" cy="-1" rx="1.6" ry="5" fill="{WIN}"/><ellipse cx="20" cy="-1" rx="1.6" ry="5" fill="{WIN}"/></g>'
        # nose / mouth / whiskers
        f'<path d="M-4 15 H4 L0 20 Z" fill="{h}" stroke="none"/>'
        f'<path d="M0 20 V26 M0 26 Q-7 32 -13 27 M0 26 Q7 32 13 27" stroke-width="1.5"/>'
        f'<path d="M-54 9 L-26 14 M-54 20 L-26 20 M-52 31 L-26 26 M54 9 L26 14 M54 20 L26 20 M52 31 L26 26" '
        f'stroke="{g2}" stroke-width="1"/>'
        f'<path d="M-30 30 H-20 L-16 36 M30 30 H20 L16 36" stroke="{g2}" stroke-width="1"/>'
        f'</g>')


# ---------------------------------------------------------------- panels
def _stats(x, y, w, h, d):
    o = [_window(x, y, w, h, "stats.md")]
    cw, ch = (w - 56 - 16 - 12) / 2, 78
    items = (("\u2605", "TOTAL STARS", d.get("stars")), ("\u2442", "TOTAL FORKS", d.get("forks")),
             ("\u25c9", "FOLLOWERS", d.get("followers")), ("\u2192", "FOLLOWING", d.get("following")))
    for i, (ic, lab, val) in enumerate(items):
        cx = x + 50 + (i % 2) * (cw + 12)
        cy = y + 44 + (i // 2) * (ch + 12)
        o.append(f'<rect x="{cx:.0f}" y="{cy}" width="{cw:.0f}" height="{ch}" rx="4" fill="#03140C" '
                 f'stroke="{C["green2"]}" stroke-opacity="0.4"/>')
        o.append(T(f"{cx+16:.0f}", cy + 36, ic, 22, C["green"]))
        o.append(T(f"{cx+52:.0f}", cy + 26, lab, 11, C["muted"], extra=' letter-spacing="2"'))
        o.append(T(f"{cx+52:.0f}", cy + 62, fmt(val), 30, C["text"], "bold"))
    n = d.get("public_repos")
    o.append(T(x + 50, y + h - 14, f"public_repos = {fmt(n)}", 11, C["highlight"]))
    return "".join(o)


def _dialogues(d: dict, seed: str, limit: int = 5) -> list[tuple[str, str]]:
    first = ("who are you?", "I'm a visual interface for the iliyahaddad profile. No AI model runs here; "
             "replies are written from live GitHub data.")
    pool: list[tuple[str, str]] = []
    if d.get("stars") is not None:
        pool.append(("how many stars?", f"{fmt(d['stars'])} stars and {fmt(d['forks'])} forks across "
                     f"{fmt(d['public_repos'])} public repositories."))
        pool.append(("how many followers?", f"{fmt(d['followers'])} followers, following {fmt(d['following'])}."))
    langs = d.get("languages") or {}
    if langs:
        tot = sum(langs.values())
        name, n = max(langs.items(), key=lambda kv: kv[1])
        pool.append(("top language?", f"{name} leads with {100*n/tot:.1f}% of the code bytes."))
    if d.get("events"):
        ev = d["events"][0]
        pool.append(("what's new?", f"Latest public activity: {ev['text']} on {ev['date']}."))
    repos = d.get("repos") or []
    if repos:
        r = max(repos, key=lambda r: r["updated"])
        pool.append(("latest push?", f"{r['name']} on {r['updated']}."))
        by = {r["name"].lower() for r in repos}
        found = [n for n in config.FEATURED if n.lower() in by]
        pool.append(("featured projects?", f"{len(found)} of {len(config.FEATURED)} found publicly: "
                     f"{', '.join(found) if found else 'none'}."))
    if d.get("contributions"):
        pool.append(("contributions this year?", f"{fmt(d['contributions']['total'])} public contributions."))
    random.Random(seed).shuffle(pool)
    return [first] + pool[:limit]


def _wrap(s: str, width: int, lines: int) -> list[str]:
    out = textwrap.wrap(" ".join(str(s).split()), width) or [""]
    if len(out) > lines:
        out = out[:lines]
        out[-1] = out[-1][: width - 1] + "\u2026"
    return out


def _chat(x, y, w, h, d, animate, seed):
    o = [_window(x, y, w, h, "farboud.chat")]
    o.append(_cat(x + 100, y + 112, 0.95, animate))
    o.append(T(x + 100, y + h - 14, "FARBOUD", 11, C["green"], anchor="middle", extra=' letter-spacing="4"'))
    tx, tw = x + 200, 44
    dl = _dialogues(d, seed)
    o.append(T(tx, y + 46, "\u25cf farboud \u00b7 simulated replies from live data", 10, C["muted"]))
    ytop = y + 72
    if animate:
        n = len(dl)
        dur = n * CHAT_SLOT
        for i, (q, a) in enumerate(dl):
            qs = f'<g class="cq{i}" opacity="0" style="animation:q{i} {dur}s linear infinite">' \
                 + T(tx, ytop, "you \u25b8 " + clean(q, tw - 6), 12, C["highlight"]) + "</g>"
            dots = f'<g opacity="0" style="animation:d{i} {dur}s linear infinite">' \
                   + T(tx, ytop + 24, "farboud \u25b8 \u2022 \u2022 \u2022", 12, C["muted"]) + "</g>"
            al = _wrap(a, tw - 10, 4)
            ans = f'<g class="ca{i}" opacity="0" style="animation:a{i} {dur}s linear infinite">'
            for k, ln in enumerate(al):
                pre = "farboud \u25b8 " if k == 0 else "           "
                ans += T(tx, ytop + 24 + k * 19, pre + clean(ln), 12, C["text"], extra=' xml:space="preserve"')
            o.append(qs + dots + ans + "</g>")
    else:
        yy = ytop
        for q, a in dl[:2]:
            o.append(T(tx, yy, "you \u25b8 " + clean(q, tw - 6), 12, C["highlight"]))
            for k, ln in enumerate(_wrap(a, tw - 10, 3)):
                pre = "farboud \u25b8 " if k == 0 else "           "
                o.append(T(tx, yy + 20 + k * 18, pre + clean(ln), 12, C["text"], extra=' xml:space="preserve"'))
            yy += 20 + 18 * min(3, len(_wrap(a, tw - 10, 3))) + 12
    iy = y + h - 40
    o.append(f'<rect x="{tx}" y="{iy}" width="{w-216}" height="26" rx="4" fill="#03140C" '
             f'stroke="{C["green2"]}" stroke-opacity="0.45"/>')
    o.append(T(tx + 12, iy + 17, "ask farboud\u2026", 11, C["muted"]))
    cls = ' class="caret"' if animate else ""
    o.append(f'<rect{cls} x="{tx+100}" y="{iy+7}" width="7" height="13" fill="{C["green"]}"/>')
    return "".join(o)


def _featured(x, y, w, h, repos):
    o = [_window(x, y, w, h, "projects/")]
    by = {r["name"].lower(): r for r in repos}
    for i, name in enumerate(config.FEATURED):
        yy = y + 52 + i * 72
        r = by.get(name.lower())
        o.append(T(x + 50, yy, clean(name), 14, C["green"], "bold"))
        if not r:
            o.append(T(x + 50, yy + 22, "no public repository found", 11, C["muted"]))
            continue
        status = "archived" if r["archived"] else f"last push {clean(r['updated'], 10)}"
        o.append(T(x + w - 16, yy, f"\u2605 {fmt(r['stars'])}  \u2442 {fmt(r['forks'])}", 12, C["highlight"], anchor="end"))
        o.append(T(x + 50, yy + 22, clean(r["description"] or "no description", int((w - 70) / 7.2)), 12))
        meta = " \u00b7 ".join(p for p in (clean(r["language"], 14), status) if p)
        o.append(T(x + 50, yy + 44, meta + "  \u00b7  " + clean(r["url"].replace("https://", ""), 40), 10.5, C["green2"]))
    return "".join(o)


def _languages(x, y, w, h, langs, animate):
    o = [_window(x, y, w, h, "languages.json")]
    tot = sum(langs.values())
    if not tot:
        return "".join(o) + T(x + 50, y + 62, "no language data available", 12, C["muted"])
    top = sorted(langs.items(), key=lambda kv: -kv[1])
    segs = [(n, v) for n, v in top[:4]]
    rest = sum(v for _, v in top[4:])
    if rest:
        segs.append(("Others", rest))
    cols = [C["green"], "#2F81F7", "#F0883E", "#E3B341", "#8B949E"]
    cx, cy, r, cum = x + 130, y + 130, 60, 0.0
    circ = 2 * math.pi * r
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#03140C" stroke-width="22"/>')
    for i, (n, v) in enumerate(segs):
        ln = circ * v / tot
        cls = ' class="arc"' if animate else ""
        o.append(f'<circle{cls} cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{cols[i]}" stroke-width="22" '
                 f'stroke-dasharray="{max(ln-1.5, 0.5):.1f} {circ:.1f}" stroke-dashoffset="{-cum:.1f}" '
                 f'transform="rotate(-90 {cx} {cy})"/>')
        cum += ln
    o.append(T(cx, cy + 7, f"{100*segs[0][1]/tot:.1f}%", 19, C["text"], "bold", "middle"))
    for i, (n, v) in enumerate(segs):
        yy = y + 78 + i * 30
        o.append(f'<circle cx="{x+270}" cy="{yy-4}" r="5" fill="{cols[i]}"/>')
        o.append(T(x + 288, yy, clean(n, 16), 13))
        o.append(T(x + w - 20, yy, f"{100*v/tot:.1f}%", 13, C["highlight"], anchor="end"))
    return "".join(o)


def _events(x, y, w, h, events):
    o = [_window(x, y, w, h, "activity.log")]
    if not events:
        return "".join(o) + T(x + 50, y + 52, "no recent public activity", 12, C["muted"])
    for i, ev in enumerate(events[: (h - 44) // 22]):
        yy = y + 52 + i * 22
        o.append(T(x + 50, yy, clean(ev["date"], 10), 11, C["muted"]))
        o.append(T(x + 132, yy, clean(ev["kind"], 8), 11, C["green"], "bold"))
        o.append(T(x + 204, yy, clean(ev["text"], int((w - 220) / 7.2)), 12))
    return "".join(o)


def _heatmap(x, y, w, h, contrib):
    o = [_window(x, y, w, h, "contributions.svg")]
    weeks = contrib["weeks"][-53:]
    peak = max((c for wk in weeks for c in wk), default=0) or 1
    shades = ["#0E2A1D", "#0E5C36", C["green2"], C["green"], C["highlight"]]
    for wi, wk in enumerate(weeks):
        for di, c in enumerate(wk):
            lvl = 0 if c == 0 else min(4, 1 + int(3 * (c - 1) / max(peak, 2)))
            o.append(f'<rect x="{x+48+wi*9.2:.1f}" y="{y+48+di*11}" width="7.5" height="8" fill="{shades[lvl]}"/>')
    o.append(T(x + 50, y + h - 18, f"{fmt(contrib['total'])} contributions in the last year", 12, C["highlight"]))
    return "".join(o)


def _repos(x, y, w, h, repos):
    o = [_window(x, y, w, h, "repos.list")]
    ex = {n.lower() for n in config.FEATURED}
    pool = [r for r in repos if not r["fork"] and r["name"].lower() not in ex]
    pool.sort(key=lambda r: r["updated"], reverse=True)
    pool.sort(key=lambda r: -r["stars"])
    if not pool:
        return "".join(o) + T(x + 50, y + 52, "no other public repositories", 12, C["muted"])
    for i, r in enumerate(pool[: (h - 44) // 22]):
        yy = y + 52 + i * 22
        o.append(T(x + 50, yy, clean(r["name"], 20), 12, C["green"], "bold"))
        o.append(T(x + 220, yy, clean(r["description"] or "no description", int((w - 340) / 7.2)), 11, C["muted"]))
        o.append(T(x + w - 16, yy, f"\u2605 {fmt(r['stars'])}", 12, C["highlight"], anchor="end"))
    return "".join(o)


# ---------------------------------------------------------------- main
def render(data: dict | None, generated: str, animate: bool = True, banner: str | None = None) -> str:
    d = data or {}
    seed = f"{config.USERNAME}-{generated[:10]}"
    n_chat = len(_dialogues(d, seed))
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="{FONT}" role="img" aria-labelledby="t d">',
         f'<title id="t">{clean(config.PRODUCT)} \u2014 {clean(config.SUBTITLE)}</title>',
         f'<desc id="d">{clean(config.TAGLINE)} Generated GitHub profile dashboard for {clean(config.USERNAME)}.</desc>',
         _defs(animate, n_chat), _rain(animate), _scene(animate)]
    L, R, Wl, Wr = 20, 620, 580, 560
    p.append(_stats(L, 350, Wl, 250, d))
    p.append(_chat(R, 350, Wr, 250, d, animate, seed))
    p.append(_featured(L, 620, Wl, 244, d.get("repos", [])))
    p.append(_languages(R, 620, Wr, 244, d.get("languages", {}), animate))
    p.append(_events(L, 884, Wl, 168, d.get("events", [])))
    if d.get("contributions"):
        p.append(_heatmap(R, 884, Wr, 168, d["contributions"]))
    else:
        p.append(_repos(R, 884, Wr, 168, d.get("repos", [])))
    foot = f"generated {clean(generated)} \u00b7 source: GitHub public API"
    if banner:
        foot = f"{clean(banner)}  \u00b7  " + foot
    p.append(T(24, H - 16, foot, 10, C["muted"], extra=' id="generated"'))
    p.append("</svg>")
    return "".join(p)
