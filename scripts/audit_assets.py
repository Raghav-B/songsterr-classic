"""Freeze the public module graph used by a Songsterr compatibility audit.

Only GET requests are issued. Existing archived July files are copied rather
than refreshed so comparison cannot silently replace the old evidence.
"""
import argparse
import concurrent.futures
import hashlib
import json
import re
import subprocess
from pathlib import Path

from recover_assets import ASSET, CDN, ENTRY, STYLES, DEST


def download(url):
    result = subprocess.run(
        ["curl", "--fail", "--silent", "--show-error", "--location",
         "--max-time", "30", url], capture_output=True, check=True)
    return result.stdout


def collect(label, entries, output, archived=False):
    directory = output / label
    directory.mkdir(parents=True, exist_ok=True)
    pending = set(entries)
    seen, records, failed = set(), {}, {}

    def fetch(name):
        try:
            source = DEST / name if archived else directory / name
            data = source.read_bytes() if source.exists() else download(CDN + name)
            (directory / name).write_bytes(data)
            return name, data, None
        except (OSError, subprocess.CalledProcessError) as error:
            return name, None, str(error)

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        while pending - seen:
            batch = sorted(pending - seen)
            seen.update(batch)
            for name, data, error in pool.map(fetch, batch):
                if error:
                    failed[name] = error
                    continue
                records[name] = {
                    "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                    "source": "retained-local" if archived and (DEST / name).exists() else CDN + name,
                }
                if name.endswith((".js", ".css")):
                    pending.update(ASSET.findall(data.decode("utf-8")))
            print(label, "assets", len(records), "failed", len(failed), flush=True)
    return {"entries": entries, "assets": records, "failed": failed}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    url = "https://www.songsterr.com/a/wsa/red-hot-chili-peppers-californication-tab-s439?sw=off"
    html = download(url)
    (args.output / "current-public-page.html").write_bytes(html)
    entries = list(dict.fromkeys(re.findall(r"appClient-[\w-]+\.js", html.decode())))
    if len(entries) != 1:
        raise RuntimeError(f"Expected one current entry, got {entries}")
    receipt = {
        "page": url,
        "scope": "Recursive hashed JS/CSS/WASM filenames referenced from the two entry graphs; not the server API specification.",
        "july": collect("july", [ENTRY, *STYLES], args.output, archived=True),
        "current": collect("current", entries, args.output),
    }
    (args.output / "asset-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
