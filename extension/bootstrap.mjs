import { adaptState } from "./compat.mjs";

try {
    const stateElement = document.getElementById("state");
    const root = document.getElementById("root");
    if (!stateElement || !root) {
        throw new Error("Songsterr did not provide the expected page bootstrap.");
    }
    const state = adaptState(JSON.parse(stateElement.textContent));
    stateElement.textContent = JSON.stringify(state);

    // The server now renders October's layout. Hydrating that DOM with July's
    // components leaves mismatched navigation behind, so rebuild only #root.
    root.replaceChildren();
    document.documentElement.dataset.songsterrClassic = "july-2026";
    const preview = document.createElement("aside");
    preview.id = "songsterr-classic-status";
    preview.textContent = "Classic preview · saving disabled";
    preview.title = "Use the extension button to restore the current UI.";
    preview.style.cssText = "position:fixed;bottom:78px;right:12px;padding:6px 10px;border-radius:4px;background:#fff0d0;color:#563b08;z-index:1000;font:12px system-ui,sans-serif;box-shadow:0 1px 5px #0002";
    document.body.append(preview);
    // Songsterr's client verifies its own source domain. Keep the original
    // pinned CDN URL and the vendor check intact; this is not an offline fork.
    await import("https://static3.songsterr.com/production-main/static3/latest/appClient-CQbxiWv10TmWc-Ge.js");
} catch (error) {
    console.error("Songsterr Classic could not start", error);
    const notice = document.createElement("p");
    notice.textContent = "Classic could not start. Open the extension and choose Restore current UI.";
    notice.style.cssText = "position:fixed;top:0;left:0;right:0;padding:16px;background:#fee;color:#411;z-index:2147483647;font:16px sans-serif";
    document.body.append(notice);
}
