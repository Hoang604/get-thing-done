# Domain Reference Research & Deep Research Prompt Builder

> **Execution Override (No Plan Generation)**: **When** the user requests researching or creating an additional domain reference, execute ONLY the protocol in this file (always running both the autonomous web-search subagent and the external Deep Research prompt handover in parallel). Do NOT run the `boundary-plan` workflow and do NOT create `implementation_plan.md` or any plan artifact.

Convert the user's raw domain query into both (1) an autonomous web-search subagent run that researches and writes a domain reference directly, and (2) a structured research prompt for an external research model to execute, matching the user's language across all outputs. Do not answer the user's domain question or introduce domain knowledge outside the user's text when constructing the prompt.

## Core principles

Every sentence you write inside the research prompt is governed by three invariants:

- **Opaque vocabulary (`opaque`)**: Treat every substantive term in the user's input as an indivisible black-box label connected only by domain-free investigative syntax. Test every sentence you write by deleting the user's verbatim words: if what remains still names any domain concept, sub-component, specialist translation, domain classification, or concrete illustration, delete it.
- **Causal blindness (`blind`)**: Treat every unverified outcome, mechanism, and directional claim—including presuppositions embedded in the user's own query—as an open proposition whose validity and boundaries must be determined by evidence. Frame the investigation to test the proposition symmetrically across confirming, disconfirming, and reversing evidence; **when** the query seeks more than a factual inventory, mandate excavating the underlying forces that generate the surface answer without naming any candidate cause or category in advance.
- **Epistemic partitioning (`baseline`)**: **When** the user includes background premises alongside their query, preserve every stated relationship intact and partition the input by epistemic status:
  1. Lock what the user states as established starting conditions or already-ruled-out paths as the **baseline**—instructing the research model to build upon this **baseline** directly without re-verifying or re-proposing ruled-out paths.
  2. Isolate any unverified suspicion or causal assumption voiced by the user as an open hypothesis to test alongside competing explanations.

## Execution protocol

Always execute both Mode 1 and Mode 2 in parallel without pausing to interview the user and without generating any implementation plan:

### Mode 1: Autonomous web-search subagent

Spawn a subagent equipped with web search to research and write the domain reference autonomously: construct the research prompt using the 6 sections in Mode 2 below (with the **Verbatim Reference Standard** appended in full) and pass it to the subagent so it executes the investigation and returns the finished reference and verification tables directly.

### Mode 2: Construct and handover the Deep Research prompt

Construct and output the research prompt for an external research model in the user's language using imperative analytical directives, and append the **Verbatim Reference Standard** block below word-for-word inside the prompt so the external model receives the complete authoring specification in a single self-contained text. Include these exact sections in order:

1. **Context** *(include **when** the user provided background premises)*: Map the complete topology of the user's background intact. Instruct the research model to treat the locked **baseline** as established truth to build upon immediately without re-searching, re-verifying, or re-proposing ruled-out paths, while treating any user-voiced suspicion as an open candidate hypothesis to test alongside competing explanations.
2. **Mission Formulation**: Formulate the core investigative mission strictly from the user's **opaque** vocabulary and **blind** framing—mandating symmetrical testing of any presupposition and excavation of the deeper generative forces that produce the surface answer. Use the field's specialized terminology, notation conventions, and evidence standards without simplification for a domain-literate reader; define foundational premises explicitly before building the argument, and state uncertainty through explicit confidence qualifiers and evidential gaps without translating jargon into everyday language.
3. **Report Structure**:
   - Mandate opening the report with the complete **target reference** (governed strictly by the appended **Verbatim Reference Standard**) that visibly emerges from the topology of evidence uncovered: **when** evidence converges on a determinate answer, state that rule directly; **when** evidence diverges across competing frameworks or depends on boundary conditions, map the landscape of positions and the exact conditions under which each holds.
   - Immediately follow the opening **target reference** with the **Authoring protocol** outputs (**Question map**, and for each open question its **Scaffolding**, **Synthesis**, and **Fit test**) and the full investigation organized organically around the evidentiary chain—moving from foundational premises and primary evidence through each deductive or empirical link to the conclusion.
   - Mandate explicitly that the entire report must be 100% text (prose and Markdown tables only) and must not include any images, generated visual elements, diagrams, `![Image]` tags, or Base64-encoded media anywhere in the output.
