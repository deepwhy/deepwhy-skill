---
name: deepwhy
description: Build OpenMAIC-inspired, analogy-first interactive knowledge-chain webpages that make complex questions understandable through familiar scenes, explicit metaphor mappings, sandboxed hands-on labs, targeted video support, and sourced phenomenon-to-boundary explanations. Use for deep topic explainers and "Why First" learning pages. Do not use for simple factual answers, API documentation, or ordinary marketing pages.
license: MIT
metadata:
  author: DeepWhy
  version: "1.0.0"
---

# DeepWhy Knowledge Chain

Create a knowledge exploration experience, not a long-form article with a table of  
contents. The primary surface is a compact, interactive chain of 3–6 ideas that  
progresses from a familiar phenomenon toward a mechanism, principle, theory,  
current frontier, or known boundary.

The learning experience must help the learner understand, not merely receive a
well-sourced explanation. Organize each core idea around one familiar scene and
one usable metaphor. Show that metaphor in motion when change or causation is the
point, then map it back to the real mechanism in plain language. Video is a
second explanation or real-world confirmation for the same node, never a generic
lecture used to fill a quota.

Prefer one chain-level anchor metaphor. Reuse and deepen it across adjacent nodes
whenever it still explains the new question; switch only when the old model has
reached a real boundary. The learner should accumulate one evolving mental model,
not collect unrelated examples from card to card.

The default deliverable is one standalone HTML file. It must preserve a useful  
local experience without a build step: node selection, previous/next navigation,  
branches, detail tabs, timeline filtering, assessment feedback, background
dossiers, and JSON export all use embedded CSS and JavaScript.  
External papers, videos, images, and DeepWhy itself still require a network.

Knowledge-bearing visuals must stay legible: no illustration, diagram, animation,
or overlay may cover text, annotations, controls, captions, or critical marks.
When a relationship is naturally temporal or causal, prefer a purposeful
animation over a static snapshot.

## Read only what the task needs

- Before research, read [references/research-playbook.md](references/research-playbook.md).
- Before planning the chain, read [references/knowledge-chain.md](references/knowledge-chain.md).
- Before designing metaphors, animations, or video pairings, read
  [references/teaching-progression.md](references/teaching-progression.md).
- Before choosing Manim, read
  [references/manim-animation.md](references/manim-animation.md).
- Before authoring a node-level lab, read
  [references/interactive-labs.md](references/interactive-labs.md).
- Before authoring JSON, read [references/content-contract.md](references/content-contract.md)  
  and [assets/content.schema.json](assets/content.schema.json).
- Before choosing or adapting the visual system, read  
  [references/visual-design-system.md](references/visual-design-system.md) and
  [references/design-presets.md](references/design-presets.md).
- Before composing the page shell, read
  [references/learning-layout.md](references/learning-layout.md) and
  [references/page-delivery.md](references/page-delivery.md).
- Before final QA, read [references/evaluation-cases.md](references/evaluation-cases.md).

Start from [assets/template.html](assets/template.html), not from a blank page.  
Use the template and scripts as structural contracts, not as sources of facts.

## Build the learning experience

1. **Frame the learner and the question.** Extract the topic, actual question,  
   likely prior knowledge, and intended depth. Preserve a false premise in  
   `meta.premiseCheck`, mark it `corrected`, explain it compactly, and continue  
   with the corrected question. Do not stop at the correction.
2. **Design the teaching route before researching details.** For every core
   node, identify:

   `recognizable scene → one metaphor → 2–4 explicit mappings → animated causal
   beat → plain-language rule → relevant video → transfer check → metaphor
   boundary`.

   Make the learner retell the idea with the metaphor. Do not move to a technical
   definition until that mental model is visible. Use one metaphor per node and
   carry it consistently through the animation, steps, and check.
3. **Plan the main knowledge chain.** Use 4–6 main  
   nodes by default and 3 only when the topic genuinely cannot support more.  
   Select node types in nondecreasing depth order from:

   `phenomenon → mechanism → principle → theory → frontier → boundary`.

   The opening node must be something the learner can recognize. Every node asks  
   one causal question. Every node answers it in one sentence, normally 20–60  
   characters, and suggests at most three optional branches. The next node must  
   answer the unanswered part of the previous node rather than restating it.
4. **Research each node.** Keep an evidence ledger while researching. Prefer  
   original papers, official pages, standards, textbooks, and institutional  
   reports. Record event dates separately from publication, prototype,  
   operational deployment, and adoption. Mark missing evidence honestly.
