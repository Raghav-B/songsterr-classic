# Current-client route coverage — 12 October 2026

184 current-client HTTP call patterns; six July-only patterns excluded by user request

**Not complete: 0/184 end-to-end certified.** This is an implementation and evidence inventory, not a green checklist.

No authenticated save, public publication, payment, credit-spending or moderation was performed. Public 200 responses and offline adapter tests are not end-to-end certification.

| Implementation state | Count |
|---|---:|
| unchanged-request-candidate | 133 |
| current-feature-not-ported | 34 |
| semantic-review-open | 13 |
| adapter-tested-offline | 4 |

| Method | Pattern | Implementation | Public response evidence | Remaining boundary / adapter |
|---|---|---|---|---|
| DELETE | `/actions/usertest/ticket` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| DELETE | `/api/edits/{songId}` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. NOT implemented: current draft-discard lifecycle; do not blindly DELETE drafts as a conflict workaround. |
| DELETE | `/api/favorites/{songId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| DELETE | `/api/playlist/{playlistId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| DELETE | `/api/playlist/{playlistId}/song/{songId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| DELETE | `/api/revision/{revisionId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| DELETE | `/api/song/{songId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| DELETE | `/api/video-points/{songId}/{revisionId}/{id}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/actions/usertest/get_usertest/{identifier}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/actions/usertests/screeners` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/artist/autocomplete` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/artist/{artistId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/artist/{artistId}/search` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/audio/{songId}/{revisionId}/export` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/autocomplete-bar/limits` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/bt-request/quota` | unchanged-request-candidate | 200 /api/bt-request/quota | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/bt-request/reset-eligibility` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| GET | `/api/chords/{songId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/chords/{songId}/{chordsRevisionId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/comment/revision/{revisionId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/comment/revision/{revisionId}/suggest` | semantic-review-open | None | Extracted request fields differ; endpoint-specific UI/state/response verification still needed. Current extra instruction is optional in the actual caller; no translation identified for July's text-only mode. |
| GET | `/api/comment/{commentId}/translate` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/contributions/available-transcriptions-count` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/contributions/songs` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/contributions/transcriptions` | adapter-tested-offline | None | transport.js: withResults=false; explicit query preserved |
| GET | `/api/contributions/transcriptions/{transcriptionId}/result` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| GET | `/api/credits/balance` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| GET | `/api/credits/catalog` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| GET | `/api/edits/{songId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. NOT implemented: current draft-discard lifecycle; do not blindly DELETE drafts as a conflict workaround. |
| GET | `/api/edits/{songId}/mine` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| GET | `/api/edits/{songId}/{revisionId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. Compare replayed note/undo state after actual private-song save and reload. |
| GET | `/api/experiments` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| GET | `/api/faq` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/favorites` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/help/commands` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/help/suggestions` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/inbox/items` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/inbox/items/items-with-num-unread` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/inbox/items/num-unread` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/meta/{songId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/meta/{songId}/revisions` | unchanged-request-candidate | 200 /api/meta/439/revisions | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/meta/{songId}/{revisionId}` | unchanged-request-candidate | 200 /api/meta/439/revisions | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/onboarding` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/part-switching-markers/{songId}/{revisionId}` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| GET | `/api/playlist` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/preference` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. NOT lifecycle-migrated: old dictionary GET/PUT exist; owner-aware import, migration and serialized writes are still missing. |
| GET | `/api/rag-chat/latest` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/rag-chat/{accessKey}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/requests/song-tasks` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/revision-notification/{songId}` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| GET | `/api/revision/{revisionId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/revision/{revisionId}/translate` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/search` | unchanged-request-candidate | 200 /api/search | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/song/copy/suggest-title` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/song/{songId}/main-video-request` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| GET | `/api/tags` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/tags/{tag}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/textpage/{slug}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/user/{*}` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. Wildcard naming may address the same profile resource as July's profileName; encoded/nested names need testing. |
| GET | `/api/useraudio/{songId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/api/video-points/{songId}/{revisionId}/list` | unchanged-request-candidate | 200 /api/video-points/439/9531578/list | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/atp-providers.csv` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/auth/billing/settings` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/auth/profile` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/auth/stripe/settings` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| GET | `/chat-api/fingering-ruleset/versions` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| GET | `/chat-api/fingering-ruleset/versions/{version}` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| GET | `/fingering-corpus` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| GET | `/version` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| PATCH | `/api/part-switching-markers/{songId}/{revisionId}` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| PATCH | `/api/rag-chat/{accessKey}/message/{messageId}/feedback` | adapter-tested-offline | None | transport.js: omit obsolete source field; plain/gzip bodies tested |
| PATCH | `/auth/profile` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/actions/usertest/ticket/idle` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/actions/usertest/{identifier}/ticket` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/billing/cancellation-flow` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| POST | `/api/bt-request/reset` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| POST | `/api/chords/{revisionId}/detect` | semantic-review-open | None | Extracted request fields differ; endpoint-specific UI/state/response verification still needed. Published-score null-body mode remains; current edited-score source needs an additional feature flow. |
| POST | `/api/comment` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/comment/approve/{commentId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/comment/block/{commentId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/credits/song/regenerate-transcription` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| POST | `/api/credits/song/transcribe-file-song` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| POST | `/api/credits/song/transcribe-song` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| POST | `/api/credits/song/transcribe-track` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| POST | `/api/credits/transcription-file-quote` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| POST | `/api/credits/transcription-quote` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| POST | `/api/edits` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. Real draft persistence, interrupted save and concurrent-tab conflict reconciliation remain unverified. |
| POST | `/api/edits/copy` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/edits/download` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. Check real GP/MIDI download and reopen; blob response is currently passed unchanged. |
| POST | `/api/edits/saveRevision` | adapter-tested-offline | None | build_local.py + track-identities.js: actual worker replay preserves identities; notification preference is not fabricated |
| POST | `/api/event` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/experiments` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| POST | `/api/inbox/item/{itemId}/set-read` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/inbox/items/set-all-read` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/mixpanel/unknown-event` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/moderation-separation/start` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/onboarding` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/part-switching-markers/migrate` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| POST | `/api/part-switching-markers/{songId}/{revisionId}/resolve-imports` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| POST | `/api/playlist` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/playlist/{playlistId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/preference` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. NOT lifecycle-migrated: old dictionary GET/PUT exist; owner-aware import, migration and serialized writes are still missing. |
| POST | `/api/preference/migrate-local` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| POST | `/api/rag-chat` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/rag-chat/attachment` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/rag-chat/clear-history` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/rag-chat/function-call` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/rag-chat/prefill` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/rag-chat/{accessKey}/turns/{turnId}/part-snapshot` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/requests/next` | semantic-review-open | None | Extracted request fields differ; endpoint-specific UI/state/response verification still needed. Current explicitly supplies allowLowPriority; queue default semantics have not been verified. |
| POST | `/api/requests/stop` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/revision/refresh` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/revision/{revisionId}/approve` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/revision/{revisionId}/deactivate` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/revision/{revisionId}/recover` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/revision/{revisionId}/reject` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/revision/{revisionId}/unblock` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/song/check-duplicate` | semantic-review-open | None | Extracted request fields differ; endpoint-specific UI/state/response verification still needed. Generic body extraction differs; actual metadata/video query remains a candidate, not a demonstrated break. |
| POST | `/api/song/copy` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/song/from-parts` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/song/regenerate-transcription` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/song/rename/{requestId}/solve` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/song/transcribe-file-song` | semantic-review-open | None | Extracted request fields differ; endpoint-specific UI/state/response verification still needed. |
| POST | `/api/song/transcribe-song` | semantic-review-open | None | Extracted request fields differ; endpoint-specific UI/state/response verification still needed. |
| POST | `/api/song/transcribe-track` | semantic-review-open | None | Extracted request fields differ; endpoint-specific UI/state/response verification still needed. |
| POST | `/api/song/transcription/process` | semantic-review-open | None | Extracted request fields differ; endpoint-specific UI/state/response verification still needed. |
| POST | `/api/song/{songId}/recover` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/song/{songId}/rename` | adapter-tested-offline | None | transport.js: optional explanation; omit additionalCheckShown; no invented prose |
| POST | `/api/song/{songId}/request` | semantic-review-open | None | Extracted request fields differ; endpoint-specific UI/state/response verification still needed. |
| POST | `/api/songs/{songId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/sound/cleanup` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/sound/generate` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/teacher-plan-requests` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| POST | `/api/upload/proxy` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/upload/sign` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/useraudio` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/video-points/manual` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/video-points/process` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/video-points/suggest` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/video-points/switch-main-to-alt` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/video-points/{songId}/alt-video` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/video-points/{songId}/auto` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/video-points/{songId}/edited` | semantic-review-open | None | Extracted request fields differ; endpoint-specific UI/state/response verification still needed. NOT adapted: current mode/parts/target/endTime and response lifecycle require UI/state migration, not a field rename. |
| POST | `/api/video-points/{songId}/{revisionId}/{id}/verify` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/video/report` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/video/report/{reportId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/api/video/report/{reportId}/reply` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/apple-token` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/billing/cancel` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/billing/migrate` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/billing/update` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/billing/upgrade/pro` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/bonus/activate-minutes` | semantic-review-open | None | Extracted request fields differ; endpoint-specific UI/state/response verification still needed. |
| POST | `/auth/bonus/purchase-feature` | semantic-review-open | None | Extracted request fields differ; endpoint-specific UI/state/response verification still needed. |
| POST | `/auth/change/email/confirm` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/change/email/request` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/change/password` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/coupon` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/credits/migration-request` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| POST | `/auth/deactivate` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/google-token` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/password/forgot` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/paypal/activate-subscription` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/paypal/cancel` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/paypal/create-subscription` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/signin` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/signout` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/signup` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/stripe/cancel` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/stripe/portal` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/stripe/subscribe/embedded` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/stripe/subscription/status` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/stripe/upgrade/pro` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/auth/stripe/upgrade/pro/authenticate` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| POST | `/chat-api/fingering-ruleset/versions` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| POST | `/feedback/web` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| POST | `/version/reload?via={dynamic}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| PUT | `/api/favorites/{songId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| PUT | `/api/playlist/{playlistId}/order` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| PUT | `/api/playlist/{playlistId}/song/{songId}` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| PUT | `/api/preference` | semantic-review-open | None | Extracted request fields differ; endpoint-specific UI/state/response verification still needed. NOT lifecycle-migrated: old dictionary GET/PUT exist; owner-aware import, migration and serialized writes are still missing. |
| PUT | `/api/revision-notification/{songId}` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |
| PUT | `/api/song/{songId}/publish` | unchanged-request-candidate | None | Pass-through; field equality is not response, authorization, or end-to-end verification. |
| PUT | `/api/teacher-plan-requests/{id}/follow-up` | current-feature-not-ported | None | July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL. |

Source offsets for every row are retained in the companion JSON and the original endpoint inventory.
WebSocket protocols (bar completion, chat, lyrics), opaque signed uploads, dynamic SDK calls and full response schemas are outside the 184-pattern count and still need separate proof.
