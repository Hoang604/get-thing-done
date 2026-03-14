const fs = require("fs");
const os = require("os");
const path = require("path");

function readHookInput() {
  return JSON.parse(fs.readFileSync(0, "utf-8"));
}

function getSessionId(input) {
  return input.session_id || process.env.GEMINI_SESSION_ID || null;
}

function getStateDir() {
  if (process.env.GEMINI_HOOK_STATE_DIR) {
    return process.env.GEMINI_HOOK_STATE_DIR;
  }

  const homeDir = process.env.HOME || os.homedir();
  return path.join(homeDir, ".gemini", "hooks", "state");
}

function getStatePath(sessionId) {
  return path.join(getStateDir(), `${sessionId}.json`);
}

function ensureStateDir() {
  fs.mkdirSync(getStateDir(), { recursive: true });
}

function loadState(sessionId) {
  if (!sessionId) {
    return null;
  }

  const statePath = getStatePath(sessionId);
  if (!fs.existsSync(statePath)) {
    return null;
  }

  return JSON.parse(fs.readFileSync(statePath, "utf-8"));
}

function saveState(sessionId, state) {
  if (!sessionId) {
    return;
  }

  ensureStateDir();
  fs.writeFileSync(getStatePath(sessionId), JSON.stringify(state, null, 2) + "\n");
}

function clearState(sessionId) {
  if (!sessionId) {
    return;
  }

  const statePath = getStatePath(sessionId);
  if (fs.existsSync(statePath)) {
    fs.unlinkSync(statePath);
  }
}

function emitJson(payload) {
  process.stdout.write(JSON.stringify(payload));
}

module.exports = {
  clearState,
  emitJson,
  getSessionId,
  getStateDir,
  loadState,
  readHookInput,
  saveState,
};
