"""Build the shared browser payload from the hash-locked local asset cache."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "artifacts/assets"
OUTPUT = ROOT / "artifacts/local-extension"
ENTRY = "appClient-CQbxiWv10TmWc-Ge.js"
CDN = "https://static3.songsterr.com/production-main/static3/latest/"


def build():
    # Rebuild only this generated directory, so old files cannot leak into a ZIP.
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / "extension").iterdir():
        if source.is_file():
            shutil.copy2(source, OUTPUT / source.name)
    shutil.copy2(ROOT / "THIRD_PARTY.md", OUTPUT / "THIRD_PARTY.md")
    (OUTPUT / "vendor").mkdir(exist_ok=True)
    records = {}
    lock = json.loads((ROOT / "build/assets.lock.json").read_text())
    pinned = lock["frontend"]
    transport = (ROOT / "extension/transport.js").read_bytes()
    identities = (ROOT / "extension/track-identities.js").read_bytes()
    for name in sorted(pinned):
        source = CACHE / "frontend" / name
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

    media = lock["media"]
    (OUTPUT / "media").mkdir(exist_ok=True)
    for path, record in media.items():
        data = (CACHE / "media" / Path(path).name).read_bytes()
        if hashlib.sha256(data).hexdigest() != record["sha256"]:
            raise ValueError(f"Archived media hash mismatch: {path}")
        (OUTPUT / "media" / Path(path).name).write_bytes(data)
    (OUTPUT / "media-assets.json").write_text(json.dumps(sorted(media), indent=2) + "\n")
    (ROOT / "artifacts/build-receipt.json").write_text(json.dumps(records, indent=2) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    build()
