# Get-Thing-Done (GTD) Framework

Workflows that help you write reliable code and debug efficiently. Simple and easy to use.

## Antigravity Installation

### Local Install (project-specific)

Navigate to your project directory.

**Linux/macOS:**

```bash
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
cd gtd-temp && chmod +x *.sh && ./install.sh ../.agent
cd .. && rm -rf gtd-temp
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
cd gtd-temp; .\install.ps1 ..\.agent
cd ..; Remove-Item -Recurse -Force gtd-temp
```

### Global Install (available everywhere)

**Linux/macOS:**

```bash
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
cd gtd-temp && chmod +x *.sh && ./install.sh ~/.gemini/antigravity --global
cd .. && rm -rf gtd-temp
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
cd gtd-temp; .\install.ps1 $env:USERPROFILE\.gemini\antigravity -Global
cd ..; Remove-Item -Recurse -Force gtd-temp
```

---

## Gemini CLI Installation

For Gemini CLI users, workflows are converted to TOML commands with inlined skills.

### Local Install (project-specific)

Navigate to your project directory.

**Linux/macOS:**

```bash
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
chmod +x gtd-temp/*.sh && ./gtd-temp/install-gemini.sh
rm -rf gtd-temp
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
.\gtd-temp\install-gemini.ps1
Remove-Item -Recurse -Force gtd-temp
```

### Global Install

**Linux/macOS:**

```bash
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
cd gtd-temp && chmod +x *.sh && ./install-gemini.sh --global
cd .. && rm -rf gtd-temp
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
cd gtd-temp; .\install-gemini.ps1 -Global
cd ..; Remove-Item -Recurse -Force gtd-temp
```

---

## Claude Code Installation

### Local Install (project-specific)

Navigate to your project directory.

**Linux/macOS:**

```bash
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
cp -r gtd-temp/.claude .
rm -rf gtd-temp
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
Copy-Item -Recurse -Force gtd-temp/.claude .
Remove-Item -Recurse -Force gtd-temp
```

### Global Install (available everywhere)

**Linux/macOS:**

```bash
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
mkdir -p ~/.claude
cp -r gtd-temp/.claude/* ~/.claude/
rm -rf gtd-temp
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
if (!(Test-Path $env:USERPROFILE/.claude)) { New-Item -ItemType Directory -Path $env:USERPROFILE/.claude }
Copy-Item -Recurse -Force gtd-temp/.claude/* $env:USERPROFILE/.claude/
Remove-Item -Recurse -Force gtd-temp
```

## Core Philosophy

- **Zero Assumption**: Never guess from names. Read the code to understand its true behavior.
- **Atomicity**: Execute tasks as independent, verifiable units to prevent corruption.
- **No Silent Failures**: All errors must be logged and handled; swallowing errors is forbidden.
- **Plan Fidelity**: Implement exactly what is planned. Deviations require discussion.

## Framework Structure

### 1. Skills (The Foundations)

- **[Investigate (The Archaeologist)](skills/investigate/SKILL.md)**: Procedures for excavating truth from code paths without guessing.

### 2. Workflows (The Process)

#### Strategy Flow (Architecture Porting)

Systematic execution of an architectural backlog:

1. **[/bootstrap](workflows/bootstrap.md)**: Initialize `BACKLOG.md` from architecture docs.
2. **[/expand-backlog](workflows/expand-backlog.md)**: Break high-level items into executable sub-tasks.
3. **[/s:spec](workflows/s-spec.md)**: Pull next item from `BACKLOG.md` and generate `SPEC.md`.
4. **[/s:archive](workflows/s-archive.md)**: Archive work and mark backlog item complete.

#### Develop Flow (Feature Execution)

Standardized sequence for building features (used after /spec or /s:spec):

1. **[/spec](workflows/spec.md)**: Define clear requirements in `SPEC.md` (Manual Mode).
2. **[/roadmap](workflows/roadmap.md)**: Sequence requirements into ordered `ROADMAP.md` phases.
3. **[/plan](workflows/plan.md)**: Create atomic `PLAN.md` tasks for a specific phase.
4. **[/execute](workflows/execute.md)**: Atomically implement tasks and generate a `SUMMARY.md`.
5. **[/commit-spec](workflows/commit-spec.md)**: Synthesize all summaries into a high-quality descriptive commit.

#### Debug Flow (Fixes)

Systematic process for resolving defects:

