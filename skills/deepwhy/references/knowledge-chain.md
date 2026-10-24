# Knowledge Chain Rules

The chain is the product. Supporting material must help a selected node or remain
behind an explicit “research background” control.

## Shape

Use 4–6 main nodes by default. Three are allowed only for a narrow question that
cannot honestly support a fourth layer.

```text
phenomenon
    ↓ unanswered causal question
mechanism
    ↓ what governs that mechanism?
principle
    ↓ which model or system explains it?
theory or engineering framework
    ↓ what is changing now?
frontier
    ↓ where does confidence stop?
boundary
```

Node types must be nondecreasing in this order:

`phenomenon < mechanism < principle < theory < frontier < boundary`.

Not every type must appear. For example, a historical mechanism may reasonably end
at `boundary` without claiming a current research frontier.

## Each main node

Each node must contain:

- one observable or answerable question;
- one sentence answer, normally 20–60 Chinese characters;
- one concept label of 2–16 characters;
- a usable everyday analogy for every mechanism, principle, theory, or frontier
  node; a phenomenon may use the opening scene itself, and a boundary may use a
  counterexample;
- a short status: `complete`, `partial`, or `insufficient`;
- at least one source for substantive claims;
- an optional diagram, linked videos, and at most three branches;
- a collapsed detail object for deeper explanation and evidence.

The answer should resolve the node's question but expose the next question. Avoid
turning it into a summary of every later node.

The analogy is not a decorative caption. It is the learner's first working
model. It must introduce one coherent familiar situation, map the essential
relationships to the concept, support an animated causal beat, and state where
the metaphor stops being literal.

Prefer a chain-level anchor metaphor that can be reused and extended across
adjacent nodes. Preserve the same scene and mapping while revealing deeper
relationships; introduce a new metaphor only when the old one has reached a
genuine explanatory boundary.

## Progressive disclosure

The default node card shows only:

1. depth type;
2. short concept label;
3. question;
4. one-sentence answer;
5. number of optional branches.

The selected-node inspector owns:

- the familiar scene and primary metaphor;
- the animated mapping between metaphor and mechanism;
- plain-language rule and transfer check;
- deep dive;
- why it matters;
- experiment or proof;
- frontier note;
- mechanism diagram;
- linked video/resources;
- node-level check.

Present the teaching order as scene → metaphor → animation → hands-on lab →
free reflection → plain rule → transfer → video → qualification. Sources and
advanced explanation remain secondary. Do not make the learner read the abstract
mechanism before seeing the mental model that makes it understandable.

At least one visual on the page must let the learner manipulate or predict a
relationship. The interaction belongs to the current question: varying distance
should reveal a distance-dependent consequence, toggling a condition should
compare its outcomes, and a prediction should be answered with concept-specific
feedback. It must not merely repeat a nearby paragraph.

Every mechanism and principle node carries a sandboxed lab. The learner should
observe a consequence, receive a concise completion summary, and explain the
result in their own words before the reference conclusion is revealed.

Never render all deep dives open at once. A learner should be able to scan the
whole chain without reading a long article.

## Branch design

Branches are curiosity paths, not extra main stages. Use zero to three per node.
Good branch questions:

- challenge an assumption;
- transfer the mechanism to another domain;
- ask for a counterexample, limit, or failure mode;
- offer a concrete application.

Bad branches:

- repeat the main next question;
- ask for a generic definition;
- are only answerable after reading multiple unrelated later nodes.

Branch answers are also one concise sentence with sources. The first version
shows one level of branching.

## Suggested opening patterns

### Everyday technology

Start with what the user sees, then reveal the invisible mechanism.

```text
手机没有向 GPS 卫星发送位置 → 卫星广播时间和位置 → 手机用伪距联立方程
→ 时钟与大气误差模型 → 多频信号部署 → 遮挡、干扰和欺骗的信任边界
```

### Natural science

Start with observation, then measurement, mechanism, law, model, and current
limit.

### Formal knowledge

Start with a surprising property or familiar calculation, then definition,
derivation, assumptions, consequences, and scope of validity.

### History and social knowledge

Start with a visible change or dispute, then actors and mechanisms, institutions,
competing interpretations, chronology, and unresolved questions.

## Quality gate

Before building, ask:

- Can a learner state the main chain from node titles alone?
- Does every node answer something the previous node left open?
- Is any card carrying more than two short paragraphs?
- Are the detailed resources one click away rather than on the main surface?
- Does the page show branches without obscuring the trunk?
- Does the final node make a defensible boundary statement?
