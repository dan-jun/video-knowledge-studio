import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from vks import mcp_server
from vks.discovery import DiscoveryError, search


class McpTests(unittest.TestCase):
    def test_stdio_protocol_and_capabilities(self):
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "capabilities", "arguments": {}}},
        ]
        result = subprocess.run([sys.executable, "-m", "vks.mcp_server"], input="\n".join(map(json.dumps, requests)) + "\n", capture_output=True, text=True, encoding="utf-8", timeout=10, check=True)
        responses = [json.loads(row) for row in result.stdout.splitlines()]
        self.assertEqual(responses[0]["result"]["protocolVersion"], "2024-11-05")
        self.assertIn("workflow_resume", {t["name"] for t in responses[1]["result"]["tools"]})
        capabilities = json.loads(responses[2]["result"]["content"][0]["text"])
        self.assertTrue(any("search" in item for item in capabilities["optional_tools"]))

    def test_invalid_origin_and_arguments_are_rejected(self):
        with patch.dict(os.environ, {"VKS_MCP_URL": "http://example.com"}):
            with self.assertRaisesRegex(ValueError, "local HTTP"):
                mcp_server.api("/api/projects")
        with self.assertRaisesRegex(ValueError, "invalid mode"):
            mcp_server.invoke("create_production_project", {"mode": "other", "title": "x"})

    def test_search_filters_urls_and_reports_platform_failure(self):
        from types import SimpleNamespace
        payload = {"entries": [{"url":"https://www.youtube.com/watch?v=abcdefghijk", "title":"Example", "duration":20}, {"url":"https://evil.example/video", "title":"Bad"}]}
        with patch("vks.discovery.shutil.which", return_value="yt-dlp"), patch("vks.discovery.subprocess.run", return_value=SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")) as run:
            result = search("youtube", "example", 2)
            self.assertEqual(len(result["results"]), 1)
            self.assertEqual(result["results"][0]["license"], "unknown")
            self.assertIn("--ignore-config", run.call_args.args[0])
        with patch("vks.discovery.shutil.which", return_value="yt-dlp"), patch("vks.discovery.subprocess.run", return_value=SimpleNamespace(returncode=1, stdout="{}", stderr="HTTP Error 412")):
            with self.assertRaisesRegex(DiscoveryError, "rejected"):
                search("bilibili", "example")
        bili = {"entries": [{"url":"http://www.bilibili.com/video/av123", "id":"123"}]}
        with patch("vks.discovery.shutil.which", return_value="yt-dlp"), patch("vks.discovery.subprocess.run", return_value=SimpleNamespace(returncode=0, stdout=json.dumps(bili), stderr="")):
            result = search("bilibili", "example")
            self.assertEqual(result["results"][0]["url"], "https://www.bilibili.com/video/av123")
            self.assertEqual(result["results"][0]["title"], "")


if __name__ == "__main__":
    unittest.main()
