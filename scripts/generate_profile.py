#!/usr/bin/env python3
"""Generate assets/farboud-matrix.svg and assets/farboud-static.svg.

Exit codes: 0 ok (written or unchanged), 1 API failure (nothing overwritten),
2 generated SVG failed validation (nothing overwritten).
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
import github_data  # noqa: E402
import svg_renderer  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
_TS = re.compile(r'(<text[^>]*id="generated"[^>]*>).*?(</text>)', re.S)
_FORBIDDEN = re.compile(r"<script|<iframe|<foreignObject|<image|<use|javascript:|\son\w+\s*=|xlink:href|href=", re.I)


def validate(svg: str) -> None:
    root = ET.fromstring(svg)  # raises on invalid XML
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise ValueError("root element is not <svg>")
    if root.get("viewBox") != f"0 0 {config.WIDTH} {config.HEIGHT}":
        raise ValueError("unexpected viewBox")
    if _FORBIDDEN.search(svg):
        raise ValueError("forbidden element or attribute present")
    if re.findall(r"https?://(?!www\.w3\.org/2000/svg)", svg):
        # URLs appear only as plain text without the scheme; any scheme is an external reference.
        raise ValueError("external URL present")


def _normalise(svg: str) -> str:
    return _TS.sub(r"\1\2", svg)


def write_if_changed(path: Path, svg: str) -> bool:
    if path.exists() and _normalise(path.read_text(encoding="utf-8")) == _normalise(svg):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=ROOT)
    ap.add_argument("--pending", action="store_true",
                    help="render the layout with no data (first-sync placeholder, no numbers)")
    ap.add_argument("--banner", help="optional footer banner text")
    args = ap.parse_args(argv)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if args.pending:
        data, banner = None, args.banner or "AWAITING FIRST LIVE SYNC"
    else:
        try:
            data = github_data.collect(github_data.GitHubClient(github_data.token_from_env()))
        except github_data.GitHubError as exc:
            print(f"error: GitHub data unavailable, keeping existing SVGs: {exc}", file=sys.stderr)
            return 1
        banner = args.banner

    outputs = {config.ASSET_ANIMATED: True, config.ASSET_STATIC: False}
    rendered = {}
    for rel, animate in outputs.items():
        svg = svg_renderer.render(data, now, animate=animate, banner=banner)
        try:
            validate(svg)
        except (ET.ParseError, ValueError) as exc:
            print(f"error: invalid SVG for {rel}: {exc}", file=sys.stderr)
            return 2
        rendered[rel] = svg
    for rel, svg in rendered.items():
        changed = write_if_changed(args.out_dir / rel, svg)
        print(f"{rel}: {'updated' if changed else 'unchanged'} ({len(svg)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
