from __future__ import annotations

import dataclasses
import json
import tempfile
import threading
import time
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from vks import server
from vks.config import load_settings


ROOT = Path(__file__).resolve().parents[1]


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        settings = dataclasses.replace(
            load_settings(),
            packs_dir=ROOT / "packs",
            data_dir=Path(cls.temp.name),
            password="",
            session_secret="test-secret",
            ai_provider="mock",
        )
        server.RUNTIME = server.Runtime(settings)
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.httpd.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.temp.cleanup()

    def get_json(self, path):
        with urllib.request.urlopen(self.base + path, timeout=20) as response:
            return response.status, json.loads(response.read())

    def post_json(self, path, body):
        request = urllib.request.Request(
            self.base + path,
            data=json.dumps(body, ensure_ascii=False).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read())

    def test_projects_and_knowledge(self):
        status, projects = self.get_json("/api/projects")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(projects), 4)
        self.assertIn("raft-e01", {row["id"] for row in projects})
        status, payload = self.get_json("/api/knowledge?id=demo-e01")
        self.assertEqual(status, 200)
        self.assertEqual(payload["episode"]["id"], "demo-e01")
        self.assertTrue(payload["episode"]["timeline"])
        status, raft = self.get_json("/api/knowledge?id=raft-e01")
        self.assertEqual(status, 200)
        self.assertIn("Raft", raft["episode"]["title"])
        self.assertTrue(raft["episode"]["terms"])

    def test_video_range(self):
        request = urllib.request.Request(
            self.base + "/media/video?id=demo-e01",
            headers={"Range": "bytes=0-255"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read()
            self.assertEqual(response.status, 206)
            self.assertEqual(len(body), 256)

    def test_mock_ai_job(self):
        status, start = self.post_json("/api/ai/ask", {
            "id": "demo-e01",
            "selected": "可信笔记需要保留证据",
            "kid": "E01:core:1",
            "action": "explain",
            "time": 12,
        })
        self.assertEqual(status, 202)
        for _ in range(20):
            _, row = self.get_json("/api/ai/job?id=" + start["job"])
            if row.get("status") == "done":
                self.assertEqual(row["result"]["provider"], "offline-demo")
                return
            time.sleep(0.05)
        self.fail("mock AI job did not finish")

    def test_production_modes_and_project_creation(self):
        status, payload = self.get_json("/api/production/modes")
        self.assertEqual(status, 200)
        self.assertEqual({row["id"] for row in payload["modes"]}, {"remix", "course", "scipop"})
        self.assertIn("dependencies", payload)
        status, created = self.post_json("/api/production/create", {
            "mode": "scipop",
            "title": "Production smoke test",
            "spec": "",
        })
        self.assertEqual(status, 200)
        project = created["project"]
        self.assertEqual(project["mode"], "scipop")
        self.assertTrue(project["spec"]["pages"])
        status, _ = self.get_json("/api/production/project?id=" + project["id"])
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
