/* Video Knowledge Studio · deep knowledge synthesis plugin */
(function (global) {
  const h = (tag, cls, value) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (value != null) node.textContent = String(value);
    return node;
  };

  const clean = (value) => String(value == null ? "" : value).trim();
  const NS = "http://www.w3.org/2000/svg";

  function rich(value) {
    const box = h("span", "kp-rich");
    const text = clean(value);
    const re = /(\*\*[^*]+\*\*|`[^`]+`)/g;
    let at = 0;
    let match;
    while ((match = re.exec(text))) {
      if (match.index > at) box.appendChild(document.createTextNode(text.slice(at, match.index)));
      const token = match[0];
      box.appendChild(token[0] === "`"
        ? h("code", "", token.slice(1, -1))
        : h("strong", "", token.slice(2, -2)));
      at = match.index + token.length;
    }
    if (at < text.length) box.appendChild(document.createTextNode(text.slice(at)));
    return box;
  }

  function section(title, hint, cls) {
    const node = h("section", "kp-section" + (cls ? " " + cls : ""));
    const head = h("div", "kp-head");
    head.appendChild(h("h3", "", title));
    if (hint) head.appendChild(h("small", "", hint));
    node.appendChild(head);
    return node;
  }

  function jumpButton(time, onSeek, label) {
    const button = h("button", "kp-time", label || time || "定位");
    button.type = "button";
    button.onclick = () => onSeek && onSeek(time || 0);
    return button;
  }

  function renderEmpty(lesson, status, onGenerate) {
    const box = h("section", "kp-empty");
    box.dataset.vksKnowledgePlugin = "empty";
    box.appendChild(h("div", "kp-overline", "深度知识总结"));
    box.appendChild(h("h2", "", "这一讲还没有做真正的知识重构"));
    box.appendChild(h("p", "", "生成器会读取完整转录、时间轴、现有笔记和关键画面，先建立证据账本，再重组为核心命题、概念机制、例子、边界、考点与主动回忆。原始字幕只作为可核验证据保留。"));

    if (status && status.state === "running") {
      const progress = h("div", "kp-progress");
      progress.appendChild(h("i"));
      progress.appendChild(h("span", "", status.stage || "正在生成深度知识总结…"));
      box.appendChild(progress);
      return box;
    }
    if (status && status.state === "failed") {
      const warning = h("div", "kp-error", status.error || "生成失败，请重试");
      box.appendChild(warning);
    }

    const actions = h("div", "kp-actions");
    const button = h("button", "kp-primary", status && status.state === "failed" ? "重新生成" : "生成本讲深度笔记");
    button.type = "button";
    button.onclick = () => onGenerate(false);
    actions.appendChild(button);
    actions.appendChild(h("span", "kp-hint", "生成后按集缓存，不重复消耗模型调用"));
    box.appendChild(actions);
    return box;
  }

  function renderHero(note, lesson, onSeek, onGenerate, status) {
    const hero = h("section", "kp-hero");
    hero.dataset.vksKnowledgePlugin = "ready";
    const top = h("div", "kp-topline");
    top.appendChild(h("span", "kp-badge", "深度知识总结"));
    const quality = note.quality || {};
    if (Number.isFinite(Number(quality.coverage))) {
      top.appendChild(h("span", "kp-coverage", "证据覆盖 " + Math.round(Number(quality.coverage) * 100) + "%"));
    }
    if (quality.conceptCount) top.appendChild(h("span", "kp-coverage", quality.conceptCount + " 个核心概念"));
    if (quality.visualEvidenceCount) {
      const reviewed = Number(quality.visualClusters || 0);
      top.appendChild(h("span", "kp-coverage",
        quality.visualEvidenceCount + " 张入选画面" + (reviewed ? " · " + reviewed + " 组已审核" : "")));
    }
    top.appendChild(h("span", "kp-model", note.model || "AI 综合"));
    hero.appendChild(top);

    hero.appendChild(h("div", "kp-kicker", "本讲要回答"));
    hero.appendChild(h("h2", "kp-question", note.centralQuestion || lesson.thesis || lesson.title));
    const thesis = h("div", "kp-bigidea");
    thesis.appendChild(rich(note.bigIdea || lesson.thesis));
    hero.appendChild(thesis);

    const actions = h("div", "kp-actions");
    actions.appendChild(jumpButton(note.mentalModel?.[0]?.time || "", onSeek, "从知识主线开始"));
    const copy = h("button", "kp-secondary", "复制 Markdown");
    copy.type = "button";
    copy.onclick = async () => {
      try {
        await navigator.clipboard.writeText(toMarkdown(note));
        copy.textContent = "已复制";
      } catch (_) {
        copy.textContent = "复制失败";
      }
    };
    actions.appendChild(copy);
    const regen = h("button", "kp-ghost", status && status.state === "running" ? "生成中…" : "重新生成");
    regen.type = "button";
    regen.disabled = !!(status && status.state === "running");
    regen.onclick = () => onGenerate(true);
    actions.appendChild(regen);
    hero.appendChild(actions);
    return hero;
  }

  function renderGoals(note) {
    if (!(note.learningGoals || []).length) return null;
    const node = section("完成后你应该能", "从“看懂”到“能解释、能判断”");
    const list = h("ol", "kp-goals");
    note.learningGoals.forEach((item) => {
      const li = h("li");
      li.appendChild(rich(item));
      list.appendChild(li);
    });
    node.appendChild(list);
    return node;
  }

  function renderMentalModel(note, onSeek) {
    if (!(note.mentalModel || []).length) return null;
    const node = section("一张图看懂知识主线", "不是章节列表，而是问题 → 机制 → 结果");
    const flow = h("div", "kp-flow");
    note.mentalModel.forEach((row, index) => {
      const card = h("article", "kp-flow-step");
      card.appendChild(h("span", "kp-step-no", String(index + 1).padStart(2, "0")));
      card.appendChild(h("h4", "", row.label));
      card.appendChild(h("p", "", row.explain));
      if (row.time) card.appendChild(jumpButton(row.time, onSeek));
      flow.appendChild(card);
      if (index < note.mentalModel.length - 1) flow.appendChild(h("i", "kp-arrow", "→"));
    });
    node.appendChild(flow);
    return node;
  }

  function renderConceptGraph(note, onSeek) {
    const graph = note.conceptGraph || {};
    const nodes = graph.nodes || [];
    const edges = graph.edges || [];
    if (nodes.length < 2 || !edges.length) return null;
    const node = section("概念知识网", "核心概念 + 前置、因果、对比、例子与应用关系");
    const canvas = h("div", "kp-graph");
    const width = 760;
    const height = 390;
    const centerX = width / 2;
    const centerY = height / 2;
    const positions = {};
    const ordered = nodes.slice().sort((a, b) => {
      const rank = { core: 0, mechanism: 1, boundary: 2, application: 3 };
      return (rank[a.role] ?? 9) - (rank[b.role] ?? 9);
    });
    ordered.forEach((row, index) => {
      const angle = -Math.PI / 2 + (Math.PI * 2 * index) / ordered.length;
      const radiusX = Math.min(285, 125 + ordered.length * 22);
      const radiusY = Math.min(145, 82 + ordered.length * 9);
      positions[row.conceptTitle] = {
        x: centerX + Math.cos(angle) * radiusX,
        y: centerY + Math.sin(angle) * radiusY,
      };
    });

    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("class", "kp-graph-edges");
    svg.setAttribute("viewBox", "0 0 " + width + " " + height);
    svg.setAttribute("aria-hidden", "true");
    const defs = document.createElementNS(NS, "defs");
    const marker = document.createElementNS(NS, "marker");
    marker.setAttribute("id", "kp-arrow");
    marker.setAttribute("viewBox", "0 0 10 10");
    marker.setAttribute("refX", "9");
    marker.setAttribute("refY", "5");
    marker.setAttribute("markerWidth", "5");
    marker.setAttribute("markerHeight", "5");
    marker.setAttribute("orient", "auto-start-reverse");
    const markerPath = document.createElementNS(NS, "path");
    markerPath.setAttribute("d", "M 0 0 L 10 5 L 0 10 z");
    markerPath.setAttribute("fill", "currentColor");
    marker.appendChild(markerPath);
    defs.appendChild(marker);
    svg.appendChild(defs);

    edges.forEach((edge, index) => {
      const left = positions[edge.from];
      const right = positions[edge.to];
      if (!left || !right) return;
      const path = document.createElementNS(NS, "path");
      const midX = (left.x + right.x) / 2;
      const midY = (left.y + right.y) / 2;
      const bend = ((index % 5) - 2) * 14;
      path.setAttribute(
        "d",
        "M " + left.x + " " + left.y +
        " Q " + (midX + bend) + " " + (midY - bend) +
        " " + right.x + " " + right.y
      );
      path.setAttribute("class", "kp-graph-edge edge-" + clean(edge.type));
      path.setAttribute("marker-end", "url(#kp-arrow)");
      const title = document.createElementNS(NS, "title");
      title.textContent = edge.from + " → " + edge.to + "：" + (edge.explain || edge.type);
      path.appendChild(title);
      svg.appendChild(path);
    });
    canvas.appendChild(svg);

    ordered.forEach((row) => {
      const at = positions[row.conceptTitle];
      const concept = (note.concepts || []).find((item) => item.title === row.conceptTitle);
      const time = concept?.evidence?.[0]?.time || "";
      const card = h("button", "kp-graph-node role-" + clean(row.role));
      card.type = "button";
      card.style.left = (at.x / width) * 100 + "%";
      card.style.top = (at.y / height) * 100 + "%";
      card.appendChild(h("b", "", row.conceptTitle));
      card.appendChild(h("small", "", row.summary || row.role));
      if (time) card.appendChild(h("span", "", time));
      card.onclick = () => onSeek && onSeek(time);
      canvas.appendChild(card);
    });

    const legend = h("div", "kp-graph-legend");
    [
      ["prerequisite", "前置"],
      ["mechanism", "机制"],
      ["cause", "因果"],
      ["contrast", "对比"],
      ["example", "例子"],
      ["application", "应用"],
      ["grouping", "体系分支"],
    ].forEach(([type, label]) => {
      const item = h("span");
      item.appendChild(h("i", "edge-" + type));
      item.appendChild(document.createTextNode(label));
      legend.appendChild(item);
    });
    canvas.appendChild(legend);
    node.appendChild(canvas);
    return node;
  }

  function renderCourseSystem(graph, onOpenEpisode) {
    if (!graph || !(graph.nodes || []).length) return null;
    const details = h("details", "kp-section kp-course-system");
    const summary = h("summary", "kp-head");
    summary.appendChild(h("h3", "", "全课程知识体系"));
    summary.appendChild(h("small", "",
      (graph.stats?.episodes || 0) + " 讲 · " +
      (graph.stats?.canonicalConcepts || graph.nodes.length) + " 个规范概念 · " +
      (graph.stats?.edges || 0) + " 条关系"
    ));
    details.appendChild(summary);
    const byId = Object.fromEntries((graph.nodes || []).map((row) => [row.id, row]));
    const flow = h("div", "kp-course-flow");
    (graph.chapters || []).forEach((chapter, index) => {
      const card = h("article", "kp-course-chapter");
      card.appendChild(h("span", "kp-step-no", String(index + 1).padStart(2, "0")));
      card.appendChild(h("h4", "", chapter.label));
      card.appendChild(h("p", "", (chapter.episodes || []).length + " 讲 · " + (chapter.conceptIds || []).length + " 个概念节点"));
      const tags = h("div", "kp-course-tags");
      (chapter.conceptIds || []).map((id) => byId[id]).filter(Boolean).slice(0, 5)
        .forEach((row) => tags.appendChild(h("span", "", row.label)));
      card.appendChild(tags);
      const open = h("button", "kp-time", "打开第 " + (chapter.episodes?.[0] ?? "?") + " 讲");
      open.type = "button";
      open.onclick = () => {
        if (chapter.episodes?.[0] != null && onOpenEpisode) {
          const episode = chapter.episodes[0];
          const node = (graph.nodes || [])
            .flatMap((row) => row.occurrences || [])
            .find((row) => row.episode === episode);
          if (node?.episodeId) onOpenEpisode(node.episodeId);
        }
      };
      card.appendChild(open);
      flow.appendChild(card);
      if (index < graph.chapters.length - 1) flow.appendChild(h("i", "kp-arrow", "→"));
    });
    details.appendChild(flow);
    const indexDetails = h("details", "kp-course-index");
    indexDetails.appendChild(h("summary", "", "展开全部概念索引"));
    (graph.chapters || []).forEach((chapter) => {
      const group = h("details", "kp-course-group");
      group.appendChild(h("summary", "", chapter.label + " · " + (chapter.conceptIds || []).length + " 个概念"));
      const list = h("div", "kp-course-concept-list");
      (chapter.conceptIds || []).map((id) => byId[id]).filter(Boolean).forEach((row) => {
        const item = h("div");
        item.appendChild(h("b", "", row.label));
        const episodes = Array.from(new Set((row.occurrences || []).map((x) => x.episode))).sort((a, b) => a - b);
        item.appendChild(h("small", "", episodes.length ? "出现于 " + episodes.map((x) => "E" + String(x).padStart(2, "0")).join("、") : ""));
        list.appendChild(item);
      });
      group.appendChild(list);
      indexDetails.appendChild(group);
    });
    details.appendChild(indexDetails);
    return details;
  }

  function renderSemanticReview(review, onSeek) {
    if (!review) return null;
    const status = clean(review.status || "missing");
    const decision = clean(review.decision || "pending");
    const node = section("独立语义复核", "新上下文审校，不复用写作过程");
    const badge = h("div", "kp-review-status status-" + status + " decision-" + decision);
    const labels = {
      valid: decision === "pass" ? "当前版本已通过" : "当前版本未通过",
      stale: "上一轮复核已失效",
      missing: "尚未复核",
    };
    badge.appendChild(h("b", "", labels[status] || "复核状态未知"));
    if (review.coverage != null) {
      badge.appendChild(h("span", "", "证据覆盖 " + Math.round(Number(review.coverage) * 100) + "%"));
    }
    if (review.omissionCount != null) {
      badge.appendChild(h("span", "", review.omissionCount + " 条审校意见"));
    }
    if (review.blockingCount) {
      badge.appendChild(h("span", "blocking", review.blockingCount + " 条待修复"));
    }
    node.appendChild(badge);
    if (review.message) node.appendChild(h("p", "kp-review-message", review.message));
    if (review.summary) node.appendChild(h("p", "kp-review-summary", review.summary));
    const blocking = (review.omissions || []).filter((row) =>
      ["high", "medium"].includes(clean(row.severity))
    );
    if (blocking.length) {
      const list = h("div", "kp-review-issues");
      blocking.slice(0, 8).forEach((row) => {
        const item = h("article", "kp-review-issue severity-" + clean(row.severity));
        const head = h("div");
        head.appendChild(h("b", "", clean(row.kind || "issue")));
        if (row.time) head.appendChild(jumpButton(row.time, onSeek));
        item.appendChild(head);
        item.appendChild(h("p", "", clean(row.issue)));
        if (row.suggestedRepair) {
          item.appendChild(h("small", "", "修复建议：" + clean(row.suggestedRepair)));
        }
        list.appendChild(item);
      });
      node.appendChild(list);
    }
    return node;
  }

  function renderEvidence(rows, onSeek) {
    const list = h("div", "kp-evidence-list");
    (rows || []).forEach((row) => {
      const box = h("div", "kp-evidence");
      box.appendChild(jumpButton(row.time, onSeek));
      const body = h("div");
      body.appendChild(h("b", "", row.reason || "视频证据"));
      if (row.quote) body.appendChild(h("q", "", row.quote));
      box.appendChild(body);
      list.appendChild(box);
    });
    return list;
  }

  function renderConcepts(note, onSeek) {
    const node = section("核心概念", "定义、机制、例子、边界、误区与证据放在一起");
    (note.concepts || []).forEach((concept, index) => {
      const card = h("article", "kp-concept");
      const head = h("div", "kp-concept-head");
      head.appendChild(h("span", "kp-concept-no", String(index + 1).padStart(2, "0")));
      const title = h("div");
      title.appendChild(h("h4", "", concept.title));
      title.appendChild(h("p", "kp-one-line", concept.oneLine));
      head.appendChild(title);
      card.appendChild(head);
      const explain = h("div", "kp-explain");
      explain.appendChild(rich(concept.explain));
      card.appendChild(explain);

      if ((concept.mechanism || []).length) {
        const mechanism = h("div", "kp-block");
        mechanism.appendChild(h("b", "", "怎么发生"));
        const list = h("ol", "kp-mechanism");
        concept.mechanism.forEach((item) => list.appendChild(h("li", "", item)));
        mechanism.appendChild(list);
        card.appendChild(mechanism);
      }
      const grid = h("div", "kp-concept-grid");
      if (concept.example) {
        const row = h("div", "kp-mini example");
        row.appendChild(h("b", "", "最小例子"));
        row.appendChild(h("p", "", concept.example));
        grid.appendChild(row);
      }
      if (concept.boundary) {
        const row = h("div", "kp-mini boundary");
        row.appendChild(h("b", "", "适用边界"));
        row.appendChild(h("p", "", concept.boundary));
        grid.appendChild(row);
      }
      if (concept.misconception) {
        const row = h("div", "kp-mini trap");
        row.appendChild(h("b", "", "常见误区"));
        row.appendChild(h("p", "", concept.misconception));
        grid.appendChild(row);
      }
      if (grid.children.length) card.appendChild(grid);
      if ((concept.evidence || []).length) {
        const details = h("details", "kp-evidence-details");
        details.appendChild(h("summary", "", "核对原片证据 · " + concept.evidence.length + " 处"));
        details.appendChild(renderEvidence(concept.evidence, onSeek));
        card.appendChild(details);
      }
      node.appendChild(card);
    });
    return node;
  }

  function renderComparisons(note) {
    if (!(note.comparisons || []).length) return null;
    const node = section("对比与判定", "把容易混淆的概念放在同一张表里");
    const wrap = h("div", "kp-table-wrap");
    const table = h("table", "kp-table");
    const head = h("tr");
    ["维度", "对象 A", "对象 B", "关键差异"].forEach((label) => head.appendChild(h("th", "", label)));
    const thead = h("thead");
    thead.appendChild(head);
    table.appendChild(thead);
    const body = h("tbody");
    note.comparisons.forEach((row) => {
      const tr = h("tr");
      [row.dimension, row.left, row.right, row.difference].forEach((value) => tr.appendChild(h("td", "", value)));
      body.appendChild(tr);
    });
    table.appendChild(body);
    wrap.appendChild(table);
    node.appendChild(wrap);
    return node;
  }

  function renderFormulas(note) {
    if (!(note.formulas || []).length) return null;
    const node = section("公式与条件", "公式、含义、适用条件必须同时出现");
    note.formulas.forEach((row) => {
      const card = h("article", "kp-formula");
      card.appendChild(h("code", "", row.expression));
      card.appendChild(h("p", "", row.meaning));
      card.appendChild(h("small", "", "适用条件：" + row.conditions));
      node.appendChild(card);
    });
    return node;
  }

  function renderExam(note, onSeek) {
    if (!(note.examPoints || []).length && !(note.uncertainties || []).length) return null;
    const node = section("考点、易错点与待核", "视频强调与证据边界分开标注");
    (note.examPoints || []).forEach((row) => {
      const card = h("article", "kp-exam");
      const top = h("div");
      top.appendChild(h("b", "", row.point));
      if (row.time) top.appendChild(jumpButton(row.time, onSeek));
      card.appendChild(top);
      card.appendChild(h("p", "", row.reason));
      node.appendChild(card);
    });
    if ((note.uncertainties || []).length) {
      const warning = h("div", "kp-uncertain");
      warning.appendChild(h("b", "", "待核 / ASR 不确定"));
      const list = h("ul");
      note.uncertainties.forEach((item) => list.appendChild(h("li", "", item)));
      warning.appendChild(list);
      node.appendChild(warning);
    }
    return node;
  }

  function renderRecall(note, onSeek) {
    if (!(note.recall || []).length) return null;
    const node = section("主动回忆", "先回答，再展开；问题必须要求解释或应用");
    note.recall.forEach((row, index) => {
      const details = h("details", "kp-recall");
      const summary = h("summary");
      summary.appendChild(h("span", "", "问题 " + (index + 1)));
      summary.appendChild(h("b", "", row.question));
      if (row.time) summary.appendChild(jumpButton(row.time, onSeek));
      details.appendChild(summary);
      details.appendChild(h("p", "", row.answer));
      node.appendChild(details);
    });
    return node;
  }

  function renderCoverage(note, onSeek) {
    if (!(note.coverage || []).length) return null;
    const details = h("details", "kp-section kp-coverage-details");
    const summary = h("summary", "kp-head");
    summary.appendChild(h("h3", "", "完整字幕覆盖账本"));
    summary.appendChild(h("small", "",
      (note.quality?.coverageBlocks || note.coverage.length) + " 块全部有归属"
    ));
    details.appendChild(summary);
    const list = h("div", "kp-coverage-list");
    note.coverage.forEach((row) => {
      const item = h("div", "kp-coverage-row");
      item.appendChild(jumpButton(row.time || (row.start + "–" + row.end), onSeek, row.start + "–" + row.end));
      const body = h("div");
      const title = h("b", "", row.topic);
      if (row.status) title.appendChild(h("span", "kp-audit-status", " · " + row.status));
      body.appendChild(title);
      if ((row.keyPoints || []).length) {
        const points = h("ul", "kp-block-points");
        row.keyPoints.forEach((point) => points.appendChild(h("li", "", point)));
        body.appendChild(points);
      }
      if ((row.conceptTitles || []).length) body.appendChild(h("p", "", "对应：" + row.conceptTitles.join(" · ")));
      if (row.exclusionReason) body.appendChild(h("p", "kp-audit-reason", "判定：" + row.exclusionReason));
      item.appendChild(body);
      list.appendChild(item);
    });
    details.appendChild(list);
    return details;
  }

  function renderVisual(note, lesson, onSeek) {
    if (!(note.visualEvidence || []).length) return null;
    const node = section(
      "画面补充了什么",
      (note.quality?.visualClusters || note.visualEvidence.length) + " 组画面已进入笔记"
    );
    const grid = h("div", "kp-visual-grid");
    note.visualEvidence.forEach((row) => {
      const card = h("article", "kp-visual");
      if (row.file) {
        const img = h("img");
        img.loading = "lazy";
        img.src = "/media/knowledge-frame?id=" + encodeURIComponent(lesson.id || "") + "&file=" + encodeURIComponent(row.file);
        img.alt = row.caption || "关键画面";
        card.appendChild(img);
      }
      const body = h("div");
      const top = h("div", "kp-visual-top");
      top.appendChild(h("b", "", row.caption || "关键画面"));
      if (row.time) top.appendChild(jumpButton(row.time, onSeek));
      body.appendChild(top);
      body.appendChild(h("p", "", row.whatItAdds));
      if ((row.ocr || []).length) {
        const details = h("details");
        details.appendChild(h("summary", "", "画面 OCR"));
        details.appendChild(h("p", "", row.ocr.join(" · ")));
        body.appendChild(details);
      }
      card.appendChild(body);
      grid.appendChild(card);
    });
    node.appendChild(grid);
    return node;
  }

  function renderVisualAudit(note, onSeek) {
    const rows = note.visualAudit || [];
    if (!rows.length) return null;
    const details = h("details", "kp-section kp-visual-audit");
    const summary = h("summary", "kp-head");
    summary.appendChild(h("h3", "", "画面审核账本"));
    summary.appendChild(h("small", "",
      rows.length + " 帧全部有决定 · " +
      (note.quality?.includedVisualClusters || 0) + " 组进入笔记"
    ));
    details.appendChild(summary);
    const list = h("div", "kp-audit-list");
    rows.forEach((row) => {
      const item = h("div", "kp-audit-row decision-" + clean(row.decision));
      item.appendChild(jumpButton(row.time, onSeek));
      const body = h("div");
      body.appendChild(h("b", "", row.candidateId + " · " + row.clusterId + " · " + row.decision));
      body.appendChild(h("p", "", row.reason || ""));
      if (row.caption) body.appendChild(h("small", "", row.caption));
      item.appendChild(body);
      list.appendChild(item);
    });
    details.appendChild(list);
    return details;
  }

  function renderGlossary(note, onSeek) {
    if (!(note.glossary || []).length) return null;
    const node = section("术语速查", "首次出现、人话解释和最小例子");
    const wrap = h("div", "kp-table-wrap");
    const table = h("table", "kp-table");
    const thead = h("thead");
    const tr = h("tr");
    ["术语", "人话解释", "最小例子", "首次出现"].forEach((x) => tr.appendChild(h("th", "", x)));
    thead.appendChild(tr);
    table.appendChild(thead);
    const tbody = h("tbody");
    note.glossary.forEach((row) => {
      const line = h("tr");
      line.appendChild(h("td", "kp-term", row.term));
      line.appendChild(h("td", "", row.plain));
      line.appendChild(h("td", "", row.example));
      const last = h("td");
      last.appendChild(jumpButton(row.time, onSeek));
      line.appendChild(last);
      tbody.appendChild(line);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    node.appendChild(wrap);
    return node;
  }

  function render(host, options) {
    const opt = options || {};
    const lesson = opt.lesson || {};
    const note = opt.note;
    const status = opt.status || {};
    const courseGraph = opt.courseGraph || null;
    const onSeek = opt.onSeek || (() => {});
    const onGenerate = opt.onGenerate || (() => {});
    const onOpenEpisode = opt.onOpenEpisode || (() => {});
    host.innerHTML = "";
    host.className = "kp-root";
    if (!note) {
      host.appendChild(renderEmpty(lesson, status, onGenerate));
      return host;
    }

    host.appendChild(renderHero(note, lesson, onSeek, onGenerate, status));
    [
      renderSemanticReview(note.semanticReview, onSeek),
      renderGoals(note),
      renderMentalModel(note, onSeek),
      renderConceptGraph(note, onSeek),
      renderCourseSystem(courseGraph, onOpenEpisode),
      renderConcepts(note, onSeek),
      renderComparisons(note),
      renderFormulas(note),
      renderExam(note, onSeek),
      renderRecall(note, onSeek),
      renderGlossary(note, onSeek),
      renderCoverage(note, onSeek),
      renderVisual(note, lesson, onSeek),
      renderVisualAudit(note, onSeek),
    ].forEach((node) => {
      if (node) host.appendChild(node);
    });

    const footer = h("div", "kp-footer");
    footer.appendChild(h("span", "", "生成时间 " + (note.generatedAt || "未知")));
    footer.appendChild(h("span", "", "模型 " + (note.model || "当前推理模型")));
    if (note.quality?.warnings?.length) {
      footer.appendChild(h("span", "warn", note.quality.warnings.join(" · ")));
    }
    host.appendChild(footer);
    return host;
  }

  async function generate(lesson, options) {
    const opt = options || {};
    const onProgress = opt.onProgress || (() => {});
    const force = !!opt.force;
    onProgress({ state: "running", stage: "提交深度总结任务" });
    const startedResponse = await fetch("/api/knowledge/deep", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: lesson.id, force }),
    });
    const started = await startedResponse.json();
    if (!started.ok) throw new Error(started.error || "无法启动深度总结");
    if (started.cached && started.note) return started.note;
    const job = started.job;
    if (!job) throw new Error("深度总结任务没有返回 job id");

    for (let attempt = 0; attempt < 600; attempt++) {
      await new Promise((resolve) => setTimeout(resolve, 1200));
      const response = await fetch("/api/knowledge/deep/job?id=" + encodeURIComponent(job));
      const payload = await response.json();
      if (!payload.ok) throw new Error(payload.error || "无法读取深度总结进度");
      onProgress({ state: payload.status === "done" ? "done" : "running", stage: payload.stage || "生成中" });
      if (payload.status === "done") {
        if (payload.note) return payload.note;
        const cached = await fetch("/api/knowledge/deep?id=" + encodeURIComponent(lesson.id));
        const result = await cached.json();
        if (result.ok && result.note) return result.note;
        throw new Error("任务完成但没有找到缓存笔记");
      }
      if (payload.status === "failed") throw new Error(payload.error || "深度总结生成失败");
    }
    throw new Error("深度总结生成超时");
  }

  function toMarkdown(note) {
    const rows = [];
    rows.push("# " + clean(note.title || "视频知识总结"));
    rows.push("");
    rows.push("> **中心问题**：" + clean(note.centralQuestion));
    rows.push("");
    rows.push("> **核心命题**：" + clean(note.bigIdea));
    if ((note.learningGoals || []).length) {
      rows.push("", "## 学习目标");
      note.learningGoals.forEach((x) => rows.push("- " + clean(x)));
    }
    if ((note.mentalModel || []).length) {
      rows.push("", "## 知识主线");
      note.mentalModel.forEach((x, i) => rows.push((i + 1) + ". **" + clean(x.label) + "** `" + clean(x.time) + "` — " + clean(x.explain)));
    }
    if ((note.conceptGraph?.edges || []).length) {
      rows.push("", "## 概念知识网");
      note.conceptGraph.edges.forEach((edge) => {
        rows.push("- **" + clean(edge.from) + " → " + clean(edge.to) + "** [" + clean(edge.type) + "] `" + clean(edge.time) + "` — " + clean(edge.explain));
      });
    }
    (note.concepts || []).forEach((concept, index) => {
      rows.push("", "## " + (index + 1) + ". " + clean(concept.title));
      rows.push("", "**一句话**：" + clean(concept.oneLine));
      rows.push("", clean(concept.explain));
      if (concept.mechanism?.length) {
        rows.push("");
        concept.mechanism.forEach((x, i) => rows.push((i + 1) + ". " + clean(x)));
      }
      if (concept.example) rows.push("", "**例子**：" + clean(concept.example));
      if (concept.boundary) rows.push("", "**边界**：" + clean(concept.boundary));
      if (concept.misconception) rows.push("", "**误区**：" + clean(concept.misconception));
      (concept.evidence || []).forEach((x) => rows.push("", `- [${clean(x.time)}] ${clean(x.reason)}${x.quote ? "\n  > " + clean(x.quote) : ""}`));
    });
    if ((note.examPoints || []).length) {
      rows.push("", "## 考点与易错");
      note.examPoints.forEach((x) => rows.push("- `" + clean(x.time) + "` **" + clean(x.point) + "** — " + clean(x.reason)));
    }
    if ((note.comparisons || []).length) {
      rows.push("", "## 对比与判定", "", "| 维度 | 对象 A | 对象 B | 关键差异 |", "|---|---|---|---|");
      note.comparisons.forEach((x) => rows.push("| " + [x.dimension, x.left, x.right, x.difference].map(clean).join(" | ") + " |"));
    }
    if ((note.formulas || []).length) {
      rows.push("", "## 公式与条件");
      note.formulas.forEach((x) => rows.push("- `" + clean(x.expression) + "` — " + clean(x.meaning) + "（条件：" + clean(x.conditions) + "）"));
    }
    if ((note.recall || []).length) {
      rows.push("", "## 主动回忆");
      note.recall.forEach((x) => rows.push("", "### " + clean(x.question), "", clean(x.answer)));
    }
    if ((note.glossary || []).length) {
      rows.push("", "## 术语速查", "", "| 术语 | 人话解释 | 例子 | 首次出现 |", "|---|---|---|---|");
      note.glossary.forEach((x) => rows.push("| " + [x.term, x.plain, x.example, x.time].map(clean).join(" | ") + " |"));
    }
    if ((note.coverage || []).length) {
      rows.push("", "## 完整字幕覆盖账本");
      note.coverage.forEach((x) => {
        rows.push("- `" + clean(x.start) + "–" + clean(x.end) + "` **" + clean(x.topic) + "** [" + clean(x.status) + "]");
        (x.keyPoints || []).forEach((point) => rows.push("  - " + clean(point)));
      });
    }
    if ((note.visualAudit || []).length) {
      rows.push("", "## 画面审核账本");
      note.visualAudit.forEach((x) => rows.push(
        "- `" + clean(x.time) + "` " + clean(x.candidateId) + " / " + clean(x.clusterId) +
        " **" + clean(x.decision) + "** — " + clean(x.reason)
      ));
    }
    if (note.quality?.warnings?.length) {
      rows.push("", "## 质量提醒");
      note.quality.warnings.forEach((x) => rows.push("- " + clean(x)));
    }
    return rows.join("\n");
  }

  const api = { render, generate, toMarkdown };
  global.VKSKnowledgePlugin = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
