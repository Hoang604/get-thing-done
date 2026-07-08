---
name: doc-coauthoring
description: Guide users through collaborative document creation (technical specs, PRDs, design docs, decision docs, proposals). Trigger when user mentions writing docs, specs, proposals, PRD, design doc, RFC, etc.
disable-model-invocation: true
---

# Doc Co-Authoring Workflow

Walk user through three stages: Context Gathering, Refinement & Structure, and Reader Testing.

## Offer Workflow
Offer a structured co-authoring workflow. Explain stages:
1. **Context Gathering**: Share context and answer clarifying questions.
2. **Refinement & Structure**: Brainstorm and edit section-by-section.
3. **Reader Testing**: Verify clarity using a fresh Gemini instance.
If accepted, proceed to Stage 1. If declined, work freeform.

---

## Stage 1: Context Gathering
**Goal**: Close context gap between user and AI.

### 1. Initial Meta-Questions
Ask user:
1. Document type? (e.g., technical spec, design doc, proposal)
2. Primary audience?
3. Desired impact/outcome?
4. Existing template or specific format to follow?
5. Key constraints or context?

- **Templates/Files**: If user provides file or template, read it. If a shared document link is shared, fetch it via integration.
- **Existing Docs**: If editing an existing doc, read current state. Check for images without alt-text. Explain Gemini cannot see them; offer to generate alt-text if they paste the images.

### 2. Info Dumping & Clarification
- Encourage user to dump raw background context (problem, discussions, rejected alternatives, politics, timeline, tech details).
- Use integrations (Slack, Teams, Drive, SharePoint) if available to pull context. If unavailable, suggest enabling connectors.
- Proactively search connected tools if unknown entities/projects are mentioned (wait for approval).
- **Clarifying Questions**: Generate 5-10 numbered questions based on gaps. Encourage shorthand answers.
- **Exit Condition**: Basics are clear; ready to discuss edge cases and tradeoffs. Proceed to Stage 2.

---

## Stage 2: Refinement & Structure
**Goal**: Iteratively build the document section by section.

### 1. Section Structure
- Ask user which section to start with. Recommend starting with the section with most unknowns (e.g., proposal or tech approach). Leave summaries for last.
- If structure is unclear, suggest 3-5 sections based on doc type.
- Create scaffold file with placeholder text (e.g., "[Content here]"). Use `create_file` for an artifact if available; otherwise create a local markdown file (e.g., `technical-spec.md`).

### 2. Section Refinement (For Each Section)
For the current section, execute these steps:
- **Step 1: Clarifying Questions**: Ask 5-10 specific questions about what should be included.
- **Step 2: Brainstorming**: List 5-20 numbered options of points/considerations to cover.
- **Step 3: Curation**: Ask user to specify which numbers to keep, remove, or combine. Parse freeform feedback if provided.
- **Step 4: Gap Check**: Ask if anything important is missing.
- **Step 5: Drafting**: Replace placeholder text with drafted content.
  - *Note for 1st Section*: Remind user to suggest changes in chat (e.g., "make paragraph 3 concise") rather than editing the doc directly to help teach their writing style.
- **Step 6: Iterative Refinement**: Apply edits using `str_replace` or code edit tools. Never reprint the entire doc. Iterate until user is satisfied.
  - *Quality Check*: If 3 iterations pass without major changes, ask if any filler/slop can be pruned.

### 3. Review & Coherence
- **Near Completion (80%+ done)**: Read the entire document. Check for flow, consistency, redundancies, filler, or generic slop. Provide feedback.
- **Complete Draft**: Perform a final review for overall coherence and completeness. Propose final suggestions, then proceed to Stage 3.

---

## Stage 3: Reader Testing
**Goal**: Verify the document works for a reader with zero context.

### Approach A: Sub-Agents Available
1. **Predict Questions**: Generate 5-10 realistic questions readers might ask to discover or understand this doc.
2. **Test**: Invoke a fresh sub-agent for each question, passing only the document content. Summarize what they got right/wrong.
3. **Ambiguity Check**: Invoke sub-agent to check for ambiguity, false assumptions, or contradictions.
4. **Fix Gaps**: Report issues clearly in chat, fix identified gaps, and loop back to refinement if needed.

### Approach B: Manual Testing (No Sub-Agents)
1. **Predict Questions**: Generate 5-10 realistic questions.
2. **User Instructions**: Instruct user to open a fresh Gemini thread, paste the doc, ask the questions, and check if it misinterprets anything.
3. **Check Gaps**: Ask user what Reader Gemini struggled with. Fix gaps and iterate.

**Exit Condition**: Reader Gemini answers all questions correctly without surfacing gaps.

---

## Final Review & Completion
Once testing passes:
1. Prompt user to do a final self read-through (verify details, links, facts, and impact).
2. Announce completion and offer final tips:
   - Link conversation in appendix for transparency.
   - Use appendices to maintain depth without bloating the main text.
   - Keep updating doc based on real reader feedback.

---

## Effective Guidance Rules
- **Tone**: Direct, procedural, no "sales pitch". Explain rationale briefly only if it affects user actions.
- **Deviations**: If user wants to skip a stage, ask to confirm working freeform. Propose speed-up strategies if they are frustrated.
- **Context Management**: Address gaps immediately as they arise; do not let them accumulate.
- **Artifacts**: Use `create_file` for drafts/scaffolds and file editing tools for updates. Provide the file link after every edit. Never put brainstorming lists in files; keep them in chat.
- **Quality**: Never rush. Ensure every sentence in the document carries weight.