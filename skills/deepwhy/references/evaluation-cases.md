# Evaluation Cases

## 1. Mathematical concept

Topic: convergence of an infinite series.

Expect a 4–6 node chain beginning with a partial-sum observation, then definition,
convergence mechanism, proof idea, and validity boundary. The node answer remains
short; derivation belongs in the inspector.

## 2. Computer science or AI

Topic: language-model hallucination.

Expect separated claims about model behavior, training, decoding, retrieval, and
system evaluation. The frontier drawer records paper dates and maturity status.

## 3. Historical or natural-science topic

Topic: plate tectonics or sky color.

Expect a chain rather than a chronology dump. Multiple contributors and
institutions remain in the background dossier. Events and publications keep
separate dates.

## 4. Insufficient frontier evidence

Expect a `partial` or `insufficient` frontier drawer with no invented papers,
dates, or deployment claims. The chain itself still renders.

## 5. Missing video metrics

Expect a verified video title and URL with `metricsStatus: "unavailable"`, all
three values null, and a visible query date. The UI must show “未获取.”

## 5b. Playable video set

Expect exactly five videos for every node, each with a normal page URL, thumbnail
URL, and tested platform embed URL. Opening the video drawer must render in-page players rather than
external-link-only cards. A 200 response from the player endpoint and a visibly
loaded iframe together count as stronger evidence than a watch-page link.

## 6. False premise

Prompt: “Why do GPS satellites track my phone?”

Expect `premiseCheck.status = "corrected"`, a compact correction in the hero, and
a valid chain about broadcast positioning rather than a refusal.

## 7. Knowledge-chain interaction

Expect:

- 4–6 main nodes visible without opening all details;
- node types in nondecreasing depth order;
- card answer length within the contract;
- clicking a node changes the inspector;
- branch chips do not replace or obscure the main trunk;
- branches remain hidden until the learner activates the disclosure;
- previous/next controls work;
- deep text is collapsed by default;
- background content is not visible until opened;
- source-matched people and institutions appear in Research Background;
- applications, timeline, and frontier/deployment information appear in the
  separate Industry Development tab;
- no numeric `S1`/`S2` source chips appear in learner-facing node panels;
- no global “people, timeline, frontier” button appears below the main chain;
- the header has no video-count, research, or theme-switch button;
- each node uses five videos with no overlap against any other node;
- a top global-view switcher exposes combined development history, related
  people, current stage, all video records, and a global quiz;
- global-view content renders in the right-side learning area, not as a modal or
  an entry inside the question-chain canvas;
- recommended questions are links to `deepwhy.cn` carrying topic and question;
- the inspector closes correctly on mobile.
- the explanation panel exposes Understand, Video, Research Background,
  Industry Development, and Check Understanding;
- all four hierarchy anchors are visible in the opening view: question, key
  insight, position, and next action;
- video playback uses one primary player and four thumbnail choices, with one
  iframe loaded at a time.
- every main node has exactly five single-choice questions with pre-authored
  answers and explanations;
- choosing a correct answer turns the selected option and feedback green;
- choosing a wrong answer turns it red, marks the correct option green, and
  reveals the explanation without a submit action;
- a five-question answer card appears after answering and preserves
  green-correct, red-incorrect, and neutral-unanswered states;
- the Next action disappears after answering the fifth question;
- the global quiz spans all 30 questions and uses the same answer card and final
  Next-hiding behavior;
- no whole-chain “verify mastery” button appears in the left completion area.

## 8. Standalone storage

Use a mixed-script special-character topic. Expect the title, hash navigation,
embedded JSON, and JSON export to preserve it. The generated page has no DeepWhy
account or API requirement; recommended questions are explicit deep links to
`deepwhy.cn`. No conversation or local file is uploaded.

For a Manim node, verify the video, poster, and fallback SVG are embedded in the
HTML. The animation appears before the lab; reduced motion prevents autoplay;
the poster, caption, transcript, and explicit replay remain available.

## 9. Visual composition

Use the real prompt “苹果为什么会落地？” and inspect the whole page.

Expect:

- one dominant opening visual showing a falling apple and direction toward Earth;
- content-specific diagrams for force, equation, comparison, and evidence nodes;
- the main chain reads as a node graph with type-colored nodes, a visible
  vertical spine, selected-node emphasis, and satellite branches;
- the chain ends with an explicit continue-or-verify placeholder;
- motion diagrams actually animate the causal movement and remain readable when
  paused or reduced;
- no diagram text, annotation, or essential mark overlaps another label, a
  control, or the diagram boundary at desktop and mobile widths;
- node and detail images remain fully visible with their intrinsic aspect ratio;
- at least one manipulable variable that changes a visible result;
- cool OpenMAIC-inspired classroom palette with a dotted stage, restrained
  violet actions, soft floating panels, and no generic SaaS card grid;
- clear hierarchy with supporting evidence subordinate to the chain;
- a complete mobile composition where the visual focal point and interactions
  remain usable.

If the result resembles a generic SaaS dashboard, article template, or repeated
card stack, it fails visual review even when the data validates.

## 10. Child-friendly progression

Use “苹果为什么会落地？” in a `child` explanation level. Expect:

- every node explicitly bridges from the previous idea;
- only one new central idea per node;
- familiar examples before terms such as “引力波” or “量子引力”;
- formulas after a plain-language rule and numbered intuition steps;
- a micro-check whose reveal is relevant to the current reasoning;
- no unexplained jump from falling apples to spacetime curvature.

## 11. Analogy-first core-node teaching

Use “苹果为什么会落地？” and inspect the relationship node.

Expect:

- one recognizable scene and one coherent metaphor, not a pile of comparisons;
- adjacent nodes reuse and deepen an anchor metaphor when it still applies,
  instead of replacing it with unrelated examples;
- explicit mapping such as giant/child on wheeled chairs ↔ Earth/apple, shared
  rope pull ↔ mutual interaction, unequal movement ↔ mass difference;
- an animation that shows the same causal mapping and settles on readable labels;
- plain-language rule, animation, video, and check all refer to that same mental
  model;
- a verified video that supplies a real demonstration or alternate explanation
  for this exact node;
- at least one operation where the learner predicts or changes a condition and
  receives concept-specific feedback;
- mechanism and principle nodes each contain one sandboxed lab, with adjacent
  labs using different modalities;
- lab completion reveals a free-reflection prompt; the reference conclusion does
  not appear before the learner writes;
- a check asking the learner to retell the idea with the metaphor and a boundary
  explaining that gravity is not literally a rope.

The node fails review if the metaphor is decorative, changes halfway through,
introduces a second unrelated model, or cannot explain the question without
falling back immediately to jargon.

## Completion criteria

- frontmatter and folder name valid;
- all linked references exist;
- schema and semantic validators pass;
- no dangling source IDs;
- no fake video metrics;
- no unchained long-form main body;
- knowledge chain is the primary and functional interaction;
- meaningful motion is animated where it carries the explanation;
- mechanism, principle, theory, and frontier nodes provide a usable, mapped
  teaching metaphor;
- every core node supports retelling through its metaphor plus a boundary check;
- at least one knowledge visual provides a functional learning interaction with
  a visible, truthful consequence;
- every lab runs in a script-only sandbox and exposes state, reset, completion,
  and fullscreen without network access beyond the permitted Three.js package;
- selected videos provide a targeted second explanation or real demonstration;
- all diagrams pass the no-occlusion and reduced-motion review;
- all knowledge-bearing node images pass the no-crop and aspect-ratio review;
- all supporting modules remain reachable;
- tests reported only when run.
