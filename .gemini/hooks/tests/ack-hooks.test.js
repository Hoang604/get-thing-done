const fs = require("fs");
const os = require("os");
const path = require("path");
const assert = require("node:assert/strict");
const { spawnSync } = require("child_process");
const { handleAfterTool } = require("../after-tool");
const { handleAfterAgent } = require("../after-agent");

const repoRoot = path.resolve(__dirname, "../../..");
const hooksDir = path.resolve(__dirname, "..");
const installerScript = path.join(repoRoot, "install-gemini.sh");

function runTest(name, fn) {
  try {
    fn();
    console.log(`PASS ${name}`);
  } catch (error) {
    console.error(`FAIL ${name}`);
    console.error(error.stack || error.message);
    process.exitCode = 1;
  }
}

runTest("after-tool stores pending acknowledge state and injects immediate reminder", () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "gemini-after-tool-"));
  const stateDir = path.join(tmpDir, "state");
  const sessionId = "session-after-tool";
  const originalStateDir = process.env.GEMINI_HOOK_STATE_DIR;
  process.env.GEMINI_HOOK_STATE_DIR = stateDir;

  const output = handleAfterTool({
    session_id: sessionId,
    tool_name: "read_file",
    tool_response: {
      llmContent: "content",
    },
    timestamp: "2026-03-12T10:00:00Z",
  });

  assert.equal(output.decision, "allow");
  assert.match(output.hookSpecificOutput.additionalContext, /Findings:/);
  assert.match(output.hookSpecificOutput.additionalContext, /Next action:/);

  const storedState = JSON.parse(
    fs.readFileSync(path.join(stateDir, `${sessionId}.json`), "utf-8"),
  );
  assert.equal(storedState.awaiting_ack, true);
  assert.equal(storedState.last_tool_name, "read_file");
  assert.equal(storedState.last_tool_category, "read");
  assert.equal(storedState.last_tool_status, "success");
  assert.equal(storedState.retry_count, 0);

  process.env.GEMINI_HOOK_STATE_DIR = originalStateDir;
});

runTest("after-agent denies responses that skip the acknowledge shape", () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "gemini-after-agent-deny-"));
  const stateDir = path.join(tmpDir, "state");
  const sessionId = "session-deny";
  const originalStateDir = process.env.GEMINI_HOOK_STATE_DIR;
  process.env.GEMINI_HOOK_STATE_DIR = stateDir;
  fs.mkdirSync(stateDir, { recursive: true });
  fs.writeFileSync(
    path.join(stateDir, `${sessionId}.json`),
    JSON.stringify({
      awaiting_ack: true,
      last_tool_name: "read_file",
      last_tool_category: "read",
      last_tool_status: "success",
      last_tool_at: "2026-03-12T10:00:00Z",
      retry_count: 0,
    }),
  );

  const output = handleAfterAgent({
    session_id: sessionId,
    prompt_response: "I will now read another file.",
    stop_hook_active: false,
  });

  assert.equal(output.decision, "deny");
  assert.match(output.reason, /Findings:/);
  assert.match(output.reason, /Next action:/);

  const storedState = JSON.parse(
    fs.readFileSync(path.join(stateDir, `${sessionId}.json`), "utf-8"),
  );
  assert.equal(storedState.retry_count, 1);

  process.env.GEMINI_HOOK_STATE_DIR = originalStateDir;
});

runTest("after-agent clears pending state after a valid acknowledgement", () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "gemini-after-agent-allow-"));
  const stateDir = path.join(tmpDir, "state");
  const sessionId = "session-allow";
  const originalStateDir = process.env.GEMINI_HOOK_STATE_DIR;
  process.env.GEMINI_HOOK_STATE_DIR = stateDir;
  fs.mkdirSync(stateDir, { recursive: true });
  fs.writeFileSync(
    path.join(stateDir, `${sessionId}.json`),
    JSON.stringify({
      awaiting_ack: true,
      last_tool_name: "run_shell_command",
      last_tool_category: "execute",
      last_tool_status: "error",
      last_tool_at: "2026-03-12T10:00:00Z",
      retry_count: 0,
    }),
  );

  const output = handleAfterAgent({
    session_id: sessionId,
    prompt_response:
      "Result: the command failed because the file does not exist, so the target path is wrong.\nNext action: I will inspect the target path before retrying.",
    stop_hook_active: false,
  });

  assert.equal(output.decision, "allow");
  assert.equal(fs.existsSync(path.join(stateDir, `${sessionId}.json`)), false);

  process.env.GEMINI_HOOK_STATE_DIR = originalStateDir;
});

