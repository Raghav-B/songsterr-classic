const CDN = "https://static3.songsterr.com/production-main/static3/latest/";

async function tabRules(tabId) {
    const rules = await chrome.declarativeNetRequest.getSessionRules();
    return rules.filter(rule => rule.condition.tabIds?.includes(tabId));
}

let pendingChange = Promise.resolve();

function changeTab(tabId, enable) {
    // Session rule IDs are shared by all tabs. Serialize the read/replace
    // transaction so two popup clicks cannot allocate the same IDs.
    const change = pendingChange.then(() => applyTabState(tabId, enable));
    pendingChange = change.catch(() => {});
    return change;
}

async function applyTabState(tabId, enable) {
    const owned = await tabRules(tabId);
    const removeRuleIds = owned.map(rule => rule.id);
    if (!enable) {
        await chrome.declarativeNetRequest.updateSessionRules({ removeRuleIds });
        await chrome.action.setBadgeText({ tabId, text: "" });
        await chrome.tabs.reload(tabId, { bypassCache: true });
        return;
    }

    const tab = await chrome.tabs.get(tabId);
    const url = new URL(tab.url);
    if (url.origin !== "https://www.songsterr.com") {
        throw new Error("Open a Songsterr song before enabling Classic.");
    }
    if (!url.pathname.startsWith("/a/wsa/")) {
        throw new Error("Start Classic on a song page, not an account or payment page.");
    }

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

    // Classic changes frontend assets, never blocks API writes. Removing the
    // tab's old rules also clears preview blocks left by a 0.2.x installation.
    await chrome.declarativeNetRequest.updateSessionRules({ removeRuleIds, addRules });
    await chrome.action.setBadgeBackgroundColor({ tabId, color: "#2876f9" });
    await chrome.action.setBadgeText({ tabId, text: "ON" });
    await chrome.tabs.reload(tabId, { bypassCache: true });
}

chrome.runtime.onMessage.addListener((message, sender, respond) => {
    (async () => {
        if (message.action === "status") {
            const rules = await tabRules(message.tabId);
            return { enabled: rules.length > 0, legacyPreview: rules.some(rule => rule.action.type === "block") };
        }
        if (message.action !== "enable" && message.action !== "disable") {
            throw new Error("Unknown Classic action");
        }
        await changeTab(message.tabId, message.action === "enable");
        return { enabled: message.action === "enable", legacyPreview: false };
    })().then(respond).catch(error => respond({ error: error.message }));
    return true;
});

chrome.tabs.onRemoved.addListener(async tabId => {
    const rules = await tabRules(tabId);
    await chrome.declarativeNetRequest.updateSessionRules({ removeRuleIds: rules.map(rule => rule.id) });
});
