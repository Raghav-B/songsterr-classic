const button = document.getElementById("toggle");
const status = document.getElementById("status");
let tabId;
let enabled = false;

function show(result) {
    if (result.error) throw new Error(result.error);
    enabled = result.enabled;
    button.textContent = enabled ? "Restore current UI" : "Load July UI";
    status.textContent = enabled ? "Classic is on · read-only" : "Current Songsterr UI";
    button.disabled = false;
}

async function start() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    tabId = tab.id;
    show(await chrome.runtime.sendMessage({ action: "status", tabId }));
}

button.addEventListener("click", async () => {
    button.disabled = true;
    try {
        show(await chrome.runtime.sendMessage({ action: enabled ? "disable" : "enable", tabId }));
    } catch (error) {
        status.textContent = error.message;
        button.disabled = false;
    }
});
start().catch(error => { status.textContent = error.message; });
