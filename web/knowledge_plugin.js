/* Video Knowledge Studio · deep knowledge synthesis plugin */
(function (global) {
  const h = (tag, cls, value) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (value != null) node.textContent = String(value);
    return node;
  };

  const clean = (value) => String(value == null ? "" : value).trim();

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
    summary.appendChild(h("h3", "", "全片知识覆盖账本"));
    summary.appendChild(h("small", "", "证明内容不是只抓了开头几段"));
    details.appendChild(summary);
    const list = h("div", "kp-coverage-list");
    note.coverage.forEach((row) => {
      const item = h("div", "kp-coverage-row");
      item.appendChild(jumpButton(row.time || (row.start + "–" + row.end), onSeek, row.start + "–" + row.end));
      const body = h("div");
      body.appendChild(h("b", "", row.topic));
      if ((row.conceptTitles || []).length) body.appendChild(h("p", "", "对应：" + row.conceptTitles.join(" · ")));
      item.appendChild(body);
      list.appendChild(item);
    });
    details.appendChild(list);
    return details;
  }

  function renderVisual(note, lesson, onSeek) {
    if (!(note.visualEvidence || []).length) return null;
    const node = section("画面补充了什么", "只保留文字之外的板书、流程、图表与界面证据");
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
    const onSeek = opt.onSeek || (() => {});
    const onGenerate = opt.onGenerate || (() => {});
    host.innerHTML = "";
    host.className = "kp-root";
    if (!note) {
      host.appendChild(renderEmpty(lesson, status, onGenerate));
      return host;
    }

    host.appendChild(renderHero(note, lesson, onSeek, onGenerate, status));
    [
      renderGoals(note),
      renderMentalModel(note, onSeek),
      renderConcepts(note, onSeek),
      renderComparisons(note),
      renderFormulas(note),
      renderExam(note, onSeek),
      renderRecall(note, onSeek),
      renderGlossary(note, onSeek),
      renderCoverage(note, onSeek),
      renderVisual(note, lesson, onSeek),
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
      rows.push("", "## 全片知识覆盖");
      note.coverage.forEach((x) => rows.push("- `" + clean(x.start) + "–" + clean(x.end) + "` **" + clean(x.topic) + "**"));
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
