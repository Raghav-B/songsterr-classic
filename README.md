# Songsterr Classic — July preview

A personal, opt-in Chrome extension that renders the archived July 15, 2026
Songsterr interface on today's Songsterr song pages. Task: T604.

## Compatibility audit

The [12 October API and local-packaging guide](docs/compatibility-guide-2026-10-12.md)
compares 124 July and 138 current JavaScript modules and inventories 190 HTTP
route patterns. It separates static compatibility candidates from actual
browser evidence and records a successful extension-owned asset-loading
prototype. This does **not** enable writes or alter the installed preview.
The [endpoint-by-endpoint appendix](docs/api-endpoint-inventory-2026-10-12.md)
includes source offsets, field differences and unresolved dynamic calls.

## Install and use

1. Extract the delivered ZIP into a permanent folder (do not leave it in a ZIP).
2. Open `chrome://extensions`, enable **Developer mode**, choose **Load unpacked**,
   and select the extracted `extension` folder containing `manifest.json`.
3. Open a song on `https://www.songsterr.com/a/wsa/...`.
4. Click the extension's toolbar/puzzle-piece icon, then **Load July UI**.
5. **Restore current UI** reverses it and reloads that tab.

The switch is per tab, off by default, and resets when Chrome restarts. Other
tabs are not opted in. If disabling/removing the extension through Chrome's
extensions page, reload any Classic tabs immediately to restore the current UI.

**This release is a read-only compatibility preview, not a production editor.**
The local editor can open, but saving/publishing, uploads, account mutations,
and other non-read Songsterr HTTP requests are blocked while Classic is enabled.
Do not use this for unfinished work. Sign in and use account/payment settings
with Classic off. No Plus features are unlocked and no subscription checks are
patched. Signed-in/private-song use still needs the owner's first-use check.

## How it works

Opening a normal song gets today's HTML and account/song bootstrap from
Songsterr. Enabling Classic installs Chrome session network rules for just that
tab and reloads it. The rules replace the main script with `bootstrap.mjs` and
replace the stylesheet requests with retained July styles.

`compat.mjs` restores the old `artist` UI state from today's `songs` filters.
`bootstrap.mjs` empties only `#root`, because July's components cannot hydrate
October's server-rendered navigation correctly. It then imports the original
July app from its original pinned Songsterr CDN address. Imports and lazy
modules remain the original vendor code, fetched from Songsterr's domain.

The original client checks its module source domain. That check is **intact**;
local extension-hosted copies cannot replace the JS. Therefore this is not an
offline archive: it depends on Songsterr continuing to serve its pinned July
files and compatible song endpoints. Account rights and backend authorization
remain entirely Songsterr's responsibility.

### Asset provenance

- Entry: `appClient-CQbxiWv10TmWc-Ge.js`, originally captured July 16.
- SHA-256: `b4ca761f3337a126a5e9d2cbc74e9178b2a63c30aad85400fbc3c4ba20fbc064`.
- Root CSS: `appClient-442d1888c9.css`, identified in an earlier July HAR.
  The exact July 15 root stylesheet hash was not retained, so minor styling
  differences are possible; do not call this a byte-perfect full build restore.
- Shared CSS: `common-7b4ff45b27.css`, referenced by the July 15 app itself.
- `assets-manifest.json` records retrieved asset names and hashes.
- Vendor files are ignored in Git. The delivered extension includes only the
  archived styles it needs; JavaScript loads from Songsterr.

Songsterr retains all rights to its third-party assets. This repository's
wrapper is not affiliated with Songsterr; no vendor JavaScript is copied into
Tab Loop or committed here. No Chrome Web Store/public distribution is prepared.

## Invariants and checks

| Promise | Owner | Evidence |
| --- | --- | --- |
| One opted-in tab only | `background.js`, every rule has `tabIds` | Real extension QA and session-rule inspection |
| No server saves/publishing in preview | Chrome DNR blocks POST/PUT/PATCH/DELETE and Songsterr WebSockets | Harmless POST probe fails with `ERR_BLOCKED_BY_CLIENT` |
| Account rights unchanged | `compat.mjs` touches only missing `artist` | Unit fixture plus live logged-out bootstrap comparison |
| Original source-domain check intact | `bootstrap.mjs` imports original CDN URL | Browser stays on Songsterr; vendor entry SHA checked |
| Restore current UI | remove owned tab rules, reload bypassing cache | Real Chrome toggle-back check |
| No normal-profile QA mutation | isolated temporary Chromium profile | `scripts/extension_qa.py` owns creation and teardown |

## Rebuild and verify

```sh
python3 scripts/recover_assets.py
node --test tests/compat.test.mjs
python3 scripts/extension_qa.py
python3 scripts/package.py
```

Browser QA uses Python Playwright and the local Chromium installation. It opens
a public song while logged out and mutes physical audio. This proves browser
behaviour, not a human listening comparison. Runtime screenshots and detailed
receipts stay in ignored `artifacts/`.

### Verified 12 October 2026

The actual ZIP was extracted and loaded as an unpacked extension into an
isolated Chromium profile, not simulated with request interception:

- Current public Californication tab renders in the July layout, in dark mode.
- Track mixer opens; changing to bass and back to lead guitar succeeds.
- Synth player reports `data-can-play=true`, switches to pressed/playing,
  advances its visible playhead, and returns to paused on the next click.
- Editor mode opens with the old bottom toolbar. The first-use tutorial can
  appear; detailed note-editing/publishing flows are not certified.
- A harmless POST to `/__classic_write_probe__` is blocked by Chrome with
  `net::ERR_BLOCKED_BY_CLIENT`.
- A second Songsterr tab remains on the current frontend.
- Disabling Classic reloads the first tab onto the current frontend.
- Two state-adapter tests pass. The live logged-out account bootstrap is
  unchanged by adaptation.

Third-party ad/network errors occurred during public-site QA; these are not a
clean-network claim. Signed-in accounts, private drafts, original-audio
playback, downloads, long-session stability and complete editor behaviour
remain unverified. No Songsterr account was logged into or changed during QA.
