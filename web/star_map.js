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
  const EDGE_COLORS = {
    prerequisite: "#65b9ff",
    mechanism: "#62e5b5",
    cause: "#f1c36e",
    contrast: "#ef928a",
    example: "#b09bff",
    application: "#7ba8ff",
    grouping: "#8da3ad",
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

    const hierarchyConceptPositions = new Map(
      Array.from(conceptPositions, ([id, row]) => [id, { x: row.x, y: row.y }])
    );

    // Start from the course/lesson hierarchy, then let evidence-backed edges shape
    // the final constellation. Chapter and lesson gravity preserve the curriculum.
    const conceptIds = Array.from(conceptPositions.keys());
    const conceptRows = conceptIds.map((id) => conceptPositions.get(id));
    const conceptCount = conceptRows.length;
    const positionX = new Float64Array(conceptCount);
    const positionY = new Float64Array(conceptCount);
    const displacementX = new Float64Array(conceptCount);
    const displacementY = new Float64Array(conceptCount);
    const conceptOrdinal = new Map(conceptIds.map((id, index) => [id, index]));
    conceptRows.forEach((row, index) => {
      positionX[index] = row.x;
      positionY[index] = row.y;
    });
    const edgeOrdinals = edges.map((edge) => {
      const left = conceptOrdinal.get(String(edge.from));
      const right = conceptOrdinal.get(String(edge.to));
      return left == null || right == null ? null : { left, right };
    }).filter(Boolean);
    const iterationCount = conceptCount > 520 ? 38 : conceptCount > 360 ? 46 : 54;
    for (let iteration = 0; iteration < iterationCount; iteration += 1) {
      displacementX.fill(0);
      displacementY.fill(0);
      for (let leftIndex = 0; leftIndex < conceptCount; leftIndex += 1) {
        const leftX = positionX[leftIndex];
        const leftY = positionY[leftIndex];
        for (let rightIndex = leftIndex + 1; rightIndex < conceptCount; rightIndex += 1) {
          let dx = leftX - positionX[rightIndex];
          let dy = leftY - positionY[rightIndex];
          let distance2 = dx * dx + dy * dy;
          if (distance2 < 1) {
            dx = (hashText(conceptIds[leftIndex] + conceptIds[rightIndex]) - 0.5) * 2;
            dy = (hashText(conceptIds[rightIndex] + conceptIds[leftIndex]) - 0.5) * 2;
            distance2 = dx * dx + dy * dy + 1;
          }
          const distance = Math.sqrt(distance2);
          const force = Math.min(2.2, 3900 / distance2);
          const fx = (dx / distance) * force;
          const fy = (dy / distance) * force;
          displacementX[leftIndex] += fx;
          displacementY[leftIndex] += fy;
          displacementX[rightIndex] -= fx;
          displacementY[rightIndex] -= fy;
        }
      }
      edgeOrdinals.forEach(({ left, right }) => {
        const dx = positionX[right] - positionX[left];
        const dy = positionY[right] - positionY[left];
        const distance = Math.max(1, Math.hypot(dx, dy));
        const force = Math.max(-1.7, Math.min(2.8, (distance - 118) * 0.010));
        const fx = (dx / distance) * force;
        const fy = (dy / distance) * force;
        displacementX[left] += fx;
        displacementY[left] += fy;
        displacementX[right] -= fx;
        displacementY[right] -= fy;
      });
      for (let index = 0; index < conceptCount; index += 1) {
        const row = conceptRows[index];
        const chapter = chapterCenters.get(row.chapterId);
        if (chapter) {
          const dx = positionX[index] - chapter.x;
          const dy = positionY[index] - chapter.y;
          const distance = Math.max(1, Math.hypot(dx, dy));
          if (distance > 250) {
            const pull = Math.min(1.6, (distance - 250) * 0.004);
            displacementX[index] -= (dx / distance) * pull;
            displacementY[index] -= (dy / distance) * pull;
          }
        }
        const hub = lessonHubs.get(row.lessonId);
        if (hub) {
          const dx = positionX[index] - hub.x;
          const dy = positionY[index] - hub.y;
          const distance = Math.max(1, Math.hypot(dx, dy));
          if (distance > 105) {
            const pull = Math.min(1.1, (distance - 105) * 0.0028);
            displacementX[index] -= (dx / distance) * pull;
            displacementY[index] -= (dy / distance) * pull;
          }
        }
        positionX[index] += Math.max(-4.2, Math.min(4.2, displacementX[index] * 0.58));
        positionY[index] += Math.max(-4.2, Math.min(4.2, displacementY[index] * 0.58));
      }
    }
    conceptRows.forEach((row, index) => {
      row.x = positionX[index];
      row.y = positionY[index];
    });
    conceptPositions.forEach((row, id) => {
      const base = hierarchyConceptPositions.get(id);
      row.baseX = base?.x ?? row.x;
      row.baseY = base?.y ?? row.y;
      row.networkX = row.x;
      row.networkY = row.y;
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
      const basePos = hierarchyConceptPositions.get(conceptId);
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
        const basePoint = basePos || fallbackCenter;
        const color = chapterCenters.get(chapterId)?.color || (pos?.color || fallbackCenter.color);
        atomPositions.set(id, {
          atom,
          conceptId,
          chapterId,
          x: point.x + Math.cos(angle) * distance,
          y: point.y + Math.sin(angle) * distance * 0.86,
          baseX: basePoint.x + Math.cos(angle) * distance,
          baseY: basePoint.y + Math.sin(angle) * distance * 0.86,
          networkX: point.x + Math.cos(angle) * distance,
          networkY: point.y + Math.sin(angle) * distance * 0.86,
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
        color: EDGE_COLORS[edge.type] || "#65d8ea",
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

    const chapterFlow = (graph.chapterFlow || []).map((edge, index) => {
      const leftId = chapterKey(edge.from);
      const rightId = chapterKey(edge.to);
      const left = chapterCenters.get(leftId);
      const right = chapterCenters.get(rightId);
      if (!left || !right) return null;
      const midX = (left.x + right.x) / 2;
      const midY = (left.y + right.y) / 2;
      const dx = midX - WORLD.cx;
      const dy = midY - WORLD.cy;
      const length = Math.max(1, Math.hypot(dx, dy));
      const bend = 90 + index * 12;
      return {
        ...edge,
        fromId: leftId,
        toId: rightId,
        fromPoint: left,
        toPoint: right,
        color: EDGE_COLORS[edge.type] || EDGE_COLORS.prerequisite,
        cx: midX + (dx / length) * bend,
        cy: midY + (dy / length) * bend,
      };
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
      chapterFlow,
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

    let qualityMode = "auto";
    let resolvedQuality = "smooth";
    const toolbar = h("div", "kp-star-toolbar");
    const searchWrap = h("div", "kp-star-search-wrap");
    const search = h("input", "kp-star-search");
    search.type = "search";
    search.placeholder = "搜索概念或知识光点…";
    search.setAttribute("aria-label", "搜索知识星图");
    searchWrap.appendChild(search);
    const suggestions = h("div", "kp-star-suggestions");
    suggestions.hidden = true;
    searchWrap.appendChild(suggestions);
    toolbar.appendChild(searchWrap);
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
    const layoutSelect = h("select", "kp-star-select");
    layoutSelect.setAttribute("aria-label", "选择图谱布局");
    [
      ["structure", "体系导图"],
      ["balanced", "混合结构"],
      ["relations", "关系网络"],
    ].forEach(([value, label]) => {
      const option = h("option", "", label);
      option.value = value;
      if (value === "relations") option.selected = true;
      layoutSelect.appendChild(option);
    });
    toolbar.appendChild(layoutSelect);
    const qualitySelect = h("select", "kp-star-select kp-star-quality");
    qualitySelect.setAttribute("aria-label", "选择星图性能模式");
    [
      ["auto", "自动性能"],
      ["smooth", "流畅优先"],
      ["cinematic", "画质优先"],
    ].forEach(([value, label]) => {
      const option = h("option", "", label);
      option.value = value;
      qualitySelect.appendChild(option);
    });
    toolbar.appendChild(qualitySelect);
    toolbar.appendChild(button("定位本讲", "kp-star-button primary", () => focusLesson()));
    toolbar.appendChild(button("全课程", "kp-star-button", () => resetView()));
    const isolateButton = button("邻域聚焦", "kp-star-button active", () => {
      isolateNeighborhood = !isolateNeighborhood;
      isolateButton.classList.toggle("active", isolateNeighborhood);
      isolateButton.setAttribute("aria-pressed", isolateNeighborhood ? "true" : "false");
      cameraChanged = true;
      noteInteraction(500);
    });
    isolateButton.setAttribute("aria-pressed", "true");
    toolbar.appendChild(isolateButton);
    toolbar.appendChild(button("＋", "kp-star-icon", () => zoomAt(1.28)));
    toolbar.appendChild(button("－", "kp-star-icon", () => zoomAt(0.78)));
    section.appendChild(toolbar);

    const relationFilters = h("details", "kp-star-relation-filters");
    const relationSummary = h("summary");
    relationSummary.appendChild(h("b", "", "关系筛选"));
    relationSummary.appendChild(h("span", "", Object.keys(TYPE_LABELS).length + " 类光线"));
    relationFilters.appendChild(relationSummary);
    const relationGrid = h("div", "kp-star-relation-filter-grid");
    const relationButtons = {};
    Object.entries(TYPE_LABELS).forEach(([type, label]) => {
      const filterButton = h("button", "kp-star-filter active", label);
      filterButton.type = "button";
      filterButton.dataset.relationType = type;
      filterButton.style.setProperty("--edge-color", EDGE_COLORS[type] || "#75dbe8");
      filterButton.setAttribute("aria-pressed", "true");
      filterButton.onclick = () => {
        if (allowedTypes.has(type)) allowedTypes.delete(type);
        else allowedTypes.add(type);
        filterButton.classList.toggle("active", allowedTypes.has(type));
        filterButton.setAttribute("aria-pressed", allowedTypes.has(type) ? "true" : "false");
        cameraChanged = true;
        noteInteraction(500);
        renderDetail();
      };
      relationButtons[type] = filterButton;
      relationGrid.appendChild(filterButton);
    });
    relationGrid.appendChild(button("全部显示", "kp-star-filter-all", () => {
      Object.keys(TYPE_LABELS).forEach((type) => allowedTypes.add(type));
      Object.entries(relationButtons).forEach(([type, item]) => {
        item.classList.add("active");
        item.setAttribute("aria-pressed", "true");
      });
      cameraChanged = true;
      noteInteraction(500);
      renderDetail();
    }));
    relationFilters.appendChild(relationGrid);
    section.appendChild(relationFilters);

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
    const depthBadge = h("div", "kp-star-depth", "课程总览");
    stage.appendChild(depthBadge);
    const performanceBadge = h("div", "kp-star-performance", "自动 · 流畅");
    stage.appendChild(performanceBadge);
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
    const ambientStars = Array.from({ length: 360 }, (_, index) => {
      const seed = hashText("ambient:" + index);
      const seed2 = hashText("ambient-y:" + index);
      const seed3 = hashText("ambient-r:" + index);
      return {
        x: 230 + seed * (WORLD.width - 460),
        y: 130 + seed2 * (WORLD.height - 260),
        size: 0.45 + seed3 * 1.15,
        alpha: 0.08 + seed3 * 0.23,
      };
    });
    const currentChapterId = clean(layout.currentLesson?.chapterId || note.chapterId || "");
    let camera = { x: WORLD.cx, y: WORLD.cy, scale: 0.35 };
    let selected = null;
    let focus = null;
    let hovered = null;
    let chapterFilter = "";
    let isolateNeighborhood = true;
    const allowedTypes = new Set(Object.keys(TYPE_LABELS));
    let suggestionHits = [];
    let relationBlend = 1;
    let active = false;
    let raf = 0;
    let timer = 0;
    let resizeObserver = null;
    let dragging = false;
    let dragStart = null;
    let cameraChanged = true;
    let qualityDirty = true;
    let quickPreviewUntil = 0;
    let animationUntil = 0;
    let lastInteractionAt = 0;
    let frameCount = 0;
    let sampledAt = 0;
    let sampledFrames = 0;
    let measuredFps = 0;
    let lastFrameAt = 0;
    const frameInterval = 1000 / 30;
    const heavyGraph = (graph.nodes || []).length > 420 ||
      (graph.knowledgeAtoms || []).length > 2200;
    const baseCanvas = document.createElement("canvas");
    const backgroundCanvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    const baseCtx = baseCanvas.getContext("2d");
    const backgroundCtx = backgroundCanvas.getContext("2d");
    const glowSprites = new Map();
    let dpr = 1;
    let size = { width: 0, height: 0 };

    function resolveQuality() {
      if (qualityMode === "auto") return heavyGraph ? "smooth" : "cinematic";
      return qualityMode;
    }

    function qualityDpr() {
      const ceiling = resolvedQuality === "cinematic" ? 2 : 1.25;
      return Math.max(1, Math.min(ceiling, global.devicePixelRatio || 1));
    }

    function glowSprite(color) {
      const key = clean(color || COLORS[0]);
      if (glowSprites.has(key)) return glowSprites.get(key);
      const sprite = document.createElement("canvas");
      sprite.width = 128;
      sprite.height = 128;
      const spriteContext = sprite.getContext("2d");
      const glow = spriteContext.createRadialGradient(64, 64, 0, 64, 64, 64);
      glow.addColorStop(0, rgba(key, 0.92));
      glow.addColorStop(0.24, rgba(key, 0.38));
      glow.addColorStop(1, rgba(key, 0));
      spriteContext.fillStyle = glow;
      spriteContext.fillRect(0, 0, 128, 128);
      glowSprites.set(key, sprite);
      return sprite;
    }

    function drawGlow(context, color, x, y, radius, alpha) {
      const sprite = glowSprite(color);
      const previous = context.globalAlpha;
      context.globalAlpha = previous * alpha;
      context.drawImage(sprite, x - radius, y - radius, radius * 2, radius * 2);
      context.globalAlpha = previous;
    }

    function fillArcBatch(context, rows, color, alpha, radiusFor) {
      if (!rows.length) return;
      context.globalAlpha = alpha;
      context.fillStyle = color;
      context.beginPath();
      rows.forEach((row) => {
        const radius = radiusFor(row);
        context.moveTo(row.x + radius, row.y);
        context.arc(row.x, row.y, radius, 0, Math.PI * 2);
      });
      context.fill();
    }

    function strokeLineBatch(context, rows, color, width, alpha) {
      if (!rows.length) return;
      context.globalAlpha = 1;
      context.beginPath();
      rows.forEach((row) => {
        context.moveTo(row.from.x, row.from.y);
        context.lineTo(row.to.x, row.to.y);
      });
      context.strokeStyle = rgba(color, alpha);
      context.lineWidth = Math.max(0.35, width / camera.scale);
      context.stroke();
    }

    function strokeCurveBatch(context, rows, color, width, alpha) {
      if (!rows.length) return;
      context.globalAlpha = 1;
      context.beginPath();
      rows.forEach((edge) => {
        context.moveTo(edge.fromPoint.x, edge.fromPoint.y);
        context.quadraticCurveTo(edge.cx, edge.cy, edge.toPoint.x, edge.toPoint.y);
      });
      context.strokeStyle = rgba(color, alpha);
      context.lineWidth = Math.max(0.34, width / camera.scale);
      context.stroke();
    }

    resolvedQuality = resolveQuality();
    dpr = qualityDpr();

    canvas.dataset.concepts = String(layout.concepts.length);
    canvas.dataset.atoms = String(layout.atoms.length);
    canvas.dataset.edges = String(layout.edges.length);
    canvas.dataset.links = String(layout.atomLinks.length + layout.membershipLinks.length + layout.edges.length);
    canvas.dataset.chapters = String(layout.chapters.length);
    canvas.dataset.lessons = String(layout.lessons.length);
    canvas.dataset.layout = "relations";
    canvas.dataset.performanceMode = qualityMode;
    canvas.dataset.resolvedQuality = resolvedQuality;
    canvas.dataset.frameState = "idle";
    canvas.dataset.frames = "0";
    canvas.dataset.fps = "0";
    canvas.dataset.dpr = String(dpr);
    performanceBadge.textContent = "自动 · " +
      (resolvedQuality === "smooth" ? "流畅" : "画质");

    function cssPoint(x, y) {
      return {
        x: size.width / 2 + (x - camera.x) * camera.scale,
        y: size.height / 2 + (y - camera.y) * camera.scale,
      };
    }

    function updateDepthBadge() {
      if (relationBlend < 0.35) {
        depthBadge.textContent = "体系导图";
      } else if (relationBlend < 0.85) {
        depthBadge.textContent = "混合结构";
      } else {
        depthBadge.textContent = camera.scale < 0.46
          ? "课程总览"
          : camera.scale < 0.9
            ? "章节结构"
            : "知识细节";
      }
    }

    function cameraTransform(context) {
      context.setTransform(
        dpr * camera.scale, 0, 0, dpr * camera.scale,
        dpr * (size.width / 2 - camera.x * camera.scale),
        dpr * (size.height / 2 - camera.y * camera.scale)
      );
    }

    function cancelScheduledRender() {
      if (timer) global.clearTimeout(timer);
      if (raf) global.cancelAnimationFrame(raf);
      timer = 0;
      raf = 0;
    }

    function requestRender(animate) {
      if (!active) {
        canvas.dataset.frameState = "paused";
        return;
      }
      if (raf || timer) return;
      const now = performance.now();
      const delay = animate
        ? Math.max(0, frameInterval - Math.max(0, now - lastFrameAt))
        : 0;
      canvas.dataset.frameState = "scheduled";
      timer = global.setTimeout(() => {
        timer = 0;
        if (!active) return;
        raf = global.requestAnimationFrame(drawFrame);
      }, delay);
    }

    function noteInteraction(duration) {
      lastInteractionAt = performance.now();
      animationUntil = Math.max(
        animationUntil,
        lastInteractionAt + Math.max(0, Number(duration) || 1100)
      );
      requestRender(true);
    }

    function paintBackground() {
      if (!size.width || !size.height) return;
      backgroundCanvas.width = canvas.width;
      backgroundCanvas.height = canvas.height;
      backgroundCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const gradient = backgroundCtx.createRadialGradient(
        size.width * 0.48, size.height * 0.48, 20,
        size.width * 0.48, size.height * 0.48, Math.max(size.width, size.height) * 0.75
      );
      gradient.addColorStop(0, "#08202a");
      gradient.addColorStop(0.46, "#040d15");
      gradient.addColorStop(1, "#02060a");
      backgroundCtx.fillStyle = gradient;
      backgroundCtx.fillRect(0, 0, size.width, size.height);
    }

    function fitView() {
      const points = [
        ...Array.from(layout.chapterCenters.values()).map((row) => ({ x: row.x, y: row.y })),
        ...Array.from(layout.conceptPositions.values()).map((row) => ({ x: row.x, y: row.y })),
      ];
      const minX = Math.min(...points.map((row) => row.x));
      const maxX = Math.max(...points.map((row) => row.x));
      const minY = Math.min(...points.map((row) => row.y));
      const maxY = Math.max(...points.map((row) => row.y));
      const width = Math.max(1, maxX - minX);
      const height = Math.max(1, maxY - minY);
      const availableWidth = Math.max(240, size.width - 100);
      const availableHeight = Math.max(240, size.height - 90);
      camera.scale = Math.min(1.45, Math.max(0.16, Math.min(
        availableWidth / width,
        availableHeight / height
      )));
      camera.x = (minX + maxX) / 2;
      camera.y = (minY + maxY) / 2;
      cameraChanged = true;
      updateDepthBadge();
    }

    function applyLayoutBlend(value) {
      relationBlend = Math.max(0, Math.min(1, Number(value)));
      layout.conceptPositions.forEach((row) => {
        row.x = row.baseX * (1 - relationBlend) + row.networkX * relationBlend;
        row.y = row.baseY * (1 - relationBlend) + row.networkY * relationBlend;
      });
      layout.atomPositions.forEach((row) => {
        row.x = row.baseX * (1 - relationBlend) + row.networkX * relationBlend;
        row.y = row.baseY * (1 - relationBlend) + row.networkY * relationBlend;
      });
      hitIndexes = buildHitIndexes();
      fitView();
      updateDepthBadge();
    }

    function focusPoint(point, scale) {
      if (!point) return;
      camera.x = point.x;
      camera.y = point.y;
      camera.scale = Math.max(0.34, Math.min(2.2, scale || Math.max(camera.scale, 0.72)));
      cameraChanged = true;
      updateDepthBadge();
      noteInteraction(1200);
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
      updateDepthBadge();
      noteInteraction(900);
    }

    function resize() {
      const rect = stage.getBoundingClientRect();
      const width = Math.max(1, Math.round(rect.width));
      const height = Math.max(430, Math.round(rect.height || 620));
      const nextDpr = qualityDpr();
      if (width === size.width && height === size.height &&
          nextDpr === dpr && !qualityDirty) return;
      size = { width, height };
      dpr = nextDpr;
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      baseCanvas.width = canvas.width;
      baseCanvas.height = canvas.height;
      qualityDirty = false;
      canvas.dataset.dpr = String(dpr);
      if (!layout.bounds || camera.scale === 0.35 && camera.x === WORLD.cx) fitView();
      paintBackground();
      cameraChanged = true;
      requestRender(false);
    }

    function worldLine(context, from, to, color, width, alpha) {
      context.beginPath();
      context.moveTo(from.x, from.y);
      context.lineTo(to.x, to.y);
      context.strokeStyle = rgba(color, alpha);
      context.lineWidth = Math.max(0.35, width / camera.scale);
      context.stroke();
    }

    function arrowHead(context, point, control, color, alpha, radius) {
      const angle = Math.atan2(point.y - control.y, point.x - control.x);
      const size = Math.max(3, (radius || 7) / camera.scale);
      context.save();
      context.translate(point.x, point.y);
      context.rotate(angle);
      context.beginPath();
      context.moveTo(0, 0);
      context.lineTo(-size, -size * 0.52);
      context.lineTo(-size, size * 0.52);
      context.closePath();
      context.fillStyle = rgba(color, alpha);
      context.fill();
      context.restore();
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
        if (kind === "concept" && !focus.concepts.has(String(id))) {
          value *= isolateNeighborhood ? 0 : 0.08;
        }
        if (kind === "atom" && !focus.atoms.has(String(id))) {
          value *= isolateNeighborhood ? 0 : 0.035;
        }
        if (kind === "chapter" && !focus.chapters.has(String(id))) {
          value *= isolateNeighborhood ? 0.16 : 0.28;
        }
      }
      return value;
    }

    function typeAllowed(type) {
      return allowedTypes.has(type || "grouping");
    }

    function paintBase(options) {
      if (!size.width || !size.height) return;
      const quick = Boolean(options && options.quick);
      const startedAt = performance.now();
      const structureMode = relationBlend < 0.35;
      const context = baseCtx;
      context.setTransform(1, 0, 0, 1, 0, 0);
      context.clearRect(0, 0, baseCanvas.width, baseCanvas.height);
      context.drawImage(backgroundCanvas, 0, 0);

      cameraTransform(context);
      context.globalCompositeOperation = "lighter";
      context.shadowBlur = 0;

      if (!quick) {
        drawGlow(context, "#40def4", WORLD.cx, WORLD.cy, 1080, 0.11);
        layout.chapterCenters.forEach((row) => {
          drawGlow(context, row.color, row.x, row.y, 540, 0.1);
        });

        const starBuckets = new Map();
        ambientStars.forEach((star) => {
          const bucket = Math.round(star.alpha * 40) / 40;
          if (!starBuckets.has(bucket)) starBuckets.set(bucket, []);
          starBuckets.get(bucket).push(star);
        });
        starBuckets.forEach((rows, alpha) => {
          fillArcBatch(context, rows, "#c6f6ff", alpha,
            (star) => Math.max(0.25, star.size / camera.scale));
        });
        context.globalAlpha = 1;

        [260, 520, 780, 1040].forEach((radius, index) => {
          context.beginPath();
          context.arc(WORLD.cx, WORLD.cy, radius, 0, Math.PI * 2);
          context.strokeStyle = "rgba(99,213,230," + (0.055 - index * 0.008) + ")";
          context.lineWidth = 1 / camera.scale;
          context.stroke();
        });
        context.setLineDash([5 / camera.scale, 12 / camera.scale]);
        layout.chapterCenters.forEach((row, id) => {
          const visible = !chapterFilter || chapterFilter === id;
          context.beginPath();
          context.arc(row.x, row.y, 430, 0, Math.PI * 2);
          context.strokeStyle = rgba(row.color, visible ? 0.055 : 0.012);
          context.lineWidth = 0.75 / camera.scale;
          context.stroke();
        });
        context.setLineDash([]);
      }

      layout.chapterLinks.forEach((row) => {
        const alpha = !focus || focus.chapters.has(row.chapterId)
          ? (structureMode ? 0.34 : 0.23)
          : 0.04;
        worldLine(context, row.from, row.to,
          layout.chapterCenters.get(row.chapterId)?.color || COLORS[0], 1.25, alpha);
      });
      layout.chapterFlow.forEach((edge) => {
        if (!typeAllowed(edge.type)) return;
        if (focus && isolateNeighborhood &&
            !focus.chapters.has(edge.fromId) && !focus.chapters.has(edge.toId)) return;
        context.beginPath();
        context.moveTo(edge.fromPoint.x, edge.fromPoint.y);
        context.quadraticCurveTo(edge.cx, edge.cy, edge.toPoint.x, edge.toPoint.y);
        context.strokeStyle = rgba(edge.color, focus ? 0.11 : 0.2);
        context.lineWidth = Math.max(0.55, 1.15 / camera.scale);
        context.stroke();
        arrowHead(context, edge.toPoint, { x: edge.cx, y: edge.cy },
          edge.color, focus ? 0.16 : 0.34, 8);
      });
      const lessonLinkGroups = new Map();
      layout.lessonLinks.forEach((row) => {
        const chapterAlpha = !chapterFilter || chapterFilter === row.chapterId
          ? (structureMode ? 0.2 : 0.1)
          : 0.018;
        const color = layout.chapterCenters.get(row.chapterId)?.color || COLORS[0];
        const key = color + ":" + chapterAlpha;
        if (!lessonLinkGroups.has(key)) {
          lessonLinkGroups.set(key, { color, alpha: chapterAlpha, rows: [] });
        }
        lessonLinkGroups.get(key).rows.push(row);
      });
      lessonLinkGroups.forEach((group) => {
        strokeLineBatch(context, group.rows, group.color, 0.7, group.alpha);
      });
      if (!quick) {
        const membershipGroups = new Map();
        layout.membershipLinks.forEach((row) => {
          const activeLesson = layout.currentLesson &&
            String(layout.currentLesson.id) === row.lessonId && !focus;
          const alpha = activeLesson ? 0.2 : (structureMode ? 0.095 : 0.024);
          const color = row.to.color || COLORS[0];
          const key = color + ":" + alpha;
          if (!membershipGroups.has(key)) {
            membershipGroups.set(key, { color, alpha, rows: [] });
          }
          membershipGroups.get(key).rows.push(row);
        });
        membershipGroups.forEach((group) => {
          strokeLineBatch(context, group.rows, group.color, 0.55, group.alpha);
        });

        const showOverviewAtomLinks = resolvedQuality === "cinematic" || camera.scale >= 0.62;
        if (focus || showOverviewAtomLinks) {
          const atomGroups = new Map();
          layout.atomLinks.forEach((row) => {
            if (focus && isolateNeighborhood && !focus.atoms.has(row.atomId)) return;
            const inFocus = focus && focus.atoms.has(row.atomId);
            const alpha = inFocus ? 0.34 : 0.018;
            const color = row.to.color || COLORS[0];
            const key = color + ":" + alpha;
            if (!atomGroups.has(key)) {
              atomGroups.set(key, { color, alpha, rows: [] });
            }
            atomGroups.get(key).rows.push(row);
          });
          atomGroups.forEach((group) => {
            strokeLineBatch(context, group.rows, group.color, 0.38, group.alpha);
          });
        }
      }

      const edgeGroups = new Map();
      layout.edges.forEach((edge) => {
        if (!typeAllowed(edge.type)) return;
        const active = Boolean(focus && focus.edges.has(String(edge.id)));
        if (focus && isolateNeighborhood && !active) return;
        const color = edge.color || (active ? "#7ef2ff" : "#56bed6");
        const alpha = active
          ? 0.82
          : focus ? 0.035 : (structureMode ? 0.055 : 0.19);
        const width = active ? 1.15 : 0.76;
        const key = color + ":" + alpha + ":" + width;
        if (!edgeGroups.has(key)) {
          edgeGroups.set(key, { color, alpha, width, rows: [] });
        }
        edgeGroups.get(key).rows.push(edge);
      });
      edgeGroups.forEach((group) => {
        strokeCurveBatch(context, group.rows, group.color, group.width, group.alpha);
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
        context.globalAlpha = group.alpha * (focus ? 0.72 : 0.42);
        context.fillStyle = group.color;
        const radius = Math.max(0.48, 0.59 / camera.scale);
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
      const conceptCoreGroups = new Map();
      conceptsByColor.forEach((group) => {
        context.globalAlpha = group.alpha;
        group.rows.forEach((row) => {
          const degree = layout.adjacency.get(row.id)?.size || 0;
          const current = layout.currentConceptIds.has(row.id);
          const isSelected = selected?.kind === "concept" && selected.id === row.id;
          const radius = Math.max(1.15, ((isSelected ? 5.6 : current ? 3.9 : 2.8) +
            Math.min(2.2, degree * 0.09)) / camera.scale);
          const emphasize = current || isSelected ||
            salientConceptIds.has(row.id) || resolvedQuality === "cinematic";
          if (!quick && emphasize) {
            drawGlow(context, group.color, row.x, row.y,
              radius * (isSelected ? 4.2 : 3.6), isSelected ? 1 : 0.82);
          } else if (quick && (current || isSelected)) {
            drawGlow(context, group.color, row.x, row.y,
              radius * (isSelected ? 4.2 : 3.6), isSelected ? 1 : 0.82);
          }
          if (!conceptCoreGroups.has(group.alpha)) conceptCoreGroups.set(group.alpha, []);
          conceptCoreGroups.get(group.alpha).push({
            x: row.x,
            y: row.y,
            radius: Math.max(0.7, radius * 0.52),
          });
        });
      });
      conceptCoreGroups.forEach((rows, alpha) => {
        fillArcBatch(context, rows, "#f0ffff", alpha * 0.94,
          (row) => row.radius);
      });

      const lessonHubGroups = new Map();
      layout.lessonHubs.forEach((hub) => {
        const alpha = chapterFilter && hub.chapterId !== chapterFilter ? 0.05 : 0.28;
        const key = hub.color + ":" + alpha;
        if (!lessonHubGroups.has(key)) {
          lessonHubGroups.set(key, { color: hub.color, alpha, rows: [] });
        }
        lessonHubGroups.get(key).rows.push(hub);
      });
      lessonHubGroups.forEach((group) => {
        fillArcBatch(context, group.rows, group.color, group.alpha,
          () => Math.max(1.1, 1.8 / camera.scale));
      });

      layout.chapterCenters.forEach((row, id) => {
        const alpha = nodeAlpha("chapter", id, id);
        context.globalAlpha = alpha;
        const radius = Math.max(4, 8 / camera.scale);
        drawGlow(context, row.color, row.x, row.y, radius * 5, 0.82);
        context.fillStyle = "rgba(235,255,255,.92)";
        context.beginPath();
        context.arc(row.x, row.y, radius * 0.62, 0, Math.PI * 2);
        context.fill();
      });

      const centerAlpha = focus && !focus.chapters.size ? 0.2 : 1;
      context.globalAlpha = centerAlpha;
      drawGlow(context, "#8ff3ff", WORLD.cx, WORLD.cy, 92, 0.95);
      context.globalAlpha = 1;
      context.globalCompositeOperation = "source-over";

      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      drawStaticLabels(context, quick);
      canvas.dataset.paintMs = (performance.now() - startedAt).toFixed(1);
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

    function roundedRect(context, x, y, width, height, radius) {
      const r = Math.min(radius, height / 2, width / 2);
      context.beginPath();
      context.moveTo(x + r, y);
      context.arcTo(x + width, y, x + width, y + height, r);
      context.arcTo(x + width, y + height, x, y + height, r);
      context.arcTo(x, y + height, x, y, r);
      context.arcTo(x, y, x + width, y, r);
      context.closePath();
    }

    function pillLabel(context, text, x, y, color, options) {
      const opt = options || {};
      const fontSize = opt.size || 11;
      const alpha = opt.alpha == null ? 1 : opt.alpha;
      const maxWidth = opt.maxWidth || 190;
      let value = clean(text);
      context.save();
      context.globalAlpha = alpha;
      context.font = (opt.weight || 600) + " " + fontSize +
        "px 'Microsoft YaHei UI', 'PingFang SC', sans-serif";
      if (context.measureText(value).width > maxWidth - 18) {
        while (value.length > 3 && context.measureText(value + "…").width > maxWidth - 18) {
          value = value.slice(0, -1);
        }
        value += "…";
      }
      const width = Math.min(maxWidth, context.measureText(value).width + 18);
      const height = fontSize + 12;
      const left = opt.anchor === "left" ? x : x - width / 2;
      const top = y - height / 2;
      const box = { left, top, right: left + width, bottom: top + height };
      if (opt.avoid && boxesOverlap(opt.avoid, box, opt.margin || 3)) {
        context.restore();
        return null;
      }
      roundedRect(context, left, top, width, height, height / 2);
      context.fillStyle = opt.fill || "rgba(2,10,15,.88)";
      context.fill();
      context.strokeStyle = rgba(color, alpha * 0.5);
      context.lineWidth = 0.8;
      context.stroke();
      context.textAlign = "center";
      context.textBaseline = "middle";
      context.fillStyle = color;
      context.fillText(value, left + width / 2, y + 0.4);
      context.restore();
      return box;
    }

    function boxesOverlap(boxes, candidate, margin) {
      const pad = margin == null ? 3 : margin;
      return boxes.some((box) =>
        candidate.left < box.right + pad &&
        candidate.right > box.left - pad &&
        candidate.top < box.bottom + pad &&
        candidate.bottom > box.top - pad
      );
    }

    function buildLabelGroups() {
      const groups = new Map();
      layout.conceptPositions.forEach((row, id) => {
        if (!groups.has(row.chapterId)) groups.set(row.chapterId, []);
        groups.get(row.chapterId).push({ id, row });
      });
      groups.forEach((rows) => {
        rows.sort((left, right) => {
          const leftScore = (layout.currentConceptIds.has(left.id) ? 1000 : 0) +
            (layout.adjacency.get(left.id)?.size || 0);
          const rightScore = (layout.currentConceptIds.has(right.id) ? 1000 : 0) +
            (layout.adjacency.get(right.id)?.size || 0);
          return rightScore - leftScore;
        });
      });
      return groups;
    }

    function buildHitIndexes() {
      const makeIndex = (rows, cellSize) => {
        const cells = new Map();
        rows.forEach((row, id) => {
          const cx = Math.floor(row.x / cellSize);
          const cy = Math.floor(row.y / cellSize);
          const key = cx + ":" + cy;
          if (!cells.has(key)) cells.set(key, []);
          cells.get(key).push({ id, row });
        });
        return { cellSize, cells };
      };
      return {
        concepts: makeIndex(layout.conceptPositions, 64),
        atoms: makeIndex(layout.atomPositions, 48),
      };
    }

    function buildSalientConceptIds() {
      const byChapter = new Map();
      layout.conceptPositions.forEach((row, id) => {
        if (!byChapter.has(row.chapterId)) byChapter.set(row.chapterId, []);
        byChapter.get(row.chapterId).push({
          id,
          degree: layout.adjacency.get(id)?.size || 0,
        });
      });
      const salient = new Set(layout.currentConceptIds);
      byChapter.forEach((rows) => {
        rows.sort((left, right) => right.degree - left.degree);
        rows.slice(0, 14).forEach((row) => salient.add(row.id));
      });
      return salient;
    }

    let labelGroups = buildLabelGroups();
    let hitIndexes = buildHitIndexes();
    const salientConceptIds = buildSalientConceptIds();

    function drawStaticLabels(context, quick) {
      const boxes = [];
      const coursePoint = cssPoint(WORLD.cx, WORLD.cy);
      boxes.push(pillLabel(context, clean(graph.course || "全课程"),
        coursePoint.x, coursePoint.y - 31, "#d9fbff",
        { size: 15, weight: 700, maxWidth: 240 }));
      label(context, "课程主干", coursePoint.x, coursePoint.y + 27,
        "rgba(132,196,210,.8)", 10);

      layout.chapterCenters.forEach((row, id) => {
        const alpha = chapterFilter && id !== chapterFilter ? 0.18 : 1;
        const point = cssPoint(row.x, row.y);
        const chapter = row.chapter;
        const title = clean(chapter.label || chapter.title || id).replace(/^第/, "第");
        const short = title.length > 18 ? title.slice(0, 18) + "…" : title;
        boxes.push(pillLabel(context, short, point.x, point.y + 31, row.color,
          { size: 11.5, weight: 700, maxWidth: 180, alpha }));
      });

      if (layout.currentLesson) {
        const lessonHub = layout.lessonHubs.get(String(layout.currentLesson.id));
        if (lessonHub) {
          const point = cssPoint(lessonHub.x, lessonHub.y);
          boxes.push(pillLabel(context, "当前 · E" +
            String(layout.currentLesson.episode).padStart(2, "0"),
          point.x, point.y - 25, "#f6d58d",
          { size: 10, maxWidth: 92 }));
        }
      }

      if (quick) return;
      const perChapter = camera.scale < 0.42 ? 1 : camera.scale < 0.72 ? 2 : 4;
      labelGroups.forEach((items, chapterId) => {
        items.slice(0, perChapter).forEach((item) => {
          const { id, row } = item;
          const alpha = nodeAlpha("concept", id, chapterId);
          if (alpha < 0.25) return;
          const point = cssPoint(row.x, row.y);
          if (point.x < 20 || point.x > size.width - 20 ||
              point.y < 20 || point.y > size.height - 20) return;
          const concept = layout.conceptIndex.get(id);
          const box = pillLabel(context, concept?.label || "概念",
            point.x + 9, point.y - 12, row.color,
            { size: 10, maxWidth: 160, anchor: "left",
              alpha: Math.min(0.9, alpha), avoid: boxes, margin: 4 });
          if (box) boxes.push(box);
        });
      });
    }

    function drawFrame(time) {
      raf = 0;
      if (!active || !size.width) {
        canvas.dataset.frameState = "paused";
        return;
      }
      const now = performance.now();
      lastFrameAt = time;
      canvas.dataset.frameState = "running";
      const quick = dragging || now < quickPreviewUntil;
      if (cameraChanged) {
        paintBase({ quick });
        cameraChanged = false;
      }
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.drawImage(baseCanvas, 0, 0);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.globalCompositeOperation = "lighter";
      const activeEdges = quick ? [] : focus
          ? layout.edges.filter((edge) =>
            typeAllowed(edge.type) && focus.edges.has(String(edge.id))).slice(0, 80)
          : layout.edges.filter((edge, index) =>
            typeAllowed(edge.type) && index % 29 === 0).slice(0, 34);
      const relationLabels = [];
      if (!quick) {
        layout.chapterFlow.forEach((edge, index) => {
          if (!typeAllowed(edge.type)) return;
          if (focus && isolateNeighborhood &&
              !focus.chapters.has(edge.fromId) && !focus.chapters.has(edge.toId)) return;
          const from = cssPoint(edge.fromPoint.x, edge.fromPoint.y);
          const control = cssPoint(edge.cx, edge.cy);
          const to = cssPoint(edge.toPoint.x, edge.toPoint.y);
          const t = (time * 0.000055 + index * 0.23) % 1;
          const mt = 1 - t;
          const px = mt * mt * from.x + 2 * mt * t * control.x + t * t * to.x;
          const py = mt * mt * from.y + 2 * mt * t * control.y + t * t * to.y;
          drawGlow(ctx, edge.color, px, py, focus ? 4.2 : 7,
            focus ? 0.44 : 0.88);
          ctx.fillStyle = rgba(edge.color, focus ? 0.5 : 0.96);
          ctx.beginPath();
          ctx.arc(px, py, focus ? 1.2 : 2.1, 0, Math.PI * 2);
          ctx.fill();
        });
      }
      activeEdges.forEach((edge, index) => {
        const from = cssPoint(edge.fromPoint.x, edge.fromPoint.y);
        const control = cssPoint(edge.cx, edge.cy);
        const to = cssPoint(edge.toPoint.x, edge.toPoint.y);
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.quadraticCurveTo(control.x, control.y, to.x, to.y);
        ctx.strokeStyle = rgba(edge.color || "#5cd5e6", focus ? 0.62 : 0.2);
        ctx.lineWidth = focus ? 1.4 : 0.7;
        ctx.stroke();
        const t = ((time * 0.00013 + index * 0.173) % 1);
        const mt = 1 - t;
        const px = mt * mt * from.x + 2 * mt * t * control.x + t * t * to.x;
        const py = mt * mt * from.y + 2 * mt * t * control.y + t * t * to.y;
        if (focus) drawGlow(ctx, edge.color || "#dffcff", px, py, 4.2, 0.6);
        ctx.fillStyle = focus ? "rgba(230,255,255,.95)" : "rgba(174,242,251,.5)";
        ctx.beginPath();
        ctx.arc(px, py, focus ? 1.8 : 1.1, 0, Math.PI * 2);
        ctx.fill();
        if (focus && activeEdges.length <= 24 && edge.type) {
          const t2 = 0.56;
          const mt2 = 1 - t2;
          relationLabels.push({
            x: mt2 * mt2 * from.x + 2 * mt2 * t2 * control.x + t2 * t2 * to.x,
            y: mt2 * mt2 * from.y + 2 * mt2 * t2 * control.y + t2 * t2 * to.y,
            text: TYPE_LABELS[edge.type] || edge.type,
            color: edge.color || "#8ce9f5",
          });
        }
      });

      ctx.globalCompositeOperation = "source-over";
      let selectedLabelBox = null;
      if (selected && !quick) {
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
          const pulse = now < animationUntil ? Math.sin(time * 0.006) * 1.6 : 0;
          ctx.arc(point.x, point.y, 8 + pulse, 0, Math.PI * 2);
          ctx.stroke();
          const title = selected.kind === "concept"
            ? layout.conceptIndex.get(selected.id)?.label
            : selected.kind === "atom"
              ? layout.atomPositions.get(selected.id)?.atom?.label
              : layout.chapterCenters.get(selected.id)?.chapter?.label;
          if (title) {
            selectedLabelBox = pillLabel(ctx, title, point.x + 11, point.y - 15, "#f0fdff",
              { size: 11.5, weight: 700, anchor: "left", maxWidth: 230 });
          }
        }
      }
      if (focus && !quick) {
        const used = selectedLabelBox ? [selectedLabelBox] : [];
        const focusRows = Array.from(focus.concepts)
          .map((id) => ({ id, row: layout.conceptPositions.get(id) }))
          .filter((item) => item.row && !(selected?.kind === "concept" && selected.id === item.id))
          .slice(0, 18);
        focusRows.forEach(({ id, row }) => {
          const point = cssPoint(row.x, row.y);
          if (point.x < 8 || point.x > size.width - 8 ||
              point.y < 8 || point.y > size.height - 8) return;
          const concept = layout.conceptIndex.get(id);
          const box = pillLabel(ctx, concept?.label || "概念",
            point.x + 7, point.y - 10, row.color,
            { size: 10, maxWidth: 170, anchor: "left", avoid: used, margin: 3 });
          if (box) used.push(box);
        });
        relationLabels.slice(0, 14).forEach((row) => {
          const box = pillLabel(ctx, row.text, row.x, row.y, row.color,
            { size: 8.5, maxWidth: 70, fill: "rgba(3,12,18,.74)", avoid: used, margin: 2 });
          if (box) used.push(box);
        });
      }
      ctx.globalCompositeOperation = "source-over";
      frameCount += 1;
      canvas.dataset.frames = String(frameCount);
      if (!sampledAt) {
        sampledAt = time;
        sampledFrames = frameCount;
      } else if (time - sampledAt >= 500) {
        measuredFps = Math.round((frameCount - sampledFrames) * 1000 / (time - sampledAt));
        canvas.dataset.fps = String(measuredFps);
        sampledAt = time;
        sampledFrames = frameCount;
      }
      if (!dragging && performance.now() < animationUntil) {
        requestRender(true);
      } else {
        animationUntil = 0;
        canvas.dataset.frameState = "idle";
      }
    }

    function stopLoop() {
      cancelScheduledRender();
      canvas.dataset.frameState = "paused";
    }

    function focusForHit(hit) {
      selected = hit || null;
      if (hit?.kind === "concept") {
        chapterFilter = layout.conceptPositions.get(hit.id)?.chapterId || "";
      } else if (hit?.kind === "atom") {
        chapterFilter = layout.atomPositions.get(hit.id)?.chapterId || "";
      } else if (hit?.kind === "chapter") {
        chapterFilter = hit.id;
      } else if (hit?.kind === "lesson") {
        chapterFilter = chapterKey(layout.lessonIndex.get(hit.id)?.chapterId || "");
      }
      filter.value = chapterFilter;
      focus = focusSets(layout, selected);
      cameraChanged = true;
      noteInteraction(1100);
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
          related.appendChild(h("b", "", "知识关系 · " + neighbors.length + " 个直接邻居"));
          const groups = new Map();
          layout.edges.forEach((edge) => {
            const outgoing = String(edge.from) === selected.id;
            const incoming = String(edge.to) === selected.id;
            if (!outgoing && !incoming) return;
            const neighborId = outgoing ? String(edge.to) : String(edge.from);
            const next = layout.conceptIndex.get(neighborId);
            if (!next) return;
            const type = clean(edge.type || "related");
            const direction = outgoing ? "out" : "in";
            const key = type + ":" + direction;
            if (!groups.has(key)) {
              groups.set(key, {
                type,
                direction,
                label: (outgoing ? "→ " : "← ") + (TYPE_LABELS[type] || "关联"),
                rows: [],
              });
            }
            groups.get(key).rows.push({ id: neighborId, concept: next });
          });
          groups.forEach((group) => {
            if (!typeAllowed(group.type)) return;
            const block = h("div", "kp-star-relation-group");
            const heading = h("div", "kp-star-relation-head");
            heading.appendChild(h("span", "", group.label));
            heading.appendChild(h("small", "", group.rows.length + " 个"));
            block.appendChild(heading);
            group.rows.slice(0, 8).forEach(({ id, concept: next }) => {
              block.appendChild(button(next.label, "kp-star-chip", () => {
                focusForHit({ kind: "concept", id });
                focusPoint(layout.conceptPositions.get(id), Math.max(camera.scale, 1.05));
              }));
            });
            related.appendChild(block);
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
      const worldX = (sx - size.width / 2) / camera.scale + camera.x;
      const worldY = (sy - size.height / 2) / camera.scale + camera.y;
      let best = null;
      let bestDistance = Infinity;
      const query = (index, thresholdPx, kind) => {
        const threshold = thresholdPx / camera.scale;
        const cellSize = index.cellSize;
        const minX = Math.floor((worldX - threshold) / cellSize);
        const maxX = Math.floor((worldX + threshold) / cellSize);
        const minY = Math.floor((worldY - threshold) / cellSize);
        const maxY = Math.floor((worldY + threshold) / cellSize);
        for (let x = minX; x <= maxX; x += 1) {
          for (let y = minY; y <= maxY; y += 1) {
            const rows = index.cells.get(x + ":" + y);
            if (!rows) continue;
            rows.forEach(({ id, row }) => {
              const distance = Math.hypot(row.x - worldX, row.y - worldY);
              if (distance <= threshold && distance < bestDistance) {
                bestDistance = distance;
                best = { kind, id };
              }
            });
          }
        }
      };
      query(hitIndexes.concepts, 11, "concept");
      if (best) return best;
      query(hitIndexes.atoms, 7, "atom");
      if (best) return best;
      layout.chapterCenters.forEach((row, id) => {
        const distance = Math.hypot(row.x - worldX, row.y - worldY) * camera.scale;
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
        requestRender(false);
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
      cameraChanged = true;
      quickPreviewUntil = 0;
      if (!moved) {
        const hit = hitTest(point.x, point.y);
        focusForHit(hit);
      }
      noteInteraction(1200);
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
      quickPreviewUntil = performance.now() + 90;
      zoomAt(event.deltaY < 0 ? 1.12 : 0.89, point.x, point.y);
      clearTimeout(canvas._kpWheelTimer);
      canvas._kpWheelTimer = setTimeout(() => {
        quickPreviewUntil = 0;
        cameraChanged = true;
        noteInteraction(600);
      }, 110);
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
      search.value = "";
      suggestions.hidden = true;
      selected = null;
      focus = null;
      fitView();
      cameraChanged = true;
      noteInteraction(1200);
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
      chapterFilter = chapterKey(layout.currentLesson?.chapterId || chapterFilter);
      filter.value = chapterFilter;
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

    layoutSelect.addEventListener("change", () => {
      const values = { structure: 0, balanced: 0.62, relations: 1 };
      canvas.dataset.layout = layoutSelect.value;
      selected = null;
      focus = null;
      applyLayoutBlend(values[layoutSelect.value] ?? 1);
      cameraChanged = true;
      noteInteraction(700);
      renderDetail();
    });

    qualitySelect.addEventListener("change", () => {
      qualityMode = qualitySelect.value;
      resolvedQuality = resolveQuality();
      qualityDirty = true;
      canvas.dataset.performanceMode = qualityMode;
      canvas.dataset.resolvedQuality = resolvedQuality;
      performanceBadge.textContent = qualityMode === "auto"
        ? "自动 · " + (resolvedQuality === "smooth" ? "流畅" : "画质")
        : qualityMode === "smooth" ? "流畅优先" : "画质优先";
      resize();
      cameraChanged = true;
      noteInteraction(700);
    });

    function searchMatches(value) {
      const query = value.trim().toLowerCase();
      if (!query) return [];
      const rows = [];
      layout.conceptPositions.forEach((row, id) => {
        const concept = layout.conceptIndex.get(id);
        const text = String(concept?.label || "").toLowerCase();
        if (!text.includes(query)) return;
        rows.push({
          kind: "concept",
          id,
          title: concept?.label || "核心概念",
          subtitle: clean(row.chapterId) + " · 核心概念",
          color: row.color,
          rank: text === query ? 0 : text.startsWith(query) ? 1 : 2,
        });
      });
      layout.atomPositions.forEach((row, id) => {
        const atom = row.atom || {};
        const text = (String(atom.label || "") + " " + String(atom.claim || "")).toLowerCase();
        if (!text.includes(query)) return;
        rows.push({
          kind: "atom",
          id,
          title: atom.label || atom.claim || "知识光点",
          subtitle: "E" + String(atom.episode || "?").padStart(2, "0") + " · 知识原子",
          color: row.color,
          rank: 3,
        });
      });
      return rows.sort((left, right) =>
        left.rank - right.rank || left.title.length - right.title.length
      ).slice(0, 8);
    }

    function chooseSearchHit(hit) {
      if (!hit) return;
      suggestions.hidden = true;
      search.value = hit.kind === "concept"
        ? layout.conceptIndex.get(hit.id)?.label || ""
        : layout.atomPositions.get(hit.id)?.atom?.label || "";
      focusForHit(hit);
      const point = hit.kind === "concept"
        ? layout.conceptPositions.get(hit.id)
        : layout.atomPositions.get(hit.id);
      focusPoint(point, hit.kind === "atom" ? 1.35 : 1.08);
    }

    function renderSuggestions(value) {
      suggestions.innerHTML = "";
      suggestionHits = searchMatches(value);
      if (!suggestionHits.length) {
        suggestions.hidden = true;
        return;
      }
      suggestionHits.forEach((hit) => {
        const row = h("button", "kp-star-suggestion");
        row.type = "button";
        const dot = h("i");
        dot.style.background = hit.color;
        dot.style.boxShadow = "0 0 8px " + hit.color;
        row.appendChild(dot);
        const body = h("span");
        body.appendChild(h("b", "", hit.title));
        body.appendChild(h("small", "", hit.subtitle));
        row.appendChild(body);
        row.onpointerdown = (event) => event.preventDefault();
        row.onclick = () => chooseSearchHit({ kind: hit.kind, id: hit.id });
        suggestions.appendChild(row);
      });
      suggestions.hidden = false;
    }

    search.addEventListener("input", () => renderSuggestions(search.value));
    search.addEventListener("focus", () => {
      if (search.value.trim()) renderSuggestions(search.value);
    });
    search.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        suggestions.hidden = true;
        return;
      }
      if (event.key === "Enter" && suggestionHits.length) {
        event.preventDefault();
        chooseSearchHit(suggestionHits[0]);
      }
    });
    function hideSuggestionsOutside(event) {
      if (!searchWrap.contains(event.target)) suggestions.hidden = true;
    }
    global.document.addEventListener("pointerdown", hideSuggestionsOutside);

    section._kpActivate = (next) => {
      active = Boolean(next);
      if (active) {
        resize();
        noteInteraction(1200);
      } else {
        stopLoop();
      }
    };
    section._kpDestroy = () => {
      stopLoop();
      if (resizeObserver) resizeObserver.disconnect();
      clearTimeout(resizeTimer);
      clearTimeout(canvas._kpWheelTimer);
      global.document.removeEventListener("pointerdown", hideSuggestionsOutside);
    };
    section._kpFocusLesson = focusLesson;
    return section;
  }

  const api = { create, buildLayout };
  global.VKSStarMap = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
