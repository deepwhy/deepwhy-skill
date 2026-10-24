# Research Playbook

Research is a staged evidence-building process. The goal is not to collect many
links; it is to know which sentence each link can support and where the evidence
stops.

## 1. Build the inquiry frame

Record these before searching broadly:

```json
{
  "topic": "short canonical topic name",
  "question": "the corrected question in one sentence",
  "priorKnowledge": "what the learner likely already recognizes",
  "scope": {
    "included": ["..."],
    "excluded": ["..."]
  },
  "premiseCheck": {
    "status": "confirmed | corrected | uncertain",
    "original": "the user's wording",
    "note": "why it is accepted, corrected, or still uncertain"
  }
}
```

Start from a familiar observation, object, failure, experiment, or question. Do
not begin with a definition dump. For a false premise, say what is useful in the
question, identify the incorrect assumption, and preserve the learner's intent.

Examples:

- "Why is the sky blue only during the day?" is a valid scope but combines two
  related questions: wavelength-dependent scattering and the absence of strong
  atmospheric scattering at night.
- "Why can a phone locate itself when GPS satellites do not know where phones
  are?" corrects the implied one-way tracking model.
- "Was theorem X proved by one person?" should be treated as a priority claim,
  not accepted at face value.

## 2. Choose the domain strategy

### Formal and mathematical topics

1. Identify definitions, assumptions, quantifiers, and the exact theorem
   statement.
2. Search for a canonical proof, a standard textbook, and an authoritative
   encyclopedia entry.
3. Check historical claims separately from the mathematics.
4. Use a small counterexample or limiting case to show what the theorem does
   and does not imply.
5. For a frontier, prefer recent papers on generalization, computation, or
   related open questions; do not call a centuries-old theorem itself "frontier".

### Computer science, AI, and engineering

1. Separate the algorithm/model idea from the system implementation and
   operational deployment.
2. Find the original paper or primary technical report.
3. Find official documentation, benchmarks, or standards for current behavior.
4. Check datasets, compute requirements, evaluation conditions, and failure
   modes.
5. Compare at least two technical routes where the field is contested.
6. Mark benchmark claims with date, task, dataset, and measurement conditions.

### History and social knowledge

1. Establish a chronology from multiple independent sources.
2. Separate event, publication, adoption, and later interpretation dates.
3. Use primary documents where possible and identify institutional context.
4. Attribute contributions carefully; organizations, collaborators, and prior
   work usually matter.
5. Distinguish evidence from later myth-making or retrospective framing.

### Natural science and medicine

1. Find the phenomenon and its measurement before the explanatory model.
2. Prefer review articles and official scientific bodies for orientation.
3. Use original papers for specific claims and note uncertainty, sample, model,
   or experimental conditions.
4. Distinguish correlation, mechanism, and clinical application.
5. Do not present a research hypothesis as established practice.

## 3. Use a research ladder

1. **Orientation:** official overviews, authoritative encyclopedias, or review
   articles to map terms and disputes.
2. **Primary evidence:** original papers, standards, official datasets, patent
   or program documents.
3. **Chronology:** official histories, dated news, publication metadata, and
   institutional records.
4. **Current state:** recent papers, standards, product documentation, and
   authoritative reports with explicit dates.
5. **Boundary check:** counterexamples, limitations, negative results, safety
   requirements, and application constraints.
6. **Teaching check:** one source that explains the idea differently, such as a
   textbook, lecture, or high-quality video, used to catch omissions.

## 4. Maintain an evidence ledger

Write the ledger while researching. Do not invent metadata afterward.

```json
{
  "id": "source-1",
  "title": "exact source title",
  "publisher": "publisher or institution",
  "url": "https://...",
  "kind": "paper | official | reference | standard | book | report | dataset | video",
  "publishedAt": "YYYY-MM-DD or null",
  "accessedAt": "YYYY-MM-DD",
  "notes": "what this source can support and any caveat"
}
```

Use the source's own publication or update date when available. If only a year is
known, store the year only when the schema permits it and say so in `notes`.
Record the query date for live or mutable data.

## 5. Fact-to-source mapping

Before writing a knowledge-chain node or background entry, create a map:

| Claim | Source | Status | Caveat |
|---|---|---|---|
| The phenomenon occurs under condition C | primary paper | verified | narrow sample |
| Event happened on date D | official chronology | verified | page updated later |
| Route B may outperform A | conference paper | research | benchmark only |
| Application is widely deployed | vendor page | partial | no independent audit |

A claim without a mapped source is either rewritten as a clearly marked
question, omitted, or placed in a gap note. Do not "fix" a missing citation by
linking a generic homepage that does not support the specific statement.

## 6. Horizon dates

Maintain a chronology with a deliberate distinction:

- **idea/background:** the intellectual problem or earlier practice;
- **paper/proposal:** the formal publication or technical proposal;
- **prototype:** an experimental system was built or demonstrated;
- **operational:** the capability was accepted, fielded, or used in practice;
- **adoption:** use became widespread or institutionally normalized.

NASA and GPS history illustrate why this matters: a constellation can be
declared operational before later spacecraft generations, signals, and broad
consumer applications arrive. A paper date is not an adoption date.

## 7. Frontline research

For current developments:

1. Search from the most recent year backward.
2. Prefer a dated primary paper, official status page, or current standard.
3. Record the report's data cutoff date.
4. State what is *not* known, including whether a signal or system is still
   pre-operational, unverified, or dependent on future deployment.
5. If the only current source is a vendor or advocacy page, mark the claim as
   partial and exclude aggressive marketing language.

Do not say "state of the art" without a date and a bounded technical field.

## 8. Video research

Search both the subject term and a nearby explanatory phrase. Evaluate:

- topical relevance to the exact learning goal;
- whether the video demonstrates the same scene, metaphor, or mechanism as the
  selected node rather than merely naming the topic;
- whether it supplies something the animation cannot: real scale, an experiment,
  a physical demonstration, or a clearly different explanation;
- speaker or institutional expertise when available;
- recency relative to a fast-changing field;
- views, likes, and comments as context, not a sole ranking signal;
- whether claims are sourced or testable.

Record the query date and each metric separately. A platform can hide or change
metrics, return a challenge page, or block the agent. In that case:

```json
{
  "metricsStatus": "unavailable",
  "metrics": {"views": null, "likes": null, "comments": null},
  "queryDate": "YYYY-MM-DD",
  "selectionRationale": "Related and explanatory, but interaction data could not be verified."
}
```

Never estimate a play count from popularity or invent an account name.

For each selected video, state the learner confusion it resolves and how it
relates to the node's primary metaphor. A generic introduction, clickbait
overview, or unrelated lecture is not a useful teaching video even if it has high
engagement. When nothing relevant is available, keep the animation and record
the gap instead of fabricating a pairing.

## 9. People and institutions

Prefer a person's university, laboratory, national academy, museum, or official
biography. Link to a reliable encyclopedia when an official profile is absent.
Explain the specific contribution and the collaborator or institutional context.

For institutions, use the official homepage and a representative project,
paper, dataset, or product. Do not imply endorsement by merely linking a lab.

## 10. Stop and degrade gracefully

If the evidence is insufficient, keep the main chain honest and move limitations
to the selected node or the background dossier. Use:

- `partial` when a node has useful evidence with a documented limitation;
- `insufficient` when a node cannot support a defensible short answer;
- `not_applicable` when the subject genuinely lacks that dimension.

Make the gap visible to the learner and suggest what evidence would resolve it.
