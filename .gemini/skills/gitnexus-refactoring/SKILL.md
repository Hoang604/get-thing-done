---
name: gitnexus-refactoring
description: "Rename, extract, split, move, or restructure code safely using GitNexus. Use when asked 'Rename this function', 'Extract this into a module', or 'Refactor this class'."
---

# Refactoring with GitNexus

Use this skill to restructure code safely by leveraging the GitNexus knowledge graph to automate updates and verify the impact of changes.

## Workflow

1. **Map Dependents**: Execute `gitnexus_impact({target: "X", direction: "upstream"})` to identify all symbols that depend on the target.
2. **Find Execution Flows**: Run `gitnexus_query({query: "X"})` to find all execution flows involving the target symbol.
3. **Analyze References**: Use `gitnexus_context({name: "X"})` to see all incoming and outgoing references.
4. **Plan Update Order**: Follow a structured sequence: interfaces → implementations → callers → tests.
5. **Verify Changes**: Run `gitnexus_detect_changes()` after the refactor to ensure only the expected scope was affected.

## Refactoring Checklists

### Rename Symbol

- [ ] Run `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` to preview all edits.
- [ ] Review **graph edits** (high confidence) and **ast_search edits** (review carefully).
- [ ] If satisfied, run `gitnexus_rename({..., dry_run: false})` to apply the changes.
- [ ] Run `gitnexus_detect_changes()` to verify the affected files.
- [ ] Execute tests for the affected processes.

### Extract Module

- [ ] Run `gitnexus_context({name: target})` to identify all incoming and outgoing references.
- [ ] Run `gitnexus_impact({target, direction: "upstream"})` to find all external callers.
- [ ] Define the new module interface.
- [ ] Extract the code and update imports.
- [ ] Run `gitnexus_detect_changes()` to verify the affected scope.
- [ ] Execute tests for the affected processes.

### Split Function or Service

- [ ] Run `gitnexus_context({name: target})` to understand all callees.
- [ ] Group callees by responsibility.
- [ ] Run `gitnexus_impact({target, direction: "upstream"})` to map callers that need updating.
- [ ] Create the new functions or services and update callers.
- [ ] Run `gitnexus_detect_changes()` to verify the affected scope.
- [ ] Execute tests for the affected processes.

## Risk Mitigation

| Risk Factor | Mitigation Strategy |
| :--- | :--- |
| **Many callers (>5)** | Use `gitnexus_rename` for automated, high-confidence updates. |
| **Cross-area references** | Use `detect_changes` after the refactor to verify the affected scope. |
| **String/dynamic refs** | Use `gitnexus_query` to find potential dynamic references. |
| **External/public API** | Ensure proper versioning and deprecation strategies are followed. |

## Tools Reference

- **gitnexus_rename**: Automated multi-file rename with confidence scoring.
- **gitnexus_impact**: Map all upstream/downstream dependents.
- **gitnexus_detect_changes**: Verify changes and affected processes after refactoring.
- **gitnexus_cypher**: Custom graph queries for deep reference analysis.

## Example: Rename `validateUser` to `authenticateUser`

1. Run `gitnexus_rename({symbol_name: "validateUser", new_name: "authenticateUser", dry_run: true})`.
   - *Result*: 12 edits: 10 graph (safe), 2 ast_search (review).
2. Review `ast_search` edits (e.g., dynamic references in config files).
3. Run `gitnexus_rename({..., dry_run: false})` to apply the 12 edits.
4. Run `gitnexus_detect_changes({scope: "all"})`.
   - *Result*: Affected: `LoginFlow`, `TokenRefresh`. Run tests for these flows.
