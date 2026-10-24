# Content Contract v2

The final HTML embeds one JSON object in:

```html
<script id="deepwhy-data" type="application/json">...</script>
```

The machine-readable schema is
[`assets/content.schema.json`](../assets/content.schema.json). The builder and
validator enforce the knowledge-chain limits and references.

## Top-level

```json
{
  "schemaVersion": "2.0",
  "meta": {},
  "presentation": {},
  "sources": [],
  "chain": {},
  "videos": {},
  "background": {},
  "assessment": {},
  "nextQuestions": []
}
```

## `meta`

Required:

```json
{
  "topic": "canonical topic",
  "question": "corrected question",
  "slug": "ascii-hyphen-slug",
  "hook": "one short familiar-observation hook",
  "asOf": "YYYY-MM-DD",
  "language": "zh-CN",
  "audience": {
    "description": "who this is for",
    "priorKnowledge": "what is assumed",
    "explanationLevel": "child | beginner | teen | expert",
    "assumptions": []
  },
  "premiseCheck": {
    "status": "confirmed | corrected | uncertain",
    "original": "user wording",
    "note": "short correction or confirmation"
  },
  "scope": {
    "included": [],
    "excluded": []
  },
  "evidenceGaps": []
}
```

`hook` appears in the compact hero. It is not a second introduction paragraph.

## `presentation`

```json
{
  "preset": "deepwhy | atlas | chronicle | fieldnotes",
  "source": "auto | user | default",
  "rationale": "why this design direction fits the topic",
  "archetype": "phenomenon_exploration | principle_derivation | historical_evolution | cross_domain_connection | understanding_assessment",
  "centralInsight": "the discovery the learner should make",
  "focalRepresentation": "the dominant visual argument",
  "hierarchy": ["opening", "chain", "node detail", "background"],
  "sectionRhythm": ["large observation", "compact chain", "evidence", "boundary"]
}
```

The builder can override the preset with CLI or environment configuration.
These fields force the composition to be decided before HTML is written.

## `sources`

```json
{
  "id": "gps-gov-space",
  "title": "Space Segment",
  "publisher": "GPS.gov",
  "url": "https://www.gps.gov/space-segment",
  "kind": "official",
  "publishedAt": null,
  "accessedAt": "2026-10-23",
  "notes": "What this source supports."
}
```

Allowed kinds: `paper`, `official`, `reference`, `standard`, `book`, `report`,
`dataset`, `video`, `other`.

## `chain`

```json
{
  "title": "Knowledge chain title",
  "openingScenario": "No more than one sentence.",
  "openingQuestion": "The first why.",
  "openingVisual": {},
  "nodes": [],
  "takeaway": "One compact conclusion."
}
```

The chain contains 3–6 nodes. Prefer 4–6. Main node types must be nondecreasing:

`phenomenon → mechanism → principle → theory → frontier → boundary`.

`openingVisual` is required and is the dominant focal point in the opening
viewport.

### Chain node

```json
{
  "id": "n1",
  "parentId": null,
  "type": "phenomenon",
  "concept": "short concept label",
  "question": "one causal question",
  "answer": "one sentence, normally 20–60 Chinese characters",
  "analogy": "the node's one primary, familiar metaphor",
  "guide": {
    "bridge": "what the learner already established",
    "plainLanguage": "a child-readable explanation",
    "steps": ["one causal move", "the next causal move"],
    "check": {
      "prompt": "a prediction or misconception check",
      "answer": "a concise reveal"
    }
  },
  "status": "complete | partial | insufficient",
  "sourceIds": ["source-1"],
  "detail": {
    "deepDive": "",
    "whyItMatters": "",
    "experimentOrProof": "",
    "frontier": ""
  },
  "diagram": null,
  "manim": null,
  "videoIds": ["video-1", "video-2", "video-3", "video-4", "video-5"],
  "lab": null,
  "branches": []
}
```

`answer` is a hard maximum of 60 characters and should normally stay within
20–60 characters.
It is the only answer text rendered on the main chain card.

`analogy` is functional teaching content, not a flavor line. For mechanism,
principle, theory, and frontier nodes it is required. It should name one coherent,
familiar situation with visible action; `guide.plainLanguage` and
`guide.steps` then explain the mapping without mixing in a second metaphor.
Phenomenon nodes may use the opening scene directly, and boundary nodes may use a
counterexample. State metaphor limitations in `detail` or the node check rather
than hiding them.

