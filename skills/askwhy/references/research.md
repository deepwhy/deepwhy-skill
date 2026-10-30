# AskWhy Research

Verify factual claims for accuracy, but do not generate learner-facing knowledge
source records.

Prefer:

- original papers, standards, and official documentation;
- institutional explainers and textbooks;
- official video channels for external links.

Do not turn a search phrase into a video record. Verify the final page URL and
include only real links. Metrics are optional and are not part of AskWhy's
content contract.

## Video discovery

Run `scripts/search_videos.py` after the node plan and content skeleton exist but
before final prose is locked:

```bash
python3 scripts/search_videos.py content.json \
  --output video-research.json --limit 5
```

The script probes platform roots once, searches every reachable platform, and
uses two queries only when the first shortlist is too small. It retries
transient Bilibili `412` responses. Bilibili-only environments do not search
YouTube unless the user explicitly forces that platform.

Search requests run with bounded concurrency: YouTube may run two requests at a
time, while Bilibili stays on a paced single lane with a persistent session to
avoid `412` rate limiting. Candidate merging, ranking, exclusion, and final
selection remain ordered, so concurrency does not change the selected content.

Candidate scores combine:

- exact concept hits in the title;
- query-term coverage in title, tags, and description;
- educational intent terms;
- trusted channel signals;
- teaching-friendly duration;
- light engagement evidence as a tie-breaker;
- clickbait and off-topic penalties.

The score only reduces the review set. Inspect every node and select the most
useful candidates. For each node, inspect the title, description, tags, author,
duration, and platform. Choose at most two videos whose content addresses the
exact node question. A short experiment that shows the mechanism may be more
suitable than a long general lecture.

Each candidate includes a canonical page URL, embed URL, thumbnail, query date,
ranking reasons, and `suggestedVideoLink`. Before selection, verify that the
embed belongs to the same BVID or YouTube video ID as the canonical page and
responds without a login wall. AskWhy requires the embed URL even though it
retains an external fallback link.

Merge selected records into the content contract; never treat a search page as a
video and never invent missing metadata.

Platform challenges, login walls, missing dates, and metrics stay explicit.
When no suitable candidate exists, keep `videoLinks: []` and report the search
gap.

If a question needs several mutually dependent causes, evidence beyond a
one-paragraph orientation, an experiment sandbox, or a complete answer chain,
route the request to DeepWhy instead of inflating AskWhy.
