import { Plugin } from "@opencode/plugin"
import { execFileSync } from "node:child_process"
import { mkdirSync, writeFileSync } from "node:fs"
import { homedir } from "node:os"

// GTD hooks port of .gemini/config/scripts/critical_instructions.sh:
// injects the critical-instructions systemMessage on the first turn, after
// >=40k token growth, or after compaction, as a persistent session message.
//
// Gemini event -> OpenCode mapping:
//   PreInvocation                  -> session "context" hook
//   persistent systemMessage       -> ctx.session.synthetic (session history)
//   compact_threshold_tracker.py   -> effective_tokens/compaction_count below

const HOME = homedir()
const SCRIPTS = `${HOME}/.gemini/config/scripts`
const STATE_DIR = process.env.AGY_COMPACT_STATE_DIR ?? "/tmp/agy_compact_state"

// hooks.json gives the critical-instructions hook a 15s timeout
const CRITICAL_INSTRUCTIONS_TIMEOUT_MS = 15_000

// Matches compact_threshold_tracker.py sanitize_id
function sanitizeID(sessionID: string): string {
  const cleaned = sessionID.replace(/[^a-zA-Z0-9_-]/g, "_")
  return cleaned.length > 0 ? cleaned : "default"
}

function writeTrackerState(sessionID: string, effectiveTokens: number, compactionCount: number): void {
  mkdirSync(STATE_DIR, { recursive: true })
  const state = {
    effective_tokens: effectiveTokens,
    compaction_count: compactionCount,
  }
  writeFileSync(`${STATE_DIR}/${sanitizeID(sessionID)}.json`, JSON.stringify(state) + "\n")
}

// Contract of critical_instructions_opencode.sh stdout:
// trigger -> {"injectSteps":[{"systemMessage":{"systemMessage":"..."}}]}, otherwise {"injectSteps":[]}
function runCriticalInstructions(sessionID: string): string[] {
  const stdout = execFileSync("bash", [`${SCRIPTS}/critical_instructions_opencode.sh`], {
    input: JSON.stringify({ conversationId: sessionID }),
    timeout: CRITICAL_INSTRUCTIONS_TIMEOUT_MS,
    encoding: "utf-8",
    stdio: ["pipe", "pipe", "pipe"],
  })
  const parsed: unknown = JSON.parse(stdout)
  if (typeof parsed !== "object" || parsed === null) {
    throw new Error("output is not a JSON object")
  }
  const steps = (parsed as { injectSteps?: unknown }).injectSteps
  if (!Array.isArray(steps)) {
    throw new Error("injectSteps is not an array")
  }
  return steps.map((step) => {
    if (typeof step !== "object" || step === null) {
      throw new Error("injectSteps entry is not an object")
    }
    const systemMessage = (step as { systemMessage?: unknown }).systemMessage
    if (typeof systemMessage !== "object" || systemMessage === null) {
      throw new Error("injectSteps entry without a systemMessage object")
    }
    const message = (systemMessage as { systemMessage?: unknown }).systemMessage
    if (typeof message !== "string" || message.length === 0) {
      throw new Error("systemMessage without a non-empty string message")
    }
    return message
  })
}

export default Plugin.define({
  id: "gtd-hooks",
  async setup(ctx) {
    await ctx.session.hook("context", async (event) => {
      type SessionMessage = Awaited<ReturnType<typeof ctx.session.context>>[number]

      const lastAssistantTokens = (messages: readonly SessionMessage[]): number => {
        for (let index = messages.length - 1; index >= 0; index -= 1) {
          const message = messages[index]
          // Assistant messages that never completed carry no usage
          if (message.type === "assistant" && message.tokens !== undefined) {
            return message.tokens.input + message.tokens.cache.read
          }
        }
        return 0
      }

      const completedCompactions = (messages: readonly SessionMessage[]): number =>
        messages.filter((message) => message.type === "compaction" && message.status === "completed").length

      try {
        const messages = await ctx.session.context({ sessionID: event.sessionID })
        writeTrackerState(event.sessionID, lastAssistantTokens(messages), completedCompactions(messages))
        for (const text of runCriticalInstructions(event.sessionID)) {
          await ctx.session.synthetic({ sessionID: event.sessionID, text })
        }
      } catch (error) {
        console.error("gtd-hooks: critical instructions injection failed:", error)
      }
    })
  },
})
