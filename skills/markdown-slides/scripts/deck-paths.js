"use strict";

const { spawnSync } = require("child_process");
const path = require("path");

const SCRIPTS = __dirname;
const SKILL_ROOT = path.resolve(SCRIPTS, "..");

function deckRootArgs(argv) {
  const forwarded = [];
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--deck-root") {
      const value = argv[i + 1];
      if (!value) {
        process.stderr.write("missing value for --deck-root\n");
        process.exit(1);
      }
      forwarded.push("--deck-root", value);
      i += 1;
    } else if (arg.startsWith("--deck-root=")) {
      forwarded.push(arg);
    }
  }
  return forwarded;
}

/** Ask scripts/config.py for deck-root artifact paths. Does not build them. */
function loadOutputs(argv) {
  const args = argv || process.argv.slice(2);
  const result = spawnSync(
    "python3",
    [path.join(SCRIPTS, "config.py"), "--print-output", "json", ...deckRootArgs(args)],
    { encoding: "utf8", env: process.env }
  );
  if (result.error) {
    process.stderr.write(`${result.error.message}\n`);
    process.exit(1);
  }
  if (result.status !== 0) {
    process.stderr.write(result.stderr || result.stdout || "config.py failed\n");
    process.exit(result.status || 1);
  }
  return JSON.parse(result.stdout);
}

function deckEnv(outputs) {
  return { ...process.env, DECK_ROOT: outputs.root };
}

module.exports = {
  SKILL_ROOT,
  SCRIPTS,
  loadOutputs,
  deckEnv,
};
