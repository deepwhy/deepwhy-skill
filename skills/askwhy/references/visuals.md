# AskWhy Node Visuals

A visual earns its space only when it explains the causal relationship faster
than another paragraph. Every node has one primary visual. When motion can
express the mechanism, Manim is the default rather than a fallback to SVG.

## Choose the medium

### Static SVG

Use an inline SVG only when one frame fully carries the idea:

- concept map;
- labeled mechanism diagram;
- before/after comparison;
- spectrum, chart, or geometric relationship;
- energy or force flow that does not need intermediate motion.

SVG is for genuinely static definitions, comparisons, spectra, and charts.

### Manim

Use Manim first when movement or state change can carry the relationship:

- an electron moves, collides, and transfers energy;
- a field pushes charge through a material;
- a trajectory or geometry is constructed;
- heat, force, or pressure propagates over time;
- one state transforms into another.

Do not force a static definition into arbitrary motion. Target 6–15 seconds,
keep essential labels visible throughout, and end on a readable frame.

## Asset rules

- The visual must describe the current node, not the whole page.
- `center.overviewVisual` is the one exception: it intentionally summarizes the
  whole page. Use a static SVG with one dominant causal path and only the labels
  needed to reconstruct the main chain.
- Analogy visuals are a separate optional visual at `analogy.visual`. They show
  the familiar scene and its mapped relationships; node visuals show the real
  mechanism.
- Give an analogy a visual whenever its scene can be drawn without inventing
  facts. Use Manim for flow, collision, pulling, or state change; use SVG for a
  stable scene or comparison.
- Do not use an AI-generated atmosphere image as factual evidence.
- Keep labels large enough for the desktop detail panel and 320px mobile view.
- Include `alt` and `caption`.
- Keep source code and local media beside the content JSON.
- The builder inlines SVG, WebM, and WebP into the final HTML.

Recommended limits:

- image: 2 MiB;
- Manim WebM: 4 MiB;
- poster: 1 MiB;
- all Manim video in one page: 20 MiB.

## Manim workflow

Probe once:

```bash
manim --version
ffmpeg -version
ffprobe -version
```

If Manim is installed, proceed. If it is missing, show the proposed installation
commands and ask for explicit confirmation before changing the machine.

Render:

```bash
python3 scripts/render_manim.py media/node.py NodeScene \
  --output-dir media/node-output \
  --transcript media/node-transcript.json \
  --fallback-svg media/node-fallback.svg \
  --alt "What the motion demonstrates" \
  --caption "The causal lesson stated in one sentence."
```

The renderer produces:

- a VP9 WebM;
- a WebP final-frame poster;
- a `visual` object with duration, transcript, and inline SVG fallback.

The renderer caches outputs by scene source hash, class name, quality, and cache
format version. An unchanged scene returns `cached: true` and reuses its WebM and
WebP without starting Manim or FFmpeg. Use `--force` only when the same source
must be rendered again deliberately.

## Content shape

Static image:

```json
{
  "kind": "image",
  "src": "media/node/diagram.svg",
  "alt": "Labeled explanation",
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
  "alt": "Labeled motion",
  "caption": "What changes and why.",
  "transcript": [
    {"start": 0, "end": 2, "text": "The initial state."},
    {"start": 2, "end": 5, "text": "The causal change."}
  ],
  "fallbackSvg": "<svg viewBox=\"0 0 800 450\">...</svg>"
}
```

## Page behavior

- Show a small diagram or poster on the corresponding chain card.
- Show the full visual at the top of the node detail panel.
- Manim plays muted and looping, with a replay action and live text captions.
- Reduced-motion mode shows the poster and does not autoplay.
- If the video decoder fails, display the static SVG fallback.
