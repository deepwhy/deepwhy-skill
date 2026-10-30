# Optional Video Export

Read this file only after the user explicitly selects `知识页 + 讲解视频`.

## Contract

Video export reuses the retained AskWhy JSON and generated HTML/media. It must
not replace or weaken the standalone knowledge page.

- Keep the validated HTML and JSON as the source of truth.
- Create a separate HyperFrames project under `videos/<slug>/`.
- Use the HyperFrames `general-video` workflow and follow its preview and render
  approval rules.
- If HyperFrames is unavailable, report the blocker and leave the completed HTML
  intact. Do not fabricate an MP4.
- Do not enter this workflow when the deliverable choice is
  `只生成知识页`.

## Storyboard

Translate the causal chain directly into the video timeline:

1. Open with a title cover built from `center.overviewVisual`.
2. Give each causal node one scene, in chain order.
3. Keep the node's question, one-sentence answer, primary mechanism visual, and
   causal position visible.
4. Include the familiar analogy and its explicit mapping when it helps explain
   the node. State the analogy boundary where the visual could overclaim.
5. Close by pulling back to the full causal chain and its honest evidence
   boundary.

Do not insert sibling topics, external search results, or video recommendations
into the explainer timeline. The external videos on the HTML page are reference
material, not footage to download or republish.

## Narration

Video selection alone does not enable narration. Keep the default video silent
with readable on-screen captions unless the user separately chooses narration.
When narration is requested, use the available media/TTS workflow and keep its
billing and credential confirmations intact.

## Output

Minimum outputs:

- `videos/<slug>/index.html` HyperFrames project;
- `videos/<slug>/STORYBOARD.md` and `BRIEF.md`;
- Studio preview URL for review;
- `renders/<slug>.mp4` only after final approval.

Run the HyperFrames lint/check/snapshot gates before handing over the preview.
The static AskWhy page remains a valid deliverable even if video review or
rendering is not approved.
