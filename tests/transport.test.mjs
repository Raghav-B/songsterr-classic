import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import vm from "node:vm";
import test from "node:test";

const source = await readFile(new URL("../extension/transport.js", import.meta.url), "utf8");

function runtime(location = {href: "https://www.songsterr.com/a/wsa/example-tab-s1", protocol: "https:", origin: "https://www.songsterr.com"}) {
    const sent = [];
    const response = new Response('{"version":7}', {status:409});
    const context = vm.createContext({Request, Response, Headers, URL, DecompressionStream, location,
        fetch: async request => {sent.push(request); return response;}});
    vm.runInContext(source, context);
    return {context, sent, response};
}

test("Autosave preserves compressed edits, authorization options and conflict response", async () => {
    // A 409 must reach July's own conflict handler, not become a fake success.
    const {context, sent, response} = runtime();
    const payload = JSON.stringify({songId:1, revisionId:2, edits:[[3, "change"]], lastVersion:6});
    const compressed = await new Response(new Blob([payload]).stream().pipeThrough(new CompressionStream("gzip"))).arrayBuffer();
    const result = await context.fetch("/api/edits", {method:"POST", body:compressed,
        headers:{"Content-Encoding":"gzip", "Content-Type":"application/json"}, credentials:"include"});
    assert.equal(result, response);
    assert.equal(sent[0].credentials, "include");
    assert.equal(sent[0].headers.get("Content-Encoding"), "gzip");
    assert.deepEqual(await sent[0].arrayBuffer(), compressed);
});

test("Optional rename explanation replaces the old boolean without inventing prose", async () => {
    const {context, sent} = runtime();
    await context.fetch("/api/song/1/rename", {method:"POST", body:JSON.stringify({toTitle:"New", toArtist:"Artist", additionalCheckShown:true})});
    assert.deepEqual(await sent[0].json(), {toTitle:"New", toArtist:"Artist", explanation:""});
});

test("Worker gzip feedback is decoded and retains only the current fields", async () => {
    // Blob workers have no relative-path base. Their origin is still the page's.
    const {context, sent} = runtime({href:"blob:https://www.songsterr.com/example", protocol:"blob:", origin:"https://www.songsterr.com"});
    const compressed = await new Response(new Blob([JSON.stringify({feedback:"positive", source:"tab"})]).stream().pipeThrough(new CompressionStream("gzip"))).arrayBuffer();
    await context.fetch("/api/rag-chat/test/message/1/feedback", {method:"PATCH", body:compressed, headers:{"Content-Encoding":"gzip"}});
    assert.deepEqual(await sent[0].json(), {feedback:"positive"});
    assert.equal(sent[0].headers.get("Content-Encoding"), null);
});

test("Explicit transcription query values are preserved and cancellation stays attached", async () => {
    const {context, sent} = runtime();
    const controller = new AbortController();
    await context.fetch("/api/contributions/transcriptions", {signal:controller.signal});
    assert.equal(new URL(sent[0].url).searchParams.get("withResults"), "false");
    controller.abort();
    assert.equal(sent[0].signal.aborted, true);
    await context.fetch("/api/contributions/transcriptions?withResults=true");
    assert.equal(new URL(sent[1].url).searchParams.get("withResults"), "true");
});

test("External uploads and unknown routes retain opaque bodies without JSON parsing", async () => {
    const {context, sent} = runtime();
    const body = new Uint8Array([0,255,1,2]);
    await context.fetch("https://storage.example/upload", {method:"POST", body});
    assert.deepEqual(new Uint8Array(await sent[0].arrayBuffer()), body);
    await context.fetch("/api/unrecognized", {method:"POST", body});
    assert.deepEqual(new Uint8Array(await sent[1].arrayBuffer()), body);
});

test("Malformed adapter input fails before the remote request and preserves server failures", async () => {
    const {context, sent} = runtime();
    await assert.rejects(context.fetch("/api/song/1/rename", {method:"POST", body:"not json"}));
    assert.equal(sent.length, 0);
    const result = await context.fetch("/api/meta/1");
    assert.equal(result.status, 409);
});
