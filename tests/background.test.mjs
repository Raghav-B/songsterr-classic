import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import vm from "node:vm";
import test from "node:test";

async function loadBackground(initialRules = []) {
    let rules = structuredClone(initialRules);
    const reloads = [];
    let listener;
    const background = await readFile(new URL("../extension/background.js", import.meta.url), "utf8");
    const context = vm.createContext({URL, fetch:async url => ({json:async () =>
        url.endsWith("asset-list.json") ? ["worker-pinned.js"] : ["/static3/media/test.svg"]}), chrome:{
        declarativeNetRequest:{
            getSessionRules:async () => structuredClone(rules),
            updateSessionRules:async ({removeRuleIds=[],addRules=[]}) => {
                rules = rules.filter(rule => !removeRuleIds.includes(rule.id)).concat(structuredClone(addRules));
                assert.equal(new Set(rules.map(rule => rule.id)).size, rules.length);
            },
        },
        tabs:{
            get:async id => ({url:id === 3 ? "https://www.songsterr.com/account" : "https://www.songsterr.com/a/wsa/test-tab-s1"}),
            reload:async id => reloads.push(id), onRemoved:{addListener:() => {}},
        },
        runtime:{getURL:path => "chrome-extension://test/" + path,onMessage:{addListener:value => { listener = value; }}},
        action:{setBadgeText:async () => {},setBadgeBackgroundColor:async () => {}},
    }});
    vm.runInContext(background, context);
    return {context, reloads, rules:() => structuredClone(rules),
        message:(message, sender = {}) => new Promise(resolve => listener(message, sender, resolve))};
}

test("Classic allows editing and restoration leaves other tabs unchanged", async () => {
    // The real rule builder runs against a fake Chrome network-rule boundary.
    // ON must never block saves; OFF must remove only this tab's redirects.
    const harness = await loadBackground();
    await harness.context.changeTab(1, true);
    await harness.context.changeTab(2, true);
    const other = harness.rules().filter(rule => rule.condition.tabIds.includes(2));
    assert.ok(harness.rules().every(rule => rule.action.type === "redirect"));
    assert.ok(harness.rules().some(rule => rule.action.redirect?.extensionPath === "/bootstrap.mjs"));
    assert.ok(harness.rules().every(rule => rule.action.redirect?.extensionPath !== "/bootstrap-edit.mjs"));
    await harness.context.changeTab(1, false);
    assert.deepEqual(harness.rules(), other);
    assert.deepEqual(harness.reloads, [1, 2, 1]);
    await assert.rejects(harness.context.changeTab(3, true), /song page/);
    assert.deepEqual(harness.rules(), other);
});

test("activating Classic replaces stale preview blocks rather than preserving a hidden read-only mode", async () => {
    // Chrome can retain session rules across an extension update. Surface the
    // old preview honestly until the user's next ON explicitly replaces it.
    const harness = await loadBackground([{id:1,action:{type:"block"},condition:{tabIds:[1],requestMethods:["post"]}}]);
    const before = await harness.message({action:"status",tabId:1});
    assert.equal(before.legacyPreview, true);
    const result = await harness.message({action:"enable",tabId:1});
    assert.equal(result.enabled, true);
    assert.equal(result.legacyPreview, false);
    assert.ok(harness.rules().every(rule => rule.action.type === "redirect"));
});

test("simultaneous switches do not reuse global rule IDs and a rejected change does not poison the queue", async () => {
    // Two tabs allocate IDs from the same Chrome rule store. Exercise actual
    // concurrent calls and a failed operation followed by successful work.
    const harness = await loadBackground();
    await Promise.all([harness.context.changeTab(1, true), harness.context.changeTab(2, true)]);
    assert.ok(harness.rules().some(rule => rule.condition.tabIds.includes(1)));
    assert.ok(harness.rules().some(rule => rule.condition.tabIds.includes(2)));
    await assert.rejects(harness.context.changeTab(3, true), /song page/);
    await harness.context.changeTab(1, false);
    assert.ok(harness.rules().every(rule => rule.condition.tabIds.includes(2)));
});

test("content-script status uses its real sender tab, not a supplied other tab", async () => {
    // Firefox's document-start loader must never enable Classic on an inactive
    // tab by querying another tab's rules. The popup still supplies its tab ID.
    const harness = await loadBackground();
    await harness.context.changeTab(1, true);
    assert.equal((await harness.message({action:"status"}, {tab:{id:1}})).enabled, true);
    assert.equal((await harness.message({action:"status",tabId:1}, {tab:{id:2}})).enabled, false);
});
