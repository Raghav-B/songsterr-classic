const toggle = document.getElementById("toggle");
const status = document.getElementById("status");
const notice = document.getElementById("notice");
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
    status.textContent = enabled ? "Classic on" : "Classic off";
    notice.hidden = !result.legacyPreview;
    if (result.legacyPreview) {
        notice.textContent = "Turn on to update the older preview.";
        status.textContent = "Turn on to enable Classic with editing";
    }
}

async function start() {
    toggle.disabled = true;
    errorNotice.hidden = true;
    notice.hidden = true;
    document.getElementById("version").textContent = "v" + chrome.runtime.getManifest().version;
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    tabId = tab?.id;
    const url = new URL(tab?.url || "about:blank");
    if (url.origin !== "https://www.songsterr.com") {
        document.body.dataset.state = "unavailable";
        notice.hidden = false;
        notice.textContent = "Open a Songsterr song to begin.";
        status.textContent = notice.textContent;
        return;
    }
    const result = await chrome.runtime.sendMessage({ action: "status", tabId });
    if (result.error) throw new Error(result.error);
    // Active Classic tabs can navigate to My tabs/search. They must still be
    // switchable OFF there; only initial activation needs a song URL.
    if (!result.enabled && !url.pathname.startsWith("/a/wsa/")) {
        document.body.dataset.state = "unavailable";
        notice.hidden = false;
        notice.textContent = "Open a song before switching.";
        status.textContent = notice.textContent;
        return;
    }
    show(result);
}

toggle.addEventListener("click", async () => {
    const enable = !enabled;
    toggle.disabled = true;
    toggle.setAttribute("aria-busy", "true");
    document.body.dataset.state = "busy";
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
            status.textContent = "Reopen the popup to check this tab";
            toggle.removeAttribute("aria-busy");
        }
        errorNotice.textContent = error.message;
        errorNotice.hidden = false;
    }
});

start().catch(error => {
    document.body.dataset.state = "unavailable";
    status.textContent = "Could not read this tab";
    errorNotice.textContent = error.message;
    errorNotice.hidden = false;
});

// Escape dismisses help without changing the switch; a new hover/focus can reopen it.
const toggleWrap = document.querySelector(".toggle-wrap");
document.addEventListener("keydown", event => {
    if (event.key === "Escape") toggleWrap.dataset.dismissed = "true";
});
for (const event of ["mouseleave", "focusout"]) {
    toggleWrap.addEventListener(event, () => delete toggleWrap.dataset.dismissed);
}
