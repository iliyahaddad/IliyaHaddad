
#!/usr/bin/env python3
"""Reliable GitHub profile SVG updater with retries and panel fallback."""

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


# --------------------------------------------------
# Configuration
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
SVG = ROOT / "matrix-github-profile.svg"

USER = "iliyahaddad"

TIMEOUT = 45
MAX_RETRIES = 3

URLS = {
    "gitshine": f"https://gitshine.com/badges/{USER}",

    "stats": (
        f"https://github-readme-stats.vercel.app/api"
        f"?username={USER}&show_icons=true"
        f"&hide_border=true&rank_icon=github"
    ),

    "langs": (
        f"https://github-readme-stats.vercel.app/api/top-langs/"
        f"?username={USER}&layout=compact&hide_border=true"
    ),

    "stars": (
        f"https://img.shields.io/github/stars/{USER}"
        f"?label=Stars&style=social"
    ),

    "followers": (
        f"https://img.shields.io/github/followers/{USER}"
        f"?label=Followers&style=social"
    ),

    "views": (
        f"https://komarev.com/ghpvc/?username={USER}"
    ),

    "streak": (
        f"https://github-readme-streak-stats.herokuapp.com/"
        f"?user={USER}&theme=meta-light"
    ),
}

SVG_NS = "http://www.w3.org/2000/svg"
S = f"{{{SVG_NS}}}"

ET.register_namespace("", SVG_NS)


# --------------------------------------------------
# Logging
# --------------------------------------------------

def log(message):
    print(f"[INFO] {message}", flush=True)


def warn(message):
    print(f"[WARNING] {message}", flush=True)


def error(message):
    print(f"[ERROR] {message}", flush=True)


# --------------------------------------------------
# HTTP downloader
# --------------------------------------------------

def fetch_png(key, url):

    req = urllib.request.Request(
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

            with urllib.request.urlopen(
                req,
                timeout=TIMEOUT
            ) as response:

                data = response.read()

            if not data:
                raise ValueError("Empty response")

            # Already PNG
            if data.startswith(b"\x89PNG\r\n\x1a\n"):

                log(f"{key}: PNG downloaded successfully")
                return data

            # Validate SVG response
            try:
                parsed = ET.fromstring(data)
            except ET.ParseError as exc:
                raise ValueError(
                    f"Response is neither valid PNG nor SVG: {exc}"
                ) from exc

            if not parsed.tag.endswith("svg"):
                raise ValueError(
                    f"Unexpected response format: {parsed.tag}"
                )

            # Convert SVG to PNG
            png = cairosvg.svg2png(
                bytestring=data
            )

            if not png.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("Invalid PNG conversion")

            log(f"{key}: SVG converted to PNG successfully")

            return png

        except urllib.error.HTTPError as exc:

            if exc.code not in retryable:
                error(f"{key}: HTTP {exc.code} - {url}")
                return None

            warn(
                f"{key}: HTTP {exc.code}, "
                f"retrying ({attempt}/{MAX_RETRIES})"
            )

        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
        ) as exc:

            warn(
                f"{key}: Network error: {exc}"
            )

        except Exception as exc:

            error(
                f"{key}: {type(exc).__name__}: {exc}"
            )

            return None

        if attempt < MAX_RETRIES:
            delay = 2 ** attempt
            log(f"Waiting {delay} seconds...")
            time.sleep(delay)

    error(f"{key}: All retry attempts failed.")

    return None


# --------------------------------------------------
# SVG helpers
# --------------------------------------------------

def find_nested_svg(root):

    for element in root.iter(S + "svg"):

        if (
            element is not root
            and element.get("viewBox") == "40 262 1520 760"
        ):
            return element

    raise RuntimeError(
        "Could not find expected nested SVG with viewBox "
        "'40 262 1520 760'"
    )


def find_groups(nested):

    groups = {}

    for element in nested:

        if (
            element.tag == S + "g"
            and element.get("clip-path", "").startswith("url(#win")
        ):
            groups[element.get("clip-path")] = element

    required = [
        "url(#win2)",
        "url(#win3)",
        "url(#win4)",
    ]

    for key in required:

        if key not in groups:
            raise RuntimeError(
                f"Missing SVG group: {key}"
            )

    return groups


def img(parent, key, x, y, w, h, assets):

    data = assets[key]

    ET.SubElement(
        parent,
        S + "image",
        {
            "x": str(x),
            "y": str(y),
            "width": str(w),
            "height": str(h),
            "preserveAspectRatio": "xMidYMid meet",
            "href": (
                "data:image/png;base64,"
                + base64.b64encode(data).decode("ascii")
            ),
        },
    )


def replace_group(group, clip, images, assets):

    group.clear()
    group.set("clip-path", clip)

    for key, x, y, w, h in images:

        img(group, key, x, y, w, h, assets)


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    if not SVG.is_file():
        raise FileNotFoundError(
            f"SVG file not found: {SVG}"
        )

    log(f"Loading {SVG}")

    tree = ET.parse(SVG)
    root = tree.getroot()

    nested = find_nested_svg(root)
    groups = find_groups(nested)

    # Download assets independently.
    assets = {}

    for key, url in URLS.items():

        result = fetch_png(key, url)

        if result is not None:
            assets[key] = result

    log(
        f"Downloaded {len(assets)}/{len(URLS)} assets."
    )

    # Update only complete panels.
    updated = []

    # Explorer panel
    if "gitshine" in assets:

        replace_group(
            groups["url(#win2)"],
            "url(#win2)",
            [
                ("gitshine", 880, 315, 630, 285),
            ],
            assets,
        )

        updated.append("Explorer")

    else:
        warn("Explorer panel preserved (GitShine unavailable).")

    # Programming panel
    if all(k in assets for k in ("stats", "langs")):

        replace_group(
            groups["url(#win3)"],
            "url(#win3)",
            [
                ("stats", 55, 715, 365, 260),
                ("langs", 430, 715, 355, 260),
            ],
            assets,
        )

        updated.append("Programming")

    else:
        warn("Programming panel preserved (incomplete assets).")

    # Activity panel
    activity_keys = (
        "stars",
        "followers",
        "views",
        "streak",
    )

    if all(k in assets for k in activity_keys):

        replace_group(
            groups["url(#win4)"],
            "url(#win4)",
            [
                ("stars", 865, 715, 205, 55),
                ("followers", 1080, 715, 225, 55),
                ("views", 1320, 715, 200, 55),
                ("streak", 860, 785, 675, 210),
            ],
            assets,
        )

        updated.append("Activity")

    else:
        warn("Activity panel preserved (incomplete assets).")

    if not updated:

        warn(
            "No complete panels could be refreshed. "
            "Original SVG was preserved."
        )

        return 0

    # Write to temporary file first.
    temp_svg = SVG.with_name(
        SVG.stem + ".tmp.svg"
    )

    try:

        tree.write(
            temp_svg,
            encoding="utf-8",
            xml_declaration=True,
        )

        # Validate generated SVG.
        ET.parse(temp_svg)

        if temp_svg.stat().st_size == 0:
            raise RuntimeError("Generated SVG is empty")

        # Replace original only after validation.
        os.replace(temp_svg, SVG)

    finally:

        if temp_svg.exists():
            temp_svg.unlink()

    log("Successfully refreshed: " + ", ".join(updated))
    log(f"Output: {SVG}")

    return 0


if __name__ == "__main__":

    try:
        sys.exit(main())

    except Exception as exc:

        error(f"Fatal error: {type(exc).__name__}: {exc}")
        sys.exit(1)
