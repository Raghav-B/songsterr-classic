# Songsterr Classic — locally packaged July UI

A personal, opt-in Chrome extension for the July 15, 2026 Songsterr interface
with live Songsterr song/account data. Task: T604.

**0.2.0 is an experimental compatibility candidate, not a complete migration.**
The normal Chrome installation remains on 0.1.0 until explicitly updated.

- [Build, installation, exact behavior and verification](docs/local-build-2026-10-12.md)
- [Every one of the 184 requested current HTTP patterns](docs/route-coverage-2026-10-12.md)
- [Original API audit and source references](docs/compatibility-guide-2026-10-12.md)
- [Endpoint-by-endpoint extracted request inventory](docs/api-endpoint-inventory-2026-10-12.md)

## Design

Keep the visible page on Songsterr and obtain its fresh bootstrap normally.
The extension redirects frontend assets to pinned local JS/CSS/WASM/media.
A small bootstrap adapts artist state and rebuilds the page root. SVG symbol
resources are embedded into the same document because cross-origin SVG use
references cannot load extension resources like ordinary images.

There is **no debugger permission**. The source-location relocation and score
worker patches are explicit and hash-recorded. Authentication, subscription
checks and server permissions are not changed. Live songs, audio and services
remain required; this is not an offline catalogue.

## Two modes

- **Preview** blocks Songsterr write methods and WebSockets. Local edits cannot
  be saved and will show a save error.
- **Experimental editing** allows live requests with the compatibility patches.
  It is not a sandbox. Use a disposable private test song only until actual
  save/reload, revision identity and conflict behavior are verified.

Both are per-tab. Restoring current UI removes that tab's rules and reloads.
Mode switches/reloads can discard unsaved work. Restarting Chrome clears the
session rules. Disable/uninstall also requires reloading open Classic tabs.

The current-only features do not exist merely because the extension permits
their endpoints. All 184 patterns remain tracked; no all-functionality claim
is made. See the coverage ledger for the remaining feature and test work.

## Reproduce

Using the retained, hash-verified audit snapshot and media files:

```sh
python3 scripts/build_local.py
node --test tests/*.test.mjs
python3 scripts/local_qa.py
python3 scripts/coverage_report.py
python3 scripts/package.py
```

The browser harness uses a fresh isolated profile, mutes output, denies writes
and denies archived asset CDN requests. It does not supply frontend bytes or
copy any normal browser session. The package contains no credentials/profile.

Vendor assets remain ignored in Git. Songsterr retains its rights in those
assets; this project is not affiliated with Songsterr and does not prepare a
Chrome Web Store/public distribution.
