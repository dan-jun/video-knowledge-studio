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
  const ATOM_KINDS = {
    definition: "定义",
    mechanism: "机制",
    cause: "因果",
    comparison: "对比",
    example: "例子",
    formula: "公式",
    boundary: "边界",
    uncertain: "待核",
    closure: "收束",
    claim: "要点",
  };
  const RELATION_LABELS = {
    prerequisite: "前置",
    mechanism: "机制",
    cause: "因果",
    contrast: "对比",
    example: "例子",
    application: "应用",
    grouping: "体系分支",
  };
  const MIND_COLORS = ["#58d8f2", "#67dfb2", "#f0c36d", "#ef9388", "#ae94ef", "#7ca8f2", "#9bb1bb"];

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

  function masteryKey(lesson) {
    return "vks.mastery." + clean(
      (lesson && (lesson.id || lesson.episodeId)) || "unknown"
    );
  }

  function loadMastery(lesson) {
    try {
      return JSON.parse(localStorage.getItem(masteryKey(lesson)) || "{}") || {};
    } catch (_) {
      return {};
    }
  }

  function saveMastery(lesson, value) {
    try {
      localStorage.setItem(masteryKey(lesson), JSON.stringify(value));
    } catch (_) {
      // Local storage can be unavailable in restricted browser contexts.
    }
  }

  function masteryControl(key, store, lesson, onChange) {
    const box = h("div", "kp-mastery");
    box.setAttribute("aria-label", "掌握度");
    box.dataset.masteryKey = key;
    [
      ["known", "会"],
      ["fuzzy", "模糊"],
      ["unknown", "不会"],
    ].forEach(([state, label]) => {
      const button = h("button", "kp-mastery-btn", label);
      button.type = "button";
      button.dataset.state = state;
      if (store[key] === state) button.classList.add("active");
      button.onclick = (event) => {
        event.stopPropagation();
        store[key] = state;
        saveMastery(lesson, store);
        document.querySelectorAll(".kp-mastery").forEach((control) => {
          if (control.dataset.masteryKey !== key) return;
          control.querySelectorAll(".kp-mastery-btn").forEach((item) => {
            item.classList.toggle("active", item.dataset.state === state);
          });
        });
        if (onChange) onChange();
      };
      box.appendChild(button);
    });
    return box;
  }

  function episodeTarget(courseGraph, row) {
    if (!row) return "";
    if (row.episodeId) return clean(row.episodeId);
    const episode = Number(row.episode);
    if (!Number.isFinite(episode)) return "";
    const lesson = (courseGraph?.lessons || []).find(
      (item) => Number(item.episode) === episode && item.episodeId
    );
    if (lesson?.episodeId) return clean(lesson.episodeId);
    const course = clean(courseGraph?.course);
    if (course.includes("操作系统")) {
      return "os-course-e" + String(episode).padStart(2, "0");
    }
    return "";
  }

  function relatedEpisodes(courseGraph, titles, currentEpisode) {
    if (!courseGraph || !(titles || []).length) return [];
    const titleSet = new Set(titles);
    const current = Number(currentEpisode);
    const found = new Map();
    (courseGraph.nodes || []).forEach((node) => {
      if (!titleSet.has(node.label)) return;
      (node.occurrences || []).forEach((occurrence) => {
        if (!occurrence || Number(occurrence.episode) === current) return;
        const target = episodeTarget(courseGraph, occurrence);
        if (target) found.set(target, { ...occurrence, episodeId: target });
      });
    });
    return [...found.values()]
      .sort((a, b) => Number(a.episode || 0) - Number(b.episode || 0))
      .slice(0, 8);
  }

  function relatedEpisodeLinks(courseGraph, titles, currentEpisode, onOpenEpisode) {
    const rows = relatedEpisodes(courseGraph, titles, currentEpisode);
    if (!rows.length) return null;
    const box = h("div", "kp-related");
    box.appendChild(h("span", "", "跨讲关联"));
    rows.forEach((row) => {
      const button = h("button", "kp-related-link",
        "E" + String(row.episode).padStart(2, "0"));
      button.type = "button";
      button.title = row.episodeTitle || row.episodeId;
      button.onclick = (event) => {
        event.stopPropagation();
        if (onOpenEpisode) onOpenEpisode(row.episodeId);
      };
      box.appendChild(button);
    });
    return box;
  }

  function atomLeaf(atom, fallback) {
    const row = atom || {};
    const extra = fallback || {};
    const title = clean(row.title || row.label || row.claim || row.atomId || row.id || "知识原子");
    const claim = clean(row.claim || row.detail || "");
    return {
      id: clean(row.atomId || row.id || ""),
      title,
      detail: claim && claim !== title ? claim : "",
      time: clean(row.time || ""),
      start: Number.isFinite(Number(row.start)) ? Number(row.start) : null,
      kind: clean(row.kind || "claim"),
      episodeId: clean(row.episodeId || extra.episodeId || ""),
      conceptTitles: (row.conceptTitles || extra.conceptTitles || []).map(clean).filter(Boolean),
    };
  }

  function buildEpisodeMindMap(note) {
    const source = note || {};
    const graphNodes = (source.conceptGraph?.nodes || []).slice();
    const rank = { core: 0, mechanism: 1, boundary: 2, application: 3 };
    graphNodes.sort((left, right) => (
      (rank[left.role] ?? 9) - (rank[right.role] ?? 9)
    ));
    const conceptsByTitle = Object.fromEntries(
      (source.concepts || []).map((row) => [clean(row.title), row])
    );
    const edges = source.conceptGraph?.edges || [];
    const branches = [];
    const byTitle = new Map();
    const ensureBranch = (title, graphNode) => {
      const name = clean(title) || "补充知识";
      if (byTitle.has(name)) return byTitle.get(name);
      const concept = conceptsByTitle[name] || {};
      const branch = {
        title: name,
        subtitle: clean(graphNode?.summary || concept.oneLine || ""),
        role: clean(graphNode?.role || "detail"),
        relations: [],
        leaves: [],
      };
      byTitle.set(name, branch);
      branches.push(branch);
      return branch;
    };
    graphNodes.forEach((row) => ensureBranch(row.conceptTitle, row));
    (source.knowledgeAtoms || []).forEach((atom) => {
      const titles = (atom.conceptTitles || []).map(clean).filter(Boolean);
      const matched = titles.find((title) => byTitle.has(title));
      const title = matched || titles[0] || clean(atom.topic) || "补充知识";
      ensureBranch(title, graphNodes.find((row) => clean(row.conceptTitle) === title))
        .leaves.push(atomLeaf(atom, { episodeId: source.episodeId }));
    });
    branches.forEach((branch) => {
      const relations = new Set();
      edges.forEach((edge) => {
        if (clean(edge.from) !== branch.title && clean(edge.to) !== branch.title) return;
        relations.add(RELATION_LABELS[clean(edge.type)] || clean(edge.type) || "关系");
      });
      branch.relations = Array.from(relations);
      branch.meta = branch.leaves.length + " 原子" +
        (branch.relations.length ? " · " + branch.relations.slice(0, 3).join(" / ") : "");
    });
    return {
      kind: "episode",
      root: {
        kicker: "本讲",
        title: clean(source.title || source.centralQuestion || "本讲知识"),
        subtitle: clean(source.centralQuestion || source.bigIdea || ""),
        meta: (source.knowledgeAtoms || []).length + " 个知识原子 · " +
          graphNodes.length + " 个核心锚点 · " + edges.length + " 条关系",
      },
      branches,
      leafCount: (source.knowledgeAtoms || []).length,
    };
  }

  function buildChapterMindMap(chapter, courseGraph) {
    const source = chapter || {};
    const graph = courseGraph || {};
    const nodesById = Object.fromEntries((graph.nodes || []).map((row) => [clean(row.id), row]));
    const atomsById = Object.fromEntries(
      (graph.knowledgeAtoms || []).map((row) => [clean(row.id || row.atomId), row])
    );
    const lessonsById = Object.fromEntries((graph.lessons || []).map((row) => [clean(row.id), row]));
    let lessons = (source.lessonIds || []).map((id) => lessonsById[clean(id)]).filter(Boolean);
    if (!lessons.length) {
      lessons = (graph.lessons || []).filter((row) => clean(row.chapterId) === clean(source.id));
    }
    lessons.sort((left, right) => Number(left.episode || 0) - Number(right.episode || 0));
    const usedAtoms = new Set();
    const branches = lessons.map((lesson) => {
      const lessonId = clean(lesson.id);
      let rows = (lesson.knowledgeAtomIds || [])
        .map((id) => atomsById[clean(id)])
        .filter(Boolean);
      if (!rows.length) {
        rows = (graph.knowledgeAtoms || []).filter((atom) => (
          clean(atom.lessonId) === lessonId ||
          Number(atom.episode) === Number(lesson.episode)
        ));
      }
      rows = rows.filter((atom) => !usedAtoms.has(clean(atom.id || atom.atomId)));
      const titles = (lesson.conceptIds || [])
        .map((id) => clean(nodesById[clean(id)]?.label || id))
        .filter(Boolean);
      const target = episodeTarget(graph, lesson);
      const leaves = rows.map((atom) => {
        const id = clean(atom.id || atom.atomId);
        if (id) usedAtoms.add(id);
        return atomLeaf(atom, { episodeId: target, conceptTitles: titles });
      });
      return {
        title: Number.isFinite(Number(lesson.episode))
          ? "E" + String(Number(lesson.episode)).padStart(2, "0")
          : lessonId,
        subtitle: clean(lesson.label || lesson.title || lessonId),
        meta: leaves.length + " 原子" + (titles.length ? " · " + titles.slice(0, 3).join(" / ") : ""),
        relations: titles.slice(0, 3),
        leaves,
      };
    });
    const leftovers = (source.atomIds || [])
      .map((id) => atomsById[clean(id)])
      .filter((atom) => atom && !usedAtoms.has(clean(atom.id || atom.atomId)))
      .map((atom) => atomLeaf(atom, { episodeId: "" }));
    if (leftovers.length) {
      branches.push({
        title: "章节补充",
        subtitle: "未归入单一讲次的章节知识",
        meta: leftovers.length + " 原子",
        relations: [],
        leaves: leftovers,
      });
    }
    const conceptCount = (source.conceptIds || []).length;
    const leafCount = branches.reduce((sum, branch) => sum + branch.leaves.length, 0);
    return {
      kind: "chapter",
      root: {
        kicker: "章节",
        title: clean(source.label || source.title || source.id || "本章"),
        subtitle: "以讲次为分支，把本章概念与完整知识原子连成一张可追溯的导图。",
        meta: lessons.length + " 讲 · " + conceptCount + " 个核心锚点 · " + leafCount + " 个知识原子",
      },
      branches,
      leafCount,
    };
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
    if (quality.conceptCount) top.appendChild(h("span", "kp-coverage", quality.conceptCount + " 个核心锚点"));
    if (quality.knowledgeAtoms) {
      top.appendChild(h("span", "kp-coverage", quality.knowledgeAtoms + " 个知识原子"));
    }
    hero.appendChild(top);

    hero.appendChild(h("div", "kp-kicker", "本讲要回答"));
    hero.appendChild(h("h2", "kp-question", note.centralQuestion || lesson.thesis || lesson.title));
    const thesis = h("div", "kp-bigidea");
    thesis.appendChild(rich(note.bigIdea || lesson.thesis));
    hero.appendChild(thesis);

    const actions = h("div", "kp-actions");
    const start = jumpButton(note.mentalModel?.[0]?.time || "", onSeek, "从知识主线开始");
    start.classList.add("kp-primary");
    actions.appendChild(start);
    const tools = h("details", "kp-tool-menu");
    tools.appendChild(h("summary", "", "更多工具"));
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
    tools.appendChild(copy);
    const regen = h("button", "kp-ghost", status && status.state === "running" ? "生成中…" : "重新生成");
    regen.type = "button";
    regen.disabled = !!(status && status.state === "running");
    regen.onclick = () => onGenerate(true);
    tools.appendChild(regen);
    actions.appendChild(tools);
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
    const node = section("先读懂这条主线", "先建立问题 → 机制 → 结果的全局，再进入细节");
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

  function renderMindMapTree(map, options) {
    const opt = options || {};
    const shell = h("div", "kp-mindmap");
    const toolbar = h("div", "kp-mindmap-toolbar");
    toolbar.appendChild(h("span", "", map.leafCount + " 个知识原子全覆盖"));
    const expand = h("button", "kp-ghost", "全部展开");
    const collapse = h("button", "kp-ghost", "全部收起");
    expand.type = "button";
    collapse.type = "button";
    toolbar.appendChild(expand);
    toolbar.appendChild(collapse);
    shell.appendChild(toolbar);

    const grid = h("div", "kp-mindmap-grid");
    const rootCard = h("article", "kp-mindmap-root");
    rootCard.appendChild(h("span", "kp-overline", map.root.kicker));
    rootCard.appendChild(h("b", "", map.root.title));
    if (map.root.subtitle) rootCard.appendChild(h("p", "", map.root.subtitle));
    rootCard.appendChild(h("small", "", map.root.meta));
    grid.appendChild(rootCard);

    const branchWrap = h("div", "kp-mind-branches");
    const branchDetails = [];
    (map.branches || []).forEach((branch, index) => {
      const color = MIND_COLORS[index % MIND_COLORS.length];
      const details = h("details", "kp-mind-branch");
      details.style.setProperty("--mind-color", color);
      if (index === 0 && opt.openFirst) details.open = true;
      const summary = h("summary", "kp-mind-branch-head");
      const marker = h("i", "kp-mind-branch-dot");
      summary.appendChild(marker);
      const head = h("span", "kp-mind-branch-copy");
      head.appendChild(h("b", "", branch.title));
      if (branch.subtitle) head.appendChild(h("small", "", branch.subtitle));
      summary.appendChild(head);
      const meta = h("span", "kp-mind-branch-meta");
      meta.appendChild(h("em", "", String(branch.leaves.length)));
      meta.appendChild(h("small", "", "原子"));
      summary.appendChild(meta);
      details.appendChild(summary);
      if ((branch.relations || []).length) {
        const relations = h("div", "kp-mind-relations");
        branch.relations.slice(0, 4).forEach((label) => {
          relations.appendChild(h("span", "", label));
        });
        details.appendChild(relations);
      }
      const leaves = h("div", "kp-mind-leaves");
      let leavesBuilt = false;
      const buildLeaves = () => {
        if (leavesBuilt) return;
        leavesBuilt = true;
        const startedAt = performance.now();
        (branch.leaves || []).forEach((leaf, leafIndex) => {
          const tag = opt.onLeaf ? "button" : "article";
          const row = h(tag, "kp-mind-leaf");
          if (tag === "button") {
            row.type = "button";
            row.setAttribute("aria-label", leaf.title);
            row.onclick = () => opt.onLeaf(leaf, branch);
          }
          const top = h("span", "kp-mind-leaf-top");
          top.appendChild(h("em", "", ATOM_KINDS[leaf.kind] || leaf.kind || "要点"));
          top.appendChild(h("small", "", leaf.time || ""));
          row.appendChild(top);
          row.appendChild(h("b", "", leaf.title));
          if (leaf.detail) row.appendChild(h("p", "", leaf.detail));
          if ((leaf.conceptTitles || []).length > 1 && map.kind === "chapter") {
            row.appendChild(h("small", "kp-mind-leaf-links",
              "关联：" + leaf.conceptTitles.slice(0, 3).join(" · ")));
          }
          row.style.setProperty("--leaf-index", String(leafIndex));
          leaves.appendChild(row);
        });
        if (!leaves.children.length) {
          leaves.appendChild(h("p", "kp-mind-empty", "这一分支暂无可展示的知识原子。"));
        }
        details.dataset.leafBuildMs = (performance.now() - startedAt).toFixed(1);
      };
      details.addEventListener("toggle", () => {
        if (details.open) buildLeaves();
      });
      if (details.open) {
        buildLeaves();
      }
      details.appendChild(leaves);
      branchDetails.push(details);
      branchWrap.appendChild(details);
    });
    grid.appendChild(branchWrap);
    shell.appendChild(grid);
    expand.onclick = () => branchDetails.forEach((row) => { row.open = true; });
    collapse.onclick = () => branchDetails.forEach((row) => { row.open = false; });
    return shell;
  }

  function renderEpisodeMindMap(note, onSeek) {
    const map = buildEpisodeMindMap(note);
    if (!(map.branches || []).length) return null;
    const node = section(
      "本讲思维导图",
      "中心问题 → 核心锚点 → 完整知识原子；点叶子回到原片",
      "kp-mindmap-section",
    );
    node.appendChild(renderMindMapTree(map, {
      openFirst: true,
      onLeaf: (leaf) => {
        if (leaf.time && onSeek) onSeek(leaf.time);
      },
    }));
    return node;
  }

  function renderConceptGraph(
    note, onSeek, lesson, mastery, onMasteryChanged, courseGraph, onOpenEpisode
  ) {
    const graph = note.conceptGraph || {};
    const nodes = graph.nodes || [];
    const edges = graph.edges || [];
    if (nodes.length < 2 || !edges.length) return null;
    const node = section("本讲核心锚点", "先读一句解释；点击锚点后只展开它在网络中的直接关系");
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
    const anchorList = h("div", "kp-anchor-list");
    const anchorRows = {};
    const network = h("details", "kp-network");
    const networkSummary = h("summary", "kp-network-summary");
    networkSummary.appendChild(h("b", "", "展开关系网络与讲解证据"));
    networkSummary.appendChild(h("small", "", edges.length + " 条直接关系 · 默认收起"));
    network.appendChild(networkSummary);
    ordered.forEach((row) => {
      const concept = (note.concepts || []).find((item) => item.title === row.conceptTitle);
      const button = h("button", "kp-anchor-row");
      button.type = "button";
      button.appendChild(h("b", "", row.conceptTitle));
      if (concept?.oneLine || row.summary) {
        button.appendChild(h("p", "", concept?.oneLine || row.summary));
      }
      const time = concept?.evidence?.[0]?.time || "";
      if (time) button.appendChild(h("small", "", time));
      button.onclick = () => showFocus(row.conceptTitle);
      anchorRows[row.conceptTitle] = button;
      anchorList.appendChild(button);
    });
    node.appendChild(anchorList);
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
    const edgeElements = [];
    edges.forEach((edge, index) => {
      const left = positions[edge.from];
      const right = positions[edge.to];
      if (!left || !right) return;
      const path = document.createElementNS(NS, "path");
      const midX = (left.x + right.x) / 2;
      const midY = (left.y + right.y) / 2;
      const bend = ((index % 5) - 2) * 14;
      path.setAttribute("d", "M " + left.x + " " + left.y + " Q " + (midX + bend) + " " + (midY - bend) + " " + right.x + " " + right.y);
      path.setAttribute("class", "kp-graph-edge edge-" + clean(edge.type));
      path.setAttribute("marker-end", "url(#kp-arrow)");
      const title = document.createElementNS(NS, "title");
      title.textContent = edge.from + " → " + edge.to + "：" + (edge.explain || edge.type);
      path.appendChild(title);
      svg.appendChild(path);
      edgeElements.push({ element: path, edge });
    });
    canvas.appendChild(svg);
    const nodeElements = {};
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
      card.onclick = () => showFocus(row.conceptTitle);
      canvas.appendChild(card);
      nodeElements[row.conceptTitle] = card;
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
    network.appendChild(canvas);

    const focus = h("div", "kp-focus-panel");
    focus.hidden = true;
    network.appendChild(focus);
    node.appendChild(network);

    function clearFocus() {
      Object.values(nodeElements).forEach((element) => {
        element.classList.remove("focused", "dimmed");
      });
      edgeElements.forEach(({ element }) => {
        element.classList.remove("focused", "dimmed");
      });
      Object.values(anchorRows).forEach((element) => element.classList.remove("selected"));
      focus.hidden = true;
      focus.innerHTML = "";
    }

    function showFocus(title) {
      const graphNode = nodes.find((row) => row.conceptTitle === title);
      const concept = (note.concepts || []).find((row) => row.title === title);
      if (!graphNode || !concept) return;
      network.open = true;
      Object.entries(anchorRows).forEach(([name, element]) => {
        element.classList.toggle("selected", name === title);
      });
      const adjacent = new Set([title]);
      const relationRows = [];
      edges.forEach((edge) => {
        if (edge.from === title || edge.to === title) {
          adjacent.add(edge.from);
          adjacent.add(edge.to);
          relationRows.push(edge);
        }
      });
      Object.entries(nodeElements).forEach(([name, element]) => {
        element.classList.toggle("focused", name === title);
        element.classList.toggle("dimmed", !adjacent.has(name));
      });
      edgeElements.forEach(({ element, edge }) => {
        const active = edge.from === title || edge.to === title;
        element.classList.toggle("focused", active);
        element.classList.toggle("dimmed", !active);
      });

      focus.innerHTML = "";
      focus.hidden = false;
      const head = h("div", "kp-focus-head");
      const titleBox = h("div");
      titleBox.appendChild(h("span", "kp-overline", "聚焦锚点"));
      titleBox.appendChild(h("h4", "", title));
      titleBox.appendChild(h("p", "", concept.oneLine || graphNode.summary || ""));
      head.appendChild(titleBox);
      const close = h("button", "kp-ghost", "清除聚焦");
      close.type = "button";
      close.onclick = clearFocus;
      head.appendChild(close);
      focus.appendChild(head);
      focus.appendChild(masteryControl(
        "anchor:" + title,
        mastery,
        lesson,
        onMasteryChanged,
      ));
      const body = h("p", "kp-focus-explain");
      body.appendChild(rich(concept.explain || ""));
      focus.appendChild(body);
      if ((concept.mechanism || []).length) {
        const mechanism = h("div", "kp-focus-mechanism");
        mechanism.appendChild(h("b", "", "关键机制"));
        const list = h("ol");
        concept.mechanism.slice(0, 5).forEach((item) => list.appendChild(h("li", "", item)));
        mechanism.appendChild(list);
        focus.appendChild(mechanism);
      }
      if (relationRows.length) {
        const relations = h("div", "kp-focus-relations");
        relations.appendChild(h("b", "", "直接关系"));
        relationRows.forEach((edge) => {
          const neighbor = edge.from === title ? edge.to : edge.from;
          const row = h("button", "kp-focus-relation");
          row.type = "button";
          row.appendChild(h("strong", "", neighbor));
          row.appendChild(h("span", "", edge.type));
          row.appendChild(h("p", "", edge.explain || ""));
          row.onclick = () => showFocus(neighbor);
          relations.appendChild(row);
        });
        focus.appendChild(relations);
      }
      const actions = h("div", "kp-focus-actions");
      const first = (concept.evidence || [])[0];
      if (first?.time) actions.appendChild(jumpButton(first.time, onSeek, "回到原片 " + first.time));
      const cross = relatedEpisodeLinks(
        courseGraph,
        [title],
        note.episode,
        onOpenEpisode,
      );
      if (cross) actions.appendChild(cross);
      if (actions.children.length) focus.appendChild(actions);
      if ((concept.evidence || []).length) {
        const evidence = h("details", "kp-focus-evidence");
        evidence.appendChild(h("summary", "", "核对本锚点证据"));
        evidence.appendChild(renderEvidence(concept.evidence, onSeek));
        focus.appendChild(evidence);
      }
    }
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
      (graph.stats?.knowledgeAtoms || 0) + " 个知识原子 · " +
      (graph.stats?.edges || 0) + " 条核心关系"
    ));
    details.appendChild(summary);
    const byId = Object.fromEntries((graph.nodes || []).map((row) => [row.id, row]));
    const lessonsById = Object.fromEntries((graph.lessons || []).map((row) => [row.id, row]));
    const flow = h("div", "kp-course-flow");
    (graph.chapters || []).forEach((chapter, index) => {
      const card = h("article", "kp-course-chapter");
      card.appendChild(h("span", "kp-step-no", String(index + 1).padStart(2, "0")));
      card.appendChild(h("h4", "", chapter.label));
      const chapterMap = buildChapterMindMap(chapter, graph);
      if ((chapterMap.branches || []).length) {
        const mapDetails = h("details", "kp-chapter-map");
        const mapSummary = h("summary", "kp-chapter-map-summary");
        const mapHead = h("span", "kp-chapter-map-head");
        mapHead.appendChild(h("em", "", "章节思维导图"));
        mapHead.appendChild(h("b", "", chapterMap.root.title));
        mapHead.appendChild(h("small", "", chapterMap.root.meta));
        mapSummary.appendChild(mapHead);
        const preview = h("span", "kp-chapter-map-preview");
        chapterMap.branches.slice(0, 4).forEach((branch, branchIndex) => {
          const item = h("span", "", branch.title);
          item.style.setProperty("--mind-color", MIND_COLORS[branchIndex % MIND_COLORS.length]);
          preview.appendChild(item);
        });
        if (chapterMap.branches.length > 4) {
          preview.appendChild(h("span", "more", "+" + (chapterMap.branches.length - 4)));
        }
        mapSummary.appendChild(preview);
        mapDetails.appendChild(mapSummary);
        let mapBuilt = false;
        mapDetails.addEventListener("toggle", () => {
          card.classList.toggle("kp-map-open", mapDetails.open);
          if (!mapDetails.open || mapBuilt) return;
          mapBuilt = true;
          const startedAt = performance.now();
          mapDetails.appendChild(renderMindMapTree(chapterMap, {
            openFirst: false,
            onLeaf: (leaf) => {
              if (leaf.episodeId && onOpenEpisode) onOpenEpisode(leaf.episodeId);
            },
          }));
          mapDetails.dataset.buildMs = (performance.now() - startedAt).toFixed(1);
        });
        card.appendChild(mapDetails);
      }
      card.appendChild(h("p", "",
        (chapter.episodes || []).length + " 讲 · " +
        (chapter.conceptIds || []).length + " 个核心锚点 · " +
        (chapter.atomIds || []).length + " 个知识原子"
      ));
      const top = (chapter.conceptIds || []).map((id) => byId[id]).filter(Boolean).slice(0, 5);
      const tags = h("div", "kp-course-tags");
      top.forEach((row) => tags.appendChild(h("span", "", row.label)));
      card.appendChild(tags);
      const lessonDetails = h("details", "kp-course-lessons");
      lessonDetails.appendChild(h("summary", "", "展开本章 " + (chapter.lessonIds || []).length + " 讲"));
      const lessonList = h("div", "kp-course-lesson-list");
      (chapter.lessonIds || []).map((id) => lessonsById[id]).filter(Boolean).forEach((lesson) => {
        const button = h("button", "kp-course-lesson");
        button.type = "button";
        button.appendChild(h("b", "", "E" + String(lesson.episode).padStart(2, "0")));
        button.appendChild(h("span", "", lesson.label));
        button.appendChild(h("small", "", (lesson.knowledgeAtomCount || 0) + " 原子"));
        button.onclick = (event) => {
          event.stopPropagation();
          const target = episodeTarget(graph, lesson);
          if (onOpenEpisode && target) onOpenEpisode(target);
        };
        lessonList.appendChild(button);
      });
      lessonDetails.appendChild(lessonList);
      card.appendChild(lessonDetails);
      const open = h("button", "kp-time", "打开第 " + (chapter.episodes?.[0] ?? "?") + " 讲");
      open.type = "button";
      open.onclick = () => {
        const episode = chapter.episodes?.[0];
        if (episode == null || !onOpenEpisode) return;
        const lesson = (graph.lessons || []).find(
          (row) => Number(row.episode) === Number(episode)
        );
        const target = episodeTarget(graph, lesson) ||
          "os-course-e" + String(episode).padStart(2, "0");
        onOpenEpisode(target);
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
      group.appendChild(h("summary", "",
        chapter.label + " · " + (chapter.conceptIds || []).length +
        " 个核心锚点 · " + (chapter.atomIds || []).length + " 个知识原子"
      ));
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

  function renderStarMap(note, lesson, courseGraph, onSeek, onOpenEpisode, onOpenKnowledge) {
    if (!global.VKSStarMap) {
      const node = section("知识星图", "全课程概念、知识原子和关系光束");
      node.appendChild(h("p", "kp-error", "星图组件未加载，请刷新页面。"));
      return node;
    }
    return global.VKSStarMap.create({
      note,
      lesson,
      courseGraph,
      onSeek,
      onOpenEpisode,
      onOpenKnowledge,
    });
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

  function renderConcepts(
    note, onSeek, lesson, mastery, onMasteryChanged, courseGraph, onOpenEpisode
  ) {
    const node = section("核心锚点", "顶层导航：定义、机制、例子、边界、误区与证据放在一起");
    (note.concepts || []).forEach((concept, index) => {
      const card = h("article", "kp-concept");
      const head = h("div", "kp-concept-head");
      head.appendChild(h("span", "kp-concept-no", String(index + 1).padStart(2, "0")));
      const title = h("div");
      title.appendChild(h("h4", "", concept.title));
      title.appendChild(h("p", "kp-one-line", concept.oneLine));
      head.appendChild(title);
      card.appendChild(head);
      card.appendChild(masteryControl(
        "anchor:" + concept.title,
        mastery,
        lesson,
        onMasteryChanged,
      ));
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
      const cross = relatedEpisodeLinks(
        courseGraph,
        [concept.title],
        note.episode,
        onOpenEpisode,
      );
      if (cross) card.appendChild(cross);
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

  function renderKnowledgeAtoms(
    note, onSeek, lesson, mastery, onMasteryChanged, courseGraph, onOpenEpisode
  ) {
    const atoms = note.knowledgeAtoms || [];
    if (!atoms.length) return null;
    const details = h("details", "kp-section kp-atom-atlas");
    const summary = h("summary", "kp-head");
    summary.appendChild(h("h3", "", "完整知识原子"));
    summary.appendChild(h("small", "",
      atoms.length + " 条细分知识 · 不设总量上限 · 每条可回到原片"
    ));
    details.appendChild(summary);

    const toolbar = h("div", "kp-atom-toolbar");
    const search = h("input", "kp-atom-search");
    search.type = "search";
    search.placeholder = "搜索本讲知识原子、锚点、块或时间…";
    search.setAttribute("aria-label", "搜索知识原子");
    toolbar.appendChild(search);
    const visible = h("span", "kp-atom-visible", atoms.length + " 条");
    toolbar.appendChild(visible);
    details.appendChild(toolbar);

    const groups = new Map();
    atoms.forEach((atom) => {
      const anchor = (atom.conceptTitles || [])[0] || "未归类";
      if (!groups.has(anchor)) groups.set(anchor, []);
      groups.get(anchor).push(atom);
    });
    const groupRoot = h("div", "kp-atom-groups");
    groups.forEach((rows, anchor) => {
      const group = h("details", "kp-atom-group");
      const groupSummary = h("summary");
      groupSummary.appendChild(h("b", "", anchor));
      groupSummary.appendChild(h("span", "", rows.length + " 条"));
      group.appendChild(groupSummary);
      const list = h("div", "kp-atom-list");
      rows.forEach((atom) => {
        const card = h("article", "kp-atom");
        card.dataset.search = [
          atom.title, atom.claim, atom.topic, atom.blockId, atom.time,
          ...(atom.conceptTitles || []),
        ].join(" ").toLowerCase();
        const top = h("div", "kp-atom-top");
        top.appendChild(h("span", "kp-atom-kind kind-" + clean(atom.kind),
          ATOM_KINDS[atom.kind] || atom.kind || "要点"));
        top.appendChild(h("span", "kp-atom-block", atom.blockId || ""));
        if ((atom.visualEvidenceIds || []).length) {
          top.appendChild(h("span", "kp-atom-visual",
            "画面 " + atom.visualEvidenceIds.length));
        }
        if (atom.time) top.appendChild(jumpButton(atom.time, onSeek, atom.time));
        card.appendChild(top);
        card.appendChild(h("b", "kp-atom-title", atom.title || atom.claim));
        if (atom.title && atom.title !== atom.claim) {
          card.appendChild(h("p", "", atom.claim));
        }
        if ((atom.conceptTitles || []).length > 1) {
          card.appendChild(h("small", "kp-atom-anchors",
            "连接锚点：" + atom.conceptTitles.join(" · ")));
        }
        const cross = relatedEpisodeLinks(
          courseGraph,
          atom.conceptTitles || [],
          note.episode,
          onOpenEpisode,
        );
        if (cross) card.appendChild(cross);
        card.appendChild(masteryControl(
          "atom:" + atom.atomId,
          mastery,
          lesson,
          onMasteryChanged,
        ));
        list.appendChild(card);
      });
      group.appendChild(list);
      groupRoot.appendChild(group);
    });
    details.appendChild(groupRoot);

    search.addEventListener("input", () => {
      const query = search.value.trim().toLowerCase();
      let count = 0;
      groupRoot.querySelectorAll(".kp-atom").forEach((card) => {
        const match = !query || (card.dataset.search || "").includes(query);
        card.hidden = !match;
        if (match) count += 1;
      });
      groupRoot.querySelectorAll(".kp-atom-group").forEach((group) => {
        const hasMatch = Boolean(group.querySelector(".kp-atom:not([hidden])"));
        group.hidden = !hasMatch;
      });
      visible.textContent = count + " 条";
    });
    return details;
  }

  function renderReviewQueue(note, lesson, mastery, onSeek, onMasteryChanged) {
    const items = [];
    (note.concepts || []).forEach((concept) => {
      const key = "anchor:" + concept.title;
      if (!["fuzzy", "unknown"].includes(mastery[key])) return;
      items.push({
        key,
        scope: "核心锚点",
        title: concept.title,
        detail: concept.oneLine,
        time: concept.evidence?.[0]?.time || "",
        status: mastery[key],
      });
    });
    (note.knowledgeAtoms || []).forEach((atom) => {
      const key = "atom:" + atom.atomId;
      if (!["fuzzy", "unknown"].includes(mastery[key])) return;
      items.push({
        key,
        scope: "知识原子 · " + ((atom.conceptTitles || [])[0] || "未归类"),
        title: atom.title || atom.claim,
        detail: atom.claim,
        time: atom.time,
        status: mastery[key],
      });
    });
    items.sort((left, right) => {
      const rank = { unknown: 0, fuzzy: 1 };
      return (rank[left.status] ?? 9) - (rank[right.status] ?? 9);
    });
    const node = section(
      "复习队列",
      items.length
        ? items.length + " 个模糊或未掌握节点"
        : "当前没有标记为模糊或不会的节点",
      "kp-review-queue",
    );
    if (!items.length) {
      const empty = h("div", "kp-review-empty");
      empty.appendChild(h("b", "", "当前已标记内容都掌握了"));
      empty.appendChild(h("p", "", "可以展开下面的主动回忆，或回到“知识”视图给新的锚点和原子评分。"));
      node.appendChild(empty);
    } else {
      const list = h("div", "kp-review-list");
      items.forEach((item) => {
        const card = h("article", "kp-review-item status-" + item.status);
        const top = h("div", "kp-review-item-top");
        top.appendChild(h("span", "kp-review-scope", item.scope));
        top.appendChild(h("span", "kp-review-state", item.status === "unknown" ? "不会" : "模糊"));
        if (item.time) top.appendChild(jumpButton(item.time, onSeek));
        card.appendChild(top);
        card.appendChild(h("b", "", item.title));
        if (item.detail && item.detail !== item.title) {
          card.appendChild(h("p", "", item.detail));
        }
        card.appendChild(masteryControl(
          item.key,
          mastery,
          lesson,
          onMasteryChanged,
        ));
        list.appendChild(card);
      });
      node.appendChild(list);
    }
    if ((note.recall || []).length) {
      const recall = h("details", "kp-review-recall");
      recall.appendChild(h("summary", "", "展开主动回忆 · " + note.recall.length + " 题"));
      const list = h("div", "kp-review-recall-list");
      note.recall.forEach((row) => {
        const details = h("details");
        details.appendChild(h("summary", "", row.question));
        details.appendChild(h("p", "", row.answer));
        if (row.time) details.appendChild(jumpButton(row.time, onSeek));
        list.appendChild(details);
      });
      recall.appendChild(list);
      node.appendChild(recall);
    }
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
    summary.appendChild(h("small", "", (note.quality?.coverageBlocks || note.coverage.length) + " 块全部有归属"));
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
    const node = section("画面补充了什么", (note.quality?.visualClusters || note.visualEvidence.length) + " 组画面已进入笔记");
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
    summary.appendChild(h("small", "", rows.length + " 帧全部有决定 · " + (note.quality?.includedVisualClusters || 0) + " 组进入笔记"));
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
    const oldMap = host.querySelector && host.querySelector(".kp-star-zone");
    if (oldMap && oldMap._kpDestroy) oldMap._kpDestroy();
    host.innerHTML = "";
    host.className = "kp-root";
    if (!note) {
      host.appendChild(renderEmpty(lesson, status, onGenerate));
      return host;
    }

    host.appendChild(renderHero(note, lesson, onSeek, onGenerate, status));
    const mastery = loadMastery(lesson);
    const reviewHost = h("div", "kp-review-host");
    const reviewBadge = h("span", "kp-tab-count", "");

    function reviewCount() {
      const live = new Set([
        ...(note.concepts || []).map((concept) => "anchor:" + concept.title),
        ...(note.knowledgeAtoms || []).map((atom) => "atom:" + atom.atomId),
      ]);
      return Object.entries(mastery).filter(([key, value]) => (
        live.has(key) && ["fuzzy", "unknown"].includes(value)
      )).length;
    }

    function refreshReview() {
      reviewHost.innerHTML = "";
      reviewHost.appendChild(
        renderReviewQueue(note, lesson, mastery, onSeek, refreshReview)
      );
      const count = reviewCount();
      reviewBadge.textContent = count ? String(count) : "";
      reviewBadge.hidden = !count;
    }

    const shell = h("div", "kp-tab-shell");
    const tabs = h("nav", "kp-tabs");
    tabs.setAttribute("aria-label", "知识视图");
    const pageRoot = h("div", "kp-pages");
    const pages = {};
    const buttons = {};

    function switchTab(name) {
      Object.entries(pages).forEach(([key, page]) => {
        page.hidden = key !== name;
      });
      Object.entries(buttons).forEach(([key, button]) => {
        button.classList.toggle("active", key === name);
        button.setAttribute("aria-selected", key === name ? "true" : "false");
      });
      host.classList.toggle("kp-star-active", name === "star");
      const scrollHost = host.closest && host.closest("#knowledge");
      if (scrollHost) scrollHost.scrollTop = 0;
      if (pages.star && pages.star._kpActivate) {
        pages.star._kpActivate(name === "star");
      }
    }

    [
      ["learn", "学习", null],
      ["knowledge", "知识", null],
      ["star", "星图", null],
      ["review", "复习", reviewBadge],
    ].forEach(([key, label, badge]) => {
      const button = h("button", "kp-tab", label);
      button.type = "button";
      button.setAttribute("role", "tab");
      if (badge) button.appendChild(badge);
      button.onclick = () => switchTab(key);
      buttons[key] = button;
      tabs.appendChild(button);
    });
    shell.appendChild(tabs);

    const learnPage = h("div", "kp-page");
    [
      renderEpisodeMindMap(note, onSeek),
      renderMentalModel(note, onSeek),
      renderConceptGraph(
        note, onSeek, lesson, mastery, refreshReview, courseGraph, onOpenEpisode
      ),
    ].forEach((node) => {
      if (node) learnPage.appendChild(node);
    });
    const libraryLink = h("button", "kp-library-link");
    libraryLink.type = "button";
    libraryLink.appendChild(h("b", "", "进入完整知识库"));
    libraryLink.appendChild(h("span", "",
      (note.concepts || []).length + " 个锚点 · " +
      (note.knowledgeAtoms || []).length + " 条原子 · 证据、对比、画面全部保留"
    ));
    libraryLink.appendChild(h("i", "", "→"));
    libraryLink.onclick = () => switchTab("knowledge");
    learnPage.appendChild(libraryLink);
    pages.learn = learnPage;

    const knowledgePage = h("div", "kp-page");
    [
      renderConcepts(
        note, onSeek, lesson, mastery, refreshReview, courseGraph, onOpenEpisode
      ),
      renderKnowledgeAtoms(
        note, onSeek, lesson, mastery, refreshReview, courseGraph, onOpenEpisode
      ),
      renderComparisons(note),
      renderFormulas(note),
      renderExam(note, onSeek),
      renderRecall(note, onSeek),
      renderGlossary(note, onSeek),
      renderCoverage(note, onSeek),
      renderVisual(note, lesson, onSeek),
      renderVisualAudit(note, onSeek),
      renderCourseSystem(courseGraph, onOpenEpisode),
      renderGoals(note),
      renderSemanticReview(note.semanticReview, onSeek),
    ].forEach((node) => {
      if (node) knowledgePage.appendChild(node);
    });
    pages.knowledge = knowledgePage;

    const starPage = h("div", "kp-page");
    const starMap = renderStarMap(
      note,
      lesson,
      courseGraph,
      onSeek,
      onOpenEpisode,
      () => switchTab("knowledge"),
    );
    starPage.appendChild(starMap);
    starPage._kpActivate = (active) => {
      if (starMap && starMap._kpActivate) starMap._kpActivate(active);
    };
    pages.star = starPage;

    pages.review = h("div", "kp-page");
    pages.review.appendChild(reviewHost);
    Object.entries(pages).forEach(([key, page]) => {
      page.dataset.tabPage = key;
      pageRoot.appendChild(page);
    });
    shell.appendChild(pageRoot);
    host.appendChild(shell);
    refreshReview();
    switchTab("learn");

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
    if ((note.knowledgeAtoms || []).length) {
      rows.push("", "## 完整知识原子");
      const groups = new Map();
      note.knowledgeAtoms.forEach((atom) => {
        const anchor = (atom.conceptTitles || [])[0] || "未归类";
        if (!groups.has(anchor)) groups.set(anchor, []);
        groups.get(anchor).push(atom);
      });
      groups.forEach((atoms, anchor) => {
        rows.push("", "### " + clean(anchor));
        atoms.forEach((atom) => {
          rows.push(
            "- `" + clean(atom.time) + "` **" + clean(atom.title) + "** [" +
            clean(ATOM_KINDS[atom.kind] || atom.kind) + "] — " + clean(atom.claim)
          );
        });
      });
    }
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
      note.visualAudit.forEach((x) => rows.push("- `" + clean(x.time) + "` " + clean(x.candidateId) + " / " + clean(x.clusterId) + " **" + clean(x.decision) + "** — " + clean(x.reason)));
    }
    if (note.quality?.warnings?.length) {
      rows.push("", "## 质量提醒");
      note.quality.warnings.forEach((x) => rows.push("- " + clean(x)));
    }
    return rows.join("\n");
  }

  const api = {
    render,
    generate,
    toMarkdown,
    relatedEpisodes,
    buildEpisodeMindMap,
    buildChapterMindMap,
  };
  global.VKSKnowledgePlugin = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
