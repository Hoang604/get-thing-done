const {
  clearState,
  emitJson,
  getSessionId,
  loadState,
  readHookInput,
  saveState,
} = require("./hook-state");

const MAX_RETRIES = 1;

function hasRequiredSection(label, responseText) {
  const sectionPattern = new RegExp(`^${label}:\\s*\\S[\\s\\S]*`, "m");
  return sectionPattern.test(responseText);
}

function getRequiredLabels(toolCategory) {
  if (toolCategory === "write") {
    return ["Change made", "Next action"];
  }

  if (toolCategory === "execute") {
    return ["Result", "Next action"];
  }

  return ["Findings", "Next action"];
}

function hasAcknowledgementShape(responseText, toolCategory) {
  const [primaryLabel, nextActionLabel] = getRequiredLabels(toolCategory);
  return (
    hasRequiredSection(primaryLabel, responseText) &&
    hasRequiredSection(nextActionLabel, responseText)
  );
}

function buildRetryReason(state) {
  const toolName = state.last_tool_name || "the previous tool";
  const toolStatus = state.last_tool_status || "unknown status";
  const toolCategory = state.last_tool_category || "read";
  const [primaryLabel, nextActionLabel] = getRequiredLabels(toolCategory);

  const primaryGuidance = {
    read: `${primaryLabel}: summarize what the tool output revealed.`,
    write: `${primaryLabel}: state exactly what the tool changed.`,
    execute: `${primaryLabel}: summarize what happened and what it means.`,
  };

  return [
    "You skipped the required acknowledge step after a tool result.",
    `The previous tool was ${toolName} (${toolStatus}, ${toolCategory}).`,
    "Retry now with this exact structure:",
    primaryGuidance[toolCategory],
    `${nextActionLabel}: state one concrete next step.`,
    `Do not call another tool or continue the task before writing ${primaryLabel}.`,
  ].join("\n");
}

function handleAfterAgent(input) {
  const sessionId = getSessionId(input);
  const state = loadState(sessionId);

  if (!sessionId || !state || !state.awaiting_ack) {
    return {
      decision: "allow",
      suppressOutput: true,
    };
  }

  const responseText = input.prompt_response || "";
  if (hasAcknowledgementShape(responseText, state.last_tool_category)) {
    clearState(sessionId);
    return {
      decision: "allow",
      suppressOutput: true,
    };
  }

  const retryCount = Number(state.retry_count || 0);
  if (input.stop_hook_active || retryCount >= MAX_RETRIES) {
    clearState(sessionId);
    return {
      decision: "allow",
      suppressOutput: true,
      systemMessage:
        "Acknowledge-validator fallback: allowing response after retry guard triggered.",
    };
  }

  saveState(sessionId, {
    ...state,
    retry_count: retryCount + 1,
  });

  return {
    decision: "deny",
    reason: buildRetryReason(state),
    suppressOutput: true,
  };
}

function main() {
  emitJson(handleAfterAgent(readHookInput()));
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    console.error(`[after-agent] ${error.message}`);
    emitJson({
      decision: "allow",
      suppressOutput: true,
    });
  }
}

module.exports = {
  handleAfterAgent,
  getRequiredLabels,
};
