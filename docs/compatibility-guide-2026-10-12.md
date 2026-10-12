# Songsterr Classic: July → October compatibility and packaging guide

Date: 12 October 2026. Task: T604. Audit of the existing `32a19fc` preview;
the installed extension and Songsterr account were not changed.

## Decision in one screen

**Keep the July frontend. Do not load both application entry points.** Basic
autosave and export have promising unchanged request envelopes; we have not
proved they need a protocol translator. Track-identity preservation, revision
submission state, video synchronization and selected newer features need
explicit compatibility work before a complete editor can be certified.

**Package the archived JavaScript/CSS in the extension.** A real isolated Chrome
prototype served the original July bytes from extension storage at their
original URLs using `chrome.debugger` / `Fetch.fulfillRequest`. The source-domain
check stayed intact. The public song, mixer, synth controls and editor entry
worked. This is feasibility proof, not a shipped or fully offline extension.

**The current read-only limit is ours.** `extension/background.js` blocks all
Songsterr POST/PUT/PATCH/DELETE requests and WebSockets at priority 100. That
was a staging choice before testing persistence, not evidence of server
incompatibility. It also blocks `/api/edits/download`, a POST-based export.
No technical rule requires us to retain that blanket block in the finished app.

## Coverage and what “all APIs” means here

The complete discovered, hashed module graphs rooted at these entry points were
frozen and parsed, including lazy modules and background workers:

- July: `appClient-CQbxiWv10TmWc-Ge.js`; SHA-256
  `b4ca761f3337a126a5e9d2cbc74e9178b2a63c30aad85400fbc3c4ba20fbc064`.
- Current: `appClient-P7U-hXvJJNFfnZ30.js`, obtained from a fresh public song page.
  The full hash and every dependency hash are in `asset-receipt.json`.
- **212 July assets, 233 retrieved current assets; 124 + 138 JavaScript modules
  parsed successfully, with zero parser failures.**
- One current referenced WASM was unavailable:
  `stretch-DvwSRxsTOISjEyM3.wasm`. No corresponding July asset download failed.
- **190 distinct relative HTTP method/route patterns:** 156 July, 184 current;
  133 shared with the same extracted body/query/path/header field names,
  17 shared with extracted field differences, 6 July-only and 34 current-only.
- Placeholder names are kept literally. `/api/user/{profileName}` and
  `/api/user/{*}` count separately, although they may address the same server
  resource. This is a call-pattern count, not a count of distinct server handlers.
- The inventory also retains **37 July and 49 current unresolved-address call
  sites**, external HTTP patterns, worker transports and WebSocket clues.
  These include generic fetch wrappers, server-signed upload destinations and
  audio resource URLs, not 86 known broken APIs.

This is **all statically discovered client call sites within those graphs**,
not Songsterr's private server specification. Arbitrarily constructed URLs,
external dynamically loaded SDKs, remote bug-reporter modules and response
schemas cannot be exhaustively recovered from field-name extraction. No
authenticated editing, purchases, uploads, public posting or revision writes
were performed. Matching paths/field names do not prove matching values or
server acceptance. Missing current calls do not prove server removal.

See [the complete endpoint inventory](api-endpoint-inventory-2026-10-12.md).
Every row has old/current source file and character offsets, field differences
and an assessment. The JSON/CSV versions retain the full field sets.

## What works, what is a candidate, what needs adaptation

