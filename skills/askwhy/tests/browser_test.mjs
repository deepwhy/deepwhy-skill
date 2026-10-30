#!/usr/bin/env node
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const testDir = path.dirname(new URL(import.meta.url).pathname);
const skillRoot = path.resolve(testDir, "..");
const defaultPage = path.join(skillRoot, "examples", "bulb-glow.html");
const contentPath = path.join(skillRoot, "examples", "bulb-glow.json");
const builderPath = path.join(skillRoot, "scripts", "build_page.py");
const pagePath = path.resolve(process.argv[2] || defaultPage);

let playwright;
try {
  playwright = await import("playwright");
} catch (error) {
  try {
    playwright = await import("@playwright/test");
  } catch (fallbackError) {
    try {
      const require = createRequire(import.meta.url);
      const resolvedName = ["playwright", "@playwright/test"]
        .find(name => {
          try {
            require.resolve(name);
            return true;
          } catch (resolveError) {
            return false;
          }
        });
      if (!resolvedName) throw fallbackError;
      playwright = await import(pathToFileURL(require.resolve(resolvedName)).href);
    } catch (resolvedFallbackError) {
      console.error("SKIP: Playwright is not installed; browser behavior was not tested.");
      process.exit(77);
    }
  }
}

const launchOptions = { headless: true };
if (process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE) {
  launchOptions.executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE;
}

const browserApi = playwright.chromium ? playwright : playwright.default;
const browser = await browserApi.chromium.launch(launchOptions);
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
  permissions: ["clipboard-read", "clipboard-write"]
});
await context.route("https://player.bilibili.com/**", route =>
  route.fulfill({
    status: 200,
    contentType: "text/html",
    body: "<!doctype html><html><body style='margin:0;background:#171322;color:#fff;font-family:sans-serif;display:grid;place-items:center;height:100vh'>Bilibili embedded player</body></html>"
  })
);
await context.route("https://www.youtube-nocookie.com/**", route =>
  route.fulfill({
    status: 200,
    contentType: "text/html",
    body: "<!doctype html><html><body style='margin:0;background:#171322;color:#fff;font-family:sans-serif;display:grid;place-items:center;height:100vh'>YouTube embedded player</body></html>"
  })
);
const page = await context.newPage();
const consoleErrors = [];
const externalRequests = [];
page.on("pageerror", error => consoleErrors.push(`pageerror: ${error.message}`));
page.on("console", message => {
  if (message.type() === "error") consoleErrors.push(`console: ${message.text()}`);
});
page.on("request", request => {
  const url = request.url();
  if (!url.startsWith("file:") && !url.startsWith("data:") && !url.startsWith("blob:")) {
    const hostname = new URL(url).hostname;
    if (hostname !== "127.0.0.1" && hostname !== "localhost") {
      externalRequests.push(url);
    }
  }
});

async function waitForLayout(targetPage, expected, nodeCount = null) {
  await targetPage.waitForFunction(
    ({ layout, count }) => {
      const map = document.getElementById("question-map");
      if (map?.dataset.layout !== layout) return false;
      return count === null || document.querySelectorAll(".why-step").length === count;
    },
    { layout: expected, count: nodeCount }
  );
}

async function assertNoOverlap(targetPage, selector, label) {
  const cards = await targetPage.locator(selector).evaluateAll(elements =>
    elements.map((element, index) => {
      const rect = element.getBoundingClientRect();
      return {
        index,
        text: element.textContent.trim().replace(/\s+/g, " "),
        left: rect.left,
        top: rect.top,
        right: rect.right,
        bottom: rect.bottom
      };
    })
  );
  for (let first = 0; first < cards.length; first += 1) {
    for (let second = first + 1; second < cards.length; second += 1) {
      const a = cards[first];
      const b = cards[second];
      const overlapWidth = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const overlapHeight = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      assert.ok(
        overlapWidth <= 1 || overlapHeight <= 1,
        `${label}: overlapping question cards\n${a.text}\n${b.text}`
      );
    }
  }
}

