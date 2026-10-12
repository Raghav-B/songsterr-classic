const button = document.getElementById("toggle");
const status = document.getElementById("status");
const editing = document.getElementById("editing");
let tabId;
let enabled = false;

function show(result) {
    if (result.error) throw new Error(result.error);
    enabled = result.enabled;
    button.textContent = enabled ? "Restore current UI" : "Load July UI";
    status.textContent = enabled ? (result.mode === "editing" ? "Classic · experimental editing" : "Classic · read-only preview") : "Current Songsterr UI";
    button.disabled = false;
    editing.disabled = enabled && result.mode === "editing";
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
editing.addEventListener("click", async () => {
    editing.disabled = true;
    try {
        show(await chrome.runtime.sendMessage({action:"enable",tabId,mode:"editing"}));
    } catch (error) {
        status.textContent = error.message;
        editing.disabled = false;
    }
});
start().catch(error => { status.textContent = error.message; });
