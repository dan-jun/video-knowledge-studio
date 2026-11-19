const $ = (id) => document.getElementById(id);
const S = { modes: [], templates: [], projects: [], current: null, job: null, workflow: null, workflowPoll: null };

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.ok === false) throw new Error(data.error || ("HTTP " + response.status));
  return data;
}

function badge(text, kind = "") {
  $("dependency").textContent = text;
  $("dependency").className = "badge " + kind;
}

function renderModes() {
  $("modes").innerHTML = "";
  $("createMode").innerHTML = "";
  S.modes.forEach((mode) => {
    const card = document.createElement("div");
    card.className = "mode";
    const duration = mode.id === "remix"
      ? "信息守恒，不按时长卡"
      : `${mode.target_min[0]}–${mode.target_min[1]} 分钟`;
    card.innerHTML = `<b><code>${mode.id}</code> · ${mode.label}</b><p>${duration}</p><p>${mode.rules.slice(0, 3).join("；")}</p>`;
    $("modes").appendChild(card);
    const option = document.createElement("option");
    option.value = mode.id;
    option.textContent = `${mode.id} · ${mode.label}`;
    $("createMode").appendChild(option);
  });
}

function renderTemplates() {
  S.templates.forEach((template) => {
    const option = document.createElement("option");
    option.value = template.name;
    option.textContent = template.title;
    $("template").appendChild(option);
  });
}

function renderProjects() {
  $("projects").innerHTML = "";
  if (!S.projects.length) {
    $("projects").innerHTML = '<div class="muted">还没有制作项目</div>';
    return;
  }
  S.projects.forEach((project) => {
    const button = document.createElement("button");
    button.className = "project" + (S.current?.id === project.id ? " on" : "");
    button.innerHTML = `<b>${escapeHtml(project.title)}</b><small>${escapeHtml(project.mode)} · ${escapeHtml(project.stage)}${project.hasVideo ? " · 已成片" : ""}</small>`;
    button.onclick = () => loadProject(project.id);
    $("projects").appendChild(button);
  });
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

function setActions(enabled) {
  document.querySelectorAll("[data-action]").forEach((button) => {
    button.disabled = !enabled || !S.current;
  });
  $("saveBtn").disabled = !enabled || !S.current;
}

function updatePageCount() {
  try {
    const spec = JSON.parse($("specEditor").value);
    const pages = spec.pages || (spec.parts || []).flatMap((part) => part.pages || []);
    $("pageCount").textContent = `${pages.length} 页`;
  } catch {
    $("pageCount").textContent = "JSON 无效";
  }
}

async function loadProject(id) {
  try {
    const data = await api("/api/production/project?id=" + encodeURIComponent(id));
    S.current = data.project;
    $("projectMode").textContent = `${S.current.mode} · ${S.current.label || ""}`;
    $("projectTitle").textContent = S.current.title;
    $("specEditor").value = JSON.stringify(S.current.spec || {}, null, 2);
    $("stage").textContent = `阶段：${S.current.stage} · 分镜：${S.current.hasStoryboard ? "已生成" : "未生成"} · 成片：${S.current.hasVideo ? "已生成" : "未生成"}`;
    const video = $("videoCard");
    if (S.current.hasVideo) {
      video.hidden = false;
      $("video").src = "/media/production?id=" + encodeURIComponent(id) + "&v=" + Date.now();
      $("downloadVideo").href = $("video").src;
    } else {
      video.hidden = true;
      $("video").removeAttribute("src");
    }
    updatePageCount();
    setActions(true);
    renderProjects();
    const workflows = await api("/api/workflows?project=" + encodeURIComponent(id));
    S.workflow = workflows.workflows[0] || null;
    renderWorkflow();
    if (S.workflow && ["running", "cancelling"].includes(S.workflow.status)) pollWorkflow(S.workflow.id);
  } catch (error) {
    $("logs").textContent = error.message;
  }
}

async function loadProjects() {
  const data = await api("/api/production/projects");
  S.projects = data.projects || [];
  renderProjects();
}

async function saveSpec() {
  if (!S.current) return false;
  try {
    const spec = JSON.parse($("specEditor").value);
    const data = await api("/api/production/save", {
      method: "POST",
      body: JSON.stringify({ id: S.current.id, spec }),
    });
    S.current = data.project;
    $("stage").textContent = "规格已保存。下一步：生成分镜。";
    await loadProjects();
    return true;
  } catch (error) {
    $("logs").textContent = "保存失败：" + error.message;
    return false;
  }
}

async function createProject() {
  const mode = $("createMode").value;
  const title = $("createTitle").value.trim();
  if (!title) {
    $("createTitle").focus();
    return;
  }
  let spec = "";
  const template = $("template").value;
  if (template) {
    const data = await api("/api/production/template?name=" + encodeURIComponent(template));
    data.spec.title = title;
    spec = JSON.stringify(data.spec);
  }
  try {
    const data = await api("/api/production/create", {
      method: "POST",
      body: JSON.stringify({ mode, title, spec }),
    });
    S.current = data.project;
    $("createTitle").value = "";
    await loadProject(S.current.id);
    await loadProjects();
  } catch (error) {
    $("logs").textContent = "创建失败：" + error.message;
  }
}

async function pollJob(id) {
  for (;;) {
    const data = await api("/api/production/job?id=" + encodeURIComponent(id));
    const job = data.job;
    S.job = job;
    $("logs").textContent = job.logs.join("\n") || "任务已启动…";
    $("logs").scrollTop = $("logs").scrollHeight;
    $("jobState").textContent = job.status === "running" ? job.action + " 中" : job.status;
    $("jobState").className = "badge " + (job.status === "done" ? "ok" : job.status === "failed" ? "warn" : "");
    if (job.status !== "running") {
      await loadProject(job.project);
      await loadProjects();
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 900));
  }
}

