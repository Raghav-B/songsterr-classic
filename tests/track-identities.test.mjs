import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import vm from "node:vm";
import test from "node:test";

const source = await readFile(new URL("../extension/track-identities.js", import.meta.url), "utf8");
const context = vm.createContext({});
vm.runInContext(source, context);
const identities = (tracks, count) => {
    const result = context.classicTrackIdentities(tracks, count);
    return result === undefined ? undefined : Array.from(result);
};

test("Same-instrument tracks preserve their hashes after reorder, deletion and addition", () => {
    // Instrument equality cannot identify a track. The stack replay owns order.
    assert.deepEqual(identities([{partId:1,hash:"lead-a",instrumentId:27},{partId:0,hash:"lead-b",instrumentId:27},{partId:2,hash:undefined}],3), ["lead-b","lead-a",null]);
    assert.deepEqual(identities([{partId:0,hash:"lead-b"}],1), ["lead-b"]);
    assert.equal(identities([{partId:0,hash:""}],1), undefined);
});

test("A mismatch or duplicated position fails instead of sending misleading identities", () => {
    assert.throws(() => identities([{partId:0,hash:"a"}],2), /cannot match/);
    assert.throws(() => identities([{partId:0,hash:"a"},{partId:0,hash:"b"}],2), /ambiguous/);
});
