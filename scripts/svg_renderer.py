"""Pure SVG renderer: data dict in, self-contained SVG string out.

No scripts, no external references, no external fonts. All external text is
sanitised and XML-escaped before insertion.
"""
from __future__ import annotations

import random
import re
from xml.sax.saxutils import escape

import config

C = config.COLORS
FONT = "ui-monospace,'SFMono-Regular',Menlo,Consolas,'DejaVu Sans Mono',monospace"
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]")


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


def _text(x, y, s, size=13, fill=None, weight="normal", anchor="start", cls="", extra=""):
    fill = fill or C["text"]
    c = f' class="{cls}"' if cls else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}"{c}{extra}>{s}</text>')


def _panel(x, y, w, h, title):
    cut = 14
    pts = f"{x+cut},{y} {x+w},{y} {x+w},{y+h-cut} {x+w-cut},{y+h} {x},{y+h} {x},{y+cut}"
    return (f'<polygon points="{pts}" fill="{C["panel"]}" fill-opacity="0.88" '
            f'stroke="{C["green2"]}" stroke-opacity="0.55" stroke-width="1"/>'
            f'<path d="M{x+cut} {y} h40" stroke="{C["green"]}" stroke-width="2"/>'
            + _text(x + 20, y + 26, clean(title), 11, C["green"], anchor="start",
                    extra=' letter-spacing="3"'))


def _rain(animate: bool) -> str:
    rnd = random.Random(1337)  # deterministic
    glyphs = "01ABCDEF<>/{}$#%=+*"
    out = [f'<g clip-path="url(#clip)" font-size="14" fill="{C["green2"]}">']
    for i in range(48):
        x = 12 + i * 25
        n = 26 if animate else 14
        chars = [rnd.choice(glyphs) for _ in range(n)]
        dur = round(rnd.uniform(9, 20), 1)
        delay = round(-rnd.uniform(0, dur), 1)
        op = round(rnd.uniform(0.10, 0.28), 2)
        tsp = "".join(f'<tspan x="{x}" dy="16">{escape(ch)}</tspan>' for ch in chars)
        if animate:
            out.append(f'<text y="-380" opacity="{op}" class="rain" '
                       f'style="animation-duration:{dur}s;animation-delay:{delay}s">{tsp}</text>')
        else:
            y0 = rnd.randint(0, config.HEIGHT - 260)
            out.append(f'<text y="{y0}" opacity="{op}">{tsp}</text>')
    out.append("</g>")
    return "".join(out)


def _cat(cx, cy, s=1.0, animate=True) -> str:
    """Original digital cat mascot: geometric head, circuit ears, scanning eyes."""
    g, h = C["green"], C["highlight"]
    blink = ' class="blink"' if animate else ""
    return (
        f'<g transform="translate({cx} {cy}) scale({s})" fill="none" stroke="{g}" '
        f'stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round">'
        f'<path d="M-46 -8 L-40 -52 L-14 -30 Q0 -34 14 -30 L40 -52 L46 -8 '
        f'Q50 30 0 44 Q-50 30 -46 -8 Z" fill="{C["bg"]}" fill-opacity="0.85"/>'
        f'<path d="M-36 -36 L-30 -20 M36 -36 L30 -20" stroke="{h}" stroke-width="1.4"/>'
        f'<g{blink} fill="{g}" stroke="none">'
        f'<path d="M-30 -4 L-12 -9 L-14 4 Z"/><path d="M30 -4 L12 -9 L14 4 Z"/></g>'
        f'<path d="M-4 14 L4 14 L0 19 Z" fill="{h}" stroke="none"/>'
        f'<path d="M0 19 V25 M0 25 Q-7 31 -13 26 M0 25 Q7 31 13 26" stroke-width="1.6"/>'
        f'<path d="M-52 10 L-26 14 M-52 20 L-26 20 M52 10 L26 14 M52 20 L26 20" '
        f'stroke="{C["green2"]}" stroke-width="1.2"/>'
        f'<path d="M-14 -30 V-18 H-6 M14 -30 V-18 H6" stroke="{C["green2"]}" stroke-width="1"/>'
        f'</g>')


