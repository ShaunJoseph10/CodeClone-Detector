"""Backend API tests. Run from backend/:  .venv/bin/python -m unittest discover -s tests"""

import io
import json
import os
import tempfile
import unittest
import zipfile

_tmp = tempfile.mkdtemp()
os.environ["CODECLONE_DATABASE_URL"] = "sqlite:///%s/test.db" % _tmp
os.environ["CODECLONE_MAX_FILE_BYTES"] = "5000"
os.environ["CODECLONE_LOG_LEVEL"] = "WARNING"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

GCD = "def gcd(a, b):\n    while b != 0:\n        t = b\n        b = a % b\n        a = t\n    return a\nprint(gcd(4, 6))\n"
GCD_RENAMED = "def g(x, y):\n    while y != 0:\n        z = y\n        y = x % y\n        x = z\n    return x\nprint(g(4, 6))\n"
OTHER = "names = ['a', 'b']\nfor n in names:\n    print('hello', n)\n"


def make_zip(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, text in entries.items():
            z.writestr(name, text)
    return buf.getvalue()


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = TestClient(app)
        cls.client = cls.ctx.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.ctx.__exit__(None, None, None)

    def new_assignment(self, title="HW1"):
        r = self.client.post("/api/assignments", json={"title": title, "course": "DSA"})
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()["id"]

    def upload(self, aid, files):
        return self.client.post("/api/assignments/%d/submissions" % aid,
                                files=[("files", (name, data)) for name, data in files])

    def test_health(self):
        self.assertEqual(self.client.get("/api/health").json(), {"status": "ok"})

    def test_upload_py_files(self):
        aid = self.new_assignment()
        r = self.upload(aid, [("alice.py", GCD), ("bob.py", GCD_RENAMED), ("broken.py", "def (:\n"),
                              ("notes.txt", "hi")])
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        self.assertEqual([s["student_name"] for s in body["created"]], ["alice", "bob", "broken"])
        self.assertIsNone(body["created"][0]["parse_error"])
        self.assertIsNotNone(body["created"][2]["parse_error"])
        self.assertEqual(body["errors"][0]["filename"], "notes.txt")
        subs = self.client.get("/api/assignments/%d/submissions" % aid).json()
        self.assertEqual(len(subs), 3)
        self.assertNotIn("source", subs[0])
        one = self.client.get("/api/submissions/%d" % subs[0]["id"]).json()
        self.assertEqual(one["source"], GCD)
        self.assertEqual(one["lines"], 7)

    def test_upload_zip_student_from_folder(self):
        aid = self.new_assignment()
        data = make_zip({"carol/solution.py": GCD, "dave/solution.py": OTHER, "eve.py": GCD,
                         "__MACOSX/carol/._solution.py": "x", "readme.md": "x"})
        r = self.upload(aid, [("class.zip", data)])
        self.assertEqual(r.status_code, 201, r.text)
        names = sorted(s["student_name"] for s in r.json()["created"])
        self.assertEqual(names, ["carol", "dave", "eve"])
        self.assertEqual([e["filename"] for e in r.json()["errors"]], ["readme.md"])

    def test_zip_slip_rejected(self):
        aid = self.new_assignment()
        for evil in ("../evil.py", "/abs/evil.py", "a/../../evil.py"):
            r = self.upload(aid, [("x.zip", make_zip({"ok.py": GCD, evil: GCD}))])
            self.assertEqual(r.status_code, 400, evil)
            self.assertEqual(r.json()["error"]["code"], "bad_request")
        self.assertEqual(self.client.get("/api/assignments/%d/submissions" % aid).json(), [])

    def test_bad_input(self):
        aid = self.new_assignment()
        self.assertEqual(self.upload(aid, [("big.py", "x = 1\n" * 2000)]).json()["errors"][0]["filename"], "big.py")
        self.assertEqual(self.upload(aid, [("x.zip", b"not a zip")]).status_code, 400)
        self.assertEqual(self.upload(9999, [("a.py", GCD)]).status_code, 404)
        r = self.client.post("/api/assignments", json={"title": ""})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["error"]["code"], "invalid")
        r = self.client.post("/api/assignments/%d/analyses" % aid, json={"threshold": 2})
        self.assertEqual(r.status_code, 422)
        r = self.client.post("/api/assignments/%d/analyses" % aid, json={"weights": {"magic": 1}})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.client.get("/api/analyses/9999").json()["error"]["code"], "not_found")

    def test_analysis_lifecycle(self):
        aid = self.new_assignment("lifecycle")
        self.upload(aid, [("alice.py", GCD), ("bob.py", GCD_RENAMED), ("carl.py", OTHER), ("bad.py", "def (:\n")])
        r = self.client.post("/api/assignments/%d/analyses" % aid, json={"threshold": 0.6})
        self.assertEqual(r.status_code, 202)
        self.assertEqual(r.json()["status"], "queued")
        an = self.client.get("/api/analyses/%d" % r.json()["id"]).json()  # TestClient runs the task first
        self.assertEqual(an["status"], "done", an)
        self.assertEqual(an["summary"]["files"], 3)
        self.assertEqual(an["summary"]["flagged"], 1)
        self.assertEqual(an["summary"]["clusters"], 1)
        self.assertIsNotNone(an["duration_ms"])

        pairs = self.client.get("/api/analyses/%d/pairs" % an["id"]).json()
        top = pairs["items"][0]
        self.assertEqual({top["a"]["student_name"], top["b"]["student_name"]}, {"alice", "bob"})
        self.assertGreater(top["score"], 0.9)
        detail = self.client.get("/api/analyses/%d/pairs/%d" % (an["id"], top["id"])).json()
        self.assertEqual(detail["a"]["source"], GCD)
        self.assertTrue(detail["matches"])

        clusters = self.client.get("/api/analyses/%d/clusters" % an["id"]).json()
        self.assertEqual(sorted(m["student_name"] for m in clusters[0]["members"]), ["alice", "bob"])
        graph = self.client.get("/api/analyses/%d/graph" % an["id"]).json()
        self.assertEqual(len(graph["nodes"]), 3)
        self.assertEqual(len(graph["edges"]), 1)

        listing = self.client.get("/api/assignments/%d" % aid).json()
        self.assertEqual(listing["last_analysis"]["status"], "done")
        self.assertGreater(listing["last_analysis"]["max_score"], 0.9)

        self.assertEqual(self.client.delete("/api/assignments/%d" % aid).status_code, 204)
        self.assertEqual(self.client.get("/api/analyses/%d" % an["id"]).status_code, 404)

    def test_pagination_filter_sort_export(self):
        aid = self.new_assignment("paging")
        files = [("s%d.py" % i, GCD if i % 2 else GCD_RENAMED) for i in range(6)]  # 15 near-identical pairs
        self.upload(aid, files)
        an = self.client.post("/api/assignments/%d/analyses" % aid, json={}).json()
        base = "/api/analyses/%d/pairs" % an["id"]
        p1 = self.client.get(base, params={"page_size": 4}).json()
        p4 = self.client.get(base, params={"page_size": 4, "page": 4}).json()
        self.assertEqual(p1["total"], 15)
        self.assertEqual(len(p1["items"]), 4)
        self.assertEqual(len(p4["items"]), 3)
        self.assertEqual(self.client.get(base, params={"student": "S3"}).json()["total"], 5)
        self.assertEqual(self.client.get(base, params={"min_score": 1.01}).status_code, 422)
        self.assertEqual(self.client.get(base, params={"sort": "bogus"}).status_code, 422)
        asc = self.client.get(base, params={"sort": "lcs"}).json()["items"]
        self.assertEqual([p["signals"]["lcs"] for p in asc], sorted(p["signals"]["lcs"] for p in asc))

        csv_r = self.client.get("/api/analyses/%d/export" % an["id"], params={"format": "csv"})
        self.assertEqual(csv_r.status_code, 200)
        self.assertIn("attachment", csv_r.headers["content-disposition"])
        lines = csv_r.text.strip().splitlines()
        self.assertEqual(lines[0].split(",")[0], "student_a")
        self.assertEqual(len(lines), 16)
        js = json.loads(self.client.get("/api/analyses/%d/export?format=json" % an["id"]).text)
        self.assertEqual(len(js["pairs"]), 15)
        self.assertEqual(self.client.get("/api/analyses/%d/export?format=xml" % an["id"]).status_code, 422)

    def test_ast(self):
        aid = self.new_assignment()
        sid = self.upload(aid, [("a.py", "for i in range(3):\n    print(i)\n")]).json()["created"][0]["id"]
        raw = self.client.get("/api/submissions/%d/ast" % sid).json()["tree"]
        self.assertEqual(raw["label"], "Module")
        self.assertEqual(raw["children"][0]["label"], "For")
        norm = self.client.get("/api/submissions/%d/ast?normalized=true" % sid).json()["tree"]
        self.assertEqual([c["label"] for c in norm["children"]], ["Assign", "While"])
        self.assertEqual(norm["children"][0]["children"][0]["value"], "VAR")
        bad = self.upload(aid, [("b.py", "def (:\n")]).json()["created"][0]["id"]
        self.assertEqual(self.client.get("/api/submissions/%d/ast" % bad).status_code, 422)


if __name__ == "__main__":
    unittest.main()
