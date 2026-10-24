#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const pagePath = path.resolve(process.argv[2] || "examples/apple-gravity.html");

let playwright;
try {
  playwright = await import("playwright");
} catch (error) {
  try {
    playwright = await import("@playwright/test");
  } catch (fallbackError) {
    try {
      const require = createRequire(import.meta.url);
      playwright = await import(pathToFileURL(require.resolve("playwright")).href);
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
const browser = await playwright.chromium.launch(launchOptions);
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const consoleErrors = [];
page.on("pageerror", error => consoleErrors.push(`pageerror: ${error.message}`));
page.on("console", message => {
  if (message.type() === "error") consoleErrors.push(`console: ${message.text()}`);
});

try {
  await page.goto(pathToFileURL(pagePath).href, { waitUntil: "load" });

  assert.equal(await page.locator("h1").count(), 1);
  assert.match(await page.locator("#page-title").innerText(), /苹果/);
  assert.equal(await page.locator(".node-card").count(), 6);
  assert.equal(await page.locator(".chain-row").count(), 6);
  const embeddedExampleData = await page
    .locator("#deepwhy-data")
    .evaluate(element => JSON.parse(element.textContent));
  assert.ok(
    embeddedExampleData.chain.nodes.every(node => node.videoIds.length === 5),
    "every knowledge node should reference exactly five external videos"
  );
  assert.equal(
    new Set(embeddedExampleData.chain.nodes.flatMap(node => node.videoIds)).size,
    30,
    "each knowledge node should use a different set of videos"
  );
  assert.equal(await page.locator("#inspector:visible").count(), 1);
  assert.equal(await page.locator("#background-dialog[open]").count(), 0);
  assert.equal(
    await page.locator("#open-background-completion").count(),
    0,
    "research entry points must not sit below the main chain"
  );
  assert.equal(await page.locator("#verify-all").count(), 0);
  assert.equal(await page.locator(".opening-visual:visible").count(), 1);
  assert.ok(await page.locator(".opening-visual svg").count() === 1);
  assert.equal(
    await page.locator(".opening-visual .motion-replay").count(),
    1,
    "animated knowledge visuals should offer a replay action"
  );
  assert.equal(
    await page.locator(".opening-visual").evaluate(
      element =>
        [...element.querySelectorAll("*")].filter(
          child => child.localName.toLowerCase() === "animatetransform"
        ).length
    ),
    1,
    "the motion opening should animate instead of only showing a static trajectory"
  );
  assert.ok((await page.locator("#key-insight").innerText()).length > 10);
  assert.match(await page.locator("#journey-position").innerText(), /第 1 \/ 6 层/);
  assert.match(await page.locator("#next-action-copy").innerText(), /下一问/);
  assert.equal(
    (await page.locator("#inspector .tab-button").allInnerTexts()).join("|"),
    "理解|视频|研究背景|行业发展|检查理解"
  );
  assert.equal(await page.locator(".source-chip").count(), 0);
  assert.equal(
    await page.locator("#video-button, #background-button, #theme-toggle").count(),
    0,
    "the header should not show video count, research, or theme buttons"
  );
  assert.ok(
    (await page.locator(".node-card").first().boundingBox()).y < 950,
    "the knowledge chain must begin in the first viewport"
  );
  const [pathBox, benchBox] = await Promise.all([
    page.locator(".chain-stage").boundingBox(),
    page.locator("#inspector").boundingBox()
  ]);
  assert.ok(pathBox);
  assert.ok(benchBox);
  assert.ok(
    pathBox.width > 500 && benchBox.width > pathBox.width * 1.1,
    "the main chain canvas should be substantial while the lesson bench remains wider"
  );
  assert.ok(
    (await page.locator("#chain-legend .chain-legend-item").count()) >= 3,
    "the graph should expose a readable node-type legend"
  );
  assert.equal(
    await page.locator(".chain-next-placeholder").count(),
    1,
    "the chain should end with an explore/verify placeholder"
  );
  assert.equal(await page.locator(".app-header [data-global-view]").count(), 5);
  assert.equal(await page.locator(".app-header .global-switcher").count(), 1);
  const inactiveSwitchStyle = await page
    .locator('[data-global-view="people"]')
    .evaluate(element => {
      const style = getComputedStyle(element);
      return {
        background: style.backgroundColor,
        border: style.borderColor
      };
    });

  await page.locator('[data-global-view="development"]').click();
  await page.waitForFunction(() => {
    const button = document.querySelector('[data-global-view="development"]');
    return button && getComputedStyle(button).color === "rgb(255, 255, 255)";
  });
  const activeSwitchStyle = await page
    .locator('[data-global-view="development"]')
    .evaluate(element => {
      const style = getComputedStyle(element);
      return {
        background: style.backgroundColor,
        color: style.color
      };
    });
  assert.equal(activeSwitchStyle.color, "rgb(255, 255, 255)");
  assert.notEqual(activeSwitchStyle.background, inactiveSwitchStyle.background);
  assert.notEqual(inactiveSwitchStyle.border, "rgba(0, 0, 0, 0)");
  assert.equal(await page.locator("#inspector-title").innerText(), "从起点到当前");
  assert.ok(await page.locator("#inspector .timeline li").count() >= 1);
  assert.ok(
    await page
      .locator("#inspector .research-section")
      .filter({ hasText: "当前阶段" })
      .count() >= 1
  );

  await page.locator('[data-global-view="people"]').click();
  assert.equal(await page.locator("#inspector-title").innerText(), "相关人物");
  assert.ok(await page.locator("#inspector .background-card").count() >= 1);

  await page.locator('[data-global-view="stage"]').click();
  assert.equal(await page.locator("#inspector-title").innerText(), "当前阶段与研究边界");
  assert.ok(
    await page
      .locator("#inspector .background-card")
      .filter({ hasText: "仍未解决" })
      .count() >= 1
  );
  await page.locator('.node-card[data-node-id="n1"]').click();
  const suggestedQuestions = page.locator("#next-question-list .next-question-link");
  assert.equal(await suggestedQuestions.count(), 3);
  const suggestedUrl = new URL(await suggestedQuestions.first().getAttribute("href"));
  assert.equal(suggestedUrl.origin, "https://deepwhy.cn");
  assert.equal(suggestedUrl.searchParams.get("topic"), "苹果为什么会落地？");
  assert.ok(suggestedUrl.searchParams.get("question"));
  assert.ok(
    await page.locator(".node-answer").first().evaluate(element => {
      const style = getComputedStyle(element);
      return style.webkitLineClamp === "2";
    }),
    "main node answers must be compact"
  );
  const diagramOverlapIssues = await page
    .locator(".figure-frame svg")
    .evaluateAll(svgs => {
      const issues = [];
      svgs.forEach((svg, svgIndex) => {
        const svgRect = svg.getBoundingClientRect();
        const textRects = [...svg.querySelectorAll("text")].map(text => {
          const rect = text.getBoundingClientRect();
          return {
            text: text.textContent.trim(),
            left: rect.left,
            top: rect.top,
            right: rect.right,
            bottom: rect.bottom
          };
        });
        textRects.forEach(rect => {
          if (
            rect.text &&
            (rect.left < svgRect.left - 1 ||
              rect.top < svgRect.top - 1 ||
              rect.right > svgRect.right + 1 ||
              rect.bottom > svgRect.bottom + 1)
          ) {
            issues.push(`svg ${svgIndex}: "${rect.text}" leaves the viewBox`);
          }
        });
        for (let first = 0; first < textRects.length; first += 1) {
          for (let second = first + 1; second < textRects.length; second += 1) {
            const a = textRects[first];
            const b = textRects[second];
            if (!a.text || !b.text) continue;
            const overlapWidth = Math.min(a.right, b.right) - Math.max(a.left, b.left);
            const overlapHeight = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
            if (overlapWidth > 1 && overlapHeight > 1) {
              issues.push(`svg ${svgIndex}: "${a.text}" overlaps "${b.text}"`);
            }
          }
        }
      });
      return issues;
    });
  assert.deepEqual(
    diagramOverlapIssues,
    [],
    `diagram text must remain legible and unoccluded:\n${diagramOverlapIssues.join("\n")}`
  );

  const firstTitle = await page.locator("#inspector-title").innerText();
  assert.match(await page.locator("#inspector .lesson-bridge").innerText(), /接着上一层/);
  assert.ok(await page.locator("#inspector .plain-language").first().isVisible());
  assert.ok((await page.locator("#inspector .lesson-steps li").count()) >= 2);
  const teachingBlocks = await page
    .locator("#inspector .plain-language")
    .allInnerTexts();
  assert.match(teachingBlocks[0], /先想象这个场景/);
  assert.match(teachingBlocks[1], /把比喻对应到知识/);
  assert.equal(
    await page.locator("#inspector .video-bridge").count(),
    1,
    "the explanation should lead directly to the node's supporting video"
  );
  const microAnswer = page.locator("#inspector .micro-answer");
  assert.equal(await microAnswer.isHidden(), true);
  await page.locator("#inspector .micro-check button").click();
  assert.equal(await microAnswer.isVisible(), true);
  await page.locator("#hero-next-action").click();
  assert.equal(
    await page.locator('.node-card[data-node-id="n2"]').getAttribute("aria-current"),
    "true",
    "the primary next action should advance to the next knowledge node"
  );
  await page.locator('.node-card[data-node-id="n1"]').click();
  assert.equal(await page.locator("#inspector-title").innerText(), firstTitle);
  await page.locator('.node-card[data-node-id="n2"]').click();
  const secondTitle = await page.locator("#inspector-title").innerText();
  assert.notEqual(firstTitle, secondTitle, "node selection should change the inspector");
  assert.equal(await page.evaluate(() => location.hash), "#node-n2");
  const exampleManim = page.locator("#inspector .manim-feature");
  assert.equal(await exampleManim.count(), 1, "the generated example should render its Manim scene");
  const exampleVideo = exampleManim.locator("video");
  await exampleVideo.waitFor();
  await page.waitForFunction(() => {
    const video = document.querySelector("#inspector .manim-media video");
    return video && video.readyState >= 1;
  });
  assert.equal(
    await exampleManim.getAttribute("data-autoplay"),
    "true",
    "the generated example should autoplay only when reduced motion is not requested"
  );
  assert.equal(await page.locator('.node-card[data-node-id="n2"]').getAttribute("aria-current"), "true");
  assert.equal(
    await page.locator('.node-card[data-node-id="n2"]').evaluate(element =>
      element.style.getPropertyValue("--node-color")
    ),
    "#3b82f6"
  );
  const [selectedNodeBox, inactiveNodeBox] = await Promise.all([
    page.locator('.node-card[data-node-id="n2"]').boundingBox(),
    page.locator('.node-card[data-node-id="n3"]').boundingBox()
  ]);
  assert.ok(selectedNodeBox);
  assert.ok(inactiveNodeBox);
  assert.ok(
    inactiveNodeBox.height < selectedNodeBox.height,
    "inactive question-chain nodes should stay compact"
  );
  const miniVisual = page.locator('.chain-row[data-node-id="n2"] .node-mini-visual');
  assert.equal(
    await miniVisual.locator(".visual-formula").count(),
    0,
    "compact node thumbnails must not reserve space for formulas"
  );
  const [miniBox, miniSvgBox] = await Promise.all([
    miniVisual.boundingBox(),
    miniVisual.locator("svg, img").first().boundingBox()
  ]);
  assert.ok(miniBox);
  assert.ok(miniSvgBox);
  assert.ok(
    miniSvgBox.y >= miniBox.y - 1 &&
      miniSvgBox.y + miniSvgBox.height <= miniBox.y + miniBox.height + 1,
    "node thumbnail media should remain fully inside its frame"
  );
  const predictionOptions = page.locator("#inspector .interaction-option");
  assert.equal(
    await predictionOptions.count(),
    3,
    "mechanism nodes should expose a content-specific prediction"
  );
  await predictionOptions.first().click();
  assert.equal(
    await page.locator("#inspector .interaction-feedback").getAttribute("data-correct"),
    "false"
  );
  await predictionOptions.nth(1).click();
  assert.equal(
    await page.locator("#inspector .interaction-feedback").getAttribute("data-correct"),
    "true"
  );
  const labShell = page.locator("#inspector .lab-shell");
  assert.equal(await labShell.count(), 1, "mechanism node should render one hands-on lab");
  assert.equal(await labShell.getAttribute("data-lab-kind"), "simulation");
  const inspectorBlockOrder = await page
    .locator("#inspector-body > *")
    .evaluateAll(nodes =>
      nodes.map(node => {
        if (node.classList.contains("manim-feature")) return "manim";
        if (node.classList.contains("lab-shell")) return "lab";
        if (node.classList.contains("figure-frame")) return "diagram";
        return null;
      }).filter(Boolean)
    );
  assert.ok(
    inspectorBlockOrder.indexOf("manim") < inspectorBlockOrder.indexOf("lab"),
    "the Manim explanation should precede the hands-on lab"
  );
  assert.ok(
    inspectorBlockOrder.indexOf("lab") < inspectorBlockOrder.indexOf("diagram"),
    "the hands-on lab should precede supporting static diagrams"
  );
  const labFrame = page.locator("#inspector iframe.lab-frame");
  assert.equal(await labFrame.count(), 1, "only one node lab iframe should be active");
  assert.equal(await labFrame.getAttribute("sandbox"), "allow-scripts");
  assert.ok(!(await labFrame.getAttribute("sandbox")).includes("allow-same-origin"));
  const lab = page.frameLocator("#inspector iframe.lab-frame");
  await lab.locator("#lab-root").waitFor();
  assert.match(
    await lab.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute("content"),
    /connect-src 'none'/
  );
  await lab.locator("#child-mass").fill("4");
  await lab.locator("#run").click();
  await page.waitForTimeout(4500);
  assert.equal(await labShell.getAttribute("data-complete"), "true");
  assert.equal(await labShell.locator(".lab-result").isVisible(), true);
  assert.equal(await labShell.locator(".lab-reflection").isVisible(), true);
  await labShell.locator(".lab-reflection textarea").fill("小孩更轻，所以同样的拉力让他移动得更明显。");
  const referenceButton = labShell.getByRole("button", { name: "查看参考思路" });
  assert.equal(await referenceButton.isEnabled(), true);
  await referenceButton.click();
  assert.equal(
    await labShell.locator(".lab-reflection > p:last-child").isVisible(),
    true
  );
  await labShell.locator(".lab-expand").click();
  assert.equal(await labShell.evaluate(element => element.classList.contains("is-expanded")), true);
  await page.keyboard.press("Escape");
  assert.equal(await labShell.evaluate(element => element.classList.contains("is-expanded")), false);
  await lab.locator("#lab-reset").click();
  await page.waitForTimeout(200);
  assert.equal(await labShell.getAttribute("data-complete"), "false");
  await page.locator('#inspector [data-tab="research"]').click();
  const researchSections = page.locator("#inspector .research-section");
  assert.ok(
    (await researchSections.count()) >= 1,
    "the research tab should surface source-matched background sections"
  );
  assert.equal(
    await page
      .locator("#inspector .research-section")
      .filter({ hasText: "人物与贡献" })
      .locator(".background-card")
      .count(),
    2,
    "the research tab should only show people tied to this node's sources"
  );
  assert.equal(await page.locator(".source-chip").count(), 0);
  await page.locator('#inspector [data-tab="industry"]').click();
  assert.ok(
    (await page.locator("#inspector .industry-section").count()) >= 1,
    "the industry tab should surface applications, timeline, or frontier context"
  );
  assert.equal(await page.locator(".source-chip").count(), 0);
  await page.locator('#inspector [data-tab="understand"]').click();

  const disclosure = page.locator("#inspector details.disclosure").first();
  assert.equal(await disclosure.count(), 1, "deep text should exist in a disclosure");
  assert.equal(await disclosure.evaluate(element => element.open), false);
  assert.equal(
    await page.locator("#inspector .disclosure-body:visible").count(),
    0,
    "deep text should be collapsed by default"
  );

  await page.locator('.node-card[data-node-id="n3"]').click();
  assert.equal(await page.locator('.chain-row[data-node-id="n3"] .branch-button').count(), 0);
  const branchToggle = page.locator('.chain-row[data-node-id="n3"] .branch-toggle');
  assert.equal(await branchToggle.getAttribute("aria-expanded"), "false");
  await branchToggle.click();
  const branch = page.locator('.chain-row[data-node-id="n3"] .branch-button').first();
  assert.equal(await branch.count(), 1, "branches should appear only after explicit expansion");
  await branch.click();
  assert.match(await page.locator("#inspector-title").innerText(), /^分支：/);
  assert.equal(await page.locator("#branch-origin-wrap .back-branch").count(), 1);
  await page.locator("#branch-origin-wrap .back-branch").click();
  assert.equal(await page.locator("#inspector-title").innerText(), "什么会让苹果和地球之间的吸引更强？");
  const interaction = page.locator("#inspector .visual-interaction input[type='range']");
  assert.equal(await interaction.count(), 1, "principle node should expose a manipulable variable");
  const initialResult = await page.locator("#inspector .visual-interaction output").innerText();
  await interaction.fill("2");
  const changedResult = await page.locator("#inspector .visual-interaction output").innerText();
  assert.notEqual(initialResult, changedResult, "range interaction should update its result");

  await page.locator("#next-node").click();
  assert.match(await page.locator("#inspector-title").innerText(), /没有伸出一根绳|弯曲/);
  await page.locator("#prev-node").click();

  await page.locator('#inspector [data-tab="video"]').click();
  assert.equal(
    await page
      .locator("#inspector")
      .getByText("YouTube 页面在当前网络环境下无法完成核验", { exact: false })
      .count(),
    0,
    "platform verification gaps should not be shown in the Video tab"
  );
  assert.ok(
    (await page.locator("#inspector .resource-card").count()) >= 1,
    "video tab should surface the selected node's video"
  );
  assert.equal(
    await page.locator("#inspector .video-thumbnail-button").count(),
    4,
    "each node's video tab should show four thumbnails below the primary player"
  );
  assert.equal(await page.locator("#inspector .video-thumbnail-media img").count(), 4);
  assert.ok(
    (
      await page
        .locator("#inspector .video-thumbnail-media img")
        .evaluateAll(images => images.map(image => image.getAttribute("src")))
    ).every(source => source?.startsWith("https://")),
    "video thumbnail cards should use external thumbnail URLs"
  );
  assert.equal(await page.locator("#inspector iframe").count(), 1, "only one primary player should load");
  const firstNodePlayerSource = await page
    .locator("#inspector iframe")
    .getAttribute("src");
  await page.locator("#inspector .video-thumbnail-button").first().click();
  await page.waitForTimeout(250);
  assert.notEqual(
    await page.locator("#inspector iframe").getAttribute("src"),
    firstNodePlayerSource,
    "selecting a node thumbnail should swap that node's primary player"
  );

  await page.locator('#inspector [data-tab="quiz"]').click();
  assert.equal(await page.locator("#inspector [data-tab='quiz']").getAttribute("aria-selected"), "true");
  const quiz = page.locator("#inspector .quiz-card").first();
  assert.equal(await quiz.count(), 1);
  assert.match(await page.locator("#inspector .quiz-topline").innerText(), /1 \/ 5/);
  assert.equal(await quiz.locator('button[type="submit"]').count(), 0);
  await quiz.locator('input[value="1"]').check();
  assert.equal(await quiz.locator(".quiz-feedback").getAttribute("data-result"), "incorrect");
  assert.equal(
    await quiz.locator('.option[data-result="incorrect"]').evaluate(element =>
      getComputedStyle(element).borderColor
    ),
    "rgb(210, 75, 102)"
  );
  assert.equal(
    await quiz.locator('.option[data-result="correct"]').evaluate(element =>
      getComputedStyle(element).borderColor
    ),
    "rgb(46, 155, 119)"
  );
  assert.match(await quiz.locator(".quiz-feedback").innerText(), /正确答案/);
  await quiz.locator('input[value="0"]').check();
  assert.equal(await quiz.locator(".quiz-feedback").getAttribute("data-result"), "correct");
  assert.match(await quiz.locator(".quiz-feedback").innerText(), /回答正确/);
  const answerCard = page.locator("#inspector .answer-card");
  assert.equal(await answerCard.count(), 1, "answering should reveal the answer card");
  assert.equal(await answerCard.locator(".answer-card-button").count(), 5);
  assert.equal(
    await answerCard.locator('.answer-card-button[data-result="correct"]').count(),
    1
  );
  await page.locator("#inspector .quiz-actions button").last().click();
  assert.match(await page.locator("#inspector .quiz-topline").innerText(), /2 \/ 5/);
  await page.locator("#inspector .answer-card-button").last().click();
  assert.match(await page.locator("#inspector .quiz-topline").innerText(), /5 \/ 5/);
  const n3Questions = embeddedExampleData.assessment.items.filter(
    item => item.nodeId === "n3"
  );
  assert.equal(
    await page.locator("#inspector .quiz-actions").getByText("下一题").count(),
    1,
    "the final unanswered question may still show a disabled next action"
  );
  await page
    .locator(`#inspector .quiz-card input[value="${n3Questions[4].correctIndex}"]`)
    .check();
  assert.equal(
    await page.locator("#inspector .quiz-actions").getByText("下一题").count(),
    0,
    "after answering the final question the next action should disappear"
  );
  assert.match(
    await page.locator("#inspector .answer-card-head").innerText(),
    /已答 2\/5/
  );
  await page.locator('[data-global-view="quiz"]').click();
  assert.equal(
    await page.locator("#inspector [data-tab='quiz']").getAttribute("aria-selected"),
    "true"
  );
  assert.match(await page.locator("#inspector .quiz-topline").innerText(), /全局测验/);
  assert.match(await page.locator("#inspector .quiz-topline").innerText(), /1 \/ 30/);
  await page.locator('.node-card[data-node-id="n3"]').click();
  assert.match(await page.locator("#inspector .quiz-topline").innerText(), /节点小测/);
  assert.match(await page.locator("#inspector .quiz-topline").innerText(), /1 \/ 5/);

  await page.locator('[data-global-view="videos"]').click();
  assert.equal(await page.locator("#inspector-title").innerText(), "视频资料库");
  assert.equal(
    await page.locator("#inspector .global-video-library-card").count(),
    30,
    "the right-side global video library should show all 30 videos"
  );
  assert.equal(await page.locator("#inspector iframe").count(), 0);
  await page.locator("#gap-link").click();
  assert.equal(await page.locator("#background-dialog[open]").count(), 1);
  await page.locator('[data-background-tab="timeline"]').click();
  const prototypeFilter = page.locator('[data-timeline-filter="prototype"]');
  await prototypeFilter.click();
  assert.equal(
    await page.locator("#background-body .timeline li").count(),
    1,
    "background timeline should filter by event type"
  );
  await page.locator("#background-body .timeline button").first().click();
  assert.equal(await page.locator("#background-body .timeline li.is-open").count(), 1);
  await page.locator('[data-background-tab="sources"]').click();
  assert.ok((await page.locator("#background-body .source-item").count()) >= 10);
  await page.locator("#background-close").click();
  assert.equal(await page.locator("#background-dialog[open]").count(), 0);

  assert.equal(
    await page.locator("#deepwhy-completion, #deepwhy-background").count(),
    0,
    "the standalone page must not include a DeepWhy system CTA"
  );

  assert.equal(await page.locator("html").getAttribute("data-theme"), "light");

  const styleFingerprints = new Set();
  for (const style of ["deepwhy", "atlas", "chronicle", "fieldnotes"]) {
    const fingerprint = await page.evaluate(name => {
      document.documentElement.dataset.style = name;
      const computed = getComputedStyle(document.documentElement);
      return [
        computed.getPropertyValue("--bg").trim(),
        computed.getPropertyValue("--radius-xl").trim(),
        computed.getPropertyValue("--display").trim()
      ].join("|");
    }, style);
    styleFingerprints.add(fingerprint);
  }
  assert.equal(styleFingerprints.size, 4, "four visual presets should have distinct visual tokens");
  const visualKinds = await page.locator(".node-card").evaluateAll(cards =>
    [...new Set(cards.map(card => card.dataset.visualKind))]
  );
  assert.ok(
    visualKinds.includes("force") &&
      visualKinds.includes("equation") &&
      visualKinds.includes("comparison") &&
      visualKinds.includes("evidence"),
    "knowledge nodes should use content-specific visual forms"
  );

  const keyboardPage = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  try {
    await keyboardPage.goto(pathToFileURL(pagePath).href, { waitUntil: "load" });
    await keyboardPage.locator("#page-title").click();
    await keyboardPage.keyboard.press("ArrowRight");
    assert.equal(
      await keyboardPage.locator('.node-card[data-node-id="n2"]').getAttribute("aria-current"),
      "true",
      "ArrowRight should move to the next knowledge node"
    );
  } finally {
    await keyboardPage.close();
  }

  const hashPage = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  try {
    await hashPage.goto(`${pathToFileURL(pagePath).href}#node-n4`, { waitUntil: "load" });
    await hashPage.locator('.node-card[data-node-id="n4"][aria-current="true"]').waitFor();
    assert.match(await hashPage.locator("#inspector-type").innerText(), /理论/);
  } finally {
    await hashPage.close();
  }

  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload({ waitUntil: "load" });
  assert.equal(await page.locator("#inspector:visible").count(), 0, "mobile inspector starts closed");
  const mobileOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth
  );
  assert.ok(mobileOverflow <= 2, `mobile page overflowed by ${mobileOverflow}px`);
  await page.locator('.node-card[data-node-id="n3"]').click();
  await page.locator("#inspector").waitFor({ state: "visible" });
  assert.equal(await page.locator("#inspector:visible").count(), 1, "mobile node click opens detail sheet");
  assert.equal(await page.locator("#inspector .close-button:visible").count(), 1);
  assert.equal(
    await page.locator("#inspector .lab-shell[data-lab-kind='diagram']").count(),
    1,
    "mobile detail should expose the node lab"
  );
  const mobileLabOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth
  );
  assert.ok(mobileLabOverflow <= 2, `mobile lab overflowed by ${mobileLabOverflow}px`);
  await page.locator("#inspector-close").click();
  await page.locator("#inspector").waitFor({ state: "hidden" });
  assert.equal(await page.locator("#inspector:visible").count(), 0);

  const html = fs.readFileSync(pagePath, "utf8");
  const match = html.match(
    /<script id="deepwhy-data" type="application\/json">([\s\S]*?)<\/script>/
  );
  assert.ok(match);
  const variantData = JSON.parse(match[1]);
  variantData.meta.topic = 'Why does an apple fall & "why" does it matter?';
  variantData.meta.premiseCheck = {
    status: "corrected",
    original: "苹果落地是因为地球单独拉它吗？",
    note: "引力的作用是相互的；地球也会受到苹果的吸引，只是加速度极小。"
  };
  variantData.videos.items[0].metricsStatus = "unavailable";
  variantData.videos.items[0].metrics = { views: null, likes: null, comments: null };
  variantData.chain.openingVisual.svg =
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 80">' +
    '<rect width="120" height="80" fill="#f4efe4"/>' +
    '<text x="8" y="20" font-size="10">motion test</text>' +
    '<circle cx="20" cy="44" r="8" fill="#9b4d36">' +
    '<animateMotion dur="2s" repeatCount="indefinite" path="M0 0 L70 0"/>' +
    "</circle></svg>";
  variantData.chain.openingVisual.interaction = {
    kind: "toggle",
    prompt: "切换条件，比较结果",
    label: "示例条件",
    onLabel: "开启",
    offLabel: "关闭",
    onFeedback: "条件开启后的结果。",
    offFeedback: "条件关闭后的结果。",
    initial: false
  };
  variantData.chain.nodes[1].manim = {
    sceneSource: "media/test_scene.py",
    sceneClass: "TestScene",
    videoSrc: "data:video/webm;base64,AAAA",
    posterSrc: "data:image/webp;base64,AAAA",
    durationSeconds: 4,
    alt: "动画不可用测试",
    caption: "视频失败时保留可读的静态说明。",
    transcript: [
      { start: 0, end: 4, text: "这是动画的文字替代。" }
    ],
    fallbackSvg:
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 80">' +
      '<rect width="120" height="80" fill="#f4efe4"/>' +
      '<text x="12" y="42" font-size="10">静态回退</text></svg>'
  };
  const variantDir = fs.mkdtempSync(path.join(os.tmpdir(), "deepwhy-chain-"));
  const variantPath = path.join(variantDir, "variant.html");
  const embedded = JSON.stringify(variantData).replaceAll("</", "<\\/");
  fs.writeFileSync(
    variantPath,
    html.replace(
      /(<script id="deepwhy-data" type="application\/json">)[\s\S]*?(<\/script>)/,
      `$1${embedded}$2`
    ),
    "utf8"
  );

  const variantPage = await browser.newPage({ viewport: { width: 1000, height: 900 } });
  try {
    await variantPage.goto(pathToFileURL(variantPath).href, { waitUntil: "load" });
    assert.match(
      await variantPage.locator("#premise-notice").innerText(),
      /前提已校正/
    );
    await variantPage.locator('.node-card[data-node-id="n1"]').click();
    await variantPage.locator('#inspector [data-tab="video"]').click();
    const metrics = await variantPage
      .locator("#inspector .resource-card")
      .first()
      .locator(".metric dd")
      .allInnerTexts();
    assert.deepEqual(metrics, ["未获取", "未获取", "未获取"]);
    assert.equal(
      await variantPage.locator(".opening-visual").evaluate(
        element =>
          [...element.querySelectorAll("*")].filter(
            child => child.localName.toLowerCase() === "animatemotion"
          ).length
      ),
      1,
      "inline SVG animation must survive sanitization"
    );
    await variantPage.locator(".opening-visual .interaction-toggle input").check();
    assert.match(
      await variantPage.locator(".opening-visual .interaction-feedback").innerText(),
      /开启/
    );
    await variantPage.locator('.node-card[data-node-id="n2"]').click();
    await variantPage.locator('#inspector [data-tab="understand"]').click();
    const manimFeature = variantPage.locator("#inspector .manim-feature");
    assert.equal(await manimFeature.count(), 1);
    assert.equal(
      await manimFeature.locator(".manim-transcript li").count(),
      1
    );
    await manimFeature.locator(".manim-media svg").waitFor();
    const manimOrder = await variantPage
      .locator("#inspector-body > *")
      .evaluateAll(nodes =>
        nodes.map(node => {
          if (node.classList.contains("manim-feature")) return "manim";
          if (node.classList.contains("lab-shell")) return "lab";
          return null;
        }).filter(Boolean)
      );
    assert.ok(
      manimOrder.indexOf("manim") < manimOrder.indexOf("lab"),
      "Manim animation must appear before the node lab"
    );
  } finally {
    await variantPage.close();
    fs.rmSync(variantDir, { recursive: true, force: true });
  }

  const reducedMotionPage = await browser.newPage({
    viewport: { width: 1000, height: 900 },
    reducedMotion: "reduce"
  });
  try {
    await reducedMotionPage.setContent(
      html.replace(
        /(<script id="deepwhy-data" type="application\/json">)[\s\S]*?(<\/script>)/,
        `$1${JSON.stringify(variantData).replaceAll("</", "<\\/")}$2`
      ),
      { waitUntil: "load" }
    );
    assert.equal(
      await reducedMotionPage
        .locator(".opening-visual svg[data-reduced-motion='true']")
        .count(),
      1,
      "animated SVGs should settle when reduced motion is requested"
    );
    await reducedMotionPage.locator('.node-card[data-node-id="n2"]').click();
    await reducedMotionPage.locator('#inspector [data-tab="understand"]').click();
    assert.equal(
      await reducedMotionPage
        .locator("#inspector .manim-feature")
        .getAttribute("data-autoplay"),
      "false",
      "Manim video must not autoplay when reduced motion is requested"
    );
  } finally {
    await reducedMotionPage.close();
  }

  assert.deepEqual(consoleErrors, [], "page should not emit uncaught errors");
  console.log(
    `PASS browser: ${path.relative(process.cwd(), pagePath)} (refined chain, collapsed branches, five node tabs, distinct node videos, top global switcher with right-side development/people/stage/video library/global quiz, DeepWhy follow-up links, answer card, final-next hiding, presets, mobile, Manim fallback)`
  );
} finally {
  await browser.close();
}
