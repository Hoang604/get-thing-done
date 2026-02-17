const fs = require("fs");
const settingsPath = process.argv[2];

if (!settingsPath) {
  console.error("Usage: node update-settings.js <settings.json path>");
  process.exit(1);
}

let content = fs.readFileSync(settingsPath, "utf8");
// Strip comments securely (preserving strings)
content = content.replace(
  /\\"|"(?:\\"|[^"])*"|(\/\/.*|\/\*[\s\S]*?\*\/)/g,
  (m, g) => (g ? "" : m),
);
const settings = JSON.parse(content);

const newHook = {
  type: "command",
  command: "node ~/.gemini/hooks/before.js",
  name: "Rules",
  description: "Add rules to prevent gemini do stupid thing",
  timeout: 5000,
};

// Initialize hooks structure if not exists
if (!settings.hooks) {
  settings.hooks = {};
}
if (!settings.hooks.BeforeAgent) {
  settings.hooks.BeforeAgent = [];
}

// Find or create the hooks array entry
let hooksEntry = settings.hooks.BeforeAgent.find((e) => e.hooks);
if (!hooksEntry) {
  hooksEntry = { hooks: [] };
  settings.hooks.BeforeAgent.push(hooksEntry);
}

// Check if this hook already exists (by name)
const existingIndex = hooksEntry.hooks.findIndex(
  (h) => h.name === newHook.name,
);
if (existingIndex >= 0) {
  hooksEntry.hooks[existingIndex] = newHook;
} else {
  hooksEntry.hooks.push(newHook);
}

fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + "\n");