async function assertNoHorizontalOverflow(targetPage, label) {
  const overflow = await targetPage.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth
  );
  assert.ok(overflow <= 1, `${label}: horizontal overflow is ${overflow}px`);
}

async function buildVariant(count, tempDir) {
  const content = JSON.parse(fs.readFileSync(contentPath, "utf8"));
  const baseNodes = content.nodes;
  content.nodes = baseNodes.slice(0, count);
  for (let index = baseNodes.length; index < count; index += 1) {
    const previous = content.nodes.at(-1);
    const clone = structuredClone(baseNodes.at(-1));
    clone.id = `variant-${index + 1}`;
    clone.parentId = previous.id;
    clone.type = "boundary";
    clone.question = `为什么第 ${index + 1} 层还需要继续解释？`;
    clone.label = `第 ${index + 1} 层完整说明`;
    clone.answer = "这是为验证 8 层因果链布局而增加的末端节点。";
    clone.summary = "用于验证长链路布局的边界节点。";
    clone.nextQuestion = null;
    previous.nextQuestion = clone.question;
    content.nodes.push(clone);
  }
  content.nodes.at(-1).nextQuestion = null;
  const visuals = [
    content.center.overviewVisual,
    content.center.analogy.visual,
    ...content.nodes.flatMap(node => [
      node.visual,
      node.analogy?.visual
    ])
  ];
  for (const visual of visuals) {
    if (!visual) continue;
    if (visual.kind === "image") {
      visual.src = path.resolve(path.dirname(contentPath), visual.src);
    } else {
      visual.sceneSource = path.resolve(path.dirname(contentPath), visual.sceneSource);
      visual.videoSrc = path.resolve(path.dirname(contentPath), visual.videoSrc);
      visual.posterSrc = path.resolve(path.dirname(contentPath), visual.posterSrc);
    }
  }
  content.meta.question = `${count} 节点布局测试`;
  content.meta.topic = `${count} 节点布局测试`;
  content.meta.slug = `askwhy-${count}-nodes`;
  const jsonPath = path.join(tempDir, `${count}.json`);
  const htmlPath = path.join(tempDir, `${count}.html`);
  fs.writeFileSync(jsonPath, JSON.stringify(content, null, 2));
  execFileSync(
    "python3",
    [builderPath, jsonPath, "--output", htmlPath],
    { cwd: skillRoot, stdio: "pipe" }
  );
  return htmlPath;
}

