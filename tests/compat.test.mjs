import test from "node:test";
import assert from "node:assert/strict";
import { adaptState } from "../extension/compat.mjs";

test("the October-to-July adapter preserves server account and restriction data", () => {
    // An authenticated bootstrap may contain subscription credentials. The UI
    // adapter must not rewrite those or promote a free user to Plus.
    const state = {
        songs: { filters: { instrument: "GUITAR" }, list: [] },
        user: { isLoggedIn: true, hasPlus: false, profile: { id: 123, token: "test-only-token" } },
        meta: { current: { restriction: "test-restriction" } },
        experiments: { example: { segment: "off" } },
    };
    const original = structuredClone(state);
    const result = adaptState(state);
    assert.deepEqual(result.user, original.user);
    assert.deepEqual(result.meta, original.meta);
    assert.deepEqual(result.experiments, original.experiments);
    result.artist.filters.instrument = "BASS";
    assert.deepEqual(result.songs, original.songs);
});

test("an existing artist state survives adaptation unchanged", () => {
    // Older server responses already have this object; do not replace their
    // selected search or instrument when adapting a page twice.
    const artist = { pattern: "Metallica", filters: { instrument: "GUITAR" } };
    assert.equal(adaptState({ artist }).artist, artist);
});
