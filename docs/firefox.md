# Firefox build

Firefox and Chrome share the popup, API adapters, rule builder and pinned
frontend assets. `scripts/build_firefox.py` derives a Firefox package from the
Chrome output. The browser-specific changes are:

- MV3 `background.scripts` instead of Chrome's `background.service_worker`.
- A fixed Gecko ID and Firefox 140+ minimum.
- `firefox/loader.js`, a document-start loader on Songsterr pages only.

Firefox rejects the cross-origin app-module redirect to a `moz-extension` URL.
The loader checks whether Classic is enabled for its own tab, then replaces the
current app's entry element with the direct packaged bootstrap URL and points
the two root stylesheets at their packaged files. Existing per-tab redirect
rules stop the current app from executing while that happens. Imports,
workers, media and API adapters remain the same packaged payload as Chrome.
No debugger or response-rewriting permission is added. There is no alternate
Firefox editor implementation or copied account session.

## Build and use

With the retained hash-verified archive available locally:

```sh
python3 scripts/build_firefox.py
```

Output: `artifacts/songsterr-classic-0.3.1-firefox.xpi` and an unpacked
`artifacts/firefox-extension/` directory. In Firefox, open
`about:debugging#/runtime/this-firefox`, choose **Load Temporary Add-on**, and
select the XPI or the unpacked manifest. Open a Songsterr song and use the same
Classic switch.

This is an **unsigned development build**. Temporary installation lasts until
Firefox exits. A normal persistent installation in Firefox release requires
Mozilla signing; no signing or submission to Mozilla has been performed. The
repository intentionally excludes Songsterr's vendor assets.

## Verified scope

Firefox 150.0.3 was exercised visibly inside the existing 1920×1080
Xephyr/Weston desktop using a separate fresh profile. Mouse operation of the
native popup and its tooltip was checked through the isolated OpenClaw node.
The page/worker smoke uses Selenium through geckodriver and a temporary QA-only
addon that blocks Songsterr writes and archived assets still headed to the
network. That guard is not part of the delivered extension and is removed
before handing the test browser back.

The repeatable smoke is `scripts/firefox_qa.py`. It attaches to a **fresh QA
session**, never a personal browser, on an externally owned geckodriver server
started with `--allow-system-access`. Pass its session receipt:

```sh
python3 scripts/firefox_qa.py --session-file /path/to/qa-session.json
```

The JSON contains `sessionId` and `capabilities` from Selenium's new-session
response. Install the Firefox package first using the persistent local XPI
path, not a short-lived upload file. The test expects a 1920px content width
for the inspected fret coordinates. It checks app loading, unchanged account
bootstrap, mixer, synth playback, local note edit/undo/redo, OFF restoration,
and repeated activation. Screenshots and the receipt go to ignored
`artifacts/firefox-qa/`. Account saves, private revisions and the remaining
184-route compatibility work are still unverified.