5. **Teach one new idea at a time.** Default to
   `meta.audience.explanationLevel = "child"` unless the request specifies a
   deeper audience. Before introducing a term or formula, anchor it in a familiar
   scene and metaphor. Every node must include a bridge, a usable `analogy`, a
   plain-language mapping, ordered causal steps, and a “predict, then reveal”
   check. Mechanism, principle, theory, and frontier nodes require the analogy;
   a phenomenon can use its opening scene directly, and a boundary may use a
   counterexample.

6. **Design active learning operations.** At least one knowledge visual on every
   page must invite the learner to do something, and a 4–6 node page should
   normally include 2–3 such operations. Choose from prediction before reveal,
   parameter manipulation with a live consequence, or a toggle that compares two
   conditions. Bind every interaction to the node's metaphor and update feedback
   immediately; the learner should discover the relationship by acting, not by
   clicking a decorative control. Do not add an interaction that merely repeats
   the answer. Mechanism and principle nodes require a self-contained sandboxed
   lab; choose simulation, diagram, code, game, spatial 3D, or procedural
   practice according to the knowledge. Adjacent labs must not use the same
   modality.
   For assessment, pre-author exactly five single-choice questions for every
   main node. Generate each correct option, model answer, explanation, and
   source list together with the question. Never depend on a runtime model to
   grade. Selecting an option must immediately reveal green-correct or
   red-incorrect feedback plus the explanation; do not require a submit action
   or a whole-chain “verify mastery” button. After the first answer in a node,
   show a five-slot answer card with green-correct, red-incorrect, and neutral
   unanswered states; each slot jumps back to that question. Hide the Next
   action after the fifth question has been answered. Also expose a global quiz
   containing all per-node questions from the top global-view switcher.
7. **Pair animation and video at the point of confusion.** Animate the metaphor
   doing the causal work, then settle on a labeled still. Every knowledge node
   requires exactly five verified external videos. The Video tab presents one
   primary player followed by four thumbnail cards for the remaining videos.
   Selecting a thumbnail swaps the primary player. All five clips demonstrate
   the same node through real phenomena, experiments, or alternate visual
   explanations. Never invent URLs, thumbnails, metrics, or embedding support to
   reach five. Different knowledge nodes must use different video records.
   Expose a global video-library view from the top global switcher, separate
   from each node's five-video set. Keep platform or network-verification gaps in the evidence
   metadata; do not surface them as learner-facing warnings in the Video tab.
   Use inline SVG/SMIL first when it explains the causal move. Only when Manim
   makes a transformation, trajectory, force, or mathematical metaphor
   materially clearer should you plan a node-level Manim scene. Probe the
   runtime only at that point. If setup is needed, run the plan command, show
   its full commands and isolated cache location, and ask for explicit consent
   before running `install --confirmed`. If consent is declined or setup fails,
   use SVG for the rest of this generation and do not repeat the prompt.
8. **Put full explanations behind disclosure.** The node card owns only the  
   question and one-sentence answer. A side inspector may include a short deep  
   dive, analogy, source-backed diagram, evidence, video/resources, and a  
   node-level check. Put source-matched people and institutions in Research
   Background, and source-matched applications, timeline events, and frontier
   deployment status in Industry Development. Keep both tabs filtered to the
   node's source set; never duplicate a global background CTA in the chain
   completion or header area.
   The inspector uses five tabs: Understand, Video, Research Background,
   Industry Development, and Check Understanding.
   Branches stay collapsed until explicitly opened. The video tab loads one
   verified primary player and four thumbnail choices; other players load only
   when selected.
   Do not render `S1`, `S2`, or similar numeric source chips in learner-facing
   node panels. Preserve source IDs in JSON for traceability.
9. **Create the complete HTML.** Put all data in `#deepwhy-data` and render it  
   with the template. Use a reviewed inline SVG for a mechanism diagram when  
   possible. Never present an AI-generated atmosphere image as a factual  
   mechanism. For motion, sequential execution, state change, propagation, flow,
   or feedback, use inline SVG animation whenever movement carries the
   explanation; retain a readable settled state and static text equivalent.
   Show node images in full: preserve the intrinsic aspect ratio and use a
   contain-style fit rather than cropping. Keep essential labels outside raster
   images. Increase the viewBox, split the visual, or remove secondary detail
   rather than allowing overlap. Keep substantive prose and citations out of
   hand-written DOM. On desktop, compose a viewport-height learning workbench:
   a 40-46% node-graph canvas beside a dominant lesson bench. The selected lab and
   reflection belong in the bench. On mobile, return to normal document flow and
   open the bench as a bottom sheet.
   If a node has `manim`, render one muted, looping, playsinline animation above
   the node lab, with its poster, caption, transcript, replay action, and inline
   SVG fallback. Reduced-motion mode must show the poster without autoplay. The
   builder embeds local WebM and WebP assets into the final HTML.