def _core(cx, cy, animate) -> str:
    rings = (
        f'<circle cx="{cx}" cy="{cy}" r="96" fill="none" stroke="{C["green2"]}" stroke-opacity="0.35" '
        f'stroke-dasharray="2 8"{" class=\"spin\"" if animate else ""} style="transform-origin:{cx}px {cy}px"/>'
        f'<circle cx="{cx}" cy="{cy}" r="80" fill="none" stroke="{C["green"]}" stroke-opacity="0.7" '
        f'stroke-width="1.5" stroke-dasharray="90 30 10 30"{" class=\"spin2\"" if animate else ""} '
        f'style="transform-origin:{cx}px {cy}px"/>'
        f'<circle cx="{cx}" cy="{cy}" r="64" fill="{C["panel"]}" stroke="{C["highlight"]}" '
        f'stroke-opacity="0.5"/>')
    ticks = "".join(
        f'<path d="M{cx} {cy-100} v8" stroke="{C["green"]}" stroke-opacity="0.6" '
        f'transform="rotate({a} {cx} {cy})"/>' for a in range(0, 360, 30))
    return rings + ticks + _cat(cx, cy + 2, 0.95, animate)


def _defs(animate: bool) -> str:
    css = ""
    if animate:
        css = (
            "<style>"
            "@keyframes fall{from{transform:translateY(0)}to{transform:translateY(%dpx)}}"
            "@keyframes spin{to{transform:rotate(360deg)}}"
            "@keyframes spinr{to{transform:rotate(-360deg)}}"
            "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
            "@keyframes scan{from{transform:translateY(0)}to{transform:translateY(%dpx)}}"
            "@keyframes pulse{0%%,100%%{opacity:1}50%%{opacity:.35}}"
            "@keyframes blink{0%%,92%%,100%%{transform:scaleY(1)}96%%{transform:scaleY(.1)}}"
            ".rain{animation-name:fall;animation-timing-function:linear;animation-iteration-count:infinite}"
            ".spin{animation:spin 40s linear infinite}.spin2{animation:spinr 24s linear infinite}"
            ".bar{transform-box:fill-box;transform-origin:left center;animation:grow 1.6s ease-out both}"
            ".scan{animation:scan 7s linear infinite}"
            ".pulse{animation:pulse 2.2s ease-in-out infinite}"
            ".blink{transform-box:fill-box;transform-origin:center;animation:blink 5s infinite}"
            "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
            "</style>" % (config.HEIGHT + 400, config.HEIGHT))
    return (
        f"<defs>{css}"
        f'<clipPath id="clip"><rect width="{config.WIDTH}" height="{config.HEIGHT}"/></clipPath>'
        f'<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
        f'<path d="M40 0H0V40" fill="none" stroke="{C["green2"]}" stroke-opacity="0.07"/></pattern>'
        f'<linearGradient id="scanline" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{C["green"]}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{C["green"]}" stop-opacity="0.10"/></linearGradient>'
        f"</defs>")


def _stat(x, y, label, value):
    return (f'<rect x="{x}" y="{y}" width="270" height="78" fill="{C["panel"]}" fill-opacity="0.88" '
            f'stroke="{C["green2"]}" stroke-opacity="0.45"/>'
            + _text(x + 20, y + 30, label, 11, C["muted"], extra=' letter-spacing="3"')
            + _text(x + 20, y + 62, fmt(value), 28, C["green"], "bold"))


def _languages(x, y, w, h, langs, animate):
    out = [_panel(x, y, w, h, "LANGUAGE MATRIX · TOP 40 ACTIVE REPOS")]
    total = sum(langs.values())
    if not total:
        return "".join(out) + _text(x + 20, y + 62, "no language data available", 12, C["muted"])
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
    for i, (name, n) in enumerate(top):
        pct = 100 * n / total
        yy = y + 58 + i * 34
        bw = 300
        out.append(_text(x + 20, yy, clean(name, 18), 13))
        out.append(f'<rect x="{x+160}" y="{yy-11}" width="{bw}" height="10" fill="{C["bg"]}" '
                   f'stroke="{C["green2"]}" stroke-opacity="0.3"/>')
        cls = ' class="bar"' if animate else ""
        out.append(f'<rect{cls} x="{x+160}" y="{yy-11}" width="{max(2, bw*pct/100):.1f}" height="10" '
                   f'fill="{C["green"]}" fill-opacity="{0.95 - i*0.1:.2f}" '
                   f'style="animation-delay:{i*0.12:.2f}s"/>')
        out.append(_text(x + w - 20, yy, f"{pct:.1f}%", 12, C["highlight"], anchor="end"))
    return "".join(out)