async function runAction(action) {
  if (!S.current) return;
  if (action === "generate" && !await saveSpec()) return;
  try {
    const data = await api("/api/production/action", {
      method: "POST",
      body: JSON.stringify({ id: S.current.id, action }),
    });
    $("logs").textContent = "任务已启动…";
    await pollJob(data.job.id);
  } catch (error) {
    $("logs").textContent = error.message;
    $("jobState").textContent = "失败";
    $("jobState").className = "badge warn";
  }
}

function renderWorkflow() {
  const flow = S.workflow;
  const running = flow && ["running", "cancelling"].includes(flow.status);
  const blocked = flow && ["running", "cancelling", "interrupted", "waiting_review"].includes(flow.status);
  setActions(!blocked);
  $("workflowStart").disabled = !S.current || !!blocked;
  $("workflowResume").disabled = !flow || running || ["done", "abandoned", "interrupted"].includes(flow.status);
  $("workflowCancel").disabled = !flow || flow.status !== "running";
  $("workflowAbandon").disabled = !flow || !["ready", "waiting_review", "failed", "cancelled"].includes(flow.status);
  $("workflowConfirmStopped").disabled = !flow || flow.status !== "interrupted";
  if (!flow) {
    $("workflowStatus").textContent = "流程依次执行生成分镜、检查、渲染；每步完成后等待确认。来源搜索和笔记生成仍需外部协助。";
    return;
  }
  const zhStatus = {ready:"待开始", running:"执行中", cancelling:"正在取消", waiting_review:"等待检查确认", done:"已完成", failed:"失败", cancelled:"已取消", interrupted:"服务中断", abandoned:"已结束", pending:"待执行"};
  const zhAction = {generate:"生成分镜", gates:"检查", render:"渲染"};
  const actionNames = {generate:"生成分镜", gates:"检查", render:"渲染"};
  const current = flow.steps.find(s => s.status === "running") || [...flow.steps].reverse().find(s => s.status !== "pending");
  const zhMessage = flow.status === "waiting_review" ? `${actionNames[current?.action] || "当前步骤"}完成，请检查后继续。`
    : flow.status === "interrupted" ? `服务中断，请先检查并停止旧进程及其子进程（进程号：${flow.activePid || "未知"}），再确认。`
    : flow.status === "done" ? "渲染已完成，请检查播放、画面和来源。"
    : flow.message;
  $("workflowStatus").textContent = window.VKS_LANG === "en"
    ? `${flow.status}: ${flow.steps.map(s => `${s.action}=${s.status}`).join(" → ")} · ${flow.message}`
    : `${zhStatus[flow.status] || flow.status}：${flow.steps.map(s => `${zhAction[s.action] || s.action}=${zhStatus[s.status] || s.status}`).join(" → ")} · ${zhMessage}`;
  const latest = [...flow.steps].reverse().find(s => s.logs?.length);
  if (flow.status === "running") {
    const current = flow.steps.find(s => s.status === "running");
    if (current?.job) api("/api/production/job?id=" + encodeURIComponent(current.job))
      .then(data => { if (S.workflow?.id === flow.id) $("logs").textContent = data.job.logs.join("\n"); }).catch(() => {});
  } else if (latest) $("logs").textContent = latest.logs.join("\n");
}

