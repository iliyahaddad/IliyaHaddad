#!/usr/bin/env python3
"""Refresh the GitHub panels in matrix-github-profile.svg.

Readable profile updater:
- Keeps the desktop-window panels opaque.
- Uses dark, high-contrast GitHub cards.
- Uses large Shields.io badges instead of tiny social badges.
- Upscales downloaded PNGs with high-quality resampling and mild sharpening.
"""

import base64
import io
import os
import sys
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path

import cairosvg
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SVG = ROOT / "matrix-github-profile.svg"
USER = "iliyahaddad"
TIMEOUT = 45
MAX_RETRIES = 3

# Keep all cards on a dark opaque surface so Matrix rain cannot reduce contrast.
BG = "061a10"
GREEN = "39ff88"
TEXT = "e8fff1"
MUTED = "a7cdb5"

URLS = {
    "gitshine": f"https://gitshine.com/badges/{USER}",
    "stats": (
        f"https://github-readme-stats.vercel.app/api"
        f"?username={USER}&show_icons=true&include_all_commits=true"
        f"&rank_icon=github&hide_border=true&card_width=440"
        f"&bg_color={BG}&title_color={GREEN}&text_color={TEXT}"
        f"&icon_color=7dffb0"
    ),
    "langs": (
        f"https://github-readme-stats.vercel.app/api/top-langs/"
        f"?username={USER}&layout=compact&langs_count=6"
        f"&hide_border=true&card_width=440"
        f"&bg_color={BG}&title_color={GREEN}&text_color={TEXT}"
    ),
    "stars": (
        f"https://img.shields.io/github/stars/{USER}"
        f"?label=GitHub%20Stars&style=for-the-badge"
        f"&color=2ea043&labelColor=10251a"
    ),
    "followers": (
        f"https://img.shields.io/github/followers/{USER}"
        f"?label=Followers&style=for-the-badge"
        f"&color=238636&labelColor=10251a"
    ),
    "views": (
        f"https://komarev.com/ghpvc/?username={USER}"
        f"&label=Profile%20Views&color=0969da&style=for-the-badge"
    ),
    "streak": (
        "https://github-readme-streak-stats.herokuapp.com/"
        f"?user={USER}&hide_border=true&background={BG}"
        f"&border={BG}&stroke=245c3b&ring={GREEN}"
        f"&fire=ffb02e&currStreakLabel={TEXT}"
        f"&sideLabels={MUTED}&dates={MUTED}&currStreakNum={TEXT}"
        f"&sideNums={TEXT}"
    ),
}

SVG_NS = "http://www.w3.org/2000/svg"
S = f"{{{SVG_NS}}}"
ET.register_namespace("", SVG_NS)


def log(message):
    print(f"[INFO] {message}", flush=True)


def warn(message):
    print(f"[WARNING] {message}", flush=True)


def error(message):
    print(f"[ERROR] {message}", flush=True)


def upscale_png(data, scale=3):
    """Improve display-size interpolation; this cannot invent missing source detail."""
    image = Image.open(io.BytesIO(data)).convert("RGBA")
    image = image.resize(
        (image.width * scale, image.height * scale),
        Image.Resampling.LANCZOS,
    )
    image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=125, threshold=3))
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def fetch_png(key, url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 GitHub-Profile-Updater",
            "Accept": "image/png,image/svg+xml,*/*",
        },
    )
    retryable = {429, 500, 502, 503, 504}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log(f"Downloading {key}: attempt {attempt}/{MAX_RETRIES}")
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                data = response.read()

            if not data:
                raise ValueError("Empty response")

            if data.startswith(b"\x89PNG\r\n\x1a\n"):
                png = data
            else:
                parsed = ET.fromstring(data)
                if not parsed.tag.endswith("svg"):
                    raise ValueError(f"Unexpected response format: {parsed.tag}")
                png = cairosvg.svg2png(bytestring=data)

            if not png.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("Invalid PNG conversion")

            log(f"{key}: downloaded and converted successfully")
            return upscale_png(png)

        except urllib.error.HTTPError as exc:
            if exc.code not in retryable:
                error(f"{key}: HTTP {exc.code} - {url}")
                return None
            warn(f"{key}: HTTP {exc.code}, retrying ({attempt}/{MAX_RETRIES})")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            warn(f"{key}: Network error: {exc}")
        except Exception as exc:
            error(f"{key}: {type(exc).__name__}: {exc}")
            return None

        if attempt < MAX_RETRIES:
            delay = 2 ** attempt
            log(f"Waiting {delay} seconds...")
            time.sleep(delay)

    error(f"{key}: all retry attempts failed")
    return None


