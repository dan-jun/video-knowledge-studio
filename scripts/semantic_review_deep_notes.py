#!/usr/bin/env python3
"""Run fresh-context semantic reviews for validated deep notes."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from vks.config import load_settings
from vks.courses import CourseStore
from vks.deep_notes import DeepNoteService, _extract_json


ROOT = Path(__file__).resolve().parents[1]
PROMPT_VERSION = "deep-semantic-review-v2"


def canonical_hash(value):
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def review_schema():
    omission = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "severity", "kind", "time", "sourceEvidence", "issue", "suggestedRepair",
        ],
        "properties": {
            "severity": {"type": "string", "enum": ["high", "medium", "low"]},
            "kind": {
                "type": "string",
                "enum": [
                    "definition", "mechanism", "condition", "formula", "example",
                    "comparison", "exception", "exam-point", "visual",
                    "traceability", "factual-error",
                ],
            },
            "time": {"type": "string"},
            "sourceEvidence": {"type": "string"},
            "issue": {"type": "string"},
            "suggestedRepair": {"type": "string"},
        },
    }
    check_names = (
        "definitions", "mechanisms", "conditions", "formulas", "examples",
        "comparisons", "exceptions", "exam_points", "visual_evidence",
        "concept_relations", "timestamp_traceability", "factual_alignment",
    )
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["decision", "coverage", "summary", "checks", "omissions", "uncertainties"],
        "properties": {
            "decision": {"type": "string", "enum": ["pass", "fail"]},
            "coverage": {"type": "number", "minimum": 0, "maximum": 1},
            "summary": {"type": "string"},
            "checks": {
                "type": "object",
                "additionalProperties": False,
                "required": list(check_names),
                "properties": {key: {"type": "boolean"} for key in check_names},
            },
            "omissions": {"type": "array", "items": omission},
            "uncertainties": {"type": "array", "items": {"type": "string"}},
        },
    }


def review_prompt(packet, note, hashes):
    review_note = dict(note)
    review_note.pop("knowledgeAtoms", None)
    review_note.pop("knowledgeGraph", None)
    evidence = {
        "lesson": packet.get("lesson"),
        "transcriptBlocks": packet.get("transcriptBlocks"),
        "visualCandidates": packet.get("visualCandidates"),
        "finalNote": review_note,
        "hashes": hashes,
        "writerRepairs": (note.get("quality") or {}).get("repairs") or [],
    }
    return f"""你是独立的知识笔记审校员。你没有参与写作，也不能沿用写作方的自我评价。请把原片证据与最终笔记逐项对照，找出真正影响学习的遗漏、曲解和错误关联。

要求：
1. transcriptBlocks 是完整连续字幕账本。逐个检查定义、机制、成立条件、公式及符号、例题/演示、对比、边界、例外、教师强调的易错点和结论，是否在 finalNote 中有可学习、可复习的表达。只判断证据中实际存在的知识，不得用课程常识补编。
2. coverage.keyPoints 只是索引，不能因为关键词出现就判定覆盖。笔记必须解释为什么、怎么做、何时成立、例子如何推出。
3. knowledgeAtoms 与 knowledgeGraph 是 coverage.keyPoints 的确定性投影，不进入本审校 payload；结构门禁已核对逐块原子数、时间、锚点归属和悬空关系。不要把缺少第二套原子改写视为遗漏。
4. 核对 coverage 的概念关联是否对应同一时间段语义；核对 conceptGraph 的每条边是否由原片支持，不能仅因节点相邻或为了连通而成立。
5. 核对 visualCandidates 与 finalNote.visualAudit/visualEvidence：每个有独有教学信息的视觉组都应有代表帧；装饰、片尾、水印可以整组排除，但必须有明确 reason。caption、whatItAdds、conceptTitles 必须说明该帧相对字幕新增的信息。
6. 重点复核 writerRepairs。自动补图、补边、补概念关联在语义上不成立时按高严重度问题报告。
7. 时间戳必须指向支持该主张的实际证据；ASR 不确定处应保留不确定性。

判定：
- 核心定义、机制、公式、关键例子或教师明确强调考点缺失/错误，记 high。
- 重要对比、边界、例子细节或视觉解释缺失/错配，记 medium。
- 不影响重建论证的措辞或可选补充，记 low。
- 任何 high/medium omission 都不得判 pass；coverage < 0.9 也不得判 pass。
- 不因排版风格、篇幅或没有逐字复述而扣分。

只返回符合 JSON Schema 的对象。每条 omission 必须引用真实时间点和简短原片证据，并给出最小修复建议。

