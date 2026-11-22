from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "Node.js is required for the knowledge contract test")
class LearningDepthTests(unittest.TestCase):
    def test_transcript_grouping_covers_every_segment_once(self):
        script = r"""
const K = require(process.argv[1]);
const rows = Array.from({ length: 24 }, (_, i) => ({
  start: i * 6,
  end: i * 6 + 6,
  text: `第${i + 1}项功能说明：这一段必须进入知识卡并且不能丢失。`,
}));
const units = K.groupTranscript(rows, { targetChars: 240, maxSeconds: 60 });
const flat = units.flatMap((unit) => unit.rows.map((row) => row.text));
if (JSON.stringify(flat) !== JSON.stringify(rows.map((row) => row.text))) process.exit(2);
if (units.length < 2 || units.some((unit) => !unit.heading || !unit.preview || !unit.rows.length)) process.exit(3);
if (K.groupTranscript([]).length !== 0) process.exit(4);
process.stdout.write(JSON.stringify({ units: units.length, segments: flat.length }));
"""
        result = subprocess.run(
            ["node", "-e", script, str(ROOT / "web" / "knowledge.js")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        self.assertIn('"segments":24', result.stdout)

    def test_ui_renders_expandable_timed_transcript_and_menu_toggles(self):
        knowledge = (ROOT / "web" / "knowledge.js").read_text(encoding="utf-8")
        plugin = (ROOT / "web" / "knowledge_plugin.js").read_text(encoding="utf-8")
        index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        player = (ROOT / "web" / "player.js").read_text(encoding="utf-8")
        self.assertIn("const transcriptUnits = groupTranscript", knowledge)
        self.assertIn("完整原文证据", knowledge)
        self.assertIn("仅供核对，不作为知识点总结", knowledge)
        self.assertIn("dataset.vksTranscriptUnit", knowledge)
        self.assertIn("details.open = false", knowledge)
        self.assertIn("line.onclick = () => seek(row.start)", knowledge)
        self.assertIn("展开全部", knowledge)
        self.assertIn("window.VKSKnowledgePlugin.render", knowledge)
        self.assertIn("/api/knowledge/course-graph?id=", knowledge)
        self.assertIn('<script src="/knowledge_plugin.js"></script>', index)
        self.assertIn("证据覆盖", plugin)
        self.assertIn("核心概念", plugin)
        self.assertIn("renderConceptGraph", plugin)
        self.assertIn("概念知识网", plugin)
        self.assertIn("renderVisualAudit", plugin)
        self.assertIn("renderCourseSystem", plugin)
        self.assertIn("renderKnowledgeAtoms", plugin)
        self.assertIn("完整知识原子", plugin)
        self.assertIn("搜索本讲知识原子", plugin)
        self.assertIn("知识原子", plugin)
        self.assertIn("renderSemanticReview", plugin)
        self.assertIn("上一轮复核已失效", plugin)
        self.assertIn("renderSemanticReview(note.semanticReview", plugin)
        self.assertIn("画面审核账本", plugin)
        self.assertIn("完整字幕覆盖账本", plugin)
        self.assertIn("全课程知识体系", plugin)
        self.assertIn("/media/knowledge-frame?id=", plugin)
        self.assertIn("case 'gear': this.toggleMenu('settings')", player)
        self.assertIn("toggleMenu(view)", player)
        self.assertIn("if (k === 'Escape' && this.el.menu.classList.contains('open'))", player)
        self.assertIn("a.startsWith('rate:')", player)

    def test_focus_views_review_queue_and_cross_episode_links(self):
        plugin = (ROOT / "web" / "knowledge_plugin.js").read_text(encoding="utf-8")
        for token in (
            "kp-tab-shell",
            "renderReviewQueue",
            "kp-focus-panel",
            "localStorage",
            "vks.mastery.",
            "跨讲关联",
            "会",
            "模糊",
            "不会",
        ):
            self.assertIn(token, plugin)
        script = r"""
const P = require(process.argv[1]);
const graph = {
  course: '操作系统知识体系',
  lessons: [
    { episode: 1, episodeId: 'os-course-e01' },
    { episode: 5, episodeId: 'os-course-e05' },
    { episode: 6, episodeId: 'os-course-e06' },
  ],
  nodes: [{
    label: '系统调用',
    occurrences: [
      { episode: 1, episodeTitle: '第一讲' },
      { episode: 5, episodeTitle: '第五讲' },
      { episode: 6, episodeTitle: '第六讲' },
    ],
  }],
};
const rows = P.relatedEpisodes(graph, ['系统调用'], 1);
if (JSON.stringify(rows.map((x) => x.episodeId)) !== '["os-course-e05","os-course-e06"]') process.exit(2);
const generic = {
  course: 'Another course',
  nodes: [{
    label: '共享概念',
    occurrences: [
      { episode: 1, episodeId: 'demo-e01' },
      { episode: 2, episodeId: 'demo-e02' },
    ],
  }],
};
const genericRows = P.relatedEpisodes(generic, ['共享概念'], 1);
if (genericRows.length !== 1 || genericRows[0].episodeId !== 'demo-e02') process.exit(3);
process.stdout.write(JSON.stringify({ episodeOnly: rows.length, explicit: genericRows.length }));
"""
        result = subprocess.run(
            ["node", "-e", script, str(ROOT / "web" / "knowledge_plugin.js")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        self.assertIn('"episodeOnly":2', result.stdout)


if __name__ == "__main__":
    unittest.main()
