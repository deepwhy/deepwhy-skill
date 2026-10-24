# DeepWhy Visual Design System

Every generated learning page must follow these requirements. They are design
constraints, not optional styling advice.

## 1. Design before coding

Before writing HTML, determine and record:

- the central learning question and its emotional or intellectual hook;
- the most important insight the learner should discover;
- the most effective visual representation of that insight;
- the page archetype: `phenomenon_exploration`, `principle_derivation`,
  `historical_evolution`, `cross_domain_connection`, or
  `understanding_assessment`;
- the visual hierarchy and section rhythm.

Do not default to a generic landing page, dashboard, article template, or card
grid.

The content contract expresses these decisions in `presentation`:

```json
{
  "archetype": "phenomenon_exploration",
  "centralInsight": "the discovery the page should make",
  "focalRepresentation": "the lead diagram or visual argument",
  "hierarchy": ["opening", "chain", "selected detail", "background"],
  "sectionRhythm": ["large observation", "compact chain", "evidence", "boundary"]
}
```

`chain.openingVisual` is the dominant opening graphic. Each node's `diagram.kind`
selects a knowledge-appropriate form.

## 2. Composition

- Establish one dominant visual focal point in the opening viewport.
- Compose the desktop page as a learning workbench: a substantial node graph and a
  dominant live lesson bench. Do not make the opening hero the largest surface
  while burying the lab in a narrow sidebar.
- Vary composition according to content purpose.
- Avoid identical card grids across consecutive sections.
- Use diagrams, timelines, comparisons, annotated illustrations, or interactive
  experiments when they explain better than prose.
- Use whitespace intentionally to separate major ideas.
- Keep supporting material visually subordinate to the central chain.
- Give every section a clear purpose and distinct visual role.

The knowledge chain is a sequence of different visual roles, not six copies of
the same card. A force node may use opposing arrows, an equation node a formula
and manipulable variable, a theory node a comparison, and a frontier node an
evidence trace.

Render the chain itself as a graph, not a stack of equal cards:

- use the system node colors: phenomenon green, mechanism blue, principle
  violet, theory amber, frontier red, boundary slate;
- place the active node on the center spine and enlarge it subtly with a
  two-layer outline and low-intensity glow;
- keep non-active nodes compact, with one-line answers and no large visual;
- show branches as satellite cards only after the learner expands them;
- end with a dashed continue-or-verify node;
- use a subtle dotted graph-paper background and a compact node-type legend.

## 3. Motion is part of the explanation

Prefer animation when the learning point is change over time, spatial movement,
causal propagation, an execution sequence, a state transition, flow, or a
feedback loop. A falling object, travelling signal, changing variable, processing
step, growing network, or oscillating wave should move when that movement itself
teaches the mechanism.

Animation must be a teaching beat, not an animated decoration. Build it in four
moves:

1. show the familiar scene or metaphor in a readable starting state;
2. animate the one relationship that explains the current question;
3. change one condition when useful so the learner can see the consequence;
4. settle on a labeled still that names the real concept.

The learner should be able to explain what moved and why it moved before reading
a formal definition. For the apple example, animate a shared pull that moves both
Earth and apple, with the much lighter apple accelerating visibly more; do not
animate a decorative apple without showing the causal relationship.

Prefer an anchor visual that can evolve across nodes. Keep its world, shapes, and
mapping stable, then reveal a new variable or consequence in the next animation.
Avoid replacing the entire visual language at every node.

Use motion only when it carries meaning:

- Animate the causal object or relationship, not decorative background elements.
- Make the metaphor's mapped elements move; keep unmapped scenery still.
- Keep one dominant motion in the current viewport; parallel motion must be
  subordinate and easy to follow.
- Ensure all key frames and the settled state are readable without waiting.
- Make the first and final positions understandable as stills for learners who
  pause or use reduced motion.
- Avoid flashing, continuous high-speed movement, and motion that moves labels or
  controls away from the reader.
- Respect `prefers-reduced-motion`; end SMIL animations at a meaningful settled
  frame rather than hiding the result.

Keep a visual static when it is an equation, comparison table, source inventory,
or a precise annotated construction where motion would add noise. “Animation
where possible” does not mean every element must move.

Pair motion with a verified video when one adds a real demonstration or a second
explanation of the same node. The animation is the controlled mental model; the
video supplies reality, scale, or an independent viewpoint.

## 4. Legibility and occlusion