| Capability | Finding | Decision |
|---|---|---|
| Public current song in July layout | Actual browser proof: score renders, mixer opens, synth reports can-play/playing, editor toolbar opens | Works for the exercised public-song path. No API adapter identified |
| Search, revision list, video-point list, backing quota | Classic-phase GETs returned 200 for `/api/search`, `/api/meta/439/revisions`, `/api/video-points/439/9531578/list`, `/api/bt-request/quota` | These specific public reads worked; not certification of every query/account combination |
| Initial page bootstrap | July expects `state.artist`; current bootstrap omits it | Existing `compat.mjs` adapter already restores this UI object. Existing root rebuild handles server-rendered layout mismatch |
| Draft autosave and reload | Same POST envelope and GET `edits` / `version` consumer, including cursor tuple normalization | Best no-adapter candidate; still requires actual edit → save → reload/undo test |
| GP/MIDI export of edited score | Same `/api/edits/download` fields and blob response mode | No translator identified. Blanket POST block is immediate obstacle; endpoint acceptance and file reopening untested |
| Create/copy a song | `/api/song/from-parts`, `/api/song/copy`, `/api/edits/copy` remain | Candidate, not verified. Generic bodies, ownership and resulting metadata require a disposable-song test |
| Publish existing song | Same `PUT /api/song/{songId}/publish`, duplicate-409 handling | No envelope adapter identified; actual publication untested and not needed for this audit |
| Submit edited revision; track operations | Current adds track identities and notification preference; internal submission flow changed | Compatibility owner must preserve identities and save lifecycle. Adapter is recommended for structural edits unless safe backend inference is demonstrated |
| Manual/original-audio synchronization | Current edited-sync body differs materially: mode/parts/target/endTime replace or extend old part-based model | Needs semantic adapter for current behavior; legacy endpoint acceptance unknown |
| Song rename | Current `explanation` replaces `additionalCheckShown` | To match current semantics, add explanation input or use current UI. A boolean cannot be translated into meaningful text |
| Published-score chord detection | Current still has old null-body call as well as new edited-source call | Old mode remains a no-adapter candidate; edited-score mode needs snapshot support |
| Preferences | Same dictionary GET/PUT remain; new POST merge/import and owner-aware migration/serialized writes added | Not an automatic payload break. Test ordinary preferences; port lifecycle behavior before claiming cross-tab/account migration compatibility |
| AI bar completion | Same socket URL but new request IDs, measure counts and result matching | Stateful WebSocket adapter needed to reproduce current reconnect/multi-measure behavior |
| AI chat | Same socket URL and inspected chat-message envelope | Candidate only; response/function-call lifecycle not exhaustively certified; preview blocks socket |
| Credit-backed transcription/backing features | New quote/catalog/credit routes and expected-credit fields | Separate feature migration; not a prerequisite for editing notes. Use the current UI until quote/consent/result handling is implemented |
| Login, entitlements, account/payment settings | Some legacy calls absent, new credit/payment flows present | Unverified. Keep official current UI for these operations; retain actual account authorization rather than inventing defaults |

### The concrete edit/save path

1. July's editor creates an editing action. `StoreWorker-DAj6qVcM_zrkZ0K4.js`
   owns the score and action/undo stack used to save it.
2. Its HTTP client calls `POST /api/edits` with
   `{songId, revisionId, edits, lastVersion}`. Both builds use body compression
   and conditional retry behavior for signed-in autosave. The nested `edits`
   operation vocabulary is not proved compatible merely because this envelope
   matches.
3. Reopening fetches `GET /api/edits/{songId}/{revisionId}`. Both inspected
   consumers read `response.edits` and `response.version` and normalize legacy
   cursor tuple forms before replaying the stack.
4. Revision submission calls `POST /api/edits/saveRevision`. Both send song and
   base revision IDs, summary/type, parts, stringified lyrics and video points.
   Current code additionally sends `trackIdentities` and
   `revisionNotificationSubscribed`.
5. The extension's priority-100 block currently stops step 2 or 4 before the
   server sees it. That failure says nothing about payload compatibility.

The current worker (`StoreWorker-CkAXslXDlDmRdqI7.js`) derives track identities
from original track metadata plus the edited stack/pointer. This is not a field
we should fill with arbitrary array indices: reorder/add/delete and duplicate
instruments make identity different from position. A translator needs to know
which original track survived each operation, and how new tracks are represented.
Whether today's server safely infers identities for an old request remains an
open test, not a confirmed incompatibility.

Current save code also has queued operation/cleanup state, discarded-own-stack
handling via `DELETE /api/edits/{songId}`, explicit saved versions and 409
reconciliation. July mostly reschedules when a save is already in progress and
updates its stack version when the save completes. Concurrent-tab and
interrupted-save correctness therefore needs testing even when a one-note save
succeeds. Do not reproduce the current worker's DELETE as a blind workaround.

### Why importing “the new save function” is insufficient by itself

That function receives track identities and lifecycle state from the new
worker's callers. It does not reconstruct them from the old UI automatically.
The UI-to-worker event contract also changed: for example, revision submission
used a `silent` input and now has `publishing` and notification-related inputs.
Replacing the entire worker or running both main bundles would introduce more
state compatibility work than replacing a narrow HTTP seam.

For a real request adapter, intercept **inside the worker's request path**.
Replacing the page's `window.fetch` misses worker fetches. Existing Chrome
declarative request rules can allow/block/redirect, not rewrite JSON bodies.
The worker can gzip request bodies, so a lower network-level adapter must
decode/encode consistently and preserve retries, auth headers, error statuses
and response semantics. Prefer a small worker-bootstrap wrapper before the
original worker loads; prove same-origin/worker import rules in Chrome before
adopting that implementation. It is a design option, not a tested adapter here.

Do not modify song IDs, ownership, login state, entitlements or server permission
checks. A rejected save remains rejected and visible to the user; an adapter
must never turn an HTTP failure into a success toast.

