# AskWhy Visual System

AskWhy borrows the spacious, question-first spirit of its reference page while
remaining a distinct product.

## Identity

- Name: AskWhy
- Tagline: “从一个问题，走向它的答案”
- Mark: a simple inline question/spark glyph
- Primary accent: violet `#7055d9`
- Supporting accents: green for evidence/observation, amber for context
- Background: near-white lilac paper
- No DeepWhy logo or DeepWhy account language

## Layout

- A compact top bar with AskWhy identity and copy/share actions.
- A single editorial hero surface: the question, short orientation, reading
  metadata, and topic overview belong to one composition rather than separate
  floating cards.
- The top-right hero area is a topic-specific `center.overviewVisual`
  infographic that summarizes the full causal chain at a glance. Do not use a
  generic question-mark or decorative orbit graphic.
- Keep the overview and hero copy in the same visual surface, but give the
  infographic its own complete, non-overlapping region. Do not mask, crop, or
  cover meaningful labels with text or another card.
- Prefer a panoramic overview composition that fits the available image region
  at a compact hero height without reducing labels below readable size.
- Do not label the infographic with a “知识总览” badge or similar floating tag;
  let the illustration and its content identify themselves.
- Keep the overview visually self-contained. Its caption remains available to
  assistive technology but should not repeat the same summary below the image.
- Keep the hero vertically compact: cap the overview width, reduce redundant
  metadata, and do not let empty space stretch the first viewport.
- Avoid the generic English “QUESTION EXPLORER” eyebrow. Use the actual subject
  category and selected learning stage as the small orienting line.
- On narrow screens, move the overview below the hero text and keep it at
  readable full-width size rather than shrinking it into an icon or covering the
  text.
- Show the selected learning stage as a metadata pill. Do not show an in-page
  stage selector because alternate-stage content is not generated.
- Desktop: the causal ladder is the dominant left surface and the detail panel
  sits on the right.
- The ladder starts with one violet root card, then descends through numbered
  question/answer cards on a continuous causal rail.
- Use the same vertical order on mobile; do not switch to a radial graph.
- Every chain card uses the same full-strength treatment because every node has
  a complete detail panel.
- The detail panel exposes previous/next question navigation.

## Components

- Question nodes are buttons with a `WHY 01` tag, type, detail-level chip,
  question, one-sentence answer, and optional image or animation poster.
- Details have summary, answer, a distinct familiar-analogy card with explicit
  mappings and limits, core knowledge, facts, optional observation, and an
  optional inline 16:9 video player.
- Show the analogy card after the answer and before the previous/next navigation
  so intuition arrives before the abstract explanation and navigation controls.
- Put the analogy visual at the top of the analogy card. It depicts the familiar
  scene; keep the node's primary visual for the real mechanism.
- A node visual appears first in the detail panel. Static images preserve their
  aspect ratio; Manim uses the same 16:9 frame with live caption cues.
- Outline nodes show the short answer and evidence without large empty detail
  sections.
- Video uses one active player. Additional videos for the same node appear below
  as selectable rows that swap the iframe source.
- Use inline Bilibili and YouTube SVG marks wherever a video source is shown.
  Do not substitute text-only platform badges or remote logo images.
- Keep an “open video” fallback link beneath every embedded player.
- YouTube blocks `file://` embeds with player error 153. Detect that protocol and
  render a branded HTTP-origin fallback instead of a broken player. Through an
  HTTP(S) host, both Bilibili and YouTube use the same inline player pattern.
- Do not render a separate follow-up or side-question strip. Keep one ordered
  causal path and use only the selected node's previous/next controls.
- Copy question and share link are the only global actions.
- Name the video section “视频讲解”.

## Motion

- Use restrained state transitions: active question, detail fade, and causal-rail
  emphasis.
- Manim motion is explanatory, muted, looping, and replayable. Reduced-motion
  users see the poster without autoplay.
- Do not add looping decorative motion.
- Respect `prefers-reduced-motion`.

## Typography and color

- Use a local system Chinese/Latin stack; do not load remote fonts.
- Keep the violet accent consistent across actions, active questions, and focus.
- Use generous spacing and restrained shadows.
