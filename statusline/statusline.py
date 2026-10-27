#!/usr/bin/python3
"""Pi-like footer: path (branch), last-message tok/s, context, chat-average tok/s, model · effort."""
import hashlib
import json
import math
import os
from datetime import datetime
from pathlib import Path
import sys
import tempfile

CACHE_DIR = Path.home() / ".claude" / "statusline-minimal" / "cache"
STATE_VERSION = 2
# Claude Code renders the status line indented and cuts it with "…" about 4 columns before the
# terminal edge (observed in PyCharm); one extra column keeps the effort level from being cut.
RIGHT_MARGIN = 5
# Restart reminder: context turns orange/red at these absolute token counts.
WARN_TOKENS = 200_000
ALERT_TOKENS = 250_000
ORANGE = "\033[38;5;208m"
RED = "\033[31m"
RESET = "\033[0m"


def positive_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(value) and value >= 0 else None


def compact_tokens(value):
    value = positive_number(value)
    if value is None:
        return "?"
    if value >= 1000000:
        return f"{value / 1000000:g}M"
    if value >= 1000:
        return f"{value / 1000:g}k"
    return f"{value:g}"


def context_text(data):
    context = data.get("context_window") or {}
    percent = positive_number(context.get("used_percentage"))
    used = "?" if percent is None else f"{percent:.1f}%"
    return f"{used}/{compact_tokens(context.get('context_window_size'))}"


def context_color(data):
    context = data.get("context_window") or {}
    percent = positive_number(context.get("used_percentage"))
    size = positive_number(context.get("context_window_size"))
    if percent is None or not size:
        return None
    used = percent * size / 100
    return RED if used >= ALERT_TOKENS else ORANGE if used >= WARN_TOKENS else None


def parse_time(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (AttributeError, ValueError):
        return None


def empty_state(identity=None):
    return {"version": STATE_VERSION, "offset": 0, "identity": identity, "previous": None, "messages": {}}


def load_state(path):
    try:
        state = json.loads(path.read_text())
        if state.get("version") == STATE_VERSION and isinstance(state.get("messages"), dict):
            return state
    except (OSError, ValueError, AttributeError):
        pass
    return empty_state()


def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".tps-")
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(state, stream)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def record_entry(line, state):
    """A message starts at the previous main-chain entry and ends at its last written block."""
    try:
        entry = json.loads(line)
        if entry.get("isSidechain"):
            return
        stamp = parse_time(entry.get("timestamp"))
        if stamp is None:
            return
        message = entry.get("message") or {}
        identifier = message.get("id")
        output = positive_number((message.get("usage") or {}).get("output_tokens"))
        if entry.get("type") == "assistant" and isinstance(identifier, str) and output is not None:
            known = state["messages"].get(identifier)
            if known is None:
                state["messages"][identifier] = [state["previous"], stamp, output]
            else:
                known[1] = max(known[1], stamp)
                known[2] = max(known[2], output)
        state["previous"] = stamp
    except (ValueError, TypeError, AttributeError):
        pass


def read_new_usage(transcript, state):
    with transcript.open("rb") as stream:
        info = os.fstat(stream.fileno())
        identity = [info.st_dev, info.st_ino]
        if state.get("identity") != identity or state.get("offset", 0) > info.st_size:
            state = empty_state(identity)
        stream.seek(state["offset"])
        while True:
            start = stream.tell()
            line = stream.readline()
            if not line.endswith(b"\n"):
                state["offset"] = start
                break
            record_entry(line, state)
            state["offset"] = stream.tell()
    return state


def rate(output, seconds):
    return f"~{output / seconds:.1f} tok/s" if output and seconds > 0 else "— tok/s"


def throughput_texts(data, cache_dir=CACHE_DIR):
    """Returns (last message, chat average); both include time to first token, hence `~`."""
    transcript = data.get("transcript_path")
    session = data.get("session_id")
    if not isinstance(transcript, str) or not isinstance(session, str):
        return "— tok/s", "Ø — tok/s"
    key = hashlib.sha256(f"{session}:{transcript}".encode()).hexdigest()
    cache = cache_dir / f"{key}.json"
    try:
        state = read_new_usage(Path(transcript), load_state(cache))
        save_state(cache, state)
    except (OSError, ValueError, TypeError):
        return "— tok/s", "Ø — tok/s"
    samples = [(end - start, output) for start, end, output in state["messages"].values()
               if start is not None and end > start and output]
    if not samples:
        return "— tok/s", "Ø — tok/s"
    seconds, output = samples[-1]
    total_seconds = sum(duration for duration, _ in samples)
    total_output = sum(tokens for _, tokens in samples)
    return rate(output, seconds), f"Ø {rate(total_output, total_seconds)}"


def git_branch(directory):
    path = Path(directory)
    for candidate in (path, *path.parents):
        git = candidate / ".git"
        try:
            if git.is_file():
                gitdir = git.read_text().strip().removeprefix("gitdir: ")
                git = (candidate / gitdir).resolve()
            head = (git / "HEAD").read_text().strip()
        except OSError:
            continue
        return head.removeprefix("ref: refs/heads/") if head.startswith("ref: ") else head[:7]
    return None


def location_text(data):
    directory = (data.get("workspace") or {}).get("current_dir") or data.get("cwd")
    if not isinstance(directory, str):
        return None
    home = str(Path.home())
    shown = "~" + directory[len(home):] if directory == home or directory.startswith(home + os.sep) else directory
    branch = git_branch(directory)
    return f"{shown} ({branch})" if branch else shown


def model_text(data):
    name = (data.get("model") or {}).get("display_name")
    effort = (data.get("effort") or {}).get("level")
    if not isinstance(name, str):
        return ""
    return f"{name} · {effort}" if isinstance(effort, str) and effort else name


def terminal_width():
    # Windows has no /dev/tty; CONOUT$ is the console of the calling Claude Code process.
    device, mode = ("CONOUT$", os.O_RDWR) if os.name == "nt" else ("/dev/tty", os.O_RDONLY)
    try:
        fd = os.open(device, mode)
        try:
            return os.get_terminal_size(fd).columns
        finally:
            os.close(fd)
    except OSError:
        pass
    try:
        return int(os.environ["COLUMNS"])
    except (KeyError, ValueError):
        return None


def align(left, right, width):
    if not right:
        return left
    gap = width - RIGHT_MARGIN - len(left) - len(right) if width else 0
    if gap >= 2:
        return left + " " * gap + right
    if width and len(left) + 2 + len(right) > width - RIGHT_MARGIN:
        return f"{left}\n{right}"
    return f"{left}  {right}"


def render(data, cache_dir=CACHE_DIR, width=None):
    last, average = throughput_texts(data, cache_dir)
    context = context_text(data)
    metrics = f"{last}  {context}  {average}"
    line = align(metrics, model_text(data), width)
    color = context_color(data)
    if color:  # after align: escape codes must not count as columns
        line = line.replace(f"  {context}  ", f"  {color}{context}{RESET}  ", 1)
    lines = [location_text(data), line]
    return "\n".join(line for line in lines if line)


def main():
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            return
        print(render(data, width=terminal_width()))
    except (ValueError, TypeError, AttributeError):
        print("— tok/s  ?/?  Ø — tok/s")


if __name__ == "__main__":
    main()
