import type { Plugin } from "@opencode-ai/plugin"
import { execFileSync } from "node:child_process"
import { homedir } from "node:os"

// GTD hooks port: injects the opencode-specific critical-instructions script
// into the system prompt on each turn.
//
// Gemini event -> opencode hook mapping:
//   PreInvocation (critical_instructions_opencode.sh) -> experimental.chat.system.transform

const HOME = homedir()
const SCRIPTS = `${HOME}/.gemini/config/scripts`

const TIMEOUTS = {
  critical: 15_000, // hooks.json: critical-instructions timeout 15
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

export const GtdHooks: Plugin = async () => {
  return {
    "experimental.chat.system.transform": async (input, output) => {
      const sessionID = input.sessionID ?? "default"

      const messages: string[] = collectEphemeral(
        runScript("bash", "critical_instructions_opencode.sh", [], { conversationId: sessionID }, TIMEOUTS.critical),
      )

      // In-place push only: reassigning output.system is a silent no-op.
      for (const msg of messages) output.system.push(msg)
    },
  }
}