证据包：
{json.dumps(evidence, ensure_ascii=False)}
"""


def validate_review(review):
    if review.get("decision") not in {"pass", "fail"}:
        raise RuntimeError("semantic review decision must be pass or fail")
    try:
        coverage = float(review.get("coverage"))
    except (TypeError, ValueError) as exc:
        raise RuntimeError("semantic review coverage is not numeric") from exc
    if not 0 <= coverage <= 1:
        raise RuntimeError("semantic review coverage is outside [0, 1]")
    omissions = review.get("omissions") or []
    blocking = [
        row for row in omissions
        if isinstance(row, dict) and row.get("severity") in {"high", "medium"}
    ]
    required = review_schema()["properties"]["checks"]["required"]
    checks = review.get("checks") or {}
    warnings = []
    if blocking:
        warnings.append(f"{len(blocking)} 条 high/medium omission")
    if coverage < 0.9:
        warnings.append("coverage < 0.9")
    failed = [key for key in required if checks.get(key) is not True]
    if failed:
        warnings.append("failed checks: " + ", ".join(failed))
    if review.get("decision") == "pass" and warnings:
        review["decision"] = "fail"
        review["validationWarnings"] = warnings
        review["summary"] = (
            str(review.get("summary") or "").strip()
            + " 审校输出与自身 checks/omissions/coverage 冲突；系统按 fail 处理。"
        ).strip()
    return review


def call_codex(prompt, settings):
    executable = shutil.which(settings.codex_exe) or settings.codex_exe
    ai_tmp = settings.data_dir / "ai-tmp"
    ai_tmp.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="semantic_review_", dir=ai_tmp))
    try:
        schema_path = run_dir / "schema.json"
        answer_path = run_dir / "answer.json"
        stdout_path = run_dir / "stdout.log"
        stderr_path = run_dir / "stderr.log"
        schema_path.write_text(
            json.dumps(review_schema(), ensure_ascii=False),
            encoding="utf-8",
        )
        command = [
            executable, "exec", "--ephemeral", "--skip-git-repo-check",
            "-s", "read-only", "-C", str(settings.root),
            "--color", "never",
            "-c", 'model_reasoning_effort="low"',
            "-c", "mcp_servers={}",
            "--output-schema", str(schema_path),
            "--output-last-message", str(answer_path),
            "-",
        ]
        child_env = {
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "TEMP": str(ai_tmp),
            "TMP": str(ai_tmp),
        }
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            result = subprocess.run(
                command,
                input=prompt.encode("utf-8"),
                stdout=stdout,
                stderr=stderr,
                cwd=settings.root,
                env=child_env,
                timeout=max(900, settings.ai_timeout * 4),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        raw = answer_path.read_text(encoding="utf-8") if answer_path.is_file() else ""
        if not raw:
            error = stderr_path.read_bytes().decode("utf-8", "replace")[-1400:]
            raise RuntimeError(error or f"Codex CLI exited with {result.returncode}")
        return _extract_json(raw)
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def prepare(settings, episode):
    service = DeepNoteService(settings)
    note = service.cached(episode)
    if not note:
        raise RuntimeError(f"{episode['id']} is missing a valid schema v3 deep note")
    packet = service.build_packet(episode)
    hashes = {
        "note_sha256": canonical_hash(note),
        "transcript_sha256": canonical_hash(packet.get("transcript") or []),
        "frame_manifest_sha256": canonical_hash(packet.get("visualCandidates") or []),
    }
    fingerprint = canonical_hash({
        "episode": episode["id"],
        "promptVersion": PROMPT_VERSION,
        **hashes,
    })
    return service, note, packet, hashes, fingerprint


def review_one(settings, episode, force=False):
    service, note, packet, hashes, fingerprint = prepare(settings, episode)
    path = service.review_path(episode["id"])
    if not force and path.is_file():
        try:
            cached = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            cached = None
        if cached and cached.get("inputFingerprint") == fingerprint:
            return {
                "episode": episode["id"],
                "status": "cached",
                "decision": cached.get("decision"),
                "coverage": cached.get("coverage"),
            }
    raw = validate_review(call_codex(review_prompt(packet, note, hashes), settings))
    reviewed_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    reviewer = {
        "mode": "codex",
        "provider": "codex",
        "model": "current",
        "fresh_context": True,
        "reviewed_at": reviewed_at,
        "prompt_version": PROMPT_VERSION,
    }
    record = {
        "schemaVersion": 1,
        "episode": episode.get("number"),
        "episodeId": episode["id"],
        "title": episode.get("title"),
        "chapter": episode.get("chapter"),
        **raw,
        **hashes,
        "inputFingerprint": fingerprint,
        "reviewer": reviewer,
        "writerRepairs": (note.get("quality") or {}).get("repairs") or [],
    }
    record["reviewId"] = canonical_hash({
        "episode": episode["id"],
        "inputFingerprint": fingerprint,
        "review": raw,
        "reviewer": reviewer,
    })
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)
    return {
        "episode": episode["id"],
        "status": "reviewed",
        "decision": record["decision"],
        "coverage": record["coverage"],
        "omissions": len(record.get("omissions") or []),
        "path": str(path),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--course", default="")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=9999)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    settings = load_settings()
    store = CourseStore(settings.packs_dir)
    episodes = [
        episode for episode in store.episodes.values()
        if (not args.course or episode["courseId"] == args.course)
        and args.start <= int(episode["number"]) <= args.end
    ]
    episodes.sort(key=lambda row: (row["courseId"], int(row["number"])))
    if not episodes:
        raise SystemExit("no matching episodes")

    def run(episode):
        errors = []
        for attempt in range(1, max(1, args.retries) + 1):
            try:
                return review_one(settings, episode, force=args.force)
            except subprocess.TimeoutExpired:
                errors.append("Codex review timed out")
            except Exception as exc:
                errors.append(str(exc)[:1600])
            if attempt < max(1, args.retries):
                time.sleep(attempt * 3)
        return {
            "episode": episode["id"],
            "status": "failed",
            "error": errors[-1] if errors else "semantic review failed",
        }

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for row in concurrent.futures.as_completed(
            [pool.submit(run, episode) for episode in episodes]
        ):
            results.append(row.result())
    failures = [row for row in results if row.get("status") == "failed"]
    print(json.dumps({
        "ok": not failures,
        "reviewed": len(results) - len(failures),
        "failed": failures,
    }, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
