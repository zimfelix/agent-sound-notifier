import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

const AGENT_STATUS = fileURLToPath(new URL("../hooks/agent-status.sh", import.meta.url));

// Windows has no afplay; PowerShell plays a system WAV synchronously, so the sound is not cut off.
const WINDOWS_SOUND_SCRIPT = [
  "$f = Join-Path $env:WINDIR 'Media\\Windows Notify System Generic.wav'",
  "if (Test-Path $f) { (New-Object Media.SoundPlayer $f).PlaySync() }",
  "else { [System.Media.SystemSounds]::Asterisk.Play(); Start-Sleep -Milliseconds 800 }",
].join("; ");

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

export function completionSoundCommand(platform: NodeJS.Platform = process.platform): [string, string[]] {
  if (platform === "win32") {
    return ["powershell.exe", ["-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", WINDOWS_SOUND_SCRIPT]];
  }
  return ["/usr/bin/afplay", ["-v", "0.5", "/System/Library/Sounds/Pop.aiff"]];
}

function playCompletionSound(): void {
  const [command, args] = completionSoundCommand();
  runQuietly(command, args, "the audio player");
}

/** Shares this agent's state with other agents of the project (see hooks/agent-status.sh). */
function reportProjectStatus(status: AgentStatus, ctx: ExtensionContext): void {
  // The status script needs a POSIX shell and terminal devices; Windows gets the sound only.
  if (process.platform === "win32") return;
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
