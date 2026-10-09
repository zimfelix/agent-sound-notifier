import assert from "node:assert/strict";
import { execFileSync, spawn, type ChildProcess } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, readdirSync, realpathSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, beforeEach, test } from "node:test";
import { fileURLToPath } from "node:url";

const SCRIPT = fileURLToPath(new URL("../hooks/agent-status.sh", import.meta.url));
const temp = mkdtempSync(join(tmpdir(), "agent-status-"));
const sleepers: ChildProcess[] = [];
let devDir = "";
let stateDir = "";
let projectDir = "";

function livePid(): number {
  const child = spawn("sleep", ["60"], { stdio: "ignore" });
  sleepers.push(child);
  return child.pid!;
}

function deadPid(): number {
  return Number(execFileSync("/bin/sh", ["-c", "sleep 0 & echo $!"], { encoding: "utf8" }).trim());
}

function run(action: string, agent: string, pid: number, tty: string, project = "demo") {
  const root = join(projectDir, project);
  mkdirSync(root, { recursive: true });
  execFileSync("/bin/sh", [SCRIPT, action, agent, String(pid), root, tty], {
    env: { ...process.env, AGENT_STATUS_DEV_DIR: devDir, AGENT_STATUS_STATE_DIR: stateDir },
  });
}

function title(tty: string): string {
  const written = readFileSync(join(devDir, tty), "utf8");
  return [...written.matchAll(/\u001b\]0;(.*?)\u0007/g)].at(-1)?.[1] ?? "";
}

beforeEach(() => {
  const root = mkdtempSync(join(temp, "run-"));
  devDir = join(root, "dev");
  stateDir = join(root, "state");
  projectDir = join(root, "projects");
  mkdirSync(devDir);
  for (const tty of ["ttys001", "ttys002", "ttys003"]) writeFileSync(join(devDir, tty), "");
});

after(() => {
  for (const child of sleepers) child.kill();
  rmSync(temp, { recursive: true, force: true });
});

test("a single agent shows only its own working and done state, including restarting", () => {
  const pid = livePid();
  run("start", "Pi", pid, "ttys001");
  assert.equal(title("ttys001"), "⚪ Pi");
  run("stop", "Pi", pid, "ttys001");
  assert.equal(title("ttys001"), "🟡 Pi");
  run("start", "Pi", pid, "ttys001");
  assert.equal(title("ttys001"), "⚪ Pi");
});

test("each terminal keeps only its own state independent of other sessions", () => {
  const claude = livePid();
  const pi = livePid();
  run("start", "Claude", claude, "ttys001");
  run("start", "Pi", pi, "ttys002");
  run("stop", "Claude", claude, "ttys001");
  assert.equal(title("ttys001"), "🟡 Claude");
  assert.equal(title("ttys002"), "⚪ Pi");
  run("stop", "Pi", pi, "ttys002");
  assert.equal(title("ttys001"), "🟡 Claude");
  assert.equal(title("ttys002"), "🟡 Pi");
});

test("projects have separate cache directories with their canonical paths", () => {
  run("start", "Claude", livePid(), "ttys001", "one");
  run("start", "Pi", livePid(), "ttys002", "two");
  const dirs = readdirSync(stateDir);
  assert.equal(dirs.length, 2);
  const paths = dirs.map(d => readFileSync(join(stateDir, d, ".project"), "utf8").trim()).sort();
  assert.deepEqual(paths, [realpathSync(join(projectDir, "one")), realpathSync(join(projectDir, "two"))].sort());
});

test("finished agent processes are dropped, metadata is retained", () => {
  run("start", "Claude", deadPid(), "ttys001");
  run("stop", "Pi", livePid(), "ttys002");
  assert.equal(title("ttys002"), "🟡 Pi");
  const [project] = readdirSync(stateDir);
  assert.deepEqual(readdirSync(join(stateDir, project)), [".project", "ttys002"]);
});

test("a new agent in the same tab replaces the previous entry", () => {
  run("stop", "Claude", livePid(), "ttys001");
  run("start", "Pi", livePid(), "ttys001");
  assert.equal(title("ttys001"), "⚪ Pi");
  const [project] = readdirSync(stateDir);
  assert.match(readFileSync(join(stateDir, project, "ttys001"), "utf8"), /^working \d+ Pi\n$/);
});

test("invalid calls, title injection and unreachable terminals change nothing", () => {
  run("pause", "Pi", livePid(), "ttys001");
  run("start", "Pi", livePid(), "ttys009");
  run("start", "Pi\u0007bad", livePid(), "ttys001");
  run("start", "Pi", livePid(), "../outside");
  run("start", "Pi", -1, "ttys001");
  assert.equal(readFileSync(join(devDir, "ttys001"), "utf8"), "");
});

test("subdirectories of a Git project share one status directory", () => {
  const root = join(projectDir, "git-demo");
  mkdirSync(root, { recursive: true });
  execFileSync("git", ["init", "-q", root]);
  run("start", "Claude", livePid(), "ttys001", "git-demo");
  run("stop", "Pi", livePid(), "ttys002", "git-demo/sub dir");
  const [project] = readdirSync(stateDir);
  assert.equal(readdirSync(stateDir).length, 1);
  assert.deepEqual(readdirSync(join(stateDir, project)), [".project", "ttys001", "ttys002"]);
});
