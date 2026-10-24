# Design Presets

The page keeps one semantic DOM and JavaScript interaction model. Presets change
the visual world and selected layout details without changing the knowledge chain.

## Automatic selection

Use `deepwhy` by default for every interactive knowledge chain. It is the
OpenMAIC-inspired classroom preset: a near-white dotted stage, cool neutral
surfaces, restrained violet actions, floating rounded panels, and a dominant
interaction bench.

Other presets are explicit alternatives, not automatic topic matches:

| Preset | Visual direction |
|---|---|
| `deepwhy` | OpenMAIC-inspired interactive classroom |
| `atlas` | Scientific field atlas, ivory surfaces, specimen labels |
| `chronicle` | Archival editorial, ruled paper, date stamps |
| `fieldnotes` | Tactile notebook, paper grid, margin notes |

Choose an alternate preset only when the user asks for that visual world or the
topic requires an archival/field-note presentation that the default classroom
metaphor cannot supply. Record the reason in `presentation.rationale`.

The user can override with:

```bash
python3 scripts/build_page.py content.json --style chronicle
```

or:

```bash
DEEPWHY_PAGE_STYLE=atlas python3 scripts/build_page.py content.json
```

## Shared invariants

All presets preserve:

- the same node data and ordering;
- the same desktop node-graph plus learning-bench composition;
- one selected node at a time;
- one active sandboxed lab at most;
- compact node answers;
- keyboard-accessible controls;
- mobile bottom-sheet inspector;
- reduced-motion behavior;
- sources and assessment;
- no DeepWhy account or API requirement; recommended questions may link to the
  DeepWhy platform;
- no external fonts or required network assets.

## Preset behavior

### DeepWhy

Use the OpenMAIC-inspired classroom language: near-white dotted background,
cool neutral ink, a single restrained violet accent, softened floating panels,
rounded action controls, and a central stage where the current lab is the
largest element. It may use one purposeful violet gradient on the primary action,
but no generic neon, heavy glass, or glow effects. The knowledge graph uses the
system six-color node palette, compact inactive cards, and satellite branches.

### Atlas

Use editorial serif display type, grid/graph-paper texture, square specimen cards,
and diagram emphasis. Citations resemble field notes rather than badges.

### Chronicle

Use a newspaper masthead feel, strong horizontal rules, date-like node indexes,
and a timeline-first background dossier. Avoid faux historical artifacts that
obscure text.

### Fieldnotes

Use warm paper, green/blue accents, slight offset card layers, margin-note labels,
and approachable spacing. Do not make the page look childish or reduce contrast.

## Forbidden

- Generating arbitrary CSS per topic.
- Replacing the semantic node graph with an unrelated infographic.
- Using stock photography as the primary explanation of a mechanism.
- Reducing details to unreadably small text merely to avoid page length.