async function startPageServer(pageHtml) {
  const server = http.createServer((request, response) => {
    if (request.url !== "/page.html" && request.url !== "/page.html#question-einstein") {
      response.writeHead(404).end("Not found");
      return;
    }
    response.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    response.end(pageHtml);
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  return {
    server,
    url: `http://127.0.0.1:${address.port}/page.html`
  };
}

const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "askwhy-browser-"));
try {
  await page.goto(pathToFileURL(pagePath).href, { waitUntil: "load" });
  await waitForLayout(page, "chain", 7);

  assert.equal(await page.locator("h1").count(), 1);
  assert.equal(await page.locator("#hero-question").innerText(), "电灯为什么会发光？");
  assert.equal(await page.locator("#chain-root-question").innerText(), "电灯为什么会发光？");
  assert.equal(
    await page.locator("#hero-category").innerText(),
    "物理 · 电学 · 初中版"
  );
  assert.doesNotMatch(
    await page.locator(".hero").innerText(),
    /知识总览|QUESTION EXPLORER/
  );
  assert.equal(await page.locator("#hero-overview").isVisible(), true);
  assert.equal(await page.locator(".hero-art").count(), 0);
  assert.equal(
    await page
      .locator("#hero-overview")
      .evaluate(element => getComputedStyle(element).position),
    "relative"
  );
  const heroLayersOverlap = await page.evaluate(() => {
    const copy = document.querySelector(".hero-copy").getBoundingClientRect();
    const overview = document.querySelector("#hero-overview").getBoundingClientRect();
    return Math.min(copy.right, overview.right) - Math.max(copy.left, overview.left);
  });
  assert.ok(
    heroLayersOverlap <= 1,
    `overview must not be covered by the hero copy; overlap is ${heroLayersOverlap}px`
  );
  assert.equal(
    await page
      .locator("#hero-overview-image")
      .evaluate(element => getComputedStyle(element).objectFit),
    "contain"
  );
  assert.equal(
    await page
      .locator("#hero-overview-image")
      .evaluate(element => getComputedStyle(element).maskImage),
    "none"
  );
  assert.match(
    await page.locator("#hero-overview-image").getAttribute("src"),
    /^data:image\/svg\+xml;base64,/
  );
  assert.ok(
    await page.locator("#hero-overview-image").evaluate(image => image.naturalWidth > 0)
  );
  assert.match(
    await page.locator("#hero-overview-caption").textContent(),
    /化学能.*电压.*电子漂移.*发热.*可见光/
  );
  assert.equal(await page.locator(".why-step").count(), 7);
  assert.equal(await page.locator(".why-step-visual").count(), 7);
  assert.equal(await page.locator(".learning-level-button").count(), 0);
  assert.match(await page.locator("#meta-pills").innerText(), /预计探索 10 分钟/);
  assert.match(await page.locator("#meta-pills").innerText(), /7 层追问/);
  const visualKinds = await page
    .locator(".why-step-visual .visual-kind-badge")
    .allInnerTexts();
  assert.equal(visualKinds.filter(value => value === "FIG").length, 3);
  assert.equal(visualKinds.filter(value => value === "ANIM").length, 4);
  assert.equal(await page.locator("#follow-up-list").count(), 0);
  assert.doesNotMatch(await page.locator("main").innerText(), /还可以继续追问/);
  assert.equal(await page.locator("#detail-sources").count(), 0);
  assert.doesNotMatch(await page.locator("#detail-panel").innerText(), /OpenStax|SRC|来源/);
  assert.equal(await page.locator("#videos-section").isHidden(), true);
  const embeddedVideoData = await page
    .locator("#askwhy-data")
    .evaluate(element => JSON.parse(element.textContent));
  assert.equal(
    embeddedVideoData.nodes.flatMap(node => node.videoLinks || []).length,
    8,
    "every node should retain at least one reviewed video"
  );
  assert.ok(
    embeddedVideoData.nodes.every(node => (node.videoLinks || []).length >= 1)
  );
  assert.ok(
    embeddedVideoData.nodes.every(
      node => node.knowledge && Array.isArray(node.facts) && node.facts.length >= 2
    )
  );
  assert.ok(
    embeddedVideoData.center.analogy &&
    embeddedVideoData.center.analogy.mappings.length >= 2
  );
  assert.ok(
    embeddedVideoData.nodes.every(
      node => node.analogy && node.analogy.mappings.length >= 2
    )
  );
  assert.match(await page.locator("#detail-kicker").innerText(), /中心问题/);
  assert.equal(await page.locator("#analogy-section").isVisible(), true);
  assert.equal(
    await page.locator("#analogy-title").innerText(),
    "把整条电路想成一条环形水路"
  );
  assert.equal(await page.locator(".analogy-mapping").count(), 4);
  assert.match(await page.locator("#analogy-limit").innerText(), /单个电子/);
  assert.equal(await page.locator("#analogy-visual video").count(), 1);
  assert.match(
    await page.locator("#analogy-visual video source").getAttribute("src"),
    /^data:video\/webm;base64,/
  );
  assert.equal(
    await page.locator("#analogy-visual .manim-poster-overlay").count(),
    1
  );
  assert.match(
    await page.locator("#analogy-visual .visual-kind-label").innerText(),
    /类比动画/
  );
  await assertNoOverlap(page, ".why-step", "desktop causal chain");
  await assertNoHorizontalOverflow(page, "desktop");

  if (process.env.ASKWHY_SCREENSHOT_DIR) {
    fs.mkdirSync(process.env.ASKWHY_SCREENSHOT_DIR, { recursive: true });
    await page.screenshot({
      path: path.join(process.env.ASKWHY_SCREENSHOT_DIR, "askwhy-desktop-1440.png"),
      fullPage: true
    });
  }

  const incandescence = page.locator('.why-step[data-node-id="incandescence"]');
  await incandescence.click();
  await page.waitForFunction(() => location.hash === "#question-incandescence");
  assert.equal(
    await incandescence.getAttribute("aria-pressed"),
    "true"
  );
  assert.equal(
    await page.locator("#detail-title").innerText(),
    "灯泡接通电源后，为什么灯丝会热到发光？"
  );
  assert.match(await page.locator("#detail-kicker").innerText(), /第 01 层/);
  assert.equal(await page.locator("#visual-section").isVisible(), true);
  assert.equal(await page.locator("#detail-visual img").count(), 1);
  assert.ok(
    await page.locator("#detail-visual img").evaluate(image => image.naturalWidth > 0)
  );
  assert.match(await page.locator("#detail-visual .visual-caption").innerText(), /热辐射/);
  assert.equal(await page.locator("#answer-section").isVisible(), true);
  assert.match(await page.locator("#detail-answer").innerText(), /电流在灯丝中耗散能量/);
  assert.equal(await page.locator("#analogy-section").isVisible(), true);
  assert.equal(
    await page.locator("#analogy-title").innerText(),
    "水流挤过狭窄管段后发热"
  );
  assert.equal(await page.locator(".analogy-mapping").count(), 4);
  assert.match(await page.locator("#analogy-limit").innerText(), /热辐射发光/);
  assert.equal(await page.locator("#analogy-visual img").count(), 1);
  assert.ok(
    await page.locator("#analogy-visual img").evaluate(image => image.naturalWidth > 0)
  );
  assert.match(
    await page.locator("#analogy-visual .visual-kind-label").innerText(),
    /类比示意图/
  );
  const analogyComesBeforeNavigation = await page.evaluate(() => {
    const analogy = document.getElementById("analogy-section");
    const navigation = document.querySelector(".chain-nav");
    return Boolean(
      analogy.compareDocumentPosition(navigation) & Node.DOCUMENT_POSITION_FOLLOWING
    );
  });
  assert.equal(analogyComesBeforeNavigation, true);
  const navAndKnowledgeSpacing = await page.evaluate(() => {
    const nav = document.querySelector(".chain-nav").getBoundingClientRect();
    const knowledge = document.getElementById("knowledge-section").getBoundingClientRect();
    return knowledge.top - nav.bottom;
  });
  assert.ok(
    navAndKnowledgeSpacing >= 20,
    `core knowledge must sit at least 20px below navigation; got ${navAndKnowledgeSpacing}px`
  );
  assert.equal(await page.locator("#videos-section").isVisible(), true);
  assert.match(
    await page.locator("#videos-section .section-heading").innerText(),
    /视频讲解/
  );
  assert.doesNotMatch(
    await page.locator("#videos-section .section-heading").innerText(),
    /核验视频/
  );
  assert.equal(await page.locator("#detail-videos .video-player").count(), 1);
  assert.equal(await page.locator("#detail-videos iframe").count(), 1);
  assert.match(
    await page.locator("#detail-videos .video-player").innerText(),
    /123职业学院/
  );
  assert.equal(
    await page.locator("#detail-videos iframe").getAttribute("src"),
    "https://player.bilibili.com/player.html?bvid=BV1F94y1f7VJ&page=1&autoplay=0"
  );
  assert.equal(
    await page.locator("#detail-videos .video-open").getAttribute("href"),
    "https://www.bilibili.com/video/BV1F94y1f7VJ"
  );
  assert.match(
    await page.locator("#detail-videos .video-player-why").innerText(),
    /先发热、再发光/
  );
  assert.match(
    await page.locator("#next-question strong").innerText(),
    /为什么热的灯丝会发出可见光/
  );
  assert.equal(await page.locator("#previous-question").isVisible(), true);
  assert.match(
    await page.locator("#previous-question strong").innerText(),
    /电灯为什么会发光/
  );
  assert.equal(
    await page
      .locator('#detail-videos .video-player-bar .platform-logo[data-platform="bilibili"]')
      .count(),
    1
  );
  if (process.env.ASKWHY_SCREENSHOT_DIR) {
    await page.screenshot({
      path: path.join(process.env.ASKWHY_SCREENSHOT_DIR, "askwhy-video-detail-1440.png"),
      fullPage: true
    });
  }

  await page.locator("#next-question").click();
  await page.waitForFunction(() => location.hash === "#question-thermal-radiation");
  assert.equal(
    await page.locator("#detail-title").innerText(),
    "为什么热的灯丝会发出可见光？"
  );
  assert.equal(
    await page.locator('.why-step[data-node-id="thermal-radiation"]').getAttribute("aria-pressed"),
    "true"
  );
  const videoPlatforms = await page
    .locator("#detail-videos .video-choice")
    .evaluateAll(buttons => buttons.map(button => button.dataset.platform));
  assert.deepEqual(videoPlatforms, ["bilibili", "youtube"]);
  await page.locator('#detail-videos .video-choice[data-platform="youtube"]').click();
  assert.equal(await page.locator("#detail-videos iframe").isHidden(), true);
  assert.equal(await page.locator("#detail-videos .video-embed-fallback").isVisible(), true);
  assert.match(
    await page.locator("#detail-videos .video-embed-fallback").innerText(),
    /HTTP 页面来源/
  );
  assert.equal(
    await page
      .locator('#detail-videos .video-player-bar .platform-logo[data-platform="youtube"]')
      .count(),
    1
  );

  await page.locator("#copy-question").click();
  await page.waitForFunction(() =>
    document.getElementById("toast")?.classList.contains("is-visible")
  );
  assert.match(await page.locator("#toast").innerText(), /为什么热的灯丝/);

  await page.locator("#share-link").click();
  await page.waitForFunction(() =>
    document.getElementById("toast")?.textContent.includes("分享链接")
  );
  assert.match(await page.locator("#toast").innerText(), /分享链接/);

  await page.locator('.why-step[data-node-id="joule-heating"]').click();
  await page.waitForFunction(() => location.hash === "#question-joule-heating");
  assert.equal(await page.locator("#visual-section").isVisible(), true);
  assert.equal(await page.locator("#detail-visual video").count(), 1);
  assert.match(
    await page.locator("#detail-visual video source").getAttribute("src"),
    /^data:video\/webm;base64,/
  );
  assert.match(
    await page.locator("#detail-visual .manim-poster-overlay img").getAttribute("src"),
    /^data:image\/webp;base64,/
  );
  assert.ok(
    await page
      .locator("#detail-visual .manim-poster-overlay img")
      .evaluate(image => image.naturalWidth > 0)
  );
  assert.match(await page.locator("#detail-visual .visual-caption").innerText(), /晶格/);
  assert.equal(await page.locator("#detail-visual .manim-replay").innerText(), "重播");
  await page.waitForFunction(() => {
    const video = document.querySelector("#detail-visual video");
    return video && video.readyState >= 2;
  });
  if (process.env.ASKWHY_SCREENSHOT_DIR) {
    await page.screenshot({
      path: path.join(process.env.ASKWHY_SCREENSHOT_DIR, "askwhy-manim-detail-1440.png"),
      fullPage: true
    });
  }
  if (await page.locator("#detail-visual .manim-poster-overlay").isVisible()) {
    await page.locator("#detail-visual .manim-poster-overlay").click();
  }
  await page.waitForFunction(() => {
    const video = document.querySelector("#detail-visual video");
    const overlay = document.querySelector("#detail-visual .manim-poster-overlay");
    return video && overlay && video.currentTime > 0.15 && overlay.hidden;
  });
  await page.evaluate(() => {
    const video = document.querySelector("#detail-visual video");
    if (video) video.pause();
  });

  await page.goto(
    `${pathToFileURL(pagePath).href}#question-voltage`,
    { waitUntil: "load" }
  );
  await waitForLayout(page, "chain", 7);
  assert.equal(
    await page.locator("#detail-title").innerText(),
    "为什么电压能够在导线中建立电场并推动电子？"
  );
  assert.equal(
    await page.locator('.why-step[data-node-id="voltage"]').getAttribute("aria-pressed"),
    "true"
  );
  assert.equal(await page.locator("#answer-section").isVisible(), true);
  assert.match(await page.locator("#detail-answer").innerText(), /单位电荷的电势能差/);
  assert.equal(await page.locator("#knowledge-section").isVisible(), true);
  assert.equal(await page.locator("#facts-section").isVisible(), true);
  assert.match(await page.locator("#detail-knowledge").innerText(), /电势差/);
  assert.equal(await page.locator("#visual-section").isVisible(), true);
  assert.equal(await page.locator("#detail-visual video").count(), 1);
  assert.match(
    await page.locator("#detail-visual video source").getAttribute("src"),
    /^data:video\/webm;base64,/
  );
  assert.equal(await page.locator("#detail-videos .video-player").count(), 1);
  assert.equal(await page.locator("#videos-section").isVisible(), true);
  assert.equal(await page.locator("#previous-question").isVisible(), true);
  assert.equal(await page.locator("#next-question").isVisible(), true);

  await page.goto(
    `${pathToFileURL(pagePath).href}#question-electrochemical-energy`,
    { waitUntil: "load" }
  );
  await waitForLayout(page, "chain", 7);
  assert.match(await page.locator("#detail-kicker").innerText(), /边界/);
  assert.equal(await page.locator("#next-question").isHidden(), true);
  assert.equal(
    await page.locator('.why-step[data-node-id="electrochemical-energy"]').getAttribute("aria-pressed"),
    "true"
  );

  for (const nodeId of ["electron-drift", "voltage", "battery"]) {
    await page.goto(
      `${pathToFileURL(pagePath).href}#question-${nodeId}`,
      { waitUntil: "load" }
    );
    await waitForLayout(page, "chain", 7);
    assert.equal(await page.locator("#detail-visual video").count(), 1);
    assert.match(
      await page.locator("#detail-visual video source").getAttribute("src"),
      /^data:video\/webm;base64,/,
      `${nodeId} should use Manim`
    );
    await page.waitForFunction(() => {
      const video = document.querySelector("#detail-visual video");
      return video && video.readyState >= 1;
    });
  }

  await page.goto(
    `${pathToFileURL(pagePath).href}#question-thermal-radiation`,
    { waitUntil: "load" }
  );
  await waitForLayout(page, "chain", 7);
  assert.equal(
    await page.locator("#detail-videos .video-player").count(),
    1
  );
  assert.equal(
    await page.locator("#detail-videos iframe").getAttribute("src"),
    "https://player.bilibili.com/player.html?bvid=BV1ze4y1t7hm&page=1&autoplay=0"
  );

  const hosted = await startPageServer(fs.readFileSync(pagePath, "utf8"));
  try {
    await page.goto(`${hosted.url}#question-thermal-radiation`, { waitUntil: "load" });
    await waitForLayout(page, "chain", 7);
    await page.locator('#detail-videos .video-choice[data-platform="youtube"]').click();
    assert.equal(
      await page.locator("#detail-videos iframe").getAttribute("src"),
      "https://www.youtube-nocookie.com/embed/Na8DULBe9xs"
    );
    assert.equal(
      await page.locator("#detail-videos .video-embed-fallback").isHidden(),
      true
    );
  } finally {
    await new Promise(resolve => hosted.server.close(resolve));
  }

  for (const count of [4, 6, 8]) {
    const variantPath = await buildVariant(count, tempDir);
    await page.goto(pathToFileURL(variantPath).href, { waitUntil: "load" });
    await waitForLayout(page, "chain", count);
    assert.equal(await page.locator(".why-step").count(), count);
    await assertNoOverlap(page, ".why-step", `desktop ${count}-node chain`);
    await assertNoHorizontalOverflow(page, `desktop ${count}-node chain`);
  }

  const mobile = await context.newPage();
  const mobileErrors = [];
  mobile.on("pageerror", error => mobileErrors.push(error.message));
  mobile.on("console", message => {
    if (message.type() === "error") mobileErrors.push(message.text());
  });

  for (const width of [390, 320]) {
    await mobile.setViewportSize({ width, height: 900 });
    await mobile.goto(pathToFileURL(pagePath).href, { waitUntil: "load" });
    await waitForLayout(mobile, "chain", 7);
    assert.equal(await mobile.locator(".why-step").count(), 7);
    await assertNoOverlap(mobile, ".why-step", `mobile ${width}px chain`);
    await assertNoHorizontalOverflow(mobile, `mobile ${width}px`);
    await mobile.locator(".why-step").first().click();
    await mobile.waitForFunction(() => location.hash === "#question-incandescence");
    assert.equal(await mobile.locator("#detail-videos .video-player").count(), 1);
    assert.equal(await mobile.locator("#detail-videos iframe").count(), 1);
    assert.equal(await mobile.locator("#detail-visual img").count(), 1);
    assert.equal(await mobile.locator("#analogy-section").isVisible(), true);
    assert.equal(await mobile.locator(".analogy-mapping").count(), 4);
    assert.equal(await mobile.locator("#analogy-visual img").count(), 1);
    assert.equal(await mobile.locator("#hero-overview-image").isVisible(), true);
    assert.equal(
      await mobile
        .locator("#hero-overview")
        .evaluate(element => getComputedStyle(element).position),
      "relative"
    );
    const overviewWidth = await mobile
      .locator("#hero-overview")
      .evaluate(element => element.getBoundingClientRect().width);
    assert.ok(
      overviewWidth >= 240,
      `mobile overview should stay readable; got ${overviewWidth}px at ${width}px viewport`
    );
    await assertNoHorizontalOverflow(mobile, `mobile ${width}px video detail`);

    if (width === 390 && process.env.ASKWHY_SCREENSHOT_DIR) {
      await mobile.screenshot({
        path: path.join(process.env.ASKWHY_SCREENSHOT_DIR, "askwhy-mobile-390.png"),
        fullPage: true
      });
    }
  }

  const mobileVariant = await buildVariant(8, tempDir);
  await mobile.setViewportSize({ width: 390, height: 900 });
  await mobile.goto(pathToFileURL(mobileVariant).href, { waitUntil: "load" });
  await waitForLayout(mobile, "chain", 8);
  await assertNoOverlap(mobile, ".why-step", "mobile eight-node chain");
  await assertNoHorizontalOverflow(mobile, "mobile eight-node chain");

  await page.goto(
    pathToFileURL(path.join(skillRoot, "examples", "apple-falls.html")).href,
    { waitUntil: "load" }
  );
  await waitForLayout(page, "chain", 6);
  assert.equal(
    await page.locator("#analogy-title").innerText(),
    "巨人和小孩坐在滑板椅上拉绳子"
  );
  assert.equal(await page.locator("#analogy-visual img").count(), 1);
  assert.ok(
    await page.locator("#analogy-visual img").evaluate(image => image.naturalWidth > 0)
  );
  assert.ok(
    await page.locator("#hero-overview-image").evaluate(image => image.naturalWidth > 0)
  );

  assert.deepEqual(consoleErrors, []);
  assert.deepEqual(mobileErrors, []);
  const allowedEmbedHosts = new Set([
    "player.bilibili.com",
    "www.youtube-nocookie.com"
  ]);
  assert.ok(
    externalRequests.every(value => allowedEmbedHosts.has(new URL(value).hostname)),
    `unexpected remote asset request: ${externalRequests.join(", ")}`
  );
  console.log("AskWhy browser tests passed: analogy visuals, causal chain, inline videos, 390px, 320px, 4/6/8 nodes.");
} finally {
  await browser.close();
  fs.rmSync(tempDir, { recursive: true, force: true });
}
