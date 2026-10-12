import { adaptState } from "./compat.mjs";
import { installLocalSprites } from "./local-sprites.mjs";

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
    await installLocalSprites();
    document.documentElement.dataset.songsterrClassic = "july-2026";
    // The build pins local bytes and records the entry's source-location patch.
    // API requests still run from the live Songsterr page and worker origins.
    await import("./vendor/appClient-CQbxiWv10TmWc-Ge.js");
} catch (error) {
    console.error("Songsterr Classic could not start", error);
    const notice = document.createElement("p");
    notice.textContent = "Classic could not start. Open the extension and choose Restore current UI.";
    notice.style.cssText = "position:fixed;top:0;left:0;right:0;padding:16px;background:#fee;color:#411;z-index:2147483647;font:16px sans-serif";
    document.body.append(notice);
}