runTest("after-agent fails open after the retry guard is already active", () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "gemini-after-agent-guard-"));
  const stateDir = path.join(tmpDir, "state");
  const sessionId = "session-guard";
  const originalStateDir = process.env.GEMINI_HOOK_STATE_DIR;
  process.env.GEMINI_HOOK_STATE_DIR = stateDir;
  fs.mkdirSync(stateDir, { recursive: true });
  fs.writeFileSync(
    path.join(stateDir, `${sessionId}.json`),
    JSON.stringify({
      awaiting_ack: true,
      last_tool_name: "read_file",
      last_tool_category: "read",
      last_tool_status: "success",
      last_tool_at: "2026-03-12T10:00:00Z",
      retry_count: 1,
    }),
  );

  const output = handleAfterAgent({
    session_id: sessionId,
    prompt_response: "Still missing the right labels.",
    stop_hook_active: true,
  });

  assert.equal(output.decision, "allow");
  assert.match(output.systemMessage, /retry guard/i);
  assert.equal(fs.existsSync(path.join(stateDir, `${sessionId}.json`)), false);

  process.env.GEMINI_HOOK_STATE_DIR = originalStateDir;
});

runTest("after-tool uses write acknowledgement labels for write tools", () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "gemini-after-tool-write-"));
  const stateDir = path.join(tmpDir, "state");
  const sessionId = "session-write";
  const originalStateDir = process.env.GEMINI_HOOK_STATE_DIR;
  process.env.GEMINI_HOOK_STATE_DIR = stateDir;

  const output = handleAfterTool({
    session_id: sessionId,
    tool_name: "write_file",
    tool_response: {},
    timestamp: "2026-03-12T10:00:00Z",
  });

  assert.match(output.hookSpecificOutput.additionalContext, /Change made:/);
  assert.match(output.hookSpecificOutput.additionalContext, /Next action:/);

  const storedState = JSON.parse(
    fs.readFileSync(path.join(stateDir, `${sessionId}.json`), "utf-8"),
  );
  assert.equal(storedState.last_tool_category, "write");

  process.env.GEMINI_HOOK_STATE_DIR = originalStateDir;
});

runTest("after-agent accepts write acknowledgements with Change made and Next action", () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "gemini-after-agent-write-"));
  const stateDir = path.join(tmpDir, "state");
  const sessionId = "session-write-allow";
  const originalStateDir = process.env.GEMINI_HOOK_STATE_DIR;
  process.env.GEMINI_HOOK_STATE_DIR = stateDir;
  fs.mkdirSync(stateDir, { recursive: true });
  fs.writeFileSync(
    path.join(stateDir, `${sessionId}.json`),
    JSON.stringify({
      awaiting_ack: true,
      last_tool_name: "write_file",
      last_tool_category: "write",
      last_tool_status: "success",
      last_tool_at: "2026-03-12T10:00:00Z",
      retry_count: 0,
    }),
  );

  const output = handleAfterAgent({
    session_id: sessionId,
    prompt_response:
      "Change made: updated the hook config to register AfterTool and AfterAgent.\nNext action: I will run the hook tests to verify the new flow.",
    stop_hook_active: false,
  });

  assert.equal(output.decision, "allow");
  assert.equal(fs.existsSync(path.join(stateDir, `${sessionId}.json`)), false);

  process.env.GEMINI_HOOK_STATE_DIR = originalStateDir;
});

runTest("install-gemini.sh --global installs and registers all acknowledge hooks", () => {
  const tmpHome = fs.mkdtempSync(path.join(os.tmpdir(), "gemini-install-home-"));
  const geminiDir = path.join(tmpHome, ".gemini");
  fs.mkdirSync(geminiDir, { recursive: true });
  fs.writeFileSync(
    path.join(geminiDir, "settings.json"),
    JSON.stringify(
      {
        ui: {
          theme: "GitHub",
        },
      },
      null,
      2,
    ) + "\n",
  );

  const result = spawnSync("bash", [installerScript, "--global"], {
    cwd: repoRoot,
    encoding: "utf-8",
    env: {
      ...process.env,
      HOME: tmpHome,
    },
  });

  assert.equal(result.status, 0, result.stderr);

  const installedSettings = JSON.parse(
    fs.readFileSync(path.join(geminiDir, "settings.json"), "utf-8"),
  );

  assert.ok(installedSettings.hooks.BeforeAgent);
  assert.ok(installedSettings.hooks.AfterTool);
  assert.ok(installedSettings.hooks.AfterAgent);

  const beforeHooks = installedSettings.hooks.BeforeAgent[0].hooks;
  const afterToolHooks = installedSettings.hooks.AfterTool[0].hooks;
  const afterAgentHooks = installedSettings.hooks.AfterAgent[0].hooks;

  assert.equal(beforeHooks.some((hook) => hook.name === "Rules"), true);
  assert.equal(afterToolHooks.some((hook) => hook.name === "AcknowledgeTool"), true);
  assert.equal(afterAgentHooks.some((hook) => hook.name === "ValidateAcknowledgement"), true);
  assert.equal(fs.existsSync(path.join(geminiDir, "hooks", "state")), true);
});

if (process.exitCode) {
  process.exit(process.exitCode);
}
