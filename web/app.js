const $ = (id) => document.getElementById(id);
const TOKEN = (() => {
  const fromUrl = new URLSearchParams(location.search).get("t");
  if (fromUrl) localStorage.setItem("vks_token", fromUrl);
  return fromUrl || localStorage.getItem("vks_token") || "";
})();
const withToken = (url) => url + (url.includes("?") ? "&" : "?") + "t=" + encodeURIComponent(TOKEN);
const nativeFetch = window.fetch.bind(window);
window.fetch = (url, options) => {
  const opts = Object.assign({}, options || {});
  opts.headers = Object.assign({}, opts.headers || {});
  if (TOKEN) opts.headers["X-VKS-Token"] = TOKEN;
  return nativeFetch(url, opts);
};

let projects = [];
let current = null;
let vp = null;

function groupOf(project) {
  return (project.courseTitle || "课程") + " · " + (project.chapter || "未分章");
}

function renderList() {
  const query = ($("search").value || "").trim().toLowerCase();
  const groups = new Map();
  projects.forEach((project) => {
    const haystack = [project.title, project.courseTitle, project.chapter, project.dir].join(" ").toLowerCase();
    if (query && !haystack.includes(query)) return;
    const name = groupOf(project);
    if (!groups.has(name)) groups.set(name, []);
    groups.get(name).push(project);
  });
  $("list").innerHTML = "";
  if (!groups.size) {
    $("list").innerHTML = '<div class="empty">没有匹配的视频</div>';
    return;
  }
  let first = null;
  groups.forEach((rows, name) => {
    rows.sort((a, b) => a.seq - b.seq);
    const section = document.createElement("section");
    section.className = "course-group";
    const header = document.createElement("h3");
    header.innerHTML = "<span>" + escapeHtml(name) + "</span><em>" + rows.length + "</em>";
    header.onclick = () => section.classList.toggle("closed");
    const body = document.createElement("div");
    body.className = "group-body";
    rows.forEach((project) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "project" + (current && current.id === project.id ? " on" : "");
      item.dataset.id = project.id;
      item.innerHTML = "<b>" + escapeHtml(project.title) + "</b><span>" +
        escapeHtml(project.minutes + " 分 · " + project.pages + " 个知识块") + "</span>";
      item.onclick = () => selectProject(project, item);
      body.appendChild(item);
      if (!first) first = { project, item };
    });
    section.appendChild(header);
    section.appendChild(body);
    $("list").appendChild(section);
  });
  return first;
}

function escapeHtml(value) {
  return String(value == null ? "" : value).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[ch]);
}

async function boot() {
  try {
    const [projectResponse, aiResponse] = await Promise.all([
      fetch("/api/projects"),
      fetch("/api/ai/status"),
    ]);
    projects = await projectResponse.json();
    const ai = await aiResponse.json();
    $("projectCount").textContent = projects.length + " 讲";
    $("aiBadge").textContent = ai.offline ? "AI：离线演示" : "AI：" + ai.provider;
    $("aiBadge").classList.toggle("offline", !!ai.offline);
    $("providerText").textContent = ai.offline
      ? "当前使用离线演示提供方。"
      : "当前使用 " + ai.provider + "；密钥只在服务端读取。";
    const first = renderList();
    if (first) selectProject(first.project, first.item);
  } catch (err) {
    $("list").innerHTML = '<div class="empty">载入失败：' + escapeHtml(err.message) + "</div>";
  }
}

function selectProject(project, item) {
  current = project;
  document.querySelectorAll(".project").forEach((x) => x.classList.toggle("on", x === item));
  $("title").textContent = project.title;
  $("courseLabel").textContent = (project.courseTitle || "课程") + " / " + (project.chapter || "未分章");
  if (!vp) {
    vp = new VP($("player"), {
      skin: "forge",
      src: withToken("/media/video?id=" + encodeURIComponent(project.id)),
      key: "vks_" + project.id,
      qualities: {},
      quality: null,
      title: "",
      sub: "",
      chapters: [],
      poster: withToken("/media/frame?id=" + encodeURIComponent(project.id) + "&at=1"),
      frameAt: (t) => withToken("/media/frame?id=" + encodeURIComponent(window.__vksId) + "&at=" + Math.max(0.1, t)),
    });
    window.__vp = vp;
  } else {
    window.__vksId = project.id;
    vp.attach(withToken("/media/video?id=" + encodeURIComponent(project.id)));
    vp.opt.key = "vks_" + project.id;
    vp.posKey = "vks_pos_" + project.id;
    vp._posRestored = false;
    vp.setTitle("", "");
  }
  window.__vksId = project.id;
  vp.video.poster = withToken("/media/frame?id=" + encodeURIComponent(project.id) + "&at=1");
  if (window.KNOWLEDGE) window.KNOWLEDGE.load(project);
}

window.selectCourseEpisode = function (id) {
  const project = projects.find((x) => x.id === id);
  if (!project) return;
  const item = document.querySelector('.project[data-id="' + CSS.escape(id) + '"]');
  selectProject(project, item);
  if (item) item.scrollIntoView({ block: "center", behavior: "smooth" });
};

document.querySelectorAll(".tab").forEach((tab) => {
  tab.onclick = () => {
    document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("on", x === tab));
    const name = tab.dataset.tab;
    $("knowledge").classList.toggle("on", name === "knowledge");
    $("about").classList.toggle("on", name === "about");
    $("knowledge").hidden = name !== "knowledge";
    $("about").hidden = name !== "about";
    $("hint").textContent = name === "knowledge"
      ? "视频与笔记同屏 · 点时间跳转 · 选中文字问 AI"
      : "本地优先 · 课程包可独立授权";
  };
});

$("search").addEventListener("input", renderList);
$("theaterBtn").onclick = () => {
  if (vp) {
    if (vp.act) vp.act("theater");
    else document.body.classList.toggle("vp-theater");
  }
};

boot();
