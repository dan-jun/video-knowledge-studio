# Launch kit

## One-line positioning

**中文：** 不是一个视频总结工具，而是把一个真实学习目标变成可追问、可复习、
可重制的本地课程。

**English:** Turn a learning goal into a sourced animated course, synchronized
notes, and a contextual AI tutor that can see what you are watching.

## GitHub About

Description:

```text
Local-first AI learning workspace that turns a knowledge gap into sourced animated courses, synchronized notes, and a contextual AI tutor.
```

Topics:

```text
ai
education
local-first
notebooklm-alternative
video-learning
knowledge-management
ai-tutor
bilibili
youtube
manim
self-hosted
```

## Primary audience

- engineers learning a new subsystem for a project;
- researchers entering an unfamiliar paper or method;
- students turning scattered Bilibili/YouTube lessons into one study path;
- creators converting existing lectures into clearer courses;
- users who care about local data ownership.

## Launch sequence

1. Publish a public GHCR image and release asset.
2. Pin the 54-second animated and screen-recorded demo at the top of the README.
3. Publish one Chinese walkthrough video.
4. Publish one technical article explaining the evidence-linked architecture.
5. Post focused variants in Chinese and English communities.
6. Turn repeated questions into FAQ and starter issues.

## Ready-to-use copy

### Bilibili

Title:

```text
我把 B 站和 YouTube 变成了自己的 AI 课程生成器
```

Opening:

```text
这不是又一个视频总结工具。它从一个真实学习目标出发：
先规划知识点，再找多个互补来源，最后做成能边看边问的动画课程和笔记。
```

### 知乎 / 少数派

Title:

```text
不收藏了：把零散视频直接做成能追问的课程
```

Lead:

```text
我真正需要的不是更多收藏，而是在做项目时快速补上一块知识，
并且以后还能找到证据、继续追问。
```

### V2EX / 即刻

```text
分享一个本地优先的 AI 学习工作台：视频、时间戳、知识笔记和 AI 上下文
共用同一份数据。还带 remix/course/scipop 三种视频制作模式和 Docker 一键启动。
```

### Show HN

```text
Show HN: Local-first AI workspace that turns learning goals into video courses

I built a local workspace that unifies video, evidence, structured notes, and an
AI tutor. A learning goal can be planned into multiple Bilibili/YouTube sources,
then rendered into an animated lesson. Questions include the current timestamp,
nearby transcript, and relevant frame; note edits require confirmation and can be
undone. The Docker image bundles FFmpeg, Manim, TTS, and fonts.
```

### Reddit

```text
[P] Video Knowledge Studio – a local-first NotebookLM alternative for learning
from video

It connects source discovery, animated course production, synchronized notes,
and an evidence-aware tutor. The important difference is traceability: a note
block, video timestamp, transcript window, and visual frame stay connected.
```

Use the same text only where self-promotion is allowed by the community rules.

## Demo assets

- `docs/images/social-preview.png` — GitHub/social card;
- `docs/images/product-demo-poster.png` — video cover;
- `docs/media/product-demo.mp4` — 54-second animated and screen-recorded walkthrough;
- `docs/images/demo.png` — learning workspace;
- `docs/images/ai-tutor-demo.png` — evidence and revision workflow;
- `docs/images/production-workspace.png` — creation workspace;
- `docs/images/production-demo.gif` — real rendered output.

## Boundaries to state publicly

- Automatic search is Agent-assisted; the app itself does not ship a universal
  search service.
- This is a local single-user workspace, not a multi-tenant SaaS.
- AI output requires review.
- Third-party media and transcripts require permission.

## Metrics that matter

- successful first run after clone;
- Docker pull/start success rate;
- external issues and course-pack examples;
- demo completion rate and repository referral sources;
- repeat usage, not only GitHub stars.
