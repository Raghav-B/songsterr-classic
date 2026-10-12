"""Recover publicly served, content-addressed July assets without credentials."""

import concurrent.futures
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "extension/vendor"
CDN = "https://static3.songsterr.com/production-main/static3/latest/"
ENTRY = "appClient-CQbxiWv10TmWc-Ge.js"
ENTRY_SHA = "b4ca761f3337a126a5e9d2cbc74e9178b2a63c30aad85400fbc3c4ba20fbc064"
# These stylesheet names were retained in our earlier browser HAR. Their
# compatibility with the July 15 JS is tested visually, not assumed exact.
STYLES = ["appClient-442d1888c9.css", "common-7b4ff45b27.css"]
ASSET = re.compile(r"(?<![\w-])([A-Za-z][A-Za-z0-9_-]*-[A-Za-z0-9_-]{8,}\.(?:js|css|wasm))(?![\w.])")


def fetch(name):
    path = DEST / name
    if not path.exists():
        result = subprocess.run(
            ["curl", "--fail", "--silent", "--show-error", "--location",
             "--max-time", "30", CDN + name], capture_output=True)
        if result.returncode:
            return name, None
        path.write_bytes(result.stdout)
    data = path.read_bytes()
    if name == ENTRY and hashlib.sha256(data).hexdigest() != ENTRY_SHA:
        raise RuntimeError("The July entry no longer matches the archived bytes")
    return name, data


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    pending = {ENTRY, *STYLES}
    seen, records, missing = set(), {}, []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        while pending:
            batch = sorted(pending - seen)
            if not batch:
                break
            seen.update(batch)
            pending = set()
            for name, data in pool.map(fetch, batch):
                if data is None:
                    missing.append(name)
                    continue
                records[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                if name.endswith((".js", ".css")):
                    pending.update(ASSET.findall(data.decode("utf-8")))
            print(f"Recovered {len(records)} assets; unavailable {len(missing)}", flush=True)
    (ROOT / "assets-manifest.json").write_text(json.dumps({
        "entry": ENTRY, "cdn": CDN, "styles": STYLES,
        "styleProvenance": "Main CSS from earlier July HAR; shared CSS referenced directly by July 15 JS. Exact July 15 main CSS hash was not cached.",
        "assets": records, "missing": sorted(missing),
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
