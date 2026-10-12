"""Download the locked frontend files without cookies or browser profiles."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def fetch(item):
    group, name, record = item
    destination = ROOT / "artifacts/assets" / group / Path(name).name
    if destination.exists():
        data = destination.read_bytes()
    else:
        with urlopen(record["url"], timeout=30) as response:
            data = response.read()
    if hashlib.sha256(data).hexdigest() != record["sha256"]:
        raise ValueError(f"Asset does not match the lockfile: {name}")
    # Do not save a failed download or silently accept changed CDN content.
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)


def main():
    lock = json.loads((ROOT / "build/assets.lock.json").read_text())
    items = [(group, name, record) for group, assets in lock.items()
             for name, record in assets.items()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(fetch, items))
    print(f"Verified {len(items)} assets")


if __name__ == "__main__":
    main()
