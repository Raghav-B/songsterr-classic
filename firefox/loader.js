// Firefox rejects cross-origin module redirects to moz-extension URLs. The
// active tab's DNR rules keep the current app from executing; replace its
// entry element with a direct packaged URL so the shared July bootstrap runs.
(async () => {
    const state = await chrome.runtime.sendMessage({ action: "status" });
    if (state.error) throw new Error(state.error);
    if (!state.enabled) return;

    function relocate() {
        for (const script of document.querySelectorAll('script[type="module"][src]')) {
            if (!/^https:\/\/static3\.songsterr\.com\/production-main\/static3\/latest\/appClient-[\w-]+\.js$/.test(script.src)) continue;
            const replacement = document.createElement("script");
            replacement.type = "module";
            replacement.src = chrome.runtime.getURL("bootstrap.mjs");
            script.replaceWith(replacement);
        }
        for (const link of document.querySelectorAll('link[rel="stylesheet"][href]')) {
            const match = link.href.match(/^https:\/\/static3\.songsterr\.com\/production-main\/static3\/latest\/(appClient|common)-[\w-]+\.css$/);
            if (!match) continue;
            const file = match[1] === "appClient" ? "appClient-442d1888c9.css" : "common-7b4ff45b27.css";
            link.href = chrome.runtime.getURL("vendor/" + file);
        }
    }

    // Start observing before the first scan: parser insertions can otherwise
    // slip between scanning the head and installing the observer.
    const observer = new MutationObserver(relocate);
    observer.observe(document, { childList: true, subtree: true });
    relocate();
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => { relocate(); observer.disconnect(); }, { once: true });
    } else {
        observer.disconnect();
    }
})().catch(error => console.error("Classic Firefox loader:", error));
