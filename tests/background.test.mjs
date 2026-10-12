import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import vm from "node:vm";
import test from "node:test";

test("Preview, experimental editing and restoration preserve another tab's rules", async () => {
    // Execute the real rule builder against Chrome's API boundary. No browser
    // network or account writes occur; this verifies mode/isolation policy.
    let rules = [];
    const reloads = [];
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
        runtime:{getURL:path => "chrome-extension://test/" + path,onMessage:{addListener:() => {}}},
        action:{setBadgeText:async () => {},setBadgeBackgroundColor:async () => {}},
    }});
    vm.runInContext(background, context);
    await context.changeTab(1, true);
    await context.changeTab(2, true);
    const other = JSON.stringify(rules.filter(rule => rule.condition.tabIds.includes(2)));
    const first = rules.filter(rule => rule.condition.tabIds.includes(1));
    assert.equal(first.filter(rule => rule.action.type === "block").length, 2);
    assert.deepEqual(Array.from(first.find(rule => rule.condition.requestMethods)?.condition.requestMethods), ["post","put","patch","delete"]);
    await context.changeTab(1, true, "editing");
    assert.ok(rules.filter(rule => rule.condition.tabIds.includes(1)).every(rule => rule.action.type !== "block"));
    assert.equal(JSON.stringify(rules.filter(rule => rule.condition.tabIds.includes(2))), other);
    assert.ok(rules.some(rule => rule.action.redirect?.extensionPath === "/bootstrap-edit.mjs"));
    await context.changeTab(1, false);
    assert.ok(rules.every(rule => !rule.condition.tabIds.includes(1)));
    assert.equal(JSON.stringify(rules), other);
    assert.deepEqual(reloads,[1,2,1,1]);
    await assert.rejects(context.changeTab(3, true), /song page/);
    await assert.rejects(context.changeTab(1, true, "unknown"), /Unknown Classic mode/);
    assert.equal(JSON.stringify(rules), other);
});
