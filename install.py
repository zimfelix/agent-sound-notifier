#!/usr/bin/env python3
"""Install or remove the Claude Code features of this repository.

Features (pick any):
  sound       sound when Claude finishes or asks a question (+ tab dot on macOS)
  statusline  status line: path (branch), tok/s, context usage, model · effort
  style       output style "Strukturiert" (skimmable German answers)

Only touches its own entries in ~/.claude/settings.json and writes a backup first.
Python 3.9+, standard library only, macOS and Windows.
"""
import argparse
import json
import os
import platform
import shutil
import sys
import time
from pathlib import Path

if sys.version_info < (3, 9):
    sys.exit("Python 3.9 or newer is required.")

REPO = Path(__file__).resolve().parent
FEATURES = {
    "sound": "Sound when Claude finishes or asks a question (+ tab dot on macOS)",
    "statusline": "Status line: path (branch), tok/s, context usage, model · effort",
    "style": "Output style 'Strukturiert': skimmable German answers",
}
HOOK_SCRIPT = "claude-notify.sh"
STATUSLINE_MARK = "statusline/statusline.py"
STYLE_SOURCE = REPO / "output-style" / "strukturiert.md"
STYLE_NAME = "Strukturiert"
TITLE_ENV = "CLAUDE_CODE_DISABLE_TERMINAL_TITLE"
ASK_MATCHER = "AskUserQuestion|ExitPlanMode"


def posix(path):
    """Forward slashes everywhere: Claude Code runs commands through Git Bash on Windows."""
    return Path(path).as_posix()


def hook_command(mode, os_name):
    script = posix(REPO / "hooks" / HOOK_SCRIPT)
    runner = f'bash "{script}"' if os_name == "Windows" else f'"{script}"'
    return f"{runner} {mode} 2>/dev/null || true"


def hook_entries(os_name):
    """(event, matcher, mode). Windows has no tab dots, so only the sound events are needed."""
    entries = [("Stop", None, "stop"), ("PreToolUse", ASK_MATCHER, "ask")]
    if os_name != "Windows":
        entries += [("UserPromptSubmit", None, "start"), ("PostToolUse", ASK_MATCHER, "start")]
    return entries


def remove_sound(settings):
    hooks = settings.get("hooks")
    if isinstance(hooks, dict):
        for event in list(hooks):
            groups = []
            for group in hooks[event] if isinstance(hooks[event], list) else []:
                inner = [h for h in group.get("hooks", []) if HOOK_SCRIPT not in str(h.get("command", ""))]
                if inner:
                    groups.append({**group, "hooks": inner})
            if groups:
                hooks[event] = groups
            else:
                del hooks[event]
        if not hooks:
            del settings["hooks"]
    env = settings.get("env")
    if isinstance(env, dict) and env.get(TITLE_ENV) == "1":
        del env[TITLE_ENV]
        if not env:
            del settings["env"]


def add_sound(settings, os_name):
    remove_sound(settings)  # idempotent: never duplicate our hooks
    hooks = settings.setdefault("hooks", {})
    for event, matcher, mode in hook_entries(os_name):
        group = {"matcher": matcher} if matcher else {}
        group["hooks"] = [{"type": "command", "command": hook_command(mode, os_name), "async": True}]
        hooks.setdefault(event, []).append(group)
    if os_name != "Windows":  # Claude's own tab title would overwrite the dot
        settings.setdefault("env", {})[TITLE_ENV] = "1"


def python_command():
    """The running Python; Apple's /usr/bin/python3 shim resolves into a versioned Xcode or
    Command Line Tools path that changes on every update, so keep the stable shim."""
    if "/Developer/" in sys.executable or "CommandLineTools" in sys.executable:
        return "/usr/bin/python3"
    return posix(sys.executable)


def statusline_command():
    return f'"{python_command()}" "{posix(REPO / "statusline" / "statusline.py")}"'


def add_statusline(settings):
    settings["statusLine"] = {"type": "command", "command": statusline_command()}


def remove_statusline(settings):
    if STATUSLINE_MARK in str((settings.get("statusLine") or {}).get("command", "")):
        del settings["statusLine"]


def style_target(claude_dir):
    return claude_dir / "output-styles" / STYLE_SOURCE.name


def add_style(settings, claude_dir, log):
    target = style_target(claude_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() != STYLE_SOURCE.read_bytes():
        backup = backup_path(target)
        shutil.copy2(target, backup)
        log(f"  existing {target.name} saved as {backup.name}")
    shutil.copyfile(STYLE_SOURCE, target)
    settings["outputStyle"] = STYLE_NAME


def remove_style(settings, claude_dir):
    if settings.get("outputStyle") == STYLE_NAME:
        del settings["outputStyle"]
    target = style_target(claude_dir)
    if target.exists() and target.read_bytes() == STYLE_SOURCE.read_bytes():
        target.unlink()  # only our unchanged copy; edited files stay


def backup_path(path):
    return path.with_name(f"{path.name}.bak-{time.strftime('%Y%m%d-%H%M%S')}")


def load_settings(path):
    if not path.exists():
        return {}
    try:
        settings = json.loads(path.read_text(encoding="utf-8") or "{}")
    except ValueError as error:
        sys.exit(f"{path} is not valid JSON ({error}); fix it first, nothing was changed.")
    if not isinstance(settings, dict):
        sys.exit(f"{path} does not contain a JSON object; nothing was changed.")
    return settings


def ask(question):
    answer = input(f"{question} [Y/n] ").strip().lower()
    return answer in ("", "y", "yes", "j", "ja")


def choose(args):
    chosen = [name for name in FEATURES if getattr(args, name)]
    if args.all:
        chosen = list(FEATURES)
    if chosen:
        return chosen
    if not sys.stdin.isatty():
        sys.exit("No feature chosen. Use --all or any of --sound --statusline --style.")
    verb = "Remove" if args.uninstall else "Install"
    return [name for name, text in FEATURES.items() if ask(f"{verb} {name}? {text}")]


def run(argv=None, os_name=None, log=print):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name, text in FEATURES.items():
        parser.add_argument(f"--{name}", action="store_true", help=text)
    parser.add_argument("--all", action="store_true", help="all three features")
    parser.add_argument("--uninstall", action="store_true", help="remove the chosen features")
    parser.add_argument("--claude-dir", type=Path,
                        default=Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude"),
                        help="Claude Code config folder (default: ~/.claude)")
    args = parser.parse_args(argv)
    os_name = os_name or platform.system()

    chosen = choose(args)
    if not chosen:
        log("Nothing chosen, nothing changed.")
        return 0
    if "sound" in chosen and os_name not in ("Darwin", "Windows") and not args.uninstall:
        log("Sound is only supported on macOS and Windows; skipping it.")
        chosen.remove("sound")
        if not chosen:
            return 0

    claude_dir = args.claude_dir
    path = claude_dir / "settings.json"
    settings = load_settings(path)
    for name in chosen:
        if args.uninstall:
            if name == "sound":
                remove_sound(settings)
            elif name == "statusline":
                remove_statusline(settings)
            else:
                remove_style(settings, claude_dir)
        elif name == "sound":
            add_sound(settings, os_name)
        elif name == "statusline":
            add_statusline(settings)
        else:
            add_style(settings, claude_dir, log)

    claude_dir.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = backup_path(path)
        shutil.copy2(path, backup)
        log(f"Backup: {backup}")
    path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log(f"{'Removed' if args.uninstall else 'Installed'}: {', '.join(chosen)} → {path}")
    log("Start a new Claude Code session to load the changes.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
