import type { Plugin } from "@opencode-ai/plugin"
import { execFileSync } from "node:child_process"
import { homedir } from "node:os"

// GTD hooks port: reuses the Gemini-side verify scripts as the decision engine
// and uses an opencode-specific critical-instructions script (default.* tool
// vocabulary) for the system prompt. Mutation-guard is intentionally disabled
// on opencode — batching is driven by critical-instructions instead.
//
// Gemini event -> opencode hook mapping:
//   PreInvocation (critical_instructions_opencode.sh) -> experimental.chat.system.transform
//   PreInvocation (verify_injector.py)                -> experimental.chat.system.transform
//   PostToolUse run_command (recorder)                -> tool.execute.after + tool.execute.error on bash
//
// NOTE: opencode's tool.execute.after is success-only; failures arrive via
// tool.execute.error. Both are registered (unknown hook names are ignored by
// older runtimes, so this is version-safe).

const HOME = homedir()
const SCRIPTS = `${HOME}/.gemini/config/scripts`

const TIMEOUTS = {
  critical: 15_000, // hooks.json: critical-instructions timeout 15
  verify: 10_000, // hooks.json: verify-recorder / verify-failure-guard timeout 10
} as const

type InjectStep = { ephemeralMessage?: string }

function runScript(
  interpreter: string,
  script: string,
  extraArgs: string[],
  payload: unknown,
  timeoutMs: number,
): Record<string, any> {
  try {
    const out = execFileSync(interpreter, [`${SCRIPTS}/${script}`, ...extraArgs], {
      input: JSON.stringify(payload),
      timeout: timeoutMs,
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "ignore"],
    })
    const text = (typeof out === "string" ? out : out.toString()).trim()
    return JSON.parse(text || "{}")
  } catch {
    return {}
  }
}

function collectEphemeral(result: Record<string, any>): string[] {
  const steps = result?.injectSteps
  if (!Array.isArray(steps)) return []
  return steps
    .map((s: InjectStep) => s?.ephemeralMessage)
    .filter((m: unknown): m is string => typeof m === "string" && m.length > 0)
}

// Opencode tool names differ from the Gemini vocabulary the Python scripts
// match on, so the adapter translates at the boundary (bash -> run_command).
const TOOL_TO_GEMINI = { bash: "run_command" } as const

function recordVerify(
  sessionID: string,
  command: string,
  cwd: string,
  error: string | null,
): void {
  if (!command) return
  runScript(
    "python3",
    "verify_recorder.py",
    [],
    {
      conversationId: sessionID,
      toolCall: { name: "run_command", args: { CommandLine: command, Cwd: cwd } },
      error,
    },
    TIMEOUTS.verify,
  )
}

// Matches VerifyRecorder._evaluate_status failure markers so `after`-hook
// result text can be translated into the recorder's `error` field.
const FAILURE_MARKER = /(?:exit status|exited with code|exit code)\s+([1-9][0-9]*)/i

export const GtdHooks: Plugin = async () => {
  return {
    "experimental.chat.system.transform": async (input, output) => {
      const sessionID = input.sessionID ?? "default"

      const messages: string[] = [
        // critical-instructions (opencode variant, default.* vocabulary), every request
        ...collectEphemeral(
          runScript("bash", "critical_instructions_opencode.sh", [], { conversationId: sessionID }, TIMEOUTS.critical),
        ),
        // verify-failure-guard: pending sync incidents for this session
        // (async-transcript scan degrades gracefully without transcriptPath)
        ...collectEphemeral(
          runScript("python3", "verify_injector.py", [], { conversationId: sessionID }, TIMEOUTS.verify),
        ),
      ]

      // In-place push only: reassigning output.system is a silent no-op.
      for (const msg of messages) output.system.push(msg)
    },

    "tool.execute.after": async (input, output) => {
      const sessionID = input.sessionID
      const args = (input.args ?? {}) as Record<string, any>

      if (input.tool === TOOL_TO_GEMINI.bash || input.tool === "bash") {
        const command = String(args.command ?? "")
        const cwd = String(args.workdir ?? args.cwd ?? "")
        const resultText = String(output?.output ?? "")
        const marker = resultText.match(FAILURE_MARKER)
        // error=null -> recorder logs PASS; matched marker -> FAIL + incident
        recordVerify(sessionID, command, cwd, marker ? marker[0] : null)
        return
      }
    },

    "tool.execute.error": async (input, output) => {
      if (input.tool !== "bash") return
      const args = (input.args ?? {}) as Record<string, any>
      const err = (output as { error?: unknown })?.error
      const message = err instanceof Error ? err.message : String(err ?? "tool failed")
      recordVerify(input.sessionID, String(args.command ?? ""), String(args.workdir ?? args.cwd ?? ""), message)
    },
  }
}
