# Interactive Labs

Use a lab when the learner can discover the node's causal relationship by doing
something. A lab is a complete activity inside DeepWhy's knowledge chain, not a
decorative animation and not a dressed-up multiple-choice question.

## When a lab is required

- Every `mechanism` and `principle` node requires a lab.
- `phenomenon`, `theory`, `frontier`, and `boundary` nodes may add one when the
  concept has a variable, structure, procedure, or decision worth exploring.
- A 4–6 node page normally has 2–3 labs.
- Adjacent lab-bearing nodes must use different `lab.kind` values.
- The lab must serve the current question. A distance slider belongs in a
  distance/force node, not in every mechanics topic.

## Choose the lab type

| `kind` | Use when the learner should | Minimum learning action |
| --- | --- | --- |
| `simulation` | vary a quantity and watch a system respond | change one input, run/pause/reset, observe a visible result |
| `diagram` | inspect structure, flow, hierarchy, or sequence | reveal/follow nodes, inspect a relationship |
| `code` | test an algorithm, rule, or transformation | edit and run JavaScript with visible tests |
| `game` | make repeated decisions under a rule | perform an action/puzzle and see progress or consequences |
| `spatial3d` | inspect a spatial object or geometry | rotate/zoom/decompose the object |
| `procedural` | practise an ordered operational task | make a decision or measurement and see a consequence |

Do not use `game` for an ordinary quiz. Do not use `code` merely to show source.
Do not use `spatial3d` when a labelled two-dimensional diagram explains the idea
more clearly.

## Data contract

Add `lab` to the node:

```json
{
  "kind": "simulation",
  "title": "拖动质量，观察谁先移动",
  "goal": "找出拉力相同、质量不同时，两人的运动有什么差别",
  "html": "<!doctype html>...complete document...</html>",
  "height": 420,
  "fallbackText": "同样拉力下，质量越小，加速度越大。",
  "completionText": "地球与苹果受到的拉力成对出现；苹果更轻，所以移动得更明显。",
  "reflectionPrompt": "用轮椅拉绳的比喻，解释苹果和地球为什么运动幅度不同。"
}
```

`height` must be an integer from 320 to 720. The parent supplies the lab shell,
goal, fullscreen action, completion state, reflection input, and static fallback.

## Required document contract

The lab `html` must be a complete, self-contained document containing:

- `<meta name="viewport">`;
- one `#lab-root`;
- visible `#lab-state` and `#lab-feedback`;
- a working `#lab-reset`;
- at least one primary learning control;
- one visible primary visual surface;
- a `window.parent.postMessage` call with the state contract below.

Stable skeleton:

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body>
  <main id="lab-root">
    <section id="lab-visual" aria-label="实验可视化"></section>
    <div id="lab-state" aria-live="polite"></div>
    <div id="lab-feedback" aria-live="polite"></div>
    <button id="lab-reset" type="button">重新开始</button>
  </main>
  <script>
    function publishState(complete, summary, state) {
      window.parent.postMessage({
        source: "deepwhy-lab",
        type: "state",
        complete,
        summary,
        state
      }, "*");
    }
  </script>
</body>
</html>
```

Publish the initial state during setup, then again after every semantic change,
including reset and programmatic changes. Use one central state object and one
render/publish path. The parent ignores messages from anywhere except the active
lab iframe.

## Security and dependencies

The parent renders the lab in:

```html
<iframe sandbox="allow-scripts" referrerpolicy="no-referrer"></iframe>
```

It adds a restrictive CSP:

- inline CSS and JavaScript are allowed;
- `data:` and `blob:` images/media are allowed;
- network connections are blocked;
- Three.js may load only from the pinned jsDelivr package.

Do not add authentication, uploads, geolocation, parent DOM access, external
fonts, analytics, or arbitrary remote libraries. JavaScript code-runner labs use
`unsafe-eval` only inside this isolated iframe.

The only permitted remote script is Three.js `0.160.0`:

```html
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
  }
}
</script>
```

Always provide a working static or CSS/SVG fallback. A failed CDN must not leave
an empty lab.

## Required visual and interaction rules

- Use the injected DeepWhy tokens: `--lab-bg`, `--lab-surface`, `--lab-text`,
  `--lab-muted`, `--lab-accent`, `--lab-accent-2`, `--lab-border`,
  `--lab-display`, `--lab-sans`, and `--lab-mono`.
- Keep the OpenMAIC-inspired classroom feel: near-white stage, cool ink,
  restrained violet controls, soft rounded panels, and clear state hierarchy.
  Avoid generic neon, heavy glass, and decorative glow.
- Keep one dominant visual and one primary motion in a viewport.
- Every control is at least 44px high and usable with mouse, touch, and keyboard.
- Keep controls outside the visualization or in a non-overlapping bottom sheet.
- At 320px, 390px, and 768px, stack controls and preserve a usable visual area.
- State text must describe the learner-visible situation, not JavaScript
  variable names.
- Feedback must explain a consequence, not merely say “正确” or “错误”.
- Reset restores all learner state and publishes the reset state.
- Respect `prefers-reduced-motion`.
- Use `font-variant-numeric: tabular-nums` for changing numbers.

## Type-specific requirements

### Simulation

- One to three variables, each with a learner-facing label, range, step, unit,
  default, and current value.
- Start/pause and reset controls.
- Observable motion or plotted change when a variable changes.
- A state display with current inputs and outcome.
- Presets may demonstrate contrasting conditions; applying a preset resets the
  simulation before running.

### Diagram

- Nodes must have stable IDs and visible labels; edges must reference existing
  nodes.
- Reveal or inspect at least one relationship through a learner action.
- Do not use CSS transforms that erase SVG positioning transforms.
- Keep arrowheads outside node boxes and avoid label/edge collisions.
- Provide a reset to the initial reveal state.

### Code

- Execute JavaScript only.
- Provide starter code, a run action, visible output, and at least one test.
- Never claim that Python, Java, C++, or another runtime executes locally.
- For non-JavaScript topics, use prediction or execution-trace labs instead.
- Keep user code inside the sandbox; never send it to a network service.

### Game

- Use action, sorting, sequencing, matching, or decision consequences.
- Do not turn a multiple-choice quiz into a “game” without changing the
  interaction model.
- Start in a safe state; do not fail the learner before they act.
- Show progress, feedback, and reset.

### Spatial 3D

- Support rotate plus zoom controls; pointer drag alone is insufficient.
- Keep object labels readable from the default view.
- Use the pinned Three.js CDN only when CSS 3D or SVG projection is inadequate.
- If Three.js fails, show the fallback scene and explanation without leaving a
  blank canvas.

### Procedural

- Include ordered steps, a decision or measurement, progress, and reset.
- At least one wrong or unsafe choice must cause a meaningful consequence.
- Reset must clear progress and restore the initial safe state.
