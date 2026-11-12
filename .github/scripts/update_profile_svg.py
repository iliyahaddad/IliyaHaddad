#!/usr/bin/env python3
"""Build a fully self-contained GitHub profile SVG using GitHub's public REST API.

No token, third-party badge/statistics service, image host, or Python dependency is used.
Only public profile/repository/event data is displayed. All cards are native SVG.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SVG_PATH = ROOT / "matrix-github-profile.svg"
USERNAME = "iliyahaddad"
API = "https://api.github.com"
API_VERSION = "2022-11-28"
TIMEOUT = 30
RETRIES = 3

NS = "http://www.w3.org/2000/svg"
S = f"{{{NS}}}"
ET.register_namespace("", NS)

BG = "#061a10"
CARD = "#092719"
CARD_ALT = "#0b3020"
GREEN = "#39ff88"
TEXT = "#e8fff1"
MUTED = "#9bc9ad"
GRID = "#1c6841"
GOLD = "#ffca68"
BLUE = "#67d5ff"


def log(message: str) -> None:
    print(f"[INFO] {message}", flush=True)


def request_json(url: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "iliyahaddad-matrix-profile/1.0",
    }
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                remaining = response.headers.get("X-RateLimit-Remaining", "unknown")
                log(f"GET {url} (rate limit remaining: {remaining})")
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                reset = exc.headers.get("X-RateLimit-Reset")
                if reset:
                    log(f"Rate limited; reset epoch: {reset}")
                raise RuntimeError(f"GitHub API rate limit/permission error: HTTP {exc.code}") from exc
            if exc.code >= 500 and attempt < RETRIES:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"GitHub API returned HTTP {exc.code} for {url}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == RETRIES:
                raise RuntimeError(f"GitHub API network error: {exc}") from exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Could not fetch {url}")


def fetch_profile_data():
    user = request_json(f"{API}/users/{USERNAME}")

    repos = []
    # Public repos only. One request per 100 repositories; no search API needed.
    for page in range(1, 6):
        batch = request_json(
            f"{API}/users/{USERNAME}/repos?type=owner&sort=updated&direction=desc&per_page=100&page={page}"
        )
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected repository API response")
        repos.extend(batch)
        if len(batch) < 100:
            break

    # Public events are useful as a recent-activity indicator, but not a complete
    # contribution calendar. GitHub only exposes a limited recent event history.
    events = request_json(f"{API}/users/{USERNAME}/events/public?per_page=100")
    if not isinstance(events, list):
        events = []

    return user, repos, events


def fmt_num(value) -> str:
    if value is None:
        return "—"
    try:
        n = int(value or 0)
    except (TypeError, ValueError):
        return "—"
    return f"{n:,}"


def short_date(value: str | None) -> str:
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return "—"


def clean_text(value, limit=42) -> str:
    value = str(value or "—")
    value = re.sub(r"[\r\n\t]+", " ", value)
    return value if len(value) <= limit else value[: limit - 1] + "…"


def add(parent, tag, **attrs):
    return ET.SubElement(parent, S + tag, {k.replace("_", "-"): str(v) for k, v in attrs.items() if v is not None})


def rect(parent, x, y, w, h, fill=CARD, stroke=GRID, radius=12, opacity=None):
    return add(parent, "rect", x=x, y=y, width=w, height=h, rx=radius, fill=fill,
               stroke=stroke, stroke_width=1.5, opacity=opacity)


def text(parent, x, y, value, size=16, fill=TEXT, weight="normal", anchor="start"):
    node = add(parent, "text", x=x, y=y, fill=fill, font_size=size,
               font_weight=weight, text_anchor=anchor,
               font_family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace")
    node.text = str(value)
    return node


def line(parent, x1, y1, x2, y2, color=GRID, width=1):
    add(parent, "line", x1=x1, y1=y1, x2=x2, y2=y2, stroke=color, stroke_width=width)


def clear_group(group, clip):
    group.clear()
    group.set("clip-path", clip)


def make_panels_opaque(nested):
    panel_strokes = {"#39ff88", "#19e6ff", "#b8ff3d", "#ffb02e"}
    for element in nested:
        if element.tag == S + "rect" and element.get("stroke") in panel_strokes and element.get("fill") == "#02100a":
            element.set("fill", BG)
            element.set("fill-opacity", "0.98")


def draw_repo_explorer(group, repos):
    clear_group(group, "url(#win2)")
    x, y, w = 880, 315, 630
    rect(group, x, y, w, 285, fill=BG, stroke=GRID, radius=14)
    text(group, x + 22, y + 34, "PUBLIC REPOSITORIES", 18, GREEN, "bold")
    text(group, x + w - 20, y + 34, f"{len(repos)} indexed", 13, MUTED, anchor="end")
    line(group, x + 18, y + 48, x + w - 18, y + 48)
    for i, repo in enumerate(repos[:4]):
        yy = y + 82 + i * 48
        name = clean_text(repo.get("name"), 32)
        desc = clean_text(repo.get("description") or "No description provided", 52)
        lang = clean_text(repo.get("language") or "Mixed / not specified", 18)
        stars = fmt_num(repo.get("stargazers_count"))
        forks = fmt_num(repo.get("forks_count"))
        text(group, x + 22, yy, name, 17, TEXT, "bold")
        text(group, x + 22, yy + 19, desc, 11, MUTED)
        text(group, x + w - 20, yy, f"★ {stars}   forks {forks}", 12, GOLD, anchor="end")
        text(group, x + w - 20, yy + 19, lang, 11, BLUE, anchor="end")
        if i < 3:
            line(group, x + 20, yy + 29, x + w - 20, yy + 29, "#174b30", 1)
    if not repos:
        text(group, x + 24, y + 100, "No public repositories returned by GitHub API", 14, MUTED)


def draw_programming(group, user, repos):
    clear_group(group, "url(#win3)")
    # Two balanced, native-vector cards. Text is deliberately large and crisp.
    lx, ly, lw, lh = 55, 710, 365, 270
    rx, ry, rw, rh = 430, 710, 355, 270
    rect(group, lx, ly, lw, lh, fill=BG, stroke=GREEN, radius=13)
    rect(group, rx, ry, rw, rh, fill=BG, stroke=GREEN, radius=13)

    text(group, lx + 20, ly + 31, "GITHUB OVERVIEW", 17, GREEN, "bold")
    line(group, lx + 18, ly + 43, lx + lw - 18, ly + 43)
    metrics = [
        ("PUBLIC REPOS", fmt_num(user.get("public_repos")), lx + 22, ly + 91, GREEN),
        ("FOLLOWERS", fmt_num(user.get("followers")), lx + 195, ly + 91, BLUE),
        ("FOLLOWING", fmt_num(user.get("following")), lx + 22, ly + 183, GOLD),
        ("PUBLIC GISTS", fmt_num(user.get("public_gists")), lx + 195, ly + 183, GREEN),
    ]
    for label, value, xx, yy, color in metrics:
        text(group, xx, yy, value, 30, color, "bold")
        text(group, xx, yy + 23, label, 11, MUTED, "bold")

    text(group, rx + 20, ry + 31, "LANGUAGE MATRIX", 17, GREEN, "bold")
    line(group, rx + 18, ry + 43, rx + rw - 18, ry + 43)
    counts = Counter((r.get("language") or "Other") for r in repos)
    top = counts.most_common(5)
    total = sum(counts.values()) or 1
    if not top:
        text(group, rx + 20, ry + 85, "No language data", 14, MUTED)
    else:
        colors = [GREEN, BLUE, GOLD, "#d49bff", "#ff8b8b"]
        for i, (lang, count) in enumerate(top):
            yy = ry + 78 + i * 36
            pct = count / total
            text(group, rx + 20, yy, clean_text(lang, 17), 13, TEXT, "bold")
            text(group, rx + rw - 20, yy, f"{count} repos  ·  {pct:.0%}", 11, MUTED, anchor="end")
            rect(group, rx + 20, yy + 9, rw - 40, 8, fill="#102f20", stroke="#102f20", radius=4)
            rect(group, rx + 20, yy + 9, max(5, (rw - 40) * pct), 8, fill=colors[i], stroke=colors[i], radius=4)
    text(group, rx + 20, ry + rh - 15, "Primary language per public repository", 10, MUTED)


def draw_activity(group, user, repos, events):
    clear_group(group, "url(#win4)")
    x, y, w = 850, 710, 690
    rect(group, x, y, w, 285, fill=BG, stroke=GOLD, radius=13)
    text(group, x + 20, y + 31, "GITHUB ACTIVITY / PUBLIC DATA", 17, GOLD, "bold")
    line(group, x + 18, y + 43, x + w - 18, y + 43)

    total_stars = sum(int(r.get("stargazers_count") or 0) for r in repos) if repos else None
    total_forks = sum(int(r.get("forks_count") or 0) for r in repos) if repos else None
    push_events = [e for e in events if e.get("type") == "PushEvent"]
    last_push = None
    if push_events:
        last_push = max((e.get("created_at", "") for e in push_events), default=None)
    tiles = [
        ("STARS RECEIVED", fmt_num(total_stars), GOLD),
        ("TOTAL FORKS", fmt_num(total_forks), BLUE),
        ("PUBLIC PUSH EVENTS", fmt_num(len(push_events)) if events else "—", GREEN),
        ("LAST PUBLIC PUSH", short_date(last_push), TEXT),
    ]
    tile_w = 155
    for i, (label, value, color) in enumerate(tiles):
        tx = x + 18 + i * 166
        rect(group, tx, y + 58, tile_w, 77, fill=CARD, stroke="#205b3a", radius=9)
        text(group, tx + 12, y + 89, value, 22, color, "bold")
        text(group, tx + 12, y + 116, label, 9, MUTED, "bold")

    text(group, x + 22, y + 166, "ACCOUNT CREATED", 10, MUTED, "bold")
    created = short_date(user.get("created_at"))
    text(group, x + 22, y + 193, created, 19, TEXT, "bold")
    text(group, x + 235, y + 166, "PUBLIC REPOSITORIES ANALYZED", 10, MUTED, "bold")
    text(group, x + 235, y + 193, fmt_num(len(repos)) if repos else "—", 19, TEXT, "bold")
    text(group, x + 22, y + 237,
         "Push events are recent public activity, not a complete contribution/streak count.",
         10, MUTED)


def main():
    if not SVG_PATH.is_file():
        raise FileNotFoundError(f"SVG not found: {SVG_PATH}")

    # Fetch everything before modifying the SVG: on failure, keep the previous file intact.
    user, repos, events = fetch_profile_data()
    if user.get("login", "").lower() != USERNAME.lower():
        raise RuntimeError("GitHub API returned an unexpected user")

    repos.sort(key=lambda r: r.get("pushed_at") or r.get("updated_at") or "", reverse=True)

    tree = ET.parse(SVG_PATH)
    root = tree.getroot()
    nested = next((e for e in root.iter(S + "svg") if e is not root and e.get("viewBox") == "40 262 1520 760"), None)
    if nested is None:
        raise RuntimeError("Expected nested SVG viewBox '40 262 1520 760' not found")

    groups = {}
    for element in nested:
        if element.tag == S + "g" and element.get("clip-path", "").startswith("url(#win"):
            groups[element.get("clip-path")] = element
    for key in ("url(#win2)", "url(#win3)", "url(#win4)"):
        if key not in groups:
            raise RuntimeError(f"Missing SVG panel group: {key}")

    make_panels_opaque(nested)
    draw_repo_explorer(groups["url(#win2)"], repos)
    draw_programming(groups["url(#win3)"], user, repos)
    draw_activity(groups["url(#win4)"], user, repos, events)

    # Preserve a small metadata note in the SVG for auditability.
    metadata = root.find(S + "metadata")
    if metadata is None:
        metadata = ET.SubElement(root, S + "metadata")
    metadata.text = (
        f"Generated from public GitHub REST API data for {USERNAME}; "
        f"updated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}; no token used."
    )

    tmp = SVG_PATH.with_suffix(".tmp.svg")
    try:
        tree.write(tmp, encoding="utf-8", xml_declaration=True)
        ET.parse(tmp)
        if tmp.stat().st_size < 1000:
            raise RuntimeError("Generated SVG unexpectedly small")
        os.replace(tmp, SVG_PATH)
    finally:
        if tmp.exists():
            tmp.unlink()

    log(f"Updated native SVG from public GitHub data: {len(repos)} repositories, {len(events)} public events")
    log(f"Output: {SVG_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
