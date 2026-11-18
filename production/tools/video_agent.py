# -*- coding: utf-8 -*-
"""视频制作 Agent —— 两种分区（科普短片 / 长教学）的统一入口。

用法：
    python tools/video_agent.py plan   --mode scipop|course --title "..." --project <目录>
    python tools/video_agent.py render --project <目录>
    python tools/video_agent.py qa     --project <目录>
    python tools/video_agent.py publish --project <目录>
    python tools/video_agent.py status --project <目录>

设计：模式只改「参数 + 门槛」，不改流水线本身。
     scipop  = 几分钟科普，动画密度优先、完播率优先、片尾复盘
     course  = 几十分钟教学，分章、每章练习题两页、片尾复盘、字幕/同步更严
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from paths import resolve_out  # noqa: E402

PY = sys.executable

# 三个分区的规则统一由 tools/modes.py 提供（单一真相源，避免两处口径打架）
try:
    from modes import MODES  # noqa: E402
except Exception:  # 兜底：同目录导入失败时退回内置副本
    MODES = {}



def save_meta(project, meta):
    """写回 agent.json 时保留已有自定义字段（如 src_duration/sources），
    避免渲染步骤把外部回填的数据冲掉。"""
    path = os.path.join(project, "agent.json")
    old = {}
    try:
        if os.path.exists(path):
            old = json.load(open(path, encoding="utf-8")) or {}
    except Exception:
        old = {}
    keep = {k: v for k, v in old.items() if k not in meta}
    merged = {**keep, **meta}
    json.dump(merged, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return merged


# 阶段只进不退：先 verify 后 qa 曾把 stage 从 verified 改回 qa（2026-11-16 实测）。
# 失败态（*-failed）不受此限，永远照写。
_STAGE_ORDER = ["planned", "transcribed", "validated", "rendered", "qa", "verified", "published"]


def _advance_stage(meta, stage):
    cur = meta.get("stage")
    if (stage.endswith("-failed") or stage not in _STAGE_ORDER
            or cur not in _STAGE_ORDER):
        meta["stage"] = stage
        return
    meta["stage"] = (stage if _STAGE_ORDER.index(stage) >= _STAGE_ORDER.index(cur) else cur)


def load_project(project):
    project = resolve_out(project) if not os.path.isabs(project) else project
    meta = os.path.join(project, "agent.json")
    if not os.path.exists(meta):
        raise SystemExit(f"不是 agent 项目（缺 agent.json）：{project}")
    return project, json.load(open(meta, encoding="utf-8"))


def cmd_plan(a):
    mode = MODES[a.mode]
    project = resolve_out(a.project) if not os.path.isabs(a.project) else a.project
    os.makedirs(project, exist_ok=True)
    sb = {
        "topic": a.mode,
        "title": a.title,
        "voice": "Chinese (Mandarin)_Reliable_Executive",
        "parts": [{"part": a.mode, "pages": []}],
    }
    json.dump(sb, open(os.path.join(project, "storyboard.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    meta = {"mode": a.mode, "title": a.title, "label": mode["label"],
            "params": {k: v for k, v in mode.items() if k not in ("rules", "label")},
            "rules": mode.get("rules_text") or [r[0] if isinstance(r, tuple) else r for r in mode["rules"]], "stage": "planned"}
    save_meta(project, meta)
    print(json.dumps({"ok": True, "project": project, "mode": a.mode,
                      "target_min": mode["target_min"], "rules": mode.get("rules_text") or [r[0] if isinstance(r, tuple) else r for r in mode["rules"]]},
                     ensure_ascii=False, indent=2))


def _polyphone_check(sb, strict=None):
    """配音前的多音字检查（validate 与 render 共用）。

    返回 None 表示检查器不在；否则返回 {hits, high_risk, items, message, strict}。
    strict 优先级：入参 > 环境变量 POLYPHONE_STRICT > False
    """
    script = os.path.join(HERE, "polyphone.py")
    if not os.path.isfile(script) or not os.path.isfile(sb):
        return None
    if strict is None:
        strict = os.environ.get("POLYPHONE_STRICT", "").lower() in ("1", "true", "yes", "on")
    r = _run([PY, script, "check", sb], timeout=120)
    try:
        data = json.loads((r.stdout or "").strip() or "{}")
    except Exception:  # noqa: BLE001
        data = {}
    high = [x for x in (data.get("items") or []) if x.get("risk") == "高"]
    msg = None
    if high:
        words = "、".join(sorted({x["word"] for x in high})[:8])
        msg = (f"多音字高风险 {len(high)} 处（配音可能读错）：{words}"
               " —— 改文案，或配音后人工听这几个词")
    return {"ok": bool(data.get("ok", True)), "hits": data.get("hits"),
            "high_risk": data.get("high_risk"), "items": high[:12],
            "message": msg, "strict": strict}


def cmd_render(a):
    project, meta = load_project(a.project)
    sb = os.path.join(project, "storyboard.json")
    p = meta["params"]
    out = os.path.join(project, "build")

    # 配音前最后一次多音字检查：这一步真会调 TTS，查不查差别最大
    poly = _polyphone_check(sb, strict=getattr(a, "strict_polyphone", False) or None)
    if poly and poly.get("message"):
        if poly.get("strict"):
            print(json.dumps({"ok": False, "stage": "render", "polyphone": poly,
                              "error": "多音字高风险未处理（strict 模式）：" + poly["message"]},
                             ensure_ascii=False, indent=2))
            raise SystemExit(1)
        print(f"[polyphone] ⚠️ {poly['message']}", file=sys.stderr)

    # 配音：默认走免费 edge-tts（不烧 API 额度）；要 MiniMax 就设 TTS_PROVIDER=minimax
    tts = os.environ.get("TTS_PROVIDER", "edge")
    voice = os.environ.get("TTS_VOICE") or (
        "zh-CN-XiaoxiaoNeural" if tts == "edge" else "Chinese (Mandarin)_Reliable_Executive"
    )
    tts_speed = float(os.environ.get("VKS_TTS_SPEED", p["mm_speed"]))
    cmd = [PY, os.path.join(HERE, "build_video.py"), sb, out,
           "--tts", tts, "--voice", voice,
           "--mm-speed", str(tts_speed)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(json.dumps({"ok": False, "stage": "render",
                          "error": (r.stdout or "")[-1200:] + (r.stderr or "")[-800:]},
                         ensure_ascii=False))
        raise SystemExit(1)
    rep = json.load(open(os.path.join(out, "build-report.json"), encoding="utf-8"))
    total = rep.get("actual_total") or sum(float(s2.get("video") or 0) for s2 in rep["segments"])
    rep["minutes"] = round(total / 60, 2)
    meta["stage"] = "rendered"
    meta["build"] = {"minutes": rep["minutes"], "pages": rep["pages"], "drift": rep["drift"]}
    save_meta(project, meta)
    print(json.dumps({"ok": True, "minutes": rep["minutes"], "pages": rep["pages"],
                      "drift": rep["drift"], "video": os.path.join(out, "final_hardsub.mp4"),
                      "polyphone": (poly or {}).get("message") and {"high_risk": poly.get("high_risk"),
                                                                   "items": poly.get("items")}},
                     ensure_ascii=False, indent=2))


def cmd_qa(a):
    project, meta = load_project(a.project)
    build = os.path.join(project, "build")
    # 2026-11-16 修：原来固定抽 merged.mkv（**无字幕**母版），字幕是这之后才烧上去的，
    # 所以「查有没有压字」永远查不到。优先抽真正会发出去的那一版。
    hardsub = os.path.join(build, "final_hardsub.mp4")
    merged = hardsub if os.path.exists(hardsub) else os.path.join(build, "merged.mkv")
    rep = json.load(open(os.path.join(build, "build-report.json"), encoding="utf-8"))
    total = rep.get("actual_total") or sum(float(s2.get("video") or 0) for s2 in rep["segments"])
    rep["minutes"] = round(total / 60, 2)
    sheet_py = os.path.join(HERE, "contact_sheet.py")
    problems = []

    # 1) 每页抽帧拼图（查画面内文字是否打架）
    r = subprocess.run([PY, sheet_py, merged, os.path.join(build, "build-report.json"),
                        os.path.join(project, "qa")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    sheets = [l.strip() for l in (r.stdout or "").splitlines() if l.strip().endswith(".png")]

    # 2) 时长是否落在模式区间
    lo, hi = MODES[meta["mode"]]["target_min"]
    if not (lo <= rep["minutes"] <= hi):
        problems.append(f"时长 {rep['minutes']:.1f} 分钟，超出 {meta['mode']} 的 {lo}–{hi} 分钟")

    # 3) 同步漂移
    if rep["drift"] > 0.1:
        problems.append(f"母版漂移 {rep['drift']:.3f}s > 0.1s")

    _advance_stage(meta, "qa-failed" if problems else "qa")
    meta["qa"] = {"sheets": sheets, "problems": problems}
    save_meta(project, meta)
    print(json.dumps({"ok": not problems, "sheets": sheets, "problems": problems},
                     ensure_ascii=False, indent=2))


def cmd_publish(a):
    project, meta = load_project(a.project)
    covers = os.path.join(project, "publish")
    r = subprocess.run([PY, os.path.join(HERE, "make_covers.py"), covers],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    # 以前不查 returncode、无条件写 published 并回 ok:true —— make_covers 崩了也当成功
    made = r.returncode == 0 and os.path.isdir(covers)
    files = sorted(os.listdir(covers)) if os.path.isdir(covers) else []
    _advance_stage(meta, "published" if made else "publish-failed")
    save_meta(project, meta)
    tail = "" if made else ((r.stdout or "") + (r.stderr or "")).strip()[-500:]
    print(json.dumps({"ok": made, "covers": covers, "files": files,
                      "returncode": r.returncode, "tail": tail},
                     ensure_ascii=False, indent=2))


def cmd_status(a):
    project, meta = load_project(a.project)
    print(json.dumps({"project": project, "mode": meta["mode"], "stage": meta.get("stage"),
                      "polish": meta.get("polish"),
                      "build": meta.get("build"), "qa": meta.get("qa")},
                     ensure_ascii=False, indent=2))



# ── 校验 / 白板 / 分章 / 字幕 ────────────────────────────────────
SKILL = os.path.join(ROOT, "skills", "whiteboard-teacher-video")
ENGINE = os.path.join(SKILL, "engine")
FFMPEG_DIR = os.path.dirname(shutil.which("ffmpeg") or "")
NODE = os.environ.get("NODE_EXE") or shutil.which("node") or "node"


def _run(cmd, cwd=None, timeout=3600):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PATH"] = FFMPEG_DIR + os.pathsep + env.get("PATH", "")
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)

VIDEO_EXT = {".mp4", ".mkv", ".mov", ".avi", ".flv", ".webm", ".m4v", ".ts", ".wmv"}


def _scan_videos(folder):
    out = []
    for dp, dn, fn in os.walk(folder):
        for f in fn:
            if os.path.splitext(f)[1].lower() in VIDEO_EXT:
                out.append(os.path.join(dp, f))
    return sorted(out)


def _slug(path):
    base = os.path.splitext(os.path.basename(path))[0]
    return re.sub(r"[^\w\u4e00-\u9fff-]+", "-", base)[:60] or "video"


# ── 校音（术语表之后的第二道工序） ─────────────────────────────
ASR_HOME = os.environ.get("VIDEO_ASR_HOME") or ""


def _polish_step(src_dir):
    """转录后自动校音。

    有 POLISH_API_KEY + POLISH_BASE_URL → 直接跑 api 模式并应用（全自动）
    没有 → 导出请求文件，把「下一步该做什么」写进返回里（由 agent 完成）
    """
    raw = os.path.join(src_dir, "_asr_raw")
    py = os.path.join(ASR_HOME, ".venv", "Scripts", "python.exe")
    script = os.path.join(ASR_HOME, "polish.py")
    if not (os.path.isfile(py) and os.path.isfile(script)):
        return {"ok": False, "reason": f"校音组件不在（检查 VIDEO_ASR_HOME={ASR_HOME}）"}
    if not os.path.isdir(raw):
        return {"ok": False, "reason": f"找不到 {raw}"}

    if os.environ.get("POLISH_API_KEY") and os.environ.get("POLISH_BASE_URL"):
        r1 = _run([py, script, "api", raw], timeout=1800)
        out = os.path.join(raw, "polish_out.json")
        if not os.path.isfile(out):
            return {"ok": False, "mode": "auto",
                    "tail": (r1.stdout or r1.stderr or "").strip()[-300:]}
        r2 = _run([py, script, "apply", raw, out, "--contract", src_dir], timeout=900)
        try:
            summary = json.loads((r2.stdout or "").strip() or "{}")
        except Exception:  # noqa: BLE001
            summary = {}
        return {"ok": r2.returncode == 0, "mode": "auto",
                "applied": summary.get("applied"), "suspicious": summary.get("suspicious"),
                "tail": (r2.stdout or r2.stderr or "").strip()[-200:]}

    r = _run([py, script, "export", raw], timeout=600)
    return {
        "ok": r.returncode == 0,
        "mode": "export",
        "request": os.path.join(raw, "polish_in.json"),
        "flat": os.path.join(raw, "polish_input.txt"),
        "apply_cmd": f'"{py}" "{script}" apply "{raw}" "{os.path.join(raw, "polish_out.json")}" '
                     f'--contract "{src_dir}"',
    }


def cmd_remix(a):
    """视频涅槃：转录原片 → 建项目 → 生成覆盖清单模板（等人补知识点）。"""
    project = resolve_out(a.project)
    os.makedirs(project, exist_ok=True)

    # ── 目录：批量涅槃 ──────────────────────────────
    if os.path.isdir(a.source):
        vids = _scan_videos(a.source)
        manifest_path = os.path.join(project, "manifest.json")
        prev = {}
        if os.path.exists(manifest_path):
            prev = {x["source"]: x for x in json.load(open(manifest_path, encoding="utf-8"))}
        rows, done = [], 0
        for v in vids:
            row = prev.get(v, {"source": v, "title": _slug(v), "status": "pending"})
            if row.get("status") != "done" and done < a.limit:
                sub = os.path.join(project, row["title"])
                r = _run([PY, os.path.join(HERE, "transcribe.py"), v, os.path.join(sub, "src")], timeout=3600)
                row["status"] = "done" if r.returncode == 0 else "failed"
                row["project"] = sub
                row["tail"] = (r.stdout or r.stderr or "").strip()[-200:]
                if row["status"] == "done" and not getattr(a, "no_polish", False):
                    row["polish"] = _polish_step(os.path.join(sub, "src"))
                # 子项目同样要有 agent.json + storyboard 骨架，否则 render 不认
                mode = MODES["remix"]
                os.makedirs(sub, exist_ok=True)
                sb_p = os.path.join(sub, "storyboard.json")
                if not os.path.exists(sb_p):
                    json.dump({"topic": "remix", "title": row["title"],
                               "voice": "Chinese (Mandarin)_Reliable_Executive",
                               "source": {"local": v},
                               "parts": [{"part": "重制", "pages": []}]},
                              open(sb_p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                json.dump({"mode": "remix", "title": row["title"], "label": mode["label"],
                           "params": {k: vv for k, vv in mode.items() if k not in ("rules", "label")},
                           "rules": mode.get("rules_text") or [r[0] if isinstance(r, tuple) else r for r in mode["rules"]], "stage": row["status"],
                           "source": {"local": v}},
                          open(os.path.join(sub, "agent.json"), "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
                done += 1
            rows.append(row)
        json.dump(rows, open(manifest_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(json.dumps({
            "ok": True, "mode": "batch", "folder": a.source,
            "total": len(rows), "transcribed": sum(1 for x in rows if x["status"] == "done"),
            "pending": sum(1 for x in rows if x["status"] == "pending"),
            "manifest": manifest_path,
            "rules": MODES["remix"]["rules"],
            "next": ["对 manifest 里 status=done 的逐个写 keys.txt 与 storyboard",
                     "coverage_check 必须 100%", "再跑 render / qa / publish",
                     "再执行一次本命令会接着转录下一批（默认每次 " + str(a.limit) + " 个）"],
        }, ensure_ascii=False, indent=2))
        return

    # 1) 转录
    src_dir = os.path.join(project, "src")
    r = _run([PY, os.path.join(HERE, "transcribe.py"), a.source, src_dir], timeout=3600)
    trans_ok = r.returncode == 0 and os.path.exists(os.path.join(src_dir, "transcript.txt"))
    tail = (r.stdout or r.stderr or "").strip()[-300:]

    # 1.5) 校音：术语表治不了的单字同音，这里补一刀
    polish_info = None
    if trans_ok and not getattr(a, "no_polish", False):
        polish_info = _polish_step(src_dir)

    # 2) 项目骨架
    meta_path = os.path.join(project, "agent.json")
    mode = MODES["remix"]
    sb_path = os.path.join(project, "storyboard.json")
    if not os.path.exists(sb_path):
        json.dump({"topic": "remix", "title": a.title or os.path.basename(a.source),
                   "voice": "Chinese (Mandarin)_Reliable_Executive",
                   "source": {"local": a.source},
                   "parts": [{"part": "重制", "pages": []}]},
                  open(sb_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump({"mode": "remix", "title": a.title or "", "label": mode["label"],
               "params": {k: v for k, v in mode.items() if k not in ("rules", "label")},
               "rules": mode.get("rules_text") or [r[0] if isinstance(r, tuple) else r for r in mode["rules"]], "stage": "transcribed" if trans_ok else "transcribe-failed",
               "polish": polish_info,
               "source": {"local": a.source}},
              open(meta_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({"ok": trans_ok, "project": project, "transcript": os.path.join(src_dir, "transcript.txt"),
                      "polish": polish_info,
                      "next": ["polish.mode=export 时：把 polish_input.txt 交给模型，回 polish_out.json，再跑 polish.apply_cmd（会自动同步 src 契约）",
                               "人工/模型从 transcript 抽知识点写 keys.txt",
                               "coverage_check 必须 100% 覆盖",
                               "写 storyboard（每页 cites 指回原片时间）", "render → qa"],
                      "rules": mode.get("rules_text") or [r[0] if isinstance(r, tuple) else r for r in mode["rules"]], "tail": tail}, ensure_ascii=False, indent=2))


def cmd_validate(a):
    """契约校验 + 时长预估（+ 可选出处校验）。"""
    project, meta = load_project(a.project)
    sb = os.path.join(project, "storyboard.json")
    checks, problems = [], []

    r = _run([PY, os.path.join(HERE, "validate_storyboard.py"), sb], timeout=300)
    ok = r.returncode == 0
    checks.append({"name": "storyboard-contract", "ok": ok,
                   "tail": (r.stdout or "").strip()[-500:]})
    if not ok:
        problems.append("契约校验未通过：见 checks[0].tail")

    # 预估只作参考：真正的时长门槛按模式区间判断（见 qa）
    # 把本模式的时长下限传给估算器，否则它用默认 --min-min 50（course 门槛），
    # remix / scipop 会一直打一行与本片无关的 [FAIL] short by …
    lo, hi = MODES[meta["mode"]]["target_min"]
    r2 = _run([PY, os.path.join(HERE, "estimate_duration.py"), sb,
               "--min-min", str(lo)], timeout=180)
    est = (r2.stdout or "").strip()[-300:]
    minutes = None
    import re as _re
    m = _re.search(r"≈\s*([0-9.]+)\s*min", est)
    if m:
        minutes = float(m.group(1))
    in_range = minutes is not None and lo <= minutes <= hi
    # ok 曾经硬编码 True，和 storyboard-contract 的「退出码 0」语义打架、会骗人。
    # 现在 ok = 是否真的落在本模式区间；ran 才表示「这道 check 跑过了」。
    checks.append({"name": "duration-estimate", "ran": True, "ok": in_range,
                   "minutes": minutes, "in_target": in_range, "target": [lo, hi], "tail": est})
    if minutes is not None and not in_range:
        problems.append(f"预估时长 {minutes:.1f} 分钟，不在 {meta['mode']} 的 {lo}–{hi} 区间")

    if a.topic_dir:
        r3 = _run([PY, os.path.join(HERE, "verify_cites.py"), a.topic_dir, sb], timeout=300)
        ok3 = r3.returncode == 0
        checks.append({"name": "cites", "ok": ok3, "tail": (r3.stdout or "").strip()[-500:]})
        if not ok3:
            problems.append("出处校验未通过（缺 cite 或格式不对）")

    # 多音字：配音前查一遍，避免 TTS 把「行优先」「卷积核」读错
    # 默认只警告（不阻断）；--strict-polyphone 或环境变量 POLYPHONE_STRICT=1 才阻断
    warnings = []
    poly = _polyphone_check(sb, strict=getattr(a, "strict_polyphone", False) or None)
    if poly is not None:
        checks.append({"name": "polyphone", "ok": poly["ok"],
                       "hits": poly["hits"], "high_risk": poly["high_risk"],
                       "items": poly["items"]})
        if poly["message"]:
            (problems if poly["strict"] else warnings).append(poly["message"])

    # 失败就别把项目标成「已验证」——下游会照着放行
    _advance_stage(meta, "validate-failed" if problems else "validated")
    meta["validate"] = {"checks": checks, "problems": problems}

    # 引用时间跨度：cites 全挤在原片开头是典型的「装饰性引用」
    # （2026-11-16 实测：3b1b 全系列 13 条 cite 全是 S1 p02 00:00–02:57，原片 9:52）。
    # 只警告不阻断：历史项目无法自动修（src/ 没留音频、转写稿无时间戳），
    # 但新片必须在 ③ 就看到这条。
    src_dur = meta.get("src_duration") or 0
    sb_obj = json.load(open(sb, encoding="utf-8"))
    pgs = sb_obj.get("pages") or [q for pt in sb_obj.get("parts", []) for q in pt.get("pages", [])]
    secs = []
    for q in pgs:
        for c in (q.get("cites") or []):
            mm = _re.search(r"(\d{1,2}):(\d{2})\s*$", str(c).strip())
            if mm:
                secs.append(int(mm.group(1)) * 60 + int(mm.group(2)))
    if secs and src_dur:
        span = max(secs) / src_dur
        if span < 0.55:
            warnings.append(
                f"引用时间只跨到原片 {span:.0%}（最大 {max(secs) // 60}:{max(secs) % 60:02d} / "
                f"全长 {src_dur / 60:.1f} 分钟）——cites 可能只是装饰，没真正指着出处")
    save_meta(project, meta)
    print(json.dumps({"ok": not problems, "checks": checks, "problems": problems,
                      "warnings": warnings},
                     ensure_ascii=False, indent=2))


def cmd_verify(a):
    """ASR 音画同步校验（听声音对不对得上画面）。"""
    project, meta = load_project(a.project)
    sb = os.path.join(project, "storyboard.json")
    build = os.path.join(project, "build")
    rep = os.path.join(project, "verify.md")
    r = _run([PY, os.path.join(HERE, "verify_av.py"), sb, build, "--n", str(a.n), "--out", rep],
             timeout=1800)
    ok = "PASS" in (r.stdout or "")
    # 以前无条件写 verified，失败也标成「已验证」——和 validate 那个同款 bug
    _advance_stage(meta, "verified" if ok else "verify-failed")
    meta["verify"] = {"ok": ok, "report": rep, "tail": (r.stdout or "").strip()[-800:]}
    save_meta(project, meta)
    print(json.dumps({"ok": ok, "report": rep, "tail": (r.stdout or "").strip()[-800:]},
                     ensure_ascii=False, indent=2))


def cmd_whiteboard(a):
    """手绘白板路线：storyboard → frametell 工程 → 配音 → lint → 渲染。"""
    project, meta = load_project(a.project)
    sb = os.path.join(project, "storyboard.json")
    _poly_warn = _polyphone_check(sb)
    if _poly_warn and _poly_warn.get("message"):
        if _poly_warn.get("strict"):
            raise SystemExit("多音字高风险未处理（strict）：" + _poly_warn["message"])
        print(f"[polyphone] ⚠️ {_poly_warn['message']}", file=sys.stderr)
    wb = os.path.join(project, "wb")
    steps = []
    # Edge 打不开非 C 盘的 file:// 路径（D 盘报 ERR_FILE_NOT_FOUND），
    # 所以渲染阶段在 C 盘临时目录做，完事把产物拷回项目。
    import shutil
    # 固定 C 盘工作目录：Edge 不认 D 盘的 file://，也避免 TMPDIR 被会话带偏
    stage_root = os.path.join(ROOT, "workspaces", "whiteboard")
    stage = os.path.join(stage_root, os.path.basename(project))
    os.makedirs(stage_root, exist_ok=True)
    if os.path.isdir(wb):
        shutil.copytree(wb, stage, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("engine", "engine_modules", "out"))
    wb = stage

    def step(name, cmd, cwd=None, timeout=1800):
        r = _run(cmd, cwd=cwd, timeout=timeout)
        ok = r.returncode == 0
        steps.append({"step": name, "ok": ok, "tail": (r.stdout or r.stderr or "").strip()[-400:]})
        return ok

    if not os.path.exists(os.path.join(wb, "index.html")):
        step("scaffold", [PY, os.path.join(SKILL, "scripts", "ftnew.py"), wb,
                          "--title", meta["title"], "--style", "whiteboard"], timeout=600)
    step("convert", [PY, os.path.join(HERE, "storyboard_to_frametell.py"), sb, wb], timeout=600)

    # 工程入口模板：ftnew 有时不铺这一步，自己写，避免渲染时报 index.html 缺失
    idx = os.path.join(wb, "index.html")
    if not os.path.exists(idx):
        open(idx, "w", encoding="utf-8").write(
            '<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="engine-modules" content="engine_modules/">\n'
            f'<title>{meta["title"]}</title>\n'
            '<script src="script.js"></script>\n<script src="engine/boot.js"></script>\n'
            '</head>\n<body></body>\n</html>\n')
    step("voice", [PY, os.path.join(SKILL, "scripts", "ftvoice.py"), wb,
                   "--backend", "edge", "--voice", "mature"], timeout=2400)
    step("check", [PY, os.path.join(SKILL, "scripts", "ftcheck.py"), wb], timeout=2400)
    # --workers 2：默认 12 路并发 1080p 会爆内存
    step("render", [NODE, os.path.join(ENGINE, "tools", "render.mjs"),
                    "--fps", "30", "--workers", "2"], cwd=wb, timeout=3600)

    bad = [x for x in steps if not x["ok"]]
    # 把渲染产物拷回项目
    dst_out = os.path.join(project, "wb", "out")
    src_out = os.path.join(wb, "out")
    if os.path.isdir(src_out):
        shutil.copytree(src_out, dst_out, dirs_exist_ok=True)
    meta["stage"] = "whiteboard" if not bad else "whiteboard-failed"
    meta["whiteboard"] = {"project": os.path.join(project, "wb"),
                          "staging": wb, "steps": steps}
    save_meta(project, meta)
    print(json.dumps({"ok": not bad, "whiteboard": wb, "steps": steps}, ensure_ascii=False, indent=2))


def cmd_course(a):
    """长教学分章：每个 part 单独渲染，再用 build_course 拼母版 + 分P + 播放页。"""
    project, meta = load_project(a.project)
    _poly_warn = _polyphone_check(os.path.join(project, "storyboard.json"))
    if _poly_warn and _poly_warn.get("message"):
        if _poly_warn.get("strict"):
            raise SystemExit("多音字高风险未处理（strict）：" + _poly_warn["message"])
        print(f"[polyphone] ⚠️ {_poly_warn['message']}", file=sys.stderr)
    sb = json.load(open(os.path.join(project, "storyboard.json"), encoding="utf-8"))
    parts = sb.get("parts") or []
    if len(parts) < 2:
        raise SystemExit("course 模式需要多个 part（每章一个）")
    segs, rendered = [], []
    for i, part in enumerate(parts, 1):
        pdir = os.path.join(project, "parts", f"p{i:02d}")
        os.makedirs(pdir, exist_ok=True)
        sub = {"title": sb.get("title"), "voice": sb.get("voice"), "parts": [part]}
        sub_sb = os.path.join(pdir, "storyboard.json")
        json.dump(sub, open(sub_sb, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        out = os.path.join(pdir, "build")
        r = _run([PY, os.path.join(HERE, "build_video.py"), sub_sb, out,
                  "--tts", "minimax", "--voice", "Chinese (Mandarin)_Reliable_Executive",
                  "--mm-speed", str(meta["params"]["mm_speed"])])
        if r.returncode != 0:
            raise SystemExit(f"part {i} 渲染失败：{(r.stdout or '')[-600:]}")
        rendered.append(part.get("part"))
        segs += ["--seg", os.path.join(out, "final_hardsub.mp4") + "|" + os.path.join(out, "chapters.json")]

    cmd = [PY, os.path.join(HERE, "build_course.py"), os.path.join(project, "course"), "--no-split"] + segs
    r = _run(cmd, timeout=1800)
    ok = r.returncode == 0
    meta["stage"] = "course" if ok else "course-failed"
    meta["course"] = {"parts": rendered, "tail": (r.stdout or "").strip()[-600:]}
    save_meta(project, meta)
    print(json.dumps({"ok": ok, "parts": len(rendered),
                      "course": os.path.join(project, "course"),
                      "tail": (r.stdout or "").strip()[-500:]}, ensure_ascii=False, indent=2))


def cmd_subs(a):
    """只重烧字幕（不重渲动画），用于调字号/位置。"""
    project, meta = load_project(a.project)
    build = os.path.join(project, "build")
    r = _run([PY, os.path.join(HERE, "reburn_subs.py"), build, a.style,
              os.path.join(build, "final_hardsub.mp4")], timeout=900)
    print(json.dumps({"ok": r.returncode == 0, "style": a.style,
                      "tail": (r.stdout or r.stderr or "").strip()[-400:]}, ensure_ascii=False, indent=2))



def cmd_card(a):
    """Remotion 包装渲染：片头卡 / 标题卡（可做片头、过渡、数据卡）。"""
    project, meta = load_project(a.project)
    out = os.path.join(project, "publish", "card.mp4")
    cmd = [PY, os.path.join(HERE, "remotion_card.py"),
           "--kicker", a.kicker or "", "--main", a.main or meta["title"],
           "--sub", a.sub or "", "--frames", str(int(a.seconds * 30)), "--out", out]
    r = _run(cmd, timeout=1800)
    print(json.dumps({"ok": r.returncode == 0, "card": out,
                      "tail": (r.stdout or r.stderr or "").strip()[-500:]}, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan"); p.add_argument("--mode", choices=list(MODES), required=True)
    p.add_argument("--title", required=True); p.add_argument("--project", required=True)
    p.set_defaults(fn=cmd_plan)

    for name, fn in (("render", cmd_render), ("qa", cmd_qa),
                     ("publish", cmd_publish), ("status", cmd_status),
                     ("whiteboard", cmd_whiteboard), ("course", cmd_course)):
        q = sub.add_parser(name); q.add_argument("--project", required=True)
        if name == "render":
            q.add_argument("--strict-polyphone", action="store_true",
                           help="多音字高风险时拒绝渲染（默认只警告）")
        q.set_defaults(fn=fn)

    q = sub.add_parser("validate"); q.add_argument("--project", required=True)
    q.add_argument("--topic-dir", default=None, help="素材目录（给了就校验 cites 出处）")
    q.add_argument("--strict-polyphone", action="store_true",
                   help="把多音字高风险当成阻断项（默认只警告）")
    q.set_defaults(fn=cmd_validate)

    q = sub.add_parser("verify"); q.add_argument("--project", required=True)
    q.add_argument("--n", type=int, default=8); q.set_defaults(fn=cmd_verify)

    q = sub.add_parser("subs"); q.add_argument("--project", required=True)
    q.add_argument("--style", default="a"); q.set_defaults(fn=cmd_subs)

    q = sub.add_parser("remix"); q.add_argument("--source", required=True)
    q.add_argument("--project", required=True); q.add_argument("--title", default="")
    q.add_argument("--limit", type=int, default=1, help="目录批量模式：本次转录几个（默认 1）")
    q.add_argument("--no-polish", action="store_true", help="跳过转录后的校音工序")
    q.set_defaults(fn=cmd_remix)

    q = sub.add_parser("card"); q.add_argument("--project", required=True)
    q.add_argument("--kicker", default=""); q.add_argument("--main", default="")
    q.add_argument("--sub", default=""); q.add_argument("--seconds", type=float, default=3.0)
    q.set_defaults(fn=cmd_card)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
