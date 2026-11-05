import json
import sys
import tempfile
import threading
import unittest
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402
import generate_profile as gp  # noqa: E402
import github_data as gd  # noqa: E402
import svg_renderer as sr  # noqa: E402

FIXTURE_REPOS = [
    {"name": "BasicForge", "full_name": "iliyahaddad/BasicForge", "description": "Compiler <b>&\"x\"</b>",
     "stargazers_count": 3, "forks_count": 1, "pushed_at": "2026-10-25T10:00:00Z", "language": "C",
     "html_url": "https://github.com/iliyahaddad/BasicForge", "fork": False, "archived": False},
    {"name": "tools", "full_name": "iliyahaddad/tools", "description": None, "stargazers_count": 0,
     "forks_count": 0, "pushed_at": "2026-09-01T00:00:00Z", "language": "Python",
     "html_url": "https://github.com/iliyahaddad/tools", "fork": False, "archived": False},
]
CAL = {"data": {"user": {"contributionsCollection": {"contributionCalendar": {
    "totalContributions": 12, "weeks": [{"contributionDays": [
        {"date": "2026-10-01", "contributionCount": c} for c in (0, 1, 2, 0, 5, 0, 4)]}] * 53}}}}}
EVENTS = [{"type": "PushEvent", "repo": {"name": "iliyahaddad/BasicForge"}, "created_at": "2026-10-25T10:00:00Z",
           "payload": {"size": 2}}, {"type": "WatchEvent", "repo": {"name": "x/y"}, "payload": {}}]


class Mock(BaseHTTPRequestHandler):
    fail_first = {"count": 0}
    contrib_ok = True

    def log_message(self, *a):
        pass

    def _send(self, code, obj, headers=()):
        body = json.dumps(obj).encode()
        self.send_response(code)
        for k, v in headers:
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = self.path
        if p.startswith("/users/iliyahaddad/repos"):
            if Mock.fail_first["count"] < 2:
                Mock.fail_first["count"] += 1
                return self._send(502, {})
            return self._send(200, FIXTURE_REPOS)
        if p == "/users/iliyahaddad":
            return self._send(200, {"public_repos": 2, "followers": 4, "following": 1})
        if p.endswith("/languages"):
            return self._send(200, {"C": 800, "Python": 200})
        if "/events/public" in p:
            return self._send(200, EVENTS)
        self._send(404, {})

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if Mock.contrib_ok:
            return self._send(200, CAL)
        self._send(403, {}, [("X-RateLimit-Remaining", "5")])


class ServerCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), Mock)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        Mock.fail_first["count"] = 0
        Mock.contrib_ok = True

    def client(self):
        return gd.GitHubClient(None, self.base, sleep=lambda s: None)


class TestData(ServerCase):
    def test_collect_retries_and_aggregates(self):
        d = gd.collect(self.client())
        self.assertEqual(Mock.fail_first["count"], 2)  # two 502s were retried
        self.assertEqual((d["public_repos"], d["followers"], d["stars"]), (2, 4, 3))
        self.assertEqual(d["languages"], {"C": 1600, "Python": 400})
        self.assertEqual(len(d["events"]), 1)  # WatchEvent ignored
        self.assertEqual(d["contributions"]["total"], 12)

    def test_contributions_omitted_when_unavailable(self):
        Mock.contrib_ok = False
        self.assertIsNone(gd.collect(self.client())["contributions"])

    def test_hard_failure_raises(self):
        with self.assertRaises(gd.GitHubError):
            self.client().get("/nope")

    def test_pagination_does_not_truncate_at_five_pages(self):
        class ManyPages:
            def __init__(self):
                self.pages = []
            def get(self, path):
                page = int(path.rsplit("page=", 1)[1])
                self.pages.append(page)
                if page <= 6:
                    return [{"id": page * 100 + i} for i in range(100)]
                return [{"id": 700}]
        client = ManyPages()
        result = gd._paginate(client, "/repos")
        self.assertEqual(len(result), 601)
        self.assertEqual(client.pages, list(range(1, 8)))


class TestRender(ServerCase):
    def setUp(self):
        super().setUp()
        self.data = gd.collect(self.client())

    def test_valid_and_safe(self):
        for animate in (True, False):
            svg = sr.render(self.data, "t", animate=animate)
            gp.validate(svg)
            self.assertNotIn("<b>", svg)  # hostile description escaped
            self.assertIn("&lt;b&gt;", svg)
        self.assertNotIn("@keyframes", sr.render(self.data, "t", animate=False))

    def test_missing_featured_repo_is_not_invented(self):
        svg = sr.render(self.data, "t")
        self.assertIn("no public repository found", svg)  # NexaPack / vTPM2 absent
        self.assertIn("github.com/iliyahaddad/BasicForge", svg)

    def test_no_contrib_layout_valid(self):
        self.data["contributions"] = None
        gp.validate(sr.render(self.data, "t"))

    def test_deterministic(self):
        a = sr.render(self.data, "t")
        self.assertEqual(a, sr.render(self.data, "t"))

    def test_pending_has_no_numbers(self):
        svg = sr.render(None, "t", banner="AWAITING FIRST LIVE SYNC")
        gp.validate(svg)
        self.assertIn(">--<", svg)


class TestClean(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(sr.clean("a\x00b\u202e<&>\"", None), "ab&lt;&amp;&gt;&quot;")
        self.assertTrue(sr.clean("x" * 50, 10).endswith("\u2026"))

    def test_validator_rejects(self):
        base = sr.render(None, "t")
        for bad in ("<script>1</script>", '<image href="x"/>', '<a xlink:href="x"/>', "http://evil.example/"):
            with self.assertRaises((ValueError, ET.ParseError)):
                gp.validate(base.replace("</svg>", bad + "</svg>"))


class TestGenerator(ServerCase):
    def test_write_only_when_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.assertEqual(gp.main(["--out-dir", str(out), "--pending"]), 0)
            f = out / config.ASSET_ANIMATED
            first = f.read_text()
            mtime = f.stat().st_mtime_ns
            self.assertEqual(gp.main(["--out-dir", str(out), "--pending"]), 0)
            self.assertEqual(mtime, f.stat().st_mtime_ns)  # timestamp-only difference -> no write
            ET.parse(f)
            self.assertEqual(first, f.read_text())

    def test_failure_keeps_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            gp.main(["--out-dir", str(out), "--pending"])
            before = (out / config.ASSET_ANIMATED).read_text()
            orig = gd.config.API_URL
            gd.config.API_URL = "http://127.0.0.1:1"  # refused connection
            gd.config.HTTP_RETRIES, retries = 1, gd.config.HTTP_RETRIES
            try:
                gd.time.sleep = lambda s: None
                self.assertEqual(gp.main(["--out-dir", str(out)]), 1)
            finally:
                gd.config.API_URL, gd.config.HTTP_RETRIES = orig, retries
            self.assertEqual(before, (out / config.ASSET_ANIMATED).read_text())


class TestRepoFiles(unittest.TestCase):
    def test_readme_and_workflow(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn("iliyahaddad/iliyahaddad/main/assets/farboud-matrix.svg", readme)
        self.assertTrue((ROOT / config.ASSET_ANIMATED).exists())
        self.assertTrue((ROOT / config.ASSET_STATIC).exists())
        import yaml
        wf = yaml.safe_load((ROOT / ".github/workflows/update-profile.yml").read_text())
        on = wf.get("on", wf.get(True))
        self.assertIn("schedule", on)
        self.assertIn("workflow_dispatch", on)
        self.assertEqual(wf["permissions"], {"contents": "write"})


if __name__ == "__main__":
    unittest.main()
