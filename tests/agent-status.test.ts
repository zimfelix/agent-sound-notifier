import assert from "node:assert/strict";
import { execFileSync, spawn, type ChildProcess } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, beforeEach, test } from "node:test";
import { fileURLToPath } from "node:url";

const SCRIPT = fileURLToPath(new URL("../hooks/agent-status.sh", import.meta.url));
const temp = mkdtempSync(join(tmpdir(), "agent-status-"));
const sleepers: ChildProcess[] = [];
let devDir = "";
let stateDir = "";

function livePid(): number {
  const child = spawn("sleep", ["60"], { stdio: "ignore" });
  sleepers.push(child);
  return child.pid!;
}

function deadPid(): number {
  const child = execFileSync("/bin/sh", ["-c", "sleep 0 & echo $!"], { encoding: "utf8" });
  return Number(child.trim());
}

function run(action: string, agent: string, pid: number, tty: string, project = "/work/demo") {
  execFileSync("/bin/sh", [SCRIPT, action, agent, String(pid), project, tty], {
    env: { ...process.env, AGENT_STATUS_DEV_DIR: devDir, AGENT_STATUS_STATE_DIR: stateDir },
  });
}

/** The fake terminal device collects every OSC title written to it; return the latest one. */
function title(tty: string): string {
  const written = readFileSync(join(devDir, tty), "utf8");
  const titles = [...written.matchAll(/\u001b\]0;(.*?)\u0007/g)].map((match) => match[1]);
  return titles.at(-1) ?? "";
}

beforeEach(() => {
  const run = mkdtempSync(join(temp, "run-"));
  devDir = join(run, "dev");
  stateDir = join(run, "state");
  mkdirSync(devDir);
  for (const tty of ["ttys001", "ttys002", "ttys003"]) writeFileSync(join(devDir, tty), "");
});

after(() => {
  for (const child of sleepers) child.kill();
  rmSync(temp, { recursive: true, force: true });
});

test("a single agent shows its own working and done state", () => {
  const pid = livePid();
  run("start", "Pi", pid, "ttys001");
  assert.equal(title("ttys001"), "⚪ 1 arbeitet · Pi");
  run("stop", "Pi", pid, "ttys001");
  assert.equal(title("ttys001"), "🟡 1 fertig · Pi");
});

test("all tabs of a project show working while one agent still works", () => {
  const claude = livePid();
  const pi = livePid();
  run("start", "Claude", claude, "ttys001");
  run("start", "Pi", pi, "ttys002");
  run("stop", "Claude", claude, "ttys001");

  assert.equal(title("ttys001"), "⚪ 1 arbeitet · 🟡 1 fertig · hier 🟡 Claude");
  assert.equal(title("ttys002"), "⚪ 1 arbeitet · 🟡 1 fertig · hier ⚪ Pi");

  run("stop", "Pi", pi, "ttys002");
  assert.equal(title("ttys001"), "🟡 2 fertig · hier 🟡 Claude");
  assert.equal(title("ttys002"), "🟡 2 fertig · hier 🟡 Pi");
});

test("projects are counted separately", () => {
  run("start", "Claude", livePid(), "ttys001", "/work/one");
  run("start", "Pi", livePid(), "ttys002", "/work/two");
  assert.equal(title("ttys001"), "⚪ 1 arbeitet · Claude");
  assert.equal(title("ttys002"), "⚪ 1 arbeitet · Pi");
});

test("finished agent processes are dropped from the count", () => {
  run("start", "Claude", deadPid(), "ttys001");
  run("stop", "Pi", livePid(), "ttys002");
  assert.equal(title("ttys002"), "🟡 1 fertig · Pi");
  const [project] = readdirSync(stateDir);
  assert.deepEqual(readdirSync(join(stateDir, project)), ["ttys002"]);
});

test("a new agent in the same tab replaces the previous entry", () => {
  run("stop", "Claude", livePid(), "ttys001");
  run("start", "Pi", livePid(), "ttys001");
  assert.equal(title("ttys001"), "⚪ 1 arbeitet · Pi");
});

test("invalid calls and unreachable terminals change nothing and exit cleanly", () => {
  assert.doesNotThrow(() => run("pause", "Pi", livePid(), "ttys001"));
  assert.doesNotThrow(() => run("start", "Pi", livePid(), "ttys009"));
  assert.equal(readFileSync(join(devDir, "ttys001"), "utf8"), "");
});
