---
name: writing-great-skills
description: Write or update skill
disable-model-invocation: true
---

A skill exists to make a stochastic agent **predictable**, taking the same process every run rather than producing the same output: for every situation a run can meet, its text decides one process, the intended one, and the point where that process is done, spending the agent's attention only where and when that decision needs it. Below, the **target skill** is the skill being written, updated, or reviewed with this one, and every section applies to every sentence of it, frontmatter included.

The principles below are not peers. Two are **roots**: skip one and a family of failures follows. The rest are **independent**: each has its own failure, unrelated to the roots.

| Principle | Failures when it is skipped | Sections |
|---|---|---|
| **Root 1, the decision**: each question gets a judge, a closed or open form, and for an open one a cause, which generality measures | enumeration (checklist, disguised enumeration), overfit, underfit, pseudo-generality, fabricated authority, exemplar anchoring | *Generality*, *Examples* |
| **Root 2, the goal**: each instruction states the state to reach, and each condition can be decided when it must be | negation, premature completion, a rule never reached | *Goals and conditions*, *Steps and reference*, *Splitting*, *Authoring protocol* |
| **Independent**: attention spent only where it is needed | sprawl, duplication, contradiction, no-op, sediment | *Words*, *Placement*, *Pruning* |

**Root 1 comes first.** It carries the skill's value: a run meets situations no author saw, and only a general instruction decides them. An agent gets the independent principles mostly right on its own and fails root 1 in almost every first draft; a skill that loses root 1 is worthless whatever else it gets right. Root 2 ranks between them.

**When** a skill shows one of these failures, fix it at the principle in its row: **fix the root, not the symptom**. A root's failures are its symptoms, and reworking a symptom's surface leaves its cause in place: a list rewritten as prose is still enumeration, and a prohibition reworded is still negation. An independent failure is fixed where it shows. A problem that fits no row is a gap in this skill, to report to the user.

## Generality

Every question the target skill answers goes through one chain: its judge decides whether it gets a rule and whether that rule can be closed; an open rule names a cause; generality measures whether what it names is a cause.

### Judges

A rule is intended only if something outside the agent can tell when it is wrong. For every question the target skill answers, that something is the question's **judge**, and it is one of two kinds:

- **the user**, when the user confirms they can tell a right answer to that question from a wrong one;
- **a source**, a document, standard, or file in the codebase that the agent can open and quote, whose text states the answer.

A judge's answer reaches the target skill only as the judge's own words, quoted: the source's text with where it sits, or what the user said. An answer credited to a judge without that quote is the agent's own judgment dressed as authority (**fabricated authority**), and so is any rule for a question with no judge: no one in the loop can catch it when it is wrong. A question with no judge gets no rule; the target skill stays silent on it and leaves it to the agent's default.

### Closed and open sets

What is right for a question depends on situations no text can list in full, unless the question's judge, in words quoted as *Judges* requires, lists those situations.

- **Closed** (the judge lists them): what is right is fixed, or varies only across the situations the judge lists. Write a literal contract that names each of them and leaves the agent no choice; nothing unlisted needs judgment, so any choice left is variance between runs.
- **Open** (no judge lists them): name the **cause**, whatever decides every situation the text governs, listed or not: the reason an action is right, the trait that makes something a member of a defined term, what makes a condition hold or a step done.

One instruction can be both, a closed form with open content; write each part by its own kind.

### Fit

**Generality** is a relation between an instruction and its cases, not a property of its wording read alone. An agent that picks both a situation and its right action imagines the case: the case carries its author's guess at the right action, so an instruction that fits it proves only that it fits the guess—the agent has graded its work against itself. A case is an **observed case** when its right action comes from the user: either from a run or situation the user already described, or from the user's ruling on a concrete scenario the agent constructed (*Authoring protocol*), where the chosen option becomes the right action and the rejected options become the tempting wrong actions. Cases test the instruction and stay out of the target skill's text (*Examples*).

An open-set instruction is **general** when it names the cause its cases share, and so, in one sentence, picks the right action in every case it was written from, picks it in a **held-out** case it was not written from, and rules out the tempting wrong action in all of them. Being true in every case is not enough: an instruction that holds everywhere but rules out no wrong action decides nothing. A general instruction is a **generative principle**: compact, and neither overfit nor underfit. The raincoat in *Enumeration* shows all three failures below in one situation.

