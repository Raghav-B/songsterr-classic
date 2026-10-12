import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import vm from "node:vm";
import test from "node:test";
import {createRequire} from "node:module";

const require = createRequire(import.meta.url);
const acorn = require("acorn");
const walk = require("acorn-walk");

async function declarations(path, names) {
    const source = await readFile(new URL(path, import.meta.url), "utf8");
    const selected = [];
    walk.simple(acorn.parse(source, {ecmaVersion:"latest",sourceType:"module"}), {
        FunctionDeclaration(node) {
            if (names.includes(node.id?.name)) selected.push(source.slice(node.start,node.end));
        },
    });
    assert.equal(selected.length, names.length);
    return selected.join("\n");
}

test("Packaged stack replay preserves distinct track hashes through structural edits and undo", async () => {
    // Execute the real worker, not a duplicate adapter implementation. Expected
    // identities describe the edited score even when two instruments are equal.
    const july = await declarations("../artifacts/local-extension/vendor/StoreWorker-DAj6qVcM_zrkZ0K4.js", ["Jw","Gw","Hw","Uw","Ww"]);
    const context = vm.createContext({structuredClone, Kw:()=>{}, Vw:e=>e.name});
    vm.runInContext(july, context);
    const original = [{partId:0,hash:"same-instrument-a",instrumentId:27}, {partId:1,hash:"same-instrument-b",instrumentId:27}];
    const index = n => [n,0,0,0,0];
    const stack = [
        [[["p","mov",index(1),index(0)]]],
        [[["p","a",index(1),{instrumentId:27},{hash:"new-track-id"}]]],
        [[["p","r",index(2)]]],
    ];
    const createAddedTrack = (value, position) => ({...value,partId:position});
    const expected = [
        ["same-instrument-a", "same-instrument-b"],
        ["same-instrument-b", "same-instrument-a"],
        ["same-instrument-b", "new-track-id", "same-instrument-a"],
        ["same-instrument-b", "new-track-id"],
    ];
    for (const pointer of [0,1,2,3,2,1,0]) {
        const options = {createAddedTrack,stackPointer:pointer};
        const oldTracks = context.Jw(stack,original,options);
        assert.deepEqual(Array.from(oldTracks, track => track.hash), expected[pointer]);
    }
});

test("The packaged save function sends identities alongside unaltered score and lyrics", async () => {
    const source = await declarations("../artifacts/local-extension/vendor/StoreWorker-DAj6qVcM_zrkZ0K4.js", ["eZ"]);
    const requests = [];
    const context = vm.createContext({DetailedError:class extends Error {}, QX:{POST:async (path,options)=>{requests.push({path,options});return {data:{revisionId:99}};}}});
    vm.runInContext(source, context);
    const input = {songId:1,revisionId:2,summary:"QA",type:"edit",parts:[{notes:[7]}],trackIdentities:["original"],lyrics:[{text:"word"}],videoPoints:[]};
    const result = await context.eZ(input);
    assert.equal(result.success,true);
    assert.equal(requests[0].path,"/api/edits/saveRevision");
    assert.equal(requests[0].options.compression,true);
    const body = requests[0].options.body;
    assert.deepEqual(body.trackIdentities,input.trackIdentities);
    assert.deepEqual(body.parts,input.parts);
    assert.equal(body.lyrics[0],JSON.stringify(input.lyrics[0]));
});
