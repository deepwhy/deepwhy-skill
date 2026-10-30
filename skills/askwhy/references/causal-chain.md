# Causal Why-Chain Method

AskWhy explains one phenomenon by following the causal link that remains
unexplained after each short answer. It is not a list of related topics.

## The rule for every step

Each step has five parts:

1. `question`: one question about the current causal link.
2. `answer`: one short sentence that resolves enough of the question to reveal
   the next unresolved link.
3. `focus`: the exact noun, action, force, or condition from the answer that is
   still unexplained.
4. `nextQuestion`: one “why” question aimed only at that focus.

The next node's `question` must equal the previous node's `nextQuestion`
verbatim. This is enforced by the validator.

## Construction procedure

1. State the observable phenomenon in ordinary language.
2. Give the nearest visible mechanism, not the deepest theory.
3. Identify one link in that answer that still feels like a leap.
4. Ask why that link occurs. Do not introduce a sibling topic.
5. Answer with the next mechanism and repeat.
6. Stop at a definition, empirical law, axiom, model boundary, or honest unknown.

The chain should feel like:

```text
现象
→ 表层答案
→ 答案中仍未解释的原因
→ 更深一层的答案
→ 更深答案中仍未解释的原因
→ 基础原理或证据边界
```

## Worked example: why an incandescent bulb glows

```text
白炽灯为什么会发光？
→ 因为灯丝被加热到高温，发出热辐射。
仍未解释：为什么高温会产生可见光？
→ 热辐射谱随温度升高而增强，峰值向短波移动。
仍未解释：灯丝的热从哪里来？
→ 电子与晶格碰撞，把电场的功转成热振动。
仍未解释：电子为什么定向移动？
→ 电压建立电场，电场推动自由电子漂移。
仍未解释：电压为什么能推动电子？
→ 电势差让电荷获得可转换的电势能，电场对电荷做功。
仍未解释：电压从哪里来？
→ 电池通过化学反应分离电荷，维持电极间的电势差。
仍未解释：化学反应为什么能持续分离电荷？
→ 反应物和产物的自由能差驱动电子转移与离子迁移。
```

The final step reaches a thermodynamic foundation. A deeper question about why
that reaction direction minimizes free energy would require statistical
mechanics and quantum chemistry, so the page marks it as a boundary instead of
pretending the chain has become intuitive at every scale.

## Familiar analogy at every layer

Each node is explained twice: first through one familiar scene, then through the
actual mechanism. The analogy is a working model, not decoration.

1. Choose one coherent scene the selected stage already understands.
2. Map 2–4 familiar elements to the exact concepts used in this node.
3. Continue the page-level analogy when it still explains the next causal link.
4. Switch scenes only when the old analogy would imply a false mechanism.
5. State where the analogy breaks before the reader treats it as literal.
6. Show the familiar scene when it can be visualized without adding new claims.
   Use Manim when motion carries the mapping, otherwise use a labeled SVG.

For the bulb chain, a page-level water-circuit analogy can connect a pump,
pressure difference, flow, and a narrow rough pipe to a battery, voltage,
current, and the filament. The analogy must stop before claiming that electrons
are water or that one electron travels from the battery to the bulb at light
speed. The page-level visual can animate water circulating through a pump and a
narrow pipe, while the mechanism visual separately shows electrons and lattice
vibrations.

## Choosing the next question

Good next questions reuse the unexplained concept:

- “电子碰撞让灯丝发热” → “电子为什么会移动？”
- “电压驱动电子” → “电压是什么？”
- “电池产生电压” → “电池为什么能持续分离电荷？”

Bad next questions change subject:

- “灯丝为什么发热？” → “谁发明了电灯？”
- “电子为什么会移动？” → “怎样节约用电？”
- “电压从哪里来？” → “灯泡有哪些品牌？”

Those may be useful follow-ups, but they do not belong in the causal chain.

## Multiple causes

Keep one primary chain. If a result genuinely requires multiple causes:

- explain the interaction in the current short answer;
- choose the cause most directly needed to continue the user's question;
- mention a genuinely necessary alternative only inside that node's explanation,
  then continue through the single primary causal path.

Do not turn the main chain into a graph merely because a second cause exists.

## Depth and detail budget

- Use 4–8 nodes.
- Every node gets a full detail panel: core explanation, 2–4 facts, visual when
  useful, and optional video.
- Keep the visible chain answer short, but do not leave later mechanisms as
  unexplained labels. Every layer must be understandable on its own.
- It is better to use fewer well-supported nodes than to add shallow nodes just
  to reach a target count.
- If the next step cannot be supported by evidence, make the current node a
  boundary and state what would be needed to go deeper.
