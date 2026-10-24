# Manim Animation

Use Manim when motion is the explanation: a transformation, force, trajectory,
geometry, timing sequence, or metaphor cannot be understood as clearly from one
still image. Do not use it as decoration or on every node. Prefer inline SVG
when a short SMIL animation already shows the causal move and remains readable
without motion.

The standalone HTML remains the primary deliverable. Manim is optional, and a
page must remain useful without the DeepWhy system, a network connection, or a
working video decoder.

## Ask before installing

Probe only after deciding that a node needs Manim. Loading the Skill is not
permission to install anything.

```bash
python3 scripts/manim_runtime.py probe --json
python3 scripts/manim_runtime.py plan --json
```

Show the learner the planned package-manager and Python commands, the isolated
cache location, the Manim version, and the expected system dependencies. Ask one
direct confirmation question that names the install location. Only then run:

```bash
python3 scripts/manim_runtime.py install --confirmed --json
```

The installer creates an isolated per-user runtime, runs a render smoke test,
and records the result in the cache. It supports macOS, Linux, WSL, and Windows
when the documented package managers are present. Never add `--confirmed`
without a fresh affirmative response in the current conversation. If the learner
declines, do not ask again during that generation. If installation fails, report
the failed step and continue with SVG/SMIL.

## Render a node

Write one short scene for the exact node metaphor. Keep essential labels in the
scene and leave enough safe margin that nothing is clipped at the page's display
size. Supply a final-frame poster, a static SVG fallback, accessible alt text,
a concise caption, and timed transcript cues.

```bash
python3 scripts/manim_render.py path/to/node_scene.py NodeScene \
  --output-dir media/apple-node \
  --transcript path/to/node_transcript.json \
  --alt "大小人与小孩拉绳，轻的一方移动更多" \
  --caption "同样的拉力下，较轻的一方加速度更大。" \
  --fallback-svg path/to/node_fallback.svg
```

The transcript JSON is an ordered, non-overlapping array:

```json
[
  {"start": 0, "end": 3, "text": "两个人拉住同一根绳。"},
  {"start": 3, "end": 7, "text": "绳子的拉力同时作用在双方身上。"}
]
```

The renderer converts the MP4 to WebM, extracts the final frame as WebP, checks
the duration and size, and prints a `node` object for the content JSON. Build the
page with `scripts/build_page.py`; the builder embeds both local media files as
data URIs so the final HTML can be shared by itself.

```json
"manim": {
  "sceneSource": "media/apple-node/node_scene.py",
  "sceneClass": "NodeScene",
  "videoSrc": "media/apple-node/node-scene.webm",
  "posterSrc": "media/apple-node/node-scene.webp",
  "durationSeconds": 8.4,
  "alt": "大小人与小孩拉绳，轻的一方移动更多",
  "caption": "同样的拉力下，较轻的一方加速度更大。",
  "transcript": [
    {"start": 0, "end": 3, "text": "两个人拉住同一根绳。"}
  ],
  "fallbackSvg": "<svg viewBox=\"0 0 800 450\">...</svg>"
}
```

Paths are relative to the content JSON. Keep a target of 6–20 seconds; the hard
limit is 30 seconds. Keep the WebM at or below 8 MiB and the poster at or below
1 MiB. Shorten the scene or remove secondary detail before increasing the limit.
The generated page plays muted and looping, exposes controls and a replay
action, and does not autoplay when reduced motion is requested.

## Manim is unavailable or declined

Continue with inline SVG/SMIL and a readable settled frame. Do not mention an
installation failure in learner-facing content, and do not add a DeepWhy
account, API, or website CTA as a fallback. Explain the same causal beat in the
node text, guide steps, and hands-on lab.
