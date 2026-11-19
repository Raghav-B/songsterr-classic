const CDN = "https://static3.songsterr.com/production-main/static3/latest/";

// Settings live in local storage so they survive browser restarts.
// everyTab: the user's choice on the settings page (off keeps the original
// one-tab behaviour). classicOn: the last popup switch position, used only
// while everyTab is on.
const DEFAULTS = { everyTab: false, classicOn: false };

async function settings() {
    return { ...DEFAULTS, ...(await chrome.storage.local.get(Object.keys(DEFAULTS))) };
}

const SW_SCRIPT = "^https://www\\.songsterr\\.com/service-worker[^/]*\\.js";
const isWorkerBlock = rule => rule.action.type === "block" && rule.condition.regexFilter === SW_SCRIPT;

async function tabRules(tabId) {
    const rules = await chrome.declarativeNetRequest.getSessionRules();
    return rules.filter(rule => rule.condition.tabIds?.includes(tabId));
}

let pendingChange = Promise.resolve();

function queue(work) {
    // Session rule IDs are shared by all tabs. Serialize the read/replace
    // transaction so two changes cannot allocate the same IDs.
    const change = pendingChange.then(work);
    pendingChange = change.catch(() => {});
    return change;
}

function changeTab(tabId, enable) {
    return queue(() => applyTabState(tabId, enable));
}

function assertSongUrl(href) {
    const url = new URL(href);
    if (url.origin !== "https://www.songsterr.com") {
        throw new Error("Open a Songsterr song before enabling Classic.");
    }
    if (!url.pathname.startsWith("/a/wsa/")) {
        throw new Error("Start Classic on a song page, not an account or payment page.");
    }
}

async function installRules(tabId) {
    const owned = await tabRules(tabId);
    const removeRuleIds = owned.map(rule => rule.id);
    const assets = await (await fetch(chrome.runtime.getURL("asset-list.json"))).json();
    const allRules = await chrome.declarativeNetRequest.getSessionRules();
    let id = Math.max(0, ...allRules.map(rule => rule.id)) + 1;
    const addRules = [];
    const redirect = (condition, path, priority = 1) => addRules.push({
        id: id++, priority,
        action: { type: "redirect", redirect: { extensionPath: path } },
        condition: { ...condition, tabIds: [tabId] },
    });

    redirect({regexFilter: "^https://static3\\.songsterr\\.com/production-main/static3/latest/appClient-[A-Za-z0-9_-]+\\.js$", resourceTypes: ["script"]}, "/bootstrap.mjs", 10);
    redirect({regexFilter: "^https://static3\\.songsterr\\.com/production-main/static3/latest/appClient-[A-Za-z0-9_-]+\\.css$", resourceTypes: ["stylesheet"]}, "/vendor/appClient-442d1888c9.css", 10);
    redirect({regexFilter: "^https://static3\\.songsterr\\.com/production-main/static3/latest/common-[A-Za-z0-9_-]+\\.css$", resourceTypes: ["stylesheet"]}, "/vendor/common-7b4ff45b27.css", 10);
    for (const name of assets) {
        for (const base of [CDN, "https://www.songsterr.com/static3/latest/"]) {
            redirect({urlFilter: "|" + base + name + "|"}, "/vendor/" + name, 20);
        }
    }

    const media = await (await fetch(chrome.runtime.getURL("media-assets.json"))).json();
    for (const path of media) {
        const name = path.split("/").pop();
        for (const origin of ["https://www.songsterr.com", "https://static3.songsterr.com/production-main"]) {
            redirect({urlFilter: "|" + origin + path + "|"}, "/media/" + name, 5);
        }
    }

    // Songsterr's service worker serves the current frontend from its own
    // cache, outside any tab, where per-tab redirects cannot reach. Keep it
    // from installing or updating while Classic is in use.
    if (!allRules.some(isWorkerBlock)) {
        addRules.push({ id: id++, priority: 1, action: { type: "block" }, condition: { regexFilter: SW_SCRIPT } });
    }

    // Classic changes frontend assets, never blocks API writes. Removing the
    // tab's old rules also clears preview blocks left by a 0.2.x installation.
    await chrome.declarativeNetRequest.updateSessionRules({ removeRuleIds, addRules });
    await chrome.action.setBadgeBackgroundColor({ tabId, color: "#2876f9" });
    await chrome.action.setBadgeText({ tabId, text: "ON" });
}

async function applyTabState(tabId, enable) {
    if (!enable) {
        const removeRuleIds = (await tabRules(tabId)).map(rule => rule.id);
        await chrome.declarativeNetRequest.updateSessionRules({ removeRuleIds });
        await chrome.action.setBadgeText({ tabId, text: "" });
        await chrome.tabs.reload(tabId, { bypassCache: true });
        return;
    }
    assertSongUrl((await chrome.tabs.get(tabId)).url);
    await installRules(tabId);
    await chrome.tabs.reload(tabId, { bypassCache: true });
}

