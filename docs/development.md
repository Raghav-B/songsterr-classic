# Development

Python 3.10+ builds both browser packages. The source repository does not
contain Songsterr's frontend assets. Download the pinned files into the ignored
local cache, then build:

```sh
python3 scripts/fetch_assets.py
python3 scripts/package.py
python3 scripts/build_firefox.py
```

The fetcher uses no cookies or browser profile. It checks every file against
`build/assets.lock.json` and fails if the contents differ or a URL is no longer
available. The lockfile is a build dependency, not permission to redistribute
third-party assets; see [Third-party materials](../THIRD_PARTY.md).

## Outputs

- Chrome ZIP: `artifacts/songsterr-classic-0.3.1-chrome.zip`
- Firefox XPI: `artifacts/songsterr-classic-0.3.1-firefox.xpi`
- Unpacked Chrome: `artifacts/local-extension/`
- Unpacked Firefox: `artifacts/firefox-extension/`

Generated build evidence stays under ignored `artifacts/` and is not packaged.
The browser version comes from `extension/manifest.json`.

## Tests

Node 20+ runs the adapter and worker tests. The worker tests need a built local
payload; they execute its real replay/save functions without contacting a server.

```sh
npm ci
node --test tests/*.test.mjs
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
playwright install chromium
python3 scripts/popup_qa.py
python3 scripts/local_qa.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

Set `CLASSIC_CHROMIUM` only to use a different full Chromium executable.
The Chromium smoke uses a fresh profile and blocks server writes and archived
CDN downloads. It tests real extension loading, mixer/playback, local note
editing, undo/redo and switching back. It does not verify server persistence.

[Firefox testing](firefox.md) runs in a separate, caller-owned desktop profile.
Never use a personal profile for automated editing tests.

## Compatibility

Chrome redirects frontend requests to the local package. Firefox rejects some
cross-origin module redirects, so `firefox/loader.js` points the page directly
at the same local bootstrap and stylesheets. The popup, request adapters, score
worker and assets are shared. Neither build requests debugger access.

Only the source-location reference and specific compatibility seams are patched.
Login, subscription checks and server-side permissions remain Songsterr's.
When a server response changes, reproduce the failing flow and adapt that
specific difference rather than replacing the current service with fixtures.

## Versioning

Versions belong to this extension, not Songsterr. `0.3.1` is the current
pre-1.0 build. UI refinements and fixes increment the patch version; added
features increment the minor version. Packaging/documentation alone does not
need a runtime version bump.