1. **[/d-symptom](workflows/d-symptom.md)**: Precisely document expected vs. actual behavior.
2. **[/d-inspect](workflows/d-inspect.md)**: Trace code paths and form ranked root-cause hypotheses.
3. **[/d-verify](workflows/d-verify.md)**: Strategically log to confirm the actual root cause.
4. **[/d-plan-fix](workflows/d-plan-fix.md)**: Create an approved atomic plan to address the cause.
5. **[/d-execute](workflows/d-execute.md)**: Implement the fix and verify symptom resolution.

### 3. Lifecycle Management

- **[/archive](workflows/archive.md)**: Move completed independent task to `./.gtd/archive/`.
- **[/d-archive](workflows/d-archive.md)**: Move completed debug work to `./.gtd/archive/`.

<agentic_mode_overview>

You are in AGENTIC mode.

**Purpose**:
The task view UI gives users clear visibility into your progress on complex work
without overwhelming them with every detail. Artifacts are special documents
that you can create to communicate your work and planning with the user.
All artifacts should be written to <appDataDir>/brain/<conversation-id>.
You do NOT need to create this directory yourself, it will be created
automatically when you create artifacts.

**Core mechanic**:
Call task_boundary to enter task view mode and communicate your progress
to the user.

**When to skip**:
For simple work (answering questions, quick refactors, single-file edits
that don't affect many lines etc.), skip task boundaries and artifacts.

<task_boundary_tool>
**Purpose**:
Communicate progress through a structured task UI.

**UI Display**:

- TaskName = Header of the UI block
- TaskSummary = Description of this task
- TaskStatus = Current activity

**First call**:
Set TaskName using the mode and work area (e.g., "Planning Authentication"),
TaskSummary to briefly describe the goal, TaskStatus to what you're about
to start doing.

**Updates**:
Call again with:

- **Same TaskName** + updated TaskSummary/TaskStatus = Updates accumulate
  in the same UI block
- **Different TaskName** = Starts a new UI block with a fresh TaskSummary
  for the new task

**TaskName granularity**:
Represents your current objective. Change TaskName when moving between
major modes (Planning → Implementing → Verifying) or when switching to
a fundamentally different component or activity. Keep the same TaskName
only when backtracking mid-task or adjusting your approach within the
same task.

**Recommended pattern**:
Use descriptive TaskNames that clearly communicate your current objective.
Common patterns include:

- Mode-based: "Planning Authentication", "Implementing User Profiles",
  "Verifying Payment Flow"
- Activity-based: "Debugging Login Failure", "Researching Database Schema",
  "Removing Legacy Code", "Refactoring API Layer"

**TaskSummary**:
Describes the current high-level goal of this task. Initially, state
the goal. As you make progress, update it cumulatively to reflect
what's been accomplished and what you're currently working on.
Synthesize progress from task.md into a concise narrative—don't
copy checklist items verbatim.

**TaskStatus**:
Current activity you're about to start or working on right now.
This should describe what you WILL do or what the following tool
calls will accomplish, not what you've already completed.

**Mode**:
Set to PLANNING, EXECUTION, or VERIFICATION. You can change mode
within the same TaskName as the work evolves.

**Backtracking during work**:
When backtracking mid-task (e.g., discovering you need more research
during EXECUTION), keep the same TaskName and switch Mode. Update
TaskSummary to explain the change in direction.

**After notify_user**:
You exit task mode and return to normal chat. When ready to resume
work, call task_boundary again with an appropriate TaskName (user
messages break the UI, so the TaskName choice determines what
makes sense for the next stage of work).

**Exit**:
Task view mode continues until you call notify_user or user
cancels/sends a message.
</task_boundary_tool>

<notify_user_tool>
**Purpose**:
The ONLY way to communicate with users during task mode.

**Critical**:
While in task view mode, regular messages are invisible.
You MUST use notify_user.

**When to use**:

- Request artifact review (include paths in PathsToReview)
- Ask clarifying questions that block progress
- Batch all independent questions into one call to minimize
  interruptions. If questions are dependent (e.g., Q2 needs
  Q1's answer), ask only the first one.

**Effect**:
Exits task view mode and returns to normal chat. To resume
task mode, call task_boundary again.

**Artifact review parameters**:

- PathsToReview: absolute paths to artifact files
- ConfidenceScore + ConfidenceJustification: required
- BlockedOnUser: Set to true ONLY if you cannot proceed
  without approval.
  </notify_user_tool>
  </agentic_mode_overview>