10. **Choose visual direction.** Use `deepwhy` by default: the
   OpenMAIC-inspired classroom language with a near-white dotted stage, cool
   neutral ink, restrained violet actions, floating rounded panels, and a
   dominant interaction bench. `atlas`, `chronicle`, and `fieldnotes` are
   explicit alternatives, not automatic topic matches. `--style` and
   `DEEPWHY_PAGE_STYLE` override the content choice. Presets may change
   typography, color, materials, and layout details; they may not change the
   data semantics or interactions.

   Before writing HTML, record the archetype, central insight, focal visual,
   hierarchy, and section rhythm in `presentation`. Build one dominant visual
   focal point, then vary composition by node purpose. Do not default to a
   landing page, dashboard, article template, or repeated card grid.
11. **Validate the experience.** Run content validation, unit tests, and a  
   Playwright test when available. Confirm that the first screen shows the chain,  
   key insight, current position, and next action; only one node detail and one
   video player are active at a time; branches remain subordinate to the primary
   path; and all background material remains reachable. Inspect every diagram at
   desktop and mobile widths for covered or clipped text, controls, captions,
   essential marks, and cropped image content. Verify that meaningful motion is
   present where it helps explain the idea, settles into a readable frame, and
   respects reduced-motion preferences. Confirm that every core node lets the
   learner retell the idea with its metaphor, transfer it once, and recognize
   where the metaphor breaks. Check that linked videos support the current node
   rather than serving as unrelated background. Exercise every interaction and
   confirm that changing the input produces a visible, truthful consequence.
   Review the complete composition and mobile version. If it resembles a generic
   AI-generated SaaS page, redesign it before delivery.

## Content coverage

The old educational modules are still covered, but they no longer map to 12  
long page sections:

- phenomenon, mechanism, principle, theory, frontier, and boundary become chain  
  node types;
- the familiar scene, primary metaphor, animated mapping, and plain rule live in
  node detail;
- each mechanism and principle node contains one sandboxed hands-on lab followed
  by free restatement and a delayed reference conclusion;
- videos are linked to the exact node they help explain;
- people, institutions, applications, evolution timeline, latest frontier, and  
  source inventory live in the background drawer, with source-matched research
  links inside the relevant right-side node;
- each node's five pre-authored single-choice checks live in its inspector
  Check Understanding tab;
- next questions become branches and chain-level follow-up suggestions; each
  recommendation is clickable and deep-links to `https://deepwhy.cn/` with the
  current topic and recommended question in the URL;
- no account or API is required; the HTML remains useful independently while
  recommended questions may open the DeepWhy platform.

The top global-view switcher is a prominent orientation surface. It renders the
combined development timeline and current stage, related people, the full video
library, and a global quiz spanning all main nodes directly in the right-side
learning area. Do not label it “global learning” and do not place the switcher
inside the question-chain canvas.

Do not make the learner scroll through every supporting module before they can  
follow the knowledge chain.

## Research rules

Prefer primary and official evidence. For each frontier entry record a date,  
source, maturity (`verified`, `research`, or `speculative`), current finding,  
unresolved issue, and competing route. Distinguish a paper from deployment.

For videos, search both YouTube and Bilibili for five directly playable results
per knowledge node, up to 30 distinct records per six-node page. A verified clip
must not be reused across nodes. If fewer verified players exist, record the
evidence gap and do not fabricate filler.
Record the normal page URL and a platform `embedUrl`, then  
verify the embed endpoint itself. Also record title, author, duration,  
thumbnail URL, publication date when available, views, likes, comments, and query date. Use  
`null` and `unavailable` when metrics cannot be observed. Rank videos by  
relevance, explanatory clarity, metaphor or scene match, and how directly they
demonstrate the selected node, ahead of engagement. Record which node confusion
the clip resolves. Do not substitute a watch-page link for a verified embed URL.

Respect access controls, robots policies, paywalls, and copyright. Do not bypass  
authentication or CAPTCHAs, and do not reproduce long source passages.

For people, state a bounded contribution and the collaborators or institutional  
context. Do not reduce a complex development to a single “inventor.”

## Delivery

Use `scripts/build_page.py` and `scripts/validate_content.py`. Report the HTML  
path, retained JSON path, visual preset, tests actually run, embedded Manim
assets or SVG fallback, network-dependent resources, and unresolved evidence
gaps.

If Manim is needed, follow the confirmation sequence in
[references/manim-animation.md](references/manim-animation.md): plan, show the
full command and location, obtain explicit consent, install, render, and verify.
A declined or failed installation falls back to inline SVG/SMIL for the rest of
that generation. Never silently install software.

Do not modify unrelated repository configuration, project licenses, or existing  
skills.
