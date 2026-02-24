---
name: log-work
description: Append a raw summary of the newly completed work to today's log.
---
<philosophy>
The user needs to report to their senior supervisor every day. Supervisors want maximum signal with minimum noise: they care about the actual impact/outcomes (what was built or fixed), active blockages, and facts. 

This workflow does NOT write the final report. Its primary purpose is to act as a silent, continuous journal. By appending the raw facts of what we just accomplished into a daily ledger, we gather the exact raw material the user needs to easily draft their own report at the end of the day.
</philosophy>

# Daily Log Update Workflow

1. Determine today's date in `YY-MM-DD` format and current time in `HH:MM`.
2. Assume the target file is `.gtd/daily-log/YY-MM-DD.md`.
3. Based **on your current conversation context**, extract the core facts of what was just accomplished:
   - **Task/Context**: What was the general objective?
   - **Action Taken/Impact**: What was actually done, built, or fixed?
   - **Blockers/Notes**: Any hurdles encountered or important context for the supervisor.
4. Append these facts as a concise bulleted list under a new `## [HH:MM] - [Task Name]` heading at the bottom of `.gtd/daily-log/YY-MM-DD.md` (create the file and necessary parent directories if they do not exist).
