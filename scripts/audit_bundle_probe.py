"""Test extension-owned July bytes without changing the installed extension.

The prototype uses Chrome's debugger response interception on the opted-in tab.
It preserves original script URLs and vendor bytes, not account entitlements.
Every non-read request is blocked by the isolated test context as well.
"""
import asyncio
import json
import shutil
import tempfile
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "artifacts/api-audit-2026-10-12"
CHROME = "/home/raghavb/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome"

MIRROR = r'''
const localServed = [], localErrors = [];
globalThis.localProbe = {served:localServed, errors:localErrors};
let localNames;
chrome.debugger.onEvent.addListener(async (source, method, event) => {
    if (method !== 'Fetch.requestPaused') return;
    try {
        const url = new URL(event.request.url);
        const name = url.pathname.split('/').pop();
        if (!localNames.has(name)) {
            await chrome.debugger.sendCommand(source, 'Fetch.continueRequest', {requestId:event.requestId});
            return;
        }
        const response = await fetch(chrome.runtime.getURL('vendor/' + name));
        if (!response.ok) throw new Error('Missing bundled asset: ' + name);
        const bytes = new Uint8Array(await response.arrayBuffer());
        let raw = '';
        for (let i=0;i<bytes.length;i+=16384) raw += String.fromCharCode(...bytes.subarray(i,i+16384));
        const mime = name.endsWith('.css') ? 'text/css' : name.endsWith('.wasm') ? 'application/wasm' : 'text/javascript';
        await chrome.debugger.sendCommand(source, 'Fetch.fulfillRequest', {
            requestId:event.requestId, responseCode:200,
            responseHeaders:[{name:'Content-Type',value:mime},{name:'Access-Control-Allow-Origin',value:'*'},{name:'Cache-Control',value:'no-store'}],
            body:btoa(raw)
        });
        localServed.push({url:event.request.url,name,bytes:bytes.length});
    } catch (error) {
        localErrors.push({url:event.request.url,error:String(error)});
        await chrome.debugger.sendCommand(source, 'Fetch.failRequest', {requestId:event.requestId,errorReason:'Failed'}).catch(()=>{});
    }
});
async function enableLocal(tabId) {
    localNames = new Set(await (await fetch(chrome.runtime.getURL('local-assets.json'))).json());
    await chrome.debugger.attach({tabId}, '1.3');
    await chrome.debugger.sendCommand({tabId}, 'Fetch.enable', {patterns:[
        {urlPattern:'https://static3.songsterr.com/production-main/static3/latest/*',requestStage:'Request'},
        {urlPattern:'https://www.songsterr.com/static3/latest/*',requestStage:'Request'}
    ]});
}
'''


async def main():
    temporary = Path(tempfile.mkdtemp(prefix="songsterr-bundle-probe-"))
    extension = temporary / "extension"
    shutil.copytree(ROOT / "extension", extension)
    manifest = json.loads((extension / "manifest.json").read_text())
    manifest["permissions"].append("debugger")
    (extension / "manifest.json").write_text(json.dumps(manifest))
    names = sorted(p.name for p in (AUDIT / "july").iterdir())
    for name in names:
        shutil.copy2(AUDIT / "july" / name, extension / "vendor" / name)
    (extension / "local-assets.json").write_text(json.dumps(names))
    background = (extension / "background.js").read_text()
    background = MIRROR + background.replace(
        'const assets = await (await fetch',
        'await enableLocal(tabId);\n    const assets = await (await fetch', 1)
    (extension / "background.js").write_text(background)
    receipt = {"prototype_only": True, "writes_blocked": True, "errors": [], "checks": {}, "responses": []}
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            str(temporary / "profile"), headless=True, executable_path=CHROME,
            viewport={"width":1440,"height":1000},
            args=["--no-sandbox", "--disable-dev-shm-usage", "--mute-audio",
                  "--disable-extensions-except=" + str(extension), "--load-extension=" + str(extension)],
            ignore_default_args=["--disable-extensions"])
        try:
            async def read_only(route):
                if route.request.method not in ("GET", "HEAD", "OPTIONS"):
                    await route.abort()
                else:
                    await route.continue_()
            await context.route("**/*", read_only)
            worker = context.service_workers[0] if context.service_workers else await context.wait_for_event("serviceworker")
            extension_id = worker.url.split("/")[2]
            page = await context.new_page()
            page.on("pageerror", lambda e: receipt["errors"].append(str(e)))
            from urllib.parse import urlsplit
            phase = "current"
            def response_seen(response):
                parsed = urlsplit(response.url)
                if parsed.hostname and parsed.hostname.endswith("songsterr.com"):
                    receipt["responses"].append({"phase":phase,"host":parsed.hostname,"path":parsed.path,"method":response.request.method,"status":response.status})
            page.on("response", response_seen)
            await page.goto("https://www.songsterr.com/a/wsa/red-hot-chili-peppers-californication-tab-s439?sw=off",wait_until="domcontentloaded")
            popup = await context.new_page()
            await popup.goto(f"chrome-extension://{extension_id}/popup.html")
            tab_id = await popup.evaluate("async()=> (await chrome.tabs.query({url:'https://www.songsterr.com/*'}))[0].id")
            phase = "classic"
            receipt["enable"] = await popup.evaluate("id=>chrome.runtime.sendMessage({action:'enable',tabId:id})",tab_id)
            await page.wait_for_timeout(12000)
            receipt["checks"]["classic"] = await page.evaluate("document.documentElement.dataset.songsterrClassic")
            receipt["url"] = page.url
            receipt["body"] = (await page.locator("body").inner_text())[:800]
            await page.locator("#control-mixer").last.click(timeout=10000)
            await page.get_by_text("Flea",exact=False).first.wait_for(timeout=10000)
            receipt["checks"]["mixer"] = True
            await page.get_by_text('John Frusciante | Gretsch White Falcon | Lead Guitar',exact=True).last.click()
            await page.locator("#control-source").click()
            await page.locator("#control-play").click()
            await page.wait_for_timeout(5000)
            receipt["checks"]["synth_playing"] = await page.locator("#control-play").get_attribute("aria-pressed")
            receipt["checks"]["synth_can_play"] = await page.locator("#control-play").get_attribute("data-can-play")
            await page.locator("#control-play").click()
            await page.locator("#control-editor").click()
            await page.locator("#control-import").wait_for(timeout=10000)
            receipt["checks"]["editor"] = True
            not_now = page.get_by_role("button",name="Not now")
            if await not_now.is_visible():
                await not_now.click()
            await page.wait_for_timeout(11000)
            receipt["checks"]["still_on_songsterr"] = page.url.startswith("https://www.songsterr.com/")
            await page.screenshot(path=str(AUDIT / "bundled-prototype.png"))
        except Exception as error:
            receipt["failure"] = str(error)
        finally:
            try:
                proof = await worker.evaluate("globalThis.localProbe")
                receipt["served"] = proof["served"]
                receipt["mirror_errors"] = proof["errors"]
            except Exception as error:
                receipt["inspection_error"] = str(error)
            await context.close()
    shutil.rmtree(temporary)
    (AUDIT / "bundled-prototype.json").write_text(json.dumps(receipt, indent=2)+"\n")
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
