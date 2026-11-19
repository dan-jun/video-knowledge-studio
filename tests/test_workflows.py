from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from vks.production import ProductionError, ProductionService
from vks.workflows import WorkflowService

ROOT = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name)
        self.production = ProductionService(ROOT, self.data)
        self.project = self.production.create("scipop", "Workflow test")["id"]
        self.flow = WorkflowService(self.production, self.data)

    def tearDown(self):
        self.tmp.cleanup()

    def wait(self, fid, states, timeout=8):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            row = self.flow.get(fid)
            if row["status"] in states:
                return row
            time.sleep(.05)
        self.fail(f"workflow did not reach {states}: {self.flow.get(fid)}")

    def test_review_checkpoints_and_persistence(self):
        flow = self.flow.create(self.project)
        with patch.object(self.production, "dependencies", return_value={"ready": True, "missing": []}), \
             patch.object(self.production, "_command", return_value=[sys.executable, "-c", "print('ok')"]), \
             patch("vks.workflows.shutil.which", return_value="ffprobe"), \
             patch("vks.workflows.subprocess.run", return_value=type("ProbeResult", (), {"returncode": 0, "stdout": "1.0"})()):
            for action in ("generate", "gates", "render"):
                if action == "generate":
                    storyboard = self.production._project(self.project) / "storyboard.json"
                    self.production._command.return_value = [sys.executable, "-c", "from pathlib import Path;Path(%r).write_text('{}');print('ok')" % str(storyboard)]
                if action == "gates":
                    self.production._command.return_value = [sys.executable, "-c", "print('ok')"]
                if action == "render":
                    build = self.production._project(self.project) / "build"
                    build.mkdir(exist_ok=True)
                    sample = ROOT / "packs" / "raft-demo-en" / "media" / "lesson.mp4"
                    command = [sys.executable, "-c", "import shutil;shutil.copyfile(%r,%r);print('{\"ok\":true}')" % (str(sample), str(build / "final_hardsub.mp4"))]
                    self.production._command.return_value = command
                self.flow.resume(flow["id"])
                result = self.wait(flow["id"], {"waiting_review", "done", "failed"})
                self.assertEqual(result["status"], "done" if action == "render" else "waiting_review")
            self.assertTrue(any("ok" in line for line in result["steps"][("generate", "gates", "render").index(action)]["logs"]))
        restored = WorkflowService(self.production, self.data).get(flow["id"])
        self.assertEqual(restored["status"], "done")
        self.assertEqual([s["status"] for s in restored["steps"]], ["done"] * 3)

    def test_failed_retry_and_spec_change(self):
        flow = self.flow.create(self.project)
        with patch.object(self.production, "_command", return_value=[sys.executable, "-c", "import sys;sys.exit(2)"]):
            self.flow.resume(flow["id"])
            self.assertEqual(self.wait(flow["id"], {"failed"})["steps"][0]["status"], "failed")
        spec = self.production.project(self.project)["spec"]
        spec["title"] = "Changed"
        self.production.save_spec(self.project, spec)
        with self.assertRaisesRegex(ProductionError, "spec changed"):
            self.flow.resume(flow["id"])

    def test_cancel_terminates_child_process_tree(self):
        marker = self.data / "child-finished"
        child = "import time,pathlib;time.sleep(2);pathlib.Path(%r).write_text('bad')" % str(marker)
        parent = "import subprocess,sys,time;subprocess.Popen([sys.executable,'-c',%r]);print('started',flush=True);time.sleep(30)" % child
        flow = self.flow.create(self.project)
        with patch.object(self.production, "_command", return_value=[sys.executable, "-c", parent]):
            self.flow.resume(flow["id"])
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                job = self.production.job(self.flow.get(flow["id"])["steps"][0]["job"])
                if "started" in job["logs"]:
                    break
                time.sleep(.05)
            else:
                self.fail("child process did not start")
            self.flow.cancel(flow["id"])
            self.assertEqual(self.wait(flow["id"], {"cancelled"})["steps"][0]["status"], "cancelled")
            time.sleep(2.2)
            self.assertFalse(marker.exists(), "cancel left child process running")

    def test_restart_marks_running_workflow_interrupted(self):
        row = self.flow.create(self.project)
        row.update(status="running", activePid=12345)
        row["steps"][0]["status"] = "running"
        (self.flow.root / (row["id"] + ".json")).write_text(json.dumps(row), encoding="utf-8")
        restored = WorkflowService(self.production, self.data)
        self.assertEqual(restored.get(row["id"])["status"], "interrupted")
        with self.assertRaisesRegex(ProductionError, "may still be running"):
            restored.resume(row["id"])
        with self.assertRaisesRegex(ProductionError, "explicitly confirm"):
            restored.abandon(row["id"])
        self.assertEqual(restored.acknowledge_stopped(row["id"])["status"], "abandoned")

    def test_render_cannot_pass_using_an_old_video(self):
        row = self.flow.create(self.project)
        stored = self.flow.rows[row["id"]]
        stored["steps"][0]["status"] = stored["steps"][1]["status"] = "done"
        stored["status"] = "waiting_review"
        path = self.production._project(self.project)
        (path / "storyboard.json").write_text("{}", encoding="utf-8")
        import hashlib
        stored["storyboardHash"] = hashlib.sha256((path / "storyboard.json").read_bytes()).hexdigest()
        (path / "build").mkdir()
        import shutil
        shutil.copyfile(ROOT / "packs" / "raft-demo-en" / "media" / "lesson.mp4", path / "build" / "final_hardsub.mp4")
        time.sleep(.05)
        with patch.object(self.production, "dependencies", return_value={"ready": True, "missing": []}), \
             patch.object(self.production, "_command", return_value=[sys.executable, "-c", "print('{\"ok\":true}')"]):
            self.flow.resume(row["id"])
            result = self.wait(row["id"], {"done", "failed"})
        self.assertEqual(result["status"], "failed")

    def test_changed_storyboard_requires_new_workflow(self):
        flow = self.flow.create(self.project)
        path = self.production._project(self.project) / "storyboard.json"
        with patch.object(self.production, "_command", return_value=[sys.executable, "-c", "from pathlib import Path;Path(%r).write_text('{}');print('ok')" % str(path)]):
            self.flow.resume(flow["id"])
            self.wait(flow["id"], {"waiting_review"})
        path.write_text('{"changed":true}', encoding="utf-8")
        with self.assertRaisesRegex(ProductionError, "storyboard changed"):
            self.flow.resume(flow["id"])


if __name__ == "__main__":
    unittest.main()
