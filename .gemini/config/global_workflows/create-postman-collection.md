---
name: create-postman-collection
description: Design and write importable Postman collections for API workflows.
---

# Create Postman Collection

## Overview
Design Postman collections: investigate code, declare contract, mirror request plan for approval, write JSON after confirmation.

## Workflow
Flow: Parse Target → Investigate → Detect conventions → Declare Oracle → Design strategy → Mirror → Confirm → Write JSON → Validate
Do not skip mirror-and-confirm.

## 1. Parse Target
Identify workflow target: feature flow, endpoint family, manual scenario, regression path.
Ask minimal question if ambiguous.

## 2. Investigate Code First
Before designing requests:
- Read controllers for routes/methods.
- Read request DTOs for body shape.
- Read response DTOs/wrappers for JSON paths.
- Read service layer for side effects/invariants.
- Find auth requirements/role guards.
- Identify setup dependencies (prerequisite ids/resources/access).
Do not guess paths, bodies, shapes, or roles.

## 3. Detect Conventions
Determine: base path, versioning, auth headers, response envelope, auto-discovery capability, runnability.
If not runnable with current roles/data, report before writing.

## 4. Declare Oracle
State ground truth before proposing assertions.

### Behavioral Claims
State what request sequence proves.
Sources: `CODE [file:line]`, `SPEC [doc §section]`, `INFERRED — reasoning`.

### Boundary Claims
State auth, setup, role boundaries.

### Data Discovery Claims
State auto-discovered vs manual variables. Specify required vs convenience workflows (subtype, setup resource, roles).

### Unverified Assumptions
Flag: `⚠️ UNVERIFIED ASSUMPTION`.

## 5. Design Collection Strategy
For each claim, define requests.

### Format:
```text
### Setup Requests
- [ ] {Request name} → VERIFY: {what this request establishes}
      SOURCE: {code/spec/structural property}
      ORACLE REF: {claim}
      BREAKS IF: {specific mutation or mismatch}

### Flow Requests
- [ ] {Request name} → VERIFY: {what runtime behavior is proven}
      SOURCE: {code/spec/structural property}
      ORACLE REF: {claim}
      BREAKS IF: {specific mutation}

### Guard / Error Requests
- [ ] {Request name} → VERIFY: {expected rejection or boundary behavior}
      SOURCE: {code/spec/structural property}
      ORACLE REF: {claim}
      BREAKS IF: {specific mutation}
```

Specify for every request: method, path, headers, body, query params, variables consumed/produced, Postman test assertions.
Rules:
- Auto-save tokens/ids.
- Avoid hardcoding. Fail early on missing prerequisites.
- Ground workflow narrowing in user intent or code constraints.
- Show multiple valid paths in mirror. Do not silently hardcode one choice (subtype, auth role, setup resource, fixture).

## 6. Mirror The Plan
Present full collection plan before writing JSON.

### Format:
```text
---
  COLLECTION PLAN — {target}
---

Target: {workflow under test}
Collection Type: {fully runnable | runnable with variables | partial template}
Output File: {planned json filename}

Oracle Claims: {N} behavioral, {N} boundary, {N} discovery, {N} unverified
Requests: {N} setup, {N} flow, {N} guard/error

---
ORACLE DECLARATION
---

### Behavioral Claims
- CLAIM: ...
  SOURCE: ...

### Boundary Claims
- CLAIM: ...
  SOURCE: ...

### Data Discovery Claims
- CLAIM: ...
  SOURCE: ...

### Unverified Assumptions
- ⚠️ ASSUMPTION: ...

---
COLLECTION STRATEGY
---

### Setup Requests
- [ ] ...
      SOURCE: ...
      ORACLE REF: ...
      BREAKS IF: ...

### Flow Requests
- [ ] ...
      SOURCE: ...
      ORACLE REF: ...
      BREAKS IF: ...

### Guard / Error Requests
- [ ] ...
      SOURCE: ...
      ORACLE REF: ...
      BREAKS IF: ...

Variables:
- {variable name}: {purpose}

Output:
- {collection filename}

---
```

**Wait for approval before writing collection JSON.**

## 7. Write The Collection
After approval:
- Create `.postman_collection.json` file.
- Produce valid importable Postman Collection v2.1 JSON.
- Prefer collection variables over hardcoded values.
- Keep request-level scripts simple, deterministic.

If "runnable immediately" requested:
- Wire auth login, auto-capture tokens (`data.accessToken`) and prior ids.
- State remaining manual variables.

## 8. Validate The Collection
Verify:
- JSON parses. Schema valid for Postman.
- Referenced variables exist.
- Endpoints, methods, headers match code.
- Test scripts read real response paths.
Run local JSON parse check.

## Prohibitions
- Do not invent routes or fields.
- Do not generate without investigating controllers/DTOs first.
- Do not skip discussing role restrictions.
- Do not silently narrow workflow or hide manual prerequisites.
- Do not output malformed JSON or write before approval.
