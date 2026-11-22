#!/usr/bin/env python3
"""Build a connected course-wide concept graph from validated deep notes."""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

from vks.config import load_settings
from vks.courses import CourseStore
from vks.deep_notes import DeepNoteService


def key_of(value):
    return re.sub(r"[\W_]+", "", str(value or "").lower(), flags=re.UNICODE)


def build(course_id: str, output: Path):
    settings = load_settings()
    store = CourseStore(settings.packs_dir)
    course = store.courses[course_id]
    service = DeepNoteService(settings)
    episode_rows = sorted(course["episodes"], key=lambda row: int(row["number"]))
    notes = {}
    for episode in episode_rows:
        note = service.cached(episode)
        if not note:
            raise RuntimeError(f"{episode['id']} is missing a valid schema v3 deep note")
        notes[episode["id"]] = note

    key_to_id = {}
    nodes = []
    knowledge_atoms = []
    lessons = []
    chapter_nodes = {}
    chapter_order = []
    for chapter in course["chapters"]:
        chapter_order.append(chapter["id"])
        chapter_nodes[chapter["id"]] = {
            "id": "chapter-" + chapter["id"],
            "label": chapter["title"],
            "conceptIds": [],
            "episodes": [],
            "lessonIds": [],
            "atomIds": [],
        }

    local_meta = {}
    episode_to_chapter = {}
    for episode in episode_rows:
        episode_id = episode["id"]
        note = notes[episode_id]
        chapter_id = episode["chapterId"]
        episode_to_chapter[episode_id] = chapter_id
        chapter_nodes[chapter_id]["episodes"].append(int(episode["number"]))
        local_concept_ids = []
        for graph_node in (note.get("conceptGraph") or {}).get("nodes", []):
            title = str(graph_node.get("conceptTitle") or "").strip()
            key = key_of(title) or title
            if key not in key_to_id:
                node_id = f"concept-{len(nodes) + 1:04d}"
                key_to_id[key] = node_id
                nodes.append({
                    "id": node_id,
                    "key": key,
                    "label": title,
                    "summary": str(graph_node.get("summary") or ""),
                    "chapterIds": [],
                    "occurrences": [],
                })
            node = next(row for row in nodes if row["id"] == key_to_id[key])
            if chapter_id not in node["chapterIds"]:
                node["chapterIds"].append(chapter_id)
            concept = next(
                (row for row in note.get("concepts", []) if row.get("title") == title),
                {},
            )
            evidence = concept.get("evidence") or []
            node["occurrences"].append({
                "episodeId": episode_id,
                "episode": int(episode["number"]),
                "episodeTitle": note.get("title"),
                "chapterId": chapter_id,
                "role": graph_node.get("role"),
                "time": evidence[0].get("time") if evidence else "",
            })
            if node["id"] not in chapter_nodes[chapter_id]["conceptIds"]:
                chapter_nodes[chapter_id]["conceptIds"].append(node["id"])
            if node["id"] not in local_concept_ids:
                local_concept_ids.append(node["id"])

        lesson_id = f"lesson-{episode_id}"
        lesson = {
            "id": lesson_id,
            "episodeId": episode_id,
            "episode": int(episode["number"]),
            "label": note.get("title") or episode.get("title") or episode_id,
            "chapterId": chapter_id,
            "conceptIds": local_concept_ids,
            "knowledgeAtomIds": [],
            "knowledgeAtomCount": len(note.get("knowledgeAtoms") or []),
        }
        lessons.append(lesson)
        chapter_nodes[chapter_id]["lessonIds"].append(lesson_id)
        for atom in note.get("knowledgeAtoms") or []:
            atom_id = "atom-" + str(atom.get("atomId"))
            concept_ids = []
            for title in atom.get("conceptTitles") or []:
                concept_id = key_to_id.get(key_of(title))
                if concept_id and concept_id not in concept_ids:
                    concept_ids.append(concept_id)
            knowledge_atoms.append({
                "id": atom_id,
                "episodeId": episode_id,
                "episode": int(episode["number"]),
                "lessonId": lesson_id,
                "chapterId": chapter_id,
                "label": atom.get("title"),
                "claim": atom.get("claim"),
                "kind": atom.get("kind"),
                "blockId": atom.get("blockId"),
                "time": atom.get("time"),
                "conceptIds": concept_ids,
                "visualEvidenceIds": atom.get("visualEvidenceIds") or [],
            })
            lesson["knowledgeAtomIds"].append(atom_id)
            chapter_nodes[chapter_id]["atomIds"].append(atom_id)

    edge_map = {}

    def add_edge(left_key, right_key, edge_type, explain, episode_id=None, course_order=False):
        left = key_to_id.get(left_key)
        right = key_to_id.get(right_key)
        if not left or not right or left == right:
            return
        edge_key = (left, right, edge_type)
        row = edge_map.setdefault(edge_key, {
            "id": f"edge-{len(edge_map) + 1:03d}",
            "from": left,
            "to": right,
            "type": edge_type,
            "episodes": [],
            "explanations": [],
            "courseOrder": False,
        })
        if episode_id and episode_id not in row["episodes"]:
            row["episodes"].append(episode_id)
        if explain and explain not in row["explanations"]:
            row["explanations"].append(explain)
        row["courseOrder"] = row["courseOrder"] or course_order

    for episode in episode_rows:
        note = notes[episode["id"]]
        graph = note.get("conceptGraph") or {}
        local_by_key = {
            key_of(row.get("conceptTitle")): row.get("conceptTitle")
            for row in graph.get("nodes", [])
        }
        indegree = {key: 0 for key in local_by_key}
        outdegree = {key: 0 for key in local_by_key}
        for edge in graph.get("edges", []):
            left_key = key_of(edge.get("from"))
            right_key = key_of(edge.get("to"))
            outdegree[left_key] = outdegree.get(left_key, 0) + 1
            indegree[right_key] = indegree.get(right_key, 0) + 1
            add_edge(
                left_key,
                right_key,
                edge.get("type"),
                edge.get("explain"),
                episode_id=episode["id"],
            )
        sources = [key for key, degree in indegree.items() if degree == 0]
        sinks = [key for key, degree in outdegree.items() if degree == 0]
        local_meta[episode["id"]] = {
            "source": sources[0] if sources else next(iter(local_by_key), ""),
            "sink": sinks[0] if sinks else next(iter(local_by_key), ""),
        }

    for chapter_id, chapter in chapter_nodes.items():
        chapter_episodes = sorted(chapter["episodes"])
        by_number = {int(episode["number"]): episode for episode in episode_rows}
        for left_number, right_number in zip(chapter_episodes, chapter_episodes[1:]):
            left_id = by_number[left_number]["id"]
            right_id = by_number[right_number]["id"]
            add_edge(
                local_meta[left_id]["sink"],
                local_meta[right_id]["source"],
                "prerequisite",
                f"课程顺序递进：{left_id} → {right_id}",
                episode_id=right_id,
                course_order=True,
            )

    chapter_flow = [
        {
            "from": chapter_nodes[left]["id"],
            "to": chapter_nodes[right]["id"],
            "type": "prerequisite",
            "explain": f"{chapter_nodes[left]['label']} 为 {chapter_nodes[right]['label']} 提供前置框架。",
        }
        for left, right in zip(chapter_order, chapter_order[1:])
    ]
    edges = list(edge_map.values())
    adjacency = {node["id"]: set() for node in nodes}
    for edge in edges:
        adjacency[edge["from"]].add(edge["to"])
        adjacency[edge["to"]].add(edge["from"])
    seen = set()
    if nodes:
        stack = [nodes[0]["id"]]
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(adjacency[node] - seen)
    if len(seen) != len(nodes):
        raise RuntimeError("course concept graph is disconnected")

    source_hash = hashlib.sha256(
        "".join(
            json.dumps(notes[row["id"]], ensure_ascii=False, sort_keys=True)
            for row in episode_rows
        ).encode("utf-8")
    ).hexdigest()
    result = {
        "schemaVersion": 2,
        "courseId": course_id,
        "course": course["title"],
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "sourceHash": source_hash,
        "stats": {
            "episodes": len(notes),
            "chapters": len(chapter_nodes),
            "lessons": len(lessons),
            "conceptOccurrences": sum(len(node["occurrences"]) for node in nodes),
            "canonicalConcepts": len(nodes),
            "knowledgeAtoms": len(knowledge_atoms),
            "knowledgeRelations": sum(
                len((note.get("knowledgeGraph") or {}).get("edges") or [])
                for note in notes.values()
            ),
            "edges": len(edges),
        },
        "chapters": [chapter_nodes[cid] for cid in chapter_order],
        "chapterFlow": chapter_flow,
        "lessons": lessons,
        "nodes": nodes,
        "edges": edges,
        "knowledgeAtoms": knowledge_atoms,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(".tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, output)
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--course", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    settings = load_settings()
    output = Path(args.output).expanduser() if args.output else (
        settings.data_dir / "cache" / "deep_notes" / f"{args.course}-course-graph.json"
    )
    result = build(args.course, output)
    print(json.dumps({"ok": True, "path": str(output), **result["stats"]}, ensure_ascii=False))
