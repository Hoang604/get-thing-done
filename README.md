# Get-Thing-Done (GTD) Framework

Workflows that help you write reliable code and debug efficiently. Simple and easy to use.

## Antigravity Installation

### Global Install (available everywhere)

**Linux/macOS:**

```bash
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
cd gtd-temp && chmod +x *.sh && ./install.sh
cd .. && rm -rf gtd-temp
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
cd gtd-temp; .\install.ps1
cd ..; Remove-Item -Recurse -Force gtd-temp
```

## Start Here (Default Workflow)

Most users should follow the **Develop Flow**:

1. **[/spec](.gemini/config/global_workflowsspec.md)** → define requirements in `./.gtd/<task>/SPEC.md`
2. **[/roadmap](.gemini/config/global_workflowsroadmap.md)** → split work into phases in `./.gtd/<task>/ROADMAP.md`
3. **[/plan-phase](.gemini/config/global_workflowsplan-phase.md)** → create `./.gtd/<task>/<phase>/PLAN.md`
4. **[/execute](.gemini/config/global_workflowsexecute.md)** → implement and produce `./.gtd/<task>/<phase>/SUMMARY.md`
5. **[/commit-spec](.gemini/config/global_workflowscommit-spec.md)** → generate final commit message from summaries
6. **[/archive](.gemini/config/global_workflowsarchive.md)** → archive completed task history

## Which Flow To Use

- **Build a new feature from requirements**: use Develop Flow (above).
- **Port/execute from architecture docs and backlog**: use Strategy Flow.
- **Fix a bug with root-cause discipline**: use Debug Flow.

## Workflow Structure

### 1. Skills (Foundations)

- **[Awareness](.gemini/skills/awareness/SKILL.md)**: Self-review loop. Applies to every non-trivial user request once manually triggered.
- **[Review Code](.gemini/skills/code-review/SKILL.md)**: Take scope, review code, and return a structured architectural report.
- **[Create Plan](.gemini/skills/create-plan/SKILL.md)**: Create execution plans following INCOSE/EARS format and ISO/IEC/IEEE 15288:2023 conformance.
- **[Doc Co-Authoring](.gemini/skills/doc-coauthoring/SKILL.md)**: Guide users through collaborative document creation (technical specs, PRDs, design docs).
- **[Explain](.gemini/skills/explain/SKILL.md)**: Explain code in a causal chain for understanding a slice or feature.
- **[Explain Architecture](.gemini/skills/explain-architecture/SKILL.md)**: Explain the skeleton of the architecture to build the global frame for understanding the codebase.
- **[Frontend Design](.gemini/skills/frontend-design/SKILL.md)**: Create distinctive, production-grade frontend interfaces with high design quality.

### 2. Strategy Flow (Architecture Porting)

Systematic execution from architecture docs to backlog-driven delivery:

1. **[/bootstrap](.gemini/config/global_workflowsbootstrap.md)**: Initialize `BACKLOG.md` from architecture docs.
2. **[/expand-backlog](.gemini/config/global_workflowsexpand-backlog.md)**: Break high-level items into executable sub-items.
3. **[/s:spec](.gemini/config/global_workflowss-spec.md)**: Pull next item from `BACKLOG.md` and generate `SPEC.md`.
4. Continue with Develop Flow (`/roadmap` → `/plan-phase` → `/execute`).
5. **[/s:archive](.gemini/config/global_workflowss-archive.md)**: Archive work and mark backlog item complete.

### 3. Debug Flow (Fixes)

Systematic process for resolving defects:

1. **[/d-symptom](.gemini/config/global_workflowsd-symptom.md)**: Document expected vs actual behavior.
2. **[/d-inspect](.gemini/config/global_workflowsd-inspect.md)**: Trace code paths and form ranked hypotheses.
3. **[/d-verify](.gemini/config/global_workflowsd-verify.md)**: Verify hypotheses with targeted debug evidence.
4. **[/d-plan-fix](.gemini/config/global_workflowsd-plan-fix.md)**: Create an atomic fix plan.
5. **[/d-execute](.gemini/config/global_workflowsd-execute.md)**: Implement fix and verify symptom resolution.
6. **[/d-archive](.gemini/config/global_workflowsd-archive.md)**: Archive completed debug work.

### 4. Lifecycle Management

- **[/archive](.gemini/config/global_workflowsarchive.md)**: Move completed independent task to `./.gtd/archive/`.
- **[/d-archive](.gemini/config/global_workflowsd-archive.md)**: Move completed debug work to `./.gtd/archive/`.