def find_nested_svg(root):
    for element in root.iter(S + "svg"):
        if element is not root and element.get("viewBox") == "40 262 1520 760":
            return element
    raise RuntimeError("Could not find nested SVG with viewBox '40 262 1520 760'")


def find_groups(nested):
    groups = {}
    for element in nested:
        if element.tag == S + "g" and element.get("clip-path", "").startswith("url(#win"):
            groups[element.get("clip-path")] = element

    for key in ("url(#win2)", "url(#win3)", "url(#win4)"):
        if key not in groups:
            raise RuntimeError(f"Missing SVG group: {key}")
    return groups


def make_panels_opaque(nested):
    """Update the existing panel plates, not the Matrix background."""
    panel_strokes = {"#39ff88", "#19e6ff", "#b8ff3d", "#ffb02e"}
    for element in nested:
        if (
            element.tag == S + "rect"
            and element.get("stroke") in panel_strokes
            and element.get("fill") == "#02100a"
        ):
            element.set("fill-opacity", "0.97")
            if element.get("stroke") == "#b8ff3d":
                element.set("fill", "#061a10")
            elif element.get("stroke") == "#ffb02e":
                element.set("fill", "#071710")


def add_image(parent, key, x, y, width, height, assets):
    data = assets[key]
    ET.SubElement(
        parent,
        S + "image",
        {
            "x": str(x),
            "y": str(y),
            "width": str(width),
            "height": str(height),
            "preserveAspectRatio": "xMidYMid meet",
            "href": "data:image/png;base64," + base64.b64encode(data).decode("ascii"),
        },
    )


def replace_group(group, clip, images, assets):
    group.clear()
    group.set("clip-path", clip)
    for key, x, y, width, height in images:
        add_image(group, key, x, y, width, height, assets)


def main():
    if not SVG.is_file():
        raise FileNotFoundError(f"SVG file not found: {SVG}")

    log(f"Loading {SVG}")
    tree = ET.parse(SVG)
    root = tree.getroot()
    nested = find_nested_svg(root)
    groups = find_groups(nested)

    # Make the programming and activity windows readable even if an asset is offline.
    make_panels_opaque(nested)

    assets = {}
    for key, url in URLS.items():
        result = fetch_png(key, url)
        if result is not None:
            assets[key] = result

    log(f"Downloaded {len(assets)}/{len(URLS)} assets")
    updated = []

    if "gitshine" in assets:
        replace_group(
            groups["url(#win2)"], "url(#win2)",
            [("gitshine", 880, 315, 630, 285)], assets,
        )
        updated.append("Explorer")
    else:
        warn("Explorer panel preserved (GitShine unavailable)")

    if all(key in assets for key in ("stats", "langs")):
        replace_group(
            groups["url(#win3)"], "url(#win3)",
            [
                ("stats", 55, 710, 365, 270),
                ("langs", 430, 710, 355, 270),
            ],
            assets,
        )
        updated.append("Programming")
    else:
        warn("Programming panel content preserved (stats/langs unavailable)")

    activity_keys = ("stars", "followers", "views", "streak")
    if all(key in assets for key in activity_keys):
        replace_group(
            groups["url(#win4)"], "url(#win4)",
            [
                ("stars", 850, 710, 225, 66),
                ("followers", 1088, 710, 225, 66),
                ("views", 1325, 710, 225, 66),
                ("streak", 850, 780, 690, 230),
            ],
            assets,
        )
        updated.append("Activity")
    else:
        warn("Activity panel content preserved (one or more assets unavailable)")

    temp_svg = SVG.with_name(SVG.stem + ".tmp.svg")
    try:
        tree.write(temp_svg, encoding="utf-8", xml_declaration=True)
        ET.parse(temp_svg)
        if temp_svg.stat().st_size == 0:
            raise RuntimeError("Generated SVG is empty")
        os.replace(temp_svg, SVG)
    finally:
        if temp_svg.exists():
            temp_svg.unlink()

    log("Panel backgrounds updated. Refreshed: " + (", ".join(updated) or "none"))
    log(f"Output: {SVG}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        error(f"Fatal error: {type(exc).__name__}: {exc}")
        sys.exit(1)
