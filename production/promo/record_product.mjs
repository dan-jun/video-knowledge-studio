import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const playwrightPath =
  "C:/Users/联想/Documents/deepseek-harness/default-workspace/ai-infra-prep/skills/whiteboard-teacher-video/node_modules/playwright-core";
const require = createRequire(import.meta.url);
const { chromium } = require(playwrightPath);

const here = path.dirname(fileURLToPath(import.meta.url));
const outputDir = path.join(here, "recordings");
fs.mkdirSync(outputDir, { recursive: true });

const baseUrl = process.env.VKS_PROMO_URL || "http://127.0.0.1:17870";
const executablePath =
  process.env.VKS_PROMO_BROWSER ||
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const cursorCss = `
  html { scrollbar-width: none; }
  body::-webkit-scrollbar, *::-webkit-scrollbar { width: 0 !important; height: 0 !important; }
  .vks-promo-cursor {
    position: fixed; z-index: 2147483647; width: 28px; height: 28px;
    border-radius: 50%; pointer-events: none; transform: translate(-50%, -50%);
    background: rgba(10, 20, 28, .78); border: 1.5px solid rgba(98, 241, 255, .95);
    box-shadow: 0 0 0 7px rgba(56, 208, 235, .08), 0 0 22px rgba(56, 208, 235, .45);
    transition: width .12s ease, height .12s ease, background .12s ease;
  }
  .vks-promo-cursor::after {
    content: ""; position: absolute; left: 50%; top: 50%; width: 7px; height: 7px;
    transform: translate(-50%, -50%); border-radius: 50%; background: #72f2ff;
  }
  .vks-promo-cursor.click {
    width: 20px; height: 20px; background: rgba(114, 242, 255, .42);
  }
`;

async function addCursor(page) {
  await page.addStyleTag({ content: cursorCss });
  await page.evaluate(() => {
    const node = document.createElement("div");
    node.className = "vks-promo-cursor";
    node.style.left = "960px";
    node.style.top = "540px";
    document.body.appendChild(node);
    const move = (event) => {
      node.style.left = `${event.clientX}px`;
      node.style.top = `${event.clientY}px`;
    };
    document.addEventListener("mousemove", move, true);
    document.addEventListener("mousedown", () => node.classList.add("click"), true);
    document.addEventListener("mouseup", () => node.classList.remove("click"), true);
  });
}

async function moveTo(page, locator, pause = 300) {
  await locator.scrollIntoViewIfNeeded().catch(() => {});
  const box = await locator.boundingBox();
  if (!box) return;
  await page.mouse.move(
    box.x + box.width / 2,
    box.y + box.height / 2,
    { steps: 26 },
  );
  await wait(pause);
}

async function openRecordedPage(browser, name) {
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
    recordVideo: {
      dir: outputDir,
      size: { width: 1920, height: 1080 },
    },
  });
  const page = await context.newPage();
  const started = Date.now();
  await page.goto(`${baseUrl}/`, { waitUntil: "networkidle" });
  await addCursor(page);
  return { context, page, started, name };
}

async function closeRecording(session) {
  const video = session.page.video();
  await session.context.close();
  const source = video ? await video.path() : "";
  const target = path.join(outputDir, `${session.name}.webm`);
  if (source && fs.existsSync(source)) {
    fs.copyFileSync(source, target);
  }
  return {
    name: session.name,
    file: target,
    wall_seconds: (Date.now() - session.started) / 1000,
  };
}

