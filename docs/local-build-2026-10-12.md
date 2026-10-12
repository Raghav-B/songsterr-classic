# Songsterr Classic 0.3.0 — local compatibility candidate

This is a **compatibility beta, not a completed all-functionality migration**.
Task T604 continues to own the remaining work.

## What this package does

Open a live Songsterr song, then turn **Classic interface ON** in the extension popup.
Chrome redirects the frontend requests into this package. July's renderer
rebuilds the page using today's song/account bootstrap. Song data, account
permissions, recordings, sound libraries and other dynamic services remain
live; this is not offline Songsterr.

The candidate packages 212 pinned JS/CSS/WASM assets and 365 literal static
media files. `packaging-receipt.json` lists source/output hashes and the exact
vendor modifications. The stylesheet caveat remains: the root stylesheet is
from an earlier July capture, not a proved exact July 15 match.

**No Chrome debugger permission is used.** An ordinary extension redirect
changes the script address to `chrome-extension://...`. The build replaces
the pinned entry's one source-location reference with its canonical Songsterr
URL, so that module's location-dependent initialization still works. Other
modules import from the local package. This is a documented relocation change,
not the earlier byte-identical debugger/response-substitution prototype.
No login, subscription or authorization checks are patched.

SVG symbols need special treatment: a page's `<use>` cannot load the extension
origin like a normal `<img>`. `local-sprites.mjs` loads the archived symbol
definitions into a hidden SVG in the Songsterr document, namespaces their IDs
and updates use references to local fragments. The actual visible controls
and logo are checked for resolved symbols and nonempty geometry.

## Single toggle and external effects

- **ON:** July's interface with editing enabled. The extension redirects frontend
  assets but does not block API writes or WebSockets. Request adapters and the
  track-identity patch run; live save/reopen has not been certified. This is not
  a sandbox or payment/publication guard. Start with a disposable private song.
- **OFF:** remove this tab's rules and reload today's Songsterr interface.
- Switching reloads the tab and can discard unsaved changes. Other tabs remain
  unaffected. Session rules reset when Chrome restarts. Disabling/uninstalling
  also requires reloading any Classic page already open.
- A tab left in the old preview mode is shown as needing activation. Switching
  ON replaces its old rules, including the write blocks. It never silently
  changes that tab's write policy simply because the popup opened.
- The animated popup includes keyboard/focus handling, reduced-motion support,
  a pending state that prevents duplicate clicks, and actionable errors. Tab
  mutations are serialized so concurrent clicks cannot allocate duplicate
  Chrome network-rule IDs. No fixed preview banner covers the song.

The build does not introduce new controls for the 34 current-only call
patterns. Credits, notification preferences, newer synchronization modes,
preferences migration, moderation and save-conflict state are not claimed
complete. Restoring today's UI is a fallback, not evidence that those features
were ported into Classic.

## Implemented compatibility work

1. The existing bootstrap adapter restores the missing artist UI state and
   rebuilds the root rather than hydrating October's HTML.
2. A shared request adapter runs before both the page and score-worker code.
   It handles lightweight transcription lists, optional rename explanations
   and the current feedback payload. Unrelated requests/responses pass through;
   abort signals, credentials and server errors remain meaningful. Gzipped
   adapted requests are decoded and sent back as ordinary JSON.
3. The pinned worker preserves track hashes through July's own replay of
   add/remove/reorder actions and supplies those identities when submitting
   revisions. Tests compare July's patched replay with today's actual replay,
   including identical-instrument tracks and undo. It does not invent a
   revision-notification subscription choice.

## Verification and boundaries

- 16 offline tests cover bootstrap account-state preservation, transport,
  per-tab activation/restoration, preview upgrades and concurrent rule changes and actual frozen worker functions.
  These do not contact Songsterr.
- Isolated browser QA denies every non-read network request and denies the
  pinned archived CDN asset names; the harness never supplies frontend bytes.
- The real popup switch activates and restores the actual packaged extension.
  Separate popup checks cover keyboard input, reduced motion, old previews,
  unsupported pages and failed activation without pretending the state changed.
- Public-song rendering, mixer, synth play/pause, editor entry, local symbol
  rendering, fret entry (0 → 7), undo (7 → 0), redo (0 → 7), and restoring the
  current UI are exercised. These are local edits with server saves blocked.
  See the exact current
  `artifacts/local-qa/receipt.json` for additional checks and failures.
- Incidental original sprite requests can be attempted before the mutation
  observer rewrites them; the harness denies them. Resolved, visible local
  symbols are the proof of independence, not an assertion of zero attempts.
- Generic failed-fetch errors occur because writes are intentionally denied.
  Local note editing produces an honest failed-save notice, not fake success.
- Signed-in save/reload, private revision submission, structural edits on the
  server, conflicts, real export/reimport and advanced feature flows remain
  unverified. Permission to reuse the owner's login is still unanswered.
- No public revision, credit expenditure, payment, account mutation or copied
  authentication session was used in these checks. The test browser is muted.

The [184-route coverage ledger](route-coverage-2026-10-12.md) accounts for the
entire requested HTTP-pattern scope. It deliberately distinguishes static
candidates, offline adapter tests, observed public responses and certification.
There is no claim that all 184 work. New current-only features and semantic
migrations remain implementation work even after login permission is granted.

## Build, inspect and use

```sh
python3 scripts/build_local.py
node --test tests/*.test.mjs
python3 scripts/popup_qa.py
python3 scripts/local_qa.py
python3 scripts/coverage_report.py
python3 scripts/package.py
```

The builder uses the frozen, hash-verified audit snapshot and media receipt;
it fails on a changed asset or changed vendor patch seam. It does not fetch a
moving latest release. Vendor assets are ignored in Git and packaged only for
this personal extension. The ZIP contains no browser profile or credentials.

To test manually, extract the ZIP, open `chrome://extensions`, enable Developer
mode, choose Load unpacked and select its `extension` directory. Do not enable two Classic versions against the same tab. Before upgrading an
existing unpacked installation, finish or preserve edits: activating the new
version reloads the song. Keep the previous package for rollback.

## Invariants

| Promise | Enforced by | Evidence / boundary |
|---|---|---|
| One opted-in tab | Every DNR rule has tabIds; tab removal deletes owned rules | Local browser toggle and restoration; lifecycle regressions still require continued testing |
| Local immutable assets | build_local.py validates archived hashes and patch counts | Packaging receipt, archived-CDN-denied browser run |
| No debugger capability | manifest permissions | Browser harness asserts absence |
| Account authority remains server-owned | compat.mjs preserves user state; transport preserves responses | Tests and logged-out state comparison; signed-in verification pending |
| Track identity is not inferred from instrument | Actual original metadata and action-stack replay | Frozen-worker differential tests; server acceptance pending |
| Save errors stay errors | Fetch response is returned unchanged | Transport rejection tests; visible blocked-save notice |
| Test does not publish edits | Independent browser-context write denial | Public-only isolated QA; no account session reused |
