# Learning Page Layout Rules

These rules are mandatory.

## 1. Obvious first-view hierarchy

The opening view must immediately make four things visible:

1. the central question;
2. the key insight the learner is expected to discover;
3. the current position in the learning journey;
4. the next meaningful action.

Sections and nodes must not all receive equal visual weight.

## 2. Vertical primary path

- Render the main knowledge chain vertically.
- Treat the chain as a small graph: colored type markers, one central spine,
  compact inactive nodes, and satellite branches around the active node.
- Every node has a clear question, a concise answer, and an optional visual.
- Highlight exactly one current node.
- Keep branches collapsed until the learner explicitly opens that node's branch
  disclosure.
- Branch controls must never compete with the primary path.
- Selecting a node does not automatically reveal its branches.
- End the trunk with a dashed continue-or-verify placeholder rather than a plain
  list ending.

## 3. Explanation panel

Desktop is a learning workbench, not a landing page followed by a sidebar:

- left graph canvas, normally 40-46% of the usable workspace: compact
  orientation, node graph, progress, completion;
- dominant right bench: current node question, metaphor, animation, lab,
  reflection, details, video, and next/previous controls.

The workbench fills the viewport below the header. The rail and bench scroll
independently on desktop. The chain must begin within the first viewport; do not
let the opening orientation push all graph nodes below the fold.

The explanation panel has exactly five primary tabs:

- Understand
- Video
- Research Background
- Industry Development
- Check Understanding

Inside Understand, teach in this order:

1. connect to the previous scene;
2. show the node's one familiar metaphor;
3. show the animated mapping;
4. run the node's hands-on lab;
5. ask for a free restatement, then reveal the reference idea;
6. state the plain-language rule;
7. ask the learner to transfer or predict;
8. offer the node's targeted video;
9. reveal formal mechanism and limitations.

Do not put a global “people, timeline, frontier” button under the main chain.
People and institutions belong in Research Background. Applications, timeline
events, and frontier/deployment status belong in Industry Development. Both tabs
are filtered to the selected node's sources.

Do not show numeric `S1`, `S2`, or equivalent source chips in learner-facing
panels. Source IDs remain in the embedded JSON.

The answer can remain in the inspector heading; do not repeat it as another
paragraph before the learner has seen the mental model.

On mobile, use one column plus a detail drawer.

At the mobile breakpoint, remove the fixed workbench height and independent
scroll. Restore normal page scrolling, render the path as the page sequence, and
open the dominant bench as a bottom sheet.

The lab shell stays inline in the detail panel, provides one fullscreen action,
and keeps its controls separate from the visualization. It loads only when its
node is selected.

## 4. Video resources

- Use a provider's official embed URL.
- Every node requires exactly five external videos.
- Video records are unique across nodes. The top global-view switcher exposes a
  combined video library.
- The same top switcher renders the full development timeline and current stage,
  related people, all videos, and the global quiz in the right-side learning
  area. Do not place these controls inside the question-chain canvas.
- Use one responsive 16:9 primary player.
- Show the four non-active videos below the player as thumbnail cards.
- Render only the selected player iframe; replace it when the learner selects
  another thumbnail.
- Keep an external watch-page link as fallback.
- Do not claim playback works until it has been verified in the target browser
  environment.
- Render each chain-level follow-up question as a clickable link to
  `https://deepwhy.cn/` with topic and question parameters.

## 5. Control visual complexity

- One dominant focus per viewport.
- Use consistent spacing, typography, border styles, and radii.
- Avoid nested cards and redundant borders.
- Diagrams explain mechanisms; they are not decoration.
- When change over time or sequence is the mechanism, animate the relevant
  object or relationship rather than freezing it into disconnected snapshots.
- No diagram element, label, annotation, or overlay may cover text, controls,
  captions, or essential marks. Use reserved label space and split crowded
  visuals.
- Keep source, metric, date, and navigation metadata visually secondary.

## 6. Validate before delivery

Check desktop and mobile:

- node selection;
- branch expansion;
- five detail tabs;
- five single-choice quiz interactions per node with immediate green/red feedback
  and explanation;
- a global quiz spanning all main nodes;
- one primary embedded video with four thumbnail choices for switching;
- keyboard navigation;
- overflow, clipped diagram content, and overlapping SVG labels;
- animation behavior and reduced-motion fallback;
- whether the metaphor precedes jargon and stays consistent through the
  animation, steps, video bridge, and check;
- whether the lab state, completion, reflection, reset, and fullscreen controls
  work without overlapping at 320px, 390px, and desktop widths;
- visual hierarchy and dominant focus.

A page is not complete merely because the HTML renders without errors.