async function recordLearning(browser) {
  const session = await openRecordedPage(browser, "learning");
  const { page } = session;
  await wait(1200);

  const second = page.locator('.project[data-id="raft-e01"]');
  await moveTo(page, second, 500);
  await second.click();
  await wait(1200);

  const play = page.locator(".vp-bigplay");
  await moveTo(page, play, 350);
  await play.click();
  await wait(1800);

  const timelineRow = page.locator(".k-timeline-item").nth(1);
  await moveTo(page, timelineRow, 450);
  await timelineRow.click();
  await wait(1800);

  const core = page.locator(".k-core-body").nth(1);
  await core.scrollIntoViewIfNeeded();
  await wait(700);
  const coreBox = await core.boundingBox();
  if (coreBox) {
    await page.mouse.move(coreBox.x + coreBox.width * 0.25, coreBox.y + 16, { steps: 18 });
  }
  await core.evaluate((node) => {
    const range = document.createRange();
    range.selectNodeContents(node);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    node.dispatchEvent(new MouseEvent("mouseup", { bubbles: true, clientX: 0, clientY: 0 }));
  });
  await wait(900);

  const explain = page.locator("#kselecttools button", { hasText: "解释" }).first();
  await moveTo(page, explain, 350);
  await explain.click();
  await wait(2200);

  await page.waitForFunction(
    () =>
      !document.querySelector("#kaiscroll .k-spinner") &&
      document.querySelector("#kaiscroll .k-ai-answer"),
    null,
    { timeout: 60000 },
  );
  await wait(1700);

  const annotate = page.locator("#kaidock button", {
    hasText: /设为浅色旁注|仅留旁注/,
  }).first();
  if (await annotate.count()) {
    await moveTo(page, annotate, 350);
    await annotate.click();
    await wait(1800);
  }

  await page.screenshot({ path: path.join(outputDir, "learning-final.png") });
  return closeRecording(session);
}

async function recordProduction(browser) {
  const session = await openRecordedPage(browser, "production");
  const { page } = session;
  await page.goto(`${baseUrl}/production.html`, { waitUntil: "networkidle" });
  await wait(1200);

  for (const mode of await page.locator(".mode").all()) {
    await moveTo(page, mode, 170);
  }

  await page.locator("#createMode").selectOption("scipop");
  await page.locator("#createTitle").fill("把复杂知识讲成一张网");
  const create = page.locator("#createBtn");
  await moveTo(page, create, 350);
  await create.click();
  await wait(1000);

  const editor = page.locator("#specEditor");
  await editor.evaluate((node) => {
    node.focus();
    const at = node.value.indexOf('"narration"');
    node.setSelectionRange(Math.max(0, at), Math.min(node.value.length, at + 36));
  });
  const editorBox = await editor.boundingBox();
  if (editorBox) {
    await page.mouse.move(
      editorBox.x + editorBox.width * 0.42,
      editorBox.y + editorBox.height * 0.36,
      { steps: 24 },
    );
  }
  await wait(1200);

  const generate = page.locator('[data-action="generate"]');
  await moveTo(page, generate, 350);
  await generate.click();
  await page.waitForFunction(
    () => {
      const text = document.querySelector("#jobState")?.textContent || "";
      return text && !text.includes("中");
    },
    { timeout: 60000 },
  );
  await wait(1400);

  const existing = page.locator(".project", {
    hasText: "4 小时读懂 Raft 日志复制",
  }).first();
  await moveTo(page, existing, 450);
  await existing.click();
  await wait(1200);

  const gates = page.locator('[data-action="gates"]');
  await moveTo(page, gates, 350);
  await gates.click();
  await page.waitForFunction(
    () => {
      const text = document.querySelector("#jobState")?.textContent || "";
      return text && !text.includes("中");
    },
    { timeout: 60000 },
  );
  await wait(1800);

  const videoCard = page.locator("#videoCard");
  await videoCard.scrollIntoViewIfNeeded();
  await wait(700);
  await page.evaluate(() => {
    const video = document.querySelector("#video");
    if (video) {
      video.currentTime = 14;
      video.play().catch(() => {});
    }
  });
  await wait(2600);

  await page.screenshot({ path: path.join(outputDir, "production-final.png") });
  return closeRecording(session);
}

const browser = await chromium.launch({
  headless: true,
  executablePath,
  args: [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--force-device-scale-factor=1",
    "--hide-scrollbars",
  ],
});

try {
  const results = [];
  results.push(await recordLearning(browser));
  results.push(await recordProduction(browser));
  fs.writeFileSync(
    path.join(outputDir, "recordings.json"),
    JSON.stringify(results, null, 2),
    "utf8",
  );
  console.log(JSON.stringify(results, null, 2));
} finally {
  await browser.close();
}