### Other real deltas worth isolating

- **Video sync:** current code constructs different bodies for modes, using
  `parts` or `target` with start/end information. It also returns response data
  where the July edited-sync caller only awaited completion. Compare mode and
  response consumers, not just a `part` → `parts` rename.
- **Bar completion:** `/ws/autocomplete-bar` now includes `requestId` and
  optional `measureCount`; response dispatch checks request IDs and validates
  measure counts. July correlates using song/revision/cursor. Handle reconnect,
  cancellation and late responses as well as the initial start message.
- **AI chat:** `/ws/rag-chat` retains the inspected `chat_message` fields:
  text, turn ID, helpdesk flag and optional page URL, access key, tab context,
  attachment IDs, source conversation, client type and experiment fields.
  That does not establish equality of all server message types or tool calls.
- **New lyrics socket:** `/ws/lyrics-align` appears only in current modules.
  It is new functionality, not required for July note editing.
- **Upload:** `/api/upload/sign` still accepts purpose/name/type/size; the
  subsequent multipart XHR POST uses the returned destination and fields.
  That destination can be off `songsterr.com`, so the preview's domain-scoped
  block is not a universal “nothing can ever upload” guarantee. No upload was
  attempted. Future write policy must own the whole upload lifecycle.
- **Legacy-only calls:** profile wildcard naming, entitlement refresh, global
  notification settings, Stripe session polling, voice bootstrap and the
  auxiliary `/editor/.../chords/detect` call need individual treatment. Current
  code absence is not proof of a dead endpoint. Do not automatically replace
  global notification settings with per-song notification endpoints.
- **External code:** current `/api/bug-report` is a base URL passed into a
  dynamically loaded reporter, not one concrete endpoint. The exact reporter
  subroutes are outside the frozen hashed graph. Payment SDK/ad endpoints and
  signed storage/audio URLs are similarly not implied to be fully enumerated.

## Packaging July locally: tested architecture and trade-offs

### What is already on disk

The 212 recovered July JS/CSS/WASM assets total **9,783,233 bytes (~9.33 MiB)**.
The main root CSS is from an earlier July capture, not a proved exact stylesheet
match to the July 15 entry. The shared CSS is directly referenced by that entry.
The audit additionally identified **366 distinct JS string values referencing
`/static3/media/` or soundfont paths**. These include pictures/icons and possibly
dynamic strings; they are a packaging checklist, not 366 verified downloaded
files. CSS data URLs are already self-contained. Fonts, worklet/WASM paths,
service-worker/manifest URLs and audio assets still need explicit coverage.

### Why plain extension URLs are not the same thing

The entry stores `import.meta.url` and checks its source against a Songsterr
domain pattern; an extension URL triggers a delayed navigation away. This is
separate from the account/entitlement logic nearby. We did not patch it out.
Directly importing all vendor JS from `chrome-extension://...` is therefore
not a drop-in replacement. Moving the whole page to an extension origin also
changes cookies, CORS, worker loading and relative API URL behavior.

### Prototype that works without changing vendor bytes

The temporary extension uses the following path:

1. Keep the visible tab on `https://www.songsterr.com/...` and obtain fresh
   public page/bootstrap data normally. The existing compatibility bootstrap
   still clears the current server DOM and adapts `state.artist`.
2. Attach `chrome.debugger` to this opted-in tab. Intercept requests at the
   request stage, only on the static-asset URL patterns.
3. Match the requested old filename against an explicit local asset list,
   read its bytes from extension storage and answer with
   `Fetch.fulfillRequest`. The URL stays the original Songsterr URL.
4. Continue live song/account/audio requests unchanged. The vendor's
   `import.meta.url` check sees its expected URL while the JS bytes come from
   disk, not the CDN.

**Final isolated-run evidence:** 29 JavaScript request occurrences fulfilled
locally, zero mirror errors, unchanged public-song origin after the check's
delay, mixer open, synth can-play/playing state and editor toolbar open. These
included the application, common bundle, store worker, audio worker, mixer and
lazy editor modules. The final screenshot was inspected. All non-read requests
were blocked by the test context; the normal installed extension was untouched.
Two generic `Failed to fetch` page errors remained in the blocked-request test;
this is not a clean-console claim. An earlier run had a canceled interception;
the final repeated run recorded none.

Evidence: `bundled-prototype.json`, `bundled-prototype.png` and
`scripts/audit_bundle_probe.py`. Play/pause state is browser evidence, not a
human listening review. Local note mutation, save/reload and private songs
were not tested in this packaging proof.

