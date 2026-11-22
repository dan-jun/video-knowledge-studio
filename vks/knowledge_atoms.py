"""Deterministically build a complete knowledge-atom layer."""
from __future__ import annotations

import hashlib
import re
from typing import Any


DEFINITION_TERMS = ("是指", "定义", "称为", "叫做", "就是", "表示")
MECHANISM_TERMS = ("通过", "流程", "步骤", "机制", "根据", "然后", "接着", "先", "再")
CAUSE_TERMS = ("因为", "原因", "因此", "所以", "导致", "从而", "造成")
COMPARISON_TERMS = ("区别", "对比", "不同", "相比", "差异", "相反")
EXAMPLE_TERMS = ("例如", "比如", "假设", "举个例子", "如：")
BOUNDARY_TERMS = ("注意", "不能", "必须", "仅在", "边界", "不等于", "只允许", "只会")
CLOSURE_TERMS = (
    "本节内容至此结束",
    "本节结束",
    "课程结束",
    "以上就是本节",
    "这次课到此结束",
    "本章内容结束",
)


def _text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _seconds(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def atom_kind(claim: str, status: str) -> str:
    value = _text(claim)
    if status == "uncertain":
        return "uncertain"
    if any(term in value for term in CLOSURE_TERMS) and len(value) <= 40:
        return "closure"
    if any(term in value for term in EXAMPLE_TERMS):
        return "example"
    if any(term in value for term in COMPARISON_TERMS):
        return "comparison"
    if re.search(r"[=→⇒<>]|\d+\s*[+*/^-]\s*\d+", value):
        return "formula"
    if any(term in value for term in BOUNDARY_TERMS):
        return "boundary"
    if any(term in value for term in DEFINITION_TERMS):
        return "definition"
    if any(term in value for term in CAUSE_TERMS):
        return "cause"
    if any(term in value for term in MECHANISM_TERMS):
        return "mechanism"
    return "claim"


def atom_title(claim: str, primary_anchor: str) -> str:
    value = _text(claim)
    clause = re.split(r"[，。；：]", value, maxsplit=1)[0].strip() or value
    if len(clause) > 30:
        clause = clause[:29].rstrip() + "…"
    if len(clause) < 5 and primary_anchor:
        return f"{primary_anchor}：{clause}"
    return clause


def _nearest_anchor(concepts: list[dict], start: float, end: float) -> str:
    midpoint = (start + end) / 2
    candidates = []
    for concept in concepts:
        for evidence in concept.get("evidence") or []:
            candidates.append((
                abs(_seconds(evidence.get("start")) - midpoint),
                concept.get("title"),
            ))
    return min(candidates)[1] if candidates else ""


def build_knowledge_atoms(note: dict) -> list[dict]:
    concepts = [row for row in note.get("concepts") or [] if row.get("title")]
    concept_by_title = {row["title"]: row for row in concepts}
    visual_rows = note.get("visualEvidence") or []
    atoms = []
    for block in note.get("coverage") or []:
        block["knowledgeAtomIds"] = []
        if block.get("status") == "housekeeping":
            continue
        start = _seconds(block.get("startSeconds"))
        end = _seconds(block.get("endSeconds"))
        anchors = [
            title for title in block.get("conceptTitles") or []
            if title in concept_by_title
        ]
        if not anchors:
            nearest = _nearest_anchor(concepts, start, end)
            if nearest:
                anchors = [nearest]
        primary = anchors[0] if anchors else ""
        visual_ids = [
            row.get("candidateId") for row in visual_rows
            if start <= _seconds(row.get("start")) < max(end, start + 0.001)
        ]
        for index, raw_claim in enumerate(block.get("keyPoints") or []):
            claim = _text(raw_claim)
            if not claim:
                continue
            atom_id = (
                f"E{int(note.get('episode') or 0):02d}-"
                f"{block.get('blockId')}-A{index + 1:02d}"
            )
            atoms.append({
                "atomId": atom_id,
                "title": atom_title(claim, primary),
                "claim": claim,
                "kind": atom_kind(claim, block.get("status")),
                "blockId": block.get("blockId"),
                "sourceIndex": index,
                "time": f"{block.get('start')}–{block.get('end')}",
                "start": start,
                "end": end,
                "topic": block.get("topic") or "",
                "conceptTitles": list(anchors),
                "visualEvidenceIds": visual_ids,
                "evidence": [{
                    "kind": "coverage",
                    "blockId": block.get("blockId"),
                    "time": f"{block.get('start')}–{block.get('end')}",
                    "start": start,
                    "end": end,
                }],
            })
            block["knowledgeAtomIds"].append(atom_id)
    return atoms


def build_knowledge_graph(note: dict, atoms: list[dict]) -> dict:
    concepts = [row for row in note.get("concepts") or [] if row.get("title")]
    anchor_id = {
        row["title"]: f"anchor-{index + 1:02d}"
        for index, row in enumerate(concepts)
    }
    graph_nodes = []
    for concept in concepts:
        graph_nodes.append({
            "id": anchor_id[concept["title"]],
            "kind": "anchor",
            "label": concept["title"],
            "summary": concept.get("oneLine") or "",
            "conceptTitle": concept["title"],
        })
    for atom in atoms:
        graph_nodes.append({
            "id": atom["atomId"],
            "kind": "atom",
            "label": atom["title"],
            "summary": atom["claim"],
            "atomKind": atom["kind"],
            "blockId": atom["blockId"],
            "time": atom["time"],
            "conceptTitles": atom["conceptTitles"],
        })
    graph_edges = []
    for atom in atoms:
        for title in atom["conceptTitles"]:
            if title in anchor_id:
                graph_edges.append({
                    "from": atom["atomId"],
                    "to": anchor_id[title],
                    "type": "supports",
                    "time": atom["time"],
                    "explain": f"该原子来自覆盖块 {atom['blockId']}，支撑核心锚点“{title}”。",
                })
    by_block: dict[str, list[dict]] = {}
    for atom in atoms:
        by_block.setdefault(atom["blockId"], []).append(atom)
    for rows in by_block.values():
        rows.sort(key=lambda row: int(row.get("sourceIndex") or 0))
        for left, right in zip(rows, rows[1:]):
            graph_edges.append({
                "from": left["atomId"],
                "to": right["atomId"],
                "type": "sequence",
                "time": right["time"],
                "explain": "同一覆盖块内的教学叙述顺序，仅表示知识展开次序。",
            })
    for edge in (note.get("conceptGraph") or {}).get("edges") or []:
        left = anchor_id.get(edge.get("from"))
        right = anchor_id.get(edge.get("to"))
        if left and right:
            graph_edges.append({
                "from": left,
                "to": right,
                "type": edge.get("type"),
                "time": edge.get("time") or "",
                "explain": edge.get("explain") or "",
            })
    return {"nodes": graph_nodes, "edges": graph_edges}


def attach_knowledge_atoms(note: dict) -> list[dict]:
    atoms = build_knowledge_atoms(note)
    note["knowledgeAtoms"] = atoms
    note["knowledgeGraph"] = build_knowledge_graph(note, atoms)
    quality = note.setdefault("quality", {})
    quality["knowledgeAtoms"] = len(atoms)
    quality["knowledgeRelations"] = len(note["knowledgeGraph"]["edges"])
    quality["atomizedCoverageBlocks"] = sum(
        1 for block in note.get("coverage") or []
        if block.get("status") != "housekeeping"
    )
    quality["atomCoverage"] = 1.0 if atoms else 0.0
    note["schemaVersion"] = max(3, int(note.get("schemaVersion") or 0))
    return atoms


def validate_knowledge_atoms(note: dict) -> list[str]:
    errors = []
    concepts = {
        row.get("title") for row in note.get("concepts") or []
        if isinstance(row, dict) and row.get("title")
    }
    blocks = {
        row.get("blockId"): row for row in note.get("coverage") or []
        if isinstance(row, dict) and row.get("blockId")
    }
    atoms = note.get("knowledgeAtoms")
    if not isinstance(atoms, list):
        return ["缺少 knowledgeAtoms 原子知识层"]
    ids = [row.get("atomId") for row in atoms if isinstance(row, dict)]
    if len(ids) != len(atoms) or len(ids) != len(set(ids)):
        errors.append("knowledgeAtoms 的 atomId 缺失或重复")
    by_block: dict[str, list[dict]] = {}
    anchored = set()
    for index, atom in enumerate(atoms, start=1):
        if not isinstance(atom, dict):
            errors.append(f"原子 {index} 不是对象")
            continue
        required = (
            "atomId", "title", "claim", "kind", "blockId", "sourceIndex",
            "time", "conceptTitles", "evidence",
        )
        missing = [key for key in required if atom.get(key) in (None, "", [])]
        if missing:
            errors.append(f"原子 {index} 缺少：{', '.join(missing)}")
            continue
        block = blocks.get(atom.get("blockId"))
        if not block:
            errors.append(f"原子 {index} 引用了不存在的覆盖块")
            continue
        source_index = int(atom.get("sourceIndex") or 0)
        points = block.get("keyPoints") or []
        if source_index < 0 or source_index >= len(points):
            errors.append(f"原子 {index} 的 sourceIndex 越界")
        elif _text(points[source_index]) != _text(atom.get("claim")):
            errors.append(f"原子 {index} 与原覆盖块 keyPoint 不一致")
        unknown = set(atom.get("conceptTitles") or []) - concepts
        if unknown:
            errors.append(f"原子 {index} 引用未知核心锚点：{', '.join(sorted(unknown))}")
        if block.get("status") != "housekeeping" and not atom.get("conceptTitles"):
            errors.append(f"原子 {index} 没有核心锚点")
        anchored.update(atom.get("conceptTitles") or [])
        by_block.setdefault(atom.get("blockId"), []).append(atom)
    for block_id, block in blocks.items():
        expected = block.get("knowledgeAtomIds")
        if block.get("status") == "housekeeping":
            if expected:
                errors.append(f"杂项覆盖块 {block_id} 不应生成知识原子")
            continue
        points = block.get("keyPoints") or []
        actual = by_block.get(block_id, [])
        if not isinstance(expected, list) or len(expected) != len(points):
            errors.append(f"覆盖块 {block_id} 的 knowledgeAtomIds 与 keyPoints 不对应")
        if len(actual) != len(points):
            errors.append(f"覆盖块 {block_id} 的原子数不等于 keyPoint 数")
    missing_anchors = concepts - anchored
    if missing_anchors:
        errors.append("核心锚点没有原子支撑：" + "、".join(sorted(missing_anchors)))
    graph = note.get("knowledgeGraph")
    if not isinstance(graph, dict):
        errors.append("缺少 knowledgeGraph")
    else:
        nodes = [row for row in graph.get("nodes") or [] if isinstance(row, dict)]
        node_ids = [row.get("id") for row in nodes]
        if len(node_ids) != len(set(node_ids)):
            errors.append("knowledgeGraph 节点 ID 重复")
        actual_atoms = {row.get("id") for row in nodes if row.get("kind") == "atom"}
        if actual_atoms != set(ids):
            errors.append("knowledgeGraph 未完整纳入 knowledgeAtoms")
        node_set = set(node_ids)
        if any(
            edge.get("from") not in node_set or edge.get("to") not in node_set
            for edge in graph.get("edges") or []
        ):
            errors.append("knowledgeGraph 存在悬空边")
    return errors


def atom_stats(note: dict) -> dict:
    atoms = note.get("knowledgeAtoms") or []
    return {
        "atoms": len(atoms),
        "anchors": len(note.get("concepts") or []),
        "relations": len((note.get("knowledgeGraph") or {}).get("edges") or []),
        "coveredBlocks": len({
            row.get("blockId") for row in atoms if row.get("blockId")
        }),
        "atomHash": hashlib.sha256(
            "\n".join(
                f"{row.get('atomId')}:{row.get('claim')}" for row in atoms
            ).encode("utf-8")
        ).hexdigest(),
    }
