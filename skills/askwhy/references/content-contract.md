# AskWhy Content Contract

AskWhy uses one center question and a 4–8 step visual causal chain. It is a
compact explanation ladder, not an unordered question explorer or causal DAG.

## Top level

```json
{
  "schemaVersion": "8.0",
  "meta": {},
  "center": {},
  "nodes": []
}
```

## Meta

Required fields:

- `topic`
- `question`
- `slug`
- `summary`
- `category`
- `estimatedMinutes`
- `language`
- `asOf`
- `audience`
- `learningLevel` (`primary`, `middle`, or `high`)
- `evidenceGaps`

## Selected learning level

The content contains exactly one level. Before generation, present `小学`,
`初中`, and `高中` as a required structured choice with no default. Do not ask
for the level as free-form text and do not include alternate-level fields or
variants.

## Center question

```json
{
  "id": "root",
  "question": "Why does the apple fall?",
  "summary": "A short orientation.",
  "insight": "The key idea to carry into all related questions.",
  "tags": ["gravity", "physics"],
  "overviewVisual": {
    "kind": "image",
    "src": "media/overview.svg",
    "alt": "One-diagram summary of the entire causal chain",
    "caption": "The whole explanation at a glance."
  },
  "analogy": {
    "title": "A rope between two wheeled chairs",
    "scene": "A child and a giant sit on wheeled chairs and pull the same rope.",
    "mappings": [
      {"familiar": "child", "concept": "apple"},
      {"familiar": "giant", "concept": "Earth"},
      {"familiar": "same rope", "concept": "mutual gravitational interaction"}
    ],
    "limit": "The rope is a visible pull; gravity is not a physical rope.",
    "visual": {
      "kind": "image",
      "src": "media/analogy/chairs-rope.svg",
      "alt": "A giant and a child pull the same rope while sitting on wheeled chairs",
      "caption": "The shared rope makes both move, while the lighter child changes speed more."
    }
  }
}
```

## Chain step

```json
{
  "id": "joule-heating",
  "parentId": "thermal-radiation",
  "type": "mechanism",
  "question": "灯丝的热又是从哪里来的？",
  "label": "电子碰撞与焦耳热",
  "answer": "电场加速电子，电子与晶格碰撞，把定向能量转成热振动。",
  "summary": "One compact orientation paragraph.",
  "nextQuestion": "灯丝里的电子为什么会定向移动？",
  "knowledge": "Complete node explanation.",
  "facts": ["fact one", "fact two"],
  "tags": ["physics", "mechanism"],
  "analogy": {
    "title": "Electrons bumping through a crowded corridor",
    "scene": "People push through a crowded corridor and lose forward motion in repeated collisions.",
    "mappings": [
      {"familiar": "push from behind", "concept": "electric field"},
      {"familiar": "people", "concept": "free electrons"},
      {"familiar": "crowd collisions", "concept": "electron-lattice scattering"},
      {"familiar": "heat from jostling", "concept": "filament warming"}
    ],
    "limit": "People collide visibly and slowly; electrons obey quantum rules and are not tiny billiard balls.",
    "visual": {
      "kind": "image",
      "src": "media/analogy/crowded-corridor.svg",
      "alt": "A crowd moves through a corridor and collides with columns",
      "caption": "Repeated collisions turn forward motion into scattered vibrations."
    }
  },
  "experiment": null,
  "videoLinks": []
}
```

Constraints:

- `id` is stable lowercase hyphen-case.
- Node IDs are unique and must not be `root`.
- 4–8 nodes.
- The first node uses `parentId: "root"`; every later node uses the previous
  node ID.
- `type` is one of `phenomenon`, `mechanism`, `principle`, `evidence`,
  `foundation`, or `boundary`.
- `answer` is the short answer displayed on the chain and opens the next causal
  gap.
- `nextQuestion` must exactly match the next node's `question`. It is `null` on
  the final node.
- Every node requires `knowledge` and 2–4 `facts`.
- The center requires one `overviewVisual` static image that condenses the full
  page causal path into a single readable infographic. It is displayed in the
  hero and is not a decorative brand illustration.
- The center and every node require one `analogy` object with `title`, `scene`,
  `mappings`, and `limit`.
- `mappings` contains 2–4 objects, each pairing one `familiar` element with the
  `concept` it explains.
- An analogy explains one coherent scene, not several unrelated comparisons.
  Reuse the page-level scene when it remains accurate; otherwise change it
  explicitly.
- `limit` must state where the familiar scene stops matching the real mechanism.
- `analogy.visual` is optional but should be present whenever the familiar scene
  can be drawn without inventing facts. It uses the same image or Manim shape as
  a node visual and appears inside the analogy card.
- Core knowledge should refer back to the analogy mapping instead of leaving the
  analogy as a decorative introduction.
- When `facts` is present, it has 2–4 entries.
- `experiment` is optional:

```json
{
  "title": "Short activity",
  "steps": ["step one", "step two"]
}
```

- `visual` is optional and contains exactly one primary image or Manim animation.

Static image:

```json
{
  "kind": "image",
  "src": "media/node/diagram.svg",
  "alt": "Accessible description of the mechanism",
  "caption": "What the reader should notice."
}
```

Manim:

```json
{
  "kind": "manim",
  "sceneSource": "media/node/node.py",
  "sceneClass": "NodeScene",
  "videoSrc": "media/node-output/node-scene.webm",
  "posterSrc": "media/node-output/node-scene.webp",
  "durationSeconds": 8.6,
  "alt": "Accessible description of the motion",
  "caption": "What changes and why.",
  "transcript": [
    {"start": 0, "end": 2, "text": "The initial state."},
    {"start": 2, "end": 5, "text": "The causal change."}
  ],
  "fallbackSvg": "<svg viewBox=\"0 0 800 450\">...</svg>"
}
```

Assets use local relative paths. The builder inlines them as data URIs for the
standalone page. Remote image URLs are rejected.

- `videoLinks` is optional and contains only real verified URLs:

```json
{
  "id": "video-1",
  "title": "Verified title",
  "url": "https://www.youtube.com/watch?v=...",
  "embedUrl": "https://www.youtube-nocookie.com/embed/...",
  "platform": "youtube",
  "author": "Verified channel",
  "thumbnailUrl": "https://i.ytimg.com/...",
  "durationSeconds": 240,
  "publishedAt": "2026-01-01",
  "queryDate": "2026-10-26",
  "relevanceScore": 86.5,
  "selectionRationale": "Why this clip teaches this exact node."
}
```

No wildcard URLs, search-result URLs, fake titles, or metrics.
`embedUrl` is required and must resolve to the same video as `url`: use
`player.bilibili.com` for Bilibili and `/embed/{videoId}` for YouTube.
`author`, `thumbnailUrl`, `durationSeconds`, `publishedAt`, `queryDate`,
`relevanceScore`, and `selectionRationale` are optional but recommended for
videos discovered through `scripts/search_videos.py`.

The page is a visual explanation surface. External source records are not part
of the content contract.
