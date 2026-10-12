# Songsterr Classic — locally packaged July UI

A personal, opt-in Chrome/Firefox extension for the July 15, 2026 Songsterr interface
with live Songsterr song/account data.

**0.3.1 keeps one compact toggle, with reload guidance on hover/focus and project links.**
It remains a compatibility beta, not a completed all-functionality migration.

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

## One switch

- **ON:** July's interface, with editing enabled. Classic does not block API
  writes or WebSockets. The request adapters and track-identity patch run.
- **OFF:** remove this tab's asset redirects and reload today's interface.

The popup supports keyboard operation, reduced motion, pending/error states,
and explicit activation when upgrading a tab from the old blocked preview.
There is no separate read-only mode or fixed in-page preview banner.

Switching reloads the tab and can discard unsaved work. The setting is per-tab
and resets when Chrome restarts. Disable/uninstall also requires reloading open
Classic tabs. Real save/reopen, revision identity and conflict behavior remain
unverified; begin with a disposable private song.

The current-only features do not exist merely because the extension permits
their endpoints. All 184 patterns remain tracked; no all-functionality claim
is made. See the coverage ledger for the remaining feature and test work.

## Reproduce

Using the retained, hash-verified audit snapshot and media files:

```sh
python3 scripts/build_local.py
node --test tests/*.test.mjs
python3 scripts/popup_qa.py
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

## Firefox

[Firefox build, temporary installation and verification](docs/firefox.md).
The same source produces both browsers; Firefox adds one small asset loader
and a generated manifest. The unsigned XPI is a development install, not an
AMO release.

## Versioning

Versions describe this extension, not Songsterr. The initial preview was 0.1;
0.2 introduced local packaging and editing adapters; 0.3 replaced the two modes
with one toggle. 0.3.1 refines that popup without changing the API adapters.
The leading zero reflects the still-incomplete compatibility work.