// "Keep Classic on in new tabs": when a song page starts loading in any tab,
// give that tab its rules before the page requests its scripts. Like the
// popup, this only starts Classic on song pages; a Classic tab may still
// browse elsewhere on Songsterr afterwards.
const autoPending = new Map();
const commits = new Map();
const autoReloading = new Set();
const SONG_PAGES = { url: [{ hostEquals: "www.songsterr.com", pathPrefix: "/a/wsa/" }] };

function watchCommit(tabId) {
    // Created before any await, so a fast commit cannot be missed.
    let resolve;
    const committed = new Promise(done => { resolve = done; });
    commits.get(tabId)?.resolve();
    commits.set(tabId, { committed, resolve });
    return committed;
}

async function autoEnable(tabId, url, committed) {
    const { everyTab, classicOn } = await settings();
    if (!everyTab || !classicOn) return;
    assertSongUrl(url);
    await queue(async () => {
        if ((await tabRules(tabId)).length > 0) return;
        autoReloading.add(tabId);
        await installRules(tabId);
        // Chrome can serve Songsterr's scripts from cache, which skips the
        // redirect rules. Reload past the cache, exactly like the popup does.
        // Wait for the page to commit first: a reload sent mid-navigation is
        // dropped. The reload finds the rules in place, so it does not loop.
        await Promise.race([committed, new Promise(done => setTimeout(done, 10000))]);
        try {
            await chrome.tabs.reload(tabId, { bypassCache: true });
        } finally {
            autoReloading.delete(tabId);
        }
    });
}

chrome.webNavigation.onBeforeNavigate.addListener(details => {
    if (details.frameId !== 0 || details.tabId < 0) return;
    const committed = watchCommit(details.tabId);
    const work = autoEnable(details.tabId, details.url, committed).catch(error => console.error("Classic auto-enable:", error));
    autoPending.set(details.tabId, work);
    work.finally(() => { if (autoPending.get(details.tabId) === work) autoPending.delete(details.tabId); });
}, SONG_PAGES);

chrome.webNavigation.onCommitted.addListener(details => {
    if (details.frameId !== 0) return;
    commits.get(details.tabId)?.resolve();
    commits.delete(details.tabId);
    if (new URL(details.url).origin === "https://www.songsterr.com") {
        evictWorker(details.tabId).catch(error => console.error("Classic worker check:", error));
    }
});

// A normal reload of a Classic tab can be answered by Songsterr's service
// worker with the current frontend. If that happened, remove the worker and
// reload past it, like the popup does. That reload is not served by a
// worker, so this runs at most once per navigation.
async function evictWorker(tabId) {
    if (autoReloading.has(tabId) || (await tabRules(tabId)).length === 0) return;
    const [{ result: controlled } = {}] = await chrome.scripting.executeScript({
        target: { tabId },
        func: async () => {
            const controlled = Boolean(navigator.serviceWorker?.controller);
            const registrations = await navigator.serviceWorker?.getRegistrations() ?? [];
            await Promise.all(registrations.map(registration => registration.unregister()));
            return controlled;
        },
    });
    if (controlled) await chrome.tabs.reload(tabId, { bypassCache: true });
}

async function setEveryTab(everyTab) {
    // Turning the setting on means "Classic by default": every song tab opened
    // from now on starts in Classic until the popup switch turns it off.
    await chrome.storage.local.set({ everyTab, classicOn: everyTab });
}

chrome.runtime.onMessage.addListener((message, sender, respond) => {
    (async () => {
        if (message.action === "status") {
            // Content scripts may query only their own tab; popup messages carry its ID.
            const tabId = sender.tab?.id ?? message.tabId;
            // Let this tab's auto-enable finish so the Firefox loader sees it.
            await autoPending.get(tabId);
            const rules = await tabRules(tabId);
            return { enabled: rules.length > 0, legacyPreview: rules.some(rule => rule.action.type === "block") };
        }
        if (message.action === "getSettings") return settings();
        if (message.action === "setEveryTab") {
            await setEveryTab(Boolean(message.everyTab));
            return settings();
        }
        if (message.action !== "enable" && message.action !== "disable") {
            throw new Error("Unknown Classic action");
        }
        const enable = message.action === "enable";
        // Save first: switching reloads the tab, and that reload must already
        // see the new choice or auto-enable would undo an OFF.
        if ((await settings()).everyTab) await chrome.storage.local.set({ classicOn: enable });
        await changeTab(message.tabId, enable);
        return { enabled: enable, legacyPreview: false };
    })().then(respond).catch(error => respond({ error: error.message }));
    return true;
});

chrome.tabs.onRemoved.addListener(async tabId => {
    autoPending.delete(tabId);
    commits.get(tabId)?.resolve();
    commits.delete(tabId);
    autoReloading.delete(tabId);
    const rules = await tabRules(tabId);
    await chrome.declarativeNetRequest.updateSessionRules({ removeRuleIds: rules.map(rule => rule.id) });
});
