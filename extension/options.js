const everyTab = document.getElementById("every-tab");
const saved = document.getElementById("saved");
const errorNotice = document.getElementById("error");

function show(settings) {
    if (settings?.error) throw new Error(settings.error);
    everyTab.setAttribute("aria-checked", String(Boolean(settings.everyTab)));
    everyTab.disabled = false;
}

function fail(error) {
    errorNotice.textContent = error.message;
    errorNotice.hidden = false;
    everyTab.disabled = false;
}

everyTab.addEventListener("click", async () => {
    const next = everyTab.getAttribute("aria-checked") !== "true";
    everyTab.disabled = true;
    errorNotice.hidden = true;
    try {
        show(await chrome.runtime.sendMessage({ action: "setEveryTab", everyTab: next }));
        saved.textContent = next ? "Saved. Reload any open song tab to switch it over." : "Saved. Classic is per tab again.";
    } catch (error) {
        fail(error);
    }
});

chrome.runtime.sendMessage({ action: "getSettings" }).then(show).catch(fail);
