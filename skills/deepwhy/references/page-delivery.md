# Page Delivery

Follow [visual-design-system.md](visual-design-system.md) before implementation.
Composition must be derived from the learning insight, not selected from a
generic page template.

## Required experience

Generate one standalone HTML file. The landing view must show:

- one dominant, content-derived visual focal point;
- a compact title and opening scenario;
- the knowledge chain itself;
- selected-node controls and short answers;
- one inspector on desktop;
- a compact “research background” entry.

Do not generate a long article with a chapter navigator. The chain is the primary
navigation.

The first desktop viewport must read as an active learning workspace:

- compact orientation and the visible node graph in the left canvas;
- the selected node's substantive teaching surface on the dominant right side.

The lab must be the visual center of mechanism and principle nodes, not a narrow
sidebar widget beneath a large marketing hero.

The selected-node experience must teach in this order:

`familiar scene → one metaphor → animated causal mapping → hands-on lab →
free reflection → plain-language rule → transfer check → relevant video →
boundary`

The video and animation must describe the same node-level idea. Sources, history,
and technical exceptions remain secondary rather than preceding the intuition.

## Composition

- Use cool near-white surfaces, a subtle dot grid, restrained violet actions,
  and soft floating panels inspired by OpenMAIC.
- Vary node composition by `diagram.kind`; repeated identical cards cannot be
  the only visual rhythm.
- Use diagrams, comparisons, equations, evidence traces, or manipulable
  variables only where they advance the learning objective.
- Use animation when motion, sequence, state change, propagation, or feedback is
  itself part of the explanation; keep the static key frames understandable.
- Animate the metaphor's mapped elements, not decorative scenery. Resolve into a
  labeled still that states the real concept.
- Put a direct bridge from the animated explanation to the node's video when a
  verified clip adds a real demonstration or a second explanation.
- If a node uses Manim, place the muted animation before its hands-on lab with a
  poster, caption, transcript, replay control, and static SVG fallback.
- Give the learner at least one operation that changes a condition and exposes a
  truthful consequence. Use prediction, parameter manipulation, or a two-state
  toggle according to the content.
- Mechanism and principle nodes use a sandboxed node-level lab. Embed it after
  the animation and before formal wording; reveal the reference conclusion only
  after the learner writes a short explanation.
- Do not let illustrations, diagram shapes, labels, callouts, animations, or
  overlays cover text, controls, captions, or critical marks.
- Show node images in full with their original proportions; use a contain-style
  fit and a lightbox for detailed inspection rather than `cover` cropping.
- Keep detailed prose collapsed and background information in the dossier.
- Remove decorative gradients, glass panels, excessive shadows, emoji, and
  controls without a learning purpose.

## Layout

Desktop:

```text
┌ header: topic / progress ────────────────────────────────────┐
├──────────────────┬───────────────────────────────────────────┤
│ compact framing  │ selected node question                    │
│ vertical path    │ metaphor / animation / sandboxed lab       │
│ progress         │ reflection / details / video               │
│ completion       │ previous / next                            │
└──────────────────┴───────────────────────────────────────────┘
```

Use a 40-46% graph canvas and a 54-60% fluid bench. Both occupy the viewport
height below the header and scroll independently. At widths below 880px, collapse
to a normal document and open the bench as a bottom sheet.

The graph canvas must use type-specific node colors, a visible center spine,
compact inactive nodes, a highlighted active node, collapsed satellite branches,
and a dashed terminal placeholder. Do not render the main path as six identical
full cards.

Mobile:

- chain becomes a compact vertical sequence;
- node cards show question and one-sentence answer;
- selecting a node opens a bottom-sheet inspector;
- background material remains in a full-screen dialog;
- touching outside or a close button dismisses the inspector;
- no horizontal page overflow.

## Interaction

- Node click selects a main node.
- Branch click selects a branch in the inspector without changing the trunk.
- Branches stay collapsed until the current node's branch disclosure is opened.
- Previous/next controls move through main nodes.
- Hash URLs such as `#node-n3` select a node.
- Inspector tabs are exactly `理解`, `视频`, `研究背景`, `行业发展`, and
  `检查理解`.
- The `理解` tab presents metaphor and animation before abstract steps and deep
  explanations.
- Learner interactions provide immediate, concept-specific feedback and remain
  usable by keyboard and touch.
- Labs run in `allow-scripts` sandboxed iframes without same-origin access. Only
  one lab iframe is active, and its state messages update the parent shell.
- Every node's video panel loads one primary 16:9 player and a five-item
  set of choices: the active player plus four thumbnail cards for the remaining
  videos. Selecting a thumbnail replaces the selected iframe;
  off-screen videos do not create additional players.
- Network or platform verification gaps stay in metadata; do not render them in
  the learner-facing Video tab.
- The “research background” dialog has people, institutions, applications,
  videos, timeline, frontier, and sources.
- Node-relevant people and institutions live in Research Background. Applications,
  timeline, and frontier material live in Industry Development. Both are filtered
  to the selected node's sources.
- Numeric `S1`, `S2`, or equivalent source chips are not rendered in node panels.
- The timeline is filterable and expandable.
- A prominent top global-view switcher exposes combined development history and
  current stage, related people, the complete video library, and the global quiz.
  Its content renders in the right-side learning area, not in the question-chain
  canvas. Node video tabs remain limited to their own five records.
- Each node has exactly five generated single-choice questions. Choosing an
  option immediately shows green-correct or red-incorrect feedback and its
  pre-authored explanation. There is no submit step, runtime model call, or
  whole-chain verify-mastery button. An answer card below the question tracks
  all five states; after the final answer the Next action disappears.
- The global quiz uses all generated questions and the same answer-card and
  final-question behavior.
- JSON export remains available. Recommended questions link to the DeepWhy
  platform with the current topic and question query parameters.

## Density

- The main card must not contain the deep dive.
- Do not show more than one node inspector at a time.
- The hero must not repeat the chain title, question, summary, and scope.
- Use `details` or tabs for deeper content.
- The first viewport must contain chain nodes, not a multi-paragraph introduction.

## Accessibility

- Use semantic headings and buttons.
- Maintain focus visibility.
- Announce inspector/quiz updates with `aria-live`.
- Use `aria-pressed` or tab semantics correctly.
- Support Escape to close overlays.
- Respect `prefers-reduced-motion`.
- Settle animated SVGs into a readable final frame when reduced motion is
  requested.
- Do not autoplay Manim video when reduced motion is requested; keep its poster,
  caption, transcript, and explicit replay control available.
- Provide text equivalents for diagrams.
- Ensure ranges, buttons, tabs, and branch controls perform real work.

## Build and test

```bash
python3 scripts/validate_content.py content.json
python3 scripts/build_page.py content.json --output page.html
python3 tests/test_deepwhy.py
node tests/browser_test.mjs page.html
```

Use `--style` for a deliberate visual override. Run the browser test at desktop
and mobile widths. Check that diagram annotations and text do not intersect or
leave their visual boundary, and that any meaningful animation still has a
readable static state. Verify that node and detail images remain fully visible
at their intrinsic aspect ratio. Check that each core node can be retold through
its metaphor, that the animation shows the intended causal mapping, and that
videos support the selected node rather than acting as unrelated filler. Exercise
every interaction and confirm that changing the input produces a visible,
truthful consequence. Verify lab sandboxing, completion state, reset,
fullscreen, reflection, and reference reveal. Report skipped browser tests
honestly.

Before delivery, inspect the complete composition and answer the final review
questions in [visual-design-system.md](visual-design-system.md). If it looks like
a generic AI-generated SaaS page, redesign it.