- Missing the held-out case is **overfit**: the instruction memorized its cases, and the cure is a cause that also decides the held-out case.
- Admitting the wrong action is **underfit**: the instruction does not steer away from it. Detail is sharpness, not count: the cure is to find the word that lets the wrong action through and replace it with a test the agent can run on its own work, one that fails the wrong action and passes the right one; a word that names a recurring idea keeps its place, and the test becomes its definition (*Words*). Added cases are no cure: they turn the instruction into an enumeration.
- Abstract vocabulary hides underfit (**pseudo-generality**): restate the instruction in plain words, and if it then picks no action in a concrete case, it is underfit whatever its wording.

### Enumeration

**Enumeration** is a list standing in for a cause in open-set text. It is overfit by construction: it decides exactly the items it names, which admits the cause was not found. An agent running it becomes a clerk ticking boxes: it invents relevance for items that do not apply and stops at the edge of the list instead of reasoning from the cause. It shows up in three shapes, and the held-out case exposes all three alike:

- a **checklist**: the items as bullets;
- **disguised enumeration**: the same items folded into a prose clause joined by commas or *or*, which is what a checklist turns into when lists are forbidden;
- a clause that changes the action in only one case: that case written in, however abstract its wording.

Every shape is a symptom of the same missing cause, so the fix is the cause (**fix the root, not the symptom**). The difference, shown in a situation unrelated to any skill:

- Enumeration: *Pack a raincoat for Da Lat, Sapa, or Hue in the rainy season.*
- Cause: *Pack a raincoat when the forecast shows rain where you are going, on the days you are there.*
- Held-out case, exposing **overfit**: a September trip to Phu Quoc. The list does not name Phu Quoc and packs nothing; the cause reads the forecast and packs the raincoat.
- Wrong action the list lets through, exposing **underfit**: Da Lat in the rainy season, during a dry week. The list packs the raincoat anyway; the cause leaves it home.
- **Pseudo-generality**: *Pack appropriately for the climate.* It sounds general and is true everywhere, but in plain words it says *pack the right things*, which decides neither trip.

A list of rules, each general on its own, is not enumeration: every item names its own cause, and none stands in for a cause that was not found. Such a flat set of peer rules is often the right shape for reference.

## Examples

**When** the target skill prescribes the shape of an output, show the shape with one example of that output, an **anchor**: one example teaches shape more reliably than rules describing it. Set the anchor in a situation any reader understands without domain knowledge, so the only traits it carries are the shape.

**When** an example would sit inside open-set text, leave it out: the reader takes its surface traits for the boundary of the set (**exemplar anchoring**). An example earns a place there only as a guardrail (*Goals and conditions*).

## Goals and conditions

Every instruction states its **goal**, the output or state the agent must reach, in a form the agent can check its own work against.

Every condition the agent must evaluate is stated so the agent can decide it from what it can see at the moment it must decide.

Every rule is reached one of two ways: a step applies it, or it opens with **When** and its condition. A rule reached neither way is read, then never applied at the moment it governs.

**Negation** is steering by prohibition. A prohibition says what is wrong and leaves what is right unsaid, so the agent learns only where not to go; and naming the failure makes it more available: tell the agent not to think of an elephant, and the elephant is what it thinks of. Test a text by deleting its prohibitions: if what remains no longer tells the agent what to produce, the prohibitions were doing the steering. Rewrite each such prohibition as the goal it was guarding, the state in which the forbidden thing does not occur.

A prohibition earns a place only as a **guardrail**: right after the goal it protects, naming a failure that runs carrying that goal still showed.

## Steps and reference

A skill holds **steps**, actions the agent executes in order, and **reference**, material it consults when a situation calls for it; a skill can be either or both.

Every step ends on a **completion criterion** that tells done from not done. The criterion also sets the **legwork**, the digging the agent does inside the work before it claims done: the agent gathers the evidence the criterion makes it show, and stops there. So the criterion names evidence covering everything the step's result depends on; a criterion that covers part of it lets the agent stop after that part. A skill made only of reference binds legwork the same way: every rule applied to everything it governs. The last step's criterion is the deliverable's: the run ends when what its user receives is finished and checked, not when a precondition for producing it is met.

**Premature completion**, ending a step before it is done, happens where the criterion leaves done undecided; the defence is a criterion decidable as *Goals and conditions* requires, then *Splitting* if runs still end early.

## Splitting

Each split adds a skill the user must remember and invoke. **When** runs keep ending a step early although its completion criterion is decidable, and the step makes sense without the details of the steps after it, split the skill right before those later steps.

