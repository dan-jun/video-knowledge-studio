import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require(
  "C:/Users/联想/Documents/deepseek-harness/default-workspace/ai-infra-prep/skills/whiteboard-teacher-video/node_modules/playwright-core",
);

const here = path.dirname(fileURLToPath(import.meta.url));
const output = path.join(here, "recordings", "learning-final.png");
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const browser = await chromium.launch({
  headless: true,
  executablePath: "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars"],
});
const page = await browser.newPage({
  viewport: { width: 1920, height: 1080 },
  deviceScaleFactor: 1,
});

try {
  await page.goto("http://127.0.0.1:17870/", { waitUntil: "networkidle" });
  await page.locator('.project[data-id="raft-e01"]').click();
  await wait(1200);

  const core = page.locator(".k-core-body").nth(1);
  await core.scrollIntoViewIfNeeded();
  await core.evaluate((node) => {
    const range = document.createRange();
    range.selectNodeContents(node);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    node.dispatchEvent(new MouseEvent("mouseup", { bubbles: true }));
  });
  await wait(500);
  await page.locator("#kselecttools button", { hasText: "解释" }).first().click();

  await page.waitForFunction(
    () =>
      !document.querySelector("#kaiscroll .k-spinner") &&
      document.querySelector("#kaiscroll .k-ai-answer"),
    null,
    { timeout: 60000 },
  );
  await wait(900);
  await page.evaluate(() => {
    const selection = window.getSelection();
    if (selection) selection.removeAllRanges();
    document.querySelector("#kselecttools")?.classList.remove("show");
    document.querySelectorAll(".k-toast, .vks-promo-cursor").forEach((node) => node.remove());
  });
  await page.mouse.move(1900, 1060);
  await wait(350);
  await page.screenshot({ path: output });
  console.log(output);
} finally {
  await browser.close();
}