`detail` fields are progressively disclosed. Empty strings are allowed when the
node status and sourced content do not support that dimension.

### Diagram

```json
{
  "mode": "svg",
  "kind": "force",
  "svg": "<svg ...>...</svg>",
  "src": null,
  "alt": "accessible description",
  "caption": "what the diagram shows and does not show",
  "formula": "optional formula or null",
  "sourceIds": ["source-1"],
  "interaction": null
}
```

Use `mode: "image"` and an absolute `src` only for a properly sourced existing
image. Render knowledge-bearing images in full at their intrinsic aspect ratio
with a contain-style fit; do not crop meaningful edges, labels, or objects to
force a preset aspect ratio. Inline SVG is preferred for exact labels.

For temporal or causal relationships, inline SVG may include the standard SMIL
elements `animate`, `animateTransform`, and `animateMotion`. Design every
animated visual so its important labels and settled result remain readable
without motion. The template ends these animations at their final state when
`prefers-reduced-motion` is active. Animate the metaphor element that performs
the causal work and resolve on the corresponding real mechanism. Essential
labels for raster images belong in adjacent DOM, not over the image. Animated or
static graphics must not cover text, annotations, controls, captions, or critical
marks.

Compact node thumbnails render only the complete graphic. Formulas, captions,
interaction controls, and other secondary content belong to the selected-node
detail view. Do not place them inside the fixed-height thumbnail container.

`kind` must dictate a knowledge-appropriate visual form: `force`, `motion`,
`geometry`, `equation`, `graph`, `architecture`, `execution_trace`, `timeline`,
`comparison`, `causal`, `feedback_loop`, `evidence`, or `illustration`.

At least one visual on the page must include an `interaction`; a 4–6 node page
should normally include two or three. Choose the form that lets the learner
discover the current relationship:

**Parameter slider.** Use for a quantity with a visible consequence:

```json
{
  "kind": "range",
  "prompt": "改变距离，观察拉力怎样变化",
  "label": "距离（相对单位）",
  "min": 0.5,
  "max": 4,
  "step": 0.25,
  "initial": 1,
  "resultTemplate": "距离 = {value} → 结果会在这里更新"
}
```

Use `kind: "inverse-square"` when the result template needs
`{inverseSquare}` as a computed `1 / value²`.

**Prediction.** Ask before revealing the causal result:

```json
{
  "kind": "prediction",
  "prompt": "如果苹果也拉地球，地球会怎样？",
  "options": [
    {"label": "完全不动", "feedback": "不对，反作用仍然存在。"},
    {"label": "移动极小", "feedback": "正确；质量越大，同样作用力下的加速度越小。"}
  ],
  "correctIndex": 1
}
```

**Two-state toggle.** Let the learner compare conditions without changing the
page's visual language:

```json
{
  "kind": "toggle",
  "prompt": "把地球变成和苹果一样轻，会发生什么？",
  "label": "地球质量",
  "onLabel": "与苹果相当",
  "offLabel": "真实地球",
  "onFeedback": "两者会向彼此移动得接近得多。",
  "offFeedback": "苹果明显移动，地球几乎不动。",
  "initial": false
}
```

Interactions must produce a truthful, immediate consequence, preserve the
metaphor, and remain readable as a static fallback. Do not use a control just to
repeat nearby text.

### Manim

`manim` is optional and `null`/absent when inline SVG already teaches the causal
move. Read [manim-animation.md](manim-animation.md) before choosing it, and obtain
explicit consent before installing the runtime.

```json
{
  "sceneSource": "media/node_scene.py",
  "sceneClass": "NodeScene",
  "videoSrc": "media/node-scene.webm",
  "posterSrc": "media/node-scene.webp",
  "durationSeconds": 8.4,
  "alt": "what motion or transformation the learner sees",
  "caption": "the causal rule shown by the animation",
  "transcript": [
    {"start": 0, "end": 3, "text": "first caption cue"},
    {"start": 3, "end": 7, "text": "second caption cue"}
  ],
  "fallbackSvg": "<svg ...>...</svg>"
}
```

Media paths are local and relative to the content JSON. The builder verifies
their existence and size, then embeds the WebM and WebP into the final HTML.
The limit is 30 seconds, 8 MiB for video, and 1 MiB for the poster. Transcript
cues must be ordered and non-overlapping. The fallback SVG must remain readable
without playback.