## Words

Use an existing word that already carries the meaning, a plain word or a concept the model knows from pretraining. Coin a term only for a meaning that recurs and that no existing word carries; define it where it first appears and use it unchanged after.

A word steers only when the agent can tell whether what it names is present in its own work. A word that names only the degree of a quality cannot be told present or absent: replace it with the observable state that degree should reach.

**When** one meaning is spelled out at more than one site, or a passage explains what a pretrained concept already carries, collapse it into a **leading word**: that concept, used wherever the meaning recurs, so the agent reaches for the same behaviour each time it meets the word. Every skill carries restatements a leading word can retire; hunt for them rather than waiting to trip over them. *Fast, deterministic, low-overhead*, restated across a phase, collapses into *tight* (a tight loop); *a loop you believe in* collapses into *red*, which also turns a fuzzy gate into a binary state: the loop goes red on the bug, or it doesn't.

A leading word that does not move the agent past its default is too weak, and the fix is a stronger word, not a different technique: *relentless* where *thorough* changes nothing.

## Placement

Put each piece where exactly the runs that need it read it:

- runs of other skills need it too: a shared file outside any skill;
- otherwise, every run of the skill needs it: SKILL.md;
- otherwise, only some runs need it: a file in the skill folder, named for what it holds.

Material read by runs that don't need it costs them attention (**sprawl**); material a run needs but doesn't read is missing for that run.

**When** material sits in a file outside SKILL.md, reach it with a **context pointer**, one sentence worded *When [condition], read [file] to [goal].* Whether a run reaches the file depends on that wording, not on the file: when a run misses a file it needed, rewrite the condition to name what the run could see at the moment it needed the file, before pulling the material back into SKILL.md.

## Pruning

Every question a run can ask the skill is answered in exactly one place; every other place that touches the question points there, and answers about one concept sit under one heading. Two places answering one question are a defect whether they agree (**duplication**) or disagree (**contradiction**): agreeing copies drift into disagreeing ones on the next edit.

A sentence stays only if you can name a situation in which an agent without it would act differently, and how. If what it asks for is already the agent's default, it is a **no-op**: delete the whole sentence. If it asks for what the agent does not yet do and still fails to produce it, it is underfit: sharpen it as *Fit* prescribes, or strengthen its leading word (*Words*).

A sentence also stays only while it bears on what the skill does now. Sentences that no longer do pile up because adding feels safe and removing feels risky (**sediment**). Deletion is the default for every sentence that fails these tests: rewrite only a sentence whose behaviour the skill still needs, and delete the rest.

## Invocation

Every skill is user-invoked: its frontmatter sets `disable-model-invocation: true`, and its `description` is a summary for the human who invokes it.

## Authoring protocol

1. **Settle the judge**: Find every question the target skill must answer where the agent's default does not suffice, and every passage in an existing target skill that fails a principle in this skill. **When** any such question or fix lacks a quoted ruling from its judge, call `ask_question` before drafting or editing:
   - Each question states the exact context that raised it (quoting the conflicting or broken passage of the existing skill, or naming the gap where the agent's default fails in a new skill) and places the user in a concrete scenario a run can meet, so the user can judge it from the question alone without guessing what is being asked.
   - The options are distinct, competing actions the target skill could take in that scenario, each stating the behaviour it produces and its consequence.
   *Completion criterion*: every question the target skill answers has a quoted ruling from its judge; if `ask_question` was called, the turn ends to await the user's answer before Step 2 runs.

2. **Fit and write**: Output to the conversation, then write to `SKILL.md`:
   - **Question map**: a table of every question the target skill answers, its quoted **judge** (dropping any question with no judge), and whether its set is **Closed** or **Open**.
   - For every **Open** question:
     - **Scaffolding**: the observed cases, each with its concrete situation, the judge-ratified right action, and the tempting wrong actions (the rejected options from Step 1 or the failures observed in runs).
     - **Synthesis**: one instruction naming the cause that makes the right action right and rules out the tempting wrong actions across every case.
     - **Fit test**: the test of that instruction alone against every case in Scaffolding and one **held-out** case outside Scaffolding, reworking Synthesis on overfit and sharpening wording as *Fit* prescribes on underfit.
   *Completion criterion*: the question map and every open instruction's Scaffolding, Synthesis, and passing Fit test are shown in the conversation, and `SKILL.md` is written satisfying every section of this skill.
