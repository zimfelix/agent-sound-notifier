import json
from pathlib import Path
import tempfile
import unittest

from statusline import render


def stamp(seconds):
    return f"2026-10-09T08:00:{seconds:02d}.000Z"


class StatuslineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cache = self.root / "cache"
        self.transcript = self.root / "session.jsonl"
        self.data = {
            "session_id": "test-session", "transcript_path": str(self.transcript),
            "context_window": {"used_percentage": 25.5, "context_window_size": 200000},
            "model": {"id": "claude-opus-5-5", "display_name": "Opus 5.5"},
            "effort": {"level": "high"},
        }

    def write(self, entry, newline=True):
        with self.transcript.open("a") as stream:
            stream.write(json.dumps(entry) + ("\n" if newline else ""))

    def user(self, seconds, **extra):
        self.write({"type": "user", "timestamp": stamp(seconds), **extra})

    def assistant(self, identifier, output, seconds, **extra):
        self.write({"type": "assistant", "timestamp": stamp(seconds),
                    "message": {"id": identifier, "usage": {"output_tokens": output}}, **extra})

    def metrics(self, width=None):
        return render(self.data, self.cache, width).splitlines()[-1]

    def test_pi_layout_last_message_and_weighted_chat_average(self):
        self.user(0)
        self.assistant("a", 40, 1)
        self.assistant("a", 40, 2)  # second block of the same message: 40 tokens over 2 s
        self.assertEqual(self.metrics(), "~20.0 tok/s  25.5%/200k  Ø ~20.0 tok/s  Opus 5.5 · high")
        self.user(3)
        self.assistant("b", 80, 5)
        self.assistant("subagent", 1000, 6, isSidechain=True)
        self.assertTrue(self.metrics().startswith("~40.0 tok/s  25.5%/200k  Ø ~30.0 tok/s"))

    def test_right_alignment_and_narrow_fallback(self):
        self.user(0)
        self.assistant("a", 10, 1)
        wide = self.metrics(width=80)
        self.assertEqual(len(wide), 75)
        self.assertTrue(wide.endswith("Opus 5.5 · high"))
        narrow = render(self.data, self.cache, 30).splitlines()
        self.assertEqual(narrow[-1], "Opus 5.5 · high")

    def test_partial_line_is_processed_only_after_completion(self):
        self.user(0)
        self.assistant("a", 40, 2)
        self.write({"type": "assistant", "timestamp": stamp(3),
                    "message": {"id": "b", "usage": {"output_tokens": 30}}}, newline=False)
        self.assertTrue(self.metrics().startswith("~20.0 tok/s"))
        with self.transcript.open("a") as stream:
            stream.write("\n")
        self.assertTrue(self.metrics().startswith("~30.0 tok/s"))

    def test_missing_data_does_not_invent_a_rate(self):
        self.assertEqual(render({}, self.cache), "— tok/s  ?/?  Ø — tok/s")
        self.assertTrue(self.metrics().startswith("— tok/s  25.5%/200k  Ø — tok/s"))
        self.assistant("without-start", 50, 1)
        self.assertTrue(self.metrics().startswith("— tok/s"))

    def test_truncation_resets_cache(self):
        self.user(0)
        self.assistant("a-long-message-id", 1000, 1)
        self.metrics()
        self.transcript.write_text("")
        self.user(0)
        self.assistant("b", 20, 2)
        self.assertIn("Ø ~10.0 tok/s", self.metrics())

    def test_location_with_branch_and_model_without_effort(self):
        repo = self.root / "repo"
        (repo / ".git").mkdir(parents=True)
        (repo / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
        self.data["workspace"] = {"current_dir": str(repo / "sub")}
        del self.data["effort"]
        lines = render(self.data, self.cache).splitlines()
        self.assertEqual(lines[0], f"{repo / 'sub'} (main)")
        self.assertTrue(lines[1].endswith("  Opus 5.5"))

    def test_context_turns_orange_and_red_at_absolute_token_counts(self):
        self.data["context_window"] = {"context_window_size": 1000000}
        for percent, color in ((19.9, None), (20.0, "\033[38;5;208m"), (24.9, "\033[38;5;208m"), (25.0, "\033[31m")):
            self.data["context_window"]["used_percentage"] = percent
            line = self.metrics(width=80)
            text = f"{percent:.1f}%/1M"
            if color is None:
                self.assertNotIn("\033[", line)
            else:
                self.assertIn(f"{color}{text}\033[0m", line)
            visible = line.replace(color or "", "").replace("\033[0m", "")
            self.assertEqual(len(visible), 75)  # escape codes do not shift the alignment
        self.data["context_window"] = {"used_percentage": 100.0, "context_window_size": 200000}
        self.assertIn("\033[38;5;208m100.0%/200k", self.metrics())


if __name__ == "__main__":
    unittest.main()
