# Get-Thing-Done (GTD) Framework

Workflows that help you write reliable code and debug efficiently. Simple and easy to use.

## Antigravity Installation

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

---

## Gemini CLI Installation

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

## Start Here (Default Workflow)

Most users should follow the **Develop Flow**:

1. **[/spec](workflows/spec.md)** → define requirements in `./.gtd/<task>/SPEC.md`
2. **[/roadmap](workflows/roadmap.md)** → split work into phases in `./.gtd/<task>/ROADMAP.md`
3. **[/plan-phase](workflows/plan-phase.md)** → create `./.gtd/<task>/<phase>/PLAN.md`
4. **[/execute](workflows/execute.md)** → implement and produce `./.gtd/<task>/<phase>/SUMMARY.md`
5. **[/commit-spec](workflows/commit-spec.md)** → generate final commit message from summaries
6. **[/archive](workflows/archive.md)** → archive completed task history

If your CLI aliases `/plan` to `/plan-phase`, use whichever is configured in your environment.

## Which Flow To Use

- **Build a new feature from requirements**: use Develop Flow (above).
- **Port/execute from architecture docs and backlog**: use Strategy Flow.
- **Fix a bug with root-cause discipline**: use Debug Flow.

## Workflow Structure

### 1. Skills (Foundations)

- **[Investigate (The Archaeologist)](skills/investigate/SKILL.md)**: Procedures for excavating truth from code paths without guessing.

### 2. Strategy Flow (Architecture Porting)

Systematic execution from architecture docs to backlog-driven delivery:

1. **[/bootstrap](workflows/bootstrap.md)**: Initialize `BACKLOG.md` from architecture docs.
2. **[/expand-backlog](workflows/expand-backlog.md)**: Break high-level items into executable sub-items.
3. **[/s:spec](workflows/s-spec.md)**: Pull next item from `BACKLOG.md` and generate `SPEC.md`.
4. Continue with Develop Flow (`/roadmap` → `/plan-phase` → `/execute`).
5. **[/s:archive](workflows/s-archive.md)**: Archive work and mark backlog item complete.

### 3. Debug Flow (Fixes)

Systematic process for resolving defects:

1. **[/d-symptom](workflows/d-symptom.md)**: Document expected vs actual behavior.
2. **[/d-inspect](workflows/d-inspect.md)**: Trace code paths and form ranked hypotheses.
3. **[/d-verify](workflows/d-verify.md)**: Verify hypotheses with targeted debug evidence.
4. **[/d-plan-fix](workflows/d-plan-fix.md)**: Create an atomic fix plan.
5. **[/d-execute](workflows/d-execute.md)**: Implement fix and verify symptom resolution.
6. **[/d-archive](workflows/d-archive.md)**: Archive completed debug work.

### 4. Lifecycle Management

- **[/archive](workflows/archive.md)**: Move completed independent task to `./.gtd/archive/`.
- **[/d-archive](workflows/d-archive.md)**: Move completed debug work to `./.gtd/archive/`.
