"""Recover literal July static media; never enumerate song/account resources."""
import concurrent.futures
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "artifacts/api-audit-2026-10-12"
DEST = ROOT / "artifacts/july-media"


def main():
    DEST.mkdir(exist_ok=True)
    strings = json.loads((AUDIT / "additional-july-resource-strings.json").read_text())
    paths = sorted({s.split("#")[0] for s in strings if re.fullmatch(r"/static3/media/[\w.-]+(?:#[^/]*)?", s)})
    records, errors = {}, {}

    def recover(path):
        destination = DEST / Path(path).name
        url = "https://static3.songsterr.com/production-main" + path
        try:
            if destination.exists():
                data = destination.read_bytes()
            else:
                result = subprocess.run(["curl", "--fail", "--silent", "--show-error", "--max-time", "25", "--max-filesize", "10000000", url], capture_output=True, check=True)
                data = result.stdout
                destination.write_bytes(data)
            return path, {"url":url,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}, None
        except subprocess.CalledProcessError as error:
            return path, None, error.stderr.decode().strip()

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for path, record, error in pool.map(recover, paths):
            if error:
                errors[path] = error
            else:
                records[path] = record
    receipt = {"assets":records,"errors":errors,"scope":"Literal /static3/media paths; excludes song audio and dynamically constructed resources"}
    (ROOT / "artifacts/media-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"recovered":len(records),"errors":errors,"bytes":sum(r['bytes'] for r in records.values())}))


if __name__ == "__main__":
    main()
