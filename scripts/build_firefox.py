"""Derive Firefox from the exact Chrome payload; only the manifest differs."""
import json
import shutil
import zipfile
from build_local import ROOT, OUTPUT, build


def main():
    build()
    target = ROOT / "artifacts/firefox-extension"
    shutil.copytree(OUTPUT, target, dirs_exist_ok=True)
    manifest = json.loads((target / "manifest.json").read_text())
    # Firefox runs MV3 background scripts as an event page, not a service worker.
    shutil.copy2(ROOT / "firefox/loader.js", target / "firefox-loader.js")
    manifest["content_scripts"] = [{"matches": ["https://www.songsterr.com/*"], "js": ["firefox-loader.js"], "run_at": "document_start"}]
    manifest["background"] = {"scripts": ["background.js"], "type": "module"}
    manifest["browser_specific_settings"] = {"gecko": {
        "id": "songsterr-classic@raghavbhardwaj.com",
        "strict_min_version": "140.0",
        "data_collection_permissions": {"required": ["none"]},
    }}
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    archive = ROOT / "artifacts" / f"songsterr-classic-{manifest['version']}-firefox.xpi"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
        for path in sorted(target.rglob("*")):
            if path.is_file():
                package.write(path, path.relative_to(target))
    print(archive)


if __name__ == "__main__":
    main()
