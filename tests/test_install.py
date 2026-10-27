"""Installer tests on a temporary Claude config folder; the real ~/.claude is never touched.

Run from the repository root: python3 -m unittest -v tests/test_install.py
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import install  # noqa: E402

OWN = {"model": "opus", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "my-own-hook.sh"}]}]},
       "env": {"KEEP": "1"}, "statusLine": {"type": "command", "command": "other-statusline"}}


class InstallerTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)
        self.settings = self.dir / "settings.json"
        self.settings.write_text(json.dumps(OWN))

    def run_installer(self, *args, os_name="Darwin"):
        return install.run([*args, "--claude-dir", str(self.dir)], os_name=os_name, log=lambda _: None)

    def load(self):
        return json.loads(self.settings.read_text(encoding="utf-8"))

    def commands(self, settings, event):
        return [h["command"] for g in settings.get("hooks", {}).get(event, []) for h in g["hooks"]]

    def test_all_on_macos_keeps_own_settings_and_is_idempotent(self):
        self.run_installer("--all")
        self.run_installer("--all")  # second run must not duplicate anything
        settings = self.load()
        self.assertEqual(settings["model"], "opus")
        self.assertEqual(settings["env"], {"KEEP": "1", install.TITLE_ENV: "1"})
        self.assertEqual(self.commands(settings, "Stop")[0], "my-own-hook.sh")
        for event in ("Stop", "PreToolUse", "UserPromptSubmit", "PostToolUse"):
            ours = [c for c in self.commands(settings, event) if install.HOOK_SCRIPT in c]
            self.assertEqual(len(ours), 1, event)
        self.assertIn(install.STATUSLINE_MARK, settings["statusLine"]["command"])
        self.assertEqual(settings["outputStyle"], "Strukturiert")
        self.assertEqual((self.dir / "output-styles" / "strukturiert.md").read_bytes(),
                         install.STYLE_SOURCE.read_bytes())
        self.assertTrue(list(self.dir.glob("settings.json.bak-*")))

    def test_windows_sound_uses_bash_and_only_sound_events(self):
        self.run_installer("--sound", os_name="Windows")
        settings = self.load()
        self.assertTrue(self.commands(settings, "Stop")[-1].startswith('bash "'))
        self.assertNotIn("\\", self.commands(settings, "Stop")[-1])
        self.assertNotIn("UserPromptSubmit", settings["hooks"])
        self.assertNotIn(install.TITLE_ENV, settings["env"])
        self.assertEqual(settings["statusLine"]["command"], "other-statusline")  # not chosen

    def test_uninstall_restores_own_settings(self):
        self.run_installer("--all")
        self.run_installer("--all", "--uninstall")
        settings = self.load()
        expected = {k: v for k, v in OWN.items() if k != "statusLine"}  # ours replaced it on install
        self.assertEqual(settings, expected)
        self.assertFalse((self.dir / "output-styles" / "strukturiert.md").exists())

    def test_edited_style_is_backed_up_and_kept_on_uninstall(self):
        target = self.dir / "output-styles" / "strukturiert.md"
        target.parent.mkdir()
        target.write_text("my edits")
        self.run_installer("--style")
        self.assertEqual(len(list(target.parent.glob("strukturiert.md.bak-*"))), 1)
        target.write_text("edited again")
        self.run_installer("--style", "--uninstall")
        self.assertEqual(target.read_text(), "edited again")

    def test_invalid_json_is_never_overwritten(self):
        self.settings.write_text("{ broken")
        with self.assertRaises(SystemExit):
            self.run_installer("--all")
        self.assertEqual(self.settings.read_text(), "{ broken")

    def test_missing_settings_file_is_created(self):
        self.settings.unlink()
        self.run_installer("--statusline")
        self.assertEqual(set(self.load()), {"statusLine"})


if __name__ == "__main__":
    unittest.main()