4. **Investigative Method**: Mandate two core investigative habits:
   - *Generative excavation*: Analyze the subject's mechanics directly rather than reciting textbook definitions or surface co-occurrences; interrogate conventional explanations against primary evidence to uncover the underlying forces that generate the phenomenon.
   - *Independent falsification*: Frame search trajectories as open questions while remaining **blind** to pre-selected categories; actively seek disconfirming evidence from frames of reference that do not share the primary explanation's assumptions, and identify the exact boundary conditions where emerging explanations break down or reverse.
5. **Logical Honesty**: Mandate *Self-contained rigor*: establish foundational premises and evidentiary links for every claim so the argument contains zero undefined conceptual leaps.
6. **Planner Directive**: Instruct the planner model to bound search scope strictly around the specific **opaque** entities anchored by the user while keeping unanchored dimensions as open investigative questions—imposing no pre-existing taxonomies, no predetermined step-by-step paths, and no superficial keyword lists, and synthesizing findings into a coherent, strictly text-only report governed by `Report Structure` and the appended **Verbatim Reference Standard**.

*Completion criterion*: The constructed prompt contains all applicable sections above in order—verified by the **opaque** deletion test and **blind** symmetry test to contain zero unquoted domain terms, zero concrete illustrations, and zero pre-named causal mechanisms outside user-stated hypotheses—followed verbatim by the entire **Verbatim Reference Standard** block below.

---

## Verbatim Reference Standard (Append Verbatim into Every Generated Prompt)

````markdown
Mathematically, an LLM is trained as a probability machine: its probabilities do not emerge from what is most reasonable or most correct, but are governed by its weights—or more precisely, by the loss function, training dataset, and gradients during training. Therefore, strictly speaking, a model trained to know when to use which concept, and how to use that concept in practice, will be able to do this better. However, input tokens also participate in conditioning the generation of the next token, so even a model not trained in that direction can still work that way by having instructions fed directly into it.

A reference is the instruction fed into input tokens to condition next-token generation: making the model know, for every situation a run can meet, when to use which concept or process, how to use it in practice, and where that process is done, spending the agent's attention only where and when that decision needs it. Below, the **target reference** is the reference being written, updated, or reviewed with this one, and every section applies to every sentence of it.

The principles below are not peers. Two are **roots**: skip one and a family of failures follows. The rest are **independent**: each has its own failure, unrelated to the roots.

| Principle | Failures when it is skipped | Sections |
|---|---|---|
| **Root 1, the decision**: each question gets a judge, a closed or open form, and for an open one a cause, which generality measures | enumeration (checklist, disguised enumeration), overfit, underfit, pseudo-generality, fabricated authority, exemplar anchoring | *Generality*, *Examples* |
| **Root 2, the goal**: each instruction states the state to reach, and each condition can be decided when it must be | negation, premature completion, a rule never reached | *Goals and conditions*, *Reference*, *Authoring protocol* |
| **Independent**: attention spent only where it is needed | sprawl, duplication, contradiction, no-op, sediment | *Words*, *Pruning* |

**Root 1 comes first.** It carries the reference's value: a run meets situations no author saw, and only a general instruction decides them. An agent gets the independent principles mostly right on its own and fails root 1 in almost every first draft; a reference that loses root 1 is worthless whatever else it gets right. Root 2 ranks between them.

**When** a reference shows one of these failures, fix it at the principle in its row: **fix the root, not the symptom**. A root's failures are its symptoms, and reworking a symptom's surface leaves its cause in place: a list rewritten as prose is still enumeration, and a prohibition reworded is still negation. An independent failure is fixed where it shows.

## Generality

Every question the target reference answers goes through one chain: its judge decides whether it gets a rule and whether that rule can be closed; an open rule names a cause; generality measures whether what it names is a cause.

### Judges

A rule is intended only if something outside the agent can tell when it is wrong. For every question the target reference answers, that something is the question's **judge**:

- **a source**, a primary document, standard, or authoritative technical text that can be opened and quoted, whose text states the answer (alongside any locked **baseline** premise provided in the prompt).

A judge's answer reaches the target reference only as the judge's own words, quoted: the source's text with where it sits. An answer credited to a judge without that quote is the author's own judgment dressed as authority (**fabricated authority**), and so is any rule for a question with no judge: no one in the loop can catch it when it is wrong. A question with no judge gets no rule; the target reference stays silent on it and leaves it to the agent's default.

### Closed and open sets

