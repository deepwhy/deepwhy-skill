# Teaching Progression

Default to an intelligent, curious learner who does not yet know the topic's
vocabulary. The measure of success is not that the page mentions every fact. It
is that the learner can retell the core idea with one familiar image, transfer
it to a nearby case, and notice where the image stops being accurate.

## Organize every core node as a teaching scene

Use this sequence before adding technical detail:

1. **Recognizable scene.** Start with something the learner has seen, felt, or
   done: an apple leaving a hand, a lamp dimming with distance, a queue moving,
   or a delivery address finding its route.
2. **One primary metaphor.** Replace the invisible or complex relationship with
   one simple, dynamic situation. A giant and a child on wheeled chairs pulling
   the same rope is a teaching model; a list of five unrelated comparisons is
   not.
3. **Explicit mapping.** State which part of the metaphor corresponds to which
   part of the concept. Keep only 2–4 correspondences.
4. **Animated demonstration.** Show the metaphor doing the causal work: the rope
   tightens, both move toward each other, and the lighter person moves more.
5. **Plain-language rule.** State the concept without jargon, then introduce its
   name.
6. **Video confirmation.** When a verified clip is relevant, use it to show the
   real phenomenon, experiment, or a second visual explanation of this same
   node. The video supplements the mental model; it does not replace it.
7. **Transfer check.** Ask the learner to use the model in a new situation.
8. **Boundary.** Explain where the metaphor is only a model and what it must not
   imply.

The existing content fields carry this structure:

- `analogy`: the one primary metaphor, written so the image is visible;
- `guide.bridge`: the scene or idea already understood;
- `guide.plainLanguage`: the mapping from metaphor to concept;
- `guide.steps`: the causal moves, using the same metaphor;
- `guide.check`: transfer or misconception check;
- `diagram`: the animation that demonstrates the mapping;
- `videoIds`: clips that reinforce this exact node;
- `detail.deepDive` and `detail.frontier`: qualifications after intuition.

## The analogy contract

Every mechanism, principle, theory, or frontier node must have a non-empty,
usable analogy. A phenomenon node can use the opening everyday scene directly.
A boundary node may use a counterexample instead of an extended metaphor.

Prefer one anchor metaphor for the whole page. Let later nodes add a new
relationship, variable, or limit to the same mental scene. One metaphor per node
does not mean introducing a different metaphor at every step. Change the anchor
only when the previous model can no longer explain the next question, and make
that transition explicit.

An acceptable analogy:

- is one coherent model, not a series of disconnected comparisons;
- can be observed without expert vocabulary;
- contains motion, change, choice, or a visible consequence;
- maps only the relationships needed for the current node;
- remains consistent while the learner advances one step;
- includes a short statement of where it breaks.

Reject analogies that are merely decorative, require more background than the
concept, imply a false physical mechanism, or introduce new unexplained jargon.
Do not mix two metaphors in one node.

## Worked example: why does an apple fall?

Do not begin with “gravity is a mutual central force.” Organize the explanation
as follows.

**Scene.** An apple leaves the branch and moves toward the ground.

**Metaphor.** A giant and a child sit on wheeled chairs and pull the same rope.

**Mapping.**

- Earth ↔ the giant;
- apple ↔ the child;
- the pull on the shared rope ↔ gravitational interaction;
- unequal movement ↔ equal force but very different mass.

**Animation.** The rope tightens; both move toward each other by the same force;
the child moves much farther while the giant barely shifts. Freeze on labels:
“same pull” and “different acceleration.”

**Plain rule.** Earth pulls the apple, and the apple pulls Earth. The apple moves
more because it is much lighter.

**Video.** Offer a verified real-world drop, experiment, or visual explanation
that lets the learner compare the model with observed motion. Attach it to this
specific node rather than to a generic introductory playlist.

**Check.** “If the giant also gets pulled, why do we usually notice only the
child moving?” The learner should transfer the mass explanation, not repeat a
definition.

**Boundary.** Gravity is not literally a rope. The rope model explains mutual
pull and unequal acceleration; it does not by itself explain spacetime curvature,
time dilation, or the inverse-square law.

## Vocabulary ladder

Introduce terms in this order:

1. familiar observation;
2. one concrete metaphor;
3. explicit metaphor-to-concept mapping;
4. plain-language rule;
5. named concept;
6. formula or technical representation;
7. caveat and boundary.

A formula must follow the intuition it summarizes. Before using a symbol, say
what it counts or means. Define jargon in the same sentence where it appears.

## Checks that teach with the model

The micro-check should do at least one of these:

- ask the learner to predict the next animated move;
- ask them to explain the same rule using the metaphor;
- change one condition and ask what changes;
- distinguish a likely misconception about the metaphor;
- transfer the model to a nearby example;
- ask where the metaphor stops being accurate.

Reveal a concise answer that restates the causal mapping. Do not use an
ungraded decorative “show answer” control that reveals an unrelated fact.

## Learning by doing

Use an interaction when the learner can discover a relationship by changing one
thing and observing the consequence. Every page needs at least one meaningful
operation; a 4–6 node page should usually include 2–3.

Every mechanism and principle node needs a node-level lab. Choose it from the
knowledge:

- `simulation` to vary quantities and watch a system respond;
- `diagram` to reveal and follow structure, flow, or hierarchy;
- `code` to modify and run JavaScript against visible tests;
- `game` to make decisions, sort, order, or act under a rule;
- `spatial3d` to rotate, zoom, or inspect a spatial object;
- `procedural` to practise decisions and steps with consequences.

Simple prediction, slider, and toggle interactions remain useful inside a node
when a full lab would add no learning value, but they do not replace the lab
required on mechanism and principle nodes.

The interaction must change the learner's mental model, not just the UI:

- change one variable at a time;
- keep the same metaphor visible;
- show the result beside the cause;
- explain both correct and incorrect predictions;
- animate or replay the causal consequence when possible;
- reveal a completion conclusion tied to the learner's observation;
- ask the learner to retell the result through the node's metaphor;
- avoid decorative sliders, fake drag targets, and controls whose result is
  already visible beside them;
- provide a non-interactive fallback with the same explanation.

For the apple example, use a simulation for the mutual pull: the learner adjusts
the two masses, starts the tug-of-war, and observes both bodies move with the
lighter one accelerating more. Use a diagram lab for the inverse-square
relationship so adjacent activities do not repeat the same modality. Each lab
ends with a short free explanation; the reference conclusion is revealed only
after the learner writes.

## Video as a second explanation

Use a video when it adds one of these:

- the real phenomenon at a scale or speed the learner cannot see;
- an experiment that makes the rule credible;
- a visual demonstration matching the current metaphor;
- a second explanation for a learner who did not follow the animation.

Choose the shortest clip that makes this node clearer. One primary video per
node is enough. Record why it belongs to that node. If no verified clip serves
the exact node, say so and let the animation carry the explanation.
Do not use a generic lecture merely to satisfy a video quota.

## When to use Manim

Inline SVG is enough for a simple moving arrow, a state toggle, or a single
trajectory. Manim is warranted when the learner must watch a multi-step
transformation, geometric construction, force interaction, or mathematical
metaphor whose intermediate states are essential.

Do not introduce Manim until the runtime plan has been shown and the learner has
explicitly agreed to installation. On refusal or failure, continue with SVG. A
Manim scene must have a stable poster, a static fallback, concise timed
transcript, and a target duration of 6–20 seconds.

## Evidence without interruption

Keep sources and qualifications visible but secondary. Do not remove necessary
uncertainty to simplify. Say “科学家目前认为” or “这里还没有定论” when that is
the honest explanation.
