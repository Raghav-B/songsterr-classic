import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import vm from "node:vm";
import test from "node:test";

async function loadBackground(initialRules = [], initialStorage = {}, workerControlled = false) {
    let rules = structuredClone(initialRules);
    const storage = structuredClone(initialStorage);
    const reloads = [];
    let listener;
    const nav = {before:[], committed:[]};
    const scripted = [];
    const background = await readFile(new URL("../extension/background.js", import.meta.url), "utf8");
    const context = vm.createContext({URL, setTimeout, console:{error:() => {}}, fetch:async url => ({json:async () =>
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
        storage:{local:{
            get:async keys => Object.fromEntries(keys.filter(key => key in storage).map(key => [key, storage[key]])),
            set:async values => { Object.assign(storage, structuredClone(values)); },
        }},
        scripting:{executeScript:async ({target}) => {
            scripted.push(target.tabId);
            const result = workerControlled;
            workerControlled = false;
            return [{result}];
        }},
        webNavigation:{
            onBeforeNavigate:{addListener:(fn, filter) => nav.before.push({fn, filter})},
            onCommitted:{addListener:(fn, filter) => nav.committed.push({fn, filter})},
        },
    }});
    vm.runInContext(background, context);
    const fire = (list, details) => list.forEach(({fn}) => fn({frameId:0, ...details}));
    const isWorkerBlock = rule => rule.action.type === "block" && !rule.condition.tabIds;
    return {context, reloads, storage, scripted, rules:() => structuredClone(rules),
        tabRules:() => structuredClone(rules).filter(rule => !isWorkerBlock(rule)),
        // Commit follows the start of navigation, as in Chrome.
        navigate:(tabId, url) => { fire(nav.before, {tabId, url}); fire(nav.committed, {tabId, url}); },
        startOnly:(tabId, url) => fire(nav.before, {tabId, url}),
        commit:(tabId, url) => fire(nav.committed, {tabId, url}),
        settle:() => new Promise(resolve => setTimeout(resolve, 20)),
        message:(message, sender = {}) => new Promise(resolve => listener(message, sender, resolve))};
}

test("Classic allows editing and restoration leaves other tabs unchanged", async () => {
    // The real rule builder runs against a fake Chrome network-rule boundary.
    // ON must never block saves; OFF must remove only this tab's redirects.
    const harness = await loadBackground();
    await harness.context.changeTab(1, true);
    await harness.context.changeTab(2, true);
    const other = harness.tabRules().filter(rule => rule.condition.tabIds.includes(2));
    assert.ok(harness.tabRules().every(rule => rule.action.type === "redirect"));
    assert.ok(harness.rules().some(rule => rule.action.redirect?.extensionPath === "/bootstrap.mjs"));
    assert.ok(harness.rules().every(rule => rule.action.redirect?.extensionPath !== "/bootstrap-edit.mjs"));
    await harness.context.changeTab(1, false);
    assert.deepEqual(harness.tabRules(), other);
    assert.deepEqual(harness.reloads, [1, 2, 1]);
    await assert.rejects(harness.context.changeTab(3, true), /song page/);
    assert.deepEqual(harness.tabRules(), other);
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
    assert.ok(harness.tabRules().every(rule => rule.action.type === "redirect"));
});

test("simultaneous switches do not reuse global rule IDs and a rejected change does not poison the queue", async () => {
    // Two tabs allocate IDs from the same Chrome rule store. Exercise actual
    // concurrent calls and a failed operation followed by successful work.
    const harness = await loadBackground();
    await Promise.all([harness.context.changeTab(1, true), harness.context.changeTab(2, true)]);
    assert.ok(harness.tabRules().some(rule => rule.condition.tabIds.includes(1)));
    assert.ok(harness.tabRules().some(rule => rule.condition.tabIds.includes(2)));
    await assert.rejects(harness.context.changeTab(3, true), /song page/);
    await harness.context.changeTab(1, false);
    assert.ok(harness.tabRules().every(rule => rule.condition.tabIds.includes(2)));
});

test("content-script status uses its real sender tab, not a supplied other tab", async () => {
    // Firefox's document-start loader must never enable Classic on an inactive
    // tab by querying another tab's rules. The popup still supplies its tab ID.
    const harness = await loadBackground();
    await harness.context.changeTab(1, true);
    assert.equal((await harness.message({action:"status"}, {tab:{id:1}})).enabled, true);
    assert.equal((await harness.message({action:"status",tabId:1}, {tab:{id:2}})).enabled, false);
});

test("new song tabs stay per-tab by default", async () => {
    // Without the setting, opening another song must not change it.
    const harness = await loadBackground();
    await harness.message({action:"enable",tabId:1});
    harness.navigate(5, "https://www.songsterr.com/a/wsa/other-tab-s2");
    await harness.settle();
    assert.equal((await harness.message({action:"status",tabId:5})).enabled, false);
    assert.equal(harness.storage.classicOn, undefined);
});

test("keep-on-in-new-tabs puts new song tabs in Classic with one cache-bypassing reload", async () => {
    const harness = await loadBackground();
    await harness.message({action:"setEveryTab",everyTab:true});
    harness.navigate(5, "https://www.songsterr.com/a/wsa/other-tab-s2");
    assert.equal((await harness.message({action:"status"}, {tab:{id:5}})).enabled, true);
    assert.deepEqual(harness.reloads, [5]);
    // The reload navigates again; rules already exist, so no second reload.
    harness.navigate(5, "https://www.songsterr.com/a/wsa/other-tab-s2");
    await harness.settle();
    assert.deepEqual(harness.reloads, [5]);
});

test("popup OFF stops new tabs and is saved before its reload", async () => {
    const harness = await loadBackground([], {everyTab:true, classicOn:true});
    harness.navigate(1, "https://www.songsterr.com/a/wsa/test-tab-s1");
    await harness.settle();
    await harness.message({action:"disable",tabId:1});
    assert.equal(harness.storage.classicOn, false);
    // The OFF reload must not bring Classic straight back.
    harness.navigate(1, "https://www.songsterr.com/a/wsa/test-tab-s1");
    await harness.settle();
    assert.equal((await harness.message({action:"status",tabId:1})).enabled, false);
    harness.navigate(6, "https://www.songsterr.com/a/wsa/third-tab-s3");
    await harness.settle();
    assert.equal((await harness.message({action:"status",tabId:6})).enabled, false);
    await harness.message({action:"enable",tabId:1});
    assert.equal(harness.storage.classicOn, true);
});

test("auto-enable waits for the page to commit before reloading", async () => {
    const harness = await loadBackground([], {everyTab:true, classicOn:true});
    harness.startOnly(4, "https://www.songsterr.com/a/wsa/fast-s4");
    await harness.settle();
    assert.ok(harness.rules().some(rule => rule.condition.tabIds.includes(4)));
    assert.deepEqual(harness.reloads, []);
    harness.commit(4, "https://www.songsterr.com/a/wsa/fast-s4");
    await harness.settle();
    assert.deepEqual(harness.reloads, [4]);
});

test("auto-enable never starts Classic outside song pages", async () => {
    const harness = await loadBackground([], {everyTab:true, classicOn:true});
    harness.navigate(8, "https://www.songsterr.com/account");
    await harness.settle();
    assert.equal(harness.rules().length, 0);
});

test("turning the setting on makes Classic the default; off restores per-tab", async () => {
    const harness = await loadBackground();
    const on = await harness.message({action:"setEveryTab",everyTab:true});
    assert.equal(on.everyTab, true);
    assert.equal(on.classicOn, true);
    const off = await harness.message({action:"setEveryTab",everyTab:false});
    assert.equal(off.everyTab, false);
    harness.navigate(9, "https://www.songsterr.com/a/wsa/x-s9");
    await harness.settle();
    assert.equal(harness.rules().length, 0);
});

test("Songsterr's service worker is blocked once, and only its script", async () => {
    // The worker answers reloads from its own cache, outside any tab, where
    // per-tab redirects cannot apply. Only its script is blocked, never API calls.
    const harness = await loadBackground();
    await harness.context.changeTab(1, true);
    await harness.context.changeTab(2, true);
    const blocks = harness.rules().filter(rule => rule.action.type === "block");
    assert.equal(blocks.length, 1);
    const pattern = new RegExp(blocks[0].condition.regexFilter);
    assert.ok(pattern.test("https://www.songsterr.com/service-worker-latest.DvxnW9iJeZFYeqSN.js?cdn=x"));
    assert.ok(!pattern.test("https://www.songsterr.com/api/revision/1"));
    assert.ok(!pattern.test("https://www.songsterr.com/a/wsa/test-tab-s1"));
    assert.equal(blocks[0].condition.requestMethods, undefined);
});

test("a normal reload served by Songsterr's worker is reloaded past it once", async () => {
    const harness = await loadBackground([], {}, true);
    await harness.context.changeTab(1, true);
    harness.reloads.length = 0;
    harness.commit(1, "https://www.songsterr.com/a/wsa/test-tab-s1");
    await harness.settle();
    assert.deepEqual(harness.reloads, [1]);
    // That reload is not worker-served, so no second reload.
    harness.commit(1, "https://www.songsterr.com/a/wsa/test-tab-s1");
    await harness.settle();
    assert.deepEqual(harness.reloads, [1]);
});

test("tabs without Classic are never scripted or reloaded by the worker check", async () => {
    const harness = await loadBackground([], {}, true);
    harness.commit(3, "https://www.songsterr.com/a/wsa/test-tab-s1");
    await harness.settle();
    assert.deepEqual(harness.scripted, []);
    assert.deepEqual(harness.reloads, []);
});
