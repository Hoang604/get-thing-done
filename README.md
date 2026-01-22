# Get-Thing-Done (GTD) Framework

A disciplined, zero-assumption framework for agentic software development and debugging.

## Installation

### Local Install (project-specific)

Navigate to your project directory.

**Linux/macOS:**

```bash
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
cd gtd-temp && chmod +x *.sh && ./install.sh ./.agent
cd .. && rm -rf gtd-temp
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
cd gtd-temp; .\install.ps1 .\.agent
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
cd gtd-temp && chmod +x *.sh && ./install-gemini.sh
cd .. && rm -rf gtd-temp
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
cd gtd-temp; .\install-gemini.ps1
cd ..; Remove-Item -Recurse -Force gtd-temp
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

## Core Philosophy

- **Zero Assumption**: Never guess from names. Read the code to understand its true behavior.
- **Atomicity**: Execute tasks as independent, verifiable units to prevent corruption.
- **No Silent Failures**: All errors must be logged and handled; swallowing errors is forbidden.
- **Plan Fidelity**: Implement exactly what is planned. Deviations require discussion.

## Framework Structure

### 1. Skills (The Foundations)

- **[Investigate (The Archaeologist)](skills/investigate/SKILL.md)**: Procedures for excavating truth from code paths without guessing.
- **[Code (The Runtime Realist)](skills/code/SKILL.md)**: Standards for implementing reliable, atomic, and magic-free code.

### 2. Workflows (The Process)

#### Develop Flow

Standardized sequence for building new features:

1. **[/spec](workflows/spec.md)**: Interview user and define clear, finalized requirements in `SPEC.md`.
2. **[/roadmap](workflows/roadmap.md)**: Sequence requirements into ordered `ROADMAP.md` phases.
3. **[/plan](workflows/plan.md)**: Create atomic `PLAN.md` tasks for a specific phase.
4. **[/execute](workflows/execute.md)**: Atomically implement tasks and generate a `SUMMARY.md`.
5. **[/commit-spec](workflows/commit-spec.md)**: Synthesize all summaries into a high-quality descriptive commit.

#### Debug Flow

Systematic process for resolving defects:

1. **[/d-symptom](workflows/d-symptom.md)**: Precisely document expected vs. actual behavior.
2. **[/d-inspect](workflows/d-inspect.md)**: Trace code paths and form ranked root-cause hypotheses.
3. **[/d-verify](workflows/d-verify.md)**: Strategically log to confirm the actual root cause.
4. **[/d-plan-fix](workflows/d-plan-fix.md)**: Create an approved atomic plan to address the cause.
5. **[/d-execute](workflows/d-execute.md)**: Implement the fix and verify symptom resolution.

### 3. Lifecycle Management

- **[/archive](workflows/archive.md)**: Move completed develop work to `./.gtd/archive/`.
- **[/d-archive](workflows/d-archive.md)**: Move completed debug work to `./.gtd/archive/`.

## Directory Standard

- `./.gtd/<task_name>/`: Active task state.
- `./.gtd/archive/`: Historical record of completed work.
- `./skills/`: Shared behavioral guidelines.
- `./workflows/`: Process automation scripts.
