import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

const COMPLETION_SOUND = "/System/Library/Sounds/Pop.aiff";
const AFPLAY = "/usr/bin/afplay";
const AGENT_STATUS = fileURLToPath(new URL("../hooks/agent-status.sh", import.meta.url));

export type AgentStatus = "start" | "stop";
export type StatusReporter = (status: AgentStatus, ctx: ExtensionContext) => void;

function runQuietly(command: string, args: string[], label: string): void {
  try {
    const child = spawn(command, args, { stdio: "ignore" });
    child.on("error", (error) => {
      console.warn(`[agent-sound-notifier] Could not run ${label}: ${error.message}`);
    });
    child.on("exit", (code) => {
      if (code !== 0) {
        console.warn(`[agent-sound-notifier] ${label} exited with code ${code}.`);
      }
    });
  } catch (error) {
    console.warn(`[agent-sound-notifier] Could not start ${label}.`, error);
  }
}

function playCompletionSound(): void {
  runQuietly(AFPLAY, ["-v", "0.5", COMPLETION_SOUND], "the audio player");
}

/** Shares this agent's state with other agents of the project (see hooks/agent-status.sh). */
function reportProjectStatus(status: AgentStatus, ctx: ExtensionContext): void {
  runQuietly("/bin/sh", [AGENT_STATUS, status, "Pi", String(process.pid), ctx.cwd], "the tab status script");
}

function setTerminalTabStatus(reportStatus: StatusReporter, status: AgentStatus, ctx: ExtensionContext): void {
  if (ctx.mode !== "tui") return;
  try {
    reportStatus(status, ctx);
  } catch (error) {
    console.warn("[agent-sound-notifier] Could not update the terminal tab title.", error);
  }
}

export function registerCompletionSound(
  pi: Pick<ExtensionAPI, "on">,
  playSound: () => void = playCompletionSound,
  reportStatus: StatusReporter = reportProjectStatus,
): void {
  pi.on("agent_start", (_event, ctx) => {
    setTerminalTabStatus(reportStatus, "start", ctx);
  });

  pi.on("agent_settled", (_event, ctx) => {
    try {
      playSound();
    } catch (error) {
      console.warn("[agent-sound-notifier] Completion sound failed.", error);
    }
    setTerminalTabStatus(reportStatus, "stop", ctx);
  });
}

export default function (pi: ExtensionAPI): void {
  registerCompletionSound(pi);
}
