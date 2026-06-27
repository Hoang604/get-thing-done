const {
  emitJson,
  getSessionId,
  readHookInput,
  saveState,
} = require("./hook-state");

const READ_TOOLS = new Set([
  "read_file",
  "glob",
  "grep_search",
  "list_directory",
  "google_web_search",
  "web_fetch",
]);

const WRITE_TOOLS = new Set([
  "write_file",
  "replace",
  "save_memory",
]);

function getToolStatus(toolResponse) {
  return toolResponse && toolResponse.error ? "error" : "success";
}

function getToolCategory(toolName) {
  if (READ_TOOLS.has(toolName)) {
    return "read";
  }

  if (WRITE_TOOLS.has(toolName)) {
    return "write";
  }

  return "execute";
}

function getAcknowledgementLabels(toolCategory) {
  if (toolCategory === "write") {
    return ["Changed", "Next"];
  }

  if (toolCategory === "execute") {
    return ["Result", "Next"];
  }

  return ["Found", "Next"];
}

function buildAdditionalContext(toolName, toolStatus, toolCategory) {
  const labels = getAcknowledgementLabels(toolCategory);
  const guidanceByCategory = {
    read: `${labels[0]}: summarize results.`,
    write: `${labels[0]}: state exact changes.`,
    execute: `${labels[0]}: summarize outcome.`,
  };
  const analysisReminder =
    toolCategory === "write"
      ? null
      : "Analyze results.";

  return [
    "Hook: AfterTool",
    `Tool: ${toolName || "unknown"} (${toolStatus}, ${toolCategory}).`,
    analysisReminder,
    "Next reply must use labels:",
    guidanceByCategory[toolCategory],
    `${labels[1]}: next step + reason.`,
    "Act now. Do not stop.",
  ]
    .filter(Boolean)
    .join("\n");
}

function handleAfterTool(input) {
  const sessionId = getSessionId(input);
  const toolStatus = getToolStatus(input.tool_response);
  const toolCategory = getToolCategory(input.tool_name);

  if (sessionId) {
    saveState(sessionId, {
      awaiting_ack: true,
      last_tool_name: input.tool_name || null,
      last_tool_category: toolCategory,
      last_tool_status: toolStatus,
      last_tool_at: input.timestamp || null,
      retry_count: 0,
    });
  }

  return {
    decision: "allow",
    suppressOutput: true,
    hookSpecificOutput: {
      additionalContext: buildAdditionalContext(input.tool_name, toolStatus, toolCategory),
    },
  };
}

function main() {
  emitJson(handleAfterTool(readHookInput()));
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    console.error(`[after-tool] ${error.message}`);
    emitJson({
      decision: "allow",
      suppressOutput: true,
    });
  }
}

module.exports = {
  handleAfterTool,
  getToolCategory,
};
