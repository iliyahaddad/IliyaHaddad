#!/usr/bin/env python3
"""Generate static repository cards and inject them into index.html."""

import html
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

USERNAME = "iliyahaddad"
API_URL = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=updated"
INDEX_PATH = "index.html"
SITEMAP_PATH = "sitemap.xml"
START_MARKER = "<!-- REPOSITORIES_START -->"
END_MARKER = "<!-- REPOSITORIES_END -->"

def fetch_repositories():
    repos = []
    page = 1
    while True:
        url = f"{API_URL}&page={page}"
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "iliyahaddad-portfolio-generator",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status != 200:
                    raise RuntimeError(f"GitHub API returned HTTP {response.status}")
                data = json.load(response)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"GitHub API HTTP error: {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"GitHub API connection error: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("GitHub API returned invalid JSON") from exc

        if not isinstance(data, list):
            raise RuntimeError("Unexpected GitHub API response format")

        repos.extend(data)
        if len(data) < 100:
            break
        page += 1

    repos = [repo for repo in repos if not repo.get("fork", False)]
    repos.sort(key=lambda repo: repo.get("updated_at", ""), reverse=True)
    return repos

def escape_attr(value):
    return html.escape(value or "", quote=True).replace("\n", " ").replace("\r", " ")

def render_card(repo):
    name = html.escape(repo.get("name") or "", quote=True)
    description_text = (
        repo.get("description")
        or "Open-source software project and development repository."
    )
    description_html = html.escape(description_text, quote=True)
    url = html.escape(repo.get("html_url") or "", quote=True)
    language = repo.get("language") or ""
    stars = int(repo.get("stargazers_count", 0))
    updated_at = repo.get("updated_at") or ""
    archived = bool(repo.get("archived", False))
    topics = repo.get("topics") or []

    try:
        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        updated_display = dt.strftime("%d/%m/%Y")
    except Exception:
        updated_display = html.escape(updated_at)

    topics_html = "".join(
        f'<span class="topic">{html.escape(str(topic))}</span>'
        for topic in topics[:8]
    )

    meta_parts = []
    if language:
        meta_parts.append(f"<span>💻 {html.escape(language)}</span>")
    meta_parts.append(f"<span>⭐ {stars}</span>")
    meta_parts.append(f"<span>Updated {html.escape(updated_display)}</span>")
    if archived:
        meta_parts.append('<span class="archived">Archived</span>')

    return (
        f'<article class="project" '
        f'data-name="{escape_attr(repo.get("name"))}" '
        f'data-description="{escape_attr(repo.get("description"))}" '
        f'data-language="{escape_attr(language)}" '
        f'data-topics="{escape_attr(" ".join(topics))}">'
        f'<h2><a href="{url}" target="_blank" rel="noopener noreferrer">{name}</a></h2>'
        f'<p class="description">{description_html}</p>'
        f'<div class="meta">{"".join(meta_parts)}</div>'
        f'<div class="topics">{topics_html}</div>'
        f"</article>"
    )

def inject_into_index(repo_count, cards_html):
    with open(INDEX_PATH, "r", encoding="utf-8") as handle:
        content = handle.read()

    if START_MARKER not in content or END_MARKER not in content:
        raise RuntimeError("Repository insertion markers were not found in index.html")

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )
    replacement = f"{START_MARKER}\n{cards_html}\n{END_MARKER}"
    content = pattern.sub(replacement, content, count=1)

    content = re.sub(
        r'(<div id="stats"[^>]*>).*?(</div>)',
        rf"\g<1>{repo_count} projects\g<2>",
        content,
        count=1,
        flags=re.DOTALL,
    )

    with open(INDEX_PATH, "w", encoding="utf-8") as handle:
        handle.write(content)

    print(f"Injected {repo_count} repositories into {INDEX_PATH}")

def update_sitemap():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://iliyahaddad.github.io/IliyaHaddad/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
"""
    with open(SITEMAP_PATH, "w", encoding="utf-8") as handle:
        handle.write(sitemap)
    print(f"Updated {SITEMAP_PATH} with lastmod {today}")

def main():
    try:
        repos = fetch_repositories()
        if not repos:
            raise RuntimeError("No non-fork repositories were returned by the GitHub API")
        cards_html = "\n".join(render_card(repo) for repo in repos)
        inject_into_index(len(repos), cards_html)
        update_sitemap()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
