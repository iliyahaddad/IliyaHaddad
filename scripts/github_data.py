"""GitHub data collection. Only genuine API data is returned; failures raise."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Callable

import config


class GitHubError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, token: str | None = None, base: str | None = None,
                 sleep: Callable[[float], None] = time.sleep):
        self.token = token
        self.base = (base or config.API_URL).rstrip("/")
        self.sleep = sleep

    def _request(self, method: str, url: str, body: bytes | None = None) -> Any:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{config.USERNAME}-profile-generator",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if body is not None:
            headers["Content-Type"] = "application/json"
        last: Exception | None = None
        for attempt in range(config.HTTP_RETRIES):
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=config.HTTP_TIMEOUT) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                last = exc
                if exc.code == 404:
                    raise GitHubError(f"404 Not Found: {url}") from exc
                limited = exc.code in (403, 429) and (
                    exc.headers.get("X-RateLimit-Remaining") == "0"
                    or exc.headers.get("Retry-After"))
                if exc.code >= 500 or limited:
                    wait = self._backoff(exc, attempt)
                    if wait is None:
                        raise GitHubError(f"rate limit reset too far away ({url})") from exc
                    self.sleep(wait)
                    continue
                raise GitHubError(f"HTTP {exc.code} for {url}") from exc
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last = exc
                self.sleep(min(2 ** attempt, 30))
        raise GitHubError(f"giving up after {config.HTTP_RETRIES} attempts: {url} ({last})")

    @staticmethod
    def _backoff(exc: urllib.error.HTTPError, attempt: int) -> float | None:
        retry_after = exc.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            return min(int(retry_after), 120)
        reset = exc.headers.get("X-RateLimit-Reset")
        if exc.headers.get("X-RateLimit-Remaining") == "0" and reset and reset.isdigit():
            delta = int(reset) - time.time()
            return None if delta > 120 else max(delta, 1)
        return min(2 ** attempt, 30)

    def get(self, path: str) -> Any:
        return self._request("GET", self.base + path)

    def graphql(self, query: str, variables: dict) -> Any:
        url = self.base + "/graphql"
        body = json.dumps({"query": query, "variables": variables}).encode()
        out = self._request("POST", url, body)
        if out.get("errors") or not out.get("data"):
            raise GitHubError(f"GraphQL error: {out.get('errors')}")
        return out["data"]


CONTRIB_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}"""


def fetch_contributions(client: GitHubClient, login: str) -> dict | None:
    """Return the real contribution calendar, or None if the API refuses it."""
    try:
        data = client.graphql(CONTRIB_QUERY, {"login": login})
        cal = data["user"]["contributionsCollection"]["contributionCalendar"]
        weeks = [[d["contributionCount"] for d in w["contributionDays"]] for w in cal["weeks"]]
        return {"total": cal["totalContributions"], "weeks": weeks}
    except (GitHubError, KeyError, TypeError):
        return None


def _paginate(client: GitHubClient, path: str) -> list:
    """Fetch every page (GitHub REST caps each page at 100 items).

    Do not silently stop at an arbitrary page count: totals for stars/forks
    must cover all public repositories. The short-page condition is GitHub's
    documented end-of-pagination signal.
    """
    items: list = []
    sep = "&" if "?" in path else "?"
    page = 1
    while True:
        chunk = client.get(f"{path}{sep}per_page=100&page={page}")
        if not isinstance(chunk, list):
            raise GitHubError(f"unexpected paginated response for {path}")
        items.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return items


def summarize_event(ev: dict) -> tuple[str, str] | None:
    """Map a public event to (kind, text). Unsupported events return None."""
    repo = (ev.get("repo") or {}).get("name", "").split("/")[-1]
    p = ev.get("payload") or {}
    t = ev.get("type")
    if t == "PushEvent":
        n = p.get("size") or len(p.get("commits") or []) or 1
        return "PUSH", f"{n} commit{'s' if n != 1 else ''} to {repo}"
    if t == "CreateEvent" and p.get("ref_type") == "repository":
        return "CREATE", f"created repository {repo}"
    if t == "ReleaseEvent":
        tag = (p.get("release") or {}).get("tag_name", "")
        return "RELEASE", f"released {tag} in {repo}".replace("  ", " ")
    if t == "PullRequestEvent":
        return "PR", f"{p.get('action', 'updated')} pull request in {repo}"
    if t == "IssuesEvent":
        return "ISSUE", f"{p.get('action', 'updated')} issue in {repo}"
    return None


def collect(client: GitHubClient, login: str | None = None) -> dict:
    login = login or config.USERNAME
    user = client.get(f"/users/{login}")
    repos = _paginate(client, f"/users/{login}/repos?type=owner&sort=pushed")
    own = [r for r in repos if not r.get("fork")]

    languages: dict[str, int] = {}
    recent = sorted(own, key=lambda r: r.get("pushed_at") or "", reverse=True)
    for r in recent[:config.MAX_LANGUAGE_REPOS]:
        if r.get("archived"):
            continue
        for lang, n in client.get(f"/repos/{r['full_name']}/languages").items():
            languages[lang] = languages.get(lang, 0) + int(n)

    events = []
    for ev in client.get(f"/users/{login}/events/public?per_page=50"):
        s = summarize_event(ev)
        if s:
            events.append({"kind": s[0], "text": s[1], "date": (ev.get("created_at") or "")[:10]})
        if len(events) >= config.MAX_EVENTS:
            break

    return {
        "login": login,
        "public_repos": user.get("public_repos", len(repos)),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "stars": sum(r.get("stargazers_count", 0) for r in own),
        "forks": sum(r.get("forks_count", 0) for r in own),
        "repos": [{
            "name": r["name"], "description": r.get("description") or "",
            "stars": r.get("stargazers_count", 0), "forks": r.get("forks_count", 0),
            "updated": (r.get("pushed_at") or r.get("updated_at") or "")[:10],
            "language": r.get("language") or "", "url": r.get("html_url", ""),
            "archived": bool(r.get("archived")), "fork": bool(r.get("fork")),
        } for r in repos],
        "languages": languages,
        "events": events,
        "contributions": fetch_contributions(client, login),
    }


def token_from_env() -> str | None:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or None
