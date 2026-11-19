(() => {
  const params = new URLSearchParams(location.search);
  const lang = params.get("lang") === "en" ? "en" : "zh";
  window.VKS_LANG = lang;

  if (lang !== "en") return;

  document.documentElement.lang = "en";
  document.title = document.title
    .replace("视频制作 · ", "Production · ")
    .replace("登录 · ", "Sign in · ");

  const exact = {
    "视频制作": "Production",
    "课程视频与结构化笔记同屏。选中任意内容，让 AI 解释、查错或给出可撤销的修改建议。": "Course video and structured notes, side by side. Select any passage to ask AI to explain it, check it, or propose an undoable edit.",
    "课程目录": "Course library",
    "搜索课程、章节或视频…": "Search courses, chapters, or lessons…",
    "选择一讲开始": "Select a lesson to begin",
    "AI 检测中": "Checking AI",
    "剧场模式": "Theater",
    "本地优先": "Local-first",
    "视频与课程包不离开你的机器；只有点击 AI 提问时，才会把当前选中的笔记、相关转录与关键画面发送给已配置的模型提供方。": "Videos and course packs stay on your machine. Only when you ask AI does the selected note, nearby transcript, and current frame leave for the configured model provider.",
    "知识点整理": "Knowledge notes",
    "使用说明": "Guide",
    "视频同步": "Video sync",
    "关键帧": "Keyframes",
    "知识网": "Knowledge graph",
    "视频与笔记同屏 · 点时间跳转 · 选中文字问 AI": "Video and notes side by side · jump by timestamp · select text to ask AI",
    "正在载入课程包…": "Loading course packs…",
    "没有匹配的视频": "No matching lessons",
    "怎样使用": "How it works",
    "在左侧选择章节和视频。": "Choose a chapter and lesson on the left.",
    "播放时，右侧时间轴会自动高亮当前知识块。": "During playback, the timeline highlights the current knowledge block.",
    "拖动选中不懂的笔记，使用浮动工具条提问。": "Select a note you do not understand and use the floating toolbar to ask.",
    "AI 修改建议只有在你点击“接受修改”后才会写入本地历史。": "AI edits are written to local history only after you choose Accept edit.",
    "快捷键": "Keyboard shortcuts",
    "课程包": "Course packs",
    "把视频、知识 JSON 和 course.json 放进 packs/<id>/，重启或调用重新载入即可。课程内容与平台代码可以分别授权。": "Put videos, knowledge JSON, and course.json under packs/<id>/, then reload. Course content and platform code can be licensed separately.",
    "AI 提供方": "AI provider",
    "正在检测…": "Checking…",
    "未配置模型时使用“离线演示模式”，只验证交互，不生成知识结论。": "Without a configured model, the app runs in offline demo mode and validates interactions only.",
    "返回学习工作台": "Back to study workspace",
    "检查生产依赖…": "Checking production dependencies…",
    "选择产线": "Production mode",
    "正在载入…": "Loading…",
    "新建项目": "New project",
    "模式": "Mode",
    "标题": "Title",
    "起始规格": "Starting spec",
    "空白骨架": "Blank scaffold",
    "创建项目": "Create project",
    "制作项目": "Projects",
    "刷新": "Refresh",
    "还没有制作项目": "No production projects yet",
    "未选择项目": "No project selected",
    "从左侧选择模式并创建项目": "Choose a mode and create a project",
    "选择项目后，在这里查看生成、门禁和渲染日志。": "Choose a project to inspect generation, gate, and render logs.",
    "保存规格": "Save spec",
    "生成分镜": "Generate storyboard",
    "运行门禁": "Run gates",
    "渲染成片": "Render video",
    "规格 JSON": "Spec JSON",
    "生产状态": "Production status",
    "创建并开始流程": "Create and start workflow",
    "继续下一步 / 重试": "Continue / retry",
    "取消当前步骤": "Cancel current step",
    "结束流程以修改规格": "End workflow to edit spec",
    "确认旧进程已停止": "Confirm old process stopped",
    "流程依次执行生成分镜、检查、渲染；每步完成后等待确认。来源搜索和笔记生成仍需外部协助。": "The workflow generates a storyboard, checks it, and renders it, pausing for review after each step. Source discovery and note creation still require external assistance.",
    "待机": "Idle",
    "尚未生成": "Not generated",
    "成片预览": "Video preview",
    "下载 MP4": "Download MP4",
    "科普短片（精品手工路线）": "Sci-pop · handcrafted",
    "长教学": "Long-form course",
    "视频涅槃": "Video remaster",
    "信息守恒，不按时长卡": "Information-preserving remix",
    "生产依赖已就绪": "Production dependencies ready",
    "生产模块不可用": "Production module unavailable",
    "失败": "Failed",
    "规格已保存。下一步：生成分镜。": "Spec saved. Next: generate the storyboard.",
    "必须由 ≥2 个 B站来源整合（多源涅槃，不是凭空生成）；全片 15–60 分钟；按章分 part，每章 90–210 秒": "Integrate at least two Bilibili sources; do not fabricate a course. Keep the full lesson between 15 and 60 minutes, split by chapter, and target 90–210 seconds per chapter.",
    "有效信息总量不变：覆盖清单漏一条不许交付；删的是废话不是知识点；每页出处严格为 S# p## mm:ss（Reject「风格参考」这类无时间戳写法）": "Preserve all substantive information: missing a coverage item blocks delivery. Remove filler, not concepts. Every page needs a strict S# p## mm:ss citation, never a style-only reference.",
    "为什么 1+2+…+n = n(n+1)/2（真 LaTeX 演示）": "Why 1+2+…+n = n(n+1)/2 (real LaTeX demo)",
    "例如：TCP 为什么需要三次握手": "e.g. Why TCP needs a three-way handshake",
    "天空为什么是蓝的（推理拆解示范：光学 → 动画）": "Why the sky is blue (reasoning to animation)",
    "TCP 为什么需要三次握手（决策器 P11 验证）": "Why TCP needs a three-way handshake",
    "Transformer 的一层里发生了什么（AvgusTa 风格）": "What happens inside one Transformer layer",
    "已成片": "ready",
    "已生成": "ready",
    "未生成": "missing",
    "第 01 讲": "LESSON 01",
    "证据覆盖 · 转录 + 关键帧": "Evidence · transcript + keyframes",
    "跟随播放：开": "Follow playback: on",
    "跟随播放：关": "Follow playback: off",
    "回到当前时间": "Jump to current time",
    "问 AI": "Ask AI",
    "一眼记住": "Key idea",
    "记忆钩子": "Memory hook",
    "最容易错的地方": "Common trap",
    "学完这一讲，你应该能做到": "After this lesson, you should be able to",
    "先装术语，再看推导": "Define the terms first",
    "术语首次出现时先定义": "Each term is defined before it is used",
    "术语": "Term",
    "人话解释": "Plain meaning",
    "最小例子": "Minimal example",
    "首次出现": "First seen",
    "自评": "Self-check",
    "未评": "Unrated",
    "会": "Know it",
    "模糊": "Unsure",
    "不会": "Need work",
    "跟着视频走": "Follow the video",
    "点时间直接跳转": "Click a timestamp to jump",
    "核心机制": "Core mechanism",
    "黄色高亮是视频强调的得分点": "Highlighted ideas are the key takeaways",
    "看画面，别只看文字": "Read the visual, not only the text",
    "点击图跳到对应讲解": "Click a frame to jump to its explanation",
    "容易失分的地方": "Where learners lose points",
    "主动回忆": "Active recall",
    "先自己回答，再展开": "Answer first, then reveal",
    "知识不是清单，是一张网": "Knowledge is a graph, not a checklist",
    "点节点看它怎样连接": "Select a concept to inspect its links",
    "打开关联视频": "Open linked lesson",
    "当前讲属于这张知识网的这个区域。": "This lesson belongs to this region of the knowledge graph.",
    "先看节点之间的箭头：它们表示前一模块为后一模块提供了什么能力。": "Follow the arrows: each concept provides a capability to the next.",
    "AI 导师": "AI tutor",
    "视频 00:00": "Video 00:00",
    "选中左侧笔记中的任意内容，或直接在下方提问。": "Select any note on the left, or ask a question below.",
    "追问：这里为什么成立？": "Ask: why does this hold?",
    "发送": "Send",
    "解释": "Explain",
    "查错": "Check",
    "白话": "Simplify",
    "例子": "Example",
    "标重点": "Highlight",
    "追问": "Ask",
    "解释这段": "Explain this",
    "检查错误": "Check for errors",
    "换一种说法": "Rewrite",
    "补充例子": "Add an example",
    "标记重点": "Mark as important",
    "我不理解": "I do not understand",
    "设置为浅色旁注": "Add as pale note",
    "设为浅色旁注": "Add as pale note",
    "继续追问": "Ask a follow-up",
    "建议修改 · 尚未应用": "Suggested edit · not applied",
    "原文": "Current",
    "建议": "Suggested",
    "原因": "Reason",
    "接受修改": "Accept edit",
    "仅留旁注": "Keep as note",
    "旁注": "Note",
    "删除旁注": "Delete note",
    "拒绝": "Reject",
    "撤销": "Undo",
    "修订历史": "Revision history",
    "已应用": "Applied",
    "已撤销": "Undone",
    "已拒绝": "Rejected",
    "仅旁注": "Note only",
    "旁注已删除": "Side note deleted",
    "删除失败": "Delete failed",
    "已放入段落旁的浅色旁注": "Added a pale note beside the paragraph",
    "旁注保存失败": "Could not save the side note",
    "修改已应用，可在 AI 抽屉的修订历史撤销": "Edit applied. Undo it from revision history.",
    "已保留为旁注，正文未改": "Kept as a note. The main text is unchanged.",
    "已拒绝修改，正文未改": "Edit rejected. The main text is unchanged.",
    "修订操作失败": "Revision failed",
    "修改已撤销": "Edit undone",
    "没有得到可靠回答。": "No reliable answer was returned.",
    "含待确认": "Needs review",
    "缓存": "Cached",
    "跳到这张关键画面": "Jump to this key frame",
    "看视频": "Open video",
    "AI 导师暂不可用": "AI tutor is unavailable",
    "AI 请求超时，请重试": "AI request timed out. Try again.",
    "模型提供方不可用时，笔记阅读、时间同步和本地旁注仍可正常使用。": "You can still read notes, follow timestamps and keep local annotations while the model is unavailable.",
    "正在结合当前画面、转录和笔记上下文…": "Reading the current frame, transcript and note context…",
    "你的问题：": "Your question: ",
    "选中：": "Selected: ",
    "已选中：": "Selected: ",
    "载入失败": "Load failed",
    "正在装入 87 讲知识数据…": "Loading knowledge data…",
    "视频加载失败": "Video failed to load",
    "播放完毕": "Playback complete",
    "可以继续看下一段": "Continue with the next section",
    "重新播放": "Replay",
    "上一段": "Previous",
    "下一段": "Next",
    "播放/暂停": "Play / pause",
    "静音": "Mute",
    "字幕": "Captions",
    "设置": "Settings",
    "画中画": "Picture in picture",
    "全屏": "Fullscreen",
    "播放速度": "Playback speed",
    "正常": "Normal",
    "母片": "Source video",
    "关闭": "Off",
    "打开": "On",
    "键盘快捷键": "Keyboard shortcuts",
    "从头播放": "Restart",
    "播放": "Play",
    "暂停": "Pause",
    "音量": "Volume",
    "上一段 (Shift+P)": "Previous (Shift+P)",
    "下一段 (Shift+N)": "Next (Shift+N)",
    "字幕 (C)": "Captions (C)",
    "设置": "Settings",
    "画中画 (I)": "Picture in picture (I)",
    "剧场模式 (T)": "Theater (T)",
    "全屏 (F)": "Fullscreen (F)",
    "静音 (M)": "Mute (M)",
    "Play或Pause": "Play or pause",
    "后退或前进 5 秒": "Seek back or forward 5 sec",
    "后退或前进 10 秒": "Seek back or forward 10 sec",
    "Production mode": "Production mode",
    "每页视觉都要专门设计：禁止用生成器模板页堆片": "Every page is visually designed; no template-page stacking",
    "每 8–12 秒换一次视觉（比量产片更密）": "Change the visual every 8–12 seconds",
    "开头 30 秒内用 2–3 个日常例子勾住观众": "Hook the viewer with 2–3 concrete examples in the first 30 seconds",
    "全片 2–6 分钟：短而密，不靠长度撑完播": "Keep the full lesson between 2 and 6 minutes",
    "术语落地说人话": "Define jargon in plain language",
    "片尾 2–4 条复盘，口播说「我们回顾一下」": "Close with a 2–4 point recap and a spoken recap cue"
  };

  const patterns = [
    [/^(\d+) 讲$/, (_, n) => `${n} ${Number(n) === 1 ? "lesson" : "lessons"}`],
    [/^(\d+(?:\.\d+)?) 分 · (\d+) 个知识块$/, "$1 min · $2 knowledge blocks"],
    [/^(\d+(?:\.\d+)?)–(\d+(?:\.\d+)?) 分钟$/, "$1–$2 minutes"],
    [/^AI：离线演示$/, "AI: offline demo"],
    [/^AI：(.*)$/, "AI: $1"],
    [/^当前使用离线演示提供方。$/, "Using the offline demo provider."],
    [/^当前使用 (.*?)；密钥只在服务端读取。$/, "Using $1; credentials stay on the server."],
    [/^第 (\d+) 讲$/, "LESSON $1"],
    [/^置信度 (高|中|低)$/, (_, v) => "Confidence " + ({高:"high",中:"medium",低:"low"}[v] || v)],
    [/^视频 ([\d:]+)$/, "Video $1"],
    [/^(\d+) 秒$/, "$1 sec"],
    [/^加载 (.+) 讲知识数据…$/, "Loading knowledge data for $1 lessons…"],
    [/^(\d+) 页$/, "$1 pages"],
    [/^缺少：(.*)$/, "Missing: $1"],
    [/^提示：(.*)$/, "Note: $1"],
    [/^阶段：(.*?) · 分镜：(已生成|未生成) · 成片：(已生成|未生成)$/,
      (_, stage, storyboard, video) => `Stage: ${stage} · Storyboard: ${storyboard === "已生成" ? "ready" : "missing"} · Video: ${video === "已生成" ? "ready" : "missing"}`],
    [/^(remix|course|scipop) · rendered · 已成片$/, (_, mode) => `${mode} · rendered · ready`],
    [/^(.+) 中$/, (_, action) => `${action}…`]
  ];

  function translateText(value) {
    if (!value || !/[\u4e00-\u9fff]/.test(value)) return value;
    const trimmed = value.trim();
    if (Object.prototype.hasOwnProperty.call(exact, trimmed)) {
      return value.replace(trimmed, exact[trimmed]);
    }
    for (const [re, replacement] of patterns) {
      const match = trimmed.match(re);
      if (match) {
        const result = typeof replacement === "function"
          ? replacement(...match)
          : trimmed.replace(re, replacement);
        return value.replace(trimmed, result);
      }
    }
    let replaced = value;
    Object.entries(exact)
      .sort((a, b) => b[0].length - a[0].length)
      .forEach(([source, target]) => {
        if (replaced.includes(source)) replaced = replaced.split(source).join(target);
      });
    if (replaced !== value) return replaced;
    return value;
  }

  function walk(root) {
    if (!root) return;
    if (root.nodeType === Node.TEXT_NODE) {
      const next = translateText(root.nodeValue);
      if (next !== root.nodeValue) root.nodeValue = next;
      return;
    }
    if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_NODE) return;
    if (root.nodeType === Node.ELEMENT_NODE) {
      ["placeholder", "title", "aria-label"].forEach((attr) => {
        if (root.hasAttribute(attr)) root.setAttribute(attr, translateText(root.getAttribute(attr)));
      });
    }
    Array.from(root.childNodes || []).forEach(walk);
  }

  function fixLinks() {
    document.querySelectorAll('a[href="/"], a[href="/production.html"]').forEach((link) => {
      const base = link.getAttribute("href");
      link.setAttribute("href", base + (base.includes("?") ? "&" : "?") + "lang=en");
    });
  }

  const start = () => {
    walk(document.body);
    fixLinks();
    // Some pages render their initial content from a later script. Sweep once
    // after that render as a second line of defense for headings and shortcuts.
    window.setTimeout(() => {
      walk(document.body);
      fixLinks();
    }, 500);
    new MutationObserver((records) => {
      records.forEach((record) => {
        record.addedNodes.forEach(walk);
        if (record.type === "characterData") walk(record.target);
      });
      fixLinks();
    }).observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ["placeholder", "title", "aria-label"],
    });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start, { once: true });
  } else {
    start();
  }
})();
