import test from "node:test";
import assert from "node:assert/strict";
import { adaptState } from "../extension/compat.mjs";

test("the October-to-July adapter preserves server account and restriction data", () => {
    // An authenticated bootstrap may contain subscription credentials. The UI
    // adapter must not rewrite those or promote a free user to Plus.
    const state = {
        songs: {
            filters: { instrument: "GUITAR" }, defaultInstrument: 24,
            songs: { list: [], hasMore: true },
        },
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

test("October's nested search state produces an independent July artist list", () => {
    // October nests search results under songs.songs. July's header falls back
    // to artist.songs.list while a song is loading; copying the outer search
    // object instead makes that render throw before navigation completes.
    const state = {
        songs: {
            pattern: "Californication", defaultInstrument: 24,
            filters: { instrument: "ANY INSTRUMENTS", difficulty: "Any difficulty", tunings: {} },
            artists: { 12: { artistId: 12, name: "Red Hot Chili Peppers" } },
            songs: { list: [{ songId: 439, artistId: 12 }], hasMore: true },
        },
    };
    const original = structuredClone(state.songs);
    const { artist } = adaptState(state);
    assert.equal(artist.songs.list.find(song => song.songId === 439), undefined);
    assert.equal(artist.id, 0);
    assert.equal(artist.songs.id, 0);
    assert.equal(artist.loading, null);
    assert.equal(artist.defaultInstrument, 24);
    assert.equal(artist.songs.defaultInstrument, 24);
    assert.equal(artist.songs.hasMore, true);
    artist.songs.filters.tunings.GUITAR = "Drop D";
    assert.deepEqual(state.songs, original);
    assert.equal(artist.filters.tunings.GUITAR, undefined);
});
