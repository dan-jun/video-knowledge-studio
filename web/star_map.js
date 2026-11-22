/* Video Knowledge Studio · interactive course knowledge galaxy */
(function (global) {
  const GOLDEN = Math.PI * (3 - Math.sqrt(5));
  const WORLD = { width: 3600, height: 2400, cx: 1800, cy: 1200 };
  const COLORS = ["#56d8ff", "#62e5b5", "#ffc768", "#f18d86", "#a68cff", "#74a7ff"];
  const TYPE_LABELS = {
    prerequisite: "前置",
    mechanism: "机制",
    cause: "因果",
    contrast: "对比",
    example: "例子",
    application: "应用",
    grouping: "体系分支",
  };

  const h = (tag, cls, value) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (value != null) node.textContent = String(value);
    return node;
  };
  const clean = (value) => String(value == null ? "" : value).trim();

  function hashText(value) {
    let hash = 2166136261;
    for (let i = 0; i < value.length; i += 1) {
      hash ^= value.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }
    return (hash >>> 0) / 4294967295;
  }

  function rgba(hex, alpha) {
    const value = hex.replace("#", "");
    const n = parseInt(value.length === 3
      ? value.split("").map((x) => x + x).join("")
      : value, 16);
    return "rgba(" + ((n >> 16) & 255) + "," + ((n >> 8) & 255) + "," +
      (n & 255) + "," + alpha + ")";
  }

  function chapterColor(index) {
    return COLORS[index % COLORS.length];
  }

  function button(label, cls, onClick) {
    const node = h("button", cls || "kp-star-button", label);
    node.type = "button";
    node.onclick = onClick;
    return node;
  }

  function lessonFor(graph, episode) {
    return (graph.lessons || []).find((row) => Number(row.episode) === Number(episode)) || null;
  }

  function chapterKey(value) {
    return clean(value).replace(/^chapter-/, "");
  }

  function chapterFor(graph, chapterId) {
    return (graph.chapters || []).find(
      (row) => chapterKey(row.id) === chapterKey(chapterId)
    ) || null;
  }

  function buildLayout(graph, currentLesson) {
    const chapters = (graph.chapters || []).slice();
    const lessons = (graph.lessons || []).slice();
    const concepts = (graph.nodes || []).slice();
    const atoms = (graph.knowledgeAtoms || []).slice();
    const edges = (graph.edges || []).slice();
    const chapterIndex = new Map();
    const lessonIndex = new Map();
    const conceptIndex = new Map();
    const lessonsByChapter = new Map();
    const conceptsByLesson = new Map();
    const atomGroups = new Map();
    const chapterCenters = new Map();
    const lessonHubs = new Map();
    const conceptPositions = new Map();
    const atomPositions = new Map();
    const adjacency = new Map();

    chapters.forEach((chapter, index) => {
      const key = chapterKey(chapter.id);
      chapterIndex.set(key, index);
      const angle = chapters.length
        ? -Math.PI / 2 + (Math.PI * 2 * index) / chapters.length
        : 0;
      chapterCenters.set(key, {
        x: WORLD.cx + Math.cos(angle) * 930,
        y: WORLD.cy + Math.sin(angle) * 650,
        color: chapterColor(index),
        id: key,
        chapter,
      });
      lessonsByChapter.set(key, []);
    });

    lessons.forEach((lesson) => {
      lessonIndex.set(String(lesson.id), lesson);
      const key = chapterKey(lesson.chapterId);
      if (!lessonsByChapter.has(key)) lessonsByChapter.set(key, []);
      lessonsByChapter.get(key).push(lesson);
      conceptsByLesson.set(String(lesson.id), new Set((lesson.conceptIds || []).map(String)));
    });

    lessonsByChapter.forEach((rows, chapterId) => {
      rows.sort((a, b) => Number(a.episode || 0) - Number(b.episode || 0));
      const center = chapterCenters.get(chapterId) || {
        x: WORLD.cx,
        y: WORLD.cy,
        color: COLORS[0],
      };
      const radius = Math.min(390, 130 + Math.sqrt(Math.max(1, rows.length)) * 42);
      rows.forEach((lesson, index) => {
        const seed = hashText(String(lesson.id) + ":" + chapterId);
        const angle = index * GOLDEN + seed * 0.85;
        const distance = rows.length === 1
          ? 0
          : radius * Math.sqrt((index + 0.55) / rows.length);
        lessonHubs.set(String(lesson.id), {
          x: center.x + Math.cos(angle) * distance,
          y: center.y + Math.sin(angle) * distance * 0.78,
          color: center.color,
          lesson,
          chapterId,
        });
      });
    });

    concepts.forEach((concept, index) => {
      conceptIndex.set(String(concept.id), concept);
      adjacency.set(String(concept.id), new Set());
      const occurrence = (concept.occurrences || [])[0] || {};
      const chapterId = chapterKey(
        (concept.chapterIds || [])[0] || occurrence.chapterId || "unassigned"
      );
      const occurrenceLesson = lessonFor(graph, occurrence.episode);
      const lesson = occurrenceLesson && chapterKey(occurrenceLesson.chapterId) === chapterId
        ? occurrenceLesson
        : lessons.find((row) =>
          chapterKey(row.chapterId) === chapterId &&
          (row.conceptIds || []).map(String).includes(String(concept.id))
        );
      const center = (lesson && lessonHubs.get(String(lesson.id))) ||
        chapterCenters.get(chapterId) || { x: WORLD.cx, y: WORLD.cy };
      const lessonConcepts = lesson
        ? Array.from(conceptsByLesson.get(String(lesson.id)) || [])
        : [];
      const localIndex = Math.max(0, lessonConcepts.indexOf(String(concept.id)));
      const seed = hashText(String(concept.id) + ":" + (lesson ? lesson.id : chapterId));
      const angle = localIndex * GOLDEN + seed * 1.3 + index * 0.003;
      const distance = 32 + Math.sqrt(localIndex + 0.7) * 24 + seed * 18;
      conceptPositions.set(String(concept.id), {
        x: center.x + Math.cos(angle) * distance,
        y: center.y + Math.sin(angle) * distance * 0.82,
        concept,
        chapterId,
        lessonId: lesson ? String(lesson.id) : "",
        color: chapterCenters.get(chapterId)?.color || COLORS[0],
      });
    });

    edges.forEach((edge) => {
      const left = adjacency.get(String(edge.from));
      const right = adjacency.get(String(edge.to));
      if (left) left.add(String(edge.to));
      if (right) right.add(String(edge.from));
    });

    atoms.forEach((atom) => {
      atomPositions.set(String(atom.id), {
        atom,
        conceptId: String((atom.conceptIds || [])[0] || ""),
        chapterId: chapterKey(atom.chapterId || ""),
        x: WORLD.cx,
        y: WORLD.cy,
        color: COLORS[0],
      });
      const conceptId = String((atom.conceptIds || [])[0] || "");
      if (!atomGroups.has(conceptId)) atomGroups.set(conceptId, []);
      atomGroups.get(conceptId).push(String(atom.id));
    });

    atomGroups.forEach((ids, conceptId) => {
      const pos = conceptPositions.get(conceptId);
      const concept = conceptIndex.get(conceptId);
      const fallbackChapter = chapterKey(concept?.chapterIds?.[0]);
      const fallbackCenter = chapterCenters.get(fallbackChapter) ||
        chapterCenters.get(chapterKey(chapters[0]?.id)) ||
        { x: WORLD.cx, y: WORLD.cy, color: COLORS[0] };
      ids.forEach((id, index) => {
        const atom = atomPositions.get(id)?.atom;
        const seed = hashText(id);
        const angle = index * GOLDEN + seed * 2.1;
        const distance = 11 + Math.sqrt(index + 0.5) * 7.2;
        const chapterId = chapterKey(atom?.chapterId || fallbackChapter);
        const point = pos || fallbackCenter;
        const color = chapterCenters.get(chapterId)?.color || (pos?.color || fallbackCenter.color);
        atomPositions.set(id, {
          atom,
          conceptId,
          chapterId,
          x: point.x + Math.cos(angle) * distance,
          y: point.y + Math.sin(angle) * distance * 0.86,
          color,
        });
      });
    });

    const lessonLinks = [];
    lessonsByChapter.forEach((rows, chapterId) => {
      const chapter = chapterCenters.get(chapterId);
      rows.forEach((lesson) => {
        const hub = lessonHubs.get(String(lesson.id));
        if (chapter && hub) {
          lessonLinks.push({
            from: { x: chapter.x, y: chapter.y },
            to: { x: hub.x, y: hub.y },
            chapterId,
          });
        }
      });
    });

    const membershipLinks = [];
    concepts.forEach((concept) => {
      const pos = conceptPositions.get(String(concept.id));
      const hub = lessonHubs.get(String(pos?.lessonId));
      if (pos && hub) {
        membershipLinks.push({
          conceptId: String(concept.id),
          lessonId: String(pos.lessonId),
          chapterId: pos.chapterId,
          from: hub,
          to: pos,
        });
      }
    });

    const graphEdges = edges.map((edge, index) => {
      const left = conceptPositions.get(String(edge.from));
      const right = conceptPositions.get(String(edge.to));
      if (!left || !right) return null;
      const dx = right.x - left.x;
      const dy = right.y - left.y;
      const length = Math.max(1, Math.hypot(dx, dy));
      const bend = (hashText(String(edge.id || index)) - 0.5) * Math.min(170, length * 0.22);
      return {
        ...edge,
        fromPoint: left,
        toPoint: right,
        cx: (left.x + right.x) / 2 - (dy / length) * bend,
        cy: (left.y + right.y) / 2 + (dx / length) * bend,
      };
    }).filter(Boolean);

    const atomLinks = atoms.map((atom) => {
      const point = atomPositions.get(String(atom.id));
      const concept = conceptPositions.get(point?.conceptId);
      if (!point || !concept) return null;
      return { atomId: String(atom.id), conceptId: point.conceptId, from: concept, to: point };
    }).filter(Boolean);

    const chapterLinks = chapters.map((chapter) => {
      const key = chapterKey(chapter.id);
      const point = chapterCenters.get(key);
      return point ? { chapterId: key, from: { x: WORLD.cx, y: WORLD.cy }, to: point } : null;
    }).filter(Boolean);

    const current = currentLesson
      ? lessons.find((row) => String(row.id) === String(currentLesson.id) ||
        Number(row.episode) === Number(currentLesson.episode))
      : null;
    const currentConceptIds = new Set(
      ((current && current.conceptIds) || (currentLesson && currentLesson.conceptIds) || []).map(String)
    );

    const points = [
      ...Array.from(chapterCenters.values()).map((row) => ({ x: row.x, y: row.y })),
      ...Array.from(conceptPositions.values()).map((row) => ({ x: row.x, y: row.y })),
    ];
    const minX = Math.min(...points.map((row) => row.x), WORLD.cx);
    const maxX = Math.max(...points.map((row) => row.x), WORLD.cx);
    const minY = Math.min(...points.map((row) => row.y), WORLD.cy);
    const maxY = Math.max(...points.map((row) => row.y), WORLD.cy);

    return {
      graph,
      chapters,
      lessons,
      concepts,
      atoms,
      edges: graphEdges,
      chapterIndex,
      lessonIndex,
      conceptIndex,
      chapterCenters,
      lessonHubs,
      conceptPositions,
      atomPositions,
      adjacency,
      lessonLinks,
      membershipLinks,
      atomLinks,
      chapterLinks,
      currentLesson: current,
      currentConceptIds,
      bounds: { minX, maxX, minY, maxY },
    };
  }

  function focusSets(layout, hit) {
    if (!hit) return null;
    const concepts = new Set();
    const atoms = new Set();
    const chapters = new Set();
    const edges = new Set();
    const addConcept = (id) => {
      const key = String(id || "");
      if (!layout.conceptPositions.has(key)) return;
      concepts.add(key);
      chapters.add(layout.conceptPositions.get(key).chapterId);
    };
    if (hit.kind === "concept") {
      addConcept(hit.id);
      (layout.adjacency.get(hit.id) || new Set()).forEach(addConcept);
      layout.atomLinks.forEach((row) => {
        if (concepts.has(row.conceptId) && row.atomId) atoms.add(row.atomId);
      });
      layout.edges.forEach((edge) => {
        if (concepts.has(String(edge.from)) || concepts.has(String(edge.to))) {
          edges.add(String(edge.id));
        }
      });
    } else if (hit.kind === "atom") {
      const atom = layout.atomPositions.get(hit.id);
      if (atom?.conceptId) {
        addConcept(atom.conceptId);
        (layout.adjacency.get(atom.conceptId) || new Set()).forEach(addConcept);
      }
      layout.atomLinks.forEach((row) => {
        if (concepts.has(row.conceptId)) atoms.add(row.atomId);
      });
      layout.edges.forEach((edge) => {
        if (concepts.has(String(edge.from)) || concepts.has(String(edge.to))) {
          edges.add(String(edge.id));
        }
      });
    } else if (hit.kind === "lesson") {
      const lesson = layout.lessonIndex.get(hit.id);
      (lesson?.conceptIds || []).forEach(addConcept);
      layout.atoms.forEach((atom) => {
        if (String(atom.lessonId) === hit.id) atoms.add(String(atom.id));
      });
      layout.edges.forEach((edge) => {
        if (concepts.has(String(edge.from)) && concepts.has(String(edge.to))) {
          edges.add(String(edge.id));
        }
      });
    } else if (hit.kind === "chapter") {
      const chapter = layout.chapterCenters.get(hit.id)?.chapter;
      (chapter?.conceptIds || []).forEach(addConcept);
      layout.atoms.forEach((atom) => {
        if (chapterKey(atom.chapterId) === chapterKey(hit.id)) atoms.add(String(atom.id));
      });
      layout.edges.forEach((edge) => {
        if (concepts.has(String(edge.from)) && concepts.has(String(edge.to))) {
          edges.add(String(edge.id));
        }
      });
    }
    if (!chapters.size && concepts.size === 1) {
      const only = layout.conceptPositions.get(Array.from(concepts)[0]);
      if (only) chapters.add(only.chapterId);
    }
    return { concepts, atoms, chapters, edges };
  }

  function create(options) {
    const opt = options || {};
    const graph = opt.courseGraph;
    const lesson = opt.lesson || {};
    const note = opt.note || {};
    const onOpenEpisode = opt.onOpenEpisode || (() => {});
    const onOpenKnowledge = opt.onOpenKnowledge || (() => {});
    const section = h("section", "kp-section kp-star-zone");

    if (!graph || !(graph.nodes || []).length) {
      section.appendChild(h("h3", "", "知识星图暂不可用"));
      section.appendChild(h("p", "kp-star-empty",
        "课程概念图还没有生成，学习、知识和复习视图仍可正常使用。"));
      return section;
    }

    const head = h("div", "kp-star-heading");
    const titleBox = h("div");
    titleBox.appendChild(h("span", "kp-overline", "全课程知识网络"));
    titleBox.appendChild(h("h3", "", "知识星图"));
    titleBox.appendChild(h("p", "", "每个光点都是一条知识；光线只表示课程里真实存在的关系。"));
    head.appendChild(titleBox);
    const stats = h("div", "kp-star-stats");
    stats.appendChild(h("span", "", (graph.nodes || []).length + " 概念"));
    stats.appendChild(h("span", "", (graph.knowledgeAtoms || []).length + " 知识光点"));
    stats.appendChild(h("span", "", (graph.edges || []).length + " 关系"));
    head.appendChild(stats);
    section.appendChild(head);

    const toolbar = h("div", "kp-star-toolbar");
    const search = h("input", "kp-star-search");
    search.type = "search";
    search.placeholder = "搜索概念或知识光点…";
    search.setAttribute("aria-label", "搜索知识星图");
    toolbar.appendChild(search);
    const filter = h("select", "kp-star-select");
    filter.setAttribute("aria-label", "选择课程章节");
    const allOption = h("option", "", "全部章节");
    allOption.value = "";
    filter.appendChild(allOption);
    (graph.chapters || []).forEach((chapter, index) => {
      const option = h("option", "", chapter.label || chapter.title || chapter.id);
      option.value = chapterKey(chapter.id);
      option.style.color = chapterColor(index);
      filter.appendChild(option);
    });
    toolbar.appendChild(filter);
    toolbar.appendChild(button("定位本讲", "kp-star-button primary", () => focusLesson()));
    toolbar.appendChild(button("全课程", "kp-star-button", () => resetView()));
    toolbar.appendChild(button("＋", "kp-star-icon", () => zoomAt(1.28)));
    toolbar.appendChild(button("－", "kp-star-icon", () => zoomAt(0.78)));
    section.appendChild(toolbar);

    const stage = h("div", "kp-star-stage");
    const canvas = h("canvas", "kp-star-canvas");
    canvas.tabIndex = 0;
    canvas.setAttribute("role", "img");
    canvas.setAttribute("aria-label", "可缩放、可点击的全课程知识星图");
    stage.appendChild(canvas);
    const tooltip = h("div", "kp-star-tooltip");
    tooltip.hidden = true;
    stage.appendChild(tooltip);
    const hint = h("div", "kp-star-help",
      "拖拽平移 · 滚轮缩放 · 点击光点查看它和谁相连");
    stage.appendChild(hint);
    const detail = h("aside", "kp-star-detail");
    detail.hidden = true;
    stage.appendChild(detail);
    section.appendChild(stage);

    const legend = h("div", "kp-star-legend");
    const legendRows = [
      ["concept", "核心概念"],
      ["atom", "知识原子"],
      ["link", "真实关系"],
      ["current", "当前讲"],
    ];
    legendRows.forEach(([kind, label]) => {
      const row = h("span", "legend-" + kind);
      row.appendChild(h("i"));
      row.appendChild(document.createTextNode(label));
      legend.appendChild(row);
    });
    section.appendChild(legend);

    const layout = buildLayout(graph, lesson);
    const currentChapterId = clean(layout.currentLesson?.chapterId || note.chapterId || "");
    let camera = { x: WORLD.cx, y: WORLD.cy, scale: 0.35 };
    let selected = null;
    let focus = null;
    let hovered = null;
    let chapterFilter = "";
    let active = false;
    let frame = 0;
    let resizeObserver = null;
    let dragging = false;
    let dragStart = null;
    let cameraChanged = true;
    let baseCanvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    const baseCtx = baseCanvas.getContext("2d");
    const dpr = Math.min(2, global.devicePixelRatio || 1);
    let size = { width: 0, height: 0 };

    canvas.dataset.concepts = String(layout.concepts.length);
    canvas.dataset.atoms = String(layout.atoms.length);
    canvas.dataset.edges = String(layout.edges.length);
    canvas.dataset.links = String(layout.atomLinks.length + layout.membershipLinks.length + layout.edges.length);
    canvas.dataset.chapters = String(layout.chapters.length);
    canvas.dataset.lessons = String(layout.lessons.length);

    function cssPoint(x, y) {
      return {
        x: size.width / 2 + (x - camera.x) * camera.scale,
        y: size.height / 2 + (y - camera.y) * camera.scale,
      };
    }

    function cameraTransform(context) {
      context.setTransform(
        dpr * camera.scale, 0, 0, dpr * camera.scale,
        dpr * (size.width / 2 - camera.x * camera.scale),
        dpr * (size.height / 2 - camera.y * camera.scale)
      );
    }

    function fitView() {
      const bounds = layout.bounds;
      const width = Math.max(1, bounds.maxX - bounds.minX);
      const height = Math.max(1, bounds.maxY - bounds.minY);
      const availableWidth = Math.max(240, size.width - 100);
      const availableHeight = Math.max(240, size.height - 90);
      camera.scale = Math.min(1.45, Math.max(0.16, Math.min(
        availableWidth / width,
        availableHeight / height
      )));
      camera.x = (bounds.minX + bounds.maxX) / 2;
      camera.y = (bounds.minY + bounds.maxY) / 2;
      cameraChanged = true;
    }

    function focusPoint(point, scale) {
      if (!point) return;
      camera.x = point.x;
      camera.y = point.y;
      camera.scale = Math.max(0.34, Math.min(2.2, scale || Math.max(camera.scale, 0.72)));
      cameraChanged = true;
    }

    function zoomAt(multiplier, sx, sy) {
      const screenX = sx == null ? size.width / 2 : sx;
      const screenY = sy == null ? size.height / 2 : sy;
      const worldX = (screenX - size.width / 2) / camera.scale + camera.x;
      const worldY = (screenY - size.height / 2) / camera.scale + camera.y;
      camera.scale = Math.max(0.16, Math.min(3.2, camera.scale * multiplier));
      camera.x = worldX - (screenX - size.width / 2) / camera.scale;
      camera.y = worldY - (screenY - size.height / 2) / camera.scale;
      cameraChanged = true;
    }

    function resize() {
      const rect = stage.getBoundingClientRect();
      const width = Math.max(1, Math.round(rect.width));
      const height = Math.max(430, Math.round(rect.height || 620));
      if (width === size.width && height === size.height && !cameraChanged) return;
      size = { width, height };
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      baseCanvas.width = canvas.width;
      baseCanvas.height = canvas.height;
      if (!layout.bounds || camera.scale === 0.35 && camera.x === WORLD.cx) fitView();
      paintBase();
      cameraChanged = false;
    }

    function worldLine(context, from, to, color, width, alpha) {
      context.beginPath();
      context.moveTo(from.x, from.y);
      context.lineTo(to.x, to.y);
      context.strokeStyle = rgba(color, alpha);
      context.lineWidth = Math.max(0.35, width / camera.scale);
      context.stroke();
    }

    function curvePath(context, edge) {
      context.beginPath();
      context.moveTo(edge.fromPoint.x, edge.fromPoint.y);
      context.quadraticCurveTo(edge.cx, edge.cy, edge.toPoint.x, edge.toPoint.y);
    }

    function edgePoint(edge, t) {
      const mt = 1 - t;
      return {
        x: mt * mt * edge.fromPoint.x + 2 * mt * t * edge.cx + t * t * edge.toPoint.x,
        y: mt * mt * edge.fromPoint.y + 2 * mt * t * edge.cy + t * t * edge.toPoint.y,
      };
    }

    function nodeAlpha(kind, id, chapterId) {
      let value = chapterFilter && chapterId !== chapterFilter ? 0.07 : 1;
      if (focus) {
        if (kind === "concept" && !focus.concepts.has(String(id))) value *= 0.08;
        if (kind === "atom" && !focus.atoms.has(String(id))) value *= 0.035;
        if (kind === "chapter" && !focus.chapters.has(String(id))) value *= 0.28;
      }
      return value;
    }

    function paintBase() {
      if (!size.width || !size.height) return;
      const context = baseCtx;
      context.setTransform(1, 0, 0, 1, 0, 0);
      context.clearRect(0, 0, baseCanvas.width, baseCanvas.height);
      const bg = context.createRadialGradient(
        size.width * 0.48, size.height * 0.48, 20,
        size.width * 0.48, size.height * 0.48, Math.max(size.width, size.height) * 0.75
      );
      bg.addColorStop(0, "#08202a");
      bg.addColorStop(0.46, "#040d15");
      bg.addColorStop(1, "#02060a");
      context.fillStyle = bg;
      context.fillRect(0, 0, baseCanvas.width, baseCanvas.height);

      cameraTransform(context);
      context.globalCompositeOperation = "lighter";
      context.shadowBlur = 0;

      const halo = context.createRadialGradient(WORLD.cx, WORLD.cy, 0, WORLD.cx, WORLD.cy, 1080);
      halo.addColorStop(0, "rgba(64,222,244,.11)");
      halo.addColorStop(0.48, "rgba(34,130,171,.045)");
      halo.addColorStop(1, "rgba(0,0,0,0)");
      context.fillStyle = halo;
      context.beginPath();
      context.arc(WORLD.cx, WORLD.cy, 1080, 0, Math.PI * 2);
      context.fill();

      [260, 520, 780, 1040].forEach((radius, index) => {
        context.beginPath();
        context.arc(WORLD.cx, WORLD.cy, radius, 0, Math.PI * 2);
        context.strokeStyle = "rgba(99,213,230," + (0.055 - index * 0.008) + ")";
        context.lineWidth = 1 / camera.scale;
        context.stroke();
      });

      layout.chapterLinks.forEach((row) => {
        const alpha = !focus || focus.chapters.has(row.chapterId) ? 0.15 : 0.035;
        worldLine(context, row.from, row.to, layout.chapterCenters.get(row.chapterId)?.color || COLORS[0], 1.1, alpha);
      });
      layout.lessonLinks.forEach((row) => {
        const chapterAlpha = !chapterFilter || chapterFilter === row.chapterId ? 0.08 : 0.015;
        worldLine(context, row.from, row.to,
          layout.chapterCenters.get(row.chapterId)?.color || COLORS[0], 0.7, chapterAlpha);
      });
      layout.membershipLinks.forEach((row) => {
        const activeLesson = layout.currentLesson && String(layout.currentLesson.id) === row.lessonId &&
          !focus;
        const alpha = activeLesson ? 0.12 : 0.024;
        worldLine(context, row.from, row.to, row.to.color || COLORS[0], 0.55, alpha);
      });

      context.globalAlpha = 1;
      layout.atomLinks.forEach((row) => {
        const inFocus = focus && focus.atoms.has(row.atomId);
        const alpha = inFocus ? 0.34 : 0.018;
        worldLine(context, row.from, row.to, row.to.color || COLORS[0], 0.38, alpha);
      });

      layout.edges.forEach((edge) => {
        const active = focus && focus.edges.has(String(edge.id));
        curvePath(context, edge);
        context.strokeStyle = active
          ? "rgba(126,242,255,.78)"
          : "rgba(86,190,214," + (focus ? 0.025 : 0.10) + ")";
        context.lineWidth = Math.max(0.32, (active ? 1.1 : 0.62) / camera.scale);
        context.stroke();
      });

      const atomsByColor = new Map();
      layout.atomPositions.forEach((row, id) => {
        const alpha = nodeAlpha("atom", id, row.chapterId);
        const key = row.color + ":" + (alpha > 0.3 ? "focus" : "dim");
        if (!atomsByColor.has(key)) {
          atomsByColor.set(key, { color: row.color, alpha, rows: [] });
        }
        atomsByColor.get(key).rows.push(row);
      });
      atomsByColor.forEach((group) => {
        context.globalAlpha = group.alpha;
        context.fillStyle = group.color;
        const radius = Math.max(0.58, 0.72 / camera.scale);
        context.beginPath();
        group.rows.forEach((row) => {
          context.moveTo(row.x + radius, row.y);
          context.arc(row.x, row.y, radius, 0, Math.PI * 2);
        });
        context.fill();
      });

      const conceptsByColor = new Map();
      layout.conceptPositions.forEach((row, id) => {
        const alpha = nodeAlpha("concept", id, row.chapterId);
        const key = row.color + ":" + (alpha > 0.3 ? "focus" : "dim");
        if (!conceptsByColor.has(key)) {
          conceptsByColor.set(key, { color: row.color, alpha, rows: [] });
        }
        conceptsByColor.get(key).rows.push({ id, ...row });
      });
      conceptsByColor.forEach((group) => {
        context.globalAlpha = group.alpha;
        group.rows.forEach((row) => {
          const degree = layout.adjacency.get(row.id)?.size || 0;
          const current = layout.currentConceptIds.has(row.id);
          const isSelected = selected?.kind === "concept" && selected.id === row.id;
          const radius = Math.max(1.15, ((isSelected ? 5.2 : current ? 3.4 : 2.4) +
            Math.min(2.2, degree * 0.09)) / camera.scale);
          const glow = context.createRadialGradient(row.x, row.y, 0, row.x, row.y, radius * 3.6);
          glow.addColorStop(0, rgba(group.color, 0.95));
          glow.addColorStop(0.28, rgba(group.color, 0.48));
          glow.addColorStop(1, rgba(group.color, 0));
          context.fillStyle = glow;
          context.beginPath();
          context.arc(row.x, row.y, radius * 3.6, 0, Math.PI * 2);
          context.fill();
          context.fillStyle = "rgba(240,255,255,.94)";
          context.beginPath();
          context.arc(row.x, row.y, Math.max(0.7, radius * 0.52), 0, Math.PI * 2);
          context.fill();
        });
      });

      layout.lessonHubs.forEach((hub) => {
        const alpha = chapterFilter && hub.chapterId !== chapterFilter ? 0.05 : 0.28;
        context.globalAlpha = alpha;
        context.fillStyle = hub.color;
        context.beginPath();
        context.arc(hub.x, hub.y, Math.max(1.1, 1.8 / camera.scale), 0, Math.PI * 2);
        context.fill();
      });

      layout.chapterCenters.forEach((row, id) => {
        const alpha = nodeAlpha("chapter", id, id);
        context.globalAlpha = alpha;
        const radius = Math.max(4, 8 / camera.scale);
        const glow = context.createRadialGradient(row.x, row.y, 0, row.x, row.y, radius * 5);
        glow.addColorStop(0, rgba(row.color, 0.8));
        glow.addColorStop(0.3, rgba(row.color, 0.26));
        glow.addColorStop(1, rgba(row.color, 0));
        context.fillStyle = glow;
        context.beginPath();
        context.arc(row.x, row.y, radius * 5, 0, Math.PI * 2);
        context.fill();
        context.fillStyle = "rgba(235,255,255,.92)";
        context.beginPath();
        context.arc(row.x, row.y, radius * 0.62, 0, Math.PI * 2);
        context.fill();
      });

      const centerAlpha = focus && !focus.chapters.size ? 0.2 : 1;
      context.globalAlpha = centerAlpha;
      const coreGlow = context.createRadialGradient(WORLD.cx, WORLD.cy, 0, WORLD.cx, WORLD.cy, 92);
      coreGlow.addColorStop(0, "rgba(230,255,255,.94)");
      coreGlow.addColorStop(0.12, "rgba(90,230,250,.5)");
      coreGlow.addColorStop(1, "rgba(30,130,190,0)");
      context.fillStyle = coreGlow;
      context.beginPath();
      context.arc(WORLD.cx, WORLD.cy, 92, 0, Math.PI * 2);
      context.fill();
      context.globalAlpha = 1;
      context.globalCompositeOperation = "source-over";

      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      drawStaticLabels(context);
    }

    function label(context, text, sx, sy, color, sizePx, align) {
      context.font = "700 " + sizePx + "px 'Microsoft YaHei UI', 'PingFang SC', sans-serif";
      context.textAlign = align || "center";
      context.textBaseline = "middle";
      context.lineWidth = Math.max(2, sizePx / 5);
      context.strokeStyle = "rgba(1,7,11,.86)";
      context.strokeText(text, sx, sy);
      context.fillStyle = color;
      context.fillText(text, sx, sy);
    }

    function drawStaticLabels(context) {
      const coursePoint = cssPoint(WORLD.cx, WORLD.cy);
      label(context, clean(graph.course || "全课程"), coursePoint.x, coursePoint.y - 27,
        "#d9fbff", 16);
      label(context, "课程主干", coursePoint.x, coursePoint.y + 27,
        "rgba(132,196,210,.8)", 10);

      layout.chapterCenters.forEach((row, id) => {
        const alpha = chapterFilter && id !== chapterFilter ? 0.18 : 1;
        context.globalAlpha = alpha;
        const point = cssPoint(row.x, row.y);
        const chapter = row.chapter;
        const title = clean(chapter.label || chapter.title || id).replace(/^第/, "第");
        const short = title.length > 18 ? title.slice(0, 18) + "…" : title;
        label(context, short, point.x, point.y + 25, row.color, 12);
      });
      context.globalAlpha = 1;

      if (layout.currentLesson) {
        const lessonHub = layout.lessonHubs.get(String(layout.currentLesson.id));
        if (lessonHub) {
          const point = cssPoint(lessonHub.x, lessonHub.y);
          label(context, "当前 · E" + String(layout.currentLesson.episode).padStart(2, "0"),
            point.x, point.y - 22, "#f6d58d", 10);
        }
      }
    }

    function drawFrame(time) {
      if (!active || !size.width) return;
      if (cameraChanged) {
        paintBase();
        cameraChanged = false;
      }
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.drawImage(baseCanvas, 0, 0);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.globalCompositeOperation = "lighter";
      const activeEdges = focus
        ? layout.edges.filter((edge) => focus.edges.has(String(edge.id))).slice(0, 80)
        : layout.edges.filter((_, index) => index % 29 === 0).slice(0, 34);
      activeEdges.forEach((edge, index) => {
        const from = cssPoint(edge.fromPoint.x, edge.fromPoint.y);
        const control = cssPoint(edge.cx, edge.cy);
        const to = cssPoint(edge.toPoint.x, edge.toPoint.y);
        const gradient = ctx.createLinearGradient(from.x, from.y, to.x, to.y);
        gradient.addColorStop(0, rgba(edge.fromPoint.color, focus ? 0.46 : 0.12));
        gradient.addColorStop(0.5, focus ? "rgba(145,248,255,.56)" : "rgba(92,213,230,.15)");
        gradient.addColorStop(1, rgba(edge.toPoint.color, focus ? 0.46 : 0.12));
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.quadraticCurveTo(control.x, control.y, to.x, to.y);
        ctx.strokeStyle = gradient;
        ctx.lineWidth = focus ? 1.4 : 0.7;
        ctx.shadowColor = "#5bdcf2";
        ctx.shadowBlur = focus ? 12 : 5;
        ctx.stroke();
        ctx.shadowBlur = 0;
        const t = ((time * 0.00013 + index * 0.173) % 1);
        const mt = 1 - t;
        const px = mt * mt * from.x + 2 * mt * t * control.x + t * t * to.x;
        const py = mt * mt * from.y + 2 * mt * t * control.y + t * t * to.y;
        ctx.fillStyle = focus ? "rgba(230,255,255,.95)" : "rgba(174,242,251,.5)";
        ctx.beginPath();
        ctx.arc(px, py, focus ? 1.8 : 1.1, 0, Math.PI * 2);
        ctx.fill();
      });

      if (selected) {
        const hit = selected.kind === "concept"
          ? layout.conceptPositions.get(selected.id)
          : selected.kind === "atom"
            ? layout.atomPositions.get(selected.id)
            : selected.kind === "chapter"
              ? layout.chapterCenters.get(selected.id)
              : null;
        if (hit) {
          const point = cssPoint(hit.x, hit.y);
          ctx.strokeStyle = "rgba(235,255,255,.82)";
          ctx.lineWidth = 1.4;
          ctx.beginPath();
          ctx.arc(point.x, point.y, 8 + Math.sin(time * 0.006) * 1.6, 0, Math.PI * 2);
          ctx.stroke();
          const title = selected.kind === "concept"
            ? layout.conceptIndex.get(selected.id)?.label
            : selected.kind === "atom"
              ? layout.atomPositions.get(selected.id)?.atom?.label
              : layout.chapterCenters.get(selected.id)?.chapter?.label;
          if (title) label(ctx, title, point.x + 12, point.y - 12, "#f0fdff", 12, "left");
        }
      }
      ctx.globalCompositeOperation = "source-over";
      frame = global.requestAnimationFrame(drawFrame);
    }

    function startLoop() {
      if (frame) return;
      frame = global.requestAnimationFrame(drawFrame);
    }

    function stopLoop() {
      if (frame) global.cancelAnimationFrame(frame);
      frame = 0;
    }

    function focusForHit(hit) {
      selected = hit || null;
      focus = focusSets(layout, selected);
      cameraChanged = true;
      renderDetail();
    }

    function renderDetail() {
      detail.innerHTML = "";
      if (!selected) {
        detail.hidden = true;
        return;
      }
      detail.hidden = false;
      const close = button("×", "kp-star-close", () => focusForHit(null));
      detail.appendChild(close);

      if (selected.kind === "concept") {
        const point = layout.conceptPositions.get(selected.id);
        const concept = layout.conceptIndex.get(selected.id);
        if (!point || !concept) return;
        const chapter = chapterFor(graph, point.chapterId);
        const occurrence = (concept.occurrences || [])[0] || {};
        detail.appendChild(h("span", "kp-star-breadcrumb",
          clean(graph.course) + " / " + clean(chapter?.label || point.chapterId) +
          (occurrence.episode ? " / E" + String(occurrence.episode).padStart(2, "0") : "")));
        detail.appendChild(h("h4", "", concept.label));
        detail.appendChild(h("p", "", concept.summary || "这张知识卡还没有摘要。"));
        const neighbors = Array.from(layout.adjacency.get(selected.id) || []);
        if (neighbors.length) {
          const related = h("div", "kp-star-related");
          related.appendChild(h("b", "", "直接相连 " + neighbors.length + " 个"));
          neighbors.slice(0, 7).forEach((id) => {
            const next = layout.conceptIndex.get(id);
            if (next) related.appendChild(button(next.label, "kp-star-chip", () => {
              focusForHit({ kind: "concept", id });
              focusPoint(layout.conceptPositions.get(id), Math.max(camera.scale, 1.05));
            }));
          });
          detail.appendChild(related);
        }
        const occurrences = h("div", "kp-star-occurrences");
        (concept.occurrences || []).slice(0, 8).forEach((row) => {
          if (!row.episodeId) return;
          occurrences.appendChild(button("E" + String(row.episode).padStart(2, "0"),
            "kp-star-episode", () => onOpenEpisode(row.episodeId)));
        });
        if (occurrences.children.length) {
          occurrences.prepend(h("b", "", "出现在这些讲"));
          detail.appendChild(occurrences);
        }
      } else if (selected.kind === "atom") {
        const row = layout.atomPositions.get(selected.id);
        const atom = row?.atom;
        if (!row || !atom) return;
        const concept = layout.conceptIndex.get(row.conceptId);
        const lessonRow = lessonFor(graph, atom.episode);
        const chapter = chapterFor(graph, atom.chapterId);
        detail.appendChild(h("span", "kp-star-breadcrumb",
          clean(graph.course) + " / " + clean(chapter?.label || atom.chapterId) +
          " / E" + String(atom.episode).padStart(2, "0")));
        detail.appendChild(h("span", "kp-star-kind", atom.kind || "知识原子"));
        detail.appendChild(h("h4", "", atom.label || atom.claim || "知识光点"));
        if (atom.claim && atom.claim !== atom.label) detail.appendChild(h("p", "", atom.claim));
        const actions = h("div", "kp-star-occurrences");
        if (atom.time) actions.appendChild(button("原片 " + atom.time, "kp-star-episode",
          () => opt.onSeek && opt.onSeek(atom.time)));
        if (lessonRow?.episodeId) actions.appendChild(button("打开本讲", "kp-star-episode",
          () => onOpenEpisode(lessonRow.episodeId)));
        if (concept) actions.appendChild(button("回到锚点 · " + concept.label, "kp-star-chip",
          () => {
            focusForHit({ kind: "concept", id: concept.id });
            focusPoint(layout.conceptPositions.get(concept.id), Math.max(camera.scale, 1.05));
          }));
        detail.appendChild(actions);
      } else if (selected.kind === "lesson") {
        const current = layout.lessonIndex.get(selected.id);
        if (!current) return;
        const chapter = chapterFor(graph, current.chapterId);
        detail.appendChild(h("span", "kp-star-breadcrumb",
          clean(graph.course) + " / " + clean(chapter?.label || current.chapterId)));
        detail.appendChild(h("h4", "", "E" + String(current.episode).padStart(2, "0") + " · " + current.label));
        detail.appendChild(h("p", "", "这一讲贡献 " + (current.conceptIds || []).length +
          " 个核心锚点、" + (current.knowledgeAtomCount || 0) + " 条知识光点。"));
        if (current.episodeId) detail.appendChild(button("打开本讲", "kp-star-episode",
          () => onOpenEpisode(current.episodeId)));
      } else if (selected.kind === "chapter") {
        const chapter = chapterFor(graph, selected.id);
        const center = layout.chapterCenters.get(selected.id);
        if (!chapter || !center) return;
        detail.appendChild(h("span", "kp-star-breadcrumb", clean(graph.course)));
        detail.appendChild(h("h4", "", chapter.label || selected.id));
        detail.appendChild(h("p", "", (chapter.episodes || []).length + " 讲、" +
          (chapter.conceptIds || []).length + " 个概念、" +
          (chapter.atomIds || []).length + " 条知识光点。"));
      }

      detail.appendChild(button("打开完整知识库", "kp-star-open", onOpenKnowledge));
    }

    function hitTest(sx, sy) {
      let best = null;
      let bestDistance = Infinity;
      layout.conceptPositions.forEach((row, id) => {
        const point = cssPoint(row.x, row.y);
        const distance = Math.hypot(point.x - sx, point.y - sy);
        const threshold = 11;
        if (distance <= threshold && distance < bestDistance) {
          bestDistance = distance;
          best = { kind: "concept", id };
        }
      });
      if (best) return best;
      layout.atomPositions.forEach((row, id) => {
        const point = cssPoint(row.x, row.y);
        const distance = Math.hypot(point.x - sx, point.y - sy);
        if (distance <= 7 && distance < bestDistance) {
          bestDistance = distance;
          best = { kind: "atom", id };
        }
      });
      if (best) return best;
      layout.chapterCenters.forEach((row, id) => {
        const point = cssPoint(row.x, row.y);
        const distance = Math.hypot(point.x - sx, point.y - sy);
        if (distance <= 18 && distance < bestDistance) {
          bestDistance = distance;
          best = { kind: "chapter", id };
        }
      });
      return best;
    }

    function hitLabel(hit) {
      if (!hit) return "";
      if (hit.kind === "concept") return layout.conceptIndex.get(hit.id)?.label || "核心概念";
      if (hit.kind === "atom") return layout.atomPositions.get(hit.id)?.atom?.label || "知识光点";
      if (hit.kind === "chapter") return layout.chapterCenters.get(hit.id)?.chapter?.label || "章节";
      return "";
    }

    function pointerPosition(event) {
      const rect = canvas.getBoundingClientRect();
      return { x: event.clientX - rect.left, y: event.clientY - rect.top };
    }

    function updateTooltip(hit, point) {
      hovered = hit;
      if (!hit) {
        tooltip.hidden = true;
        canvas.style.cursor = dragging ? "grabbing" : "grab";
        return;
      }
      tooltip.textContent = hitLabel(hit);
      tooltip.hidden = false;
      tooltip.style.left = Math.min(size.width - 180, point.x + 13) + "px";
      tooltip.style.top = Math.max(8, point.y - 15) + "px";
      canvas.style.cursor = "pointer";
    }

    canvas.addEventListener("pointerdown", (event) => {
      const point = pointerPosition(event);
      dragging = true;
      canvas.setPointerCapture?.(event.pointerId);
      dragStart = { ...point, cameraX: camera.x, cameraY: camera.y, moved: false };
      canvas.style.cursor = "grabbing";
    });
    canvas.addEventListener("pointermove", (event) => {
      const point = pointerPosition(event);
      if (dragging && dragStart) {
        const dx = point.x - dragStart.x;
        const dy = point.y - dragStart.y;
        if (Math.abs(dx) + Math.abs(dy) > 3) dragStart.moved = true;
        camera.x = dragStart.cameraX - dx / camera.scale;
        camera.y = dragStart.cameraY - dy / camera.scale;
        cameraChanged = true;
        tooltip.hidden = true;
        return;
      }
      updateTooltip(hitTest(point.x, point.y), point);
    });
    function endDrag(event) {
      if (!dragging) return;
      const point = pointerPosition(event);
      const moved = dragStart && dragStart.moved;
      dragging = false;
      canvas.releasePointerCapture?.(event.pointerId);
      canvas.style.cursor = "grab";
      if (!moved) {
        const hit = hitTest(point.x, point.y);
        focusForHit(hit);
      }
      dragStart = null;
    }
    canvas.addEventListener("pointerup", endDrag);
    canvas.addEventListener("pointercancel", endDrag);
    canvas.addEventListener("pointerleave", () => {
      if (!dragging) {
        hovered = null;
        tooltip.hidden = true;
      }
    });
    canvas.addEventListener("wheel", (event) => {
      event.preventDefault();
      const point = pointerPosition(event);
      zoomAt(event.deltaY < 0 ? 1.12 : 0.89, point.x, point.y);
    }, { passive: false });
    canvas.addEventListener("keydown", (event) => {
      if (event.key === "+" || event.key === "=") zoomAt(1.2);
      if (event.key === "-") zoomAt(0.82);
      if (event.key === "0") resetView();
    });

    let resizeTimer = 0;
    function scheduleResize() {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(resize, 40);
    }
    if (global.ResizeObserver) {
      resizeObserver = new ResizeObserver(scheduleResize);
      resizeObserver.observe(stage);
    } else {
      global.addEventListener("resize", scheduleResize);
    }

    function resetView() {
      chapterFilter = "";
      filter.value = "";
      selected = null;
      focus = null;
      fitView();
      renderDetail();
    }

    function focusLesson() {
      const current = layout.currentLesson;
      if (!current) {
        const first = layout.lessons[0];
        if (first) {
          selected = { kind: "lesson", id: String(first.id) };
          focus = focusSets(layout, selected);
        }
      } else {
        selected = { kind: "lesson", id: String(current.id) };
        focus = focusSets(layout, selected);
      }
      const lessonId = selected?.id;
      const hub = lessonId ? layout.lessonHubs.get(lessonId) : null;
      if (hub) focusPoint(hub, 0.92);
      else resetView();
      renderDetail();
    }

    filter.addEventListener("change", () => {
      chapterFilter = filter.value;
      if (!chapterFilter) {
        focusForHit(null);
        fitView();
        return;
      }
      const center = layout.chapterCenters.get(chapterFilter);
      if (center) {
        focusForHit({ kind: "chapter", id: chapterFilter });
        focusPoint(center, 0.78);
      }
    });

    search.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      const query = search.value.trim().toLowerCase();
      if (!query) return;
      let conceptMatch = null;
      layout.conceptPositions.forEach((row, id) => {
        const concept = layout.conceptIndex.get(id);
        if (!conceptMatch && String(concept?.label || "").toLowerCase().includes(query)) {
          conceptMatch = { kind: "concept", id };
        }
      });
      if (conceptMatch) {
        focusForHit(conceptMatch);
        focusPoint(layout.conceptPositions.get(conceptMatch.id), 1.08);
        return;
      }
      let atomMatch = null;
      layout.atomPositions.forEach((row, id) => {
        if (atomMatch) return;
        const atom = row.atom || {};
        if ((String(atom.label || "") + " " + String(atom.claim || ""))
          .toLowerCase().includes(query)) {
          atomMatch = { kind: "atom", id };
        }
      });
      if (atomMatch) {
        focusForHit(atomMatch);
        focusPoint(layout.atomPositions.get(atomMatch.id), 1.35);
      }
    });

    section._kpActivate = (next) => {
      active = Boolean(next);
      if (active) {
        resize();
        if (cameraChanged) {
          paintBase();
          cameraChanged = false;
        }
        startLoop();
      } else {
        stopLoop();
      }
    };
    section._kpDestroy = () => {
      stopLoop();
      if (resizeObserver) resizeObserver.disconnect();
      clearTimeout(resizeTimer);
    };
    section._kpFocusLesson = focusLesson;
    return section;
  }

  const api = { create, buildLayout };
  global.VKSStarMap = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