No generated illustration, diagram, animation, label, callout, tooltip, or
overlay may cover text, annotations, controls, captions, or critical marks.

- Reserve separate label lanes; do not rely on transparency or short overlaps to
  make crowded annotations fit.
- Check text against other text, lines, arrows, nodes, plotted marks, and the
  diagram boundary.
- Put essential labels for raster images in adjacent DOM instead of over the
  image. Generated or atmospheric imagery must not carry must-read text.
- Show knowledge-bearing images in nodes and detail panels in full. Preserve
  their intrinsic aspect ratio and use a contain-style fit; do not use cover
  cropping that removes diagram labels, edges, objects, or other meaningful
  content. Constrain the container and, when needed, open the original in a
  lightbox rather than hiding part of the image.
- If content does not fit, enlarge the viewBox, split the visual, shorten labels,
  or remove secondary detail. Do not shrink type below a readable size.
- Keep captions, formulas, controls, and explanatory prose outside the plotting
  or illustration area.

Review both desktop and mobile rendered output. A clean source SVG is not enough:
responsive scaling can still cause clipping or overlap.

## 5. Classroom visual language

- Use a cool, restrained interactive-classroom language inspired by OpenMAIC.
- Prefer a near-white dotted stage, cool neutral ink, and one violet accent used
  consistently across primary actions and active states.
- Use soft rounded panels and floating control bars. Shadows should be cool and
  low-contrast, not heavy black drop shadows.
- Maintain one palette, type scale, spacing scale, and border system.
- Prefer strong typography, alignment, and whitespace over decoration.
- Avoid excessive rounded cards, nested panels, gradients, shadows, and
  meaningless icons.
- Do not use emoji as a substitute for designed illustrations.
- Diagrams must be readable, accurate, and relevant to the learning objective.
- Ensure responsive clarity on desktop and mobile.

## 6. Content-driven visual forms

- Physical mechanisms: force diagrams, motion sequences, annotated illustrations.
- Mathematics: graphs, geometric constructions, equations, manipulable variables.
- Computer science: architecture diagrams, execution traces, state transitions.
- History: timelines, turning points, competing explanations.
- Complex systems: causal graphs, feedback loops, system maps.
- Assessment: prediction, interactive choices, explanation feedback.

Do not add a visualization merely to fill space. Use the enum
`diagram.kind` to make the intended visual form explicit.

## 7. Interaction quality

Every control must have a meaningful purpose and working behavior. Prefer
interactions that help learners predict, manipulate, compare, test, or explain.
Do not add fake buttons or decorative controls.

At least one knowledge visual must be operable. Choose prediction, a parameter
control, or a two-state comparison based on the concept. The learner's action
should change the result, animation, or feedback in a way that makes the causal
relationship easier to understand. Every interactive visual also needs a
readable static fallback.

Node-level labs use one restrained DeepWhy shell around a sandboxed iframe:
visible goal, one dominant activity surface, state feedback, completion,
reflection, reset, and fullscreen. The shell and iframe follow the injected
OpenMAIC-inspired DeepWhy tokens: near-white stage, soft neutral panels,
restrained violet controls, and cool ink. Controls must not overlap the
visualization or each other.

For a manipulable variable, include its accessible label, range, units or
normalization, initial value, and live result. Verify behavior in a browser.

## 8. Final visual review

Before delivery, inspect the page as a complete composition:

- Is the first viewport distinctive and focused?
- Does the first desktop viewport clearly read as a node graph beside a dominant
  interactive learning bench, rather than a marketing hero above a card stack?
- Is the main insight obvious without reading every paragraph?
- Do sections and knowledge nodes have appropriate visual variation?
- Are diagrams more informative than generic illustrations?
- Does meaningful motion explain temporal or causal relationships where useful?
- Does the animation visibly demonstrate the node's metaphor-to-mechanism
  mapping instead of merely moving for attention?
- Are animated visuals readable in a paused or settled frame?
- Do any labels, shapes, annotations, captions, or controls overlap or clip at
  desktop and mobile widths?
- Are node and detail images fully visible at their intrinsic aspect ratio,
  without cover cropping?
- Does each mechanism/principle node have one functional lab with a visible
  goal, truthful state, completion, reflection, reset, and fullscreen action?
- Is hierarchy clear at a glance?
- Does the page avoid repetitive card-based layout?
- Does mobile preserve the learning experience?
- Do all controls work?

If the result looks like a generic AI-generated SaaS page, redesign the
composition before delivery.
