---
name: askwhy
description: Build a polished standalone visual causal why-chain around one phenomenon, using 4–8 fully detailed steps that pair each abstract mechanism with a familiar analogy while repeatedly asking why toward a foundational cause or evidence boundary. An optional HTML-plus-video mode is selected explicitly after the learning stage. Use only when the user explicitly invokes $askwhy; use DeepWhy when the request needs labs, assessments, and causal branches.
metadata:
  author: AskWhy
  version: "3.2.0"
---

# AskWhy Question Explorer

Turn one question into a compact causal ladder. AskWhy is separate from DeepWhy:

- AskWhy follows one linear “why” chain with 4–8 fully explained steps.
- DeepWhy provides labs, assessments, richer animation, and explicit causal
  branches.

The default output is one standalone HTML file with embedded content and
interactions. A knowledge explainer video is an optional second deliverable.

## Read only what is needed

- Before authoring content, read
  [references/causal-chain.md](references/causal-chain.md),
  [references/content-contract.md](references/content-contract.md) and
  [assets/content.schema.json](assets/content.schema.json).
- Before researching claims and links, read
  [references/research.md](references/research.md).
- Before changing the shell, read
  [references/visual-system.md](references/visual-system.md).
- Before choosing a node diagram or animation, read
  [references/visuals.md](references/visuals.md).
- Before adapting language and concepts to a learning stage, read
  [references/learning-levels.md](references/learning-levels.md).
- Only when the user selects video export, read
  [references/video-export.md](references/video-export.md).
- Use [assets/template.html](assets/template.html) through the builder; do not
  reimplement the page from a blank file.

## Required intake

Collect exactly two upfront choices, in this order, before research or content
generation:

1. **Learning stage:** `小学`, `初中`, or `高中`. There is no default. Always
   present this as a structured choice. If the request already names a stage,
   preselect that option but wait for confirmation.
2. **Deliverable:** `只生成知识页` or `知识页 + 讲解视频`. Default to
   `只生成知识页`. Present this only after the learning stage is confirmed.

Use the host's structured picker or selectable options when available. If the
host has no picker, render a numbered menu and accept a listed number. Never ask
either question as an open-ended text prompt and never infer the video choice
from a previous task.

## Build

1. Use the confirmed learning stage for all generation and store its content
   value (`primary`, `middle`, or `high`) in `meta.learningLevel`. Do not
   generate multiple stage variants.
2. Plan one causal chain using
   [references/causal-chain.md](references/causal-chain.md). The chain starts
   with an observable phenomenon, gives the nearest cause, then asks why the
   most important remaining link in that answer occurs. Continue until a
   definition, law, empirical foundation, or honest boundary.
3. Generate 4–8 fully detailed nodes for the selected stage only. Give the
   center question one page-level analogy, then give every node one coherent,
   familiar analogy with 2–4 explicit mappings and a statement of where the
   analogy stops being accurate. Every node needs a complete core explanation
   and 2–4 facts. Every nonterminal node must state the next unanswered question
   in `nextQuestion`; it must match the next node's question verbatim.
   Whenever the familiar scene can be shown without inventing facts, add an
   `analogy.visual`. Prefer Manim when motion explains the mapping; otherwise
   use a clean labeled SVG.
4. Add one `center.overviewVisual` static SVG that summarizes the whole causal
   chain in a single glance. It must show the actual knowledge path, not repeat
   the question-mark brand art or merely serve as decoration.
5. Draft the content skeleton with empty `videoLinks`, then search real videos
   before polishing each node:

   ```bash
   python3 scripts/search_videos.py content.json \
     --output video-research.json --limit 5
   ```

   The script probes Bilibili and YouTube once, searches every reachable
   platform, retries temporary Bilibili rate limits, scores candidates, and
   writes reviewable `suggestedVideoLink` records. Use
   `--node <id>` to retry one node and `--platform bilibili|youtube|all` only
   when the user explicitly constrains the platform. It searches every node
   with bounded concurrency while preserving the original result order.
6. Review the shortlist for every node. Select at most two videos that best match
   the exact node question; prefer an experiment, demonstration, or clear
   mechanism over a generic topic overview. Do not accept the first result
   blindly and do not reuse one video across nodes.
7. Every node needs a short label, clear question, one-sentence answer, summary,
   one structured analogy, one core explanation, 2–4 facts, 1–3 tags, and an
   optional safe hands-on observation. Selected videos carry author, duration,
   publication date when known, query date, relevance score, rationale, and a
   verified `embedUrl`.
8. Add one primary `visual` per node. Prefer Manim whenever the mechanism can be
   expressed through movement, flow, collision, propagation, force, or state
   change. Use a local SVG only for a genuinely one-frame definition,
   comparison, spectrum, or static chart. Render Manim with
   `scripts/render_manim.py`; the builder inlines the WebM, poster, and fallback.
   Probe Manim once. If it is missing, show installation commands and ask for
   explicit confirmation before installing.
   Once node questions and visual plans are frozen, run video discovery and
   Manim rendering concurrently. Keep at most two CPU-heavy Manim renders
   active at once.
9. Merge each selected `suggestedVideoLink` into that node's `videoLinks`.
10. Validate the final AskWhy content JSON:

   ```bash
   python3 scripts/validate_content.py content.json
   ```

11. Build the standalone page:

   ```bash
   python3 scripts/build_page.py content.json --output page.html
   ```

