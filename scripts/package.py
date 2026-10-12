"""Package only reviewed source and pinned assets, never browser/account state."""
import json
import zipfile
from build_local import ROOT, OUTPUT, build


def main():
    build()
    manifest = json.loads((OUTPUT / "manifest.json").read_text())
    destination = ROOT / "artifacts" / f"songsterr-classic-{manifest['version']}-chrome.zip"
    source_files = [path.name for path in (ROOT / "extension").iterdir() if path.is_file()]
    generated = ["media-assets.json", "THIRD_PARTY.md"]
    assets = json.loads((OUTPUT / "asset-list.json").read_text())
    media = json.loads((OUTPUT / "media-assets.json").read_text())
    names = set(source_files + generated)
    names.update("vendor/" + name for name in assets)
    names.update("media/" + path.rsplit("/", 1)[-1] for path in media)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(ROOT / "docs/chrome-install.txt", "INSTALL.txt")
        for name in sorted(names):
            archive.write(OUTPUT / name, "extension/" + name)
    print(destination)


if __name__ == "__main__":
    main()
