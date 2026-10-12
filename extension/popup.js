const toggle = document.getElementById("toggle");
const status = document.getElementById("status");
const description = document.getElementById("description");
const stateLabel = document.getElementById("state-label");
const errorNotice = document.getElementById("error");
let tabId;
let enabled = false;

function show(result) {
    if (result.error) throw new Error(result.error);
    // An old preview can survive an extension update. Present it as needing
    // activation: the next ON replaces its old blocks without a second mode.
    enabled = result.enabled && !result.legacyPreview;
    document.body.dataset.state = enabled ? "on" : "off";
    toggle.setAttribute("aria-checked", String(enabled));
    toggle.removeAttribute("aria-busy");
    toggle.disabled = false;
    stateLabel.textContent = enabled ? "On" : "Off";
    description.textContent = enabled ? "July layout · editing enabled" : "Current Songsterr layout";
    status.textContent = enabled ? "Classic is active on this tab" : "Ready when you are";
    if (result.legacyPreview) {
        description.textContent = "Older preview needs a refresh";
        status.textContent = "Turn on to enable Classic with editing";
    }
}

async function start() {
    toggle.disabled = true;
    errorNotice.hidden = true;
    document.getElementById("version").textContent = "v" + chrome.runtime.getManifest().version;
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    tabId = tab?.id;
    const url = new URL(tab?.url || "about:blank");
    if (url.origin !== "https://www.songsterr.com") {
        document.body.dataset.state = "unavailable";
        stateLabel.textContent = "Not here";
        description.textContent = "Open a Songsterr song to begin";
        status.textContent = "Available on songsterr.com";
        return;
    }
    const result = await chrome.runtime.sendMessage({ action: "status", tabId });
    if (result.error) throw new Error(result.error);
    // Active Classic tabs can navigate to My tabs/search. They must still be
    // switchable OFF there; only initial activation needs a song URL.
    if (!result.enabled && !url.pathname.startsWith("/a/wsa/")) {
        document.body.dataset.state = "unavailable";
        stateLabel.textContent = "Open a song";
        description.textContent = "Choose a song before switching";
        status.textContent = "Your current page stays unchanged";
        return;
    }
    show(result);
}

toggle.addEventListener("click", async () => {
    const enable = !enabled;
    toggle.disabled = true;
    toggle.setAttribute("aria-busy", "true");
    document.body.dataset.state = "busy";
    stateLabel.textContent = "Switching";
    status.textContent = enable ? "Loading Classic…" : "Restoring current interface…";
    errorNotice.hidden = true;
    try {
        show(await chrome.runtime.sendMessage({ action: enable ? "enable" : "disable", tabId }));
    } catch (error) {
        // A tab reload may fail after its network rules changed. Re-read the
        // real rules so the switch never invents a successful rollback.
        try {
            show(await chrome.runtime.sendMessage({ action: "status", tabId }));
        } catch {
            document.body.dataset.state = "unavailable";
            stateLabel.textContent = "Unavailable";
            status.textContent = "Reopen the popup to check this tab";
            toggle.removeAttribute("aria-busy");
        }
        errorNotice.textContent = error.message;
        errorNotice.hidden = false;
    }
});

start().catch(error => {
    document.body.dataset.state = "unavailable";
    stateLabel.textContent = "Unavailable";
    status.textContent = "Could not read this tab";
    errorNotice.textContent = error.message;
    errorNotice.hidden = false;
});