12. If the deliverable includes video, continue with
    [references/video-export.md](references/video-export.md) only after the
    standalone page passes validation. A video failure must not remove or
    invalidate the completed HTML.
13. For content generation, validate, build, and inspect 1440px and 390px
    layouts. Run the full unit and browser suites only after changing Skill
    scripts, schema, template, or shared assets.

## Content rules

- Do not generate or display external knowledge-source records.
- Every step must answer the previous step’s unresolved causal link. Never jump
  directly from a surface phenomenon to a distant foundation.
- The next question must be a single why-question aimed at one unexplained
  concept in the preceding answer.
- Use one coherent everyday scene per analogy. Map only the relationships
  needed for the current causal layer; do not stack unrelated similes.
- Show the familiar scene when it can be drawn: use `analogy.visual` for a
  labeled image or Manim animation. The visual must picture the analogy itself,
  not merely repeat the abstract mechanism diagram.
- Fill the hero's right side with `center.overviewVisual`: a static,
  self-contained infographic that condenses the full causal chain. Use a
  horizontal flow, vertical stack, loop, or layered hierarchy based on what
  makes this topic clearest.
- Prefer extending the page-level anchor analogy through adjacent nodes. Switch
  to a new familiar scene only when the old one would teach the wrong mechanism.
- State where every analogy breaks, especially when it could imply that a model
  is literally the real system.
- Make analogies appropriate to the selected learning stage. Familiar wording
  must lower the entry cost without hiding a causal step.
- Do not use a search keyword or generic recommendation as a video.
- Never invent video URLs, view counts, authors, or publication dates.
- Use `scripts/search_videos.py` for discovery instead of relying on model memory.
- Reuse an unchanged Manim render through its source-hash cache; do not pass
  `--force` unless the scene must be regenerated deliberately.
- Treat its scores as a shortlist, not a substitute for judging whether the clip
  teaches the exact node question.
- When no suitable verified video exists, omit the video block and record the
  platform/search gap.
- Keep each node compact. Detailed essays belong in another product.
- Do not copy the reference page's unverified video suggestions.
- Preserve the user's scope. Mark unsupported frontiers honestly.

## Page rules

- Use a distinct AskWhy identity and a question-spark mark; do not reuse the
  DeepWhy logo.
- The center question and causal ladder dominate the first viewport.
- Render the chain as a numbered vertical causal ladder on desktop and mobile.
- The root is a prominent start card. Each following step shows its question,
  one-sentence answer, type, and visual preview on a visible causal rail.
- Do not use a radial map or unordered card grid; they encourage sibling topics
  instead of causal progression.
- Do not add a separate “还可以继续追问” strip or side-question navigation. The
  main causal ladder and the detail panel's previous/next controls are the only
  question paths.
- Clicking a step updates the detail panel. The panel exposes previous/next
  navigation backed by `parentId` and `nextQuestion`.
- Show the selected stage as a metadata pill. Do not include a stage selector or
  generate hidden alternate-stage content.
- Render `center.overviewVisual` as the hero's knowledge overview. Do not use a
  generic question-mark illustration. On mobile, show the overview at readable
  full-card width below the question instead of shrinking it to an icon.
- Keep the overview in the same hero surface as the copy, but give it a
  non-overlapping image region. Never place text or another card over the
  infographic, clip it, or fade away meaningful labels.
- Keep the hero compact: avoid large empty top/bottom padding, redundant
  captions, and oversized title gaps. The overview image should earn the space
  it occupies rather than stretch the header artificially.
- Keep at least 20px between the previous/next card row and the core-knowledge
  section on desktop and mobile.
- Every node shows the complete explanation, facts, optional experiment, visual,
  and videos when available.
- Label the video section “视频讲解”, not “核验视频”.
- Show a “换个熟悉说法” analogy card after “这一层的回答” and before the
  previous/next navigation. Present the familiar scene, explicit concept
  mappings, analogy visual when available, and the analogy boundary as a
  distinct visual block.
- Show the full image or animation at the top of the selected node detail.
- A Manim visual plays muted/looping with live caption cues, a replay control,
  and an SVG fallback. Under reduced motion it remains paused on the poster.
- Support hash links such as `#question-joule-heating`.
- The selected node has a visible active state.
- Support copy-question and share-link actions.
- Keep all CSS, JS, and artwork inline.
- Do not require external fonts, scripts, analytics, accounts, or servers.
- Render one inline 16:9 video player at a time. Multiple videos for the same
  node use thumbnail-like selector buttons that swap the iframe source.
- Every video player and selector shows the platform's inline website logo, not
  a text-only platform badge.
- Keep an external “open video” fallback for when an embed is blocked.
- YouTube requires an HTTP(S) page origin. When the standalone file is opened
  directly through `file://`, show a branded fallback and keep the external
  YouTube link; Bilibili can play inline from the local file.
- Do not download or proxy the video stream; the standalone HTML embeds the
  platform player URL only.

## Delivery

Report:

- HTML path;
- retained JSON path;
- selected learning stage and whether video export was requested;
- causal chain length and layout mode;
- network mode, platforms searched, and selected video count;
- whether any Manim renders were served from cache;
- tests actually run;
- unresolved video gaps.

If video export was requested, also report the video project path, preview URL,
rendered MP4 path when approved and completed, and any narration or render gap.

Do not modify unrelated skills or repository configuration.
