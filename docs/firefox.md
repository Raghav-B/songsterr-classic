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

After fetching the locked assets (see [development](development.md)):

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
Mozilla signing. Signing is on hold; the current package is not signed or
submitted. Follow the [README installation caveat](../README.md#firefox).
See [release preparation](releasing.md) for a future signed build. The
repository intentionally excludes Songsterr's vendor assets.

## Browser test

`scripts/firefox_qa.py` attaches to a fresh Selenium session in a caller-owned
Firefox desktop. Start geckodriver with `--allow-system-access`, create a new
profile/session, install the XPI using its persistent absolute path, then pass
a JSON file containing Selenium's `sessionId` and `capabilities`:

```sh
python3 scripts/firefox_qa.py --session-file /path/to/qa-session.json
```

The test expects a 1920px content width. It checks local loading, unchanged
account state, mixer, synth playback, note editing with undo/redo, OFF and repeat
activation. A temporary QA-only addon blocks writes and archived CDN requests;
it is removed in the cleanup path. It is never part of the release package.

Use only a fresh testing profile. The script leaves Firefox running. Test
screenshots and results are written to ignored `artifacts/firefox-qa/`.
Server save/reopen is a separate test and is not covered by this smoke.