async function pollWorkflow(id) {
  if (S.workflowPoll === id) return;
  S.workflowPoll = id;
  try {
    while (S.workflow?.id === id) {
      const data = await api("/api/workflows/item?id=" + encodeURIComponent(id));
      if (S.workflow?.id !== id) break;
      S.workflow = data.workflow;
      renderWorkflow();
      if (!["running", "cancelling"].includes(S.workflow.status)) {
        if (S.current?.id === S.workflow.project) {
          const project = await api("/api/production/project?id=" + encodeURIComponent(S.workflow.project));
          if (S.current?.id === S.workflow.project) {
            S.current = project.project;
            $("stage").textContent = `阶段：${S.current.stage} · 分镜：${S.current.hasStoryboard ? "已生成" : "未生成"} · 成片：${S.current.hasVideo ? "已生成" : "未生成"}`;
            if (S.current.hasVideo) {
              $("videoCard").hidden = false;
              $("video").src = "/media/production?id=" + encodeURIComponent(S.current.id) + "&v=" + Date.now();
              $("downloadVideo").href = $("video").src;
            }
            await loadProjects();
          }
        }
        break;
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  } catch (error) { $("logs").textContent = error.message; }
  finally { if (S.workflowPoll === id) S.workflowPoll = null; }
}

async function workflowAction(action) {
  try {
    if (action === "create") {
      if (!await saveSpec()) return;
      const data = await api("/api/workflows/create", {method: "POST", body: JSON.stringify({project: S.current.id})});
      S.workflow = data.workflow;
      action = "resume";
    }
    if (action === "resume" && S.workflow?.steps.find(step => step.status !== "done")?.action === "render") {
      const message = window.VKS_LANG === "en"
        ? "Rendering may take significant time and may use an online voice service or a configured paid provider. Continue?"
        : "渲染可能耗时较长，并可能使用在线配音或已配置的付费服务。是否继续？";
      if (!confirm(message)) return;
    }
    const data = await api("/api/workflows/" + action, {method: "POST", body: JSON.stringify({id: S.workflow.id})});
    S.workflow = data.workflow;
    renderWorkflow();
    pollWorkflow(S.workflow.id);
  } catch (error) { $("logs").textContent = error.message; }
}

async function boot() {
  $("saveBtn").onclick = saveSpec;
  $("createBtn").onclick = createProject;
  $("refreshBtn").onclick = loadProjects;
  $("workflowStart").onclick = () => workflowAction("create");
  $("workflowResume").onclick = () => workflowAction("resume");
  $("workflowCancel").onclick = () => workflowAction("cancel");
  $("workflowAbandon").onclick = () => workflowAction("abandon");
  $("workflowConfirmStopped").onclick = async () => {
    if (!S.workflow || !confirm(`请先检查并停止之前的制作进程及其子进程（记录的进程号：${S.workflow.activePid || "未知"}）。确定它们已经停止吗？`)) return;
    try {
      const data = await api("/api/workflows/acknowledge-stopped", {method: "POST", body: JSON.stringify({id: S.workflow.id, confirmed: true})});
      S.workflow = data.workflow;
      renderWorkflow();
    } catch (error) { $("logs").textContent = error.message; }
  };
  $("specEditor").addEventListener("input", updatePageCount);
  document.querySelectorAll("[data-action]").forEach((button) => {
    button.onclick = () => runAction(button.dataset.action);
  });
  try {
    const data = await api("/api/production/modes");
    S.modes = data.modes || [];
    S.templates = data.templates || [];
    renderModes();
    renderTemplates();
    if (data.dependencies.ready) {
      badge("生产依赖已就绪", "ok");
    } else {
      badge("缺少：" + data.dependencies.missing.join("、"), "warn");
      $("logs").textContent = "提示：" + data.dependencies.install + "\n\n仍可创建、编辑、保存规格并生成分镜；安装依赖后才能运行门禁与渲染。";
    }
    await loadProjects();
    if (S.projects.length) await loadProject(S.projects[0].id);
    else setActions(false);
  } catch (error) {
    badge("生产模块不可用", "warn");
    $("logs").textContent = error.message;
  }
}

boot();
