"""Package the personal extension without account data or vendor JavaScript."""
import json
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
extension = root / "extension"
manifest = json.loads((root / "assets-manifest.json").read_text())
styles = sorted(name for name in manifest["assets"] if name.endswith(".css"))
(extension / "asset-list.json").write_text(json.dumps(styles, indent=2) + "\n")
destination = root / "artifacts/songsterr-classic-0.1.0.zip"
destination.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
    archive.write(root / "README.md", "README.md")
    for path in sorted(extension.iterdir()):
        if path.is_file():
            archive.write(path, "extension/" + path.name)
    for name in styles:
        archive.write(extension / "vendor" / name, "extension/vendor/" + name)
print(destination)