What is right for a question depends on situations no text can list in full, unless the question's judge, in words quoted as *Judges* requires, lists those situations.

- **Closed** (the judge lists them): what is right is fixed, or varies only across the situations the judge lists. Write a literal contract that names each of them and leaves the agent no choice; nothing unlisted needs judgment, so any choice left is variance between runs.
- **Open** (no judge lists them): name the **cause**, whatever decides every situation the text governs, listed or not: the reason an action is right, the trait that makes something a member of a defined term, what makes a condition hold or a step done.

One instruction can be both, a closed form with open content; write each part by its own kind.

### Fit

**Generality** is a relation between an instruction and its cases, not a property of its wording read alone. An author that picks both a situation and its right action imagines the case: the case carries its author's guess at the right action, so an instruction that fits it proves only that it fits the guess—the author has graded its work against itself. A case is an **observed case** when its concrete situation, its right action, and the tempting wrong actions come from the question's quoted **judge** (*Authoring protocol*). Cases test the instruction and stay out of the target reference's text (*Examples*).

An open-set instruction is **general** when it names the cause its cases share, and so, in one sentence, picks the right action in every case it was written from, picks it in a **held-out** case it was not written from, and rules out the tempting wrong action in all of them. Being true in every case is not enough: an instruction that holds everywhere but rules out no wrong action decides nothing. A general instruction is a **generative principle**: compact, and neither overfit nor underfit. The raincoat in *Enumeration* shows all three failures below in one situation.

- Missing the held-out case is **overfit**: the instruction memorized its cases, and the cure is a cause that also decides the held-out case.
- Admitting the wrong action is **underfit**: the instruction does not steer away from it. Detail is sharpness, not count: the cure is to find the word that lets the wrong action through and replace it with a test the agent can run on its own work, one that fails the wrong action and passes the right one; a word that names a recurring idea keeps its place, and the test becomes its definition (*Words*). Added cases are no cure: they turn the instruction into an enumeration.
- Abstract vocabulary hides underfit (**pseudo-generality**): restate the instruction in plain words, and if it then picks no action in a concrete case, it is underfit whatever its wording.

### Enumeration

**Enumeration** is a list standing in for a cause or patching a weak instruction in open-set text. It is overfit by construction: it decides only the items it names, which admits the text around it could not decide them on its own. An agent running it becomes a clerk ticking boxes: it invents relevance for items that do not apply and stops at the edge of the list instead of reasoning from the cause. It shows up in three shapes, and the held-out case exposes all three alike:

- a **checklist**: the items as bullets;
- **disguised enumeration**: the same items folded into a prose clause joined by commas or *or*, which is what a checklist turns into when lists are forbidden;
- a clause that changes the action in only one case: that case written in, however abstract its wording.

**When** an enumeration appears, deleting the list alone leaves the broken wording it was patching, and replacing the list with an umbrella term turns it into **pseudo-generality** (*Fit*). Instead, strip the enumeration and turn its items into **observed cases** in *Scaffolding* (*Authoring protocol*), then run the remaining wording alone against those cases: where it fails to pick the right action or to decide when its condition or goal holds exposes the failure in the table above that the enumeration was patching. Fix the instruction at that principle's row, and verify that the rewritten instruction alone passes both *Fit* across those cases and a **held-out** case, and *Goals and conditions* on the agent's own output. The difference, shown in a situation unrelated to any reference:

- Enumeration: *Pack a raincoat for Da Lat, Sapa, or Hue in the rainy season.*
- Cause: *Pack a raincoat when the forecast shows rain where you are going, on the days you are there.*
- Held-out case, exposing **overfit**: a September trip to Phu Quoc. The list does not name Phu Quoc and packs nothing; the cause reads the forecast and packs the raincoat.
- Wrong action the list lets through, exposing **underfit**: Da Lat in the rainy season, during a dry week. The list packs the raincoat anyway; the cause leaves it home.
- **Pseudo-generality**: *Pack appropriately for the climate.* It sounds general and is true everywhere, but in plain words it says *pack the right things*, which decides neither trip.

A list of rules, each general on its own, is not enumeration: every item names its own cause, and none stands in for a cause that was not found. Such a flat set of peer rules is often the right shape for reference.

## Examples

**When** the target reference prescribes the shape of an output, show the shape with one example of that output, an **anchor**: one example teaches shape more reliably than rules describing it. Set the anchor in a situation any reader understands without domain knowledge, so the only traits it carries are the shape.

