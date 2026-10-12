"""Build a personal, debugger-free July package from the pinned audit snapshot.

The one vendor relocation change gives the entry its canonical source URL.
Authentication, entitlement and API code are not replaced. The receipt records
both source and output hashes so the change cannot be mistaken for original bytes.
"""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "artifacts/api-audit-2026-10-12"
OUTPUT = ROOT / "artifacts/local-extension"
ENTRY = "appClient-CQbxiWv10TmWc-Ge.js"
CDN = "https://static3.songsterr.com/production-main/static3/latest/"


def build():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "extension", OUTPUT, dirs_exist_ok=True)
    (OUTPUT / "vendor").mkdir(exist_ok=True)
    records = {}
    pinned = json.loads((ROOT / "docs/asset-receipt-2026-10-12.json").read_text())["july"]["assets"]
    transport = (ROOT / "extension/transport.js").read_bytes()
    identities = (ROOT / "extension/track-identities.js").read_bytes()
    for name in sorted(pinned):
        source = AUDIT / "july" / name
        original = source.read_bytes()
        if hashlib.sha256(original).hexdigest() != pinned[name]["sha256"]:
            raise ValueError(f"Archived asset hash mismatch: {name}")
        data = original
        patches = []
        if source.name == ENTRY:
            if data.count(b"import.meta.url") != 1:
                raise ValueError("The pinned entry's relocation seam changed")
            data = data.replace(b"import.meta.url", json.dumps(CDN + ENTRY).encode())
            patches.append("Resolve the entry source-location reference to its canonical URL")
        if source.name in (ENTRY, "StoreWorker-DAj6qVcM_zrkZ0K4.js"):
            data = transport + b"\n" + data
            patches.append("Install the shared request adapter before page/score-worker startup")
        if source.name == "StoreWorker-DAj6qVcM_zrkZ0K4.js":
            replacements = {
                b"parts:s,lyrics:c,...p?{videoPoints:p}:{},type:m,gpImport:a}":
                    b"parts:s,trackIdentities:i||a||!t.draw.meta.originalTracks?undefined:globalThis.classicTrackIdentities(Yw({originalTracks:t.draw.meta.originalTracks,stack:t.history.stack,createAddedTrack:sL,stackPointer:t.history.pointer}).tracks,s.length),lyrics:c,...p?{videoPoints:p}:{},type:m,gpImport:a}",
                b"parts:e.parts,lyrics:e.lyrics.map(e=>JSON.stringify(e)),videoPoints:e.videoPoints}":
                    b"parts:e.parts,trackIdentities:e.trackIdentities,lyrics:e.lyrics.map(e=>JSON.stringify(e)),videoPoints:e.videoPoints}",
                b"if(r[1]===`a`&&a.splice(e,0,n(r[3],e)),r[1]===`r`":
                    b"if(r[1]===`a`&&a.splice(e,0,{...n(r[3],e),hash:r[4]?.hash}),r[1]===`r`",
            }
            for old, new in replacements.items():
                if data.count(old) != 1:
                    raise ValueError("The pinned score-worker identity seam changed")
                data = data.replace(old, new)
            data = identities + b"\n" + data
            patches.append("Preserve track hashes through July's existing stack replay and revision submission")
        (OUTPUT / "vendor" / source.name).write_bytes(data)
        records[source.name] = {
            "source_sha256": hashlib.sha256(original).hexdigest(),
            "packaged_sha256": hashlib.sha256(data).hexdigest(), "patches": patches,
        }

    manifest = json.loads((OUTPUT / "manifest.json").read_text())
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (OUTPUT / "asset-list.json").write_text(json.dumps(sorted(records), indent=2) + "\n")
    bootstrap = (OUTPUT / "bootstrap.mjs").read_text()
    (OUTPUT / "bootstrap.mjs").write_text(bootstrap)
    (OUTPUT / "bootstrap-edit.mjs").write_text(bootstrap)

    media = json.loads((ROOT / "docs/media-receipt-2026-10-12.json").read_text())["assets"]
    (OUTPUT / "media").mkdir(exist_ok=True)
    for path, record in media.items():
        data = (ROOT / "artifacts/july-media" / Path(path).name).read_bytes()
        if hashlib.sha256(data).hexdigest() != record["sha256"]:
            raise ValueError(f"Archived media hash mismatch: {path}")
        (OUTPUT / "media" / Path(path).name).write_bytes(data)
    (OUTPUT / "media-assets.json").write_text(json.dumps(sorted(media), indent=2) + "\n")
    (OUTPUT / "packaging-receipt.json").write_text(json.dumps(records, indent=2) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    build()
