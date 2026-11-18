/* 知识点整理：流式笔记、视频时间同步、选中提问与可撤销修订 */
(function () {
  const byId = (id) => document.getElementById(id);
  const NS = "http://www.w3.org/2000/svg";
  const ACTION_TEXT = {
    explain: "解释这段",
    check: "检查错误",
    simplify: "换一种说法",
    example: "补充例子",
    highlight: "标记重点",
    clarify: "我不理解",
    custom: "追问",
  };

  const S = {
    project: null,
    data: null,
    index: null,
    kstate: null,
    follow: true,
    loadSeq: 0,
    selected: null,
    lastAnswer: null,
    history: [],
    currentTimeline: -1,
  };

  function el(tag, cls, text) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = String(text);
    return node;
  }

  function authUrl(url) {
    let token = "";
    try { token = localStorage.getItem("vks_token") || ""; } catch (_) {}
    return url + (url.includes("?") ? "&" : "?") + "t=" + encodeURIComponent(token);
  }

  function clock(seconds, withHours) {
    const sec = Math.max(0, Math.round(Number(seconds) || 0));
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = sec % 60;
    if (withHours || h) {
      return String(h).padStart(2, "0") + ":" + String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
    }
    return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
  }

  function rich(text, className) {
    const box = el("span", className || "k-rich");
    const value = String(text == null ? "" : text);
    const re = /(\*\*[^*]+\*\*|`[^`]+`)/g;
    let at = 0;
    let m;
    while ((m = re.exec(value))) {
      if (m.index > at) box.appendChild(document.createTextNode(value.slice(at, m.index)));
      const token = m[0];
      if (token.startsWith("**")) {
        box.appendChild(el("strong", "", token.slice(2, -2)));
      } else {
        box.appendChild(el("code", "", token.slice(1, -1)));
      }
      at = m.index + token.length;
    }
    if (at < value.length) box.appendChild(document.createTextNode(value.slice(at)));
    return box;
  }

  function setTextBlock(node, value) {
    node.innerHTML = "";
    node.appendChild(rich(value));
  }

  function sectionHead(title, hint) {
    const head = el("div", "k-section-head");
    head.appendChild(el("h3", "", title));
    if (hint) head.appendChild(el("small", "", hint));
    return head;
  }

  function chip(text, tone) {
    return el("i", "k-chip" + (tone ? " " + tone : ""), text);
  }

  function button(text, cls, handler) {
    const b = el("button", "k-btn" + (cls ? " " + cls : ""), text);
    b.type = "button";
    b.onclick = handler;
    return b;
  }

  function seek(seconds) {
    const vp = window.__vp;
    if (!vp || !vp.video) return;
    const max = Number.isFinite(vp.video.duration) ? Math.max(0, vp.video.duration - 0.15) : Number(seconds);
    vp.video.currentTime = Math.max(0, Math.min(max, Number(seconds) || 0));
    vp.play && vp.play();
  }

  function nodeAt(kid, root) {
    if (!kid) return null;
    const scope = root || byId("knowledge");
    if (!scope) return null;
    return Array.from(scope.querySelectorAll("[data-kid]")).find((x) => x.dataset.kid === kid) || null;
  }

  function applyOverride(kid, value) {
    const node = nodeAt(kid);
    if (!node) return;
    setTextBlock(node, value);
    node.dataset.revised = "1";
  }

  function render() {
    const box = byId("knowledge");
    const lesson = S.data && S.data.episode;
    if (!box || !lesson) return;
    box.innerHTML = "";

    const hero = el("section", "k-hero");
    const eyebrow = el("div", "k-eyebrow");
    eyebrow.appendChild(chip("第 " + String(lesson.episode).padStart(2, "0") + " 讲"));
    eyebrow.appendChild(chip(lesson.chapter || "课程"));
    eyebrow.appendChild(chip(clock(lesson.duration), "mint"));
    eyebrow.appendChild(chip("证据覆盖 · 转录 + 关键帧", "amber"));
    hero.appendChild(eyebrow);
    hero.appendChild(el("h2", "k-title", lesson.title));
    const thesis = el("p", "k-thesis");
    thesis.dataset.kid = "E" + String(lesson.episode).padStart(2, "0") + ":thesis";
    setTextBlock(thesis, lesson.thesis);
    hero.appendChild(thesis);
    const actions = el("div", "k-hero-actions");
    const follow = button("跟随播放：开", "on", () => toggleFollow());
    follow.id = "kfollow";
    actions.appendChild(follow);
    actions.appendChild(button("回到当前时间", "", () => {
      if (window.__vp && window.__vp.video) seek(window.__vp.video.currentTime + 0.01);
    }));
    actions.appendChild(button("问 AI", "primary", () => openDock("custom")));
    hero.appendChild(actions);
    box.appendChild(hero);

    if (lesson.formula || lesson.trap || lesson.memoryHook) {
      const quick = el("section", "k-quick");
      if (lesson.formula) {
        const card = el("article", "k-quick-card formula");
        card.appendChild(el("span", "k-card-label", "一眼记住"));
        const value = el("div", "k-rich");
        value.dataset.kid = "E" + String(lesson.episode).padStart(2, "0") + ":formula";
        setTextBlock(value, lesson.formula);
        card.appendChild(value);
        quick.appendChild(card);
      }
      if (lesson.memoryHook) {
        const card = el("article", "k-quick-card hook");
        card.appendChild(el("span", "k-card-label", "记忆钩子"));
        const value = el("div", "k-rich");
        value.dataset.kid = "E" + String(lesson.episode).padStart(2, "0") + ":hook";
        setTextBlock(value, lesson.memoryHook);
        card.appendChild(value);
        quick.appendChild(card);
      }
      if (lesson.trap) {
        const card = el("article", "k-quick-card trap wide");
        card.appendChild(el("span", "k-card-label", "最容易错的地方"));
        const value = el("div", "k-rich");
        value.dataset.kid = "E" + String(lesson.episode).padStart(2, "0") + ":trap";
        setTextBlock(value, lesson.trap);
        card.appendChild(value);
        quick.appendChild(card);
      }
      box.appendChild(quick);
    }

    if ((lesson.objectives || []).length) {
      const section = el("section", "k-section");
      section.appendChild(sectionHead("学完这一讲，你应该能做到"));
      const list = el("ol", "k-objectives");
      lesson.objectives.forEach((row, i) => {
        const li = el("li");
        const value = typeof row === "string" ? row : row.text;
        li.dataset.kid = typeof row === "string"
          ? "E" + String(lesson.episode).padStart(2, "0") + ":objective:" + i
          : row.id;
        li.appendChild(rich(value));
        list.appendChild(li);
      });
      section.appendChild(list);
      box.appendChild(section);
    }

    if ((lesson.terms || []).length) {
      const section = el("section", "k-section");
      section.appendChild(sectionHead("先装术语，再看推导", "术语首次出现时先定义"));
      const wrap = el("div", "k-table-wrap");
      const table = el("table", "k-term-table");
      const thead = el("thead");
      const hr = el("tr");
      ["术语", "人话解释", "最小例子", "首次出现", "自评"].forEach((x) => hr.appendChild(el("th", "", x)));
      thead.appendChild(hr);
      table.appendChild(thead);
      const tbody = el("tbody");
      lesson.terms.forEach((row) => {
        const tr = el("tr");
        const name = el("td");
        name.dataset.kid = row.id + ":name";
        name.className = "k-term-name";
        name.appendChild(rich(row.term));
        tr.appendChild(name);
        const plain = el("td");
        plain.dataset.kid = row.id;
        plain.appendChild(rich(row.plain));
        tr.appendChild(plain);
        const example = el("td");
        example.dataset.kid = row.id + ":example";
        example.appendChild(rich(row.example));
        tr.appendChild(example);
        tr.appendChild(el("td", "", row.first || ""));
        const self = el("td");
        const select = el("select", "k-self");
        ["未评", "会", "模糊", "不会"].forEach((x) => {
          const opt = el("option", "", x);
          opt.value = x;
          select.appendChild(opt);
        });
        try {
          select.value = localStorage.getItem("vks_self_" + S.data.episode.id + "_" + row.id) || "未评";
        } catch (_) {}
        select.onchange = () => {
          try {
            localStorage.setItem("vks_self_" + S.data.episode.id + "_" + row.id, select.value);
          } catch (_) {}
        };
        self.appendChild(select);
        tr.appendChild(self);
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
      wrap.appendChild(table);
      section.appendChild(wrap);
      box.appendChild(section);
    }

    if (S.index && S.index.network) {
      box.appendChild(renderNetwork(lesson));
    }

    if ((lesson.timeline || []).length) {
      const section = el("section", "k-section");
      section.appendChild(sectionHead("跟着视频走", "点时间直接跳转"));
      const list = el("div", "k-timeline");
      list.id = "ktimeline";
      lesson.timeline.forEach((row, i) => {
        const item = el("div", "k-timeline-item");
        item.dataset.index = i;
        item.dataset.start = row.start == null ? "" : row.start;
        item.dataset.end = row.end == null ? "" : row.end;
        item.onclick = () => {
          if (row.start != null) seek(row.start);
        };
        const time = el("button", "k-time", row.time || clock(row.start));
        time.type = "button";
        time.onclick = (ev) => {
          ev.stopPropagation();
          if (row.start != null) seek(row.start);
        };
        item.appendChild(time);
        const body = el("div");
        const topic = el("div", "k-timeline-topic");
        topic.dataset.kid = row.id + ":topic";
        topic.appendChild(rich(row.topic));
        body.appendChild(topic);
        const must = el("div", "k-timeline-must");
        must.dataset.kid = row.id + ":must";
        must.appendChild(rich(row.must));
        body.appendChild(must);
        item.appendChild(body);
        list.appendChild(item);
      });
      section.appendChild(list);
      box.appendChild(section);
    }

    if ((lesson.core || []).length) {
      const section = el("section", "k-section");
      section.appendChild(sectionHead("核心机制", "黄色高亮是视频强调的得分点"));
      lesson.core.forEach((row) => {
        const card = el("article", "k-core-card");
        const top = el("div", "k-core-top");
        const heading = el("h4");
        heading.dataset.kid = row.id + ":heading";
        heading.appendChild(rich(row.heading));
        top.appendChild(heading);
        const time = el("button", "k-core-time", row.time || clock(row.start));
        time.type = "button";
        time.onclick = () => seek(row.start || 0);
        top.appendChild(time);
        card.appendChild(top);
        const body = el("div", "k-core-body");
        body.dataset.kid = row.id;
        body.appendChild(rich(row.body));
        card.appendChild(body);
        section.appendChild(card);
      });
      box.appendChild(section);
    }

    if ((lesson.visuals || []).length) {
      const section = el("section", "k-section");
      section.appendChild(sectionHead("看画面，别只看文字", "点击图跳到对应讲解"));
      const grid = el("div", "k-visual-grid");
      lesson.visuals.forEach((row) => {
        const card = el("article", "k-visual");
        const hit = el("button");
        hit.type = "button";
        hit.title = "跳到 " + (row.time || clock(row.start));
        hit.onclick = () => seek(row.start || 0);
        const img = el("img");
        img.loading = "lazy";
        const src = row.file
          ? "/media/knowledge-frame?id=" + encodeURIComponent(S.data.episode.id) + "&file=" + encodeURIComponent(row.file)
          : "/media/frame?id=" + encodeURIComponent(S.data.episode.id) + "&at=" + Math.max(0.1, row.start || 0);
        img.src = authUrl(src);
        img.alt = row.caption || "关键画面";
        img.onerror = () => { hit.style.display = "none"; };
        hit.appendChild(img);
        hit.appendChild(el("time", "", row.time || clock(row.start)));
        card.appendChild(hit);
        const caption = el("div", "k-visual-caption");
        caption.dataset.kid = row.id + ":caption";
        caption.appendChild(rich(row.caption));
        card.appendChild(caption);
        grid.appendChild(card);
      });
      section.appendChild(grid);
      if (lesson.visualThesis) {
        const callout = el("div", "k-callout visual");
        callout.dataset.kid = "E" + String(lesson.episode).padStart(2, "0") + ":visualThesis";
        callout.appendChild(rich(lesson.visualThesis));
        section.appendChild(callout);
      }
      (lesson.visualRead || []).forEach((row, i) => {
        const callout = el("div", "k-callout visual");
        callout.dataset.kid = typeof row === "string"
          ? "E" + String(lesson.episode).padStart(2, "0") + ":visualRead:" + i
          : row.id;
        callout.appendChild(rich(typeof row === "string" ? row : row.text));
        section.appendChild(callout);
      });
      box.appendChild(section);
    }

    if (lesson.trap || lesson.memoryHook) {
      const section = el("section", "k-section");
      section.appendChild(sectionHead("容易失分的地方"));
      if (lesson.trap) {
        const callout = el("div", "k-callout");
        callout.dataset.kid = "E" + String(lesson.episode).padStart(2, "0") + ":trap";
        callout.appendChild(rich(lesson.trap));
        section.appendChild(callout);
      }
      if (lesson.memoryHook) {
        const callout = el("div", "k-callout hook");
        callout.dataset.kid = "E" + String(lesson.episode).padStart(2, "0") + ":hook";
        callout.appendChild(rich(lesson.memoryHook));
        section.appendChild(callout);
      }
      box.appendChild(section);
    }

    if ((lesson.recall || []).length) {
      const section = el("section", "k-section k-recall");
      section.appendChild(sectionHead("主动回忆", "先自己回答，再展开"));
      lesson.recall.forEach((row) => {
        const details = el("details");
        const summary = el("summary");
        summary.dataset.kid = row.id + ":q";
        summary.appendChild(rich(row.q));
        const answer = el("div", "answer");
        answer.dataset.kid = row.id + ":a";
        answer.appendChild(rich(row.a));
        details.appendChild(summary);
        details.appendChild(answer);
        section.appendChild(details);
      });
      box.appendChild(section);
    }

    const overrides = (S.kstate && S.kstate.overrides) || {};
    Object.entries(overrides).forEach(([kid, value]) => applyOverride(kid, value));
    renderAnnotations();
    bindVideo();
    renderThumbs();
    syncTimeline(window.__vp && window.__vp.video ? window.__vp.video.currentTime : 0, false);
  }

  function renderNetwork(lesson) {
    const section = el("section", "k-section");
    section.appendChild(sectionHead("知识不是清单，是一张网", "点节点看它怎样连接"));
    const card = el("div", "k-network-card");
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", "0 0 920 330");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", S.index.network.title);
    svg.classList.add("k-network-svg");
    const defs = document.createElementNS(NS, "defs");
    defs.innerHTML = '<marker id="k-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(0,229,255,.35)"/></marker>';
    svg.appendChild(defs);
    const knownPos = {
      overview: [460, 45], process: [170, 165], memory: [460, 165],
      file: [750, 165], io: [460, 285],
    };
    const pos = {};
    S.index.network.nodes.forEach((node, i) => {
      if (knownPos[node.id]) {
        pos[node.id] = knownPos[node.id];
        return;
      }
      const perRow = Math.min(3, S.index.network.nodes.length);
      const row = Math.floor(i / perRow);
      const col = i % perRow;
      const count = Math.min(perRow, S.index.network.nodes.length - row * perRow);
      pos[node.id] = [460 + (col - (count - 1) / 2) * 285, 80 + row * 155];
    });
    const groups = {};
    S.index.network.nodes.forEach((n) => {
      groups[n.id] = n;
    });
    S.index.network.edges.forEach((edge) => {
      const a = pos[edge.from], b = pos[edge.to];
      if (!a || !b) return;
      const path = document.createElementNS(NS, "path");
      const mx = (a[0] + b[0]) / 2;
      const my = (a[1] + b[1]) / 2 + (edge.dash ? 12 : 0);
      path.setAttribute("d", `M ${a[0]} ${a[1]} Q ${mx} ${my} ${b[0]} ${b[1]}`);
      path.setAttribute("class", "edge" + (edge.dash ? " dash" : ""));
      path.setAttribute("marker-end", "url(#k-arrow)");
      svg.appendChild(path);
      const label = document.createElementNS(NS, "text");
      label.setAttribute("x", String(mx));
      label.setAttribute("y", String(my - 5));
      label.setAttribute("class", "edge-label");
      label.textContent = edge.label;
      svg.appendChild(label);
    });
    S.index.network.nodes.forEach((n) => {
      const xy = pos[n.id];
      if (!xy) return;
      const g = document.createElementNS(NS, "g");
      g.setAttribute("class", "node");
      g.setAttribute("role", "button");
      g.setAttribute("tabindex", "0");
      g.setAttribute("aria-label", n.label + "：" + n.subtitle);
      g.dataset.nodeId = n.id;
      g.setAttribute("transform", `translate(${xy[0] - 82},${xy[1] - 27})`);
      const rect = document.createElementNS(NS, "rect");
      rect.setAttribute("width", "164");
      rect.setAttribute("height", "54");
      rect.setAttribute("rx", "9");
      g.appendChild(rect);
      const title = document.createElementNS(NS, "text");
      title.setAttribute("x", "82");
      title.setAttribute("y", "22");
      title.textContent = n.label;
      g.appendChild(title);
      const sub = document.createElementNS(NS, "text");
      sub.setAttribute("x", "82");
      sub.setAttribute("y", "39");
      sub.setAttribute("class", "sub");
      sub.textContent = n.subtitle;
      g.appendChild(sub);
      g.addEventListener("click", () => {
        svg.querySelectorAll(".node").forEach((x) => x.classList.toggle("on", x === g));
        showNetworkDetail(n);
      });
      g.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          g.dispatchEvent(new Event("click"));
        }
      });
      svg.appendChild(g);
    });
    card.appendChild(svg);
    const detail = el("div", "k-network-detail");
    detail.id = "knetdetail";
    const currentChapter = String(lesson.chapter || "");
    const active = S.index.network.nodes.find((n) => {
      const ids = n.episodeIds || n.episodes || [];
      return ids.includes(lesson.id) || ids.includes(lesson.episode);
    }) || S.index.network.nodes.find((n) => currentChapter.includes(n.label.replace("操作系统", "")));
    if (active) {
      detail.textContent = active.label + "：" + active.subtitle + "。当前讲属于这张知识网的这个区域。";
    } else {
      detail.textContent = "先看节点之间的箭头：它们表示前一模块为后一模块提供了什么能力。";
    }
    card.appendChild(detail);
    if ((lesson.bridges || []).length) {
      const bridges = el("div", "k-bridge-list");
      lesson.bridges.forEach((row, i) => {
        const b = el("span", "k-bridge");
        b.dataset.kid = typeof row === "string"
          ? "E" + String(lesson.episode).padStart(2, "0") + ":bridge:" + i
          : row.id;
        b.appendChild(rich(typeof row === "string" ? row : row.text));
        bridges.appendChild(b);
      });
      card.appendChild(bridges);
    }
    section.appendChild(card);
    return section;
  }

  function showNetworkDetail(node) {
    const box = byId("knetdetail");
    if (!box) return;
    box.innerHTML = "";
    const ids = node.episodeIds || node.episodes || [];
    const first = ids[0];
    box.appendChild(document.createTextNode(
      node.label + "：" + node.subtitle + "。覆盖 " + ids.length + " 个知识节点。"
    ));
    if (first && typeof window.selectCourseEpisode === "function") {
      const b = button("打开关联视频", "", () => window.selectCourseEpisode(String(first)));
      b.style.marginLeft = "6px";
      b.style.padding = "2px 6px";
      box.appendChild(b);
    }
  }

  function renderThumbs() {
    const th = byId("thumbs");
    const lesson = S.data && S.data.episode;
    if (!th || !lesson) return;
    th.innerHTML = "";
    const visuals = (lesson.visuals || []).slice(0, 8);
    if (!visuals.length) {
      const start = (lesson.timeline || []).map((x) => x.start).filter((x) => x != null).slice(0, 6);
      start.forEach((at, i) => visuals.push({ start: at, time: clock(at), _generated: i }));
    }
    visuals.forEach((row) => {
      const box = el("div", "th");
      const img = el("img");
      img.loading = "lazy";
      const src = row.file
        ? "/media/knowledge-frame?id=" + encodeURIComponent(lesson.id) + "&file=" + encodeURIComponent(row.file)
        : "/media/frame?id=" + encodeURIComponent(lesson.id) + "&at=" + Math.max(0.1, row.start || 0);
      img.src = authUrl(src);
      img.onerror = () => { box.style.opacity = ".35"; };
      box.appendChild(img);
      box.appendChild(el("u", "", row.time || clock(row.start)));
      box.onclick = () => seek(row.start || 0);
      th.appendChild(box);
    });
  }

  function bindVideo() {
    const vp = window.__vp;
    if (!vp || !vp.video) return;
    const video = vp.video;
    if (!video._vfKnowledgeBound) {
      video._vfKnowledgeBound = true;
      video.addEventListener("timeupdate", () => syncTimeline(video.currentTime, true));
      video.addEventListener("seeked", () => syncTimeline(video.currentTime, true));
    }
    const lesson = S.data && S.data.episode;
    if (lesson && vp.setChapters) {
      const chapters = (lesson.timeline || [])
        .filter((x) => x.start != null)
        .map((x) => ({ start: x.start, label: x.topic }));
      vp.chapters = chapters;
      vp._pendingChapters = chapters;
      vp.setChapters(chapters);
    }
  }

  function syncTimeline(seconds, allowScroll) {
    const lesson = S.data && S.data.episode;
    if (!lesson) return;
    let active = -1;
    for (let i = 0; i < (lesson.timeline || []).length; i++) {
      const row = lesson.timeline[i];
      if (row.start != null && seconds >= row.start - 0.05 &&
          (row.end == null || seconds < row.end + 0.05)) {
        active = i;
        break;
      }
    }
    if (active < 0) {
      for (let i = 0; i < (lesson.timeline || []).length; i++) {
        if (lesson.timeline[i].start != null && seconds >= lesson.timeline[i].start) active = i;
      }
    }
    const list = byId("ktimeline");
    if (list) {
      const rows = list.querySelectorAll(".k-timeline-item");
      rows.forEach((x, i) => x.classList.toggle("on", i === active));
      if (allowScroll && S.follow && active >= 0 && active !== S.currentTimeline && rows[active]) {
        const target = Math.max(0, rows[active].offsetTop - list.clientHeight / 2 + rows[active].clientHeight / 2);
        list.scrollTo({ top: target, behavior: "smooth" });
      }
    }
    S.currentTimeline = active;
    const dockTime = document.querySelector(".k-ai-head span");
    if (dockTime) dockTime.textContent = "视频 " + clock(seconds);
  }

  function toggleFollow() {
    S.follow = !S.follow;
    const b = byId("kfollow");
    if (b) {
      b.textContent = "跟随播放：" + (S.follow ? "开" : "关");
      b.classList.toggle("on", S.follow);
    }
    if (S.follow && window.__vp && window.__vp.video) syncTimeline(window.__vp.video.currentTime, true);
  }

  function renderAnnotations() {
    const box = byId("knowledge");
    if (!box) return;
    box.querySelectorAll(".k-annotation").forEach((x) => x.remove());
    const rows = (S.kstate && S.kstate.annotations) || [];
    rows.forEach((row) => {
      const note = el("aside", "k-annotation");
      note.dataset.annotationId = row.id;
      const span = el("span");
      span.appendChild(rich(row.text));
      note.appendChild(span);
      const kill = el("button", "", "×");
      kill.title = "删除旁注";
      kill.onclick = () => deleteAnnotation(row.id);
      note.appendChild(kill);
      const target = nodeAt(row.kid, box);
      if (target) {
        if (target.matches("td,summary,li,span")) {
          (target.closest("tr") || target.closest("details") || target.closest("li") || target.parentElement || box).appendChild(note);
        } else {
          target.appendChild(note);
        }
      } else {
        box.appendChild(note);
      }
    });
  }

  async function deleteAnnotation(id) {
    if (!S.data) return;
    const res = await fetch("/api/annotations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: S.data.episode.id, act: "del", annotationId: id }),
    });
    const d = await res.json();
    if (d.ok) {
      S.kstate = d.state;
      renderAnnotations();
      toast("旁注已删除");
    } else {
      toast(d.error || "删除失败");
    }
  }

  async function addAnnotation(text, kid, time, kind) {
    if (!S.data || !text) return;
    const res = await fetch("/api/annotations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: S.data.episode.id,
        act: "add",
        text,
        kid: kid || "",
        time: time || 0,
        kind: kind || "ai",
      }),
    });
    const d = await res.json();
    if (d.ok) {
      S.kstate = d.state;
      renderAnnotations();
      toast("已放入段落旁的浅色旁注");
    } else {
      toast(d.error || "旁注保存失败");
    }
  }

  function setupSelection() {
    const tools = el("div", "k-select-tools");
    tools.id = "kselecttools";
    [
      ["explain", "解释"],
      ["check", "查错"],
      ["simplify", "白话"],
      ["example", "例子"],
      ["highlight", "标重点"],
      ["custom", "追问"],
    ].forEach(([action, label]) => {
      if (label === "追问") tools.appendChild(el("i", "sep"));
      const b = el("button", "", label);
      b.type = "button";
      b.onmousedown = (ev) => ev.preventDefault();
      b.onclick = () => {
        tools.classList.remove("show");
        ask(action);
      };
      tools.appendChild(b);
    });
    document.body.appendChild(tools);

    document.addEventListener("mouseup", () => {
      const root = byId("knowledge");
      if (!root) return;
      window.setTimeout(() => {
        const sel = window.getSelection();
        if (!sel || sel.isCollapsed || !root.contains(sel.anchorNode) || !root.contains(sel.focusNode)) {
          tools.classList.remove("show");
          S.selected = null;
          return;
        }
        const text = sel.toString().replace(/\s+/g, " ").trim();
        if (text.length < 2) {
          tools.classList.remove("show");
          return;
        }
        const range = sel.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        let host = sel.anchorNode.nodeType === 1 ? sel.anchorNode : sel.anchorNode.parentElement;
        const target = host && host.closest("[data-kid]");
        S.selected = {
          text: text.slice(0, 4000),
          kid: target ? target.dataset.kid : "",
          time: window.__vp && window.__vp.video ? window.__vp.video.currentTime : 0,
        };
        tools.style.left = Math.max(8, Math.min(window.innerWidth - 350, rect.left + rect.width / 2 - 160)) + "px";
        tools.style.top = Math.max(8, rect.top - 38) + "px";
        tools.classList.add("show");
      }, 0);
    });

    document.addEventListener("mousedown", (ev) => {
      if (!tools.contains(ev.target) && !byId("knowledge").contains(ev.target)) {
        tools.classList.remove("show");
      }
    });
    window.addEventListener("scroll", () => tools.classList.remove("show"), true);
  }

  function setupDock() {
    const right = document.querySelector(".col.right");
    if (!right) return;
    const dock = el("section", "k-ai-dock");
    dock.id = "kaidock";
    const head = el("div", "k-ai-head");
    head.appendChild(el("b", "", "AI 导师"));
    head.appendChild(el("span", "", "视频 00:00"));
    const close = el("button", "", "×");
    close.type = "button";
    close.onclick = () => dock.classList.remove("show");
    head.appendChild(close);
    dock.appendChild(head);
    const scroll = el("div", "k-ai-scroll");
    scroll.id = "kaiscroll";
    scroll.innerHTML = '<div class="k-ai-status">选中左侧笔记中的任意内容，或直接在下方提问。</div>';
    dock.appendChild(scroll);
    const compose = el("form", "k-ai-compose");
    const input = el("input");
    input.id = "kaiinput";
    input.placeholder = "追问：这里为什么成立？";
    input.autocomplete = "off";
    const go = el("button", "", "发送");
    go.type = "submit";
    compose.appendChild(input);
    compose.appendChild(go);
    compose.onsubmit = (ev) => {
      ev.preventDefault();
      const q = input.value.trim();
      if (!q && !(S.selected && S.selected.text)) return;
      input.value = "";
      ask("custom", q);
    };
    dock.appendChild(compose);
    right.appendChild(dock);

    const toastBox = el("div", "k-toast");
    toastBox.id = "ktoast";
    document.body.appendChild(toastBox);
  }

  function openDock(action) {
    const dock = byId("kaidock");
    if (dock) dock.classList.add("show");
    if (action === "custom") {
      const input = byId("kaiinput");
      if (input) setTimeout(() => input.focus(), 50);
      if (S.selected && S.selected.text) {
        const scroll = byId("kaiscroll");
        if (scroll && !S.lastAnswer) {
          scroll.innerHTML = "";
          const hint = el("div", "k-ai-status", "已选中：" + S.selected.text.slice(0, 220));
          scroll.appendChild(hint);
        }
      }
    }
  }

  async function ask(action, question) {
    if (!S.data) return;
    const selected = S.selected || { text: "", kid: "", time: 0 };
    const current = window.__vp && window.__vp.video ? window.__vp.video.currentTime : selected.time;
    openDock(action);
    const scroll = byId("kaiscroll");
    if (!scroll) return;
    scroll.innerHTML = "";
    scroll.scrollTop = 0;
    const status = el("div", "k-ai-status");
    status.innerHTML = '<span class="k-spinner"></span>正在结合当前画面、转录和笔记上下文…';
    scroll.appendChild(status);
    const questionText = String(question || "").trim();
    if (questionText) {
      const preview = el("div", "k-ai-answer");
      preview.style.marginTop = "7px";
      preview.textContent = "你的问题：" + questionText;
      scroll.appendChild(preview);
    } else if (selected.text) {
      const preview = el("div", "k-ai-answer");
      preview.style.marginTop = "7px";
      preview.textContent = "选中：" + selected.text.slice(0, 220);
      scroll.appendChild(preview);
    }
    try {
      const res = await fetch("/api/ai/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: S.data.episode.id,
          selected: selected.text || "",
          kid: selected.kid || "",
          action: action,
          question: questionText,
          time: current,
          history: S.history.slice(-4),
        }),
      });
      const started = await res.json();
      if (!started.ok) throw new Error(started.error || "AI 导师暂不可用");
      let d = null;
      for (let i = 0; i < 240; i++) {
        await new Promise((resolve) => setTimeout(resolve, 900));
        const poll = await fetch("/api/ai/job?id=" + encodeURIComponent(started.job));
        const row = await poll.json();
        if (!row.ok) throw new Error(row.error || "AI 推理失败");
        if (row.status === "done") {
          d = Object.assign({}, row.result, { ok: true });
          break;
        }
      }
      if (!d) throw new Error("AI 请求超时，请重试");
      d._action = action;
      S.lastAnswer = d;
      S.history.push({ role: "user", text: questionText || selected.text || ACTION_TEXT[action] });
      S.history.push({ role: "assistant", text: d.answer || "" });
      renderAnswer(d);
    } catch (err) {
      scroll.innerHTML = "";
      const fail = el("div", "k-ai-answer");
      fail.style.color = "#ffb3a2";
      fail.textContent = err.message || String(err);
      scroll.appendChild(fail);
      const tip = el("div", "k-ai-status");
      tip.style.marginTop = "7px";
      tip.textContent = "模型提供方不可用时，笔记阅读、时间同步和本地旁注仍可正常使用。";
      scroll.appendChild(tip);
    }
  }

  function renderMarkdown(box, text) {
    const lines = String(text || "").replace(/\r/g, "").split("\n");
    let i = 0;
    while (i < lines.length) {
      const line = lines[i];
      if (!line.trim()) { i++; continue; }
      if (line.trim().startsWith("```")) {
        const code = [];
        i++;
        while (i < lines.length && !lines[i].trim().startsWith("```")) code.push(lines[i++]);
        i++;
        const pre = el("pre");
        pre.style.cssText = "white-space:pre-wrap;background:rgba(0,8,14,.75);border:1px solid rgba(0,229,255,.13);border-radius:7px;padding:7px;color:#a8e8f4;font:9.8px/1.55 Consolas,monospace;overflow:auto";
        pre.textContent = code.join("\n");
        box.appendChild(pre);
        continue;
      }
      if (line.includes("|") && i + 1 < lines.length && /^\s*\|?[\s:|-]+\|[\s:|-]*\s*$/.test(lines[i + 1])) {
        const table = el("table", "k-term-table");
        const heads = line.split("|").map((x) => x.trim()).filter((_, idx, arr) => !(idx === 0 && !arr[idx]) && !(idx === arr.length - 1 && !arr[idx]));
        const thead = el("thead");
        const trh = el("tr");
        heads.forEach((x) => trh.appendChild(el("th", "", x)));
        thead.appendChild(trh);
        table.appendChild(thead);
        const tbody = el("tbody");
        i += 2;
        while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {
          const cells = lines[i].split("|").map((x) => x.trim());
          if (!cells[0]) cells.shift();
          if (cells.length && !cells[cells.length - 1]) cells.pop();
          const tr = el("tr");
          cells.forEach((x) => {
            const td = el("td");
            td.appendChild(rich(x));
            tr.appendChild(td);
          });
          tbody.appendChild(tr);
          i++;
        }
        table.appendChild(tbody);
        const wrap = el("div", "k-table-wrap");
        wrap.style.margin = "6px 0";
        wrap.appendChild(table);
        box.appendChild(wrap);
        continue;
      }
      if (/^\s*[-*]\s+/.test(line) || /^\s*\d+[.)、]\s*/.test(line)) {
        const ordered = /^\s*\d+[.)、]\s*/.test(line);
        const list = el(ordered ? "ol" : "ul");
        list.style.cssText = "margin:5px 0 7px;padding-left:19px;color:#c6e2ea";
        while (i < lines.length && lines[i].trim() &&
               (/^\s*[-*]\s+/.test(lines[i]) || /^\s*\d+[.)、]\s*/.test(lines[i]))) {
          const item = el("li");
          item.style.cssText = "margin:2px 0;font-size:10.8px;line-height:1.6";
          item.appendChild(rich(lines[i].replace(/^\s*(?:[-*]|\d+[.)、])\s*/, "")));
          list.appendChild(item);
          i++;
        }
        box.appendChild(list);
        continue;
      }
      const p = el("p");
      p.style.cssText = "margin:0 0 7px;white-space:normal";
      p.appendChild(rich(line));
      box.appendChild(p);
      i++;
    }
  }

  function renderAnswer(d) {
    const scroll = byId("kaiscroll");
    if (!scroll) return;
    scroll.innerHTML = "";
    const answer = el("div", "k-ai-answer");
    renderMarkdown(answer, d.answer || "没有得到可靠回答。");
    scroll.appendChild(answer);

    const meta = el("div", "k-ai-meta");
    meta.appendChild(chip("置信度 " + ({ high: "高", medium: "中", low: "低" }[d.confidence] || "低"),
      d.confidence === "high" ? "mint" : (d.confidence === "low" ? "amber" : "")));
    if (d.uncertain) meta.appendChild(chip("含待确认", "amber"));
    if (d.cached) meta.appendChild(chip("缓存"));
    if (d.model) meta.appendChild(chip(d.model));
    scroll.appendChild(meta);

    if (Number.isFinite(Number(d.frameAt))) {
      const img = el("img", "k-ai-frame");
      img.loading = "lazy";
      img.src = authUrl("/media/frame?id=" + encodeURIComponent(S.data.episode.id) + "&at=" + Math.max(0.1, Number(d.frameAt)));
      img.title = "跳到这张关键画面";
      img.onclick = () => seek(Number(d.frameAt));
      scroll.appendChild(img);
    }

    (d.evidence || []).forEach((row) => {
      const rowBox = el("div", "k-evidence");
      const at = parseTime(row.time);
      const jump = el("button", "", row.time || "看视频");
      jump.type = "button";
      jump.onclick = () => { if (at != null) seek(at); };
      rowBox.appendChild(jump);
      rowBox.appendChild(el("span", "", row.reason || ""));
      scroll.appendChild(rowBox);
    });

    const actions = el("div", "k-ai-actions");
    if (d.annotation) {
      actions.appendChild(button("设为浅色旁注", "amber", () => {
        const sel = S.selected || {};
        addAnnotation(d.annotation, sel.kid || "", sel.time || 0, "ai");
      }));
    }
    if (d.proposed_revision) {
      renderRevision(d, scroll, actions);
    }
    actions.appendChild(button("继续追问", "", () => {
      const input = byId("kaiinput");
      if (input) input.focus();
    }));
    scroll.appendChild(actions);
    renderHistory(scroll);
    scroll.scrollTop = 0;
  }

  function parseTime(value) {
    if (value == null || value === "") return null;
    if (typeof value === "number") return value;
    const p = String(value).split(":").map(Number);
    if (p.some((x) => !Number.isFinite(x))) return null;
    if (p.length === 2) return p[0] * 60 + p[1];
    if (p.length === 3) return p[0] * 3600 + p[1] * 60 + p[2];
    return null;
  }

  function renderRevision(d, scroll, actions) {
    const draft = Object.assign({}, d.proposed_revision || {});
    if (!draft.kid && S.selected) draft.kid = S.selected.kid || "";
    if (!draft.original && S.selected) draft.original = S.selected.text || "";
    const diff = el("div", "k-diff");
    const h = el("h5", "", "建议修改 · 尚未应用");
    diff.appendChild(h);
    const before = el("div", "k-diff-row before");
    before.appendChild(el("b", "", "原文"));
    before.appendChild(document.createTextNode(draft.original || "（选中内容）"));
    const after = el("div", "k-diff-row after");
    after.appendChild(el("b", "", "建议"));
    after.appendChild(document.createTextNode(draft.replacement || ""));
    diff.appendChild(before);
    diff.appendChild(after);
    if (draft.reason) {
      const why = el("div", "k-diff-row");
      why.appendChild(el("b", "", "原因"));
      why.appendChild(document.createTextNode(draft.reason));
      diff.appendChild(why);
    }
    scroll.appendChild(diff);
    actions.appendChild(button("接受修改", "primary", () => revisionAction("apply", draft)));
    actions.appendChild(button("仅留旁注", "amber", () => revisionAction("annotation", draft)));
    actions.appendChild(button("拒绝", "danger", () => revisionAction("reject", draft)));
  }

  async function revisionAction(act, draft) {
    if (!S.data) return;
    const target = nodeAt(draft.kid);
    if (target) {
      draft.before = target.textContent || "";
      if (S.selected && S.selected.text && (!draft.original || !draft.before.includes(draft.original))) {
        draft.original = S.selected.text;
      }
    }
    const res = await fetch("/api/revisions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: S.data.episode.id, act, draft }),
    });
    const d = await res.json();
    if (!d.ok) {
      toast(d.error || "修订操作失败");
      return;
    }
    S.kstate = d.state;
    if (act === "apply") {
      const value = d.state.overrides[draft.kid];
      if (value != null) applyOverride(draft.kid, value);
      toast("修改已应用，可在 AI 抽屉的修订历史撤销");
    } else if (act === "annotation") {
      if (S.lastAnswer && S.lastAnswer.annotation) {
        await addAnnotation(S.lastAnswer.annotation, draft.kid, S.selected ? S.selected.time : 0, "revision-note");
      }
      toast("已保留为旁注，正文未改");
    } else {
      toast("已拒绝修改，正文未改");
    }
    const scroll = byId("kaiscroll");
    if (scroll) renderHistory(scroll);
  }

  async function undoRevision(id) {
    if (!S.data) return;
    const res = await fetch("/api/revisions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: S.data.episode.id, act: "undo", revisionId: id }),
    });
    const d = await res.json();
    if (!d.ok) {
      toast(d.error || "撤销失败");
      return;
    }
    S.kstate = d.state;
    const row = (d.state.revisions || []).find((x) => x.id === id);
    if (row) {
      if (row.before) applyOverride(row.kid, row.before);
      else {
        const node = nodeAt(row.kid);
        if (node) {
          delete node.dataset.revised;
          render();
        }
      }
    }
    toast("修改已撤销");
    const scroll = byId("kaiscroll");
    if (scroll) renderHistory(scroll);
  }

  function renderHistory(scroll) {
    const old = scroll.querySelector(".k-ai-history");
    if (old) old.remove();
    const rows = ((S.kstate && S.kstate.revisions) || []).slice(-8).reverse();
    if (!rows.length) return;
    const details = el("details", "k-ai-history");
    details.appendChild(el("summary", "", "修订历史（" + rows.length + "）"));
    rows.forEach((row) => {
      const line = el("div", "k-history-row");
      line.appendChild(el("span", "", ({ applied: "已应用", undone: "已撤销",
        rejected: "已拒绝", annotation_only: "仅旁注" }[row.status] || row.status) +
        " · " + (row.reason || row.kid)));
      if (row.status === "applied") {
        const b = el("button", "", "撤销");
        b.onclick = () => undoRevision(row.id);
        line.appendChild(b);
      }
      details.appendChild(line);
    });
    scroll.appendChild(details);
  }

  function toast(message) {
    const box = byId("ktoast");
    if (!box) return;
    box.textContent = message;
    box.classList.add("show");
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => box.classList.remove("show"), 2200);
  }

  async function load(project) {
    const root = byId("knowledge");
    if (!root) return;
    if (S.project && S.project.id === project.id && S.data) {
      bindVideo();
      return;
    }
    S.project = project;
    S.data = null;
    S.kstate = null;
    S.lastAnswer = null;
    S.history = [];
    S.selected = null;
    S.currentTimeline = -1;
    const seq = ++S.loadSeq;
    root.innerHTML = '<div class="k-loading"><div class="k-spinner"></div>正在装入 87 讲知识数据…</div>';
    try {
      const res = await fetch("/api/knowledge?id=" + encodeURIComponent(project.id));
      const d = await res.json();
      if (seq !== S.loadSeq) return;
      if (!d.ok) throw new Error(d.error || "载入失败");
      S.data = d;
      S.index = d.index;
      S.kstate = d.state;
      render();
    } catch (err) {
      if (seq !== S.loadSeq) return;
      root.innerHTML = "";
      const fail = el("div", "k-empty", err.message || String(err));
      fail.style.marginTop = "20px";
      root.appendChild(fail);
    }
  }

  function clear() {
    S.project = null;
    S.data = null;
    S.index = null;
    S.kstate = null;
    const root = byId("knowledge");
    if (root) root.innerHTML = "";
    const dock = byId("kaidock");
    if (dock) dock.classList.remove("show");
  }

  setupSelection();
  setupDock();
  window.KNOWLEDGE = { load, clear, seek, ask, syncTimeline };
})();
