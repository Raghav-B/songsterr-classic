"""Exercise the real MV3 extension in an isolated, logged-out Chrome session."""
import asyncio
import json
import re
import sys
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
EXTENSION = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "extension"


async def main():
    async with async_playwright() as p:
        import tempfile
        profile = tempfile.mkdtemp(prefix="songsterr-classic-qa-")
        context = await p.chromium.launch_persistent_context(
            profile, headless=True, color_scheme="dark", executable_path="/home/raghavb/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome",
            args=["--no-sandbox", "--disable-dev-shm-usage", "--mute-audio",
                  "--disable-extensions-except=" + str(EXTENSION),
                  "--load-extension=" + str(EXTENSION)],
            ignore_default_args=["--disable-extensions"],
        )
        try:
            worker = context.service_workers[0] if context.service_workers else await context.wait_for_event("serviceworker")
            extension_id = worker.url.split("/")[2]
            print("extension", extension_id, flush=True)
            page = await context.new_page()
            page.on("framenavigated", lambda f: print("NAV", f.url, flush=True) if f == page.main_frame else None)
            await page.goto("https://www.songsterr.com/a/wsa/red-hot-chili-peppers-californication-tab-s439")
            await page.set_viewport_size({"width": 1440, "height": 1000})
            original_user = await page.evaluate("JSON.parse(document.getElementById('state').textContent).user")
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            popup = await context.new_page()
            await popup.goto(f"chrome-extension://{extension_id}/popup.html")
            tab_id = await popup.evaluate("async () => (await chrome.tabs.query({url:'https://www.songsterr.com/*'}))[0].id")
            result = await popup.evaluate("id => chrome.runtime.sendMessage({action:'enable',tabId:id})", tab_id)
            print("enable", result, flush=True)
            print("rules", await popup.evaluate("async()=> (await chrome.declarativeNetRequest.getSessionRules()).slice(0,3)"), flush=True)
            await page.wait_for_timeout(12000)
            (ROOT / "artifacts").mkdir(exist_ok=True)
            await page.screenshot(path=str(ROOT / "artifacts/extension.png"))
            print(json.dumps({"classic": await page.evaluate("document.documentElement.dataset.songsterrClassic"),
                              "errors": list(dict.fromkeys(errors))[:10],
                              "url": page.url, "text": (await page.locator("body").inner_text())[:1000]}), flush=True)
            print("controls", await page.locator("button,[role=button]").evaluate_all("es=>es.map(e=>({id:e.id,title:e.title,label:e.getAttribute('aria-label'),text:e.textContent.slice(0,60)}))"), flush=True)
            assert await page.evaluate("document.documentElement.dataset.songsterrClassic") == "july-2026"
            assert await page.evaluate("JSON.parse(document.getElementById('state').textContent).user") == original_user
            await page.locator("#control-mixer").last.click()
            await page.get_by_text("Flea", exact=False).first.wait_for(timeout=15000)
            print("mixer", (await page.locator("body").inner_text())[-6000:], flush=True)
            await page.screenshot(path=str(ROOT / "artifacts/mixer.png"))
            await page.get_by_text(re.compile('Michael "Flea"')).first.click()
            await page.wait_for_timeout(1500)
            assert "Flea" in await page.locator("#control-mixer").last.inner_text()
            print("track switching verified", flush=True)
            await page.locator("#control-mixer").last.click()
            await page.get_by_text("John Frusciante | Gretsch White Falcon | Lead Guitar", exact=True).last.click()
            await page.locator("#control-source").click()
            await page.locator("#control-play").click()
            await page.wait_for_timeout(6000)
            print("play title", await page.locator("#control-play").get_attribute("title"), flush=True)
            print("play text", (await page.locator("body").inner_text())[:900], flush=True)
            await page.screenshot(path=str(ROOT / "artifacts/playing.png"))
            assert await page.locator("#control-play").get_attribute("aria-pressed") == "true"
            assert await page.locator("#control-play").get_attribute("data-can-play") == "true"
            await page.locator("#control-play").click()
            assert await page.locator("#control-play").get_attribute("aria-pressed") == "false"
            print("synth play and pause verified", flush=True)
            await page.locator("#control-editor").click()
            await page.locator("#control-import").wait_for(timeout=15000)
            await page.wait_for_timeout(2500)
            not_now = page.get_by_role("button", name="Not now")
            if await not_now.is_visible():
                await not_now.click()
            await page.wait_for_timeout(800)
            print("editor", (await page.locator("body").inner_text())[:1800], flush=True)
            await page.screenshot(path=str(ROOT / "artifacts/editor.png"))
            print("editor controls", await page.locator("button").evaluate_all("es=>es.map(e=>({id:e.id,title:e.title,text:e.textContent.slice(0,40)}))"), flush=True)

            failures = []
            page.on("requestfailed", lambda request: failures.append({"url":request.url,"failure":request.failure}) if "__classic_write_probe__" in request.url else None)
            blocked = await page.evaluate("async()=>{try{await fetch('/__classic_write_probe__',{method:'POST'});return false}catch{return true}}")
            assert blocked
            assert any("BLOCKED_BY_CLIENT" in failure["failure"] for failure in failures), failures
            print("write block verified", failures, flush=True)
            other = await context.new_page()
            await other.goto("https://www.songsterr.com/a/wsa/red-hot-chili-peppers-californication-tab-s439")
            await other.wait_for_timeout(2000)
            assert await other.evaluate("document.documentElement.dataset.songsterrClassic") is None
            await other.close()
            print("other tab unchanged", flush=True)
            result = await popup.evaluate("id => chrome.runtime.sendMessage({action:'disable',tabId:id})", tab_id)
            assert result == {"enabled":False}, result
            await page.wait_for_timeout(5000)
            assert await page.evaluate("document.documentElement.dataset.songsterrClassic") is None
            await page.screenshot(path=str(ROOT / "artifacts/restored.png"))
            print("restore verified", flush=True)
            print("final errors", list(dict.fromkeys(errors)), flush=True)
        finally:
            await context.close()
            import shutil
            shutil.rmtree(profile)


asyncio.run(main())