**When** an example would sit inside open-set text, leave it out: the reader takes its surface traits for the boundary of the set (**exemplar anchoring**). An example earns a place there only as a guardrail (*Goals and conditions*).

## Goals and conditions

Every instruction states its **goal**, the output or state the agent must reach, in a form the agent can check its own work against.

Every condition the agent must evaluate is stated so the agent can decide it from what it can see at the moment it must decide.

Every open rule opens with **When** and its condition. A rule that does not open with **When** and its condition is read, then never applied at the moment it governs.

**Negation** is steering by prohibition. A prohibition says what is wrong and leaves what is right unsaid, so the agent learns only where not to go. Test a text by deleting its prohibitions: if what remains no longer tells the agent what to produce, the prohibitions were doing the steering. Rewrite each such prohibition as the goal it was guarding, the state in which the forbidden thing does not occur.

A prohibition earns a place only as a **guardrail**: right after the goal it protects, naming a failure that runs carrying that goal still showed, so the agent cannot rationalize its default habit as serving the goal.

## Reference

A **reference** holds material the agent consults when a situation calls for it. Open the target reference with an explicit notice that it is a reference document and that every application of its rules or primitives must be evaluated against the target system's actual architecture, constraints, and requirements to judge whether it fits.

A reference binds **legwork**—the digging the agent does inside the work before it claims done—through a closing **completion criterion** that tells done from not done: the agent gathers the evidence the criterion makes it show, and stops there. So the criterion names evidence covering everything the reference's rules govern: every applicable rule applied to everything it governs, verified before the deliverable is claimed done.

**Premature completion**, ending work before it is done, happens where the criterion leaves done undecided; the defence is a criterion decidable as *Goals and conditions* requires.

## Words

Use an existing word that already carries the meaning, a plain word or a concept the model knows from pretraining. Coin a term only for a meaning that recurs and that no existing word carries; define it where it first appears and use it unchanged after.

A word steers only when the agent can tell whether what it names is present in its own work. A word that names only the degree of a quality cannot be told present or absent: replace it with the observable state that degree should reach.

## Pruning

Every question a run can ask the reference is answered in exactly one place; every other place that touches the question points there, and answers about one concept sit under one heading. Two places answering one question are a defect whether they agree (**duplication**) or disagree (**contradiction**): agreeing copies drift into disagreeing ones on the next edit.

A sentence stays only if you can name a situation in which an agent without it would act differently, and how. If what it asks for is already the agent's default, it is a **no-op**: delete the whole sentence. If it asks for what the agent does not yet do and still fails to produce it, it is underfit: sharpen it as *Fit* and *Words* prescribe. **When** sharpening still does not move the agent's behaviour in runs, delete the addition rather than spending attention on a rule that changes nothing.

A sentence also stays only while it bears on what the reference does now. Sentences that no longer do pile up because adding feels safe and removing feels risky (**sediment**). Deletion is the default for every sentence that fails these tests: rewrite only a sentence whose behaviour the reference still needs, and delete the rest.

## Authoring protocol

1. **Settle the judge**: Find every question the target reference must answer where the agent's default does not suffice, and establish a verbatim quoted ruling from its **judge** (*Judges*) for each question, dropping any question that lacks a quoted ruling from its judge.
   *Completion criterion*: every question the target reference answers has a quoted ruling from its judge.

2. **Fit and write**: Output in the report both the complete **target reference** and its verification tables:
   - **Question map**: a table of every question the target reference answers, its quoted **judge** (dropping any question with no judge), and whether its set is **Closed** or **Open**.
   - For every **Open** question:
     - **Scaffolding**: the observed cases from the quoted judges, each with its concrete situation, the judge-ratified right action, and the tempting wrong actions.
     - **Synthesis**: one instruction naming the cause that makes the right action right and rules out the tempting wrong actions across every case, satisfying every section of this standard and entering the target reference verbatim.
     - **Fit test**: the test of that instruction alone against every case in Scaffolding and one **held-out** case outside Scaffolding, reworking Synthesis on overfit and sharpening wording as *Fit* prescribes on underfit.
   *Completion criterion*: the complete **target reference** (written with each Synthesis verbatim and satisfying every section of this standard), the **Question map**, and every open instruction's **Scaffolding**, **Synthesis**, and passing **Fit test** are output in full.
````
