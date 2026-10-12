"""Check the delivery archives, including accidental-file leaks and browser parity."""
import json
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_archives_contain_only_the_runtime_payload(self):
        """A stale receipt/profile in a build directory must not become a download."""
        version = json.loads((ROOT / "extension/manifest.json").read_text())["version"]
        lock = json.loads((ROOT / "build/assets.lock.json").read_text())
        expected = {p.name for p in (ROOT / "extension").iterdir() if p.is_file()}
        expected.update({"media-assets.json", "THIRD_PARTY.md"})
        expected.update("vendor/" + name for name in lock["frontend"])
        expected.update("media/" + Path(name).name for name in lock["media"])
        with zipfile.ZipFile(ROOT / f"artifacts/songsterr-classic-{version}-chrome.zip") as chrome:
            self.assertIsNone(chrome.testzip())
            self.assertEqual(set(chrome.namelist()), {"INSTALL.txt"} | {"extension/" + n for n in expected})
            with zipfile.ZipFile(ROOT / f"artifacts/songsterr-classic-{version}-firefox.xpi") as firefox:
                self.assertIsNone(firefox.testzip())
                self.assertEqual(set(firefox.namelist()), expected | {"firefox-loader.js"})
                for name in expected - {"manifest.json"}:
                    self.assertEqual(chrome.read("extension/" + name), firefox.read(name), name)
                manifest = json.loads(firefox.read("manifest.json"))
                self.assertEqual(manifest["version"], version)
                self.assertNotIn("service_worker", manifest["background"])
                self.assertNotIn("debugger", manifest["permissions"])
                self.assertNotIn("webRequestBlocking", manifest["permissions"])


if __name__ == "__main__":
    unittest.main()