def _heatmap(x, y, w, h, contrib):
    out = [_panel(x, y, w, h, "CONTRIBUTION GRID")]
    weeks = contrib["weeks"][-53:]
    peak = max((c for wk in weeks for c in wk), default=0) or 1
    cell, gap = 7, 2
    shades = ["#0A2A1A", "#0E5C36", C["green2"], C["green"], C["highlight"]]
    for wi, wk in enumerate(weeks):
        for di, c in enumerate(wk):
            lvl = 0 if c == 0 else min(4, 1 + int(3 * (c - 1) / max(peak, 2)))
            out.append(f'<rect x="{x+22+wi*(cell+gap)}" y="{y+48+di*(cell+gap)}" '
                       f'width="{cell}" height="{cell}" fill="{shades[lvl]}"/>')
    out.append(_text(x + 22, y + h - 18, f"{fmt(contrib['total'])} contributions in the last year",
                     12, C["highlight"]))
    return "".join(out)


def _events(x, y, w, h, events):
    out = [_panel(x, y, w, h, "RECENT ACTIVITY")]
    if not events:
        return "".join(out) + _text(x + 20, y + 62, "no recent public activity", 12, C["muted"])
    for i, ev in enumerate(events[: (h - 50) // 28]):
        yy = y + 58 + i * 28
        out.append(_text(x + 20, yy, clean(ev["date"], 10), 11, C["muted"]))
        out.append(_text(x + 100, yy, clean(ev["kind"], 8), 11, C["green"], "bold"))
        out.append(_text(x + 170, yy, clean(ev["text"], int((w - 190) / 7.4)), 12))
    return "".join(out)


def _featured(x, y, w, h, repos, names):
    by = {r["name"].lower(): r for r in repos}
    cw = (w - 32 - 2 * 20) / 3
    out = [_panel(x, y, w, h, "PROJECT SHOWCASE")]
    for i, name in enumerate(names):
        cx = x + 16 + i * (cw + 20)
        top = y + 44
        r = by.get(name.lower())
        out.append(f'<rect x="{cx:.0f}" y="{top}" width="{cw:.0f}" height="{h-62}" fill="{C["bg"]}" '
                   f'stroke="{C["green2"]}" stroke-opacity="0.4"/>')
        out.append(_text(f"{cx+16:.0f}", top + 30, clean(name, 22), 18, C["green"], "bold"))
        if not r:
            out.append(_text(f"{cx+16:.0f}", top + 58, "no public repository found", 12, C["muted"]))
            continue
        lim = int((cw - 32) / 7.2)
        out.append(_text(f"{cx+16:.0f}", top + 58, clean(r["description"] or "no description", lim), 12))
        status = "archived" if r["archived"] else f"last push {clean(r['updated'], 10)}"
        meta = " · ".join(p for p in (clean(r["language"], 14), status) if p)
        out.append(_text(f"{cx+16:.0f}", top + 84, meta, 11, C["highlight"]))
        out.append(_text(f"{cx+16:.0f}", top + 106, f"\u2605 {fmt(r['stars'])}   \u2442 {fmt(r['forks'])}",
                         12, C["muted"]))
        out.append(_text(f"{cx+16:.0f}", top + 128,
                         clean(r["url"].replace("https://", ""), lim), 11, C["green2"]))
    return "".join(out)


def _repos(x, y, w, h, repos, exclude):
    out = [_panel(x, y, w, h, "REPOSITORY INTELLIGENCE")]
    ex = {e.lower() for e in exclude}
    pool = [r for r in repos if not r["fork"] and r["name"].lower() not in ex]
    # Stable two-pass sort: stars descending, then most recently pushed first
    pool.sort(key=lambda r: r["updated"], reverse=True)
    pool.sort(key=lambda r: r["stars"], reverse=True)
    for i, r in enumerate(pool[: config.MAX_REPOS_SHOWN]):
        yy = y + 56 + i * 40
        out.append(_text(x + 20, yy, clean(r["name"], 24), 13, C["green"], "bold"))
        out.append(_text(x + 20, yy + 17, clean(r["description"] or "no description", int((w - 200) / 7)), 11, C["muted"]))
        out.append(_text(x + w - 20, yy, f"\u2605 {fmt(r['stars'])}  \u2442 {fmt(r['forks'])}", 12, C["highlight"], anchor="end"))
        out.append(_text(x + w - 20, yy + 17, clean(r["updated"], 10), 11, C["muted"], anchor="end"))
    if not pool:
        out.append(_text(x + 20, y + 62, "no other public repositories", 12, C["muted"]))
    return "".join(out)


def render(data: dict | None, generated: str, animate: bool = True, banner: str | None = None) -> str:
    W, H = config.WIDTH, config.HEIGHT
    d = data or {}
    contrib = d.get("contributions")
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="{FONT}" role="img" aria-labelledby="t d">',
         f'<title id="t">{clean(config.PRODUCT)} \u2014 {clean(config.SUBTITLE)}</title>',
         f'<desc id="d">{clean(config.TAGLINE)} Generated GitHub profile dashboard for {clean(config.USERNAME)}.</desc>',
         _defs(animate),
         f'<rect width="{W}" height="{H}" fill="{C["bg"]}"/>',
         f'<rect width="{W}" height="{H}" fill="url(#grid)"/>',
         _rain(animate)]
    if animate:
        p.append(f'<rect class="scan" y="-200" width="{W}" height="200" fill="url(#scanline)"/>')

    # Header
    p.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" fill="none" stroke="{C["green2"]}" '
             f'stroke-opacity="0.5"/>')
    p.append(_text(48, 92, clean(config.PRODUCT), 54, C["green"], "bold", extra=' letter-spacing="6"'))
    p.append(_text(52, 126, clean(config.SUBTITLE), 15, C["highlight"], extra=' letter-spacing="8"'))
    p.append(_text(52, 160, clean(config.TAGLINE), 14, C["text"]))
    pulse = ' class="pulse"' if animate else ""
    p.append(f'<circle{pulse} cx="58" cy="196" r="5" fill="{C["green"]}"/>')
    p.append(_text(74, 200, "INTERFACE: ONLINE", 12, C["green"]))
    p.append(_text(250, 200, "AI BACKEND: NONE \u2014 VISUAL PRESENTATION", 12, C["muted"]))
    p.append(_text(52, 224, f"&gt; user: {clean(config.USERNAME)}", 12, C["muted"]))
    p.append(_core(1010, 124, animate))

    # Stats
    sy = 256
    for i, (lbl, key) in enumerate((("PUBLIC REPOS", "public_repos"), ("TOTAL STARS", "stars"),
                                    ("TOTAL FORKS", "forks"), ("FOLLOWERS", "followers"))):
        p.append(_stat(40 + i * 288, sy, lbl, d.get(key)))

    # Row A
    ry, rh = 360, 270
    p.append(_languages(40, ry, 560, rh, d.get("languages", {}), animate))
    if contrib:
        p.append(_heatmap(620, ry, 540, rh, contrib))
    else:
        p.append(_events(620, ry, 540, rh, d.get("events", [])))

    # Showcase
    p.append(_featured(40, 650, 1120, 210, d.get("repos", []), config.FEATURED))

    # Row C
    cy, ch = 880, 230
    if contrib:
        p.append(_repos(40, cy, 560, ch, d.get("repos", []), config.FEATURED))
        p.append(_events(620, cy, 540, ch, d.get("events", [])))
    else:
        p.append(_repos(40, cy, 1120, ch, d.get("repos", []), config.FEATURED))

    # Footer / banner
    foot = f"generated {clean(generated)} \u00b7 source: GitHub public API"
    if banner:
        foot = f"{clean(banner)}  \u00b7  " + foot
    p.append(_text(48, H - 14, foot, 10, C["muted"], extra=' id="generated"'))
    p.append("</svg>")
    return "".join(p)
