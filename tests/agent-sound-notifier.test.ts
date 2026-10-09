import assert from "node:assert/strict";
import { afterEach, mock, test } from "node:test";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { registerCompletionSound, type AgentStatus } from "../extensions/agent-sound-notifier.js";

type PiHandler = (event: unknown, ctx: ExtensionContext) => void;

function fakePi() {
  const registrations: string[] = [];
  const handlers = new Map<string, PiHandler>();
  const pi = {
    on(event: string, handler: unknown) {
      registrations.push(event);
      handlers.set(event, handler as PiHandler);
      return () => {};
    },
  } as unknown as Pick<ExtensionAPI, "on">;

  return {
    pi,
    registrations,
    fire(event: string, ctx: ExtensionContext) {
      const handler = handlers.get(event);
      assert.ok(handler, `${event} handler should be registered`);
      handler({ type: event }, ctx);
    },
  };
}

function fakeContext(mode: "tui" | "rpc" = "tui", cwd = "/work/demo") {
  return { mode, cwd } as unknown as ExtensionContext;
}

function recorder() {
  const statuses: string[] = [];
  return { statuses, report: (status: AgentStatus, ctx: ExtensionContext) => statuses.push(`${status} ${ctx.cwd}`) };
}

afterEach(() => mock.reset());

test("reports the project status as done only after the agent settles", () => {
  const { pi, registrations, fire } = fakePi();
  const { statuses, report } = recorder();
  const ctx = fakeContext();
  let playCount = 0;

  registerCompletionSound(pi, () => playCount++, report);

  assert.deepEqual(registrations, ["agent_start", "agent_settled"]);
  fire("agent_start", ctx);
  assert.deepEqual(statuses, ["start /work/demo"]);
  assert.equal(playCount, 0);

  fire("agent_settled", ctx);
  assert.deepEqual(statuses, ["start /work/demo", "stop /work/demo"]);
  assert.equal(playCount, 1);
});

test("does not change terminal titles in non-TUI modes", () => {
  const { pi, fire } = fakePi();
  const { statuses, report } = recorder();

  registerCompletionSound(pi, () => {}, report);
  fire("agent_start", fakeContext("rpc"));

  assert.deepEqual(statuses, []);
});

test("does not let terminal-title failures interrupt agent events", () => {
  const { pi, fire } = fakePi();
  const warning = mock.method(console, "warn", () => {});
  let playCount = 0;

  registerCompletionSound(pi, () => playCount++, () => { throw new Error("terminal title unavailable"); });

  assert.doesNotThrow(() => fire("agent_start", fakeContext()));
  assert.doesNotThrow(() => fire("agent_settled", fakeContext()));
  assert.equal(playCount, 1);
  assert.equal(warning.mock.callCount(), 2);
});

test("does not let a sound failure interrupt the settled event", () => {
  const { pi, fire } = fakePi();
  const { statuses, report } = recorder();
  const warning = mock.method(console, "warn", () => {});

  registerCompletionSound(pi, () => {
    throw new Error("audio unavailable");
  }, report);

  assert.doesNotThrow(() => fire("agent_settled", fakeContext()));
  assert.equal(warning.mock.callCount(), 1);
  assert.deepEqual(statuses, ["stop /work/demo"]);
});