**Costs:** the extension must declare Chrome's powerful `debugger` permission,
can show a debugging banner, and needs an explicit detach/restoration lifecycle.
DevTools or another debugger may detach/conflict depending on Chrome behavior;
test that interaction rather than promising seamless coexistence. Handle tab
closure, restore, service-worker suspension and browser restart. Do not attach
to unrelated tabs or expose API/auth responses to the asset mirror.

This does **not** prove operation with the entire CDN blocked. Unknown icons,
media, fonts, sound libraries and fetched audio may still use it. A completed
local package should fail visibly for missing pinned assets rather than
silently downloading them and claiming CDN independence. The packaging test
must eventually block the archived JS/CSS/WASM/media network paths and exercise
all supported screens. Normal live APIs/audio remain separate dependencies.

### What about embedding HTML too?

The useful UI HTML is generated by July's renderer; it need not be saved as a
giant static page. A small shell and the compatibility bootstrap can be bundled.
The initial server HTML currently also carries **fresh song, account and
configuration state**. Freezing that state would leave stale identities or
permissions, so keep fetching live state. Removing dependence on the *shape*
of that server HTML would require a separately verified bootstrap-data loader.

Recommendation: bundle JS, CSS, shell, workers and static media, retain the
Songsterr tab origin, and keep song/account data live. “Locally packaged
frontend” is achievable; “offline Songsterr with login, private songs and audio”
is a different product and is not established by this prototype.

## Migration sequence and acceptance criteria

These are implementation slices for T604, not a separate task-status ledger.

1. **Replace preview policy with explicit modes.** Keep read-only as an option;
   add tested editing mode instead of classifying every POST as a dangerous
   mutation. Account/payment flows can stay on current UI. Do not globally
   enable every write merely to make autosave work.
2. **Disposable private-song persistence proof.** Start from a backed-up,
   intentionally disposable private song. Change one note, save, reload,
   verify actual score, undo/redo, reopen in current UI. Compare decoded edit
   tuples and response versions. No adapter unless a concrete difference
   requires one. Retry after an interrupted request and test stale tabs.
3. **Revision/identity proof.** Submit a private revision, reopen in both UIs,
   then add/remove/reorder tracks, including two tracks using the same
   instrument. Check identities, notation, tuning, lyrics and video points.
   Preserve fields July does not understand, or block that unsupported edit
   with a clear explanation. Determine whether missing identity fields are
   safely handled by the server before implementing translation.
4. **Export and richer editing.** Permit the correct export POST; reopen the
   resulting GP/MIDI file and compare notes/durations. Test bends, ties,
   tuplets, tempo/time signatures and supported notation. Test failures, not
   just a success toast. Video-sync and rename get separate semantic adapters.
5. **Ship the local package.** Pin hash manifest; close the static-resource
   inventory; implement per-tab mirror attach/detach, missing-asset reporting,
   restart/restore and DevTools tests. Test without archived asset CDN access.
   Keep the existing installed release until this replacement is reviewable.

## Invariants and evidence

| Promise | Owner / enforcement | Evidence / remaining boundary |
|---|---|---|
| No real account writes during audit | Isolated fresh browser; context blocks non-GET/HEAD/OPTIONS; preview DNR retained | Probe script + receipt. No authenticated session imported |
| Comparison uses fixed bytes | Asset snapshot and SHA-256 receipt | Zero JS parse failures; one named current WASM gap |
| Request-shape equality is not overstated | Inventory labels and unresolved-call appendix | 133 candidates are not 133 certified APIs |
| Local asset proof uses genuine old code | Temporary extension reads retained bytes, original URLs kept | 29 local fulfill occurrences; application/worker included; no vendor patch |
| Source identity isn't account permission | Live origin/bootstrap; no entitlement-field changes | Public logged-out flow only; signed-in persistence still unverified |
| Existing installation stays unchanged | Prototype in temporary directory/profile, removed on close | Runtime extension files not edited; repository changes are audit tooling/docs |

## Reproduce and inspect

The scripts are audit utilities, not part of the shipped extension:

```sh
python3 scripts/audit_assets.py artifacts/api-audit-2026-10-12
# Install pinned acorn 8.15.0 + acorn-walk 8.3.4 in an isolated tools directory.
node scripts/audit_api.cjs artifacts/api-audit-2026-10-12 /absolute/parser/node_modules
python3 scripts/audit_bundle_probe.py
python3 scripts/render_api_audit.py
```

Do not overwrite this snapshot when comparing another deployment: use a new
dated evidence folder and deliberately adjust the report/probe owner paths.
`api-calls.json` contains source options/snippets; `endpoint-inventory.json`
and `.csv` contain every inventory row; `asset-receipt.json` is the byte-level
manifest. Vendor assets remain ignored locally and are not committed or
published as a public extension distribution.