### Lab

`lab` is the node's self-contained hands-on activity. It is `null` when absent.
Every mechanism and principle node requires a lab; adjacent lab-bearing nodes
must use different `kind` values.

```json
{
  "kind": "simulation | diagram | code | game | spatial3d | procedural",
  "title": "short learner-facing activity title",
  "goal": "what relationship the learner should discover",
  "html": "<!doctype html>...complete sandboxed activity...</html>",
  "height": 420,
  "fallbackText": "static explanation if the activity cannot run",
  "completionText": "the conclusion revealed after completion",
  "reflectionPrompt": "ask the learner to retell the result with the metaphor"
}
```

The lab HTML must follow
[interactive-labs.md](interactive-labs.md): complete document, required stable
IDs, reset, accessible state feedback, the `deepwhy-lab` postMessage contract,
no unsandboxed parent access, and no network dependency except the pinned
Three.js package for `spatial3d`.

### Branch

```json
{
  "id": "n1-b1",
  "type": "mechanism",
  "question": "optional curiosity question",
  "answer": "one concise sourced answer",
  "sourceIds": ["source-1"]
}
```

Use no more than three per node. Branch IDs are globally unique.

## `videos`

```json
{
  "platformsSearched": ["youtube", "bilibili"],
  "items": [],
  "gap": null
}
```

Every main node references exactly five external videos, and no video ID may be
shared by two nodes. Each video records an
`id`, title, author, platform, URL, publication date, `embedUrl`, duration in
seconds, `thumbnailUrl`, query date, metric status, exact metrics, selection rationale, and
source IDs. The embed URL must point to the matching platform player, not merely
the normal watch page. Null metrics are required when values were not observed.
The selection rationale must state which node it supports and whether it shows
the real phenomenon, an experiment, the node's metaphor, or an alternate
explanation. A six-node page can contain up to 30 video records, but each node's
five-video set always renders as one active player plus four thumbnails.

## `background`

```json
{
  "summary": "one short sentence",
  "people": [],
  "institutions": [],
  "applications": [],
  "timeline": [],
  "frontier": [],
  "gap": null
}
```

This is the secondary “research background” drawer. It may contain enough detail
for investigation, but it is never open on page load.

The selected node's right-side tabs expose contextual entry points to background
people, timeline events, and frontier items that share at least one source with
that node. Both tabs stay filtered to the node's source set.

The right inspector separates this context: Research Background shows people and
institutions, while Industry Development shows applications, timeline events, and
frontier/deployment status. Do not render numeric `S1`/`S2` source chips in
learner-facing panels; source IDs remain in the JSON.

People must include contribution, context, limits, profile URL, and sources.
Institutions must include role, homepage, representative work, and sources.
Applications must include case, value, limitations, and sources.

Timeline items include `date`, `sortDate`, `eventType`, `title`, `description`,
`impact`, and `sourceIds`.

Frontier items include a date, maturity status, technical route, finding,
unresolved issue, and sources.

## `assessment`

```json
{
  "instructions": "Each node has five single-choice questions.",
  "items": []
}
```

Every main node requires exactly five questions. Questions are generated with
their answers: each item has a required main-node `nodeId`, `format: "choice"`,
2–4 options, a valid `correctIndex`, model answer, explanation, rubric, and
sources. The generated page grades locally on selection and immediately shows
green feedback for a correct choice or red feedback for an incorrect choice,
followed by the pre-authored explanation. It never calls a model at runtime and
does not need a separate submit action. Once answering begins, the page shows a
five-question answer card that preserves each correct/incorrect state and links
back to the corresponding question. The final answered question removes the
Next action.

The page also exposes a global quiz using every assessment item across all main
nodes. It shares the same immediate feedback and answer-card behavior as a node
quiz.

## `nextQuestions`

Each item has `question`, `why`, and `sourceIds`. Keep these after the chain or in
the completion state, not as twelve additional main sections. Render each item
as a link to `https://deepwhy.cn/` with `topic` and `question` query parameters.

The generated page requires no DeepWhy account or API. JSON export, the chain,
labs, quizzes, and background dossier all work in the standalone HTML; only the
clickable follow-up questions link to `https://deepwhy.cn/`.
